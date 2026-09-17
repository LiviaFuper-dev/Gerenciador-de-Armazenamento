from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from storage_manager.errors import AppError, OperationCancelled, WrongAccountError
from storage_manager.models import DeleteResult, MessagePreview, ScanResult
from storage_manager.utils import chunks, get_header


ProgressCallback = Callable[[int, int, str], None]


class GmailClient:
    def __init__(self, credentials: Credentials, logger: logging.Logger):
        self.api = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        self.logger = logger

    def verify_account(self, expected_account: str = "") -> str:
        try:
            profile = self.api.users().getProfile(userId="me").execute(num_retries=3)
        except HttpError as exc:
            raise AppError(f"Não foi possível consultar a conta Google: {exc.reason}") from exc
        connected = str(profile.get("emailAddress", "")).strip().casefold()
        if not connected:
            raise AppError("O Google não informou qual conta foi conectada.")
        if expected_account and connected != expected_account.casefold():
            raise WrongAccountError(
                f"A conta conectada foi {connected or '(não identificada)'}.\n\n"
                f"Este aplicativo aceita somente {expected_account}. Desconecte e escolha a conta correta."
            )
        return connected

    def scan_sender(
        self,
        query: str,
        preview_limit: int,
        cancel: threading.Event,
        progress: ProgressCallback,
    ) -> ScanResult:
        message_ids: list[str] = []
        page_token: str | None = None

        # includeSpamTrash garante que todos os e-mails do remetente sejam encontrados.
        while True:
            if cancel.is_set():
                raise OperationCancelled("Análise cancelada. Nenhum e-mail foi alterado.")
            try:
                response = (
                    self.api.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        includeSpamTrash=True,
                        maxResults=500,
                        pageToken=page_token,
                    )
                    .execute(num_retries=3)
                )
            except HttpError as exc:
                raise AppError(f"Falha ao pesquisar os e-mails: {exc.reason}") from exc
            message_ids.extend(item["id"] for item in response.get("messages", []))
            progress(len(message_ids), 0, "Localizando todos os e-mails do remetente...")
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        result = ScanResult(query=query, message_ids=message_ids)
        if not message_ids:
            self.logger.info("Análise concluída sem resultados")
            return result

        details: dict[str, MessagePreview] = {}
        processed = 0

        for group in chunks(message_ids, 100):
            if cancel.is_set():
                raise OperationCancelled("Análise cancelada. Nenhum e-mail foi alterado.")

            def callback(request_id, response, exception):
                nonlocal processed
                processed += 1
                if exception is None and response:
                    headers = response.get("payload", {}).get("headers", [])
                    details[request_id] = MessagePreview(
                        message_id=request_id,
                        subject=get_header(headers, "Subject") or "(sem assunto)",
                        date=get_header(headers, "Date") or "(data não informada)",
                        size_bytes=int(response.get("sizeEstimate", 0)),
                    )
                progress(processed, len(message_ids), "Calculando a estimativa de espaço...")

            batch = self.api.new_batch_http_request(callback=callback)
            for message_id in group:
                request = (
                    self.api.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message_id,
                        format="metadata",
                        metadataHeaders=["Subject", "Date"],
                    )
                )
                batch.add(request, request_id=message_id)
            try:
                batch.execute()
            except HttpError as exc:
                raise AppError(f"Falha ao obter os detalhes dos e-mails: {exc.reason}") from exc

        ordered = [details[item_id] for item_id in message_ids if item_id in details]
        result.previews = ordered[:preview_limit]
        result.total_bytes = sum(item.size_bytes for item in ordered)
        self.logger.info("Análise concluída: %d mensagens encontradas", result.count)
        return result

    def permanently_delete(
        self,
        scan: ScanResult,
        batch_size: int,
        cancel: threading.Event,
        progress: ProgressCallback,
    ) -> DeleteResult:
        # A lista é congelada pela análise. Não refazemos a busca durante a exclusão,
        # pois apagar resultados pode invalidar tokens de paginação.
        deleted = 0
        failed = 0
        for group in chunks(scan.message_ids, batch_size):
            if cancel.is_set():
                break
            try:
                (
                    self.api.users()
                    .messages()
                    .batchDelete(userId="me", body={"ids": group})
                    .execute(num_retries=3)
                )
                deleted += len(group)
            except HttpError as exc:
                failed += len(group)
                self.logger.error("Falha ao excluir lote de %d mensagens: %s", len(group), exc.reason)
            progress(deleted + failed, scan.count, "Excluindo permanentemente em lotes...")

        self.logger.info(
            "Exclusão concluída: solicitadas=%d excluídas=%d falhas=%d",
            scan.count,
            deleted,
            failed,
        )
        return DeleteResult(
            requested=scan.count,
            deleted=deleted,
            failed=failed,
            estimated_bytes=scan.total_bytes,
        )
