"""
Google Drive Uploader
Handles folder creation, photo uploads, and share link generation
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from drive_credentials_manager import DriveCredentialsManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriveUploader:
    """
    Handles Google Drive operations:
    - Create person folders
    - Upload photos
    - Generate shareable links
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self):
        self.drive_manager = DriveCredentialsManager()
        
        if not self.drive_manager.is_configured():
            raise ValueError("Google Drive is not configured. Please upload credentials first.")
        
        self.config = self.drive_manager.get_config()
        self.service = None
        self.creds_path = None
        
    def __enter__(self):
        """Context manager entry - setup credentials"""
        try:
            # Get temporary credentials file
            self.creds_path = self.drive_manager.get_credentials_path()
            
            # Create credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.creds_path,
                scopes=self.SCOPES
            )
            
            # Build Drive service
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Drive service initialized successfully")
            
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {str(e)}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup credentials"""
        if self.creds_path:
            self.drive_manager.cleanup_temp_credentials()
            logger.debug("Cleaned up temporary credentials")
    
    def _get_folder_name(self, first_name: str, last_name: str) -> str:
        """
        Generate folder name based on configured format
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            
        Returns:
            str: Formatted folder name
        """
        format_type = self.config.get('folder_name_format', 'FirstName_LastName')
        
        # Sanitize names (remove special characters)
        first_clean = ''.join(c for c in first_name if c.isalnum() or c in ' -_').strip().replace(' ', '_')
        last_clean = ''.join(c for c in last_name if c.isalnum() or c in ' -_').strip().replace(' ', '_')
        
        if format_type == 'LastName_FirstName':
            return f"{last_clean}_{first_clean}"
        elif format_type == 'Event_YYYYMMDD/FirstName_LastName':
            event_date = datetime.now().strftime('%Y%m%d')
            return f"Event_{event_date}/{first_clean}_{last_clean}"
        else:  # Default: FirstName_LastName
            return f"{first_clean}_{last_clean}"
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID
            
        Returns:
            str: Created folder ID
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            # Add parent if specified
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created folder '{folder_name}' with ID: {folder_id}")
            
            return folder_id
            
        except HttpError as e:
            logger.error(f"Failed to create folder '{folder_name}': {str(e)}")
            raise
    
    def create_person_folder(self, first_name: str, last_name: str) -> Tuple[str, str]:
        """
        Create a folder for a person's photos
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            
        Returns:
            Tuple[str, str]: (folder_id, folder_name)
        """
        folder_name = self._get_folder_name(first_name, last_name)
        parent_folder_id = self.config.get('parent_folder_id')
        
        # Handle nested folder structure (e.g., Event_YYYYMMDD/FirstName_LastName)
        if '/' in folder_name:
            parts = folder_name.split('/')
            current_parent = parent_folder_id
            
            # Create parent folders if needed
            for i, part in enumerate(parts[:-1]):
                # Check if folder already exists
                existing_folder = self._find_folder(part, current_parent)
                if existing_folder:
                    current_parent = existing_folder
                    logger.info(f"Using existing folder: {part}")
                else:
                    current_parent = self.create_folder(part, current_parent)
            
            # Create final folder
            final_folder_name = parts[-1]
            folder_id = self.create_folder(final_folder_name, current_parent)
            
        else:
            folder_id = self.create_folder(folder_name, parent_folder_id)
        
        return folder_id, folder_name
    
    def _find_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find a folder by name in a parent folder
        
        Args:
            folder_name: Name of folder to find
            parent_id: Optional parent folder ID
            
        Returns:
            Optional[str]: Folder ID if found, None otherwise
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            return None
            
        except HttpError as e:
            logger.error(f"Error finding folder '{folder_name}': {str(e)}")
            return None
    
    def upload_photo(self, photo_path: str, folder_id: str, 
                    progress_callback=None) -> Tuple[bool, Optional[str]]:
        """
        Upload a single photo to Google Drive
        
        Args:
            photo_path: Path to the photo file
            folder_id: Drive folder ID to upload to
            progress_callback: Optional callback for upload progress
            
        Returns:
            Tuple[bool, Optional[str]]: (success, file_id)
        """
        try:
            photo_path = Path(photo_path)
            
            if not photo_path.exists():
                logger.error(f"Photo not found: {photo_path}")
                return False, None
            
            file_metadata = {
                'name': photo_path.name,
                'parents': [folder_id]
            }
            
            # Determine MIME type
            mime_type = 'image/jpeg'
            if photo_path.suffix.lower() in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif photo_path.suffix.lower() == '.png':
                mime_type = 'image/png'
            
            media = MediaFileUpload(
                str(photo_path),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Uploaded '{photo_path.name}' to Drive (ID: {file_id})")
            
            if progress_callback:
                progress_callback(photo_path.name)
            
            return True, file_id
            
        except HttpError as e:
            logger.error(f"Failed to upload '{photo_path}': {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error uploading '{photo_path}': {str(e)}")
            return False, None
    
    def upload_photos_batch(self, photo_paths: List[str], folder_id: str,
                           progress_callback=None) -> Tuple[int, int]:
        """
        Upload multiple photos to a folder
        
        Args:
            photo_paths: List of photo file paths
            folder_id: Drive folder ID to upload to
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Tuple[int, int]: (successful_uploads, failed_uploads)
        """
        successful = 0
        failed = 0
        total = len(photo_paths)
        
        for idx, photo_path in enumerate(photo_paths, 1):
            if progress_callback:
                progress_callback(idx, total, Path(photo_path).name)
            
            success, file_id = self.upload_photo(photo_path, folder_id)
            
            if success:
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Batch upload complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def generate_share_link(self, folder_id: str) -> str:
        """
        Generate a shareable link for a folder (anyone with link can view)
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            str: Shareable link URL
        """
        try:
            # Create permission for anyone with link
            permission = {
                'type': 'anyone',
                'role': 'reader'  # View only
            }
            
            self.service.permissions().create(
                fileId=folder_id,
                body=permission,
                fields='id'
            ).execute()
            
            # Get the folder info including web link
            folder = self.service.files().get(
                fileId=folder_id,
                fields='webViewLink'
            ).execute()
            
            share_link = folder.get('webViewLink')
            logger.info(f"Generated share link for folder {folder_id}: {share_link}")
            
            return share_link
            
        except HttpError as e:
            logger.error(f"Failed to generate share link for folder {folder_id}: {str(e)}")
            raise
    
    def upload_person_photos(self, first_name: str, last_name: str, 
                            photo_paths: List[str],
                            progress_callback=None) -> dict:
        """
        Complete workflow: Create folder, upload photos, generate share link
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            photo_paths: List of photo file paths
            progress_callback: Optional callback(action, details)
            
        Returns:
            dict: {
                'success': bool,
                'folder_id': str,
                'folder_name': str,
                'share_link': str,
                'photos_uploaded': int,
                'photos_failed': int
            }
        """
        try:
            # Step 1: Create folder
            if progress_callback:
                progress_callback('creating_folder', f"Creating folder for {first_name} {last_name}...")
            
            folder_id, folder_name = self.create_person_folder(first_name, last_name)
            
            # Step 2: Upload photos
            if progress_callback:
                progress_callback('uploading_photos', f"Uploading {len(photo_paths)} photos...")
            
            def upload_progress(current, total, filename):
                if progress_callback:
                    progress_callback('uploading_photo', 
                                    f"Uploading photo {current}/{total}: {filename}")
            
            successful, failed = self.upload_photos_batch(
                photo_paths, 
                folder_id,
                progress_callback=upload_progress
            )
            
            # Step 3: Generate share link
            if progress_callback:
                progress_callback('generating_link', "Generating shareable link...")
            
            share_link = self.generate_share_link(folder_id)
            
            return {
                'success': True,
                'folder_id': folder_id,
                'folder_name': folder_name,
                'share_link': share_link,
                'photos_uploaded': successful,
                'photos_failed': failed,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to upload photos for {first_name} {last_name}: {str(e)}")
            return {
                'success': False,
                'folder_id': None,
                'folder_name': None,
                'share_link': None,
                'photos_uploaded': 0,
                'photos_failed': len(photo_paths),
                'error': str(e)
            }
    
    def test_connection(self) -> dict:
        """
        Test Drive API connection and permissions
        
        Returns:
            dict: Test results with details
        """
        try:
            # Get user info
            about = self.service.about().get(fields='user').execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            result = {
                'success': True,
                'service_account': user_email,
                'parent_folder': None,
                'can_create': False
            }
            
            # Test parent folder access if configured
            parent_folder_id = self.config.get('parent_folder_id')
            
            if parent_folder_id:
                try:
                    folder = self.service.files().get(
                        fileId=parent_folder_id,
                        fields='id, name, capabilities'
                    ).execute()
                    
                    result['parent_folder'] = folder.get('name')
                    result['can_create'] = folder.get('capabilities', {}).get('canAddChildren', False)
                    
                except HttpError as e:
                    result['success'] = False
                    result['error'] = f"Cannot access parent folder: {str(e)}"
            else:
                result['parent_folder'] = 'Root (My Drive)'
                result['can_create'] = True
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
