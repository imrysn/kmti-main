import os
import json
import uuid
import time
import threading
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from services.file_approval_constant import FileApprovalStatus

class NewApprovalFileService:
    """
    New user-side approval service - COMPATIBLE with existing UI
    Replace your old ApprovalFileService imports with this
    """

    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        
        # User metadata storage (keep in system area)
        self.system_data_folder = os.path.join("data", "user_approvals", username)
        self.approval_status_file = os.path.join(self.system_data_folder, "file_approval_status.json")
        self.notifications_file = os.path.join(self.system_data_folder, "approval_notifications.json")
        
        # Ensure folders exist
        os.makedirs(self.user_folder, exist_ok=True)
        os.makedirs(self.system_data_folder, exist_ok=True)
        
        # Cache and threading
        self._approval_cache: Dict[str, Dict] = {}
        self._cache_timestamp = 0.0
        self._cache_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Get user team
        self.user_team = self._get_user_team_cached()
        
        # Core service reference
        from services.new_approval_service import NewFileApprovalService
        self.core_service = NewFileApprovalService()
    
    def _get_user_team_cached(self) -> str:
        """Get user's team from users.json"""
        try:
            users_file = r"\\KMTI-NAS\Shared\data\users.json"
            if os.path.exists(users_file):
                with open(users_file, "r", encoding="utf-8") as f:
                    users = json.load(f)
                for _, data in users.items():
                    if data.get("username") == self.username:
                        teams = data.get("team_tags", [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error reading user team for {self.username}: {e}")
        return "DEFAULT"
    
    def _update_approval_cache(self, force_refresh: bool = False):
        """Update local cache of user approval metadata"""
        with self._cache_lock:
            now = time.time()
            if not force_refresh and (now - self._cache_timestamp < 2.0):
                return
            try:
                if os.path.exists(self.approval_status_file):
                    with open(self.approval_status_file, "r", encoding="utf-8") as f:
                        self._approval_cache = json.load(f)
                else:
                    self._approval_cache = {}
                self._cache_timestamp = now
            except Exception as e:
                print(f"Cache update error ({self.username}): {e}")
                self._approval_cache = {}

    def load_approval_status(self) -> Dict[str, Dict]:
        """Load user's approval metadata"""
        self._update_approval_cache()
        with self._cache_lock:
            return self._approval_cache.copy()

    def save_approval_status(self, status_data: Dict[str, Dict]) -> bool:
        """Save user's approval metadata"""
        try:
            os.makedirs(os.path.dirname(self.approval_status_file), exist_ok=True)
            with open(self.approval_status_file, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
            with self._cache_lock:
                self._approval_cache = status_data.copy()
                self._cache_timestamp = time.time()
            return True
        except Exception as e:
            print(f"Error saving approval status ({self.username}): {e}")
            return False
    
    # ---------------------------------------------------------------------------------
    # COMPATIBILITY METHODS - KEEP EXISTING UI WORKING
    # ---------------------------------------------------------------------------------
    
    def submit_file_for_approval(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """
        COMPATIBILITY METHOD: Submit file for Team Leader approval
        This is called by your existing UI components
        """
        try:
            file_path = os.path.join(self.user_folder, filename)
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
                
            if tags is None:
                tags = []

            # Generate file ID
            file_id = str(uuid.uuid4())
            
            # Submit to core service
            result_file_id = self.core_service._submit_file_to_queue(
                user_id=self.username,
                filename=filename,
                file_path=file_path,
                user_team=self.user_team,
                description=description,
                tags=tags,
                file_id=file_id
            )
            
            if result_file_id:
                # Update user's local metadata
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
                        "comment": "Submitted to Team Leader"
                    }]
                }
                
                if self.save_approval_status(approval_data):
                    print(f"✓ Successfully submitted {filename} for approval")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error submitting file for approval ({self.username}): {e}")
            return False
    
    def withdraw_submission(self, filename: str) -> bool:
        """
        COMPATIBILITY METHOD: Withdraw submission
        """
        try:
            approval_data = self.load_approval_status()
            if filename not in approval_data:
                return False
                
            file_data = approval_data[filename]
            file_id = file_data.get("file_id")
            current_status = file_data.get("status")
            
            # Only allow withdraw from pending states
            if current_status not in [FileApprovalStatus.PENDING_TEAM_LEADER, FileApprovalStatus.PENDING_ADMIN]:
                return False
            
            # Update local metadata
            approval_data[filename] = {
                "status": FileApprovalStatus.WITHDRAWN,
                "submitted_for_approval": False,
                "submission_date": None,
                "admin_comments": [],
                "status_history": file_data.get("status_history", []) + [{
                    "status": FileApprovalStatus.WITHDRAWN,
                    "timestamp": datetime.now().isoformat(),
                    "comment": "Withdrawn by user"
                }],
                "description": "",
                "tags": [],
                "withdrawn_date": datetime.now().isoformat()
            }
            
            # Remove from core service queue
            if file_id:
                self.executor.submit(self._remove_from_core_queue, file_id)
            
            return self.save_approval_status(approval_data)
            
        except Exception as e:
            print(f"Error withdrawing submission ({self.username}): {e}")
            return False
    
    def resubmit_file(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """
        COMPATIBILITY METHOD: Resubmit rejected file
        """
        try:
            approval_data = self.load_approval_status()
            if filename not in approval_data:
                return False
                
            file_data = approval_data[filename]
            current_status = file_data.get("status")
            
            # Only allow resubmit from rejected states
            if current_status not in [FileApprovalStatus.REJECTED_TEAM_LEADER, FileApprovalStatus.REJECTED_ADMIN]:
                return False
            
            # Create new submission (fresh start)
            return self.submit_file_for_approval(filename, description, tags)
            
        except Exception as e:
            print(f"Error resubmitting file ({self.username}): {e}")
            return False
    
    def get_user_submissions(self) -> List[Dict]:
        """
        FIXED VERSION: Get user's submissions for File Approvals tab
        """
        try:
            print(f"[DEBUG] Getting submissions for user: {self.username}")
            
            submissions = []
            
            # METHOD 1: Get from local user metadata (this should always work)
            print("[DEBUG] Method 1: Checking local user metadata...")
            approval_data = self.load_approval_status()
            
            for filename, file_data in approval_data.items():
                if file_data.get("submitted_for_approval", False):
                    # This file was submitted, include it
                    
                    # Get file info from actual file
                    file_path = os.path.join(self.user_folder, filename)
                    file_size = 0
                    upload_date = datetime.now().isoformat()
                    
                    if os.path.exists(file_path):
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        upload_date = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    submission = {
                        "original_filename": filename,
                        "file_size": file_size,
                        "upload_date": upload_date,
                        "submission_date": file_data.get("submission_date"),
                        "status": file_data.get("status", "unknown"),
                        "description": file_data.get("description", ""),
                        "tags": file_data.get("tags", []),
                        "admin_comments": file_data.get("admin_comments", []),
                        "status_history": file_data.get("status_history", [])
                    }
                    submissions.append(submission)
                    print(f"[DEBUG] Added {filename} from local metadata with status: {submission['status']}")
            
            # METHOD 2: Also check core service (for consistency)
            print("[DEBUG] Method 2: Checking core service...")
            try:
                # Check active queue
                queue_data = self.core_service._load_json_file(self.core_service.queue_file)
                for file_data in queue_data.values():
                    if file_data.get("user_id") == self.username:
                        filename = file_data.get("original_filename")
                        
                        # Only add if not already in submissions (from Method 1)
                        if not any(s.get("original_filename") == filename for s in submissions):
                            submission = {
                                "original_filename": filename,
                                "file_size": file_data.get("file_size", 0),
                                "upload_date": file_data.get("submission_date"),
                                "submission_date": file_data.get("submission_date"),
                                "status": file_data.get("status"),
                                "description": file_data.get("description", ""),
                                "tags": file_data.get("tags", []),
                                "admin_comments": [],
                                "status_history": file_data.get("workflow_history", [])
                            }
                            submissions.append(submission)
                            print(f"[DEBUG] Added {filename} from core queue with status: {submission['status']}")
                
                # Check approved files
                approved_data = self.core_service._load_json_file(self.core_service.approved_file)
                for file_data in approved_data.values():
                    if file_data.get("user_id") == self.username:
                        filename = file_data.get("original_filename")
                        
                        # Only add if not already in submissions
                        if not any(s.get("original_filename") == filename for s in submissions):
                            submission = {
                                "original_filename": filename,
                                "file_size": file_data.get("file_size", 0),
                                "upload_date": file_data.get("submission_date"),
                                "submission_date": file_data.get("submission_date"),
                                "status": file_data.get("status"),
                                "description": file_data.get("description", ""),
                                "tags": file_data.get("tags", []),
                                "admin_comments": [],
                                "status_history": file_data.get("workflow_history", [])
                            }
                            submissions.append(submission)
                            print(f"[DEBUG] Added {filename} from approved files with status: {submission['status']}")
                
                # Check rejected files  
                rejected_data = self.core_service._load_json_file(self.core_service.rejected_file)
                for file_data in rejected_data.values():
                    if file_data.get("user_id") == self.username:
                        filename = file_data.get("original_filename")
                        
                        # Only add if not already in submissions
                        if not any(s.get("original_filename") == filename for s in submissions):
                            submission = {
                                "original_filename": filename,
                                "file_size": file_data.get("file_size", 0),
                                "upload_date": file_data.get("submission_date"),
                                "submission_date": file_data.get("submission_date"),
                                "status": file_data.get("status"),
                                "description": file_data.get("description", ""),
                                "tags": file_data.get("tags", []),
                                "admin_comments": [],
                                "status_history": file_data.get("workflow_history", [])
                            }
                            submissions.append(submission)
                            print(f"[DEBUG] Added {filename} from rejected files with status: {submission['status']}")
                            
            except Exception as e:
                print(f"[DEBUG] Error checking core service: {e}")
                # Continue with just local metadata
            
            # Sort by submission date
            submissions.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
            
            print(f"[DEBUG] Final result: {len(submissions)} submissions found")
            for s in submissions:
                print(f"[DEBUG]   - {s['original_filename']}: {s['status']}")
            
            return submissions
            
        except Exception as e:
            print(f"[ERROR] Error getting user submissions ({self.username}): {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_uploaded_files(self) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get uploaded files for Files view
        """
        files = []
        approval_data = self.load_approval_status()

        try:
            if os.path.exists(self.user_folder):
                excluded = {
                    "files_metadata.json", "profile.json",
                    "file_approval_status.json", "approval_notifications.json",
                }
                
                for filename in os.listdir(self.user_folder):
                    if filename in excluded or filename.startswith("."):
                        continue
                        
                    file_path = os.path.join(self.user_folder, filename)
                    if not os.path.isfile(file_path):
                        continue
                        
                    stat = os.stat(file_path)
                    modified_iso = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    # Get approval status (default to MY_FILES if not submitted)
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
                        "upload_date": modified_iso,
                        **file_approval
                    }
                    files.append(file_info)
                    
                files.sort(key=lambda x: x["upload_date"], reverse=True)
        except Exception as e:
            print(f"Error enumerating uploaded files ({self.username}): {e}")
            
        return files
    
    def get_available_files_for_submission(self) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get files available for submission
        """
        files = self.get_uploaded_files()
        return [
            {
                "filename": fi["filename"],
                "file_size": fi["file_size"],
                "upload_date": fi["upload_date"]
            }
            for fi in files
            if fi.get("status") in [FileApprovalStatus.MY_FILES, FileApprovalStatus.WITHDRAWN] or 
               not fi.get("submitted_for_approval", False)
        ]
    
    def get_pending_team_leader_files(self, team: str) -> List[Dict]:
        """Get files pending Team Leader approval - CORRECTED"""
        try:
            print(f"[DEBUG] NewFileApprovalService: Getting TL files for team {team}")
            print(f"[DEBUG] Queue file path: {self.queue_file}")
            
            # Make sure the file exists
            if not os.path.exists(self.queue_file):
                print(f"[WARNING] Queue file doesn't exist: {self.queue_file}")
                return []
            
            queue = self._load_json_file(self.queue_file)
            print(f"[DEBUG] Loaded {len(queue)} files from queue")
            
            result = []
            for file_id, file_data in queue.items():
                file_status = file_data.get("status", "")
                file_team = file_data.get("user_team", "")
                filename = file_data.get("original_filename", "unknown")
                
                print(f"[DEBUG] File {filename}: status='{file_status}', team='{file_team}'")
                print(f"[DEBUG] Looking for status='{FileApprovalStatus.PENDING_TEAM_LEADER}', team='{team}'")
                
                if file_status == FileApprovalStatus.PENDING_TEAM_LEADER and file_team == team:
                    result.append(file_data)
                    print(f"[DEBUG] ✓ MATCH: Added {filename} to result")
                else:
                    print(f"[DEBUG] ✗ No match for {filename}")
            
            print(f"[DEBUG] Final TL result: {len(result)} files for team {team}")
            return result
            
        except Exception as e:
            print(f"[ERROR] Error in get_pending_team_leader_files: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_pending_admin_files(self) -> List[Dict]:
        """Get files pending Admin approval - CORRECTED"""
        try:
            print(f"[DEBUG] NewFileApprovalService: Getting admin files")
            print(f"[DEBUG] Queue file path: {self.queue_file}")
            
            if not os.path.exists(self.queue_file):
                print(f"[WARNING] Queue file doesn't exist: {self.queue_file}")
                return []
            
            queue = self._load_json_file(self.queue_file)
            print(f"[DEBUG] Loaded {len(queue)} files from queue")
            
            result = []
            for file_id, file_data in queue.items():
                file_status = file_data.get("status", "")
                filename = file_data.get("original_filename", "unknown")
                
                print(f"[DEBUG] File {filename}: status='{file_status}'")
                print(f"[DEBUG] Looking for status='{FileApprovalStatus.PENDING_ADMIN}'")
                
                if file_status == FileApprovalStatus.PENDING_ADMIN:
                    result.append(file_data)
                    print(f"[DEBUG] ✓ MATCH: Added {filename} to result")
                else:
                    print(f"[DEBUG] ✗ No match for {filename}")
            
            print(f"[DEBUG] Final admin result: {len(result)} files")
            return result
            
        except Exception as e:
            print(f"[ERROR] Error in get_pending_admin_files: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # ---------------------------------------------------------------------------------
    # NOTIFICATION COMPATIBILITY
    # ---------------------------------------------------------------------------------
    
    def load_notifications(self) -> List[Dict]:
        """Load user notifications"""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, "r", encoding="utf-8") as f:
                    notifications = json.load(f)
                    return notifications if isinstance(notifications, list) else []
        except Exception as e:
            print(f"Error loading notifications ({self.username}): {e}")
        return []

    def save_notifications(self, notifications: List[Dict]) -> bool:
        """Save user notifications"""
        try:
            os.makedirs(os.path.dirname(self.notifications_file), exist_ok=True)
            with open(self.notifications_file, "w", encoding="utf-8") as f:
                json.dump(notifications, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving notifications ({self.username}): {e}")
            return False

    def get_unread_notification_count(self) -> int:
        """Get count of unread notifications"""
        try:
            notifications = self.load_notifications()
            return sum(1 for n in notifications if not n.get("read", False))
        except Exception:
            return 0
    
    def mark_notification_read(self, index: int) -> bool:
        """Mark notification as read"""
        try:
            notifications = self.load_notifications()
            if 0 <= index < len(notifications):
                notifications[index]["read"] = True
                self.save_notifications(notifications)
                return True
        except Exception as e:
            print(f"Error marking notification ({self.username}): {e}")
        return False
    
    def add_notification(self, notification: Dict):
        """Add notification"""
        try:
            notifications = self.load_notifications()
            notifications.insert(0, notification)
            notifications = notifications[:50]  # Keep only recent 50
            self.save_notifications(notifications)
        except Exception as e:
            print(f"Error adding notification ({self.username}): {e}")
    
    # ---------------------------------------------------------------------------------
    # HELPER METHODS
    # ---------------------------------------------------------------------------------
    
    def _remove_from_core_queue(self, file_id: str):
        """Remove file from core service queue"""
        try:
            queue = self.core_service._load_json_file(self.core_service.queue_file)
            if file_id in queue:
                del queue[file_id]
                self.core_service._save_json_file(self.core_service.queue_file, queue)
                print(f"Removed file {file_id} from core queue")
        except Exception as e:
            print(f"Error removing from core queue: {e}")
    
    def cleanup_resources(self):
        """Cleanup resources"""
        try:
            self.executor.shutdown(wait=False)
        except Exception:
            pass

    def _submit_file_to_queue(self, user_id: str, filename: str, file_path: str, 
        user_team: str, description: str, tags: List[str], file_id: str) -> Optional[str]:
        """Internal method to submit file to approval queue"""
        try:
            if not os.path.exists(file_path):
                return None
            
            file_size = os.path.getsize(file_path)
            
            # Create submission record
            submission = {
                "file_id": file_id,
                "original_filename": filename,
                "file_path": file_path,
                "user_id": user_id,
                "user_team": user_team,
                "file_size": file_size,
                "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                "submission_date": datetime.now().isoformat(),
                "description": description,
                "tags": tags,
                "workflow_history": [{
                    "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                    "timestamp": datetime.now().isoformat(),
                    "action": "submitted",
                    "actor": user_id,
                    "comment": "File submitted for Team Leader review"
                }]
            }
            
            # Add to queue
            with self._lock:
                queue = self._load_json_file(self.queue_file)
                queue[file_id] = submission
                
                if self._save_json_file(self.queue_file, queue):
                    print(f"✓ File {filename} added to approval queue with ID: {file_id}")
                    return file_id
                else:
                    return None
                    
        except Exception as e:
            print(f"Error adding file to queue: {e}")
            return None

    def debug_submission_data(self, filename: str):
        """Debug method to see what's happening with file submissions"""
        print(f"\n=== DEBUGGING SUBMISSION FOR {filename} ===")
        
        # 1. Check user's local metadata
        print("1. Checking user's local approval metadata...")
        approval_data = self.load_approval_status()
        if filename in approval_data:
            print(f"✓ Found {filename} in user metadata:")
            print(f"   Status: {approval_data[filename].get('status')}")
            print(f"   File ID: {approval_data[filename].get('file_id')}")
            print(f"   Submitted: {approval_data[filename].get('submitted_for_approval')}")
        else:
            print(f"✗ {filename} NOT found in user metadata")
        
        # 2. Check core service queue
        print("\n2. Checking core approval queue...")
        try:
            queue_data = self.core_service._load_json_file(self.core_service.queue_file)
            user_files = [f for f in queue_data.values() if f.get('user_id') == self.username]
            print(f"Found {len(user_files)} files in queue for user {self.username}")
            
            for file_data in user_files:
                if file_data.get('original_filename') == filename:
                    print(f"✓ Found {filename} in core queue:")
                    print(f"   File ID: {file_data.get('file_id')}")
                    print(f"   Status: {file_data.get('status')}")
                    print(f"   Team: {file_data.get('user_team')}")
                    break
            else:
                print(f"✗ {filename} NOT found in core queue")
                
        except Exception as e:
            print(f"✗ Error checking core queue: {e}")
        
        # 3. Check what get_user_submissions() returns
        print("\n3. Checking get_user_submissions() result...")
        try:
            submissions = self.get_user_submissions()
            print(f"get_user_submissions() returned {len(submissions)} files")
            
            for submission in submissions:
                if submission.get('original_filename') == filename:
                    print(f"✓ Found {filename} in submissions:")
                    print(f"   Status: {submission.get('status')}")
                    break
            else:
                print(f"✗ {filename} NOT found in submissions list")
                
        except Exception as e:
            print(f"✗ Error in get_user_submissions(): {e}")
        
        print("=== END DEBUG ===\n")

    def submit_file_for_approval(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """
        FIXED VERSION: Submit file for Team Leader approval
        """
        try:
            print(f"[DEBUG] Starting submission for {filename}")
            
            file_path = os.path.join(self.user_folder, filename)
            if not os.path.exists(file_path):
                print(f"[ERROR] File not found: {file_path}")
                return False
                
            if tags is None:
                tags = []

            # Generate file ID
            file_id = str(uuid.uuid4())
            print(f"[DEBUG] Generated file_id: {file_id}")
            
            # FIRST: Update user's local metadata (this ensures File Approvals tab works)
            print("[DEBUG] Updating local user metadata...")
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
                    "comment": "Submitted to Team Leader"
                }]
            }
            
            local_save_success = self.save_approval_status(approval_data)
            print(f"[DEBUG] Local metadata save result: {local_save_success}")
            
            if not local_save_success:
                print("[ERROR] Failed to save local metadata")
                return False
            
            # SECOND: Submit to core service (this enables admin/TL to see it)
            print("[DEBUG] Submitting to core service...")
            try:
                # Direct submission to core queue
                file_size = os.path.getsize(file_path)
                
                submission = {
                    "file_id": file_id,
                    "original_filename": filename,
                    "file_path": file_path,
                    "user_id": self.username,
                    "user_team": self.user_team,
                    "file_size": file_size,
                    "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                    "submission_date": datetime.now().isoformat(),
                    "description": description,
                    "tags": tags,
                    "workflow_history": [{
                        "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                        "timestamp": datetime.now().isoformat(),
                        "action": "submitted",
                        "actor": self.username,
                        "comment": "File submitted for Team Leader review"
                    }]
                }
                
                # Add to core queue
                queue = self.core_service._load_json_file(self.core_service.queue_file)
                queue[file_id] = submission
                core_save_success = self.core_service._save_json_file(self.core_service.queue_file, queue)
                print(f"[DEBUG] Core queue save result: {core_save_success}")
                
                if core_save_success:
                    print(f"[SUCCESS] ✓ Successfully submitted {filename} for approval")
                    
                    # Debug: Verify both saves worked
                    self.debug_submission_data(filename)
                    
                    return True
                else:
                    print("[ERROR] Failed to save to core queue")
                    return False
                    
            except Exception as e:
                print(f"[ERROR] Exception in core service submission: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            print(f"[ERROR] Exception in submit_file_for_approval ({self.username}): {e}")
            import traceback
            traceback.print_exc()
            return False

    # =====================================================================================
    # QUICK DIAGNOSTIC SCRIPT
    # =====================================================================================

    # Create this as debug_approvals.py in your root directory
    def debug_user_approvals(username: str):
        """
        Run this to see what's in the user's approval data
        """
        print(f"=== DEBUGGING APPROVALS FOR {username} ===")
        
        # Check user metadata
        user_metadata_file = f"data/user_approvals/{username}/file_approval_status.json"
        print(f"\n1. Checking user metadata: {user_metadata_file}")
        
        if os.path.exists(user_metadata_file):
            try:
                with open(user_metadata_file, 'r') as f:
                    data = json.load(f)
                print(f"✓ Found {len(data)} files in user metadata:")
                for filename, file_data in data.items():
                    print(f"   {filename}: {file_data.get('status')} (submitted: {file_data.get('submitted_for_approval')})")
            except Exception as e:
                print(f"✗ Error reading user metadata: {e}")
        else:
            print("✗ User metadata file does not exist")
        
        # Check new approval queue
        queue_file = "data/new_file_approvals/approval_queue.json"
        print(f"\n2. Checking new approval queue: {queue_file}")
        
        if os.path.exists(queue_file):
            try:
                with open(queue_file, 'r') as f:
                    data = json.load(f)
                user_files = [f for f in data.values() if f.get('user_id') == username]
                print(f"✓ Found {len(user_files)} files for {username} in new queue:")
                for file_data in user_files:
                    print(f"   {file_data.get('original_filename')}: {file_data.get('status')}")
            except Exception as e:
                print(f"✗ Error reading new queue: {e}")
        else:
            print("✗ New approval queue file does not exist")
        
        # Check old approval queue
        old_queue_file = "data/approvals/file_approvals.json"
        print(f"\n3. Checking old approval queue: {old_queue_file}")
        
        if os.path.exists(old_queue_file):
            try:
                with open(old_queue_file, 'r') as f:
                    data = json.load(f)
                user_files = [f for f in data.values() if f.get('user_id') == username]
                print(f"✓ Found {len(user_files)} files for {username} in old queue:")
                for file_data in user_files:
                    print(f"   {file_data.get('original_filename')}: {file_data.get('status')}")
            except Exception as e:
                print(f"✗ Error reading old queue: {e}")
        else:
            print("✗ Old approval queue file does not exist")
        
        print("=== END DEBUG ===")