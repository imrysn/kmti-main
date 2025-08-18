import shutil
import os
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict
from functools import lru_cache
from utils.config_loader import get_config

# Setup logging
logger = logging.getLogger(__name__)

# Your existing function - kept unchanged for backward compatibility
def save_file(file, dest_folder):
    """Your existing save_file function - unchanged"""
    os.makedirs(dest_folder, exist_ok=True)
    shutil.copy(file.path, os.path.join(dest_folder, file.name))

class SecurityError(Exception):
    """Custom exception for security-related file operations"""
    pass

class SecureFileManager:
    """Enhanced file manager with security validation and performance optimization"""
    
    def __init__(self):
        self.config = get_config()
        self._path_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Security patterns for input validation
        self.safe_filename_pattern = re.compile(r'^[a-zA-Z0-9\s._-]+$')
        self.safe_user_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
        logger.debug("SecureFileManager initialized")
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent security issues.
        
        Args:
            filename: Original filename from user input
            
        Returns:
            Sanitized filename safe for file operations
            
        Raises:
            SecurityError: If filename contains unsafe characters
        """
        if not filename or not isinstance(filename, str):
            raise SecurityError("Invalid filename provided")
        
        # Remove path separators and dangerous characters
        filename = filename.replace('/', '').replace('\\', '').replace('\0', '')
        filename = filename.strip(' .')
        
        # Check for Windows reserved names
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 
                         'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 
                         'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 
                         'LPT7', 'LPT8', 'LPT9'}
        
        if filename.upper() in reserved_names:
            raise SecurityError(f"Filename '{filename}' is reserved")
        
        # Validate against safe pattern
        if not self.safe_filename_pattern.match(filename):
            raise SecurityError(f"Filename contains invalid characters: {filename}")
        
        # Limit length
        if len(filename) > 255:
            raise SecurityError("Filename too long")
        
        return filename
    
    def sanitize_user_id(self, user_id: str) -> str:
        if not user_id or not isinstance(user_id, str):
            raise SecurityError("Invalid user ID provided")
        
        user_id = user_id.strip()
        
        if not self.safe_user_id_pattern.match(user_id):
            raise SecurityError(f"User ID contains invalid characters: {user_id}")
        
        if len(user_id) > 50:
            raise SecurityError("User ID too long")
        
        return user_id
    
    def validate_file_path(self, file_path: str | Path) -> Path:
        try:
            path = Path(file_path).resolve()
            
            # Check if path is within allowed directories
            if self.config.is_path_allowed(path):
                return path
            
            raise SecurityError(f"Path outside allowed directories: {file_path}")
            
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path: {file_path}") from e
    
    def secure_save_file(self, file, dest_folder: str, user_id: str = None) -> bool:
        try:
            # Validate and sanitize inputs
            safe_filename = self.sanitize_filename(file.name)
            validated_dest = self.validate_file_path(dest_folder)
            
            if user_id:
                safe_user_id = self.sanitize_user_id(user_id)
                logger.info(f"Saving file {safe_filename} for user {safe_user_id}")
            
            # Check file extension
            file_ext = Path(safe_filename).suffix.lower()
            allowed_extensions = self.config.get_file_constant('allowed_extensions', set())
            
            if file_ext not in allowed_extensions:
                raise SecurityError(f"File extension '{file_ext}' not allowed")
            
            # Check file size
            if hasattr(file, 'size'):
                max_size = self.config.get_file_constant('max_file_size', 100 * 1024 * 1024)
                if file.size > max_size:
                    raise SecurityError(f"File too large: {file.size} bytes")
            
            # Create destination directory securely
            os.makedirs(validated_dest, exist_ok=True)
            
            # Save file
            dest_path = validated_dest / safe_filename
            shutil.copy(file.path, dest_path)
            
            logger.info(f"File saved securely: {dest_path}")
            return True
            
        except SecurityError:
            logger.error(f"Security error saving file: {file.name}")
            raise
        except Exception as e:
            logger.error(f"Error saving file {file.name}: {e}")
            raise SecurityError(f"Failed to save file: {e}")
    
    @lru_cache(maxsize=100)
    def resolve_file_path(self, user_id: str, file_id: str, filename: str) -> Optional[Path]:
        cache_key = f"{user_id}:{file_id}:{filename}"
        
        if cache_key in self._path_cache:
            self._cache_hits += 1
            cached_path = self._path_cache[cache_key]
            if cached_path and cached_path.exists():
                return cached_path
            else:
                del self._path_cache[cache_key]
        
        self._cache_misses += 1
        
        # Try common file locations
        search_patterns = [
            f"data/uploads/{user_id}/{filename}",
            f"data/uploads/{user_id}/{file_id}_{filename}",
            f"data/uploads/{user_id}/{file_id}",
            f"storage/files/{file_id}",
            f"storage/{user_id}/{file_id}",
            f"storage/{user_id}/{filename}",
        ]
        
        for pattern in search_patterns:
            try:
                validated_path = self.validate_file_path(pattern)
                if validated_path.exists() and validated_path.is_file():
                    self._path_cache[cache_key] = validated_path
                    logger.debug(f"File resolved: {validated_path}")
                    return validated_path
            except SecurityError:
                continue
        
        logger.warning(f"File not found: {user_id}/{file_id}/{filename}")
        self._path_cache[cache_key] = None
        return None
    
    def safe_file_exists(self, file_path: str | Path) -> bool:
        try:
            validated_path = self.validate_file_path(file_path)
            return validated_path.exists() and validated_path.is_file()
        except SecurityError:
            logger.warning(f"Attempted access to restricted path: {file_path}")
            return False
        except Exception:
            return False
    
    def safe_read_file(self, file_path: str | Path) -> Optional[bytes]:
        validated_path = self.validate_file_path(file_path)
        
        if not validated_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not validated_path.is_file():
            raise SecurityError(f"Path is not a file: {file_path}")
        
        # Check file size before reading
        file_size = validated_path.stat().st_size
        max_size = self.config.get_file_constant('max_file_size', 100 * 1024 * 1024)
        
        if file_size > max_size:
            raise SecurityError(f"File too large: {file_size} bytes")
        
        try:
            with open(validated_path, 'rb') as f:
                return f.read()
        except PermissionError:
            raise SecurityError(f"Permission denied reading file: {file_path}")
    
    def get_safe_download_path(self, filename: str) -> Path:
        safe_filename = self.sanitize_filename(filename)
        
        # Try user's Downloads folder first
        downloads_dir = Path.home() / 'Downloads'
        if not downloads_dir.exists():
            # Fallback to current directory downloads folder
            downloads_dir = Path.cwd() / 'downloads'
            downloads_dir.mkdir(exist_ok=True)
        
        return downloads_dir / safe_filename
    
    def bulk_file_check(self, file_requests: List[Dict]) -> Dict[str, bool]:

        results = {}
        
        for request in file_requests:
            user_id = request.get('user_id')
            file_id = request.get('file_id')
            filename = request.get('filename')
            
            if not all([user_id, file_id, filename]):
                continue
            
            try:
                safe_user_id = self.sanitize_user_id(user_id)
                safe_filename = self.sanitize_filename(filename)
                
                key = f"{safe_user_id}:{file_id}:{safe_filename}"
                resolved_path = self.resolve_file_path(safe_user_id, file_id, safe_filename)
                results[key] = resolved_path is not None
                
            except SecurityError:
                results[f"{user_id}:{file_id}:{filename}"] = False
        
        return results
    
    def get_cache_stats(self) -> Dict:
        """Get file resolver cache statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self._path_cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate_percent': round(hit_rate, 2)
        }
    
    def invalidate_cache(self, user_id: str = None):
        """Invalidate file path cache"""
        if user_id:
            # Remove entries for specific user
            keys_to_remove = [k for k in self._path_cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self._path_cache[key]
        else:
            # Clear entire cache
            self._path_cache.clear()
            self.resolve_file_path.cache_clear()

# Global instance for easy access
_file_manager_instance = None

def get_file_manager() -> SecureFileManager:
    """Get global secure file manager instance"""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = SecureFileManager()
    return _file_manager_instance

# Backward compatibility wrapper that adds security to your existing function
def secure_save_file_wrapper(file, dest_folder, user_id=None):

    try:
        file_manager = get_file_manager()
        return file_manager.secure_save_file(file, dest_folder, user_id)
    except SecurityError as e:
        logger.error(f"Security error in save_file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error in save_file: {e}")
        save_file(file, dest_folder)
        return True