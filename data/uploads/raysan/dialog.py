import flet as ft
from typing import Callable, Optional

class CustomDialog:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_dialog = None
    
    def show_rename_dialog(self, current_name: str, on_rename_callback: Callable[[str], None]):
        """Show custom rename file dialog"""
        name_field = ft.TextField(
            label="File Name",
            value=current_name,
            width=400,
            text_size=14,
            border_radius=8,
            on_submit=lambda e: self.confirm_rename(name_field.value, on_rename_callback)
        )
        
        def confirm_rename_click(e):
            self.confirm_rename(name_field.value, on_rename_callback)
        
        def cancel_rename_click(e):
            self.close_current_dialog()
        
        # Create custom dialog container
        dialog_content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.EDIT, size=24, color=ft.Colors.BLUE),
                    ft.Text("Rename File", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE,
                        on_click=cancel_rename_click,
                        tooltip="Close"
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                ft.Container(height=10),
                ft.Text("Enter the new name for the file:", size=14, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                
                name_field,
                
                ft.Container(height=20),
                ft.Row([
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Cancel",
                        on_click=cancel_rename_click,
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREY_600
                        )
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Rename",
                        on_click=confirm_rename_click,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE
                        ),
                        icon=ft.Icons.CHECK
                    )
                ])
            ], spacing=0),
            width=450,
            height=200,
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )
        
        # Create backdrop
        backdrop = ft.Container(
            content=ft.Stack([
                # Semi-transparent overlay
                ft.Container(
                    bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                    expand=True,
                    on_click=cancel_rename_click
                ),
                # Centered dialog
                ft.Container(
                    content=dialog_content,
                    alignment=ft.alignment.center,
                    expand=True
                )
            ]),
            expand=True
        )
        
        # Show as AlertDialog (fallback for compatibility)
        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.EDIT, size=24, color=ft.Colors.BLUE),
                ft.Text("Rename File", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    ft.Icons.CLOSE,
                    on_click=cancel_rename_click,
                    tooltip="Close"
                )
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Enter the new name for the file:", size=14, color=ft.Colors.GREY_700),
                    ft.Container(height=10),
                    name_field
                ], tight=True),
                width=400
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_rename_click
                ),
                ft.ElevatedButton(
                    "Rename",
                    on_click=confirm_rename_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = self.current_dialog
        self.current_dialog.open = True
        self.page.update()
        
        # Focus on the text field
        name_field.focus()
    
    def confirm_rename(self, new_name: str, callback: Callable[[str], None]):
        """Confirm rename operation"""
        if new_name and new_name.strip():
            callback(new_name.strip())
        self.close_current_dialog()
    
    def close_current_dialog(self):
        """Close the current dialog"""
        if self.current_dialog:
            self.current_dialog.open = False
            self.page.dialog = None
            self.page.update()
    
    def show_confirmation_dialog(
        self, 
        title: str, 
        message: str, 
        on_confirm: Callable[[], None],
        on_cancel: Optional[Callable[[], None]] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_color: str = ft.Colors.BLUE
    ):
        """Show custom confirmation dialog"""
        def confirm_click(e):
            on_confirm()
            self.close_current_dialog()
        
        def cancel_click(e):
            if on_cancel:
                on_cancel()
            self.close_current_dialog()
        
        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.HELP_OUTLINE, size=24, color=confirm_color),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=cancel_click
                ),
                ft.ElevatedButton(
                    confirm_text,
                    on_click=confirm_click,
                    style=ft.ButtonStyle(
                        bgcolor=confirm_color,
                        color=ft.Colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = self.current_dialog
        self.current_dialog.open = True
        self.page.update()
    
    def show_success_dialog(
        self,
        title: str,
        message: str,
        on_close: Optional[Callable[[], None]] = None,
        auto_close_seconds: Optional[int] = None
    ):
        """Show custom success dialog"""
        def close_click(e):
            if on_close:
                on_close()
            self.close_current_dialog()
        
        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=30, color=ft.Colors.GREEN),
                ft.Container(width=10),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Container(
                content=ft.Text(message, size=14),
                width=300
            ),
            actions=[
                ft.ElevatedButton(
                    "OK",
                    on_click=close_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREEN,
                        color=ft.Colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = self.current_dialog
        self.current_dialog.open = True
        self.page.update()
        
        # Auto close if specified
        if auto_close_seconds:
            import threading
            import time
            
            def auto_close():
                time.sleep(auto_close_seconds)
                if self.current_dialog and self.current_dialog.open:
                    self.close_current_dialog()
            
            threading.Thread(target=auto_close, daemon=True).start()
    
    def show_error_dialog(
        self,
        title: str,
        message: str,
        on_close: Optional[Callable[[], None]] = None
    ):
        """Show custom error dialog"""
        def close_click(e):
            if on_close:
                on_close()
            self.close_current_dialog()
        
        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR, size=30, color=ft.Colors.RED),
                ft.Container(width=10),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD)
            ]),
            content=ft.Text(message, size=14),
            actions=[
                ft.ElevatedButton(
                    "OK",
                    on_click=close_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = self.current_dialog
        self.current_dialog.open = True
        self.page.update()
    
    def show_input_dialog(
        self,
        title: str,
        label: str,
        initial_value: str = "",
        on_submit: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        input_type: str = "text",  # "text", "multiline", "number", "email"
        width: int = 400
    ):
        """Show custom input dialog"""
        # Create input field based on type
        if input_type == "multiline":
            input_field = ft.TextField(
                label=label,
                value=initial_value,
                width=width,
                multiline=True,
                min_lines=3,
                max_lines=5,
                text_size=14
            )
        elif input_type == "number":
            input_field = ft.TextField(
                label=label,
                value=initial_value,
                width=width,
                keyboard_type=ft.KeyboardType.NUMBER,
                text_size=14
            )
        elif input_type == "email":
            input_field = ft.TextField(
                label=label,
                value=initial_value,
                width=width,
                keyboard_type=ft.KeyboardType.EMAIL,
                text_size=14
            )
        else:  # text
            input_field = ft.TextField(
                label=label,
                value=initial_value,
                width=width,
                text_size=14,
                on_submit=lambda e: self.submit_input(input_field.value, on_submit)
            )
        
        def submit_click(e):
            self.submit_input(input_field.value, on_submit)
        
        def cancel_click(e):
            if on_cancel:
                on_cancel()
            self.close_current_dialog()
        
        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=input_field,
                width=width
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=cancel_click
                ),
                ft.ElevatedButton(
                    "Submit",
                    on_click=submit_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        color=ft.Colors.WHITE
                    )
                )
            ]
        )
        
        self.page.dialog = self.current_dialog
        self.current_dialog.open = True
        self.page.update()
        
        # Focus on the input field
        input_field.focus()
    
    def submit_input(self, value: str, callback: Optional[Callable[[str], None]]):
        """Submit input value"""
        if callback:
            callback(value)
        self.close_current_dialog()
    def confirm_action(page, title, message, on_confirm):
        def yes_click(e):
            page.dialog.open = False
            page.update()
            on_confirm()

        def no_click(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Yes", on_click=yes_click),
                ft.TextButton("No", on_click=no_click)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )


    def prompt_folder_name(page, title, message, on_submit):
        name_field = ft.TextField(label="Folder Name", autofocus=True)

        def submit_click(e):
            if name_field.value.strip() == "":
                name_field.error_text = "Folder name cannot be empty"
                page.dialog.update()
                return
            page.dialog.open = False
            page.update()
            on_submit(name_field.value.strip())

        def cancel_click(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column([ft.Text(message), name_field], tight=True),
            actions=[
                ft.TextButton("Create", on_click=submit_click),
                ft.TextButton("Cancel", on_click=cancel_click)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()
