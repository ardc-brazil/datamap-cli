"""Tests for the DataMap API models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from datamap_cli.api.models import (
    DataFile,
    Version,
    Dataset,
    DataFileDownloadResponse,
)


class TestDataFile:
    """Test cases for DataFile model."""
    
    def test_valid_data_file(self):
        """Test creating a valid DataFile."""
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "test.csv",
            "size_bytes": 1024,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "extension": ".csv",
            "format": "CSV",
            "storage_file_name": "test_file.csv",
            "storage_path": "/path/to/file",
            "created_by": "user-123",
        }
        
        data_file = DataFile(**data)
        
        assert data_file.id == "123e4567-e89b-12d3-a456-426614174000"
        assert data_file.name == "test.csv"
        assert data_file.size_bytes == 1024
        assert data_file.extension == ".csv"
        assert data_file.format == "CSV"
        assert data_file.storage_file_name == "test_file.csv"
        assert data_file.storage_path == "/path/to/file"
        assert data_file.created_by == "user-123"
    
    def test_invalid_uuid(self):
        """Test that invalid UUID raises validation error."""
        data = {
            "id": "invalid-uuid",
            "name": "test.csv",
            "size_bytes": 1024,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        with pytest.raises(ValidationError, match="Invalid UUID format"):
            DataFile(**data)
    
    def test_formatted_size_property(self):
        """Test the formatted_size property."""
        # Test bytes
        data_file = DataFile(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="test.csv",
            size_bytes=512,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )
        assert data_file.formatted_size == "512.0 B"
        
        # Test KB
        data_file.size_bytes = 1536
        assert data_file.formatted_size == "1.5 KB"
        
        # Test MB
        data_file.size_bytes = 1572864  # 1.5 MB
        assert data_file.formatted_size == "1.5 MB"


class TestVersion:
    """Test cases for Version model."""
    
    def test_valid_version(self):
        """Test creating a valid Version."""
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "v1.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        version = Version(**data)
        
        assert version.id == "123e4567-e89b-12d3-a456-426614174000"
        assert version.name == "v1.0"
        assert version.design_state == "active"
        assert version.is_enabled is True
        assert version.files == []
    
    def test_version_with_files(self):
        """Test Version with files."""
        file_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "test.csv",
            "size_bytes": 1024,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "v1.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [file_data],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        version = Version(**data)
        
        assert len(version.files) == 1
        assert version.files[0].name == "test.csv"
        assert version.file_count == 1
        assert version.total_size == 1024


class TestDataset:
    """Test cases for Dataset model."""
    
    def test_valid_dataset(self):
        """Test creating a valid Dataset."""
        data = {
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
        
        dataset = Dataset(**data)
        
        assert dataset.id == "123e4567-e89b-12d3-a456-426614174000"
        assert dataset.name == "Test Dataset"
        assert dataset.data == {"description": "Test dataset"}
        assert dataset.tenancy == "test"
        assert dataset.is_enabled is True
        assert dataset.design_state == "active"
        assert dataset.versions == []
        assert dataset.current_version is None
    
    def test_dataset_with_versions(self):
        """Test Dataset with versions."""
        version_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "v1.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Dataset",
            "data": {"description": "Test dataset"},
            "tenancy": "test",
            "is_enabled": True,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "design_state": "active",
            "versions": [version_data],
            "current_version": version_data,
        }
        
        dataset = Dataset(**data)
        
        assert len(dataset.versions) == 1
        assert dataset.version_count == 1
        assert dataset.total_files == 0
        assert dataset.current_version is not None
        assert dataset.current_version.name == "v1.0"
    
    def test_get_version_by_name(self):
        """Test get_version_by_name method."""
        version1_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "v1.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        version2_data = {
            "id": "456e7890-e89b-12d3-a456-426614174000",
            "name": "v2.0",
            "design_state": "active",
            "is_enabled": True,
            "files": [],
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }
        
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test Dataset",
            "data": {"description": "Test dataset"},
            "tenancy": "test",
            "is_enabled": True,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "design_state": "active",
            "versions": [version1_data, version2_data],
            "current_version": None,
        }
        
        dataset = Dataset(**data)
        
        # Test finding existing version
        version = dataset.get_version_by_name("v1.0")
        assert version is not None
        assert version.name == "v1.0"
        
        # Test finding non-existing version
        version = dataset.get_version_by_name("v3.0")
        assert version is None


class TestDataFileDownloadResponse:
    """Test cases for DataFileDownloadResponse model."""
    
    def test_valid_download_response(self):
        """Test creating a valid DataFileDownloadResponse."""
        data = {
            "url": "https://example.com/download/file.zip",
        }
        
        response = DataFileDownloadResponse(**data)
        
        assert response.url == "https://example.com/download/file.zip"
    
    def test_invalid_url(self):
        """Test that invalid URL raises validation error."""
        data = {
            "url": "not-a-url",
        }
        
        with pytest.raises(ValidationError, match="Invalid URL format"):
            DataFileDownloadResponse(**data)
    
    def test_http_url(self):
        """Test HTTP URL is accepted."""
        data = {
            "url": "http://example.com/download/file.zip",
        }
        
        response = DataFileDownloadResponse(**data)
        assert response.url == "http://example.com/download/file.zip" 