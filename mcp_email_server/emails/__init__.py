import abc
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_email_server.emails.models import EmailOperationResult, EmailPageResponse, FolderInfo


class EmailHandler(abc.ABC):
    @abc.abstractmethod
    async def get_emails(
        self,
        page: int = 1,
        page_size: int = 10,
        before: datetime | None = None,
        after: datetime | None = None,
        subject: str | None = None,
        body: str | None = None,
        text: str | None = None,
        from_address: str | None = None,
        to_address: str | None = None,
        order: str = "desc",
    ) -> "EmailPageResponse":
        """
        Get emails
        """

    @abc.abstractmethod
    async def send_email(
        self, recipients: list[str], subject: str, body: str, cc: list[str] | None = None, bcc: list[str] | None = None
    ) -> None:
        """
        Send email
        """

    @abc.abstractmethod
    async def list_folders(self) -> list["FolderInfo"]:
        """
        List all available folders/mailboxes
        """

    @abc.abstractmethod
    async def create_folder(self, folder_name: str) -> bool:
        """
        Create a new folder/mailbox
        """

    @abc.abstractmethod
    async def copy_emails(self, uids: list[str], destination_folder: str) -> "EmailOperationResult":
        """
        Copy emails to another folder by UID
        """

    @abc.abstractmethod
    async def move_emails(self, uids: list[str], destination_folder: str) -> "EmailOperationResult":
        """
        Move emails to another folder by UID
        """
