"""Configuration settings for DataMap CLI."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import yaml
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable and configuration file support."""
    
    # API Configuration
    api_key: str = Field(..., description="DataMap API key")
    api_secret: str = Field(..., description="DataMap API secret")
    api_base_url: str = Field(
        default="https://datamap.pcs.usp.br/api/v1",
        description="DataMap API base URL"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts for failed requests"
    )
    
    # Optional API Configuration
    user_id: Optional[str] = Field(None, description="User ID")
    tenancies: Optional[str] = Field(None, description="Tenancy information")
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        pattern="^(json|text)$",
        description="Log format (json or text)"
    )
    
    # Output Configuration
    output_format: str = Field(
        default="table",
        pattern="^(table|json|yaml|csv)$",
        description="Output format"
    )
    color_output: bool = Field(
        default=True,
        description="Enable colored output"
    )
    
    # Download Configuration
    download_concurrency: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of concurrent downloads"
    )
    chunk_size: int = Field(
        default=8192,
        ge=1024,
        le=1048576,
        description="Download chunk size in bytes"
    )
    
    # Configuration file paths
    config_file: Optional[str] = Field(None, description="Path to configuration file")
    
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
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate user ID format if provided."""
        if v is not None and v.strip() == "":
            return None
        return v.strip() if v else None
    
    @field_validator("tenancies")
    @classmethod
    def validate_tenancies(cls, v: Optional[str]) -> Optional[str]:
        """Validate tenancies format if provided."""
        if v is not None and v.strip() == "":
            return None
        return v.strip() if v else None
    
    @model_validator(mode='after')
    def validate_configuration(self) -> 'Settings':
        """Validate overall configuration."""
        # Check if API credentials are provided
        if not self.api_key or not self.api_secret:
            raise ValueError("Both API key and secret are required")
        
        # Validate URL is accessible (basic check)
        try:
            parsed = urlparse(self.api_base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid API base URL format")
        except Exception as e:
            raise ValueError(f"Invalid API base URL: {e}")
        
        return self
    
    def get_credential_summary(self) -> Dict[str, str]:
        """Get a summary of credentials (for debugging, without exposing secrets)."""
        return {
            "api_key": f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***",
            "api_secret": f"{self.api_secret[:8]}..." if len(self.api_secret) > 8 else "***",
            "api_base_url": self.api_base_url,
            "user_id": self.user_id or "Not set",
            "tenancies": self.tenancies or "Not set"
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)."""
        data = self.model_dump()
        # Mask sensitive data
        data["api_key"] = "***"
        data["api_secret"] = "***"
        return data
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        env_prefix="DATAMAP_"
    )


class ConfigurationManager:
    """Manages configuration loading and validation."""
    
    def __init__(self):
        self.config_paths = self._get_config_paths()
        self._settings: Optional[Settings] = None
    
    def _get_config_paths(self) -> List[Path]:
        """Get list of configuration file paths in order of precedence."""
        paths = []
        
        # 1. Command line specified config file
        if len(sys.argv) > 1:
            for i, arg in enumerate(sys.argv):
                if arg in ["--config", "-c"] and i + 1 < len(sys.argv):
                    paths.append(Path(sys.argv[i + 1]))
        
        # 2. Current directory
        paths.extend([
            Path(".datamap.yaml"),
            Path(".datamap.yml"),
            Path(".datamap.ini"),
            Path("datamap.yaml"),
            Path("datamap.yml"),
            Path("datamap.ini"),
        ])
        
        # 3. User home directory
        home = Path.home()
        paths.extend([
            home / ".datamap" / "config.yaml",
            home / ".datamap" / "config.yml",
            home / ".datamap" / "config.ini",
            home / ".datamaprc",
        ])
        
        # 4. System-wide configuration
        if sys.platform == "win32":
            system_config = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "datamap"
        else:
            system_config = Path("/etc/datamap")
        
        paths.extend([
            system_config / "config.yaml",
            system_config / "config.yml",
            system_config / "config.ini",
        ])
        
        return paths
    
    def load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not config_path.exists():
            return {}
        
        try:
            if config_path.suffix in [".yaml", ".yml"]:
                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            elif config_path.suffix == ".ini":
                return self._load_ini_config(config_path)
            else:
                return {}
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}", file=sys.stderr)
            return {}
    
    def _load_ini_config(self, config_path: Path) -> Dict[str, Any]:
        """Load INI configuration file."""
        import configparser
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        
        result = {}
        if "datamap" in config:
            for key, value in config["datamap"].items():
                # Convert string values to appropriate types
                if value.lower() in ["true", "false"]:
                    result[key] = value.lower() == "true"
                elif value.isdigit():
                    result[key] = int(value)
                else:
                    result[key] = value
        
        return result
    
    def get_settings(self) -> Settings:
        """Get settings with configuration file support."""
        if self._settings is None:
            # Load configuration from files
            config_data = {}
            for config_path in self.config_paths:
                if config_path.exists():
                    file_config = self.load_config_file(config_path)
                    config_data.update(file_config)
                    break  # Use first found config file
            
            # Temporarily set environment variables from config file
            # This allows environment variables to take precedence
            original_env = {}
            try:
                for key, value in config_data.items():
                    env_key = f"DATAMAP_{key.upper()}"
                    if env_key not in os.environ:
                        original_env[env_key] = os.environ.get(env_key)
                        os.environ[env_key] = str(value)
                
                # Create settings - environment variables will take precedence
                self._settings = Settings()
            finally:
                # Restore original environment variables
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        
        return self._settings
    
    def reload_settings(self) -> Settings:
        """Reload settings from all sources."""
        self._settings = None
        return self.get_settings()
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        try:
            settings = self.get_settings()
            
            # Check API credentials
            if not settings.api_key:
                issues.append("API key is not configured")
            if not settings.api_secret:
                issues.append("API secret is not configured")
            
            # Check API URL
            try:
                urlparse(settings.api_base_url)
            except Exception:
                issues.append("Invalid API base URL")
            
            # Check numeric values
            if settings.timeout < 1 or settings.timeout > 300:
                issues.append("Timeout must be between 1 and 300 seconds")
            
            if settings.retry_attempts < 0 or settings.retry_attempts > 10:
                issues.append("Retry attempts must be between 0 and 10")
            
            if settings.download_concurrency < 1 or settings.download_concurrency > 10:
                issues.append("Download concurrency must be between 1 and 10")
            
            if settings.chunk_size < 1024 or settings.chunk_size > 1048576:
                issues.append("Chunk size must be between 1024 and 1048576 bytes")
            
        except Exception as e:
            issues.append(f"Configuration validation error: {e}")
        
        return issues
    
    def get_config_help(self) -> str:
        """Get configuration help text."""
        return """
Configuration Sources (in order of precedence):
1. Command line arguments (--config, -c)
2. Environment variables (DATAMAP_*)
3. Configuration files:
   - .datamap.yaml/.datamap.yml/.datamap.ini (current directory)
   - datamap.yaml/datamap.yml/datamap.ini (current directory)
   - ~/.datamap/config.yaml (user home)
   - ~/.datamaprc (user home)
   - /etc/datamap/config.yaml (system-wide)

Required Environment Variables:
- DATAMAP_API_KEY: Your DataMap API key
- DATAMAP_API_SECRET: Your DataMap API secret

Optional Environment Variables:
- DATAMAP_API_BASE_URL: API base URL (default: https://datamap.pcs.usp.br/api/v1)
- DATAMAP_TIMEOUT: Request timeout in seconds (default: 30)
- DATAMAP_RETRY_ATTEMPTS: Number of retry attempts (default: 3)
- DATAMAP_USER_ID: User ID
- DATAMAP_TENANCIES: Tenancy information
- DATAMAP_LOG_LEVEL: Logging level (DEBUG|INFO|WARNING|ERROR|CRITICAL)
- DATAMAP_LOG_FORMAT: Log format (json|text)
- DATAMAP_OUTPUT_FORMAT: Output format (table|json|yaml|csv)
- DATAMAP_COLOR_OUTPUT: Enable colored output (true|false)
- DATAMAP_DOWNLOAD_CONCURRENCY: Concurrent downloads (1-10)
- DATAMAP_CHUNK_SIZE: Download chunk size in bytes (1024-1048576)

Configuration File Format (YAML):
```yaml
api_key: "your-api-key"
api_secret: "your-api-secret"
api_base_url: "https://datamap.pcs.usp.br/api/v1"
timeout: 30
retry_attempts: 3
log_level: "INFO"
output_format: "table"
color_output: true
download_concurrency: 3
chunk_size: 8192
```
"""


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_settings() -> Settings:
    """Get the global settings instance with configuration file support."""
    return get_config_manager().get_settings()


def reload_settings() -> Settings:
    """Reload settings from all sources."""
    return get_config_manager().reload_settings()


def validate_configuration() -> List[str]:
    """Validate configuration and return list of issues."""
    return get_config_manager().validate_configuration()


def get_config_help() -> str:
    """Get configuration help text."""
    return get_config_manager().get_config_help()
