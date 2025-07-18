"""Tests for utility modules."""

import pytest
from unittest.mock import Mock, patch

from datamap_cli.utils import (
    get_logger,
    ProgressManager,
    DownloadProgressTracker,
    format_file_size,
    format_download_speed,
    OutputFormatter,
    format_dataset_info,
    format_version_info,
    format_file_info,
)


class TestLogging:
    """Test logging utilities."""
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test")
        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")


class TestProgress:
    """Test progress utilities."""
    
    @patch('datamap_cli.utils.progress.get_settings')
    def test_progress_manager_creation(self, mock_get_settings):
        """Test progress manager creation."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        manager = ProgressManager()
        assert manager is not None
        assert manager.console is not None
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
    
    def test_format_download_speed(self):
        """Test download speed formatting."""
        assert format_download_speed(1024) == "1.0 KB/s"
        assert format_download_speed(1024 * 1024) == "1.0 MB/s"
    
    @patch('datamap_cli.utils.progress.get_settings')
    def test_download_progress_tracker(self, mock_get_settings):
        """Test download progress tracker."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        tracker = DownloadProgressTracker()
        assert tracker is not None
        assert tracker.total_files == 0
        assert tracker.completed_files == 0


class TestOutput:
    """Test output formatting utilities."""
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_output_formatter_creation(self, mock_get_settings):
        """Test output formatter creation."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.output_format = "table"
        mock_settings.color_output = True
        mock_get_settings.return_value = mock_settings
        
        formatter = OutputFormatter()
        assert formatter is not None
        assert formatter.settings is not None
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_format_json(self, mock_get_settings):
        """Test JSON formatting."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.output_format = "json"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        formatter = OutputFormatter()
        data = {"key": "value", "number": 42}
        result = formatter._format_json(data)
        assert '"key": "value"' in result
        assert '"number": 42' in result
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_format_yaml(self, mock_get_settings):
        """Test YAML formatting."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.output_format = "yaml"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        formatter = OutputFormatter()
        data = {"key": "value", "number": 42}
        result = formatter._format_yaml(data)
        assert "key: value" in result
        assert "number: 42" in result
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_format_csv(self, mock_get_settings):
        """Test CSV formatting."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.output_format = "csv"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        formatter = OutputFormatter()
        data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        result = formatter._format_csv(data)
        assert "name,age" in result
        assert "John,30" in result
        assert "Jane,25" in result
    
    def test_format_dataset_info(self):
        """Test dataset info formatting."""
        dataset_data = {
            "uuid": "test-uuid",
            "name": "Test Dataset",
            "description": "Test description",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "versions": [{"name": "v1"}, {"name": "v2"}],
            "tags": ["test", "data"],
        }
        
        result = format_dataset_info(dataset_data)
        assert result["uuid"] == "test-uuid"
        assert result["name"] == "Test Dataset"
        assert result["version_count"] == 2
        assert result["tags"] == ["test", "data"]
    
    def test_format_version_info(self):
        """Test version info formatting."""
        version_data = {
            "name": "v1.0",
            "description": "First version",
            "created_at": "2023-01-01T00:00:00Z",
            "files": [
                {"size": 1024},
                {"size": 2048},
            ],
        }
        
        result = format_version_info(version_data)
        assert result["name"] == "v1.0"
        assert result["file_count"] == 2
        assert result["total_size"] == 3072
    
    def test_format_file_info(self):
        """Test file info formatting."""
        file_data = {
            "uuid": "file-uuid",
            "name": "test.txt",
            "size": 1024,
            "mime_type": "text/plain",
            "created_at": "2023-01-01T00:00:00Z",
        }
        
        result = format_file_info(file_data)
        assert result["uuid"] == "file-uuid"
        assert result["name"] == "test.txt"
        assert result["size"] == 1024
        assert result["size_formatted"] == "1.0 KB"
        assert result["mime_type"] == "text/plain"


class TestIntegration:
    """Test integration between utilities."""
    
    @patch('datamap_cli.utils.progress.get_settings')
    def test_logging_with_progress(self, mock_get_settings):
        """Test that logging and progress work together."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        # Create progress manager
        manager = ProgressManager()
        
        # Get logger
        logger = get_logger("test")
        
        # Both should work without conflicts
        assert logger is not None
        assert manager is not None
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_output_with_formatting(self, mock_get_settings):
        """Test output formatting with different data types."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.output_format = "json"
        mock_settings.color_output = False
        mock_get_settings.return_value = mock_settings
        
        formatter = OutputFormatter()
        
        # Test with dataset info
        dataset_data = {
            "uuid": "test-uuid",
            "name": "Test Dataset",
            "description": "Test description",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "versions": [],
            "tags": [],
        }
        
        formatted_data = format_dataset_info(dataset_data)
        
        # Should format to JSON
        json_result = formatter._format_json(formatted_data)
        assert '"uuid": "test-uuid"' in json_result
        
        # Should format to YAML
        yaml_result = formatter._format_yaml(formatted_data)
        assert "uuid: test-uuid" in yaml_result 