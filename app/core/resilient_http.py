"""
Resilient HTTP client with exponential backoff retry logic.

This module provides a wrapper around httpx for making resilient HTTP requests
to external services, implementing retry with exponential backoff for transient failures.
"""
import logging
import random
import asyncio
from typing import Dict, Any, Optional, Union, Callable
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.core.exceptions import DependencyException

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MIN_WAIT_MS = 100
DEFAULT_MAX_WAIT_MS = 2000


class ResilientHTTPClient:
    """
    HTTP client with built-in resilience patterns.
    
    Features:
    - Retry with exponential backoff
    - Circuit breaking (future enhancement)
    - Timeout handling
    - Consistent error propagation
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        min_wait_ms: int = DEFAULT_MIN_WAIT_MS,
        max_wait_ms: int = DEFAULT_MAX_WAIT_MS,
        timeout: float = 10.0
    ):
        """
        Initialize the resilient HTTP client.
        
        Args:
            base_url: Base URL for all requests (optional)
            max_attempts: Maximum number of retry attempts
            min_wait_ms: Minimum wait time in milliseconds
            max_wait_ms: Maximum wait time in milliseconds
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.max_attempts = max_attempts
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms
        self.timeout = timeout
    
    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=0.1, min=DEFAULT_MIN_WAIT_MS/1000, max=DEFAULT_MAX_WAIT_MS/1000),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.ConnectError, httpx.ReadTimeout, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True
    )
    async def request(
        self,
        method: str,
        url: str,
        service_name: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make a HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            service_name: Name of the service being called (for logging/error reporting)
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            httpx.Response: The HTTP response
            
        Raises:
            DependencyException: If the request fails after all retries
        """
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        # Build full URL if base_url is set
        if self.base_url and not url.startswith(('http://', 'https://')):
            full_url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        else:
            full_url = url
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Making {method} request to {service_name}: {full_url}")
                response = await client.request(method, full_url, **kwargs)
                response.raise_for_status()
                return response
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error from {service_name}: {e.response.status_code} - {e.response.text}")
            raise DependencyException(
                service=service_name,
                message=f"HTTP {e.response.status_code} error: {e.response.text[:100]}",
                details={"status_code": e.response.status_code, "url": full_url}
            )
        except (httpx.RequestError, asyncio.TimeoutError) as e:
            logger.warning(f"Request error to {service_name}: {str(e)}")
            raise DependencyException(
                service=service_name,
                message=f"Request failed: {str(e)}",
                details={"url": full_url}
            )
    
    async def get(self, url: str, service_name: str, **kwargs) -> httpx.Response:
        """Perform a GET request with retry logic."""
        return await self.request("GET", url, service_name, **kwargs)
    
    async def post(self, url: str, service_name: str, **kwargs) -> httpx.Response:
        """Perform a POST request with retry logic."""
        return await self.request("POST", url, service_name, **kwargs)
    
    async def put(self, url: str, service_name: str, **kwargs) -> httpx.Response:
        """Perform a PUT request with retry logic."""
        return await self.request("PUT", url, service_name, **kwargs)
    
    async def patch(self, url: str, service_name: str, **kwargs) -> httpx.Response:
        """Perform a PATCH request with retry logic."""
        return await self.request("PATCH", url, service_name, **kwargs)
    
    async def delete(self, url: str, service_name: str, **kwargs) -> httpx.Response:
        """Perform a DELETE request with retry logic."""
        return await self.request("DELETE", url, service_name, **kwargs)


# Singleton client instances for major services
task_service_client = ResilientHTTPClient()
user_profile_service_client = ResilientHTTPClient()


async def get_json_response(response: httpx.Response) -> Dict[str, Any]:
    """
    Extract JSON data from response with error handling.
    
    Args:
        response: HTTP response object
        
    Returns:
        Dict containing JSON response data
        
    Raises:
        DependencyException: If response cannot be parsed as JSON
    """
    try:
        return response.json()
    except ValueError as e:
        service = response.request.url.host
        logger.error(f"Failed to parse JSON from {service}: {str(e)}")
        raise DependencyException(
            service=service,
            message="Invalid JSON response",
            details={"status_code": response.status_code, "content": response.text[:100]}
        )
