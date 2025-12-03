"""
Azure AD OAuth integration for Microsoft 365 Business
"""

from msal import ConfidentialClientApplication
import os
from typing import Dict, Optional


class AzureOAuth:
    """Azure AD OAuth handler"""
    
    AUTHORITY = "https://login.microsoftonline.com/{tenant}"
    SCOPES = [
        "https://graph.microsoft.com/Files.ReadWrite.All",
        "https://graph.microsoft.com/Sites.ReadWrite.All",
        "https://graph.microsoft.com/User.Read",
        "offline_access"
    ]
    
    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.redirect_uri = os.getenv("AZURE_REDIRECT_URI", "https://sync.lincsolution.net/auth/callback/microsoft")
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Azure AD credentials not configured")
        
        self.authority = self.AUTHORITY.format(tenant=self.tenant_id)
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
    
    def get_authorization_url(self, state: str = None) -> tuple[str, str]:
        """
        Get authorization URL for user consent
        
        Returns:
            (auth_url, state)
        """
        flow = self.app.initiate_auth_code_flow(
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
            state=state
        )
        return flow["auth_uri"], flow.get("state")
    
    def acquire_token_by_code(self, code: str) -> Dict:
        """
        Exchange authorization code for tokens
        
        Returns:
            {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int,
                'id_token_claims': dict
            }
        """
        result = self.app.acquire_token_by_auth_code_flow(
            {"code": code},
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        if "error" in result:
            raise Exception(f"Token acquisition failed: {result.get('error_description')}")
        
        return result
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token
        
        Returns:
            {
                'access_token': str,
                'refresh_token': str,
                'expires_in': int
            }
        """
        result = self.app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=self.SCOPES
        )
        
        if "error" in result:
            print(f"Token refresh failed: {result.get('error_description')}")
            return None
        
        return result
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Microsoft Graph"""
        import requests
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
