import flet as ft
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
from services.approval_service import FileApprovalService, ApprovalStatus
from services.notification_service import NotificationService
from services.permission_service import PermissionService

# Import the file details popup
try:
    from admin.components.file_details_popup import FileDetailsPopup
except ImportError:
    try:
        from .file_details_popup import FileDetailsPopup
    except ImportError:
        try:
            from file_details_popup import FileDetailsPopup
        except ImportError:
            print("Warning: FileDetailsPopup could not be imported. Make sure file_details_popup.py is in the correct location.")
            FileDetailsPopup = None

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
        self.files_table = None
        self.selected_file_data = None
        self.open_details_button = None
        
        # Filter state - automatically set team filter to admin's team
        self.current_team_filter = self.get_admin_default_team()
        self.current_sort = "submission_date"
        
        # Initialize file details popup
        if FileDetailsPopup:
            self.file_details_popup = FileDetailsPopup(page, admin_user)
            self.file_details_popup.set_callback(self.on_file_action_completed)
        else:
            self.file_details_popup = None
            print("Warning: File details popup is not available")
        
        # File rename dialog (for double-click functionality)
        self.rename_dialog = None
    
    def get_admin_teams(self) -> List[str]:
        """Get admin's team tags safely"""
        try:
            return self.permission_service.get_user_teams(self.admin_user)
        except Exception as e:
            print(f"Error getting admin teams: {e}")
            return ["DEFAULT"]
    
    def get_admin_default_team(self) -> str:
        """Get admin's default team for auto-filtering"""
        if self.admin_teams and len(self.admin_teams) > 0:
            return self.admin_teams[0]  # Use first team as default
        return "ALL"
    
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
        """Create the main file approval interface with expanded files panel"""
        try:
            # Header with stats
            header = self.create_header()
            
            # Filters and controls (simplified - no search, no bulk mode)
            filters = self.create_filters_bar()
            
            # Main content area - only the files table (expanded to full width)
            main_content = ft.Container(
                content=self.create_files_table(),
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=10,
                expand=True
            )
            
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
            # Refresh files table
            self.refresh_files_table()
            # Refresh header to update counts
            self.page.update()
        except Exception as e:
            print(f"Error refreshing interface: {e}")
    
    def create_header(self) -> ft.Container:
        """Create header with updated approval statistics"""
        file_counts = self.get_file_counts()
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval Center", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Managing approvals for: {', '.join(self.admin_teams)}", 
                           size=12, color=ft.Colors.GREY_600)
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
                ft.Text(label, size=11, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            bgcolor=ft.Colors.GREY_50,
            border_radius=10,
            padding=15,
            width=110,
            height=70,
            alignment=ft.alignment.center
        )
    
    def create_filters_bar(self) -> ft.Column:
        """Create simplified filters bar with Open Details button"""
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
        
        # Create Open Details button
        self.open_details_button = ft.ElevatedButton(
            "Open File Details",
            icon=ft.Icons.INFO,
            on_click=self.open_selected_file_details,
            disabled=True,  # Initially disabled
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PURPLE,
                color=ft.Colors.WHITE
            )
        )
        
        # Filters row
        filters_row = ft.Row([
            ft.Dropdown(
                label="Filter by Team",
                width=150,
                options=team_options,
                value=self.current_team_filter,  # Auto-set to admin's team
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
            self.open_details_button,
            ft.Container(width=10),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table()
            )
        ])
        
        return ft.Column([filters_row], spacing=5)
    
    def create_files_table(self) -> ft.Container:
        """Create expanded files table that consumes the whole page"""
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD))
            ],
            rows=[],
            column_spacing=12,
            horizontal_margin=8,
            data_row_max_height=55,
            data_row_min_height=45
        )
        
        self.refresh_files_table()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pending Files", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Click on a file to select it, then use 'Open File Details' button. Double-click filename to open file directly.", 
                       size=12, color=ft.Colors.GREY_600),
                ft.Container(height=5),
                ft.Container(
                    content=ft.Column([self.files_table], scroll=ft.ScrollMode.ALWAYS),
                    expand=True  # Make table expand to fill available space
                )
            ], expand=True)
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
        """Refresh the files table with filtering"""
        try:
            # Clear current selection
            self.selected_file_data = None
            if self.open_details_button:
                self.open_details_button.disabled = True
                self.open_details_button.text = "Open File Details"
            
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
            
            # Apply team filter
            if self.current_team_filter != "ALL":
                pending_files = [f for f in pending_files 
                               if f.get('user_team', '') == self.current_team_filter]
            
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
                    size_str = self.format_file_size(file_size)
                    
                    # Format submission date
                    try:
                        submit_date = datetime.fromisoformat(file_data['submission_date'])
                        date_str = submit_date.strftime("%m/%d %H:%M")
                    except:
                        date_str = "Unknown"
                    
                    # Get filename with length limit for responsive display
                    original_filename = file_data.get('original_filename', 'Unknown')
                    display_filename = self.limit_filename_display(original_filename, 40)
                    
                    row = ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Text(
                                    display_filename, 
                                    tooltip=original_filename,
                                    size=13,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                # Add double-click handler for opening file
                                on_double_tap=lambda e, file_data=file_data: self.show_file_open_confirmation(file_data)
                            ),
                            ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'), size=13)),
                            ft.DataCell(ft.Text(file_data.get('user_team', 'Unknown'), size=13)),
                            ft.DataCell(ft.Text(size_str, size=13)),
                            ft.DataCell(ft.Text(date_str, size=13)),
                            ft.DataCell(ft.Container(
                                content=ft.Text("PENDING", color=ft.Colors.WHITE, size=11),
                                bgcolor=ft.Colors.ORANGE,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=4
                            ))
                        ],
                        # Handle row selection for button enabling
                        on_select_changed=lambda e, file_data=file_data: self.on_file_selected(e, file_data)
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
    
    def on_file_selected(self, e, file_data: Dict):
        """Handle file selection - enable/disable Open Details button"""
        if e.control.selected:
            # File is selected - enable button and store file data
            self.selected_file_data = file_data
            self.open_details_button.disabled = False
            self.open_details_button.text = f"Open Details: {self.limit_filename_display(file_data.get('original_filename', 'Unknown'), 20)}"
            print(f"File selected: {file_data.get('original_filename', 'Unknown')}")
        else:
            # File is deselected - disable button and clear file data
            self.selected_file_data = None
            self.open_details_button.disabled = True
            self.open_details_button.text = "Open File Details"
            print("File deselected")
        
        self.page.update()
    
    def open_selected_file_details(self, e):
        """Open file details popup for selected file"""
        if self.selected_file_data:
            if self.file_details_popup:
                try:
                    print(f"Opening file details popup for: {self.selected_file_data.get('original_filename', 'Unknown')}")
                    self.file_details_popup.show_file_details(self.selected_file_data)
                except Exception as ex:
                    print(f"Error opening file details popup: {ex}")
                    self.show_snackbar("Error opening file details", ft.Colors.RED)
            else:
                self.show_snackbar("File details popup is not available", ft.Colors.RED)
        else:
            self.show_snackbar("No file selected", ft.Colors.ORANGE)
    
    def show_file_open_confirmation(self, file_data: Dict):
        """Show confirmation dialog before opening file (double-click)"""
        try:
            # Try to import custom dialog from utils
            try:
                from utils.dialog import CustomDialog
                dialog = CustomDialog(self.page)
                dialog.show_confirmation_dialog(
                    title="Open File",
                    message=f"Do you want to open '{file_data['original_filename']}'?",
                    on_confirm=lambda: self.open_file_directly(file_data),
                    on_cancel=None,
                    confirm_text="Open",
                    cancel_text="Cancel",
                    confirm_color=ft.Colors.GREEN
                )
            except ImportError:
                print("utils.dialog not found, using fallback AlertDialog")
                # Fallback to simple AlertDialog if utils.dialog doesn't exist
                def confirm_open(e):
                    self.open_file_directly(file_data)
                    self.close_open_dialog()
                
                def cancel_open(e):
                    self.close_open_dialog()
                
                self.open_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Row([
                        ft.Icon(ft.Icons.OPEN_IN_NEW, size=24, color=ft.Colors.GREEN),
                        ft.Text("Open File", size=18, weight=ft.FontWeight.BOLD)
                    ]),
                    content=ft.Text(f"Do you want to open '{file_data['original_filename']}'?", size=14),
                    actions=[
                        ft.TextButton("Cancel", on_click=cancel_open),
                        ft.ElevatedButton(
                            "Open",
                            on_click=confirm_open,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
                            icon=ft.Icons.OPEN_IN_NEW
                        )
                    ]
                )
                
                self.page.dialog = self.open_dialog
                self.open_dialog.open = True
                self.page.update()
                
        except Exception as e:
            print(f"Error showing open confirmation: {e}")
            # Fallback - just open the file directly
            self.open_file_directly(file_data)
    
    def close_open_dialog(self):
        """Close open file dialog"""
        if hasattr(self, 'open_dialog') and self.open_dialog:
            self.open_dialog.open = False
            self.page.update()
    
    def open_file_directly(self, file_data: Dict):
        """Open file directly without showing any dialog"""
        try:
            import subprocess
            import platform
            
            file_id = file_data['file_id']
            user_id = file_data['user_id']
            original_filename = file_data['original_filename']
            
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
                    print(f"Found file at: {path}")
                    break
            
            if source_path:
                # Open with system default application
                if platform.system() == "Windows":
                    os.startfile(source_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", source_path])
                else:  # Linux
                    subprocess.run(["xdg-open", source_path])
                
                self.show_snackbar(f"Opening: {original_filename}", ft.Colors.BLUE)
            else:
                print(f"File not found. Checked paths: {possible_paths[:3]}...")
                self.show_snackbar("File not found in storage", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error opening file directly: {e}")
            self.show_snackbar("Error opening file", ft.Colors.RED)
    
    def on_file_action_completed(self, action: str, filename: str):
        """Callback when file is approved/rejected from popup"""
        if action == "approved":
            self.show_snackbar(f"File '{filename}' approved!", ft.Colors.GREEN)
        elif action == "rejected":
            self.show_snackbar(f"File '{filename}' rejected!", ft.Colors.RED)
        
        # Clear selection and disable button
        self.selected_file_data = None
        if self.open_details_button:
            self.open_details_button.disabled = True
            self.open_details_button.text = "Open File Details"
        
        # Refresh table and header stats
        self.refresh_files_table()
        # Refresh interface to update header cards
        self.refresh_interface()
    
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