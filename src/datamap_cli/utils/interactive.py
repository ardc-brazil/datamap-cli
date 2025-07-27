"""Interactive utilities for DataMap CLI."""

from typing import Optional, List
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .cli_context import should_show_progress

console = Console()


def confirm_action(
    message: str,
    default: bool = False,
    force: bool = False,
) -> bool:
    """Confirm an action with the user.
    
    Args:
        message: Confirmation message
        default: Default answer if user just presses Enter
        force: Skip confirmation if True
        
    Returns:
        True if confirmed, False otherwise
    """
    if force:
        return True
    
    if not should_show_progress():
        # In quiet mode, use default
        return default
    
    return typer.confirm(message, default=default)


def confirm_download(
    file_count: int,
    total_size: int,
    output_path: Path,
    force: bool = False,
) -> bool:
    """Confirm a download operation.
    
    Args:
        file_count: Number of files to download
        total_size: Total size in bytes
        output_path: Output path
        force: Skip confirmation if True
        
    Returns:
        True if confirmed, False otherwise
    """
    if force:
        return True
    
    if not should_show_progress():
        return True
    
    # Format size
    from .progress import format_file_size
    size_str = format_file_size(total_size)
    
    # Create confirmation message
    message = f"""
[bold yellow]Download Confirmation[/bold yellow]

📁 Files to download: {file_count}
📊 Total size: {size_str}
📂 Output location: {output_path}

Do you want to proceed with the download?
"""
    
    panel = Panel(
        message,
        title="[bold]Confirm Download[/bold]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)
    
    return typer.confirm("Proceed with download?", default=True)


def confirm_overwrite(
    file_path: Path,
    force: bool = False,
) -> bool:
    """Confirm overwriting an existing file.
    
    Args:
        file_path: Path to the file that would be overwritten
        force: Skip confirmation if True
        
    Returns:
        True if confirmed, False otherwise
    """
    if force:
        return True
    
    if not should_show_progress():
        return True
    
    if not file_path.exists():
        return True
    
    # Get file info
    stat = file_path.stat()
    from .progress import format_file_size
    size_str = format_file_size(stat.st_size)
    
    message = f"""
[bold red]File Already Exists[/bold red]

📄 File: {file_path}
📊 Size: {size_str}
📅 Modified: {stat.st_mtime}

This file will be overwritten. Do you want to continue?
"""
    
    panel = Panel(
        message,
        title="[bold]Confirm Overwrite[/bold]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)
    
    return typer.confirm("Overwrite existing file?", default=False)


def confirm_large_download(
    file_size: int,
    threshold_mb: int = 100,
    force: bool = False,
) -> bool:
    """Confirm downloading a large file.
    
    Args:
        file_size: File size in bytes
        threshold_mb: Size threshold in MB to trigger confirmation
        force: Skip confirmation if True
        
    Returns:
        True if confirmed, False otherwise
    """
    if force:
        return True
    
    if not should_show_progress():
        return True
    
    size_mb = file_size / (1024 * 1024)
    if size_mb < threshold_mb:
        return True
    
    from .progress import format_file_size
    size_str = format_file_size(file_size)
    
    message = f"""
[bold yellow]Large File Download[/bold yellow]

📊 File size: {size_str} ({size_mb:.1f} MB)
⚠️  This is a large file that may take significant time to download.

Do you want to proceed with the download?
"""
    
    panel = Panel(
        message,
        title="[bold]Large File Warning[/bold]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)
    
    return typer.confirm("Proceed with large file download?", default=True)


def confirm_disk_space(
    required_bytes: int,
    available_bytes: int,
    force: bool = False,
) -> bool:
    """Confirm if user wants to proceed with insufficient disk space.
    
    Args:
        required_bytes: Required bytes
        available_bytes: Available bytes
        force: Skip confirmation if True
        
    Returns:
        True if confirmed, False otherwise
    """
    if force:
        return True
    
    if not should_show_progress():
        return True
    
    if available_bytes >= required_bytes:
        return True
    
    from .progress import format_file_size
    required_str = format_file_size(required_bytes)
    available_str = format_file_size(available_bytes)
    shortfall_str = format_file_size(required_bytes - available_bytes)
    
    message = f"""
[bold red]Insufficient Disk Space[/bold red]

📊 Required: {required_str}
💾 Available: {available_str}
❌ Shortfall: {shortfall_str}

There is not enough disk space for this operation.
Do you want to proceed anyway? (This may fail)
"""
    
    panel = Panel(
        message,
        title="[bold]Disk Space Warning[/bold]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(panel)
    
    return typer.confirm("Proceed despite insufficient disk space?", default=False)


def show_download_preview(
    files: List[dict],
    total_size: int,
    output_path: Path,
) -> None:
    """Show a preview of what will be downloaded.
    
    Args:
        files: List of file information dictionaries
        total_size: Total size in bytes
        output_path: Output path
    """
    if not should_show_progress():
        return
    
    from .progress import format_file_size
    size_str = format_file_size(total_size)
    
    # Create preview table
    table = Table(title="[bold]Download Preview[/bold]")
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Size", style="green", justify="right")
    table.add_column("Type", style="yellow")
    
    for file_info in files:
        name = file_info.get("name", "Unknown")
        size = format_file_size(file_info.get("size", 0))
        mime_type = file_info.get("mime_type", "Unknown")
        
        table.add_row(name, size, mime_type)
    
    console.print(table)
    
    # Show summary
    summary = f"""
[bold]Download Summary[/bold]
📁 Files: {len(files)}
📊 Total size: {size_str}
📂 Output: {output_path}
"""
    
    console.print(summary)


def prompt_for_credentials() -> tuple[str, str]:
    """Prompt user for API credentials.
    
    Returns:
        Tuple of (api_key, api_secret)
    """
    if not should_show_progress():
        raise ValueError("Cannot prompt for credentials in quiet mode")
    
    console.print("[bold blue]DataMap API Credentials[/bold blue]")
    console.print("Please enter your DataMap API credentials:")
    
    api_key = typer.prompt("API Key", hide_input=True)
    api_secret = typer.prompt("API Secret", hide_input=True)
    
    return api_key, api_secret


def prompt_for_output_path(
    default_path: Path,
    message: str = "Enter output path",
) -> Path:
    """Prompt user for output path.
    
    Args:
        default_path: Default path to suggest
        message: Prompt message
        
    Returns:
        Selected output path
    """
    if not should_show_progress():
        return default_path
    
    path_str = typer.prompt(
        message,
        default=str(default_path),
        type=str
    )
    
    return Path(path_str)


def show_interactive_menu(
    title: str,
    options: List[tuple[str, str]],
    default: Optional[int] = None,
) -> int:
    """Show an interactive menu.
    
    Args:
        title: Menu title
        options: List of (value, description) tuples
        default: Default selection index
        
    Returns:
        Selected option index
    """
    if not should_show_progress():
        return default or 0
    
    console.print(f"\n[bold blue]{title}[/bold blue]")
    
    for i, (value, description) in enumerate(options):
        marker = "→" if i == default else " "
        console.print(f"{marker} {i + 1}. {description}")
    
    while True:
        try:
            choice = typer.prompt(
                f"Select option (1-{len(options)})",
                default=default + 1 if default is not None else 1,
                type=int
            )
            
            if 1 <= choice <= len(options):
                return choice - 1
            
            console.print(f"[red]Please enter a number between 1 and {len(options)}[/red]")
            
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")


def show_progress_summary(
    operation: str,
    total_items: int,
    completed_items: int,
    failed_items: int,
    total_time: float,
) -> None:
    """Show a summary of operation progress.
    
    Args:
        operation: Operation name
        total_items: Total number of items
        completed_items: Number of completed items
        failed_items: Number of failed items
        total_time: Total time in seconds
    """
    if not should_show_progress():
        return
    
    success_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    
    summary = f"""
[bold green]Operation Complete[/bold green]

🔧 Operation: {operation}
✅ Completed: {completed_items}/{total_items} ({success_rate:.1f}%)
❌ Failed: {failed_items}
⏱️  Time: {total_time:.1f}s
"""
    
    panel = Panel(
        summary,
        title="[bold]Summary[/bold]",
        border_style="green" if failed_items == 0 else "yellow",
        padding=(1, 2)
    )
    console.print(panel) 