"""
Admin Access Requests Panel Component
Shows pending file move requests that require manual admin intervention
"""

import flet as ft
from typing import List, Dict, Optional
from datetime import datetime
from services.enhanced_file_movement_service import get_enhanced_file_movement_service
from utils.logger import log_action

class AdminAccessRequestsPanel:
    """Panel for managing admin access requests"""
    
    def __init__(self, page: ft.Page, admin_user: str):
        self.page = page
        self.admin_user = admin_user
        self.movement_service = get_enhanced_file_movement_service()
        self.requests_table = None
        self.selected_request = None
    
    def create_requests_panel(self) -> ft.Container:
        """Create the admin access requests panel"""
        try:
            header = self._create_header()
            table_section = self._create_requests_table()
            actions_section = self._create_actions_section()
            
            return ft.Container(
                content=ft.Column([
                    header,
                    ft.Divider(),
                    table_section,
                    ft.Container(height=10),
                    actions_section
                ], expand=True, scroll=ft.ScrollMode.AUTO),
                padding=20,
                expand=True
            )
            
        except Exception as e:
            return self._create_error_panel(str(e))
    
    def _create_header(self) -> ft.Container:
        """Create header section"""
        pending_count = len(self.movement_service.get_pending_access_requests())
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Admin Access Requests", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Files requiring manual intervention due to network access issues", 
                           size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"Pending requests: {pending_count}", 
                           size=14, color=ft.Colors.ORANGE if pending_count > 0 else ft.Colors.GREEN)
                ]),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Refresh",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.refresh_requests(),
                    style=self._get_button_style("secondary")
                )
            ]),
            padding=ft.padding.only(bottom=10)
        )
    
    def _create_requests_table(self) -> ft.Container:
        """Create requests table"""
        self.requests_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Request ID", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Created", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
            ],
            rows=[]
        )
        
        self.refresh_requests()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pending Access Requests", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Container(
                    content=self.requests_table,
                    expand=True,
                    bgcolor=ft.Colors.WHITE,
                    padding=10,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300)
                )
            ]),
            expand=True
        )
    
    def _create_actions_section(self) -> ft.Container:
        """Create actions section"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Actions", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "Mark as Manually Completed",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=lambda e: self._handle_mark_completed(),
                        style=self._get_button_style("success")
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Retry Automatic Move",
                        icon=ft.Icons.REPLAY,
                        on_click=lambda e: self._handle_retry_move(),
                        style=self._get_button_style("primary")
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "View Details",
                        icon=ft.Icons.INFO,
                        on_click=lambda e: self._handle_view_details(),
                        style=self._get_button_style("secondary")
                    )
                ], wrap=True),
                ft.Container(height=10),
                ft.Text("Instructions:", size=16, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text("1. Select a request from the table above", size=14),
                    ft.Text("2. If you manually moved the file, click 'Mark as Manually Completed'", size=14),
                    ft.Text("3. If you want to retry automatic move, click 'Retry Automatic Move'", size=14),
                    ft.Text("4. Check 'View Details' for specific file paths and instructions", size=14),
                ], spacing=5)
            ]),
            bgcolor=ft.Colors.GREY_50,
            padding=15,
            border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_200)
        )
    
    def refresh_requests(self):
        """Refresh the requests table"""
        try:
            requests = self.movement_service.get_pending_access_requests()
            
            self.requests_table.rows.clear()
            
            if not requests:
                self.requests_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("No pending requests", style=ft.TextStyle(italic=True))),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text(""))
                    ])
                )
            else:
                for request in requests:
                    row = self._create_request_row(request)
                    self.requests_table.rows.append(row)
            
            self.page.update()
            
        except Exception as e:
            self._show_error(f"Error refreshing requests: {e}")
    
    def _create_request_row(self, request: Dict) -> ft.DataRow:
        """Create a table row for a request"""
        file_data = request.get('file_data', {})
        request_id = request.get('request_id', 'Unknown')
        
        # Format creation date
        try:
            created_date = datetime.fromisoformat(request.get('created_date', ''))
            date_str = created_date.strftime('%m/%d %H:%M')
        except:
            date_str = "Unknown"
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(request_id[:20] + "..." if len(request_id) > 20 else request_id, 
                                  tooltip=request_id)),
                ft.DataCell(ft.Text(file_data.get('original_filename', 'Unknown')[:25], 
                                  tooltip=file_data.get('original_filename', 'Unknown'))),
                ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'))),
                ft.DataCell(ft.Text(file_data.get('user_team', 'Unknown'))),
                ft.DataCell(ft.Text(date_str)),
                ft.DataCell(self._create_status_badge(request.get('status', 'unknown')))
            ],
            on_select_changed=lambda e, req=request: self._select_request(req)
        )
    
    def _create_status_badge(self, status: str) -> ft.Container:
        """Create status badge"""
        color_map = {
            'pending_manual_move': ft.Colors.ORANGE,
            'manually_completed': ft.Colors.GREEN,
            'automatically_completed': ft.Colors.BLUE
        }
        
        return ft.Container(
            content=ft.Text(status.replace('_', ' ').title(), 
                          color=ft.Colors.WHITE, size=10, weight=ft.FontWeight.BOLD),
            bgcolor=color_map.get(status, ft.Colors.GREY),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=6
        )
    
    def _select_request(self, request: Dict):
        """Select a request"""
        self.selected_request = request
        request_id = request.get('request_id', 'Unknown')
        self._show_info(f"Selected request: {request_id}")
    
    def _handle_mark_completed(self):
        """Handle marking request as manually completed"""
        if not self.selected_request:
            self._show_warning("Please select a request first")
            return
        
        request_id = self.selected_request.get('request_id', '')
        
        def on_confirm(e):
            try:
                from process_admin_requests import AdminRequestProcessor
                processor = AdminRequestProcessor()
                
                success = processor.process_request_manually(request_id, self.admin_user)
                
                if success:
                    self._show_success("Request marked as manually completed")
                    self.refresh_requests()
                    self.selected_request = None
                else:
                    self._show_error("Failed to mark request as completed")
                    
                dialog.open = False
                self.page.update()
                
            except Exception as ex:
                self._show_error(f"Error processing request: {ex}")
                dialog.open = False
                self.page.update()
        
        def on_cancel(e):
            dialog.open = False
            self.page.update()
        
        file_data = self.selected_request.get('file_data', {})
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Manual Completion"),
            content=ft.Column([
                ft.Text("Are you sure you have manually moved this file?"),
                ft.Text(f"File: {file_data.get('original_filename', 'Unknown')}"),
                ft.Text(f"Target: {self.selected_request.get('target_path', 'Unknown')}"),
                ft.Text("This action cannot be undone.", color=ft.Colors.ORANGE)
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Confirm", on_click=on_confirm)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _handle_retry_move(self):
        """Handle retrying automatic move"""
        if not self.selected_request:
            self._show_warning("Please select a request first")
            return
        
        request_id = self.selected_request.get('request_id', '')
        
        try:
            from process_admin_requests import AdminRequestProcessor
            processor = AdminRequestProcessor()
            
            success = processor.retry_automatic_move(request_id, self.admin_user)
            
            if success:
                self._show_success("Automatic move successful!")
                self.refresh_requests()
                self.selected_request = None
            else:
                self._show_error("Automatic move still failed - manual intervention required")
                
        except Exception as e:
            self._show_error(f"Error retrying move: {e}")
    
    def _handle_view_details(self):
        """Handle viewing request details"""
        if not self.selected_request:
            self._show_warning("Please select a request first")
            return
        
        file_data = self.selected_request.get('file_data', {})
        instructions = self.selected_request.get('instructions', {})
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Request Details"),
            content=ft.Column([
                ft.Text(f"Request ID: {self.selected_request.get('request_id', 'Unknown')}"),
                ft.Text(f"File: {file_data.get('original_filename', 'Unknown')}"),
                ft.Text(f"User: {file_data.get('user_id', 'Unknown')}"),
                ft.Text(f"Team: {file_data.get('user_team', 'Unknown')}"),
                ft.Text(f"Error: {self.selected_request.get('error_message', 'Unknown')}"),
                ft.Divider(),
                ft.Text("Manual Instructions:", weight=ft.FontWeight.BOLD),
                *[ft.Text(f"{key}: {value}") for key, value in instructions.items()]
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Close", on_click=close_dialog)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_error(self, message: str):
        """Show error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_warning(self, message: str):
        """Show warning message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.ORANGE
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_info(self, message: str):
        """Show info message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _get_button_style(self, button_type: str):
        """Get button style"""
        if button_type == "success":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                         ft.ControlState.HOVERED: ft.Colors.GREEN_700},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE}
            )
        elif button_type == "primary":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                         ft.ControlState.HOVERED: ft.Colors.BLUE_700},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE}
            )
        else:  # secondary
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_300,
                         ft.ControlState.HOVERED: ft.Colors.GREY_400},
                color={ft.ControlState.DEFAULT: ft.Colors.BLACK}
            )
    
    def _create_error_panel(self, error_msg: str) -> ft.Container:
        """Create error panel"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED),
                ft.Text("Error Loading Access Requests", size=24, weight=ft.FontWeight.BOLD),
                ft.Text(f"Details: {error_msg}", size=16, color=ft.Colors.GREY_600),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.refresh_requests()
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            expand=True
        )
