import uuid
import logging
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Response, Cookie, Request
from fastapi.responses import RedirectResponse, JSONResponse
from src.core.auth0 import auth0_manager
from src.services.redis_service import redis_service
from src.services.token_service import TokenService
from src.core.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/login")
@router.post("/login")
async def login(response: Response, request: Request):
    """Initiate OAuth2 login flow"""
    try:
        state = str(uuid.uuid4())
        auth_url = auth0_manager.get_authorization_url(state)
        
        await redis_service.client.setex(f"auth_state:{state}", 600, "pending")
        
        logger.info(f"Initiating login with state {state}")
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/callback")
@router.post("/callback")
async def callback(code: str, state: str):
    """Handle OAuth2 callback from Auth0"""
    try:
        stored_state = await redis_service.client.get(f"auth_state:{state}")
        if not stored_state:
            logger.error(f"Invalid state: {state}")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        tokens = await auth0_manager.exchange_code_for_token(code)
        if not tokens:
            logger.error("Failed to exchange code for tokens")
            raise HTTPException(status_code=500, detail="Token exchange failed")
        
        user_info = await auth0_manager.get_user_info(tokens.get("access_token"))
        if not user_info:
            logger.error("Failed to get user info")
            raise HTTPException(status_code=500, detail="Failed to get user info")
        
        session_id = await TokenService.create_session(tokens, user_info)
        if not session_id:
            logger.error("Failed to create session")
            raise HTTPException(status_code=500, detail="Session creation failed")
        
        response = RedirectResponse(url=f"{settings.FRONTEND_URL}/")
        
        response.set_cookie(
            key="session_id",
            value=session_id,
            path="/",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        
        logger.info(f"User {user_info.get('email')} logged in, session: {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Callback processing failed")


@router.get("/me")
async def get_current_user(response: Response, session_id: str = Cookie(None)):
    """Get current user from session"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    try:
        if not session_id:
            raise HTTPException(status_code=401, detail="No session")
        
        user = await TokenService.get_user_from_session(session_id)
        
        if not user:
            logger.warning(f"Invalid or expired session: {session_id}")
            response.delete_cookie(key="session_id", path="/")
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user")


@router.get("/logout")
async def logout(response: Response, session_id: str = Cookie(None)):
    """Logout user and return Auth0 logout URL"""
    try:
        logger.info(f"Logout started, session_id: {session_id}")
        
        if session_id:
            await TokenService.destroy_session(session_id)
        
        params = {
            "client_id": settings.AUTH0_CLIENT_ID,
            "returnTo": settings.FRONTEND_URL
        }
        auth0_logout_url = f"https://{settings.AUTH0_DOMAIN}/v2/logout?{urlencode(params)}"
        
        content = {
            "message": "Logged out successfully",
            "logout_url": auth0_logout_url
        }
        
        response = JSONResponse(content=content, status_code=200)
        
        response.delete_cookie(
            key="session_id",
            path="/",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")