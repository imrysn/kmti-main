import flet as ft
import os
import shutil
from datetime import datetime
from ..services.file_service import FileService
from .shared_ui import SharedUI
from .dialogs import DialogManager

class FilesView:
    """Files view component for displaying and managing user files with real functionality"""
    
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
        
        # Store reference to files table for direct updates
        self.files_table_ref = None
        self.files_container_ref = None
    
    def set_navigation(self, navigation):
        """Set navigation functions"""
        self.navigation = navigation
        self.shared.set_navigation(navigation)
    
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
    
    def delete_file_immediately(self, filename: str):
        """Delete file immediately without confirmation dialog"""
        try:
            print(f"DEBUG: Attempting immediate deletion of file: {filename}")
            print(f"DEBUG: File service user folder: {self.file_service.user_folder}")
            
            # Check if file exists before deletion
            file_path = os.path.join(self.file_service.user_folder, filename)
            print(f"DEBUG: File path: {file_path}")
            print(f"DEBUG: File exists before deletion: {os.path.exists(file_path)}")
            
            # Attempt deletion
            deletion_result = self.file_service.delete_file(filename)
            print(f"DEBUG: Deletion result: {deletion_result}")
            
            # Check if file exists after deletion attempt
            print(f"DEBUG: File exists after deletion: {os.path.exists(file_path)}")
            
            if deletion_result:
                print(f"DEBUG: File deleted successfully")
                # Success - show success message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ File '{filename}' deleted successfully!"), 
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                
                # Immediately refresh the files table
                print(f"DEBUG: Refreshing files table")
                self.update_files_table_content()
                
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
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
            
            # Show error message
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Error: {str(ex)}"), 
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def upload_file(self, e: ft.FilePickerResultEvent):
        """Handle file upload with duplicate support and instant refresh"""
        if e.files:
            try:
                # Upload files with duplicate handling
                uploaded_files, failed_files = self.upload_files_with_duplicates(e.files)
                
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
                        import threading
                        timer = threading.Timer(3.0, show_error)
                        timer.start()
                    else:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(error_text), 
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                
                # Update the files table content directly
                if self.files_container_ref and uploaded_files:
                    self.update_files_table_content()
                
                # Minimal page update
                self.page.update()
                
            except Exception as ex:
                # Show error message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Upload failed: {str(ex)}"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def update_files_table_content(self):
        """Update only the files table content without affecting anything else"""
        try:
            print(f"DEBUG: Updating files table content")
            # Get fresh file data
            files = self.file_service.get_files()
            print(f"DEBUG: Found {len(files)} files after refresh")
            
            # Update the scrollable files container
            if self.files_container_ref:
                # Clear existing content
                self.files_container_ref.content.controls.clear()
                
                # Add updated file rows
                if files:
                    for file in files:
                        self.files_container_ref.content.controls.append(
                            self.create_file_row(file)
                        )
                else:
                    # Add empty state
                    self.files_container_ref.content.controls.append(
                        self.create_empty_state()
                    )
                
                print(f"DEBUG: Files table updated successfully")
                # Update the page
                self.page.update()
            else:
                print(f"DEBUG: files_container_ref is None")
            
        except Exception as ex:
            print(f"DEBUG: Error updating files table: {ex}")
            import traceback
            print(f"DEBUG: Full traceback: {traceback.format_exc()}")
    
    def refresh_files(self):
        """Refresh the files view"""
        self.update_files_table_content()
    
    def create_file_row(self, file_info):
        """Create a file row for the files table with enhanced functionality (no Edit button)"""
        
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
                # File icon and name - EXPANDED FOR MORE SPACE
                ft.Row([
                    ft.Icon(icon, size=20, color=icon_color),
                    ft.Container(width=10),  # Small spacer
                    ft.Column([
                        ft.Text(file_info["name"], size=13, weight=ft.FontWeight.W_500, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{file_info['size']} • {file_info['type']}", 
                               size=11, color=ft.Colors.GREY_500) if file_info.get('size') else ft.Container()
                    ], spacing=2, expand=True)
                ], spacing=5, expand=5),  # INCREASED FROM 3 TO 5
                
                # Date modified
                ft.Container(
                    content=ft.Text(file_info["date_modified"], size=12),
                    expand=2
                ),
                
                # Type badge
                ft.Container(
                    content=ft.Container(
                        content=ft.Text(file_info["type"], size=10, color=ft.Colors.WHITE),
                        bgcolor=icon_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=12,
                    ),
                    expand=1
                ),
                
                # Action buttons - MODIFIED FOR IMMEDIATE DELETE
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                        tooltip="View Details",
                        icon_size=18,
                        on_click=lambda e, filename=file_info["name"]: self.dialogs.show_file_details_dialog(
                            filename, 
                            self.file_service
                        )
                    ),
                    ft.ElevatedButton(
                        "Delete",
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        on_click=lambda e, filename=file_info["name"]: self.delete_file_immediately(filename),
                        bgcolor=ft.Colors.RED_50,
                        color=ft.Colors.RED_700,
                        height=32,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=6)
                        )
                    )
                ], spacing=8, expand=2)  # REDUCED FROM 3 TO 2 SINCE WE REMOVED EDIT
            ]),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_200))
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
        """Create the files table with real file data and maximized scrollable functionality"""
        files = self.file_service.get_files()
        
        # Create file count summary
        file_count_text = f"{len(files)} file{'s' if len(files) != 1 else ''}"
        if files:
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
                except:
                    pass
            file_count_text += f" • {total_size:.1f} MB total"
        
        # Create scrollable files container
        files_container = ft.Container(
            content=ft.Column([
                self.create_file_row(file) for file in files
            ] if files else [self.create_empty_state()]),
            expand=True
        )
        
        # Store reference for updates
        self.files_container_ref = files_container
        
        # Store reference for direct updates
        files_table = ft.Container(
            content=ft.Column([
                # Header with upload button and file count
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("My Files", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text(file_count_text, size=12, color=ft.Colors.GREY_600)
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
                    margin=ft.margin.only(bottom=15)  # REDUCED MARGIN
                ),
                
                # Files table with maximized scrollable content
                ft.Container(
                    content=ft.Column([
                        # Table header - UPDATED PROPORTIONS
                        ft.Container(
                            content=ft.Row([
                                ft.Text("File", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, expand=5),
                                ft.Text("Modified", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, expand=2),
                                ft.Text("Type", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, expand=1),
                                ft.Text("Actions", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, expand=2)
                            ]),
                            bgcolor=ft.Colors.GREY_700,
                            padding=ft.padding.symmetric(horizontal=20, vertical=12),  # REDUCED PADDING
                        ),
                        
                        # MAXIMIZED SCROLLABLE CONTAINER FOR FILE ROWS
                        ft.Container(
                            content=ft.Column([
                                files_container
                            ], scroll=ft.ScrollMode.AUTO),  # ENABLE SCROLLING HERE
                            expand=True,  # USE ALL AVAILABLE SPACE
                            width=None  # LET IT USE FULL WIDTH
                        )
                    ], expand=True),  # MAKE THE ENTIRE COLUMN EXPAND
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    expand=True  # EXPAND TO USE ALL AVAILABLE HEIGHT
                )
            ], expand=True),  # MAKE THE OUTER COLUMN EXPAND TOO
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(20),  # REDUCED PADDING
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_200),
            expand=True
        )
        
        # Store reference for updates
        self.files_table_ref = files_table
        return files_table
    
    def create_content(self):
        """Create the main files content with maximized space utilization"""
        return ft.Container(
            content=ft.Column([
                # Back button
                self.shared.create_back_button(
                    lambda e: self.navigation['show_browser']() if self.navigation else None
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
                        ft.Container(width=20),  # REDUCED SPACER EVEN MORE
                        # Right side - Files content - EXPANDED TO USE REMAINING SPACE
                        ft.Container(
                            content=self.create_files_table(),
                            expand=True  # USE ALL REMAINING HORIZONTAL SPACE
                        )
                    ], alignment=ft.MainAxisAlignment.START, 
                       vertical_alignment=ft.CrossAxisAlignment.START,
                       expand=True),  # MAKE THE ROW EXPAND VERTICALLY TOO
                    margin=ft.margin.only(left=15, right=15, top=5, bottom=10),  # REDUCED ALL MARGINS
                    expand=True  # USE FULL VERTICAL SPACE
                )
            ], alignment=ft.MainAxisAlignment.START, spacing=0, expand=True),  # MAKE OUTER COLUMN EXPAND
            alignment=ft.alignment.top_center,
            expand=True
        )