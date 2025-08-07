import flet as ft
from datetime import datetime
from typing import Dict, Callable
import os
import shutil
import tempfile
import subprocess
import platform
from services.approval_service import FileApprovalService, ApprovalStatus
from services.notification_service import NotificationService

class FileDetailsPopup:
    def __init__(self, page: ft.Page, admin_user: str):
        self.page = page
        self.admin_user = admin_user
        self.approval_service = FileApprovalService()
        self.notification_service = NotificationService()
        self.file_data = None
        self.on_file_action_callback = None
        
        # UI components
        self.comment_field = None
        self.reason_field = None
        self.dialog = None
    
    def set_callback(self, callback: Callable):
        """Set callback function to notify parent when file is approved/rejected"""
        self.on_file_action_callback = callback
    
    def show_file_details(self, file_data: Dict):
        """Show file details popup"""
        self.file_data = file_data
        self.create_popup_dialog()
    
    def create_popup_dialog(self):
        """Create the file details popup dialog"""
        if not self.file_data:
            return
        
        # Load comments for this file
        comments = self.approval_service.load_comments().get(self.file_data['file_id'], [])
        
        # Create comment field
        self.comment_field = ft.TextField(
            label="Add comment (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=450,
            text_size=14
        )
        
        # Create reason field for rejection
        self.reason_field = ft.TextField(
            label="Reason for rejection",
            multiline=True,
            min_lines=2,
            max_lines=3,
            width=450,
            text_size=14
        )
        
        # Format submission date
        submit_date = "Unknown"
        try:
            submit_date = datetime.fromisoformat(self.file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
        except:
            pass
        
        # File info section
        file_info = ft.Column([
            ft.Text("File Information", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"📄 {self.file_data.get('original_filename', 'Unknown')}", size=16, weight=ft.FontWeight.W_500),
            ft.Text(f"👤 User: {self.file_data.get('user_id', 'Unknown')}", size=14),
            ft.Text(f"🏢 Team: {self.file_data.get('user_team', 'Unknown')}", size=14),
            ft.Text(f"📏 Size: {self.format_file_size(self.file_data.get('file_size', 0))}", size=14),
            ft.Text(f"📅 Submitted: {submit_date}", size=14),
            ft.Container(height=10),
            ft.Text("Description:", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(self.file_data.get('description', 'No description provided'), size=13, color=ft.Colors.GREY_700),
                bgcolor=ft.Colors.GREY_50,
                padding=10,
                border_radius=4,
                margin=ft.margin.only(bottom=10)
            ),
            ft.Text("Tags:", size=14, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(', '.join(self.file_data.get('tags', [])) or 'No tags', size=13, color=ft.Colors.GREY_700),
                bgcolor=ft.Colors.GREY_50,
                padding=10,
                border_radius=4
            ),
            
            # Download and Open buttons
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    "Download File",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=self.download_file,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Open File",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=self.open_file,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ])
        
        # Comments section
        comment_controls = []
        if comments:
            for comment in comments:
                try:
                    timestamp = datetime.fromisoformat(comment['timestamp']).strftime('%Y-%m-%d %H:%M')
                except:
                    timestamp = "Unknown"
                
                comment_controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(comment['admin_id'], size=12, weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Text(timestamp, size=10, color=ft.Colors.GREY_500)
                            ]),
                            ft.Text(comment['comment'], size=12, color=ft.Colors.GREY_800)
                        ], spacing=2),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=8,
                        border_radius=4,
                        margin=ft.margin.only(bottom=5)
                    )
                )
        else:
            comment_controls.append(
                ft.Container(
                    content=ft.Text("No comments yet", size=12, color=ft.Colors.GREY_500),
                    padding=10,
                    alignment=ft.alignment.center
                )
            )
        
        comments_section = ft.Column([
            ft.Text("Comments", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(comment_controls, scroll=ft.ScrollMode.AUTO),
                height=120,
                bgcolor=ft.Colors.GREY_50,
                padding=10,
                border_radius=4
            )
        ])
        
        # Action buttons
        actions = ft.Column([
            ft.Text("Actions", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            
            # Comment section
            self.comment_field,
            ft.Container(height=5),
            ft.ElevatedButton(
                "Add Comment & Notify User",
                icon=ft.Icons.COMMENT,
                on_click=self.add_comment,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                width=450
            ),
            
            ft.Container(height=15),
            ft.Divider(),
            ft.Container(height=10),
            
            # Reason field for rejection
            self.reason_field,
            ft.Container(height=10),
            
            # Approval buttons
            ft.Row([
                ft.ElevatedButton(
                    "✓ Approve",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=self.approve_file,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                    width=200
                ),
                ft.Container(width=20),
                ft.ElevatedButton(
                    "✗ Reject",
                    icon=ft.Icons.CANCEL,
                    on_click=self.reject_file,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    width=200
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ])
        
        # Create dialog content
        dialog_content = ft.Container(
            content=ft.Column([
                file_info,
                ft.Divider(),
                comments_section,
                ft.Divider(),
                actions
            ], scroll=ft.ScrollMode.AUTO),
            width=500,
            height=600,
            padding=20
        )
        
        # Create custom dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE,
                    on_click=self.close_dialog,
                    tooltip="Close"
                )
            ]),
            content=dialog_content,
            actions=[],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )
        
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def download_file(self, e):
        """Download the selected file with custom success dialog"""
        try:
            file_id = self.file_data['file_id']
            user_id = self.file_data['user_id']
            original_filename = self.file_data['original_filename']
            
            # Find the file in storage
            possible_paths = [
                f"data/uploads/{user_id}/{original_filename}",
                f"data/uploads/{user_id}/{file_id}",
                f"data/uploads/{user_id}/{file_id}_{original_filename}",
                f"storage/files/{file_id}",
                f"storage/{user_id}/{file_id}",
                f"storage/{user_id}/{original_filename}",
                f"uploads/{user_id}/{original_filename}",
                f"files/{file_id}",
                f"{user_id}/{original_filename}"
            ]
            
            source_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    source_path = path
                    break
            
            if source_path:
                # Copy to downloads folder
                downloads_path = os.path.expanduser("~/Downloads")
                if not os.path.exists(downloads_path):
                    downloads_path = tempfile.gettempdir()
                
                dest_path = os.path.join(downloads_path, original_filename)
                shutil.copy2(source_path, dest_path)
                
                # Show custom success dialog
                self.show_download_success_dialog(original_filename)
            else:
                self.show_error_dialog("File not found in storage")
                
        except Exception as e:
            print(f"Error downloading file: {e}")
            self.show_error_dialog("Error downloading file")
    
    def open_file(self, e):
        """Open the selected file without dialog"""
        try:
            file_id = self.file_data['file_id']
            user_id = self.file_data['user_id']
            original_filename = self.file_data['original_filename']
            
            # Find the file in storage
            possible_paths = [
                f"data/uploads/{user_id}/{original_filename}",
                f"data/uploads/{user_id}/{file_id}",
                f"data/uploads/{user_id}/{file_id}_{original_filename}",
                f"storage/files/{file_id}",
                f"storage/{user_id}/{file_id}",
                f"storage/{user_id}/{original_filename}",
                f"uploads/{user_id}/{original_filename}",
                f"files/{file_id}",
                f"{user_id}/{original_filename}"
            ]
            
            source_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    source_path = path
                    break
            
            if source_path:
                # Open with system default application
                if platform.system() == "Windows":
                    os.startfile(source_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", source_path])
                else:  # Linux
                    subprocess.run(["xdg-open", source_path])
            else:
                self.show_error_dialog("File not found in storage")
                
        except Exception as e:
            print(f"Error opening file: {e}")
            self.show_error_dialog("Error opening file")
    
    def add_comment(self, e):
        """Add comment to selected file and notify user"""
        if not self.comment_field.value:
            self.show_error_dialog("Please enter a comment")
            return
        
        try:
            success = self.approval_service.add_comment(
                self.file_data['file_id'],
                self.admin_user,
                self.comment_field.value
            )
            
            if success:
                # Send comment notification to user
                self.notification_service.notify_comment_added(
                    self.file_data['user_id'],
                    self.file_data['original_filename'], 
                    self.admin_user,
                    self.comment_field.value
                )
                
                self.comment_field.value = ""
                # Refresh the dialog to show new comment
                self.show_file_details(self.file_data)
            else:
                self.show_error_dialog("Failed to add comment")
        except Exception as e:
            print(f"Error adding comment: {e}")
            self.show_error_dialog("Error adding comment")
    
    def approve_file(self, e):
        """Approve the selected file and notify user"""
        try:
            success = self.approval_service.approve_file(
                self.file_data['file_id'],
                self.admin_user
            )
            
            if success:
                # Send notification to user
                self.notification_service.notify_approval_status(
                    self.file_data['user_id'],
                    self.file_data['original_filename'],
                    ApprovalStatus.APPROVED.value,
                    self.admin_user
                )
                
                filename = self.file_data.get('original_filename', 'Unknown')
                
                # Close dialog and notify parent
                self.close_dialog(e)
                if self.on_file_action_callback:
                    self.on_file_action_callback("approved", filename)
            else:
                self.show_error_dialog("Failed to approve file")
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self.show_error_dialog("Error approving file")
    
    def reject_file(self, e):
        """Reject file and notify user"""
        if not self.reason_field.value:
            self.show_error_dialog("Please provide a reason for rejection")
            return
        
        try:
            success = self.approval_service.reject_file(
                self.file_data['file_id'],
                self.admin_user,
                self.reason_field.value,
                False
            )
            
            if success:
                # Send notification to user
                self.notification_service.notify_approval_status(
                    self.file_data['user_id'],
                    self.file_data['original_filename'],
                    ApprovalStatus.REJECTED.value,
                    self.admin_user,
                    self.reason_field.value
                )
                
                filename = self.file_data.get('original_filename', 'Unknown')
                
                # Close dialog and notify parent
                self.close_dialog(e)
                if self.on_file_action_callback:
                    self.on_file_action_callback("rejected", filename)
            else:
                self.show_error_dialog("Failed to reject file")
                
        except Exception as e:
            print(f"Error rejecting file: {e}")
            self.show_error_dialog("Error processing file")
    
    def show_download_success_dialog(self, filename: str):
        """Show custom download success dialog"""
        success_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=30),
                ft.Container(width=10),
                ft.Text("Download Success", size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"File '{filename}' has been downloaded successfully!", size=14),
                    ft.Text("Check your Downloads folder.", size=12, color=ft.Colors.GREY_600)
                ], tight=True),
                width=300
            ),
            actions=[
                ft.ElevatedButton(
                    "OK",
                    on_click=lambda e: self.close_success_dialog(success_dialog),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                )
            ]
        )
        
        self.page.dialog = success_dialog
        success_dialog.open = True
        self.page.update()
    
    def show_error_dialog(self, message: str):
        """Show error dialog"""
        error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=30),
                ft.Container(width=10),
                ft.Text("Error", size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Text(message, size=14),
            actions=[
                ft.ElevatedButton(
                    "OK",
                    on_click=lambda e: self.close_error_dialog(error_dialog),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
                )
            ]
        )
        
        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()
    
    def close_success_dialog(self, dialog):
        """Close success dialog"""
        dialog.open = False
        self.page.dialog = self.dialog  # Return to main dialog
        self.page.update()
    
    def close_error_dialog(self, dialog):
        """Close error dialog"""
        dialog.open = False
        self.page.dialog = self.dialog  # Return to main dialog
        self.page.update()
    
    def close_dialog(self, e=None):
        """Close the file details dialog"""
        if self.dialog:
            self.dialog.open = False
            self.page.dialog = None
            self.page.update()