"""
Synchronization Engine

Handles file synchronization between OneDrive and Google Drive.
"""

from src.auth.onedrive_auth import OneDriveAuth
from src.auth.gdrive_auth import GDriveAuth


class SyncEngine:
    """Main synchronization engine"""
    
    def __init__(self):
        self.onedrive = OneDriveAuth()
        self.gdrive = GDriveAuth()
    
    def sync_onedrive_to_gdrive(self, folder_path=None):
        """Sync files from OneDrive to Google Drive"""
        print("Starting OneDrive → Google Drive sync...")
        
        # Get OneDrive files
        endpoint = "me/drive/root/children" if not folder_path else f"me/drive/root:/{folder_path}:/children"
        onedrive_files = self.onedrive.make_api_call(endpoint)
        
        print(f"Found {len(onedrive_files.get('value', []))} files in OneDrive")
        
        # Get Google Drive files
        gdrive_files = self.gdrive.list_files()
        gdrive_file_names = {f['name'] for f in gdrive_files}
        
        # Sync files
        for file in onedrive_files.get('value', []):
            file_name = file['name']
            
            if file_name not in gdrive_file_names:
                print(f"Uploading: {file_name}")
                # TODO: Implement file download from OneDrive and upload to GDrive
            else:
                print(f"Skipping (already exists): {file_name}")
        
        print("Sync completed!")
    
    def sync_gdrive_to_onedrive(self, folder_path=None):
        """Sync files from Google Drive to OneDrive"""
        print("Starting Google Drive → OneDrive sync...")
        
        # Get Google Drive files
        gdrive_files = self.gdrive.list_files()
        
        print(f"Found {len(gdrive_files)} files in Google Drive")
        
        # Get OneDrive files
        endpoint = "me/drive/root/children" if not folder_path else f"me/drive/root:/{folder_path}:/children"
        onedrive_files = self.onedrive.make_api_call(endpoint)
        onedrive_file_names = {f['name'] for f in onedrive_files.get('value', [])}
        
        # Sync files
        for file in gdrive_files:
            file_name = file['name']
            
            if file_name not in onedrive_file_names:
                print(f"Uploading: {file_name}")
                # TODO: Implement file download from GDrive and upload to OneDrive
            else:
                print(f"Skipping (already exists): {file_name}")
        
        print("Sync completed!")
    
    def bidirectional_sync(self, folder_path=None):
        """Perform bidirectional synchronization"""
        print("Starting bidirectional sync...")
        
        # Sync both directions
        self.sync_onedrive_to_gdrive(folder_path)
        self.sync_gdrive_to_onedrive(folder_path)
        
        print("Bidirectional sync completed!")
