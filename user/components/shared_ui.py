import flet as ft
import os
from typing import Optional, Dict, Callable

class SharedUI:
    """Shared UI components for user views - CONSISTENT DESIGN"""
    
    def __init__(self, page: ft.Page, username: str, user_data: Dict):
        self.page = page
        self.username = username
        self.user_data = user_data
        self.navigation = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
    
    def create_user_avatar(self, size: int = 80) -> ft.Container:
        """Create user avatar with initials - CONSISTENT DESIGN"""
        # Get user's initials
        full_name = self.user_data.get("fullname") or self.user_data.get("full_name", self.username or "User")
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            initials = f"{name_parts[0][0].upper()}{name_parts[1][0].upper()}"
        else:
            initials = full_name[:2].upper() if full_name else "U"
        
        # Check for profile image first
        user_folder = f"data/uploads/{self.username}"
        profile_images_folder = os.path.join(user_folder, "profile_images")
        
        has_image = False
        image_path = None
        
        try:
            if os.path.exists(profile_images_folder):
                valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
                for file in os.listdir(profile_images_folder):
                    if any(file.lower().endswith(ext) for ext in valid_extensions):
                        image_path = os.path.join(profile_images_folder, file)
                        has_image = True
                        break
        except:
            pass
        
        if has_image and image_path and os.path.exists(image_path):
            # Use uploaded profile image
            avatar_content = ft.Image(
                src=os.path.abspath(image_path),
                width=size,
                height=size,
                fit=ft.ImageFit.COVER,
                border_radius=size//2,
                error_content=ft.Text(
                    initials,
                    size=size//3,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                )
            )
        else:
            # Use initials
            avatar_content = ft.Text(
                initials,
                size=size//3,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            )
        
        return ft.Container(
            content=avatar_content,
            width=size,
            height=size,
            bgcolor=ft.Colors.BLUE_500,
            border_radius=size//2,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.BLUE_500)
        )
    
    def create_menu_item(self, icon, label, page_key, current_section):
        """Create navigation menu item with consistent styling"""
        is_active = (page_key == current_section) or (
            page_key == "approval_files" and current_section == "approvals"
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    icon, 
                    size=20, 
                    color=ft.Colors.BLUE_600 if is_active else ft.Colors.GREY_600
                ),
                ft.Container(width=12),
                ft.Text(
                    label, 
                    size=14, 
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    color=ft.Colors.BLUE_600 if is_active else ft.Colors.GREY_700
                )
            ]),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            bgcolor=ft.Colors.BLUE_50 if is_active else ft.Colors.TRANSPARENT,
            border_radius=8,
            margin=ft.margin.only(bottom=5),
            on_click=self.get_navigation_handler(page_key),
            ink=True,
            ink_color=ft.Colors.BLUE_100
        )
    
    def get_navigation_handler(self, page_key: str):
        """Get navigation handler for menu item"""
        def handle_navigation(e):
            if self.navigation:
                if page_key == "browser":
                    self.navigation['show_browser']()
                elif page_key == "profile":
                    self.navigation['show_profile']()
                elif page_key == "files":
                    self.navigation['show_files']()
                elif page_key == "approval_files":
                    self.navigation['show_approval_files']()
        
        return handle_navigation
    
    def create_user_menu(self, current_section: str) -> ft.Column:
        """Create user menu for sidebar - CONSISTENT DESIGN"""
        menu_items = []
        
        if self.navigation:
            # Profile menu item
            menu_items.append(
                self.create_menu_item(ft.Icons.ACCOUNT_CIRCLE, "Profile", "profile", current_section)
            )
            
            # Files menu item  
            menu_items.append(
                self.create_menu_item(ft.Icons.INSERT_DRIVE_FILE, "Files", "files", current_section)
            )
            
            # File Approvals menu item
            menu_items.append(
                self.create_menu_item(ft.Icons.CHECK_CIRCLE, "File Approvals", "approval_files", current_section)
            )
        
        return ft.Container(
            content=ft.Column(menu_items, spacing=0),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            padding=ft.padding.all(10),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_user_info_card(self):
        """Create user info card - CONSISTENT DESIGN"""
        return ft.Container(
            content=ft.Column([
                # Profile avatar
                self.create_user_avatar(80),
                
                ft.Container(height=15),
                
                # Username
                ft.Text(
                    f"@{self.username}",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Email
                ft.Text(
                    self.user_data.get('email', f'{self.username}@example.com'),
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Role badge
                ft.Container(
                    content=ft.Text(
                        self.user_data.get('role', 'USER').upper(),
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.GREEN_500,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                    margin=ft.margin.only(top=8)
                )
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            margin=ft.margin.only(bottom=15),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_user_sidebar(self, current_section: str) -> ft.Column:
        """Create complete user sidebar - CONSISTENT DESIGN MATCHING IMAGE 1"""
        return ft.Column([
            # User info card
            self.create_user_info_card(),
            
            # Navigation menu
            self.create_user_menu(current_section)
        ], spacing=0)
    
    def create_back_button(self, on_click: Callable, text: str = "Back") -> ft.Container:
        """Create a back button - CONSISTENT DESIGN"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.BLUE_600,
                    icon_size=20,
                    on_click=on_click,
                    tooltip="Go back"
                ),
                ft.Text(
                    text,
                    size=14,
                    color=ft.Colors.BLUE_600,
                    weight=ft.FontWeight.W_500
                )
            ], spacing=5),
            margin=ft.margin.only(bottom=10)
        )
    
    def create_section_header(self, title: str, subtitle: str = None, icon: str = None) -> ft.Container:
        """Create a section header with title and optional subtitle"""
        header_content = []
        
        if icon:
            header_content.append(
                ft.Icon(icon, size=28, color=ft.Colors.BLUE_700)
            )
            header_content.append(ft.Container(width=10))
        
        title_column = [ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)]
        if subtitle:
            title_column.append(
                ft.Text(subtitle, size=14, color=ft.Colors.GREY_600)
            )
        
        header_content.append(
            ft.Column(title_column, spacing=5)
        )
        
        return ft.Container(
            content=ft.Row(header_content, alignment=ft.MainAxisAlignment.START),
            margin=ft.margin.only(bottom=20)
        )
    
    def create_info_card(self, title: str, value: str, icon: str, color: str = ft.Colors.BLUE_600) -> ft.Container:
        """Create an info card with icon, title and value"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=24, color=color),
                    ft.Container(expand=True),
                ]),
                ft.Container(height=10),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                ft.Text(title, size=12, color=ft.Colors.GREY_600)
            ], spacing=5),
            bgcolor=ft.Colors.WHITE,
            padding=20,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                blur_radius=4,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
            ),
            width=150,
            height=120
        )
    
    def create_status_badge(self, text: str, status: str) -> ft.Container:
        """Create a status badge with appropriate color"""
        colors = {
            "active": ft.Colors.GREEN,
            "inactive": ft.Colors.GREY,
            "pending": ft.Colors.ORANGE,
            "approved": ft.Colors.GREEN,
            "rejected": ft.Colors.RED,
            "error": ft.Colors.RED
        }
        
        bg_colors = {
            "active": ft.Colors.GREEN_100,
            "inactive": ft.Colors.GREY_100,
            "pending": ft.Colors.ORANGE_100,
            "approved": ft.Colors.GREEN_100,
            "rejected": ft.Colors.RED_100,
            "error": ft.Colors.RED_100
        }
        
        color = colors.get(status.lower(), ft.Colors.GREY)
        bg_color = bg_colors.get(status.lower(), ft.Colors.GREY_100)
        
        return ft.Container(
            content=ft.Text(
                text,
                size=11,
                color=color,
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
            border_radius=12,
            border=ft.border.all(1, color)
        )