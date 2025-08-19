import flet as ft
from datetime import datetime
from typing import List, Dict, Callable
from admin.components.file_utils import get_file_info_display, create_file_action_buttons
from admin.components.approval_actions import create_approval_buttons


class PreviewPanelManager:
    
    def __init__(self, config, approval_service):

        self.config = config
        self.approval_service = approval_service
    
    def create_empty_preview_panel(self) -> ft.Column:
        padding = self.config.get_ui_constant('preview_panel_padding', 15)
        
        preview_column = ft.Column([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
        alignment=ft.MainAxisAlignment.CENTER, 
        scroll=ft.ScrollMode.AUTO,
        expand=True
        )
        
        return preview_column
    
    def create_file_preview_content(self, file_data: Dict, action_handler,
                                   file_handler, show_snackbar_callback,
                                   button_style_func, refresh_callback) -> List:

        file_info = self._create_file_info_section(file_data, file_handler,
                                                  show_snackbar_callback, button_style_func)
        
        comments_section = self._create_comments_section(file_data)
        
        actions_section = self._create_actions_section(file_data, action_handler,
                                                     button_style_func, refresh_callback)
        
        return file_info + [ft.Divider()] + comments_section + [ft.Divider()] + actions_section
    
    def _create_file_info_section(self, file_data: Dict, file_handler,
                                 show_snackbar_callback, button_style_func) -> List:

        submit_date = "Unknown"
        try:
            submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
        except (ValueError, KeyError, TypeError):
            pass
        
        file_info_display = get_file_info_display(file_data)
        status = file_data.get('status', 'unknown')
        
        return [
            ft.Text("File Details", size=20, weight=ft.FontWeight.BOLD),  # Increased size
            ft.Divider(),
            ft.Column([
                ft.Text(f"File: {file_info_display['filename']}", 
                       size=16, weight=ft.FontWeight.W_500),  # Increased size
                ft.Text(f"User: {file_info_display['user']}", size=16),  # Increased size
                ft.Text(f"Team: {file_info_display['team']}", size=16),  # Increased size
                ft.Text(f"Size: {file_info_display['size']}", size=16),  # Increased size
                ft.Text(f"Submitted: {submit_date}", size=16),  # Increased size
                ft.Row([
                    ft.Text("Status: ", size=16),  # Increased size
                    self._create_status_badge(status, file_data)
                ])
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            ft.Text("Description:", size=16, weight=ft.FontWeight.BOLD),  # Increased size
            ft.Text(file_info_display['description'], 
                   size=16, color=ft.Colors.GREY_600),  # Increased size
            
            # File operations section - Open button restored
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    "Open",
                    icon=ft.Icons.OPEN_IN_NEW_OUTLINED,
                    on_click=lambda e: self._handle_open_file(file_data, file_handler, show_snackbar_callback),
                    style=button_style_func("secondary")
                )
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider()
        ]
    
    def _handle_open_file(self, file_data: Dict, file_handler, show_snackbar_callback):
        """Handle file opening like in TLPanel."""
        try:
            file_handler.open_file(file_data, show_snackbar_callback)
        except Exception as e:
            print(f"Error opening file: {e}")
            show_snackbar_callback("Error opening file", "red")
    
    def _create_status_badge(self, status: str, file_data: Dict) -> ft.Container:
        """Create color-coded status badge like TLPanel."""
        status_configs = {
            'pending_team_leader': {'text': 'PENDING TL', 'color': ft.Colors.ORANGE},
            'pending': {'text': 'PENDING TL', 'color': ft.Colors.ORANGE},
            'pending_admin': {'text': 'PENDING ADMIN', 'color': ft.Colors.ORANGE},
            'approved': {'text': 'APPROVED', 'color': ft.Colors.GREEN},
            'rejected_team_leader': {'text': 'REJECTED TL', 'color': ft.Colors.RED},
            'rejected_admin': {'text': 'REJECTED ADMIN', 'color': ft.Colors.RED_900}
        }
        
        config = status_configs.get(status, {'text': status.upper(), 'color': ft.Colors.GREY})
        
        # Add reviewer info for approved/rejected files
        tooltip_text = f"Status: {status}"
        if status == 'pending_admin' and file_data.get('tl_approved_by'):
            tooltip_text += f"\nApproved by: {file_data['tl_approved_by']}"
        elif status == 'rejected_team_leader' and file_data.get('tl_rejected_by'):
            tooltip_text += f"\nRejected by: {file_data['tl_rejected_by']}"
        
        return ft.Container(
            content=ft.Text(config['text'], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
            bgcolor=config['color'],
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            tooltip=tooltip_text
        )
    
    def _create_comments_section(self, file_data: Dict) -> List:

        comments = self.approval_service.load_comments().get(file_data['file_id'], [])
        
        comment_controls = []
        if comments:
            for comment in comments:
                comment_controls.append(
                    ft.Text(f"{comment.get('admin_id', 'Unknown')}: {comment.get('comment', '')}", size=16)  # Increased size
                )
        else:
            comment_controls.append(ft.Text("No comments yet", size=16, color=ft.Colors.GREY_500))  # Increased size
        
        return [
            ft.Text("Comments", size=18, weight=ft.FontWeight.BOLD),  # Increased size
            ft.Container(
                content=ft.Column(comment_controls, alignment=ft.MainAxisAlignment.START),
                height=100,
                bgcolor=ft.Colors.GREY_50,
                padding=10,
                border_radius=4,
                alignment=ft.alignment.center_left
            )
        ]
    
    def _create_actions_section(self, file_data: Dict, action_handler,
                               button_style_func, refresh_callback) -> List:

        status = file_data.get('status', 'unknown')
        
        # Comment field (always available)
        comment_field = ft.TextField(
            label="Add comment (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=16,  # Increased size
            expand=True
        )
        
        # Comments section
        actions = [
            ft.Text("Admin Actions", size=18, weight=ft.FontWeight.BOLD),  # Increased size
            comment_field,
            ft.Container(height=5),
            ft.Row([
                ft.ElevatedButton(
                    "Add Comment",
                    icon=ft.Icons.COMMENT,
                    on_click=lambda e: self._handle_add_comment(action_handler, file_data, comment_field, refresh_callback),
                    style=button_style_func("primary")
                )
            ], alignment=ft.MainAxisAlignment.START)
        ]
        
        # Conditional approval/rejection actions based on status
        if status in ['pending_admin', 'pending_team_leader', 'pending']:
            reason_field = ft.TextField(
                label="Reason for rejection",
                multiline=True,
                min_lines=2,
                max_lines=3,
                text_size=16,  # Increased size
                expand=True
            )
            
            actions.extend([
                ft.Container(height=10),
                ft.Divider(),
                ft.Text("Approval Decision", size=18, weight=ft.FontWeight.BOLD),  # Increased size
                ft.Container(height=10),
                reason_field,
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "✓ Approve",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=lambda e: self._handle_approve_with_confirmation(action_handler, file_data, refresh_callback),
                        style=button_style_func("success")
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "✗ Reject",
                        icon=ft.Icons.CANCEL,
                        on_click=lambda e: self._handle_reject_with_validation(action_handler, file_data, reason_field, refresh_callback),
                        style=button_style_func("danger")
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
            ])
        elif status == 'approved':
            actions.extend([
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text("✓ File approved - No further action needed", 
                                   color=ft.Colors.GREEN, size=16, weight=ft.FontWeight.W_500),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=10,
                    border_radius=5,
                    border=ft.border.all(1, ft.Colors.GREEN_200)
                )
            ])
        elif status in ['rejected_admin', 'rejected_team_leader']:
            rejection_reason = file_data.get('admin_rejection_reason') or file_data.get('tl_rejection_reason', 'No reason provided')
            actions.extend([
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("✗ File rejected", 
                               color=ft.Colors.RED, size=16, weight=ft.FontWeight.W_500),
                        ft.Text(f"Reason: {rejection_reason}", 
                               color=ft.Colors.RED_700, size=16)
                    ]),
                    bgcolor=ft.Colors.RED_50,
                    padding=10,
                    border_radius=5,
                    border=ft.border.all(1, ft.Colors.RED_200)
                )
            ])
        
        return actions
    
    def _handle_add_comment(self, action_handler, file_data: Dict, comment_field: ft.TextField, refresh_callback):
        """Handle adding comment to file."""
        if action_handler.handle_add_comment(file_data, comment_field.value, refresh_callback):
            comment_field.value = ""
            comment_field.update()
    
    def _handle_approve_with_confirmation(self, action_handler, file_data: Dict, refresh_callback):
        """Handle file approval with confirmation dialog."""
        try:
            from user.components.dialogs import DialogManager
            dialog_manager = DialogManager(action_handler.page, action_handler.admin_user)
            filename = file_data.get('original_filename', 'Unknown')
            
            def on_confirm():
                action_handler.handle_approve_file(file_data, refresh_callback)
            
            dialog_manager.show_confirmation_dialog(
                title="Confirm Approval",
                message=f"Are you sure you want to approve this file?",
                on_confirm=on_confirm,
                confirm_text="Approve",
                cancel_text="Cancel",
                confirm_color=ft.Colors.GREEN
            )
            
        except Exception as e:
            print(f"Error showing approval confirmation: {e}")
            action_handler.handle_approve_file(file_data, refresh_callback)
    
    def _handle_reject_with_validation(self, action_handler, file_data: Dict, reason_field: ft.TextField, refresh_callback):
        """Handle file rejection with validation for rejection reason."""
        try:
            reason = reason_field.value
            if not reason or not reason.strip():
                # Show notification that rejection reason is required
                action_handler._show_snackbar("Please enter a rejection reason in the text field before proceeding", ft.Colors.ORANGE)
                return
            
            # Proceed with rejection
            action_handler.handle_reject_file(file_data, reason, refresh_callback)
            
        except Exception as e:
            print(f"Error validating rejection: {e}")
            action_handler._show_snackbar("Error processing rejection", ft.Colors.RED)
    
    def clear_preview_panel(self, preview_panel_widget: ft.Column):

        preview_panel_widget.controls.clear()
        preview_panel_widget.controls.extend([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ])

        preview_panel_widget.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        preview_panel_widget.alignment = ft.MainAxisAlignment.CENTER
        preview_panel_widget.scroll = ft.ScrollMode.AUTO
    
    def update_preview_panel(self, preview_panel_widget: ft.Column, file_data: Dict,
                           action_handler, file_handler, show_snackbar_callback,
                           button_style_func, refresh_callback):

        try:
            preview_content = self.create_file_preview_content(
                file_data, action_handler, file_handler, show_snackbar_callback,
                button_style_func, refresh_callback
            )
            
            preview_panel_widget.controls.clear()
            preview_panel_widget.controls.extend(preview_content)
            preview_panel_widget.horizontal_alignment = ft.CrossAxisAlignment.START
            preview_panel_widget.alignment = ft.MainAxisAlignment.START
            
        except Exception as e:
            # Log error and show error state
            import logging
            logging.error(f"Error updating preview panel: {e}")
            self._show_preview_error(preview_panel_widget, str(e))
    
    def _show_preview_error(self, preview_panel_widget: ft.Column, error_msg: str):

        preview_panel_widget.controls.clear()
        preview_panel_widget.controls.extend([
            ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED),
            ft.Container(height=10),
            ft.Text("Error Loading Preview", size=16, weight=ft.FontWeight.BOLD, 
                   color=ft.Colors.RED),
            ft.Container(height=10),
            ft.Text(f"Details: {error_msg}", size=12, color=ft.Colors.GREY_600,
                   text_align=ft.TextAlign.CENTER)
        ])
        
        preview_panel_widget.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        preview_panel_widget.alignment = ft.MainAxisAlignment.CENTER


def create_preview_section_container(preview_panel_widget: ft.Column,
                                   config) -> ft.Container:

    padding = config.get_ui_constant('preview_panel_padding', 15)
    
    return ft.Container(
        content=ft.Container(
            content=preview_panel_widget,
            expand=True,
            padding=padding,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200)
        ),
        expand=True,
        padding=0
    )
