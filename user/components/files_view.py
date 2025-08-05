import flet as ft
import os
import shutil
import time
import threading
from datetime import datetime
from ..services.file_service import FileService
from .shared_ui import SharedUI
from .dialogs import DialogManager

class FilesView:
    """Files view component for displaying and managing user files with real-time updates"""
    
    def __init__(self, page: ft.Page, username: str, file_service: FileService):
        self.page = page
        self.username = username
        self.file_service = file_service
        
        # Load user profile for shared components
        from ..services.profile_service import ProfileService
        profile_service = ProfileService(file_service.user_folder, username)
        self.user_data = profile_service.load_profile()
        
        self.navigation = None
        self.shared = SharedUI(page, username, self.user_data)
        self.dialogs = DialogManager(page, username)
        
        # File picker
        self.file_picker = ft.FilePicker(on_result=self.upload_file)
        page.overlay.append(self.file_picker)
        
        # Store references for real-time updates - IMPROVED TRACKING
        self.main_files_column_ref = None  # NEW: Direct reference to main files column
        self.file_count_text_ref = None
        self.files_scrollable_container_ref = None  # NEW: Direct reference to scrollable container
        
        # Success notifications
        self.success_notification = None
        self.delete_notification = None  # NEW: Delete notification
    
    def create_success_notification(self):
        """Create simple success notification for uploads"""
        self.success_notification = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=24),
                ft.Text("Files uploaded successfully!", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(2, ft.Colors.GREEN),
            border_radius=8,
            padding=ft.padding.all(15),
            top=20,
            right=20,
            animate_opacity=300,
            opacity=0,
            visible=False
        )
        
        return self.success_notification
    
    def create_delete_notification(self):
        """Create delete success notification"""
        self.delete_notification = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.RED, size=24),
                ft.Text("File deleted successfully!", color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(2, ft.Colors.RED),
            border_radius=8,
            padding=ft.padding.all(15),
            top=20,  # Position at the top like upload notification
            right=20,
            animate_opacity=300,
            opacity=0,
            visible=False
        )
        
        return self.delete_notification
    
    def show_success_animation(self, file_count: int):
        """Show simple success animation for uploads"""
        if self.success_notification:
            # Update the message
            self.success_notification.content.controls[1].value = f"{file_count} file{'s' if file_count != 1 else ''} uploaded successfully!"
            
            # Show notification
            self.success_notification.visible = True
            self.success_notification.opacity = 1
            self.page.update()
            
            # Hide after 2 seconds
            def hide_notification():
                time.sleep(2)
                if self.success_notification:
                    self.success_notification.opacity = 0
                    self.page.update()
                    time.sleep(0.3)  # Wait for fade out
                    self.success_notification.visible = False
                    self.page.update()
            
            threading.Thread(target=hide_notification, daemon=True).start()
    
    def show_delete_success_animation(self, filename: str):
        """Show delete success animation"""
        if self.delete_notification:
            # Update the message with filename
            self.delete_notification.content.controls[1].value = f"'{filename}' deleted successfully!"
            
            # Show notification
            self.delete_notification.visible = True
            self.delete_notification.opacity = 1
            self.page.update()
            
            # Hide after 2 seconds
            def hide_notification():
                time.sleep(2)
                if self.delete_notification:
                    self.delete_notification.opacity = 0
                    self.page.update()
                    time.sleep(0.3)  # Wait for fade out
                    self.delete_notification.visible = False
                    self.page.update()
            
            threading.Thread(target=hide_notification, daemon=True).start()
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
    def calculate_total_size_immediately(self, files):
        """Calculate total size of files immediately"""
        total_size = 0
        for file_info in files:
            size_str = file_info.get('size', '0 MB')
            try:
                if 'KB' in size_str:
                    size_num = float(size_str.replace(' KB', ''))
                    total_size += size_num / 1024  # Convert to MB
                elif 'MB' in size_str:
                    size_num = float(size_str.replace(' MB', ''))
                    total_size += size_num
                elif 'GB' in size_str:
                    size_num = float(size_str.replace(' GB', ''))
                    total_size += size_num * 1024  # Convert to MB
            except:
                pass
        return total_size
    
    def update_file_count_display_immediately(self):
        """Update file count display immediately without any delay"""
        try:
            # Get fresh file data immediately
            files = self.file_service.get_files()
            
            # Calculate new totals immediately
            file_count = len(files)
            total_size = self.calculate_total_size_immediately(files) if files else 0
            
            # Create new file count text
            file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
            if files:
                file_count_text += f" • {total_size:.1f} MB total"
            
            # Update the file count display immediately
            if self.file_count_text_ref:
                self.file_count_text_ref.value = file_count_text
                print(f"DEBUG: Updated file count display to: {file_count_text}")
            
        except Exception as ex:
            print(f"DEBUG: Error updating file count display: {ex}")
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to handle duplicates"""
        user_folder = self.file_service.user_folder
        file_path = os.path.join(user_folder, original_filename)
        
        # If file doesn't exist, return original name
        if not os.path.exists(file_path):
            return original_filename
        
        # Split filename and extension
        name, ext = os.path.splitext(original_filename)
        counter = 1
        
        # Keep incrementing counter until we find a unique name
        while True:
            new_filename = f"{name} ({counter}){ext}"
            new_file_path = os.path.join(user_folder, new_filename)
            
            if not os.path.exists(new_file_path):
                return new_filename
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 1000:
                # Fallback with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{name}_{timestamp}{ext}"
    
    def upload_files_with_duplicates(self, files):
        """Upload files allowing duplicates with unique naming"""
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                # Generate unique filename for this file
                unique_filename = self.generate_unique_filename(file.name)
                
                # Create full path for destination
                dest_path = os.path.join(self.file_service.user_folder, unique_filename)
                
                # Copy the file to destination
                shutil.copy2(file.path, dest_path)
                
                uploaded_files.append({
                    'original': file.name,
                    'saved_as': unique_filename
                })
                
                print(f"DEBUG: Uploaded '{file.name}' as '{unique_filename}'")
                
            except Exception as ex:
                print(f"DEBUG: Failed to upload {file.name}: {str(ex)}")
                failed_files.append({
                    'name': file.name,
                    'error': str(ex)
                })
        
        return uploaded_files, failed_files
    
    def show_delete_confirmation(self, filename: str, file_service: FileService, refresh_callback=None):
        """Show delete confirmation dialog and delete file on user confirmation."""
        def delete_file(e):
            try:
                # Close dialog properly
                dialog.open = False
                self.page.dialog = None
                self.page.update()
                
                file_path = os.path.join(file_service.user_folder, filename)
                print(f"DEBUG: Deleting file at: {file_path}")
                deletion_result = file_service.delete_file(filename)
                print(f"DEBUG: Deletion result: {deletion_result}")
                
                if deletion_result:
                    # Show delete success animation - NEW
                    self.show_delete_success_animation(filename)
                    
                    # COMPLETE TABLE REBUILD APPROACH - MORE RELIABLE
                    print(f"DEBUG: Starting complete table rebuild after deletion")
                    
                    # Use the more robust rebuild approach
                    self.rebuild_files_table_completely()
                    
                    print(f"DEBUG: Complete table rebuild completed")
                    self.page.update()
                else:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"❌ Error deleting file '{filename}'!"),
                        bgcolor=ft.Colors.RED
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    
            except Exception as ex:
                print(f"DEBUG: Exception occurred during deletion: {str(ex)}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error: {str(ex)}"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()

        def cancel_delete(e):
            dialog.open = False
            self.page.dialog = None
            self.page.update()

        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete File"),
            content=ft.Text(f"Are you sure you want to delete '{filename}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=delete_file, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
        )
        
        # Add to overlay first (workaround for some Flet versions)
        self.page.overlay.append(dialog)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def delete_file_immediately(self, filename: str):
        """Delete file immediately without confirmation dialog"""
        try:
            print(f"DEBUG: Attempting immediate deletion of file: {filename}")
            
            # Check if file exists before deletion
            file_path = os.path.join(self.file_service.user_folder, filename)
            print(f"DEBUG: File path: {file_path}")
            print(f"DEBUG: File exists before deletion: {os.path.exists(file_path)}")
            
            # Attempt deletion
            deletion_result = self.file_service.delete_file(filename)
            print(f"DEBUG: Deletion result: {deletion_result}")
            
            if deletion_result:
                print(f"DEBUG: File deleted successfully")
                
                # Show delete success animation - NEW
                self.show_delete_success_animation(filename)
                
                # Use complete table rebuild
                self.rebuild_files_table_completely()
                self.page.update()
            else:
                print(f"DEBUG: File deletion failed")
                # Show error message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error deleting file '{filename}'!"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                
        except Exception as ex:
            print(f"DEBUG: Exception occurred during deletion: {str(ex)}")
            # Show error message
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(ex)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def upload_file(self, e: ft.FilePickerResultEvent):
        """Handle file upload with immediate real-time updates"""
        if e.files:
            try:
                # Upload files with duplicate handling
                uploaded_files, failed_files = self.upload_files_with_duplicates(e.files)
                
                # Show simple success animation
                if uploaded_files:
                    self.show_success_animation(len(uploaded_files))
                
                # Create success message
                if uploaded_files:
                    success_messages = []
                    for file_info in uploaded_files[:3]:  # Show first 3
                        if file_info['original'] != file_info['saved_as']:
                            success_messages.append(f"'{file_info['original']}' → '{file_info['saved_as']}'")
                        else:
                            success_messages.append(f"'{file_info['original']}'")
                    
                    if len(uploaded_files) > 3:
                        success_messages.append(f"and {len(uploaded_files) - 3} more")
                    
                    success_text = "✅ Uploaded: " + ", ".join(success_messages)
                    
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(success_text), 
                        bgcolor=ft.Colors.GREEN
                    )
                    self.page.snack_bar.open = True
                
                # Show failure message if any failed
                if failed_files:
                    failed_names = [f['name'] for f in failed_files[:2]]
                    if len(failed_files) > 2:
                        failed_names.append(f"and {len(failed_files) - 2} more")
                    
                    error_text = f"❌ Failed to upload: {', '.join(failed_names)}"
                    
                    # If there were also successes, show error after success
                    if uploaded_files:
                        def show_error():
                            self.page.snack_bar = ft.SnackBar(
                                content=ft.Text(error_text), 
                                bgcolor=ft.Colors.RED
                            )
                            self.page.snack_bar.open = True
                            self.page.update()
                        
                        # Show error after 3 seconds
                        timer = threading.Timer(3.0, show_error)
                        timer.start()
                    else:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(error_text), 
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                
                # COMPLETE TABLE REBUILD AFTER UPLOAD
                if uploaded_files:
                    print(f"DEBUG: Starting complete table rebuild after upload")
                    self.rebuild_files_table_completely()
                    print(f"DEBUG: Upload table rebuild completed")
                
                # Single page update at the end
                self.page.update()
                
            except Exception as ex:
                # Show error message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Upload failed: {str(ex)}"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def rebuild_files_table_completely(self):
        """IMPROVED: Completely rebuild the files table and file count - more reliable approach"""
        try:
            print(f"DEBUG: Starting complete files table rebuild")
            
            # Get fresh file data from filesystem
            files = self.file_service.get_files()
            print(f"DEBUG: Found {len(files)} files in filesystem")
            
            # Update file count display
            file_count = len(files)
            total_size = self.calculate_total_size_immediately(files) if files else 0
            file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
            if files:
                file_count_text += f" • {total_size:.1f} MB total"
            
            if self.file_count_text_ref:
                self.file_count_text_ref.value = file_count_text
                print(f"DEBUG: Updated file count to: {file_count_text}")
            
            # Rebuild the scrollable content completely
            if self.files_scrollable_container_ref:
                print(f"DEBUG: Rebuilding scrollable container content")
                
                # Clear all existing content
                self.files_scrollable_container_ref.content.controls.clear()
                
                # Add fresh content
                if files:
                    # Add each file row
                    for file in files:
                        file_row = self.create_file_row(file)
                        self.files_scrollable_container_ref.content.controls.append(file_row)
                    print(f"DEBUG: Added {len(files)} file rows")
                else:
                    # Add empty state
                    empty_state = self.create_empty_state()
                    self.files_scrollable_container_ref.content.controls.append(empty_state)
                    print(f"DEBUG: Added empty state")
                
                print(f"DEBUG: Files table rebuild completed successfully")
            else:
                print(f"DEBUG: files_scrollable_container_ref is None - cannot rebuild")
            
        except Exception as ex:
            print(f"DEBUG: Error during complete table rebuild: {ex}")
    
    def create_file_row(self, file_info):
        """Create a file row for the files table with responsive design and proper text handling"""
        
        # Create file icon based on type
        file_type = file_info.get("type", "FILE").upper()
        if file_type in ["JPG", "JPEG", "PNG", "GIF"]:
            icon = ft.Icons.IMAGE_ROUNDED
            icon_color = ft.Colors.GREEN
        elif file_type in ["PDF"]:
            icon = ft.Icons.PICTURE_AS_PDF_ROUNDED
            icon_color = ft.Colors.RED
        elif file_type in ["DOC", "DOCX", "TXT"]:
            icon = ft.Icons.DESCRIPTION_ROUNDED
            icon_color = ft.Colors.BLUE
        elif file_type in ["ZIP", "RAR"]:
            icon = ft.Icons.ARCHIVE_ROUNDED
            icon_color = ft.Colors.ORANGE
        elif file_type in ["MP4", "AVI"]:
            icon = ft.Icons.VIDEO_FILE_ROUNDED
            icon_color = ft.Colors.PURPLE
        elif file_type in ["ICAD", "SLDPRT", "DWG"]:
            icon = ft.Icons.ENGINEERING_ROUNDED
            icon_color = ft.Colors.TEAL
        else:
            icon = ft.Icons.INSERT_DRIVE_FILE_ROUNDED
            icon_color = ft.Colors.GREY_600
        
        return ft.Container(
            content=ft.Row([
                # File name column - with better text handling for responsive design
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=16, color=icon_color),  # Smaller icon for better space usage
                        ft.Container(width=6),  # Reduced spacing
                        ft.Column([
                            ft.Container(
                                content=ft.Text(
                                    file_info["name"], 
                                    size=12,  # Reduced font size
                                    weight=ft.FontWeight.W_500, 
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=1,
                                    no_wrap=True  # Prevent wrapping to avoid overlap
                                ),
                                width=None,  # Let it expand but respect max width
                            ),
                            ft.Text(
                                file_info['size'], 
                                size=10,  # Smaller size text
                                color=ft.Colors.GREY_500,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1
                            ) if file_info.get('size') else ft.Container()
                        ], spacing=1, alignment=ft.MainAxisAlignment.CENTER, tight=True)
                    ], alignment=ft.MainAxisAlignment.START, tight=True),
                    expand=5,  # Increased from 4 to give more space to filename
                    alignment=ft.alignment.center_left
                ),
                
                # Date modified column - with responsive text handling
                ft.Container(
                    content=ft.Text(
                        file_info["date_modified"], 
                        size=10,  # Reduced font size for better fit
                        text_align=ft.TextAlign.CENTER,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        max_lines=1,
                        no_wrap=True
                    ),
                    expand=3,  # Increased from 2 to prevent cramping
                    alignment=ft.alignment.center
                ),
                
                # Type badge column - smaller and more compact
                ft.Container(
                    content=ft.Container(
                        content=ft.Text(
                            file_info["type"], 
                            size=9,  # Smaller text
                            color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER
                        ),
                        bgcolor=icon_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),  # Reduced padding
                        border_radius=6,
                        height=32,
                        alignment=ft.alignment.center,
                        width=80,  # Fixed width to prevent growth
                    ),
                    expand=1,
                    alignment=ft.alignment.center
                ),
                
                # Actions column - compact delete button
                ft.Container(
                    content=ft.ElevatedButton(
                        "Delete",
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        on_click=lambda e, filename=file_info["name"]: self.show_delete_confirmation(
                            filename, 
                            self.file_service, 
                            self.rebuild_files_table_completely
                        ),
                        bgcolor=ft.Colors.RED_50,
                        color=ft.Colors.RED_700,
                        height=32,  # Reduced height
                        width=80,  # Fixed width
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6),
                            text_style=ft.TextStyle(size=11)  # Smaller button text
                        )
                    ),
                    expand=2,
                    alignment=ft.alignment.center
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, tight=True),
            padding=ft.padding.symmetric(horizontal=15, vertical=8),  # Reduced padding
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
            height=60  # Reduced height for more compact rows
        )
    
    def create_empty_state(self):
        """Create empty state when no files are present"""
        return ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=64, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.Text("No files uploaded yet", size=16, color=ft.Colors.GREY_600),
                ft.Text("Click 'Upload Files' to add your files", size=12, color=ft.Colors.GREY_500),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Upload Your First File",
                    icon=ft.Icons.UPLOAD_FILE_ROUNDED,
                    on_click=lambda e: self.file_picker.pick_files(allow_multiple=True),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE
                ),
                ft.Container(height=40)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            height=300  # Fixed height for empty state
        )
    
    def create_files_table(self):
        """IMPROVED: Create the files table with simplified, more reliable structure"""
        files = self.file_service.get_files()
        
        # Create file count summary with reference for real-time updates
        file_count = len(files)
        total_size = self.calculate_total_size_immediately(files) if files else 0
        file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
        if files:
            file_count_text += f" • {total_size:.1f} MB total"
        
        # Create file count text with reference for real-time updates
        self.file_count_text_ref = ft.Text(file_count_text, size=12, color=ft.Colors.GREY_600)
        
        # IMPROVED: Create scrollable content with better reference tracking
        file_rows = []
        if files:
            for file in files:
                file_rows.append(self.create_file_row(file))
        else:
            file_rows.append(self.create_empty_state())
        
        # Create the main scrollable container with DIRECT reference
        scrollable_content = ft.Column(file_rows, spacing=0)
        self.files_scrollable_container_ref = ft.Container(
            content=scrollable_content,
            expand=True
        )
        
        # Create header with real-time file count
        header_container = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("My Files", size=20, weight=ft.FontWeight.BOLD),
                    self.file_count_text_ref  # Use reference for real-time updates
                ], spacing=4),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Upload Files",
                    icon=ft.Icons.CLOUD_UPLOAD_ROUNDED,
                    on_click=lambda e: self.file_picker.pick_files(allow_multiple=True),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ]),
            margin=ft.margin.only(bottom=15)
        )
        
        # SIMPLIFIED: Main files table structure with better reference tracking
        main_files_column = ft.Column([
            # Header with upload button and file count
            header_container,
            
            # Files table container
            ft.Container(
                content=ft.Column([
                    # Table header - updated to match responsive column structure
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text("File", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                                expand=5,  # Updated to match file row
                                alignment=ft.alignment.center_left,
                                padding=ft.padding.only(left=22)  # Align with icon + text
                            ),
                            ft.Container(
                                content=ft.Text("Modified", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                                expand=3,  # Updated to match file row
                                alignment=ft.alignment.center
                            ),
                            ft.Container(
                                content=ft.Text("Type", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                                expand=1,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(
                                content=ft.Text("Actions", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                                expand=2,
                                alignment=ft.alignment.center
                            )
                        ], tight=True),
                        bgcolor=ft.Colors.GREY_700,
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),  # Reduced padding to match rows
                    ),
                    
                    # DIRECT SCROLLABLE CONTAINER - Better reference tracking
                    ft.Container(
                        content=ft.Column([
                            self.files_scrollable_container_ref
                        ], scroll=ft.ScrollMode.AUTO),
                        expand=True,
                        width=None
                    )
                ], expand=True),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                expand=True
            )
        ], expand=True)
        
        # Store reference to main column for potential complete rebuilds
        self.main_files_column_ref = main_files_column
        
        return ft.Container(
            content=main_files_column,
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(20),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            expand=True
        )
    
    def create_content(self):
        """Create the main files content with real-time updates - FIXED BACK BUTTON"""
        return ft.Container(
            content=ft.Stack([
                # Main content
                ft.Column([
                    # Back button - FIXED: Navigate to main dashboard (browser) like profile view
                    self.shared.create_back_button(
                        lambda e: self.navigation['show_browser']() if self.navigation else None,
                        text="Back"
                    ),
                    
                    # Main content card - MAXIMIZED SPACE
                    ft.Container(
                        content=ft.Row([
                            # Left side - Avatar and menu (FIXED AT TOP)
                            ft.Container(
                                content=self.shared.create_user_sidebar("files"),
                                alignment=ft.alignment.top_center,
                                width=200  # FIXED WIDTH FOR USER SIDEBAR
                            ),
                            ft.Container(width=20),  # REDUCED SPACER
                            # Right side - Files content with IMPROVED REAL-TIME UPDATES
                            ft.Container(
                                content=self.create_files_table(),
                                expand=True  # USE ALL REMAINING HORIZONTAL SPACE
                            )
                        ], alignment=ft.MainAxisAlignment.START, 
                           vertical_alignment=ft.CrossAxisAlignment.START,
                           expand=True),
                        margin=ft.margin.only(left=15, right=15, top=5, bottom=10),
                        expand=True
                    )
                ], alignment=ft.MainAxisAlignment.START, spacing=0, expand=True), 
                
                # Success notifications stack (top-right corner)
                self.create_success_notification(),  # Upload notification
                self.create_delete_notification()    # Delete notification
            ]),
            alignment=ft.alignment.top_center,
            expand=True
        )