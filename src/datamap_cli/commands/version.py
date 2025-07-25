"""Version-related commands for DataMap CLI."""

import asyncio
import re
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..api.client import DataMapAPIClient
from ..api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataMapAPIError,
    NotFoundError,
    ValidationError,
)
from ..config.settings import get_settings
from ..utils.output import OutputFormatter, format_file_info

# Create the version command group
app = typer.Typer(
    name="version",
    help="Version-related commands"
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
    
    # Version names should be alphanumeric with possible hyphens/underscores
    version_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    if not version_pattern.match(version_name):
        raise typer.BadParameter(
            f"Invalid version name format: {version_name}. "
            "Version names should contain only alphanumeric characters, hyphens, and underscores"
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


@app.command()
def files(
    dataset_uuid: str = typer.Argument(
        ...,
        help="Dataset UUID",
        callback=validate_uuid,
    ),
    version_name: str = typer.Argument(
        ...,
        help="Version name",
        callback=validate_version_name,
    ),
    output_format: str = typer.Option(
        None,
        "--output-format",
        "-f",
        help="Output format (table, json, yaml, csv)",
    ),
    color_output: bool = typer.Option(
        None,
        "--color/--no-color",
        help="Enable/disable colored output",
    ),
) -> None:
    """List files in a specific dataset version.
    
    This command retrieves and displays all files available in a specific version
    of a dataset, including file metadata such as size, format, and creation date.
    
    Examples:
        datamap version files 12345678-1234-1234-1234-123456789012 v1.0
        datamap version files 12345678-1234-1234-1234-123456789012 latest --output-format json
        datamap version files 12345678-1234-1234-1234-123456789012 v2.1 --no-color
    """
    
    async def _files():
        """Async implementation of the files command."""
        try:
            # Get API client
            client = await _get_api_client()
            
            # Fetch version information
            with console.status(
                f"[bold blue]Fetching files for version '{version_name}'...",
                spinner="dots"
            ):
                version = await client.get_version(dataset_uuid, version_name)
            
            # Prepare output data
            files_data = []
            for file in version.files_in:
                files_data.append(format_file_info(file.model_dump()))
            
            # Create output formatter
            formatter = OutputFormatter(console)
            
            # Display results
            if output_format == "table" or output_format is None:
                # Create rich table for display
                table = Table(
                    title=f"Files in Version '{version_name}'",
                    show_header=True,
                    header_style="bold magenta",
                    border_style="blue",
                )
                
                table.add_column("File ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="green")
                table.add_column("Size", style="yellow", justify="right")
                table.add_column("Format", style="blue")
                table.add_column("Created", style="dim")
                table.add_column("Updated", style="dim")
                
                for file in version.files_in:
                    table.add_row(
                        file.id,
                        file.name,
                        file.formatted_size,
                        file.format or "N/A",
                        file.created_at.strftime("%Y-%m-%d %H:%M"),
                        file.updated_at.strftime("%Y-%m-%d %H:%M"),
                    )
                
                # Add summary information
                summary = f"Total: {version.file_count} files, Size: {version.formatted_size}"
                
                console.print(table)
                console.print(f"\n[bold green]{summary}[/bold green]")
                
            else:
                # Use formatter for other output formats
                formatter.print_output(
                    {
                        "version_name": version_name,
                        "dataset_uuid": dataset_uuid,
                        "file_count": version.file_count,
                        "total_size": version.total_size,
                        "formatted_size": version.formatted_size,
                        "files": files_data,
                    },
                    output_format=output_format,
                    color_output=color_output,
                )
            
        except AuthenticationError:
            console.print(
                Panel(
                    "[bold red]Authentication Error[/bold red]\n"
                    "Your API credentials are invalid or expired. "
                    "Please check your configuration.",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
            
        except AuthorizationError:
            console.print(
                Panel(
                    "[bold red]Authorization Error[/bold red]\n"
                    "You don't have permission to access this dataset or version. "
                    "Please check your permissions.",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
            
        except NotFoundError as e:
            console.print(
                Panel(
                    f"[bold red]Not Found Error[/bold red]\n"
                    f"Could not find the requested resource: {e.resource_type} '{e.resource_id}'",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
            
        except ValidationError as e:
            console.print(
                Panel(
                    f"[bold red]Validation Error[/bold red]\n"
                    f"Invalid input: {str(e)}",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
            
        except DataMapAPIError as e:
            console.print(
                Panel(
                    f"[bold red]API Error[/bold red]\n"
                    f"An error occurred while communicating with the API: {str(e)}",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
            
        except Exception as e:
            console.print(
                Panel(
                    f"[bold red]Unexpected Error[/bold red]\n"
                    f"An unexpected error occurred: {str(e)}",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
    
    # Run the async function
    asyncio.run(_files())
