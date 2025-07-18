"""Pydantic models for DataMap API responses."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DataFile(BaseModel):
    """Model representing a data file in a dataset version."""
    
    id: str = Field(..., description="File UUID")
    name: str = Field(..., description="File name")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="File creation timestamp")
    updated_at: datetime = Field(..., description="File last update timestamp")
    extension: Optional[str] = Field(None, description="File extension")
    format: Optional[str] = Field(None, description="File format")
    storage_file_name: Optional[str] = Field(None, description="Storage file name")
    storage_path: Optional[str] = Field(None, description="Storage path")
    created_by: Optional[str] = Field(None, description="Creator UUID")

    @field_validator('id')
    @classmethod
    def validate_uuid(cls, v):
        """Validate that the ID is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError('Invalid UUID format')
        return v

    @property
    def formatted_size(self) -> str:
        """Return human-readable file size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size_bytes < 1024.0:
                return f"{self.size_bytes:.1f} {unit}"
            self.size_bytes /= 1024.0
        return f"{self.size_bytes:.1f} PB"


class Version(BaseModel):
    """Model representing a dataset version."""
    
    id: str = Field(..., description="Version UUID")
    name: str = Field(..., description="Version name (string, not UUID)")
    design_state: str = Field(..., description="Version design state")
    is_enabled: bool = Field(..., description="Whether the version is enabled")
    files: List[DataFile] = Field(default_factory=list, description="List of files in this version")
    created_at: datetime = Field(..., description="Version creation timestamp")
    updated_at: datetime = Field(..., description="Version last update timestamp")

    @field_validator('id')
    @classmethod
    def validate_uuid(cls, v):
        """Validate that the ID is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError('Invalid UUID format')
        return v

    @property
    def total_size(self) -> int:
        """Return total size of all files in this version."""
        return sum(file.size_bytes for file in self.files)

    @property
    def file_count(self) -> int:
        """Return number of files in this version."""
        return len(self.files)


class Dataset(BaseModel):
    """Model representing a dataset."""
    
    id: str = Field(..., description="Dataset UUID")
    name: str = Field(..., description="Dataset name")
    data: Dict = Field(..., description="Dataset information in JSON format")
    tenancy: str = Field(..., description="Dataset tenancy")
    is_enabled: bool = Field(..., description="Whether the dataset is enabled")
    created_at: datetime = Field(..., description="Dataset creation timestamp")
    updated_at: datetime = Field(..., description="Dataset last update timestamp")
    design_state: str = Field(..., description="Dataset design state")
    versions: List[Version] = Field(default_factory=list, description="List of dataset versions")
    current_version: Optional[Version] = Field(None, description="Current version of the dataset")

    @field_validator('id')
    @classmethod
    def validate_uuid(cls, v):
        """Validate that the ID is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        if not uuid_pattern.match(v):
            raise ValueError('Invalid UUID format')
        return v

    def get_version_by_name(self, version_name: str) -> Optional[Version]:
        """Get a specific version by name."""
        for version in self.versions:
            if version.name == version_name:
                return version
        return None

    @property
    def version_count(self) -> int:
        """Return number of versions in this dataset."""
        return len(self.versions)

    @property
    def total_files(self) -> int:
        """Return total number of files across all versions."""
        return sum(version.file_count for version in self.versions)


class DataFileDownloadResponse(BaseModel):
    """Model representing a file download response."""
    
    url: str = Field(..., description="Download URL for the file")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate that the URL is properly formatted."""
        import re
        url_pattern = re.compile(
            r'^(http://|https://).*$',
            re.IGNORECASE
        )
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v


class APIResponse(BaseModel):
    """Generic API response wrapper."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Dict] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")


class PaginatedResponse(BaseModel):
    """Model for paginated API responses."""
    
    data: List[Dict] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
