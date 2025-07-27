"""CLI context management for DataMap CLI."""

import contextvars
from typing import Optional

# Context variables for global CLI options
_global_output_format = contextvars.ContextVar('output_format', default=None)
_global_color_output = contextvars.ContextVar('color_output', default=None)
_global_verbose = contextvars.ContextVar('verbose', default=False)
_global_quiet = contextvars.ContextVar('quiet', default=False)


class CLIContext:
    """Context manager for CLI global options."""
    
    def __init__(
        self,
        output_format: Optional[str] = None,
        color_output: Optional[bool] = None,
        verbose: bool = False,
        quiet: bool = False,
    ):
        """Initialize CLI context.
        
        Args:
            output_format: Global output format override
            color_output: Global color output override
            verbose: Enable verbose mode
            quiet: Enable quiet mode
        """
        self.output_format = output_format
        self.color_output = color_output
        self.verbose = verbose
        self.quiet = quiet
        self._tokens = []
    
    def __enter__(self):
        """Set context variables."""
        if self.output_format is not None:
            token = _global_output_format.set(self.output_format)
            self._tokens.append((_global_output_format, token))
        
        if self.color_output is not None:
            token = _global_color_output.set(self.color_output)
            self._tokens.append((_global_color_output, token))
        
        token = _global_verbose.set(self.verbose)
        self._tokens.append((_global_verbose, token))
        
        token = _global_quiet.set(self.quiet)
        self._tokens.append((_global_quiet, token))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset context variables."""
        for var, token in self._tokens:
            var.reset(token)


def get_global_output_format() -> Optional[str]:
    """Get global output format setting."""
    return _global_output_format.get()


def get_global_color_output() -> Optional[bool]:
    """Get global color output setting."""
    return _global_color_output.get()


def get_global_verbose() -> bool:
    """Get global verbose setting."""
    return _global_verbose.get()


def get_global_quiet() -> bool:
    """Get global quiet setting."""
    return _global_quiet.get()


def resolve_output_format(command_format: Optional[str] = None) -> str:
    """Resolve output format with precedence: command > global > default.
    
    Args:
        command_format: Command-specific output format
        
    Returns:
        Resolved output format
    """
    if command_format is not None:
        return command_format
    
    global_format = get_global_output_format()
    if global_format is not None:
        return global_format
    
    # Default from settings
    from ..config.settings import get_settings
    return get_settings().output_format


def resolve_color_output(command_color: Optional[bool] = None) -> bool:
    """Resolve color output with precedence: command > global > default.
    
    Args:
        command_color: Command-specific color setting
        
    Returns:
        Resolved color output setting
    """
    if command_color is not None:
        return command_color
    
    global_color = get_global_color_output()
    if global_color is not None:
        return global_color
    
    # Default from settings
    from ..config.settings import get_settings
    return get_settings().color_output


def should_show_progress() -> bool:
    """Determine if progress indicators should be shown.
    
    Returns:
        True if progress should be shown
    """
    return not get_global_quiet()


def get_effective_log_level() -> str:
    """Get effective log level based on global options and configuration.
    
    Returns:
        Effective log level
    """
    if get_global_verbose():
        return "DEBUG"
    elif get_global_quiet():
        return "ERROR"
    else:
        # Use configuration file log level as default
        from ..config.settings import get_settings
        return get_settings().log_level 