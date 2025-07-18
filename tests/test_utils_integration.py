"""Integration tests for utility modules."""

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


class TestUtilsIntegration:
    """Test utility integration in real scenarios."""
    
    @patch('datamap_cli.utils.progress.get_settings')
    @patch('datamap_cli.utils.output.get_settings')
    def test_download_scenario(self, mock_output_settings, mock_progress_settings):
        """Test a complete download scenario with all utilities."""
        # Mock settings for both progress and output
        mock_progress_settings.return_value = Mock(
            log_level="INFO",
            log_format="text",
            color_output=False,
            download_concurrency=3,
            chunk_size=8192,
        )
        
        mock_output_settings.return_value = Mock(
            output_format="table",
            color_output=True,
        )
        
        # Create logger
        logger = get_logger("download_test")
        assert logger is not None
        
        # Create progress manager
        progress_manager = ProgressManager()
        assert progress_manager is not None
        
        # Create download tracker
        tracker = DownloadProgressTracker()
        assert tracker is not None
        
        # Create output formatter
        formatter = OutputFormatter()
        assert formatter is not None
        
        # Simulate download scenario
        dataset_data = {
            "uuid": "test-dataset-uuid",
            "name": "Test Dataset",
            "description": "A test dataset for integration testing",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "versions": [
                {"name": "v1.0", "files": [{"size": 1024}, {"size": 2048}]},
                {"name": "v2.0", "files": [{"size": 4096}]},
            ],
            "tags": ["test", "integration"],
        }
        
        # Format dataset info
        formatted_dataset = format_dataset_info(dataset_data)
        assert formatted_dataset["uuid"] == "test-dataset-uuid"
        assert formatted_dataset["version_count"] == 2
        
        # Test file size formatting
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        
        # Test download speed formatting
        assert format_download_speed(1024) == "1.0 KB/s"
        assert format_download_speed(1024 * 1024) == "1.0 MB/s"
        
        # Test output formatting
        json_output = formatter._format_json(formatted_dataset)
        assert '"uuid": "test-dataset-uuid"' in json_output
        
        yaml_output = formatter._format_yaml(formatted_dataset)
        assert "uuid: test-dataset-uuid" in yaml_output
        
        # Test version formatting
        version_data = {
            "name": "v1.0",
            "description": "First version",
            "created_at": "2023-01-01T00:00:00Z",
            "files": [{"size": 1024}, {"size": 2048}],
        }
        
        formatted_version = format_version_info(version_data)
        assert formatted_version["name"] == "v1.0"
        assert formatted_version["file_count"] == 2
        assert formatted_version["total_size"] == 3072
        
        # Test file formatting
        file_data = {
            "uuid": "file-uuid",
            "name": "test.txt",
            "size": 1024,
            "mime_type": "text/plain",
            "created_at": "2023-01-01T00:00:00Z",
        }
        
        formatted_file = format_file_info(file_data)
        assert formatted_file["uuid"] == "file-uuid"
        assert formatted_file["size_formatted"] == "1.0 KB"
    
    @patch('datamap_cli.utils.progress.get_settings')
    def test_progress_tracking(self, mock_settings):
        """Test progress tracking functionality."""
        mock_settings.return_value = Mock(
            log_level="INFO",
            log_format="text",
            color_output=False,
        )
        
        tracker = DownloadProgressTracker()
        
        # Test basic properties
        assert tracker.total_files == 0
        assert tracker.completed_files == 0
        assert tracker.downloaded_bytes == 0
        
        # Test file size and speed formatting
        assert format_file_size(1024) == "1.0 KB"
        assert format_download_speed(1024) == "1.0 KB/s"
        
        # Test progress manager creation
        manager = ProgressManager()
        assert manager is not None
        assert manager.console is not None
    
    @patch('datamap_cli.utils.output.get_settings')
    def test_output_formats(self, mock_settings):
        """Test all output formats."""
        mock_settings.return_value = Mock(
            output_format="json",
            color_output=False,
        )
        
        formatter = OutputFormatter()
        
        # Test data
        test_data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "San Francisco"},
            {"name": "Charlie", "age": 35, "city": "Chicago"},
        ]
        
        # Test JSON
        json_result = formatter._format_json(test_data)
        assert '"name": "Alice"' in json_result
        assert '"age": 30' in json_result
        
        # Test YAML
        yaml_result = formatter._format_yaml(test_data)
        assert "name: Alice" in yaml_result
        assert "age: 30" in yaml_result
        
        # Test CSV
        csv_result = formatter._format_csv(test_data)
        assert "name,age,city" in csv_result
        assert "Alice,30,New York" in csv_result
        
        # Test table (string format)
        table_result = formatter._format_table(test_data, color_output=False)
        assert "name" in table_result
        assert "Alice" in table_result 