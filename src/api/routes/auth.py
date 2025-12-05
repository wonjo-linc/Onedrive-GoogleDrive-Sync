"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from src.database.session import get_db
from src.database.models import User
from src.auth.azure_oauth import AzureOAuth
from src.auth.google_oauth import GoogleOAuth
from src.auth.jwt_manager import jwt_manager
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize OAuth handlers
azure_oauth = AzureOAuth()
google_oauth = GoogleOAuth()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    provider: str


@router.get("/login/microsoft")
async def login_microsoft():
    """Initiate Microsoft OAuth login"""
    auth_url, state = azure_oauth.get_authorization_url()
    return {"auth_url": auth_url, "state": state}


@router.get("/login/google")
async def login_google():
    """Initiate Google OAuth login"""
    auth_url = google_oauth.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/callback/microsoft")
async def callback_microsoft(code: str, state: str = None, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth callback"""
    try:
        # Exchange code for tokens using stored flow
        token_result = azure_oauth.acquire_token_by_code(code, state)
        
        # Get user info
        user_info = azure_oauth.get_user_info(token_result['access_token'])
        
        # Find or create user
        user = db.query(User).filter(User.email == user_info['mail']).first()
        
        if not user:
            user = User(
                email=user_info['mail'],
                name=user_info.get('displayName'),
                provider='microsoft',
                provider_user_id=user_info['id']
            )
            db.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        access_token = jwt_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Redirect to dashboard with token
        return RedirectResponse(
            url=f"/?token={access_token}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/callback/google")
async def callback_google(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Exchange code for tokens
        token_result = google_oauth.acquire_token_by_code(code)
        
        # Get user info
        user_info = google_oauth.get_user_info(token_result['access_token'])
        
        # Find or create user
        user = db.query(User).filter(User.email == user_info['email']).first()
        
        if not user:
            user = User(
                email=user_info['email'],
                name=user_info.get('name'),
                provider='google',
                provider_user_id=user_info['id']
            )
            db.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        access_token = jwt_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"https://sync.lincsolution.net/auth/success?token={access_token}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current user information"""
    return user


@router.post("/logout")
async def logout():
    """Logout (client should delete token)"""
    return {"message": "Logged out successfully"}
