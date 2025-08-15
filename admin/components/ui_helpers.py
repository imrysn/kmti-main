import flet as ft
import json
import os
from typing import List, Dict, Callable, Optional
from datetime import datetime

class UIComponentHelper:

    
    def __init__(self, config, enhanced_auth, enhanced_logger):

        self.config = config
        self.enhanced_auth = enhanced_auth
        self.enhanced_logger = enhanced_logger
    
    def create_header_section(self, admin_teams: List[str], 
                             file_counts: Dict[str, int]) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("File Approval", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Managing approvals for: {', '.join(admin_teams)}", 
                           size=16, color=ft.Colors.GREY_600)
                ]),
                ft.Container(expand=True),
                ft.Row([
                    self._create_stat_card("Pending", str(file_counts['pending']), ft.Colors.ORANGE),
                    ft.Container(width=15),
                    self._create_stat_card("Approved", str(file_counts['approved']), ft.Colors.GREEN),
                    ft.Container(width=15),
                    self._create_stat_card("Rejected", str(file_counts['rejected']), ft.Colors.RED)
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(bottom=10)
        )
    
    def _create_stat_card(self, label: str, value: str, color: str) -> ft.Container:

        card_width = self.config.get_ui_constant('stat_card_width', 110)
        card_height = self.config.get_ui_constant('stat_card_height', 80)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=14, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=card_width,
            height=card_height,
            alignment=ft.alignment.center
        )
    
    def create_filters_section(self, teams: List[str], search_query: str,
                              current_team_filter: str, current_sort: str,
                              on_search_changed: Callable, on_team_filter_changed: Callable,
                              on_sort_changed: Callable, on_refresh: Callable) -> ft.Row:

        try:
            team_options = self._create_team_options(teams)
            
            search_width = self.config.get_ui_constant('search_field_width', 200)
            dropdown_width = self.config.get_ui_constant('dropdown_width', 150)
        except:
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
            search_width = 200
            dropdown_width = 150
        
        return ft.Row([
            ft.TextField(
                hint_text="Search files...",
                width=search_width,
                value=search_query,
                on_change=on_search_changed,
                prefix_icon=ft.Icons.SEARCH
            ),
            ft.Dropdown(
                label="Filter by Team",
                width=dropdown_width,
                options=team_options,
                value=current_team_filter,
                on_change=on_team_filter_changed
            ),
            ft.Dropdown(
                label="Sort by", 
                width=dropdown_width,
                value=current_sort,
                options=[
                    ft.dropdown.Option("submission_date", "Date Submitted"),
                    ft.dropdown.Option("filename", "File Name"),
                    ft.dropdown.Option("user_id", "User"),
                    ft.dropdown.Option("file_size", "File Size")
                ],
                on_change=on_sort_changed
            ),
            ft.Container(expand=True),
            ft.ElevatedButton(
                "Refresh",
                icon=ft.Icons.REFRESH,
                on_click=on_refresh,
                style=self.get_button_style("secondary")
            )
        ])
    
    def _create_team_options(self, teams: List[str]) -> List[ft.dropdown.Option]:

        try:
            team_options = [ft.dropdown.Option("ALL", "All Teams")]
            
            for team in teams:
                if team and isinstance(team, str) and len(team.strip()) > 0:
                    safe_team = team.strip()[:50]  # Limit length
                    safe_team = ''.join(c for c in safe_team if c.isalnum() or c in ' _-.') 
                    if safe_team:
                        team_options.append(ft.dropdown.Option(safe_team, safe_team))
            
            return team_options
        
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error creating team options: {e}")
            return [ft.dropdown.Option("ALL", "All Teams")]
    
    def get_button_style(self, button_type: str) -> ft.ButtonStyle:

        border_radius = self.config.get_ui_constant('button_border_radius', 5)
        
        if button_type == "primary":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        elif button_type == "success":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.GREEN},
                color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        elif button_type == "danger":
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.RED},
                color={ft.ControlState.DEFAULT: ft.Colors.RED,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
        else:  # secondary
            return ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=border_radius)
            )
    
    def create_empty_preview_panel(self) -> List:

        return [
            ft.Text("Select a file to review", size=16, color=ft.Colors.GREY_500, 
                   text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=64, color=ft.Colors.GREY_300),
            ft.Container(height=20),
            ft.Text("Click on any file in the table to view details and approval options", 
                   size=14, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
        ]
    
    def create_error_interface(self, error_msg: str, admin_user: str,
                              on_retry: Callable) -> ft.Container:

        from utils.logger import log_security_event
        
        log_security_event(
            username=admin_user,
            event_type="INTERFACE_ERROR",
            details={"error": error_msg},
            severity="ERROR"
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED),
                ft.Text("File Approval Panel", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Error loading approval system", size=16, color=ft.Colors.RED),
                ft.Text(f"Details: {error_msg}", size=16, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Retry",
                    icon=ft.Icons.REFRESH,
                    on_click=on_retry,
                    style=self.get_button_style("primary")
                ),
                ft.Container(height=20),
                ft.Text("Please check that all required services are running and data files exist.", 
                       size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            expand=True
        )


class TeamLoader:
    """Helper class for loading team information safely."""
    
    def __init__(self, enhanced_auth, enhanced_logger, permission_service):

        self.enhanced_auth = enhanced_auth
        self.enhanced_logger = enhanced_logger
        self.permission_service = permission_service
    
    def load_teams_safely(self, admin_user: str, admin_teams: List[str]) -> List[str]:

        try:
            teams_file = r"\\KMTI-NAS\Shared\data\teams.json"  
            if os.path.exists(teams_file):
                with open(teams_file, 'r', encoding='utf-8') as f:
                    teams_data = json.load(f)
                    
                    if isinstance(teams_data, list):
                        return self._sanitize_team_list(teams_data)
                    elif isinstance(teams_data, dict):
                        return self._sanitize_team_dict(teams_data)
            
            # Fallback to permission service
            reviewable_teams = self.permission_service.get_reviewable_teams(
                admin_user, admin_teams)
            return self._sanitize_team_list(reviewable_teams)
            
        except Exception as e:
            self.enhanced_logger.general_logger.error(f"Error loading teams: {e}")
            return [str(team)[:50] for team in admin_teams]
    
    def _sanitize_team_list(self, teams: List) -> List[str]:

        safe_teams = []
        for team in teams:
            try:
                safe_teams.append(self.enhanced_auth.sanitize_username(team))
            except:
                safe_teams.append(str.upper(team)[:50])
        return safe_teams
    
    def _sanitize_team_dict(self, teams_data: Dict) -> List[str]:

        safe_teams = []
        for team_key, team_data in teams_data.items():
            team_name = team_data.get('name', team_key) if isinstance(team_data, dict) else team_key
            try:
                safe_teams.append(self.enhanced_auth.sanitize_username(team_name))
            except:
                safe_teams.append(str.upper(team_name)[:50])
        return safe_teams


def create_snackbar_helper(page: ft.Page, enhanced_logger):

    def show_snackbar(message: str, color_type: str):

        try:
            color_map = {
                "green": (ft.Colors.GREEN, ft.Icons.CHECK_CIRCLE, "info"),
                "orange": (ft.Colors.ORANGE, ft.Icons.WARNING, "warning"),
                "red": (ft.Colors.RED, ft.Icons.ERROR, "error"),
                "blue": (ft.Colors.BLUE, ft.Icons.INFO, "info")
            }
            
            color, icon, log_level = color_map.get(color_type, 
                                                 (ft.Colors.BLUE, ft.Icons.INFO, "info"))
            
            page.snack_bar = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(icon, color=ft.Colors.WHITE, size=16),
                    ft.Text(message, color=ft.Colors.WHITE)
                ]),
                bgcolor=color,
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
            getattr(enhanced_logger.general_logger, log_level)(f"User notification: {message}")
                
        except Exception as e:
            enhanced_logger.general_logger.error(f"Error showing snackbar: {e}")
    
    return show_snackbar
