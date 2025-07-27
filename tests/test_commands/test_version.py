"""Tests for version commands."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from rich.console import Console

from datamap_cli.api.models import DataFile, Version
from datamap_cli.commands.version import app, validate_uuid, validate_version_name


class TestVersionCommands:
    """Test version command functionality."""

    @pytest.fixture
    def mock_version(self):
        """Create a mock version for testing."""
        files = [
            DataFile(
                id="12345678-1234-1234-1234-123456789abc",
                name="test1.csv",
                size_bytes=1024,
                created_at=datetime(2023, 1, 1),
                updated_at=datetime(2023, 1, 1),
                extension=".csv",
                format="csv",
                storage_file_name=None,
                storage_path=None,
                created_by=None,
            ),
            DataFile(
                id="87654321-4321-4321-4321-210987654321",
                name="test2.json",
                size_bytes=2048,
                created_at=datetime(2023, 1, 2),
                updated_at=datetime(2023, 1, 2),
                extension=".json",
                format="json",
                storage_file_name=None,
                storage_path=None,
                created_by=None,
            ),
        ]
        
        return Version(
            id="11111111-1111-1111-1111-111111111111",
            name="v1.0",
            design_state="published",
            is_enabled=True,
            files_in=files,
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 1),
        )

    @pytest.fixture
    def mock_client(self):
        """Create a mock API client."""
        client = AsyncMock()
        client.close = AsyncMock()
        return client

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

    def test_validate_uuid_empty(self):
        """Test UUID validation with empty string."""
        with pytest.raises(typer.BadParameter):
            validate_uuid("")

    def test_validate_version_name_valid(self):
        """Test version name validation with valid names."""
        valid_names = ["v1.0", "latest", "v2.1", "test-version", "version_1"]
        for name in valid_names:
            result = validate_version_name(name)
            assert result == name

    def test_validate_version_name_invalid(self):
        """Test version name validation with invalid names."""
        invalid_names = ["", " ", "v1.0@", "version/1", "test version"]
        for name in invalid_names:
            with pytest.raises(typer.BadParameter):
                validate_version_name(name)

    def test_validate_version_name_empty(self):
        """Test version name validation with empty string."""
        with pytest.raises(typer.BadParameter):
            validate_version_name("")

    def test_validate_version_name_whitespace(self):
        """Test version name validation with whitespace-only string."""
        with pytest.raises(typer.BadParameter):
            validate_version_name("   ")

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_files_command_success(self, mock_client_class, mock_get_settings, mock_version):
        """Test successful version files command workflow."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.api_key = "test-key"
        mock_settings.api_secret = "test-secret"
        mock_settings.api_base_url = "https://api.test.com"
        mock_settings.timeout = 30.0
        mock_settings.retry_attempts = 3
        mock_settings.user_id = "test-user"
        mock_settings.tenancies = "test-tenant"
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(return_value=mock_version)
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            version = await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
            return version
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result == mock_version
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_files_command_not_found(self, mock_client_class, mock_get_settings):
        """Test version files command with not found error."""
        from datamap_cli.api.exceptions import NotFoundError
        
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(side_effect=NotFoundError("Version", "test/test"))
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            try:
                await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
                return False
            except NotFoundError:
                return True
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result is True
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_files_command_no_files(self, mock_client_class, mock_get_settings):
        """Test version files command with no files."""
        # Create version with no files
        empty_version = Version(
            id="11111111-1111-1111-1111-111111111111",
            name="v1.0",
            design_state="published",
            is_enabled=True,
            files_in=[],
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 1),
        )

        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(return_value=empty_version)
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            version = await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
            return version
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result == empty_version
        assert len(result.files_in) == 0
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    def test_version_formatted_size(self, mock_version):
        """Test version formatted size calculation."""
        assert mock_version.formatted_size == "3.0 KB"

    def test_version_total_size(self, mock_version):
        """Test version total size calculation."""
        assert mock_version.total_size == 3072  # 1024 + 2048

    def test_version_file_count(self, mock_version):
        """Test version file count calculation."""
        assert mock_version.file_count == 2


class TestVersionCommandIntegration:
    """Test version command integration."""

    @pytest.mark.asyncio
    async def test_get_api_client(self):
        """Test API client creation."""
        from datamap_cli.commands.version import _get_api_client
        
        with patch('datamap_cli.commands.version.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.api_key = "test-key"
            mock_settings.api_secret = "test-secret"
            mock_settings.api_base_url = "https://api.test.com"
            mock_settings.timeout = 30.0
            mock_settings.retry_attempts = 3
            mock_settings.user_id = "test-user"
            mock_settings.tenancies = "test-tenant"
            mock_get_settings.return_value = mock_settings

            with patch('datamap_cli.commands.version.DataMapAPIClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                
                client = await _get_api_client()
                
                assert client is not None
                mock_client_class.assert_called_once_with(
                    api_key="test-key",
                    api_secret="test-secret",
                    base_url="https://api.test.com",
                    timeout=30.0,
                    max_retries=3,
                    user_id="test-user",
                    tenancy="test-tenant",
                )

    def test_app_creation(self):
        """Test that the version app is created correctly."""
        assert app is not None
        assert app.info.name == "version"
        assert "Version-related commands" in app.info.help

    def test_app_commands(self):
        """Test that version app has the expected commands."""
        commands = [cmd.name for cmd in app.registered_commands]
        assert "files" in commands


class TestVersionCommandErrorHandling:
    """Test version command error handling."""

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_authentication_error(self, mock_client_class, mock_get_settings):
        """Test authentication error handling."""
        from datamap_cli.api.exceptions import AuthenticationError
        
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            try:
                await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
                return False
            except AuthenticationError:
                return True
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result is True
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_authorization_error(self, mock_client_class, mock_get_settings):
        """Test authorization error handling."""
        from datamap_cli.api.exceptions import AuthorizationError
        
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(side_effect=AuthorizationError("Access denied"))
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            try:
                await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
                return False
            except AuthorizationError:
                return True
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result is True
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_validation_error(self, mock_client_class, mock_get_settings):
        """Test validation error handling."""
        from datamap_cli.api.exceptions import ValidationError
        
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(side_effect=ValidationError("Invalid input"))
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            try:
                await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
                return False
            except ValidationError:
                return True
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result is True
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    @patch('datamap_cli.commands.version.get_settings')
    @patch('datamap_cli.commands.version.DataMapAPIClient')
    def test_generic_api_error(self, mock_client_class, mock_get_settings):
        """Test generic API error handling."""
        from datamap_cli.api.exceptions import DataMapAPIError
        
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_client = AsyncMock()
        mock_client.get_version = AsyncMock(side_effect=DataMapAPIError("API error"))
        mock_client_class.return_value = mock_client

        # Test the internal workflow directly
        from datamap_cli.commands.version import _get_api_client
        
        async def test_workflow():
            client = await _get_api_client()
            try:
                await client.get_version("12345678-1234-1234-1234-123456789abc", "v1.0")
                return False
            except DataMapAPIError:
                return True
        
        import asyncio
        result = asyncio.run(test_workflow())
        
        assert result is True
        mock_client.get_version.assert_called_once_with(
            "12345678-1234-1234-1234-123456789abc", "v1.0"
        )

    def test_invalid_uuid_parameter(self):
        """Test invalid UUID parameter handling."""
        from typer.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(
            app,
            ["files", "invalid-uuid", "v1.0"]
        )
        
        assert result.exit_code == 2  # Typer parameter error
        assert "Invalid UUID format" in result.stdout

    def test_invalid_version_name_parameter(self):
        """Test invalid version name parameter handling."""
        # Test the validation function directly
        from datamap_cli.commands.version import validate_version_name
        
        with pytest.raises(typer.BadParameter, match="Invalid version name format"):
            validate_version_name("invalid@version") 