"""
HTTP API client with retry logic and error handling.

Provides:
- Retry logic with exponential backoff
- Timeout handling
- Connection error recovery
- Structured error responses
"""

import time
import requests
from typing import Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import get_logger


class APIClient:
    """
    HTTP client with retry logic and error handling.
    
    Features:
    - Automatic retries on transient failures
    - Exponential backoff
    - Timeout handling
    - Connection pooling
    """
    
    def __init__(
        self,
        base_url: str = "",
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        logger_name: str = "api_client"
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplier (1.0 = 1s, 2s, 4s...)
            logger_name: Name for logger
        """
        self.base_url = base_url
        self.timeout = timeout
        self.logger = get_logger(logger_name)
        
        # Create session with retry strategy
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make GET request with retry logic.
        
        Args:
            url: URL to request (absolute or relative to base_url)
            params: Query parameters
            headers: Request headers
            
        Returns:
            Response data as dict with keys:
            - success: bool
            - data: response data (if successful)
            - error: error message (if failed)
            - status_code: HTTP status code
        """
        full_url = self._build_url(url)
        
        try:
            self.logger.debug(f"GET {full_url}", params=params or {})
            
            response = self.session.get(
                full_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            self.logger.debug(
                f"GET {full_url} succeeded",
                status_code=response.status_code
            )
            
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
            
        except requests.exceptions.Timeout:
            self.logger.error(f"GET {full_url} timed out after {self.timeout}s")
            return {
                "success": False,
                "error": f"Request timed out after {self.timeout} seconds",
                "status_code": None
            }
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"GET {full_url} connection failed", error=str(e))
            return {
                "success": False,
                "error": f"Connection error: {str(e)}",
                "status_code": None
            }
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(
                f"GET {full_url} HTTP error",
                status_code=e.response.status_code,
                error=str(e)
            )
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code
            }
            
        except Exception as e:
            self.logger.error(f"GET {full_url} unexpected error", error=str(e))
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None
            }
    
    def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make POST request with retry logic.
        
        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Request headers
            
        Returns:
            Response data dict (same format as get())
        """
        full_url = self._build_url(url)
        
        try:
            self.logger.debug(f"POST {full_url}")
            
            response = self.session.post(
                full_url,
                data=data,
                json=json,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            self.logger.debug(
                f"POST {full_url} succeeded",
                status_code=response.status_code
            )
            
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
            
        except requests.exceptions.Timeout:
            self.logger.error(f"POST {full_url} timed out")
            return {
                "success": False,
                "error": f"Request timed out after {self.timeout} seconds",
                "status_code": None
            }
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"POST {full_url} HTTP error", status_code=e.response.status_code)
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {str(e)}",
                "status_code": e.response.status_code
            }
            
        except Exception as e:
            self.logger.error(f"POST {full_url} unexpected error", error=str(e))
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "status_code": None
            }
    
    def _build_url(self, url: str) -> str:
        """Build full URL from base_url and relative path."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
        
        return url
    
    def close(self):
        """Close session and cleanup resources."""
        self.session.close()


def create_client(
    base_url: str = "",
    timeout: int = 30,
    max_retries: int = 3
) -> APIClient:
    """
    Create API client instance.
    
    Args:
        base_url: Base URL for API
        timeout: Request timeout
        max_retries: Maximum retries
        
    Returns:
        APIClient instance
    """
    return APIClient(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries
    )
