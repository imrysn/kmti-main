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
                with open(self.users_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
        return {}

    def load_permissions(self) -> Dict:
        """Load permissions configuration"""
        try:
            if os.path.exists(self.permissions_file):
                with open(self.permissions_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading permissions: {e}")

        # Return default structure (no super admins)
        return {
            "team_admins": {},
            "approval_teams": ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"],
            "settings": {
                "cross_team_approval": False,
                "require_multiple_approvals": False,
                "auto_approve_threshold_mb": 0,
            },
        }

    def save_permissions(self, permissions: Dict) -> bool:
        """Save permissions configuration"""
        try:
            with open(self.permissions_file, "w") as f:
                json.dump(permissions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving permissions: {e}")
            return False

    def is_admin(self, username: str) -> bool:
        """Check if user is ADMIN"""
        try:
            users = self.load_users()
            for _, user_data in users.items():
                if user_data.get("username") == username:
                    return user_data.get("role", "").upper() == "ADMIN"
        except Exception as e:
            print(f"Error checking admin status: {e}")
        return False

    def is_team_leader(self, username: str, team: str) -> bool:
        """Check if user is TEAM LEADER for a specific team"""
        try:
            permissions = self.load_permissions()
            team_admins = permissions.get("team_admins", {})
            return username in team_admins.get(team, [])
        except Exception as e:
            print(f"Error checking team leader status: {e}")
        return False

    def get_user_teams(self, username: str) -> List[str]:
        """Get teams that a user belongs to"""
        try:
            users = self.load_users()
            for _, user_data in users.items():
                if user_data.get("username") == username:
                    teams = user_data.get("team_tags", [])
                    return teams if teams else ["DEFAULT"]
        except Exception as e:
            print(f"Error getting user teams: {e}")
        return ["DEFAULT"]

    def get_reviewable_teams(self, username: str, page=None) -> List[str]:
        """Get teams that a user can review files for."""
        try:
            permissions = self.load_permissions()

            # ADMIN can review all teams
            if self.is_admin(username):
                return permissions.get(
                    "approval_teams",
                    ["KUSAKABE", "KMTI PJ", "DAIICHI", "WINDSMILE"],
                )

            # TEAM LEADER can review only their assigned teams
            team_admins = permissions.get("team_admins", {})
            reviewable_teams = [team for team, leaders in team_admins.items() if username in leaders]

            return reviewable_teams or ["DEFAULT"]

        except Exception as e:
            print(f"Error getting reviewable teams: {e}")
            return ["DEFAULT"]


    def can_approve_file(self, username: str, file_team: str) -> bool:
        """Check if user can approve files from a specific team"""
        try:
            if self.is_admin(username):
                return True
            reviewable_teams = self.get_reviewable_teams(username)
            return file_team in reviewable_teams
        except Exception as e:
            print(f"Error checking file approval permission: {e}")
        return False

    def add_team_leader(self, username: str, team: str) -> bool:
        """Assign a TEAM LEADER for a specific team"""
        try:
            permissions = self.load_permissions()
            team_admins = permissions.setdefault("team_admins", {})
            leaders = team_admins.setdefault(team, [])

            if username not in leaders:
                leaders.append(username)
                return self.save_permissions(permissions)
            return True
        except Exception as e:
            print(f"Error adding team leader: {e}")
            return False

    def remove_team_leader(self, username: str, team: str) -> bool:
        """Remove TEAM LEADER from a team"""
        try:
            permissions = self.load_permissions()
            if team in permissions.get("team_admins", {}):
                if username in permissions["team_admins"][team]:
                    permissions["team_admins"][team].remove(username)
                    if not permissions["team_admins"][team]:
                        del permissions["team_admins"][team]
                    return self.save_permissions(permissions)
            return True
        except Exception as e:
            print(f"Error removing team leader: {e}")
            return False

    def get_all_teams(self) -> List[str]:
        """Get all available teams"""
        try:
            permissions = self.load_permissions()
            return permissions.get(
                "approval_teams",
                ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"],
            )
        except Exception as e:
            print(f"Error getting all teams: {e}")
            return ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"]

    def add_team(self, team: str) -> bool:
        """Add a new team to the approval system"""
        try:
            permissions = self.load_permissions()
            if team not in permissions.get("approval_teams", []):
                permissions["approval_teams"].append(team)
                return self.save_permissions(permissions)
            return True
        except Exception as e:
            print(f"Error adding team: {e}")
            return False

    def remove_team(self, team: str) -> bool:
        """Remove a team from the approval system"""
        try:
            permissions = self.load_permissions()
            if team in permissions.get("approval_teams", []):
                permissions["approval_teams"].remove(team)
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
            return {
                "team_admins": permissions.get("team_admins", {}),
                "approval_teams": permissions.get("approval_teams", []),
                "total_users": len(users),
                "admin_users": len(
                    [u for u in users.values() if u.get("role", "").upper() == "ADMIN"]
                ),
                "team_leaders": sum(
                    len(leaders) for leaders in permissions.get("team_admins", {}).values()
                ),
                "settings": permissions.get("settings", {}),
            }
        except Exception as e:
            print(f"Error getting permission summary: {e}")
            return {}

    def update_settings(self, settings: Dict) -> bool:
        """Update permission settings"""
        try:
            permissions = self.load_permissions()
            permissions.setdefault("settings", {}).update(settings)
            return self.save_permissions(permissions)
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False

    def initialize_default_permissions(self) -> bool:
        """Initialize default permissions if none exist"""
        try:
            if not os.path.exists(self.permissions_file):
                default_permissions = {
                    "team_admins": {},
                    "approval_teams": ["KUSAKABE", "MARKETING", "SALES", "DEFAULT"],
                    "settings": {
                        "cross_team_approval": False,
                        "require_multiple_approvals": False,
                        "auto_approve_threshold_mb": 0,
                    },
                }
                return self.save_permissions(default_permissions)
            return True
        except Exception as e:
            print(f"Error initializing default permissions: {e}")
            return False
