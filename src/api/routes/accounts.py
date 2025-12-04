"""
Account management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List

from src.database.session import get_db
from src.database.models import User, ConnectedAccount
from src.api.dependencies import get_current_user
from src.auth.azure_oauth import AzureOAuth
from src.auth.google_oauth import GoogleOAuth
from src.auth.token_manager import TokenManager

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Initialize OAuth handlers
azure_oauth = AzureOAuth()
google_oauth = GoogleOAuth()
token_manager = TokenManager()


class ConnectAccountRequest(BaseModel):
    code: str


class AccountResponse(BaseModel):
    id: int
    platform: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/connect/onedrive/start")
async def start_onedrive_connection(user: User = Depends(get_current_user)):
    """Start OneDrive account connection flow"""
    auth_url, state = azure_oauth.get_authorization_url()
    return {
        "auth_url": auth_url,
        "state": state,
        "instructions": "Visit the auth_url, login, and copy the 'code' parameter from the redirect URL (before &state=)"
    }


@router.get("/connect/gdrive/start")
async def start_gdrive_connection(user: User = Depends(get_current_user)):
    """Start Google Drive account connection flow"""
    auth_url = google_oauth.get_authorization_url()
    return {
        "auth_url": auth_url,
        "instructions": "Visit the auth_url, login, and copy the 'code' parameter from the redirect URL"
    }


@router.post("/connect/onedrive", response_model=AccountResponse)
async def connect_onedrive(
    request: ConnectAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect OneDrive account"""
    try:
        # Exchange code for tokens
        token_result = azure_oauth.acquire_token_by_code(request.code)
        
        # Get user info
        user_info = azure_oauth.get_user_info(token_result['access_token'])
        
        # Check if account already connected
        existing = db.query(ConnectedAccount).filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.platform == 'onedrive',
            ConnectedAccount.email == user_info['mail']
        ).first()
        
        if existing:
            # Update tokens
            existing.access_token_encrypted = token_manager.encrypt_token(token_result['access_token'])
            existing.refresh_token_encrypted = token_manager.encrypt_token(token_result.get('refresh_token'))
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new connected account
        account = ConnectedAccount(
            user_id=user.id,
            platform='onedrive',
            email=user_info['mail'],
            access_token_encrypted=token_manager.encrypt_token(token_result['access_token']),
            refresh_token_encrypted=token_manager.encrypt_token(token_result.get('refresh_token')),
            token_expires_at=datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect OneDrive account: {str(e)}"
        )


@router.post("/connect/gdrive", response_model=AccountResponse)
async def connect_gdrive(
    request: ConnectAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect Google Drive account"""
    try:
        # Exchange code for tokens
        token_result = google_oauth.acquire_token_by_code(request.code)
        
        # Get user info
        user_info = google_oauth.get_user_info(token_result['access_token'])
        
        # Check if account already connected
        existing = db.query(ConnectedAccount).filter(
            ConnectedAccount.user_id == user.id,
            ConnectedAccount.platform == 'gdrive',
            ConnectedAccount.email == user_info['email']
        ).first()
        
        if existing:
            # Update tokens
            existing.access_token_encrypted = token_manager.encrypt_token(token_result['access_token'])
            existing.refresh_token_encrypted = token_manager.encrypt_token(token_result.get('refresh_token'))
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new connected account
        account = ConnectedAccount(
            user_id=user.id,
            platform='gdrive',
            email=user_info['email'],
            access_token_encrypted=token_manager.encrypt_token(token_result['access_token']),
            refresh_token_encrypted=token_manager.encrypt_token(token_result.get('refresh_token')),
            token_expires_at=datetime.utcnow() + timedelta(seconds=token_result.get('expires_in', 3600))
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect Google Drive account: {str(e)}"
        )


@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List connected accounts"""
    accounts = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user.id
    ).all()
    return accounts


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect account"""
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id,
        ConnectedAccount.user_id == user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Account disconnected successfully"}
