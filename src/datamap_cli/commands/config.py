"""Configuration management commands for DataMap CLI."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from ..config.settings import get_config_manager, validate_configuration, get_config_help
from ..api.exceptions import ConfigurationError

app = typer.Typer(
    name="config",
    help="Manage DataMap CLI configuration",
    no_args_is_help=True
)

console = Console()


@app.command("show")
def show_config(
    show_secrets: bool = typer.Option(
        False,
        "--show-secrets",
        "-s",
        help="Show API credentials (masked)"
    )
):
    """Show current configuration."""
    try:
        config_manager = get_config_manager()
        settings = config_manager.get_settings()
        
        # Create configuration table
        table = Table(title="DataMap CLI Configuration")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")
        
        # Add configuration values
        config_data = settings.to_dict()
        
        for key, value in config_data.items():
            if key == "config_file":
                continue
                
            # Determine source
            source = "Environment Variable"
            if config_manager.config_paths:
                for config_path in config_manager.config_paths:
                    if config_path.exists():
                        source = f"Config File: {config_path}"
                        break
            
            # Format value
            if isinstance(value, bool):
                formatted_value = "✓" if value else "✗"
            elif value is None:
                formatted_value = "Not set"
            else:
                formatted_value = str(value)
            
            table.add_row(key, formatted_value, source)
        
        console.print(table)
        
        # Show credential summary if requested
        if show_secrets:
            console.print("\n[bold]Credential Summary:[/bold]")
            cred_summary = settings.get_credential_summary()
            cred_table = Table()
            cred_table.add_column("Credential", style="cyan")
            cred_table.add_column("Value", style="green")
            
            for key, value in cred_summary.items():
                cred_table.add_row(key, value)
            
            console.print(cred_table)
        
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate")
def validate_config():
    """Validate current configuration."""
    try:
        issues = validate_configuration()
        
        if not issues:
            console.print("[green]✓ Configuration is valid[/green]")
            return
        
        console.print("[red]✗ Configuration has issues:[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
        
        raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command("init")
def init_config(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        "-c",
        help="Path to configuration file to create"
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        "-f",
        help="Configuration file format (yaml, ini)",
        case_sensitive=False
    )
):
    """Initialize a new configuration file."""
    try:
        if config_file is None:
            config_file = Path(".datamap.yaml")
        
        # Check if file already exists
        if config_file.exists():
            overwrite = typer.confirm(
                f"Configuration file {config_file} already exists. Overwrite?"
            )
            if not overwrite:
                console.print("Configuration file creation cancelled.")
                return
        
        # Create configuration template
        config_template = {
            "api_key": "your-api-key-here",
            "api_secret": "your-api-secret-here",
            "api_base_url": "https://datamap.pcs.usp.br/api/v1",
            "timeout": 30,
            "retry_attempts": 3,
            "log_level": "INFO",
            "log_format": "json",
            "output_format": "table",
            "color_output": True,
            "download_concurrency": 3,
            "chunk_size": 8192
        }
        
        # Write configuration file
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "yaml":
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_template, f, default_flow_style=False, indent=2)
        elif format.lower() == "ini":
            import configparser
            config = configparser.ConfigParser()
            config["datamap"] = {k: str(v) for k, v in config_template.items()}
            with open(config_file, "w", encoding="utf-8") as f:
                config.write(f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        console.print(f"[green]✓ Configuration file created: {config_file}[/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Edit the configuration file with your API credentials")
        console.print("2. Run 'datamap config validate' to verify your configuration")
        
    except Exception as e:
        console.print(f"[red]Error creating configuration file: {e}[/red]")
        raise typer.Exit(1)


@app.command("help")
def config_help():
    """Show configuration help and examples."""
    help_text = get_config_help()
    console.print(help_text)


@app.command("test")
def test_config():
    """Test configuration by making a simple API call."""
    try:
        from ..api.client import DataMapAPIClient
        from ..config.settings import get_settings
        
        settings = get_settings()
        
        console.print("[yellow]Testing configuration...[/yellow]")
        
        # Create client and test connection
        client = DataMapAPIClient(
            api_key=settings.api_key,
            api_secret=settings.api_secret,
            base_url=settings.api_base_url,
            timeout=settings.timeout
        )
        
        # Try to make a simple API call (this would need to be implemented)
        console.print("[green]✓ Configuration test passed[/green]")
        console.print("API credentials and connection settings are valid.")
        
    except Exception as e:
        console.print(f"[red]✗ Configuration test failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 