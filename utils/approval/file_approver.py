"""File approval system core functionality"""
import os
import json
import shutil
from datetime import datetime
from typing import Dict, Optional, List

from .paths import APPROVAL_QUEUE, APPROVED_DB, METADATA_FILE

def ensure_dirs():
    """Ensure all required directories exist"""
    os.makedirs(APPROVAL_QUEUE, exist_ok=True)
    os.makedirs(APPROVED_DB, exist_ok=True)
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

def load_metadata() -> Dict:
    """Load approval metadata from JSON"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_metadata(metadata: Dict) -> None:
    """Save approval metadata to JSON"""
    ensure_dirs()
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

def add_comment(file_id: str, admin: str, comment: str) -> bool:
    """Add a review comment to a file"""
    metadata = load_metadata()
    if file_id not in metadata:
        metadata[file_id] = {
            "comments": [],
            "status": "pending"
        }
    
    metadata[file_id]["comments"].append({
        "comment": comment,
        "admin": admin,
        "timestamp": datetime.now().isoformat()
    })
    save_metadata(metadata)
    return True

def approve_file(user_folder: str, filename: str, admin: str, comment: Optional[str] = None) -> bool:
    """Approve and move file to public database"""
    try:
        ensure_dirs()
        src_path = os.path.join(APPROVAL_QUEUE, user_folder, filename)
        dst_path = os.path.join(APPROVED_DB, filename)
        
        # Move file to approved directory
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
        
        # Update metadata
        metadata = load_metadata()
        file_id = f"{user_folder}/{filename}"
        
        metadata[file_id] = metadata.get(file_id, {})
        metadata[file_id].update({
            "status": "approved",
            "approved_by": admin,
            "approved_at": datetime.now().isoformat()
        })
        
        if comment:
            add_comment(file_id, admin, comment)
            
        save_metadata(metadata)
        return True
        
    except Exception as e:
        print(f"Error approving file: {e}")
        return False

def reject_file(user_folder: str, filename: str, admin: str, comment: Optional[str] = None) -> bool:
    """Reject a file with optional comment"""
    try:
        ensure_dirs()
        src_path = os.path.join(APPROVAL_QUEUE, user_folder, filename)
        if os.path.exists(src_path):
            os.remove(src_path)
        
        # Update metadata
        metadata = load_metadata()
        file_id = f"{user_folder}/{filename}"
        
        metadata[file_id] = metadata.get(file_id, {})
        metadata[file_id].update({
            "status": "rejected",
            "rejected_by": admin,
            "rejected_at": datetime.now().isoformat()
        })
        
        if comment:
            add_comment(file_id, admin, comment)
            
        save_metadata(metadata)
        return True
        
    except Exception as e:
        print(f"Error rejecting file: {e}")
        return False

def get_pending_files(user_folder: Optional[str] = None) -> List[Dict]:
    """Get list of pending files, optionally filtered by user folder"""
    try:
        ensure_dirs()
        pending_files = []
        metadata = load_metadata()
        
        def scan_folder(folder_path: str, user: str) -> None:
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    if os.path.isfile(os.path.join(folder_path, filename)):
                        file_id = f"{user}/{filename}"
                        file_info = {
                            "filename": filename,
                            "user_folder": user,
                            "uploaded_at": datetime.fromtimestamp(
                                os.path.getmtime(os.path.join(folder_path, filename))
                            ).isoformat()
                        }
                        
                        # Add metadata if exists
                        if file_id in metadata:
                            file_info.update(metadata[file_id])
                            
                        # Only include if pending
                        if file_info.get("status", "pending") == "pending":
                            pending_files.append(file_info)
        
        # Scan specific user folder or all folders
        if user_folder:
            folder_path = os.path.join(APPROVAL_QUEUE, user_folder)
            scan_folder(folder_path, user_folder)
        else:
            # Scan all user folders
            if os.path.exists(APPROVAL_QUEUE):
                for user in os.listdir(APPROVAL_QUEUE):
                    user_path = os.path.join(APPROVAL_QUEUE, user)
                    if os.path.isdir(user_path):
                        scan_folder(user_path, user)
                            
        return sorted(pending_files, key=lambda x: x["uploaded_at"], reverse=True)
        
    except Exception as e:
        print(f"Error getting pending files: {e}")
        return []
