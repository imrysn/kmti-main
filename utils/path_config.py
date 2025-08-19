"""
Centralized path configuration for KMTI Data Management System
This file defines all data paths used throughout the application
"""
import os
from pathlib import Path

# Network data directory (main data storage)
NETWORK_DATA_DIR = r"\\KMTI-NAS\Shared\data"

# Local data directory (for sessions, logs, and local config)
LOCAL_DATA_DIR = "data"

# Ensure directories exist
os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
try:
    os.makedirs(NETWORK_DATA_DIR, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create network directory {NETWORK_DATA_DIR}: {e}")

class DataPaths:
    """Centralized data paths configuration"""
    
    # Base directories
    NETWORK_BASE = NETWORK_DATA_DIR
    LOCAL_BASE = LOCAL_DATA_DIR
    
    # Network paths (shared data)
    @property
    def approvals_dir(self):
        return os.path.join(self.NETWORK_BASE, "approvals")
    
    @property
    def file_approvals_file(self):
        return os.path.join(self.approvals_dir, "file_approvals.json")
    
    @property
    def comments_file(self):
        return os.path.join(self.approvals_dir, "comments.json")
    
    @property
    def uploads_dir(self):
        return os.path.join(self.NETWORK_BASE, "uploads")
    
    @property
    def user_approvals_dir(self):
        return os.path.join(self.NETWORK_BASE, "user_approvals")
    
    @property
    def users_file(self):
        return os.path.join(self.NETWORK_BASE, "users.json")
    
    @property
    def config_file(self):
        return os.path.join(self.NETWORK_BASE, "config.json")
    
    @property
    def cache_dir(self):
        return os.path.join(self.NETWORK_BASE, "cache")
    
    @property
    def notifications_dir(self):
        return os.path.join(self.NETWORK_BASE, "notifications")
    
    # Local paths (not shared)
    @property
    def local_sessions_dir(self):
        return os.path.join(self.LOCAL_BASE, "sessions")
    
    @property
    def local_logs_dir(self):
        return os.path.join(self.LOCAL_BASE, "logs")
    
    @property
    def local_config_file(self):
        return os.path.join(self.LOCAL_BASE, "config.json")
    
    # User-specific paths
    def get_user_upload_dir(self, username: str):
        """Get user's upload directory"""
        return os.path.join(self.uploads_dir, username)
    
    def get_user_approval_dir(self, username: str):
        """Get user's approval data directory"""
        return os.path.join(self.user_approvals_dir, username)
    
    def get_user_approval_status_file(self, username: str):
        """Get user's approval status file"""
        return os.path.join(self.get_user_approval_dir(username), "file_approval_status.json")
    
    def get_user_notifications_file(self, username: str):
        """Get user's notifications file"""
        return os.path.join(self.get_user_approval_dir(username), "approval_notifications.json")
    
    def get_user_profile_images_dir(self, username: str):
        """Get user's profile images directory"""
        return os.path.join(self.get_user_upload_dir(username), "profile_images")
    
    # Utility methods
    def ensure_network_dirs(self):
        """Ensure all network directories exist"""
        directories = [
            self.approvals_dir,
            self.uploads_dir,
            self.user_approvals_dir,
            self.cache_dir,
            self.notifications_dir
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"[PATH_CONFIG] Ensured directory: {directory}")
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")
    
    def ensure_local_dirs(self):
        """Ensure all local directories exist"""
        directories = [
            self.local_sessions_dir,
            self.local_logs_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def ensure_user_dirs(self, username: str):
        """Ensure all user-specific directories exist"""
        directories = [
            self.get_user_upload_dir(username),
            self.get_user_approval_dir(username),
            self.get_user_profile_images_dir(username)
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")
    
    def is_network_available(self):
        """Check if network directory is accessible"""
        return os.path.exists(self.NETWORK_BASE)

# Global instance
DATA_PATHS = DataPaths()

# Initialize directories
DATA_PATHS.ensure_local_dirs()
if DATA_PATHS.is_network_available():
    DATA_PATHS.ensure_network_dirs()
else:
    print(f"Warning: Network directory {NETWORK_DATA_DIR} is not accessible")

# Backward compatibility functions
def get_base_dir():
    """Backward compatibility - returns network base directory"""
    return Path(DATA_PATHS.NETWORK_BASE)

def get_network_data_dir():
    """Get network data directory"""
    return DATA_PATHS.NETWORK_BASE

def get_local_data_dir():
    """Get local data directory"""
    return DATA_PATHS.LOCAL_BASE
