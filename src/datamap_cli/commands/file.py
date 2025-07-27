"""File-related commands for DataMap CLI."""

import asyncio
import re
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..api.client import DataMapAPIClient
from ..api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataMapAPIError,
    NotFoundError,
    ValidationError,
)
from ..api.models import DataFile
from ..config.settings import get_settings

# Create the file command group
app = typer.Typer(
    name="file",
    help="File-related commands"
)

# Create console for rich output
console = Console()


def validate_uuid(uuid: str) -> str:
    """Validate UUID format.
    
    Args:
        uuid: UUID string to validate
        
    Returns:
        Validated UUID string
        
    Raises:
        typer.BadParameter: If UUID format is invalid
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    if not uuid_pattern.match(uuid):
        raise typer.BadParameter(
            f"Invalid UUID format: {uuid}. "
            "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        )
    return uuid


def validate_version_name(version_name: str) -> str:
    """Validate version name format.
    
    Args:
        version_name: Version name to validate
        
    Returns:
        Validated version name
        
    Raises:
        typer.BadParameter: If version name format is invalid
    """
    if not version_name or not version_name.strip():
        raise typer.BadParameter("Version name cannot be empty")
    
    # Version names should be alphanumeric with dots, dashes, and underscores
    version_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
    if not version_pattern.match(version_name):
        raise typer.BadParameter(
            f"Invalid version name format: {version_name}. "
            "Only alphanumeric characters, dots, dashes, and underscores are allowed"
        )
    
    return version_name.strip()


async def _get_api_client() -> DataMapAPIClient:
    """Get configured API client.
    
    Returns:
        Configured DataMapAPIClient instance
    """
    settings = get_settings()
    return DataMapAPIClient(
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        base_url=settings.api_base_url,
        timeout=settings.timeout,
        max_retries=settings.retry_attempts,
        user_id=settings.user_id,
        tenancy=settings.tenancies,
    )


async def _get_file_info(
    api_client: DataMapAPIClient,
    dataset_id: str,
    version_name: str,
    file_id: str,
) -> DataFile:
    """Get file information from API.
    
    Args:
        api_client: API client instance
        dataset_id: Dataset UUID
        version_name: Version name
        file_id: File UUID
        
    Returns:
        DataFile object
        
    Raises:
        typer.Exit: If file not found
    """
    try:
        # Get version to find the file
        version = await api_client.get_version(dataset_id, version_name)
        
        # Find the specific file
        for file in version.files_in:
            if file.id == file_id:
                return file
        
        raise typer.Exit(f"File {file_id} not found in version {version_name}")
        
    except NotFoundError:
        raise typer.Exit(f"Version {version_name} not found in dataset {dataset_id}")
    except Exception as e:
        raise typer.Exit(f"Error getting file info: {str(e)}")


@app.command()
def info(
    dataset_id: str = typer.Argument(
        ...,
        help="Dataset UUID",
        callback=validate_uuid,
    ),
    version_name: str = typer.Argument(
        ...,
        help="Version name",
        callback=validate_version_name,
    ),
    file_id: str = typer.Argument(
        ...,
        help="File UUID",
        callback=validate_uuid,
    ),
) -> None:
    """Get detailed information about a file.
    
    This command retrieves comprehensive information about a specific file
    in a dataset version, including metadata, size, format, and timestamps.
    
    Examples:
        datamap file info 12345678-1234-1234-1234-123456789abc v1.0 87654321-4321-4321-4321-cba987654321
    """
    
    async def _info():
        try:
            # Get API client
            api_client = await _get_api_client()
            
            # Get file information
            file_info = await _get_file_info(api_client, dataset_id, version_name, file_id)
            
            # Display file information
            table = Table(title=f"File Information: {file_info.name}")
            table.add_column("Property", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            
            table.add_row("File ID", file_info.id)
            table.add_row("Name", file_info.name)
            table.add_row("Size", file_info.formatted_size)
            table.add_row("Format", file_info.format or "Unknown")
            table.add_row("Extension", file_info.extension or "None")
            table.add_row("Created", file_info.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("Updated", file_info.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("Created By", file_info.created_by or "Unknown")
            table.add_row("Storage File Name", file_info.storage_file_name or "None")
            table.add_row("Storage Path", file_info.storage_path or "None")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"❌ Error: {str(e)}", style="red")
            raise typer.Exit(1)
    
    asyncio.run(_info())
