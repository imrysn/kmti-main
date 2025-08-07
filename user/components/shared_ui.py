import flet as ft
from typing import Optional, Dict, Callable

class SharedUI:
    """Shared UI components for user views"""
    
    def __init__(self, page: ft.Page, username: str, user_data: Dict):
        self.page = page
        self.username = username
        self.user_data = user_data
        self.navigation = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
    
    def create_user_avatar(self, size: int = 80) -> ft.Container:
        """Create user avatar with initials"""
        # Get user's initials
        full_name = self.user_data.get("fullname", self.username or "User")
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            initials = f"{name_parts[0][0].upper()}{name_parts[1][0].upper()}"
        else:
            initials = full_name[:2].upper() if full_name else "U"
        
        return ft.Container(
            content=ft.Text(
                initials,
                size=size//3,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER
            ),
            width=size,
            height=size,
            bgcolor=ft.Colors.BLUE_600,
            border_radius=size//2,
            alignment=ft.alignment.center
        )
    
    def create_user_menu(self, current_section: str) -> ft.Column:
        """Create user menu for sidebar - simple version"""
        menu_items = []
        
        if self.navigation:
            # Files menu item
            files_color = ft.Colors.BLUE_700 if current_section == "files" else ft.Colors.GREY_700
            menu_items.append(
                ft.Container(
                    content=ft.TextButton(
                        "📁 Files",
                        on_click=lambda e: self.navigation.get('show_files', lambda: None)(),
                        style=ft.ButtonStyle(color=files_color)
                    ),
                    bgcolor=ft.Colors.BLUE_50 if current_section == "files" else ft.Colors.TRANSPARENT,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2)
                )
            )
            
            # File Approvals menu item
            approvals_color = ft.Colors.BLUE_700 if current_section == "approvals" else ft.Colors.GREY_700
            menu_items.append(
                ft.Container(
                    content=ft.TextButton(
                        "✅ File Approvals",
                        on_click=lambda e: self.navigation.get('show_approval_files', lambda: None)(),
                        style=ft.ButtonStyle(color=approvals_color)
                    ),
                    bgcolor=ft.Colors.BLUE_50 if current_section == "approvals" else ft.Colors.TRANSPARENT,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2)
                )
            )
            
            # Profile menu item
            profile_color = ft.Colors.BLUE_700 if current_section == "profile" else ft.Colors.GREY_700
            menu_items.append(
                ft.Container(
                    content=ft.TextButton(
                        "👤 Profile Settings",
                        on_click=lambda e: self.navigation.get('show_profile', lambda: None)(),
                        style=ft.ButtonStyle(color=profile_color)
                    ),
                    bgcolor=ft.Colors.BLUE_50 if current_section == "profile" else ft.Colors.TRANSPARENT,
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2)
                )
            )
        
        return ft.Column(menu_items, spacing=5)
    
    def create_user_sidebar(self, current_section: str) -> ft.Column:
        """Create complete user sidebar with avatar and menu - rollback version"""
        return ft.Column([
            # User avatar and basic info
            ft.Container(
                content=ft.Column([
                    self.create_user_avatar(80),
                    ft.Container(height=15),
                    ft.Text(
                        self.user_data.get("fullname", self.username or "User"),
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2
                    ),
                    ft.Text(
                        f"@{self.username}",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20
            ),
            
            # Team tags
            ft.Container(
                content=ft.Text(
                    f"Team: {', '.join(self.user_data.get('team_tags', ['User']))}",
                    size=12,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                margin=ft.margin.only(bottom=20)
            ),
            
            # Menu items
            ft.Container(
                content=self.create_user_menu(current_section),
                padding=ft.padding.symmetric(horizontal=10)
            )
        ])
    
    def create_back_button(self, on_click: Callable, text: str = "← Back") -> ft.Container:
        """Create a back button"""
        return ft.Container(
            content=ft.TextButton(
                text,
                icon=ft.Icons.ARROW_BACK,
                on_click=on_click,
                style=ft.ButtonStyle(color=ft.Colors.BLUE_700)
            ),
            margin=ft.margin.only(left=10, top=10, bottom=10)
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