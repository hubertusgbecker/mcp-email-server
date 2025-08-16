from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EmailData(BaseModel):
    subject: str
    sender: str
    body: str
    date: datetime
    attachments: list[str]
    uid: str | None = None  # IMAP UID for operations like move/copy

    @classmethod
    def from_email(cls, email: dict[str, Any]):
        return cls(
            subject=email["subject"],
            sender=email["from"],
            body=email["body"],
            date=email["date"],
            attachments=email["attachments"],
            uid=email.get("uid"),
        )


class EmailPageResponse(BaseModel):
    page: int
    page_size: int
    before: datetime | None
    since: datetime | None
    subject: str | None
    body: str | None
    text: str | None
    emails: list[EmailData]
    total: int


class FolderInfo(BaseModel):
    """Information about an IMAP folder/mailbox."""
    name: str
    delimiter: str
    flags: list[str]


class EmailOperationResult(BaseModel):
    """Result of email move/copy operations."""
    success: bool
    message: str
    moved_count: int = 0
    copied_count: int = 0
    failed_uids: list[str] = []
