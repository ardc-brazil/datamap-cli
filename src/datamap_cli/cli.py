"""Main CLI entry point for DataMap CLI."""

import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__
from .config.settings import get_settings, validate_configuration
from .utils.logging import setup_logging, get_logger
from .utils.cli_context import CLIContext, get_effective_log_level
from .utils.help import (
    show_main_help,
    show_command_examples,
    show_troubleshooting_guide,
    show_output_format_guide,
    show_configuration_guide,
    show_scripting_guide,
)

# Create the main Typer app
app = typer.Typer(
    name="datamap",
    help="DataMap CLI - A command-line interface for the DataMap platform API",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Create console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        version_text = Text()
        version_text.append("DataMap CLI", style="bold blue")
        version_text.append(" version ", style="white")
        version_text.append(__version__, style="bold green")
        
        # Add additional version info
        version_text.append("\n\n", style="white")
        version_text.append("Python ", style="dim")
        version_text.append(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", style="cyan")
        version_text.append(" • ", style="dim")
        version_text.append("Rich ", style="dim")
        version_text.append("for beautiful terminal output", style="cyan")
        
        panel = Panel(
            version_text,
            title="[bold]Version Information[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
        raise typer.Exit()


def validate_config_callback(value: bool) -> None:
    """Validate configuration and display results."""
    if value:
        console.print("\n[bold blue]Validating Configuration...[/bold blue]")
        
        issues = validate_configuration()
        
        if not issues:
            console.print("[bold green]✓[/bold green] Configuration is valid!")
            
            # Show configuration summary
            try:
                settings = get_settings()
                summary = settings.get_credential_summary()
                
                console.print("\n[bold]Configuration Summary:[/bold]")
                for key, value in summary.items():
                    console.print(f"  [cyan]{key}:[/cyan] {value}")
                    
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] Could not load configuration: {e}")
        else:
            console.print("[bold red]✗[/bold red] Configuration issues found:")
            for issue in issues:
                console.print(f"  [red]•[/red] {issue}")
            
            console.print("\n[yellow]Please check your configuration and try again.[/yellow]")
            console.print("Use [cyan]datamap config help[/cyan] for configuration guidance.")
        
        raise typer.Exit()


def help_topic_callback(value: str) -> None:
    """Callback for help topic option."""
    if value is None:
        return
    
    show_help_topic(value)
    raise typer.Exit()


def show_help_topic(topic: str) -> None:
    """Show help for a specific topic."""
    topic = topic.lower()
    
    if topic == "examples":
        show_command_examples()
    elif topic == "troubleshooting":
        show_troubleshooting_guide()
    elif topic == "formats":
        show_output_format_guide()
    elif topic == "config":
        show_configuration_guide()
    elif topic == "scripting":
        show_scripting_guide()
    else:
        console.print(f"[red]Unknown help topic: {topic}[/red]")
        console.print("Available topics: examples, troubleshooting, formats, config, scripting")
        raise typer.Exit(1)


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
        "-V",
        help="Enable verbose output (DEBUG level logging)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress output except errors",
    ),
    config: str = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        metavar="PATH",
    ),
    output_format: str = typer.Option(
        None,
        "--output-format",
        "-f",
        help="Output format (table, json, yaml, csv)",
        case_sensitive=False,
    ),
    color_output: bool = typer.Option(
        None,
        "--color/--no-color",
        help="Enable/disable colored output",
    ),
    validate_config: bool = typer.Option(
        None,
        "--validate-config",
        callback=validate_config_callback,
        help="Validate configuration and exit",
        is_eager=True,
    ),
    help_topic: str = typer.Option(
        None,
        "--help-topic",
        help="Show help for specific topic (examples, troubleshooting, formats, config, scripting)",
        callback=help_topic_callback,
        is_eager=True,
    ),
) -> None:
    """DataMap CLI - Interact with the DataMap platform API from the command line.
    
    [bold blue]Overview[/bold blue]
    
    This tool provides a comprehensive command-line interface for the DataMap platform,
    allowing you to retrieve dataset information, list versions, download files, and
    manage API interactions efficiently.
    
    [bold blue]Quick Start[/bold blue]
    
    1. [cyan]Configure your API credentials:[/cyan]
       export DATAMAP_API_KEY="your-api-key"
       export DATAMAP_API_SECRET="your-api-secret"
    
    2. [cyan]List available datasets:[/cyan]
       datamap dataset list
    
    3. [cyan]Get dataset information:[/cyan]
       datamap dataset info <dataset-uuid>
    
    4. [cyan]List dataset versions:[/cyan]
       datamap version files <dataset-uuid> <version-name>
    
    5. [cyan]Download files:[/cyan]
       datamap download file <dataset-uuid> <version-name> <file-uuid>
    
    [bold blue]Global Options[/bold blue]
    
    • [cyan]--verbose, -V[/cyan]: Enable detailed logging and output
    • [cyan]--quiet, -q[/cyan]: Suppress normal output, show only errors
    • [cyan]--config, -c[/cyan]: Specify custom configuration file
    • [cyan]--output-format, -f[/cyan]: Choose output format (table/json/yaml/csv)
    • [cyan]--color/--no-color[/cyan]: Control colored output
    • [cyan]--validate-config[/cyan]: Validate configuration and exit
    
    [bold blue]Command Groups[/bold blue]
    
    • [cyan]dataset[/cyan]: Dataset management and information
    • [cyan]version[/cyan]: Version and file listing
    • [cyan]download[/cyan]: File and version downloads
    • [cyan]config[/cyan]: Configuration management
    • [cyan]file[/cyan]: File-specific operations
    
    [bold blue]Examples[/bold blue]
    
    [dim]# List all datasets in JSON format[/dim]
    datamap dataset list --output-format json
    
    [dim]# Get dataset info with verbose logging[/dim]
    datamap dataset info 123e4567-e89b-12d3-a456-426614174000 --verbose
    
    [dim]# Download a specific file with progress[/dim]
    datamap download file 123e4567-e89b-12d3-a456-426614174000 v1.0 file-uuid
    
    [dim]# Use custom configuration file[/dim]
    datamap --config ~/.datamap/config.yaml dataset list
    
    [bold blue]Configuration[/bold blue]
    
    Configuration can be provided via:
    • Environment variables (DATAMAP_*)
    • Configuration files (.datamap.yaml, ~/.datamap/config.yaml, etc.)
    • Command line options
    
    Use [cyan]datamap config help[/cyan] for detailed configuration guidance.
    
    [bold blue]Getting Help[/bold blue]
    
    • [cyan]datamap --help[/cyan]: Show this help message
    • [cyan]datamap <command> --help[/cyan]: Show command-specific help
    • [cyan]datamap config help[/cyan]: Configuration help and examples
    """
    # Validate output format if provided
    if output_format is not None:
        if output_format.lower() not in ["table", "json", "yaml", "csv"]:
            console.print(f"[red]Error:[/red] Invalid output format '{output_format}'. "
                         f"Valid formats: table, json, yaml, csv")
            raise typer.Exit(1)
    
    # Set up logging
    log_level = get_effective_log_level()
    
    # Use CLI context to resolve color_output
    from .utils.cli_context import resolve_color_output
    resolved_color_output = resolve_color_output(color_output)
    
    setup_logging(
        log_level=log_level,
        color_output=resolved_color_output
    )
    

    
    # Log command execution
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        # Validate configuration if not already done
        if not validate_config:
            issues = validate_configuration()
            if issues:
                console.print("[bold red]Configuration Error:[/bold red]")
                for issue in issues:
                    console.print(f"  [red]•[/red] {issue}")
                console.print("\n[yellow]Use 'datamap --validate-config' to check your configuration.[/yellow]")
                raise typer.Exit(1)
        
        logger.info(
            "Command started",
            command="main",
            args={
                "verbose": verbose,
                "quiet": quiet,
                "config": config,
                "output_format": output_format,
                "color_output": color_output,
            }
        )
        
    except Exception as e:
        logger.error("Command failed", error=str(e))
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


# Import command modules
from .commands import config, dataset, version, download, file

# Add command groups with enhanced help
app.add_typer(
    config.app,
    name="config",
    help="Configuration management commands",
    rich_help_panel="Configuration"
)
app.add_typer(
    dataset.app,
    name="dataset",
    help="Dataset-related commands",
    rich_help_panel="Data Management"
)
app.add_typer(
    version.app,
    name="version",
    help="Version-related commands",
    rich_help_panel="Data Management"
)
app.add_typer(
    download.app,
    name="download",
    help="Download commands",
    rich_help_panel="Data Transfer"
)
app.add_typer(
    file.app,
    name="file",
    help="File-related commands",
    rich_help_panel="Data Management"
)


if __name__ == "__main__":
    app()
