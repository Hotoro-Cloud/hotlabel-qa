"""
Resilient HTTP client for cross-service communication.

This module provides a client for making HTTP requests to other services
with built-in resilience patterns like retry with exponential backoff and
circuit breakers.
"""
import logging
import httpx
from typing import Dict, Any, Optional, List, Union

from app.core.resilience import resilient_http_call, with_retry, with_circuit_breaker
from app.core.config import settings

logger = logging.getLogger(__name__)

class ServiceClient:
    """
    Resilient client for communicating with external services.
    
    Provides methods for making HTTP requests to other services with
    built-in resilience patterns.
    """
    
    def __init__(self, service_name: str, base_url: str):
        """
        Initialize the service client.
        
        Args:
            service_name: Name of the service (used for circuit breaker naming)
            base_url: Base URL for the service
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get(
        self, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> httpx.Response:
        """
        Make a resilient GET request to the service.
        
        Args:
            path: Path to append to the base URL
            params: Query parameters for the request
            headers: HTTP headers for the request
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response: The HTTP response
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        circuit_name = f"{self.service_name}_get_{path.split('/')[0]}"
        
        try:
            return await resilient_http_call(
                client=self.client,
                method="GET",
                url=url,
                circuit_name=circuit_name,
                timeout=timeout,
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to make GET request to {url}: {str(e)}")
            raise
    
    async def post(
        self, 
        path: str, 
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> httpx.Response:
        """
        Make a resilient POST request to the service.
        
        Args:
            path: Path to append to the base URL
            json: JSON data for the request body
            data: Form data for the request body
            params: Query parameters for the request
            headers: HTTP headers for the request
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response: The HTTP response
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        circuit_name = f"{self.service_name}_post_{path.split('/')[0]}"
        
        try:
            return await resilient_http_call(
                client=self.client,
                method="POST",
                url=url,
                circuit_name=circuit_name,
                timeout=timeout,
                json=json,
                data=data,
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to make POST request to {url}: {str(e)}")
            raise
    
    async def put(
        self, 
        path: str, 
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> httpx.Response:
        """
        Make a resilient PUT request to the service.
        
        Args:
            path: Path to append to the base URL
            json: JSON data for the request body
            data: Form data for the request body
            params: Query parameters for the request
            headers: HTTP headers for the request
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response: The HTTP response
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        circuit_name = f"{self.service_name}_put_{path.split('/')[0]}"
        
        try:
            return await resilient_http_call(
                client=self.client,
                method="PUT",
                url=url,
                circuit_name=circuit_name,
                timeout=timeout,
                json=json,
                data=data,
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to make PUT request to {url}: {str(e)}")
            raise
    
    async def delete(
        self, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> httpx.Response:
        """
        Make a resilient DELETE request to the service.
        
        Args:
            path: Path to append to the base URL
            params: Query parameters for the request
            headers: HTTP headers for the request
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response: The HTTP response
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        circuit_name = f"{self.service_name}_delete_{path.split('/')[0]}"
        
        try:
            return await resilient_http_call(
                client=self.client,
                method="DELETE",
                url=url,
                circuit_name=circuit_name,
                timeout=timeout,
                params=params,
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to make DELETE request to {url}: {str(e)}")
            raise


# Service client instances
task_service_client = ServiceClient("task_service", settings.TASK_SERVICE_URL)
user_service_client = ServiceClient("user_service", settings.USER_SERVICE_URL)


# API functions for task service
async def get_task_details(task_id: str) -> Dict[str, Any]:
    """
    Get details for a task from the Task service.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Dict: Task details
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    response = await task_service_client.get(f"tasks/{task_id}")
    return response.json()


async def update_task_quality_score(task_id: str, quality_score: float) -> Dict[str, Any]:
    """
    Update the quality score for a task.
    
    Args:
        task_id: ID of the task
        quality_score: Quality score to set
        
    Returns:
        Dict: Updated task details
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    response = await task_service_client.put(
        f"tasks/{task_id}/quality",
        json={"quality_score": quality_score}
    )
    return response.json()


# API functions for user service
async def get_user_profile(session_id: str) -> Dict[str, Any]:
    """
    Get user profile information from the User service.
    
    Args:
        session_id: ID of the user session
        
    Returns:
        Dict: User profile data
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    response = await user_service_client.get(f"sessions/{session_id}")
    return response.json()


async def update_user_expertise(session_id: str, task_quality: float, task_type: str) -> Dict[str, Any]:
    """
    Update user expertise based on task performance.
    
    Args:
        session_id: ID of the user session
        task_quality: Quality score for the task
        task_type: Type of task completed
        
    Returns:
        Dict: Updated user profile
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    response = await user_service_client.post(
        f"sessions/{session_id}/task-completed",
        json={
            "task_type": task_type,
            "quality_score": task_quality
        }
    )
    return response.json()


# Cleanup function for application lifecycle
async def close_service_clients():
    """Close all service clients when the application shuts down."""
    await task_service_client.close()
    await user_service_client.close()
