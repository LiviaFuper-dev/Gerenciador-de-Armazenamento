from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MessagePreview:
    message_id: str
    subject: str
    date: str
    size_bytes: int


@dataclass
class ScanResult:
    query: str
    message_ids: list[str] = field(default_factory=list)
    previews: list[MessagePreview] = field(default_factory=list)
    total_bytes: int = 0

    @property
    def count(self) -> int:
        return len(self.message_ids)


@dataclass(frozen=True)
class DeleteResult:
    requested: int
    deleted: int
    failed: int
    estimated_bytes: int


def format_bytes(value: int) -> str:
    size = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

