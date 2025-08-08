import flet as ft
import json
import os
from datetime import datetime
from pathlib import Path

def admin_panel(page: ft.Page, username: str):
    """Simple admin panel with hybrid backend"""
    
    page.title = f"KMTI Admin - {username}"
    page.clean()
    
    # Get hybrid app
    try:
        from main import get_hybrid_app
        hybrid_app = get_hybrid_app(page)
    except:
        hybrid_app = None
    
    # Get user info
    current_user = None
    user_role = "ADMIN"
    user_teams = []
    
    if hybrid_app:
        current_user = hybrid_app.get_current_user()
        if current_user:
            user_role = current_user['role']
            user_teams = current_user.get('team_tags', [])
    else:
        # Legacy user lookup
        try:
            with open("data/users.json", "r") as f:
                users_data = json.load(f)
                for email, user_data in users_data.items():
                    if user_data['username'] == username:
                        user_role = user_data.get('role', 'ADMIN')
                        user_teams = user_data.get('team_tags', [])
                        break
        except:
            pass
    
    print(f"Admin panel: {username} ({user_role}) Teams: {user_teams}")
    
    # Header with logout
    def logout_clicked(e):
        try:
            if hybrid_app:
                hybrid_app.logout()
            else:
                # Legacy logout
                session_file = "data/session.json"
                if os.path.exists(session_file):
                    os.remove(session_file)
            
            from login_window import login_view
            login_view(page)
            
        except Exception as error:
            print(f"Logout error: {error}")
    
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=28, color=ft.Colors.BLUE),
                ft.Column([
                    ft.Text("KMTI Admin Panel", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Welcome, {username}", size=12, color=ft.Colors.GREY_700)
                ], spacing=0)
            ], spacing=10),
            
            ft.Row([
                # Role badge
                ft.Container(
                    content=ft.Text(user_role, color="white", size=12, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.RED if user_role == "ADMIN" else ft.Colors.BLUE,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=12
                ),
                
                # System status
                ft.Container(
                    content=ft.Text(
                        "NAS Connected" if hybrid_app else "Legacy Mode", 
                        size=11, 
                        color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE
                    ),
                    bgcolor=ft.Colors.GREEN_100 if hybrid_app else ft.Colors.ORANGE_100,
                    padding=6,
                    border_radius=10
                ),
                
                # Logout
                ft.ElevatedButton(
                    text="Logout",
                    icon=ft.Icons.LOGOUT,
                    on_click=logout_clicked,
                    bgcolor=ft.Colors.RED_400,
                    color="white"
                )
            ], spacing=10)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=ft.Colors.BLUE_50,
        padding=15,
        border_radius=8,
        margin=ft.margin.only(bottom=20)
    )
    
    # File Approval Tab
    def create_file_approval_content():
        """Simple file approval interface"""
        
        # Get pending files
        pending_files = []
        
        if hybrid_app:
            try:
                pending_files = hybrid_app.file_service.get_files_for_approval()
            except Exception as e:
                print(f"Error loading files: {e}")
        else:
            # Legacy file loading - simplified
            try:
                approval_queue_path = Path("data/approval_queue")
                if approval_queue_path.exists():
                    for file_path in approval_queue_path.glob("*.json"):
                        with open(file_path, 'r') as f:
                            file_data = json.load(f)
                            
                            # Simple team filtering
                            file_teams = file_data.get('team_tags', [])
                            if user_role == 'ADMIN' or not user_teams or \
                               any(team in user_teams for team in file_teams):
                                pending_files.append(file_data)
            except Exception as e:
                print(f"Legacy file loading error: {e}")
        
        # Show team context for team leaders
        if user_role == "TEAM_LEADER":
            team_text = ft.Container(
                content=ft.Text(
                    f"Your Teams: {', '.join(user_teams)}", 
                    size=14, 
                    color=ft.Colors.BLUE_700,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=ft.Colors.BLUE_50,
                padding=10,
                border_radius=8,
                margin=ft.margin.only(bottom=15)
            )
        else:
            team_text = ft.Container()
        
        # File approval function
        def approve_file(file_id: str, approved: bool):
            try:
                if hybrid_app:
                    hybrid_app.file_service.approve_file(file_id, approved)
                else:
                    # Legacy approval - simplified
                    print(f"Legacy: {'Approve' if approved else 'Reject'} file {file_id}")
                
                # Show success and refresh
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"File {'approved' if approved else 'rejected'}!"),
                    bgcolor=ft.Colors.GREEN if approved else ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
                
                # Refresh the view
                admin_panel(page, username)
                
            except Exception as e:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error: {e}"),
                    bgcolor=ft.Colors.RED
                )
                page.snack_bar.open = True
                page.update()
        
        # File list
        if not pending_files:
            files_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=48, color=ft.Colors.GREY_400),
                    ft.Text("No files pending approval", size=16, color=ft.Colors.GREY_600),
                    ft.Text("Files will appear here when uploaded", size=12, color=ft.Colors.GREY_500)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                height=200
            )
        else:
            files_list = []
            
            for file_data in pending_files:
                file_id = file_data.get('id', 'unknown')
                filename = file_data.get('filename', 'Unknown File')
                file_teams = file_data.get('team_tags', [])
                creator = file_data.get('creator_name', file_data.get('created_by', 'Unknown'))
                
                file_card = ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            # File info
                            ft.Column([
                                ft.Text(filename, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Teams: {', '.join(file_teams) if file_teams else 'No teams'}", size=12),
                                ft.Text(f"By: {creator}", size=11, color=ft.Colors.GREY_600)
                            ], expand=True, spacing=4),
                            
                            # Actions
                            ft.Row([
                                ft.ElevatedButton(
                                    text="Approve",
                                    icon=ft.Icons.CHECK,
                                    on_click=lambda e, fid=file_id: approve_file(fid, True),
                                    bgcolor=ft.Colors.GREEN,
                                    color="white"
                                ),
                                ft.ElevatedButton(
                                    text="Reject", 
                                    icon=ft.Icons.CLOSE,
                                    on_click=lambda e, fid=file_id: approve_file(fid, False),
                                    bgcolor=ft.Colors.RED,
                                    color="white"
                                )
                            ], spacing=8)
                        ]),
                        padding=15
                    ),
                    margin=ft.margin.only(bottom=10)
                )
                files_list.append(file_card)
            
            files_content = ft.Column(files_list, scroll=ft.ScrollMode.AUTO)
        
        return ft.Column([
            team_text,
            files_content
        ])
    
    # User Management (Admin only)
    def create_user_management_content():
        """Simple user management"""
        if user_role != "ADMIN":
            return ft.Text("Access denied - Admin only", color=ft.Colors.RED)
        
        # Get all users
        all_users = []
        
        if hybrid_app:
            try:
                all_users = hybrid_app.user_service.get_users()
            except Exception as e:
                print(f"Error loading users: {e}")
        else:
            # Legacy user loading
            try:
                with open("data/users.json", "r") as f:
                    users_data = json.load(f)
                    for email, user_data in users_data.items():
                        user_info = user_data.copy()
                        user_info['email'] = email
                        all_users.append(user_info)
            except Exception as e:
                print(f"Legacy user loading error: {e}")
        
        # Simple user list
        users_list = []
        
        for user in all_users:
            user_card = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(user.get('fullname', 'Unknown'), weight=ft.FontWeight.BOLD),
                            ft.Text(user.get('username', ''), size=12),
                            ft.Text(f"Role: {user.get('role', 'USER')}", size=11, color=ft.Colors.GREY_600)
                        ], expand=True),
                        
                        ft.Column([
                            ft.Text("Teams:", size=11, color=ft.Colors.GREY_600),
                            ft.Text(', '.join(user.get('team_tags', [])) or 'None', size=12)
                        ])
                    ]),
                    padding=15
                ),
                margin=ft.margin.only(bottom=8)
            )
            users_list.append(user_card)
        
        return ft.Column([
            ft.Text(f"Total Users: {len(all_users)}", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column(users_list, scroll=ft.ScrollMode.AUTO, height=400)
        ])
    
    # Create tabs based on role
    tabs = []
    
    # File Approval (both admin and team leader)
    if user_role in ["ADMIN", "TEAM_LEADER"]:
        tabs.append(ft.Tab(
            text="📋 File Approval",
            content=ft.Container(
                content=create_file_approval_content(),
                padding=15
            )
        ))
    
    # User Management (admin only)
    if user_role == "ADMIN":
        tabs.append(ft.Tab(
            text="👥 Users",
            content=ft.Container(
                content=create_user_management_content(),
                padding=15
            )
        ))
        
        # System Info (admin only)
        system_info = ft.Column([
            ft.Text("System Information", size=16, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Backend: {'Hybrid (SQLite)' if hybrid_app else 'Legacy (JSON)'}"),
            ft.Text(f"Database: {'\\\\KMTI-NAS\\SHARED\\data\\kmti.db' if hybrid_app else 'Local JSON files'}"),
            ft.Text(f"Users: {len(all_users) if 'all_users' in locals() else 'Unknown'}")
        ])
        
        tabs.append(ft.Tab(
            text="⚙️ System",
            content=ft.Container(
                content=system_info,
                padding=15
            )
        ))
    
    # Main content
    main_content = ft.Column([
        header,
        ft.Tabs(
            tabs=tabs,
            selected_index=0
        )
    ], spacing=0)
    
    page.add(main_content)
    page.update()