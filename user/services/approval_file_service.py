"""
User-side approval service that integrates with the main approval system
Uses the central new_approval_service.py for backend operations
"""

import os
import json
import uuid
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from services.file_approval_constant import FileApprovalStatus
from utils.logger import log_action
from utils.session_logger import log_activity

class ApprovalFileService:
    """Clean user-side approval service - works with new_approval_service.py backend"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder  # For user uploads only
        self.username = username
        
        # Store system files in data folder, not user upload folder
        self.system_data_folder = os.path.join("data", "user_approvals", username)
        self.approval_status_file = os.path.join(self.system_data_folder, "file_approval_status.json")
        self.notifications_file = os.path.join(self.system_data_folder, "approval_notifications.json")
        
        # Ensure folders exist
        os.makedirs(user_folder, exist_ok=True)
        os.makedirs(self.system_data_folder, exist_ok=True)
        
        # Cache for approval data
        self._approval_cache = {}
        self._cache_timestamp = 0
        self._cache_lock = threading.Lock()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Get user team (cached)
        self.user_team = self._get_user_team_cached()
        
        # Import the main approval service
        from services.new_approval_service import NewFileApprovalService
        self.main_approval_service = NewFileApprovalService()
    
    def _get_user_team_cached(self) -> str:
        """Get user's team from users.json with caching"""
        try:
            users_file = r"\\KMTI-NAS\Shared\data\users.json"
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                for email, data in users.items():
                    if data.get('username') == self.username:
                        teams = data.get('team_tags', [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error getting user team: {e}")
        return "DEFAULT"
    
    def get_user_team(self) -> str:
        """Get user's team (backward compatibility)"""
        return self.user_team
    
    def _update_approval_cache(self, force_refresh: bool = False):
        """Update internal cache of approval data"""
        with self._cache_lock:
            current_time = time.time()
            
            if not force_refresh and (current_time - self._cache_timestamp < 2.0):
                return
            
            try:
                if os.path.exists(self.approval_status_file):
                    with open(self.approval_status_file, 'r', encoding='utf-8') as f:
                        self._approval_cache = json.load(f)
                else:
                    self._approval_cache = {}
                
                self._cache_timestamp = current_time
                
            except Exception as e:
                print(f"Cache update error: {e}")
                self._approval_cache = {}
    
    def load_approval_status(self) -> Dict:
        """Load approval status with caching"""
        self._update_approval_cache()
        with self._cache_lock:
            return self._approval_cache.copy()
    
    def save_approval_status(self, status_data: Dict) -> bool:
        """Save approval status with cache update"""
        try:
            os.makedirs(os.path.dirname(self.approval_status_file), exist_ok=True)
            with open(self.approval_status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2)
            
            # Update cache immediately
            with self._cache_lock:
                self._approval_cache = status_data.copy()
                self._cache_timestamp = time.time()
            
            return True
        except Exception as e:
            print(f"Error saving approval status: {e}")
            return False
    
    def load_notifications(self) -> List[Dict]:
        """Load user's approval notifications"""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
                    return notifications if isinstance(notifications, list) else []
        except Exception as e:
            print(f"Error loading notifications: {e}")
        return []
    
    def save_notifications(self, notifications: List[Dict]) -> bool:
        """Save user's approval notifications"""
        try:
            os.makedirs(os.path.dirname(self.notifications_file), exist_ok=True)
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving notifications: {e}")
            return False
    
    def get_uploaded_files(self) -> List[Dict]:
        """Get all uploaded files with approval status - EXCLUDES system files"""
        files = []
        approval_data = self.load_approval_status()  # Uses cache
        
        try:
            if os.path.exists(self.user_folder):
                # Exclude system files
                excluded_files = {
                    "files_metadata.json", 
                    "profile.json", 
                    "file_approval_status.json", 
                    "approval_notifications.json"
                }
                
                for filename in os.listdir(self.user_folder):
                    if filename in excluded_files or filename.startswith("."):
                        continue
                    
                    file_path = os.path.join(self.user_folder, filename)
                    
                    # Skip directories
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Get file stats
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Get approval status
                    file_approval = approval_data.get(filename, {
                        "status": FileApprovalStatus.MY_FILES,
                        "submitted_for_approval": False,
                        "submission_date": None,
                        "admin_comments": [],
                        "status_history": [],
                        "description": "",
                        "tags": []
                    })
                    
                    file_info = {
                        "filename": filename,
                        "file_path": file_path,
                        "file_size": stat.st_size,
                        "upload_date": modified_time.isoformat(),
                        **file_approval  # Merge approval data
                    }
                    files.append(file_info)
                
                # Sort files by upload time (newest first)
                files.sort(key=lambda x: x["upload_date"], reverse=True)
                        
        except Exception as e:
            print(f"Error getting uploaded files: {e}")
            
        return files
    
    def submit_file_for_approval(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """Submit an uploaded file for approval using the main approval service"""
        try:
            file_path = os.path.join(self.user_folder, filename)
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            if tags is None:
                tags = []
            
            # Submit through main approval service
            file_id = self.main_approval_service.submit_file_for_approval(
                user_id=self.username,
                filename=filename, 
                file_path=file_path,
                user_team=self.user_team,
                description=description,
                tags=tags
            )
            
            if file_id:
                # Update local approval status
                approval_data = self.load_approval_status()
                approval_data[filename] = {
                    "file_id": file_id,
                    "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                    "submitted_for_approval": True,
                    "submission_date": datetime.now().isoformat(),
                    "description": description,
                    "tags": tags,
                    "admin_comments": [],
                    "status_history": [{
                        "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                        "timestamp": datetime.now().isoformat(),
                        "comment": "File submitted for team leader review"
                    }]
                }
                
                if self.save_approval_status(approval_data):
                    # Log in background
                    self.executor.submit(self._log_submission_async, filename)
                    return True
                
        except Exception as e:
            print(f"Error submitting file for approval: {e}")
        
        return False
    
    def _log_submission_async(self, filename: str):
        """Log submission asynchronously"""
        try:
            log_action(self.username, f"Submitted file for approval: {filename}")
            log_activity(self.username, f"Submitted file for approval: {filename}")
        except Exception as e:
            print(f"Async logging error: {e}")
    
    def withdraw_submission(self, filename: str) -> bool:
        """Withdraw submission using the main approval service"""
        try:
            # Get file_id from local status
            approval_data = self.load_approval_status()
            
            if filename not in approval_data:
                return False
            
            file_data = approval_data[filename]
            current_status = file_data.get("status", FileApprovalStatus.MY_FILES)
            
            if current_status not in [FileApprovalStatus.PENDING_TEAM_LEADER, FileApprovalStatus.PENDING_ADMIN]:
                return False
            
            file_id = file_data.get("file_id")
            if not file_id:
                return False
            
            # Withdraw through main service
            success = self.main_approval_service.withdraw_submission(file_id)
            
            if success:
                # Update local status
                approval_data[filename] = {
                    "status": FileApprovalStatus.MY_FILES,
                    "submitted_for_approval": False,
                    "submission_date": None,
                    "admin_comments": [],
                    "status_history": file_data.get("status_history", []) + [{
                        "status": FileApprovalStatus.WITHDRAWN,
                        "timestamp": datetime.now().isoformat(),
                        "comment": "Submission withdrawn by user"
                    }],
                    "description": "",
                    "tags": [],
                    "withdrawn_date": datetime.now().isoformat()
                }
                
                if self.save_approval_status(approval_data):
                    self.executor.submit(self._log_withdrawal_async, filename)
                    return True
            
        except Exception as e:
            print(f"Error withdrawing submission: {e}")
        
        return False
    
    def _log_withdrawal_async(self, filename: str):
        """Log withdrawal actions asynchronously"""
        try:
            log_action(self.username, f"Withdrew submission: {filename}")
            log_activity(self.username, f"Withdrew submission: {filename}")
        except Exception as e:
            print(f"Logging error: {e}")
    
    def get_user_submissions(self) -> List[Dict]:
        """Get all files with their approval status for submissions view"""
        files = self.get_uploaded_files()
        
        submissions = []
        for file_info in files:
            if file_info["submitted_for_approval"] or file_info["status"] != FileApprovalStatus.MY_FILES:
                submission = {
                    "original_filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "upload_date": file_info["upload_date"],
                    "submission_date": file_info["submission_date"],
                    "status": file_info["status"],
                    "description": file_info["description"],
                    "tags": file_info["tags"],
                    "admin_comments": file_info["admin_comments"],
                    "status_history": file_info["status_history"]
                }
                submissions.append(submission)
        
        return submissions
    
    def get_available_files_for_submission(self) -> List[Dict]:
        """Get files available for submission"""
        files = self.get_uploaded_files()
        
        available_files = []
        for file_info in files:
            if not file_info["submitted_for_approval"] and file_info["status"] == FileApprovalStatus.MY_FILES:
                available = {
                    "filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "upload_date": file_info["upload_date"]
                }
                available_files.append(available)
        
        return available_files
    
    def update_file_status(self, filename: str, new_status: str, admin_comment: str = "", admin_id: str = ""):
        """Update file status (called by admin system)"""
        try:
            approval_data = self.load_approval_status()
            
            if filename in approval_data:
                approval_data[filename]["status"] = new_status
                approval_data[filename]["last_updated"] = datetime.now().isoformat()
                
                # Add admin comment if provided
                if admin_comment:
                    if "admin_comments" not in approval_data[filename]:
                        approval_data[filename]["admin_comments"] = []
                    
                    approval_data[filename]["admin_comments"].append({
                        "admin_id": admin_id,
                        "comment": admin_comment,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Add to status history
                if "status_history" not in approval_data[filename]:
                    approval_data[filename]["status_history"] = []
                
                approval_data[filename]["status_history"].append({
                    "status": new_status,
                    "timestamp": datetime.now().isoformat(),
                    "admin_id": admin_id,
                    "comment": admin_comment
                })
                
                self.save_approval_status(approval_data)
                
                # Add notification
                self.add_notification({
                    "type": "status_update",
                    "filename": filename,
                    "old_status": "pending",
                    "new_status": new_status,
                    "admin_id": admin_id,
                    "comment": admin_comment,
                    "timestamp": datetime.now().isoformat(),
                    "read": False
                })
                
                return True
        except Exception as e:
            print(f"Error updating file status: {e}")
        return False
    
    def add_notification(self, notification: Dict):
        """Add notification"""
        try:
            notifications = self.load_notifications()
            notifications.insert(0, notification)
            
            # Keep only last 50 notifications
            notifications = notifications[:50]
            
            self.save_notifications(notifications)
        except Exception as e:
            print(f"Error adding notification: {e}")
    
    def mark_notification_read(self, notification_index: int):
        """Mark notification as read"""
        try:
            notifications = self.load_notifications()
            if 0 <= notification_index < len(notifications):
                notifications[notification_index]["read"] = True
                self.save_notifications(notifications)
                return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
        return False
    
    def get_unread_notification_count(self) -> int:
        """Get unread notification count"""
        try:
            notifications = self.load_notifications()
            return sum(1 for n in notifications if not n.get("read", False))
        except:
            return 0
    
    def resubmit_file(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """Resubmit a file that was rejected or needed changes"""
        try:
            approval_data = self.load_approval_status()
            
            if filename in approval_data:
                file_data = approval_data[filename]
                current_status = file_data.get("status")
                
                # Only allow resubmission of rejected or changes_requested files
                if current_status not in [FileApprovalStatus.REJECTED_TEAM_LEADER, FileApprovalStatus.REJECTED_ADMIN, FileApprovalStatus.CHANGES_REQUESTED]:
                    return False
                
                # Submit as new file
                file_path = os.path.join(self.user_folder, filename)
                if not os.path.exists(file_path):
                    return False
                
                # Use main approval service to resubmit
                file_id = self.main_approval_service.submit_file_for_approval(
                    user_id=self.username,
                    filename=filename,
                    file_path=file_path,
                    user_team=self.user_team,
                    description=description or file_data.get("description", ""),
                    tags=tags or file_data.get("tags", [])
                )
                
                if file_id:
                    # Update local status
                    approval_data[filename].update({
                        "file_id": file_id,
                        "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                        "description": description or file_data.get("description", ""),
                        "tags": tags or file_data.get("tags", []),
                        "resubmission_date": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    })
                    
                    approval_data[filename]["status_history"].append({
                        "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                        "timestamp": datetime.now().isoformat(),
                        "comment": "File resubmitted after changes"
                    })
                    
                    # Clear admin comments for fresh review
                    approval_data[filename]["admin_comments"] = []
                    
                    self.save_approval_status(approval_data)
                    self.executor.submit(self._log_resubmission_async, filename)
                    
                    return True
        except Exception as e:
            print(f"Error resubmitting file: {e}")
        return False
    
    def _log_resubmission_async(self, filename: str):
        """Log resubmission asynchronously"""
        try:
            log_action(self.username, f"Resubmitted file: {filename}")
            log_activity(self.username, f"Resubmitted file: {filename}")
        except Exception as e:
            print(f"Resubmission logging error: {e}")
    
    def get_submission_by_filename(self, filename: str) -> Optional[Dict]:
        """Get specific submission by filename"""
        approval_data = self.load_approval_status()
        if filename in approval_data:
            file_path = os.path.join(self.user_folder, filename)
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                submission_data = approval_data[filename].copy()
                submission_data.update({
                    "original_filename": filename,
                    "file_size": file_stat.st_size,
                    "upload_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
                return submission_data
        return None
    
    def cleanup_resources(self):
        """Cleanup resources when done"""
        try:
            self.executor.shutdown(wait=False)
        except:
            pass
