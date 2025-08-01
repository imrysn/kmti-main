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
        """Create the user sidebar with avatar and menu - FIXED ALIGNMENT"""
        return ft.Container(
            content=ft.Column([
                # Fixed spacing container for avatar
                ft.Container(height=20),
                
                # Avatar - centered and consistent
                ft.Container(
                    content=ft.CircleAvatar(
                        bgcolor=ft.Colors.BLUE_400,
                        radius=40,  # Consistent size
                        content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=40, color=ft.Colors.WHITE)
                    ),
                    alignment=ft.alignment.center,
                    width=300,  # Fixed width for consistency
                ),
                
                # Fixed spacing
                ft.Container(height=20),
                
                # User info - centered and aligned
                ft.Container(
                    content=ft.Column([
                        ft.Text("User", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.user_data["full_name"], size=14, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.user_data["email"], size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    width=300,
                    alignment=ft.alignment.center,
                ),
                
                # Fixed spacing before menu
                ft.Container(height=30),
                
                # Menu items - FIXED ALIGNMENT - SAME SIDE, LOCKED IN PLACE
                ft.Container(
                    content=ft.Column([
                        # Both items in exact same position with fixed alignment
                        ft.Container(
                            content=self.create_menu_item("Profile", "profile", active_tab),
                            alignment=ft.alignment.center,
                            width=300,
                            height=44  # Fixed height container
                        ),
                        ft.Container(height=8),  # Fixed spacing between items
                        ft.Container(
                            content=self.create_menu_item("Files", "files", active_tab),
                            alignment=ft.alignment.center, 
                            width=300,
                            height=44  # Fixed height container
                        )
                    ], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    spacing=0,
                    alignment=ft.alignment.center
                    ),
                    width=300,
                    alignment=ft.alignment.center,
                )
                
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0  # Remove automatic spacing, use containers instead
            ),
            width=300,  # Fixed sidebar width
            bgcolor=ft.Colors.GREY_100,  # Light background
            padding=ft.padding.all(0),  # Remove default padding
            alignment=ft.alignment.top_center
        )
    
    def create_menu_item(self, label: str, tab_name: str, active_tab: str):
        """Create a menu item for the sidebar - FIXED ALIGNMENT WITH SMOOTH HOVER"""
        is_active = tab_name == active_tab
        
        def on_click(e):
            if self.navigation:
                if tab_name == "profile":
                    self.navigation['show_profile']()
                elif tab_name == "files":
                    self.navigation['show_files']()
        
        def on_hover(e):
            if not is_active:
                if e.data == "true":  # Mouse enter
                    e.control.bgcolor = ft.Colors.GREY_300
                    e.control.content.color = ft.Colors.GREY_800
                else:  # Mouse leave
                    e.control.bgcolor = ft.Colors.TRANSPARENT
                    e.control.content.color = ft.Colors.GREY_700
                e.control.update()
        
        return ft.Container(
            content=ft.Text(
                label, 
                color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700,
                text_align=ft.TextAlign.CENTER,
                size=14,
                weight=ft.FontWeight.W_500
            ),
            bgcolor=ft.Colors.GREY_600 if is_active else ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=8,
            width=140,  # LOCKED WIDTH - prevents shifting
            height=44,   # LOCKED HEIGHT - prevents shifting
            alignment=ft.alignment.center,  # LOCKED CENTER ALIGNMENT
            on_click=on_click if not is_active else None,
            on_hover=on_hover if not is_active else None,
            ink=not is_active,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT) if not is_active else None,
            # POSITION LOCK - prevents movement during state changes
            margin=ft.margin.all(0),  # No margins that could shift
            border=ft.border.all(0, ft.Colors.TRANSPARENT)  # Invisible border to maintain exact positioning
        )
    
    def create_back_button(self, on_click_handler):
        """Create a standardized back button - FIXED POSITIONING"""
        return ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.CHEVRON_LEFT,
                icon_color=ft.Colors.GREY_700,
                icon_size=24,
                on_click=on_click_handler,
                tooltip="Go back"
            ),
            alignment=ft.alignment.top_left,
            margin=ft.margin.only(left=15, top=15),
            width=50,
            height=50
        )
    
    def create_profile_content_area(self):
        """Create the right side content area for profile editing"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Text("Profile Settings", size=24, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),  # Push edit button to right
                        ft.ElevatedButton(
                            "Edit Profile",
                            icon=ft.Icons.EDIT,
                            on_click=lambda e: print("Edit profile clicked")
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=ft.border_radius.only(top_left=10, top_right=10)
                ),
                
                # Form fields
                ft.Container(
                    content=ft.Column([
                        self.create_form_field("Full Name:", self.user_data.get("full_name", "")),
                        self.create_form_field("Email:", self.user_data.get("email", "")),
                        self.create_form_field("Role:", "User"),  # You can customize this
                        self.create_form_field("Join Date:", self.user_data.get("created_date", "")[:10] if self.user_data.get("created_date") else ""),
                    ], spacing=20),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.WHITE,
                    expand=True
                )
            ], spacing=0),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            expand=True,
            margin=ft.margin.all(20)
        )
    
    def create_form_field(self, label: str, value: str):
        """Create a consistent form field"""
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                ft.Container(height=5),
                ft.TextField(
                    value=value,
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_50,
                    border_color=ft.Colors.GREY_300,
                    focused_border_color=ft.Colors.BLUE_400,
                    content_padding=ft.padding.symmetric(horizontal=15, vertical=10)
                )
            ], spacing=0),
            width=400
        )