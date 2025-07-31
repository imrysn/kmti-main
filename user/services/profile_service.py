import json
import os
from datetime import datetime

class ProfileService:
    """Service for handling user profile operations"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.profile_file = os.path.join(user_folder, "profile.json")
        
        # Create user folder if it doesn't exist
        os.makedirs(user_folder, exist_ok=True)
    
    def load_profile(self):
        """Load user profile data"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    
                # Ensure all required fields exist
                default_profile = self.get_default_profile()
                for key, value in default_profile.items():
                    if key not in profile_data:
                        profile_data[key] = value
                
                return profile_data
            else:
                # Create default profile
                return self.create_default_profile()
                
        except Exception as e:
            print(f"Error loading profile: {e}")
            return self.get_default_profile()
    
    def save_profile(self, profile_data):
        """Save user profile data"""
        try:
            # Update last modified timestamp
            profile_data['last_modified'] = datetime.now().isoformat()
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to save profile: {str(e)}")
    
    def get_default_profile(self):
        """Get default profile structure"""
        return {
            "username": self.username,
            "email": f"{self.username}@example.com",
            "full_name": self.username.title(),
            "bio": "",
            "location": "",
            "phone": "",
            "website": "",
            "avatar_path": "",
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "preferences": {
                "theme": "light",
                "language": "en",
                "notifications": True,
                "file_upload_limit": 10  # MB
            },
            "stats": {
                "files_uploaded": 0,
                "total_storage_used": 0,
                "last_login": datetime.now().isoformat()
            }
        }
    
    def create_default_profile(self):
        """Create and save default profile"""
        default_profile = self.get_default_profile()
        self.save_profile(default_profile)
        return default_profile
    
    def update_profile_field(self, field_name, value):
        """Update a specific profile field"""
        try:
            profile = self.load_profile()
            
            # Handle nested fields (e.g., "preferences.theme")
            if '.' in field_name:
                keys = field_name.split('.')
                current = profile
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = value
            else:
                profile[field_name] = value
            
            self.save_profile(profile)
            return True
            
        except Exception as e:
            raise Exception(f"Failed to update profile field: {str(e)}")
    
    def update_stats(self, **kwargs):
        """Update profile statistics"""
        try:
            profile = self.load_profile()
            
            for key, value in kwargs.items():
                if key in profile['stats']:
                    if isinstance(value, (int, float)) and key != 'last_login':
                        # For numeric values, add to existing value
                        profile['stats'][key] += value
                    else:
                        # For other values, replace
                        profile['stats'][key] = value
            
            self.save_profile(profile)
            return True
            
        except Exception as e:
            raise Exception(f"Failed to update stats: {str(e)}")
    
    def get_profile_summary(self):
        """Get a summary of profile information"""
        try:
            profile = self.load_profile()
            
            # Calculate account age
            created_date = datetime.fromisoformat(profile['created_date'])
            account_age_days = (datetime.now() - created_date).days
            
            return {
                "username": profile['username'],
                "full_name": profile['full_name'],
                "email": profile['email'],
                "account_age_days": account_age_days,
                "files_count": profile['stats']['files_uploaded'],
                "storage_used_mb": profile['stats']['total_storage_used'] / (1024 * 1024),
                "last_login": profile['stats']['last_login']
            }
            
        except Exception as e:
            raise Exception(f"Failed to get profile summary: {str(e)}")
    
    def validate_profile_data(self, profile_data):
        """Validate profile data before saving"""
        errors = []
        
        # Required fields
        required_fields = ['username', 'email', 'full_name']
        for field in required_fields:
            if not profile_data.get(field):
                errors.append(f"{field} is required")
        
        # Email validation
        email = profile_data.get('email', '')
        if email and '@' not in email:
            errors.append("Invalid email format")
        
        # Username validation
        username = profile_data.get('username', '')
        if username and (len(username) < 3 or not username.replace('_', '').isalnum()):
            errors.append("Username must be at least 3 characters and contain only letters, numbers, and underscores")
        
        return errors
    
    def backup_profile(self):
        """Create a backup of the current profile"""
        try:
            if os.path.exists(self.profile_file):
                backup_file = f"{self.profile_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(self.profile_file, backup_file)
                return backup_file
            return None
            
        except Exception as e:
            raise Exception(f"Failed to backup profile: {str(e)}")
    
    def restore_profile_from_backup(self, backup_file):
        """Restore profile from backup file"""
        try:
            if os.path.exists(backup_file):
                import shutil
                shutil.copy2(backup_file, self.profile_file)
                return True
            else:
                raise FileNotFoundError("Backup file not found")
                
        except Exception as e:
            raise Exception(f"Failed to restore profile: {str(e)}")
    
    def delete_profile(self):
        """Delete user profile (use with caution)"""
        try:
            if os.path.exists(self.profile_file):
                # Create backup before deletion
                backup_file = self.backup_profile()
                os.remove(self.profile_file)
                return backup_file
            return None
            
        except Exception as e:
            raise Exception(f"Failed to delete profile: {str(e)}")