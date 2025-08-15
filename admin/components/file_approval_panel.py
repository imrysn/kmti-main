# file_approval_panel.py
import flet as ft
import os 
import shutil
import subprocess
import platform
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from utils.config_loader import get_config
from utils.file_manager import get_file_manager, SecurityError
from utils.logger import get_enhanced_logger, log_security_event, log_file_operation, log_approval_action, PerformanceTimer
from utils.auth import get_enhanced_authenticator
from utils.dialog import show_confirm_dialog
from services.new_approval_service import NewFileApprovalService
from services.file_approval_constant import FileApprovalStatus
from services.notification_service import NotificationService
from services.permission_service import PermissionService

class FileApprovalPanel:
    
    def __init__(self, page: ft.Page, admin_user: str):
        self.page = page
        
        # Initialize configuration and utilities
        self.config = get_config()
        self.file_manager = get_file_manager()
        self.enhanced_logger = get_enhanced_logger()
        self.enhanced_auth = get_enhanced_authenticator()
        self.current_view = "pending"

        # Initialize UI state
        self.selected_file = None
        self.files_table = None
        self.preview_panel_widget = None
        
        try:
            # Sanitize admin user input for security
            self.admin_user = self.enhanced_auth.sanitize_username(admin_user)
        except SecurityError as e:
            self.enhanced_logger.security_logger.error(f"Invalid admin user ID: {e}")
            raise ValueError(f"Invalid admin user: {admin_user}")
        
        # Initialize services with error handling
        self._initialize_services()
        
        # Get admin details with proper error handling
        self.admin_teams = self._get_admin_teams_safely()
        
        # Initialize UI state
        self.selected_file = None
        self.files_table = None
        self.preview_panel_widget = None
        
        # Initialize filter state
        self.current_team_filter = "ALL"
        self.current_sort = "submission_date"
        self.search_query = ""
        
        # Create UI components
        self._initialize_ui_components()
        
        self.enhanced_logger.general_logger.info(f"File approval panel initialized for admin: {self.admin_user}")
    
    def _initialize_services(self):
        try:
            self.approval_service = NewFileApprovalService()
            self.permission_service = PermissionService()
            self.notification_service = NotificationService()
            
            # Initialize default permissions if needed
            try:
                self.permission_service.initialize_default_permissions()
            except Exception:
                # ignore if not present or already initialized
                pass
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Failed to initialize services: {e}")
            raise RuntimeError("Service initialization failed") from e
    
    def _get_admin_teams_safely(self) -> List[str]:

        try:
            teams = self.permission_service.get_user_teams(self.admin_user)
            # Use your existing logger for activity tracking
            from utils.logger import log_action
            log_action(self.admin_user, f"Retrieved team access: {teams}")
            return teams
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting admin teams: {e}")
            return ["DEFAULT"]
    
    def _initialize_ui_components(self):

        # Get UI constants from your enhanced config
        self.ui_config = self.config.ui_constants
        self.file_config = self.config.file_constants
    
    def create_approval_interface(self) -> ft.Container:

        try:
            with PerformanceTimer("FileApprovalPanel", "create_interface"):
                # Create header with statistics
                header = self._create_header_section()
                
                # Create filter bar
                filters = self._create_filters_section()
                
                # Create main content area with responsive layout
                main_content = self._create_main_content_area()
                
                return ft.Container(
                    content=ft.Column([
                        header,
                        ft.Divider(),
                        filters,
                        ft.Container(height=10),
                        main_content
                    ], expand=True, scroll=ft.ScrollMode.HIDDEN),
                    padding=20,
                    expand=True
                )
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error creating approval interface: {e}")
            return self._create_error_interface(str(e))
    
    def _create_header_section(self) -> ft.Container:

        file_counts = self._get_file_counts_safely()
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Managing approvals for: {', '.join(self.admin_teams)}", 
                            size=16, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self._create_stat_card("Pending", str(file_counts['pending']), ft.Colors.ORANGE, "pending"),
                    ft.Container(width=15),
                    self._create_stat_card("Approved", str(file_counts['approved']), ft.Colors.GREEN, "approved"),
                    ft.Container(width=15),
                    self._create_stat_card("Rejected", str(file_counts['rejected']), ft.Colors.RED, "rejected")
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=10)
        )
    
    def _create_stat_card(self, label: str, value: str, color: str, view_type: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=14, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=self.config.get_ui_constant('stat_card_width', 110),
            height=self.config.get_ui_constant('stat_card_height', 80),
            alignment=ft.alignment.center,
            on_click=lambda e: self._switch_table_view(view_type, label) 
        )

    def _switch_table_view(self, view_type: str, label: str):
        self.current_view = view_type
        self.update_files_table_title(label) 
        # Reset team filter to ALL when switching views to avoid accidental hiding
        self.current_team_filter = "ALL"
        self.refresh_files_table()
    
    def _create_filters_section(self) -> ft.Row:

        try:
            teams = self._load_teams_safely()
            return self._create_filter_bar(teams)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error creating filters section: {e}")
            
            return ft.Row([
                ft.TextField(
                    hint_text="Search files...",
                    width=200,
                    value=self.search_query,
                    on_change=self._on_search_changed,
                    prefix_icon=ft.Icons.SEARCH
                ),
                ft.Dropdown(
                    label="Filter by Team",
                    width=150,
                    options=[ft.dropdown.Option("ALL", "All Teams")],
                    value="ALL",
                    on_change=self._on_team_filter_changed
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
                    on_change=self._on_sort_changed
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Refresh",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.refresh_files_table(),
                    style=self._get_button_style("secondary") if hasattr(self, '_get_button_style') else None
                )
            ])
    
    def _load_teams_safely(self) -> List[str]:
        """Load teams with simplified approach"""
        try:
            # Use permission service directly - get_reviewable_teams should return list of teams
            return self.permission_service.get_reviewable_teams(self.admin_user)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error loading teams: {e}")
            return ["DEFAULT"]

    def _create_filter_bar(self, teams: List[str]) -> ft.Row:

        try:
            # Create team options with more lenient validation
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
            
            for team in teams:
                if team and isinstance(team, str) and len(team.strip()) > 0:
                    # Simple validation - just ensure it's a reasonable string
                    safe_team = team.strip()[:50]  # Limit length
                    # Remove any potentially problematic characters but keep it simple  
                    safe_team = ''.join(c for c in safe_team if c.isalnum() or c in ' _-.')
                    
                    if safe_team:  # Only add if we have a valid team name
                        team_options.append(ft.dropdown.Option(safe_team, safe_team))
        
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error creating team options: {e}")
            # Minimal fallback
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
        
        try:
            search_width = self.config.get_ui_constant('search_field_width', 200)
            dropdown_width = self.config.get_ui_constant('dropdown_width', 150)
        except:
            search_width = 200
            dropdown_width = 150
        
        return ft.Row([
            ft.TextField(
                hint_text="Search files...",
                width=search_width,
                value=self.search_query,
                on_change=self._on_search_changed,
                prefix_icon=ft.Icons.SEARCH
            ),
            ft.Dropdown(
                label="Filter by Team",
                width=dropdown_width,
                options=team_options,
                value=self.current_team_filter,
                on_change=self._on_team_filter_changed
            ),
            ft.Dropdown(
                label="Sort by", 
                width=dropdown_width,
                value=self.current_sort,
                options=[
                    ft.dropdown.Option("submission_date", "Date Submitted"),
                    ft.dropdown.Option("filename", "File Name"),
                    ft.dropdown.Option("user_id", "User"),
                    ft.dropdown.Option("file_size", "File Size")
                ],
                on_change=self._on_sort_changed
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table(),
                style=self._get_button_style("secondary")
            )
        ])
    
    def _get_button_style(self, button_type: str):

        border_radius = self.config.get_ui_constant('button_border_radius', 5)
        
        if button_type == "primary":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        elif button_type == "success":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        elif button_type == "danger":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.RED},
                color={ft.ControlState.DEFAULT: ft.Colors.RED,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        else: 
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
    
    def _create_main_content_area(self) -> ft.ResponsiveRow:

        return ft.ResponsiveRow([
            ft.Container(
                content=self._create_files_table_section(),
                col={"sm": 12, "md": 7, "lg": 8},
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=20
            ),
            ft.Container(
                content=self._create_preview_section(),
                col={"sm": 12, "md": 5, "lg": 4},
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=10
            )
        ])
    
    def _create_files_table_section(self) -> ft.Container:
        self.files_table_title = ft.Text("Pending Files", size=20, weight=ft.FontWeight.BOLD)
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
        
        column_configs = {
            "xs": {"file": True, "user": False, "team": False, "size": False, "submitted": False, "status": True},
            "sm": {"file": True, "user": True, "team": False, "size": False, "submitted": False, "status": True},
            "md": {"file": True, "user": True, "team": True, "size": False, "submitted": True, "status": True},
            "lg": {"file": True, "user": True, "team": True, "size": True, "submitted": True, "status": True}
        }

        try:
            min_height = self.config.get_ui_constant('table_row_min_height', 40)
            max_height = self.config.get_ui_constant('table_row_max_height', 50)
        except:
            min_height = 40
            max_height = 50

        self.files_table = ft.DataTable(
            columns=get_columns_for_size(column_configs["lg"]),  # Start with all columns
            rows=[],
            column_spacing=10,
            horizontal_margin=5,
            data_row_max_height=max_height,
            data_row_min_height=min_height,
            expand=True,
        )

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
        self.column_configs = column_configs
        self.get_columns_for_size = get_columns_for_size

        return ft.Container(
            content=ft.Column([
                self.files_table_title, 
                ft.Divider(),
                ft.Container(height=10),
                table_content
            ], expand=True, spacing=0),
            expand=True,
            padding=0
        )

    def update_files_table_title(self, status_label: str):
        """Update the files table title dynamically."""
        # status_label expected like "Pending", "Approved", "Rejected"
        try:
            self.files_table_title.value = f"{status_label} Files"
            self.files_table_title.update()
        except Exception:
            # In case title not initialized yet
            pass

    def _is_admin_user(self) -> bool:
        """Helper to check if current admin_user is an Admin role"""
        try:
            if hasattr(self.permission_service, "is_admin"):
                return bool(self.permission_service.is_admin(self.admin_user))
            # Fallback: check user's teams length or roles via users.json
            return False
        except Exception:
            return False

    def _is_team_leader(self) -> bool:
        """Helper to check if the current user is a team leader (team admin)"""
        try:
            # PermissionService may expose is_team_admin(team) for a team - check any team
            if hasattr(self.permission_service, "is_team_admin"):
                # if they are team admin for any of their teams, consider team leader
                for t in self.admin_teams:
                    try:
                        if self.permission_service.is_team_admin(self.admin_user, t):
                            return True
                    except Exception:
                        continue
            return False
        except Exception:
            return False

    def _get_filtered_approved_files(self) -> List[Dict]:
        """Get approved files with current filters applied"""
        try:
            reviewable_teams = self.permission_service.get_reviewable_teams(
                self.admin_user, self.admin_teams
            )
            all_approved = []
            for team in reviewable_teams:
                try:
                    team_files = self.approval_service.get_approved_files_by_team(team)
                    all_approved.extend(team_files)
                except Exception as team_error:
                    self.enhanced_logger.general_logger.warning(
                        f"Error getting approved files for team {team}: {team_error}"
                    )
            unique_files = {f['file_id']: f for f in all_approved}
            return self._apply_current_filters(list(unique_files.values()))
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting approved files: {e}")
            return []

    def _get_filtered_rejected_files(self) -> List[Dict]:
        """Get rejected files with current filters applied"""
        try:
            reviewable_teams = self.permission_service.get_reviewable_teams(
                self.admin_user, self.admin_teams
            )
            all_rejected = []
            for team in reviewable_teams:
                try:
                    team_files = self.approval_service.get_rejected_files_by_team(team)
                    all_rejected.extend(team_files)
                except Exception as team_error:
                    self.enhanced_logger.general_logger.warning(
                        f"Error getting rejected files for team {team}: {team_error}"
                    )
            unique_files = {f['file_id']: f for f in all_rejected}
            return self._apply_current_filters(list(unique_files.values()))
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting rejected files: {e}")
            return []
    
    def _get_table_columns(self) -> List[ft.DataColumn]:
        size_category = self._get_container_size_category()
        config = self.config.get_column_config(size_category)
        
        columns = []
        if config.get("file", True):
            columns.append(ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("user", True):
            columns.append(ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("team", True):
            columns.append(ft.DataColumn(ft.Text("Team", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("size", True):
            columns.append(ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("submitted", True):
            columns.append(ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)))
        if config.get("status", True):
            columns.append(ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)))
        return columns

    def _create_preview_section(self) -> ft.Container:

        padding = self.config.get_ui_constant('preview_panel_padding', 15)
        self.preview_panel_widget = ft.Column([
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

        return ft.Container(
            content=ft.Container(
                content=self.preview_panel_widget,
                expand=True,
                padding=padding,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_200)
            ),
            expand=True,
            padding=0
        )
    
    def _create_error_interface(self, error_msg: str) -> ft.Container:
        """Create error interface when main interface fails"""
        log_security_event(
            username=self.admin_user,
            event_type="INTERFACE_ERROR",
            details={"error": error_msg},
            severity="ERROR"
        )
        
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
                    on_click=lambda e: self.refresh_interface(),
                    style=self._get_button_style("primary")
                ),
                ft.Container(height=20),
                ft.Text("Please check that all required services are running and data files exist.", 
                       size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            expand=True
        )
    
    def _get_file_counts_safely(self) -> Dict[str, int]:
        """Get file counts with comprehensive error handling and update stat cards if present"""
        try:
            with PerformanceTimer("FileApprovalPanel", "get_file_counts"):
                # Determine role
                is_admin = self._is_admin_user()
                is_tl = self._is_team_leader()

                # Get reviewable teams for this admin
                reviewable_teams = self.permission_service.get_reviewable_teams(
                    self.admin_user, self.admin_teams
                )

                pending_files = set()
                approved_files = set()
                rejected_files = set()

                # Admin sees pending_admin across all teams
                if is_admin:
                    try:
                        admin_pending = self.approval_service.get_pending_admin_files()
                        for file_data in admin_pending:
                            pending_files.add(file_data['file_id'])
                    except Exception as err:
                        self.enhanced_logger.general_logger.warning(f"Error getting admin pending files: {err}")

                # Team leaders see pending_team_leader for their teams
                if is_tl:
                    for team in reviewable_teams:
                        try:
                            team_pending = self.approval_service.get_pending_team_leader_files(team)
                            for file_data in team_pending:
                                pending_files.add(file_data['file_id'])
                        except Exception as team_error:
                            self.enhanced_logger.general_logger.warning(
                                f"Error getting TL pending files for team {team}: {team_error}"
                            )

                # Counts for approved/rejected aggregated per team for reviewable teams
                for team in reviewable_teams:
                    try:
                        team_approved = self.approval_service.get_approved_files_by_team(team)
                        for fd in team_approved:
                            approved_files.add(fd['file_id'])
                    except Exception as team_error:
                        self.enhanced_logger.general_logger.warning(
                            f"Error getting approved files for team {team}: {team_error}"
                        )

                    try:
                        team_rejected = self.approval_service.get_rejected_files_by_team(team)
                        for fd in team_rejected:
                            rejected_files.add(fd['file_id'])
                    except Exception as team_error:
                        self.enhanced_logger.general_logger.warning(
                            f"Error getting rejected files for team {team}: {team_error}"
                        )

                counts = {
                    'pending': len(pending_files),
                    'approved': len(approved_files),
                    'rejected': len(rejected_files)
                }

                # ✅ Update stat card labels if they exist
                try:
                    if hasattr(self, "pending_count_label"):
                        self.pending_count_label.value = str(counts['pending'])
                    if hasattr(self, "approved_count_label"):
                        self.approved_count_label.value = str(counts['approved'])
                    if hasattr(self, "rejected_count_label"):
                        self.rejected_count_label.value = str(counts['rejected'])
                    if hasattr(self, "page"):
                        self.page.update()
                except Exception as update_error:
                    self.enhanced_logger.general_logger.error(
                        f"Error updating stat card labels: {update_error}"
                    )

                # Log performance metric
                from utils.logger import log_performance_metric
                try:
                    log_performance_metric("FileApprovalPanel", "file_counts", 50.0, counts)
                except Exception:
                    pass

                return counts

        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error getting file counts: {e}")
            return {'pending': 0, 'approved': 0, 'rejected': 0}

    
    def _get_approved_files_by_team_safe(self, team: str) -> List[Dict]:
        """Safely get approved files with fallback methods"""
        try:
            return self.approval_service.get_approved_files_by_team(team)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team)
                return [f for f in all_files if f.get('status') == ApprovalStatus.APPROVED]
            except Exception:
                return []
    
    def _get_rejected_files_by_team_safe(self, team: str) -> List[Dict]:
        """Safely get rejected files with fallback methods"""
        try:
            return self.approval_service.get_rejected_files_by_team(team)
        except AttributeError:
            # Fallback to general method
            try:
                all_files = self.approval_service.get_all_files_by_team(team)
                return [f for f in all_files if f.get('status') == ApprovalStatus.REJECTED]
            except Exception:
                return []
    
    def _get_container_size_category(self) -> str:
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
        except Exception:
            return "lg"  # Safe default
    
    def refresh_files_table(self):
        try:
            # Ensure files_table exists before working with it
            if not hasattr(self, "files_table") or self.files_table is None:
                self.enhanced_logger.general_logger.warning(
                    f"Files table not initialized yet for view '{getattr(self, 'current_view', 'unknown')}'."
                )
                return

            # Fallback to "pending" if current_view is not yet set
            view = getattr(self, "current_view", "pending")

            if view == "approved":
                files = self._get_filtered_approved_files()
            elif view == "rejected":
                files = self._get_filtered_rejected_files()
            else:  # default pending
                files = self._get_filtered_pending_files()

            files = self._sort_files(files)

            # Clear and repopulate the table
            self.files_table.rows.clear()
            if not files:
                self._add_empty_table_row()
            else:
                for file_data in files:
                    try:
                        self.files_table.rows.append(self._create_table_row(file_data))
                    except Exception as row_error:
                        self.enhanced_logger.general_logger.error(
                            f"Error creating table row: {row_error}"
                        )
                        continue

            # ✅ Update stat card counts after refreshing table
            self._get_file_counts_safely()

            self.page.update()

        except Exception as e:
            self.enhanced_logger.general_logger.error(
                f"Error refreshing {getattr(self, 'current_view', 'pending')} files table: {e}"
            )
            self._show_table_error(str(e))

    
    def _get_filtered_pending_files(self) -> List[Dict]:
        """Get pending files from NEW data location"""
        try:
            is_admin = self._is_admin_user()
            is_tl = self._is_team_leader()
            
            print(f"[DEBUG] Getting files for {self.admin_user} (admin: {is_admin}, tl: {is_tl})")
            
            files_to_process = []
            
            # Team Leader: get pending_team_leader files
            if is_tl:
                reviewable_teams = self.permission_service.get_reviewable_teams(self.admin_user)
                print(f"[DEBUG] TL teams: {reviewable_teams}")
                
                for team in reviewable_teams:
                    team_files = self.approval_service.get_pending_team_leader_files(team)
                    print(f"[DEBUG] Team {team}: {len(team_files)} pending files")
                    files_to_process.extend(team_files)
            
            # Admin: get pending_admin files  
            if is_admin:
                admin_files = self.approval_service.get_pending_admin_files()
                print(f"[DEBUG] Admin: {len(admin_files)} pending files")
                files_to_process.extend(admin_files)
            
            # Remove duplicates
            unique = {f['file_id']: f for f in files_to_process}
            result = list(unique.values())
            
            print(f"[DEBUG] Final result: {len(result)} files")
            for f in result:
                print(f"[DEBUG]   - {f.get('original_filename')}: {f.get('status')}")
                
            return self._apply_current_filters(result)
            
        except Exception as e:
            print(f"[ERROR] Error getting pending files: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _apply_current_filters(self, files: List[Dict]) -> List[Dict]:
        """Apply current search and team filters to file list"""
        filtered_files = files
        
        # Apply search filter
        if self.search_query:
            search_lower = self.search_query.lower()
            filtered_files = [
                f for f in filtered_files
                if (search_lower in f.get('original_filename', '').lower() or
                    search_lower in f.get('user_id', '').lower() or
                    search_lower in f.get('description', '').lower())
            ]
        
        # Apply team filter
        if self.current_team_filter != "ALL":
            filtered_files = [f for f in filtered_files 
                            if f.get('user_team', '') == self.current_team_filter]
        
        return filtered_files
    
    def _sort_files(self, files: List[Dict]) -> List[Dict]:
        """Sort files based on current sort option"""
        try:
            if self.current_sort == "filename":
                return sorted(files, key=lambda x: x.get('original_filename', '').lower())
            elif self.current_sort == "user_id":
                return sorted(files, key=lambda x: x.get('user_id', '').lower())
            elif self.current_sort == "file_size":
                return sorted(files, key=lambda x: x.get('file_size', 0), reverse=True)
            else:  # submission_date (default)
                return sorted(files, key=lambda x: x.get('submission_date', ''), reverse=True)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error sorting files: {e}")
            return files
    
    def _create_table_row(self, file_data: Dict) -> ft.DataRow:
        """Create table row for file data - Updated for preferred responsiveness"""
        size_category = self._get_container_size_category()
        
        # Use stored column config or fallback
        if hasattr(self, 'column_configs'):
            config = self.column_configs.get(size_category, self.column_configs["lg"])
        else:
            config = self.config.get_column_config(size_category)
        
        # Format file size
        file_size = file_data.get('file_size', 0)
        size_str = self._format_file_size(file_size)
        
        # Format submission date
        try:
            submit_date = datetime.fromisoformat(file_data['submission_date'])
            date_str = submit_date.strftime("%m/%d %H:%M")
        except:
            date_str = "Unknown"
        
        # Get filename with length limit for responsive display
        original_filename = file_data.get('original_filename', 'Unknown')
        max_lengths = {'xs': 15, 'sm': 20, 'md': 25, 'lg': 30}
        max_filename_length = max_lengths.get(size_category, 30)
        display_filename = self._limit_filename_display(original_filename, max_filename_length)
        
        # Build cells based on configuration
        cells = []
        
        if config.get("file", True):
            cells.append(ft.DataCell(
                ft.Text(
                    display_filename,
                    tooltip=original_filename,
                    size=14,
                    overflow=ft.TextOverflow.ELLIPSIS
                )
            ))
        
        if config.get("user", True):
            cells.append(ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'), size=14)))
        
        if config.get("team", True):
            cells.append(ft.DataCell(ft.Text(file_data.get('user_team', 'Unknown'), size=14)))
        
        if config.get("size", True):
            cells.append(ft.DataCell(ft.Text(size_str, size=14)))
        
        if config.get("submitted", True):
            cells.append(ft.DataCell(ft.Text(date_str, size=14)))
        
        # Status display: map internal statuses to UI labels/colors
        status_val = (file_data.get('status') or "").lower()
        status_text = "Unknown"
        status_color = ft.Colors.GREY_600
        status_bg = ft.Colors.GREY_200

        try:
            if status_val == FileApprovalStatus.PENDING_TEAM_LEADER:
                status_text = "Pending (TL)"
                status_color = ft.Colors.WHITE
                status_bg = ft.Colors.ORANGE
            elif status_val == FileApprovalStatus.PENDING_ADMIN:
                status_text = "Pending (Admin)"
                status_color = ft.Colors.WHITE
                status_bg = ft.Colors.ORANGE
            elif status_val == FileApprovalStatus.APPROVED:
                status_text = "Approved"
                status_color = ft.Colors.WHITE
                status_bg = ft.Colors.GREEN
            elif status_val in [FileApprovalStatus.REJECTED_TEAM_LEADER, FileApprovalStatus.REJECTED_ADMIN, FileApprovalStatus.CHANGES_REQUESTED]:
                status_text = "Rejected" if status_val in [FileApprovalStatus.REJECTED_TEAM_LEADER, FileApprovalStatus.REJECTED_ADMIN] else "Changes Requested"
                status_color = ft.Colors.WHITE
                status_bg = ft.Colors.RED
            elif status_val == FileApprovalStatus.WITHDRAWN:
                status_text = "Withdrawn"
                status_color = ft.Colors.BLACK
                status_bg = ft.Colors.GREY_100
            else:
                status_text = status_val.upper() if status_val else "UNKNOWN"
                status_color = ft.Colors.BLACK
                status_bg = ft.Colors.GREY_100
        except Exception:
            status_text = file_data.get('status', 'Unknown')

        if config.get("status", True):
            cells.append(ft.DataCell(ft.Container(
                content=ft.Text(status_text, color=status_color, size=10),
                bgcolor=status_bg,
                padding=ft.padding.symmetric(horizontal=6, vertical=3),
                border_radius=4
            )))

        return ft.DataRow(
            cells=cells,
            on_select_changed=lambda e, data=file_data: self.select_file(data)
        )
    
    def _limit_filename_display(self, filename: str, max_length: int) -> str:
        """Limit filename display length for responsive table"""
        if len(filename) <= max_length:
            return filename
        
        if max_length > 10:
            start_len = max_length // 2 - 2
            end_len = max_length - start_len - 3
            return f"{filename[:start_len]}...{filename[-end_len:]}"
        else:
            return filename[:max_length-3] + "..."
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def _add_empty_table_row(self):
        """Add empty table row when no files are found - Updated for dynamic columns"""
        # Determine how many columns are currently visible
        num_columns = len(self.files_table.columns)
        
        empty_cells = []
        # First cell shows the message
        empty_cells.append(ft.DataCell(
            ft.Text("No files found for this view", style=ft.TextStyle(italic=True))
        ))
        
        # Add empty cells for remaining columns
        for i in range(num_columns - 1):
            empty_cells.append(ft.DataCell(ft.Text("")))
        
        self.files_table.rows.append(ft.DataRow(cells=empty_cells))
    
    def _show_table_error(self, error_msg: str):
        """Show error message in the table"""
        self.files_table.rows.clear()
        
        error_cells = [ft.DataCell(ft.Text(f"Error loading files: {error_msg}", color=ft.Colors.RED))]
        for i in range(len(self.files_table.columns) - 1):
            error_cells.append(ft.DataCell(ft.Text("")))
        
        self.files_table.rows.append(ft.DataRow(cells=error_cells))
        self.page.update()
    
    def select_file(self, file_data: Dict):
        """Select a file for review with validation"""
        try:
            # Validate file data
            if not file_data or 'file_id' not in file_data:
                self.enhanced_logger.general_logger.warning("Invalid file data provided for selection")
                return
            
            self.selected_file = file_data
            self._update_preview_panel()
            
            # Log file selection
            log_file_operation(
                username=self.admin_user,
                operation="SELECT_FILE",
                file_path=file_data.get('original_filename', 'unknown'),
                result="SUCCESS",
                details={"file_id": file_data.get('file_id')}
            )
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error selecting file: {e}")
            self._show_snackbar("Error selecting file", ft.Colors.RED)
    
    def _update_preview_panel(self):
        """Update the preview panel with selected file info - FIXED alignment"""
        if not self.selected_file:
            return
        
        try:
            file_data = self.selected_file
            
            # Load comments for this file
            try:
                comments = self.approval_service.load_comments().get(file_data['file_id'], [])
            except Exception:
                comments = []
            
            # Create file preview content
            preview_content = self._create_file_preview(file_data, comments)
            
            # Update the preview panel widget
            self.preview_panel_widget.controls.clear()
            self.preview_panel_widget.controls.extend(preview_content)
            
            # FIXED: Change alignment when content is loaded (left-align content)
            self.preview_panel_widget.horizontal_alignment = ft.CrossAxisAlignment.START
            self.preview_panel_widget.alignment = ft.MainAxisAlignment.START
            
            self.page.update()
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error updating preview panel: {e}")
            self._show_snackbar("Error loading file preview", ft.Colors.RED)

    def _create_file_preview(self, file_data: Dict, comments: List[Dict]) -> List:
        """Create file preview content - FIXED with left-aligned layout"""
        # Format submission date
        submit_date = "Unknown"
        try:
            submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
        except (ValueError, KeyError, TypeError):
            pass
        
        file_size = self._format_file_size(file_data.get('file_size', 0))
        
        # Create comment and reason fields
        comment_field = ft.TextField(
            label="Add comment",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            expand=True  # Make comment field expand to fill width
        )
        
        reason_field = ft.TextField(
            label="Reason for rejection",
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=14,
            expand=True  # Make reason field expand to fill width
        )
        
        # FIXED: File information section with left alignment
        file_info = [
            ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            # FIXED: Left-aligned file details instead of centered
            ft.Column([
                ft.Text(f"File name: {file_data.get('original_filename', 'Unknown')}", 
                       size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"User: {file_data.get('user_id', 'Unknown')}", size=14),
                ft.Text(f"Team: {file_data.get('user_team', 'Unknown')}", size=14),
                ft.Text(f"Size: {file_size}", size=14),
                ft.Text(f"Submitted: {submit_date}", size=14),
            ], spacing=5, alignment=ft.MainAxisAlignment.START),  # Left-aligned
            
            ft.Container(height=10),
            ft.Text("Description:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(file_data.get('description', 'No description provided'), 
                   size=12, color=ft.Colors.GREY_600),
            ft.Container(height=10),
            ft.Text("Tags:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(', '.join(file_data.get('tags', [])) or 'No tags', 
                   size=12, color=ft.Colors.GREY_600),
            
            # Download and Open buttons - keep centered for better UX
            ft.Container(height=15),
            ft.Row([
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Open",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: self._handle_open_file(file_data),
                    style=self._get_button_style("success")
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ]

        # Comments section with left alignment
        comment_controls = []
        if comments:
            for comment in comments:
                comment_controls.append(
                    ft.Text(f"{comment.get('admin_id', 'Unknown')}: {comment.get('comment', '')}", size=14)
                )
        else:
            comment_controls.append(ft.Text("No comments yet", size=14, color=ft.Colors.GREY_500))
        
        comments_section = [
            ft.Text("Comments", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(comment_controls, alignment=ft.MainAxisAlignment.START),  # Left-aligned comments
                height=100,
                bgcolor=ft.Colors.GREY_50,
                padding=10,
                border_radius=4,
                alignment=ft.alignment.center_left  # Left-align container content
            )
        ]
        
        # Actions section with left-aligned Add Comment button
        actions_section = [
            ft.Text("Actions", size=16, weight=ft.FontWeight.BOLD),
            comment_field,
            ft.Container(height=5),
            ft.Row([
                ft.ElevatedButton(
                    "Add Comment",
                    icon=ft.Icons.COMMENT,
                    on_click=lambda e: self._handle_add_comment(file_data, comment_field),
                    style=self._get_button_style("primary")
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Container(height=10),
            ft.Divider(),
            ft.Container(height=10),
            reason_field,
            ft.Container(height=10),
            
            # Approve/Reject buttons
            ft.Row([
                ft.ElevatedButton(
                    "Approve",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=lambda e: self._handle_approve_file(file_data),
                    style=self._get_button_style("success")
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Reject",
                    icon=ft.Icons.CANCEL,
                    on_click=lambda e: self._handle_reject_file(file_data, reason_field),
                    style=self._get_button_style("danger")
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        ]
        
        return file_info + [ft.Divider()] + comments_section + [ft.Divider()] + actions_section

    # Event handlers for UI components
    def _on_search_changed(self, e):
        """Handle search input change"""
        try:
            self.search_query = e.control.value.lower()
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling search change: {error}")
    
    def _on_team_filter_changed(self, e):
        """Handle team filter change"""
        try:
            self.current_team_filter = e.control.value
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling team filter change: {error}")
    
    def _on_sort_changed(self, e):
        """Handle sort option change"""
        try:
            self.current_sort = e.control.value
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling sort change: {error}")
    
    # File operation handlers with enhanced security
    def _handle_download_file(self, file_data: Dict):
        """Handle file download with security validation"""
        try:
            # Extract and validate file information
            file_id = file_data.get('file_id')
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not all([file_id, user_id, original_filename]):
                raise ValueError("Missing required file information")
            
            # Use your enhanced file manager for secure resolution
            resolved_path = self.file_manager.resolve_file_path(user_id, file_id, original_filename)
            
            if not resolved_path:
                self._show_snackbar("File not found in storage", ft.Colors.RED)
                log_file_operation(self.admin_user, "DOWNLOAD", original_filename, "FAILED", 
                                 {"reason": "file_not_found", "file_id": file_id})
                return
            
            # Get safe download path
            download_path = self.file_manager.get_safe_download_path(original_filename)
            
            # Copy file securely
            shutil.copy2(resolved_path, download_path)
            
            self._show_snackbar(f"Downloaded: {original_filename}", ft.Colors.GREEN)
            log_file_operation(self.admin_user, "DOWNLOAD", original_filename, "SUCCESS", 
                             {"download_path": str(download_path), "file_id": file_id})
            
        except (SecurityError, ValueError) as e:
            log_security_event(self.admin_user, "FILE_DOWNLOAD_VIOLATION", 
                             {"error": str(e), "file_data": file_data}, "WARNING")
            self._show_snackbar("Invalid file operation request", ft.Colors.RED)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error downloading file: {e}")
            self._show_snackbar("Error downloading file", ft.Colors.RED)
    
    def _handle_open_file(self, file_data: Dict):
        """Handle file opening with security validation"""
        try:
            # Extract and validate file information
            file_id = file_data.get('file_id')
            user_id = file_data.get('user_id')
            original_filename = file_data.get('original_filename')
            
            if not all([file_id, user_id, original_filename]):
                raise ValueError("Missing required file information")
            
            # Use your enhanced file manager for secure resolution
            resolved_path = self.file_manager.resolve_file_path(user_id, file_id, original_filename)
            
            if not resolved_path:
                self._show_snackbar("File not found in storage", ft.Colors.RED)
                log_file_operation(self.admin_user, "OPEN", original_filename, "FAILED", 
                                 {"reason": "file_not_found", "file_id": file_id})
                return
            
            # Open with system default application
            self._open_file_with_system_default(resolved_path)
            
            self._show_snackbar(f"Opening: {original_filename}", ft.Colors.BLUE)
            log_file_operation(self.admin_user, "OPEN", original_filename, "SUCCESS", 
                             {"file_id": file_id})
            
        except (SecurityError, ValueError) as e:
            log_security_event(self.admin_user, "FILE_OPEN_VIOLATION", 
                             {"error": str(e), "file_data": file_data}, "WARNING")
            self._show_snackbar("Invalid file operation request", ft.Colors.RED)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error opening file: {e}")
            self._show_snackbar("Error opening file", ft.Colors.RED)
    
    def _open_file_with_system_default(self, file_path: Path):
        """Open file with system default application"""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(str(file_path))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)], check=True)
            else:  # Linux and others
                subprocess.run(["xdg-open", str(file_path)], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to open file with system application: {e}")
        except Exception as e:
            raise RuntimeError(f"Error opening file: {e}")
    
    def _handle_add_comment(self, file_data: Dict, comment_field: ft.TextField):
        """Handle adding comment to file"""
        try:
            if not file_data or not comment_field.value:
                self._show_snackbar("Please enter a comment", ft.Colors.ORANGE)
                return
            
            comment_text = comment_field.value.strip()
            if not comment_text:
                self._show_snackbar("Comment cannot be empty", ft.Colors.ORANGE)
                return
            
            # Add comment through service
            success = self.approval_service.add_comment(
                file_data['file_id'],
                self.admin_user,
                comment_text
            )
            
            if success:
                # Send notification to user
                try:
                    self.notification_service.notify_comment_added(
                        file_data['user_id'],
                        file_data['original_filename'],
                        self.admin_user,
                        comment_text
                    )
                except Exception:
                    pass
                
                comment_field.value = ""
                self._show_snackbar("Comment added and user notified!", ft.Colors.GREEN)
                self._update_preview_panel()
                
                # Log comment action
                log_approval_action(self.admin_user, file_data['user_id'], 
                                  file_data['file_id'], "COMMENT", comment_text)
                
            else:
                self._show_snackbar("Failed to add comment", ft.Colors.RED)
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error adding comment: {e}")
            self._show_snackbar("Error adding comment", ft.Colors.RED)
    
    def _handle_approve_file(self, file_data: Dict):
        """Handle file approval - role-aware (Team Leader vs Admin)"""
        try:
            if not file_data:
                return
            
            file_id = file_data.get('file_id')
            status = file_data.get('status', '').lower()
            success = False
            
            # Determine action based on current status and user role
            if status == FileApprovalStatus.PENDING_TEAM_LEADER:
                # Team Leader approval: Stage 1 → Stage 2
                try:
                    success = self.approval_service.team_leader_approve(file_id, self.admin_user)
                    action_message = "forwarded to Admin"
                except Exception as e:
                    print(f"Error in team leader approve: {e}")
                    success = False
                    
            elif status == FileApprovalStatus.PENDING_ADMIN:
                # Admin approval: Stage 2 → Stage 3 (final)
                try:
                    success = self.approval_service.approve_by_admin(file_id, self.admin_user)
                    action_message = "given final approval"
                except Exception as e:
                    print(f"Error in admin approve: {e}")
                    success = False
            else:
                self._show_snackbar(f"Cannot approve file with status: {status}", ft.Colors.RED)
                return
            
            if success:
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' {action_message}!", ft.Colors.GREEN)
                
                # Send notification to user
                try:
                    self.notification_service.notify_approval_status(
                        file_data['user_id'],
                        filename,
                        FileApprovalStatus.PENDING_ADMIN if status == FileApprovalStatus.PENDING_TEAM_LEADER else FileApprovalStatus.APPROVED,
                        self.admin_user
                    )
                except Exception as e:
                    print(f"Error sending notification: {e}")
                
                # Log the action
                from utils.logger import log_approval_action
                log_approval_action(self.admin_user, file_data['user_id'], 
                                file_id, "APPROVE", action_message)
                
                # Clear selection and refresh
                self._clear_selection()
                self.refresh_files_table()
                
            else:
                self._show_snackbar("Failed to approve file", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self._show_snackbar("Error approving file", ft.Colors.RED)
    
    def _handle_reject_file(self, file_data: Dict, reason_field: ft.TextField):
        """Handle file rejection with confirmation dialog (role-aware)"""
        try:
            if not file_data:
                return
            
            if not reason_field.value or not reason_field.value.strip():
                self._show_snackbar("Please provide a reason for rejection", ft.Colors.ORANGE)
                return
            
            rejection_reason = reason_field.value.strip()
            filename = file_data.get('original_filename', 'Unknown')
            
            # Use your existing dialog utility for confirmation
            show_confirm_dialog(
                self.page,
                "Confirm Rejection",
                f"Are you sure you want to reject '{filename}'?\n\nReason: {rejection_reason}",
                lambda: self._execute_file_rejection(file_data, rejection_reason)
            )
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error handling file rejection: {e}")
            self._show_snackbar("Error processing file rejection", ft.Colors.RED)
    
    def _execute_file_rejection(self, file_data: Dict, rejection_reason: str):
        """Execute the actual file rejection after confirmation (role-aware)"""
        try:
            status = (file_data.get('status') or "").lower()
            success = False

            # For pending TL files, TL rejects via team_leader_reject
            if status == FileApprovalStatus.PENDING_TEAM_LEADER:
                try:
                    success = self.approval_service.team_leader_reject(file_data['file_id'], self.admin_user, rejection_reason, False)
                except Exception as e:
                    print(f"Error in team leader reject: {e}")
                    success = False

            # For pending admin files, admin rejects via reject_by_admin
            elif status == FileApprovalStatus.PENDING_ADMIN:
                try:
                    success = self.approval_service.reject_by_admin(file_data['file_id'], self.admin_user, rejection_reason, False)
                except Exception as e:
                    print(f"Error in admin reject: {e}")
                    success = False
            else:
                # fallback to generic reject
                try:
                    success = self.approval_service.reject_by_admin(file_data['file_id'], self.admin_user, rejection_reason, False)
                except Exception:
                    success = False

            if success:
                # Send notification to user
                try:
                    self.notification_service.notify_approval_status(
                        file_data['user_id'],
                        file_data['original_filename'],
                        FileApprovalStatus.REJECTED_ADMIN if status == FileApprovalStatus.PENDING_ADMIN else FileApprovalStatus.REJECTED_TEAM_LEADER,
                        self.admin_user,
                        rejection_reason
                    )
                except Exception:
                    pass
                
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' rejected!", ft.Colors.RED)
                
                # Log rejection action
                log_approval_action(self.admin_user, file_data['user_id'], 
                                  file_data['file_id'], "REJECT", rejection_reason)
                
                # Clear selection and refresh
                self._clear_selection()
                self.refresh_files_table()
                self.refresh_interface()
                
            else:
                self._show_snackbar("Failed to reject file", ft.Colors.RED)
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error executing file rejection: {e}")
            self._show_snackbar("Error rejecting file", ft.Colors.RED)
    
    def _clear_selection(self):
        """Clear current file selection - FIXED to restore center alignment for empty state"""
        self.selected_file = None
        
        # Reset preview panel to empty state
        self.preview_panel_widget.controls.clear()
        self.preview_panel_widget.controls.extend([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ])
        
        # FIXED: Restore center alignment for empty state
        self.preview_panel_widget.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.preview_panel_widget.alignment = ft.MainAxisAlignment.CENTER
        self.preview_panel_widget.scroll = ft.ScrollMode.AUTO

    def _handle_tl_approve(self, file_data):
        file_id = file_data['file_id']
        ok = self.approval_service.team_leader_approve(file_id, self.admin_user)
        if ok:
            # notify user, refresh table, etc.
            self._show_snackbar("Forwarded to admin", ft.Colors.GREEN)
            self.refresh_files_table()
    
    def refresh_interface(self):
        """Refresh the entire interface"""
        try:
            with PerformanceTimer("FileApprovalPanel", "refresh_interface"):
                # Refresh files table and preview
                self.refresh_files_table()
                self._update_preview_panel()
                
                # Invalidate file manager cache to ensure fresh data
                try:
                    self.file_manager.invalidate_cache()
                except Exception:
                    pass
                
                # Update page
                self.page.update()
            
            self.enhanced_logger.general_logger.info("Interface refreshed successfully")
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error refreshing interface: {e}")
            self._show_snackbar("Error refreshing interface", ft.Colors.RED)
    
    def _show_snackbar(self, message: str, color: str):
        """Show snackbar message with enhanced styling"""
        try:
            # Determine icon based on color
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
            
            # Log the message using your existing logger
            getattr(self.enhanced_logger.general_logger, log_level)(f"User notification: {message}")
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error showing snackbar: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get file manager cache statistics for debugging"""
        return self.file_manager.get_cache_stats()
    
    def get_security_stats(self) -> Dict:
        """Get security statistics for monitoring"""
        return self.enhanced_auth.get_security_stats()
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed"""
        try:
            if hasattr(self, 'file_manager'):
                try:
                    self.file_manager.invalidate_cache()
                except Exception:
                    pass
            
            # Use your existing logger for cleanup activity
            from utils.logger import log_action
            try:
                log_action(self.admin_user, "File approval panel session ended")
            except Exception:
                pass
            
            self.enhanced_logger.general_logger.info("File approval panel cleanup completed")
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error during cleanup: {e}")

    
           
