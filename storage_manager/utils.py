from __future__ import annotations

from collections.abc import Iterable


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def get_header(headers: list[dict], name: str) -> str:
    wanted = name.casefold()
    for header in headers:
        if str(header.get("name", "")).casefold() == wanted:
            return str(header.get("value", ""))
    return ""
