"""Tests for the DataMap API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from datamap_cli.api import DataMapAPIClient
from datamap_cli.api.exceptions import (
    AuthenticationError,
    ConfigurationError,
    NotFoundError,
)
from datamap_cli.api.models import Dataset, Version, DataFileDownloadResponse


class TestDataMapAPIClient:
    """Test cases for DataMapAPIClient."""
    
    def test_init_with_valid_credentials(self):
        """Test client initialization with valid credentials."""
        client = DataMapAPIClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://test.api.com",
        )
        
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.base_url == "https://test.api.com"
        assert client.timeout == 30.0
        assert client.max_retries == 3
    
    def test_init_without_credentials(self):
        """Test client initialization without credentials raises error."""
        with pytest.raises(ConfigurationError, match="API key and secret are required"):
            DataMapAPIClient(api_key="", api_secret="")
        
        with pytest.raises(ConfigurationError, match="API key and secret are required"):
            DataMapAPIClient(api_key=None, api_secret="test-secret")
    
    def test_get_default_headers(self):
        """Test default headers generation."""
        client = DataMapAPIClient(
            api_key="test-key",
            api_secret="test-secret",
            user_id="user-123",
            tenancy="test-tenancy",
        )
        
        headers = client._get_default_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["X-Api-Key"] == "test-key"
        assert headers["X-Api-Secret"] == "test-secret"
        assert headers["X-User-Id"] == "user-123"
        assert headers["X-Datamap-Tenancies"] == "test-tenancy"
    
    def test_build_url(self):
        """Test URL building functionality."""
        client = DataMapAPIClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://test.api.com",
        )
        
        # Test with leading slash
        url = client._build_url("/datasets/123")
        assert url == "https://test.api.com/datasets/123"
        
        # Test without leading slash
        url = client._build_url("datasets/123")
        assert url == "https://test.api.com/datasets/123"
        
        # Test with trailing slash in base_url
        client.base_url = "https://test.api.com/"
        url = client._build_url("datasets/123")
        assert url == "https://test.api.com/datasets/123"
    
    @pytest.mark.asyncio
    async def test_get_dataset_success(self):
        """Test successful dataset retrieval."""
        mock_dataset_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Dataset",
            "data": {"description": "Test dataset"},
            "tenancy": "test",
            "is_enabled": True,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "design_state": "active",
            "versions": [],
            "current_version": None,
        }
        
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            mock_request.return_value = Dataset(**mock_dataset_data)
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            dataset = await client.get_dataset("123e4567-e89b-12d3-a456-426614174000")
            
            assert isinstance(dataset, Dataset)
            assert dataset.id == "123e4567-e89b-12d3-a456-426614174000"
            assert dataset.name == "Test Dataset"
            
            mock_request.assert_called_once_with(
                method="GET",
                endpoint="/datasets/123e4567-e89b-12d3-a456-426614174000",
                model_class=Dataset,
            )
    
    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self):
        """Test dataset retrieval when dataset is not found."""
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            mock_request.side_effect = NotFoundError("Resource", "unknown")
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            with pytest.raises(NotFoundError, match="Dataset with ID 'test-id' not found"):
                await client.get_dataset("test-id")
    
    @pytest.mark.asyncio
    async def test_get_version_success(self):
        """Test successful version retrieval."""
        mock_version_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "v1.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            # Mock the response to include the version key as expected by the API
            mock_request.return_value = {"version": mock_version_data}
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            version = await client.get_version("dataset-id", "v1.0")
            
            assert isinstance(version, Version)
            assert version.id == "123e4567-e89b-12d3-a456-426614174000"
            assert version.name == "v1.0"
            
            mock_request.assert_called_once_with(
                method="GET",
                endpoint="/datasets/dataset-id/versions/v1.0",
            )
    
    @pytest.mark.asyncio
    async def test_get_file_download_url_success(self):
        """Test successful file download URL retrieval."""
        mock_download_data = {
            "url": "https://example.com/download/file.zip",
        }
        
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            mock_request.return_value = DataFileDownloadResponse(**mock_download_data)
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            download_response = await client.get_file_download_url(
                "dataset-id", "v1.0", "file-id"
            )
            
            assert isinstance(download_response, DataFileDownloadResponse)
            assert download_response.url == "https://example.com/download/file.zip"
            
            mock_request.assert_called_once_with(
                method="GET",
                endpoint="/datasets/dataset-id/versions/v1.0/files/file-id",
                model_class=DataFileDownloadResponse,
            )
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            mock_request.return_value = {"status": "healthy"}
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            result = await client.health_check()
            
            assert result is True
            mock_request.assert_called_once_with(
                method="GET",
                endpoint="/health",
            )
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        with patch.object(DataMapAPIClient, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            
            client = DataMapAPIClient(
                api_key="test-key",
                api_secret="test-secret",
            )
            
            result = await client.health_check()
            
            assert result is False 