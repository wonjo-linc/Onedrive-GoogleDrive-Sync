"""
Authentication routes - Session-based
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession
from datetime import datetime

from src.database.session import get_db
from src.database.models import User, ConnectedAccount
from src.auth.azure_oauth import AzureOAuth
from src.auth.google_oauth import GoogleOAuth
from src.auth.token_manager import TokenManager

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize OAuth handlers
azure_oauth = AzureOAuth()
google_oauth = GoogleOAuth()
token_manager = TokenManager()


@router.get("/login/microsoft")
async def login_microsoft():
    """Start Microsoft OAuth login (also connects OneDrive)"""
    auth_url, state = azure_oauth.get_authorization_url()
    return {"auth_url": auth_url, "state": state}


@router.get("/callback/microsoft")
async def callback_microsoft(
    code: str,
    state: str = None,
    request: Request = None,
    db: DBSession = None
):
    """Handle Microsoft OAuth callback - Creates user + OneDrive account + session"""
    if db is None:
        from src.database.session import SessionLocal
        db = SessionLocal()
    
    try:
        # Exchange code for tokens
        token_result = azure_oauth.acquire_token_by_code(code, state)
        
        # Get user info
        user_info = azure_oauth.get_user_info(token_result['access_token'])
        
        # Create or update user
        user = db.query(User).filter(User.email == user_info['mail']).first()
        if not user:
            user = User(
                email=user_info['mail'],
                name=user_info.get('displayName', user_info['mail'])
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create or update OneDrive account
        onedrive_account = db.query(ConnectedAccount).filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.platform == 'onedrive'
        ).first()
        
        if onedrive_account:
            # Update tokens
            onedrive_account.access_token_encrypted = token_manager.encrypt_token(token_result['access_token'])
            onedrive_account.refresh_token_encrypted = token_manager.encrypt_token(token_result.get('refresh_token'))
            from datetime import timedelta
            onedrive_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
        else:
            # Create new account
            from datetime import timedelta
            onedrive_account = ConnectedAccount(
                user_id=user.id,
                platform='onedrive',
                email=user_info['mail'],
                access_token_encrypted=token_manager.encrypt_token(token_result['access_token']),
                refresh_token_encrypted=token_manager.encrypt_token(token_result.get('refresh_token')),
                token_expires_at=datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
            )
            db.add(onedrive_account)
        
        db.commit()
        
        # Create session
        request.session['user_id'] = user.id
        
        # Redirect to dashboard
        return RedirectResponse(url="/")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/login/google")
async def login_google():
    """Start Google OAuth login (for Google Drive connection)"""
    auth_url = google_oauth.get_authorization_url()
    return {"auth_url": auth_url}


@router.get("/callback/google")
async def callback_google(
    code: str,
    state: str = None,
    request: Request = None,
    db: DBSession = None
):
    """Handle Google OAuth callback - Adds Google Drive account"""
    if db is None:
        from src.database.session import SessionLocal
        db = SessionLocal()
    
    # Check session
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        # Exchange code for tokens
        token_result = google_oauth.acquire_token_by_code(code)
        
        # Get user info
        user_info = google_oauth.get_user_info(token_result['access_token'])
        
        # Create or update Google Drive account
        gdrive_account = db.query(ConnectedAccount).filter(
            ConnectedAccount.user_id == user_id,
            ConnectedAccount.platform == 'gdrive'
        ).first()
        
        if gdrive_account:
            # Update tokens
            gdrive_account.access_token_encrypted = token_manager.encrypt_token(token_result['access_token'])
            gdrive_account.refresh_token_encrypted = token_manager.encrypt_token(token_result.get('refresh_token'))
            from datetime import timedelta
            gdrive_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
        else:
            # Create new account
            from datetime import timedelta
            gdrive_account = ConnectedAccount(
                user_id=user_id,
                platform='gdrive',
                email=user_info['email'],
                access_token_encrypted=token_manager.encrypt_token(token_result['access_token']),
                refresh_token_encrypted=token_manager.encrypt_token(token_result.get('refresh_token')),
                token_expires_at=datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
            )
            db.add(gdrive_account)
        
        db.commit()
        
        # Redirect to dashboard
        return RedirectResponse(url="/")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google Drive connection failed: {str(e)}"
        )


@router.get("/logout")
async def logout(request: Request):
    """Logout and clear session"""
    request.session.clear()
    return RedirectResponse(url="/")


@router.get("/me")
async def get_me(request: Request, db: DBSession = None):
    """Get current user info"""
    if db is None:
        from src.database.session import SessionLocal
        db = SessionLocal()
    
    user_id = request.session.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name
    }
