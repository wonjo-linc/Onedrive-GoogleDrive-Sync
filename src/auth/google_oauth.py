"""
Google OAuth integration for Google Workspace
"""

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
from typing import Dict, Optional
import json


class GoogleOAuth:
    """Google OAuth handler"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://sync.lincsolution.net/auth/callback/google")
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Google OAuth credentials not configured")
        
        # Create client config
        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Get authorization URL for user consent
        
        Returns:
            auth_url
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        return auth_url
    
    def acquire_token_by_code(self, code: str) -> Dict:
        """
        Exchange authorization code for tokens
        
        Returns:
            {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'token_uri': str,
                'scopes': list
            }
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        flow.fetch_token(code=code)
        
        creds = flow.credentials
        
        return {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'expires_in': creds.expiry.timestamp() if creds.expiry else None,
            'token_uri': creds.token_uri,
            'scopes': creds.scopes
        }
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token
        
        Returns:
            {
                'access_token': str,
                'expires_in': int
            }
        """
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.SCOPES
            )
            
            creds.refresh(Request())
            
            return {
                'access_token': creds.token,
                'expires_in': creds.expiry.timestamp() if creds.expiry else None
            }
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Google"""
        import requests
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
