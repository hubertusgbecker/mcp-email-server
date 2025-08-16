"""Test email move/copy operations."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from mcp_email_server.config import EmailServer, EmailSettings
from mcp_email_server.emails.classic import ClassicEmailHandler, EmailClient
from mcp_email_server.emails.models import EmailData, EmailOperationResult, FolderInfo


@pytest.fixture
def email_settings():
    return EmailSettings(
        account_name="test_account",
        full_name="Test User",
        email_address="test@example.com",
        incoming=EmailServer(
            user_name="test_user",
            password="test_password",
            host="imap.example.com",
            port=993,
            use_ssl=True,
        ),
        outgoing=EmailServer(
            user_name="test_user",
            password="test_password",
            host="smtp.example.com",
            port=465,
            use_ssl=True,
        ),
    )


@pytest.fixture
def email_client(email_settings):
    return EmailClient(email_settings.incoming)


@pytest.fixture
def classic_handler(email_settings):
    return ClassicEmailHandler(email_settings)


class TestEmailClientFolderOperations:
    @pytest.mark.asyncio
    async def test_list_folders(self, email_client):
        """Test listing folders."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.list = AsyncMock(return_value=(None, [
            b'(\\HasNoChildren) "." "INBOX"',
            b'(\\HasNoChildren) "." "INBOX.Sent"',
            b'(\\HasNoChildren) "." "INBOX.Drafts"',
        ]))
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            folders = await email_client.list_folders()

            assert len(folders) == 3
            assert isinstance(folders[0], FolderInfo)
            assert folders[0].name == "INBOX"
            assert folders[0].delimiter == "."
            assert "HasNoChildren" in folders[0].flags

            mock_imap.login.assert_called_once_with(
                email_client.email_server.user_name, email_client.email_server.password
            )
            mock_imap.list.assert_called_once_with("", "*")
            mock_imap.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder(self, email_client):
        """Test creating a folder."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.create = AsyncMock(return_value=(None, [b'OK']))
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            result = await email_client.create_folder("Test Folder")

            assert result is True
            mock_imap.login.assert_called_once_with(
                email_client.email_server.user_name, email_client.email_server.password
            )
            mock_imap.create.assert_called_once_with("Test Folder")
            mock_imap.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder_failure(self, email_client):
        """Test creating a folder that fails."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.create = AsyncMock(return_value=(None, [b'NO']))
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            result = await email_client.create_folder("Invalid/Folder")

            assert result is False

    @pytest.mark.asyncio
    async def test_copy_emails(self, email_client):
        """Test copying emails."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.select = AsyncMock()
        mock_imap.uid = AsyncMock(return_value=(None, [b'OK']))
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            result = await email_client.copy_emails(["123", "456"], "Archive")

            assert isinstance(result, EmailOperationResult)
            assert result.success is True
            assert result.copied_count == 2
            assert result.moved_count == 0
            assert len(result.failed_uids) == 0
            assert "Successfully copied 2 emails" in result.message

            mock_imap.login.assert_called_once()
            mock_imap.select.assert_called_once_with("INBOX")
            assert mock_imap.uid.call_count == 2
            mock_imap.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_emails_partial_failure(self, email_client):
        """Test copying emails with some failures."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.select = AsyncMock()
        # First UID succeeds, second fails
        mock_imap.uid = AsyncMock(side_effect=[
            (None, [b'OK']),
            (None, [b'NO'])
        ])
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            result = await email_client.copy_emails(["123", "456"], "Archive")

            assert isinstance(result, EmailOperationResult)
            assert result.success is False
            assert result.copied_count == 1
            assert result.failed_uids == ["456"]
            assert "1 failed" in result.message

    @pytest.mark.asyncio
    async def test_move_emails_with_move_command(self, email_client):
        """Test moving emails using MOVE command."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.select = AsyncMock()
        mock_imap.uid = AsyncMock(return_value=(None, [b'OK']))
        mock_imap.expunge = AsyncMock()
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            result = await email_client.move_emails(["123", "456"], "Archive")

            assert isinstance(result, EmailOperationResult)
            assert result.success is True
            assert result.moved_count == 2
            assert result.copied_count == 0
            assert len(result.failed_uids) == 0
            assert "Successfully moved 2 emails" in result.message

            # Should use MOVE command
            mock_imap.uid.assert_any_call('move', '123', 'Archive')
            mock_imap.uid.assert_any_call('move', '456', 'Archive')
            mock_imap.expunge.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_emails_fallback_to_copy_delete(self, email_client):
        """Test moving emails with fallback to COPY+DELETE."""
        # Mock IMAP client
        mock_imap = AsyncMock()
        mock_imap._client_task = asyncio.Future()
        mock_imap._client_task.set_result(None)
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock()
        mock_imap.select = AsyncMock()

        # MOVE command fails, so it falls back to COPY+STORE
        def uid_side_effect(command, uid, *args):
            if command == 'move':
                raise ValueError("MOVE not supported")
            elif command == 'copy' or command == 'store':
                return (None, [b'OK'])
            return (None, [b'OK'])

        mock_imap.uid = AsyncMock(side_effect=uid_side_effect)
        mock_imap.expunge = AsyncMock()
        mock_imap.logout = AsyncMock()

        with patch.object(email_client, "imap_class", return_value=mock_imap):
            with patch.object(email_client, "_move_single_email", return_value=True) as mock_move:
                result = await email_client.move_emails(["123"], "Archive")

                assert isinstance(result, EmailOperationResult)
                assert result.success is True
                assert result.moved_count == 1

                # Should call the helper method
                mock_move.assert_called_once_with(mock_imap, '123', 'Archive')
                mock_imap.expunge.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_single_email_with_move_command(self, email_client):
        """Test the _move_single_email helper method with MOVE command."""
        mock_imap = AsyncMock()
        mock_imap.uid = AsyncMock(return_value=(None, [b'OK']))

        result = await email_client._move_single_email(mock_imap, "123", "Archive")

        assert result is True
        mock_imap.uid.assert_called_once_with('move', '123', 'Archive')

    @pytest.mark.asyncio
    async def test_move_single_email_fallback_to_copy_delete(self, email_client):
        """Test the _move_single_email helper method with fallback."""
        mock_imap = AsyncMock()

        def uid_side_effect(command, uid, *args):
            if command == 'move':
                raise ValueError("MOVE not supported")
            elif command == 'copy' or command == 'store':
                return (None, [b'OK'])
            return (None, [b'OK'])

        mock_imap.uid = AsyncMock(side_effect=uid_side_effect)

        result = await email_client._move_single_email(mock_imap, "123", "Archive")

        assert result is True
        mock_imap.uid.assert_any_call('move', '123', 'Archive')
        mock_imap.uid.assert_any_call('copy', '123', 'Archive')
        mock_imap.uid.assert_any_call('store', '123', '+FLAGS.SILENT', '\\Deleted')


class TestClassicEmailHandlerOperations:
    @pytest.mark.asyncio
    async def test_list_folders(self, classic_handler):
        """Test list folders through handler."""
        expected_folders = [
            FolderInfo(name="INBOX", delimiter=".", flags=["HasNoChildren"]),
            FolderInfo(name="Sent", delimiter=".", flags=["HasNoChildren"]),
        ]

        with patch.object(classic_handler.incoming_client, "list_folders", return_value=expected_folders):
            folders = await classic_handler.list_folders()

            assert folders == expected_folders
            classic_handler.incoming_client.list_folders.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder(self, classic_handler):
        """Test create folder through handler."""
        with patch.object(classic_handler.incoming_client, "create_folder", return_value=True):
            result = await classic_handler.create_folder("Test Folder")

            assert result is True
            classic_handler.incoming_client.create_folder.assert_called_once_with("Test Folder")

    @pytest.mark.asyncio
    async def test_copy_emails(self, classic_handler):
        """Test copy emails through handler."""
        expected_result = EmailOperationResult(
            success=True,
            message="Successfully copied 2 emails",
            copied_count=2
        )

        with patch.object(classic_handler.incoming_client, "copy_emails", return_value=expected_result):
            result = await classic_handler.copy_emails(["123", "456"], "Archive")

            assert result == expected_result
            classic_handler.incoming_client.copy_emails.assert_called_once_with(["123", "456"], "Archive")

    @pytest.mark.asyncio
    async def test_move_emails(self, classic_handler):
        """Test move emails through handler."""
        expected_result = EmailOperationResult(
            success=True,
            message="Successfully moved 2 emails",
            moved_count=2
        )

        with patch.object(classic_handler.incoming_client, "move_emails", return_value=expected_result):
            result = await classic_handler.move_emails(["123", "456"], "Archive")

            assert result == expected_result
            classic_handler.incoming_client.move_emails.assert_called_once_with(["123", "456"], "Archive")


class TestEmailDataWithUID:
    def test_email_data_with_uid(self):
        """Test EmailData model with UID."""
        email_dict = {
            "subject": "Test Subject",
            "from": "sender@example.com",
            "body": "Test Body",
            "date": datetime.now(),
            "attachments": [],
            "uid": "12345"
        }

        email_data = EmailData.from_email(email_dict)

        assert email_data.subject == "Test Subject"
        assert email_data.sender == "sender@example.com"
        assert email_data.body == "Test Body"
        assert email_data.uid == "12345"

    def test_email_data_without_uid(self):
        """Test EmailData model without UID."""
        email_dict = {
            "subject": "Test Subject",
            "from": "sender@example.com",
            "body": "Test Body",
            "date": datetime.now(),
            "attachments": []
        }

        email_data = EmailData.from_email(email_dict)

        assert email_data.subject == "Test Subject"
        assert email_data.sender == "sender@example.com"
        assert email_data.body == "Test Body"
        assert email_data.uid is None
