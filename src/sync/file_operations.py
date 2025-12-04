"""
File operations for sync engine
"""

import os
import requests
from typing import Optional, BinaryIO
from datetime import datetime, timedelta
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential


class FileOperations:
    """Handle file upload/download operations"""
    
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def download_onedrive_file(
        self,
        access_token: str,
        file_id: str,
        destination_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Download file from OneDrive
        
        Args:
            access_token: OneDrive access token
            file_id: OneDrive file ID
            destination_path: Local path to save file
            progress_callback: Optional callback(bytes_downloaded, total_bytes)
        
        Returns:
            Path to downloaded file
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get download URL
        url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
        
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        with open(destination_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return destination_path
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def upload_to_gdrive(
        self,
        access_token: str,
        file_path: str,
        folder_id: str,
        file_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        Upload file to Google Drive with resumable upload
        
        Args:
            access_token: Google Drive access token
            file_path: Local file path
            folder_id: Google Drive folder ID
            file_name: Optional custom file name
            progress_callback: Optional callback(bytes_uploaded, total_bytes)
        
        Returns:
            File metadata dict
        """
        if not file_name:
            file_name = os.path.basename(file_path)
        
        file_size = os.path.getsize(file_path)
        
        # Initiate resumable upload
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        metadata = {
            "name": file_name,
            "parents": [folder_id]
        }
        
        init_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
        init_response = requests.post(init_url, headers=headers, json=metadata)
        init_response.raise_for_status()
        
        upload_url = init_response.headers['Location']
        
        # Upload file in chunks
        uploaded = 0
        with open(file_path, 'rb') as f:
            while uploaded < file_size:
                chunk_size = min(self.CHUNK_SIZE, file_size - uploaded)
                chunk = f.read(chunk_size)
                
                headers = {
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {uploaded}-{uploaded + len(chunk) - 1}/{file_size}"
                }
                
                response = requests.put(upload_url, headers=headers, data=chunk)
                
                if response.status_code in [200, 201]:
                    # Upload complete
                    uploaded += len(chunk)
                    if progress_callback:
                        progress_callback(uploaded, file_size)
                    return response.json()
                elif response.status_code == 308:
                    # Resume incomplete
                    uploaded += len(chunk)
                    if progress_callback:
                        progress_callback(uploaded, file_size)
                else:
                    response.raise_for_status()
        
        raise Exception("Upload failed")
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def download_gdrive_file(
        self,
        access_token: str,
        file_id: str,
        destination_path: str,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Download file from Google Drive"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        with open(destination_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return destination_path
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )
    def upload_to_onedrive(
        self,
        access_token: str,
        file_path: str,
        folder_path: str,
        file_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """Upload file to OneDrive with resumable upload"""
        if not file_name:
            file_name = os.path.basename(file_path)
        
        file_size = os.path.getsize(file_path)
        
        # Create upload session
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        clean_path = folder_path.lstrip('/')
        upload_path = f"{clean_path}/{file_name}" if clean_path else file_name
        
        session_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{upload_path}:/createUploadSession"
        
        session_response = requests.post(session_url, headers=headers)
        session_response.raise_for_status()
        
        upload_url = session_response.json()['uploadUrl']
        
        # Upload file in chunks
        uploaded = 0
        with open(file_path, 'rb') as f:
            while uploaded < file_size:
                chunk_size = min(self.CHUNK_SIZE, file_size - uploaded)
                chunk = f.read(chunk_size)
                
                headers = {
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {uploaded}-{uploaded + len(chunk) - 1}/{file_size}"
                }
                
                response = requests.put(upload_url, headers=headers, data=chunk)
                
                if response.status_code in [200, 201]:
                    # Upload complete
                    uploaded += len(chunk)
                    if progress_callback:
                        progress_callback(uploaded, file_size)
                    return response.json()
                elif response.status_code == 202:
                    # Continue uploading
                    uploaded += len(chunk)
                    if progress_callback:
                        progress_callback(uploaded, file_size)
                else:
                    response.raise_for_status()
        
        raise Exception("Upload failed")
