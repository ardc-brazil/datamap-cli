"""Comprehensive help system for DataMap CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax

console = Console()


def show_main_help() -> None:
    """Show comprehensive main help."""
    help_text = """
[bold blue]DataMap CLI - Command Line Interface[/bold blue]

A powerful command-line tool for interacting with the DataMap platform API.

[bold green]Quick Start Guide[/bold green]

1. [cyan]Set up your API credentials:[/cyan]
   export DATAMAP_API_KEY="your-api-key"
   export DATAMAP_API_SECRET="your-api-secret"

2. [cyan]Verify your configuration:[/cyan]
   datamap --validate-config

3. [cyan]Explore available datasets:[/cyan]
   datamap dataset list

4. [cyan]Get detailed dataset information:[/cyan]
   datamap dataset info <dataset-uuid>

5. [cyan]Download files:[/cyan]
   datamap download file <dataset-uuid> <version> <file-uuid>

[bold green]Command Groups[/bold green]

[cyan]Dataset Management[/cyan]
  • dataset list     - List all available datasets
  • dataset info     - Get detailed dataset information
  • dataset versions - List dataset versions

[cyan]Version Management[/cyan]
  • version files    - List files in a specific version

[cyan]Download Operations[/cyan]
  • download file    - Download a specific file
  • download version - Download all files in a version

[cyan]Configuration[/cyan]
  • config show     - Display current configuration
  • config validate - Validate configuration
  • config init     - Initialize configuration file
  • config help     - Configuration help

[cyan]File Operations[/cyan]
  • file info       - Get file information

[bold green]Global Options[/bold green]

[cyan]Output Control[/cyan]
  --output-format, -f    Choose output format (table/json/yaml/csv)
  --color/--no-color     Enable/disable colored output
  --verbose, -V          Enable detailed logging
  --quiet, -q            Suppress normal output

[cyan]Configuration[/cyan]
  --config, -c           Specify configuration file
  --validate-config      Validate configuration and exit

[bold green]Examples[/bold green]

[dim]# List datasets in JSON format[/dim]
datamap dataset list --output-format json

[dim]# Get dataset info with verbose logging[/dim]
datamap dataset info 123e4567-e89b-12d3-a456-426614174000 --verbose

[dim]# Download file with progress tracking[/dim]
datamap download file 123e4567-e89b-12d3-a456-426614174000 v1.0 file-uuid

[dim]# Use custom configuration[/dim]
datamap --config ~/.datamap/config.yaml dataset list

[dim]# Quiet mode for scripting[/dim]
datamap --quiet --output-format json dataset list

[bold green]Getting Help[/bold green]

• [cyan]datamap --help[/cyan]                    - This help message
• [cyan]datamap <command> --help[/cyan]         - Command-specific help
• [cyan]datamap config help[/cyan]              - Configuration help
• [cyan]datamap --validate-config[/cyan]        - Validate your setup

[bold green]Troubleshooting[/bold green]

[cyan]Common Issues:[/cyan]
• [yellow]Authentication errors:[/yellow] Check your API credentials
• [yellow]Configuration issues:[/yellow] Run 'datamap --validate-config'
• [yellow]Network problems:[/yellow] Verify your internet connection
• [yellow]Permission errors:[/yellow] Check file/directory permissions

[cyan]For more help:[/cyan]
• Check the configuration guide: datamap config help
• Validate your setup: datamap --validate-config
• Enable verbose logging: datamap --verbose <command>
"""

    panel = Panel(
        help_text,
        title="[bold]DataMap CLI Help[/bold]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def show_command_examples() -> None:
    """Show comprehensive command examples."""
    examples = {
        "dataset": {
            "list": "datamap dataset list",
            "info": "datamap dataset info 123e4567-e89b-12d3-a456-426614174000",
            "versions": "datamap dataset versions 123e4567-e89b-12d3-a456-426614174000",
        },
        "version": {
            "files": "datamap version files 123e4567-e89b-12d3-a456-426614174000 v1.0",
        },
        "download": {
            "file": "datamap download file 123e4567-e89b-12d3-a456-426614174000 v1.0 file-uuid",
            "version": "datamap download version 123e4567-e89b-12d3-a456-426614174000 v1.0",
        },
        "config": {
            "show": "datamap config show",
            "validate": "datamap config validate",
            "init": "datamap config init --config-file ~/.datamap/config.yaml",
            "help": "datamap config help",
        },
        "file": {
            "info": "datamap file info 123e4567-e89b-12d3-a456-426614174000 v1.0 file-uuid",
        },
    }
    
    table = Table(title="[bold]Command Examples[/bold]")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Example", style="green")
    table.add_column("Description", style="yellow")
    
    for group, commands in examples.items():
        for cmd, example in commands.items():
            full_cmd = f"{group} {cmd}"
            description = get_command_description(full_cmd)
            table.add_row(full_cmd, example, description)
    
    console.print(table)


def get_command_description(command: str) -> str:
    """Get description for a command."""
    descriptions = {
        "dataset list": "List all available datasets",
        "dataset info": "Get detailed information about a dataset",
        "dataset versions": "List all versions of a dataset",
        "version files": "List files in a specific version",
        "download file": "Download a specific file",
        "download version": "Download all files in a version",
        "config show": "Display current configuration",
        "config validate": "Validate configuration settings",
        "config init": "Initialize configuration file",
        "config help": "Show configuration help",
        "file info": "Get information about a specific file",
    }
    return descriptions.get(command, "No description available")


def show_troubleshooting_guide() -> None:
    """Show troubleshooting guide."""
    troubleshooting = """
[bold red]Troubleshooting Guide[/bold red]

[bold yellow]Authentication Issues[/bold yellow]

[cyan]Problem:[/cyan] "Authentication failed" or "Invalid credentials"
[cyan]Solutions:[/cyan]
1. Verify your API credentials are correct
2. Check environment variables: echo $DATAMAP_API_KEY
3. Validate configuration: datamap --validate-config
4. Ensure credentials are not expired

[bold yellow]Configuration Issues[/bold yellow]

[cyan]Problem:[/cyan] "Configuration error" or missing settings
[cyan]Solutions:[/cyan]
1. Run: datamap --validate-config
2. Check configuration file: datamap config show
3. Initialize new config: datamap config init
4. Verify environment variables are set

[bold yellow]Network Issues[/bold yellow]

[cyan]Problem:[/cyan] "Connection timeout" or "Network error"
[cyan]Solutions:[/cyan]
1. Check internet connection
2. Verify API base URL is accessible
3. Check firewall/proxy settings
4. Try with verbose logging: datamap --verbose <command>

[bold yellow]File System Issues[/bold yellow]

[cyan]Problem:[/cyan] "Permission denied" or "Disk space full"
[cyan]Solutions:[/cyan]
1. Check file/directory permissions
2. Verify sufficient disk space
3. Ensure write access to download directory
4. Try different output directory

[bold yellow]Output Format Issues[/bold yellow]

[cyan]Problem:[/cyan] "Invalid output format" or formatting errors
[cyan]Solutions:[/cyan]
1. Use valid formats: table, json, yaml, csv
2. Check format case sensitivity
3. Verify data structure compatibility

[bold yellow]Performance Issues[/bold yellow]

[cyan]Problem:[/cyan] Slow downloads or timeouts
[cyan]Solutions:[/cyan]
1. Reduce concurrent downloads: --download-concurrency 1
2. Increase timeout: --timeout 60
3. Check network bandwidth
4. Use quiet mode for faster output: --quiet

[bold green]Getting More Help[/bold green]

• Enable verbose logging: datamap --verbose <command>
• Check configuration: datamap config show
• Validate setup: datamap --validate-config
• View configuration help: datamap config help
"""

    panel = Panel(
        troubleshooting,
        title="[bold]Troubleshooting Guide[/bold]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)


def show_output_format_guide() -> None:
    """Show output format guide."""
    formats = {
        "table": {
            "description": "Rich formatted tables (default)",
            "best_for": "Interactive use, human reading",
            "example": "datamap dataset list --output-format table"
        },
        "json": {
            "description": "Structured JSON output",
            "best_for": "Scripting, API integration",
            "example": "datamap dataset list --output-format json"
        },
        "yaml": {
            "description": "YAML formatted output",
            "best_for": "Configuration files, documentation",
            "example": "datamap dataset list --output-format yaml"
        },
        "csv": {
            "description": "Comma-separated values",
            "best_for": "Spreadsheets, data analysis",
            "example": "datamap dataset list --output-format csv"
        }
    }
    
    table = Table(title="[bold]Output Format Guide[/bold]")
    table.add_column("Format", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Best For", style="yellow")
    table.add_column("Example", style="blue")
    
    for fmt, info in formats.items():
        table.add_row(
            fmt,
            info["description"],
            info["best_for"],
            info["example"]
        )
    
    console.print(table)
    
    console.print("\n[bold]Usage Tips:[/bold]")
    console.print("• Use [cyan]--output-format[/cyan] or [cyan]-f[/cyan] to specify format")
    console.print("• Formats are case-insensitive")
    console.print("• JSON/YAML are best for scripting")
    console.print("• CSV is ideal for spreadsheet import")
    console.print("• Table format provides the best visual experience")


def show_configuration_guide() -> None:
    """Show configuration setup guide."""
    config_guide = """
[bold blue]Configuration Setup Guide[/bold blue]

[bold green]Method 1: Environment Variables (Recommended)[/bold green]

Set these environment variables in your shell:

[cyan]bash/zsh:[/cyan]
export DATAMAP_API_KEY="your-api-key-here"
export DATAMAP_API_SECRET="your-api-secret-here"

[cyan]Windows (PowerShell):[/cyan]
$env:DATAMAP_API_KEY="your-api-key-here"
$env:DATAMAP_API_SECRET="your-api-secret-here"

[bold green]Method 2: Configuration File[/bold green]

1. [cyan]Initialize configuration file:[/cyan]
   datamap config init --config-file ~/.datamap/config.yaml

2. [cyan]Edit the file with your credentials:[/cyan]
   nano ~/.datamap/config.yaml

3. [cyan]Validate your configuration:[/cyan]
   datamap config validate

[bold green]Method 3: Command Line Options[/bold green]

Use --config to specify a custom configuration file:
datamap --config /path/to/config.yaml dataset list

[bold green]Configuration Precedence[/bold green]

1. Command line options (highest priority)
2. Environment variables
3. Configuration files
4. Default values (lowest priority)

[bold green]Configuration File Locations[/bold green]

• [cyan]Current directory:[/cyan] .datamap.yaml, datamap.yaml
• [cyan]User home:[/cyan] ~/.datamap/config.yaml, ~/.datamaprc
• [cyan]System-wide:[/cyan] /etc/datamap/config.yaml

[bold green]Required Settings[/bold green]

• [cyan]DATAMAP_API_KEY[/cyan]: Your DataMap API key
• [cyan]DATAMAP_API_SECRET[/cyan]: Your DataMap API secret

[bold green]Optional Settings[/bold green]

• [cyan]DATAMAP_API_BASE_URL[/cyan]: API base URL (default: https://datamap.pcs.usp.br/api/v1)
• [cyan]DATAMAP_TIMEOUT[/cyan]: Request timeout in seconds (default: 30)
• [cyan]DATAMAP_OUTPUT_FORMAT[/cyan]: Output format (default: table)
• [cyan]DATAMAP_COLOR_OUTPUT[/cyan]: Enable colored output (default: true)

[bold green]Validation[/bold green]

Always validate your configuration:
datamap --validate-config

This will check:
• API credentials are set
• API URL is valid
• All settings are within valid ranges
"""

    panel = Panel(
        config_guide,
        title="[bold]Configuration Guide[/bold]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def show_scripting_guide() -> None:
    """Show scripting and automation guide."""
    scripting_guide = """
[bold blue]Scripting and Automation Guide[/bold blue]

[bold green]Basic Scripting[/bold green]

[cyan]Bash script example:[/cyan]
```bash
#!/bin/bash
# Get dataset list in JSON format
datamap --quiet --output-format json dataset list > datasets.json

# Process each dataset
for uuid in $(jq -r '.[].uuid' datasets.json); do
    echo "Processing dataset: $uuid"
    datamap --quiet dataset info "$uuid"
done
```

[cyan]Python script example:[/cyan]
```python
import json
import subprocess

# Get datasets
result = subprocess.run([
    'datamap', '--quiet', '--output-format', 'json', 'dataset', 'list'
], capture_output=True, text=True)

datasets = json.loads(result.stdout)
for dataset in datasets:
    print(f"Dataset: {dataset['name']} ({dataset['uuid']})")
```

[bold green]Output Formats for Scripting[/bold green]

[cyan]JSON (Recommended for scripting):[/cyan]
• Structured data
• Easy to parse
• Consistent format
• Example: datamap --output-format json dataset list

[cyan]CSV (For spreadsheet integration):[/cyan]
• Tabular data
• Excel/Google Sheets compatible
• Example: datamap --output-format csv dataset list > datasets.csv

[cyan]YAML (For configuration):[/cyan]
• Human readable
• Configuration files
• Example: datamap --output-format yaml dataset info <uuid> > info.yaml

[bold green]Quiet Mode[/bold green]

Use --quiet for clean output in scripts:
```bash
# No progress bars or extra output
datamap --quiet --output-format json dataset list
```

[bold green]Error Handling[/bold green]

Check exit codes in scripts:
```bash
if datamap --quiet dataset info "$uuid"; then
    echo "Success"
else
    echo "Error: $?"
    exit 1
fi
```

[bold green]Batch Operations[/bold green]

[cyan]Download multiple files:[/cyan]
```bash
# Get file list
files=$(datamap --quiet --output-format json version files "$dataset_uuid" "$version")

# Download each file
echo "$files" | jq -r '.[].uuid' | while read file_uuid; do
    datamap download file "$dataset_uuid" "$version" "$file_uuid"
done
```

[bold green]Configuration for Scripts[/bold green]

• Use environment variables for credentials
• Set DATAMAP_OUTPUT_FORMAT=json for consistent parsing
• Use DATAMAP_COLOR_OUTPUT=false for clean output
• Set appropriate timeouts for batch operations

[bold green]Best Practices[/bold green]

1. [cyan]Always use --quiet in scripts[/cyan]
2. [cyan]Use JSON format for data processing[/cyan]
3. [cyan]Check exit codes for error handling[/cyan]
4. [cyan]Set appropriate timeouts for batch operations[/cyan]
5. [cyan]Use environment variables for credentials[/cyan]
6. [cyan]Validate configuration before running scripts[/cyan]
"""

    panel = Panel(
        scripting_guide,
        title="[bold]Scripting Guide[/bold]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel) 