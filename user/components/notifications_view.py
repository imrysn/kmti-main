import flet as ft
import os
from datetime import datetime
from ..services.approval_file_service import ApprovalFileService
from .shared_ui import SharedUI
from typing import Dict, Optional

class NotificationsView:
    """Notifications view with CONSISTENT UI DESIGN and improved styling"""
    
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
        """Create card for a notification with improved styling"""
        is_read = notification.get("read", False)
        filename = notification.get("filename", "Unknown file")
        
        def mark_read(e):
            self.approval_service.mark_notification_read(index)
            self.refresh_notifications()
        
        # Handle file name click - navigate to file approvals with highlighting
        def handle_file_click(e):
            print(f"[DEBUG] File clicked from notifications view: {filename}")
            if self.navigation and 'on_notification_file_click' in self.navigation:
                self.navigation['on_notification_file_click'](filename)
        
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
        
        # BUTTON STYLE: Blue button/tag style like in the image
        filename_display = ft.Container(
            content=ft.Text(
                filename, 
                size=14, 
                weight=ft.FontWeight.NORMAL,
                color=ft.Colors.BLUE_700  # Blue text
            ),
            on_click=handle_file_click,
            tooltip=f"Click to view {filename} in File Approvals",
            bgcolor=ft.Colors.BLUE_50,  # Light blue background
            border=ft.border.all(1, ft.Colors.BLUE_300),  # Blue border
            border_radius=6,  # Rounded corners
            padding=ft.padding.symmetric(horizontal=12, vertical=6)  # Button-like padding
        )
        
        return ft.Container(
            content=ft.Row([
                # SIMPLE: Clean read status indicator
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.FIBER_MANUAL_RECORD if not is_read else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        size=12, 
                        color=ft.Colors.BLUE_600 if not is_read else ft.Colors.GREY_400
                    ),
                    width=20,
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    filename_display,  # Use simple clickable filename container
                    ft.Text(message, size=12, color=ft.Colors.GREY_700),
                    ft.Text(f"By: {notification.get('admin_id', 'System')} • {timestamp}", 
                            size=10, color=ft.Colors.GREY_500)
                ], spacing=4, expand=True),
                # SIMPLE: Clean action button
                ft.Container(
                    content=ft.ElevatedButton(
                        "Mark Read" if not is_read else "Read",
                        on_click=mark_read if not is_read else None,
                        disabled=is_read,
                        bgcolor=ft.Colors.BLUE_50 if not is_read else ft.Colors.GREY_100,
                        color=ft.Colors.BLUE_700 if not is_read else ft.Colors.GREY_500,
                        height=32,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6),
                            elevation=0 if is_read else 1
                        )
                    ) if not is_read else ft.Container(),
                    width=80
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            # SIMPLE: Clean card styling without special highlighting
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            padding=16,
            margin=ft.margin.only(bottom=8),
            # SIMPLE: Standard shadow
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1)
            )
        )
    
    def create_notifications_content(self):
        """Create notifications content"""
        notifications = self.approval_service.load_notifications()
        
        if not notifications:
            empty_state = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color=ft.Colors.GREY_400),
                    ft.Container(height=16),
                    ft.Text("No notifications", size=16, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                    ft.Container(height=8),
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
                    ft.Text(f"{unread_count} unread of {total_count} total", size=12, color=ft.Colors.GREY_600),
                    # SIMPLE: Clean hint styling
                    ft.Container(
                        content=ft.Text("💡 Click file names to view in File Approvals", 
                                       size=11, color=ft.Colors.BLUE_600, italic=True),
                        margin=ft.margin.only(top=6)
                    ) if total_count > 0 else ft.Container()
                ], spacing=4),
                ft.Container(expand=True),
                # SIMPLE: Clean mark all button
                ft.ElevatedButton(
                    "Mark All Read",
                    icon=ft.Icons.DONE_ALL,
                    on_click=lambda e: self.mark_all_notifications_read(),
                    disabled=unread_count == 0,
                    bgcolor=ft.Colors.BLUE_600 if unread_count > 0 else ft.Colors.GREY_300,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8),
                        elevation=2 if unread_count > 0 else 0
                    )
                ) if unread_count > 0 else ft.Container()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            margin=ft.margin.only(bottom=20)
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
                spread_radius=0,
                blur_radius=2,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 1)
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