"""Custom exceptions for the DataMap API client."""

from typing import Optional


class DataMapAPIError(Exception):
    """Base exception for all DataMap API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class AuthenticationError(DataMapAPIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed. Please check your API key and secret."):
        super().__init__(message, status_code=401)


class AuthorizationError(DataMapAPIError):
    """Raised when the user is not authorized to access a resource."""
    
    def __init__(self, message: str = "You are not authorized to access this resource."):
        super().__init__(message, status_code=403)


class NotFoundError(DataMapAPIError):
    """Raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID '{resource_id}' not found."
        super().__init__(message, status_code=404)


class ValidationError(DataMapAPIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str = "Invalid request data provided."):
        super().__init__(message, status_code=400)


class RateLimitError(DataMapAPIError):
    """Raised when the API rate limit is exceeded."""
    
    def __init__(self, message: str = "API rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)


class ServerError(DataMapAPIError):
    """Raised when the server encounters an error."""
    
    def __init__(self, message: str = "Server error occurred. Please try again later."):
        super().__init__(message, status_code=500)


class NetworkError(DataMapAPIError):
    """Raised when network connectivity issues occur."""
    
    def __init__(self, message: str = "Network error occurred. Please check your connection."):
        super().__init__(message)


class TimeoutError(DataMapAPIError):
    """Raised when a request times out."""
    
    def __init__(self, message: str = "Request timed out. Please try again."):
        super().__init__(message)


class ConfigurationError(DataMapAPIError):
    """Raised when there are configuration issues."""
    
    def __init__(self, message: str = "Configuration error. Please check your settings."):
        super().__init__(message)
