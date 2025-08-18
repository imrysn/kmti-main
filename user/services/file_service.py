import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from utils.file_manager import save_file
from utils.logger import log_action
from utils.session_logger import log_activity
from utils.path_config import DATA_PATHS

class FileService:
    """Fixed service - comprehensive system file filtering to prevent system files from showing in user file view"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.metadata_file = os.path.join(user_folder, "files_metadata.json")
        
        # Ensure user folder exists
        os.makedirs(user_folder, exist_ok=True)
        
        # FIXED: Comprehensive list of system files to exclude from user view
        self.system_files = {
            "files_metadata.json",
            "profile.json", 
            "file_approval_status.json",
            "approval_notifications.json",
            "profile_images"  # This is a directory
        }
    
    def get_file_metadata(self) -> Dict:
        """Load file metadata from JSON file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading file metadata: {e}")
        return {}
    
    def save_file_metadata(self, metadata: Dict) -> bool:
        """Save file metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving file metadata: {e}")
            return False
    
    def get_file_size_mb(self, file_path: str) -> str:
        """Get file size in MB format"""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            if size_mb < 0.1:
                size_kb = size_bytes / 1024
                return f"{size_kb:.1f} KB"
            return f"{size_mb:.1f} MB"
        except:
            return "Unknown"
    
    def get_file_type(self, filename: str) -> str:
        """Get file type from extension"""
        extension = os.path.splitext(filename)[1].lower()
        type_mapping = {
            '.pdf': 'PDF',
            '.doc': 'DOC',
            '.docx': 'DOCX',
            '.txt': 'TXT',
            '.jpg': 'JPG',
            '.jpeg': 'JPEG',
            '.png': 'PNG',
            '.gif': 'GIF',
            '.mp4': 'MP4',
            '.avi': 'AVI',
            '.zip': 'ZIP',
            '.rar': 'RAR',
            '.exe': 'EXE',
            '.icd': 'ICAD',
            '.sldprt': 'SLDPRT',
            '.dwg': 'DWG',
            '.step': 'STEP',
            '.iges': 'IGES'
        }
        return type_mapping.get(extension, extension.upper().replace('.', '') or 'FILE')
    
    def is_system_file(self, filename: str) -> bool:
        """Check if a file should be excluded from user view"""
        # Check exact filename matches
        if filename in self.system_files:
            return True
        
        # Check for hidden files (starting with .)
        if filename.startswith('.'):
            return True
        
        # Check for temporary files
        if filename.endswith('.tmp') or filename.endswith('.lock'):
            return True
        
        # Check for backup files
        if filename.endswith('.backup') or filename.endswith('.bak'):
            return True
        
        return False
    
    def scan_user_files(self) -> List[Dict]:
        """Scan user folder for actual files and return file information - EXCLUDES all system files"""
        files = []
        metadata = self.get_file_metadata()
        
        try:
            if os.path.exists(self.user_folder):
                for filename in os.listdir(self.user_folder):
                    file_path = os.path.join(self.user_folder, filename)
                    
                    # FIXED: Comprehensive system file filtering
                    # Skip if it's a system file
                    if self.is_system_file(filename):
                        continue
                    
                    # Skip directories (including profile_images folder)
                    if not os.path.isfile(file_path):
                        continue
                    
                    try:
                        # Get file stats
                        stat = os.stat(file_path)
                        modified_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Check if we have custom metadata for this file
                        file_metadata = metadata.get(filename, {})
                        
                        file_info = {
                            "name": filename,
                            "date_modified": modified_time.strftime("%Y/%m/%d %I:%M %p"),
                            "type": self.get_file_type(filename),
                            "size": self.get_file_size_mb(file_path),
                            "path": file_path,
                            "description": file_metadata.get("description", ""),
                            "tags": file_metadata.get("tags", [])
                        }
                        files.append(file_info)
                        
                    except (OSError, PermissionError) as e:
                        # Skip files that can't be accessed
                        print(f"[DEBUG] Skipping file {filename}: {e}")
                        continue
                        
                # Sort files by modification time (newest first)
                files.sort(key=lambda x: x["date_modified"], reverse=True)
                        
        except Exception as e:
            print(f"Error scanning user files: {e}")
            
        return files
    
    def get_files(self) -> List[Dict]:
        """Get list of user files (now scans actual files and excludes system files)"""
        return self.scan_user_files()
    
    def upload_files(self, files):
        """Handle file upload with real file saving"""
        if files:
            for f in files:
                try:
                    # Check if it's a system file name (shouldn't happen, but just in case)
                    if self.is_system_file(f.name):
                        print(f"[WARNING] Attempted to upload system file: {f.name}")
                        log_action(self.username, f"Blocked system file upload: {f.name}")
                        continue
                    
                    # Save file using existing file manager
                    save_file(f, self.user_folder)
                    log_action(self.username, f"Uploaded file: {f.name}")
                    log_activity(self.username, f"Uploaded file: {f.name}")
                    
                    # Initialize metadata for new file
                    metadata = self.get_file_metadata()
                    if f.name not in metadata:
                        metadata[f.name] = {
                            "description": "",
                            "tags": [],
                            "uploaded_date": datetime.now().isoformat()
                        }
                        self.save_file_metadata(metadata)
                        
                except Exception as e:
                    print(f"Error uploading file {f.name}: {e}")
                    log_action(self.username, f"Failed to upload file: {f.name} - {str(e)}")
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file permanently - with system file protection"""
        try:
            # FIXED: Prevent deletion of system files
            if self.is_system_file(filename):
                print(f"[SECURITY] Attempted to delete system file: {filename}")
                log_action(self.username, f"BLOCKED: Attempted to delete system file: {filename}")
                return False
            
            file_path = os.path.join(self.user_folder, filename)
            
            if os.path.exists(file_path):
                # Delete the actual file
                os.remove(file_path)
                
                # Remove from metadata
                metadata = self.get_file_metadata()
                if filename in metadata:
                    del metadata[filename]
                    self.save_file_metadata(metadata)
                
                log_action(self.username, f"Deleted file: {filename}")
                log_activity(self.username, f"Deleted file: {filename}")
                return True
            else:
                print(f"File not found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            log_action(self.username, f"Failed to delete file: {filename} - {str(e)}")
            return False
    
    def update_file_metadata(self, filename: str, description: str, tags: List[str]) -> bool:
        """Update file metadata (description and tags) - with system file protection"""
        try:
            # FIXED: Prevent modification of system file metadata
            if self.is_system_file(filename):
                print(f"[SECURITY] Attempted to modify system file metadata: {filename}")
                return False
            
            file_path = os.path.join(self.user_folder, filename)
            
            if os.path.exists(file_path):
                metadata = self.get_file_metadata()
                
                if filename not in metadata:
                    metadata[filename] = {}
                
                metadata[filename].update({
                    "description": description,
                    "tags": tags,
                    "last_edited": datetime.now().isoformat()
                })
                
                if self.save_file_metadata(metadata):
                    log_action(self.username, f"Updated metadata for file: {filename}")
                    log_activity(self.username, f"Updated metadata for file: {filename}")
                    return True
            else:
                print(f"File not found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error updating file metadata {filename}: {e}")
            return False
    
    def rename_file(self, old_filename: str, new_filename: str) -> bool:
        """Rename a file - with system file protection"""
        try:
            # FIXED: Prevent renaming of system files
            if self.is_system_file(old_filename) or self.is_system_file(new_filename):
                print(f"[SECURITY] Attempted to rename system file: {old_filename} -> {new_filename}")
                return False
            
            old_path = os.path.join(self.user_folder, old_filename)
            new_path = os.path.join(self.user_folder, new_filename)
            
            if os.path.exists(old_path) and not os.path.exists(new_path):
                # Rename the actual file
                os.rename(old_path, new_path)
                
                # Update metadata
                metadata = self.get_file_metadata()
                if old_filename in metadata:
                    metadata[new_filename] = metadata.pop(old_filename)
                    self.save_file_metadata(metadata)
                
                log_action(self.username, f"Renamed file: {old_filename} → {new_filename}")
                return True
            else:
                if not os.path.exists(old_path):
                    print(f"Source file not found: {old_filename}")
                if os.path.exists(new_path):
                    print(f"Target file already exists: {new_filename}")
                return False
                
        except Exception as e:
            print(f"Error renaming file {old_filename}: {e}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """Get detailed information about a specific file - with system file protection"""
        try:
            # FIXED: Prevent access to system file info
            if self.is_system_file(filename):
                print(f"[SECURITY] Attempted to access system file info: {filename}")
                return None
            
            file_path = os.path.join(self.user_folder, filename)
            
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                metadata = self.get_file_metadata().get(filename, {})
                
                return {
                    "name": filename,
                    "path": file_path,
                    "size": self.get_file_size_mb(file_path),
                    "size_bytes": stat.st_size,
                    "type": self.get_file_type(filename),
                    "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y/%m/%d %I:%M %p"),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y/%m/%d %I:%M %p"),
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "uploaded_date": metadata.get("uploaded_date", "")
                }
        except Exception as e:
            print(f"Error getting file info for {filename}: {e}")
        
        return None
    
    def cleanup_old_system_files(self):
        """Clean up any old system files that might be in user folder"""
        try:
            if not os.path.exists(self.user_folder):
                return
            
            cleaned_files = []
            for filename in os.listdir(self.user_folder):
                # Check for old system files that shouldn't be here
                if filename in ["file_approval_status.json", "approval_notifications.json"]:
                    file_path = os.path.join(self.user_folder, filename)
                    try:
                        # Move to backup location before deletion
                        backup_dir = os.path.join("data", "cleanup_backup", self.username)
                        os.makedirs(backup_dir, exist_ok=True)
                        backup_path = os.path.join(backup_dir, f"{filename}.backup")
                        
                        shutil.move(file_path, backup_path)
                        cleaned_files.append(filename)
                        print(f"[CLEANUP] Moved {filename} to backup for user {self.username}")
                        
                    except Exception as e:
                        print(f"[CLEANUP] Error cleaning {filename}: {e}")
            
            if cleaned_files:
                log_action(self.username, f"System cleanup: moved files {', '.join(cleaned_files)} to backup")
                
        except Exception as e:
            print(f"Cleanup error for {self.username}: {e}")
    
    def get_user_file_count(self) -> int:
        """Get count of actual user files (excluding system files)"""
        try:
            return len(self.get_files())
        except:
            return 0
    
    def get_total_file_size(self) -> int:
        """Get total size of user files in bytes (excluding system files)"""
        try:
            total_size = 0
            for file_info in self.get_files():
                try:
                    total_size += os.path.getsize(file_info["path"])
                except:
                    continue
            return total_size
        except:
            return 0