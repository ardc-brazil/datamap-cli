"""DataMap API client module."""

from .client import DataMapAPIClient
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataMapAPIError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    APIResponse,
    DataFile,
    DataFileDownloadResponse,
    Dataset,
    PaginatedResponse,
    Version,
)

__all__ = [
    # Client
    "DataMapAPIClient",
    # Exceptions
    "DataMapAPIError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
    # Models
    "Dataset",
    "Version",
    "DataFile",
    "DataFileDownloadResponse",
    "APIResponse",
    "PaginatedResponse",
]
