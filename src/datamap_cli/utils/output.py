"""Output formatting utilities for DataMap CLI."""

import csv
import json
import sys
from io import StringIO
from typing import Any, Dict, List, Optional, Union

import yaml
from rich.console import Console
from rich.table import Table

from ..config.settings import get_settings


class OutputFormatter:
    """Handles different output formats for CLI commands."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize output formatter.
        
        Args:
            console: Rich console instance (creates new one if not provided)
        """
        self.console = console or Console()
        self.settings = get_settings()
    
    def format_output(
        self,
        data: Any,
        output_format: Optional[str] = None,
        color_output: Optional[bool] = None,
    ) -> str:
        """Format data according to the specified output format.
        
        Args:
            data: Data to format
            output_format: Output format (table, json, yaml, csv)
            color_output: Whether to enable colored output
            
        Returns:
            Formatted output string
        """
        output_format = output_format or self.settings.output_format
        color_output = color_output if color_output is not None else self.settings.color_output
        
        if output_format == "json":
            return self._format_json(data)
        elif output_format == "yaml":
            return self._format_yaml(data)
        elif output_format == "csv":
            return self._format_csv(data)
        elif output_format == "table":
            return self._format_table(data, color_output)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def print_output(
        self,
        data: Any,
        output_format: Optional[str] = None,
        color_output: Optional[bool] = None,
    ) -> None:
        """Print formatted output to console.
        
        Args:
            data: Data to format and print
            output_format: Output format
            color_output: Whether to enable colored output
        """
        if output_format == "table" or (output_format is None and self.settings.output_format == "table"):
            # For tables, use rich's built-in printing
            self._print_table(data, color_output or False)
        else:
            # For other formats, format as string and print
            formatted = self.format_output(data, output_format, color_output)
            print(formatted)
    
    def _format_json(self, data: Any) -> str:
        """Format data as JSON.
        
        Args:
            data: Data to format
            
        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, default=str)
    
    def _format_yaml(self, data: Any) -> str:
        """Format data as YAML.
        
        Args:
            data: Data to format
            
        Returns:
            YAML string
        """
        return yaml.dump(data, default_flow_style=False, sort_keys=False, default_style=None)
    
    def _format_csv(self, data: Any) -> str:
        """Format data as CSV.
        
        Args:
            data: Data to format
            
        Returns:
            CSV string
        """
        if not data:
            return ""
        
        # Handle different data types
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                # List of dictionaries
                fieldnames = list(data[0].keys())
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
            else:
                # Simple list
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(data)
                return output.getvalue()
        elif isinstance(data, dict):
            # Single dictionary
            output = StringIO()
            writer = csv.writer(output)
            for key, value in data.items():
                writer.writerow([key, value])
            return output.getvalue()
        else:
            # Single value
            return str(data)
    
    def _format_table(self, data: Any, color_output: bool = True) -> str:
        """Format data as a table string (for non-rich output).
        
        Args:
            data: Data to format
            color_output: Whether to enable colored output
            
        Returns:
            Table string
        """
        # This is a fallback for when rich is not available
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            if not data:
                return "No data"
            
            fieldnames = list(data[0].keys())
            lines = [" | ".join(fieldnames)]
            lines.append("-" * len(lines[0]))
            
            for row in data:
                values = [str(row.get(field, "")) for field in fieldnames]
                lines.append(" | ".join(values))
            
            return "\n".join(lines)
        else:
            return str(data)
    
    def _print_table(self, data: Any, color_output: bool = True) -> None:
        """Print data as a rich table.
        
        Args:
            data: Data to print
            color_output: Whether to enable colored output
        """
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            table = Table(show_header=True, header_style="bold magenta")
            
            # Add columns
            fieldnames = list(data[0].keys())
            for field in fieldnames:
                table.add_column(field, style="cyan")
            
            # Add rows
            for row in data:
                values = [str(row.get(field, "")) for field in fieldnames]
                table.add_row(*values)
            
            self.console.print(table)
        elif isinstance(data, dict):
            # Single dictionary
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in data.items():
                table.add_row(str(key), str(value))
            
            self.console.print(table)
        else:
            # Single value or other types
            self.console.print(str(data))


def format_dataset_info(dataset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format dataset information for output.
    
    Args:
        dataset_data: Raw dataset data from API
        
    Returns:
        Formatted dataset information
    """
    return {
        "uuid": dataset_data.get("uuid"),
        "name": dataset_data.get("name"),
        "description": dataset_data.get("description"),
        "created_at": dataset_data.get("created_at"),
        "updated_at": dataset_data.get("updated_at"),
        "version_count": len(dataset_data.get("versions", [])),
        "tags": dataset_data.get("tags", []),
    }


def format_version_info(version_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format version information for output.
    
    Args:
        version_data: Raw version data from API
        
    Returns:
        Formatted version information
    """
    return {
        "name": version_data.get("name"),
        "description": version_data.get("description"),
        "created_at": version_data.get("created_at"),
        "file_count": len(version_data.get("files", [])),
        "total_size": sum(file.get("size", 0) for file in version_data.get("files", [])),
    }


def format_file_info(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format file information for output.
    
    Args:
        file_data: Raw file data from API
        
    Returns:
        Formatted file information
    """
    return {
        "uuid": file_data.get("uuid"),
        "name": file_data.get("name"),
        "size": file_data.get("size"),
        "size_formatted": format_file_size(file_data.get("size", 0)),
        "mime_type": file_data.get("mime_type"),
        "created_at": file_data.get("created_at"),
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


# Global output formatter instance (lazy initialization)
_output_formatter_instance: Optional[OutputFormatter] = None


def get_output_formatter() -> OutputFormatter:
    """Get the global output formatter instance.
    
    Returns:
        OutputFormatter instance
    """
    global _output_formatter_instance
    if _output_formatter_instance is None:
        _output_formatter_instance = OutputFormatter()
    return _output_formatter_instance 