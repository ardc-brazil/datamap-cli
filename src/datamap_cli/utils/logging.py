"""Structured logging configuration for DataMap CLI."""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from ..config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    color_output: Optional[bool] = None,
) -> None:
    """Set up structured logging with the specified configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        color_output: Whether to enable colored output
    """
    # Get settings if not provided
    settings = get_settings()
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format
    color_output = color_output if color_output is not None else settings.color_output
    
    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper())
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Text format with rich console for colored output
        if color_output:
            console = Console(stderr=True)
            processors.append(
                structlog.dev.ConsoleRenderer(
                    colors=True,
                )
            )
        else:
            processors.append(
                structlog.dev.ConsoleRenderer(
                    colors=False,
                )
            )
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
        handlers=[RichHandler(console=Console(stderr=True))] if color_output else None,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


def log_request_response(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    response_time: Optional[float] = None,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log HTTP request/response information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        status_code: Response status code
        response_time: Response time in seconds
        error: Error message if request failed
        **kwargs: Additional context to log
    """
    log_data = {
        "event": "http_request",
        "method": method,
        "url": url,
        **kwargs,
    }
    
    if status_code is not None:
        log_data["status_code"] = status_code
    
    if response_time is not None:
        log_data["response_time"] = response_time
    
    if error is not None:
        log_data["error"] = error
        logger.error(**log_data)
    else:
        logger.info(**log_data)


def log_download_progress(
    logger: structlog.stdlib.BoundLogger,
    file_uuid: str,
    filename: str,
    downloaded_bytes: int,
    total_bytes: int,
    speed: Optional[float] = None,
    **kwargs: Any,
) -> None:
    """Log download progress information.
    
    Args:
        logger: Logger instance
        file_uuid: File UUID being downloaded
        filename: File name
        downloaded_bytes: Number of bytes downloaded
        total_bytes: Total file size in bytes
        speed: Download speed in bytes per second
        **kwargs: Additional context to log
    """
    progress_percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
    
    log_data = {
        "event": "download_progress",
        "file_uuid": file_uuid,
        "filename": filename,
        "downloaded_bytes": downloaded_bytes,
        "total_bytes": total_bytes,
        "progress_percent": round(progress_percent, 2),
        **kwargs,
    }
    
    if speed is not None:
        log_data["speed_bytes_per_sec"] = speed
    
    logger.debug(**log_data)


def log_configuration(
    logger: structlog.stdlib.BoundLogger,
    settings: Any,
    include_sensitive: bool = False,
) -> None:
    """Log configuration information.
    
    Args:
        logger: Logger instance
        settings: Settings object
        include_sensitive: Whether to include sensitive data
    """
    if include_sensitive:
        config_data = settings.model_dump()
    else:
        config_data = settings.to_dict()
    
    logger.info(
        "Configuration loaded",
        config=config_data,
    )


def log_command_execution(
    logger: structlog.stdlib.BoundLogger,
    command: str,
    args: Dict[str, Any],
    execution_time: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Log command execution information.
    
    Args:
        logger: Logger instance
        command: Command name
        args: Command arguments
        execution_time: Command execution time in seconds
        success: Whether command executed successfully
        error: Error message if command failed
    """
    log_data = {
        "event": "command_execution",
        "command": command,
        "args": args,
        "success": success,
    }
    
    if execution_time is not None:
        log_data["execution_time"] = execution_time
    
    if error is not None:
        log_data["error"] = error
        logger.error(**log_data)
    else:
        logger.info(**log_data)
