"""Test MCP tools for email operations."""
from unittest.mock import AsyncMock, patch

import pytest

from mcp_email_server.app import copy_emails, create_folder, list_folders, move_emails
from mcp_email_server.emails.models import EmailOperationResult, FolderInfo


class TestMCPEmailOperations:
    @pytest.mark.asyncio
    async def test_list_folders_mcp_tool(self):
        """Test list_folders MCP tool."""
        expected_folders = [
            FolderInfo(name="INBOX", delimiter=".", flags=["HasNoChildren"]),
            FolderInfo(name="Sent", delimiter=".", flags=["HasNoChildren"]),
        ]

        with patch("mcp_email_server.app.dispatch_handler") as mock_dispatch:
            mock_handler = AsyncMock()
            mock_handler.list_folders.return_value = expected_folders
            mock_dispatch.return_value = mock_handler

            result = await list_folders("test_account")

            assert result == expected_folders
            mock_dispatch.assert_called_once_with("test_account")
            mock_handler.list_folders.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_folder_mcp_tool(self):
        """Test create_folder MCP tool."""
        with patch("mcp_email_server.app.dispatch_handler") as mock_dispatch:
            mock_handler = AsyncMock()
            mock_handler.create_folder.return_value = True
            mock_dispatch.return_value = mock_handler

            result = await create_folder("test_account", "New Folder")

            assert result is True
            mock_dispatch.assert_called_once_with("test_account")
            mock_handler.create_folder.assert_called_once_with("New Folder")

    @pytest.mark.asyncio
    async def test_copy_emails_mcp_tool(self):
        """Test copy_emails MCP tool."""
        expected_result = EmailOperationResult(
            success=True,
            message="Successfully copied 2 emails",
            copied_count=2
        )

        with patch("mcp_email_server.app.dispatch_handler") as mock_dispatch:
            mock_handler = AsyncMock()
            mock_handler.copy_emails.return_value = expected_result
            mock_dispatch.return_value = mock_handler

            result = await copy_emails("test_account", ["123", "456"], "Archive")

            assert result == expected_result
            mock_dispatch.assert_called_once_with("test_account")
            mock_handler.copy_emails.assert_called_once_with(["123", "456"], "Archive")

    @pytest.mark.asyncio
    async def test_move_emails_mcp_tool(self):
        """Test move_emails MCP tool."""
        expected_result = EmailOperationResult(
            success=True,
            message="Successfully moved 2 emails",
            moved_count=2
        )

        with patch("mcp_email_server.app.dispatch_handler") as mock_dispatch:
            mock_handler = AsyncMock()
            mock_handler.move_emails.return_value = expected_result
            mock_dispatch.return_value = mock_handler

            result = await move_emails("test_account", ["123", "456"], "Archive")

            assert result == expected_result
            mock_dispatch.assert_called_once_with("test_account")
            mock_handler.move_emails.assert_called_once_with(["123", "456"], "Archive")
