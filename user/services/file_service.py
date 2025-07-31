import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from utils.file_manager import save_file
from utils.logger import log_action

class FileService:
    """Service class to handle file operations with real file persistence"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.metadata_file = os.path.join(user_folder, "files_metadata.json")
        
        # Ensure user folder exists
        os.makedirs(user_folder, exist_ok=True)
        
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
    
    def scan_user_files(self) -> List[Dict]:
        """Scan user folder for actual files and return file information"""
        files = []
        metadata = self.get_file_metadata()
        
        try:
            if os.path.exists(self.user_folder):
                for filename in os.listdir(self.user_folder):
                    file_path = os.path.join(self.user_folder, filename)
                    
                    # Skip directories and metadata file
                    if os.path.isfile(file_path) and filename != "files_metadata.json" and filename != "profile.json":
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
                        
                # Sort files by modification time (newest first)
                files.sort(key=lambda x: x["date_modified"], reverse=True)
                        
        except Exception as e:
            print(f"Error scanning user files: {e}")
            
        return files
    
    def get_files(self) -> List[Dict]:
        """Get list of user files (now scans actual files)"""
        return self.scan_user_files()
    
    def upload_files(self, files):
        """Handle file upload with real file saving"""
        if files:
            for f in files:
                try:
                    # Save file using existing file manager
                    save_file(f, self.user_folder)
                    log_action(self.username, f"Uploaded file: {f.name}")
                    
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
        """Delete a file permanently"""
        try:
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
                return True
            else:
                print(f"File not found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            log_action(self.username, f"Failed to delete file: {filename} - {str(e)}")
            return False
    
    def update_file_metadata(self, filename: str, description: str, tags: List[str]) -> bool:
        """Update file metadata (description and tags)"""
        try:
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
                    return True
            else:
                print(f"File not found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error updating file metadata {filename}: {e}")
            return False
    
    def rename_file(self, old_filename: str, new_filename: str) -> bool:
        """Rename a file"""
        try:
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
        """Get detailed information about a specific file"""
        try:
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