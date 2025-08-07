import flet as ft
import os
import time
import threading
from datetime import datetime
from ..services.approval_file_service import ApprovalFileService
from .shared_ui import SharedUI
from .dialogs import DialogManager
from typing import Dict

class ApprovalFilesView:
    """Files view component for approval system - submissions only"""
    
    def __init__(self, page: ft.Page, username: str, approval_service: ApprovalFileService):
        self.page = page
        self.username = username
        self.approval_service = approval_service
        
        # Load user profile for shared components
        from ..services.profile_service import ProfileService
        profile_service = ProfileService(approval_service.user_folder, username)
        self.user_data = profile_service.load_profile()
        
        self.navigation = None
        self.shared = SharedUI(page, username, self.user_data)
        self.dialogs = DialogManager(page, username)
        
        # UI references
        self.submissions_container_ref = None
        self.stats_ref = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def create_stats_summary(self):
        """Create statistics summary"""
        submissions = self.approval_service.get_user_submissions()
        
        # Count by status
        pending_count = len([s for s in submissions if s.get("status") == "pending"])
        approved_count = len([s for s in submissions if s.get("status") == "approved"])
        rejected_count = len([s for s in submissions if s.get("status") == "rejected"])
        changes_count = len([s for s in submissions if s.get("status") == "changes_requested"])
        
        def create_stat_card(title: str, count: int, icon: str, color: str):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=32, color=color),
                    ft.Text(str(count), size=24, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_200),
                border_radius=8,
                padding=15,
                width=130
            )
        
        self.stats_ref = ft.Row([
            create_stat_card("Pending", pending_count, ft.Icons.SCHEDULE, ft.Colors.ORANGE),
            create_stat_card("Approved", approved_count, ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN),
            create_stat_card("Changes Req.", changes_count, ft.Icons.EDIT, ft.Colors.BLUE),
            create_stat_card("Rejected", rejected_count, ft.Icons.CANCEL, ft.Colors.RED)
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Container(
            content=self.stats_ref,
            margin=ft.margin.only(bottom=20)
        )
    
    def get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            "pending": ft.Colors.ORANGE,
            "approved": ft.Colors.GREEN,
            "rejected": ft.Colors.RED,
            "changes_requested": ft.Colors.BLUE,
            "not_submitted": ft.Colors.GREY
        }
        return colors.get(status, ft.Colors.GREY)
    
    def get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "pending": ft.Icons.SCHEDULE,
            "approved": ft.Icons.CHECK_CIRCLE,
            "rejected": ft.Icons.CANCEL,
            "changes_requested": ft.Icons.EDIT,
            "not_submitted": ft.Icons.UPLOAD_FILE
        }
        return icons.get(status, ft.Icons.HELP)
    
    def format_status_text(self, status: str) -> str:
        """Format status text for display"""
        status_map = {
            "pending": "Pending Review",
            "approved": "Approved",
            "rejected": "Rejected",
            "changes_requested": "Changes Requested",
            "not_submitted": "Not Submitted"
        }
        return status_map.get(status, status.title())
    
    def create_submission_card(self, submission: Dict):
        """Create card for a submission"""
        status = submission.get("status", "unknown")
        
        def show_details(e):
            self.show_submission_details(submission)
        
        def withdraw_submission(e):
            if submission.get("status") == "pending":
                self.confirm_withdraw(submission["original_filename"])
        
        def resubmit_file(e):
            if submission.get("status") in ["rejected", "changes_requested"]:
                self.show_resubmit_dialog(submission)
        
        # Action buttons based on status
        action_buttons = []
        if status == "pending":
            action_buttons.append(
                ft.ElevatedButton(
                    "Withdraw",
                    icon=ft.Icons.REMOVE_CIRCLE,
                    on_click=withdraw_submission,
                    bgcolor=ft.Colors.RED_100,
                    color=ft.Colors.RED_700
                )
            )
        elif status in ["rejected", "changes_requested"]:
            action_buttons.append(
                ft.ElevatedButton(
                    "Resubmit",
                    icon=ft.Icons.REFRESH,
                    on_click=resubmit_file,
                    bgcolor=ft.Colors.BLUE_100,
                    color=ft.Colors.BLUE_700
                )
            )
        
        action_buttons.append(
            ft.TextButton(
                "View Details",
                icon=ft.Icons.VISIBILITY,
                on_click=show_details,
                style=ft.ButtonStyle(color=ft.Colors.BLUE_700)
            )
        )
        
        # Format dates
        try:
            submission_date = datetime.fromisoformat(submission["submission_date"]).strftime('%Y-%m-%d %H:%M') if submission.get("submission_date") else "Unknown"
        except:
            submission_date = "Unknown"
        
        # Format file size
        file_size = submission.get("file_size", 0)
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DESCRIPTION, size=20, color=ft.Colors.BLUE_700),
                    ft.Column([
                        ft.Text(submission["original_filename"], size=14, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Size: {size_str} • Submitted: {submission_date}", 
                                size=11, color=ft.Colors.GREY_600)
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(self.get_status_icon(status), size=16, color=self.get_status_color(status)),
                            ft.Text(self.format_status_text(status), size=12, color=self.get_status_color(status))
                        ], spacing=5),
                        bgcolor=f"{self.get_status_color(status)}20",
                        border_radius=15,
                        padding=ft.padding.symmetric(horizontal=10, vertical=5)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Description and tags if available
                ft.Container(height=5),
                ft.Text(submission.get("description", "No description"), size=12, color=ft.Colors.GREY_700, max_lines=2),
                
                # Tags
                ft.Row([
                    ft.Text("Tags:", size=10, color=ft.Colors.GREY_500),
                    ft.Text(", ".join(submission.get("tags", [])) or "None", size=10, color=ft.Colors.GREY_600)
                ], spacing=5) if submission.get("tags") else ft.Container(),
                
                # Action buttons
                ft.Container(height=10),
                ft.Row(action_buttons, spacing=10)
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            padding=15,
            margin=ft.margin.only(bottom=10)
        )
    
    def create_submissions_view(self):
        """Create submissions view"""
        submissions = self.approval_service.get_user_submissions()
        
        if not submissions:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.UPLOAD_FILE, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No file submissions yet", size=16, color=ft.Colors.GREY_600),
                    ft.Text("Upload files in the Files page, then submit them for approval", 
                           size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Go to Files",
                        icon=ft.Icons.FOLDER,
                        on_click=lambda e: self.navigation['show_files']() if self.navigation else None,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=300
            )
            
            self.submissions_container_ref = ft.Container(content=empty_state)
        else:
            submission_cards = [self.create_submission_card(sub) for sub in submissions]
            
            self.submissions_container_ref = ft.Container(
                content=ft.Column(
                    submission_cards,
                    scroll=ft.ScrollMode.AUTO
                ),
                expand=True
            )
        
        return self.submissions_container_ref
    
    def refresh_stats(self):
        """Refresh statistics"""
        if self.stats_ref:
            new_stats = self.create_stats_summary()
            self.stats_ref.controls = new_stats.content.controls
            self.page.update()
    
    def refresh_content(self):
        """Refresh current content"""
        self.refresh_stats()
        self.refresh_submissions()
    
    def refresh_submissions(self):
        """Refresh submissions display"""
        if self.submissions_container_ref:
            new_content = self.create_submissions_view()
            self.submissions_container_ref.content = new_content.content
            self.page.update()
    
    def confirm_withdraw(self, filename: str):
        """Confirm withdrawal of submission"""
        def handle_withdraw():
            if self.approval_service.withdraw_submission(filename):
                self.dialogs.show_success_notification(f"Withdrawn: {filename}")
                self.refresh_content()
            else:
                self.dialogs.show_error_notification("Failed to withdraw submission")
        
        self.dialogs.show_confirmation_dialog(
            title="Withdraw Submission",
            message=f"Are you sure you want to withdraw '{filename}'?\nThis cannot be undone.",
            on_confirm=handle_withdraw,
            confirm_text="Withdraw",
            is_destructive=True
        )
    
    def show_resubmit_dialog(self, submission: Dict):
        """Show resubmit dialog with updated description and tags"""
        def handle_resubmit(values):
            description = values.get("description", "")
            tags_str = values.get("tags", "")
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []
            
            if self.approval_service.resubmit_file(submission["original_filename"], description, tags):
                self.dialogs.show_success_notification(f"Resubmitted: {submission['original_filename']}")
                self.refresh_content()
            else:
                self.dialogs.show_error_notification("Failed to resubmit file")
        
        fields = [
            {
                "key": "description",
                "type": "multiline",
                "label": "Updated Description",
                "value": submission.get("description", ""),
                "min_lines": 2,
                "max_lines": 4
            },
            {
                "key": "tags",
                "type": "text",
                "label": "Updated Tags (comma-separated)",
                "value": ", ".join(submission.get("tags", [])),
                "hint": "e.g., report, draft, urgent"
            }
        ]
        
        self.dialogs.show_input_dialog(
            title=f"Resubmit: {submission['original_filename']}",
            fields=fields,
            on_submit=handle_resubmit,
            submit_text="Resubmit"
        )
    
    def show_submission_details(self, submission: Dict):
        """Show detailed view of submission"""
        # Format status history
        history_items = []
        for entry in submission.get("status_history", []):
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
            except:
                timestamp = "Unknown"
            
            admin_info = f" by {entry.get('admin_id', 'System')}" if entry.get('admin_id') else ""
            comment = f": {entry['comment']}" if entry.get('comment') else ""
            
            history_items.append(
                ft.Container(
                    content=ft.Text(f"• {entry['status'].upper()}{admin_info} - {timestamp}{comment}", size=11),
                    margin=ft.margin.only(bottom=5)
                )
            )
        
        # Admin comments
        comment_items = []
        for comment in submission.get("admin_comments", []):
            try:
                timestamp = datetime.fromisoformat(comment["timestamp"]).strftime("%Y-%m-%d %H:%M")
            except:
                timestamp = "Unknown"
            
            comment_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{comment['admin_id']} - {timestamp}", size=10, weight=ft.FontWeight.BOLD),
                        ft.Text(comment['comment'], size=11)
                    ], spacing=5),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=5,
                    padding=10,
                    margin=ft.margin.only(bottom=5)
                )
            )
        
        # Format file size
        file_size = submission.get("file_size", 0)
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        # Create details content
        details_content = ft.Column([
            ft.Text(f"File: {submission['original_filename']}", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(f"Status: {self.format_status_text(submission.get('status', 'unknown'))}", size=12),
            ft.Text(f"Size: {size_str}", size=12),
            ft.Divider(),
            ft.Text("Description:", size=12, weight=ft.FontWeight.BOLD),
            ft.Text(submission.get("description", "No description"), size=11),
            ft.Text("Tags:", size=12, weight=ft.FontWeight.BOLD),
            ft.Text(", ".join(submission.get("tags", [])) or "None", size=11),
            ft.Divider(),
            ft.Text("Status History:", size=12, weight=ft.FontWeight.BOLD),
            ft.Column(history_items, spacing=0) if history_items else ft.Text("No history available", size=11, color=ft.Colors.GREY_500),
            ft.Divider() if comment_items else ft.Container(),
            ft.Text("Admin Comments:", size=12, weight=ft.FontWeight.BOLD) if comment_items else ft.Container(),
            ft.Column(comment_items, spacing=0) if comment_items else ft.Container()
        ], scroll=ft.ScrollMode.AUTO, spacing=10)
        
        self.dialogs.show_details_dialog(
            title="Submission Details",
            content=details_content,
            width=600,
            height=500
        )
    
    def create_main_content(self):
        """Create main content area - only submissions"""
        content = ft.Column([
            # Statistics summary
            self.create_stats_summary(),
            
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("My Submissions", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Text(
                        "💡 Submit files from the Files page using the Submit button",
                        size=12,
                        color=ft.Colors.GREY_600,
                        italic=True
                    )
                ]),
                margin=ft.margin.only(bottom=15)
            ),
            
            # Submissions content
            self.create_submissions_view()
        ], expand=True)
        
        return ft.Container(
            content=content,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
            padding=20,
            expand=True
        )
    
    def create_content(self):
        """Create the main approval files content"""
        return ft.Container(
            content=ft.Column([
                # Back button
                self.shared.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None,
                    text="Back to Dashboard"
                ),
                
                # Main content card
                ft.Container(
                    content=ft.Row([
                        # Left side - User sidebar
                        ft.Container(
                            content=self.shared.create_user_sidebar("approvals"),
                            alignment=ft.alignment.top_center,
                            width=200
                        ),
                        ft.Container(width=20),
                        # Right side - Approval content
                        ft.Container(
                            content=self.create_main_content(),
                            expand=True
                        )
                    ], alignment=ft.MainAxisAlignment.START, 
                       vertical_alignment=ft.CrossAxisAlignment.START,
                       expand=True),
                    margin=ft.margin.only(left=15, right=15, top=5, bottom=10),
                    expand=True
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0, expand=True),
            alignment=ft.alignment.top_center,
            expand=True
        )