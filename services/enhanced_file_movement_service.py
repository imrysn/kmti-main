"""
Network Access Manager for KMTI File Approval System
Handles network access validation and fallback mechanisms
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from utils.logger import log_action
from utils.path_config import DATA_PATHS

class NetworkAccessManager:
    """Manages network access and provides fallback mechanisms"""
    
    def __init__(self):
        self.project_base = r"\\KMTI-NAS\Database\PROJECTS"
        self.fallback_base = os.path.join(DATA_PATHS.NETWORK_BASE, "approved_files_staging")
        self.access_cache = {}
        
        # Ensure fallback directory exists
        try:
            os.makedirs(self.fallback_base, exist_ok=True)
            print(f"[ACCESS_MANAGER] Fallback directory ready: {self.fallback_base}")
        except Exception as e:
            print(f"[ACCESS_MANAGER] Warning: Could not create fallback directory: {e}")
    
    def test_network_access(self, path: str, username: str = None) -> Tuple[bool, str]:
        """
        Test if user has access to a network path
        Returns (has_access, message)
        """
        cache_key = f"{username}_{path}" if username else path
        
        # Check cache first (valid for 5 minutes)
        if cache_key in self.access_cache:
            cached_time, cached_result = self.access_cache[cache_key]
            if (datetime.now() - cached_time).seconds < 300:  # 5 minutes
                return cached_result
        
        try:
            # Try to create a test directory
            test_dir = os.path.join(path, f"access_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(test_dir, exist_ok=True)
            
            # If successful, clean up test directory
            try:
                os.rmdir(test_dir)
            except:
                pass
            
            result = (True, "Access granted")
            
        except PermissionError:
            result = (False, f"Access denied to {path}")
        except FileNotFoundError:
            result = (False, f"Path not found: {path}")
        except Exception as e:
            result = (False, f"Network error: {str(e)}")
        
        # Cache result
        self.access_cache[cache_key] = (datetime.now(), result)
        
        if username:
            log_action(username, f"Network access test for {path}: {result[1]}")
        
        return result
    
    def get_accessible_project_path(self, team_tag: str, year: str, username: str) -> Tuple[bool, str, str]:
        """
        Get accessible project path with fallback
        Returns (success, path, access_type)
        access_type: "direct", "fallback", or "failed"
        """
        # First try direct access
        direct_path = os.path.join(self.project_base, team_tag, year)
        has_access, message = self.test_network_access(direct_path, username)
        
        if has_access:
            return True, direct_path, "direct"
        
        print(f"[ACCESS_MANAGER] Direct access failed for {username}: {message}")
        
        # Try fallback path
        fallback_path = os.path.join(self.fallback_base, team_tag, year)
        try:
            os.makedirs(fallback_path, exist_ok=True)
            return True, fallback_path, "fallback"
        except Exception as e:
            print(f"[ACCESS_MANAGER] Fallback path failed: {e}")
            return False, f"No accessible path: {message}", "failed"
    
    def create_admin_access_request(self, file_data: Dict, admin_user: str, 
                                  target_path: str, error_message: str) -> str:
        """Create an access request for manual admin processing"""
        try:
            requests_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "admin_access_requests")
            os.makedirs(requests_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request_id = f"access_request_{timestamp}_{file_data.get('file_id', 'unknown')}"
            request_file = os.path.join(requests_dir, f"{request_id}.json")
            
            request_data = {
                "request_id": request_id,
                "created_date": datetime.now().isoformat(),
                "admin_user": admin_user,
                "file_data": file_data,
                "target_path": target_path,
                "error_message": error_message,
                "status": "pending_manual_move",
                "instructions": {
                    "step1": f"Copy file from: {file_data.get('file_path', 'source unknown')}",
                    "step2": f"To directory: {target_path}",
                    "step3": f"Update request status to 'completed' when done",
                    "step4": "Run process_admin_requests.py to finalize"
                }
            }
            
            with open(request_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(request_data, f, indent=2)
            
            log_action(admin_user, f"Created access request: {request_id}")
            
            return request_id
            
        except Exception as e:
            print(f"[ACCESS_MANAGER] Error creating access request: {e}")
            return f"Error creating request: {e}"


class EnhancedFileMovementService:
    """Enhanced file movement service with admin access management"""
    
    def __init__(self):
        self.access_manager = NetworkAccessManager()
        self.users_file = DATA_PATHS.users_file
    
    def get_user_team_tag(self, username: str) -> str:
        """Get user's team tag from users.json"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    import json
                    users = json.load(f)
                
                for email, user_data in users.items():
                    if user_data.get('username') == username:
                        teams = user_data.get('team_tags', [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error getting user team tag: {e}")
        return "DEFAULT"
    
    def move_approved_file_with_access_management(self, file_data: Dict, approved_by: str) -> Tuple[bool, str, Optional[str]]:
        """
        Move approved file with proper access management and fallback
        """
        try:
            # Get file information
            original_filename = file_data.get('original_filename')
            current_file_path = file_data.get('file_path')
            user_id = file_data.get('user_id')
            
            if not all([original_filename, current_file_path, user_id]):
                return False, "Missing file information", None
            
            if not os.path.exists(current_file_path):
                return False, f"Source file not found: {current_file_path}", None
            
            # Get user's team tag
            team_tag = self.get_user_team_tag(user_id)
            current_year = str(datetime.now().year)
            
            print(f"[FILE_MOVEMENT] Moving file for team: {team_tag}, year: {current_year}")
            
            # Get accessible project path
            has_access, project_dir, access_type = self.access_manager.get_accessible_project_path(
                team_tag, current_year, approved_by)
            
            if not has_access:
                # Create admin access request for manual processing
                request_id = self.access_manager.create_admin_access_request(
                    file_data, approved_by, f"{self.access_manager.project_base}\\{team_tag}\\{current_year}", 
                    project_dir)  # project_dir contains error message
                
                return False, f"Access denied - Manual processing required. Request ID: {request_id}", None
            
            # Generate unique filename if conflict exists
            new_filename = self._generate_unique_filename(project_dir, original_filename)
            new_file_path = os.path.join(project_dir, new_filename)
            
            # Move the file
            shutil.move(current_file_path, new_file_path)
            
            # Create metadata file
            self._create_file_metadata(new_file_path, file_data, approved_by, team_tag, current_year, access_type)
            
            # Log successful movement
            log_action(approved_by, f"Moved approved file {original_filename} to {access_type} path: {team_tag}/{current_year}")
            
            success_message = f"File moved to {access_type} directory: {team_tag}/{current_year}/{new_filename}"
            if access_type == "fallback":
                success_message += " (using fallback path - admin may need to manually move to final location)"
            
            print(f"[FILE_MOVEMENT] Success: {success_message}")
            
            return True, success_message, new_file_path
            
        except Exception as e:
            error_msg = f"Error moving file: {str(e)}"
            print(f"[FILE_MOVEMENT] Error: {error_msg}")
            
            # Create access request on any error
            try:
                request_id = self.access_manager.create_admin_access_request(
                    file_data, approved_by, "Unknown target", error_msg)
                return False, f"Move failed - Manual processing required. Request ID: {request_id}", None
            except:
                return False, error_msg, None
    
    def _generate_unique_filename(self, directory: str, filename: str) -> str:
        """Generate unique filename if conflict exists"""
        if not os.path.exists(os.path.join(directory, filename)):
            return filename
        
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_filename = f"{name}_{counter:03d}{ext}"
            if not os.path.exists(os.path.join(directory, new_filename)):
                return new_filename
            counter += 1
            
            if counter > 999:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{name}_{timestamp}{ext}"
    
    def _create_file_metadata(self, file_path: str, file_data: Dict, approved_by: str, 
                             team_tag: str, year: str, access_type: str):
        """Create metadata file for the moved file"""
        try:
            metadata = {
                "original_submission": {
                    "filename": file_data.get('original_filename'),
                    "user_id": file_data.get('user_id'),
                    "user_team": file_data.get('user_team'),
                    "submission_date": file_data.get('submission_date'),
                    "description": file_data.get('description', ''),
                    "tags": file_data.get('tags', []),
                    "file_size": file_data.get('file_size', 0)
                },
                "approval_info": {
                    "approved_by": approved_by,
                    "approved_date": datetime.now().isoformat(),
                    "team_leader_approved_by": file_data.get('tl_approved_by'),
                    "team_leader_approved_date": file_data.get('tl_approved_date'),
                    "status_history": file_data.get('status_history', [])
                },
                "project_info": {
                    "team_tag": team_tag,
                    "project_year": year,
                    "moved_date": datetime.now().isoformat(),
                    "project_directory": os.path.dirname(file_path),
                    "access_type": access_type,
                    "final_location_pending": access_type == "fallback"
                },
                "comments": {
                    "admin_comments": file_data.get('admin_comments', []),
                    "team_leader_comments": file_data.get('tl_comments', [])
                }
            }
            
            metadata_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.metadata.json"
            metadata_path = os.path.join(os.path.dirname(file_path), metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, indent=2)
            
            print(f"[METADATA] Created metadata file: {metadata_path}")
            
        except Exception as e:
            print(f"Error creating file metadata: {e}")
    
    def get_pending_access_requests(self) -> List[Dict]:
        """Get all pending access requests for admin review"""
        try:
            requests_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "admin_access_requests")
            
            if not os.path.exists(requests_dir):
                return []
            
            requests = []
            for filename in os.listdir(requests_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(requests_dir, filename), 'r', encoding='utf-8') as f:
                            import json
                            request_data = json.load(f)
                            
                        if request_data.get('status') == 'pending_manual_move':
                            requests.append(request_data)
                            
                    except Exception as e:
                        print(f"Error reading request file {filename}: {e}")
            
            # Sort by creation date (newest first)
            requests.sort(key=lambda x: x.get('created_date', ''), reverse=True)
            return requests
            
        except Exception as e:
            print(f"Error getting pending access requests: {e}")
            return []


# Global instance
_enhanced_file_movement_service = None

def get_enhanced_file_movement_service() -> EnhancedFileMovementService:
    """Get global enhanced file movement service instance"""
    global _enhanced_file_movement_service
    if _enhanced_file_movement_service is None:
        _enhanced_file_movement_service = EnhancedFileMovementService()
    return _enhanced_file_movement_service
