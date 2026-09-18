from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass


LATEST_RELEASE_API = (
    "https://api.github.com/repos/"
    "LiviaFuper-dev/Gerenciador-de-Armazenamento/releases/latest"
)
RELEASE_URL_PREFIX = (
    "https://github.com/LiviaFuper-dev/"
    "Gerenciador-de-Armazenamento/releases/"
)
VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    page_url: str


def version_tuple(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Versão inválida: {value}")
    return tuple(int(part) for part in match.groups())


def update_from_release(current_version: str, release: dict) -> UpdateInfo | None:
    tag = str(release.get("tag_name", "")).strip()
    page_url = str(release.get("html_url", "")).strip()
    if not tag or not page_url.startswith(RELEASE_URL_PREFIX):
        return None
    if version_tuple(tag) <= version_tuple(current_version):
        return None
    return UpdateInfo(version=tag.removeprefix("v"), page_url=page_url)


def check_for_update(current_version: str, timeout: float = 5.0) -> UpdateInfo | None:
    request = urllib.request.Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "GerenciadorDeArmazenamento",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            release = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return None
    try:
        return update_from_release(current_version, release)
    except ValueError:
        return None
