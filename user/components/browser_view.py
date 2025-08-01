import flet as ft
from ..models.data_models import ProjectData
from utils.logger import log_action

class BrowserView:
    """Browser view component for displaying project folders"""
    
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username
        self.projects_data = ProjectData.get_projects()
        self.navigation = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
    
    def create_folder_item(self, project):
        """Create a folder item widget"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.FOLDER_ROUNDED, size=70, color=ft.Colors.BLACK),
                ft.Container(height=6),
                ft.Text(
                    project["name"], 
                    size=11, 
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    width=120
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0),
            width=120,
            height=100,
            on_click=lambda e: self.open_folder(project["name"]),
            ink=True,
            padding=ft.padding.all(3)
        )
    
    def open_folder(self, folder_name):
        """Handle folder click"""
        log_action(self.username, f"Opened folder: {folder_name}")
    
    def create_navigation_bar(self):
        """Create the navigation bar"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=ft.Colors.GREY_700),
                        ft.IconButton(ft.Icons.REFRESH_ROUNDED, icon_color=ft.Colors.GREY_700),
                    ], spacing=0)
                ),
                ft.Container(expand=True),
                # Search bar
                ft.Container(
                    content=ft.Row([
                        ft.TextField(
                            hint_text="Search...",
                            border=ft.InputBorder.NONE,
                            content_padding=ft.padding.symmetric(horizontal=15, vertical=10),
                            text_size=14,
                            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Icon(ft.Icons.SEARCH_ROUNDED, color=ft.Colors.BLACK, size=22),
                            padding=ft.padding.only(right=15),
                            alignment=ft.alignment.center
                        )
                    ], spacing=0, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=3,
                    width=450,
                    height=38
                ),
                ft.Container(expand=True)
            ], spacing=10),
            bgcolor=ft.Colors.GREY_300,
            padding=ft.padding.all(10)
        )
    
    def create_projects_grid(self):
        """Create the projects grid"""
        return ft.Container(
            content=ft.Column([
                ft.Column([
                    ft.Row([
                        self.create_folder_item(self.projects_data[i]) if i < len(self.projects_data) else ft.Container(),
                        self.create_folder_item(self.projects_data[i+1]) if i+1 < len(self.projects_data) else ft.Container(),
                        self.create_folder_item(self.projects_data[i+2]) if i+2 < len(self.projects_data) else ft.Container(),
                        self.create_folder_item(self.projects_data[i+3]) if i+3 < len(self.projects_data) else ft.Container(),
                        self.create_folder_item(self.projects_data[i+4]) if i+4 < len(self.projects_data) else ft.Container()
                    ], spacing=25, alignment=ft.MainAxisAlignment.START)
                    for i in range(0, len(self.projects_data), 5)
                ], spacing=25, alignment=ft.MainAxisAlignment.START)
            ], 
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START),
            padding=ft.padding.only(top=20, bottom=20, left=30, right=30),
            alignment=ft.alignment.top_left
        )
    
    def create_content(self):
        """Create the main browser content"""
        return ft.Column([
            self.create_navigation_bar(),
            
            # Main content
            ft.Container(
                content=ft.Row([
                    # Sidebar
                    ft.Container(
                        width=200,
                        bgcolor=ft.Colors.GREY_100,
                        border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300))
                    ),
                    # Projects grid
                    self.create_projects_grid(),
                    ft.Container(expand=True)
                ], alignment=ft.MainAxisAlignment.START),
                expand=True,
                bgcolor=ft.Colors.GREY_200
            )
        ], spacing=0, expand=True)