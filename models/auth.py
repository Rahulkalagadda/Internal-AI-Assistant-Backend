from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class NotionToken(BaseModel):
    token: str
    workspace_name: Optional[str] = None

class GoogleToken(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    token_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: Optional[list[str]] = None 