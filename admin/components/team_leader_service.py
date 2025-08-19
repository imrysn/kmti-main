"""
Enhanced Team Leader Approval Functions

This module provides functions specifically for team leader approval workflow,
with improved team filtering, statistics synchronization, and role-based access control.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from utils.path_config import DATA_PATHS


class TeamLeaderApprovalService:
    """Enhanced service for team leader specific approval operations."""
    
    def __init__(self):
        self.global_queue_file = DATA_PATHS.file_approvals_file
        self.users_file = DATA_PATHS.users_file
        # Ensure network directories exist
        DATA_PATHS.ensure_network_dirs()
    
    def load_global_queue(self) -> Dict:
        """Load global approval queue."""
        try:
            if os.path.exists(self.global_queue_file):
                with open(self.global_queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading global queue: {e}")
        return {}
    
    def save_global_queue(self, queue: Dict) -> bool:
        """Save global approval queue."""
        try:
            with open(self.global_queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving global queue: {e}")
            return False
    
    def get_user_team(self, username: str) -> str:
        """Get user's team from users.json."""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                for email, user_data in users.items():
                    if user_data.get('username') == username:
                        teams = user_data.get('team_tags', [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error getting user team: {e}")
        return "DEFAULT"
    
    def get_all_teams(self) -> List[str]:
        """Get all available teams from team_utils."""
        try:
            from admin.utils.team_utils import get_team_options
            return get_team_options()
        except Exception as e:
            print(f"Error getting all teams: {e}")
            return ["AGCC", "DAIICHI", "KMTI PJ", "KUSAKABE", "MINATOGUMI", "WINDSMILE"]
    
    def get_pending_files_for_team_leader(self, team_leader_username: str, include_filters: Dict = None) -> List[Dict]:
        """
        Get files pending team leader approval for the specific team with enhanced filtering.
        
        Args:
            team_leader_username: Username of the team leader
            include_filters: Optional filters {'team': str, 'status': str, 'search': str}
        """
        try:
            queue = self.load_global_queue()
            team_leader_team = self.get_user_team(team_leader_username)
            pending_files = []
            
            print(f"[DEBUG] TL Service: Looking for files for team '{team_leader_team}' (TL: {team_leader_username})")
            
            for file_id, file_data in queue.items():
                file_status = file_data.get('status', '')
                file_team = file_data.get('user_team', '')
                
                print(f"[DEBUG] File {file_data.get('original_filename', 'Unknown')}: status='{file_status}', team='{file_team}'")
                
                # Team Leader should only see files from their assigned team
                if file_team != team_leader_team:
                    print(f"[DEBUG] ❌ Skipping file (team mismatch: {file_team} != {team_leader_team})")
                    continue
                
                # Only show files that are pending team leader review
                if file_status == 'pending_team_leader' or file_status == 'pending':
                    print(f"[DEBUG] ✅ Adding file to pending list")
                    pending_files.append(file_data)
                else:
                    print(f"[DEBUG] ❌ Skipping file (status not pending TL: {file_status})")
            
            # Apply additional filters if provided
            if include_filters:
                pending_files = self._apply_filters(pending_files, include_filters)
            
            print(f"[DEBUG] Found {len(pending_files)} pending files for team leader")
            
            # Sort by submission date (newest first)
            pending_files.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
            return pending_files
            
        except Exception as e:
            print(f"Error getting pending files for team leader: {e}")
            return []
    
    def _apply_filters(self, files: List[Dict], filters: Dict) -> List[Dict]:
        """Apply additional filters to file list."""
        filtered_files = files
        
        # Search filter
        search_query = filters.get('search', '').lower()
        if search_query:
            filtered_files = [
                f for f in filtered_files
                if (search_query in f.get('original_filename', '').lower() or
                    search_query in f.get('user_id', '').lower() or
                    search_query in f.get('description', '').lower())
            ]
        
        # Status filter (for team leaders showing their approved/rejected files)
        status_filter = filters.get('status', '')
        if status_filter and status_filter != 'ALL':
            filtered_files = [f for f in filtered_files if f.get('status', '') == status_filter]
        
        return filtered_files
    
    def get_team_files_by_status(self, team_leader_username: str, status_filter: str = None) -> Dict[str, List[Dict]]:
        """
        Get all files from team leader's team organized by status.
        🚨 ENHANCED: Now includes approved files that have been moved to project directories.
        Used for comprehensive statistics and filtering.
        """
        try:
            queue = self.load_global_queue()
            team_leader_team = self.get_user_team(team_leader_username)
            
            files_by_status = {
                'pending_team_leader': [],
                'pending_admin': [],
                'approved': [],
                'rejected_by_tl': [],
                'rejected_by_admin': []
            }
            
            # Get files from current queue (pending and in-process files)
            for file_id, file_data in queue.items():
                file_status = file_data.get('status', '')
                file_team = file_data.get('user_team', '')
                
                # Only files from the team leader's team
                if file_team != team_leader_team:
                    continue
                
                # Categorize files by status
                if file_status in ['pending_team_leader', 'pending']:
                    files_by_status['pending_team_leader'].append(file_data)
                elif file_status == 'pending_admin' and file_data.get('tl_approved_by') == team_leader_username:
                    files_by_status['pending_admin'].append(file_data)
                elif file_status == 'approved' and file_data.get('tl_approved_by') == team_leader_username:
                    files_by_status['approved'].append(file_data)
                elif file_status == 'rejected_team_leader' and file_data.get('tl_rejected_by') == team_leader_username:
                    files_by_status['rejected_by_tl'].append(file_data)
                elif file_status == 'rejected_admin':
                    files_by_status['rejected_by_admin'].append(file_data)
            
            # 🚨 ENHANCED: Also get approved files from archives (they've been moved out of queue)
            archived_approved_files = self._get_archived_approved_files_for_team_leader(team_leader_username, team_leader_team)
            files_by_status['approved'].extend(archived_approved_files)
            
            # If status filter is specified, return only that status
            if status_filter and status_filter in files_by_status:
                return {status_filter: files_by_status[status_filter]}
            
            return files_by_status
            
        except Exception as e:
            print(f"Error getting team files by status: {e}")
            return {status: [] for status in ['pending_team_leader', 'pending_admin', 'approved', 'rejected_by_tl', 'rejected_by_admin']}
    
    def submit_for_team_leader(self, file_id: str) -> Tuple[bool, str]:
        """
        Submit file for team leader review.
        Changes status from 'my_files' to 'pending_team_leader'.
        
        Args:
            file_id: File ID to submit
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            queue = self.load_global_queue()
            
            if file_id not in queue:
                return False, "File not found in queue"
            
            file_data = queue[file_id]
            current_status = file_data.get('status', '')
            
            if current_status != 'my_files':
                return False, f"File cannot be submitted from status: {current_status}"
            
            # Update status and add history
            file_data['status'] = 'pending_team_leader'
            file_data['submitted_for_tl_date'] = datetime.now().isoformat()
            
            if 'status_history' not in file_data:
                file_data['status_history'] = []
            
            file_data['status_history'].append({
                'status': 'pending_team_leader',
                'timestamp': datetime.now().isoformat(),
                'comment': 'File submitted for team leader review'
            })
            
            if self.save_global_queue(queue):
                return True, "File submitted for team leader review"
            else:
                return False, "Failed to save submission"
                
        except Exception as e:
            print(f"Error submitting file for team leader: {e}")
            return False, f"Error: {str(e)}"
    
    def approve_as_team_leader(self, file_id: str, reviewer: str) -> Tuple[bool, str]:
        """
        Approve file as team leader.
        Changes status from 'pending_team_leader' to 'pending_admin'.
        
        Args:
            file_id: File ID to approve
            reviewer: Team leader username
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            queue = self.load_global_queue()
            
            if file_id not in queue:
                return False, "File not found in queue"
            
            file_data = queue[file_id]
            current_status = file_data.get('status', '')
            
            if current_status not in ['pending_team_leader', 'pending']:
                return False, f"File cannot be approved from status: {current_status}"
            
            # Verify team leader is from the same team as the file
            reviewer_team = self.get_user_team(reviewer)
            file_team = file_data.get('user_team', '')
            
            if reviewer_team != file_team:
                return False, "Team leader can only approve files from their own team"
            
            # Update status and add approval info
            file_data['status'] = 'pending_admin'
            file_data['tl_approved_by'] = reviewer
            file_data['tl_approved_date'] = datetime.now().isoformat()
            
            if 'status_history' not in file_data:
                file_data['status_history'] = []
            
            file_data['status_history'].append({
                'status': 'pending_admin',
                'timestamp': datetime.now().isoformat(),
                'reviewer': reviewer,
                'comment': f'Approved by team leader {reviewer}'
            })
            
            if self.save_global_queue(queue):
                # Send notification to user about team leader approval
                print(f"[INFO] Sending TL approval notification for file {file_data.get('original_filename')}")
                self._notify_user_status_update(file_data, 'pending_admin', reviewer, 
                    f"Approved by team leader {reviewer} - now pending admin review")
                
                return True, f"File approved by team leader and sent to admin review"
            else:
                return False, "Failed to save approval"
                
        except Exception as e:
            print(f"Error approving file as team leader: {e}")
            return False, f"Error: {str(e)}"
    
    def reject_as_team_leader(self, file_id: str, reviewer: str, reason: str) -> Tuple[bool, str]:
        """
        Reject file as team leader.
        Changes status from 'pending_team_leader' to 'rejected_team_leader'.
        
        Args:
            file_id: File ID to reject
            reviewer: Team leader username
            reason: Rejection reason
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not reason or not reason.strip():
                return False, "Rejection reason is required"
            
            queue = self.load_global_queue()
            
            if file_id not in queue:
                return False, "File not found in queue"
            
            file_data = queue[file_id]
            current_status = file_data.get('status', '')
            
            if current_status not in ['pending_team_leader', 'pending']:
                return False, f"File cannot be rejected from status: {current_status}"
            
            # Verify team leader is from the same team as the file
            reviewer_team = self.get_user_team(reviewer)
            file_team = file_data.get('user_team', '')
            
            if reviewer_team != file_team:
                return False, "Team leader can only reject files from their own team"
            
            # Update status and add rejection info
            file_data['status'] = 'rejected_team_leader'
            file_data['tl_rejected_by'] = reviewer
            file_data['tl_rejected_date'] = datetime.now().isoformat()
            file_data['tl_rejection_reason'] = reason.strip()
            
            if 'status_history' not in file_data:
                file_data['status_history'] = []
            
            file_data['status_history'].append({
                'status': 'rejected_team_leader',
                'timestamp': datetime.now().isoformat(),
                'reviewer': reviewer,
                'comment': f'Rejected by team leader {reviewer}: {reason.strip()}'
            })
            
            if self.save_global_queue(queue):
                # Send notification to user about team leader rejection
                print(f"[INFO] Sending TL rejection notification for file {file_data.get('original_filename')}")
                self._notify_user_status_update(file_data, 'rejected_team_leader', reviewer, 
                    f"Rejected by team leader {reviewer}: {reason.strip()}")
                
                # Archive the rejected file
                self._archive_file(file_data, 'rejected_team_leader')
                
                return True, f"File rejected by team leader"
            else:
                return False, "Failed to save rejection"
                
        except Exception as e:
            print(f"Error rejecting file as team leader: {e}")
            return False, f"Error: {str(e)}"
    
    def get_file_counts_for_team_leader(self, team_leader_username: str, filtered_files: List[Dict] = None) -> Dict[str, int]:
        """
        Get file counts for team leader dashboard.
        Enhanced to support filtered counts or full team statistics.
        
        Args:
            team_leader_username: Username of team leader
            filtered_files: If provided, count only these files instead of all team files
        """
        try:
            if filtered_files is not None:
                # Count from filtered files (for dynamic stats)
                counts = {
                    'pending_team_leader': 0,
                    'approved_by_tl': 0,
                    'rejected_by_tl': 0,
                    'total_visible': len(filtered_files)
                }
                
                for file_data in filtered_files:
                    status = file_data.get('status', '')
                    if status in ['pending_team_leader', 'pending']:
                        counts['pending_team_leader'] += 1
                    elif status == 'pending_admin' and file_data.get('tl_approved_by') == team_leader_username:
                        counts['approved_by_tl'] += 1
                    elif status == 'rejected_team_leader' and file_data.get('tl_rejected_by') == team_leader_username:
                        counts['rejected_by_tl'] += 1
                
                return counts
            else:
                # Count from all team files (for full statistics)
                files_by_status = self.get_team_files_by_status(team_leader_username)
                
                return {
                    'pending_team_leader': len(files_by_status['pending_team_leader']),
                    'approved_by_tl': len(files_by_status['pending_admin']) + len(files_by_status['approved']),
                    'rejected_by_tl': len(files_by_status['rejected_by_tl']),
                    'total_team_files': sum(len(files) for files in files_by_status.values())
                }
            
        except Exception as e:
            print(f"Error getting file counts for team leader: {e}")
            return {'pending_team_leader': 0, 'approved_by_tl': 0, 'rejected_by_tl': 0, 'total_visible': 0}
    
    def _get_archived_approved_files_for_team_leader(self, team_leader_username: str, team_leader_team: str) -> List[Dict]:
        """
        🚨 NEW: Get approved files that have been archived (moved to project directories)
        These files are no longer in the main queue but should still be visible to team leaders
        """
        try:
            archived_approved_files = []
            
            # Load approved files from archive
            archive_dir = os.path.join(DATA_PATHS.SHARED_BASE, "approvals", "archived")
            approved_archive_file = os.path.join(archive_dir, "approved_files.json")
            
            if os.path.exists(approved_archive_file):
                with open(approved_archive_file, 'r', encoding='utf-8') as f:
                    archived_files = json.load(f)
                
                for file_id, file_data in archived_files.items():
                    # Only include files from the team leader's team that they approved
                    if (file_data.get('user_team') == team_leader_team and 
                        file_data.get('tl_approved_by') == team_leader_username):
                        
                        # 🚨 ENHANCED: Add project file location information
                        file_data['current_location'] = self._get_approved_file_current_location(file_data)
                        file_data['file_moved_to_project'] = file_data.get('moved_to_project', True)
                        file_data['display_status'] = 'approved_and_moved'
                        
                        archived_approved_files.append(file_data)
            
            print(f"[DEBUG] Found {len(archived_approved_files)} archived approved files for TL {team_leader_username}")
            return archived_approved_files
            
        except Exception as e:
            print(f"[ERROR] Error getting archived approved files for team leader: {e}")
            return []
    
    def _get_approved_file_current_location(self, file_data: Dict) -> Optional[str]:
        """
        🚨 NEW: Find the current location of an approved file using the enhanced path config
        """
        try:
            original_filename = file_data.get('original_filename')
            team_tag = file_data.get('user_team', 'DEFAULT')
            
            if not original_filename:
                return None
            
            # Try to find the file in possible project locations
            current_path = DATA_PATHS.find_approved_file(original_filename, team_tag)
            
            if current_path and os.path.exists(current_path):
                print(f"[DEBUG] Found approved file {original_filename} at: {current_path}")
                return current_path
            else:
                # Check if it's in the stored project file path
                stored_path = file_data.get('project_file_path')
                if stored_path and os.path.exists(stored_path):
                    print(f"[DEBUG] Found approved file {original_filename} at stored path: {stored_path}")
                    return stored_path
                
                print(f"[WARNING] Could not locate approved file {original_filename} for team {team_tag}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error finding approved file location: {e}")
            return None
    
    def add_comment_to_file(self, file_id: str, reviewer: str, comment: str) -> Tuple[bool, str]:
        """Add a comment to a file without changing its status."""
        try:
            if not comment or not comment.strip():
                return False, "Comment cannot be empty"
            
            queue = self.load_global_queue()
            
            if file_id not in queue:
                return False, "File not found in queue"
            
            file_data = queue[file_id]
            
            # Verify team leader is from the same team as the file
            reviewer_team = self.get_user_team(reviewer)
            file_team = file_data.get('user_team', '')
            
            if reviewer_team != file_team:
                return False, "Team leader can only comment on files from their own team"
            
            if 'tl_comments' not in file_data:
                file_data['tl_comments'] = []
            
            file_data['tl_comments'].append({
                'reviewer': reviewer,
                'comment': comment.strip(),
                'timestamp': datetime.now().isoformat()
            })
            
            if self.save_global_queue(queue):
                return True, "Comment added successfully"
            else:
                return False, "Failed to save comment"
                
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False, f"Error: {str(e)}"


    def _notify_user_status_update(self, file_data: Dict, status: str, reviewer: str, comment: str = ""):
        """Send notification to user about status updates from team leader actions."""
        try:
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not user_id or not original_filename:
                print(f"[WARNING] Missing user_id ({user_id}) or filename ({original_filename}) for TL notification")
                return
            
            # Import here to avoid circular dependencies
            from services.notification_service import NotificationService
            notification_service = NotificationService()
            
            # Update user's approval status file directly
            user_upload_folder = DATA_PATHS.get_user_upload_dir(user_id)
            if os.path.exists(user_upload_folder):
                # Get the user approval service to update their local status
                from user.services.approval_file_service import ApprovalFileService
                user_approval_service = ApprovalFileService(user_upload_folder, user_id)
                
                # Update local approval status
                success = user_approval_service.update_file_status(original_filename, status, comment, reviewer)
                
                if success:
                    print(f"[SUCCESS] Updated user {user_id} file status: {original_filename} -> {status}")
                else:
                    print(f"[WARNING] Failed to update user {user_id} file status: {original_filename}")
            
            # Send notification based on status
            if status == "pending_admin":
                notification_service.notify_approval_status(
                    user_id, original_filename, "approved_by_team_leader", reviewer,
                    f"Your file has been approved by the team leader and is now pending admin review.")
            elif status == "rejected_team_leader":
                notification_service.notify_approval_status(
                    user_id, original_filename, "rejected_by_team_leader", reviewer,
                    f"Your file has been rejected by the team leader. Reason: {comment}")
            
            print(f"[SUCCESS] Notification sent to user {user_id} for TL action on {original_filename}")
            
        except Exception as e:
            print(f"[ERROR] Error sending TL notification to user: {e}")
            import traceback
            traceback.print_exc()
    
    def _archive_file(self, file_data: Dict, status: str):
        """Archive rejected files from team leader actions."""
        try:
            import uuid
            
            archive_dir = os.path.join(DATA_PATHS.SHARED_BASE, "approvals", "archived")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Team leader rejections go to a separate archive
            if status == 'rejected_team_leader':
                archive_file = os.path.join(archive_dir, 'tl_rejected_files.json')
            else:
                return  # Don't archive other statuses from TL
            
            # Load existing archived files
            archived_files = {}
            if os.path.exists(archive_file):
                try:
                    with open(archive_file, 'r', encoding='utf-8') as f:
                        archived_files = json.load(f)
                except Exception as e:
                    print(f"[WARNING] Error loading TL archive file {archive_file}: {e}")
                    archived_files = {}
            
            # Add current file to archive
            file_id = file_data.get('file_id', str(uuid.uuid4()))
            file_data['archived_date'] = datetime.now().isoformat()
            archived_files[file_id] = file_data
            
            # Keep only last 1000 archived files
            if len(archived_files) > 1000:
                # Sort by archived_date and keep newest 1000
                sorted_files = sorted(archived_files.items(), 
                                     key=lambda x: x[1].get('archived_date', ''), 
                                     reverse=True)
                archived_files = dict(sorted_files[:1000])
            
            # Save updated archive
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archived_files, f, indent=2)
            
            print(f"[INFO] TL Archived file {file_data.get('original_filename')} with status {status}")
            
        except Exception as e:
            print(f"[ERROR] Error archiving TL file: {e}")
            import traceback
            traceback.print_exc()


def get_team_leader_service() -> TeamLeaderApprovalService:
    """Get team leader approval service instance."""
    return TeamLeaderApprovalService()
