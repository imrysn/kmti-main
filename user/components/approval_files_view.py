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
    """Files view component for approval system with FILE CARD LAYOUT DESIGN"""
    
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
        self.file_count_text_ref = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def get_file_type_info(self, filename: str):
        """Get file type icon and color based on filename extension"""
        extension = filename.split('.')[-1].upper() if '.' in filename else 'FILE'
        
        if extension in ["JPG", "JPEG", "PNG", "GIF", "BMP", "WEBP"]:
            return ft.Icons.IMAGE_ROUNDED, ft.Colors.WHITE, ft.Colors.GREEN
        elif extension == "PDF":
            return ft.Icons.PICTURE_AS_PDF_ROUNDED, ft.Colors.WHITE, ft.Colors.RED
        elif extension in ["DOC", "DOCX", "TXT", "RTF"]:
            return ft.Icons.DESCRIPTION_ROUNDED, ft.Colors.WHITE, ft.Colors.BLUE
        elif extension in ["ZIP", "RAR", "7Z"]:
            return ft.Icons.ARCHIVE_ROUNDED, ft.Colors.WHITE, ft.Colors.ORANGE
        elif extension in ["MP4", "AVI", "MOV", "WMV"]:
            return ft.Icons.VIDEO_FILE_ROUNDED, ft.Colors.WHITE, ft.Colors.PURPLE
        elif extension in ["MP3", "WAV", "FLAC", "OGG"]:
            return ft.Icons.AUDIO_FILE_ROUNDED, ft.Colors.WHITE, ft.Colors.PINK
        elif extension in ["XLS", "XLSX", "CSV"]:
            return ft.Icons.TABLE_CHART_ROUNDED, ft.Colors.WHITE, ft.Colors.GREEN_700
        elif extension in ["PPT", "PPTX"]:
            return ft.Icons.SLIDESHOW_ROUNDED, ft.Colors.WHITE, ft.Colors.ORANGE_700
        else:
            return ft.Icons.INSERT_DRIVE_FILE_ROUNDED, ft.Colors.WHITE, ft.Colors.GREY_600
    
    def format_file_size(self, file_size: int) -> str:
        """Format file size for display"""
        if file_size > 1024 * 1024:
            return f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            return f"{file_size / 1024:.1f} KB"
        else:
            return f"{file_size} bytes"
    
    def get_status_details(self, status: str):
        """Get status icon, color and text"""
        status_map = {
            "pending": (ft.Icons.SCHEDULE, ft.Colors.ORANGE, "Pending Review"),
            "approved": (ft.Icons.VERIFIED, ft.Colors.GREEN, "Approved"),
            "rejected": (ft.Icons.CANCEL, ft.Colors.RED, "Rejected"),
            "changes_requested": (ft.Icons.EDIT, ft.Colors.BLUE, "Changes Requested")
        }
        return status_map.get(status, (ft.Icons.HELP, ft.Colors.GREY, "Unknown"))
    
    def create_submission_card(self, submission: Dict):
        """Create a file card similar to Files view layout"""
        filename = submission.get("original_filename", "Unknown")
        status = submission.get("status", "pending")
        file_size = submission.get("file_size", 0)
        
        # Get file type info
        icon, icon_color, badge_color = self.get_file_type_info(filename)
        
        # Get status details
        status_icon, status_color, status_text = self.get_status_details(status)
        
        # File icon container
        file_icon = ft.Container(
            content=ft.Icon(icon, color=icon_color, size=24),
            bgcolor=badge_color,
            width=50,
            height=50,
            border_radius=8,
            alignment=ft.alignment.center
        )
        
        # File info
        file_name_text = ft.Text(
            filename, 
            size=14,
            weight=ft.FontWeight.W_500, 
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1
        )
        
        file_size_text = ft.Text(
            self.format_file_size(file_size), 
            size=12,
            color=ft.Colors.GREY_600
        )
        
        file_info_column = ft.Column(
            controls=[file_name_text, file_size_text],
            spacing=2, 
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Status display
        status_display = ft.Container(
            content=ft.Row([
                ft.Icon(status_icon, color=status_color, size=16),
                ft.Text(status_text, size=12, color=status_color, weight=ft.FontWeight.BOLD)
            ], spacing=5),
            margin=ft.margin.only(right=15)
        )
        
        # Action buttons based on status
        action_buttons = []
        
        if status == "pending":
            # Withdraw button
            def handle_withdraw(e, fn=filename):
                e.control.page.update()
                self.confirm_withdraw(fn)
            
            withdraw_button = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.REMOVE_CIRCLE, size=16),
                    ft.Text("Withdraw", size=12)
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                on_click=handle_withdraw,
                bgcolor=ft.Colors.RED_50,
                color=ft.Colors.RED_700,
                height=35,
                width=100,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    elevation=0
                )
            )
            action_buttons.append(withdraw_button)
            
        elif status in ["rejected", "changes_requested"]:
            # Resubmit button
            def handle_resubmit(e, sub=submission):
                e.control.page.update()
                self.show_resubmit_dialog(sub)
            
            resubmit_button = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.REFRESH, size=16),
                    ft.Text("Resubmit", size=12)
                ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
                on_click=handle_resubmit,
                bgcolor=ft.Colors.BLUE_50,
                color=ft.Colors.BLUE_700,
                height=35,
                width=100,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    elevation=0
                )
            )
            action_buttons.append(resubmit_button)
        
        # Details button (always present)
        def handle_details(e, sub=submission):
            e.control.page.update()
            self.show_submission_details(sub)
        
        details_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.VISIBILITY, size=16),
                ft.Text("Details", size=12)
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            on_click=handle_details,
            bgcolor=ft.Colors.GREY_100,
            color=ft.Colors.GREY_700,
            height=35,
            width=90,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0
            )
        )
        action_buttons.append(details_button)
        
        # Action buttons container
        action_buttons_container = ft.Container(
            content=ft.Row(
                controls=action_buttons + [ft.Container(width=10)] if len(action_buttons) > 1 else action_buttons,
                spacing=10
            ),
            on_click=lambda e: None,  # Absorb clicks
            ink=False
        )
        
        # Main content row
        main_row = ft.Row([
            file_icon,
            ft.Container(width=15),
            ft.Container(
                content=file_info_column,
                expand=True,
                alignment=ft.alignment.center_left
            ),
            status_display,
            action_buttons_container
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Final card container
        return ft.Container(
            content=main_row,
            padding=ft.padding.all(20),
            margin=ft.margin.only(bottom=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            ink=False
        )
    
    def separate_submissions_by_status(self, submissions):
        """Separate submissions by status"""
        pending_submissions = [s for s in submissions if s.get("status") == "pending"]
        approved_submissions = [s for s in submissions if s.get("status") == "approved"]
        rejected_submissions = [s for s in submissions if s.get("status") == "rejected"]
        changes_requested = [s for s in submissions if s.get("status") == "changes_requested"]
        
        return {
            "pending": pending_submissions,
            "approved": approved_submissions,
            "rejected": rejected_submissions,
            "changes_requested": changes_requested
        }
    
    def create_section_header(self, title: str, count: int, icon: str, color: str):
        """Create section header similar to Files view"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=20),
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(f"({count})", size=14, color=ft.Colors.GREY_600)
            ], spacing=8),
            margin=ft.margin.only(bottom=10, top=5)
        )
    
    def create_empty_state(self):
        """Create empty state when no submissions exist"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.Icon(ft.Icons.UPLOAD_FILE, size=64, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.Text("No file submissions yet", size=16, color=ft.Colors.GREY_600),
                ft.Text("Upload files in the Files page, then submit them for approval", size=12, color=ft.Colors.GREY_500),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Go to Files",
                    icon=ft.Icons.FOLDER,
                    on_click=lambda e: self.navigation['show_files']() if self.navigation else None,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE
                ),
                ft.Container(height=40)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            height=300
        )
    
    def create_stats_summary(self):
        """Create statistics summary cards"""
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
                width=130,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=2,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 1)
                )
            )
        
        self.stats_ref = ft.Row([
            create_stat_card("Pending", pending_count, ft.Icons.SCHEDULE, ft.Colors.ORANGE),
            create_stat_card("Approved", approved_count, ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN),
            create_stat_card("Changes Req.", changes_count, ft.Icons.EDIT, ft.Colors.BLUE),
            create_stat_card("Rejected", rejected_count, ft.Icons.CANCEL, ft.Colors.RED)
        ], spacing=15, alignment=ft.MainAxisAlignment.CENTER)
        
        return ft.Container(
            content=self.stats_ref,
            margin=ft.margin.only(bottom=25)
        )

    def create_submissions_list(self):
        """Create submissions list with card-based design similar to Files view"""
        submissions = self.approval_service.get_user_submissions()
        
        # Sort submissions by submission date (newest first)
        submissions = sorted(submissions, key=lambda x: x.get("submission_date", ""), reverse=True)
        
        file_count = len(submissions)
        file_count_text = f"{file_count} submission{'s' if file_count != 1 else ''}"
        
        self.file_count_text_ref = ft.Text(file_count_text, size=12, color=ft.Colors.GREY_600)
        
        # Create file cards organized by status
        file_cards = []
        
        if submissions:
            # Separate by status
            status_groups = self.separate_submissions_by_status(submissions)
            
            # Add sections in order: Pending, Changes Requested, Rejected, Approved
            sections = [
                ("pending", "Pending Review", ft.Icons.SCHEDULE, ft.Colors.ORANGE),
                ("changes_requested", "Changes Requested", ft.Icons.EDIT, ft.Colors.BLUE),
                ("rejected", "Rejected", ft.Icons.CANCEL, ft.Colors.RED),
                ("approved", "Approved", ft.Icons.VERIFIED, ft.Colors.GREEN)
            ]
            
            sections_added = 0
            for status_key, title, icon, color in sections:
                status_submissions = status_groups.get(status_key, [])
                if status_submissions:
                    # Add spacing between sections (except first)
                    if sections_added > 0:
                        file_cards.append(ft.Container(height=20))
                    
                    # Section header
                    section_header = self.create_section_header(title, len(status_submissions), icon, color)
                    file_cards.append(section_header)
                    
                    # Add submission cards
                    for submission in status_submissions:
                        file_cards.append(self.create_submission_card(submission))
                    
                    sections_added += 1
        else:
            file_cards.append(self.create_empty_state())
        
        # Create scrollable content
        scrollable_content = ft.Column(file_cards, spacing=0)
        self.submissions_container_ref = ft.Container(
            content=scrollable_content,
            expand=True
        )
        
        # Header container
        header_container = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approvals", size=20, weight=ft.FontWeight.BOLD),
                    self.file_count_text_ref
                ], spacing=4),
                ft.Container(expand=True),
                ft.Text(
                    "💡 Submit files from the Files page",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            ]),
            margin=ft.margin.only(bottom=20)
        )
        
        # Main column with stats at the top
        main_column = ft.Column([
            # Statistics summary at the top
            self.create_stats_summary(),
            
            header_container,
            
            # Files list container
            ft.Container(
                content=ft.Column([
                    self.submissions_container_ref
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True,
                bgcolor=ft.Colors.GREY_50,
                padding=ft.padding.all(15),
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200)
            )
        ], expand=True)
        
        return ft.Container(
            content=main_column,
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(20),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            expand=True
        )
    
    def refresh_content(self):
        """Refresh submissions display and stats"""
        # Refresh stats
        if self.stats_ref:
            submissions = self.approval_service.get_user_submissions()
            
            # Count by status
            pending_count = len([s for s in submissions if s.get("status") == "pending"])
            approved_count = len([s for s in submissions if s.get("status") == "approved"])
            rejected_count = len([s for s in submissions if s.get("status") == "rejected"])
            changes_count = len([s for s in submissions if s.get("status") == "changes_requested"])
            
            # Update stat cards
            if len(self.stats_ref.controls) >= 4:
                self.stats_ref.controls[0].content.controls[1].value = str(pending_count)  # Pending count
                self.stats_ref.controls[1].content.controls[1].value = str(approved_count)  # Approved count
                self.stats_ref.controls[2].content.controls[1].value = str(changes_count)  # Changes count  
                self.stats_ref.controls[3].content.controls[1].value = str(rejected_count)  # Rejected count
        
        # Refresh submissions list
        if self.submissions_container_ref:
            # Get updated submissions
            submissions = self.approval_service.get_user_submissions()
            submissions = sorted(submissions, key=lambda x: x.get("submission_date", ""), reverse=True)
            
            # Update file count
            file_count = len(submissions)
            file_count_text = f"{file_count} submission{'s' if file_count != 1 else ''}"
            if self.file_count_text_ref:
                self.file_count_text_ref.value = file_count_text
            
            # Rebuild content
            file_cards = []
            
            if submissions:
                status_groups = self.separate_submissions_by_status(submissions)
                sections = [
                    ("pending", "Pending Review", ft.Icons.SCHEDULE, ft.Colors.ORANGE),
                    ("changes_requested", "Changes Requested", ft.Icons.EDIT, ft.Colors.BLUE),
                    ("rejected", "Rejected", ft.Icons.CANCEL, ft.Colors.RED),
                    ("approved", "Approved", ft.Icons.VERIFIED, ft.Colors.GREEN)
                ]
                
                sections_added = 0
                for status_key, title, icon, color in sections:
                    status_submissions = status_groups.get(status_key, [])
                    if status_submissions:
                        if sections_added > 0:
                            file_cards.append(ft.Container(height=20))
                        
                        section_header = self.create_section_header(title, len(status_submissions), icon, color)
                        file_cards.append(section_header)
                        
                        for submission in status_submissions:
                            file_cards.append(self.create_submission_card(submission))
                        
                        sections_added += 1
            else:
                file_cards.append(self.create_empty_state())
            
            # Update container content
            self.submissions_container_ref.content = ft.Column(file_cards, spacing=0)
            self.page.update()
    
    def confirm_withdraw(self, filename: str):
        """Confirm withdrawal of submission"""
        def handle_withdraw():
            if self.approval_service.withdraw_submission(filename):
                self.refresh_content()
                self.dialogs.show_success_notification(f"Withdrawn: {filename}")
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
        
        # Create details content
        details_content = ft.Column([
            ft.Text(f"File: {submission['original_filename']}", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(f"Status: {self.get_status_details(submission.get('status', 'unknown'))[2]}", size=12),
            ft.Text(f"Size: {self.format_file_size(submission.get('file_size', 0))}", size=12),
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
    
    def create_content(self):
        """Create the main approval files content with CONSISTENT UI DESIGN"""
        return ft.Container(
            content=ft.Column([
                # Back button - CONSISTENT DESIGN
                self.shared.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None,
                    text="Back"
                ),
                
                # Main content layout - CONSISTENT WITH IMAGE 1
                ft.Container(
                    content=ft.Row([
                        # Left sidebar - CONSISTENT USER INFO CARD + NAVIGATION  
                        ft.Container(
                            content=self.shared.create_user_sidebar("approvals"),
                            width=200
                        ),
                        
                        ft.Container(width=20),
                        
                        # Right side - Approval content with FILES LAYOUT
                        ft.Container(
                            content=self.create_submissions_list(),
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