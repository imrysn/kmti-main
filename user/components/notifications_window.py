import flet as ft
import time
import threading
from datetime import datetime
from typing import Dict, Optional, Callable

def show_center_sheet(page: ft.Page, title: str, message: str, on_confirm):
    """
    Creates a custom centered confirmation dialog with CONSISTENT DESIGN to match DialogManager
    """
    def close_overlay(e=None):
        print(f"DEBUG: Closing overlay - Cancel clicked")
        try:
            if overlay in page.overlay:
                page.overlay.remove(overlay)
                print(f"DEBUG: Overlay removed successfully")
            page.update()
        except Exception as ex:
            print(f"DEBUG: Error closing overlay: {ex}")

    def confirm_action(e):
        print(f"DEBUG: Closing overlay - Delete confirmed")
        try:
            if overlay in page.overlay:
                page.overlay.remove(overlay)
                print(f"DEBUG: Overlay removed successfully")
            page.update()
            if on_confirm:
                on_confirm()
        except Exception as ex:
            print(f"DEBUG: Error in confirm action: {ex}")

    # Smart filename truncation for better display
    display_message = _format_delete_message(message)

    overlay = ft.Container(
        content=ft.Container(
            content=ft.Column([
                # Title with consistent height
                ft.Container(
                    content=ft.Text(
                        title, 
                        size=18, 
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_800
                    ),
                    height=30,
                    alignment=ft.alignment.center_left
                ),
                
                ft.Container(height=15),
                
                # Message with fixed height and smart text handling
                ft.Container(
                    content=ft.Text(
                        display_message, 
                        size=14,
                        text_align=ft.TextAlign.LEFT,
                        color=ft.Colors.GREY_700,
                        max_lines=4,  # Allow up to 4 lines
                        overflow=ft.TextOverflow.VISIBLE
                    ),
                    height=90,  # Increased height to accommodate 4 lines
                    width=440,
                    alignment=ft.alignment.top_left,
                    padding=ft.padding.symmetric(horizontal=5, vertical=5)
                ),
                
                # Warning text
                ft.Container(
                    content=ft.Text(
                        "This action cannot be undone.",
                        size=12,
                        color=ft.Colors.GREY_600,
                        italic=True
                    ),
                    height=20,
                    alignment=ft.alignment.center_left
                ),
                
                ft.Container(height=15),
                
                # Buttons with consistent styling to match DialogManager
                ft.Row([
                    ft.ElevatedButton(
                        "Cancel",
                        on_click=close_overlay,
                        bgcolor=ft.Colors.GREY_100,
                        color=ft.Colors.GREY_700,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    ),
                    ft.ElevatedButton(
                        "Delete",
                        on_click=confirm_action,
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=15)
            ], spacing=0, tight=True),
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            width=500,   # CONSISTENT width to match DialogManager
            height=240,  # CONSISTENT height to match DialogManager
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            )
        ),
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
        expand=True,
    )

    try:
        page.overlay.append(overlay)
        page.update()
        print(f"DEBUG: Overlay dialog created and added to page")
    except Exception as ex:
        print(f"DEBUG: Error creating overlay: {ex}")

def _format_delete_message(message: str) -> str:
    """Smart formatting for delete confirmation messages with filename handling"""
    # Extract filename from delete messages
    if "Are you sure you want to delete" in message and "?" in message:
        try:
            # Extract the filename between quotes
            start = message.find("'") + 1
            end = message.rfind("'")
            if start > 0 and end > start:
                filename = message[start:end]
                
                # Smart filename truncation
                if len(filename) > 45:
                    # For very long filenames, show beginning and end
                    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
                    if len(name) > 35:
                        truncated_name = name[:20] + "..." + name[-12:]
                        filename = f"{truncated_name}.{ext}" if ext else truncated_name
                
                return f"Are you sure you want to delete '{filename}'?"
        except:
            pass
    
    # For other messages, just ensure reasonable length
    if len(message) > 150:
        return message[:147] + "..."
    
    return message

def show_confirm_dialog(page: ft.Page, title: str, message: str, on_confirm):
    """
    Same style as show_center_sheet but specifically for confirmation.
    """
    show_center_sheet(page, title, message, on_confirm)

class NotificationsWindow:
    """Full screen notifications window with enhanced delete functionality"""
    
    def __init__(self, page: ft.Page, username: str, approval_service):
        self.page = page
        self.username = username
        self.approval_service = approval_service
        self.is_visible = False
        self.window_container = None
        self.on_close_callback = None
        
        # Success/delete notification animations
        self.delete_notification_ui = None
        
        # Initialize and add delete notification to page overlay
        self.create_delete_notification()
        if self.delete_notification_ui:
            self.page.overlay.append(self.delete_notification_ui)
        
    def set_close_callback(self, callback: Callable):
        """Set callback for when window is closed"""
        self.on_close_callback = callback
    
    def create_delete_notification(self):
        """Create delete success notification"""
        self.delete_notification_ui = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=24),
                ft.Text("Notification deleted successfully!", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(2, ft.Colors.GREEN),
            border_radius=8,
            padding=ft.padding.all(15),
            top=20,
            right=20,
            opacity=0,
            visible=False,
            animate_opacity=300
        )
        return self.delete_notification_ui
    
    def show_delete_success_animation(self, notification_title: str):
        """Show delete success animation with improved error handling"""
        if not self.delete_notification_ui:
            print("DEBUG: Delete notification UI not initialized")
            return
            
        try:
            # Update the message
            self.delete_notification_ui.content.controls[1].value = f"'{notification_title}' deleted successfully!"
            self.delete_notification_ui.visible = True
            self.delete_notification_ui.opacity = 1
            self.page.update()
            
            def hide_notification():
                try:
                    time.sleep(2)
                    if self.delete_notification_ui and self.delete_notification_ui.visible:
                        self.delete_notification_ui.opacity = 0
                        self.page.update()
                        time.sleep(0.3)
                        self.delete_notification_ui.visible = False
                        self.page.update()
                except Exception as e:
                    print(f"DEBUG: Error hiding notification: {e}")
            
            threading.Thread(target=hide_notification, daemon=True).start()
            
        except Exception as e:
            print(f"DEBUG: Error showing delete animation: {e}")
    
    def show_delete_confirmation_dialog(self, filename: str, delete_callback):
        """Show delete confirmation dialog using custom overlay system - CONSISTENT WITH DialogManager"""
        print(f"DEBUG: Showing confirmation dialog for '{filename}'")
        
        def on_confirm():
            print(f"DEBUG: Delete confirmed for '{filename}'")
            try:
                delete_callback()
            except Exception as error:
                print(f"DEBUG: Error in confirm_delete: {error}")
        
        show_confirm_dialog(
            self.page,
            "Delete Notification",
            f"Are you sure you want to delete '{filename}'?",
            on_confirm
        )
        print(f"DEBUG: Dialog displayed successfully")
    
    def delete_notification(self, index: int, show_confirmation: bool = True):
        """Delete a notification with improved error handling and validation"""
        print(f"DEBUG: delete_notification called for index {index}, show_confirmation={show_confirmation}")
        
        def do_delete():
            print(f"DEBUG: do_delete() executing for index {index}")
            try:
                # Load current notifications
                notifications = self.approval_service.load_notifications()
                print(f"DEBUG: Loaded {len(notifications)} notifications")
                
                # Validate index
                if not (0 <= index < len(notifications)):
                    print(f"DEBUG: Invalid index {index} for {len(notifications)} notifications")
                    self.show_error_message(f"Invalid notification index: {index}")
                    return
                
                # Get notification details before deletion
                notification_to_delete = notifications[index]
                filename = notification_to_delete.get('filename', 'Unknown')
                print(f"DEBUG: Deleting notification: {filename}")
                
                # Remove the notification
                deleted_notification = notifications.pop(index)
                print(f"DEBUG: Notification removed from list")
                
                # Save updated notifications
                success = self.approval_service.save_notifications(notifications)
                if not success:
                    print(f"DEBUG: Failed to save notifications")
                    self.show_error_message("Failed to save notifications")
                    return
                
                print(f"DEBUG: Notifications saved successfully, {len(notifications)} remaining")
                
                # Show success animation
                self.show_delete_success_animation(filename)
                
                # Refresh the UI
                self.refresh_notifications()
                
                # Notify parent component
                if self.on_close_callback:
                    self.on_close_callback()
                
                print(f"DEBUG: Notification '{filename}' deleted successfully")
                
            except Exception as e:
                error_msg = f"Error deleting notification: {str(e)}"
                print(f"DEBUG: {error_msg}")
                self.show_error_message(error_msg)
        
        if show_confirmation:
            try:
                notifications = self.approval_service.load_notifications()
                if 0 <= index < len(notifications):
                    filename = notifications[index].get('filename', 'Unknown')
                    print(f"DEBUG: Showing confirmation for '{filename}' at index {index}")
                    self.show_delete_confirmation_dialog(filename, do_delete)
                else:
                    print(f"DEBUG: Invalid index {index} for confirmation")
                    self.show_error_message(f"Invalid notification index: {index}")
            except Exception as e:
                print(f"DEBUG: Error in confirmation flow: {e}")
                self.show_error_message(f"Error showing confirmation: {str(e)}")
        else:
            print(f"DEBUG: Skipping confirmation, deleting directly")
            do_delete()
    
    def delete_all_notifications(self):
        """Delete all notifications with improved confirmation and error handling"""
        try:
            notifications = self.approval_service.load_notifications()
            if not notifications:
                self.show_info_message("No notifications to delete")
                return
            
            notification_count = len(notifications)
            print(f"DEBUG: Preparing to delete all {notification_count} notifications")
            
            def do_delete_all():
                try:
                    # Clear all notifications
                    success = self.approval_service.save_notifications([])
                    if not success:
                        self.show_error_message("Failed to delete all notifications")
                        return
                    
                    # Show success animation
                    self.show_delete_success_animation(f"All {notification_count} notifications")
                    
                    # Refresh UI
                    self.refresh_notifications()
                    
                    # Notify parent
                    if self.on_close_callback:
                        self.on_close_callback()
                    
                    print(f"DEBUG: All {notification_count} notifications deleted successfully")
                    
                except Exception as e:
                    error_msg = f"Error deleting all notifications: {str(e)}"
                    print(f"DEBUG: {error_msg}")
                    self.show_error_message(error_msg)
            
            # Show confirmation dialog
            self.show_delete_all_confirmation_dialog(notification_count, do_delete_all)
            
        except Exception as e:
            error_msg = f"Error preparing to delete all notifications: {str(e)}"
            print(f"DEBUG: {error_msg}")
            self.show_error_message(error_msg)
    
    def show_delete_all_confirmation_dialog(self, count: int, delete_callback):
        """Show confirmation dialog for deleting all notifications - CONSISTENT WITH DialogManager"""
        def on_confirm():
            try:
                print(f"DEBUG: Delete all confirmed")
                delete_callback()
            except Exception as error:
                print(f"DEBUG: Error in confirm_delete_all: {error}")
        
        show_confirm_dialog(
            self.page,
            "Delete All Notifications",
            f"Are you sure you want to delete all {count} notifications?",
            on_confirm
        )
        print(f"DEBUG: Delete all dialog displayed successfully")
    
    def show_error_message(self, message: str):
        """Show error message to user"""
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ {message}"),
                bgcolor=ft.Colors.RED,
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"DEBUG: Error showing error message: {e}")
    
    def show_info_message(self, message: str):
        """Show info message to user"""
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"ℹ️ {message}"),
                bgcolor=ft.Colors.ORANGE,
                duration=2000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"DEBUG: Error showing info message: {e}")
    
    def show_success_message(self, message: str):
        """Show success message to user"""
        try:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✅ {message}"),
                bgcolor=ft.Colors.GREEN,
                duration=2000
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            print(f"DEBUG: Error showing success message: {e}")
    
    def get_file_icon_and_color(self, filename: str):
        """Get appropriate icon and color based on file extension"""
        if not filename:
            return ft.Icons.DESCRIPTION, ft.Colors.GREY_500, ft.Colors.GREY_100
        
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        # Define icon mappings
        icon_map = {
            'pdf': (ft.Icons.PICTURE_AS_PDF, ft.Colors.RED_600, ft.Colors.RED_100),
            'doc': (ft.Icons.DESCRIPTION, ft.Colors.BLUE_600, ft.Colors.BLUE_100),
            'docx': (ft.Icons.DESCRIPTION, ft.Colors.BLUE_600, ft.Colors.BLUE_100),
            'txt': (ft.Icons.TEXT_SNIPPET, ft.Colors.GREY_600, ft.Colors.GREY_100),
            'jpg': (ft.Icons.IMAGE, ft.Colors.GREEN_600, ft.Colors.GREEN_100),
            'jpeg': (ft.Icons.IMAGE, ft.Colors.GREEN_600, ft.Colors.GREEN_100),
            'png': (ft.Icons.IMAGE, ft.Colors.GREEN_600, ft.Colors.GREEN_100),
            'gif': (ft.Icons.IMAGE, ft.Colors.GREEN_600, ft.Colors.GREEN_100),
            'xlsx': (ft.Icons.TABLE_CHART, ft.Colors.GREEN_700, ft.Colors.GREEN_100),
            'xls': (ft.Icons.TABLE_CHART, ft.Colors.GREEN_700, ft.Colors.GREEN_100),
            'ppt': (ft.Icons.SLIDESHOW, ft.Colors.ORANGE_600, ft.Colors.ORANGE_100),
            'pptx': (ft.Icons.SLIDESHOW, ft.Colors.ORANGE_600, ft.Colors.ORANGE_100),
            'zip': (ft.Icons.ARCHIVE, ft.Colors.PURPLE_600, ft.Colors.PURPLE_100),
            'rar': (ft.Icons.ARCHIVE, ft.Colors.PURPLE_600, ft.Colors.PURPLE_100),
        }
        
        return icon_map.get(extension, (ft.Icons.DESCRIPTION, ft.Colors.BLUE_600, ft.Colors.BLUE_100))
    
    def create_notification_item(self, notification: Dict, index: int):
        """Create a single notification item with circular file icons - cellphone style"""
        is_read = notification.get("read", False)
        
        def mark_read(e):
            try:
                self.approval_service.mark_notification_read(index)
                self.refresh_notifications()
                if self.on_close_callback:
                    self.on_close_callback()
            except Exception as error:
                print(f"DEBUG: Error marking notification as read: {error}")
                self.show_error_message("Failed to mark notification as read")
        
        def delete_with_confirmation(e):
            print(f"DEBUG: Delete button clicked for index {index}")
            self.delete_notification(index, show_confirmation=True)
        
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(notification["timestamp"]).strftime("%m/%d %H:%M")
        except:
            timestamp = "Unknown"
        
        # Get notification details
        filename = notification.get("filename", "Unknown file")
        old_status = notification.get("old_status", "unknown")
        new_status = notification.get("new_status", "unknown")
        admin_id = notification.get("admin_id", "admin")
        
        # Create display filename (limit for UI)
        display_filename = filename[:30] + "..." if len(filename) > 30 else filename
        
        # Get file-specific icon and colors
        file_icon, icon_color, bg_color = self.get_file_icon_and_color(filename)
        
        # Create the notification container with cellphone-style centering
        notification_container = ft.Container(
            content=ft.Container(
                content=ft.Row([
                    # Left circular icon (file type indicator)
                    ft.Container(
                        content=ft.Icon(
                            file_icon, 
                            color=icon_color, 
                            size=26
                        ),
                        padding=ft.padding.all(14),
                        bgcolor=bg_color,
                        border_radius=50,  # Make it perfectly circular
                        width=54,
                        height=54,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(0, 2),
                        )
                    ),
                    
                    # Main content area
                    ft.Container(
                        content=ft.Column([
                            # File name
                            ft.Text(
                                display_filename,
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.BLACK87,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Container(height=3),
                            # Status message
                            ft.Text(
                                f"Status: {old_status} → {new_status}",
                                size=13,
                                color=ft.Colors.GREY_700,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Container(height=2),
                            # Admin and time
                            ft.Text(
                                f"By {admin_id} • {timestamp}",
                                size=11,
                                color=ft.Colors.GREY_500,
                            )
                        ], 
                        spacing=0, 
                        tight=True,
                        alignment=ft.MainAxisAlignment.CENTER
                        ),
                        expand=True,
                        padding=ft.padding.only(left=14, right=8, top=6, bottom=6),
                        on_click=mark_read if not is_read else None,
                        alignment=ft.alignment.center_left
                    ),
                    
                    # Right action button (circular delete button)
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_400,
                            icon_size=20,
                            tooltip="Delete notification",
                            on_click=delete_with_confirmation,
                            style=ft.ButtonStyle(
                                shape=ft.CircleBorder(),
                                bgcolor={
                                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                                    ft.ControlState.HOVERED: ft.Colors.RED_50,
                                    ft.ControlState.PRESSED: ft.Colors.RED_100
                                },
                                padding=ft.padding.all(6)
                            )
                        ),
                        width=42,
                        height=42,
                        alignment=ft.alignment.center
                    )
                ], 
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=10
                ),
                bgcolor=ft.Colors.WHITE if is_read else ft.Colors.BLUE_50,
                border_radius=14,
                padding=ft.padding.all(16),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.Colors.BLACK12,
                    offset=ft.Offset(0, 2),
                ),
                border=ft.border.all(
                    1, 
                    ft.Colors.BLUE_200 if not is_read else ft.Colors.GREY_200
                )
            ),
            on_hover=lambda e: self.on_notification_hover(e),
            ink=True,
            ink_color=ft.Colors.BLUE_50 if not is_read else ft.Colors.GREY_50
        )
        
        # Center the notification like a cellphone notification
        return ft.Container(
            content=notification_container,
            width=480,  # Fixed width like a phone notification
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=12),
        )
    
    def on_notification_hover(self, e):
        """Handle notification hover effect"""
        if e.data == "true":
            e.control.content.content.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.BLACK,
                offset=ft.Offset(0, 4),
            )
        else:
            e.control.content.content.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2),
            )
        self.page.update()
    
    def create_empty_state(self):
        """Create empty state for no notifications"""
        return ft.Container(
            content=ft.Column([
                # Large circular icon for empty state
                ft.Container(
                    content=ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=48, color=ft.Colors.GREY_400),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=50,
                    width=96,
                    height=96,
                    alignment=ft.alignment.center
                ),
                ft.Container(height=24),
                ft.Text("No notifications", size=22, color=ft.Colors.GREY_600, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Status updates and comments will appear here", 
                    size=16, 
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.Text(
                    "✓ File approval notifications\n✓ Admin comments\n✓ System updates", 
                    size=14, 
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            alignment=ft.alignment.center,
            expand=True
        )
    
    def mark_all_read(self, e):
        """Mark all notifications as read with improved error handling"""
        try:
            notifications = self.approval_service.load_notifications()
            unread_count = len([n for n in notifications if not n.get("read", False)])
            
            if unread_count == 0:
                self.show_info_message("No unread notifications to mark")
                return
            
            # Mark all as read
            for notification in notifications:
                notification["read"] = True
            
            success = self.approval_service.save_notifications(notifications)
            if not success:
                self.show_error_message("Failed to mark notifications as read")
                return
            
            # Refresh UI
            self.refresh_notifications()
            if self.on_close_callback:
                self.on_close_callback()
            
            # Show success message
            self.show_success_message(f"{unread_count} notifications marked as read")
            
        except Exception as e:
            error_msg = f"Error marking all notifications as read: {str(e)}"
            print(f"DEBUG: {error_msg}")
            self.show_error_message(error_msg)
    
    def close_window(self, e):
        """Close the notifications window"""
        self.hide()
    
    def refresh_notifications(self):
        """Refresh the notifications content with improved error handling"""
        try:
            if self.window_container:
                new_content = self.create_window_content()
                self.window_container.content = new_content
                self.page.update()
                print("DEBUG: Notifications refreshed successfully")
        except Exception as e:
            print(f"DEBUG: Error refreshing notifications: {e}")
            self.show_error_message("Failed to refresh notifications")
    
    def create_window_content(self):
        """Create the full screen window content with enhanced error handling"""
        try:
            notifications = self.approval_service.load_notifications()
            total_count = len(notifications)
            unread_count = len([n for n in notifications if not n.get("read", False)])
            
            print(f"DEBUG: Creating window content with {total_count} notifications ({unread_count} unread)")
            
            # Header with title, stats and action buttons
            header = ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("Notifications", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                        ft.Container(height=5),
                        ft.Row([
                            ft.Text(f"{total_count} Total", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            ft.Container(width=20),
                            ft.Text(f"{unread_count} unread", size=16, color=ft.Colors.GREY_600)
                        ])
                    ], spacing=0),
                    ft.Container(expand=True),
                    ft.Row([
                        # Mark All Read button (only show if there are unread notifications)
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.MARK_EMAIL_READ, size=16, color=ft.Colors.BLUE),
                                ft.Text("Mark All Read", size=14, color=ft.Colors.BLUE, weight=ft.FontWeight.W_500)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                            on_click=self.mark_all_read,
                            bgcolor=ft.Colors.BLUE_50,
                            color=ft.Colors.BLUE,
                            height=36,
                            width=140,
                            disabled=unread_count == 0,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=18),
                                elevation=2
                            )
                        ) if unread_count > 0 else ft.Container(),
                        ft.Container(width=10) if unread_count > 0 else ft.Container(),
                        # Delete All button
                        ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.DELETE_SWEEP, size=16, color=ft.Colors.WHITE),
                                ft.Text("Delete All", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                            on_click=lambda e: self.delete_all_notifications(),
                            bgcolor=ft.Colors.RED,
                            color=ft.Colors.WHITE,
                            height=36,
                            width=120,
                            disabled=total_count == 0,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=18),
                                shadow_color=ft.Colors.RED_300,
                                elevation=3
                            )
                        ),
                        ft.Container(width=10),
                        # Close button (circular)
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=22,
                                on_click=self.close_window,
                                tooltip="Close",
                                icon_color=ft.Colors.GREY_600,
                                style=ft.ButtonStyle(
                                    shape=ft.CircleBorder(),
                                    bgcolor={ft.ControlState.HOVERED: ft.Colors.GREY_100}
                                )
                            ),
                            bgcolor=ft.Colors.WHITE,
                            border_radius=21,
                            width=42,
                            height=42,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=4,
                                color=ft.Colors.BLACK12,
                                offset=ft.Offset(0, 2),
                            )
                        )
                    ])
                ]),
                bgcolor=ft.Colors.GREY_50,
                padding=ft.padding.all(24),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            )
            
            # Notifications list - centered like cellphone notifications
            if not notifications:
                notifications_content = self.create_empty_state()
            else:
                notification_items = [
                    self.create_notification_item(notif, i)
                    for i, notif in enumerate(notifications)
                ]
                
                notifications_content = ft.Container(
                    content=ft.Column([
                        ft.Container(height=20),
                        # Center all notifications horizontally
                        ft.Container(
                            content=ft.Column(
                                notification_items,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=0,
                                scroll=ft.ScrollMode.AUTO
                            ),
                            alignment=ft.alignment.center,
                            expand=True
                        ),
                        ft.Container(height=20)
                    ], spacing=0, expand=True),
                    expand=True,
                    bgcolor=ft.Colors.GREY_50,
                    alignment=ft.alignment.center
                )
            
            return ft.Container(
                content=ft.Column([
                    header,
                    notifications_content
                ], spacing=0, expand=True),
                bgcolor=ft.Colors.GREY_50,
                expand=True
            )
            
        except Exception as e:
            print(f"DEBUG: Error creating window content: {e}")
            # Return error state
            return ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.ERROR, size=48, color=ft.Colors.RED_400),
                        bgcolor=ft.Colors.RED_100,
                        border_radius=50,
                        width=96,
                        height=96,
                        alignment=ft.alignment.center
                    ),
                    ft.Container(height=20),
                    ft.Text("Error Loading Notifications", size=20, color=ft.Colors.RED_600, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"Error: {str(e)}", 
                        size=14, 
                        color=ft.Colors.RED_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=ft.Colors.WHITE
            )
    
    def create_window(self):
        """Create the full screen notifications window"""
        if not self.window_container:
            self.window_container = ft.Container(
                content=self.create_window_content(),
                left=0,
                top=0,
                right=0,
                bottom=0,
                visible=False,
                bgcolor=ft.Colors.GREY_50,
                animate_opacity=300
            )
            self.page.overlay.append(self.window_container)
        
        return self.window_container
    
    def show(self):
        """Show the full screen notifications window"""
        try:
            if not self.window_container:
                self.create_window()
            
            # Refresh content before showing
            self.refresh_notifications()
            
            self.window_container.visible = True
            self.window_container.opacity = 1
            self.is_visible = True
            self.page.update()
            
            print("DEBUG: Notifications window shown successfully")
            
        except Exception as e:
            print(f"DEBUG: Error showing notifications window: {e}")
            self.show_error_message("Failed to open notifications window")
    
    def hide(self):
        """Hide the notifications window"""
        try:
            if self.window_container:
                self.window_container.visible = False
                self.window_container.opacity = 0
                self.is_visible = False
                self.page.update()
                
            print("DEBUG: Notifications window hidden successfully")
            
        except Exception as e:
            print(f"DEBUG: Error hiding notifications window: {e}")
    
    def toggle(self):
        """Toggle the notifications window visibility"""
        if self.is_visible:
            self.hide()
        else:
            self.show()
