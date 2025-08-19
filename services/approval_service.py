import os
import json
import uuid
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from utils.logger import log_action
from utils.session_logger import log_activity
from utils.path_config import DATA_PATHS
from services.enhanced_file_movement_service import get_enhanced_file_movement_service

class ApprovalStatus(Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    WITHDRAWN = "withdrawn"

class ApprovalFileService:
    """User-side approval service - system files stored in data folder, not user upload folder"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder  # This is for user uploads only
        self.username = username
        
        # Store system files in network data folder, not user upload folder
        self.system_data_folder = DATA_PATHS.get_user_approval_dir(username)
        self.approval_status_file = DATA_PATHS.get_user_approval_status_file(username)
        self.notifications_file = DATA_PATHS.get_user_notifications_file(username)
        
        # Ensure folders exist
        os.makedirs(user_folder, exist_ok=True)
        os.makedirs(self.system_data_folder, exist_ok=True)
        
        # Migrate existing files if they exist in wrong location
        self._migrate_system_files()
        
        # Cache for approval data to reduce file I/O
        self._approval_cache = {}
        self._cache_timestamp = 0
        self._cache_lock = threading.Lock()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Get user team (cached)
        self.user_team = self._get_user_team_cached()
    
    def _migrate_system_files(self):
        """Migrate system files from user folder to data folder if they exist"""
        try:
            # Check for old files in user folder
            old_approval_file = os.path.join(self.user_folder, "file_approval_status.json")
            old_notifications_file = os.path.join(self.user_folder, "approval_notifications.json")
            
            # Move approval status file if it exists
            if os.path.exists(old_approval_file) and not os.path.exists(self.approval_status_file):
                import shutil
                shutil.move(old_approval_file, self.approval_status_file)
                print(f"[MIGRATION] Moved approval status file for {self.username} to data folder")
            
            # Move notifications file if it exists
            if os.path.exists(old_notifications_file) and not os.path.exists(self.notifications_file):
                import shutil
                shutil.move(old_notifications_file, self.notifications_file)
                print(f"[MIGRATION] Moved notifications file for {self.username} to data folder")
            
            # Clean up any remaining old files
            if os.path.exists(old_approval_file):
                os.remove(old_approval_file)
                print(f"[CLEANUP] Removed old approval status file from user folder")
            
            if os.path.exists(old_notifications_file):
                os.remove(old_notifications_file) 
                print(f"[CLEANUP] Removed old notifications file from user folder")
                
        except Exception as e:
            print(f"Migration error for {self.username}: {e}")
    
    def _get_user_team_cached(self) -> str:
        """Get user's team from users.json with caching"""
        try:
            users_file = DATA_PATHS.users_file
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    users = json.load(f)
                
                for email, data in users.items():
                    if data.get('username') == self.username:
                        teams = data.get('team_tags', [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error getting user team: {e}")
        return "DEFAULT"
    
    def get_user_team(self) -> str:
        """Get user's team from users.json (backward compatibility)"""
        return self.user_team
    
    def _update_approval_cache(self, force_refresh: bool = False):
        """Update internal cache of approval data"""
        with self._cache_lock:
            current_time = time.time()
            
            # Only refresh cache if forced or older than 2 seconds
            if not force_refresh and (current_time - self._cache_timestamp < 2.0):
                return
            
            try:
                if os.path.exists(self.approval_status_file):
                    with open(self.approval_status_file, 'r') as f:
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
            with open(self.approval_status_file, 'w') as f:
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
                with open(self.notifications_file, 'r') as f:
                    notifications = json.load(f)
                    return notifications if isinstance(notifications, list) else []
        except Exception as e:
            print(f"Error loading notifications: {e}")
        return []
    
    def save_notifications(self, notifications: List[Dict]) -> bool:
        """Save user's approval notifications"""
        try:
            with open(self.notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving notifications: {e}")
            return False
    
    def get_uploaded_files(self) -> List[Dict]:
        """🚨 ENHANCED: Get all files including processed ones that have been moved/deleted from uploads"""
        files = []
        approval_data = self.load_approval_status()  # Uses cache
        
        try:
            # First, get files that still physically exist in the uploads folder
            physical_files = set()
            if os.path.exists(self.user_folder):
                # Comprehensive system file exclusion
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
                    
                    # Skip directories (including profile_images folder)
                    if not os.path.isfile(file_path):
                        continue
                    
                    physical_files.add(filename)
                    
                    # Get file stats
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Get cached approval status
                    file_approval = approval_data.get(filename, {
                        "status": "my_files",  # Initial status for uploaded files
                        "submitted_for_approval": False,
                        "submission_date": None,
                        "admin_comments": [],
                        "team_leader_comments": [],
                        "status_history": [],
                        "description": "",
                        "tags": [],
                        "file_still_in_uploads": True
                    })
                    
                    file_info = {
                        "filename": filename,
                        "file_path": file_path,
                        "file_size": stat.st_size,
                        "upload_date": modified_time.isoformat(),
                        "file_still_in_uploads": True,
                        **file_approval  # Merge approval data
                    }
                    files.append(file_info)
            
            # 🚨 CRITICAL: Also include processed files that are no longer in uploads folder
            # These are files that have been approved/rejected and physically moved/deleted
            for filename, file_approval in approval_data.items():
                if filename not in physical_files:
                    # This file was processed and is no longer in uploads
                    file_status = file_approval.get('status', 'unknown')
                    
                    # Only include files that were submitted for approval (not just local files)
                    if file_approval.get('submitted_for_approval', False) or file_status not in ['my_files']:
                        file_info = {
                            "filename": filename,
                            "file_path": None,  # No longer in uploads
                            "file_size": file_approval.get('original_file_size', 0),
                            "upload_date": file_approval.get('original_upload_date', datetime.now().isoformat()),
                            "file_still_in_uploads": False,
                            "file_processed": True,
                            "processed_status": file_status,
                            **file_approval  # Merge approval data
                        }
                        
                        # Add helpful status messages for processed files
                        if file_status == 'approved':
                            file_info['status_message'] = '🟢 File approved and moved to project directory'
                        elif file_status == 'rejected':
                            file_info['status_message'] = '🔴 File rejected and removed from uploads'
                        elif file_status == 'changes_requested':
                            file_info['status_message'] = '🟡 Changes requested - file kept for resubmission'
                        else:
                            file_info['status_message'] = f'Status: {file_status}'
                        
                        files.append(file_info)
            
            # Sort files: processed files by last update, physical files by upload time
            def sort_key(file_info):
                if file_info.get('file_still_in_uploads', True):
                    return file_info.get('upload_date', '')
                else:
                    return file_info.get('last_updated', file_info.get('submission_date', ''))
            
            files.sort(key=sort_key, reverse=True)
                        
        except Exception as e:
            print(f"Error getting uploaded files: {e}")
            import traceback
            traceback.print_exc()
            
        return files
    
    def get_file_approval_status(self, filename: str) -> Dict:
        """Get approval status for a specific file (cached)"""
        approval_data = self.load_approval_status()  # Uses cache
        return approval_data.get(filename, {
            "status": "my_files",
            "submitted_for_approval": False,
            "submission_date": None,
            "admin_comments": [],
            "team_leader_comments": [],
            "status_history": [],
            "description": "",
            "tags": []
        })
    
    def submit_file_for_approval(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """Submit an uploaded file for approval with optimized processing"""
        try:
            file_path = os.path.join(self.user_folder, filename)
            if not os.path.exists(file_path):
                return False
            
            if tags is None:
                tags = []
            
            # Generate unique file ID for tracking
            file_id = str(uuid.uuid4())
            
            # Update local approval status
            approval_data = self.load_approval_status()
            approval_data[filename] = {
                "file_id": file_id,
                "status": "pending_team_leader",
                "submitted_for_approval": True,
                "submission_date": datetime.now().isoformat(),
                "description": description,
                "tags": tags,
                "admin_comments": [],
                "team_leader_comments": [],
                "status_history": [{
                    "status": "pending_team_leader",
                    "timestamp": datetime.now().isoformat(),
                    "comment": "File submitted for team leader review"
                }]
            }
            
            if self.save_approval_status(approval_data):
                # Add to global queue in background
                self.executor.submit(self.add_to_global_queue, filename, file_id, description, tags)
                
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
    
    def add_to_global_queue(self, filename: str, file_id: str, description: str, tags: List[str]):
        """Add file to global approval queue with file locking"""
        try:
            # Ensure global approvals directory exists on network
            global_approvals_dir = DATA_PATHS.approvals_dir
            os.makedirs(global_approvals_dir, exist_ok=True)
            
            global_queue_file = DATA_PATHS.file_approvals_file
            
            # Simple file locking mechanism
            lock_file = f"{global_queue_file}.lock"
            max_attempts = 10
            
            for attempt in range(max_attempts):
                try:
                    if not os.path.exists(lock_file):
                        # Create lock
                        with open(lock_file, 'w') as f:
                            f.write(str(time.time()))
                        
                        # Load existing queue
                        queue = {}
                        if os.path.exists(global_queue_file):
                            with open(global_queue_file, 'r') as f:
                                queue = json.load(f)
                        
                        # Get file info
                        file_path = os.path.join(self.user_folder, filename)
                        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                        
                        # Add new submission with correct initial status
                        submission_data = {
                            "file_id": file_id,
                            "original_filename": filename,
                            "user_id": self.username,
                            "user_team": self.user_team,
                            "file_size": file_size,
                            "submission_date": datetime.now().isoformat(),
                            "status": "pending_team_leader",  # Start with team leader review
                            "description": description,
                            "tags": tags,
                            "admin_comments": [],
                            "team_leader_comments": [],
                            "status_history": [{
                                "status": "pending_team_leader",
                                "timestamp": datetime.now().isoformat(),
                                "comment": "File submitted for team leader review"
                            }],
                            "file_path": file_path  # Store path for admin access
                        }
                        
                        queue[file_id] = submission_data
                        
                        # Save updated queue
                        with open(global_queue_file, 'w') as f:
                            json.dump(queue, f, indent=2)
                        
                        # Remove lock
                        os.remove(lock_file)
                        break
                        
                except Exception:
                    # Wait before retry
                    time.sleep(0.05)
                    continue
                finally:
                    # Clean up lock if it exists
                    try:
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error adding to global queue: {e}")
    
    def withdraw_submission(self, filename: str) -> bool:
        """OPTIMIZED: Fast withdrawal with immediate data update for instant UI feedback"""
        try:
            # Quick validation and optimistic update
            approval_data = self.load_approval_status()
            
            if filename not in approval_data:
                return False
            
            file_data = approval_data[filename]
            current_status = file_data.get("status", "my_files")
            
            if current_status not in ["pending_team_leader", "pending_admin", "under_review"]:
                return False
            
            # Get file_id for global queue removal
            file_id = file_data.get("file_id")
            
            # IMMEDIATE local update (optimistic) - KEY FOR INSTANT UI
            approval_data[filename] = {
                "status": "my_files",
                "submitted_for_approval": False,
                "submission_date": None,
                "admin_comments": [],
                "team_leader_comments": [],
                "status_history": file_data.get("status_history", []) + [{
                    "status": "withdrawn",
                    "timestamp": datetime.now().isoformat(),
                    "comment": "Submission withdrawn by user"
                }],
                "description": "",
                "tags": [],
                "withdrawn_date": datetime.now().isoformat()
            }
            
            # Save immediately for instant UI feedback
            if self.save_approval_status(approval_data):
                # Background cleanup (global queue removal and logging)
                if file_id:
                    self.executor.submit(self.remove_from_global_queue, file_id)
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
    
    def remove_from_global_queue(self, file_id: str):
        """Remove submission from global approval queue with file locking"""
        try:
            global_queue_file = DATA_PATHS.file_approvals_file
            if not os.path.exists(global_queue_file):
                return
            
            # File locking for thread safety
            lock_file = f"{global_queue_file}.lock"
            max_attempts = 10
            
            for attempt in range(max_attempts):
                try:
                    if not os.path.exists(lock_file):
                        # Create lock
                        with open(lock_file, 'w') as f:
                            f.write(str(time.time()))
                        
                        # Read, modify, write
                        with open(global_queue_file, 'r') as f:
                            queue = json.load(f)
                        
                        if file_id in queue:
                            del queue[file_id]
                            
                            with open(global_queue_file, 'w') as f:
                                json.dump(queue, f, indent=2)
                        
                        # Remove lock
                        os.remove(lock_file)
                        break
                        
                except Exception:
                    # Wait before retry
                    time.sleep(0.05)
                    continue
                finally:
                    # Clean up lock if it exists
                    try:
                        if os.path.exists(lock_file):
                            os.remove(lock_file)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error removing from global queue: {e}")
    
    def get_user_submissions(self) -> List[Dict]:
        """Get all files with their approval status (optimized)"""
        files = self.get_uploaded_files()
        
        # Use list comprehension for better performance
        submissions = [
            {
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
            for file_info in files
            if (file_info["submitted_for_approval"] or file_info["status"] != "not_submitted")
        ]
        
        return submissions
    
    def get_available_files_for_submission(self) -> List[Dict]:
        """Get files available for submission (optimized)"""
        files = self.get_uploaded_files()
        
        # Use list comprehension for better performance
        available_files = [
            {
                "filename": file_info["filename"],
                "file_size": file_info["file_size"],
                "upload_date": file_info["upload_date"]
            }
            for file_info in files
            if not file_info["submitted_for_approval"] and file_info["status"] == "my_files"
        ]
        
        return available_files
    
    def update_file_status(self, filename: str, new_status: str, admin_comment: str = "", admin_id: str = ""):
        """🚨 ENHANCED: Update file status and preserve original file info for processed files"""
        try:
            approval_data = self.load_approval_status()
            
            if filename in approval_data:
                old_status = approval_data[filename].get("status", "unknown")
                
                # 🚨 CRITICAL: Preserve original file information if file is being processed
                if new_status in ["approved", "rejected"] and old_status not in ["approved", "rejected"]:
                    # File is being processed - preserve original file info
                    file_path = os.path.join(self.user_folder, filename)
                    if os.path.exists(file_path):
                        try:
                            stat = os.stat(file_path)
                            approval_data[filename]["original_file_size"] = stat.st_size
                            approval_data[filename]["original_upload_date"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
                            print(f"[INFO] Preserved original file info for {filename} before processing")
                        except Exception as e:
                            print(f"[WARNING] Could not preserve original file info for {filename}: {e}")
                
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
                    "old_status": old_status,
                    "new_status": new_status,
                    "admin_id": admin_id,
                    "comment": admin_comment,
                    "timestamp": datetime.now().isoformat(),
                    "read": False
                })
                
                print(f"[SUCCESS] Updated file status: {filename} -> {old_status} to {new_status}")
                return True
        except Exception as e:
            print(f"[ERROR] Error updating file status: {e}")
            import traceback
            traceback.print_exc()
        return False
    
    def add_notification(self, notification: Dict):
        """Add notification with better performance"""
        try:
            notifications = self.load_notifications()
            notifications.insert(0, notification)
            
            # Keep only last 50 notifications for better performance
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
        """Get unread notification count (optimized)"""
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
                
                # Only allow resubmission of rejected or changes_requested files
                if file_data.get("status") not in ["rejected", "changes_requested"]:
                    return False
                
                # Generate new file_id for resubmission
                new_file_id = str(uuid.uuid4())
                
                # Update approval status
                approval_data[filename].update({
                    "file_id": new_file_id,
                    "status": "pending",
                    "description": description or file_data.get("description", ""),
                    "tags": tags or file_data.get("tags", []),
                    "resubmission_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                })
                
                # Add to status history
                approval_data[filename]["status_history"].append({
                    "status": "pending",
                    "timestamp": datetime.now().isoformat(),
                    "comment": "File resubmitted after changes"
                })
                
                # Clear admin comments for fresh review
                approval_data[filename]["admin_comments"] = []
                
                self.save_approval_status(approval_data)
                
                # Add back to global queue in background
                self.executor.submit(self.add_to_global_queue, filename, new_file_id, 
                                   description or file_data.get("description", ""), 
                                   tags or file_data.get("tags", []))
                
                # Log in background
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


class FileApprovalService:
    """Admin-side file approval service"""
    
    def __init__(self):
        self.global_queue_file = DATA_PATHS.file_approvals_file
        self.comments_file = DATA_PATHS.comments_file
        os.makedirs(DATA_PATHS.approvals_dir, exist_ok=True)
    
    def load_global_queue(self) -> Dict:
        """Load global approval queue"""
        try:
            if os.path.exists(self.global_queue_file):
                with open(self.global_queue_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading global queue: {e}")
        return {}
    
    def save_global_queue(self, queue: Dict) -> bool:
        """Save global approval queue"""
        try:
            with open(self.global_queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving global queue: {e}")
            return False
    
    def load_comments(self) -> Dict:
        """Load comments data"""
        try:
            if os.path.exists(self.comments_file):
                with open(self.comments_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading comments: {e}")
        return {}
    
    def save_comments(self, comments: Dict) -> bool:
        """Save comments data"""
        try:
            with open(self.comments_file, 'w') as f:
                json.dump(comments, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving comments: {e}")
            return False
    
    def get_pending_files_by_team(self, team: str, user_role: str = 'USER') -> List[Dict]:
        """Get pending files for a specific team based on user role"""
        queue = self.load_global_queue()
        pending_files = []
        
        for file_id, file_data in queue.items():
            file_status = file_data.get('status')
            # Filter files based on role and status
            if user_role == 'ADMIN':
                # Admin sees files pending admin approval
                if file_status == 'pending_admin':
                    pending_files.append(file_data)
            elif user_role == 'TEAM_LEADER':
                # Team leader sees files pending team leader approval from their team
                if file_status == 'pending_team_leader' and file_data.get('user_team') == team:
                    pending_files.append(file_data)
        
        return pending_files
    
    def get_all_files_by_team(self, team: str, user_role: str = 'USER') -> List[Dict]:
        """Get all files for a specific team based on user role"""
        queue = self.load_global_queue()
        team_files = []
        
        for file_id, file_data in queue.items():
            # ADMIN can see all files, TEAM_LEADER only their team files
            if user_role == 'ADMIN' or file_data.get('user_team') == team:
                team_files.append(file_data)
        
        return team_files
    
    def get_approved_files_by_team(self, team: str, user_role: str = 'USER') -> List[Dict]:
        """Get approved files for a specific team - Note: approved files are moved out of queue"""
        # Since approved files are removed from queue, this would need to access a separate archive
        # For now, return empty list as approved files are processed and removed
        return []
    
    def get_rejected_files_by_team(self, team: str, user_role: str = 'USER') -> List[Dict]:
        """Get rejected files for a specific team - Note: rejected files are moved out of queue"""
        # Since rejected files are removed from queue, this would need to access a separate archive
        # For now, return empty list as rejected files are processed and removed
        return []
    
    def approve_file(self, file_id: str, admin_user: str) -> bool:
        """🚨 ENHANCED: Approve a file - moves it to project directory AND cleans up from user uploads"""
        try:
            queue = self.load_global_queue()
            
            if file_id in queue:
                file_data = queue[file_id]
                original_filename = file_data.get('original_filename')
                user_id = file_data.get('user_id')
                
                file_data['status'] = ApprovalStatus.APPROVED.value
                file_data['approved_by'] = admin_user
                file_data['approved_date'] = datetime.now().isoformat()
                
                # Add to status history
                if 'status_history' not in file_data:
                    file_data['status_history'] = []
                
                file_data['status_history'].append({
                    'status': ApprovalStatus.APPROVED.value,
                    'timestamp': datetime.now().isoformat(),
                    'admin_id': admin_user,
                    'comment': 'File approved by admin - processing physical file movement'
                })
                
                # 🚨 CRITICAL: Move approved file from user uploads to project directory
                # This will DELETE the file from user uploads folder after successful move
                file_movement_service = get_enhanced_file_movement_service()
                move_success, move_message, new_file_path = file_movement_service.move_approved_file_with_access_management(
                    file_data, admin_user)
                
                if move_success:
                    # Update file path in data
                    file_data['project_file_path'] = new_file_path
                    file_data['moved_to_project'] = True
                    file_data['move_message'] = move_message
                    file_data['file_cleaned_from_uploads'] = True
                    
                    # 🚨 CRITICAL: Update user's approval status with new file location info
                    self._update_user_status(file_data, ApprovalStatus.APPROVED.value, admin_user, 
                                           f"File approved and moved to project directory: {move_message}. Original file removed from uploads.")
                    
                    # Archive the approved file before removing from queue
                    self._archive_file(file_data, 'approved')
                    
                    # Remove from global queue (approved files are processed)
                    del queue[file_id]
                    
                    log_action(admin_user, f"APPROVED and MOVED file: {original_filename} from user {user_id} uploads to project directory - {move_message}")
                    print(f"[APPROVAL_SUCCESS] File {original_filename} approved and moved to project, cleaned from user uploads")
                    
                else:
                    # File approval succeeded but move failed - keep file in user uploads for now
                    file_data['moved_to_project'] = False
                    file_data['move_error'] = move_message
                    file_data['file_cleaned_from_uploads'] = False
                    
                    # Update user's approval status (still approved, but file move failed)
                    self._update_user_status(file_data, ApprovalStatus.APPROVED.value, admin_user, 
                                           f"File approved but move failed: {move_message}. File remains in your uploads folder until issue is resolved.")
                    
                    # Keep in queue with approved status for manual handling
                    print(f"[WARNING] File {original_filename} approved but move failed: {move_message}")
                    log_action(admin_user, f"Approved file with move error: {original_filename} - {move_message}")
                
                return self.save_global_queue(queue)
            
        except Exception as e:
            print(f"[ERROR] Error approving file {file_id}: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def reject_file(self, file_id: str, admin_user: str, reason: str, request_changes: bool = False) -> bool:
        """🚨 ENHANCED: Reject a file or request changes - deletes file from user uploads"""
        try:
            queue = self.load_global_queue()
            
            if file_id in queue:
                file_data = queue[file_id]
                original_filename = file_data.get('original_filename')
                user_id = file_data.get('user_id')
                
                status = ApprovalStatus.CHANGES_REQUESTED.value if request_changes else ApprovalStatus.REJECTED.value
                
                file_data['status'] = status
                file_data['rejected_by'] = admin_user
                file_data['rejection_date'] = datetime.now().isoformat()
                file_data['rejection_reason'] = reason
                
                # Add to status history
                if 'status_history' not in file_data:
                    file_data['status_history'] = []
                
                file_data['status_history'].append({
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'admin_id': admin_user,
                    'comment': reason + (' - processing physical file cleanup' if not request_changes else '')
                })
                
                # 🚨 CRITICAL: Handle physical file cleanup based on rejection type
                if request_changes:
                    # For changes requested, keep file in user uploads for resubmission
                    file_data['file_cleaned_from_uploads'] = False
                    
                    # Update user's approval status (file remains in uploads for changes)
                    self._update_user_status(file_data, status, admin_user, 
                                           f"Changes requested: {reason}. File remains in your uploads folder for resubmission after making changes.")
                    
                    print(f"[CHANGES_REQUESTED] File {original_filename} kept in user uploads for resubmission")
                    log_action(admin_user, f"Requested changes for file: {original_filename} from user {user_id} - file kept in uploads")
                    
                else:
                    # For rejected files, delete from user uploads
                    file_cleanup_success, cleanup_message = self._delete_rejected_file_from_uploads(file_data, admin_user, reason)
                    
                    if file_cleanup_success:
                        file_data['file_cleaned_from_uploads'] = True
                        file_data['cleanup_message'] = cleanup_message
                        
                        # Update user's approval status with file deletion info
                        self._update_user_status(file_data, status, admin_user, 
                                               f"File rejected: {reason}. File has been removed from your uploads folder.")
                        
                        print(f"[REJECTION_SUCCESS] File {original_filename} rejected and deleted from user uploads")
                        log_action(admin_user, f"REJECTED and DELETED file: {original_filename} from user {user_id} uploads - {reason}")
                        
                    else:
                        file_data['file_cleaned_from_uploads'] = False
                        file_data['cleanup_error'] = cleanup_message
                        
                        # Update user's approval status (rejected but file deletion failed)
                        self._update_user_status(file_data, status, admin_user, 
                                               f"File rejected: {reason}. Warning: File deletion from uploads failed: {cleanup_message}")
                        
                        print(f"[WARNING] File {original_filename} rejected but deletion from uploads failed: {cleanup_message}")
                        log_action(admin_user, f"Rejected file with cleanup error: {original_filename} - {cleanup_message}")
                
                # Archive the rejected file before removing from queue
                self._archive_file(file_data, 'rejected_admin')
                
                # Remove from global queue
                del queue[file_id]
                
                return self.save_global_queue(queue)
            
        except Exception as e:
            print(f"[ERROR] Error rejecting file {file_id}: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _delete_rejected_file_from_uploads(self, file_data: Dict, admin_user: str, reason: str) -> Tuple[bool, str]:
        """
        🚨 CRITICAL: Delete rejected file from user uploads folder
        Returns (success, message)
        """
        try:
            original_filename = file_data.get('original_filename')
            user_id = file_data.get('user_id')
            current_file_path = file_data.get('file_path')
            
            if not all([original_filename, user_id, current_file_path]):
                return False, "Missing file information for deletion"
            
            # Validate file path is in user uploads folder (security check)
            upload_base = os.path.join(r"\\KMTI-NAS\Shared\data", "uploads")
            if not current_file_path.startswith(upload_base):
                return False, f"Security: File path not in uploads directory: {current_file_path}"
            
            # Check if file still exists in uploads
            if not os.path.exists(current_file_path):
                return True, f"File {original_filename} already removed from uploads directory"
            
            # Delete the file
            os.remove(current_file_path)
            
            # Verify deletion
            if os.path.exists(current_file_path):
                return False, f"File deletion verification failed: {current_file_path}"
            
            success_message = f"Rejected file {original_filename} successfully deleted from user {user_id} uploads folder"
            print(f"[FILE_DELETION] {success_message}")
            
            return True, success_message
            
        except PermissionError as pe:
            error_msg = f"Permission denied deleting file {original_filename}: {pe}"
            print(f"[PERMISSION_ERROR] {error_msg}")
            return False, error_msg
            
        except FileNotFoundError:
            # File already gone, consider this success
            return True, f"File {original_filename} was already removed from uploads"
            
        except Exception as e:
            error_msg = f"Error deleting rejected file {original_filename}: {str(e)}"
            print(f"[DELETION_ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def add_comment(self, file_id: str, admin_user: str, comment: str) -> bool:
        """Add comment to a file"""
        try:
            comments = self.load_comments()
            
            if file_id not in comments:
                comments[file_id] = []
            
            comments[file_id].append({
                'admin_id': admin_user,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            return self.save_comments(comments)
            
        except Exception as e:
            print(f"Error adding comment: {e}")
        
        return False
    
    def _update_user_status(self, file_data: Dict, status: str, admin_user: str, comment: str = ""):
        """Update user's local approval status and send notifications"""
        try:
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not user_id or not original_filename:
                print(f"[ERROR] Missing user_id ({user_id}) or filename ({original_filename}) for status update")
                return
            
            # Create a user approval service instance to update their data
            user_upload_folder = DATA_PATHS.get_user_upload_dir(user_id)
            if os.path.exists(user_upload_folder):
                print(f"[INFO] Updating user status for {user_id}: {original_filename} -> {status}")
                user_approval_service = ApprovalFileService(user_upload_folder, user_id)
                
                # Update the file status
                success = user_approval_service.update_file_status(original_filename, status, comment, admin_user)
                
                if success:
                    print(f"[SUCCESS] Status updated for user {user_id}: {original_filename}")
                    
                    # Send notification using the notification service
                    from services.notification_service import NotificationService
                    notification_service = NotificationService()
                    
                    # Create appropriate notification message
                    if status == "approved":
                        notification_service.notify_approval_status(
                            user_id, original_filename, "approved", admin_user, 
                            f"Your file has been approved and moved to the project directory. {comment}")
                    elif status == "rejected_admin":
                        notification_service.notify_approval_status(
                            user_id, original_filename, "rejected", admin_user, 
                            f"Your file has been rejected. Reason: {comment}")
                    elif status == "pending_admin":
                        notification_service.notify_approval_status(
                            user_id, original_filename, "approved_by_team_leader", admin_user,
                            f"Your file has been approved by the team leader and is now pending admin review.")
                    elif status == "rejected_team_leader":
                        notification_service.notify_approval_status(
                            user_id, original_filename, "rejected_by_team_leader", admin_user,
                            f"Your file has been rejected by the team leader. Reason: {comment}")
                    
                    print(f"[SUCCESS] Notification sent to user {user_id} for file {original_filename}")
                else:
                    print(f"[WARNING] Failed to update status for user {user_id}: {original_filename}")
            else:
                print(f"[WARNING] User upload folder not found: {user_upload_folder}")
                
        except Exception as e:
            print(f"[ERROR] Error updating user status: {e}")
            import traceback
            traceback.print_exc()
    
    def _archive_file(self, file_data: Dict, status: str):
        """Archive approved/rejected files for admin panel display"""
        try:
            archive_dir = os.path.join(DATA_PATHS.SHARED_BASE, "approvals", "archived")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Determine archive file based on status
            if status == 'approved':
                archive_file = os.path.join(archive_dir, 'approved_files.json')
            elif status == 'rejected_admin':
                archive_file = os.path.join(archive_dir, 'rejected_files.json')
            else:
                return  # Don't archive other statuses
            
            # Load existing archived files
            archived_files = {}
            if os.path.exists(archive_file):
                try:
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        archived_files = json.load(f)
                except Exception as e:
                    print(f"[WARNING] Error loading archive file {archive_file}: {e}")
                    archived_files = {}
            
            # Add current file to archive
            file_id = file_data.get('file_id', str(uuid.uuid4()))
            file_data['archived_date'] = datetime.now().isoformat()
            archived_files[file_id] = file_data
            
            # Keep only last 1000 archived files per status
            if len(archived_files) > 1000:
                # Sort by archived_date and keep newest 1000
                sorted_files = sorted(archived_files.items(), 
                                     key=lambda x: x[1].get('archived_date', ''), 
                                     reverse=True)
                archived_files = dict(sorted_files[:1000])
            
            # Save updated archive
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archived_files, f, indent=2)
            
            print(f"[INFO] Archived file {file_data.get('original_filename')} with status {status}")
            
        except Exception as e:
            print(f"[ERROR] Error archiving file: {e}")
            import traceback
            traceback.print_exc()