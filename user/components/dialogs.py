import flet as ft
from typing import Callable, Optional, List
import threading
import time
from typing import Dict

class DialogManager:
    """Centralized dialog management for user components"""
    
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
    
    def show_confirmation_dialog(self, 
                                title: str, 
                                message: str, 
                                on_confirm: Callable, 
                                on_cancel: Optional[Callable] = None,
                                confirm_text: str = "Confirm",
                                cancel_text: str = "Cancel",
                                confirm_color: str = ft.Colors.BLUE,
                                is_destructive: bool = False):
        """Show a confirmation dialog with CONSISTENT SIZE and improved filename handling"""
        
        def handle_confirm(e):
            self.page.overlay.pop()
            self.page.update()
            if on_confirm:
                on_confirm()
        
        def handle_cancel(e):
            self.page.overlay.pop()
            self.page.update()
            if on_cancel:
                on_cancel()
        
        # Smart filename truncation for better display
        display_message = self._format_delete_message(message)
        
        # Create modal background
        modal_background = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            expand=True,
            on_click=handle_cancel
        )
        
        # Create dialog content with FIXED DIMENSIONS
        dialog_content = ft.Container(
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
                
                # Buttons with consistent styling
                ft.Row([
                    ft.ElevatedButton(
                        cancel_text,
                        on_click=handle_cancel,
                        bgcolor=ft.Colors.GREY_100,
                        color=ft.Colors.GREY_700,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    ),
                    ft.ElevatedButton(
                        confirm_text,
                        on_click=handle_confirm,
                        bgcolor=ft.Colors.RED if is_destructive else confirm_color,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=15)
            ], spacing=0, tight=True),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=12,
            width=500,   # Consistent width
            height=240,  # Consistent height
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            )
        )
        
        # Create centered dialog
        centered_dialog = ft.Container(
            content=dialog_content,
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Add to page overlay
        dialog_stack = ft.Stack([modal_background, centered_dialog])
        self.page.overlay.append(dialog_stack)
        self.page.update()
    
    def _format_delete_message(self, message: str) -> str:
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
    
    def show_input_dialog(self,
                         title: str,
                         fields: List[Dict],
                         on_submit: Callable,
                         on_cancel: Optional[Callable] = None,
                         submit_text: str = "Submit",
                         cancel_text: str = "Cancel"):
        """Show an input dialog with multiple fields"""
        
        field_refs = {}
        field_controls = []
        
        for field in fields:
            if field["type"] == "text":
                control = ft.TextField(
                    label=field["label"],
                    hint_text=field.get("hint", ""),
                    value=field.get("value", ""),
                    width=440
                )
            elif field["type"] == "multiline":
                control = ft.TextField(
                    label=field["label"],
                    hint_text=field.get("hint", ""),
                    value=field.get("value", ""),
                    multiline=True,
                    min_lines=field.get("min_lines", 2),
                    max_lines=field.get("max_lines", 4),
                    width=440
                )
            else:
                continue
            
            field_refs[field["key"]] = control
            field_controls.append(control)
            field_controls.append(ft.Container(height=10))
        
        def handle_submit(e):
            # Collect field values
            values = {}
            for key, control in field_refs.items():
                values[key] = control.value
            
            self.page.overlay.pop()
            self.page.update()
            
            if on_submit:
                on_submit(values)
        
        def handle_cancel(e):
            self.page.overlay.pop()
            self.page.update()
            if on_cancel:
                on_cancel()
        
        # Create modal background
        modal_background = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            expand=True,
            on_click=handle_cancel
        )
        
        # Create dialog content
        dialog_content = ft.Container(
            content=ft.Column([
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                ft.Column(field_controls[:-1], spacing=0),  # Remove last spacer
                ft.Container(height=20),
                ft.Row([
                    ft.TextButton(
                        cancel_text,
                        on_click=handle_cancel,
                        style=ft.ButtonStyle(color=ft.Colors.GREY_700)
                    ),
                    ft.ElevatedButton(
                        submit_text,
                        on_click=handle_submit,
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=10, tight=True),
            bgcolor=ft.Colors.WHITE,
            padding=30,
            border_radius=12,
            width=540,
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            )
        )
        
        # Create centered dialog
        centered_dialog = ft.Container(
            content=dialog_content,
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Add to page overlay
        dialog_stack = ft.Stack([modal_background, centered_dialog])
        self.page.overlay.append(dialog_stack)
        self.page.update()
    
    def show_details_dialog(self,
                           title: str,
                           content: ft.Control,
                           width: int = 600,
                           height: int = 500):
        """Show a details dialog with custom content"""
        
        def handle_close(e):
            self.page.overlay.pop()
            self.page.update()
        
        # Create modal background
        modal_background = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            expand=True,
            on_click=handle_close
        )
        
        # Create dialog content
        dialog_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        on_click=handle_close,
                        icon_color=ft.Colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    content=content,
                    expand=True
                )
            ], expand=True),
            bgcolor=ft.Colors.WHITE,
            padding=20,
            border_radius=12,
            width=width,
            height=height,
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=2,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            )
        )
        
        # Create centered dialog
        centered_dialog = ft.Container(
            content=dialog_content,
            alignment=ft.alignment.center,
            expand=True
        )
        
        # Add to page overlay
        dialog_stack = ft.Stack([modal_background, centered_dialog])
        self.page.overlay.append(dialog_stack)
        self.page.update()
    
    def show_success_notification(self, 
                                message: str, 
                                duration: int = 3,
                                icon: str = ft.Icons.CHECK_CIRCLE):
        """Show a temporary success notification"""
        
        notification = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=ft.Colors.GREEN, size=24),
                ft.Text(message, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(2, ft.Colors.GREEN),
            border_radius=8,
            padding=ft.padding.all(15),
            top=20,
            right=20,
            opacity=1,
            shadow=ft.BoxShadow(
                blur_radius=5,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
            )
        )
        
        self.page.overlay.append(notification)
        self.page.update()
        
        def hide_notification():
            time.sleep(duration)
            if notification in self.page.overlay:
                self.page.overlay.remove(notification)
                self.page.update()
        
        threading.Thread(target=hide_notification, daemon=True).start()
    
    def show_error_notification(self, 
                               message: str, 
                               duration: int = 4,
                               icon: str = ft.Icons.ERROR):
        """Show a temporary error notification"""
        
        notification = ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=ft.Colors.RED, size=24),
                ft.Text(message, color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(2, ft.Colors.RED),
            border_radius=8,
            padding=ft.padding.all(15),
            top=20,
            right=20,
            opacity=1,
            shadow=ft.BoxShadow(
                blur_radius=5,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            )
        )
        
        self.page.overlay.append(notification)
        self.page.update()
        
        def hide_notification():
            time.sleep(duration)
            if notification in self.page.overlay:
                self.page.overlay.remove(notification)
                self.page.update()
        
        threading.Thread(target=hide_notification, daemon=True).start()