import os
import shutil
from typing import Optional
import uuid


class ProfileImageService:
    """Service for handling profile image operations"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.profile_images_folder = os.path.join(user_folder, "profile_images")
        
        # Ensure the profile images folder exists
        os.makedirs(self.profile_images_folder, exist_ok=True)
    
    def get_profile_image_path(self) -> Optional[str]:
        """Get the path to the user's profile image if it exists"""
        # Check for common image extensions
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        
        for ext in extensions:
            image_path = os.path.join(self.profile_images_folder, f"profile{ext}")
            if os.path.exists(image_path):
                return image_path
        
        return None
    
    def has_profile_image(self) -> bool:
        """Check if user has a profile image"""
        return self.get_profile_image_path() is not None
    
    def upload_profile_image(self, source_path: str) -> bool:
        """Upload a new profile image, replacing any existing one"""
        try:
            # Remove any existing profile images first
            self.remove_profile_image()
            
            # Get file extension from source
            file_ext = os.path.splitext(source_path)[1].lower()
            
            # Validate extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            if file_ext not in valid_extensions:
                return False
            
            # Create destination path
            dest_path = os.path.join(self.profile_images_folder, f"profile{file_ext}")
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            return True
            
        except Exception as e:
            print(f"Error uploading profile image: {e}")
            return False
    
    def remove_profile_image(self) -> bool:
        """Remove the user's profile image"""
        try:
            existing_image = self.get_profile_image_path()
            if existing_image and os.path.exists(existing_image):
                os.remove(existing_image)
            return True
        except Exception as e:
            print(f"Error removing profile image: {e}")
            return False
    
    def get_profile_image_url(self) -> Optional[str]:
        """Get URL/path for web display (same as get_profile_image_path for local files)"""
        return self.get_profile_image_path()
    
    def validate_image_file(self, file_path: str) -> tuple[bool, str]:
        """Validate an image file"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            
            if file_ext not in valid_extensions:
                return False, f"Invalid file type. Supported: {', '.join(valid_extensions)}"
            
            # Check file size (10MB limit)
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024  # 10MB
            
            if file_size > max_size:
                return False, "File size too large (max 10MB)"
            
            return True, "Valid image file"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def get_profile_image_info(self) -> dict:
        """Get information about the current profile image"""
        image_path = self.get_profile_image_path()
        
        if not image_path:
            return {
                "has_image": False,
                "path": None,
                "size": 0,
                "extension": None
            }
        
        try:
            file_size = os.path.getsize(image_path)
            file_ext = os.path.splitext(image_path)[1].lower()
            
            return {
                "has_image": True,
                "path": image_path,
                "size": file_size,
                "extension": file_ext
            }
        except:
            return {
                "has_image": False,
                "path": None,
                "size": 0,
                "extension": None
            }