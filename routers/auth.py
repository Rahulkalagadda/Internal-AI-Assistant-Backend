from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from core.config import settings
from models.auth import NotionToken, TokenResponse, UserResponse
from services.auth import AuthService
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from clerk_auth import verify_clerk_token

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = verify_clerk_token(token)
        return payload  # or extract user info as needed
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# Example protected endpoint
from fastapi import APIRouter
router = APIRouter()

@router.get("/clerk-protected")
def clerk_protected_route(user=Depends(get_current_user)):
    return {"message": "You are authenticated with Clerk!", "user": user}

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
auth_service = AuthService()

# Debug: Print the Google Client ID
print("GOOGLE_CLIENT_ID from settings:", settings.GOOGLE_CLIENT_ID)

# Configure OAuth
config = Config('.env')
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/drive.readonly'
    }
)

@router.get("/login/google")
async def google_login(request: Request):
    """Initiate Google OAuth login flow"""
    redirect_uri = request.url_for('google_auth')
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )

@router.get("/google/login")
async def google_login_alias(request: Request):
    """Alias for Google OAuth login to support /auth/google/login path"""
    redirect_uri = request.url_for('google_auth')
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent"
    )

@router.get("/google/callback")
async def google_auth(request: Request):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        print("OAuth token:", token)
        if "id_token" not in token:
            raise HTTPException(status_code=400, detail="No id_token in OAuth response. Check your Google OAuth client and scopes.")
        nonce = token.get("userinfo", {}).get("nonce")
        if not nonce:
            raise HTTPException(status_code=400, detail="No nonce found in token. Cannot verify ID token.")
        user = await oauth.google.parse_id_token(token, nonce)
        print("OAuth user:", user)
        if not user or "email" not in user:
            raise HTTPException(status_code=400, detail="Google user info missing email")
        # Create access token
        access_token = auth_service.create_access_token(user)
        # Store Google token
        auth_service.store_google_token(user['email'], token)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        print("OAuth callback error:", e)
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {e}")

@router.post("/notion")
async def set_notion_token(
    token: NotionToken,
    current_user: UserResponse = Depends(auth_service.get_current_user)
):
    """Set Notion integration token"""
    try:
        # Store token securely
        auth_service.store_notion_token(current_user.id, token.token)
        return {"message": "Notion token set successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(auth_service.get_current_user)):
    """Get current user information"""
    return current_user 