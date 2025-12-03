"""
OneDrive Authentication Module

Handles OAuth 2.0 authentication with Microsoft Graph API for OneDrive access.
"""

import os
import msal
import requests
from dotenv import load_dotenv

load_dotenv()


class OneDriveAuth:
    """OneDrive OAuth 2.0 Authentication Handler"""
    
    AUTHORITY = "https://login.microsoftonline.com/{tenant}"
    SCOPES = ["Files.ReadWrite.All"]
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    def __init__(self):
        self.client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        self.client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
        self.tenant_id = os.getenv("ONEDRIVE_TENANT_ID", "common")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("OneDrive credentials not found in environment variables")
        
        self.authority = self.AUTHORITY.format(tenant=self.tenant_id)
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        self.token = None
    
    def get_auth_url(self):
        """Generate authorization URL for user consent"""
        flow = self.app.initiate_auth_code_flow(
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8080/callback"
        )
        return flow["auth_uri"], flow
    
    def acquire_token_by_auth_code(self, auth_code, flow):
        """Exchange authorization code for access token"""
        result = self.app.acquire_token_by_auth_code_flow(flow, auth_code)
        
        if "access_token" in result:
            self.token = result["access_token"]
            return self.token
        else:
            raise Exception(f"Authentication failed: {result.get('error_description')}")
    
    def get_access_token(self):
        """Get valid access token (refresh if needed)"""
        if self.token:
            return self.token
        
        # Try to acquire token silently
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.token = result["access_token"]
                return self.token
        
        # If silent acquisition fails, need interactive login
        raise Exception("No valid token available. Please authenticate first.")
    
    def make_api_call(self, endpoint, method="GET", data=None):
        """Make authenticated API call to Microsoft Graph"""
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.GRAPH_ENDPOINT}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json() if response.content else None
