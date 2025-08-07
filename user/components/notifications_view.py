import flet as ft
import os
from datetime import datetime
from ..services.approval_file_service import ApprovalFileService
from .shared_ui import SharedUI
from typing import Dict, Optional

class NotificationsView:
    """Standalone notifications view accessible from header bar"""
    
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
        
        # Get notification message
        if notification["type"] == "status_update":
            message = f"Status changed from '{notification.get('old_status', 'unknown')}' to '{notification.get('new_status', 'unknown')}'"
            if notification.get("comment"):
                message += f"\nComment: {notification['comment']}"
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
                    ft.Text(f"By: {notification.get('admin_id', 'System')} • {timestamp}", 
                            size=10, color=ft.Colors.GREY_500)
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
            border=ft.border.all(1, ft.Colors.BLUE_200 if not is_read else ft.Colors.GREY_200),
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
                           size=12, color=ft.Colors.GREY_500)
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
                    ft.Text("Notifications", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{unread_count} unread of {total_count} total", size=14, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Mark All Read",
                    icon=ft.Icons.DONE_ALL,
                    on_click=lambda e: self.mark_all_notifications_read(),
                    disabled=unread_count == 0
                ) if unread_count > 0 else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=20)
        )
    
    def create_content(self):
        """Create the main notifications content"""
        return ft.Container(
            content=ft.Column([
                # Back button to profile
                ft.Container(
                    content=ft.TextButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda e: self.navigation['show_profile']() if self.navigation else None,
                        style=ft.ButtonStyle(color=ft.Colors.BLACK)
                    ),
                    margin=ft.margin.only(left=10, top=10, bottom=10)
                ),
                
                # Main content
                ft.Container(
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
                    margin=ft.margin.all(20),
                    expand=True
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0, expand=True),
            alignment=ft.alignment.top_center,
            expand=True
        )