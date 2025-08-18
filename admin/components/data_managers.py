from typing import Dict, List, Optional
from utils.logger import PerformanceTimer, log_performance_metric
import json
import os


class FileDataManager:
    """Enhanced file data manager with improved statistics and filtering capabilities."""
    
    def __init__(self, approval_service, permission_service, enhanced_logger):

        self.approval_service = approval_service
        self.permission_service = permission_service
        self.enhanced_logger = enhanced_logger
    
    def get_file_counts_safely(self, admin_user: str, admin_teams: List[str],
                              admin_role: str, filtered_files: Optional[List[Dict]] = None) -> Dict[str, int]:
        """
        Get file counts with option to calculate from filtered files for dynamic statistics.
        
        Args:
            admin_user: Admin username
            admin_teams: Admin's teams
            admin_role: Admin's role
            filtered_files: If provided, calculate stats from these files instead of all files
        """
        try:
            with PerformanceTimer("FileApprovalPanel", "get_file_counts"):
                if filtered_files is not None:
                    # Calculate from filtered files (for dynamic statistics)
                    return self._calculate_counts_from_files(filtered_files)
                
                # Calculate from all accessible files (for overall statistics)
                reviewable_teams = self.permission_service.get_reviewable_teams(
                    admin_user, admin_teams)
                
                pending_files = set()
                approved_files = set()
                rejected_files = set()
                
                for team in reviewable_teams:
                    try:
                        team_pending = self.approval_service.get_pending_files_by_team(
                            team, admin_role)
                        for file_data in team_pending:
                            pending_files.add(file_data['file_id'])
                        
                        team_approved = self._get_approved_files_by_team_safe(team, admin_role)
                        for file_data in team_approved:
                            approved_files.add(file_data['file_id'])
                        
                        team_rejected = self._get_rejected_files_by_team_safe(team, admin_role)
                        for file_data in team_rejected:
                            rejected_files.add(file_data['file_id'])
                            
                    except Exception as team_error:
                        self.enhanced_logger.general_logger.warning(
                            f"Error getting files for team {team}: {team_error}")
                        continue
                
                counts = {
                    'pending': len(pending_files),
                    'approved': len(approved_files), 
                    'rejected': len(rejected_files),
                    'total': len(pending_files) + len(approved_files) + len(rejected_files)
                }
                
                log_performance_metric("FileApprovalPanel", "file_counts", 50.0, counts)
                
                return counts
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting file counts: {e}")
            return {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}
    
    def _calculate_counts_from_files(self, files: List[Dict]) -> Dict[str, int]:
        """Calculate statistics from a specific list of files."""
        counts = {
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'total': len(files)
        }
        
        for file_data in files:
            status = file_data.get('status', '').lower()
            if status in ['pending_team_leader', 'pending_admin', 'pending']:
                counts['pending'] += 1
            elif status in ['approved', 'approved_by_admin']:
                counts['approved'] += 1
            elif status in ['rejected_team_leader', 'rejected_admin', 'rejected']:
                counts['rejected'] += 1
        
        return counts
    
    def _get_approved_files_by_team_safe(self, team: str, admin_role: str) -> List[Dict]:

        try:
            return self.approval_service.get_approved_files_by_team(team, admin_role)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team, admin_role)
                return [f for f in all_files if f.get('status') in ['approved', 'approved_by_admin']]
            except Exception:
                return []
    
    def _get_rejected_files_by_team_safe(self, team: str, admin_role: str) -> List[Dict]:

        try:
            return self.approval_service.get_rejected_files_by_team(team, admin_role)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team, admin_role)
                return [f for f in all_files if f.get('status') in ['rejected_team_leader', 'rejected_admin', 'rejected']]
            except Exception:
                return []
    
    def get_filtered_pending_files(self, admin_user: str, admin_teams: List[str],
                                  admin_role: str) -> List[Dict]:
        """Get pending files that admin can review with improved filtering."""
        try:
            # For admin, get files pending admin review (status = 'pending_admin')
            if admin_role.upper() == 'ADMIN':
                return self._get_admin_pending_files(admin_user, admin_teams)
            
            # For team leaders, delegate to their service
            reviewable_teams = self.permission_service.get_reviewable_teams(
                admin_user, admin_teams)
            all_pending = []
            
            for team in reviewable_teams:
                try:
                    team_files = self.approval_service.get_pending_files_by_team(
                        team, admin_role)
                    all_pending.extend(team_files)
                except Exception as team_error:
                    self.enhanced_logger.general_logger.warning(
                        f"Error getting files for team {team}: {team_error}")
                    continue
            
            # Remove duplicates based on file_id
            unique_files = {file_data['file_id']: file_data for file_data in all_pending}
            return list(unique_files.values())
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting filtered pending files: {e}")
            return []
    
    def _get_admin_pending_files(self, admin_user: str, admin_teams: List[str]) -> List[Dict]:
        """Get files pending admin review (status = 'pending_admin')."""
        try:
            approvals_file = os.path.join(r"\\KMTI-NAS\Shared\data", "approvals", "file_approvals.json")
            if not os.path.exists(approvals_file):
                return []
            
            with open(approvals_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            
            pending_admin_files = []
            for file_id, file_data in queue.items():
                status = file_data.get('status', '')
                
                # Admin sees files that are pending_admin (approved by TL, waiting for admin)
                if status == 'pending_admin':
                    # Check team access if admin has team restrictions
                    if admin_teams and admin_teams != ['ALL']:
                        file_team = file_data.get('user_team', '')
                        if file_team not in admin_teams:
                            continue
                    
                    pending_admin_files.append(file_data)
            
            return pending_admin_files
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting admin pending files: {e}")
            return []
    
    def get_all_files_for_admin(self, admin_user: str, admin_teams: List[str],
                               status_filter: Optional[str] = None) -> List[Dict]:
        """Get all files accessible to admin with optional status filtering."""
        try:
            approvals_file = os.path.join(r"\\KMTI-NAS\Shared\data", "approvals", "file_approvals.json")
            
            all_files = []
            
            # Get files from active queue
            if os.path.exists(approvals_file):
                with open(approvals_file, 'r', encoding='utf-8') as f:
                    queue = json.load(f)
                
                for file_id, file_data in queue.items():
                    # Check team access if admin has team restrictions
                    if admin_teams and admin_teams != ['ALL']:
                        file_team = file_data.get('user_team', '')
                        if file_team not in admin_teams:
                            continue
                    
                    # Apply status filter if provided
                    if status_filter:
                        file_status = file_data.get('status', '')
                        if file_status != status_filter:
                            continue
                    
                    all_files.append(file_data)
            
            # Also check archived approved/rejected files if needed
            if not status_filter or status_filter in ['approved', 'rejected_admin']:
                archived_files = self._get_archived_files(admin_teams, status_filter)
                all_files.extend(archived_files)
            
            return all_files
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting all files for admin: {e}")
            return []
    
    def _get_admin_approved_files(self, admin_user: str, admin_teams: List[str]) -> List[Dict]:
        """Get files approved by admin (may be archived)."""
        try:
            # First check active queue for recently approved files
            active_files = self.get_all_files_for_admin(admin_user, admin_teams, 'approved')
            
            # Add archived approved files
            archived_files = self._get_archived_files(admin_teams, 'approved')
            
            all_approved = active_files + archived_files
            
            # Remove duplicates based on file_id
            unique_approved = {f.get('file_id', f.get('original_filename', '')): f for f in all_approved}
            return list(unique_approved.values())
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting admin approved files: {e}")
            return []
    
    def _get_admin_rejected_files(self, admin_user: str, admin_teams: List[str]) -> List[Dict]:
        """Get files rejected by admin (may be archived)."""
        try:
            # First check active queue for recently rejected files
            active_files = self.get_all_files_for_admin(admin_user, admin_teams, 'rejected_admin')
            
            # Add archived rejected files
            archived_files = self._get_archived_files(admin_teams, 'rejected_admin')
            
            all_rejected = active_files + archived_files
            
            # Remove duplicates based on file_id
            unique_rejected = {f.get('file_id', f.get('original_filename', '')): f for f in all_rejected}
            return list(unique_rejected.values())
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting admin rejected files: {e}")
            return []
    
    def _get_archived_files(self, admin_teams: List[str], status_filter: Optional[str] = None) -> List[Dict]:
        """Get archived approved/rejected files from archive directory."""
        try:
            archived_files = []
            archive_dir = os.path.join(r"\\KMTI-NAS\Shared\data", "approvals", "archived")
            
            if not os.path.exists(archive_dir):
                return []
            
            # Check for status-specific archive files
            archive_files = {
                'approved': os.path.join(archive_dir, 'approved_files.json'),
                'rejected_admin': os.path.join(archive_dir, 'rejected_files.json'),
                'all': os.path.join(archive_dir, 'all_processed_files.json')
            }
            
            files_to_check = []
            if status_filter and status_filter in archive_files:
                files_to_check = [archive_files[status_filter]]
            elif not status_filter:
                files_to_check = [archive_files['all']] if os.path.exists(archive_files['all']) else list(archive_files.values())
            
            for archive_file in files_to_check:
                if os.path.exists(archive_file):
                    try:
                        with open(archive_file, 'r', encoding='utf-8') as f:
                            archive_data = json.load(f)
                        
                        # Handle both dict (file_id -> file_data) and list formats
                        if isinstance(archive_data, dict):
                            file_list = list(archive_data.values())
                        else:
                            file_list = archive_data
                        
                        # Filter by team access
                        for file_data in file_list:
                            if admin_teams and admin_teams != ['ALL']:
                                file_team = file_data.get('user_team', '')
                                if file_team not in admin_teams:
                                    continue
                            
                            archived_files.append(file_data)
                            
                    except Exception as file_error:
                        self.enhanced_logger.general_logger.warning(
                            f"Error reading archive file {archive_file}: {file_error}")
                        continue
            
            return archived_files
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting archived files: {e}")
            return []
    
    def get_admin_teams_safely(self, admin_user: str, permission_service) -> List[str]:

        try:
            teams = permission_service.get_user_teams(admin_user)
            from utils.logger import log_action
            log_action(admin_user, f"Retrieved team access: {teams}")
            return teams
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting admin teams: {e}")
            return ["DEFAULT"]


class StatisticsManager:
    """Enhanced statistics manager with real-time updates."""
    
    def __init__(self, file_manager, enhanced_auth):

        self.file_manager = file_manager
        self.enhanced_auth = enhanced_auth
    
    def get_cache_stats(self) -> Dict:

        return self.file_manager.get_cache_stats()
    
    def get_security_stats(self) -> Dict:

        return self.enhanced_auth.get_security_stats()
    
    def get_dynamic_file_stats(self, files: List[Dict]) -> Dict:
        """Get statistics for a specific set of files (for dynamic updates)."""
        try:
            stats = {
                'total_files': len(files),
                'by_status': {},
                'by_team': {},
                'by_user': {},
                'size_stats': {
                    'total_size': 0,
                    'avg_size': 0,
                    'max_size': 0,
                    'min_size': float('inf') if files else 0
                }
            }
            
            total_size = 0
            for file_data in files:
                # Status breakdown
                status = file_data.get('status', 'unknown')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Team breakdown
                team = file_data.get('user_team', 'unknown')
                stats['by_team'][team] = stats['by_team'].get(team, 0) + 1
                
                # User breakdown
                user = file_data.get('user_id', 'unknown')
                stats['by_user'][user] = stats['by_user'].get(user, 0) + 1
                
                # Size statistics
                file_size = file_data.get('file_size', 0)
                total_size += file_size
                stats['size_stats']['max_size'] = max(stats['size_stats']['max_size'], file_size)
                stats['size_stats']['min_size'] = min(stats['size_stats']['min_size'], file_size)
            
            stats['size_stats']['total_size'] = total_size
            stats['size_stats']['avg_size'] = total_size / len(files) if files else 0
            
            if not files:
                stats['size_stats']['min_size'] = 0
            
            return stats
            
        except Exception as e:
            return {
                'total_files': 0,
                'by_status': {},
                'by_team': {},
                'by_user': {},
                'size_stats': {'total_size': 0, 'avg_size': 0, 'max_size': 0, 'min_size': 0}
            }


class ServiceInitializer:
    """Handles service initialization and validation."""
    
    def __init__(self, enhanced_logger):

        self.enhanced_logger = enhanced_logger
    
    def initialize_services(self) -> Dict:

        try:
            from services.approval_service import FileApprovalService
            from services.permission_service import PermissionService
            from services.notification_service import NotificationService
            
            approval_service = FileApprovalService()
            permission_service = PermissionService()
            notification_service = NotificationService()
            permission_service.initialize_default_permissions()
            
            return {
                'approval_service': approval_service,
                'permission_service': permission_service,
                'notification_service': notification_service
            }
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Failed to initialize services: {e}")
            raise RuntimeError("Service initialization failed") from e


def cleanup_resources(admin_user: str, file_manager, enhanced_logger):

    try:
        if hasattr(file_manager, 'invalidate_cache'):
            file_manager.invalidate_cache()
        
        from utils.logger import log_action
        log_action(admin_user, "File approval panel session ended")
        
        enhanced_logger.general_logger.info("File approval panel cleanup completed")
    except Exception as e:
        enhanced_logger.general_logger.error(f"Error during cleanup: {e}")
