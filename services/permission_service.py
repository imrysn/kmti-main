import os
import json
from typing import List, Dict

class PermissionService:
    """Service to handle permissions and team access for file approvals"""
    
    def __init__(self):
        self.users_file = r"\\KMTI-NAS\Shared\data\users.json"
        self.permissions_file = r"\\KMTI-NAS\Shared\data\permissions.json"
    
    def load_users(self) -> Dict:
        """Load users data"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
        return {}
    
    def load_permissions(self) -> Dict:
        """Load permissions configuration"""
        try:
            if os.path.exists(self.permissions_file):
                with open(self.permissions_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading permissions: {e}")
        
        # Return default structure without super_admins
        return {
            "team_admins": {},
            "approval_teams": ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"],
            "settings": {
                "cross_team_approval": False,
                "require_multiple_approvals": False,
                "auto_approve_threshold_mb": 0
            }
        }
    
    def save_permissions(self, permissions: Dict) -> bool:
        """Save permissions configuration"""
        try:
            with open(self.permissions_file, 'w') as f:
                json.dump(permissions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving permissions: {e}")
            return False
    
    def is_super_admin(self, username: str) -> bool:
        """Check if user is an admin (renamed from super_admin)"""
        try:
            users = self.load_users()
            for email, user_data in users.items():
                if user_data.get('username') == username:
                    return user_data.get('role', '').upper() == 'ADMIN'
        except Exception as e:
            print(f"Error checking admin status: {e}")
        return False
    
    def is_team_admin(self, username: str, team: str) -> bool:
        """Check if user is admin for a specific team"""
        try:
            permissions = self.load_permissions()
            team_admins = permissions.get("team_admins", {})
            
            return username in team_admins.get(team, [])
            
        except Exception as e:
            print(f"Error checking team admin status: {e}")
        
        return False
    
    def get_user_teams(self, username: str) -> List[str]:
        """Get teams that a user belongs to"""
        try:
            users = self.load_users()
            
            for email, user_data in users.items():
                if user_data.get('username') == username:
                    teams = user_data.get('team_tags', [])
                    return teams if teams else ["DEFAULT"]
            
        except Exception as e:
            print(f"Error getting user teams: {e}")
        
        return ["DEFAULT"]
    
    def get_reviewable_teams(self, username: str, page=None) -> List[str]:
        """Get teams that a user can review files for."""
        try:
            # Super admin can review all teams
            if self.is_super_admin(username):
                permissions = self.load_permissions()
                return permissions.get(
                    "approval_teams",
                    ["KUSAKABE", "KMTI PJ", "DAIICHI", "WINDSMILE"]
                )

            # Team admins can review their own teams
            reviewable_teams = []
            permissions = self.load_permissions()
            team_admins = permissions.get("team_admins", {})

            for team, admins in team_admins.items():
                if username in admins:
                    reviewable_teams.append(team)

            return reviewable_teams if reviewable_teams else ["DEFAULT"]

        except Exception as e:
            print(f"Error getting reviewable teams: {e}")
            return ["DEFAULT"]
    
    def can_approve_file(self, username: str, file_team: str) -> bool:
        """Check if user can approve files from a specific team"""
        try:
            if self.is_super_admin(username):
                return True
            
            # Get user's reviewable teams
            reviewable_teams = self.get_reviewable_teams(username)
            return file_team in reviewable_teams
        except Exception as e:
            print(f"Error checking file approval permission: {e}")
        return False
    
    def add_super_admin(self, username: str) -> bool:
        """Add user as super admin"""
        try:
            permissions = self.load_permissions()
            
            if "super_admins" not in permissions:
                permissions["super_admins"] = []
            
            if username not in permissions["super_admins"]:
                permissions["super_admins"].append(username)
                return self.save_permissions(permissions)
            
            return True  # Already exists
            
        except Exception as e:
            print(f"Error adding super admin: {e}")
            return False
    
    def remove_super_admin(self, username: str) -> bool:
        """Remove user from super admins"""
        try:
            permissions = self.load_permissions()
            
            if username in permissions.get("super_admins", []):
                permissions["super_admins"].remove(username)
                return self.save_permissions(permissions)
            
            return True  # Already removed
            
        except Exception as e:
            print(f"Error removing super admin: {e}")
            return False
    
    def add_team_admin(self, username: str, team: str) -> bool:
        """Add user as admin for a specific team"""
        try:
            permissions = self.load_permissions()
            
            if "team_admins" not in permissions:
                permissions["team_admins"] = {}
            
            if team not in permissions["team_admins"]:
                permissions["team_admins"][team] = []
            
            if username not in permissions["team_admins"][team]:
                permissions["team_admins"][team].append(username)
                return self.save_permissions(permissions)
            
            return True  # Already exists
            
        except Exception as e:
            print(f"Error adding team admin: {e}")
            return False
    
    def remove_team_admin(self, username: str, team: str) -> bool:
        """Remove user from team admin"""
        try:
            permissions = self.load_permissions()
            
            if team in permissions.get("team_admins", {}):
                if username in permissions["team_admins"][team]:
                    permissions["team_admins"][team].remove(username)
                    
                    # Clean up empty team admin lists
                    if not permissions["team_admins"][team]:
                        del permissions["team_admins"][team]
                    
                    return self.save_permissions(permissions)
            
            return True  # Already removed
            
        except Exception as e:
            print(f"Error removing team admin: {e}")
            return False
    
    def get_all_teams(self) -> List[str]:
        """Get all available teams"""
        try:
            permissions = self.load_permissions()
            return permissions.get("approval_teams", ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"])
        except Exception as e:
            print(f"Error getting all teams: {e}")
            return ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"]
    
    def add_team(self, team: str) -> bool:
        """Add a new team to the approval system"""
        try:
            permissions = self.load_permissions()
            
            if "approval_teams" not in permissions:
                permissions["approval_teams"] = []
            
            if team not in permissions["approval_teams"]:
                permissions["approval_teams"].append(team)
                return self.save_permissions(permissions)
            
            return True  # Already exists
            
        except Exception as e:
            print(f"Error adding team: {e}")
            return False
    
    def remove_team(self, team: str) -> bool:
        """Remove a team from the approval system"""
        try:
            permissions = self.load_permissions()
            
            # Remove from approval teams
            if team in permissions.get("approval_teams", []):
                permissions["approval_teams"].remove(team)
            
            # Remove team admin entries
            if team in permissions.get("team_admins", {}):
                del permissions["team_admins"][team]
            
            return self.save_permissions(permissions)
            
        except Exception as e:
            print(f"Error removing team: {e}")
            return False
    
    def get_permission_summary(self) -> Dict:
        """Get summary of all permissions"""
        try:
            permissions = self.load_permissions()
            users = self.load_users()
            
            summary = {
                "super_admins": permissions.get("super_admins", []),
                "team_admins": permissions.get("team_admins", {}),
                "approval_teams": permissions.get("approval_teams", []),
                "total_users": len(users),
                "admin_users": len([u for u in users.values() if u.get('role', '').upper() == 'ADMIN']),
                "settings": permissions.get("settings", {})
            }
            
            return summary
            
        except Exception as e:
            print(f"Error getting permission summary: {e}")
            return {}
    
    def update_settings(self, settings: Dict) -> bool:
        """Update permission settings"""
        try:
            permissions = self.load_permissions()
            
            if "settings" not in permissions:
                permissions["settings"] = {}
            
            permissions["settings"].update(settings)
            return self.save_permissions(permissions)
            
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
    
    def initialize_default_permissions(self) -> bool:
        """Initialize default permissions if none exist"""
        try:
            if not os.path.exists(self.permissions_file):
                default_permissions = {
                    "super_admins": [],
                    "team_admins": {},
                    "approval_teams": ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"],
                    "settings": {
                        "cross_team_approval": False,
                        "require_multiple_approvals": False,
                        "auto_approve_threshold_mb": 0
                    }
                }
                
                # Add all current ADMIN users as super admins
                users = self.load_users()
                for email, user_data in users.items():
                    if user_data.get('role', '').upper() == 'ADMIN':
                        username = user_data.get('username')
                        if username:
                            default_permissions["super_admins"].append(username)
                
                return self.save_permissions(default_permissions)
            
            return True
            
        except Exception as e:
            print(f"Error initializing default permissions: {e}")
            return False
