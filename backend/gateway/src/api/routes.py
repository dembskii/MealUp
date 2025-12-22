import logging
from fastapi import APIRouter, Request, Cookie, Depends
from src.core.config import settings
from src.core.proxy import proxy
from typing import Optional, Dict
from src.services.redis_service import redis_service

logger = logging.getLogger(__name__)


router = APIRouter()


async def get_auth_headers(request: Request, session_id: Optional[str] = Cookie(None)) -> Dict:
    """
    Extract auth headers from session and prepare headers for downstream services.
    Adds Authorization header and X-User-Id header if session exists.
    """
    headers = dict(request.headers)
    
    if session_id:
        session = await redis_service.get_session(session_id)
        if session:
            # Add Authorization header with access token
            logger.info(session)
            access_token = session.get("access_token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            
            # Extract user ID from session and add as X-User-Id header
            # user_info = session.get("user_info") or {}
            user_id = session.get("internal_uid")
            
            if user_id:
                headers["X-User-Id"] = str(user_id)
                logger.info(f"Gateway forwarding user_id: {user_id}")
            # logger.info(f"Gateway forwarding headers: {headers}")

    return headers


@router.get("/status")
async def get_status():
    return {"status": "Gateway is operational"}

@router.get("/services")
async def get_services():
    return {
        "auth_service": settings.AUTH_SERVICE_URL,
        "user_service": settings.USER_SERVICE_URL,
        "recipe_service": settings.RECIPE_SERVICE_URL,
        "user_service": settings.USER_SERVICE_URL,
        "forum_service": settings.FORUM_SERVICE_URL,
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
@router.api_route("/user/{path:path}", methods = ["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_users(path: str, request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy all requests to user service"""
    return await proxy.forward_request(
        service_name = "user",
        path = f"/user/{path}",
        method = request.method,
        headers = headers,
        body = await request.body(),
        params = dict(request.query_params)
    )


@router.api_route("/user", methods = ["GET", "POST"])
async def proxy_users_root(request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy requests to user service root"""
    return await proxy.forward_request(
        service_name = "user",
        path = "/user",
        method = request.method,
        headers = headers,
        body = await request.body(),
        params = dict(request.query_params)
    )


# Recipe Service Proxy Routes
@router.api_route("/recipes/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_recipes(path: str, request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy all requests to recipe service"""
    return await proxy.forward_request(
        service_name="recipe",
        path=f"/recipes/{path}",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )


@router.api_route("/recipes", methods=["GET", "POST"])
async def proxy_recipes_root(request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy requests to recipe service root"""
    return await proxy.forward_request(
        service_name="recipe",
        path="/recipes",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )



# Recipe Service Proxy Routes
@router.api_route("/workouts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_workouts(path: str, request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy all requests to workout service"""
    return await proxy.forward_request(
        service_name="workout",
        path=f"/workouts/{path}",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )


@router.api_route("/workouts", methods=["GET", "POST"])
async def proxy_workouts_root(request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy requests to workout service root"""
    return await proxy.forward_request(
        service_name="workout",
        path="/workouts",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )



# Forum Service Proxy Routes
@router.api_route("/forum/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_forum(path: str, request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy all requests to forum service"""
    return await proxy.forward_request(
        service_name="forum",
        path=f"/forum/{path}",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )


@router.api_route("/forum", methods=["GET", "POST"])
async def proxy_forum_root(request: Request, headers: Dict = Depends(get_auth_headers)):
    """Proxy requests to forum service root"""
    return await proxy.forward_request(
        service_name="forum",
        path="/forum",
        method=request.method,
        headers=headers,
        body=await request.body() if request.method in ["POST", "PUT", "PATCH", "DELETE"] else None,
        params=dict(request.query_params)
    )