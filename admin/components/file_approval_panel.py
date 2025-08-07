import flet as ft
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
from services.approval_service import FileApprovalService, ApprovalStatus
from services.notification_service import NotificationService
from services.permission_service import PermissionService

class FileApprovalPanel:
    def __init__(self, page: ft.Page, admin_user: str):
        self.page = page
        self.admin_user = admin_user
        
        # Initialize services
        self.approval_service = FileApprovalService()
        self.permission_service = PermissionService()
        self.notification_service = NotificationService()
        
        # Initialize default permissions if needed
        self.permission_service.initialize_default_permissions()
        
        # Get admin details
        self.admin_teams = self.get_admin_teams()
        self.is_super_admin = self.permission_service.is_super_admin(admin_user)
        
        # UI components
        self.selected_file = None
        self.files_table = None
        self.preview_panel = None
        self.comment_field = None
        self.reason_field = None
    
    def get_admin_teams(self) -> List[str]:
        """Get admin's team tags safely"""
        try:
            return self.permission_service.get_user_teams(self.admin_user)
        except Exception as e:
            print(f"Error getting admin teams: {e}")
            return ["DEFAULT"]
    
    def create_approval_interface(self) -> ft.Container:
        """Create the main file approval interface"""
        try:
            # Header with stats
            header = self.create_header()
            
            # Filters and controls
            filters = self.create_filters_bar()
            
            # Main content area
            main_content = ft.Row([
                # Left: Files table
                ft.Container(
                    content=self.create_files_table(),
                    expand=2,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    padding=10
                ),
                
                ft.Container(width=20),
                
                # Right: Preview and actions
                ft.Container(
                    content=self.create_preview_panel(),
                    expand=1,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    padding=10
                )
            ], expand=True)
            
            return ft.Container(
                content=ft.Column([
                    header,
                    ft.Divider(),
                    filters,
                    ft.Container(height=10),
                    main_content
                ], expand=True),
                padding=20,
                expand=True
            )
        except Exception as e:
            print(f"Error creating approval interface: {e}")
            return self.create_error_interface(str(e))
    
    def create_error_interface(self, error_msg: str) -> ft.Container:
        """Create error interface when main interface fails"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                ft.Text("File Approval Panel", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Error loading approval system", size=16, color=ft.Colors.RED),
                ft.Text(f"Details: {error_msg}", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.refresh_interface()
                ),
                ft.Container(height=20),
                ft.Text("Please check that all required services are running and data files exist.", 
                       size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            expand=True
        )
    
    def refresh_interface(self):
        """Refresh the interface"""
        try:
            # Refresh files table and preview
            self.refresh_files_table()
            self.update_preview_panel()
        except Exception as e:
            print(f"Error refreshing interface: {e}")
    
    def create_header(self) -> ft.Container:
        """Create header with approval statistics"""
        try:
            # Get reviewable teams for this admin
            reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
            
            # Get pending files
            all_pending = []
            for team in reviewable_teams:
                team_files = self.approval_service.get_pending_files_by_team(team, self.is_super_admin)
                all_pending.extend(team_files)
            
            # Remove duplicates
            seen_ids = set()
            unique_pending = []
            for file_data in all_pending:
                if file_data['file_id'] not in seen_ids:
                    unique_pending.append(file_data)
                    seen_ids.add(file_data['file_id'])
            
            pending_count = len(unique_pending)
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = len([f for f in unique_pending 
                              if f['submission_date'].startswith(today)])
        except Exception as e:
            print(f"Error in create_header: {e}")
            pending_count = 0
            today_count = 0
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval Center", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Super Admin" if self.is_super_admin else f"Teams: {', '.join(self.admin_teams)}", 
                           size=14, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self.create_stat_card("Pending", str(pending_count), ft.Colors.ORANGE),
                    ft.Container(width=10),
                    self.create_stat_card("Today", str(today_count), ft.Colors.BLUE)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=10)
        )
    
    def create_stat_card(self, label: str, value: str, color: str) -> ft.Container:
        """Create a statistics card"""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=12, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            padding=15,
            width=100
        )
    
    def create_filters_bar(self) -> ft.Row:
        """Create filters and search bar"""
        try:
            # Get available teams for filtering
            reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
            team_options.extend([ft.dropdown.Option(team, team) for team in reviewable_teams])
        except:
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
        
        return ft.Row([
            ft.TextField(
                hint_text="Search files...",
                width=300,
                border_radius=8,
                prefix_icon=ft.Icons.SEARCH,
                on_change=self.on_search_changed
            ),
            ft.Dropdown(
                label="Filter by Team",
                width=150,
                options=team_options,
                value="ALL",
                on_change=self.on_team_filter_changed
            ),
            ft.Dropdown(
                label="Sort by",
                width=150,
                value="submission_date",
                options=[
                    ft.dropdown.Option("submission_date", "Date Submitted"),
                    ft.dropdown.Option("filename", "File Name"),
                    ft.dropdown.Option("user_id", "User"),
                    ft.dropdown.Option("file_size", "File Size")
                ],
                on_change=lambda e: self.refresh_files_table()
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table()
            )
        ])
    
    def create_files_table(self) -> ft.Container:
        """Create the files table"""
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD))
            ],
            rows=[]
        )
        
        self.refresh_files_table()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pending Files", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column([self.files_table], scroll=ft.ScrollMode.AUTO),
                    height=400,
                    expand=True
                )
            ])
        )
    
    def create_preview_panel(self) -> ft.Container:
        """Create file preview and action panel"""
        self.preview_panel = ft.Column([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=12, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(
            content=self.preview_panel,
            height=500
        )
    
    def refresh_files_table(self):
        """Refresh the files table"""
        try:
            # Get reviewable teams for this admin
            reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
            
            # Get pending files from all reviewable teams
            all_pending = []
            for team in reviewable_teams:
                team_files = self.approval_service.get_pending_files_by_team(team, self.is_super_admin)
                all_pending.extend(team_files)
            
            # Remove duplicates based on file_id
            seen_ids = set()
            pending_files = []
            for file_data in all_pending:
                if file_data['file_id'] not in seen_ids:
                    pending_files.append(file_data)
                    seen_ids.add(file_data['file_id'])
            
            self.files_table.rows.clear()
            
            if not pending_files:
                # Show "No files" message
                self.files_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("No pending files found", style=ft.TextStyle(italic=True))),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text(""))
                    ])
                )
            else:
                for file_data in pending_files:
                    # Format file size
                    file_size = file_data.get('file_size', 0)
                    if file_size > 0:
                        size_mb = file_size / (1024 * 1024)
                        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{file_size / 1024:.1f} KB"
                    else:
                        size_str = "Unknown"
                    
                    # Format submission date
                    try:
                        submit_date = datetime.fromisoformat(file_data['submission_date'])
                        date_str = submit_date.strftime("%m/%d %H:%M")
                    except:
                        date_str = "Unknown"
                    
                    row = ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(file_data.get('original_filename', 'Unknown'))),
                            ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'))),
                            ft.DataCell(ft.Text(file_data.get('user_team', 'Unknown'))),
                            ft.DataCell(ft.Text(size_str)),
                            ft.DataCell(ft.Text(date_str)),
                            ft.DataCell(ft.Container(
                                content=ft.Text("PENDING", color=ft.Colors.WHITE, size=11),
                                bgcolor=ft.Colors.ORANGE,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            ))
                        ],
                        on_select_changed=lambda e, file_data=file_data: self.select_file(file_data)
                    )
                    
                    self.files_table.rows.append(row)
            
            self.page.update()
        except Exception as e:
            print(f"Error refreshing files table: {e}")
            # Show error message in the table
            self.files_table.rows.clear()
            self.files_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"Error loading files: {e}", color=ft.Colors.RED)),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text(""))
                ])
            )
            self.page.update()
    
    def select_file(self, file_data: Dict):
        """Select a file for review"""
        try:
            self.selected_file = file_data
            self.update_preview_panel()
        except Exception as e:
            print(f"Error selecting file: {e}")
    
    def update_preview_panel(self):
        """Update the preview panel with selected file info"""
        if not self.selected_file:
            return
        
        try:
            file_data = self.selected_file
            
            # Load comments for this file
            comments = self.approval_service.load_comments().get(file_data['file_id'], [])
            
            # Create comment field
            self.comment_field = ft.TextField(
                label="Add comment (optional)",
                multiline=True,
                min_lines=2,
                max_lines=4,
                width=300
            )
            
            # Create reason field for rejection
            self.reason_field = ft.TextField(
                label="Reason for rejection/changes",
                multiline=True,
                min_lines=2,
                max_lines=3,
                width=300
            )
            
            # File info
            submit_date = "Unknown"
            try:
                submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
            except:
                pass
            
            file_info = ft.Column([
                ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"📄 {file_data.get('original_filename', 'Unknown')}", size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"👤 User: {file_data.get('user_id', 'Unknown')}", size=12),
                ft.Text(f"🏢 Team: {file_data.get('user_team', 'Unknown')}", size=12),
                ft.Text(f"📏 Size: {file_data.get('file_size', 0) / (1024*1024):.1f} MB", size=12),
                ft.Text(f"📅 Submitted: {submit_date}", size=12),
                ft.Container(height=10),
                ft.Text("Description:", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(file_data.get('description', 'No description provided'), size=12, color=ft.Colors.GREY_600),
                ft.Container(height=10),
                ft.Text("Tags:", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(', '.join(file_data.get('tags', [])) or 'No tags', size=12, color=ft.Colors.GREY_600)
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
                        ft.Text(f"{comment['admin_id']} ({timestamp}): {comment['comment']}", size=11)
                    )
            else:
                comment_controls.append(ft.Text("No comments yet", size=11, color=ft.Colors.GREY_500))
            
            comments_section = ft.Column([
                ft.Text("Comments", size=14, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(comment_controls),
                    height=100,
                    bgcolor=ft.Colors.GREY_50,
                    padding=10,
                    border_radius=4
                )
            ])
            
            # Action buttons
            actions = ft.Column([
                ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD),
                self.comment_field,
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Add Comment",
                    icon=ft.Icons.COMMENT,
                    on_click=self.add_comment,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE)
                ),
                ft.Container(height=10),
                self.reason_field,
                ft.Container(height=5),
                ft.Row([
                    ft.ElevatedButton(
                        "Approve",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=self.approve_file,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                    ),
                    ft.ElevatedButton(
                        "Request Changes", 
                        icon=ft.Icons.EDIT,
                        on_click=lambda e: self.reject_file(True),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE)
                    )
                ], spacing=10),
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Reject",
                    icon=ft.Icons.CANCEL,
                    on_click=lambda e: self.reject_file(False),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED, color=ft.Colors.WHITE),
                    width=200
                )
            ])
            
            # Update preview panel
            self.preview_panel.controls.clear()
            self.preview_panel.controls.extend([
                file_info,
                ft.Divider(),
                comments_section,
                ft.Divider(), 
                actions
            ])
            
            self.page.update()
        except Exception as e:
            print(f"Error updating preview panel: {e}")
    
    def add_comment(self, e):
        """Add comment to selected file"""
        if not self.selected_file or not self.comment_field.value:
            self.show_snackbar("Please enter a comment", ft.Colors.ORANGE)
            return
        
        try:
            success = self.approval_service.add_comment(
                self.selected_file['file_id'],
                self.admin_user,
                self.comment_field.value
            )
            
            if success:
                self.comment_field.value = ""
                self.show_snackbar("Comment added successfully!", ft.Colors.GREEN)
                self.update_preview_panel()
            else:
                self.show_snackbar("Failed to add comment", ft.Colors.RED)
        except Exception as e:
            print(f"Error adding comment: {e}")
            self.show_snackbar("Error adding comment", ft.Colors.RED)
    
    def approve_file(self, e):
        """Approve the selected file"""
        if not self.selected_file:
            return
        
        try:
            success = self.approval_service.approve_file(
                self.selected_file['file_id'],
                self.admin_user
            )
            
            if success:
                # Send notification to user
                self.notification_service.notify_approval_status(
                    self.selected_file['user_id'],
                    self.selected_file['original_filename'],
                    ApprovalStatus.APPROVED.value,
                    self.admin_user
                )
                
                filename = self.selected_file.get('original_filename', 'Unknown')
                self.show_snackbar(f"File '{filename}' approved!", ft.Colors.GREEN)
                
                # Clear selection and refresh
                self.selected_file = None
                self.preview_panel.controls.clear()
                self.preview_panel.controls.extend([
                    ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500),
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300)
                ])
                self.refresh_files_table()
            else:
                self.show_snackbar("Failed to approve file", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self.show_snackbar("Error approving file", ft.Colors.RED)
    
    def reject_file(self, request_changes: bool):
        """Reject file or request changes"""
        if not self.selected_file:
            return
        
        if not self.reason_field.value:
            self.show_snackbar("Please provide a reason for rejection/changes", ft.Colors.ORANGE)
            return
        
        try:
            success = self.approval_service.reject_file(
                self.selected_file['file_id'],
                self.admin_user,
                self.reason_field.value,
                request_changes
            )
            
            if success:
                # Send notification to user
                status = ApprovalStatus.CHANGES_REQUESTED.value if request_changes else ApprovalStatus.REJECTED.value
                self.notification_service.notify_approval_status(
                    self.selected_file['user_id'],
                    self.selected_file['original_filename'],
                    status,
                    self.admin_user,
                    self.reason_field.value
                )
                
                filename = self.selected_file.get('original_filename', 'Unknown')
                action = "Changes requested for" if request_changes else "Rejected"
                self.show_snackbar(f"{action} '{filename}'", 
                                  ft.Colors.ORANGE if request_changes else ft.Colors.RED)
                
                # Clear selection and refresh
                self.selected_file = None
                self.preview_panel.controls.clear()
                self.preview_panel.controls.extend([
                    ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500),
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300)
                ])
                self.refresh_files_table()
            else:
                self.show_snackbar("Failed to process file", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error rejecting file: {e}")
            self.show_snackbar("Error processing file", ft.Colors.RED)
    
    def show_snackbar(self, message: str, color: str):
        """Show snackbar message"""
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"Error showing snackbar: {e}")
    
    def on_search_changed(self, e):
        """Handle search input change"""
        # TODO: Implement search functionality
        print(f"Search: {e.control.value}")
    
    def on_team_filter_changed(self, e):
        """Handle team filter change"""
        # TODO: Implement team filtering
        print(f"Team filter: {e.control.value}")
        self.refresh_files_table()
