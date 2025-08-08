import flet as ft
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
import shutil
import tempfile
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
        
        # Filter state
        self.current_team_filter = "ALL"
        self.current_sort = "submission_date"
        
        # Search features
        self.search_query = ""
    
    def get_admin_teams(self) -> List[str]:
        """Get admin's team tags safely"""
        try:
            return self.permission_service.get_user_teams(self.admin_user)
        except Exception as e:
            print(f"Error getting admin teams: {e}")
            return ["DEFAULT"]
    
    def limit_filename_display(self, filename: str, max_length: int = 35) -> str:
        """Limit filename display length for responsive table"""
        if len(filename) <= max_length:
            return filename
        # Show start and end of filename with ellipsis in middle
        if max_length > 10:
            start_len = max_length // 2 - 2
            end_len = max_length - start_len - 3
            return f"{filename[:start_len]}...{filename[-end_len:]}"
        else:
            return filename[:max_length-3] + "..."
    
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
    
    def get_file_counts(self) -> Dict[str, int]:
        """Get counts for pending, approved, and rejected files"""
        try:
            # Get reviewable teams for this admin
            reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
            
            pending_files = set()
            approved_files = set()
            rejected_files = set()
            
            for team in reviewable_teams:
                # Get pending files
                team_pending = self.approval_service.get_pending_files_by_team(team, self.is_super_admin)
                for file_data in team_pending:
                    pending_files.add(file_data['file_id'])
                
                # Get approved files - try different methods to get approved files
                try:
                    team_approved = self.approval_service.get_approved_files_by_team(team, self.is_super_admin)
                    for file_data in team_approved:
                        approved_files.add(file_data['file_id'])
                except AttributeError:
                    # If method doesn't exist, try to get from general files with status
                    try:
                        all_files = self.approval_service.get_all_files_by_team(team, self.is_super_admin)
                        for file_data in all_files:
                            if file_data.get('status') == 'APPROVED':
                                approved_files.add(file_data['file_id'])
                    except:
                        pass
                
                # Get rejected files - try different methods
                try:
                    team_rejected = self.approval_service.get_rejected_files_by_team(team, self.is_super_admin)
                    for file_data in team_rejected:
                        rejected_files.add(file_data['file_id'])
                except AttributeError:
                    # If method doesn't exist, try to get from general files with status
                    try:
                        all_files = self.approval_service.get_all_files_by_team(team, self.is_super_admin)
                        for file_data in all_files:
                            if file_data.get('status') == 'REJECTED':
                                rejected_files.add(file_data['file_id'])
                    except:
                        pass
            
            return {
                'pending': len(pending_files),
                'approved': len(approved_files),
                'rejected': len(rejected_files)
            }
            
        except Exception as e:
            print(f"Error getting file counts: {e}")
            return {'pending': 0, 'approved': 0, 'rejected': 0}
    
    def create_approval_interface(self) -> ft.Container:
        """Create the main file approval interface"""
        try:
            # Header with stats
            header = self.create_header()
            
            # Filters and controls
            filters = self.create_filters_bar()
            
            # Main content area - responsive layout
            main_content = ft.ResponsiveRow([
                # Left: Files table
                ft.Container(
                    content=self.create_files_table(),
                    col={"sm": 12, "md": 7, "lg": 8},
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    padding=20
                ),
                
                # Right: Preview and actions
                ft.Container(
                    content=self.create_preview_panel(),
                    col={"sm": 12, "md": 5, "lg": 4},
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    padding=10
                )
            ])
            
            return ft.Container(
                content=ft.Column([
                    header,
                    ft.Divider(),
                    filters,
                    ft.Container(height=10),
                    main_content
                ], expand=True, scroll=ft.ScrollMode.HIDDEN),  # Prevent page-level scrolling
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
                ft.Text(f"Details: {error_msg}", size=16, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.refresh_interface()
                ),
                ft.Container(height=20),
                ft.Text("Please check that all required services are running and data files exist.", 
                       size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
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
            # Refresh header stats
            header = self.create_header()
            self.page.update()
        except Exception as e:
            print(f"Error refreshing interface: {e}")
    
    def create_header(self) -> ft.Container:
        """Create header with updated approval statistics"""
        file_counts = self.get_file_counts()
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Managing approvals for: {', '.join(self.admin_teams)}", 
                           size=16, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self.create_stat_card("Pending", str(file_counts['pending']), ft.Colors.ORANGE),
                    ft.Container(width=15),
                    self.create_stat_card("Approved", str(file_counts['approved']), ft.Colors.GREEN),
                    ft.Container(width=15),
                    self.create_stat_card("Rejected", str(file_counts['rejected']), ft.Colors.RED)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=10)
        )
    
    def create_stat_card(self, label: str, value: str, color: str) -> ft.Container:
        """Create a statistics card with proper text sizing"""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=14, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=110,
            height=80,
            alignment=ft.alignment.center
        )
    
    def create_filters_bar(self) -> ft.Row:
        """Create filters bar with search and controls"""
        try:
            # Load teams from data/teams.json
            teams_file = "data/teams.json"
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
            
            if os.path.exists(teams_file):
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                    if isinstance(teams_data, list):
                        # If teams.json is a list of team names
                        team_options.extend([ft.dropdown.Option(team, team) for team in teams_data])
                    elif isinstance(teams_data, dict):
                        # If teams.json is a dict with team objects
                        for team_key, team_data in teams_data.items():
                            team_name = team_data.get('name', team_key) if isinstance(team_data, dict) else team_key
                            team_options.append(ft.dropdown.Option(team_key, team_name))
            else:
                # Fallback to permission service teams
                reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
                team_options.extend([ft.dropdown.Option(team, team) for team in reviewable_teams])
                
        except Exception as e:
            print(f"Error loading teams: {e}")
            # Fallback to permission service teams
            try:
                reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user, self.admin_teams)
                team_options.extend([ft.dropdown.Option(team, team) for team in reviewable_teams])
            except:
                team_options = [ft.dropdown.Option("ALL", "All Teams")]
        
        # Filters row
        filters_row = ft.Row([
            ft.TextField(
                hint_text="Search files...",
                width=200,
                value=self.search_query,
                on_change=self.on_search_changed,
                prefix_icon=ft.Icons.SEARCH
            ),
            ft.Dropdown(
                label="Filter by Team",
                width=150,
                options=team_options,
                value=self.current_team_filter,
                on_change=self.on_team_filter_changed
            ),
            ft.Dropdown(
                label="Sort by",
                width=150,
                value=self.current_sort,
                options=[
                    ft.dropdown.Option("submission_date", "Date Submitted"),
                    ft.dropdown.Option("filename", "File Name"),
                    ft.dropdown.Option("user_id", "User"),
                    ft.dropdown.Option("file_size", "File Size")
                ],
                on_change=self.on_sort_changed
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table(),
                style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.BLUE},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
            )
        ])
        
        return ft.Column([
            filters_row,
        ], spacing=5)
    
    def on_search_changed(self, e):
        """Handle search input change"""
        self.search_query = e.control.value.lower()
        self.refresh_files_table()
    
    def get_container_size_category(self) -> str:
        """Determine container size category based on page width"""
        try:
            page_width = self.page.width if self.page.width else 1200
            if page_width < 600:
                return "xs"
            elif page_width < 900:
                return "sm"
            elif page_width < 1200:
                return "md"
            else:
                return "lg"
        except:
            return "lg"  # Default to large if can't determine
    
    def update_table_columns_for_size(self, size_category: str):
        """Update table columns based on container size"""
        if not hasattr(self, 'column_configs'):
            return
            
        config = self.column_configs.get(size_category, self.column_configs["lg"])
        
        # Rebuild columns based on size
        new_columns = []
        if config.get("file", True):
            new_columns.append(ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("user", True):
            new_columns.append(ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("team", True):
            new_columns.append(ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("size", True):
            new_columns.append(ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("submitted", True):
            new_columns.append(ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("status", True):
            new_columns.append(ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)))
        
        self.files_table.columns = new_columns
        return config
    
    def apply_filters(self, files: List[Dict]) -> List[Dict]:
        """Apply current filters to file list"""
        filtered_files = files.copy()
        
        # Apply search filter
        if self.search_query:
            filtered_files = [
                f for f in filtered_files
                if (self.search_query in f.get('original_filename', '').lower() or
                    self.search_query in f.get('user_id', '').lower() or
                    self.search_query in f.get('description', '').lower())
            ]
        
        # Apply team filter
        if self.current_team_filter != "ALL":
            filtered_files = [f for f in filtered_files 
                            if f.get('user_team', '') == self.current_team_filter]
        
        return filtered_files
    
    def create_files_table(self) -> ft.Container:
        """Create responsive files table that adapts to container size using ResponsiveRow"""
        
        # Define columns that will be shown based on container size
        def get_columns_for_size(col_config):
            columns = []
            if col_config.get("file", True):
                columns.append(ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("user", True):
                columns.append(ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("team", True):
                columns.append(ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("size", True):
                columns.append(ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("submitted", True):
                columns.append(ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("status", True):
                columns.append(ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)))
            return columns
        
        # Store column configurations for different sizes
        self.column_configs = {
            "xs": {"file": True, "user": False, "team": False, "size": False, "submitted": False, "status": True},  # Very small: only file and status
            "sm": {"file": True, "user": True, "team": False, "size": False, "submitted": False, "status": True},  # Small: add user
            "md": {"file": True, "user": True, "team": True, "size": False, "submitted": True, "status": True},  # Medium: add team and date
            "lg": {"file": True, "user": True, "team": True, "size": True, "submitted": True, "status": True}   # Large: all columns
        }
        
        # Create responsive data table
        self.files_table = ft.DataTable(
            columns=get_columns_for_size(self.column_configs["lg"]),  # Start with all columns
            rows=[],
            column_spacing=10,
            horizontal_margin=5,
            data_row_max_height=50,
            data_row_min_height=40,
            expand=True,
        )
        
        # Create responsive container for the table
        table_content = ft.ResponsiveRow([
            ft.Container(
                content=self.files_table,
                col={"xs": 12, "sm": 12, "md": 12, "lg": 12},  
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                padding=5,
                expand=True
            )
        ])
        
        self.refresh_files_table()
        
        return ft.Container(
            content=ft.Column([
                ft.ResponsiveRow([
                    ft.Container(
                        content=ft.Text("Pending Files", size=20, weight=ft.FontWeight.BOLD),
                        col={"xs": 12, "sm": 12, "md": 12, "lg": 12}
                    )
                ]),
                ft.Divider(),
                ft.Container(height=10),
                table_content
            ], expand=True, spacing=0),
            expand=True,
            padding=0
        )
    
    def create_preview_panel(self) -> ft.Container:
        """Create file preview and action panel with proper scrolling contained within panel"""
        self.preview_panel = ft.Column([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        
        return ft.Container(
            content=ft.Container(
                content=self.preview_panel,
                expand=True,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_200)
            ),
            expand=True,
            height=None,  # Let container determine height
            padding=0
        )
    
    def on_team_filter_changed(self, e):
        """Handle team filter change"""
        self.current_team_filter = e.control.value
        self.refresh_files_table()
    
    def on_sort_changed(self, e):
        """Handle sort change"""
        self.current_sort = e.control.value
        self.refresh_files_table()
    
    def refresh_files_table(self):
        """Refresh the files table with filtering, sorting, and responsive columns"""
        try:
            # Determine container size and update columns accordingly
            size_category = self.get_container_size_category()
            column_config = self.update_table_columns_for_size(size_category)
            
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
            
            # Apply all filters (search, team, etc.)
            pending_files = self.apply_filters(pending_files)
            
            # Apply sorting
            if self.current_sort == "filename":
                pending_files.sort(key=lambda x: x.get('original_filename', '').lower())
            elif self.current_sort == "user_id":
                pending_files.sort(key=lambda x: x.get('user_id', '').lower())
            elif self.current_sort == "file_size":
                pending_files.sort(key=lambda x: x.get('file_size', 0), reverse=True)
            else:  # submission_date
                pending_files.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
            
            self.files_table.rows.clear()
            
            if not pending_files:
                # Show "No files" message - adapt cells to visible columns
                empty_cells = []
                if column_config.get("file", True):
                    empty_cells.append(ft.DataCell(ft.Text("No pending files found", style=ft.TextStyle(italic=True))))
                for i in range(len(self.files_table.columns) - 1):
                    empty_cells.append(ft.DataCell(ft.Text("")))
                
                self.files_table.rows.append(ft.DataRow(cells=empty_cells))
            else:
                for file_data in pending_files:
                    # Format file size
                    file_size = file_data.get('file_size', 0)
                    size_str = self.format_file_size(file_size)
                    
                    # Format submission date
                    try:
                        submit_date = datetime.fromisoformat(file_data['submission_date'])
                        date_str = submit_date.strftime("%m/%d %H:%M")
                    except:
                        date_str = "Unknown"
                    
                    # Get filename with length limit for responsive display
                    original_filename = file_data.get('original_filename', 'Unknown')
                    # Adjust filename length based on container size
                    max_filename_length = 20 if size_category in ["xs", "sm"] else 30
                    display_filename = self.limit_filename_display(original_filename, max_filename_length)
                    
                    file_id = file_data['file_id']
                    
                    # Build cells based on visible columns
                    cells = []
                    if column_config.get("file", True):
                        cells.append(ft.DataCell(
                            ft.Text(
                                display_filename, 
                                tooltip=original_filename,
                                size=14,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ))
                    if column_config.get("user", True):
                        cells.append(ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'), size=14)))
                    if column_config.get("team", True):
                        cells.append(ft.DataCell(ft.Text(file_data.get('user_team', 'Unknown'), size=14)))
                    if column_config.get("size", True):
                        cells.append(ft.DataCell(ft.Text(size_str, size=14)))
                    if column_config.get("submitted", True):
                        cells.append(ft.DataCell(ft.Text(date_str, size=14)))
                    if column_config.get("status", True):
                        cells.append(ft.DataCell(ft.Container(
                            content=ft.Text("PENDING", color=ft.Colors.WHITE, size=10),
                            bgcolor=ft.Colors.ORANGE,
                            padding=ft.padding.symmetric(horizontal=6, vertical=3),
                            border_radius=4
                        )))
                    
                    row = ft.DataRow(
                        cells=cells,
                        on_select_changed=lambda e, file_data=file_data: self.select_file(file_data)
                    )
                    
                    self.files_table.rows.append(row)
            
            self.page.update()
        except Exception as e:
            print(f"Error refreshing files table: {e}")
            # Show error message in the table
            self.files_table.rows.clear()
            error_cells = [ft.DataCell(ft.Text(f"Error loading files: {e}", color=ft.Colors.RED))]
            for i in range(len(self.files_table.columns) - 1):
                error_cells.append(ft.DataCell(ft.Text("")))
            self.files_table.rows.append(ft.DataRow(cells=error_cells))
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
                label="Add comment",
                multiline=True,
                min_lines=2,
                max_lines=4,
                text_size=14
            )
            
            # Create reason field for rejection
            self.reason_field = ft.TextField(
                label="Reason for rejection",
                multiline=True,
                min_lines=2,
                max_lines=3,
                text_size=14
            )
            
            # Format submission date
            submit_date = "Unknown"
            try:
                submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
            except:
                pass
            
            # File info
            file_info = ft.Column([
                ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"File name: {file_data.get('original_filename', 'Unknown')}", size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"User: {file_data.get('user_id', 'Unknown')}", size=14),
                ft.Text(f"Team: {file_data.get('user_team', 'Unknown')}", size=14),
                ft.Text(f"Size: {self.format_file_size(file_data.get('file_size', 0))}", size=14),
                ft.Text(f"Submitted: {submit_date}", size=14),
                ft.Container(height=10),
                ft.Text("Description:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(file_data.get('description', 'No description provided'), size=12, color=ft.Colors.GREY_600),
                ft.Container(height=10),
                ft.Text("Tags:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(', '.join(file_data.get('tags', [])) or 'No tags', size=12, color=ft.Colors.GREY_600),
                
                # Download and Open buttons
                ft.Container(height=15),
                ft.Row([
                    ft.ElevatedButton(
                        "Download",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=lambda e: self.download_file(file_data),
                        style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.BLUE},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Open",
                        icon=ft.Icons.OPEN_IN_NEW,
                        on_click=lambda e: self.open_file(file_data),
                        style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ])
            
            # Comments section
            comment_controls = []
            if comments:
                for comment in comments:
                    comment_controls.append(
                        ft.Text(f"{comment['admin_id']}: {comment['comment']}", size=14)
                    )
            else:
                comment_controls.append(ft.Text("No comments yet", size=14, color=ft.Colors.GREY_500))
            
            comments_section = ft.Column([
                ft.Text("Comments", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(comment_controls),
                    height=100,
                    bgcolor=ft.Colors.GREY_50,
                    padding=10,
                    border_radius=4,
                    alignment=ft.alignment.center_left
                )
            ])
            
            # Action buttons
            actions = ft.Column([
                ft.Text("Actions", size=16, weight=ft.FontWeight.BOLD),
                self.comment_field,
                ft.Container(height=5),
                ft.ElevatedButton(
                    "Add Comment",
                    icon=ft.Icons.COMMENT,
                    on_click=self.add_comment,
                    style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.BLUE},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                ),
                ft.Container(height=10),
                ft.Divider(),
                ft.Container(height=10),
                self.reason_field,
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "Approve",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=self.approve_file,
                        style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Reject",
                        icon=ft.Icons.CANCEL,
                        on_click=self.reject_file,
                        style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.RED},
                                  color={ft.ControlState.DEFAULT: ft.Colors.RED,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                                        ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                    )
                ], spacing=10)
            ])
            
            # Update preview panel with scroll support
            self.preview_panel.controls.clear()
            self.preview_panel.controls.extend([
                file_info,
                ft.Divider(),
                comments_section,
                ft.Divider(), 
                actions
            ])
            
            # Ensure the preview panel has scroll enabled and is contained
            self.preview_panel.scroll = ft.ScrollMode.AUTO
            self.preview_panel.expand = True
            
            self.page.update()
        except Exception as e:
            print(f"Error updating preview panel: {e}")
    
    def download_file(self, file_data: Dict):
        """Download the selected file"""
        try:
            file_id = file_data['file_id']
            user_id = file_data['user_id']
            original_filename = file_data['original_filename']
            
            # Find the file in storage (improved path checking)
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
                    print(f"Found file at: {path}")
                    break
            
            if source_path:
                # For desktop apps, copy to downloads or temp folder
                downloads_path = os.path.expanduser("~/Downloads")
                if not os.path.exists(downloads_path):
                    downloads_path = tempfile.gettempdir()
                
                dest_path = os.path.join(downloads_path, original_filename)
                shutil.copy2(source_path, dest_path)
                
                self.show_snackbar(f"Downloaded: {original_filename}", ft.Colors.GREEN)
            else:
                # Show which paths were checked for debugging
                checked_paths = "\n".join(possible_paths[:3]) + "\n..."
                print(f"File not found. Checked paths:\n{checked_paths}")
                self.show_snackbar(f"File not found in storage. Checked multiple locations.", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error downloading file: {e}")
            self.show_snackbar("Error downloading file", ft.Colors.RED)
    
    def open_file(self, file_data: Dict):
        """Open/preview the selected file"""
        try:
            file_id = file_data['file_id']
            user_id = file_data['user_id']
            original_filename = file_data['original_filename']
            
            # Find the file in storage (improved path checking)
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
                    print(f"Found file at: {path}")
                    break
            
            if source_path:
                # Open with system default application
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(source_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", source_path])
                else:  # Linux
                    subprocess.run(["xdg-open", source_path])
                
                self.show_snackbar(f"Opening: {original_filename}", ft.Colors.BLUE)
            else:
                # Show which paths were checked for debugging
                checked_paths = "\n".join(possible_paths[:3]) + "\n..."
                print(f"File not found. Checked paths:\n{checked_paths}")
                self.show_snackbar(f"File not found in storage. Checked multiple locations.", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error opening file: {e}")
            self.show_snackbar("Error opening file", ft.Colors.RED)
    
    def add_comment(self, e):
        """Add comment to selected file and notify user"""
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
                # Send comment notification to user
                self.notification_service.notify_comment_added(
                    self.selected_file['user_id'],
                    self.selected_file['original_filename'], 
                    self.admin_user,
                    self.comment_field.value
                )
                
                self.comment_field.value = ""
                self.show_snackbar("Comment added and user notified!", ft.Colors.GREEN)
                self.update_preview_panel()
            else:
                self.show_snackbar("Failed to add comment", ft.Colors.RED)
        except Exception as e:
            print(f"Error adding comment: {e}")
            self.show_snackbar("Error adding comment", ft.Colors.RED)
    
    def approve_file(self, e):
        """Approve the selected file and notify user"""
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
                self.clear_selection()
                self.refresh_files_table()
                # Refresh header to update counts
                self.refresh_interface()
            else:
                self.show_snackbar("Failed to approve file", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self.show_snackbar("Error approving file", ft.Colors.RED)
    
    def reject_file(self, e):
        """Reject file and notify user"""
        if not self.selected_file:
            return
        
        if not self.reason_field.value:
            self.show_snackbar("Please provide a reason for rejection", ft.Colors.ORANGE)
            return
        
        try:
            success = self.approval_service.reject_file(
                self.selected_file['file_id'],
                self.admin_user,
                self.reason_field.value,
                False  # Always reject, no changes requested
            )
            
            if success:
                # Send notification to user
                self.notification_service.notify_approval_status(
                    self.selected_file['user_id'],
                    self.selected_file['original_filename'],
                    ApprovalStatus.REJECTED.value,
                    self.admin_user,
                    self.reason_field.value
                )
                
                filename = self.selected_file.get('original_filename', 'Unknown')
                self.show_snackbar(f"File '{filename}' rejected!", ft.Colors.RED)
                
                # Clear selection and refresh
                self.clear_selection()
                self.refresh_files_table()
                # Refresh header to update counts
                self.refresh_interface()
            else:
                self.show_snackbar("Failed to reject file", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error rejecting file: {e}")
            self.show_snackbar("Error processing file", ft.Colors.RED)
    
    def clear_selection(self):
        """Clear current file selection"""
        self.selected_file = None
        self.preview_panel.controls.clear()
        self.preview_panel.controls.extend([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ])
        # Maintain scroll and expand properties
        self.preview_panel.scroll = ft.ScrollMode.AUTO
        self.preview_panel.expand = True
    
    def show_snackbar(self, message: str, color: str):
        """Show snackbar message with enhanced styling"""
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if color == ft.Colors.GREEN 
                        else ft.Icons.WARNING if color == ft.Colors.ORANGE 
                        else ft.Icons.ERROR if color == ft.Colors.RED 
                        else ft.Icons.INFO,
                        color=ft.Colors.WHITE, size=16
                    ),
                    ft.Text(message, color=ft.Colors.WHITE)
                ]),
                bgcolor=color,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"Error showing snackbar: {e}")
