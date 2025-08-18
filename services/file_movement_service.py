import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
from utils.path_config import DATA_PATHS
from utils.logger import log_action
from typing import List

# Project directory base path
PROJECT_BASE_DIR = r"\\KMTI-NAS\Database\PROJECTS"

class FileMovementService:
    """Service for handling file movements to project directories"""
    
    def __init__(self):
        self.project_base = PROJECT_BASE_DIR
        self.users_file = DATA_PATHS.users_file
        
        # Ensure project base directory exists
        try:
            os.makedirs(self.project_base, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create project directory {self.project_base}: {e}")
    
    def get_user_team_tag(self, username: str) -> str:
        """Get user's team tag from users.json"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                for email, user_data in users.items():
                    if user_data.get('username') == username:
                        teams = user_data.get('team_tags', [])
                        return teams[0] if teams else "DEFAULT"
        except Exception as e:
            print(f"Error getting user team tag: {e}")
        return "DEFAULT"
    
    def get_project_directory_path(self, team_tag: str, year: Optional[str] = None) -> str:
        """
        Get the project directory path for a team and year
        Format: \\KMTI-NAS\Database\PROJECTS\{team_tag}\{YYYY}
        """
        if year is None:
            year = str(datetime.now().year)
        
        return os.path.join(self.project_base, team_tag, year)
    
    def ensure_project_directory(self, team_tag: str, year: Optional[str] = None) -> Tuple[bool, str]:
        """
        Ensure project directory exists for team and year
        Returns (success, directory_path)
        """
        try:
            project_dir = self.get_project_directory_path(team_tag, year)
            os.makedirs(project_dir, exist_ok=True)
            return True, project_dir
        except Exception as e:
            return False, f"Failed to create directory: {e}"
    
    def move_approved_file(self, file_data: Dict, approved_by: str) -> Tuple[bool, str, Optional[str]]:
        """
        Move approved file to project directory
        
        Args:
            file_data: File data from approval queue
            approved_by: Username of approver (admin)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, new_file_path)
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
            
            # Ensure project directory exists
            success, project_dir = self.ensure_project_directory(team_tag, current_year)
            if not success:
                return False, project_dir, None  # project_dir contains error message
            
            # Generate unique filename if conflict exists
            new_filename = self._generate_unique_filename(project_dir, original_filename)
            new_file_path = os.path.join(project_dir, new_filename)
            
            # Move the file
            shutil.move(current_file_path, new_file_path)
            
            # Create metadata file for the moved file
            self._create_file_metadata(new_file_path, file_data, approved_by, team_tag, current_year)
            
            # Log the file movement
            log_action(approved_by, f"Moved approved file {original_filename} to project directory: {team_tag}/{current_year}")
            
            print(f"[FILE_MOVEMENT] Successfully moved {original_filename} to {new_file_path}")
            
            return True, f"File moved to project directory: {team_tag}/{current_year}/{new_filename}", new_file_path
            
        except Exception as e:
            print(f"Error moving approved file: {e}")
            return False, f"Error moving file: {str(e)}", None
    
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
            
            # Safety limit
            if counter > 999:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{name}_{timestamp}{ext}"
    
    def _create_file_metadata(self, file_path: str, file_data: Dict, approved_by: str, team_tag: str, year: str):
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
                    "project_directory": os.path.dirname(file_path)
                },
                "comments": {
                    "admin_comments": file_data.get('admin_comments', []),
                    "team_leader_comments": file_data.get('tl_comments', [])
                }
            }
            
            metadata_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.metadata.json"
            metadata_path = os.path.join(os.path.dirname(file_path), metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"[METADATA] Created metadata file: {metadata_path}")
            
        except Exception as e:
            print(f"Error creating file metadata: {e}")
    
    def get_project_files(self, team_tag: str, year: Optional[str] = None) -> List[Dict]:
        """Get all files in a project directory"""
        try:
            project_dir = self.get_project_directory_path(team_tag, year)
            
            if not os.path.exists(project_dir):
                return []
            
            files = []
            for filename in os.listdir(project_dir):
                if filename.endswith('.metadata.json'):
                    continue  # Skip metadata files
                
                file_path = os.path.join(project_dir, filename)
                if os.path.isfile(file_path):
                    # Try to load metadata
                    metadata_path = os.path.join(project_dir, f"{os.path.splitext(filename)[0]}.metadata.json")
                    metadata = {}
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    file_stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'size': file_stat.st_size,
                        'modified_date': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'metadata': metadata
                    })
            
            return files
            
        except Exception as e:
            print(f"Error getting project files: {e}")
            return []
    
    def get_available_years(self, team_tag: str) -> List[str]:
        """Get available years for a team"""
        try:
            team_dir = os.path.join(self.project_base, team_tag)
            if not os.path.exists(team_dir):
                return []
            
            years = []
            for item in os.listdir(team_dir):
                item_path = os.path.join(team_dir, item)
                if os.path.isdir(item_path) and item.isdigit() and len(item) == 4:
                    years.append(item)
            
            return sorted(years, reverse=True)  # Most recent first
            
        except Exception as e:
            print(f"Error getting available years: {e}")
            return []
    
    def get_team_directories(self) -> List[str]:
        """Get all team directories"""
        try:
            if not os.path.exists(self.project_base):
                return []
            
            teams = []
            for item in os.listdir(self.project_base):
                item_path = os.path.join(self.project_base, item)
                if os.path.isdir(item_path):
                    teams.append(item)
            
            return sorted(teams)
            
        except Exception as e:
            print(f"Error getting team directories: {e}")
            return []


# Global instance
_file_movement_service = None

def get_file_movement_service() -> FileMovementService:
    """Get global file movement service instance"""
    global _file_movement_service
    if _file_movement_service is None:
        _file_movement_service = FileMovementService()
    return _file_movement_service
