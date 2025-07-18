"""Tests for configuration management system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from datamap_cli.config.settings import (
    Settings,
    ConfigurationManager,
    get_config_manager,
    validate_configuration,
    get_config_help,
)


class TestSettings:
    """Test Settings class."""
    
    def test_valid_settings(self):
        """Test creating valid settings."""
        settings = Settings(
            api_key="test-key",
            api_secret="test-secret",
            api_base_url="https://api.example.com"
        )
        
        assert settings.api_key == "test-key"
        assert settings.api_secret == "test-secret"
        assert settings.api_base_url == "https://api.example.com"
        assert settings.timeout == 30  # default value
        assert settings.log_level == "INFO"  # default value
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError):
            Settings()
        
        with pytest.raises(ValidationError):
            Settings(api_key="test-key")  # missing api_secret
    
    def test_invalid_api_url(self):
        """Test validation of API URL."""
        with pytest.raises(ValidationError, match="API base URL must start with http:// or https://"):
            Settings(
                api_key="test-key",
                api_secret="test-secret",
                api_base_url="invalid-url"
            )
    
    def test_invalid_timeout(self):
        """Test validation of timeout values."""
        with pytest.raises(ValidationError):
            Settings(
                api_key="test-key",
                api_secret="test-secret",
                timeout=0  # too low
            )
        
        with pytest.raises(ValidationError):
            Settings(
                api_key="test-key",
                api_secret="test-secret",
                timeout=400  # too high
            )
    
    def test_invalid_log_level(self):
        """Test validation of log level."""
        with pytest.raises(ValidationError):
            Settings(
                api_key="test-key",
                api_secret="test-secret",
                log_level="INVALID"
            )
    
    def test_credential_summary(self):
        """Test credential summary method."""
        settings = Settings(
            api_key="test-key-12345",
            api_secret="test-secret-67890",
            api_base_url="https://api.example.com"
        )
        
        summary = settings.get_credential_summary()
        
        assert summary["api_key"] == "test-key..."
        assert summary["api_secret"] == "test-sec..."
        assert summary["api_base_url"] == "https://api.example.com"
        assert summary["user_id"] == "Not set"
    
    def test_to_dict_masks_secrets(self):
        """Test that to_dict method masks sensitive data."""
        settings = Settings(
            api_key="test-key",
            api_secret="test-secret",
            api_base_url="https://api.example.com"
        )
        
        data = settings.to_dict()
        
        assert data["api_key"] == "***"
        assert data["api_secret"] == "***"
        assert data["api_base_url"] == "https://api.example.com"


class TestConfigurationManager:
    """Test ConfigurationManager class."""
    
    def test_get_config_paths(self):
        """Test configuration path discovery."""
        manager = ConfigurationManager()
        paths = manager._get_config_paths()
        
        # Should include various config file locations
        assert any(".datamap.yaml" in str(p) for p in paths)
        assert any("datamap.yaml" in str(p) for p in paths)
        assert any(".datamaprc" in str(p) for p in paths)
    
    def test_load_yaml_config(self):
        """Test loading YAML configuration file."""
        config_data = {
            "api_key": "yaml-key",
            "api_secret": "yaml-secret",
            "timeout": 60,
            "log_level": "DEBUG"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            manager = ConfigurationManager()
            loaded_data = manager.load_config_file(config_path)
            
            assert loaded_data["api_key"] == "yaml-key"
            assert loaded_data["api_secret"] == "yaml-secret"
            assert loaded_data["timeout"] == 60
            assert loaded_data["log_level"] == "DEBUG"
        finally:
            config_path.unlink()
    
    def test_load_ini_config(self):
        """Test loading INI configuration file."""
        config_content = """
[datamap]
api_key = ini-key
api_secret = ini-secret
timeout = 45
color_output = true
download_concurrency = 5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            manager = ConfigurationManager()
            loaded_data = manager.load_config_file(config_path)
            
            assert loaded_data["api_key"] == "ini-key"
            assert loaded_data["api_secret"] == "ini-secret"
            assert loaded_data["timeout"] == 45
            assert loaded_data["color_output"] is True
            assert loaded_data["download_concurrency"] == 5
        finally:
            config_path.unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file."""
        manager = ConfigurationManager()
        loaded_data = manager.load_config_file(Path("/nonexistent/config.yaml"))
        
        assert loaded_data == {}
    
    def test_get_settings_with_config_file(self):
        """Test getting settings with configuration file."""
        config_data = {
            "api_key": "file-key",
            "api_secret": "file-secret",
            "timeout": 90
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            # Mock the config paths to include our test file
            with patch.object(ConfigurationManager, '_get_config_paths') as mock_paths:
                mock_paths.return_value = [config_path]
                
                manager = ConfigurationManager()
                settings = manager.get_settings()
                
                assert settings.api_key == "file-key"
                assert settings.api_secret == "file-secret"
                assert settings.timeout == 90
        finally:
            config_path.unlink()
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid settings."""
        config_data = {
            "api_key": "valid-key",
            "api_secret": "valid-secret",
            "timeout": 30,
            "retry_attempts": 3,
            "download_concurrency": 3,
            "chunk_size": 8192
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            with patch.object(ConfigurationManager, '_get_config_paths') as mock_paths:
                mock_paths.return_value = [config_path]
                
                manager = ConfigurationManager()
                issues = manager.validate_configuration()
                
                assert len(issues) == 0
        finally:
            config_path.unlink()
    
    def test_validate_configuration_invalid(self):
        """Test configuration validation with invalid settings."""
        config_data = {
            "api_key": "",  # empty key
            "api_secret": "valid-secret",
            "timeout": 400,  # too high
            "retry_attempts": 15,  # too high
            "download_concurrency": 0,  # too low
            "chunk_size": 500  # too low
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            with patch.object(ConfigurationManager, '_get_config_paths') as mock_paths:
                mock_paths.return_value = [config_path]
                
                manager = ConfigurationManager()
                issues = manager.validate_configuration()

                print(f"Validation issues: {issues}")
                assert len(issues) > 0
                assert any("API credentials cannot be empty" in issue for issue in issues)
                assert any("Input should be less than or equal to 300" in issue for issue in issues)
        finally:
            config_path.unlink()
    
    def test_get_config_help(self):
        """Test configuration help text."""
        manager = ConfigurationManager()
        help_text = manager.get_config_help()
        
        assert "Configuration Sources" in help_text
        assert "DATAMAP_API_KEY" in help_text
        assert "DATAMAP_API_SECRET" in help_text
        assert "yaml" in help_text


class TestConfigurationFunctions:
    """Test configuration utility functions."""
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
    
    def test_validate_configuration_function(self):
        """Test validate_configuration function."""
        # This will use environment variables or defaults
        issues = validate_configuration()
        
        # Should return a list (may be empty if env vars are set)
        assert isinstance(issues, list)
    
    def test_get_config_help_function(self):
        """Test get_config_help function."""
        help_text = get_config_help()
        
        assert isinstance(help_text, str)
        assert len(help_text) > 0
        assert "Configuration Sources" in help_text


class TestEnvironmentVariables:
    """Test environment variable handling."""
    
    def test_environment_variable_loading(self):
        """Test loading settings from environment variables."""
        with patch.dict(os.environ, {
            "DATAMAP_API_KEY": "env-key",
            "DATAMAP_API_SECRET": "env-secret",
            "DATAMAP_TIMEOUT": "45",
            "DATAMAP_LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()
            
            assert settings.api_key == "env-key"
            assert settings.api_secret == "env-secret"
            assert settings.timeout == 45
            assert settings.log_level == "DEBUG"
    
    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over config files."""
        config_data = {
            "api_key": "file-key",
            "api_secret": "file-secret",
            "timeout": 60
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            with patch.object(ConfigurationManager, '_get_config_paths') as mock_paths:
                mock_paths.return_value = [config_path]
                
                with patch.dict(os.environ, {
                    "DATAMAP_API_KEY": "env-key",
                    "DATAMAP_TIMEOUT": "30"
                }):
                    manager = ConfigurationManager()
                    settings = manager.get_settings()
                    
                    # Environment variables should take precedence
                    assert settings.api_key == "env-key"
                    assert settings.timeout == 30
                    # File config should be used for non-env vars
                    assert settings.api_secret == "file-secret"
        finally:
            config_path.unlink() 