"""
Google Drive Authentication Module

Handles OAuth 2.0 authentication with Google Drive API.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GDriveAuth:
    """Google Drive OAuth 2.0 Authentication Handler"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    TOKEN_FILE = 'config/token.pickle'
    CREDENTIALS_FILE = 'config/credentials.json'
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from token file or initiate OAuth flow"""
        # Check if token file exists
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If credentials are invalid or don't exist, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired token
                self.creds.refresh(Request())
            else:
                # Start new OAuth flow
                if not os.path.exists(self.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.CREDENTIALS_FILE}\n"
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, self.SCOPES
                )
                self.creds = flow.run_local_server(port=8080)
            
            # Save credentials for future use
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(self.creds, token)
    
    def get_service(self):
        """Get authenticated Google Drive service"""
        if not self.service:
            self.service = build('drive', 'v3', credentials=self.creds)
        return self.service
    
    def list_files(self, page_size=100, query=None):
        """List files in Google Drive"""
        service = self.get_service()
        
        results = service.files().list(
            pageSize=page_size,
            q=query,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)"
        ).execute()
        
        return results.get('files', [])
    
    def download_file(self, file_id, destination):
        """Download a file from Google Drive"""
        service = self.get_service()
        
        request = service.files().get_media(fileId=file_id)
        
        with open(destination, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%")
    
    def upload_file(self, file_path, parent_folder_id=None):
        """Upload a file to Google Drive"""
        service = self.get_service()
        
        file_metadata = {
            'name': os.path.basename(file_path)
        }
        
        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        ).execute()
        
        return file
