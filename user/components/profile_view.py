import flet as ft
from ..services.profile_service import ProfileService
from .shared_ui import SharedUI

class ProfileView:
    """Profile view component for displaying and editing user profile"""
    
    def __init__(self, page: ft.Page, username: str, profile_service: ProfileService):
        self.page = page
        self.username = username
        self.profile_service = profile_service
        self.user_data = profile_service.load_profile()
        self.navigation = None
        self.shared = SharedUI(page, username, self.user_data)
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def show_edit_profile_dialog(self):
        """Show the edit profile dialog"""
        # Create form fields
        name_field = ft.TextField(
            label="Full Name",
            value=self.user_data.get("full_name", ""),
            width=300,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_400,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8)
        )
        
        email_field = ft.TextField(
            label="Email",
            value=self.user_data.get("email", ""),
            width=300,
            border_color=ft.Colors.GREY_400,
            focused_border_color=ft.Colors.BLUE_400,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8)
        )
        
        def save_profile(e):
            # Validation
            error_msg = self.profile_service.validate_profile_data(
                name_field.value, email_field.value
            )
            
            if error_msg:
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(error_msg), 
                    bgcolor=ft.Colors.RED
                ))
                return
            
            # Update user data
            self.user_data["full_name"] = name_field.value.strip()
            self.user_data["email"] = email_field.value.strip()
            
            # Save to file
            if self.profile_service.save_profile(self.user_data):
                dialog.open = False
                self.page.update()
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Profile updated successfully!"), 
                    bgcolor=ft.Colors.GREEN
                ))
                # Refresh the view
                if self.navigation:
                    self.navigation['show_profile']()
            else:
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Error saving profile!"), 
                    bgcolor=ft.Colors.RED
                ))
        
        def cancel_edit(e):
            dialog.open = False
            self.page.update()
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Text("Edit Profile", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.GREY_600,
                    on_click=cancel_edit
                )
            ]),
            content=ft.Container(
                width=500,
                height=300,
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Full Name:", size=14, weight=ft.FontWeight.W_500, width=80),
                                ft.Container(width=20),
                                name_field
                            ], alignment=ft.MainAxisAlignment.START),
                            
                            ft.Container(height=20),
                            
                            ft.Row([
                                ft.Text("Email:", size=14, weight=ft.FontWeight.W_500, width=80),
                                ft.Container(width=20),
                                email_field
                            ], alignment=ft.MainAxisAlignment.START),
                            
                            ft.Container(height=20),
                            
                            ft.Row([
                                ft.Text("Role:", size=14, weight=ft.FontWeight.W_500, width=80),
                                ft.Container(width=20),
                                ft.Text(self.user_data.get("role", "User"), size=14, color=ft.Colors.GREY_700)
                            ], alignment=ft.MainAxisAlignment.START),
                            
                            ft.Container(height=10),
                            
                            ft.Row([
                                ft.Text("Join Date:", size=14, weight=ft.FontWeight.W_500, width=80),
                                ft.Container(width=20),
                                ft.Text(self.user_data.get("join_date", "N/A"), size=14, color=ft.Colors.GREY_700)
                            ], alignment=ft.MainAxisAlignment.START),
                        ], spacing=0),
                        padding=ft.padding.all(20)
                    )
                ], spacing=0)
            ),
            actions=[
                ft.Container(
                    content=ft.Row([
                        ft.Container(expand=True),
                        ft.TextButton(
                            "Cancel",
                            on_click=cancel_edit,
                            style=ft.ButtonStyle(
                                color=ft.Colors.GREY_700,
                                bgcolor=ft.Colors.TRANSPARENT
                            )
                        ),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "Save",
                            on_click=save_profile,
                            bgcolor=ft.Colors.BLACK,
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
    
    def create_profile_details(self):
        """Create the profile details section"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Full Name:", size=14, weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(self.user_data.get("full_name", "N/A"), size=14)
                ]),
                ft.Container(height=20),
                ft.Row([
                    ft.Text("Email:", size=14, weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(self.user_data.get("email", "N/A"), size=14)
                ]),
                ft.Container(height=20),
                ft.Row([
                    ft.Text("Role:", size=14, weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(self.user_data.get("role", "User"), size=14)
                ]),
                ft.Container(height=20),
                ft.Row([
                    ft.Text("Join Date:", size=14, weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(self.user_data.get("join_date", "N/A"), size=14)
                ]),
                ft.Container(height=40),
                ft.ElevatedButton(
                    "Edit Profile",
                    on_click=lambda e: self.show_edit_profile_dialog(),
                    bgcolor=ft.Colors.GREY_300,
                    color=ft.Colors.BLACK
                )
            ]),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(30),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            expand=True
        )
    
    def create_content(self):
        """Create the main profile content"""
        return ft.Container(
            content=ft.Column([
                # Back button
                self.shared.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None
                ),
                
                # Profile card
                ft.Container(
                    content=ft.Row([
                        # Left side - Avatar and menu
                        self.shared.create_user_sidebar("profile"),
                        ft.Container(width=50),
                        # Right side - Profile details
                        self.create_profile_details()
                    ], alignment=ft.MainAxisAlignment.START),
                    margin=ft.margin.only(left=50, right=50, top=5, bottom=20)
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0),
            alignment=ft.alignment.top_center,
            expand=True
        )