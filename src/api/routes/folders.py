"""
Folder browsing routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import requests

from src.database.session import get_db
from src.database.models import User, ConnectedAccount
from src.api.session_deps import get_current_user
from src.auth.token_manager import token_manager
from src.auth.azure_oauth import AzureOAuth
from src.auth.google_oauth import GoogleOAuth

router = APIRouter(prefix="/folders", tags=["folders"])

azure_oauth = AzureOAuth()
google_oauth = GoogleOAuth()


class FolderItem(BaseModel):
    id: str
    name: str
    path: str
    is_folder: bool
    size: Optional[int] = None
    modified: Optional[datetime] = None


class FolderListResponse(BaseModel):
    folders: List[FolderItem]
    parent_path: Optional[str] = None


def get_valid_token(account: ConnectedAccount, db: Session) -> str:
    """Get valid access token, refresh if needed"""
    
    # Check if token is expired
    if account.token_expires_at and account.token_expires_at < datetime.utcnow():
        # Refresh token
        refresh_token = token_manager.decrypt_token(account.refresh_token_encrypted)
        
        if account.platform == 'onedrive':
            result = azure_oauth.refresh_access_token(refresh_token)
        else:  # gdrive
            result = google_oauth.refresh_access_token(refresh_token)
        
        if result:
            # Update tokens
            account.access_token_encrypted = token_manager.encrypt_token(result['access_token'])
            if result.get('refresh_token'):
                account.refresh_token_encrypted = token_manager.encrypt_token(result['refresh_token'])
            account.token_expires_at = datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))
            db.commit()
            
            return result['access_token']
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token"
            )
    
    return token_manager.decrypt_token(account.access_token_encrypted)


@router.get("/onedrive/{account_id}", response_model=FolderListResponse)
async def list_onedrive_folders(
    account_id: int,
    path: str = Query("/", description="Folder path to list"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List OneDrive folders"""
    
    # Get account
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id,
        ConnectedAccount.user_id == user.id,
        ConnectedAccount.platform == 'onedrive'
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OneDrive account not found"
        )
    
    # Get valid token
    access_token = get_valid_token(account, db)
    
    # Call Microsoft Graph API
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Determine the API endpoint
    if path == "/" or path == "":
        url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
    else:
        # Remove leading slash
        clean_path = path.lstrip('/')
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{clean_path}:/children"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        folders = []
        for item in data.get('value', []):
            folders.append(FolderItem(
                id=item['id'],
                name=item['name'],
                path=f"{path.rstrip('/')}/{item['name']}",
                is_folder='folder' in item,
                size=item.get('size'),
                modified=item.get('lastModifiedDateTime')
            ))
        
        # Get parent path
        parent_path = None
        if path != "/" and path != "":
            parts = path.rstrip('/').split('/')
            parent_path = '/'.join(parts[:-1]) if len(parts) > 1 else "/"
        
        return FolderListResponse(folders=folders, parent_path=parent_path)
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to list OneDrive folders: {e.response.text}"
        )


@router.get("/gdrive/{account_id}", response_model=FolderListResponse)
async def list_gdrive_folders(
    account_id: int,
    folder_id: str = Query("root", description="Folder ID to list (use 'root' for root folder)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Google Drive folders"""
    
    # Get account
    account = db.query(ConnectedAccount).filter(
        ConnectedAccount.id == account_id,
        ConnectedAccount.user_id == user.id,
        ConnectedAccount.platform == 'gdrive'
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive account not found"
        )
    
    # Get valid token
    access_token = get_valid_token(account, db)
    
    # Call Google Drive API
    headers = {"Authorization": f"Bearer {access_token}"}
    
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        'q': f"'{folder_id}' in parents and trashed=false",
        'fields': 'files(id,name,mimeType,size,modifiedTime,parents)',
        'orderBy': 'folder,name'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        folders = []
        for item in data.get('files', []):
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            folders.append(FolderItem(
                id=item['id'],
                name=item['name'],
                path=item['name'],  # Google Drive uses IDs, not paths
                is_folder=is_folder,
                size=int(item.get('size', 0)) if item.get('size') else None,
                modified=item.get('modifiedTime')
            ))
        
        return FolderListResponse(folders=folders, parent_path=None)
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to list Google Drive folders: {e.response.text}"
        )
