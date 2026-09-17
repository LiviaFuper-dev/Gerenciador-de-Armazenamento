from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from storage_manager.config import application_dir
from storage_manager.errors import MissingClientSecretError
from storage_manager.logging_setup import data_dir


# Exclusão imediata exige este escopo. O aplicativo não solicita outros escopos.
SCOPES = ["https://mail.google.com/"]


def client_secret_path() -> Path:
    override = os.environ.get("GERENCIADOR_GMAIL_CLIENT_SECRET")
    return Path(override).expanduser() if override else application_dir() / "client_secret.json"


def token_path() -> Path:
    return data_dir() / "token.json"


def authorize() -> Credentials:
    secret = client_secret_path()
    if not secret.exists():
        raise MissingClientSecretError(
            "O arquivo client_secret.json ainda não foi configurado.\n\n"
            "Baixe a credencial OAuth do tipo Aplicativo para computador no Google Cloud "
            "e coloque o arquivo ao lado do programa."
        )

    credentials: Credentials | None = None
    stored = token_path()
    if stored.exists():
        try:
            credentials = Credentials.from_authorized_user_file(str(stored), SCOPES)
        except (ValueError, json.JSONDecodeError):
            stored.unlink(missing_ok=True)

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:
            credentials = None

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES)
        credentials = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
            authorization_prompt_message="Abrindo o Google para autorizar o acesso...",
            success_message=(
                "Autorização concluída. Feche esta página e volte ao "
                "Gerenciador de Armazenamento."
            ),
        )
        stored.write_text(credentials.to_json(), encoding="utf-8")

    return credentials


def disconnect() -> None:
    token_path().unlink(missing_ok=True)

