import os
import json
import shutil
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Set up import paths first
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from utils.file_manager import save_file
from utils.logger import log_action
from utils.session_logger import log_activity
from utils.approval import load_metadata, save_metadata, APPROVAL_QUEUE, APPROVED_DB

class FileService:
    """Service class to handle file operations with real file persistence"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.metadata_file = os.path.join(user_folder, "files_metadata.json")
        self.approval_queue = APPROVAL_QUEUE
        self.approved_db = APPROVED_DB
        
        # Ensure all required directories exist
        os.makedirs(user_folder, exist_ok=True)
        os.makedirs(os.path.join(self.approval_queue, username), exist_ok=True)
        os.makedirs(self.approved_db, exist_ok=True)
        
        # Initialize metadata file if it doesn't exist
        if not os.path.exists(self.metadata_file):
            self.save_file_metadata({})
        
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
        """Handle file upload with approval queue integration"""
        if files:
            from utils.approval import load_metadata, save_metadata
            
            for f in files:
                try:
                    # Prepare paths
                    queue_path = os.path.join(self.approval_queue, self.username)
                    os.makedirs(queue_path, exist_ok=True)
                    os.makedirs(self.user_folder, exist_ok=True)
                    
                    # Save to both locations
                    save_file(f, queue_path)  # To approval queue
                    save_file(f, self.user_folder)  # Local copy for user
                    
                    # Initialize metadata
                    file_id = f"{self.username}/{f.name}"
                    timestamp = datetime.now().isoformat()
                    
                    # Update user's local metadata
                    local_metadata = self.get_file_metadata()
                    local_metadata[f.name] = {
                        "description": "",
                        "tags": [],
                        "uploaded_date": timestamp,
                        "status": "pending_approval",
                        "comments": [],
                        "in_approval_queue": True  # Track approval status
                    }
                    self.save_file_metadata(local_metadata)
                    
                    # Update global approval metadata
                    global_metadata = load_metadata()
                    global_metadata[file_id] = {
                        "status": "pending",
                        "uploaded_by": self.username,
                        "uploaded_at": timestamp,
                        "comments": []
                    }
                    save_metadata(global_metadata)
                    
                    log_action(self.username, f"Uploaded file for approval: {f.name}")
                    log_activity(self.username, f"Uploaded file for approval: {f.name}")
                        
                except Exception as e:
                    print(f"Error uploading file {f.name}: {e}")
                    log_action(self.username, f"Failed to upload file: {f.name} - {str(e)}")
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file permanently from both user folder and approval queue"""
        try:
            success = False
            
            # Delete from user folder
            file_path = os.path.join(self.user_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                success = True
                
            # Delete from approval queue if exists
            queue_path = os.path.join(self.approval_queue, self.username, filename)
            if os.path.exists(queue_path):
                os.remove(queue_path)
                success = True
                
            if success:
                # Remove from both local and global metadata
                local_metadata = self.get_file_metadata()
                if filename in local_metadata:
                    del local_metadata[filename]
                    self.save_file_metadata(local_metadata)
                
                # Remove from global approval metadata
                from utils.approval import load_metadata, save_metadata
                global_metadata = load_metadata()
                file_id = f"{self.username}/{filename}"
                if file_id in global_metadata:
                    del global_metadata[file_id]
                    save_metadata(global_metadata)
                
                log_action(self.username, f"Deleted file: {filename}")
                log_activity(self.username, f"Deleted file: {filename}")
                return True
                
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
                    log_activity(self.username, f"Updated metadata for file: {filename}")
                    return True
                else:
                    return False
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
    
    def handle_file_approval(self, filename: str, approved: bool, comment: Optional[str] = None) -> bool:
        """Handle file approval or rejection"""
        try:
            metadata = self.get_file_metadata()
            if filename not in metadata:
                return False
                
            queue_path = os.path.join(self.approval_queue, self.username, filename)
            user_path = os.path.join(self.user_folder, filename)
            
            if approved:
                # Move file to approved database
                if os.path.exists(queue_path):
                    shutil.move(queue_path, os.path.join(self.approved_db, filename))
                    metadata[filename].update({
                        "status": "approved",
                        "approved_at": datetime.now().isoformat()
                    })
                    log_action(self.username, f"File approved: {filename}")
            else:
                # Handle rejection - file stays in user folder
                if os.path.exists(queue_path):
                    os.remove(queue_path)
                metadata[filename].update({
                    "status": "rejected",
                    "rejected_at": datetime.now().isoformat()
                })
                log_action(self.username, f"File rejected: {filename}")
            
            # Add comment if provided
            if comment:
                if "comments" not in metadata[filename]:
                    metadata[filename]["comments"] = []
                metadata[filename]["comments"].append({
                    "comment": comment,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.save_file_metadata(metadata)
            return True
            
        except Exception as e:
            print(f"Error handling file approval for {filename}: {e}")
            return False
            
    def add_to_approval_queue(self, filename: str, file_type: str, is_profile: bool = False) -> bool:
        """Add a file to the approval queue with metadata"""
        try:
            # Initialize metadata
            file_id = f"{self.username}/{filename}"
            timestamp = datetime.now().isoformat()
            
            # Update global approval metadata
            global_metadata = load_metadata()
            global_metadata[file_id] = {
                "status": "pending",
                "uploaded_by": self.username,
                "uploaded_at": timestamp,
                "type": file_type,
                "is_profile": is_profile,
                "comments": []
            }
            save_metadata(global_metadata)
            return True
            
        except Exception as e:
            print(f"Error adding to approval queue: {e}")
            return False
            
    def get_file_approval_status(self, filename: str) -> Dict:
        """Get file approval status and comments"""
        metadata = self.get_file_metadata()
        if filename in metadata:
            return {
                "status": metadata[filename].get("status", "unknown"),
                "comments": metadata[filename].get("comments", []),
                "approved_at": metadata[filename].get("approved_at"),
                "rejected_at": metadata[filename].get("rejected_at")
            }
        return {"status": "unknown", "comments": []}