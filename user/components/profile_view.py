import flet as ft
import os
import sys
import time

class ProfileImageService:
    """ProfileImageService with proper image display handling"""
    def __init__(self, user_folder: str, username: str):
        self.user_folder = user_folder
        self.username = username
        self.profile_images_folder = os.path.join(user_folder, "profile_images")
        os.makedirs(self.profile_images_folder, exist_ok=True)
    
    def has_profile_image(self) -> bool:
        """Check if user has uploaded a profile image"""
        try:
            if not os.path.exists(self.profile_images_folder):
                return False
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            for file in os.listdir(self.profile_images_folder):
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    return True
            return False
        except:
            return False
    
    def get_profile_image_path(self) -> str:
        """Get the path to the user's profile image"""
        try:
            if not os.path.exists(self.profile_images_folder):
                return None
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
            for file in os.listdir(self.profile_images_folder):
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    return os.path.join(self.profile_images_folder, file)
            return None
        except:
            return None
    
    def upload_profile_image(self, source_path: str) -> bool:
        """Upload a new profile image with timestamp for cache busting"""
        try:
            import shutil
            
            # Clear existing images
            if os.path.exists(self.profile_images_folder):
                for file in os.listdir(self.profile_images_folder):
                    file_path = os.path.join(self.profile_images_folder, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            
            # Copy new image with timestamp for cache busting
            file_ext = os.path.splitext(source_path)[1]
            timestamp = int(time.time())
            filename = f"profile_{timestamp}{file_ext}"
            dest_path = os.path.join(self.profile_images_folder, filename)
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            return False

class ProfileView:
    """Profile view with camera icon at bottom of profile picture"""
    
    def __init__(self, page: ft.Page, username: str, profile_service):
        self.page = page
        self.username = username
        self.profile_service = profile_service
        
        # Load user data safely
        try:
            self.user_data = profile_service.load_profile()
        except:
            self.user_data = {
                'fullname': username.title(),
                'email': f'{username}@example.com',
                'role': 'User',
                'join_date': 'N/A'
            }
        
        self.navigation = None
        
        # Initialize profile image service
        user_folder = f"data/uploads/{username}"
        self.image_service = ProfileImageService(user_folder, username)
        
        # Store references to profile image components for real-time updates
        self.profile_avatar_container = None
        self.user_info_card = None
        
        # File picker for profile image
        self.image_picker = ft.FilePicker(
            on_result=self.on_image_selected
        )
        page.overlay.append(self.image_picker)
        
        # Check upload directory setup
        self.check_upload_directory()
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
    
    def on_image_selected(self, e: ft.FilePickerResultEvent):
        """Handle profile image selection with proper display update"""
        if e.files:
            selected_file = e.files[0]
            
            # Check directory setup first
            if not self.check_upload_directory():
                return
            
            try:
                # Basic validation first
                valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
                file_ext = os.path.splitext(selected_file.name)[1].lower()
                
                if file_ext not in valid_extensions:
                    self.show_message(f"Invalid file type. Please select: {', '.join(valid_extensions)}", False)
                    return
                
                # Check file size (10MB limit)
                try:
                    file_size = os.path.getsize(selected_file.path)
                    if file_size > 10 * 1024 * 1024:
                        self.show_message("File too large! Please select image smaller than 10MB.", False)
                        return
                except Exception as size_error:
                    self.show_message("Could not check file size, but proceeding...", False)
                
                # Upload the image first
                success = self.image_service.upload_profile_image(selected_file.path)
                
                if success:
                    self.show_message("Profile image updated successfully!", True)
                    # Force update the display
                    self.force_update_profile_image()
                else:
                    self.show_message("Failed to upload image. Please try again.", False)
                    
            except Exception as upload_error:
                self.show_message(f"Error uploading image: {str(upload_error)}", False)
        else:
            self.show_message("No file selected", False)
    
    def force_update_profile_image(self):
        """Force update the profile image display by recreating the entire container"""
        if self.profile_avatar_container:
            try:
                # Recreate the entire avatar with camera icon
                new_avatar = self.create_clickable_profile_avatar()
                
                # Replace the current avatar in the user info card
                if self.user_info_card:
                    # Find and replace the avatar in the user info card
                    self.user_info_card.content.controls[0] = new_avatar
                
                # Force page update
                self.page.update()
                
                # Small delay then try to refresh again (helps with Flet's image loading)
                def delayed_update():
                    import threading
                    import time
                    time.sleep(0.5)
                    self.page.update()
                
                threading.Thread(target=delayed_update, daemon=True).start()
                
            except Exception as update_error:
                print(f"Update error: {update_error}")
    
    def show_message(self, message: str, is_success: bool):
        """Show success or error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN if is_success else ft.Colors.RED,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def check_upload_directory(self):
        """Check and create upload directories if needed"""
        try:
            user_folder = f"data/uploads/{self.username}"
            profile_images_folder = os.path.join(user_folder, "profile_images")
            
            # Create directories if they don't exist
            os.makedirs(profile_images_folder, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(profile_images_folder, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return True
            
        except Exception as dir_error:
            self.show_message(f"Error setting up upload directory: {str(dir_error)}", False)
            return False
    
    def create_clickable_profile_avatar(self):
        """Create clickable profile avatar with camera icon at bottom"""
        has_image = self.image_service.has_profile_image()
        
        if has_image:
            image_path = self.image_service.get_profile_image_path()
            if image_path and os.path.exists(image_path):
                abs_path = os.path.abspath(image_path)
                print(f"[DEBUG] Loading image from: {abs_path}")
                
                avatar_content = ft.Image(
                    src=abs_path,
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                    border_radius=40,
                    error_content=ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.WHITE)
                )
            else:
                print("[DEBUG] No valid image path, using default icon")
                avatar_content = ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.WHITE)
        else:
            print("[DEBUG] No profile image found, using default icon")
            avatar_content = ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.WHITE)
        
        def trigger_file_picker(e):
            """Trigger file picker"""
            try:
                self.image_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp'],
                    dialog_title="Select Profile Picture"
                )
            except Exception as picker_error:
                self.show_message(f"Error opening file picker: {str(picker_error)}", False)
        
        # Main avatar container
        avatar_container = ft.Container(
            content=avatar_content,
            width=80,
            height=80,
            bgcolor=ft.Colors.BLUE_500 if not has_image else None,
            border_radius=40,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.BLUE_500),
            ink=True
        )
        
        # Camera icon at bottom
        camera_icon = ft.Container(
            content=ft.Icon(
                ft.Icons.CAMERA_ALT,
                size=12,
                color=ft.Colors.WHITE
            ),
            width=24,
            height=24,
            bgcolor=ft.Colors.BLUE_600,
            border_radius=12,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.WHITE)
        )
        
        # Container that holds both avatar and camera icon with proper positioning
        self.profile_avatar_container = ft.Container(
            content=ft.Column([
                # Avatar
                avatar_container,
                # Camera icon positioned at bottom with negative margin to overlap
                ft.Container(
                    content=camera_icon,
                    margin=ft.margin.only(top=-15),  # Move up to overlap with avatar
                    alignment=ft.alignment.center
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
            ),
            on_click=trigger_file_picker,
            tooltip="Click to change profile picture",
            ink=True,
            width=84,  # Slightly wider to accommodate any overflow
            height=84   # Slightly taller to accommodate the camera icon
        )
        
        return self.profile_avatar_container
    
    def create_user_info_card(self):
        """Create user info card with clickable profile image"""
        self.user_info_card = ft.Container(
            content=ft.Column([
                # Clickable profile avatar with camera icon - ONLY this is clickable
                self.create_clickable_profile_avatar(),
                
                ft.Container(height=15),
                
                # Username - NOT clickable
                ft.Text(
                    f"@{self.username}",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Email - NOT clickable
                ft.Text(
                    self.user_data.get('email', f'{self.username}@example.com'),
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                ),
                
                # Role badge - NOT clickable
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
        
        return self.user_info_card
    
    def create_menu_item(self, icon, label, page_key):
        """Create navigation menu item"""
        is_active = page_key == "profile"
        
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
        
        return handle_navigation
    
    def create_navigation_menu(self):
        """Create navigation menu"""
        return ft.Container(
            content=ft.Column([
                self.create_menu_item(ft.Icons.ACCOUNT_CIRCLE, "Profile", "profile"),
                self.create_menu_item(ft.Icons.INSERT_DRIVE_FILE, "Files", "files"),
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
    
    def create_sidebar(self):
        """Create complete sidebar with user info and navigation"""
        return ft.Column([
            # User info card with clickable profile image
            self.create_user_info_card(),
            
            # Navigation menu
            self.create_navigation_menu()
        ], spacing=0)
    
    def show_edit_profile_dialog(self):
        """Show edit profile dialog"""
        # Create form fields
        name_field = ft.TextField(
            label="Full Name",
            value=self.user_data.get("fullname", ""),
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
            # Basic validation
            if not name_field.value.strip():
                self.show_message("Name cannot be empty", False)
                return
            
            if not email_field.value.strip():
                self.show_message("Email cannot be empty", False)
                return
            
            # Update user data
            self.user_data["fullname"] = name_field.value.strip()
            self.user_data["email"] = email_field.value.strip()
            
            # Save to file
            try:
                if self.profile_service.save_profile(self.user_data):
                    dialog.open = False
                    self.page.update()
                    self.show_message("Profile updated successfully!", True)
                    # Refresh the view
                    if self.navigation:
                        self.navigation['show_profile']()
                else:
                    self.show_message("Error saving profile!", False)
            except:
                self.show_message("Error saving profile!", False)
        
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
        """Create profile details section"""
        return ft.Container(
            content=ft.Column([
                # Header without edit button
                ft.Row([
                    ft.Text("Profile Details", size=20, weight=ft.FontWeight.BOLD),
                ]),
                
                ft.Container(height=30),
                
                # Profile details
                ft.Row([
                    ft.Text("Full Name:", size=14, weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(self.user_data.get("fullname", "N/A"), size=14)
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
            ]),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(30),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_back_button(self, on_click_handler, text: str = "Back"):
        """Create back button - ONLY the arrow icon is clickable"""
        return ft.Container(
            content=ft.Row([
                # Only this arrow icon is clickable
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.BLUE_600,
                    icon_size=20,
                    on_click=on_click_handler,
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
    
    def create_content(self):
        """Create main profile content with sidebar profile image"""
        return ft.Container(
            content=ft.Column([
                # Back button
                self.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None
                ),
                
                # Profile layout
                ft.Container(
                    content=ft.Row([
                        # Left sidebar with profile image and navigation
                        ft.Container(
                            content=self.create_sidebar(),
                            width=200
                        ),
                        
                        ft.Container(width=20),
                        
                        # Right side - Profile details
                        self.create_profile_details()
                        
                    ], alignment=ft.MainAxisAlignment.START, expand=True),
                    margin=ft.margin.only(left=15, right=15, top=5, bottom=10)
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0),
            alignment=ft.alignment.top_center,
            expand=True
        )