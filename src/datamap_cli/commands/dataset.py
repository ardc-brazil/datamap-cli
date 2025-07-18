"""Dataset-related commands for DataMap CLI."""

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
from ..utils.output import OutputFormatter, format_dataset_info

# Create the dataset command group
app = typer.Typer(
    name="dataset",
    help="Dataset-related commands"
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
def info(
    uuid: str = typer.Argument(
        ...,
        help="Dataset UUID",
        callback=validate_uuid,
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
    """Get detailed information about a dataset.
    
    This command retrieves comprehensive information about a dataset including
    its metadata, versions, and current status.
    
    Examples:
        datamap dataset info 12345678-1234-1234-1234-123456789abc
        datamap dataset info 12345678-1234-1234-1234-123456789abc --output-format json
    """
    async def _info():
        try:
            # Get API client
            client = await _get_api_client()
            
            # Show loading message
            with console.status("[bold green]Fetching dataset information..."):
                # Fetch dataset
                dataset = await client.get_dataset(uuid)
            
            # Format output
            formatter = OutputFormatter(console)
            
            # Prepare dataset data for output
            dataset_data = {
                "UUID": dataset.id,
                "Name": dataset.name,
                "Design State": dataset.design_state,
                "Enabled": "Yes" if dataset.is_enabled else "No",
                "Tenancy": dataset.tenancy,
                "Created": dataset.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Updated": dataset.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Version Count": dataset.version_count,
                "Total Files": dataset.total_files,
            }
            
            # Add current version info if available
            if dataset.current_version:
                dataset_data["Current Version"] = dataset.current_version.name
                dataset_data["Current Version Files"] = dataset.current_version.file_count
                dataset_data["Current Version Size"] = dataset.current_version.formatted_size
            
            # Print dataset information
            if output_format == "table" or (output_format is None and get_settings().output_format == "table"):
                # Create rich table
                table = Table(title=f"Dataset: {dataset.name}", show_header=True, header_style="bold magenta")
                table.add_column("Property", style="cyan", no_wrap=True)
                table.add_column("Value", style="green")
                
                for key, value in dataset_data.items():
                    table.add_row(key, str(value))
                
                console.print(table)
                
                # Show dataset data if available
                if dataset.data:
                    console.print("\n[bold]Dataset Data:[/bold]")
                    console.print(Panel(str(dataset.data), title="Additional Data"))
            else:
                # Use formatter for other output formats
                formatter.print_output(dataset_data, output_format, color_output)
            
            # Show versions summary if available
            if dataset.versions:
                console.print(f"\n[bold]Versions ({len(dataset.versions)}):[/bold]")
                versions_table = Table(show_header=True, header_style="bold blue")
                versions_table.add_column("Name", style="cyan")
                versions_table.add_column("Files", style="green")
                versions_table.add_column("Size", style="yellow")
                versions_table.add_column("State", style="magenta")
                versions_table.add_column("Enabled", style="red")
                
                for version in dataset.versions:
                    versions_table.add_row(
                        version.name,
                        str(version.file_count),
                        version.formatted_size,
                        version.design_state,
                        "Yes" if version.is_enabled else "No"
                    )
                
                console.print(versions_table)
            
        except NotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] Dataset not found: {uuid}")
            raise typer.Exit(1)
        except AuthenticationError:
            console.print("[bold red]Error:[/bold red] Authentication failed. Please check your API credentials.")
            raise typer.Exit(1)
        except AuthorizationError:
            console.print("[bold red]Error:[/bold red] Authorization failed. You don't have permission to access this dataset.")
            raise typer.Exit(1)
        except ValidationError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid input: {e}")
            raise typer.Exit(1)
        except DataMapAPIError as e:
            console.print(f"[bold red]Error:[/bold red] API error: {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Unexpected error: {e}")
            raise typer.Exit(1)
        finally:
            # Close client if it was created
            if 'client' in locals():
                await client.close()
    
    # Run the async function
    asyncio.run(_info())


@app.command()
def versions(
    uuid: str = typer.Argument(
        ...,
        help="Dataset UUID",
        callback=validate_uuid,
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
    """List all versions of a dataset.
    
    This command retrieves and displays all available versions of a dataset
    with their metadata and file information.
    
    Examples:
        datamap dataset versions 12345678-1234-1234-1234-123456789abc
        datamap dataset versions 12345678-1234-1234-1234-123456789abc --output-format json
    """
    async def _versions():
        try:
            # Get API client
            client = await _get_api_client()
            
            # Show loading message
            with console.status("[bold green]Fetching dataset versions..."):
                # Fetch dataset (which includes versions)
                dataset = await client.get_dataset(uuid)
            
            # Format output
            formatter = OutputFormatter(console)
            
            # Prepare versions data for output
            versions_data = []
            for version in dataset.versions:
                version_info = {
                    "Name": version.name,
                    "UUID": version.id,
                    "Files": version.file_count,
                    "Size": version.formatted_size,
                    "State": version.design_state,
                    "Enabled": "Yes" if version.is_enabled else "No",
                    "Created": version.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "Updated": version.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                versions_data.append(version_info)
            
            # Print versions information
            if output_format == "table" or (output_format is None and get_settings().output_format == "table"):
                # Create rich table
                table = Table(title=f"Dataset Versions: {dataset.name}", show_header=True, header_style="bold magenta")
                table.add_column("Name", style="cyan", no_wrap=True)
                table.add_column("UUID", style="blue")
                table.add_column("Files", style="green")
                table.add_column("Size", style="yellow")
                table.add_column("State", style="magenta")
                table.add_column("Enabled", style="red")
                table.add_column("Created", style="white")
                table.add_column("Updated", style="white")
                
                for version_info in versions_data:
                    table.add_row(
                        version_info["Name"],
                        version_info["UUID"],
                        str(version_info["Files"]),
                        version_info["Size"],
                        version_info["State"],
                        version_info["Enabled"],
                        version_info["Created"],
                        version_info["Updated"]
                    )
                
                console.print(table)
            else:
                # Use formatter for other output formats
                formatter.print_output(versions_data, output_format, color_output)
            
        except NotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] Dataset not found: {uuid}")
            raise typer.Exit(1)
        except AuthenticationError:
            console.print("[bold red]Error:[/bold red] Authentication failed. Please check your API credentials.")
            raise typer.Exit(1)
        except AuthorizationError:
            console.print("[bold red]Error:[/bold red] Authorization failed. You don't have permission to access this dataset.")
            raise typer.Exit(1)
        except ValidationError as e:
            console.print(f"[bold red]Error:[/bold red] Invalid input: {e}")
            raise typer.Exit(1)
        except DataMapAPIError as e:
            console.print(f"[bold red]Error:[/bold red] API error: {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Unexpected error: {e}")
            raise typer.Exit(1)
        finally:
            # Close client if it was created
            if 'client' in locals():
                await client.close()
    
    # Run the async function
    asyncio.run(_versions())


@app.command()
def list(
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
    """List all datasets (placeholder for future implementation).
    
    This command will list all available datasets for the authenticated user.
    
    Examples:
        datamap dataset list
        datamap dataset list --output-format json
    """
    console.print("[yellow]Dataset listing functionality will be implemented in a future version.[/yellow]")
    console.print("For now, use 'datamap dataset info <uuid>' to get information about a specific dataset.")


if __name__ == "__main__":
    app()
