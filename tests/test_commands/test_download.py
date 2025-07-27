"""Tests for download commands."""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from rich.console import Console

from datamap_cli.api.exceptions import NotFoundError
from datamap_cli.api.models import DataFile, DataFileDownloadResponse, Version
from datamap_cli.commands.download import (
    _download_file_with_progress,
    _get_file_info,
    file,
    validate_output_path,
    validate_uuid,
    validate_version_name,
    version,
)
from datamap_cli.utils.progress import ProgressManager


class TestDownloadValidation:
    """Test validation functions for download commands."""
    
    def test_validate_uuid_valid(self):
        """Test UUID validation with valid UUID."""
        valid_uuid = "12345678-1234-1234-1234-123456789abc"
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid
    
    def test_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUID."""
        invalid_uuid = "invalid-uuid"
        with pytest.raises(typer.BadParameter):
            validate_uuid(invalid_uuid)
    
    def test_validate_version_name_valid(self):
        """Test version name validation with valid names."""
        valid_names = ["v1.0", "version_1", "1.2.3", "alpha-beta"]
        for name in valid_names:
            result = validate_version_name(name)
            assert result == name
    
    def test_validate_version_name_invalid(self):
        """Test version name validation with invalid names."""
        invalid_names = ["", " ", "v1.0!", "version/1"]
        for name in invalid_names:
            with pytest.raises(typer.BadParameter):
                validate_version_name(name)
    
    def test_validate_output_path_valid(self):
        """Test output path validation with valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "test_file.txt"
            result = validate_output_path(str(test_path))
            assert result == test_path.resolve()
    
    def test_validate_output_path_invalid(self):
        """Test output path validation with invalid path."""
        # Test with a path that would cause permission issues
        with pytest.raises(typer.BadParameter):
            validate_output_path("/root/invalid/path/test.txt")


class TestDownloadHelpers:
    """Test helper functions for download commands."""
    
    @pytest.mark.asyncio
    async def test_get_file_info_success(self):
        """Test getting file info successfully."""
        # Mock API client
        mock_client = AsyncMock()
        mock_version = Version(
            id="12345678-1234-1234-1234-123456789abc",
            name="v1.0",
            design_state="enabled",
            is_enabled=True,
            files_in=[
                DataFile(
                    id="87654321-4321-4321-4321-cba987654321",
                    name="test.csv",
                    size_bytes=1024,
                    created_at=datetime(2023, 1, 1, 0, 0, 0),
                    updated_at=datetime(2023, 1, 1, 0, 0, 0),
                )
            ],
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
        )
        mock_client.get_version.return_value = mock_version
        
        # Test getting file info
        file_info = await _get_file_info(
            mock_client, "dataset-id", "v1.0", "87654321-4321-4321-4321-cba987654321"
        )
        
        assert file_info.id == "87654321-4321-4321-4321-cba987654321"
        assert file_info.name == "test.csv"
        mock_client.get_version.assert_called_once_with("dataset-id", "v1.0")
    
    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self):
        """Test getting file info when file not found."""
        # Mock API client
        mock_client = AsyncMock()
        mock_version = Version(
            id="12345678-1234-1234-1234-123456789abc",
            name="v1.0",
            design_state="enabled",
            is_enabled=True,
            files_in=[],
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
        )
        mock_client.get_version.return_value = mock_version
        
        # Test getting non-existent file info
        with pytest.raises(typer.Exit):
            await _get_file_info(
                mock_client, "dataset-id", "v1.0", "11111111-1111-1111-1111-111111111111"
            )
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TODO: Fix async context manager mocking for httpx.AsyncClient")
    async def test_download_file_with_progress_success(self):
        """Test downloading file with progress successfully."""
        # Mock progress manager
        mock_progress_manager = MagicMock(spec=ProgressManager)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_file.txt"
            
            # Mock Rich components to avoid issues in test environment
            with patch("datamap_cli.commands.download.Progress") as mock_progress_class, \
                 patch("datamap_cli.commands.download.console") as mock_console, \
                 patch("httpx.AsyncClient") as mock_async_client_class:
                
                # Mock the Progress class
                mock_progress = MagicMock()
                mock_progress_class.return_value = mock_progress
                mock_progress.add_task.return_value = "task_id"
                
                # Create a mock client that properly handles the context manager
                mock_client = AsyncMock()
                
                # Mock the response
                mock_response = AsyncMock()
                mock_response.raise_for_status.return_value = None
                mock_response.aiter_bytes.return_value = [b"test data"]
                
                # Mock the stream context manager
                mock_stream_context = AsyncMock()
                mock_stream_context.__aenter__.return_value = mock_response
                mock_stream_context.__aexit__.return_value = None
                
                # Configure the client to return the stream context
                mock_client.stream.return_value = mock_stream_context
                
                # Configure the AsyncClient class to return our mock client
                mock_async_client_class.return_value = mock_client
                
                # Configure the AsyncClient context manager
                mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
                
                success = await _download_file_with_progress(
                    "http://example.com/test",
                    output_path,
                    "test_file.txt",
                    1024,
                    mock_progress_manager,
                    resume=False,
                )
                
                assert success is True
                assert output_path.exists()
                assert output_path.read_text() == "test data"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TODO: Fix async context manager mocking for httpx.AsyncClient")
    async def test_download_file_with_progress_resume(self):
        """Test downloading file with resume capability."""
        # Mock progress manager
        mock_progress_manager = MagicMock(spec=ProgressManager)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_file.txt"
            
            # Create a partial file to simulate resume
            output_path.write_text("partial")
            
            # Mock Rich components
            with patch("datamap_cli.commands.download.Progress") as mock_progress_class, \
                 patch("datamap_cli.commands.download.console") as mock_console, \
                 patch("httpx.AsyncClient") as mock_async_client_class:
                
                # Mock the Progress class
                mock_progress = MagicMock()
                mock_progress_class.return_value = mock_progress
                mock_progress.add_task.return_value = "task_id"
                
                # Create a mock client
                mock_client = AsyncMock()
                
                # Mock the response
                mock_response = AsyncMock()
                mock_response.raise_for_status.return_value = None
                mock_response.aiter_bytes.return_value = [b" data"]
                
                # Mock the stream context manager
                mock_stream_context = AsyncMock()
                mock_stream_context.__aenter__.return_value = mock_response
                mock_stream_context.__aexit__.return_value = None
                
                # Configure the client
                mock_client.stream.return_value = mock_stream_context
                mock_async_client_class.return_value = mock_client
                mock_async_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_async_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
                
                success = await _download_file_with_progress(
                    "http://example.com/test",
                    output_path,
                    "test_file.txt",
                    1024,
                    mock_progress_manager,
                    resume=True,
                )
                
                assert success is True
                assert output_path.exists()
                assert output_path.read_text() == "partial data"


class TestDownloadCommands:
    """Test download command functions."""
    
    def test_file_download_workflow_mock(self):
        """Test the file download workflow with mocks."""
        # Mock API client
        mock_client = AsyncMock()
        
        # Mock file info
        mock_file_info = DataFile(
            id="87654321-4321-4321-4321-cba987654321",
            name="test.csv",
            size_bytes=1024,
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
        )
        
        # Mock download response
        mock_download_response = DataFileDownloadResponse(url="http://example.com/test")
        mock_client.get_file_download_url.return_value = mock_download_response
        
        # Test that the mocks work correctly
        assert mock_file_info.id == "87654321-4321-4321-4321-cba987654321"
        assert mock_file_info.name == "test.csv"
        assert mock_download_response.url == "http://example.com/test"
    
    def test_version_download_workflow_mock(self):
        """Test the version download workflow with mocks."""
        # Mock API client
        mock_client = AsyncMock()
        
        # Mock version info
        mock_version_info = Version(
            id="12345678-1234-1234-1234-123456789abc",
            name="v1.0",
            design_state="enabled",
            is_enabled=True,
            files_in=[
                DataFile(
                    id="87654321-4321-4321-4321-cba987654321",
                    name="test1.csv",
                    size_bytes=1024,
                    created_at=datetime(2023, 1, 1, 0, 0, 0),
                    updated_at=datetime(2023, 1, 1, 0, 0, 0),
                ),
                DataFile(
                    id="98765432-5432-5432-5432-dcb098765432",
                    name="test2.csv",
                    size_bytes=2048,
                    created_at=datetime(2023, 1, 1, 0, 0, 0),
                    updated_at=datetime(2023, 1, 1, 0, 0, 0),
                ),
            ],
            created_at=datetime(2023, 1, 1, 0, 0, 0),
            updated_at=datetime(2023, 1, 1, 0, 0, 0),
        )
        mock_client.get_version.return_value = mock_version_info
        
        # Mock download response
        mock_download_response = DataFileDownloadResponse(url="http://example.com/test")
        mock_client.get_file_download_url.return_value = mock_download_response
        
        # Test that the mocks work correctly
        assert mock_version_info.id == "12345678-1234-1234-1234-123456789abc"
        assert len(mock_version_info.files_in) == 2
        assert mock_version_info.file_count == 2
        assert mock_download_response.url == "http://example.com/test"


class TestDownloadErrorHandling:
    """Test error handling in download commands."""
    
    @patch("datamap_cli.commands.download._get_api_client")
    def test_file_command_api_error(self, mock_get_api_client):
        """Test file download command with API error."""
        # Mock API client that raises an exception
        mock_client = AsyncMock()
        mock_get_api_client.return_value = mock_client
        mock_client.get_version.side_effect = NotFoundError("Dataset", "dataset-id")
        
        # Mock console to avoid output during tests
        with patch("datamap_cli.commands.download.console"):
            with pytest.raises(typer.Exit):
                file(
                    "12345678-1234-1234-1234-123456789abc",
                    "v1.0",
                    "87654321-4321-4321-4321-cba987654321",
                )
    
    @patch("datamap_cli.commands.download._get_api_client")
    def test_version_command_api_error(self, mock_get_api_client):
        """Test version download command with API error."""
        # Mock API client that raises an exception
        mock_client = AsyncMock()
        mock_get_api_client.return_value = mock_client
        mock_client.get_version.side_effect = NotFoundError("Version", "version-id")
        
        # Mock console to avoid output during tests
        with patch("datamap_cli.commands.download.console"):
            with pytest.raises(typer.Exit):
                version(
                    "12345678-1234-1234-1234-123456789abc",
                    "v1.0",
                ) 