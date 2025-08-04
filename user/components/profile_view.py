import flet as ft
import os
from ..services.profile_service import ProfileService
from .shared_ui import SharedUI
from .profile_image_service import ProfileImageService

class ProfileView:
    """Profile view with sidebar profile image and real-time updates"""
    
    def __init__(self, page: ft.Page, username: str, profile_service: ProfileService):
        self.page = page
        self.username = username
        self.profile_service = profile_service
        self.user_data = profile_service.load_profile()
        self.navigation = None
        
        # Initialize profile image service
        user_folder = f"data/uploads/{username}"
        self.image_service = ProfileImageService(user_folder, username)
        print(f"Profile image folder: {self.image_service.profile_images_folder}")  # Debug print
        
        # Initialize shared UI with updated image service
        self.shared = SharedUI(page, username, self.user_data)
        self.shared.image_service = self.image_service
        
        # Store references to profile image components for real-time updates
        self.profile_avatar_container = None
        self.user_info_card = None
        
        # File picker for profile image - with explicit configuration
        self.image_picker = ft.FilePicker(
            on_result=self.on_image_selected
        )
        page.overlay.append(self.image_picker)
        print("File picker initialized and added to page overlay")  # Debug print
        
        # Check upload directory setup
        self.check_upload_directory()
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def on_image_selected(self, e: ft.FilePickerResultEvent):
        """Handle profile image selection with real-time update"""
        print(f"File picker result: {e}")  # Debug print
        
        if e.files:
            selected_file = e.files[0]
            print(f"Selected file: {selected_file.name}, Path: {selected_file.path}")  # Debug print
            
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
                    print(f"File size OK: {file_size} bytes")  # Debug print
                except Exception as size_error:
                    print(f"Size check error: {size_error}")  # Debug print
                    self.show_message("Could not check file size, but proceeding...", False)
                
                # Try to upload the image
                print(f"Attempting to upload image...")  # Debug print
                success = self.image_service.upload_profile_image(selected_file.path)
                print(f"Upload result: {success}")  # Debug print
                
                if success:
                    self.show_message("Profile image updated successfully!", True)
                    # Small delay to ensure file is written
                    import time
                    time.sleep(0.2)
                    
                    # Test if we can find the uploaded image
                    self.test_uploaded_image()
                    
                    # Real-time update instead of page refresh
                    self.update_profile_image_realtime()
                    
                    # If real-time update doesn't work, offer manual refresh
                    import threading
                    def delayed_check():
                        time.sleep(1)  # Wait 1 second
                        if self.image_service.has_profile_image():
                            print("Image upload confirmed after delay")
                        else:
                            print("Image still not showing, may need page refresh")
                            # Uncomment next line if you want automatic fallback
                            # self.force_refresh_view()
                    
                    thread = threading.Thread(target=delayed_check)
                    thread.daemon = True
                    thread.start()
                else:
                    self.show_message("Failed to upload image. Please try again.", False)
                    # Fallback: try full page refresh
                    if self.navigation:
                        print("Attempting fallback page refresh...")  # Debug print
                        self.navigation['show_profile']()
                    
            except Exception as upload_error:
                print(f"Upload error: {upload_error}")  # Debug print
                self.show_message(f"Error uploading image: {str(upload_error)}", False)
        else:
            print("No files selected")  # Debug print
            self.show_message("No file selected", False)
    
    def update_profile_image_realtime(self):
        """Update profile image in real-time without page refresh"""
        print("Starting real-time profile image update...")  # Debug print
        
        if self.profile_avatar_container:
            # Re-initialize image service to get latest image
            user_folder = f"data/uploads/{self.username}"
            self.image_service = ProfileImageService(user_folder, self.username)
            
            # Get updated image status
            has_image = self.image_service.has_profile_image()
            print(f"Has image after upload: {has_image}")  # Debug print
            
            if has_image:
                # Get absolute path for better compatibility
                import os
                image_path = self.image_service.get_profile_image_path()
                print(f"Image path for display: {image_path}")  # Debug print
                
                if image_path and os.path.exists(image_path):
                    # Convert to absolute path
                    abs_path = os.path.abspath(image_path)
                    print(f"Absolute path: {abs_path}")  # Debug print
                    
                    # Update to show uploaded image
                    new_content = ft.Image(
                        src=abs_path,
                        width=80,
                        height=80,
                        fit=ft.ImageFit.COVER,
                        border_radius=40,
                        error_content=ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.WHITE)
                    )
                    # Update background color to None since we have an image
                    self.profile_avatar_container.bgcolor = None
                    print("Updated container to show uploaded image")  # Debug print
                else:
                    print(f"Image path doesn't exist: {image_path}")  # Debug print
                    # Show default avatar
                    new_content = ft.Icon(
                        ft.Icons.PERSON,
                        size=48,
                        color=ft.Colors.WHITE
                    )
                    self.profile_avatar_container.bgcolor = ft.Colors.BLUE_500
            else:
                print("No image found, showing default avatar")  # Debug print
                # Update to show default icon
                new_content = ft.Icon(
                    ft.Icons.PERSON,
                    size=48,
                    color=ft.Colors.WHITE
                )
                # Set background color back to blue
                self.profile_avatar_container.bgcolor = ft.Colors.BLUE_500
            
            # Update the container content
            self.profile_avatar_container.content = new_content
            print("Container content updated")  # Debug print
            
            # Refresh shared UI avatar as well
            self.shared.image_service = self.image_service
            self.shared.refresh_avatar()
            print("Shared UI refreshed")  # Debug print
            
            # Force page update to reflect changes
            self.page.update()
            print("Page updated")  # Debug print
            
            # Also update any other profile images on the page
            self.refresh_all_profile_images()
            print("All profile images refreshed")  # Debug print
        else:
            print("No profile avatar container found!")  # Debug print
    
    def show_message(self, message: str, is_success: bool):
        """Show success or error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN if is_success else ft.Colors.RED,
            duration=3000  # Show for 3 seconds
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def force_refresh_view(self):
        """Force refresh the entire view if real-time update fails"""
        if self.navigation:
            self.navigation['show_profile']()
    
    def test_uploaded_image(self):
        """Test if uploaded image can be found and accessed"""
        print("=== Testing uploaded image ===")
        
        # Re-check image service
        user_folder = f"data/uploads/{self.username}"
        test_service = ProfileImageService(user_folder, self.username)
        
        has_image = test_service.has_profile_image()
        print(f"Image service reports has_image: {has_image}")
        
        if has_image:
            image_path = test_service.get_profile_image_path()
            print(f"Image path from service: {image_path}")
            
            if image_path:
                exists = os.path.exists(image_path)
                print(f"File exists on disk: {exists}")
                
                if exists:
                    file_size = os.path.getsize(image_path)
                    print(f"File size: {file_size} bytes")
                    
                    # List all files in profile images directory
                    profile_dir = os.path.join(user_folder, "profile_images")
                    if os.path.exists(profile_dir):
                        files = os.listdir(profile_dir)
                        print(f"Files in profile directory: {files}")
        
        print("=== End test ===")
    
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
            
            print(f"Upload directory setup OK: {profile_images_folder}")  # Debug print
            return True
            
        except Exception as dir_error:
            print(f"Directory setup error: {dir_error}")  # Debug print
            self.show_message(f"Error setting up upload directory: {str(dir_error)}", False)
            return False
    
    def refresh_all_profile_images(self):
        """Refresh all profile images on the page to handle multiple uploads"""
        # Re-initialize image service to get latest image
        user_folder = f"data/uploads/{self.username}"
        self.image_service = ProfileImageService(user_folder, self.username)
        
        # Update shared UI image service as well
        self.shared.image_service = self.image_service
    
    def create_clickable_profile_avatar(self):
        """Create clickable profile avatar for sidebar with reference storage"""
        has_image = self.image_service.has_profile_image()
        
        if has_image:
            # Get absolute path for better compatibility
            import os
            image_path = self.image_service.get_profile_image_path()
            
            if image_path and os.path.exists(image_path):
                # Convert to absolute path
                abs_path = os.path.abspath(image_path)
                # Use file:// protocol for local files
                file_url = f"file:///{abs_path.replace(os.sep, '/')}"
                print(f"Image file URL: {file_url}")  # Debug print
                
                # Show uploaded image
                avatar_content = ft.Image(
                    src=abs_path,  # Try absolute path first
                    width=80,
                    height=80,
                    fit=ft.ImageFit.COVER,
                    border_radius=40,
                    error_content=ft.Icon(ft.Icons.PERSON, size=48, color=ft.Colors.WHITE)
                )
            else:
                # Show default avatar
                avatar_content = ft.Icon(
                    ft.Icons.PERSON,
                    size=48,
                    color=ft.Colors.WHITE
                )
        else:
            # Show default avatar
            avatar_content = ft.Icon(
                ft.Icons.PERSON,
                size=48,
                color=ft.Colors.WHITE
            )
        
        def trigger_file_picker(e):
            """Trigger file picker with debugging"""
            print("Avatar clicked - triggering file picker")  # Debug print
            try:
                self.image_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp'],
                    dialog_title="Select Profile Picture"
                )
                print("File picker triggered successfully")  # Debug print
            except Exception as picker_error:
                print(f"File picker error: {picker_error}")  # Debug print
                self.show_message(f"Error opening file picker: {str(picker_error)}", False)
        
        # Store reference to the container for real-time updates
        self.profile_avatar_container = ft.Container(
            content=avatar_content,
            width=80,
            height=80,
            bgcolor=ft.Colors.BLUE_500 if not has_image else None,
            border_radius=40,
            alignment=ft.alignment.center,
            border=ft.border.all(2, ft.Colors.BLUE_500),
            on_click=trigger_file_picker,
            tooltip="Click to change profile picture",
            ink=True
        )
        
        return self.profile_avatar_container
    
    def create_user_info_card(self):
        """Create user info card with clickable profile image"""
        # Store reference for potential updates
        self.user_info_card = ft.Container(
            content=ft.Column([
                # Clickable profile avatar
                self.create_clickable_profile_avatar(),
                
                ft.Container(height=15),
                
                # User name
                ft.Text(
                    "User",
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
                    self.user_data.get('email', f'{self.username}@example.com'),
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
                self.create_menu_item(ft.Icons.DASHBOARD, "Folders", "browser"),
                self.create_menu_item(ft.Icons.PERSON, "Profile", "profile"),
                self.create_menu_item(ft.Icons.FOLDER, "Files", "files"),
            ], spacing=0),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            padding=ft.padding.all(10)
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
                self.show_message(error_msg, False)
                return
            
            # Update user data
            self.user_data["full_name"] = name_field.value.strip()
            self.user_data["email"] = email_field.value.strip()
            
            # Save to file
            if self.profile_service.save_profile(self.user_data):
                dialog.open = False
                self.page.update()
                self.show_message("Profile updated successfully!", True)
                # Refresh the view
                if self.navigation:
                    self.navigation['show_profile']()
            else:
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
        """Create profile details section"""
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
            ]),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(30),
            border_radius=10,
            border=ft.border.all(1, ft.Colors.GREY_300),
            expand=True
        )
    
    def create_content(self):
        """Create main profile content with sidebar profile image"""
        return ft.Container(
            content=ft.Column([
                # Back button
                self.shared.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None
                ),
                
                # Profile layout
                ft.Container(
                    content=ft.Row([
                        # Left sidebar with profile image and navigation
                        ft.Container(
                            content=self.create_sidebar(),
                            width=220
                        ),
                        
                        ft.Container(width=50),
                        
                        # Right side - Profile details only
                        self.create_profile_details()
                        
                    ], alignment=ft.MainAxisAlignment.START, expand=True),
                    margin=ft.margin.only(left=50, right=50, top=5, bottom=20)
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0),
            alignment=ft.alignment.top_center,
            expand=True
        )