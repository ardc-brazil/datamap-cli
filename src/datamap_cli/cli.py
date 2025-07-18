"""Main CLI entry point for DataMap CLI."""

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__

# Create the main Typer app
app = typer.Typer(
    name="datamap",
    help="DataMap CLI - A command-line interface for the DataMap platform API",
    add_completion=False,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        console.print(Panel(f"[bold blue]DataMap CLI[/bold blue] version [bold green]{__version__}[/bold green]"))
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit",
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose output",
    ),
    config: str = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        "-f",
        help="Output format (table, json, yaml, csv)",
    ),
) -> None:
    """DataMap CLI - Interact with the DataMap platform API from the command line.
    
    This tool provides commands to:
    - Retrieve dataset information
    - List dataset versions
    - Download files and versions
    - Manage API interactions
    """
    # Global configuration will be handled here
    pass


# Import command modules (will be implemented in subsequent tasks)
# from .commands import dataset, version, download

# Add command groups
# app.add_typer(dataset.app, name="dataset", help="Dataset-related commands")
# app.add_typer(version.app, name="version", help="Version-related commands")
# app.add_typer(download.app, name="download", help="Download commands")


if __name__ == "__main__":
    app()
