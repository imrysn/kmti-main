import flet as ft
import os
from datetime import datetime
from ..services.approval_file_service import ApprovalFileService
from .shared_ui import SharedUI
from typing import Dict, Optional

class NotificationsView:
    """Notifications view with CONSISTENT UI DESIGN"""
    
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
        
        # UI references
        self.notifications_container_ref = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def _extract_comment_author(self, notification: Dict) -> str:
        """🚨 NEW: Extract comment author with fallback logic"""
        # Try multiple fields for comment author
        author_fields = ['comment_author', 'admin_id', 'tl_id', 'user_id']
        for field in author_fields:
            author = notification.get(field)
            if author and author.strip() and author.lower() != 'unknown':
                return author
        
        print(f"[WARNING] Could not extract comment author from notification: {notification}")
        return "Unknown"
    
    def _extract_role_display(self, notification: Dict) -> str:
        """🚨 NEW: Extract role display with fallback logic"""
        # Try explicit role_display first
        role_display = notification.get('role_display')
        if role_display and role_display.strip():
            return role_display
        
        # Try comment_author_role and convert to display format
        comment_author_role = notification.get('comment_author_role')
        if comment_author_role:
            role_map = {
                'admin': 'Admin',
                'team_leader': 'Team Leader',
                'user': 'User'
            }
            return role_map.get(comment_author_role, comment_author_role.replace('_', ' ').title())
        
        # Try to determine from other fields
        if notification.get('admin_id'):
            return 'Admin'
        elif notification.get('tl_id'):
            return 'Team Leader'
        elif notification.get('user_id'):
            return 'User'
        
        print(f"[WARNING] Could not extract role display from notification: {notification}")
        return "Unknown"
    
    def _extract_comment_text(self, notification: Dict) -> str:
        """🚨 NEW: Extract comment text with fallback logic"""
        # Try multiple fields for comment text
        text_fields = ['comment', 'text', 'message']
        for field in text_fields:
            text = notification.get(field)
            if text and text.strip():
                return text
        
        return "No comment text"
    
    def create_notification_card(self, notification: Dict, index: int):
        """Create card for a notification"""
        is_read = notification.get("read", False)
        
        def mark_read(e):
            self.approval_service.mark_notification_read(index)
            self.refresh_notifications()
        
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(notification["timestamp"]).strftime("%Y-%m-%d %H:%M")
        except:
            timestamp = "Unknown"
        
        # 🚨 FIXED: Get notification message with proper comment author display
        if notification["type"] == "status_update":
            # Use the formatted status transition if available
            if notification.get("status_transition"):
                message = f"Status: {notification['status_transition']}"
            else:
                # Fallback to old format but improved
                old_status = notification.get('old_status', 'unknown').replace('_', ' ').title()
                new_status = notification.get('new_status', 'unknown').replace('_', ' ').title()
                message = f"Status: {old_status} → {new_status}"
            
            # Add comment if provided
            if notification.get("comment"):
                message += f"\n💬 {notification['comment']}"
            
            # Add source system info
            source = notification.get("source_system", "admin")
            if source == "team_leader":
                message += "\n👥 Updated by Team Leader"
            elif source == "admin":
                message += "\n⚡ Updated by Admin"
        elif notification["type"] == "comment_added":
            # 🚨 ENHANCED: Handle comment notifications with better data validation
            comment_author = self._extract_comment_author(notification)
            role_display = self._extract_role_display(notification)
            comment_text = self._extract_comment_text(notification)
            
            # Create properly formatted message
            if comment_author != "Unknown" and role_display != "Unknown":
                message = f"[{role_display}] {comment_author} commented: \"{comment_text}\""
            else:
                # Fallback for malformed notifications
                message = f"New comment: \"{comment_text}\""
                print(f"[DEBUG] Malformed comment notification data: {notification}")
        else:
            message = notification.get("message", "Notification received")
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CIRCLE if not is_read else ft.Icons.RADIO_BUTTON_UNCHECKED,
                    size=16, 
                    color=ft.Colors.BLUE if not is_read else ft.Colors.GREY_300
                ),
                ft.Column([
                    ft.Text(
                        notification.get("filename", "Unknown file"), 
                        size=14, 
                        weight=ft.FontWeight.BOLD if not is_read else ft.FontWeight.NORMAL
                    ),
                    ft.Text(message, size=12, color=ft.Colors.GREY_700),
                    ft.Row([
                        ft.Icon(
                            ft.Icons.SUPERVISOR_ACCOUNT if notification.get("source_system") == "team_leader" or notification.get("comment_author_role") == "team_leader" else ft.Icons.ADMIN_PANEL_SETTINGS,
                            size=12, 
                            color=ft.Colors.BLUE_600 if notification.get("source_system") == "team_leader" or notification.get("comment_author_role") == "team_leader" else ft.Colors.GREEN_600
                        ),
                        ft.Text(
                            f"{notification.get('admin_id') or notification.get('comment_author', 'System')} • {timestamp}", 
                            size=10, 
                            color=ft.Colors.GREY_500
                        )
                    ], spacing=4)
                ], spacing=2, expand=True),
                ft.ElevatedButton(
                    "Mark Read" if not is_read else "Read",
                    on_click=mark_read if not is_read else None,
                    disabled=is_read,
                    bgcolor=ft.Colors.BLUE_100 if not is_read else ft.Colors.GREY_100,
                    color=ft.Colors.BLUE_700 if not is_read else ft.Colors.GREY_500
                ) if not is_read else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.BLUE_50 if not is_read else ft.Colors.WHITE,
            border=ft.border.all(
                1, 
                ft.Colors.BLUE_200 if not is_read else ft.Colors.GREY_200
            ),
            border_radius=8,
            padding=15,
            margin=ft.margin.only(bottom=10)
        )
    
    def create_notifications_content(self):
        """Create notifications content"""
        notifications = self.approval_service.load_notifications()
        
        if not notifications:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No notifications", size=16, color=ft.Colors.GREY_600),
                    ft.Text("Approval status updates and admin comments will appear here", 
                           size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=300
            )
            
            self.notifications_container_ref = ft.Container(content=empty_state)
        else:
            notification_cards = [
                self.create_notification_card(notif, i) 
                for i, notif in enumerate(notifications)
            ]
            
            self.notifications_container_ref = ft.Container(
                content=ft.Column(
                    notification_cards,
                    scroll=ft.ScrollMode.AUTO
                ),
                expand=True
            )
        
        return self.notifications_container_ref
    
    def refresh_notifications(self):
        """Refresh notifications display"""
        if self.notifications_container_ref:
            new_content = self.create_notifications_content()
            self.notifications_container_ref.content = new_content.content
            self.page.update()
    
    def mark_all_notifications_read(self):
        """Mark all notifications as read"""
        notifications = self.approval_service.load_notifications()
        for notification in notifications:
            notification["read"] = True
        self.approval_service.save_notifications(notifications)
        self.refresh_notifications()
    
    def create_header_section(self):
        """Create header with stats and actions"""
        notifications = self.approval_service.load_notifications()
        total_count = len(notifications)
        unread_count = len([n for n in notifications if not n.get("read", False)])
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Notifications", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{unread_count} unread of {total_count} total", size=12, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Mark All Read",
                    icon=ft.Icons.DONE_ALL,
                    on_click=lambda e: self.mark_all_notifications_read(),
                    disabled=unread_count == 0,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE
                ) if unread_count > 0 else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=15)
        )
    
    def create_main_content(self):
        """Create main notifications content"""
        return ft.Container(
            content=ft.Column([
                # Header section
                self.create_header_section(),
                
                # Notifications content
                self.create_notifications_content()
            ], expand=True),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            padding=20,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_content(self):
        """Create the main notifications content with CONSISTENT UI DESIGN"""
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
                            content=self.shared.create_user_sidebar("notifications"),
                            width=200
                        ),
                        
                        ft.Container(width=20),
                        
                        # Right side - Notifications content
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