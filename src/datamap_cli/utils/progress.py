"""Progress indicators and utilities for DataMap CLI."""

import time
from typing import Optional, Callable, Any
from pathlib import Path

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    DownloadColumn,
)
from rich.live import Live
from rich.text import Text
from rich.panel import Panel

from ..config.settings import get_settings
from .cli_context import should_show_progress


class ProgressManager:
    """Manages progress indicators and spinners."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize progress manager.
        
        Args:
            console: Rich console instance (creates new one if not provided)
        """
        self.console = console or Console()
        self.settings = get_settings()
        self._current_spinner: Optional[Any] = None
        self._current_progress: Optional[Progress] = None
    
    def start_spinner(self, text: str, style: str = "blue") -> None:
        """Start a spinner for API calls or long-running operations.
        
        Args:
            text: Text to display with spinner
            style: Spinner style
        """
        if not should_show_progress():
            return
            
        if self._current_spinner:
            self.stop_spinner()
        
        self._current_spinner = self.console.status(
            Text(text, style=style),
            spinner="dots",
        )
        self._current_spinner.start()
    
    def stop_spinner(self) -> None:
        """Stop the current spinner."""
        if self._current_spinner:
            self._current_spinner.stop()
            self._current_spinner = None
    
    def update_spinner_text(self, text: str) -> None:
        """Update the spinner text.
        
        Args:
            text: New text to display
        """
        if self._current_spinner:
            self._current_spinner.update(Text(text))
    
    def create_download_progress(self) -> Progress:
        """Create a progress bar for downloads.
        
        Returns:
            Configured progress bar
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )
        return progress
    
    def create_simple_progress(self, description: str) -> Progress:
        """Create a simple progress bar.
        
        Args:
            description: Progress description
            
        Returns:
            Configured progress bar
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            transient=False,
        )
        return progress
    
    def show_message(self, message: str, style: str = "green") -> None:
        """Show a message in the console.
        
        Args:
            message: Message to display
            style: Message style
        """
        if not should_show_progress():
            return
        self.console.print(message, style=style)
    
    def show_error(self, message: str) -> None:
        """Show an error message.
        
        Args:
            message: Error message to display
        """
        self.console.print(f"❌ {message}", style="red")
    
    def show_success(self, message: str) -> None:
        """Show a success message.
        
        Args:
            message: Success message to display
        """
        if not should_show_progress():
            return
        self.console.print(f"✅ {message}", style="green")
    
    def show_warning(self, message: str) -> None:
        """Show a warning message.
        
        Args:
            message: Warning message to display
        """
        if not should_show_progress():
            return
        self.console.print(f"⚠️  {message}", style="yellow")


class DownloadProgressTracker:
    """Tracks download progress for multiple files."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize download progress tracker.
        
        Args:
            console: Rich console instance
        """
        self.console = console or Console()
        self.progress_manager = ProgressManager(console)
        self.overall_progress: Optional[Progress] = None
        self.file_progress: Optional[Progress] = None
        self.total_files = 0
        self.completed_files = 0
        self.total_bytes = 0
        self.downloaded_bytes = 0
    
    def start_overall_progress(self, total_files: int, total_bytes: int) -> None:
        """Start overall download progress tracking.
        
        Args:
            total_files: Total number of files to download
            total_bytes: Total bytes to download
        """
        self.total_files = total_files
        self.total_bytes = total_bytes
        self.completed_files = 0
        self.downloaded_bytes = 0
        
        if not should_show_progress():
            return
            
        self.overall_progress = self.progress_manager.create_simple_progress(
            f"Downloading {total_files} files"
        )
        self.overall_progress.start()
    
    def start_file_progress(self, filename: str, file_size: int) -> None:
        """Start progress tracking for a single file.
        
        Args:
            filename: Name of the file being downloaded
            file_size: Size of the file in bytes
        """
        if not should_show_progress():
            return
            
        if self.file_progress:
            self.file_progress.stop()
        
        self.file_progress = self.progress_manager.create_download_progress()
        self.file_progress.start()
        
        self.current_task = self.file_progress.add_task(
            f"Downloading {filename}",
            total=file_size,
        )
    
    def update_file_progress(self, downloaded_bytes: int) -> None:
        """Update progress for the current file.
        
        Args:
            downloaded_bytes: Number of bytes downloaded for current file
        """
        if not should_show_progress():
            return
            
        if self.file_progress and hasattr(self, 'current_task'):
            self.file_progress.update(self.current_task, completed=downloaded_bytes)
    
    def complete_file(self, file_size: int) -> None:
        """Mark a file as completed.
        
        Args:
            file_size: Size of the completed file
        """
        self.completed_files += 1
        self.downloaded_bytes += file_size
        
        if self.file_progress:
            self.file_progress.stop()
            self.file_progress = None
        
        if self.overall_progress:
            progress_percent = (self.completed_files / self.total_files) * 100
            self.overall_progress.update(
                self.overall_progress.task_ids[0],
                completed=self.completed_files,
                total=self.total_files,
            )
    
    def stop(self) -> None:
        """Stop all progress tracking."""
        if self.file_progress:
            self.file_progress.stop()
        if self.overall_progress:
            self.overall_progress.stop()


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


def format_download_speed(speed_bytes_per_sec: float) -> str:
    """Format download speed in human-readable format.
    
    Args:
        speed_bytes_per_sec: Speed in bytes per second
        
    Returns:
        Formatted speed string
    """
    return f"{format_file_size(int(speed_bytes_per_sec))}/s"


def show_download_summary(
    console: Console,
    total_files: int,
    total_bytes: int,
    download_time: float,
    success_count: int,
    error_count: int,
) -> None:
    """Show download summary.
    
    Args:
        console: Rich console instance
        total_files: Total number of files
        total_bytes: Total bytes downloaded
        download_time: Total download time in seconds
        success_count: Number of successful downloads
        error_count: Number of failed downloads
    """
    avg_speed = total_bytes / download_time if download_time > 0 else 0
    
    summary = Panel(
        f"[bold]Download Summary[/bold]\n\n"
        f"📁 Files: {success_count}/{total_files} completed\n"
        f"📊 Size: {format_file_size(total_bytes)}\n"
        f"⏱️  Time: {download_time:.1f}s\n"
        f"🚀 Speed: {format_download_speed(avg_speed)}\n"
        f"✅ Success: {success_count}\n"
        f"❌ Errors: {error_count}",
        title="Download Complete",
        border_style="green" if error_count == 0 else "yellow",
    )
    
    console.print(summary)


def with_progress_spinner(
    description: str,
    console: Optional[Console] = None,
) -> Callable:
    """Decorator to add progress spinner to functions.
    
    Args:
        description: Spinner description
        console: Rich console instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            progress_manager = ProgressManager(console)
            try:
                progress_manager.start_spinner(description)
                result = func(*args, **kwargs)
                progress_manager.stop_spinner()
                return result
            except Exception as e:
                progress_manager.stop_spinner()
                progress_manager.show_error(f"Error: {str(e)}")
                raise
        return wrapper
    return decorator
