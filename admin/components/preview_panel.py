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
        
        return [
            ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column([
                ft.Text(f"File name: {file_info_display['filename']}", 
                       size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"User: {file_info_display['user']}", size=14),
                ft.Text(f"Team: {file_info_display['team']}", size=14),
                ft.Text(f"Size: {file_info_display['size']}", size=14),
                ft.Text(f"Submitted: {submit_date}", size=14),
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            ft.Text("Description:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(file_info_display['description'], 
                   size=12, color=ft.Colors.GREY_600),
            ft.Container(height=10),
            ft.Text("Tags:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(file_info_display['tags'], 
                   size=12, color=ft.Colors.GREY_600),
            ft.Container(height=15),
        ] + create_file_action_buttons(file_data, file_handler,
                                     show_snackbar_callback, button_style_func)
    
    def _create_comments_section(self, file_data: Dict) -> List:

        comments = self.approval_service.load_comments().get(file_data['file_id'], [])
        
        comment_controls = []
        if comments:
            for comment in comments:
                comment_controls.append(
                    ft.Text(f"{comment.get('admin_id', 'Unknown')}: {comment.get('comment', '')}", size=14)
                )
        else:
            comment_controls.append(ft.Text("No comments yet", size=14, color=ft.Colors.GREY_500))
        
        return [
            ft.Text("Comments", size=16, weight=ft.FontWeight.BOLD),
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

        comment_field = ft.TextField(
            label="Add comment",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            expand=True
        )
        
        reason_field = ft.TextField(
            label="Reason for rejection",
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=14,
            expand=True
        )
        
        return create_approval_buttons(
            file_data, action_handler, comment_field, reason_field,
            refresh_callback, button_style_func
        ).controls
    
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
