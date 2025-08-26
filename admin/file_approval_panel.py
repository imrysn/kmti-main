import flet as ft
from typing import Dict, List, Optional
from utils.config_loader import get_config
from utils.file_manager import get_file_manager, SecurityError
from utils.logger import get_enhanced_logger, log_file_operation, PerformanceTimer
from utils.auth import get_enhanced_authenticator

# Import component modules
from admin.components.approval_actions import ApprovalActionHandler
from admin.components.table_helpers import TableHelper, FileFilter
from admin.components.file_utils import FileOperationHandler
from admin.components.ui_helpers import UIComponentHelper, TeamLoader, create_snackbar_helper
from admin.components.preview_panel import PreviewPanelManager, create_preview_section_container
from admin.components.data_managers import FileDataManager, StatisticsManager, ServiceInitializer, cleanup_resources
from admin.components.role_permissions import RoleValidator


class EnhancedFileApprovalPanel:
    """Enhanced File Approval Panel with dynamic filtering and statistics synchronization."""
    
    def __init__(self, page: ft.Page, admin_user: str):
        self.page = page
        
        # Initialize core services
        self._initialize_core_services()
        
        # Validate and set admin user
        try:
            self.admin_user = self.enhanced_auth.sanitize_username(admin_user)
        except SecurityError as e:
            self.enhanced_logger.security_logger.error(f"Invalid admin user ID: {e}")
            raise ValueError(f"Invalid admin user: {admin_user}")
        
        # Initialize role validator
        self.role_validator = RoleValidator()
        
        # Initialize services and data
        self._initialize_services_and_data()
        
        # Initialize component helpers
        self._initialize_component_helpers()
        
        # Initialize UI state with enhanced filtering
        self._initialize_ui_state()
        
        # Store current filtered files for dynamic statistics
        self.current_filtered_files = []
        
        # Statistics card references for dynamic updates
        self.stat_pending_card = None
        self.stat_approved_card = None
        self.stat_rejected_card = None
        
        self.enhanced_logger.general_logger.info(
            f"Enhanced file approval panel initialized for admin: {self.admin_user}")
    
    def _initialize_core_services(self):
        """Initialize core services and utilities."""
        self.config = get_config()
        self.file_manager = get_file_manager()
        self.enhanced_logger = get_enhanced_logger()
        self.enhanced_auth = get_enhanced_authenticator()
    
    def _initialize_services_and_data(self):
        """Initialize services and get admin data."""
        # Initialize services
        service_initializer = ServiceInitializer(self.enhanced_logger)
        services = service_initializer.initialize_services()
        
        self.approval_service = services['approval_service']
        self.permission_service = services['permission_service']
        self.notification_service = services['notification_service']
        
        # Get admin data
        data_manager = FileDataManager(
            self.approval_service, self.permission_service, self.enhanced_logger)
        
        self.admin_teams = data_manager.get_admin_teams_safely(
            self.admin_user, self.permission_service)
        self.admin_role = self.permission_service.get_user_role(self.admin_user)
        
        # Validate role access to file approval panel
        access_validation = self.role_validator.validate_file_approval_access(
            self.admin_role, self.admin_teams)
        
        if not access_validation['has_access']:
            raise ValueError(f"Access denied: {access_validation['reason']}")
        
        self.access_level = access_validation['access_level']
        
        # Initialize statistics manager
        self.stats_manager = StatisticsManager(self.file_manager, self.enhanced_auth)
    
    def _initialize_component_helpers(self):
        """Initialize component helper classes."""
        # Services dictionary for handlers
        services_dict = {
            'approval_service': self.approval_service,
            'notification_service': self.notification_service,
            'enhanced_logger': self.enhanced_logger
        }
        
        # Initialize component helpers
        self.ui_helper = UIComponentHelper(
            self.config, self.enhanced_auth, self.enhanced_logger)
        self.table_helper = TableHelper(self.config, self.enhanced_logger)
        self.file_filter = FileFilter(self.enhanced_logger)
        self.approval_handler = ApprovalActionHandler(
            self.page, self.admin_user, services_dict)
        self.file_handler = FileOperationHandler(
            self.admin_user, self.file_manager, self.enhanced_logger)
        self.preview_manager = PreviewPanelManager(
            self.config, self.approval_service)
        self.team_loader = TeamLoader(
            self.enhanced_auth, self.enhanced_logger, self.permission_service)
        
        # Create snackbar helper
        self.show_snackbar = create_snackbar_helper(self.page, self.enhanced_logger)
        
        # Initialize data manager
        self.data_manager = FileDataManager(
            self.approval_service, self.permission_service, self.enhanced_logger)
    
    def _initialize_ui_state(self):
        """Initialize UI state variables with enhanced filtering options."""
        self.selected_file = None
        self.files_table = None
        self.preview_panel_widget = None
        self.current_team_filter = "ALL"
        self.current_sort = "submission_date"
        self.search_query = ""
        self.current_status_filter = "ALL"
        self.current_view_mode = "pending_admin"  # For admins, default to files pending admin review
    
    def create_approval_interface(self) -> ft.Container:
        """Create the enhanced approval interface."""
        try:
            with PerformanceTimer("EnhancedFileApprovalPanel", "create_interface"):
                header = self._create_header_section()
                filters = self._create_filters_section()
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
        """Create header section with dynamic statistics."""
        # Initialize with default counts
        file_counts = self.data_manager.get_file_counts_safely(
            self.admin_user, self.admin_teams, self.admin_role)
        
        # Create stat cards and store references for dynamic updates
        self.stat_pending_card = self._create_stat_card("Pending", 
                                   str(file_counts['pending']), ft.Colors.ORANGE)
        self.stat_approved_card = self._create_stat_card("Approved", 
                                   str(file_counts['approved']), ft.Colors.GREEN)
        self.stat_rejected_card = self._create_stat_card("Rejected", 
                                   str(file_counts['rejected']), ft.Colors.RED)
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval - Admin ", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Managing approvals for: {', '.join(self.admin_teams)} FILES", 
                           size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"Role: {self.admin_role or 'Unknown'} | Access: {self.access_level or 'Unknown'}", 
                           size=14, color=ft.Colors.GREY_500)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self.stat_pending_card,
                    ft.Container(width=15),
                    self.stat_approved_card,
                    ft.Container(width=15),
                    self.stat_rejected_card
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=10)
        )
    
    def _create_stat_card(self, label: str, value: str, color: str) -> ft.Container:
        """Create statistics card."""
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=14, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=120,
            height=80,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )
        )
    
    def _create_filters_section(self) -> ft.Container:
        """Create enhanced filters section with padding."""
        teams = self.team_loader.load_teams_safely(self.admin_user, self.admin_teams)
        
        return ft.Container(
            content=ft.Row(
                [
                    # Search field
                    ft.TextField(
                        hint_text="Search files...",
                        width=200,
                        value=self.search_query,
                        on_change=self._on_search_changed,
                        prefix_icon=ft.Icons.SEARCH
                    ),

                    # Team filter with real teams
                    ft.Dropdown(
                        label="Filter by Team",
                        width=160,
                        options=self._create_team_filter_options(teams),
                        value=self.current_team_filter,
                        on_change=self._on_team_filter_changed
                    ),

                    # Status filter
                    ft.Dropdown(
                        label="Status",
                        width=160,
                        value=self.current_status_filter,
                        options=[
                            ft.dropdown.Option("ALL", "All Status"),
                            ft.dropdown.Option("pending_admin", "Pending Admin"),
                            ft.dropdown.Option("approved", "Approved"),
                            ft.dropdown.Option("rejected_admin", "Rejected")
                        ],
                        on_change=self._on_status_filter_changed
                    ),

                    # Sort selector
                    ft.Dropdown(
                        label="Sort by",
                        width=150,
                        value=self.current_sort,
                        options=[
                            ft.dropdown.Option("submission_date", "Date Submitted"),
                            ft.dropdown.Option("original_filename", "File Name"),
                            ft.dropdown.Option("user_id", "User"),
                            ft.dropdown.Option("file_size", "File Size")
                        ],
                        on_change=self._on_sort_changed
                    ),

                    ft.Container(expand=True),

                    # Status indicator
                    ft.Container(
                        content=ft.Text(
                            f"Showing: {self._get_view_description()}",
                            size=16,
                            color=ft.Colors.GREY_600
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                        border_radius=5
                    ),

                    # Refresh button
                    ft.ElevatedButton(
                        "Refresh",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: self.refresh_files_table(),
                        style=self._get_button_style("secondary")
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=15,
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=8), 
        )

    
    def _create_team_filter_options(self, teams: List[str]) -> List[ft.dropdown.Option]:
        """Create team filter dropdown options."""
        options = [ft.dropdown.Option("ALL", "All Teams")]
        for team in teams:
            options.append(ft.dropdown.Option(team, team))
        return options
    
    def _get_view_description(self) -> str:
        """Get description of current view."""
        if self.current_team_filter != "ALL":
            team_desc = f"Team {self.current_team_filter}"
        else:
            team_desc = "All teams"
        
        if self.current_status_filter != "ALL":
            status_desc = f", {self.current_status_filter} status"
        else:
            status_desc = ""
        
        return f"{team_desc}{status_desc}"
    
    def _create_main_content_area(self) -> ft.ResponsiveRow:
        """Create main content area with individually scrollable sections."""
        return ft.ResponsiveRow([
            # Left: Files table - individually scrollable
            ft.Container(
                content=ft.Column([
                    self._create_files_table_section()
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                col={"xs": 12, "sm": 12, "md": 7, "lg": 8, "xl": 8},
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=20,
                expand=True,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )
            ),
            
            # Right: Preview and actions - individually scrollable
            ft.Container(
                content=ft.Column([
                    self._create_preview_section()
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                col={"xs": 12, "sm": 12, "md": 5, "lg": 4, "xl": 4},
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=10,
                expand=True,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    )
            )
        ], expand=True)
    
    def _create_files_table_section(self) -> ft.Container:
        """Create files table section with dynamic responsive columns."""
        
        # Define columns that will be shown based on container size - similar to TLPanel
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
        column_configs = {
            "xs": {"file": True, "user": False, "team": False, "size": False, "submitted": False, "status": True},
            "sm": {"file": True, "user": True, "team": False, "size": False, "submitted": False, "status": True},
            "md": {"file": True, "user": True, "team": True, "size": False, "submitted": True, "status": True},
            "lg": {"file": True, "user": True, "team": True, "size": True, "submitted": True, "status": True}
        }
        
        # Create responsive data table
        self.files_table = self.table_helper.create_responsive_table(self.select_file)
        
        # Override columns with responsive configuration
        self.files_table.columns = get_columns_for_size(column_configs["lg"])
        
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
        
        # Initial table population
        self.refresh_files_table()
        
        # Store column configs for use in refresh method
        self.column_configs = column_configs
        self.get_columns_for_size = get_columns_for_size
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{self._get_view_description()}", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Text(f"Access Level: {self.access_level}", size=16, color=ft.Colors.GREY_600)
                ]),
                ft.Divider(),
                ft.Container(height=10),
                # Create scrollable table container
                ft.Container(
                    content=ft.Column([
                        table_content  # Use responsive approach
                    ], scroll=ft.ScrollMode.AUTO),
                    expand=True
                )
            ], expand=True, spacing=0),
            expand=True,
            padding=0
        )
    
    def _create_preview_section(self) -> ft.Container:
        """Create preview section."""
        self.preview_panel_widget = self.preview_manager.create_empty_preview_panel()
        return create_preview_section_container(self.preview_panel_widget, self.config)
    
    def _create_error_interface(self, error_msg: str) -> ft.Container:
        """Create error interface when main interface fails."""
        return self.ui_helper.create_error_interface(
            error_msg, self.admin_user, lambda e: self.refresh_interface()
        )
    
    def refresh_files_table(self):
        """Refresh the files table with enhanced filtering and dynamic statistics."""
        try:
            with PerformanceTimer("EnhancedFileApprovalPanel", "refresh_files_table"):
                # Get files based on role and filters
                if self.admin_role.upper() == 'ADMIN':
                    # Admin sees files based on status filter
                    if self.current_status_filter == "ALL":
                        all_files = self.data_manager.get_all_files_for_admin(
                            self.admin_user, self.admin_teams, None)  # Get all files
                    elif self.current_status_filter == "pending_admin":
                        all_files = self.data_manager._get_admin_pending_files(
                            self.admin_user, self.admin_teams)
                    elif self.current_status_filter == "approved":
                        all_files = self.data_manager._get_admin_approved_files(
                            self.admin_user, self.admin_teams)
                    elif self.current_status_filter == "rejected_admin":
                        all_files = self.data_manager._get_admin_rejected_files(
                            self.admin_user, self.admin_teams)
                    else:
                        all_files = self.data_manager.get_all_files_for_admin(
                            self.admin_user, self.admin_teams, self.current_status_filter)
                else:
                    # Team leaders and others
                    all_files = self.data_manager.get_filtered_pending_files(
                        self.admin_user, self.admin_teams, self.admin_role)
                
                # Apply team filter
                if self.current_team_filter != "ALL":
                    all_files = [f for f in all_files 
                                if f.get('user_team', '') == self.current_team_filter]
                
                # Apply search filter
                if self.search_query:
                    search_lower = self.search_query.lower()
                    all_files = [
                        f for f in all_files
                        if (search_lower in f.get('original_filename', '').lower() or
                            search_lower in f.get('user_id', '').lower() or
                            search_lower in f.get('description', '').lower())
                    ]
                
                # Apply sorting
                filtered_files = self._sort_files(all_files)
                
                # Store current filtered files for statistics
                self.current_filtered_files = filtered_files
                
                # Update statistics cards dynamically
                self._update_statistics_cards()
                
                # Clear and populate table
                self.files_table.rows.clear()
                
                if not filtered_files:
                    self.table_helper.add_empty_table_row(self.files_table)
                else:
                    size_category = self.table_helper.get_size_category_from_page_width(
                        self.page.width)
                    
                    for file_data in filtered_files:
                        try:
                            row = self.table_helper.create_table_row(
                                file_data, size_category, self.select_file)
                            self.files_table.rows.append(row)
                        except Exception as row_error:
                            self.enhanced_logger.general_logger.error(
                                f"Error creating table row: {row_error}")
                            continue
                
                self.page.update()
                self.enhanced_logger.general_logger.debug(
                    f"Files table refreshed with {len(filtered_files)} files")
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error refreshing files table: {e}")
            self.table_helper.show_table_error(self.files_table, str(e))
    
    def _update_statistics_cards(self):
        """Update statistics cards with current filtered files."""
        try:
            # Calculate dynamic counts from current filtered files
            dynamic_counts = self.data_manager.get_file_counts_safely(
                self.admin_user, self.admin_teams, self.admin_role, self.current_filtered_files)
            
            # Update stat card values
            if self.stat_pending_card:
                self.stat_pending_card.content.controls[0].value = str(dynamic_counts['pending'])
            if self.stat_approved_card:
                self.stat_approved_card.content.controls[0].value = str(dynamic_counts['approved'])
            if self.stat_rejected_card:
                self.stat_rejected_card.content.controls[0].value = str(dynamic_counts['rejected'])
                
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error updating statistics cards: {e}")
    
    def _sort_files(self, files: List[Dict]) -> List[Dict]:
        """Sort files based on current sort option."""
        try:
            if self.current_sort == "original_filename":
                return sorted(files, key=lambda x: x.get('original_filename', '').lower())
            elif self.current_sort == "user_id":
                return sorted(files, key=lambda x: x.get('user_id', '').lower())
            elif self.current_sort == "file_size":
                return sorted(files, key=lambda x: x.get('file_size', 0), reverse=True)
            else:  # submission_date
                return sorted(files, key=lambda x: x.get('submission_date', ''), reverse=True)
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error sorting files: {e}")
            return files
    
    def select_file(self, file_data: Dict):
        """Select a file for review with validation."""
        try:
            if not file_data or 'file_id' not in file_data:
                self.enhanced_logger.general_logger.warning(
                    "Invalid file data provided for selection")
                return
            
            self.selected_file = file_data
            self._update_preview_panel()

            log_file_operation(
                username=self.admin_user,
                operation="SELECT_FILE",
                file_path=file_data.get('original_filename', 'unknown'),
                result="SUCCESS",
                details={"file_id": file_data.get('file_id')}
            )
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error selecting file: {e}")
            self.show_snackbar("Error selecting file", "red")
    
    def _update_preview_panel(self):
        """Update the preview panel with selected file info."""
        if not self.selected_file:
            return
        
        try:
            self.preview_manager.update_preview_panel(
                self.preview_panel_widget, self.selected_file,
                self.approval_handler, self.file_handler, self.show_snackbar,
                self._get_button_style, self._get_refresh_callback()
            )
            self.page.update()
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error updating preview panel: {e}")
            self.show_snackbar("Error loading file preview", "red")
    
    def _get_refresh_callback(self):
        """Get refresh callback function."""
        def refresh():
            self._clear_selection()
            self.refresh_files_table()
            self.refresh_interface()
        return refresh
    
    def _clear_selection(self):
        """Clear current file selection."""
        self.selected_file = None
        self.preview_manager.clear_preview_panel(self.preview_panel_widget)
    
    def refresh_interface(self):
        """Refresh the entire interface."""
        try:
            with PerformanceTimer("EnhancedFileApprovalPanel", "refresh_interface"):
                self.refresh_files_table()
                self._update_preview_panel()
                self.file_manager.invalidate_cache()
                self.page.update()
            
            self.enhanced_logger.general_logger.info("Interface refreshed successfully")
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error refreshing interface: {e}")
            self.show_snackbar("Error refreshing interface", "red")
    
    def _get_button_style(self, button_type: str):
        """Get button style."""
        return self.ui_helper.get_button_style(button_type)
    
    # Event handlers
    def _on_search_changed(self, e):
        """Handle search input change."""
        try:
            self.search_query = e.control.value.lower()
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling search change: {error}")
    
    def _on_team_filter_changed(self, e):
        """Handle team filter change."""
        try:
            self.current_team_filter = e.control.value
            self._clear_selection()  # Clear selection when changing filters
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling team filter change: {error}")
    
    def _on_status_filter_changed(self, e):
        """Handle status filter change."""
        try:
            self.current_status_filter = e.control.value
            self._clear_selection()  # Clear selection when changing filters
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling status filter change: {error}")
    
    def _on_sort_changed(self, e):
        """Handle sort option change."""
        try:
            self.current_sort = e.control.value
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling sort change: {error}")
    
    # Statistics and monitoring methods
    def get_cache_stats(self) -> Dict:
        """Get file manager cache statistics for debugging."""
        return self.stats_manager.get_cache_stats()
    
    def get_security_stats(self) -> Dict:
        """Get security statistics for monitoring."""
        return self.stats_manager.get_security_stats()
    
    def get_dynamic_stats(self) -> Dict:
        """Get dynamic statistics for current filtered files."""
        return self.stats_manager.get_dynamic_file_stats(self.current_filtered_files)
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed."""
        cleanup_resources(self.admin_user, self.file_manager, self.enhanced_logger)


# Alias for backward compatibility
FileApprovalPanel = EnhancedFileApprovalPanel
