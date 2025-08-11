import flet as ft
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from utils.session_logger import log_activity

class FileApprovalPanel:
    """Enhanced File Approval Panel with hybrid backend support (corrected)"""
    
    def __init__(self, page: ft.Page, username: str, hybrid_app=None):
        self.page = page
        self.username = username
        self.hybrid_app = hybrid_app
        self.user_role = "ADMIN"
        self.user_teams = []
        
        # Get user info and teams
        self._load_user_info()
        
        print(f"📋 FileApprovalPanel: {username} ({self.user_role}) Teams: {self.user_teams}")
    
    def _load_user_info(self):
        """Load user role and team information"""
        if self.hybrid_app:
            try:
                current_user = self.hybrid_app.get_current_user()
                if current_user:
                    self.user_role = current_user['role']
                    self.user_teams = current_user.get('team_tags', [])
                    return
            except Exception as e:
                print(f"⚠️ Error getting hybrid user info: {e}")
        
        # Fallback to legacy
        try:
            users_file = "data/users.json"
            if os.path.exists(users_file):
                with open(users_file, "r") as f:
                    users_data = json.load(f)
                    for email, user_data in users_data.items():
                        if user_data['username'] == self.username:
                            self.user_role = user_data.get('role', 'ADMIN')
                            self.user_teams = user_data.get('team_tags', [])
                            break
        except Exception as e:
            print(f"⚠️ Error loading legacy user info: {e}")
    
    def get_pending_files(self):
        """Get files pending approval from hybrid or legacy system"""
        pending_files = []
        
        if self.hybrid_app:
            try:
                # Get files from hybrid backend (if file_service exists)
                if hasattr(self.hybrid_app, 'file_service'):
                    all_pending = self.hybrid_app.file_service.get_files_for_approval()
                    
                    # Apply team filtering for team leaders
                    if self.user_role == "TEAM_LEADER" and self.user_teams:
                        pending_files = [
                            f for f in all_pending 
                            if any(team in f.get('team_tags', []) for team in self.user_teams)
                        ]
                    else:
                        pending_files = all_pending
                        
                    print(f"📋 Hybrid: Loaded {len(pending_files)} files for approval")
                else:
                    print("⚠️ Hybrid app has no file_service - falling back to legacy")
                    
            except Exception as e:
                print(f"⚠️ Error loading hybrid files: {e}")
        
        # Legacy file loading or fallback
        if not pending_files:
            try:
                approval_queue_path = Path("data/approval_queue")
                if approval_queue_path.exists():
                    for file_path in approval_queue_path.glob("*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                                
                            # Apply team filtering for team leaders
                            if self.user_role == "TEAM_LEADER" and self.user_teams:
                                file_teams = file_data.get('team_tags', [])
                                if any(team in self.user_teams for team in file_teams):
                                    pending_files.append(file_data)
                            else:
                                pending_files.append(file_data)
                                
                        except Exception as fe:
                            print(f"⚠️ Error loading file {file_path}: {fe}")
                            
                print(f"📋 Legacy: Loaded {len(pending_files)} files for approval")
                
            except Exception as e:
                print(f"⚠️ Error loading legacy approval files: {e}")
        
        return pending_files
    
    def approve_file(self, file_id: str, approved: bool, filename: str = ""):
        """Approve or reject a file using hybrid or legacy system"""
        try:
            print(f"📝 {'Approving' if approved else 'Rejecting'} file: {file_id}")
            
            if self.hybrid_app and hasattr(self.hybrid_app, 'file_service'):
                # Use hybrid backend file service
                result = self.hybrid_app.file_service.approve_file(file_id, approved)
                if result:
                    # Log activity using existing session_logger
                    log_activity(
                        self.username, 
                        f"File {'approved' if approved else 'rejected'}: {filename or file_id}"
                    )
                    print(f"✅ Hybrid: File {'approved' if approved else 'rejected'}")
                    return True
                else:
                    return False
            else:
                # Legacy approval system
                approval_file = Path(f"data/approval_queue/{file_id}.json")
                if approval_file.exists():
                    if approved:
                        # Move to approved folder
                        approved_dir = Path("data/approved_files")
                        approved_dir.mkdir(exist_ok=True)
                        approval_file.rename(approved_dir / approval_file.name)
                    else:
                        # Move to rejected folder
                        rejected_dir = Path("data/rejected_files")
                        rejected_dir.mkdir(exist_ok=True)
                        approval_file.rename(rejected_dir / approval_file.name)
                    
                    # Log activity using existing session_logger
                    log_activity(self.username, f"File {'approved' if approved else 'rejected'}: {filename or file_id}")
                    print(f"✅ Legacy: File {'approved' if approved else 'rejected'}")
                    return True
                else:
                    return False
            
        except Exception as e:
            print(f"❌ Error {'approving' if approved else 'rejecting'} file: {e}")
            return False
    
    def get_teams_list(self):
        """Get available teams from hybrid or legacy system"""
        teams = []
        
        if self.hybrid_app:
            try:
                # Try to get teams from hybrid (if team_service exists)
                if hasattr(self.hybrid_app, 'team_service'):
                    teams = self.hybrid_app.team_service.get_teams()
                    return teams
            except Exception as e:
                print(f"⚠️ Error getting hybrid teams: {e}")
        
        # Fallback to legacy teams
        try:
            teams_file = Path("data/teams.json")
            if teams_file.exists():
                with open(teams_file, 'r', encoding='utf-8') as f:
                    teams_data = json.load(f)
                
                if isinstance(teams_data, list):
                    return teams_data
                elif isinstance(teams_data, dict):
                    return list(teams_data.keys())
        except Exception as e:
            print(f"⚠️ Error loading legacy teams: {e}")
        
        # Default teams as fallback
        return ["Minatogumi", "SOLID WORKS", "WINDSMILE", "AGCC Project", "KMTI PJ", "KUSAKABE", "ADMIN", "IT"]
    
    def create_approval_interface(self):
        """Create the file approval interface"""
        
        # Get pending files
        pending_files = self.get_pending_files()
        
        # Header section
        header_content = []
        
        # System status
        system_status = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CLOUD_DONE if self.hybrid_app else ft.Icons.FOLDER, 
                    color=ft.Colors.GREEN if self.hybrid_app else ft.Colors.ORANGE,
                    size=16
                ),
                ft.Text(
                    f"{'NAS Database' if self.hybrid_app else 'Legacy Files'} - {len(pending_files)} pending",
                    size=12,
                    color=ft.Colors.GREEN if self.hybrid_app else ft.Colors.ORANGE,
                    weight=ft.FontWeight.BOLD
                )
            ], spacing=5),
            bgcolor=ft.Colors.GREEN_100 if self.hybrid_app else ft.Colors.ORANGE_100,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=10,
            margin=ft.margin.only(bottom=15)
        )
        header_content.append(system_status)
        
        # Team context for team leaders
        if self.user_role == "TEAM_LEADER":
            team_context = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.GROUP, color=ft.Colors.BLUE, size=20),
                    ft.Text(
                        f"Showing files for your teams: {', '.join(self.user_teams)}", 
                        size=14, 
                        color=ft.Colors.BLUE_700, 
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=10),
                bgcolor=ft.Colors.BLUE_50,
                padding=15,
                border_radius=8,
                margin=ft.margin.only(bottom=20)
            )
            header_content.append(team_context)
        
        # Refresh button
        refresh_button = ft.ElevatedButton(
            "Refresh Files",
            icon=ft.Icons.REFRESH,
            on_click=lambda e: self._refresh_interface(),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                        ft.ControlState.HOVERED: ft.Colors.BLUE_700},
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.WHITE},
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        )
        
        header_row = ft.Row([
            ft.Text("File Approval Panel", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            refresh_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        header_content.insert(0, header_row)
        
        # Files list section
        if not pending_files:
            files_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=64, color=ft.Colors.GREY_400),
                    ft.Text("No files pending approval", size=18, color=ft.Colors.GREY_600),
                    ft.Text("Files will appear here when users upload them", size=14, color=ft.Colors.GREY_500),
                    ft.Text(
                        f"You can approve files for: {', '.join(self.user_teams) if self.user_teams else 'all teams'}", 
                        size=12, color=ft.Colors.GREY_400
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                alignment=ft.alignment.center,
                height=400,
                bgcolor=ft.Colors.GREY_50,
                border_radius=10
            )
        else:
            files_list = []
            
            for i, file_data in enumerate(pending_files):
                file_card = self._create_file_card(file_data, i)
                files_list.append(file_card)
            
            files_content = ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"📋 {len(pending_files)} file(s) pending approval", 
                        size=16, 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.GREY_700
                    ),
                    ft.Divider(),
                    ft.Column(files_list, scroll=ft.ScrollMode.AUTO, spacing=10)
                ], spacing=10),
                height=500,
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.GREY_200)
            )
        
        # Main layout
        main_content = ft.Column([
            *header_content,
            files_content
        ], spacing=15, expand=True)
        
        return main_content
    
    def _create_file_card(self, file_data: dict, index: int):
        """Create a file card for approval"""
        file_id = file_data.get('id', f'unknown_{index}')
        filename = file_data.get('filename', 'Unknown File')
        file_teams = file_data.get('team_tags', [])
        creator = file_data.get('creator_name', file_data.get('created_by', 'Unknown'))
        upload_time = file_data.get('created_at', file_data.get('timestamp', ''))
        description = file_data.get('description', '')
        file_size = file_data.get('file_size', file_data.get('size', 0))
        
        # Format upload time
        time_str = "Unknown time"
        if upload_time:
            try:
                if "T" in upload_time:  # ISO format
                    dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                else:  # Legacy format
                    dt = datetime.strptime(upload_time, "%Y-%m-%d %H:%M:%S")
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = str(upload_time)
        
        # Format file size
        if isinstance(file_size, (int, float)) and file_size > 0:
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
        else:
            size_str = "Unknown size"
        
        # File type icon
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext in ['pdf']:
            file_icon = ft.Icons.PICTURE_AS_PDF
            icon_color = ft.Colors.RED
        elif file_ext in ['xlsx', 'xls']:
            file_icon = ft.Icons.TABLE_CHART
            icon_color = ft.Colors.GREEN
        elif file_ext in ['dwg', 'icd']:
            file_icon = ft.Icons.ARCHITECTURE
            icon_color = ft.Colors.BLUE
        elif file_ext in ['zip', 'rar']:
            file_icon = ft.Icons.FOLDER_ZIP
            icon_color = ft.Colors.ORANGE
        else:
            file_icon = ft.Icons.DESCRIPTION
            icon_color = ft.Colors.GREY
        
        # Approval action
        def handle_approval(approved: bool):
            success = self.approve_file(file_id, approved, filename)
            if success:
                # Show success message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        f"File '{filename}' {'approved' if approved else 'rejected'} successfully!"
                    ),
                    bgcolor=ft.Colors.GREEN if approved else ft.Colors.RED_400,
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.page.update()
                
                # Refresh the interface after a short delay
                import threading
                threading.Timer(1.0, self._refresh_interface).start()
            else:
                # Show error message
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error processing file approval"),
                    bgcolor=ft.Colors.RED,
                    duration=5000
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Create file card
        file_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # File header
                    ft.Row([
                        ft.Icon(file_icon, size=32, color=icon_color),
                        ft.Column([
                            ft.Text(filename, weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(f"Uploaded by: {creator}", size=12, color=ft.Colors.GREY_600),
                            ft.Text(f"Time: {time_str}", size=11, color=ft.Colors.GREY_500)
                        ], expand=True, spacing=2)
                    ], spacing=15),
                    
                    ft.Divider(height=10),
                    
                    # File details
                    ft.Column([
                        ft.Row([
                            ft.Text("Teams:", size=12, color=ft.Colors.GREY_600, width=60),
                            ft.Text(
                                ', '.join(file_teams) if file_teams else 'No teams assigned', 
                                size=13, 
                                color=ft.Colors.BLUE_700 if file_teams else ft.Colors.GREY_500,
                                expand=True
                            )
                        ]),
                        ft.Row([
                            ft.Text("Size:", size=12, color=ft.Colors.GREY_600, width=60),
                            ft.Text(size_str, size=12, color=ft.Colors.GREY_700, expand=True)
                        ]),
                        ft.Row([
                            ft.Text("Description:", size=12, color=ft.Colors.GREY_600, width=60),
                            ft.Text(
                                description if description else 'No description provided', 
                                size=12, 
                                color=ft.Colors.GREY_700 if description else ft.Colors.GREY_500,
                                expand=True
                            )
                        ]) if description or True else ft.Container()
                    ], spacing=8),
                    
                    ft.Divider(height=10),
                    
                    # Action buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "✅ Approve",
                            icon=ft.Icons.CHECK_CIRCLE,
                            on_click=lambda e: handle_approval(True),
                            bgcolor=ft.Colors.GREEN,
                            color="white",
                            style=ft.ButtonStyle(
                                padding=ft.padding.symmetric(horizontal=25, vertical=12)
                            )
                        ),
                        ft.ElevatedButton(
                            "❌ Reject",
                            icon=ft.Icons.CANCEL,
                            on_click=lambda e: handle_approval(False),
                            bgcolor=ft.Colors.RED,
                            color="white",
                            style=ft.ButtonStyle(
                                padding=ft.padding.symmetric(horizontal=25, vertical=12)
                            )
                        )
                    ], spacing=20, alignment=ft.MainAxisAlignment.END)
                ], spacing=15),
                padding=20
            ),
            margin=ft.margin.only(bottom=15),
            elevation=3
        )
        
        return file_card
    
    def _refresh_interface(self):
        """Refresh the file approval interface"""
        try:
            # Re-create the interface by calling the admin panel navigation
            from admin_panel import admin_panel
            admin_panel(self.page, self.username, initial_tab=4)  # File approval tab
        except Exception as e:
            print(f"⚠️ Error refreshing interface: {e}")