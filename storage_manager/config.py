from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from storage_manager.errors import AppError


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AppConfig:
    app_name: str
    expected_account: str
    target_sender: str
    preview_limit: int
    delete_batch_size: int

    @property
    def gmail_query(self) -> str:
        return f"from:{self.target_sender}"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or application_dir() / "app_config.json"
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AppError(f"Configuração não encontrada: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise AppError(f"Configuração inválida em {config_path.name}: {exc}") from exc

    config = AppConfig(
        app_name=str(raw.get("app_name", "Gerenciador de Armazenamento")).strip(),
        expected_account=str(raw.get("expected_account", "")).strip().casefold(),
        target_sender=str(raw.get("target_sender", "")).strip().casefold(),
        preview_limit=int(raw.get("preview_limit", 500)),
        delete_batch_size=int(raw.get("delete_batch_size", 500)),
    )
    if config.expected_account and not EMAIL_PATTERN.fullmatch(config.expected_account):
        raise AppError("A conta esperada em app_config.json não é um e-mail válido.")
    if not EMAIL_PATTERN.fullmatch(config.target_sender):
        raise AppError("O remetente em app_config.json não é um e-mail válido.")
    if config.preview_limit < 1 or config.delete_batch_size not in range(1, 1001):
        raise AppError("Os limites numéricos de app_config.json são inválidos.")
    return config
