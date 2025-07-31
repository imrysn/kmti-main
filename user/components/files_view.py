import flet as ft
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
    
    def upload_file(self, e: ft.FilePickerResultEvent):
        """Handle file upload with real file persistence and instant refresh"""
        if e.files:
            try:
                # Upload files
                self.file_service.upload_files(e.files)
                
                # Show success message
                file_count = len(e.files)
                file_names = ", ".join([f.name for f in e.files[:3]])
                if file_count > 3:
                    file_names += f" and {file_count - 3} more"
                
                # CORRECT FLET API for snack bar
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ Successfully uploaded: {file_names}"), 
                    bgcolor=ft.Colors.GREEN
                )
                self.page.snack_bar.open = True
                
                # Update the files table content directly
                if self.files_container_ref:
                    self.update_files_table_content()
                
                # Minimal page update that won't affect profile section
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
            # Get fresh file data
            files = self.file_service.get_files()
            
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
                
                # Update the page
                self.page.update()
            
        except Exception as ex:
            print(f"Error updating files table: {ex}")
    
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
                
                # Action buttons - REMOVED EDIT BUTTON, ONLY KEEP INFO AND DELETE
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
                        on_click=lambda e, filename=file_info["name"]: self.dialogs.show_delete_confirmation(
                            filename, 
                            self.file_service,
                            self.refresh_files
                        ),
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