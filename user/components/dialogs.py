import flet as ft
from ..services.file_service import FileService

class DialogManager:
    """Dialog components for various user interactions with real functionality"""
    
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
    
    def close_dialog(self, dialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()
    
    def show_delete_confirmation(self, filename: str, file_service: FileService, refresh_callback=None):
        """Show delete confirmation dialog with real file deletion that removes from both filesystem and database"""
        
        # Get file info for display
        file_info = file_service.get_file_info(filename)
        
        def delete_file(e):
            try:
                # The file_service.delete_file method already handles both:
                # 1. Removing the physical file from filesystem
                # 2. Removing the metadata from the JSON database
                if file_service.delete_file(filename):
                    # Success - file removed from both filesystem and database
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"✅ File '{filename}' deleted successfully!"), 
                        bgcolor=ft.Colors.GREEN
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    self.close_dialog(dialog)
                    
                    # Refresh the files view to show updated list
                    if refresh_callback:
                        refresh_callback()
                else:
                    # Error occurred during deletion
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"❌ Error deleting file '{filename}'!"), 
                        bgcolor=ft.Colors.RED
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
            except Exception as ex:
                # Handle any unexpected errors
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {str(ex)}"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Create detailed confirmation dialog
        content_text = f"Are you sure you want to permanently delete this file?\n\nFile: {filename}"
        if file_info:
            content_text += f"\nSize: {file_info.get('size', 'Unknown')}\nType: {file_info.get('type', 'Unknown')}"
            if file_info.get('description'):
                content_text += f"\nDescription: {file_info.get('description')}"
        
        content_text += "\n\n⚠️ This action cannot be undone!"
        content_text += "\n• File will be removed from storage"
        content_text += "\n• All metadata will be deleted"
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_ROUNDED, color=ft.Colors.RED, size=24),
                ft.Container(width=10),
                ft.Text("Delete File", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
            ]),
            content=ft.Container(
                width=450,
                content=ft.Text(
                    content_text,
                    size=14
                )
            ),
            actions=[
                ft.Row([
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Cancel", 
                        on_click=lambda e: self.close_dialog(dialog),
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREY_700
                        )
                    ),
                    ft.Container(width=10),
                    ft.ElevatedButton(
                        "Delete Permanently", 
                        bgcolor=ft.Colors.RED, 
                        color=ft.Colors.WHITE, 
                        on_click=delete_file,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=5)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END)
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def show_file_details_dialog(self, filename: str, file_service: FileService):
        """Show detailed file information dialog"""
        file_info = file_service.get_file_info(filename)
        
        if not file_info:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("File not found!"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        def close_details(e):
            self.close_dialog(dialog)
        
        # Create file details content with enhanced layout
        details_content = ft.Column([
            # File name header
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE_ROUNDED, color=ft.Colors.BLUE, size=24),
                    ft.Container(width=10),
                    ft.Text(file_info["name"], size=16, weight=ft.FontWeight.BOLD)
                ]),
                margin=ft.margin.only(bottom=20)
            ),
            
            # File properties in a clean grid
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text("Type:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            width=100
                        ),
                        ft.Text(file_info["type"])
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text("Size:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            width=100
                        ),
                        ft.Text(file_info["size"])
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text("Created:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            width=100
                        ),
                        ft.Text(file_info["created"])
                    ]),
                    ft.Row([
                        ft.Container(
                            content=ft.Text("Modified:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                            width=100
                        ),
                        ft.Text(file_info["modified"])
                    ]),
                ], spacing=12),
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.GREY_50,
                border_radius=8
            ),
            
            ft.Container(height=20),
            
            # Description section
            ft.Container(
                content=ft.Column([
                    ft.Text("Description:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ft.Container(height=5),
                    ft.Text(
                        file_info["description"] or "No description provided", 
                        color=ft.Colors.GREY_600 if not file_info["description"] else ft.Colors.BLACK
                    ),
                ]),
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8
            ),
            
            ft.Container(height=15),
            
            # Tags section
            ft.Container(
                content=ft.Column([
                    ft.Text("Tags:", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                    ft.Container(height=5),
                    ft.Text(
                        ", ".join(file_info["tags"]) if file_info["tags"] else "No tags assigned", 
                        color=ft.Colors.GREY_600 if not file_info["tags"] else ft.Colors.BLACK
                    ),
                ]),
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.GREEN_50,
                border_radius=8
            ),
        ], spacing=0)
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.INFO_ROUNDED, color=ft.Colors.BLUE, size=24),
                ft.Container(width=10),
                ft.Text("File Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.GREY_600,
                    on_click=close_details
                )
            ]),
            content=ft.Container(
                width=500,
                height=400,
                content=ft.Column([
                    details_content
                ], scroll=ft.ScrollMode.AUTO)  # Make content scrollable if needed
            ),
            actions=[
                ft.Container(
                    content=ft.Row([
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Close",
                            on_click=close_details,
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=5)
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.END),
                    padding=ft.padding.only(right=10, bottom=10)
                )
            ],
            actions_padding=ft.padding.all(0)
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()