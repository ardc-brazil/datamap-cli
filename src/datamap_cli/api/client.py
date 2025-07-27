"""DataMap API client implementation."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar
from urllib.parse import urljoin

import httpx
import structlog
from pydantic import ValidationError

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
    ValidationError as APIValidationError,
)
from .models import (
    DataFileDownloadResponse,
    Dataset,
    Version,
)

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class DataMapAPIClient:
    """Async HTTP client for the DataMap API."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://datamap.pcs.usp.br/api/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_id: Optional[str] = None,
        tenancy: Optional[str] = None,
    ):
        """Initialize the API client.
        
        Args:
            api_key: Application API key
            api_secret: Application API secret
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (will be exponential)
            user_id: Optional user ID for requests
            tenancy: Optional tenancy information
        """
        if not api_key or not api_secret:
            raise ConfigurationError("API key and secret are required")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_id = user_id
        self.tenancy = tenancy
        
        # Create HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            headers=self._get_default_headers(),
        )
        
        logger.info(
            "DataMap API client initialized",
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Api-Key": self.api_key,
            "X-Api-Secret": self.api_secret,
        }
        
        if self.user_id:
            headers["X-User-Id"] = self.user_id
        
        if self.tenancy:
            headers["X-Datamap-Tenancies"] = self.tenancy
        
        return headers
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("DataMap API client closed")
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        return urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_body = e.response.text
            
            logger.error(
                "HTTP error occurred",
                status_code=status_code,
                response_body=response_body,
                url=str(e.request.url),
            )
            
            if status_code == 400:
                raise APIValidationError(f"Bad request: {response_body}")
            elif status_code == 401:
                raise AuthenticationError()
            elif status_code == 403:
                raise AuthorizationError()
            elif status_code == 404:
                raise NotFoundError("Resource", "unknown")
            elif status_code == 429:
                raise RateLimitError()
            elif status_code >= 500:
                raise ServerError()
            else:
                raise DataMapAPIError(
                    f"HTTP {status_code}: {response_body}",
                    status_code=status_code,
                    response_body=response_body,
                )
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        model_class: Optional[Type[T]] = None,
    ) -> T:
        """Make an HTTP request with retry logic and response validation."""
        url = self._build_url(endpoint)
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    "Making API request",
                    method=method,
                    url=url,
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                )
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                )
                
                response_data = self._handle_response(response)
                
                logger.debug(
                    "API request successful",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                )
                
                # Validate response with Pydantic model if provided
                if model_class:
                    try:
                        return model_class(**response_data)
                    except ValidationError as e:
                        logger.error(
                            "Response validation failed",
                            model_class=model_class.__name__,
                            errors=e.errors(),
                            response_data=response_data,
                        )
                        raise DataMapAPIError(f"Invalid response format: {e}")
                
                return response_data
                
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                if attempt == self.max_retries:
                    logger.error(
                        "Network error after all retries",
                        error=str(e),
                        url=url,
                    )
                    raise NetworkError(f"Network error: {e}")
                
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    "Network error, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    delay=delay,
                    url=url,
                )
                await asyncio.sleep(delay)
                
            except httpx.TimeoutException as e:
                if attempt == self.max_retries:
                    logger.error(
                        "Request timeout after all retries",
                        error=str(e),
                        url=url,
                    )
                    raise TimeoutError()
                
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(
                    "Request timeout, retrying",
                    attempt=attempt + 1,
                    delay=delay,
                    url=url,
                )
                await asyncio.sleep(delay)
    
    async def get_dataset(self, dataset_id: str) -> Dataset:
        """Get dataset information by ID.
        
        Args:
            dataset_id: Dataset UUID
            
        Returns:
            Dataset object with all metadata and versions
            
        Raises:
            NotFoundError: If dataset is not found
            AuthenticationError: If authentication fails
            DataMapAPIError: For other API errors
        """
        logger.info("Fetching dataset", dataset_id=dataset_id)
        
        try:
            dataset = await self._make_request(
                method="GET",
                endpoint=f"/datasets/{dataset_id}",
                model_class=Dataset,
            )
            
            logger.info(
                "Dataset fetched successfully",
                dataset_id=dataset_id,
                name=dataset.name,
                version_count=dataset.version_count,
            )
            
            return dataset
            
        except NotFoundError:
            raise NotFoundError("Dataset", dataset_id)
    
    async def get_version(
        self, dataset_id: str, version_name: str
    ) -> Version:
        """Get specific version information.
        
        Args:
            dataset_id: Dataset UUID
            version_name: Version name (string, not UUID)
            
        Returns:
            Version object with all files
            
        Raises:
            NotFoundError: If dataset or version is not found
            AuthenticationError: If authentication fails
            DataMapAPIError: For other API errors
        """
        logger.info(
            "Fetching version",
            dataset_id=dataset_id,
            version_name=version_name,
        )
        
        try:
            # Get the raw response first
            response_data = await self._make_request(
                method="GET",
                endpoint=f"/datasets/{dataset_id}/versions/{version_name}",
            )
            
            # Extract the version data from the response
            if isinstance(response_data, dict) and 'version' in response_data:
                version_data = response_data['version']
                # logger.debug(f"Extracted version data: {version_data}")
                
                # Parse the version data
                version = Version(**version_data)
                
                logger.info(
                    "Version fetched successfully",
                    dataset_id=dataset_id,
                    version_name=version_name,
                    file_count=version.file_count,
                )
                
                return version
            else:
                raise DataMapAPIError("Response does not contain version data")
            
        except NotFoundError:
            raise NotFoundError("Version", f"{dataset_id}/{version_name}")
    
    async def get_file_download_url(
        self, dataset_id: str, version_name: str, file_id: str
    ) -> DataFileDownloadResponse:
        """Get download URL for a specific file.
        
        Args:
            dataset_id: Dataset UUID
            version_name: Version name
            file_id: File UUID
            
        Returns:
            DataFileDownloadResponse with download URL
            
        Raises:
            NotFoundError: If dataset, version, or file is not found
            AuthenticationError: If authentication fails
            DataMapAPIError: For other API errors
        """
        logger.info(
            "Getting file download URL",
            dataset_id=dataset_id,
            version_name=version_name,
            file_id=file_id,
        )
        
        try:
            download_response = await self._make_request(
                method="GET",
                endpoint=f"/datasets/{dataset_id}/versions/{version_name}/files/{file_id}",
                model_class=DataFileDownloadResponse,
            )
            
            logger.info(
                "File download URL obtained",
                dataset_id=dataset_id,
                version_name=version_name,
                file_id=file_id,
            )
            
            return download_response
            
        except NotFoundError:
            raise NotFoundError("File", f"{dataset_id}/{version_name}/{file_id}")
    
    async def health_check(self) -> bool:
        """Check if the API is healthy and accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try to make a simple request to check connectivity
            await self._make_request(method="GET", endpoint="/health")
            logger.info("API health check passed")
            return True
        except Exception as e:
            logger.warning("API health check failed", error=str(e))
            return False
