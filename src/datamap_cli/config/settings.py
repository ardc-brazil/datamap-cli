"""Configuration settings for DataMap CLI."""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_key: str = Field(..., env="DATAMAP_API_KEY", description="DataMap API key")
    api_secret: str = Field(..., env="DATAMAP_API_SECRET", description="DataMap API secret")
    api_base_url: str = Field(
        default="https://datamap.pcs.usp.br/api/v1",
        env="DATAMAP_API_BASE_URL",
        description="DataMap API base URL"
    )
    timeout: int = Field(
        default=30,
        env="DATAMAP_TIMEOUT",
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        env="DATAMAP_RETRY_ATTEMPTS",
        ge=0,
        le=10,
        description="Number of retry attempts for failed requests"
    )
    
    # Optional API Configuration
    user_id: Optional[str] = Field(None, env="DATAMAP_USER_ID", description="User ID")
    tenancies: Optional[str] = Field(None, env="DATAMAP_TENANCIES", description="Tenancy information")
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="DATAMAP_LOG_LEVEL",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        env="DATAMAP_LOG_FORMAT",
        pattern="^(json|text)$",
        description="Log format (json or text)"
    )
    
    # Output Configuration
    output_format: str = Field(
        default="table",
        env="DATAMAP_OUTPUT_FORMAT",
        pattern="^(table|json|yaml|csv)$",
        description="Output format"
    )
    color_output: bool = Field(
        default=True,
        env="DATAMAP_COLOR_OUTPUT",
        description="Enable colored output"
    )
    
    # Download Configuration
    download_concurrency: int = Field(
        default=3,
        env="DATAMAP_DOWNLOAD_CONCURRENCY",
        ge=1,
        le=10,
        description="Number of concurrent downloads"
    )
    chunk_size: int = Field(
        default=8192,
        env="DATAMAP_CHUNK_SIZE",
        ge=1024,
        le=1048576,
        description="Download chunk size in bytes"
    )
    
    @field_validator("api_key", "api_secret")
    @classmethod
    def validate_api_credentials(cls, v: str) -> str:
        """Validate API credentials are not empty."""
        if not v or v.strip() == "":
            raise ValueError("API credentials cannot be empty")
        return v.strip()
    
    @field_validator("api_base_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate API base URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("API base URL must start with http:// or https://")
        return v.rstrip("/")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance (lazy loading)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global _settings
    _settings = Settings()
    return _settings
