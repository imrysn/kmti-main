import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"

class FileApprovalService:
    """Service to handle file approvals from admin side"""
    
    def __init__(self):
        self.approvals_dir = "data/approvals"
        self.approvals_file = os.path.join(self.approvals_dir, "file_approvals.json")
        self.comments_file = os.path.join(self.approvals_dir, "approval_comments.json")
        
        # Ensure directories exist
        os.makedirs(self.approvals_dir, exist_ok=True)
    
    def load_approvals(self) -> Dict:
        """Load all pending approvals"""
        try:
            if os.path.exists(self.approvals_file):
                with open(self.approvals_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading approvals: {e}")
        return {}
    
    def save_approvals(self, approvals: Dict) -> bool:
        """Save approvals data"""
        try:
            with open(self.approvals_file, 'w') as f:
                json.dump(approvals, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving approvals: {e}")
            return False
    
    def load_comments(self) -> Dict:
        """Load approval comments"""
        try:
            if os.path.exists(self.comments_file):
                with open(self.comments_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading comments: {e}")
        return {}
    
    def save_comments(self, comments: Dict) -> bool:
        """Save approval comments"""
        try:
            with open(self.comments_file, 'w') as f:
                json.dump(comments, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving comments: {e}")
            return False
    
    def get_pending_files_by_team(self, team: str, is_super_admin: bool = False) -> List[Dict]:
        """Get pending files filtered by team"""
        try:
            approvals = self.load_approvals()
            pending_files = []
            
            for file_id, file_data in approvals.items():
                if file_data.get('status') == 'pending':
                    # Super admin can see all files
                    if is_super_admin or file_data.get('user_team') == team:
                        pending_files.append(file_data)
            
            # Sort by submission date (newest first)
            pending_files.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
            return pending_files
            
        except Exception as e:
            print(f"Error getting pending files: {e}")
            return []
    
    def approve_file(self, file_id: str, admin_id: str) -> bool:
        """Approve a file"""
        try:
            approvals = self.load_approvals()
            
            if file_id in approvals:
                file_data = approvals[file_id]
                
                # Update approval status
                approvals[file_id]['status'] = ApprovalStatus.APPROVED.value
                approvals[file_id]['approved_by'] = admin_id
                approvals[file_id]['approved_date'] = datetime.now().isoformat()
                approvals[file_id]['last_updated'] = datetime.now().isoformat()
                
                # Add to status history
                if 'status_history' not in approvals[file_id]:
                    approvals[file_id]['status_history'] = []
                
                approvals[file_id]['status_history'].append({
                    'status': ApprovalStatus.APPROVED.value,
                    'timestamp': datetime.now().isoformat(),
                    'admin_id': admin_id,
                    'comment': 'File approved'
                })
                
                # Save approvals
                if self.save_approvals(approvals):
                    # Update user's submission status
                    self.update_user_file_status(file_data, ApprovalStatus.APPROVED.value, admin_id, "File approved")
                    return True
            
        except Exception as e:
            print(f"Error approving file: {e}")
        
        return False
    
    def reject_file(self, file_id: str, admin_id: str, reason: str, request_changes: bool = False) -> bool:
        """Reject a file or request changes"""
        try:
            approvals = self.load_approvals()
            
            if file_id in approvals:
                file_data = approvals[file_id]
                
                # Update approval status
                status = ApprovalStatus.CHANGES_REQUESTED.value if request_changes else ApprovalStatus.REJECTED.value
                approvals[file_id]['status'] = status
                approvals[file_id]['rejected_by'] = admin_id
                approvals[file_id]['rejected_date'] = datetime.now().isoformat()
                approvals[file_id]['rejection_reason'] = reason
                approvals[file_id]['last_updated'] = datetime.now().isoformat()
                
                # Add to status history
                if 'status_history' not in approvals[file_id]:
                    approvals[file_id]['status_history'] = []
                
                approvals[file_id]['status_history'].append({
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'admin_id': admin_id,
                    'comment': reason
                })
                
                # Save approvals
                if self.save_approvals(approvals):
                    # Update user's submission status
                    self.update_user_file_status(file_data, status, admin_id, reason)
                    return True
            
        except Exception as e:
            print(f"Error rejecting file: {e}")
        
        return False
    
    def add_comment(self, file_id: str, admin_id: str, comment: str) -> bool:
        """Add comment to a file"""
        try:
            comments = self.load_comments()
            
            if file_id not in comments:
                comments[file_id] = []
            
            comment_data = {
                'admin_id': admin_id,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            }
            
            comments[file_id].append(comment_data)
            
            if self.save_comments(comments):
                # Also add comment to user's submission
                approvals = self.load_approvals()
                if file_id in approvals:
                    file_data = approvals[file_id]
                    
                    if 'admin_comments' not in approvals[file_id]:
                        approvals[file_id]['admin_comments'] = []
                    
                    approvals[file_id]['admin_comments'].append(comment_data)
                    self.save_approvals(approvals)
                    
                    # Update user's submission with comment
                    self.update_user_file_comment(file_data, admin_id, comment)
                
                return True
        
        except Exception as e:
            print(f"Error adding comment: {e}")
        
        return False
    
    def update_user_file_status(self, file_data: Dict, status: str, admin_id: str, comment: str = ""):
        """Update the user's local file approval status"""
        try:
            username = file_data.get('user_id')
            filename = file_data.get('original_filename')
            
            if not username or not filename:
                return
            
            # Find user's approval status file
            user_folder = f"data/uploads/{username}"
            user_status_file = os.path.join(user_folder, "file_approval_status.json")
            
            if os.path.exists(user_status_file):
                with open(user_status_file, 'r') as f:
                    user_status = json.load(f)
                
                if filename in user_status:
                    user_status[filename]['status'] = status
                    user_status[filename]['last_updated'] = datetime.now().isoformat()
                    
                    # Add admin comment if provided
                    if comment:
                        if 'admin_comments' not in user_status[filename]:
                            user_status[filename]['admin_comments'] = []
                        
                        user_status[filename]['admin_comments'].append({
                            'admin_id': admin_id,
                            'comment': comment,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    # Add to status history
                    if 'status_history' not in user_status[filename]:
                        user_status[filename]['status_history'] = []
                    
                    user_status[filename]['status_history'].append({
                        'status': status,
                        'timestamp': datetime.now().isoformat(),
                        'admin_id': admin_id,
                        'comment': comment
                    })
                    
                    # Save updated status
                    with open(user_status_file, 'w') as f:
                        json.dump(user_status, f, indent=2)
                    
                    # Add notification for user
                    self.add_user_notification(username, {
                        'type': 'status_update',
                        'filename': filename,
                        'old_status': 'pending',
                        'new_status': status,
                        'admin_id': admin_id,
                        'comment': comment,
                        'timestamp': datetime.now().isoformat(),
                        'read': False
                    })
        
        except Exception as e:
            print(f"Error updating user file status: {e}")
    
    def update_user_file_comment(self, file_data: Dict, admin_id: str, comment: str):
        """Update user's file with new comment"""
        try:
            username = file_data.get('user_id')
            filename = file_data.get('original_filename')
            
            if not username or not filename:
                return
            
            # Find user's approval status file
            user_folder = f"data/uploads/{username}"
            user_status_file = os.path.join(user_folder, "file_approval_status.json")
            
            if os.path.exists(user_status_file):
                with open(user_status_file, 'r') as f:
                    user_status = json.load(f)
                
                if filename in user_status:
                    if 'admin_comments' not in user_status[filename]:
                        user_status[filename]['admin_comments'] = []
                    
                    user_status[filename]['admin_comments'].append({
                        'admin_id': admin_id,
                        'comment': comment,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Save updated status
                    with open(user_status_file, 'w') as f:
                        json.dump(user_status, f, indent=2)
                    
                    # Add notification for user
                    self.add_user_notification(username, {
                        'type': 'comment_added',
                        'filename': filename,
                        'admin_id': admin_id,
                        'comment': comment,
                        'timestamp': datetime.now().isoformat(),
                        'read': False
                    })
        
        except Exception as e:
            print(f"Error updating user file comment: {e}")
    
    def add_user_notification(self, username: str, notification: Dict):
        """Add notification to user's notification list"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            # Load existing notifications
            notifications = []
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                    if not isinstance(notifications, list):
                        notifications = []
            
            # Add new notification to beginning
            notifications.insert(0, notification)
            
            # Keep only last 50 notifications
            notifications = notifications[:50]
            
            # Save notifications
            os.makedirs(user_folder, exist_ok=True)
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
        
        except Exception as e:
            print(f"Error adding user notification: {e}")
    
    def get_approval_statistics(self) -> Dict:
        """Get approval statistics"""
        try:
            approvals = self.load_approvals()
            
            stats = {
                'total': len(approvals),
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'changes_requested': 0
            }
            
            for file_data in approvals.values():
                status = file_data.get('status', 'unknown')
                if status in stats:
                    stats[status] += 1
            
            return stats
        
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0, 'changes_requested': 0}
    
    def cleanup_old_approvals(self, days: int = 30):
        """Clean up old approved/rejected submissions"""
        try:
            approvals = self.load_approvals()
            cutoff_date = datetime.now()
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            to_remove = []
            
            for file_id, file_data in approvals.items():
                if file_data.get('status') in ['approved', 'rejected']:
                    last_updated = file_data.get('last_updated')
                    if last_updated:
                        try:
                            update_date = datetime.fromisoformat(last_updated)
                            if update_date < cutoff_date:
                                to_remove.append(file_id)
                        except:
                            pass
            
            # Remove old entries
            for file_id in to_remove:
                del approvals[file_id]
            
            if to_remove:
                self.save_approvals(approvals)
                print(f"Cleaned up {len(to_remove)} old approval records")
            
        except Exception as e:
            print(f"Error cleaning up old approvals: {e}")