
from typing import Dict, List
from utils.logger import PerformanceTimer, log_performance_metric


class FileDataManager:
    """Manages file data operations including counts and retrieval."""
    
    def __init__(self, approval_service, permission_service, enhanced_logger):

        self.approval_service = approval_service
        self.permission_service = permission_service
        self.enhanced_logger = enhanced_logger
    
    def get_file_counts_safely(self, admin_user: str, admin_teams: List[str],
                              is_super_admin: bool) -> Dict[str, int]:
        try:
            with PerformanceTimer("FileApprovalPanel", "get_file_counts"):
                reviewable_teams = self.permission_service.get_reviewable_teams(
                    admin_user, admin_teams)
                
                pending_files = set()
                approved_files = set()
                rejected_files = set()
                
                for team in reviewable_teams:
                    try:
                        team_pending = self.approval_service.get_pending_files_by_team(
                            team, is_super_admin)
                        for file_data in team_pending:
                            pending_files.add(file_data['file_id'])
                        
                        team_approved = self._get_approved_files_by_team_safe(team, is_super_admin)
                        for file_data in team_approved:
                            approved_files.add(file_data['file_id'])
                        
                        team_rejected = self._get_rejected_files_by_team_safe(team, is_super_admin)
                        for file_data in team_rejected:
                            rejected_files.add(file_data['file_id'])
                            
                    except Exception as team_error:
                        self.enhanced_logger.general_logger.warning(
                            f"Error getting files for team {team}: {team_error}")
                        continue
                
                counts = {
                    'pending': len(pending_files),
                    'approved': len(approved_files), 
                    'rejected': len(rejected_files)
                }
                
                log_performance_metric("FileApprovalPanel", "file_counts", 50.0, counts)
                
                return counts
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting file counts: {e}")
            return {'pending': 0, 'approved': 0, 'rejected': 0}
    
    def _get_approved_files_by_team_safe(self, team: str, is_super_admin: bool) -> List[Dict]:

        try:
            return self.approval_service.get_approved_files_by_team(team, is_super_admin)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team, is_super_admin)
                return [f for f in all_files if f.get('status') == 'APPROVED']
            except Exception:
                return []
    
    def _get_rejected_files_by_team_safe(self, team: str, is_super_admin: bool) -> List[Dict]:

        try:
            return self.approval_service.get_rejected_files_by_team(team, is_super_admin)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team, is_super_admin)
                return [f for f in all_files if f.get('status') == 'REJECTED']
            except Exception:
                return []
    
    def get_filtered_pending_files(self, admin_user: str, admin_teams: List[str],
                                  is_super_admin: bool) -> List[Dict]:

        try:
            reviewable_teams = self.permission_service.get_reviewable_teams(
                admin_user, admin_teams)
            all_pending = []
            
            for team in reviewable_teams:
                try:
                    team_files = self.approval_service.get_pending_files_by_team(
                        team, is_super_admin)
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
    """Manages statistics and monitoring data."""
    
    def __init__(self, file_manager, enhanced_auth):

        self.file_manager = file_manager
        self.enhanced_auth = enhanced_auth
    
    def get_cache_stats(self) -> Dict:

        return self.file_manager.get_cache_stats()
    
    def get_security_stats(self) -> Dict:

        return self.enhanced_auth.get_security_stats()


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
