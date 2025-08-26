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
    """Files view component with CARD-BASED UI DESIGN + ADMIN APPROVAL STATUS"""
    
    def __init__(self, page: ft.Page, username: str, file_service: FileService):
        self.page = page
        self.username = username
        self.file_service = file_service
        
        # Load user profile for shared components
        from ..services.profile_service import ProfileService
        profile_service = ProfileService(file_service.user_folder, username)
        self.user_data = profile_service.load_profile()
        
        # Load approval service for submissions
        from ..services.approval_file_service import ApprovalFileService
        self.approval_service = ApprovalFileService(file_service.user_folder, username)
        
        self.navigation = None
        self.shared = SharedUI(page, username, self.user_data)
        self.dialogs = DialogManager(page, username)
        
        # File picker
        self.file_picker = ft.FilePicker(on_result=self.upload_file)
        page.overlay.append(self.file_picker)
        
        # Store references for real-time updates
        self.main_files_column_ref = None
        self.file_count_text_ref = None
        self.files_scrollable_container_ref = None
        
        # Success notifications
        self.success_notification = None
        self.delete_notification = None
    
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
            top=20,
            right=20,
            opacity=0,
            visible=False
        )
        
        return self.delete_notification
    
    def show_success_animation(self, file_count: int):
        """Show simple success animation for uploads"""
        if self.success_notification:
            self.success_notification.content.controls[1].value = f"{file_count} file{'s' if file_count != 1 else ''} uploaded successfully!"
            self.success_notification.visible = True
            self.success_notification.opacity = 1
            self.page.update()
            
            def hide_notification():
                time.sleep(2)
                if self.success_notification:
                    self.success_notification.opacity = 0
                    self.page.update()
                    time.sleep(0.3)
                    self.success_notification.visible = False
                    self.page.update()
            
            threading.Thread(target=hide_notification, daemon=True).start()
    
    def show_delete_success_animation(self, filename: str):
        """Show delete success animation"""
        if self.delete_notification:
            self.delete_notification.content.controls[1].value = f"'{filename}' deleted successfully!"
            self.delete_notification.visible = True
            self.delete_notification.opacity = 1
            self.page.update()
            
            def hide_notification():
                time.sleep(2)
                if self.delete_notification:
                    self.delete_notification.opacity = 0
                    self.page.update()
                    time.sleep(0.3)
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
                    total_size += size_num / 1024
                elif 'MB' in size_str:
                    size_num = float(size_str.replace(' MB', ''))
                    total_size += size_num
                elif 'GB' in size_str:
                    size_num = float(size_str.replace(' GB', ''))
                    total_size += size_num * 1024
            except:
                pass
        return total_size
    
    def update_file_count_display_immediately(self):
        """Update file count display immediately without any delay"""
        try:
            files = self.file_service.get_files()
            file_count = len(files)
            total_size = self.calculate_total_size_immediately(files) if files else 0
            
            file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
            if files:
                file_count_text += f" • {total_size:.1f} MB total"
            
            if self.file_count_text_ref:
                self.file_count_text_ref.value = file_count_text
                print(f"DEBUG: Updated file count display to: {file_count_text}")
            
        except Exception as ex:
            print(f"DEBUG: Error updating file count display: {ex}")
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to handle duplicates"""
        user_folder = self.file_service.user_folder
        file_path = os.path.join(user_folder, original_filename)
        
        if not os.path.exists(file_path):
            return original_filename
        
        name, ext = os.path.splitext(original_filename)
        counter = 1
        
        while True:
            new_filename = f"{name} ({counter}){ext}"
            new_file_path = os.path.join(user_folder, new_filename)
            
            if not os.path.exists(new_file_path):
                return new_filename
            
            counter += 1
            
            if counter > 1000:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{name}_{timestamp}{ext}"
    
    def upload_files_with_duplicates(self, files):
        """Upload files allowing duplicates with unique naming"""
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                unique_filename = self.generate_unique_filename(file.name)
                dest_path = os.path.join(self.file_service.user_folder, unique_filename)
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
    
    def show_submit_dialog(self, filename: str):
        """Show submit dialog for file approval"""
        def handle_submit(values):
            description = values.get("description", "")
            tags_str = values.get("tags", "")
            tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []
            
            if self.approval_service.submit_file_for_approval(filename, description, tags):
                self.dialogs.show_success_notification(f"'{filename}' submitted for approval!")
                self.rebuild_files_list_completely()
            else:
                self.dialogs.show_error_notification("Failed to submit file for approval")
        
        fields = [
            {
                "key": "description",
                "type": "multiline",
                "label": "Description (optional)",
                "value": "",
                "min_lines": 2,
                "max_lines": 4,
                "hint": "Describe the purpose of this file"
            },
            {
                "key": "tags",
                "type": "text",
                "label": "Tags (comma-separated, optional)",
                "value": "",
                "hint": "e.g., report, draft, urgent"
            }
        ]
        
        self.dialogs.show_input_dialog(
            title=f"Submit '{filename}' for Approval",
            fields=fields,
            on_submit=handle_submit,
            submit_text="Submit"
        )
    
    def show_delete_confirmation(self, filename: str, file_service: FileService, refresh_callback=None):
        """Show delete confirmation dialog and delete file on user confirmation."""
        def delete_file():
            try:
                file_path = os.path.join(file_service.user_folder, filename)
                print(f"DEBUG: Deleting file at: {file_path}")
                deletion_result = file_service.delete_file(filename)
                print(f"DEBUG: Deletion result: {deletion_result}")
                
                if deletion_result:
                    self.show_delete_success_animation(filename)
                    print(f"DEBUG: Starting complete list rebuild after deletion")
                    self.rebuild_files_list_completely()
                    print(f"DEBUG: Complete list rebuild completed")
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

        self.dialogs.show_confirmation_dialog(
            title="Delete File",
            message=f"Are you sure you want to delete '{filename}'?",
            on_confirm=delete_file,
            confirm_text="Delete",
            is_destructive=True
        )
    
    def open_file(self, filename: str):
        """Open file using the default system application"""
        try:
            file_path = os.path.join(self.file_service.user_folder, filename)
            
            if not os.path.exists(file_path):
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ File '{filename}' not found!"),
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Open file with default system application
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux and others
                subprocess.call(["xdg-open", file_path])
            
            print(f"DEBUG: Opened file: {filename}")
            
            # Show success notification
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"📂 Opening '{filename}'..."),
                bgcolor=ft.Colors.BLUE
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"DEBUG: Error opening file {filename}: {str(ex)}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"❌ Could not open '{filename}': {str(ex)}"),
                bgcolor=ft.Colors.RED
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def upload_file(self, e: ft.FilePickerResultEvent):
        """Handle file upload with immediate real-time updates"""
        if e.files:
            try:
                uploaded_files, failed_files = self.upload_files_with_duplicates(e.files)
                
                if uploaded_files:
                    self.show_success_animation(len(uploaded_files))
                
                if uploaded_files:
                    success_messages = []
                    for file_info in uploaded_files[:3]:
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
                
                if failed_files:
                    failed_names = [f['name'] for f in failed_files[:2]]
                    if len(failed_files) > 2:
                        failed_names.append(f"and {len(failed_files) - 2} more")
                    
                    error_text = f"❌ Failed to upload: {', '.join(failed_names)}"
                    
                    if uploaded_files:
                        def show_error():
                            self.page.snack_bar = ft.SnackBar(
                                content=ft.Text(error_text), 
                                bgcolor=ft.Colors.RED
                            )
                            self.page.snack_bar.open = True
                            self.page.update()
                        
                        timer = threading.Timer(3.0, show_error)
                        timer.start()
                    else:
                        self.page.snack_bar = ft.SnackBar(
                            content=ft.Text(error_text), 
                            bgcolor=ft.Colors.RED
                        )
                        self.page.snack_bar.open = True
                
                if uploaded_files:
                    print(f"DEBUG: Starting complete list rebuild after upload")
                    self.rebuild_files_list_completely()
                    print(f"DEBUG: Upload list rebuild completed")
                
                self.page.update()
                
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Upload failed: {str(ex)}"), 
                    bgcolor=ft.Colors.RED
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def sort_files_by_date(self, files):
        """Sort files by creation/modification time (newest first) - use the most recent timestamp"""
        try:
            def get_file_timestamp(file_info):
                try:
                    file_path = os.path.join(self.file_service.user_folder, file_info["name"])
                    # Get both creation and modification time, use the most recent one
                    mtime = os.path.getmtime(file_path)
                    ctime = os.path.getctime(file_path)
                    # Return the most recent timestamp (max of creation and modification time)
                    return max(mtime, ctime)
                except:
                    return 0
            
            # Sort by timestamp, newest first
            sorted_files = sorted(files, key=get_file_timestamp, reverse=True)
            print(f"DEBUG: Sorted {len(sorted_files)} files by timestamp (newest first)")
            
            # Debug: print first few file timestamps
            for i, file_info in enumerate(sorted_files[:3]):
                try:
                    file_path = os.path.join(self.file_service.user_folder, file_info["name"])
                    mtime = os.path.getmtime(file_path)
                    ctime = os.path.getctime(file_path)
                    print(f"DEBUG: File {i+1}: {file_info['name']} - mtime: {mtime}, ctime: {ctime}, max: {max(mtime, ctime)}")
                except:
                    pass
            
            return sorted_files
        except Exception as ex:
            print(f"DEBUG: Error sorting files by date: {ex}")
            # Fall back to original order if sorting fails
            return files
    
    def separate_files_by_submission_status(self, files):
        """Separate files into submitted and non-submitted lists"""
        submitted_files = []
        not_submitted_files = []
        
        for file_info in files:
            approval_status = self.approval_service.get_file_approval_status(file_info["name"])
            is_submitted = approval_status.get("submitted_for_approval", False)
            
            if is_submitted:
                submitted_files.append(file_info)
            else:
                not_submitted_files.append(file_info)
        
        print(f"DEBUG: Separated files - {len(not_submitted_files)} not submitted, {len(submitted_files)} submitted")
        return not_submitted_files, submitted_files
    
    def get_file_approval_status_detailed(self, filename: str):
        """Get detailed approval status including admin approval status"""
        try:
            # Get basic approval status (submitted_for_approval)
            approval_status = self.approval_service.get_file_approval_status(filename)
            
            # Check if file has been approved by admin by looking at submissions
            submissions = self.approval_service.get_user_submissions()
            for submission in submissions:
                if submission.get("original_filename") == filename:
                    status = submission.get("status", "")
                    return {
                        "submitted_for_approval": approval_status.get("submitted_for_approval", False),
                        "admin_status": status,
                        "is_approved": status == "approved",
                        "is_rejected": status == "rejected",
                        "needs_changes": status == "changes_requested",
                        "is_pending": status == "pending"
                    }
            
            # If not found in submissions but marked as submitted, it's pending
            if approval_status.get("submitted_for_approval", False):
                return {
                    "submitted_for_approval": True,
                    "admin_status": "pending",
                    "is_approved": False,
                    "is_rejected": False,
                    "needs_changes": False,
                    "is_pending": True
                }
            
            # File not submitted for approval
            return {
                "submitted_for_approval": False,
                "admin_status": None,
                "is_approved": False,
                "is_rejected": False,
                "needs_changes": False,
                "is_pending": False
            }
            
        except Exception as e:
            print(f"DEBUG: Error getting detailed approval status for {filename}: {e}")
            return {
                "submitted_for_approval": False,
                "admin_status": None,
                "is_approved": False,
                "is_rejected": False,
                "needs_changes": False,
                "is_pending": False
            }
    
    def rebuild_files_list_completely(self):
        """IMPROVED: Completely rebuild the files list - separated by submission status with newest files first"""
        try:
            print(f"DEBUG: Starting complete files list rebuild")
            
            files = self.file_service.get_files()
            print(f"DEBUG: Found {len(files)} files in filesystem")
            
            # Sort files by timestamp (newest first)
            files = self.sort_files_by_date(files)
            
            # Separate files by submission status
            not_submitted_files, submitted_files = self.separate_files_by_submission_status(files)
            
            file_count = len(files)
            total_size = self.calculate_total_size_immediately(files) if files else 0
            file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
            if files:
                file_count_text += f" • {total_size:.1f} MB total"
            
            if self.file_count_text_ref:
                self.file_count_text_ref.value = file_count_text
                print(f"DEBUG: Updated file count to: {file_count_text}")
            
            if self.files_scrollable_container_ref:
                print(f"DEBUG: Rebuilding scrollable container content with separated sections")
                
                self.files_scrollable_container_ref.content.controls.clear()
                
                if files:
                    # Add "Not Submitted" section if there are unsubmitted files
                    if not_submitted_files:
                        # Section header for not submitted files
                        section_header = ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.UPLOAD_FILE, color=ft.Colors.BLUE, size=20),
                                ft.Text("Not Submitted", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                                ft.Text(f"({len(not_submitted_files)})", size=14, color=ft.Colors.GREY_600)
                            ], spacing=8),
                            margin=ft.margin.only(bottom=10, top=5)
                        )
                        self.files_scrollable_container_ref.content.controls.append(section_header)
                        
                        # Add not submitted file cards
                        for file in not_submitted_files:
                            file_card = self.create_file_card(file)
                            self.files_scrollable_container_ref.content.controls.append(file_card)
                    
                    # Add spacing between sections if both exist
                    if not_submitted_files and submitted_files:
                        spacing = ft.Container(height=20)
                        self.files_scrollable_container_ref.content.controls.append(spacing)
                    
                    # Add "Submitted" section if there are submitted files
                    if submitted_files:
                        # Section header for submitted files
                        section_header = ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=20),
                                ft.Text("Submitted for Approval", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                ft.Text(f"({len(submitted_files)})", size=14, color=ft.Colors.GREY_600)
                            ], spacing=8),
                            margin=ft.margin.only(bottom=10, top=5)
                        )
                        self.files_scrollable_container_ref.content.controls.append(section_header)
                        
                        # Add submitted file cards
                        for file in submitted_files:
                            file_card = self.create_file_card(file)
                            self.files_scrollable_container_ref.content.controls.append(file_card)
                    
                    print(f"DEBUG: Added {len(not_submitted_files)} not submitted + {len(submitted_files)} submitted file cards")
                else:
                    empty_state = self.create_empty_state()
                    self.files_scrollable_container_ref.content.controls.append(empty_state)
                    print(f"DEBUG: Added empty state")
                
                print(f"DEBUG: Files list rebuild completed successfully")
            else:
                print(f"DEBUG: files_scrollable_container_ref is None - cannot rebuild")
            
        except Exception as ex:
            print(f"DEBUG: Error during complete list rebuild: {ex}")
    
    def create_file_card(self, file_info):
        """Create a file card with ADMIN APPROVAL STATUS - FIXED to prevent hover tooltip on action buttons"""
        
        # Check detailed approval status including admin decision
        detailed_status = self.get_file_approval_status_detailed(file_info["name"])
        is_submitted = detailed_status["submitted_for_approval"]
        is_approved = detailed_status["is_approved"]
        is_rejected = detailed_status["is_rejected"]
        needs_changes = detailed_status["needs_changes"]
        is_pending = detailed_status["is_pending"]
        
        # Determine file type and icon
        file_type = file_info.get("type", "FILE").upper()
        if file_type in ["JPG", "JPEG", "PNG", "GIF"]:
            icon = ft.Icons.IMAGE_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.GREEN
        elif file_type in ["PDF"]:
            icon = ft.Icons.PICTURE_AS_PDF_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.RED
        elif file_type in ["DOC", "DOCX", "TXT"]:
            icon = ft.Icons.DESCRIPTION_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.BLUE
        elif file_type in ["ZIP", "RAR"]:
            icon = ft.Icons.ARCHIVE_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.ORANGE
        elif file_type in ["MP4", "AVI"]:
            icon = ft.Icons.VIDEO_FILE_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.PURPLE
        elif file_type in ["ICAD", "SLDPRT", "DWG"]:
            icon = ft.Icons.ENGINEERING_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.TEAL
        else:
            icon = ft.Icons.INSERT_DRIVE_FILE_ROUNDED
            icon_color = ft.Colors.WHITE
            badge_color = ft.Colors.GREY_600
        
        # Build the card components step by step
        file_icon = ft.Container(
            content=ft.Icon(icon, color=icon_color, size=24),
            bgcolor=badge_color,
            width=50,
            height=50,
            border_radius=8,
            alignment=ft.alignment.center
        )
        
        file_name_text = ft.Text(
            file_info["name"], 
            size=14,
            weight=ft.FontWeight.W_500, 
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1
        )
        
        file_size_text = ft.Text(
            file_info.get('size', ''), 
            size=12,
            color=ft.Colors.GREY_600
        )
        
        file_info_column = ft.Column(
            controls=[file_name_text, file_size_text],
            spacing=2, 
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        file_info_container = ft.Container(
            content=file_info_column,
            expand=True,
            alignment=ft.alignment.center_left,
            on_click=lambda e, fn=file_info["name"]: self.open_file(fn),
            ink=True,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            tooltip=f"Click to open '{file_info['name']}'"
        )
        
        # Submission status - show different statuses based on admin decision
        submission_status_controls = []

        # Approved status
        if is_approved:
            submission_status_controls.append(ft.Row([
                ft.Icon(ft.Icons.VERIFIED, color=ft.Colors.GREEN, size=16),
                ft.Text("Approved by admin", size=12, color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)
            ], spacing=5))

        # Rejected status
        elif is_rejected:
            submission_status_controls.append(ft.Row([
                ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED, size=16),
                ft.Text("Rejected by admin", size=12, color=ft.Colors.RED, weight=ft.FontWeight.BOLD)
            ], spacing=5))

        # Changes requested status
        elif needs_changes:
            submission_status_controls.append(ft.Row([
                ft.Icon(ft.Icons.EDIT, color=ft.Colors.ORANGE, size=16),
                ft.Text("Changes requested", size=12, color=ft.Colors.ORANGE, weight=ft.FontWeight.BOLD)
            ], spacing=5))

        # Pending approval status
        elif is_pending:
            submission_status_controls.append(ft.Row([
                ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.BLUE, size=16),
                ft.Text("Pending approval", size=12, color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD)
            ], spacing=5))

        # Original submitted status (fallback)
        elif is_submitted:
            submission_status_controls.append(ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                ft.Text("Submitted for approval", size=12, color=ft.Colors.GREEN, italic=True)
            ], spacing=5))

        # Create the submission status container
        if submission_status_controls:
            submission_status = ft.Container(
                content=submission_status_controls[0],
                visible=True
            )
        else:
            submission_status = ft.Container()
        
        # Submit button with event stopping - UPDATED LOGIC FOR ADMIN APPROVAL
        def handle_submit_click(e, fn=file_info["name"]):
            e.control.page.update()  # Stop event propagation
            if not is_submitted or is_rejected or needs_changes:
                self.show_submit_dialog(fn)
        
        submit_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.SEND if not is_submitted or is_rejected or needs_changes else ft.Icons.CHECK, size=16),
                ft.Text("Submit" if not is_submitted or is_rejected or needs_changes else "Submitted", size=12)
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            on_click=handle_submit_click,
            disabled=is_submitted and not is_rejected and not needs_changes,
            bgcolor=ft.Colors.GREEN_100 if not is_submitted or is_rejected or needs_changes else ft.Colors.GREY_100,
            color=ft.Colors.GREEN_700 if not is_submitted or is_rejected or needs_changes else ft.Colors.GREY_500,
            height=35,
            width=100,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0
            ),
            visible=not is_approved  # Hide submit button if already approved
        )
        
        # Delete button with event stopping
        def handle_delete_click(e, fn=file_info["name"]):
            e.control.page.update()  # Stop event propagation
            self.show_delete_confirmation(fn, self.file_service, self.rebuild_files_list_completely)
        
        delete_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE_OUTLINE, size=16),
                ft.Text("Delete", size=12)
            ], spacing=5, alignment=ft.MainAxisAlignment.CENTER),
            on_click=handle_delete_click,
            bgcolor=ft.Colors.RED_50,
            color=ft.Colors.RED_700,
            height=35,
            width=90,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0
            )
        )
        
        # Action buttons container that prevents click-through
        action_buttons_container = ft.Container(
            content=ft.Row(
                controls=[submit_button, ft.Container(width=10), delete_button] if not is_approved else [ft.Container(width=110), delete_button],
                spacing=0
            ),
            # This container will absorb clicks and prevent them from reaching the parent
            on_click=lambda e: None,  # Absorb the click event
            ink=False  # Remove ink effect for this container
        )
        
        # Main content row
        main_row = ft.Row([
            file_icon,
            ft.Container(width=15),
            file_info_container,
            submission_status,
            ft.Container(width=15),
            action_buttons_container,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Final container - removed the on_click and tooltip from here to prevent conflicts
        card_container = ft.Container(
            content=main_row,
            padding=ft.padding.all(20),
            margin=ft.margin.only(bottom=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            ink=False
        )
        
        return card_container
    
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
            height=300
        )
    
    def create_files_list(self):
        """Create the files list with card-based design - separated by submission status with newest files first"""
        files = self.file_service.get_files()
        
        # Sort files by timestamp (newest first)
        files = self.sort_files_by_date(files)
        
        # Separate files by submission status
        not_submitted_files, submitted_files = self.separate_files_by_submission_status(files)
        
        file_count = len(files)
        total_size = self.calculate_total_size_immediately(files) if files else 0
        file_count_text = f"{file_count} file{'s' if file_count != 1 else ''}"
        if files:
            file_count_text += f" • {total_size:.1f} MB total"
        
        self.file_count_text_ref = ft.Text(file_count_text, size=12, color=ft.Colors.GREY_600)
        
        file_cards = []
        if files:
            # Add "Not Submitted" section if there are unsubmitted files
            if not_submitted_files:
                # Section header for not submitted files
                section_header = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.UPLOAD_FILE, color=ft.Colors.BLUE, size=20),
                        ft.Text("Not Submitted", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                        ft.Text(f"({len(not_submitted_files)})", size=14, color=ft.Colors.GREY_600)
                    ], spacing=8),
                    margin=ft.margin.only(bottom=10, top=5)
                )
                file_cards.append(section_header)
                
                # Add not submitted file cards
                for file in not_submitted_files:
                    file_cards.append(self.create_file_card(file))
            
            # Add spacing between sections if both exist
            if not_submitted_files and submitted_files:
                spacing = ft.Container(height=20)
                file_cards.append(spacing)
            
            # Add "Submitted" section if there are submitted files
            if submitted_files:
                # Section header for submitted files
                section_header = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=20),
                        ft.Text("Submitted for Approval", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                        ft.Text(f"({len(submitted_files)})", size=14, color=ft.Colors.GREY_600)
                    ], spacing=8),
                    margin=ft.margin.only(bottom=10, top=5)
                )
                file_cards.append(section_header)
                
                # Add submitted file cards
                for file in submitted_files:
                    file_cards.append(self.create_file_card(file))
        else:
            file_cards.append(self.create_empty_state())
        
        scrollable_content = ft.Column(file_cards, spacing=0)
        self.files_scrollable_container_ref = ft.Container(
            content=scrollable_content,
            expand=True
        )
        
        header_container = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("My Files", size=20, weight=ft.FontWeight.BOLD),
                    self.file_count_text_ref
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
            margin=ft.margin.only(bottom=20)
        )
        
        main_files_column = ft.Column([
            header_container,
            
            # Files list container
            ft.Container(
                content=ft.Column([
                    self.files_scrollable_container_ref
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True,
                bgcolor=ft.Colors.GREY_50,
                padding=ft.padding.all(15),
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_200)
            )
        ], expand=True)
        
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
        """Create the main files content with CONSISTENT UI DESIGN"""
        return ft.Container(
            content=ft.Stack([
                # Main content
                ft.Column([
                    # Back button - CONSISTENT DESIGN
                    self.shared.create_back_button(
                        lambda e: self.navigation['show_browser']() if self.navigation else None,
                        text="Back"
                    ),
                    
                    # Main content layout - CONSISTENT WITH IMAGE 1
                    ft.Container(
                        content=ft.Row([
                            # Left sidebar - CONSISTENT USER INFO CARD + NAVIGATION
                            ft.Container(
                                content=self.shared.create_user_sidebar("files"),
                                width=200
                            ),
                            
                            ft.Container(width=20),
                            
                            # Right side - Files content
                            ft.Container(
                                content=self.create_files_list(),
                                expand=True
                            )
                        ], alignment=ft.MainAxisAlignment.START, 
                           vertical_alignment=ft.CrossAxisAlignment.START,
                           expand=True),
                        margin=ft.margin.only(left=15, right=15, top=5, bottom=10),
                        expand=True
                    )
                ], alignment=ft.MainAxisAlignment.START, spacing=0, expand=True), 
                
                # Success notifications stack
                self.create_success_notification(),
                self.create_delete_notification()
            ]),
            alignment=ft.alignment.top_center,
            expand=True
        )