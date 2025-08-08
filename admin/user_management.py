import flet as ft
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class UserManagementService:
    """Comprehensive user management service for KMTI system"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.is_hybrid = page.session.get("hybrid_available", False)
        self.hybrid_app = page.session.get("hybrid_app")
        
    def get_all_users(self) -> List[Dict]:
        """Get all users from the system"""
        if self.is_hybrid and self.hybrid_app:
            try:
                return self.hybrid_app.user_service.get_users()
            except Exception as e:
                print(f"Error getting hybrid users: {e}")
                return []
        else:
            # Legacy user loading
            try:
                users_file = Path("data/users.json")
                if users_file.exists():
                    with open(users_file, 'r') as f:
                        users_data = json.load(f)
                    
                    users_list = []
                    for email, user_data in users_data.items():
                        user_info = user_data.copy()
                        user_info['email'] = email
                        users_list.append(user_info)
                    
                    return users_list
                return []
            except Exception as e:
                print(f"Error loading legacy users: {e}")
                return []
    
    def create_user(self, email: str, username: str, fullname: str, 
                   password: str, role: str = "USER", 
                   team_tags: List[str] = None) -> Dict:
        """Create a new user"""
        try:
            if self.is_hybrid and self.hybrid_app:
                success = self.hybrid_app.user_service.create_user(
                    email, username, fullname, password, role, team_tags or []
                )
                return {"success": success, "message": "User created successfully" if success else "User creation failed"}
            else:
                # Legacy user creation
                users_file = Path("data/users.json")
                users_data = {}
                
                if users_file.exists():
                    with open(users_file, 'r') as f:
                        users_data = json.load(f)
                
                # Check for duplicates
                for existing_email, user_data in users_data.items():
                    if existing_email == email or user_data.get('username') == username:
                        return {"success": False, "message": "User already exists"}
                
                # Create password hash
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Add new user
                users_data[email] = {
                    "fullname": fullname,
                    "username": username,
                    "password": password_hash,
                    "role": role,
                    "team_tags": team_tags or [],
                    "join_date": datetime.now().strftime("%Y-%m-%d"),
                    "runtime_start": datetime.now().isoformat()
                }
                
                # Save to file
                users_file.parent.mkdir(exist_ok=True)
                with open(users_file, 'w') as f:
                    json.dump(users_data, f, indent=4)
                
                return {"success": True, "message": "User created successfully"}
                
        except Exception as e:
            return {"success": False, "message": f"Error creating user: {str(e)}"}
    
    def update_user(self, email: str, updates: Dict) -> Dict:
        """Update user information"""
        try:
            if self.is_hybrid and self.hybrid_app:
                conn = self.hybrid_app.db_manager.get_connection()
                try:
                    # Build update query dynamically
                    update_fields = []
                    values = []
                    
                    for field, value in updates.items():
                        if field == 'team_tags':
                            update_fields.append("team_tags = ?")
                            values.append(json.dumps(value))
                        elif field == 'password':
                            update_fields.append("password_hash = ?")
                            values.append(hashlib.sha256(value.encode()).hexdigest())
                        else:
                            update_fields.append(f"{field} = ?")
                            values.append(value)
                    
                    values.append(email)  # For WHERE clause
                    
                    query = f"UPDATE users SET {', '.join(update_fields)} WHERE email = ?"
                    conn.execute(query, values)
                    conn.commit()
                    
                    return {"success": True, "message": "User updated successfully"}
                finally:
                    conn.close()
            else:
                # Legacy user update
                users_file = Path("data/users.json")
                if not users_file.exists():
                    return {"success": False, "message": "Users file not found"}
                
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                
                if email not in users_data:
                    return {"success": False, "message": "User not found"}
                
                # Update user data
                for field, value in updates.items():
                    if field == 'password':
                        users_data[email][field] = hashlib.sha256(value.encode()).hexdigest()
                    else:
                        users_data[email][field] = value
                
                # Save updated data
                with open(users_file, 'w') as f:
                    json.dump(users_data, f, indent=4)
                
                return {"success": True, "message": "User updated successfully"}
                
        except Exception as e:
            return {"success": False, "message": f"Error updating user: {str(e)}"}
    
    def delete_user(self, email: str) -> Dict:
        """Soft delete user (deactivate)"""
        return self.update_user(email, {"is_active": False})
    
    def activate_user(self, email: str) -> Dict:
        """Activate user"""
        return self.update_user(email, {"is_active": True})
    
    def get_teams(self) -> List[Dict]:
        """Get all available teams"""
        try:
            teams_file = Path("data/teams.json")
            if teams_file.exists():
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                
                teams_list = []
                for team_id, team_info in teams_data.items():
                    team = {
                        "id": team_id,
                        "name": team_info.get("name", team_id),
                        "description": team_info.get("description", "")
                    }
                    teams_list.append(team)
                
                return teams_list
            return [{"id": "IT", "name": "IT Department", "description": "Information Technology"}]
        except Exception as e:
            print(f"Error loading teams: {e}")
            return []

def show_add_user_dialog(page: ft.Page, on_success=None):
    """Show dialog to add a new user"""
    
    user_service = UserManagementService(page)
    available_teams = user_service.get_teams()
    
    # Form fields
    email_field = ft.TextField(
        label="Email Address",
        hint_text="user@example.com",
        width=300,
        keyboard_type=ft.KeyboardType.EMAIL
    )
    
    username_field = ft.TextField(
        label="Username",
        hint_text="john.doe",
        width=300
    )
    
    fullname_field = ft.TextField(
        label="Full Name",
        hint_text="John Doe",
        width=300
    )
    
    password_field = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=300
    )
    
    confirm_password_field = ft.TextField(
        label="Confirm Password",
        password=True,
        width=300
    )
    
    role_dropdown = ft.Dropdown(
        label="Role",
        width=300,
        value="USER",
        options=[
            ft.dropdown.Option("USER", "Regular User"),
            ft.dropdown.Option("TEAM_LEADER", "Team Leader"),
            ft.dropdown.Option("ADMIN", "Administrator")
        ]
    )
    
    # Team selection
    team_checkboxes = []
    for team in available_teams:
        checkbox = ft.Checkbox(
            label=f"{team['name']} - {team['description']}",
            value=False
        )
        checkbox.data = team['id']
        team_checkboxes.append(checkbox)
    
    teams_container = ft.Column([
        ft.Text("Assign Teams:", weight=ft.FontWeight.BOLD),
        *team_checkboxes
    ], spacing=5)
    
    status_text = ft.Text("", color=ft.Colors.ERROR)
    
    def validate_form():
        """Validate form inputs"""
        errors = []
        
        # Email validation
        if not email_field.value or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_field.value):
            errors.append("Valid email is required")
        
        # Username validation
        if not username_field.value or len(username_field.value) < 3:
            errors.append("Username must be at least 3 characters")
        
        # Full name validation
        if not fullname_field.value or len(fullname_field.value) < 2:
            errors.append("Full name is required")
        
        # Password validation
        if not password_field.value or len(password_field.value) < 6:
            errors.append("Password must be at least 6 characters")
        
        if password_field.value != confirm_password_field.value:
            errors.append("Passwords do not match")
        
        return errors
    
    def create_user_clicked(e):
        """Handle create user button click"""
        errors = validate_form()
        if errors:
            status_text.value = "; ".join(errors)
            status_text.color = ft.Colors.ERROR
            page.update()
            return
        
        # Get selected teams
        selected_teams = [cb.data for cb in team_checkboxes if cb.value]
        
        # Create user
        result = user_service.create_user(
            email=email_field.value,
            username=username_field.value,
            fullname=fullname_field.value,
            password=password_field.value,
            role=role_dropdown.value,
            team_tags=selected_teams
        )
        
        if result["success"]:
            status_text.value = result["message"]
            status_text.color = ft.Colors.GREEN
            
            # Call success callback
            if on_success:
                on_success()
            
            # Close dialog after short delay
            import time
            time.sleep(1)
            dialog.open = False
            page.update()
        else:
            status_text.value = result["message"]
            status_text.color = ft.Colors.ERROR
        
        page.update()
    
    def cancel_clicked(e):
        dialog.open = False
        page.update()
    
    # Create dialog
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add New User"),
        content=ft.Container(
            content=ft.Column([
                email_field,
                username_field,
                fullname_field,
                password_field,
                confirm_password_field,
                role_dropdown,
                ft.Divider(),
                teams_container,
                status_text
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            width=400,
            height=500
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel_clicked),
            ft.ElevatedButton(
                "Create User",
                icon=ft.Icons.PERSON_ADD,
                on_click=create_user_clicked
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()

def show_edit_user_dialog(page: ft.Page, user: Dict, on_success=None):
    """Show dialog to edit user information"""
    
    user_service = UserManagementService(page)
    available_teams = user_service.get_teams()
    
    # Pre-fill form with user data
    email_field = ft.TextField(
        label="Email Address",
        value=user.get('email', ''),
        width=300,
        disabled=True  # Email shouldn't be changed
    )
    
    username_field = ft.TextField(
        label="Username",
        value=user.get('username', ''),
        width=300,
        disabled=True  # Username shouldn't be changed
    )
    
    fullname_field = ft.TextField(
        label="Full Name",
        value=user.get('fullname', ''),
        width=300
    )
    
    role_dropdown = ft.Dropdown(
        label="Role",
        width=300,
        value=user.get('role', 'USER'),
        options=[
            ft.dropdown.Option("USER", "Regular User"),
            ft.dropdown.Option("TEAM_LEADER", "Team Leader"),
            ft.dropdown.Option("ADMIN", "Administrator")
        ]
    )
    
    # Team selection with pre-selected values
    user_teams = set(user.get('team_tags', []))
    team_checkboxes = []
    for team in available_teams:
        checkbox = ft.Checkbox(
            label=f"{team['name']} - {team['description']}",
            value=team['id'] in user_teams
        )
        checkbox.data = team['id']
        team_checkboxes.append(checkbox)
    
    teams_container = ft.Column([
        ft.Text("Assigned Teams:", weight=ft.FontWeight.BOLD),
        *team_checkboxes
    ], spacing=5)
    
    # Password change section
    change_password_checkbox = ft.Checkbox(
        label="Change Password",
        value=False
    )
    
    new_password_field = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=300,
        visible=False
    )
    
    confirm_password_field = ft.TextField(
        label="Confirm New Password",
        password=True,
        width=300,
        visible=False
    )
    
    def password_change_toggled(e):
        show_password_fields = change_password_checkbox.value
        new_password_field.visible = show_password_fields
        confirm_password_field.visible = show_password_fields
        page.update()
    
    change_password_checkbox.on_change = password_change_toggled
    
    status_text = ft.Text("", color=ft.Colors.ERROR)
    
    def validate_form():
        """Validate form inputs"""
        errors = []
        
        # Full name validation
        if not fullname_field.value or len(fullname_field.value) < 2:
            errors.append("Full name is required")
        
        # Password validation (if changing)
        if change_password_checkbox.value:
            if not new_password_field.value or len(new_password_field.value) < 6:
                errors.append("New password must be at least 6 characters")
            
            if new_password_field.value != confirm_password_field.value:
                errors.append("New passwords do not match")
        
        return errors
    
    def update_user_clicked(e):
        """Handle update user button click"""
        errors = validate_form()
        if errors:
            status_text.value = "; ".join(errors)
            status_text.color = ft.Colors.ERROR
            page.update()
            return
        
        # Prepare updates
        updates = {
            "fullname": fullname_field.value,
            "role": role_dropdown.value,
            "team_tags": [cb.data for cb in team_checkboxes if cb.value]
        }
        
        # Add password if changing
        if change_password_checkbox.value:
            updates["password"] = new_password_field.value
        
        # Update user
        result = user_service.update_user(user['email'], updates)
        
        if result["success"]:
            status_text.value = result["message"]
            status_text.color = ft.Colors.GREEN
            
            # Call success callback
            if on_success:
                on_success()
            
            # Close dialog after short delay
            import time
            time.sleep(1)
            dialog.open = False
            page.update()
        else:
            status_text.value = result["message"]
            status_text.color = ft.Colors.ERROR
        
        page.update()
    
    def cancel_clicked(e):
        dialog.open = False
        page.update()
    
    # Create dialog
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"Edit User: {user.get('fullname', 'Unknown')}"),
        content=ft.Container(
            content=ft.Column([
                email_field,
                username_field,
                fullname_field,
                role_dropdown,
                ft.Divider(),
                teams_container,
                ft.Divider(),
                change_password_checkbox,
                new_password_field,
                confirm_password_field,
                status_text
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            width=400,
            height=600
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel_clicked),
            ft.ElevatedButton(
                "Update User",
                icon=ft.Icons.SAVE,
                on_click=update_user_clicked
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()

def show_user_details_dialog(page: ft.Page, user: Dict):
    """Show detailed user information dialog"""
    
    # Create user info display
    user_info = ft.Column([
        ft.Row([
            ft.Text("Email:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(user.get('email', 'N/A'))
        ]),
        ft.Row([
            ft.Text("Username:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(user.get('username', 'N/A'))
        ]),
        ft.Row([
            ft.Text("Full Name:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(user.get('fullname', 'N/A'))
        ]),
        ft.Row([
            ft.Text("Role:", weight=ft.FontWeight.BOLD, width=120),
            ft.Container(
                content=ft.Text(user.get('role', 'USER'), color="white"),
                bgcolor=get_role_color(user.get('role', 'USER')),
                padding=ft.padding.symmetric(horizontal=10, vertical=2),
                border_radius=10
            )
        ]),
        ft.Row([
            ft.Text("Teams:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(', '.join(user.get('team_tags', [])) or 'No teams assigned')
        ]),
        ft.Row([
            ft.Text("Join Date:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(user.get('join_date', 'N/A'))
        ]),
        ft.Row([
            ft.Text("Last Login:", weight=ft.FontWeight.BOLD, width=120),
            ft.Text(format_datetime(user.get('last_login', user.get('runtime_start', 'Never'))))
        ]),
        ft.Row([
            ft.Text("Status:", weight=ft.FontWeight.BOLD, width=120),
            ft.Container(
                content=ft.Text(
                    "Active" if user.get('is_active', True) else "Inactive",
                    color="white"
                ),
                bgcolor=ft.Colors.GREEN if user.get('is_active', True) else ft.Colors.RED,
                padding=ft.padding.symmetric(horizontal=10, vertical=2),
                border_radius=10
            )
        ])
    ], spacing=10)
    
    def close_clicked(e):
        dialog.open = False
        page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"User Details: {user.get('fullname', 'Unknown')}"),
        content=ft.Container(
            content=user_info,
            width=400,
            padding=20
        ),
        actions=[
            ft.TextButton("Close", on_click=close_clicked)
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()

def show_delete_user_confirmation(page: ft.Page, user: Dict, on_confirm=None):
    """Show confirmation dialog for user deletion/deactivation"""
    
    def confirm_clicked(e):
        user_service = UserManagementService(page)
        result = user_service.delete_user(user['email'])
        
        if result["success"]:
            if on_confirm:
                on_confirm()
        
        dialog.open = False
        page.update()
        
        # Show result message
        page.snack_bar = ft.SnackBar(
            content=ft.Text(result["message"]),
            bgcolor=ft.Colors.GREEN if result["success"] else ft.Colors.RED
        )
        page.snack_bar.open = True
        page.update()
    
    def cancel_clicked(e):
        dialog.open = False
        page.update()
    
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirm User Deactivation"),
        content=ft.Text(
            f"Are you sure you want to deactivate user '{user.get('fullname', 'Unknown')}'?\n\n"
            f"This will prevent them from logging in, but their data will be preserved."
        ),
        actions=[
            ft.TextButton("Cancel", on_click=cancel_clicked),
            ft.ElevatedButton(
                "Deactivate",
                icon=ft.Icons.PERSON_OFF,
                on_click=confirm_clicked,
                bgcolor=ft.Colors.RED,
                color="white"
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    
    page.dialog = dialog
    dialog.open = True
    page.update()

# Helper functions
def get_role_color(role: str) -> str:
    """Get color for user role badge"""
    role_Colors = {
        "ADMIN": ft.Colors.RED,
        "TEAM_LEADER": ft.Colors.BLUE,
        "USER": ft.Colors.GREEN
    }
    return role_Colors.get(role, ft.Colors.GREY)

def format_datetime(datetime_str: str) -> str:
    """Format datetime string for display"""
    if not datetime_str or datetime_str == "Never":
        return "Never"
    
    try:
        if 'T' in datetime_str:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(datetime_str, '%Y-%m-%d')
        
        # Show relative time if recent
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                return f"{diff.seconds // 60} minutes ago"
            else:
                return f"{diff.seconds // 3600} hours ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime('%m/%d/%Y')
            
    except:
        return datetime_str[:10] if len(datetime_str) >= 10 else datetime_str

# Export main functions for use in other modules
__all__ = [
    'UserManagementService',
    'show_add_user_dialog',
    'show_edit_user_dialog', 
    'show_user_details_dialog',
    'show_delete_user_confirmation'
]