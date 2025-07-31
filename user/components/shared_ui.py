import flet as ft

class SharedUI:
    """Shared UI components used across different views"""
    
    def __init__(self, page: ft.Page, username: str, user_data: dict):
        self.page = page
        self.username = username
        self.user_data = user_data
        self.navigation = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
    
    def create_user_sidebar(self, active_tab: str = "profile"):
        """Create the user sidebar with avatar and menu"""
        return ft.Column([
            # Avatar
            ft.CircleAvatar(
                bgcolor=ft.Colors.BLUE_400,
                radius=60,
                content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=60, color=ft.Colors.WHITE)
            ),
            ft.Container(height=20),
            
            # User info
            ft.Text("User", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(self.user_data["full_name"], size=14, color=ft.Colors.GREY_700),
            ft.Text(self.user_data["email"], size=12, color=ft.Colors.GREY_600),
            ft.Container(height=30),
            
            # Menu items
            self.create_menu_item("Profile", "profile", active_tab),
            self.create_menu_item("Files", "files", active_tab)
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    def create_menu_item(self, label: str, tab_name: str, active_tab: str):
        """Create a menu item for the sidebar"""
        is_active = tab_name == active_tab
        
        def on_click(e):
            if self.navigation:
                if tab_name == "profile":
                    self.navigation['show_profile']()
                elif tab_name == "files":
                    self.navigation['show_files']()
        
        return ft.Container(
            content=ft.Text(
                label, 
                color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700
            ),
            bgcolor=ft.Colors.GREY_600 if is_active else ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            border_radius=5 if is_active else 0,
            width=120,
            on_click=on_click if not is_active else None,
            ink=not is_active
        )
    
    def create_back_button(self, on_click_handler):
        """Create a standardized back button"""
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color=ft.Colors.GREY_700,
                on_click=on_click_handler
            ),
            alignment=ft.alignment.top_left,
            margin=ft.margin.only(left=10, top=10)
        )