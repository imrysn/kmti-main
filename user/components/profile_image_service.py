import os
import shutil
import time
from typing import Optional


class ProfileImageService:
    """Service for handling profile image operations with cache busting support"""
    
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
        
        try:
            if not os.path.exists(self.profile_images_folder):
                return None
                
            # Look for any image file in the folder (now supports timestamped filenames)
            for filename in os.listdir(self.profile_images_folder):
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in extensions:
                    return os.path.join(self.profile_images_folder, filename)
        except Exception as e:
            print(f"Error getting profile image path: {e}")
        
        return None
    
    def has_profile_image(self) -> bool:
        """Check if user has a profile image"""
        return self.get_profile_image_path() is not None
    
    def upload_profile_image(self, source_path: str) -> bool:
        """Upload a new profile image with timestamp for cache busting"""
        try:
            # Remove any existing profile images first
            self.remove_profile_image()
            
            # Get file extension from source
            file_ext = os.path.splitext(source_path)[1].lower()
            
            # Validate extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            if file_ext not in valid_extensions:
                return False
            
            # Create destination path with timestamp for cache busting
            timestamp = int(time.time())
            filename = f"profile_{timestamp}{file_ext}"
            dest_path = os.path.join(self.profile_images_folder, filename)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            return True
            
        except Exception as e:
            print(f"Error uploading profile image: {e}")
            return False
    
    def remove_profile_image(self) -> bool:
        """Remove the user's profile image"""
        try:
            if not os.path.exists(self.profile_images_folder):
                return True
                
            # Remove all image files in the profile images folder
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            
            for filename in os.listdir(self.profile_images_folder):
                file_path = os.path.join(self.profile_images_folder, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in extensions and os.path.isfile(file_path):
                    os.remove(file_path)
            
            return True
            
        except Exception as e:
            print(f"Error removing profile image: {e}")
            return False
    
    def get_profile_image_url_with_cache_buster(self) -> Optional[str]:
        """Get profile image URL with cache buster for immediate updates"""
        image_path = self.get_profile_image_path()
        
        if not image_path or not os.path.exists(image_path):
            return None
            
        try:
            # Use file modification time as cache buster
            mtime = int(os.path.getmtime(image_path) * 1000)  # Milliseconds for precision
            abs_path = os.path.abspath(image_path)
            return f"{abs_path}?v={mtime}"
        except Exception as e:
            print(f"Error getting cache-busted URL: {e}")
            return os.path.abspath(image_path)
    
    def get_profile_image_url(self) -> Optional[str]:
        """Get URL/path for web display (with cache busting)"""
        return self.get_profile_image_url_with_cache_buster()
    
    def validate_image_file(self, file_path: str) -> tuple[bool, str]:
        """Validate an image file with comprehensive checks"""
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
            
            # Check if it's actually an image (basic check)
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    img.verify()  # Verify it's a valid image
            except ImportError:
                # PIL not available, skip image verification
                pass
            except Exception:
                return False, "File appears to be corrupted or not a valid image"
            
            return True, "Valid image file"
            
        except Exception as e:
            return False, f"Error validating file: {str(e)}"
    
    def get_profile_image_info(self) -> dict:
        """Get comprehensive information about the current profile image"""
        image_path = self.get_profile_image_path()
        
        if not image_path or not os.path.exists(image_path):
            return {
                "has_image": False,
                "path": None,
                "url": None,
                "size": 0,
                "size_mb": 0,
                "extension": None,
                "modified_time": None,
                "cache_buster": None
            }
        
        try:
            file_size = os.path.getsize(image_path)
            file_ext = os.path.splitext(image_path)[1].lower()
            modified_time = os.path.getmtime(image_path)
            cache_buster = int(modified_time * 1000)
            
            return {
                "has_image": True,
                "path": image_path,
                "url": self.get_profile_image_url_with_cache_buster(),
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "extension": file_ext,
                "modified_time": modified_time,
                "cache_buster": cache_buster
            }
            
        except Exception as e:
            print(f"Error getting profile image info: {e}")
            return {
                "has_image": False,
                "path": None,
                "url": None,
                "size": 0,
                "size_mb": 0,
                "extension": None,
                "modified_time": None,
                "cache_buster": None
            }
    
    def cleanup_old_images(self, keep_latest: int = 1):
        """Clean up old profile images, keeping only the latest ones"""
        try:
            if not os.path.exists(self.profile_images_folder):
                return True
                
            extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            image_files = []
            
            # Get all image files with their modification times
            for filename in os.listdir(self.profile_images_folder):
                file_path = os.path.join(self.profile_images_folder, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in extensions and os.path.isfile(file_path):
                    mtime = os.path.getmtime(file_path)
                    image_files.append((file_path, mtime))
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old files, keeping only the latest ones
            for i, (file_path, _) in enumerate(image_files):
                if i >= keep_latest:
                    os.remove(file_path)
                    print(f"Cleaned up old profile image: {file_path}")
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up old images: {e}")
            return False