import httpx
import json
from src.core.config import settings
from typing import Dict, Optional
import logging
from urllib.parse import urlencode


logger = logging.getLogger(__name__)

class Auth0Manager:
    """Manages Auth0 OAuth2 flow"""
    
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.redirect_uri = settings.AUTH0_REDIRECT_URI
    

    def get_authorization_url(self, state: str, prompt: str = None) -> str:
        """Generate Auth0 authorization URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email offline_access",
            "state": state,
            "audience": settings.AUTH0_AUDIENCE 
        }
        
        if prompt == "signup":
            params["screen_hint"] = "signup"
        elif prompt:
            params['prompt'] = prompt
        
        return f"https://{self.domain}/authorize?{urlencode(params)}"
    

    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for tokens"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.domain}/oauth/token",
                    json = {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri,
                        "code": code
                    },
                    timeout = 10.0
                )
                
                if response.status_code == 200:
                    tokens = response.json()
                    logger.info("Successfully exchanged code for tokens")
                    return tokens
                else:
                    logger.error(f"Token exchange failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error exchanging code: {str(e)}")
            return None
    

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.domain}/oauth/token",
                    json = {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token
                    },
                    timeout = 10.0
                )
                
                if response.status_code == 200:
                    tokens = response.json()
                    logger.info("Successfully refreshed access token")
                    return tokens
                else:
                    logger.error(f"Token refresh failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    

    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user info from Auth0"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.domain}/userinfo",
                    headers = {"Authorization": f"Bearer {access_token}"},
                    timeout = 10.0
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info(f"Retrieved user info for {user_info.get('email')}")
                    return user_info
                else:
                    logger.error(f"Failed to get user info: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None


auth0_manager = Auth0Manager()