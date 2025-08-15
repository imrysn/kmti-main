import os
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional
from services.file_approval_constant import FileApprovalStatus

class NewFileApprovalService:
    """
    New approval service that maintains compatibility with existing UI
    Replace your old approval_service.py imports with this
    """
    
    def __init__(self):
        self.data_dir = "data/new_file_approvals"
        self.queue_file = os.path.join(self.data_dir, "approval_queue.json") 
        self.approved_file = os.path.join(self.data_dir, "approved_files.json")
        self.rejected_file = os.path.join(self.data_dir, "rejected_files.json")
        self.comments_file = os.path.join(self.data_dir, "file_comments.json")
        self._lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON files if they don't exist"""
        for file_path in [self.queue_file, self.approved_file, self.rejected_file, self.comments_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
    
    def _load_json_file(self, file_path: str) -> dict:
        """Safely load JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json_file(self, file_path: str, data: dict) -> bool:
        """Safely save JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            return False
        
    def team_leader_approve(self, file_id: str, leader_user: str) -> bool:
        """
        COMPATIBILITY METHOD: Team Leader approves file
        Stage 1 (pending_team_leader) → Stage 2 (pending_admin)
        """
        with self._lock:
            try:
                queue = self._load_json_file(self.queue_file)
                
                if file_id not in queue:
                    print(f"File ID {file_id} not found in queue")
                    return False
                
                file_data = queue[file_id]
                current_status = file_data.get("status")
                
                if current_status != FileApprovalStatus.PENDING_TEAM_LEADER:
                    print(f"File {file_id} has status '{current_status}', cannot approve at Team Leader stage")
                    return False
                
                # Move to Stage 2: Pending Admin
                file_data["status"] = FileApprovalStatus.PENDING_ADMIN
                file_data["team_leader_approved_by"] = leader_user
                file_data["team_leader_approved_date"] = datetime.now().isoformat()
                
                file_data.setdefault("workflow_history", []).append({
                    "status": FileApprovalStatus.PENDING_ADMIN,
                    "timestamp": datetime.now().isoformat(),
                    "admin_id": leader_user,
                    "comment": "Approved by Team Leader - forwarded to Admin"
                })
                
                if self._save_json_file(self.queue_file, queue):
                    print(f"✓ Team Leader {leader_user} approved file {file_id}")
                    return True
                else:
                    return False
                    
            except Exception as e:
                print(f"Error in team_leader_approve: {e}")
                return False
    
    def team_leader_reject(self, file_id: str, leader_user: str, reason: str, request_changes: bool = False) -> bool:
        """
        COMPATIBILITY METHOD: Team Leader rejects file
        """
        with self._lock:
            try:
                queue = self._load_json_file(self.queue_file)
                
                if file_id not in queue:
                    return False
                
                file_data = queue[file_id]
                if file_data.get("status") != FileApprovalStatus.PENDING_TEAM_LEADER:
                    return False
                
                # Set rejection status
                new_status = FileApprovalStatus.CHANGES_REQUESTED if request_changes else FileApprovalStatus.REJECTED_TEAM_LEADER
                file_data["status"] = new_status
                file_data["rejected_by"] = leader_user
                file_data["rejected_date"] = datetime.now().isoformat()
                file_data["rejection_reason"] = reason
                
                file_data.setdefault("workflow_history", []).append({
                    "status": new_status,
                    "timestamp": datetime.now().isoformat(),
                    "admin_id": leader_user,
                    "comment": f"Rejected by Team Leader: {reason}"
                })
                
                # Move to rejected files
                rejected_files = self._load_json_file(self.rejected_file)
                rejected_files[file_id] = file_data
                
                # Remove from active queue
                del queue[file_id]
                
                # Save both files
                success = (self._save_json_file(self.queue_file, queue) and 
                          self._save_json_file(self.rejected_file, rejected_files))
                
                if success:
                    print(f"✓ Team Leader {leader_user} rejected file {file_id}")
                return success
                
            except Exception as e:
                print(f"Error in team_leader_reject: {e}")
                return False
    
    def approve_by_admin(self, file_id: str, admin_user: str) -> bool:
        """
        COMPATIBILITY METHOD: Admin gives final approval
        Stage 2 (pending_admin) → Stage 3 (approved)  
        """
        with self._lock:
            try:
                queue = self._load_json_file(self.queue_file)
                
                if file_id not in queue:
                    print(f"File ID {file_id} not found in queue")
                    return False
                
                file_data = queue[file_id]
                current_status = file_data.get("status")
                
                if current_status != FileApprovalStatus.PENDING_ADMIN:
                    print(f"File {file_id} has status '{current_status}', cannot approve at Admin stage")
                    return False
                
                # Final approval - Stage 3
                file_data["status"] = FileApprovalStatus.APPROVED
                file_data["admin_approved_by"] = admin_user
                file_data["admin_approved_date"] = datetime.now().isoformat()
                
                file_data.setdefault("workflow_history", []).append({
                    "status": FileApprovalStatus.APPROVED,
                    "timestamp": datetime.now().isoformat(),
                    "admin_id": admin_user,
                    "comment": "Final approval by Admin"
                })
                
                # Move to approved files
                approved_files = self._load_json_file(self.approved_file)
                approved_files[file_id] = file_data
                
                # Remove from active queue  
                del queue[file_id]
                
                # Save both files
                success = (self._save_json_file(self.queue_file, queue) and 
                          self._save_json_file(self.approved_file, approved_files))
                
                if success:
                    print(f"✓ Admin {admin_user} gave final approval to file {file_id}")
                return success
                
            except Exception as e:
                print(f"Error in approve_by_admin: {e}")
                return False
    
    def reject_by_admin(self, file_id: str, admin_user: str, reason: str, request_changes: bool = False) -> bool:
        """
        COMPATIBILITY METHOD: Admin rejects file
        """
        with self._lock:
            try:
                queue = self._load_json_file(self.queue_file)
                
                if file_id not in queue:
                    return False
                
                file_data = queue[file_id]
                if file_data.get("status") != FileApprovalStatus.PENDING_ADMIN:
                    return False
                
                # Set rejection status
                new_status = FileApprovalStatus.CHANGES_REQUESTED if request_changes else FileApprovalStatus.REJECTED_ADMIN
                file_data["status"] = new_status
                file_data["rejected_by"] = admin_user
                file_data["rejected_date"] = datetime.now().isoformat()
                file_data["rejection_reason"] = reason
                
                file_data.setdefault("workflow_history", []).append({
                    "status": new_status,
                    "timestamp": datetime.now().isoformat(),
                    "admin_id": admin_user,
                    "comment": f"Rejected by Admin: {reason}"
                })
                
                # Move to rejected files
                rejected_files = self._load_json_file(self.rejected_file)
                rejected_files[file_id] = file_data
                
                # Remove from active queue
                del queue[file_id]
                
                # Save both files
                success = (self._save_json_file(self.queue_file, queue) and 
                          self._save_json_file(self.rejected_file, rejected_files))
                
                if success:
                    print(f"✓ Admin {admin_user} rejected file {file_id}")
                return success
                
            except Exception as e:
                print(f"Error in reject_by_admin: {e}")
                return False
    
    def add_comment(self, file_id: str, admin_user: str, comment: str) -> bool:
        """
        COMPATIBILITY METHOD: Add comment to file
        """
        try:
            comments = self._load_json_file(self.comments_file)
            
            if file_id not in comments:
                comments[file_id] = []
            
            comment_entry = {
                "admin_id": admin_user,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            comments[file_id].append(comment_entry)
            return self._save_json_file(self.comments_file, comments)
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def load_comments(self) -> Dict[str, List[Dict]]:
        """
        COMPATIBILITY METHOD: Load all comments
        """
        return self._load_json_file(self.comments_file)
    
    # ---------------------------------------------------------------------------------
    # USER SUBMISSION AND WITHDRAWAL METHODS 
    # ---------------------------------------------------------------------------------
    
    def submit_file_for_approval(self, user_id: str, filename: str, file_path: str, 
                                user_team: str, description: str = "", tags: list = None) -> Optional[str]:
        """Submit file for Team Leader approval (Stage 0 → Stage 1)"""
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return None
            
            file_id = str(uuid.uuid4())
            file_size = os.path.getsize(file_path)
            
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
                "tags": tags or [],
                "workflow_history": [{
                    "status": FileApprovalStatus.PENDING_TEAM_LEADER,
                    "timestamp": datetime.now().isoformat(),
                    "action": "submitted",
                    "actor": user_id,
                    "comment": "File submitted for Team Leader review"
                }]
            }
            
            with self._lock:
                queue = self._load_json_file(self.queue_file)
                queue[file_id] = submission
                
                if self._save_json_file(self.queue_file, queue):
                    print(f"✓ File {filename} submitted for approval with ID: {file_id}")
                    return file_id
                else:
                    return None
                    
        except Exception as e:
            print(f"Error submitting file {filename}: {e}")
            return None
    
    def withdraw_submission(self, file_id: str) -> bool:
        """Withdraw a submission from the queue"""
        try:
            with self._lock:
                queue = self._load_json_file(self.queue_file)
                
                if file_id not in queue:
                    print(f"File ID {file_id} not found in queue")
                    return False
                
                file_data = queue[file_id]
                current_status = file_data.get("status")
                
                # Only allow withdrawal of pending files
                if current_status not in [FileApprovalStatus.PENDING_TEAM_LEADER, FileApprovalStatus.PENDING_ADMIN]:
                    print(f"Cannot withdraw file with status: {current_status}")
                    return False
                
                # Add to workflow history
                file_data["status"] = FileApprovalStatus.WITHDRAWN
                file_data["withdrawn_date"] = datetime.now().isoformat()
                file_data.setdefault("workflow_history", []).append({
                    "status": FileApprovalStatus.WITHDRAWN,
                    "timestamp": datetime.now().isoformat(),
                    "action": "withdrawn",
                    "actor": file_data.get("user_id"),
                    "comment": "Submission withdrawn by user"
                })
                
                # Remove from active queue
                del queue[file_id]
                
                if self._save_json_file(self.queue_file, queue):
                    print(f"✓ File {file_id} withdrawn successfully")
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Error withdrawing file {file_id}: {e}")
            return False
    
    # ---------------------------------------------------------------------------------
    # QUERY METHODS FOR UI COMPONENTS
    # ---------------------------------------------------------------------------------
    
    def get_pending_team_leader_files(self, team: str) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get files pending Team Leader approval for specific team
        """
        queue = self._load_json_file(self.queue_file)
        return [
            file_data for file_data in queue.values()
            if (file_data.get("status") == FileApprovalStatus.PENDING_TEAM_LEADER and
                file_data.get("user_team") == team)
        ]
    
    def get_pending_admin_files(self) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get files pending Admin approval
        """
        queue = self._load_json_file(self.queue_file)
        return [
            file_data for file_data in queue.values()
            if file_data.get("status") == FileApprovalStatus.PENDING_ADMIN
        ]
    
    def get_approved_files_by_team(self, team: str) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get approved files for a team
        """
        approved = self._load_json_file(self.approved_file)
        return [
            file_data for file_data in approved.values()
            if file_data.get("user_team") == team
        ]
    
    def get_rejected_files_by_team(self, team: str) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get rejected files for a team
        """
        rejected = self._load_json_file(self.rejected_file)
        return [
            file_data for file_data in rejected.values()
            if file_data.get("user_team") == team
        ]
    
    def get_all_files_by_team(self, team: str) -> List[Dict]:
        """
        COMPATIBILITY METHOD: Get all files for a team
        """
        all_files = []
        
        # Active queue
        queue = self._load_json_file(self.queue_file)
        all_files.extend([f for f in queue.values() if f.get("user_team") == team])
        
        # Approved files
        approved = self._load_json_file(self.approved_file)
        all_files.extend([f for f in approved.values() if f.get("user_team") == team])
        
        # Rejected files
        rejected = self._load_json_file(self.rejected_file)
        all_files.extend([f for f in rejected.values() if f.get("user_team") == team])
        
        return all_files
