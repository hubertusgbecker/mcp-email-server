"""Integration tests for email move/copy functionality.

These tests demonstrate the complete workflow of the new move/copy features.
They use mocks to avoid requiring actual email servers during testing.
"""
from datetime import datetime
from unittest.mock import patch

import pytest

from mcp_email_server.config import EmailServer, EmailSettings
from mcp_email_server.emails.classic import ClassicEmailHandler
from mcp_email_server.emails.models import EmailOperationResult, FolderInfo


@pytest.fixture
def email_settings():
    return EmailSettings(
        account_name="integration_test",
        full_name="Integration Test User",
        email_address="test@integration.com",
        incoming=EmailServer(
            user_name="test_user",
            password="test_password",
            host="imap.integration.com",
            port=993,
            use_ssl=True,
        ),
        outgoing=EmailServer(
            user_name="test_user",
            password="test_password",
            host="smtp.integration.com",
            port=465,
            use_ssl=True,
        ),
    )


@pytest.fixture
def handler(email_settings):
    return ClassicEmailHandler(email_settings)


class TestEmailManagementWorkflow:
    @pytest.mark.asyncio
    async def test_complete_email_management_workflow(self, handler):
        """Test a complete workflow: list folders, get emails, create folder, move emails."""

        # Step 1: List existing folders
        mock_folders = [
            FolderInfo(name="INBOX", delimiter=".", flags=["HasNoChildren"]),
            FolderInfo(name="Sent", delimiter=".", flags=["HasNoChildren"]),
            FolderInfo(name="Drafts", delimiter=".", flags=["HasNoChildren"]),
        ]

        with patch.object(handler.incoming_client, "list_folders", return_value=mock_folders):
            folders = await handler.list_folders()
            assert len(folders) == 3
            assert any(f.name == "INBOX" for f in folders)
            assert any(f.name == "Sent" for f in folders)
            assert any(f.name == "Drafts" for f in folders)

        # Step 2: Get emails from INBOX
        mock_emails = [
            {
                "subject": "Important Email 1",
                "from": "boss@company.com",
                "body": "This is an important email that needs to be archived.",
                "date": datetime.now(),
                "attachments": [],
                "uid": "12345"
            },
            {
                "subject": "Important Email 2",
                "from": "client@business.com",
                "body": "Another important email for archiving.",
                "date": datetime.now(),
                "attachments": [],
                "uid": "12346"
            }
        ]

        # Mock the email stream
        async def mock_email_stream(*args, **kwargs):
            for email in mock_emails:
                yield email

        with patch.object(handler.incoming_client, "get_emails_stream", side_effect=mock_email_stream):
            with patch.object(handler.incoming_client, "get_email_count", return_value=2):
                emails_result = await handler.get_emails(page=1, page_size=10)
                assert len(emails_result.emails) == 2
                assert emails_result.emails[0].uid == "12345"
                assert emails_result.emails[1].uid == "12346"

        # Step 3: Create a new "Archive" folder
        with patch.object(handler.incoming_client, "create_folder", return_value=True):
            folder_created = await handler.create_folder("Archive")
            assert folder_created is True

        # Step 4: Copy emails to Archive folder
        copy_result = EmailOperationResult(
            success=True,
            message="Successfully copied 2 emails",
            copied_count=2,
            failed_uids=[]
        )

        with patch.object(handler.incoming_client, "copy_emails", return_value=copy_result):
            result = await handler.copy_emails(["12345", "12346"], "Archive")
            assert result.success is True
            assert result.copied_count == 2
            assert len(result.failed_uids) == 0

        # Step 5: Move one email to a different folder
        move_result = EmailOperationResult(
            success=True,
            message="Successfully moved 1 emails",
            moved_count=1,
            failed_uids=[]
        )

        with patch.object(handler.incoming_client, "move_emails", return_value=move_result):
            result = await handler.move_emails(["12345"], "Processed")
            assert result.success is True
            assert result.moved_count == 1
            assert len(result.failed_uids) == 0

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, handler):
        """Test error handling during email operations."""

        # Test failed folder creation
        with patch.object(handler.incoming_client, "create_folder", return_value=False):
            folder_created = await handler.create_folder("Invalid/Folder/Name")
            assert folder_created is False

        # Test partial failure during copy operation
        partial_failure_result = EmailOperationResult(
            success=False,
            message="Successfully copied 1 emails, 1 failed",
            copied_count=1,
            failed_uids=["invalid_uid"]
        )

        with patch.object(handler.incoming_client, "copy_emails", return_value=partial_failure_result):
            result = await handler.copy_emails(["12345", "invalid_uid"], "Archive")
            assert result.success is False
            assert result.copied_count == 1
            assert "invalid_uid" in result.failed_uids

        # Test complete failure during move operation
        complete_failure_result = EmailOperationResult(
            success=False,
            message="Move operation failed: Connection lost",
            moved_count=0,
            failed_uids=["12345", "12346"]
        )

        with patch.object(handler.incoming_client, "move_emails", return_value=complete_failure_result):
            result = await handler.move_emails(["12345", "12346"], "NonExistentFolder")
            assert result.success is False
            assert result.moved_count == 0
            assert len(result.failed_uids) == 2

    @pytest.mark.asyncio
    async def test_email_organization_workflow(self, handler):
        """Test a realistic email organization workflow."""

        # Simulate getting emails with different criteria
        old_emails = [
            {
                "subject": "Old Newsletter",
                "from": "newsletter@company.com",
                "body": "Old newsletter content",
                "date": datetime(2023, 1, 1),
                "attachments": [],
                "uid": "old_001"
            }
        ]

        important_emails = [
            {
                "subject": "URGENT: Action Required",
                "from": "ceo@company.com",
                "body": "Important business matter",
                "date": datetime.now(),
                "attachments": ["report.pdf"],
                "uid": "urgent_001"
            }
        ]

        # Mock getting old emails
        async def mock_old_emails(*args, **kwargs):
            # This will be called for the old emails query
            for email in old_emails:
                yield email

        # Mock getting important emails
        async def mock_important_emails(*args, **kwargs):
            # This will be called for the important emails query
            for email in important_emails:
                yield email

        # Test organizing old emails
        with patch.object(handler.incoming_client, "get_emails_stream", side_effect=mock_old_emails):
            with patch.object(handler.incoming_client, "get_email_count", return_value=1):
                old_result = await handler.get_emails(
                    before=datetime(2023, 12, 31),
                    page_size=100
                )
                assert len(old_result.emails) == 1
                assert old_result.emails[0].uid == "old_001"

        # Create Archive folder and move old emails
        with patch.object(handler.incoming_client, "create_folder", return_value=True):
            await handler.create_folder("Archive_2023")

        move_old_result = EmailOperationResult(
            success=True,
            message="Successfully moved 1 emails",
            moved_count=1,
            failed_uids=[]
        )

        with patch.object(handler.incoming_client, "move_emails", return_value=move_old_result):
            result = await handler.move_emails(["old_001"], "Archive_2023")
            assert result.success is True
            assert result.moved_count == 1

        # Test organizing important emails
        with patch.object(handler.incoming_client, "get_emails_stream", side_effect=mock_important_emails):
            with patch.object(handler.incoming_client, "get_email_count", return_value=1):
                urgent_result = await handler.get_emails(subject="URGENT")
                assert len(urgent_result.emails) == 1
                assert urgent_result.emails[0].uid == "urgent_001"

        # Copy important emails to Important folder
        copy_important_result = EmailOperationResult(
            success=True,
            message="Successfully copied 1 emails",
            copied_count=1,
            failed_uids=[]
        )

        with patch.object(handler.incoming_client, "copy_emails", return_value=copy_important_result):
            result = await handler.copy_emails(["urgent_001"], "Important")
            assert result.success is True
            assert result.copied_count == 1
