from fastapi import APIRouter, Request, Cookie, Depends
from src.core.config import settings
from src.core.proxy import proxy
from typing import Optional, Dict
from src.services.redis_service import redis_service


router = APIRouter()



# FOR FURTHER USAGE WHEN IMPLEMENTING OTHER SERVICES,
# WE WILL USE IT TO MOUNT BEARER TOKEN FOR SECURED ENPOINTS
async def get_auth_headers(request: Request, session_id: Optional[str] = Cookie(None)) -> Dict:
    headers = dict(request.headers)
    if session_id:
        token = await redis_service.get_token(session_id)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        pass 

    return headers



@router.get("/status")
async def get_status():
    return {"status": "Gateway is operational"}

@router.get("/services")
async def get_services():
    return {
        "auth_service": settings.AUTH_SERVICE_URL,
        "user_service": settings.USER_SERVICE_URL
    }


# Auth Service Proxy Routes
@router.api_route("/auth/{path:path}", methods = ["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(path: str, request: Request):
    """Proxy all requests to auth service"""
    return await proxy.forward_request(
        service_name = "auth",
        path = f"/auth/{path}",
        method = request.method,
        headers = dict(request.headers),
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None,
        params = dict(request.query_params)
    )


@router.api_route("/auth", methods = ["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth_root(request: Request):
    """Proxy requests to auth service root"""
    return await proxy.forward_request(
        service_name = "auth",
        path = "/auth",
        method = request.method,
        headers = dict(request.headers),
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None,
        params = dict(request.query_params)
    )


# User Service Proxy Routes
@router.api_route("/users/{path:path}", methods = ["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_users(path: str, request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy all requests to user service"""
    return await proxy.forward_request(
        service_name = "user",
        path = f"/users/{path}",
        method = request.method,
        headers = headers,
        body = await request.body(),
        params = dict(request.query_params)
    )


@router.api_route("/users", methods = ["GET", "POST"])
async def proxy_users_root(request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy requests to user service root"""
    return await proxy.forward_request(
        service_name = "user",
        path = "/users",
        method = request.method,
        headers = headers,
        body = await request.body(),
        params = dict(request.query_params)
    )

