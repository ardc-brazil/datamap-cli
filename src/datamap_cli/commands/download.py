"""Download commands for DataMap CLI."""

import asyncio
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.table import Table

from ..api.client import DataMapAPIClient
from ..api.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DataMapAPIError,
    NotFoundError,
    ValidationError,
)
from ..api.models import DataFile, Version
from ..config.settings import get_settings
from ..utils.progress import ProgressManager, DownloadProgressTracker, format_file_size, show_download_summary

# Create the download command group
app = typer.Typer(
    name="download",
    help="Download commands for files and versions"
)

# Create console for rich output
console = Console()

# Create a separate console for downloads to avoid conflicts with other commands
download_console = Console()




def check_disk_space(path: Path, required_bytes: int) -> bool:
    """Check if there's enough disk space available.
    
    Args:
        path: Path to check disk space for
        required_bytes: Required bytes
        
    Returns:
        True if enough space available, False otherwise
    """
    try:
        # Get disk usage statistics
        statvfs = os.statvfs(path)
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        
        return free_bytes >= required_bytes
    except OSError:
        # If we can't check disk space, assume it's available
        return True


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


def validate_output_path(output_path: str) -> Path:
    """Validate and create output path.
    
    Args:
        output_path: Output path string
        
    Returns:
        Path object
        
    Raises:
        typer.BadParameter: If path is invalid
    """
    try:
        path = Path(output_path).resolve()
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        return path
    except Exception as e:
        raise typer.BadParameter(f"Invalid output path: {e}")


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


async def _download_file_with_progress(
    url: str,
    output_path: Path,
    filename: str,
    file_size: int,
    progress_manager: ProgressManager,
    resume: bool = False,
    verify_checksum: bool = True,
    shared_progress: Optional[Progress] = None,
    task_id: Optional[int] = None,
) -> bool:
    """Download a file with progress tracking and resume capability.
    
    Args:
        url: Download URL
        output_path: Output file path
        filename: File name for display
        file_size: Expected file size
        progress_manager: Progress manager instance
        resume: Whether to resume download
        shared_progress: Shared progress instance for concurrent downloads
        task_id: Task ID in shared progress
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        # Check if file exists for resume
        start_byte = 0
        if resume and output_path.exists():
            start_byte = output_path.stat().st_size
            if start_byte >= file_size:
                progress_manager.show_warning(f"File {filename} already exists and is complete")
                return True
        
        # Stop any existing spinner before starting progress
        progress_manager.stop_spinner()
        
        # Use shared progress or create new one
        if shared_progress is not None and task_id is not None:
            progress = shared_progress
            task = task_id
        else:
            # Create progress bar for single file download
            progress = Progress(
                SpinnerColumn(),
                TextColumn(f"[bold blue]Downloading {filename}"),
                BarColumn(),
                TaskProgressColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=download_console,
            )
            progress.start()
            task = progress.add_task("", total=file_size, completed=start_byte)
        
        # Prepare headers for resume
        headers = {}
        if resume and start_byte > 0:
            headers["Range"] = f"bytes={start_byte}-"
        
        # Download file
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()
                
                # Open file for writing (append if resuming)
                mode = "ab" if resume and start_byte > 0 else "wb"
                with open(output_path, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        start_byte += len(chunk)
                        progress.update(task, completed=start_byte)
        
        # Only stop progress if we created it (single file download)
        if shared_progress is None:
            progress.stop()
        
        # Verify checksum if requested
        if verify_checksum:
            progress_manager.start_spinner(f"Verifying checksum for {filename}...")
            # TODO: Implement actual checksum verification when API provides checksums
            # For now, just verify file size
            actual_size = output_path.stat().st_size
            if actual_size != file_size:
                progress_manager.show_error(f"File size mismatch for {filename}: expected {file_size}, got {actual_size}")
                return False
            progress_manager.stop_spinner()
        
        progress_manager.show_success(f"Downloaded {filename}")
        return True
        
    except PermissionError as e:
        progress_manager.show_error(f"Permission denied for {filename}: {str(e)}")
        return False
    except OSError as e:
        if e.errno == 28:  # No space left on device
            progress_manager.show_error(f"Disk full while downloading {filename}")
        else:
            progress_manager.show_error(f"File system error for {filename}: {str(e)}")
        return False
    except Exception as e:
        progress_manager.show_error(f"Failed to download {filename}: {str(e)}")
        return False


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
def file(
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
    output_path: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (defaults to file name in current directory)",
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume interrupted download",
    ),
    verify_checksum: bool = typer.Option(
        True,
        "--verify-checksum/--no-verify-checksum",
        help="Verify file checksum after download",
    ),
) -> None:
    """Download a single file from a dataset version.
    
    This command downloads a specific file from a dataset version. The file
    will be saved to the specified output path or to the current directory
    using the original file name.
    
    Examples:
        datamap download file 12345678-1234-1234-1234-123456789abc v1.0 87654321-4321-4321-4321-cba987654321
        datamap download file 12345678-1234-1234-1234-123456789abc v1.0 87654321-4321-4321-4321-cba987654321 --output ./my_file.csv
        datamap download file 12345678-1234-1234-1234-123456789abc v1.0 87654321-4321-4321-4321-cba987654321 --resume
    """
    
    async def _download_file():
        progress_manager = ProgressManager(console)
        
        try:
            # Get API client
            api_client = await _get_api_client()
            
            # Get file information
            progress_manager.start_spinner("Getting file information...")
            file_info = await _get_file_info(api_client, dataset_id, version_name, file_id)
            progress_manager.stop_spinner()
            
            # Determine output path
            if output_path:
                output_file = validate_output_path(output_path)
            else:
                output_file = Path.cwd() / file_info.name
            
            # Check disk space
            if not check_disk_space(output_file.parent, file_info.size_bytes):
                progress_manager.show_error(
                    f"Insufficient disk space. Need {file_info.formatted_size} but not enough space available."
                )
                raise typer.Exit(1)
            
            # Show file information
            table = Table(title=f"File Information: {file_info.name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("File ID", file_info.id)
            table.add_row("Name", file_info.name)
            table.add_row("Size", file_info.formatted_size)
            table.add_row("Format", file_info.format or "Unknown")
            table.add_row("Created", file_info.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("Output Path", str(output_file))
            
            console.print(table)
            
            # Confirm download
            if not typer.confirm(f"Download {file_info.name} ({file_info.formatted_size})?"):
                console.print("Download cancelled")
                return
            
            # Get download URL
            progress_manager.start_spinner("Getting download URL...")
            download_response = await api_client.get_file_download_url(
                dataset_id, version_name, file_id
            )
            progress_manager.stop_spinner()
            
            # Download file
            success = await _download_file_with_progress(
                download_response.url,
                output_file,
                file_info.name,
                file_info.size_bytes,
                progress_manager,
                resume=resume,
                verify_checksum=verify_checksum,
            )
            
            if success:
                # Verify file size
                if output_file.exists():
                    actual_size = output_file.stat().st_size
                    if actual_size != file_info.size_bytes:
                        progress_manager.show_warning(
                            f"File size mismatch: expected {file_info.formatted_size}, "
                            f"got {format_file_size(actual_size)}"
                        )
                    else:
                        progress_manager.show_success(
                            f"File downloaded successfully: {output_file}"
                        )
                else:
                    progress_manager.show_error("Download completed but file not found")
            
        except Exception as e:
            progress_manager.stop_spinner()
            progress_manager.show_error(f"Download failed: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_download_file())


@app.command()
def version(
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
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory (defaults to version name in current directory)",
    ),
    max_concurrent: int = typer.Option(
        3,
        "--max-concurrent",
        "-c",
        help="Maximum concurrent downloads",
        min=1,
        max=10,
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume interrupted downloads",
    ),
    verify_checksum: bool = typer.Option(
        True,
        "--verify-checksum/--no-verify-checksum",
        help="Verify file checksums after download",
    ),
) -> None:
    """Download all files from a dataset version.
    
    This command downloads all files from a specific dataset version. Files
    will be saved to the specified output directory or to a directory named
    after the version in the current directory.
    
    Examples:
        datamap download version 12345678-1234-1234-1234-123456789abc v1.0
        datamap download version 12345678-1234-1234-1234-123456789abc v1.0 --output-dir ./my_data
        datamap download version 12345678-1234-1234-1234-123456789abc v1.0 --max-concurrent 5 --resume
    """
    
    async def _download_version():
        progress_manager = ProgressManager(console)
        
        try:
            # Get API client
            api_client = await _get_api_client()
            
            # Get version information
            progress_manager.start_spinner("Getting version information...")
            version_info = await api_client.get_version(dataset_id, version_name)
            progress_manager.stop_spinner()
            
            if not version_info.files_in:
                progress_manager.show_warning(f"No files found in version {version_name}")
                return
            
            # Determine output directory
            if output_dir:
                output_directory = validate_output_path(output_dir)
            else:
                output_directory = Path.cwd() / version_name
            
            # Create output directory
            output_directory.mkdir(parents=True, exist_ok=True)
            
            # Check total disk space needed
            total_size_needed = sum(file.size_bytes for file in version_info.files_in)
            if not check_disk_space(output_directory, total_size_needed):
                progress_manager.show_error(
                    f"Insufficient disk space. Need {version_info.formatted_size} but not enough space available."
                )
                raise typer.Exit(1)
            
            # Show version information
            table = Table(title=f"Version Information: {version_name}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Version ID", version_info.id)
            table.add_row("Name", version_info.name)
            table.add_row("File Count", str(version_info.file_count))
            table.add_row("Total Size", version_info.formatted_size)
            table.add_row("Design State", version_info.design_state)
            table.add_row("Output Directory", str(output_directory))
            
            console.print(table)
            
            # Show files to be downloaded
            files_table = Table(title="Files to Download")
            files_table.add_column("File ID", style="cyan")
            files_table.add_column("Name", style="white")
            files_table.add_column("Size", style="green")
            files_table.add_column("Format", style="yellow")
            
            for file_info in version_info.files_in:
                files_table.add_row(
                    file_info.id,
                    file_info.name,
                    file_info.formatted_size,
                    file_info.format or "Unknown"
                )
            
            console.print(files_table)
            
            # Confirm download
            if not typer.confirm(
                f"Download {version_info.file_count} files ({version_info.formatted_size})?"
            ):
                console.print("Download cancelled")
                return
            
            # Download files
            success_count = 0
            error_count = 0
            total_bytes = 0
            
            # Create semaphore for concurrent downloads
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # Stop any existing spinner before starting progress
            progress_manager.stop_spinner()
            
            # Create shared progress bar for all downloads
            shared_progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Downloading files"),
                BarColumn(),
                TaskProgressColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=download_console,
            )
            
            # Add tasks for all files
            task_ids = {}
            for file_info in version_info.files_in:
                task_id = shared_progress.add_task(
                    f"Downloading {file_info.name}",
                    total=file_info.size_bytes,
                    completed=0
                )
                task_ids[file_info.id] = task_id
            
            shared_progress.start()
            
            async def download_single_file(file_info: DataFile) -> bool:
                """Download a single file with semaphore control."""
                async with semaphore:
                    try:
                        # Get download URL
                        download_response = await api_client.get_file_download_url(
                            dataset_id, version_name, file_info.id
                        )
                        
                        # Determine output path
                        output_file = output_directory / file_info.name
                        
                        # Download file with shared progress
                        success = await _download_file_with_progress(
                            download_response.url,
                            output_file,
                            file_info.name,
                            file_info.size_bytes,
                            progress_manager,
                            resume=resume,
                            verify_checksum=verify_checksum,
                            shared_progress=shared_progress,
                            task_id=task_ids[file_info.id],
                        )
                        
                        return success
                        
                    except Exception as e:
                        progress_manager.show_error(f"Failed to download {file_info.name}: {str(e)}")
                        return False
            
            # Download all files concurrently
            tasks = [
                download_single_file(file_info) 
                for file_info in version_info.files_in
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            shared_progress.stop()
            
            # Count results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    progress_manager.show_error(f"Download failed: {str(result)}")
                elif result:
                    success_count += 1
                    total_bytes += version_info.files_in[i].size_bytes
                else:
                    error_count += 1
            
            # Show summary
            show_download_summary(
                console,
                version_info.file_count,
                total_bytes,
                0.0,  # TODO: Track actual download time
                success_count,
                error_count,
            )
            
            if error_count > 0:
                raise typer.Exit(1)
            
        except Exception as e:
            progress_manager.stop_spinner()
            progress_manager.show_error(f"Download failed: {str(e)}")
            raise typer.Exit(1)
    
    asyncio.run(_download_version())
