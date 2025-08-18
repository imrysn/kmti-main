"""
Role-Based Permission Helper

This module provides utilities for managing the 3-role system:
ADMIN, USER, and TEAM_LEADER roles with their respective permissions.
"""

from enum import Enum
from typing import List, Dict, Optional


class UserRole(Enum):
    """Enumeration of user roles in the system."""
    ADMIN = "ADMIN"
    USER = "USER"  
    TEAM_LEADER = "TEAM_LEADER"


class RolePermissions:
    """Defines permissions for each role in the file approval system."""
    
    # Role-based permissions mapping
    PERMISSIONS = {
        UserRole.ADMIN: {
            'can_approve_files': True,
            'can_reject_files': True,
            'can_view_all_teams': True,
            'can_manage_users': True,
            'can_view_statistics': True,
            'can_access_system_settings': True,
            'can_view_activity_logs': True,
            'can_manage_data': True
        },
        UserRole.TEAM_LEADER: {
            'can_approve_files': True,
            'can_reject_files': True,
            'can_view_all_teams': False,  # Only their assigned teams
            'can_manage_users': False,
            'can_view_statistics': True,  # Limited to their teams
            'can_access_system_settings': False,
            'can_view_activity_logs': True,  # Limited to their teams
            'can_manage_data': False
        },
        UserRole.USER: {
            'can_approve_files': False,
            'can_reject_files': False,
            'can_view_all_teams': False,
            'can_manage_users': False,
            'can_view_statistics': False,
            'can_access_system_settings': False,
            'can_view_activity_logs': False,
            'can_manage_data': False
        }
    }


def get_user_role_enum(role_string: str) -> Optional[UserRole]:
    """
    Convert role string to UserRole enum.
    
    Args:
        role_string: Role as string
        
    Returns:
        UserRole enum or None if invalid
    """
    try:
        return UserRole(role_string.upper())
    except (ValueError, AttributeError):
        return None


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if a user role has a specific permission.
    
    Args:
        user_role: User role as string
        permission: Permission to check
        
    Returns:
        bool: True if role has permission
    """
    role_enum = get_user_role_enum(user_role)
    if not role_enum:
        return False
    
    return RolePermissions.PERMISSIONS.get(role_enum, {}).get(permission, False)


def can_approve_files(user_role: str) -> bool:
    """Check if user role can approve files."""
    return has_permission(user_role, 'can_approve_files')


def can_reject_files(user_role: str) -> bool:
    """Check if user role can reject files."""
    return has_permission(user_role, 'can_reject_files')


def can_view_all_teams(user_role: str) -> bool:
    """Check if user role can view all teams."""
    return has_permission(user_role, 'can_view_all_teams')


def can_manage_users(user_role: str) -> bool:
    """Check if user role can manage users."""
    return has_permission(user_role, 'can_manage_users')


def can_view_statistics(user_role: str) -> bool:
    """Check if user role can view statistics."""
    return has_permission(user_role, 'can_view_statistics')


def can_access_system_settings(user_role: str) -> bool:
    """Check if user role can access system settings."""
    return has_permission(user_role, 'can_access_system_settings')


def can_view_activity_logs(user_role: str) -> bool:
    """Check if user role can view activity logs."""
    return has_permission(user_role, 'can_view_activity_logs')


def can_manage_data(user_role: str) -> bool:
    """Check if user role can manage data."""
    return has_permission(user_role, 'can_manage_data')


def is_admin_or_team_leader(user_role: str) -> bool:
    """
    Check if user is ADMIN or TEAM_LEADER (can access file approval panel).
    
    Args:
        user_role: User role as string
        
    Returns:
        bool: True if user can access file approval panel
    """
    role_enum = get_user_role_enum(user_role)
    return role_enum in [UserRole.ADMIN, UserRole.TEAM_LEADER]


def get_accessible_teams(user_role: str, user_teams: List[str], all_teams: List[str]) -> List[str]:
    """
    Get teams accessible to a user based on their role.
    
    Args:
        user_role: User role as string
        user_teams: Teams user is assigned to
        all_teams: All teams in system
        
    Returns:
        List[str]: Accessible teams
    """
    if can_view_all_teams(user_role):
        return all_teams
    else:
        # Team leaders and users can only see their assigned teams
        return user_teams


def get_file_access_level(user_role: str) -> str:
    """
    Get file access level for a user role.
    
    Args:
        user_role: User role as string
        
    Returns:
        str: Access level ('full', 'team_limited', 'none')
    """
    role_enum = get_user_role_enum(user_role)
    
    if role_enum == UserRole.ADMIN:
        return 'full'  # Can see all files
    elif role_enum == UserRole.TEAM_LEADER:
        return 'team_limited'  # Can see files from their teams
    else:
        return 'none'  # Cannot access approval system


def validate_role_access(user_role: str, required_permission: str) -> bool:
    """
    Validate if a user role has required permission for an action.
    
    Args:
        user_role: User role as string
        required_permission: Required permission
        
    Returns:
        bool: True if access is granted
    """
    return has_permission(user_role, required_permission)


def get_role_display_name(user_role: str) -> str:
    """
    Get display-friendly role name.
    
    Args:
        user_role: User role as string
        
    Returns:
        str: Display name
    """
    role_map = {
        'ADMIN': 'Administrator',
        'TEAM_LEADER': 'Team Leader',
        'USER': 'User'
    }
    return role_map.get(user_role.upper(), user_role.title())


def get_all_roles() -> List[str]:
    """Get all available roles in the system."""
    return [role.value for role in UserRole]


class RoleValidator:
    """Helper class for role validation and permission checking."""
    
    def __init__(self):
        self.valid_roles = get_all_roles()
    
    def is_valid_role(self, role: str) -> bool:
        """Check if role is valid."""
        return role.upper() in self.valid_roles
    
    def validate_file_approval_access(self, user_role: str, user_teams: List[str]) -> Dict:
        """
        Validate access to file approval panel.
        
        Args:
            user_role: User role
            user_teams: User teams
            
        Returns:
            Dict: Validation result with access info
        """
        if not self.is_valid_role(user_role):
            return {
                'has_access': False,
                'reason': 'Invalid user role',
                'access_level': 'none'
            }
        
        if not is_admin_or_team_leader(user_role):
            return {
                'has_access': False,
                'reason': 'Insufficient permissions. Only ADMIN and TEAM_LEADER roles can access file approval.',
                'access_level': 'none'
            }
        
        return {
            'has_access': True,
            'reason': 'Access granted',
            'access_level': get_file_access_level(user_role),
            'can_approve': can_approve_files(user_role),
            'can_reject': can_reject_files(user_role),
            'accessible_teams': user_teams if user_role == 'TEAM_LEADER' else 'all'
        }
