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
        """🚨 ENHANCED: Validate file path including network paths for KMTI system"""
        try:
            path = Path(file_path)
            
            # Handle network paths differently - don't resolve them as it may fail
            path_str = str(path)
            if path_str.startswith(('\\\\', '//')):  # Network path
                # For network paths, do basic validation without resolve()
                if self._is_network_path_safe(path):
                    return path
                else:
                    raise SecurityError(f"Network path outside allowed directories: {file_path}")
            else:
                # For local paths, use normal resolution
                path = path.resolve()
                
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
        """🚨 ENHANCED: Resolve file path with proper network path handling for KMTI system"""
        cache_key = f"{user_id}:{file_id}:{filename}"
        
        if cache_key in self._path_cache:
            self._cache_hits += 1
            cached_path = self._path_cache[cache_key]
            if cached_path and cached_path.exists():
                return cached_path
            else:
                del self._path_cache[cache_key]
        
        self._cache_misses += 1
        
        # 🚨 ENHANCED: Network-aware file path resolution for KMTI system
        # Try network paths first (primary locations)
        network_search_patterns = [
            # Primary network upload location
            f"\\\\KMTI-NAS\\Shared\\data\\uploads\\{user_id}\\{filename}",
            # Project directories (for approved files)
            f"\\\\KMTI-NAS\\Database\\PROJECTS\\*\\{filename}",  # Will need wildcard handling
            # Fallback staging areas
            f"\\\\KMTI-NAS\\Shared\\data\\approved_files_staging\\*\\{filename}",
        ]
        
        # Local fallback patterns
        local_search_patterns = [
            f"data/uploads/{user_id}/{filename}",
            f"data/uploads/{user_id}/{file_id}_{filename}",
            f"data/uploads/{user_id}/{file_id}",
            f"storage/files/{file_id}",
            f"storage/{user_id}/{file_id}",
            f"storage/{user_id}/{filename}",
        ]
        
        # First, try direct network paths
        for pattern in network_search_patterns:
            try:
                if '*' in pattern:
                    # Handle wildcard patterns (e.g., for project directories)
                    resolved_path = self._resolve_wildcard_path(pattern, filename)
                    if resolved_path and resolved_path.exists() and resolved_path.is_file():
                        self._path_cache[cache_key] = resolved_path
                        logger.debug(f"File resolved (network wildcard): {resolved_path}")
                        return resolved_path
                else:
                    # Direct network path
                    network_path = Path(pattern)
                    if network_path.exists() and network_path.is_file():
                        # Validate path security (even for network paths)
                        if self._is_network_path_safe(network_path):
                            self._path_cache[cache_key] = network_path
                            logger.debug(f"File resolved (network): {network_path}")
                            return network_path
                        else:
                            logger.warning(f"Network path failed security check: {network_path}")
            except (OSError, ValueError) as e:
                logger.debug(f"Network path resolution failed for {pattern}: {e}")
                continue
        
        # Then try local fallback patterns
        for pattern in local_search_patterns:
            try:
                local_path = Path(pattern)
                validated_path = self.validate_file_path(local_path)
                if validated_path.exists() and validated_path.is_file():
                    self._path_cache[cache_key] = validated_path
                    logger.debug(f"File resolved (local): {validated_path}")
                    return validated_path
            except SecurityError:
                continue
            except (OSError, ValueError):
                continue
        
        logger.warning(f"File not found in any location: {user_id}/{file_id}/{filename}")
        self._path_cache[cache_key] = None
        return None
    
    def _resolve_wildcard_path(self, pattern: str, filename: str) -> Optional[Path]:
        """Resolve wildcard patterns in network paths"""
        try:
            # Split pattern at wildcard
            before_wildcard, after_wildcard = pattern.split('*', 1)
            base_path = Path(before_wildcard)
            
            if not base_path.exists():
                return None
            
            # Search through subdirectories
            for item in base_path.iterdir():
                if item.is_dir():
                    potential_path = item / after_wildcard.lstrip('\\\\')
                    if potential_path.exists() and potential_path.is_file():
                        if potential_path.name == filename:  # Ensure filename matches
                            return potential_path
            
            return None
            
        except Exception as e:
            logger.debug(f"Wildcard resolution failed for {pattern}: {e}")
            return None
    
    def _is_network_path_safe(self, network_path: Path) -> bool:
        """Check if network path is within allowed KMTI network locations"""
        try:
            path_str = str(network_path).lower()
            
            # Allowed KMTI network locations
            allowed_network_bases = [
                r'\\kmti-nas\shared\data',
                r'\\kmti-nas\database\projects',
                r'/kmti-nas/shared/data',  # Linux-style paths
                r'/kmti-nas/database/projects'
            ]
            
            # Check if path starts with any allowed base
            for base in allowed_network_bases:
                if path_str.startswith(base.lower()):
                    return True
            
            return False
            
        except Exception:
            return False
    
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