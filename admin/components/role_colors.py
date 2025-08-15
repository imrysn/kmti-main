"""
Role Color Management System

Provides consistent color coding for the 3-role system:
- Admin: Red (ft.Colors.RED)
- Team Leader: Blue (ft.Colors.BLUE) 
- User: Green (ft.Colors.GREEN)
"""

import flet as ft
from typing import Dict, Optional


class RoleColors:
    """Central role color management."""
    
    # Role color mapping
    COLORS = {
        "ADMIN": ft.Colors.RED,
        "TEAM_LEADER": ft.Colors.BLUE,
        "USER": ft.Colors.GREEN
    }
    
    # Alternative color names for flexibility
    COLORS_ALT = {
        "ADMINISTRATOR": ft.Colors.RED,
        "TL": ft.Colors.BLUE,
        "TEAM LEADER": ft.Colors.BLUE,
        "NORMAL": ft.Colors.GREEN,
        "REGULAR": ft.Colors.GREEN
    }
    
    # Role display names
    DISPLAY_NAMES = {
        "ADMIN": "Administrator",
        "TEAM_LEADER": "Team Leader",
        "USER": "User"
    }


def get_role_color(role: str) -> str:
    """
    Get color for a user role.
    
    Args:
        role: User role string
        
    Returns:
        str: Flet color constant
    """
    if not role:
        return ft.Colors.GREY_500
    
    role_upper = role.upper().strip()
    
    # Check primary colors
    if role_upper in RoleColors.COLORS:
        return RoleColors.COLORS[role_upper]
    
    # Check alternative names
    if role_upper in RoleColors.COLORS_ALT:
        return RoleColors.COLORS_ALT[role_upper]
    
    # Default for unknown roles
    return ft.Colors.GREY_500


def get_role_display_name(role: str) -> str:
    """
    Get display-friendly role name.
    
    Args:
        role: User role string
        
    Returns:
        str: Display name
    """
    if not role:
        return "Unknown"
    
    role_upper = role.upper().strip()
    return RoleColors.DISPLAY_NAMES.get(role_upper, role.title())


def create_role_badge(role: str, size: int = 12) -> ft.Container:
    """
    Create a colored role badge.
    
    Args:
        role: User role string
        size: Text size
        
    Returns:
        ft.Container: Role badge container
    """
    color = get_role_color(role)
    display_name = get_role_display_name(role)
    
    return ft.Container(
        content=ft.Text(
            display_name.upper(),
            color=ft.Colors.WHITE,
            size=size,
            weight=ft.FontWeight.BOLD
        ),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=4,
        alignment=ft.alignment.center
    )


def create_role_text(role: str, size: int = 14, weight: ft.FontWeight = None) -> ft.Text:
    """
    Create colored role text.
    
    Args:
        role: User role string
        size: Text size
        weight: Font weight
        
    Returns:
        ft.Text: Colored role text
    """
    color = get_role_color(role)
    display_name = get_role_display_name(role)
    
    return ft.Text(
        display_name,
        color=color,
        size=size,
        weight=weight or ft.FontWeight.W_500
    )


def create_status_indicator(role: str, is_online: bool = False) -> ft.Row:
    """
    Create role status indicator with online/offline status.
    
    Args:
        role: User role string
        is_online: Whether user is online
        
    Returns:
        ft.Row: Status indicator row
    """
    role_badge = create_role_badge(role, size=10)
    
    status_color = ft.Colors.GREEN if is_online else ft.Colors.GREY_400
    status_text = "Online" if is_online else "Offline"
    
    return ft.Row([
        role_badge,
        ft.Container(width=8),
        ft.Icon(ft.Icons.CIRCLE, color=status_color, size=12),
        ft.Container(width=4),
        ft.Text(status_text, size=12, color=status_color)
    ], alignment=ft.MainAxisAlignment.START, spacing=0)


def get_panel_theme_color(role: str) -> Dict[str, str]:
    """
    Get theme colors for a role's panel.
    
    Args:
        role: User role string
        
    Returns:
        Dict: Theme color mapping
    """
    base_color = get_role_color(role)
    
    return {
        "primary": base_color,
        "primary_light": ft.Colors.with_opacity(0.1, base_color),
        "primary_dark": ft.Colors.with_opacity(0.8, base_color),
        "accent": ft.Colors.WHITE,
        "background": ft.Colors.GREY_100
    }


def create_role_header(username: str, role: str, panel_name: str) -> ft.Container:
    """
    Create role-themed header for panels.
    
    Args:
        username: Username
        role: User role
        panel_name: Name of the panel
        
    Returns:
        ft.Container: Themed header
    """
    theme = get_panel_theme_color(role)
    role_badge = create_role_badge(role, size=14)
    
    return ft.Container(
        content=ft.Row([
            ft.Text(panel_name, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(expand=True),
            ft.Row([
                ft.Text(f"Welcome, {username}", size=16, color=ft.Colors.WHITE),
                ft.Container(width=15),
                role_badge
            ])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=theme["primary"],
        padding=20,
        border_radius=ft.border_radius.only(top_left=8, top_right=8)
    )


def validate_role_color_consistency():
    """Validate that all roles have consistent color mapping."""
    required_roles = ["ADMIN", "TEAM_LEADER", "USER"]
    missing_colors = []
    
    for role in required_roles:
        if role not in RoleColors.COLORS:
            missing_colors.append(role)
    
    if missing_colors:
        raise ValueError(f"Missing color definitions for roles: {missing_colors}")
    
    print("[INFO] Role color system validation passed")


# Validate on import
try:
    validate_role_color_consistency()
except Exception as e:
    print(f"[ERROR] Role color system validation failed: {e}")
