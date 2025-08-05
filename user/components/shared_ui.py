import flet as ft
import os
from typing import Optional, Dict, Callable, Any

class SharedUI:
    """Complete shared UI components with enhanced functionality"""
    
    def __init__(self, page: ft.Page, username: str, user_data: dict):
        self.page = page
        self.username = username
        self.user_data = user_data
        self.navigation = None
        self.theme_mode = "light"  # Default theme
        
        # Initialize profile image service for checking image existence
        try:
            from .profile_image_service import ProfileImageService
            # Assume user folder structure
            user_folder = f"data/uploads/{username}"
            self.image_service = ProfileImageService(user_folder, username)
        except:
            self.image_service = None
    
    def set_navigation(self, navigation: Dict[str, Callable]):
        """Set navigation functions"""
        self.navigation = navigation
    
    def create_user_avatar(self, size: int = 80, show_border: bool = True, clickable: bool = False, on_click=None) -> ft.Control:
        """Create user avatar with profile image or default icon"""
        
        # Check if user has uploaded profile image
        if self.image_service and self.image_service.has_profile_image():
            # Show uploaded profile image
            avatar_content = ft.Image(
                src=self.image_service.get_profile_image_path(),
                width=size,
                height=size,
                fit=ft.ImageFit.COVER,
                border_radius=size // 2  # Circular image
            )
        else:
            # Show default avatar
            avatar_content = ft.Icon(
                ft.Icons.PERSON,
                size=size * 0.6,  # Icon size relative to container
                color=ft.Colors.WHITE
            )
        
        avatar_container = ft.Container(
            content=avatar_content,
            width=size,
            height=size,
            bgcolor=ft.Colors.BLUE_500 if not (self.image_service and self.image_service.has_profile_image()) else None,
            border_radius=size // 2,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.BLUE_500 if show_border else ft.Colors.TRANSPARENT),
            padding=0
        )
        
        if clickable and on_click:
            avatar_container.on_click = on_click
            avatar_container.tooltip = "Click to change profile image"
            avatar_container.ink = True
        
        return avatar_container
    
    def create_user_info_card(self, clickable_avatar: bool = False, on_avatar_click=None) -> ft.Container:
        """Create user information card with profile image"""
        return ft.Container(
            content=ft.Column([
                # Profile avatar - can be clickable
                self.create_user_avatar(
                    size=80, 
                    show_border=True, 
                    clickable=clickable_avatar,
                    on_click=on_avatar_click
                ),
                
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
                    self.user_data.get('email', f'{self.username}@gmail.com'),
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Role badge
                ft.Container(
                    content=ft.Text(
                        self.user_data.get('role', 'User').upper(),
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
    
    def create_navigation_menu(self, current_page: str) -> ft.Container:
        """Create navigation menu with improved icons - FOLDERS REMOVED"""
        
        def create_menu_item(icon, label, page_key, badge_count: int = 0):
            is_active = current_page == page_key
            
            # Create badge if there's a count
            badge = None
            if badge_count > 0:
                badge = ft.Container(
                    content=ft.Text(
                        str(badge_count),
                        size=10,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.Colors.RED_500,
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    margin=ft.margin.only(left=5)
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
                    ),
                    badge if badge else ft.Container()  # Add badge if exists
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=15, vertical=12),
                bgcolor=ft.Colors.BLUE_50 if is_active else ft.Colors.TRANSPARENT,
                border_radius=8,
                margin=ft.margin.only(bottom=5),
                on_click=self.get_navigation_handler(page_key),
                ink=True,
                ink_color=ft.Colors.BLUE_100
            )
        
        return ft.Container(
            content=ft.Column([
                # REMOVED: create_menu_item(ft.Icons.FOLDER_OPEN, "Folders", "browser"),
                create_menu_item(ft.Icons.ACCOUNT_CIRCLE, "Profile", "profile"),
                create_menu_item(ft.Icons.INSERT_DRIVE_FILE, "Files", "files"),
            ], spacing=0),
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
    
    def get_navigation_handler(self, page_key: str):
        """Get navigation handler for menu item - BROWSER REMOVED"""
        def handle_navigation(e):
            if self.navigation:
                if page_key == "profile":
                    self.navigation['show_profile']()
                elif page_key == "files":
                    self.navigation['show_files']()
                # REMOVED: browser navigation
        
        return handle_navigation
    
    def create_user_sidebar(self, current_page: str, clickable_avatar: bool = False, on_avatar_click=None) -> ft.Column:
        """Create complete user sidebar with profile image"""
        return ft.Column([
            # User info card with profile image - can be clickable
            self.create_user_info_card(
                clickable_avatar=clickable_avatar,
                on_avatar_click=on_avatar_click
            ),
            
            # Navigation menu
            self.create_navigation_menu(current_page)
        ], spacing=0)
    
    def create_back_button(self, on_click_handler, text: str = "Back", show_to_profile: bool = False) -> ft.Container:
        """Create back button - ONLY the arrow icon is clickable"""
        
        def handle_back_click(e):
            if on_click_handler:
                on_click_handler(e)
            elif show_to_profile and self.navigation and 'show_profile' in self.navigation:
                # Default fallback to profile if no handler provided
                self.navigation['show_profile']()
        
        return ft.Container(
            content=ft.Row([
                # Only this arrow icon is clickable
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.BLUE_600,
                    icon_size=20,
                    on_click=handle_back_click,
                    tooltip="Go back"
                ),
                # This text is just for display - NOT clickable
                ft.Text(
                    text,
                    size=14,
                    color=ft.Colors.BLUE_600,
                    weight=ft.FontWeight.W_500
                )
            ], spacing=5),
            margin=ft.margin.only(bottom=10)
        )
    
    def create_mini_avatar(self, size: int = 40, clickable: bool = False, on_click=None) -> ft.Control:
        """Create small avatar for headers/toolbars"""
        
        # Check if user has uploaded profile image
        if self.image_service and self.image_service.has_profile_image():
            # Show uploaded profile image
            avatar = ft.Container(
                content=ft.Image(
                    src=self.image_service.get_profile_image_path(),
                    width=size,
                    height=size,
                    fit=ft.ImageFit.COVER,
                    border_radius=size // 2
                ),
                border=ft.border.all(1, ft.Colors.BLUE_400),
                border_radius=(size // 2) + 1,
                padding=0
            )
        else:
            # Show default mini avatar
            avatar = ft.Container(
                content=ft.Icon(
                    ft.Icons.PERSON,
                    size=size * 0.6,
                    color=ft.Colors.WHITE
                ),
                width=size,
                height=size,
                bgcolor=ft.Colors.BLUE_500,
                border_radius=size // 2,
                alignment=ft.alignment.center,
                border=ft.border.all(1, ft.Colors.BLUE_400)
            )
        
        if clickable and on_click:
            avatar.on_click = on_click
            avatar.tooltip = "Click to change profile image"
            avatar.ink = True
        
        return avatar
    
    def create_header_bar(self, title: str, actions: list = None, show_user_info: bool = True) -> ft.Container:
        """Create a consistent header bar for all views"""
        header_controls = [
            ft.Text(
                title,
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLACK87
            )
        ]
        
        if show_user_info:
            header_controls.extend([
                ft.Container(expand=True),  # Spacer
                self.create_mini_avatar(clickable=True),
                ft.Container(width=10),
                ft.Text(
                    f"Hi, {self.user_data.get('fullname', self.username)}",
                    size=14,
                    color=ft.Colors.GREY_600
                )
            ])
        
        if actions:
            header_controls.extend(actions)
        
        return ft.Container(
            content=ft.Row(header_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            margin=ft.margin.only(bottom=20),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_action_button(self, text: str, icon: str, on_click, color: str = None, variant: str = "filled") -> ft.ElevatedButton:
        """Create consistent action buttons"""
        button_color = color or ft.Colors.BLUE_600
        
        if variant == "outlined":
            return ft.OutlinedButton(
                content=ft.Row([
                    ft.Icon(icon, size=18),
                    ft.Text(text, size=14)
                ], spacing=8, tight=True),
                on_click=on_click,
                style=ft.ButtonStyle(
                    color=button_color,
                    side=ft.BorderSide(1, button_color)
                )
            )
        else:
            return ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, size=18, color=ft.Colors.WHITE),
                    ft.Text(text, size=14, color=ft.Colors.WHITE)
                ], spacing=8, tight=True),
                on_click=on_click,
                bgcolor=button_color,
                color=ft.Colors.WHITE
            )
    
    def create_info_card(self, title: str, value: str, icon: str, color: str = None) -> ft.Container:
        """Create information display cards"""
        card_color = color or ft.Colors.BLUE_500
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=card_color, size=24),
                    ft.Container(expand=True),
                    ft.Text(
                        title,
                        size=12,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.W_500
                    )
                ]),
                ft.Container(height=10),
                ft.Text(
                    value,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK87
                )
            ], spacing=5),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_loading_indicator(self, text: str = "Loading...") -> ft.Container:
        """Create loading indicator"""
        return ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, stroke_width=4),
                ft.Container(height=20),
                ft.Text(
                    text,
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(40),
            alignment=ft.alignment.center
        )
    
    def create_empty_state(self, title: str, description: str, icon: str, action_text: str = None, on_action=None) -> ft.Container:
        """Create empty state display"""
        controls = [
            ft.Icon(icon, size=64, color=ft.Colors.GREY_400),
            ft.Container(height=20),
            ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=10),
            ft.Text(
                description,
                size=14,
                color=ft.Colors.GREY_500,
                text_align=ft.TextAlign.CENTER
            )
        ]
        
        if action_text and on_action:
            controls.extend([
                ft.Container(height=20),
                ft.ElevatedButton(
                    text=action_text,
                    on_click=on_action,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE
                )
            ])
        
        return ft.Container(
            content=ft.Column(
                controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.center
        )
    
    def show_snackbar(self, message: str, action_text: str = None, on_action=None, bgcolor: str = None):
        """Show snackbar notification"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=bgcolor or ft.Colors.BLUE_600,
            action=action_text,
            action_color=ft.Colors.WHITE,
            on_action=on_action
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def show_confirmation_dialog(self, title: str, content: str, on_confirm, on_cancel=None):
        """Show confirmation dialog"""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
            if on_cancel:
                on_cancel()
        
        def confirm_action(e):
            dialog.open = False
            self.page.update()
            on_confirm()
        
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(content),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Confirm",
                    on_click=confirm_action,
                    bgcolor=ft.Colors.RED_500,
                    color=ft.Colors.WHITE
                )
            ]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_help_dialog(self):
        """Show help dialog"""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Help & Support"),
            content=ft.Column([
                ft.Text("KMTI Data Management System", weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text("• Navigate using the sidebar menu"),
                ft.Text("• Click your avatar to update profile picture"),
                ft.Text("• Upload and manage files in the Files section"),
                ft.Container(height=10),
                ft.Text("For technical support, contact your administrator.", 
                       style=ft.TextStyle(italic=True))
            ], tight=True),
            actions=[ft.TextButton("Got it", on_click=close_dialog)]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_not_implemented_dialog(self, feature_name: str):
        """Show not implemented dialog"""
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Coming Soon"),
            content=ft.Text(f"The {feature_name} feature is coming soon!"),
            actions=[ft.TextButton("OK", on_click=close_dialog)]
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def refresh_avatar(self):
        """Refresh avatar display (call after profile image changes)"""
        # Reload image service to check for updated profile image
        if self.image_service:
            try:
                # Re-initialize to pick up any changes
                user_folder = f"data/uploads/{self.username}"
                from .profile_image_service import ProfileImageService
                self.image_service = ProfileImageService(user_folder, self.username)
            except:
                pass
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics for display"""
        try:
            user_folder = f"data/uploads/{self.username}"
            
            # Count files
            file_count = 0
            if os.path.exists(user_folder):
                for item in os.listdir(user_folder):
                    item_path = os.path.join(user_folder, item)
                    if os.path.isfile(item_path) and not item.startswith('.'):
                        file_count += 1
            
            # Calculate storage used (in MB)
            storage_used = 0
            if os.path.exists(user_folder):
                for root, dirs, files in os.walk(user_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            storage_used += os.path.getsize(file_path)
            
            storage_used_mb = round(storage_used / (1024 * 1024), 2)
            
            return {
                'file_count': file_count,
                'storage_used': storage_used_mb,
                'last_login': 'Today',  # You can implement actual last login tracking
                'account_type': self.user_data.get('role', 'User').title()
            }
        except:
            return {
                'file_count': 0,
                'storage_used': 0.0,
                'last_login': 'Unknown',
                'account_type': 'User'
            }