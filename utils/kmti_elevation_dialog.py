"""
KMTI UAC Elevation Dialog
Custom UAC-style elevation prompt for KMTI administrator access
"""

import flet as ft
import sys
import os
from typing import Optional, Tuple
import ctypes
import subprocess
import tempfile

class KMTIElevationDialog:
    """Custom elevation dialog for KMTI administrator access"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.elevation_result = None
        self.dialog = None
    
    def show_elevation_dialog(self, username: str, user_role: str, required_access: str) -> bool:
        """
        Show elevation dialog and return user choice
        Returns True if user approves elevation, False otherwise
        """
        self.elevation_result = None
        
        # Create the elevation dialog
        self.dialog = ft.AlertDialog(
            modal=True,
            title=self._create_dialog_title(),
            content=self._create_dialog_content(username, user_role, required_access),
            actions=self._create_dialog_actions(),
            bgcolor=ft.Colors.WHITE,
            title_padding=20,
            content_padding=20,
            actions_padding=ft.padding.only(right=20, bottom=20),
            shape=ft.RoundedRectangleBorder(radius=8)
        )
        
        # Show dialog
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()
        
        # Wait for user response (simplified for this implementation)
        # In a real implementation, this would use async/await patterns
        return self._wait_for_user_response()
    
    def _create_dialog_title(self) -> ft.Row:
        """Create dialog title with UAC shield icon"""
        return ft.Row([
            ft.Icon(ft.Icons.SECURITY, color=ft.Colors.BLUE_600, size=32),
            ft.Container(width=10),
            ft.Column([
                ft.Text("User Account Control", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Do you want to allow this app to make changes to your device?", 
                       size=14, color=ft.Colors.GREY_700)
            ], spacing=0)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
    
    def _create_dialog_content(self, username: str, user_role: str, required_access: str) -> ft.Column:
        """Create dialog content with details"""
        return ft.Column([
            # Program info
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.BUSINESS_CENTER, size=48, color=ft.Colors.BLUE_600),
                    ft.Container(width=15),
                    ft.Column([
                        ft.Text("KMTI Data Management System", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Verified publisher: KMTI Corporation", size=12, color=ft.Colors.GREY_600),
                        ft.Text("File origin: Local computer", size=12, color=ft.Colors.GREY_600)
                    ], spacing=2)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.GREY_50,
                padding=15,
                border_radius=5,
                border=ft.border.all(1, ft.Colors.GREY_300)
            ),
            
            ft.Container(height=15),
            
            # User and access details
            ft.Column([
                ft.Text(f"Administrator: {username} ({user_role})", size=14, weight=ft.FontWeight.W_500),
                ft.Container(height=5),
                ft.Text("Required access:", size=12, weight=ft.FontWeight.BOLD),
                ft.Text(f"• {required_access}", size=12, color=ft.Colors.GREY_700),
                ft.Text(f"• Network directory write permissions", size=12, color=ft.Colors.GREY_700),
                ft.Text(f"• File system folder creation", size=12, color=ft.Colors.GREY_700),
            ], spacing=3),
            
            ft.Container(height=15),
            
            # Warning message
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_600, size=20),
                    ft.Container(width=10),
                    ft.Text("Elevation is required for network file operations.\n"
                           "Without elevation, approved files will be staged for manual processing.",
                           size=12, color=ft.Colors.GREY_700)
                ]),
                bgcolor=ft.Colors.ORANGE_50,
                padding=10,
                border_radius=5,
                border=ft.border.all(1, ft.Colors.ORANGE_200)
            )
        ], spacing=0)
    
    def _create_dialog_actions(self) -> List[ft.Control]:
        """Create dialog action buttons"""
        return [
            ft.TextButton(
                "No",
                on_click=self._on_deny_elevation,
                style=ft.ButtonStyle(
                    color={ft.ControlState.DEFAULT: ft.Colors.GREY_700}
                )
            ),
            ft.ElevatedButton(
                "Yes",
                on_click=self._on_approve_elevation,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_600,
                            ft.ControlState.HOVERED: ft.Colors.BLUE_700},
                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE}
                )
            )
        ]
    
    def _on_approve_elevation(self, e):
        """Handle elevation approval"""
        self.elevation_result = True
        self.dialog.open = False
        self.page.update()
    
    def _on_deny_elevation(self, e):
        """Handle elevation denial"""
        self.elevation_result = False
        self.dialog.open = False
        self.page.update()
    
    def _wait_for_user_response(self) -> bool:
        """Wait for user response (simplified implementation)"""
        # In a real implementation, this would use proper async/await
        # For now, we'll use a simple polling approach
        import time
        timeout = 60  # 60 second timeout
        elapsed = 0
        
        while self.elevation_result is None and elapsed < timeout:
            time.sleep(0.1)
            elapsed += 0.1
            
            # Update page to handle events
            try:
                self.page.update()
            except:
                break
        
        return self.elevation_result or False


class WindowsElevationPrompt:
    """Windows-style elevation prompt for KMTI"""
    
    @staticmethod
    def show_system_elevation_prompt(username: str, user_role: str) -> bool:
        """Show system-level UAC elevation prompt"""
        try:
            # Check if already running as admin
            if ctypes.windll.shell32.IsUserAnAdmin():
                print("[ELEVATION] Already running with administrator privileges")
                return True
            
            # Create UAC elevation request
            program_name = "KMTI Data Management System"
            reason = f"Administrator {username} ({user_role}) requires elevated privileges for network file operations"
            
            # Try to trigger UAC elevation
            result = WindowsElevationPrompt._trigger_uac_elevation(program_name, reason)
            
            return result
            
        except Exception as e:
            print(f"[ELEVATION] Error showing system elevation prompt: {e}")
            return False
    
    @staticmethod
    def _trigger_uac_elevation(program_name: str, reason: str) -> bool:
        """Trigger Windows UAC elevation"""
        try:
            # Get current executable path
            if hasattr(sys, '_MEIPASS'):
                # Running as compiled executable
                executable_path = sys.executable
            else:
                # Running as Python script
                executable_path = sys.executable
                script_args = [os.path.abspath(sys.argv[0])] + sys.argv[1:]
            
            # Create temporary elevation marker
            elevation_marker = os.path.join(tempfile.gettempdir(), f"kmti_elevation_{os.getpid()}.tmp")
            with open(elevation_marker, 'w') as f:
                f.write(f"Elevation requested for {program_name}: {reason}")
            
            # Use ShellExecute with 'runas' verb to trigger UAC
            if hasattr(sys, '_MEIPASS'):
                # For compiled executable
                cmd_args = ""
            else:
                # For Python script
                cmd_args = " ".join([f'"{arg}"' for arg in script_args])
            
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # This triggers the UAC prompt
                executable_path,
                cmd_args,
                None,
                1  # SW_SHOWNORMAL
            )
            
            # Clean up marker
            try:
                os.remove(elevation_marker)
            except:
                pass
            
            # ShellExecute returns > 32 on success
            if result > 32:
                print("[ELEVATION] ✅ UAC elevation request successful")
                # The new elevated process will start, current process should exit
                return True
            else:
                print(f"[ELEVATION] ❌ UAC elevation request failed: {result}")
                return False
                
        except Exception as e:
            print(f"[ELEVATION] Error triggering UAC elevation: {e}")
            return False
    
    @staticmethod
    def create_elevation_info_dialog(page: ft.Page, username: str, user_role: str) -> ft.AlertDialog:
        """Create informational dialog about elevation"""
        return ft.AlertDialog(
            modal=True,
            title=ft.Text("Administrator Privileges Required", size=18, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=64, color=ft.Colors.BLUE_600),
                ft.Container(height=10),
                ft.Text(f"User: {username}", size=14, weight=ft.FontWeight.W_500),
                ft.Text(f"Role: {user_role}", size=14, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                ft.Text("The application needs administrator privileges to:", size=14),
                ft.Text("• Access network project directories", size=12),
                ft.Text("• Create team and year folders", size=12),
                ft.Text("• Move approved files to final locations", size=12),
                ft.Container(height=10),
                ft.Text("Without elevation, approved files will be staged for manual processing.",
                       size=12, color=ft.Colors.ORANGE_700, italic=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            actions=[
                ft.TextButton("Continue without elevation", on_click=lambda e: None),
                ft.ElevatedButton("Request elevation", on_click=lambda e: None)
            ],
            bgcolor=ft.Colors.WHITE
        )


def show_elevation_dialog(page: ft.Page, username: str, user_role: str, required_access: str) -> bool:
    """
    Show KMTI elevation dialog
    Returns True if elevation is approved, False otherwise
    """
    dialog = KMTIElevationDialog(page)
    return dialog.show_elevation_dialog(username, user_role, required_access)


def check_and_request_elevation(page: ft.Page, username: str, user_role: str) -> Tuple[bool, str]:
    """
    Check current elevation status and request if needed
    Returns (has_elevation, message)
    """
    try:
        # Check if already running as admin
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True, "Administrator privileges confirmed"
        
        # Show custom elevation dialog first
        user_approved = show_elevation_dialog(
            page, username, user_role, 
            "Network file operations and directory management"
        )
        
        if not user_approved:
            return False, "User declined administrator elevation"
        
        # If user approved, try system elevation
        system_elevation = WindowsElevationPrompt.show_system_elevation_prompt(username, user_role)
        
        if system_elevation:
            return True, "System elevation successful"
        else:
            return False, "System elevation failed or was cancelled"
            
    except Exception as e:
        return False, f"Elevation check error: {str(e)}"
