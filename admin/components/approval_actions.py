
import flet as ft
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from utils.logger import log_approval_action, log_security_event, log_file_operation
from utils.dialog import show_confirm_dialog
from services.approval_service import ApprovalStatus


class ApprovalActionHandler:
    """Handles file approval actions with comprehensive validation and logging."""
    
    def __init__(self, page: ft.Page, admin_user: str, services_dict: Dict):

        self.page = page
        self.admin_user = admin_user
        self.approval_service = services_dict['approval_service']
        self.notification_service = services_dict['notification_service']
        self.enhanced_logger = services_dict['enhanced_logger']
    
    def handle_approve_file(self, file_data: Dict, refresh_callback) -> bool:

        try:
            if not file_data:
                return False
            
            success = self.approval_service.approve_file(
                file_data['file_id'],
                self.admin_user
            )
            
            if success:
                self.notification_service.notify_approval_status(
                    file_data['user_id'],
                    file_data['original_filename'],
                    ApprovalStatus.APPROVED.value,
                    self.admin_user
                )
                
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' approved!", ft.Colors.GREEN)
                
                log_approval_action(self.admin_user, file_data['user_id'], 
                                  file_data['file_id'], "APPROVE")
                
                refresh_callback()
                return True
                
            else:
                self._show_snackbar("Failed to approve file", ft.Colors.RED)
                return False
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error approving file: {e}")
            self._show_snackbar("Error approving file", ft.Colors.RED)
            return False
    
    def handle_reject_file(self, file_data: Dict, rejection_reason: str, 
                          refresh_callback, permanent: bool = False) -> bool:

        try:
            if not file_data:
                return False
            
            if not rejection_reason or not rejection_reason.strip():
                self._show_snackbar("Please provide a reason for rejection", ft.Colors.ORANGE)
                return False
            
            filename = file_data.get('original_filename', 'Unknown')
            
            show_confirm_dialog(
                self.page,
                "Confirm Rejection",
                f"Are you sure you want to reject '{filename}'?\n\nReason: {rejection_reason}",
                lambda: self._execute_file_rejection(file_data, rejection_reason, 
                                                   refresh_callback, permanent)
            )
            
            return True
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error handling file rejection: {e}")
            self._show_snackbar("Error processing file rejection", ft.Colors.RED)
            return False
    
    def _execute_file_rejection(self, file_data: Dict, rejection_reason: str, 
                               refresh_callback, permanent: bool = False):

        try:
            success = self.approval_service.reject_file(
                file_data['file_id'],
                self.admin_user,
                rejection_reason,
                permanent
            )
            
            if success:
                self.notification_service.notify_approval_status(
                    file_data['user_id'],
                    file_data['original_filename'],
                    ApprovalStatus.REJECTED.value,
                    self.admin_user,
                    rejection_reason
                )
                
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' rejected!", ft.Colors.RED)

                log_approval_action(self.admin_user, file_data['user_id'], 
                                  file_data['file_id'], "REJECT", rejection_reason)
                
                refresh_callback()
                
            else:
                self._show_snackbar("Failed to reject file", ft.Colors.RED)
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error executing file rejection: {e}")
            self._show_snackbar("Error rejecting file", ft.Colors.RED)
    
    def handle_add_comment(self, file_data: Dict, comment_text: str, 
                          refresh_callback) -> bool:

        try:
            if not file_data or not comment_text:
                self._show_snackbar("Please enter a comment", ft.Colors.ORANGE)
                return False
            
            comment_text = comment_text.strip()
            if not comment_text:
                self._show_snackbar("Comment cannot be empty", ft.Colors.ORANGE)
                return False
            
            success = self.approval_service.add_comment(
                file_data['file_id'],
                self.admin_user,
                comment_text
            )
            
            if success:
                self.notification_service.notify_comment_added(
                    file_data['user_id'],
                    file_data['original_filename'],
                    self.admin_user,
                    comment_text
                )
                
                self._show_snackbar("Comment added and user notified!", ft.Colors.GREEN)
                refresh_callback()
                
                log_approval_action(self.admin_user, file_data['user_id'], 
                                  file_data['file_id'], "COMMENT", comment_text)
                
                return True
            else:
                self._show_snackbar("Failed to add comment", ft.Colors.RED)
                return False
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error adding comment: {e}")
            self._show_snackbar("Error adding comment", ft.Colors.RED)
            return False
    
    def _show_snackbar(self, message: str, color: str):

        try:
            if color == ft.Colors.GREEN:
                icon = ft.Icons.CHECK_CIRCLE
                log_level = "info"
            elif color == ft.Colors.ORANGE:
                icon = ft.Icons.WARNING
                log_level = "warning"
            elif color == ft.Colors.RED:
                icon = ft.Icons.ERROR
                log_level = "error"
            else:
                icon = ft.Icons.INFO
                log_level = "info"
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=16),
                    ft.Text(message, color=ft.Colors.WHITE)
                ]),
                bgcolor=color,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            getattr(self.enhanced_logger.general_logger, log_level)(f"User notification: {message}")
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error showing snackbar: {e}")


def create_approval_buttons(file_data: Dict, action_handler: ApprovalActionHandler,
                           comment_field: ft.TextField, reason_field: ft.TextField,
                           refresh_callback, button_style_func) -> ft.Column:

    return ft.Column([
        ft.Text("Actions", size=16, weight=ft.FontWeight.BOLD),
        comment_field,
        ft.Container(height=5),
        ft.Row([
            ft.ElevatedButton(
                "Add Comment",
                icon=ft.Icons.COMMENT,
                on_click=lambda e: _handle_add_comment_click(
                    action_handler, file_data, comment_field, refresh_callback
                ),
                style=button_style_func("primary")
            )
        ], alignment=ft.MainAxisAlignment.START),
        
        ft.Container(height=10),
        ft.Divider(),
        ft.Container(height=10),
        reason_field,
        ft.Container(height=10),
        ft.Row([
            ft.ElevatedButton(
                "Approve",
                icon=ft.Icons.CHECK_CIRCLE,
                on_click=lambda e: action_handler.handle_approve_file(
                    file_data, refresh_callback
                ),
                style=button_style_func("success")
            ),
            ft.Container(width=10),
            ft.ElevatedButton(
                "Reject",
                icon=ft.Icons.CANCEL,
                on_click=lambda e: action_handler.handle_reject_file(
                    file_data, reason_field.value, refresh_callback
                ),
                style=button_style_func("danger")
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
    ], spacing=5)


def _handle_add_comment_click(action_handler: ApprovalActionHandler, file_data: Dict,
                             comment_field: ft.TextField, refresh_callback):

    if action_handler.handle_add_comment(file_data, comment_field.value, refresh_callback):
        comment_field.value = ""
        comment_field.update()
