"""
Google Drive Credentials Manager
Handles secure storage and retrieval of service account credentials
"""

import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DriveCredentialsManager:
    """
    Manages Google Drive service account credentials with encryption
    """
    
    def __init__(self, credentials_dir='instance/drive_credentials'):
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        
        self.encrypted_file = self.credentials_dir / 'credentials.enc'
        self.key_file = self.credentials_dir / '.key'
        self.config_file = self.credentials_dir / 'config.json'
        
        # Generate or load encryption key
        self.cipher = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self):
        """Get existing encryption key or create a new one"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new encryption key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (owner only)
            os.chmod(self.key_file, 0o600)
            logger.info("Generated new encryption key for Drive credentials")
        
        return Fernet(key)
    
    def save_credentials(self, credentials_json: dict, parent_folder_id: str = None, 
                        folder_name_format: str = 'FirstName_LastName') -> bool:
        """
        Encrypt and save service account credentials
        
        Args:
            credentials_json: The service account JSON content
            parent_folder_id: Optional Google Drive parent folder ID
            folder_name_format: Format for creating folder names
            
        Returns:
            bool: Success status
        """
        try:
            # Validate credentials structure
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                             'client_email', 'client_id']
            
            for field in required_fields:
                if field not in credentials_json:
                    raise ValueError(f"Missing required field: {field}")
            
            if credentials_json['type'] != 'service_account':
                raise ValueError("Invalid credentials type. Expected 'service_account'")
            
            # Encrypt credentials
            credentials_str = json.dumps(credentials_json)
            encrypted_data = self.cipher.encrypt(credentials_str.encode())
            
            # Save encrypted credentials
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.encrypted_file, 0o600)
            
            # Save configuration
            config = {
                'service_account_email': credentials_json['client_email'],
                'project_id': credentials_json['project_id'],
                'parent_folder_id': parent_folder_id,
                'folder_name_format': folder_name_format,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Drive credentials saved successfully for {config['service_account_email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save Drive credentials: {str(e)}")
            raise
    
    def load_credentials(self) -> dict:
        """
        Decrypt and load service account credentials
        
        Returns:
            dict: The decrypted credentials JSON
        """
        try:
            if not self.encrypted_file.exists():
                raise FileNotFoundError("No credentials file found")
            
            # Read and decrypt
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to load Drive credentials: {str(e)}")
            raise
    
    def get_config(self) -> dict:
        """
        Get Drive configuration (non-sensitive info)
        
        Returns:
            dict: Configuration including parent folder ID, format, etc.
        """
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Failed to load Drive config: {str(e)}")
            return None
    
    def update_config(self, parent_folder_id: str = None, 
                     folder_name_format: str = None) -> bool:
        """
        Update Drive configuration without changing credentials
        
        Args:
            parent_folder_id: New parent folder ID
            folder_name_format: New folder naming format
            
        Returns:
            bool: Success status
        """
        try:
            config = self.get_config()
            if not config:
                raise ValueError("No existing configuration found")
            
            if parent_folder_id is not None:
                config['parent_folder_id'] = parent_folder_id
            
            if folder_name_format is not None:
                config['folder_name_format'] = folder_name_format
            
            config['updated_at'] = datetime.utcnow().isoformat()
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Drive configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update Drive config: {str(e)}")
            raise
    
    def delete_credentials(self) -> bool:
        """
        Delete all stored credentials and configuration
        
        Returns:
            bool: Success status
        """
        try:
            files_to_delete = [self.encrypted_file, self.config_file]
            
            for file_path in files_to_delete:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted {file_path.name}")
            
            logger.info("Drive credentials deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Drive credentials: {str(e)}")
            raise
    
    def is_configured(self) -> bool:
        """Check if credentials are configured"""
        return self.encrypted_file.exists() and self.config_file.exists()
    
    def get_credentials_path(self) -> str:
        """
        Get path to a temporary unencrypted credentials file
        Used by Google API client which needs a file path
        
        Returns:
            str: Path to temporary credentials file
        """
        try:
            credentials = self.load_credentials()
            
            # Create temporary file
            temp_file = self.credentials_dir / 'temp_credentials.json'
            with open(temp_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            os.chmod(temp_file, 0o600)
            
            return str(temp_file)
            
        except Exception as e:
            logger.error(f"Failed to create temporary credentials file: {str(e)}")
            raise
    
    def cleanup_temp_credentials(self):
        """Remove temporary credentials file"""
        temp_file = self.credentials_dir / 'temp_credentials.json'
        if temp_file.exists():
            temp_file.unlink()
            logger.debug("Cleaned up temporary credentials file")
    
    @staticmethod
    def get_oauth_credentials(user_identifier='admin'):
        """
        Get OAuth credentials from database
        
        Args:
            user_identifier: User identifier (default: 'admin')
            
        Returns:
            tuple: (access_token, refresh_token, token_expiry) or (None, None, None)
        """
        try:
            # Import here to avoid circular import
            from app import DriveOAuthToken, db
            from datetime import datetime
            
            token = DriveOAuthToken.query.filter_by(user_identifier=user_identifier).first()
            
            if not token:
                logger.warning(f"No OAuth token found for {user_identifier}")
                return None, None, None
            
            return token.access_token, token.refresh_token, token.token_expiry
            
        except Exception as e:
            logger.error(f"Failed to get OAuth credentials: {str(e)}")
            return None, None, None
    
    @staticmethod
    def refresh_oauth_token(user_identifier='admin'):
        """
        Refresh expired OAuth access token
        
        Args:
            user_identifier: User identifier (default: 'admin')
            
        Returns:
            str: New access token or None
        """
        try:
            import requests
            from app import DriveOAuthToken, db
            from datetime import datetime, timedelta
            
            token = DriveOAuthToken.query.filter_by(user_identifier=user_identifier).first()
            
            if not token:
                logger.error(f"No OAuth token found for {user_identifier}")
                return None
            
            # Check if token needs refresh
            if not token.is_expired():
                logger.debug("Token is still valid, no refresh needed")
                return token.access_token
            
            # Get OAuth client credentials
            client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
            client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                logger.error("OAuth credentials not configured in environment")
                return None
            
            # Refresh the access token
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': token.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            logger.info(f"Refreshing OAuth token for {user_identifier}...")
            response = requests.post(token_url, data=token_data)
            
            if response.status_code != 200:
                logger.error(f'Token refresh failed: {response.text}')
                return None
            
            token_response = response.json()
            access_token = token_response.get('access_token')
            expires_in = token_response.get('expires_in', 3600)
            
            # Update token in database
            token.access_token = access_token
            token.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            token.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info('OAuth token refreshed successfully')
            return access_token
            
        except Exception as e:
            logger.error(f'Error refreshing OAuth token: {str(e)}')
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    @staticmethod
    def is_oauth_configured(user_identifier='admin'):
        """
        Check if OAuth is configured for user
        
        Args:
            user_identifier: User identifier (default: 'admin')
            
        Returns:
            bool: True if OAuth is configured
        """
        try:
            from app import DriveOAuthToken
            
            token = DriveOAuthToken.query.filter_by(user_identifier=user_identifier).first()
            return token is not None
            
        except Exception as e:
            logger.error(f"Error checking OAuth configuration: {str(e)}")
            return False
