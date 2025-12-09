import os
import jwt
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = os.getenv("ALGORITHMS")


class Auth0Validator:
    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(self.jwks_url)

    def verify_token(self, token: str) -> Dict:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=ALGORITHMS,
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{self.domain}/",
                leeway=30
            )
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token validation failed: Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token validation failed: Invalid token - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token Error: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to validate token credentials"
            )

auth0_validator = Auth0Validator()
security = HTTPBearer()

async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authentication token provided"
        )
    return auth0_validator.verify_token(token)