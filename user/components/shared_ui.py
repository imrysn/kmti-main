import flet as ft
import os
from typing import Optional

class SharedUI:
    """Shared UI components with clickable profile image support"""
    
    def __init__(self, page: ft.Page, username: str, user_data: dict):
        self.page = page
        self.username = username
        self.user_data = user_data
        self.navigation = None
        
        # Initialize profile image service for checking image existence
        try:
            from .profile_image_service import ProfileImageService
            # Assume user folder structure
            user_folder = f"data/uploads/{username}"
            self.image_service = ProfileImageService(user_folder, username)
        except:
            self.image_service = None
    
    def set_navigation(self, navigation):
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
                
                # User name
                ft.Text(
                    self.user_data.get('fullname', 'User'),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLACK87,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Username
                ft.Text(
                    self.username,
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
                
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            margin=ft.margin.only(bottom=15)
        )
    
    def create_navigation_menu(self, current_page: str) -> ft.Container:
        """Create navigation menu"""
        
        def create_menu_item(icon, label, page_key):
            is_active = current_page == page_key
            
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
        
        return ft.Container(
            content=ft.Column([
                create_menu_item(ft.Icons.DASHBOARD, "Folders", "browser"),
                create_menu_item(ft.Icons.PERSON, "Profile", "profile"),
                create_menu_item(ft.Icons.FOLDER, "Files", "files"),
            ], spacing=0),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            padding=ft.padding.all(10)
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
    
    def create_back_button(self, on_click_handler) -> ft.Container:
        """Create back button"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.BLUE_600,
                    icon_size=20,
                    on_click=on_click_handler,
                    tooltip="Back"
                ),
                ft.Text(
                    "Back",
                    size=14,
                    color=ft.Colors.BLUE_600,
                    weight=ft.FontWeight.W_500
                )
            ], spacing=5),
            margin=ft.margin.only(bottom=10),
            on_click=on_click_handler,
            ink=True
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