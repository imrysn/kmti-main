"""
Enhanced File Movement Service for KMTI File Approval System
Handles network access validation, approved/rejected file movement, and fallback mechanisms
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from utils.logger import log_action
from utils.metadata_manager import get_metadata_manager
from utils.path_config import DATA_PATHS

class NetworkAccessManager:
    """Manages network access and provides fallback mechanisms"""
    
    def __init__(self):
        self.project_base = r"\\KMTI-NAS\Database\PROJECTS"
        self.fallback_base = os.path.join(DATA_PATHS.NETWORK_BASE, "PROJECTS")
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


class EnhancedFileMovementService:
    """Enhanced file movement service with admin access management for both approved and rejected files"""
    
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
        Move approved file from user uploads to project directory with proper access management and fallback
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
            
            print(f"[FILE_MOVEMENT] Moving approved file for team: {team_tag}, year: {current_year}")
            
            # Get accessible project path
            has_access, project_dir, access_type = self.access_manager.get_accessible_project_path(
                team_tag, current_year, approved_by)
            
            if not has_access:
                # Create fallback in network data directory if primary fails
                fallback_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "approved_files_fallback", team_tag, current_year)
                try:
                    os.makedirs(fallback_dir, exist_ok=True)
                    project_dir = fallback_dir
                    access_type = "fallback"
                except Exception as fallback_error:
                    return False, f"All access methods failed: {project_dir} | Fallback: {fallback_error}", None
            
            # Generate unique filename if conflict exists
            new_filename = self._generate_unique_filename(project_dir, original_filename)
            new_file_path = os.path.join(project_dir, new_filename)
            
            # Move the file (this deletes from user uploads)
            shutil.move(current_file_path, new_file_path)
            
            # Create metadata file
            self._create_approved_file_metadata(new_file_path, file_data, approved_by, team_tag, current_year, access_type)
            
            # Log successful movement
            log_action(approved_by, f"Moved approved file {original_filename} to {access_type} path: {team_tag}/{current_year}")
            
            success_message = f"File moved to {access_type} directory: {team_tag}/{current_year}/{new_filename}"
            if access_type == "fallback":
                success_message += " (using fallback path - admin may need to manually move to final location)"
            
            print(f"[FILE_MOVEMENT] Success: {success_message}")
            
            return True, success_message, new_file_path
            
        except Exception as e:
            error_msg = f"Error moving approved file: {str(e)}"
            print(f"[FILE_MOVEMENT] Error: {error_msg}")
            return False, error_msg, None
    
    def move_rejected_file_to_archive(self, file_data: Dict, rejected_by: str, rejection_reason: str) -> Tuple[bool, str, Optional[str]]:
        """
        Move rejected file from user uploads to archive directory and clean up from user uploads
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
            
            # Get user's team tag and create rejected files directory
            team_tag = self.get_user_team_tag(user_id)
            current_year = str(datetime.now().year)
            
            # Create rejected files archive directory
            rejected_dir = os.path.join(DATA_PATHS.SHARED_BASE, "rejected_files_archive", team_tag, current_year)
            os.makedirs(rejected_dir, exist_ok=True)
            
            print(f"[FILE_MOVEMENT] Moving rejected file for team: {team_tag}, year: {current_year}")
            
            # Generate unique filename if conflict exists
            new_filename = self._generate_unique_filename(rejected_dir, original_filename)
            new_file_path = os.path.join(rejected_dir, new_filename)
            
            # Move the file to rejected archive (this deletes from user uploads)
            shutil.move(current_file_path, new_file_path)
            
            # Create metadata file for rejected file
            self._create_rejected_file_metadata(new_file_path, file_data, rejected_by, rejection_reason, team_tag, current_year)
            
            # Log successful movement
            log_action(rejected_by, f"Moved rejected file {original_filename} to archive: {team_tag}/{current_year}")
            
            success_message = f"Rejected file archived: {team_tag}/{current_year}/{new_filename}"
            print(f"[FILE_MOVEMENT] Success: {success_message}")
            
            return True, success_message, new_file_path
            
        except Exception as e:
            error_msg = f"Error archiving rejected file: {str(e)}"
            print(f"[FILE_MOVEMENT] Error: {error_msg}")
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
    
    def _create_approved_file_metadata(self, file_path: str, file_data: Dict, approved_by: str, 
                                     team_tag: str, year: str, access_type: str):
        """Create metadata file for approved file using metadata manager"""
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
                    "final_file_location": file_path,
                    "access_type": access_type,
                    "final_location_pending": access_type == "fallback"
                },
                "comments": {
                    "admin_comments": file_data.get('admin_comments', []),
                    "team_leader_comments": file_data.get('tl_comments', [])
                }
            }
            
            # Use metadata manager to save the metadata
            metadata_manager = get_metadata_manager()
            filename = os.path.basename(file_path)
            success, message = metadata_manager.save_metadata(filename, metadata, team_tag, year)
            
            if success:
                print(f"[METADATA] {message}")
            else:
                print(f"[METADATA] Error: {message}")
                
        except Exception as e:
            print(f"Error creating approved file metadata: {e}")
    
    def _create_rejected_file_metadata(self, file_path: str, file_data: Dict, rejected_by: str, 
                                     rejection_reason: str, team_tag: str, year: str):
        """Create metadata file for rejected file"""
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
                "rejection_info": {
                    "rejected_by": rejected_by,
                    "rejected_date": datetime.now().isoformat(),
                    "rejection_reason": rejection_reason,
                    "team_leader_approved_by": file_data.get('tl_approved_by'),
                    "team_leader_approved_date": file_data.get('tl_approved_date'),
                    "status_history": file_data.get('status_history', [])
                },
                "archive_info": {
                    "team_tag": team_tag,
                    "archive_year": year,
                    "archived_date": datetime.now().isoformat(),
                    "archive_directory": os.path.dirname(file_path),
                    "final_file_location": file_path
                },
                "comments": {
                    "admin_comments": file_data.get('admin_comments', []),
                    "team_leader_comments": file_data.get('tl_comments', [])
                }
            }
            
            # Use metadata manager to save the metadata (create a rejected-specific method if needed)
            metadata_manager = get_metadata_manager()
            filename = os.path.basename(file_path)
            
            # Save rejected file metadata in a separate rejected folder structure
            success, message = metadata_manager.save_rejected_file_metadata(filename, metadata, team_tag, year)
            
            if success:
                print(f"[METADATA] {message}")
            else:
                print(f"[METADATA] Error: {message}")
                
        except Exception as e:
            print(f"Error creating rejected file metadata: {e}")


# Global instance
_enhanced_file_movement_service = None

def get_enhanced_file_movement_service() -> EnhancedFileMovementService:
    """Get global enhanced file movement service instance"""
    global _enhanced_file_movement_service
    if _enhanced_file_movement_service is None:
        _enhanced_file_movement_service = EnhancedFileMovementService()
    return _enhanced_file_movement_service
