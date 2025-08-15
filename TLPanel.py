"""
Team Leader Panel - Independent Implementation

This panel implements the correct workflow for team leader file approval:
1. Shows only files with status 'pending_team_leader' from the TL's team
2. Allows approve → changes status to 'pending_admin' 
3. Allows reject → changes status to 'rejected_team_leader'
4. Provides file download/open functionality
5. Maintains proper status transitions without depending on FileApprovalPanel
"""

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


class TeamLeaderPanel:
    """Team Leader Panel for reviewing files from their team."""
    
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
        self.tl_service = get_team_leader_service()
        self.selected_file = None
        self.files_table = None
        self.preview_panel = None
        self.user_team = self.tl_service.get_user_team(username)
        
        # UI State
        self.search_query = ""
        self.current_sort = "submission_date"
    
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
        """Create header with statistics."""
        file_counts = self.tl_service.get_file_counts_for_team_leader(self.username)
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Team Leader - File Review", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Team: {self.user_team} | Reviewer: {self.username}", 
                           size=16, color=ft.Colors.GREY_600),
                    ft.Text("Role: TEAM_LEADER | Access: team_limited", 
                           size=14, color=ft.Colors.GREY_500)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self._create_stat_card("Pending Review", 
                                         str(file_counts['pending_team_leader']), 
                                         ft.Colors.ORANGE),
                    ft.Container(width=15),
                    self._create_stat_card("Approved by Me", 
                                         str(file_counts['approved_by_tl']), 
                                         ft.Colors.GREEN),
                    ft.Container(width=15),
                    self._create_stat_card("Rejected by Me", 
                                         str(file_counts['rejected_by_tl']), 
                                         ft.Colors.RED)
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
            width=140,
            height=80,
            alignment=ft.alignment.center
        )
    
    def _create_filters_section(self) -> ft.Row:
        """Create filters section."""
        return ft.Row([
            ft.TextField(
                hint_text="Search files...",
                width=200,
                value=self.search_query,
                on_change=self._on_search_changed,
                prefix_icon=ft.Icons.SEARCH
            ),
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
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=lambda e: self.refresh_files_table(),
                style=self._get_button_style("secondary")
            )
        ])
    
    def _create_main_content(self) -> ft.ResponsiveRow:
        """Create main content area."""
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
        self.files_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=16)),
                ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, size=16)),
                ft.DataColumn(ft.Text("Size", weight=ft.FontWeight.BOLD, size=16)),
                ft.DataColumn(ft.Text("Submitted", weight=ft.FontWeight.BOLD, size=16)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, size=16)),
            ],
            rows=[],
            column_spacing=10,
            horizontal_margin=5,
            data_row_max_height=50,
            data_row_min_height=40,
            expand=True,
        )
        
        self.refresh_files_table()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Pending Files for Review", size=20, weight=ft.FontWeight.BOLD),
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
        self.preview_panel = ft.Column([
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
        """Refresh the files table."""
        try:
            pending_files = self.tl_service.get_pending_files_for_team_leader(self.username)
            
            # Apply search filter
            if self.search_query:
                search_lower = self.search_query.lower()
                pending_files = [
                    f for f in pending_files
                    if (search_lower in f.get('original_filename', '').lower() or
                        search_lower in f.get('user_id', '').lower() or
                        search_lower in f.get('description', '').lower())
                ]
            
            # Apply sorting
            pending_files = self._sort_files(pending_files)
            
            # Clear and populate table
            self.files_table.rows.clear()
            
            if not pending_files:
                self._add_empty_table_row()
            else:
                for file_data in pending_files:
                    try:
                        row = self._create_table_row(file_data)
                        self.files_table.rows.append(row)
                    except Exception as row_error:
                        print(f"Error creating table row: {row_error}")
                        continue
            
            self.page.update()
            
        except Exception as e:
            print(f"Error refreshing files table: {e}")
            self._show_table_error(str(e))
    
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
    
    def _create_table_row(self, file_data: Dict) -> ft.DataRow:
        """Create table row for file data."""
        file_size = file_data.get('file_size', 0)
        size_str = self._format_file_size(file_size)

        try:
            submit_date = datetime.fromisoformat(file_data['submission_date'])
            date_str = submit_date.strftime("%m/%d %H:%M")
        except:
            date_str = "Unknown"
        
        original_filename = file_data.get('original_filename', 'Unknown')
        display_filename = self._limit_filename_display(original_filename, 25)
        
        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(
                    display_filename,
                    tooltip=original_filename,
                    size=14,
                    overflow=ft.TextOverflow.ELLIPSIS
                )),
                ft.DataCell(ft.Text(file_data.get('user_id', 'Unknown'), size=14)),
                ft.DataCell(ft.Text(size_str, size=14)),
                ft.DataCell(ft.Text(date_str, size=14)),
                ft.DataCell(ft.Container(
                    content=ft.Text("PENDING TL", color=ft.Colors.WHITE, size=10),
                    bgcolor=ft.Colors.ORANGE,
                    padding=ft.padding.symmetric(horizontal=6, vertical=3),
                    border_radius=4
                ))
            ],
            on_select_changed=lambda e, data=file_data: self.select_file(data)
        )
    
    def select_file(self, file_data: Dict):
        """Select a file for review."""
        try:
            self.selected_file = file_data
            self._update_preview_panel()
            log_file_operation(
                username=self.username,
                operation="SELECT_FILE",
                file_path=file_data.get('original_filename', 'unknown'),
                result="SUCCESS",
                details={"file_id": file_data.get('file_id')}
            )
        except Exception as e:
            print(f"Error selecting file: {e}")
            self._show_snackbar("Error selecting file", ft.Colors.RED)
    
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
            self._show_snackbar("Error loading file preview", ft.Colors.RED)
    
    def _create_file_preview(self, file_data: Dict) -> List:
        """Create file preview content."""
        submit_date = "Unknown"
        try:
            submit_date = datetime.fromisoformat(file_data['submission_date']).strftime('%Y-%m-%d %H:%M')
        except:
            pass
        
        file_size = self._format_file_size(file_data.get('file_size', 0))
        
        # Comment field
        comment_field = ft.TextField(
            label="Add comment (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            text_size=14,
            expand=True
        )
        
        # Rejection reason field
        reason_field = ft.TextField(
            label="Reason for rejection",
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=14,
            expand=True
        )
        
        return [
            ft.Text("File Details", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column([
                ft.Text(f"File: {file_data.get('original_filename', 'Unknown')}", 
                       size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"User: {file_data.get('user_id', 'Unknown')}", size=14),
                ft.Text(f"Team: {file_data.get('user_team', 'Unknown')}", size=14),
                ft.Text(f"Size: {file_size}", size=14),
                ft.Text(f"Submitted: {submit_date}", size=14),
            ], spacing=5, alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            ft.Text("Description:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(file_data.get('description', 'No description provided'), 
                   size=12, color=ft.Colors.GREY_600),
            
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    "Download",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda e: self._handle_download_file(file_data),
                    style=self._get_button_style("primary")
                ),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Open",
                    icon=ft.Icons.OPEN_IN_NEW,
                    on_click=lambda e: self._handle_open_file(file_data),
                    style=self._get_button_style("secondary")
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            
            ft.Divider(),
            ft.Text("Team Leader Actions", size=16, weight=ft.FontWeight.BOLD),
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
            
            ft.Container(height=10),
            ft.Divider(),
            ft.Container(height=10),
            reason_field,
            ft.Container(height=10),
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
    
    def _handle_download_file(self, file_data: Dict):
        """Handle file download."""
        try:
            file_path = file_data.get('file_path')
            original_filename = file_data.get('original_filename', 'unknown_file')
            
            if not file_path or not os.path.exists(file_path):
                self._show_snackbar("File not found in storage", ft.Colors.RED)
                return
            
            # Create downloads directory if it doesn't exist
            downloads_dir = Path.home() / "Downloads" / "KMTI_Reviews"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            
            download_path = downloads_dir / original_filename
            shutil.copy2(file_path, download_path)
            
            self._show_snackbar(f"Downloaded: {original_filename}", ft.Colors.GREEN)
            log_file_operation(self.username, "DOWNLOAD", original_filename, "SUCCESS")
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            self._show_snackbar("Error downloading file", ft.Colors.RED)
    
    def _handle_open_file(self, file_data: Dict):
        """Handle file opening."""
        try:
            file_path = file_data.get('file_path')
            original_filename = file_data.get('original_filename', 'unknown_file')
            
            if not file_path or not os.path.exists(file_path):
                self._show_snackbar("File not found in storage", ft.Colors.RED)
                return
            
            # Open file with system default application
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.run(["open", file_path], check=True)
            else:
                subprocess.run(["xdg-open", file_path], check=True)
            
            self._show_snackbar(f"Opening: {original_filename}", ft.Colors.BLUE)
            log_file_operation(self.username, "OPEN", original_filename, "SUCCESS")
            
        except Exception as e:
            print(f"Error opening file: {e}")
            self._show_snackbar("Error opening file", ft.Colors.RED)
    
    def _handle_add_comment(self, file_data: Dict, comment_field: ft.TextField):
        """Handle adding comment to file."""
        try:
            comment_text = comment_field.value
            if not comment_text or not comment_text.strip():
                self._show_snackbar("Please enter a comment", ft.Colors.ORANGE)
                return
            
            success, message = self.tl_service.add_comment_to_file(
                file_data['file_id'], self.username, comment_text
            )
            
            if success:
                comment_field.value = ""
                comment_field.update()
                self._show_snackbar("Comment added successfully", ft.Colors.GREEN)
                log_activity(self.username, f"Added comment to file: {file_data.get('original_filename')}")
            else:
                self._show_snackbar(f"Failed to add comment: {message}", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error adding comment: {e}")
            self._show_snackbar("Error adding comment", ft.Colors.RED)
    
    def _handle_approve_file(self, file_data: Dict):
        """Handle file approval."""
        try:
            success, message = self.tl_service.approve_as_team_leader(
                file_data['file_id'], self.username
            )
            
            if success:
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' approved and sent to admin!", ft.Colors.GREEN)
                log_activity(self.username, f"Approved file: {filename}")
                
                self._clear_selection()
                self.refresh_files_table()
                
            else:
                self._show_snackbar(f"Failed to approve: {message}", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error approving file: {e}")
            self._show_snackbar("Error approving file", ft.Colors.RED)
    
    def _handle_reject_file(self, file_data: Dict, reason_field: ft.TextField):
        """Handle file rejection."""
        try:
            reason = reason_field.value
            if not reason or not reason.strip():
                self._show_snackbar("Please provide a reason for rejection", ft.Colors.ORANGE)
                return
            
            success, message = self.tl_service.reject_as_team_leader(
                file_data['file_id'], self.username, reason
            )
            
            if success:
                filename = file_data.get('original_filename', 'Unknown')
                self._show_snackbar(f"File '{filename}' rejected", ft.Colors.RED)
                log_activity(self.username, f"Rejected file: {filename} - Reason: {reason}")
                
                self._clear_selection()
                self.refresh_files_table()
                
            else:
                self._show_snackbar(f"Failed to reject: {message}", ft.Colors.RED)
                
        except Exception as e:
            print(f"Error rejecting file: {e}")
            self._show_snackbar("Error rejecting file", ft.Colors.RED)
    
    def _clear_selection(self):
        """Clear current file selection."""
        self.selected_file = None
        self.preview_panel.controls.clear()
        self.preview_panel.controls.extend([
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ])
        self.preview_panel.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.preview_panel.alignment = ft.MainAxisAlignment.CENTER
    
    def _create_error_interface(self, error_msg: str) -> ft.Container:
        """Create error interface."""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                ft.Text("Team Leader Panel", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Error loading review system", size=16, color=ft.Colors.RED),
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
        self.files_table.rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text("No pending files for review", style=ft.TextStyle(italic=True))),
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
    
    def _show_snackbar(self, message: str, color: str):
        """Show snackbar message."""
        try:
            if color == ft.Colors.GREEN:
                icon = ft.Icons.CHECK_CIRCLE
            elif color == ft.Colors.ORANGE:
                icon = ft.Icons.WARNING
            elif color == ft.Colors.RED:
                icon = ft.Icons.ERROR
            else:
                icon = ft.Icons.INFO
            
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
        except Exception as e:
            print(f"Error showing snackbar: {e}")
    
    # Event handlers
    def _on_search_changed(self, e):
        """Handle search input change."""
        try:
            self.search_query = e.control.value.lower()
            self.refresh_files_table()
        except Exception as error:
            print(f"Error handling search change: {error}")
    
    def _on_sort_changed(self, e):
        """Handle sort option change."""
        try:
            self.current_sort = e.control.value
            self.refresh_files_table()
        except Exception as error:
            print(f"Error handling sort change: {error}")


def TLPanel(page: ft.Page, username: str):
    """Team Leader Panel - Main Entry Point."""
    page.title = "KMTI Data Management System - Team Leader"
    page.bgcolor = ft.Colors.GREY_100
    page.padding = 0

    content = ft.Column(expand=True, spacing=0)

    def on_logout():
        from login_window import clear_session
        log_logout(username, "TEAM_LEADER")
        clear_session(username)
        page.clean()
        from login_window import login_view
        login_view(page)

    # Navigation bar
    navbar = ft.Container(
        bgcolor=ft.Colors.GREY_800,
        padding=10,
        margin=0,
        content=ft.Row(
            controls=[
                ft.Container(expand=True),  
                ft.Row(
                    controls=[
                        ft.Text(f"Hi, {username}", size=16, color=ft.Colors.WHITE),
                        ft.TextButton(
                            content=ft.Text("Logout", size=16, color=ft.Colors.WHITE),
                            on_click=lambda e: on_logout(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    def show_team_leader_panel():
        """Show the independent team leader panel."""
        content.controls.clear()
        try:
            tl_panel = TeamLeaderPanel(page, username)
            content.controls.append(tl_panel.create_interface())
        except Exception as ex:
            print(f"[ERROR] Failed to load Team Leader Panel: {ex}")
            content.controls.append(
                ft.Container(
                    content=ft.Text(
                        f"Error loading panel: {ex}", color=ft.Colors.RED
                    )
                )
            )
        content.update()

    page.add(navbar, content)
    show_team_leader_panel()
