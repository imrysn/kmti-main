import json
import os
from datetime import datetime
from utils.session_logger import log_activity

class ProfileService:
    """Service for handling user profile operations"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.profile_file = os.path.join(user_folder, "profile.json")
        self.users_file = r"\\KMTI-NAS\Shared\data\users.json"  # Main users file
        
        # Create user folder if it doesn't exist
        os.makedirs(user_folder, exist_ok=True)
    
    def load_users_data(self):
        """Load data from main users.json file"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                # Find user by username or email
                user_data = None
                for email, data in users_data.items():
                    if data.get('username') == self.username:
                        user_data = data.copy()
                        user_data['email'] = email  # Add email from key
                        break
                
                return user_data
            return None
        except Exception as e:
            print(f"Error loading users data: {e}")
            return None
    
    def load_profile(self):
        """Load user profile data from both users.json and local profile.json"""
        try:
            # First, load from main users.json file
            users_data = self.load_users_data()
            
            # Load local profile data if exists
            local_profile = {}
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    local_profile = json.load(f)
            
            # Merge data, prioritizing users.json for core fields
            if users_data:
                profile_data = {
                    # Core data from users.json
                    'username': users_data.get('username', self.username),
                    'fullname': users_data.get('fullname', self.username.title()),
                    'full_name': users_data.get('fullname', self.username.title()),  # Support both keys
                    'email': users_data.get('email', f'{self.username}@example.com'),
                    'role': users_data.get('role', 'USER'),
                    'team_tags': users_data.get('team_tags', []),
                    'join_date': users_data.get('join_date', 'N/A'),
                    
                    # Additional data from local profile or defaults
                    'bio': local_profile.get('bio', ''),
                    'location': local_profile.get('location', ''),
                    'phone': local_profile.get('phone', ''),
                    'website': local_profile.get('website', ''),
                    'avatar_path': local_profile.get('avatar_path', ''),
                    'created_date': local_profile.get('created_date', datetime.now().isoformat()),
                    'last_modified': local_profile.get('last_modified', datetime.now().isoformat()),
                    'preferences': local_profile.get('preferences', {
                        'theme': 'light',
                        'language': 'en',
                        'notifications': True,
                        'file_upload_limit': 10
                    }),
                    'stats': local_profile.get('stats', {
                        'files_uploaded': 0,
                        'total_storage_used': 0,
                        'last_login': datetime.now().isoformat()
                    })
                }
            else:
                # Fallback to local profile or defaults
                profile_data = local_profile if local_profile else self.get_default_profile()
            
            return profile_data
                
        except Exception as e:
            print(f"Error loading profile: {e}")
            return self.get_default_profile()
    
    def save_profile(self, profile_data):
        """Save user profile data (only saves local profile data, not core user data)"""
        try:
            # Only save local profile fields, not core user data
            local_profile_data = {
                'bio': profile_data.get('bio', ''),
                'location': profile_data.get('location', ''),
                'phone': profile_data.get('phone', ''),
                'website': profile_data.get('website', ''),
                'avatar_path': profile_data.get('avatar_path', ''),
                'last_modified': datetime.now().isoformat(),
                'preferences': profile_data.get('preferences', {}),
                'stats': profile_data.get('stats', {})
            }
            
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(local_profile_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to save profile: {str(e)}")
    
    def get_default_profile(self):
        """Get default profile structure"""
        return {
            "username": self.username,
            "email": f"{self.username}@gmail.com",
            "fullname": self.username.title(),
            "full_name": self.username.title(),
            "role": "USER",
            "team_tags": [],
            "join_date": "N/A",
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
        """Update a specific profile field (only local fields can be updated)"""
        try:
            profile = self.load_profile()
            
            # Only allow updating local profile fields, not core user data
            updatable_fields = ['bio', 'location', 'phone', 'website', 'avatar_path', 'preferences', 'stats']
            
            # Handle nested fields (e.g., "preferences.theme")
            if '.' in field_name:
                keys = field_name.split('.')
                if keys[0] in updatable_fields:
                    current = profile
                    for key in keys[:-1]:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    current[keys[-1]] = value
                else:
                    raise Exception(f"Field '{keys[0]}' is not updatable through profile service")
            else:
                if field_name in updatable_fields:
                    profile[field_name] = value
                else:
                    raise Exception(f"Field '{field_name}' is not updatable through profile service")
            
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
                "full_name": profile.get('fullname') or profile.get('full_name'),
                "email": profile['email'],
                "role": profile.get('role', 'USER'),
                "team_tags": profile.get('team_tags', []),
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
        required_fields = ['username', 'email', 'fullname']
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
