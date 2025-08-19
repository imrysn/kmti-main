import os
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional
from utils.file_manager import SecurityError
from utils.logger import log_file_operation, log_security_event


class FileOperationHandler:
    """Handles file operations with security validation and logging."""
    
    def __init__(self, admin_user: str, file_manager, enhanced_logger):

        self.admin_user = admin_user
        self.file_manager = file_manager
        self.enhanced_logger = enhanced_logger
    
    def download_file(self, file_data: Dict, show_snackbar_callback) -> bool:

        try:
            file_id = file_data.get('file_id')
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not all([file_id, user_id, original_filename]):
                raise ValueError("Missing required file information")
            
            resolved_path = self.file_manager.resolve_file_path(user_id, file_id, original_filename)
            
            if not resolved_path:
                show_snackbar_callback("File not found in storage", "red")
                log_file_operation(self.admin_user, "DOWNLOAD", original_filename, "FAILED", 
                                 {"reason": "file_not_found", "file_id": file_id})
                return False
            
            download_path = self.file_manager.get_safe_download_path(original_filename)
            
            shutil.copy2(resolved_path, download_path)
            
            show_snackbar_callback(f"Downloaded: {original_filename}", "green")
            log_file_operation(self.admin_user, "DOWNLOAD", original_filename, "SUCCESS", 
                             {"download_path": str(download_path), "file_id": file_id})
            
            return True
            
        except (SecurityError, ValueError) as e:
            log_security_event(self.admin_user, "FILE_DOWNLOAD_VIOLATION", 
                             {"error": str(e), "file_data": file_data}, "WARNING")
            show_snackbar_callback("Invalid file operation request", "red")
            return False
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error downloading file: {e}")
            show_snackbar_callback("Error downloading file", "red")
            return False
    
    def open_file(self, file_data: Dict, show_snackbar_callback) -> bool:

        try:
            file_id = file_data.get('file_id')
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not all([file_id, user_id, original_filename]):
                raise ValueError("Missing required file information")
            
            resolved_path = self.file_manager.resolve_file_path(user_id, file_id, original_filename)
            
            if not resolved_path:
                show_snackbar_callback("File not found in storage", "red")
                log_file_operation(self.admin_user, "OPEN", original_filename, "FAILED", 
                                 {"reason": "file_not_found", "file_id": file_id})
                return False
            
            self._open_file_with_system_default(resolved_path)
            
            show_snackbar_callback(f"Opening: {original_filename}", "blue")
            log_file_operation(self.admin_user, "OPEN", original_filename, "SUCCESS", 
                             {"file_id": file_id})
            
            return True
            
        except (SecurityError, ValueError) as e:
            log_security_event(self.admin_user, "FILE_OPEN_VIOLATION", 
                             {"error": str(e), "file_data": file_data}, "WARNING")
            show_snackbar_callback("Invalid file operation request", "red")
            return False
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error opening file: {e}")
            show_snackbar_callback("Error opening file", "red")
            return False
    
    def _open_file_with_system_default(self, file_path: Path):

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(str(file_path))
            elif system == "Darwin":  
                subprocess.run(["open", str(file_path)], check=True)
            else: 
                subprocess.run(["xdg-open", str(file_path)], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to open file with system application: {e}")
        except Exception as e:
            raise RuntimeError(f"Error opening file: {e}")


def create_file_action_buttons(file_data: Dict, file_handler: FileOperationHandler,
                              show_snackbar_callback, button_style_func) -> list:
    """Create file action buttons - Open button restored, Download removed for security"""
    import flet as ft
    
    # Restore Open button functionality like TLPanel
    return [
        ft.Row([
            ft.ElevatedButton(
                "Open",
                icon=ft.Icons.OPEN_IN_NEW_OUTLINED,
                on_click=lambda e: file_handler.open_file(file_data, show_snackbar_callback),
                style=button_style_func("secondary")
            )
        ], alignment=ft.MainAxisAlignment.START),
        ft.Container(height=10)
    ]


def validate_file_data(file_data: Dict) -> tuple[bool, str]:

    if not file_data:
        return False, "No file data provided"
    
    required_fields = ['file_id', 'user_id', 'original_filename']
    missing_fields = [field for field in required_fields if not file_data.get(field)]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""


def get_file_info_display(file_data: Dict) -> Dict[str, str]:

    from admin.components.table_helpers import TableHelper
    
    return {
        'filename': file_data.get('original_filename', 'Unknown'),
        'user': file_data.get('user_id', 'Unknown'),
        'team': file_data.get('user_team', 'Unknown'),
        'size': TableHelper.format_file_size(file_data.get('file_size', 0)),
        'description': file_data.get('description', 'No description provided'),
        'tags': ', '.join(file_data.get('tags', [])) or 'No tags'
    }
