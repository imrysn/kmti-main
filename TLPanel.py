import flet as ft
import os
import shutil
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from admin.components.team_leader_service import get_team_leader_service
from utils.session_logger import log_logout, log_activity
from utils.logger import log_file_operation
from admin.components.role_colors import create_role_badge, get_role_color
from user.components.dialogs import DialogManager


class TeamLeaderPanel:
    """Enhanced Team Leader Panel with dynamic filtering and statistics."""
    
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
        self.tl_service = get_team_leader_service()
        self.dialog_manager = DialogManager(page, username)
        self.selected_file = None
        self.files_table = None
        self.preview_panel = None
        self.selected_row_index = None  # Track selected row for highlighting
        self.user_team = self.tl_service.get_user_team(username)
        
        # Statistics cards references for dynamic updates
        self.stat_pending_card = None
        self.stat_approved_card = None
        self.stat_rejected_card = None
        
        # UI State with enhanced filtering
        self.search_query = ""
        self.current_sort = "submission_date"
        self.current_status_filter = "ALL"
        self.current_view_mode = "pending_only"  # pending_only, my_approved, my_rejected, all_team
        
        # Current filtered files for statistics
        self.current_filtered_files = []
    
    def create_interface(self) -> ft.Container:
        """Create the main team leader interface."""
        try:
            header = self._create_header_section()
            filters = self._create_filters_section()
            main_content = self._create_main_content()
            
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
            print(f"Error creating team leader interface: {e}")
            return self._create_error_interface(str(e))
    
    def _create_header_section(self) -> ft.Container:
        """Create header with dynamic statistics."""
        # Initialize with default counts
        file_counts = self.tl_service.get_file_counts_for_team_leader(self.username)
        
        # Create stat cards and store references
        self.stat_pending_card = self._create_stat_card("Pending Review", 
                                     str(file_counts['pending_team_leader']), 
                                     ft.Colors.ORANGE)
        self.stat_approved_card = self._create_stat_card("Approved", 
                                      str(file_counts['approved_by_tl']), 
                                      ft.Colors.GREEN)
        self.stat_rejected_card = self._create_stat_card("Rejected", 
                                      str(file_counts['rejected_by_tl']), 
                                      ft.Colors.RED)
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval", size=26, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Team: {self.user_team}", 
                           size=18, color=ft.Colors.GREY_600),
                    ft.Row([
                        ft.Text("Role: ", size=16, color=ft.Colors.GREY_500),
                        create_role_badge("TEAM_LEADER", size=14)
                    ])
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
                ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=16, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=140,
            height=80,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.GREY_200)
        )
    
    def _create_filters_section(self) -> ft.Row:
        """Create enhanced filters section."""
        return ft.Row([
            # Search field
            ft.TextField(
                hint_text="Search files...",
                width=200,
                value=self.search_query,
                on_change=self._on_search_changed,
                prefix_icon=ft.Icons.SEARCH
            ),
            
            # View mode selector
            ft.Dropdown(
                label="View",
                width=160,
                value=self.current_view_mode,
                options=[
                    ft.dropdown.Option("pending_only", "Pending Review"),
                    ft.dropdown.Option("my_approved", "My Approved"),
                    ft.dropdown.Option("my_rejected", "My Rejected"),
                    ft.dropdown.Option("all_team", "All Team Files")
                ],
                on_change=self._on_view_mode_changed
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
                content=ft.Text(f"Showing: {self._get_view_description()}", 
                               size=16, color=ft.Colors.GREY_600),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.GREY_200,
                border_radius=5
            ),
            
            # Refresh button
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table(),
                style=self._get_button_style("secondary")
            )
        ])
    
    def _get_view_description(self) -> str:
        """Get description of current view mode."""
        descriptions = {
            "pending_only": "Files awaiting your review",
            "my_approved": "Files you've approved", 
            "my_rejected": "Files you've rejected",
            "all_team": "All files from your team"
        }
        return descriptions.get(self.current_view_mode, "Unknown view")
    
    def _create_main_content(self) -> ft.ResponsiveRow:
        """Create main content area with responsive layout."""
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
                expand=True
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
                expand=True
            )
        ], expand=True)
    
    def _create_files_table_section(self) -> ft.Container:
        """Create files table section with dynamic responsive columns."""
        
        # Define columns that will be shown based on container size
        def get_columns_for_size(col_config):
            columns = []
            if col_config.get("file", True):
                columns.append(ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("user", True):
                columns.append(ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("size", True):
                columns.append(ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("submitted", True):
                columns.append(ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)))
            if col_config.get("status", True):
                columns.append(ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)))
            return columns
        
        # Store column configurations for different sizes
        column_configs = {
            "xs": {"file": True, "user": False, "size": False, "submitted": False, "status": True},
            "sm": {"file": True, "user": True, "size": False, "submitted": False, "status": True},
            "md": {"file": True, "user": True, "size": False, "submitted": True, "status": True},
            "lg": {"file": True, "user": True, "size": True, "submitted": True, "status": True}
        }
        
        # Create responsive data table
        self.files_table = ft.DataTable(
            columns=get_columns_for_size(column_configs["lg"]),  # Start with all columns
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
                    ft.Text(f"Team: {self.user_team}", size=18, color=ft.Colors.GREY_600)
                ]),
                ft.Divider(),
                ft.Container(height=10),
                table_content  # Use responsive approach
            ], expand=True, spacing=0),
            expand=True,
            padding=0
        )
    
    def _create_preview_section(self) -> ft.Container:
        """Create preview section."""
        self.preview_panel = ft.Column([
            ft.Text("Select a file to review", size=18, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=16, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
        alignment=ft.MainAxisAlignment.CENTER, 
        scroll=ft.ScrollMode.AUTO,
        expand=True
        )
        
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
            padding=0
        )
    
    def refresh_files_table(self):
        """Refresh the files table with enhanced filtering."""
        try:
            # Get files based on current view mode
            if self.current_view_mode == "pending_only":
                all_files = self.tl_service.get_pending_files_for_team_leader(self.username)
            elif self.current_view_mode == "my_approved":
                files_by_status = self.tl_service.get_team_files_by_status(self.username)
                all_files = files_by_status.get('pending_admin', []) + files_by_status.get('approved', [])
            elif self.current_view_mode == "my_rejected":
                files_by_status = self.tl_service.get_team_files_by_status(self.username)
                all_files = files_by_status.get('rejected_by_tl', [])
            else:  # all_team
                files_by_status = self.tl_service.get_team_files_by_status(self.username)
                all_files = []
                for status_files in files_by_status.values():
                    all_files.extend(status_files)
            
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
            all_files = self._sort_files(all_files)
            
            # Store current filtered files for statistics
            self.current_filtered_files = all_files
            
            # Update statistics cards dynamically
            self._update_statistics_cards()
            
            # Clear and populate table
            self.files_table.rows.clear()
            
            # Reset selection when table is refreshed
            self.selected_row_index = None
            
            if not all_files:
                self._add_empty_table_row()
            else:
                for i, file_data in enumerate(all_files):
                    try:
                        row = self._create_table_row(file_data, i)
                        self.files_table.rows.append(row)
                    except Exception as row_error:
                        print(f"Error creating table row: {row_error}")
                        continue
            
            self.page.update()
            
        except Exception as e:
            print(f"Error refreshing files table: {e}")
            self._show_table_error(str(e))
    
    def _update_statistics_cards(self):
        """Update statistics cards with current filtered files."""
        try:
            # Get counts for current filtered files
            dynamic_counts = self.tl_service.get_file_counts_for_team_leader(
                self.username, self.current_filtered_files)
            
            # Also get overall team statistics for reference
            overall_counts = self.tl_service.get_file_counts_for_team_leader(self.username)
            
            # Update card values based on view mode
            if self.current_view_mode == "pending_only":
                # Show actual filtered counts
                pending_text = str(len(self.current_filtered_files))
                approved_text = str(overall_counts['approved_by_tl'])
                rejected_text = str(overall_counts['rejected_by_tl'])
            elif self.current_view_mode == "my_approved":
                pending_text = str(overall_counts['pending_team_leader'])
                approved_text = str(len(self.current_filtered_files))
                rejected_text = str(overall_counts['rejected_by_tl'])
            elif self.current_view_mode == "my_rejected":
                pending_text = str(overall_counts['pending_team_leader'])
                approved_text = str(overall_counts['approved_by_tl'])
                rejected_text = str(len(self.current_filtered_files))
            else:  # all_team
                # Show dynamic counts from filtered files
                pending_text = str(dynamic_counts['pending_team_leader'])
                approved_text = str(dynamic_counts['approved_by_tl'])
                rejected_text = str(dynamic_counts['rejected_by_tl'])
            
            # Update stat card values
            if self.stat_pending_card:
                self.stat_pending_card.content.controls[0].value = pending_text
            if self.stat_approved_card:
                self.stat_approved_card.content.controls[0].value = approved_text  
            if self.stat_rejected_card:
                self.stat_rejected_card.content.controls[0].value = rejected_text
                
        except Exception as e:
            print(f"Error updating statistics cards: {e}")
    
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
            print(f"Error sorting files: {e}")
            return files
    
    def _create_table_row(self, file_data: Dict, row_index: int) -> ft.DataRow:
        """Create table row with dynamic column visibility based on current configuration."""
        file_size = file_data.get('file_size', 0)
        size_str = self._format_file_size(file_size)

        try:
            submit_date = datetime.fromisoformat(file_data['submission_date'])
            date_str = submit_date.strftime("%m/%d %H:%M")
        except:
            date_str = "Unknown"
        
        original_filename = file_data.get('original_filename', 'Unknown')
        display_filename = self._limit_filename_display(original_filename, 25)
        
        # Enhanced status display with color coding
        status = file_data.get('status', 'unknown')
        status_badge = self._create_status_badge(status, file_data)
        
        # Get current column configuration (default to lg if not set)
        col_config = getattr(self, 'column_configs', {}).get('lg', {
            "file": True, "user": True, "size": True, "submitted": True, "status": True
        })
        
        cells = []
        
        if col_config.get("file", True):
            cells.append(ft.DataCell(ft.Text(
                display_filename,
                tooltip=original_filename,
                size=16,
                overflow=ft.TextOverflow.ELLIPSIS
            )))
        
        if col_config.get("user", True):
            cells.append(ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'), size=16)))
        
        if col_config.get("size", True):
            cells.append(ft.DataCell(ft.Text(size_str, size=16)))
        
        if col_config.get("submitted", True):
            cells.append(ft.DataCell(ft.Text(date_str, size=16)))
        
        if col_config.get("status", True):
            cells.append(ft.DataCell(status_badge))
        
        return ft.DataRow(
            cells=cells,
            selected=self.selected_row_index == row_index,
            on_select_changed=lambda e, data=file_data, idx=row_index: self.select_file(data, idx),
            color={
                ft.ControlState.SELECTED: ft.Colors.GREY_300,
                ft.ControlState.HOVERED: ft.Colors.GREY_100,
            }
        )
    
    def _create_status_badge(self, status: str, file_data: Dict) -> ft.Container:
        """🚨 ENHANCED: Create color-coded status badge with support for moved files."""
        # Handle special display status for moved files
        display_status = file_data.get('display_status', status)
        
        status_configs = {
            'pending_team_leader': {'text': 'PENDING TL', 'color': ft.Colors.ORANGE},
            'pending': {'text': 'PENDING TL', 'color': ft.Colors.ORANGE},
            'pending_admin': {'text': 'PENDING ADMIN', 'color': ft.Colors.ORANGE},
            'approved': {'text': 'APPROVED', 'color': ft.Colors.GREEN},
            'approved_and_moved': {'text': 'APPROVED & MOVED', 'color': ft.Colors.GREEN_700},
            'rejected_team_leader': {'text': 'REJECTED TL', 'color': ft.Colors.RED},
            'rejected_admin': {'text': 'REJECTED ADMIN', 'color': ft.Colors.RED_900}
        }
        
        config = status_configs.get(display_status, {'text': display_status.upper(), 'color': ft.Colors.GREY})
        
        # Add reviewer info for approved/rejected files
        tooltip_text = f"Status: {display_status}"
        if status == 'pending_admin' and file_data.get('tl_approved_by'):
            tooltip_text += f"\\nApproved by: {file_data['tl_approved_by']}"
        elif status == 'rejected_team_leader' and file_data.get('tl_rejected_by'):
            tooltip_text += f"\\nRejected by: {file_data['tl_rejected_by']}"
        elif display_status == 'approved_and_moved':
            tooltip_text += f"\\nApproved by TL: {file_data.get('tl_approved_by', 'Unknown')}"
            tooltip_text += f"\\nApproved by Admin: {file_data.get('approved_by', 'Unknown')}"
            current_location = file_data.get('current_location')
            if current_location:
                tooltip_text += f"\\nMoved to: {current_location}"
            else:
                tooltip_text += "\\nFile moved to project directory"
        
        return ft.Container(
            content=ft.Text(config['text'], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
            bgcolor=config['color'],
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            tooltip=tooltip_text
        )
    
    def select_file(self, file_data: Dict, row_index: int):
        """Select a file for review and highlight the row."""
        try:
            # Update selected file and row index
            self.selected_file = file_data
            old_selected_index = self.selected_row_index
            self.selected_row_index = row_index
            
            # Update row highlighting
            if old_selected_index is not None and old_selected_index < len(self.files_table.rows):
                self.files_table.rows[old_selected_index].selected = False
            
            if row_index < len(self.files_table.rows):
                self.files_table.rows[row_index].selected = True
            
            self._update_preview_panel()
            self.page.update()
            
            log_file_operation(
                username=self.username,
                operation="SELECT_FILE",
                file_path=file_data.get('original_filename', 'unknown'),
                result="SUCCESS",
                details={"file_id": file_data.get('file_id')}
            )
        except Exception as e:
            print(f"Error selecting file: {e}")
            self.dialog_manager.show_error_notification("Error selecting file")
    
    def _update_preview_panel(self):
        """Update the preview panel with selected file info."""
        if not self.selected_file:
            return
        
        try:
            file_data = self.selected_file
            preview_content = self._create_file_preview(file_data)
            self.preview_panel.controls.clear()
            self.preview_panel.controls.extend(preview_content)
            self.preview_panel.horizontal_alignment = ft.CrossAxisAlignment.START
            self.preview_panel.alignment = ft.MainAxisAlignment.START
            self.page.update()
            
        except Exception as e:
            print(f"Error updating preview panel: {e}")
            self.dialog_manager.show_error_notification("Error loading file preview")
    
    def _create_file_preview(self, file_data: Dict) -> List:
        """Create enhanced file preview content."""
        submit_date = "Unknown"
        try:
            submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
        except:
            pass
        
        file_size = self._format_file_size(file_data.get('file_size', 0))
        status = file_data.get('status', 'unknown')
        
        # File details section
        details_section = [
            ft.Text("File Details", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column([
                ft.Text(f"File: {file_data.get('original_filename', 'Unknown')}", 
                       size=16, weight=ft.FontWeight.W_500),
                ft.Text(f"User: {file_data.get('user_id', 'Unknown')}", size=16),
                ft.Text(f"Team: {file_data.get('user_team', 'Unknown')}", size=16),
                ft.Text(f"Size: {file_size}", size=16),
                ft.Text(f"Submitted: {submit_date}", size=16),
                ft.Row([
                    ft.Text("Status: ", size=16),
                    self._create_status_badge(status, file_data)
                ])
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            ft.Text("Description:", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(file_data.get('description', 'No description provided'), 
                   size=16, color=ft.Colors.GREY_600),
        ]
        
        # File operations section - Open button back in preview section
        operations_section = [
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    "Open",
                    icon=ft.Icons.OPEN_IN_NEW_OUTLINED,
                    on_click=lambda e: self._handle_open_file(file_data),
                    style=self._get_button_style("secondary")
                )
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider()
        ]
        
        # Action sections based on file status and view mode
        action_sections = self._create_action_sections(file_data)
        
        return details_section + operations_section + action_sections
    
    def _create_action_sections(self, file_data: Dict) -> List:
        """Create action sections based on file status."""
        status = file_data.get('status', 'unknown')
        actions = []
        
        # Comment field (always available)
        comment_field = ft.TextField(
            label="Add comment (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=16,
            expand=True
        )
        
        # Comments section
        actions.extend([
            ft.Text("Team Leader Actions", size=18, weight=ft.FontWeight.BOLD),
            comment_field,
            ft.Container(height=5),
            ft.Row([
                ft.ElevatedButton(
                    "Add Comment",
                    icon=ft.Icons.COMMENT,
                    on_click=lambda e: self._handle_add_comment(file_data, comment_field),
                    style=self._get_button_style("primary")
                )
            ], alignment=ft.MainAxisAlignment.START),
        ])
        
        # Approval/Rejection actions (only for pending files)
        if status in ['pending_team_leader', 'pending']:
            reason_field = ft.TextField(
                label="Reason for rejection",
                multiline=True,
                min_lines=2,
                max_lines=3,
                text_size=16,
                expand=True
            )
            
            actions.extend([
                ft.Container(height=10),
                ft.Divider(),
                ft.Text("Approval Decision", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                reason_field,
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        "✓ Approve",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=lambda e: self._handle_approve_file_with_confirmation(file_data),
                        style=self._get_button_style("success")
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "✗ Reject", 
                        icon=ft.Icons.CANCEL,
                        on_click=lambda e: self._handle_reject_file_with_validation(file_data, reason_field),
                        style=self._get_button_style("danger")
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
            ])
        elif status == 'pending_admin':
            actions.extend([
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text("✓ File approved - waiting for admin review", 
                                   color=ft.Colors.GREEN, size=16, weight=ft.FontWeight.W_500),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=10,
                    border_radius=5,
                    border=ft.border.all(1, ft.Colors.GREEN_200)
                )
            ])
        elif status == 'rejected_team_leader':
            rejection_reason = file_data.get('tl_rejection_reason', 'No reason provided')
            actions.extend([
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Text("✗ File rejected by you", 
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
    
    def _handle_download_file(self, file_data: Dict):
        """Handle file download."""
        try:
            file_path = file_data.get('file_path')
            original_filename = file_data.get('original_filename', 'unknown_file')
            
            if not file_path or not os.path.exists(file_path):
                self.dialog_manager.show_error_notification("File not found in storage")
                return
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path.home() / "Downloads" / "KMTI_Reviews"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            
            download_path = downloads_dir / original_filename
            shutil.copy2(file_path, download_path)
            
            self.dialog_manager.show_success_notification(f"Downloaded: {original_filename}")
            log_file_operation(self.username, "DOWNLOAD", original_filename, "SUCCESS")
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            self.dialog_manager.show_error_notification("Error downloading file")
    
    def _handle_open_file(self, file_data: Dict):
        """🚨 ENHANCED: Handle file opening with support for moved files."""
        try:
            file_path = file_data.get('file_path')
            original_filename = file_data.get('original_filename', 'unknown_file')
            
            # 🚨 ENHANCED: Check for moved files in project directories
            if not file_path or not os.path.exists(file_path):
                # Try to find the file in its new location if it's an approved file
                current_location = file_data.get('current_location')
                if current_location and os.path.exists(current_location):
                    file_path = current_location
                    print(f"[OPEN_FILE] Using moved file location: {file_path}")
                else:
                    self.dialog_manager.show_error_notification("File not found in storage or project directory")
                    return
            
            # Open file with system default application
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            
            self.dialog_manager.show_success_notification(f"Opening: {original_filename}")
            log_file_operation(self.username, "OPEN", original_filename, "SUCCESS")
            
        except Exception as e:
            print(f"Error opening file: {e}")
            self.dialog_manager.show_error_notification("Error opening file")
    
    def _handle_add_comment(self, file_data: Dict, comment_field: ft.TextField):
        """Handle adding comment to file."""
        try:
            comment_text = comment_field.value
            if not comment_text or not comment_text.strip():
                self.dialog_manager.show_error_notification("Please enter a comment")
                return
            
            success, message = self.tl_service.add_comment_to_file(
                file_data['file_id'], self.username, comment_text
            )
            
            if success:
                comment_field.value = ""
                comment_field.update()
                self.dialog_manager.show_success_notification("Comment added successfully")
                log_activity(self.username, f"Added comment to file: {file_data.get('original_filename')}")
            else:
                self.dialog_manager.show_error_notification(f"Failed to add comment: {message}")
                
        except Exception as e:
            print(f"Error adding comment: {e}")
            self.dialog_manager.show_error_notification("Error adding comment")
    
    def _handle_approve_file(self, file_data: Dict):
        """Handle file approval."""
        try:
            success, message = self.tl_service.approve_as_team_leader(
                file_data['file_id'], self.username
            )
            
            if success:
                filename = file_data.get('original_filename', 'Unknown')
                self.dialog_manager.show_success_notification(f"File '{filename}' approved and sent to admin!")
                log_activity(self.username, f"Approved file: {filename}")
                
                self._clear_selection()
                self.refresh_files_table()
                
            else:
                self.dialog_manager.show_error_notification(f"Failed to approve: {message}")
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self.dialog_manager.show_error_notification("Error approving file")
    
    def _handle_reject_file(self, file_data: Dict, reason_field: ft.TextField):
        """Handle file rejection."""
        try:
            reason = reason_field.value
            if not reason or not reason.strip():
                self.dialog_manager.show_error_notification("Please provide a reason for rejection")
                return
            
            success, message = self.tl_service.reject_as_team_leader(
                file_data['file_id'], self.username, reason
            )
            
            if success:
                filename = file_data.get('original_filename', 'Unknown')
                self.dialog_manager.show_success_notification(f"File '{filename}' rejected")
                log_activity(self.username, f"Rejected file: {filename} - Reason: {reason}")
                
                self._clear_selection()
                self.refresh_files_table()
                
            else:
                self.dialog_manager.show_error_notification(f"Failed to reject: {message}")
                
        except Exception as e:
            print(f"Error rejecting file: {e}")
            self.dialog_manager.show_error_notification("Error rejecting file")
    
    def _handle_approve_file_with_confirmation(self, file_data: Dict):
        """Handle file approval with confirmation dialog."""
        try:
            filename = file_data.get('original_filename', 'Unknown')
            
            def on_confirm():
                self._handle_approve_file(file_data)
            
            self.dialog_manager.show_confirmation_dialog(
                title="Confirm Approval",
                message=f"Are you sure you want to approve this file?",
                on_confirm=on_confirm,
                confirm_text="Approve",
                cancel_text="Cancel",
                confirm_color=ft.Colors.GREEN
            )
            
        except Exception as e:
            print(f"Error showing approval confirmation: {e}")
            self.dialog_manager.show_error_notification("Error showing confirmation dialog")
    
    def _handle_reject_file_with_validation(self, file_data: Dict, reason_field: ft.TextField):
        """Handle file rejection with validation for rejection reason."""
        try:
            reason = reason_field.value
            if not reason or not reason.strip():
                # Show notification that rejection reason is required
                self.dialog_manager.show_error_notification("Please enter a rejection reason in the text field before proceeding")
                return
            
            # Proceed with rejection
            self._handle_reject_file(file_data, reason_field)
            
        except Exception as e:
            print(f"Error validating rejection: {e}")
            self.dialog_manager.show_error_notification("Error processing rejection")
    
    def _clear_selection(self):
        """Clear current file selection."""
        # Clear row highlighting
        if self.selected_row_index is not None and self.selected_row_index < len(self.files_table.rows):
            self.files_table.rows[self.selected_row_index].selected = False
        
        self.selected_file = None
        self.selected_row_index = None
        
        self.preview_panel.controls.clear()
        self.preview_panel.controls.extend([
            ft.Text("Select a file to review", size=18, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=16, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ])
        self.preview_panel.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.preview_panel.alignment = ft.MainAxisAlignment.CENTER
    
    def _create_error_interface(self, error_msg: str) -> ft.Container:
        """Create error interface."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                ft.Text("Team Leader Panel", size=26, weight=ft.FontWeight.BOLD),
                ft.Text("Error loading review system", size=18, color=ft.Colors.RED),
                ft.Text(f"Details: {error_msg}", size=16, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: self.page.update(),
                    style=self._get_button_style("primary")
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            expand=True
        )
    
    def _add_empty_table_row(self):
        """Add empty table row when no files are found."""
        empty_message = {
            "pending_only": "No files pending your review",
            "my_approved": "No files approved by you",
            "my_rejected": "No files rejected by you", 
            "all_team": "No files found for your team"
        }.get(self.current_view_mode, "No files found")
        
        self.files_table.rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(empty_message, style=ft.TextStyle(italic=True), color=ft.Colors.GREY_600)),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text(""))
        ]))
    
    def _show_table_error(self, error_msg: str):
        """Show error message in the table."""
        self.files_table.rows.clear()
        self.files_table.rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(f"Error loading files: {error_msg}", color=ft.Colors.RED)),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text("")),
            ft.DataCell(ft.Text(""))
        ]))
        self.page.update()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def _limit_filename_display(self, filename: str, max_length: int) -> str:
        """Limit filename display length."""
        if len(filename) <= max_length:
            return filename
        
        if max_length > 10:
            start_len = max_length // 2 - 2
            end_len = max_length - start_len - 3
            return f"{filename[:start_len]}...{filename[-end_len:]}"
        else:
            return filename[:max_length-3] + "..."
    
    def _get_button_style(self, button_type: str):
        """Get button style based on type."""
        border_radius = 5
        
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
        else:  # secondary
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
    
    # Event handlers
    def _on_search_changed(self, e):
        """Handle search input change."""
        try:
            self.search_query = e.control.value.lower()
            self.refresh_files_table()
        except Exception as error:
            print(f"Error handling search change: {error}")
    
    def _on_view_mode_changed(self, e):
        """Handle view mode change."""
        try:
            self.current_view_mode = e.control.value
            self._clear_selection()  # Clear selection when switching views
            self.refresh_files_table()
        except Exception as error:
            print(f"Error handling view mode change: {error}")
    
    def _on_sort_changed(self, e):
        """Handle sort option change."""
        try:
            self.current_sort = e.control.value
            self.refresh_files_table()
        except Exception as error:
            print(f"Error handling sort change: {error}")


def TLPanel(page: ft.Page, username: str):
    """Enhanced Team Leader Panel - Main Entry Point - Accessible only by TEAM_LEADER role."""
    # Verify user has team leader role
    from utils.auth import load_users
    users = load_users()
    user_role = None
    for email, data in users.items():
        if data.get("username") == username:
            user_role = data.get("role", "").upper()
            # Normalize role string
            if user_role == "TEAM LEADER":
                user_role = "TEAM_LEADER"
            break
    
    print(f"[DEBUG] TL Panel access check: username={username}, role={user_role}")
    
    if user_role != "TEAM_LEADER":
        print(f"[WARNING] Non-team-leader user {username} (role: {user_role}) attempted to access TL panel")
        page.clean()
        from login_window import login_view
        login_view(page)
        return
    
    page.bgcolor = ft.Colors.GREY_200
    page.padding = 0

    content = ft.Column(expand=True, spacing=0)

    def on_logout():
        from login_window import clear_session
        log_logout(username, "TEAM_LEADER")
        clear_session(username)
        page.clean()
        from login_window import login_view
        login_view(page)

    # Enhanced navigation bar with Team Leader badge
    tl_badge = create_role_badge("TEAM_LEADER", size=12)
    navbar = ft.Container(
        bgcolor=ft.Colors.GREY_800,
        padding=10,
        margin=0,
        content=ft.Row(
            controls=[
                ft.Row([
                    ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.WHITE, size=22),
                    ft.Text("KMTI Data Management", color=ft.Colors.WHITE, size=18, weight=ft.FontWeight.BOLD)
                ]),
                ft.Container(expand=True),  
                ft.Row(
                    controls=[
                        ft.Text(f"Hi, {username}", size=18, color=ft.Colors.WHITE),
                        tl_badge,
                        ft.TextButton(
                            content=ft.Text("Logout", size=16, color=ft.Colors.WHITE),
                            on_click=lambda e: on_logout(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=15,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    def show_team_leader_panel():
        """Show the enhanced team leader panel."""
        content.controls.clear()
        try:
            tl_panel = TeamLeaderPanel(page, username)
            content.controls.append(tl_panel.create_interface())
        except Exception as ex:
            print(f"[ERROR] Failed to load Team Leader Panel: {ex}")
            content.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                        ft.Text(f"Error loading panel: {ex}", color=ft.Colors.RED, size=18),
                        ft.ElevatedButton(
                            "Retry",
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: show_team_leader_panel()
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=50
                )
            )
        content.update()

    page.add(navbar, content)
    show_team_leader_panel()
