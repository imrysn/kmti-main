import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from utils.logger import log_action
from utils.session_logger import log_activity

class ApprovalFileService:
    """Service class to handle file approval status for uploaded files"""
    
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.approval_status_file = os.path.join(user_folder, "file_approval_status.json")
        self.notifications_file = os.path.join(user_folder, "approval_notifications.json")
        
        # Ensure folders exist
        os.makedirs(user_folder, exist_ok=True)
        
        # Get user team from users.json
        self.user_team = self.get_user_team()
    
    def get_user_team(self) -> str:
        """Get user's team from users.json"""
        try:
            users_file = "data/users.json"
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
    
    def load_approval_status(self) -> Dict:
        """Load approval status for user's files"""
        try:
            if os.path.exists(self.approval_status_file):
                with open(self.approval_status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading approval status: {e}")
        return {}
    
    def save_approval_status(self, status_data: Dict) -> bool:
        """Save approval status for user's files"""
        try:
            with open(self.approval_status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
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
        """Get all uploaded files from the regular files directory"""
        files = []
        try:
            if os.path.exists(self.user_folder):
                for filename in os.listdir(self.user_folder):
                    file_path = os.path.join(self.user_folder, filename)
                    
                    # Skip directories and system files
                    if (os.path.isfile(file_path) and 
                        filename not in ["files_metadata.json", "profile.json", "file_approval_status.json", "approval_notifications.json"] and
                        not filename.startswith(".")):
                        
                        # Get file stats
                        stat = os.stat(file_path)
                        modified_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Get approval status for this file
                        approval_status = self.get_file_approval_status(filename)
                        
                        file_info = {
                            "filename": filename,
                            "file_path": file_path,
                            "file_size": stat.st_size,
                            "upload_date": modified_time.isoformat(),
                            "status": approval_status.get("status", "not_submitted"),
                            "submitted_for_approval": approval_status.get("submitted_for_approval", False),
                            "submission_date": approval_status.get("submission_date"),
                            "admin_comments": approval_status.get("admin_comments", []),
                            "status_history": approval_status.get("status_history", []),
                            "description": approval_status.get("description", ""),
                            "tags": approval_status.get("tags", [])
                        }
                        files.append(file_info)
                        
                # Sort files by upload time (newest first)
                files.sort(key=lambda x: x["upload_date"], reverse=True)
                        
        except Exception as e:
            print(f"Error getting uploaded files: {e}")
            
        return files
    
    def get_file_approval_status(self, filename: str) -> Dict:
        """Get approval status for a specific file"""
        approval_data = self.load_approval_status()
        return approval_data.get(filename, {
            "status": "not_submitted",
            "submitted_for_approval": False,
            "submission_date": None,
            "admin_comments": [],
            "status_history": [],
            "description": "",
            "tags": []
        })
    
    def submit_file_for_approval(self, filename: str, description: str = "", tags: List[str] = None) -> bool:
        """Submit an uploaded file for approval"""
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
                "status": "pending",
                "submitted_for_approval": True,
                "submission_date": datetime.now().isoformat(),
                "description": description,
                "tags": tags,
                "admin_comments": [],
                "status_history": [{
                    "status": "pending",
                    "timestamp": datetime.now().isoformat(),
                    "comment": "File submitted for approval"
                }]
            }
            
            if self.save_approval_status(approval_data):
                # Add to global approval queue
                self.add_to_global_queue(filename, file_id, description, tags)
                
                log_action(self.username, f"Submitted file for approval: {filename}")
                log_activity(self.username, f"Submitted file for approval: {filename}")
                return True
                
        except Exception as e:
            print(f"Error submitting file for approval: {e}")
        
        return False
    
    def add_to_global_queue(self, filename: str, file_id: str, description: str, tags: List[str]):
        """Add file to global approval queue"""
        try:
            # Ensure global approvals directory exists
            global_approvals_dir = "data/approvals"
            os.makedirs(global_approvals_dir, exist_ok=True)
            
            global_queue_file = os.path.join(global_approvals_dir, "file_approvals.json")
            
            # Load existing queue
            queue = {}
            if os.path.exists(global_queue_file):
                with open(global_queue_file, 'r') as f:
                    queue = json.load(f)
            
            # Get file info
            file_path = os.path.join(self.user_folder, filename)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            # Add new submission
            submission_data = {
                "file_id": file_id,
                "original_filename": filename,
                "user_id": self.username,
                "user_team": self.user_team,
                "file_size": file_size,
                "submission_date": datetime.now().isoformat(),
                "status": "pending",
                "description": description,
                "tags": tags,
                "admin_comments": [],
                "status_history": [{
                    "status": "pending",
                    "timestamp": datetime.now().isoformat(),
                    "comment": "File submitted for approval"
                }],
                "file_path": file_path  # Store path for admin access
            }
            
            queue[file_id] = submission_data
            
            # Save updated queue
            with open(global_queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
                
        except Exception as e:
            print(f"Error adding to global queue: {e}")
    
    def get_user_submissions(self) -> List[Dict]:
        """Get all files with their approval status"""
        files = self.get_uploaded_files()
        
        # Filter to show only files that have been submitted for approval or have status updates
        submissions = []
        for file_info in files:
            if (file_info["submitted_for_approval"] or 
                file_info["status"] != "not_submitted"):
                submissions.append({
                    "original_filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "upload_date": file_info["upload_date"],
                    "submission_date": file_info["submission_date"],
                    "status": file_info["status"],
                    "description": file_info["description"],
                    "tags": file_info["tags"],
                    "admin_comments": file_info["admin_comments"],
                    "status_history": file_info["status_history"]
                })
        
        return submissions
    
    def get_available_files_for_submission(self) -> List[Dict]:
        """Get files that can be submitted for approval (not yet submitted)"""
        files = self.get_uploaded_files()
        
        available_files = []
        for file_info in files:
            if not file_info["submitted_for_approval"] and file_info["status"] == "not_submitted":
                available_files.append({
                    "filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "upload_date": file_info["upload_date"]
                })
        
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
                    "old_status": "pending",  # This could be improved to track actual old status
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
        """Add a new notification for the user"""
        try:
            notifications = self.load_notifications()
            notifications.insert(0, notification)  # Add to beginning (newest first)
            
            # Keep only last 50 notifications
            notifications = notifications[:50]
            
            self.save_notifications(notifications)
        except Exception as e:
            print(f"Error adding notification: {e}")
    
    def mark_notification_read(self, notification_index: int):
        """Mark a notification as read"""
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
        """Get count of unread notifications"""
        notifications = self.load_notifications()
        return len([n for n in notifications if not n.get("read", False)])
    
    def withdraw_submission(self, filename: str) -> bool:
        """Withdraw a pending submission"""
        try:
            approval_data = self.load_approval_status()
            
            if filename in approval_data:
                file_data = approval_data[filename]
                
                # Only allow withdrawal of pending submissions
                if file_data.get("status") != "pending":
                    return False
                
                # Get file_id for global queue removal
                file_id = file_data.get("file_id")
                
                # Reset approval status
                approval_data[filename] = {
                    "status": "not_submitted",
                    "submitted_for_approval": False,
                    "submission_date": None,
                    "admin_comments": [],
                    "status_history": [],
                    "description": "",
                    "tags": []
                }
                
                self.save_approval_status(approval_data)
                
                # Remove from global queue if file_id exists
                if file_id:
                    self.remove_from_global_queue(file_id)
                
                log_action(self.username, f"Withdrew submission: {filename}")
                log_activity(self.username, f"Withdrew submission: {filename}")
                
                return True
        except Exception as e:
            print(f"Error withdrawing submission: {e}")
        return False
    
    def remove_from_global_queue(self, file_id: str):
        """Remove submission from global approval queue"""
        try:
            global_queue_file = "data/approvals/file_approvals.json"
            if os.path.exists(global_queue_file):
                with open(global_queue_file, 'r') as f:
                    queue = json.load(f)
                
                if file_id in queue:
                    del queue[file_id]
                    
                    with open(global_queue_file, 'w') as f:
                        json.dump(queue, f, indent=2)
        except Exception as e:
            print(f"Error removing from global queue: {e}")
    
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
                
                # Add back to global queue
                self.add_to_global_queue(filename, new_file_id, description or file_data.get("description", ""), tags or file_data.get("tags", []))
                
                log_action(self.username, f"Resubmitted file: {filename}")
                log_activity(self.username, f"Resubmitted file: {filename}")
                
                return True
        except Exception as e:
            print(f"Error resubmitting file: {e}")
        return False
    
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