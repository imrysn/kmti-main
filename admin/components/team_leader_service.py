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


def get_team_leader_service() -> TeamLeaderApprovalService:
    """Get team leader approval service instance."""
    return TeamLeaderApprovalService()
