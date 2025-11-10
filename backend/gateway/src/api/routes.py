from fastapi import APIRouter, Request
from src.core.config import settings
from src.core.proxy import proxy

router = APIRouter()

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
@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(path: str, request: Request):
    """Proxy all requests to auth service"""
    return await proxy.forward_request(
        service_name="auth",
        path=f"/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        params=dict(request.query_params)
    )

# User Service Proxy Routes
@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_users(path: str, request: Request):
    """Proxy all requests to user service"""
    return await proxy.forward_request(
        service_name="user",
        path=f"/users/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        params=dict(request.query_params)
    )

@router.api_route("/users", methods=["GET", "POST"])
async def proxy_users_root(request: Request):
    """Proxy requests to user service root"""
    return await proxy.forward_request(
        service_name="user",
        path="/users",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        params=dict(request.query_params)
    )

