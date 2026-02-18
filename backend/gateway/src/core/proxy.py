import httpx
import logging
from fastapi import Request, Response, HTTPException
from typing import Optional, Dict
from src.core.config import settings

logger = logging.getLogger(__name__)

class ServiceProxy:
    """Proxy for forwarding requests to microservices with timeout and retry logic"""
    
    def __init__(self):
        self.timeout = httpx.Timeout(
            timeout=settings.REQUEST_TIMEOUT,
            connect=settings.CONNECT_TIMEOUT
        )
        self.services = {
            "auth": settings.AUTH_SERVICE_URL,
            "user": settings.USER_SERVICE_URL,
            "recipe": settings.RECIPE_SERVICE_URL,
            "workout": settings.WORKOUT_SERVICE_URL,
            "forum": settings.FORUM_SERVICE_URL,
            "analytics": settings.ANALYTICS_SERVICE_URL,
        }
    
    async def forward_request(
        self,
        service_name: str,
        path: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        body: Optional[bytes] = None,
        params: Optional[Dict] = None,
    ) -> Response:
        
        if service_name not in self.services:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown service: {service_name}"
            )
        
        service_url = self.services[service_name]
        url = f"{service_url}{path}"
        
        filtered_headers = self._filter_headers(headers or {})
        
        logger.info(f"Proxying {method} request to {service_name}: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=filtered_headers,
                    content=body,
                    params=params,
                    follow_redirects=False
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                # Tworzymy obiekt Response ręcznie, aby poprawnie obsłużyć nagłówki
                proxy_response = Response(
                    content=response.content,
                    status_code=response.status_code,
                    media_type=response.headers.get("content-type")
                )
                
                excluded_headers = {"content-length", "content-type", "transfer-encoding", "connection", "host"}
                
                for key, value in response.headers.multi_items():
                    if key.lower() not in excluded_headers:
                        proxy_response.headers.append(key, value)
                        if key.lower() == "set-cookie":
                            logger.info(f"Forwarding Set-Cookie: {value}")

                return proxy_response
                
        except httpx.TimeoutException:
            logger.error(f"Timeout while connecting to {service_name} service")
            raise HTTPException(
                status_code=504,
                detail=f"Gateway timeout: {service_name} service did not respond in time"
            )
        except httpx.ConnectError:
            logger.error(f"Cannot connect to {service_name} service at {service_url}")
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: Cannot connect to {service_name} service"
            )
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while calling {service_name}: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Bad gateway: Error communicating with {service_name} service"
            )
        except Exception as e:
            logger.error(f"Unexpected error while calling {service_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error while proxying to {service_name}"
            )
    
    def _filter_headers(self, headers: Dict) -> Dict:
        """Filter out headers that shouldn't be forwarded"""
        excluded_headers = {
            "host",
            "content-length",
            "connection",
            "keep-alive",
            "transfer-encoding",
            "upgrade",
        }
        
        return {
            key: value
            for key, value in headers.items()
            if key.lower() not in excluded_headers
        }

proxy = ServiceProxy()