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


class FileApprovalPanel:
    
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
        
        # Initialize services and data
        self._initialize_services_and_data()
        
        # Initialize component helpers
        self._initialize_component_helpers()
        
        # Initialize UI state
        self._initialize_ui_state()
        
        self.enhanced_logger.general_logger.info(
            f"File approval panel initialized for admin: {self.admin_user}")
    
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
        self.is_super_admin = self.permission_service.is_super_admin(self.admin_user)
        
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
        """Initialize UI state variables."""
        self.selected_file = None
        self.files_table = None
        self.preview_panel_widget = None
        self.current_team_filter = "ALL"
        self.current_sort = "submission_date"
        self.search_query = ""
    
    def create_approval_interface(self) -> ft.Container:

        try:
            with PerformanceTimer("FileApprovalPanel", "create_interface"):
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
        """Create header section with statistics."""
        file_counts = self.data_manager.get_file_counts_safely(
            self.admin_user, self.admin_teams, self.is_super_admin)
        
        return self.ui_helper.create_header_section(self.admin_teams, file_counts)
    
    def _create_filters_section(self) -> ft.Row:
        """Create filters section."""
        teams = self.team_loader.load_teams_safely(self.admin_user, self.admin_teams)
        
        return self.ui_helper.create_filters_section(
            teams, self.search_query, self.current_team_filter, self.current_sort,
            self._on_search_changed, self._on_team_filter_changed,
            self._on_sort_changed, lambda e: self.refresh_files_table()
        )
    
    def _create_main_content_area(self) -> ft.ResponsiveRow:
        """Create main content area with table and preview."""
        return ft.ResponsiveRow([
            # Left: Files table
            ft.Container(
                content=self._create_files_table_section(),
                col={"sm": 12, "md": 7, "lg": 8},
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                padding=20
            ),
            
            # Right: Preview and actions  
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
        """Create files table section."""
        self.files_table = self.table_helper.create_responsive_table(self.select_file)
        self.refresh_files_table()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pending Files", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(height=10),
                ft.Container(
                    content=self.files_table,
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
        """Refresh the files table with current filters and sorting."""
        try:
            with PerformanceTimer("FileApprovalPanel", "refresh_files_table"):
                # Get pending files
                pending_files = self.data_manager.get_filtered_pending_files(
                    self.admin_user, self.admin_teams, self.is_super_admin)
                
                # Apply filters and sorting
                filtered_files = self.file_filter.apply_filters(
                    pending_files, self.search_query, self.current_team_filter, self.current_sort)
                
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
                self.ui_helper.get_button_style, self._get_refresh_callback()
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
            with PerformanceTimer("FileApprovalPanel", "refresh_interface"):
                self.refresh_files_table()
                self._update_preview_panel()
                self.file_manager.invalidate_cache()
                self.page.update()
            
            self.enhanced_logger.general_logger.info("Interface refreshed successfully")
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error refreshing interface: {e}")
            self.show_snackbar("Error refreshing interface", "red")
    
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
            self.refresh_files_table()
        except Exception as error:
            self.enhanced_logger.general_logger.error(f"Error handling team filter change: {error}")
    
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
    
    def cleanup(self):
        """Cleanup resources when panel is destroyed."""
        cleanup_resources(self.admin_user, self.file_manager, self.enhanced_logger)
