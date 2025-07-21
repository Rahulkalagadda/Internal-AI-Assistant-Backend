from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from models.auth import UserResponse, TokenResponse
from core.config import settings
import json

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthService:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        # In production, use a proper database
        self.notion_tokens = {}
        self.google_tokens = {}
        
    def create_access_token(self, user_data: dict) -> str:
        """Create JWT access token"""
        to_encode = {
            "sub": user_data["email"],
            "name": user_data.get("name", ""),
            "picture": user_data.get("picture", ""),
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserResponse:
        """Validate and return current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            return UserResponse(
                id=email,
                email=email,
                name=payload.get("name", ""),
                avatar=payload.get("picture")
            )
        except JWTError:
            raise credentials_exception
    
    def validate_notion_token(self, token: str) -> bool:
        """Validate Notion token by making a test API call"""
        try:
            notion = NotionClient(auth=token)
            # Make a test API call
            notion.users.me
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Notion token"
            )
    
    def store_notion_token(self, user_id: str, token: str):
        """Store Notion token securely"""
        # In production, use a proper database and encryption
        self.notion_tokens[user_id] = token
    
    def get_notion_token(self, user_id: str) -> Optional[str]:
        """Retrieve Notion token"""
        return self.notion_tokens.get(user_id)
    
    def store_google_token(self, user_id: str, token_info: dict):
        """Store Google token securely"""
        # In production, use a proper database and encryption
        self.google_tokens[user_id] = json.dumps(token_info)
    
    def get_google_token(self, user_id: str) -> Optional[dict]:
        """Retrieve Google token"""
        token_str = self.google_tokens.get(user_id)
        return json.loads(token_str) if token_str else None 