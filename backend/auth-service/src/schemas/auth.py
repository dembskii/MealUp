from pydantic import BaseModel, EmailStr
from typing import Optional

#REQUEST SCHEMAS
class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str



#RESPONSE SCHEMAS
class UserInfo(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int

class LoginResponse(BaseModel):
    user: UserInfo
    tokens: TokenResponse
    session_id: str

class MeResponse(BaseModel):
    user: UserInfo
    session_id: str

class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    status_code: int



#SESSION SCHEMAS
class SessionData(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    refresh_token: str
    access_token: str
    created_at: int
    expires_at: int
    
    class Config:
        from_attributes = True



#AUTH0 SCHEMAS
class Auth0TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: str
    expires_in: int

class Auth0UserInfo(BaseModel):
    sub: str
    email: str
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True