"""
Windows Administrator Access Manager
Handles UAC prompts and elevated privilege access for admin roles
"""

import os
import sys
import subprocess
import ctypes
import getpass
from typing import Tuple, Optional
from pathlib import Path
import tempfile
import json
from datetime import datetime

class WindowsAdminAccessManager:
    """Manages Windows administrator access and UAC prompts"""
    
    def __init__(self):
        self.is_admin = self._is_admin()
        self.current_user = getpass.getuser()
        self.admin_credentials = None
        
    def _is_admin(self) -> bool:
        """Check if current process is running as administrator"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def check_admin_status(self) -> dict:
        """Get comprehensive admin status information"""
        return {
            "is_admin": self.is_admin,
            "current_user": self.current_user,
            "can_elevate": self._can_request_elevation(),
            "process_elevated": self._is_process_elevated(),
            "uac_enabled": self._is_uac_enabled()
        }
    
    def _can_request_elevation(self) -> bool:
        """Check if we can request UAC elevation"""
        try:
            # Check if current user is in administrators group
            import win32security
            import win32api
            import win32con
            
            # Get current user SID
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
                win32security.TokenUser
            )[0]
            
            # Check if user is in administrators group
            admins_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")  # Built-in Administrators
            return win32security.CheckTokenMembership(None, admins_sid)
        except:
            return True  # Assume we can try if we can't check
    
    def _is_process_elevated(self) -> bool:
        """Check if current process has elevated privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except:
            return False
    
    def _is_uac_enabled(self) -> bool:
        """Check if UAC is enabled on the system"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
            value, _ = winreg.QueryValueEx(key, "EnableLUA")
            winreg.CloseKey(key)
            return value == 1
        except:
            return True  # Assume UAC is enabled if we can't check
    
    def request_admin_elevation(self, reason: str = "KMTI requires administrator access for network operations") -> bool:
        """
        Request administrator elevation for the current application
        Returns True if elevation was granted, False otherwise
        """
        if self.is_admin:
            print("[ADMIN_ACCESS] Already running as administrator")
            return True
        
        print(f"[ADMIN_ACCESS] Requesting elevation: {reason}")
        
        try:
            # Get current script path
            if hasattr(sys, '_MEIPASS'):
                # Running as compiled executable
                current_script = sys.executable
            else:
                # Running as Python script
                current_script = sys.argv[0]
                if not os.path.isabs(current_script):
                    current_script = os.path.abspath(current_script)
            
            # Prepare arguments
            args = sys.argv[1:] if len(sys.argv) > 1 else []
            
            # Create temporary file to signal elevation request
            elevation_marker = os.path.join(tempfile.gettempdir(), "kmti_elevation_request.json")
            elevation_data = {
                "requested_time": datetime.now().isoformat(),
                "reason": reason,
                "original_user": self.current_user,
                "process_id": os.getpid()
            }
            
            with open(elevation_marker, 'w') as f:
                json.dump(elevation_data, f, indent=2)
            
            # Use ShellExecute with 'runas' verb to trigger UAC prompt
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable if not hasattr(sys, '_MEIPASS') else current_script,
                " ".join([f'"{arg}"' for arg in args]) if args else "",
                None, 
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecute returns > 32 on success
            if result > 32:
                print("[ADMIN_ACCESS] ✅ Elevation request sent successfully")
                print("[ADMIN_ACCESS] ⚠️ Note: Application will continue with current privileges for fallback processing")
                # Instead of exiting, return False to indicate elevation wasn't obtained
                # but allow the application to continue with reduced functionality
                return False
            else:
                print(f"[ADMIN_ACCESS] ❌ Elevation request failed with code: {result}")
                return False
                
        except Exception as e:
            print(f"[ADMIN_ACCESS] ❌ Error requesting elevation: {e}")
            return False
    
    def check_and_request_elevation_with_dialog(self, page, username: str, user_role: str) -> Tuple[bool, str]:
        """
        Check current elevation status and show dialog if needed
        Returns (has_elevation, message)
        """
        try:
            # Check if already running as admin
            if self.is_admin:
                return True, "Administrator privileges already active"
            
            # Import here to avoid circular imports
            from utils.kmti_elevation_dialog import check_and_request_elevation
            
            return check_and_request_elevation(page, username, user_role)
            
        except ImportError:
            # Fallback to basic elevation request
            print("[ELEVATION] Using fallback elevation method")
            return True, "Elevation dialog not available - proceeding with basic access checking"
        except Exception as e:
            return False, f"Elevation dialog error: {str(e)}"
    
    def create_elevated_script(self, script_content: str, script_name: str = "elevated_operation.py") -> str:
        """Create a temporary script that will run with elevation"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="kmti_elevated_")
            script_path = os.path.join(temp_dir, script_name)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            return script_path
        except Exception as e:
            print(f"[ADMIN_ACCESS] Error creating elevated script: {e}")
            return ""
    
    def run_elevated_script(self, script_path: str, wait: bool = True) -> Tuple[bool, str]:
        """Run a Python script with elevated privileges"""
        try:
            if not os.path.exists(script_path):
                return False, f"Script not found: {script_path}"
            
            # Use ShellExecute with 'runas' to run the script elevated
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                f'"{script_path}"',
                None,
                1  # SW_SHOWNORMAL
            )
            
            if result > 32:
                if wait:
                    # Wait for the process to complete (simplified)
                    import time
                    time.sleep(2)  # Give process time to start
                return True, "Elevated script started successfully"
            else:
                return False, f"Failed to start elevated script: {result}"
                
        except Exception as e:
            return False, f"Error running elevated script: {e}"
    
    def test_and_fix_permissions(self, target_path: str) -> Tuple[bool, str]:
        """Test permissions and attempt to fix them with elevation if needed"""
        print(f"[ADMIN_ACCESS] Testing permissions for: {target_path}")
        
        # Test current access
        try:
            test_dir = os.path.join(target_path, f"permission_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(test_dir, exist_ok=True)
            os.rmdir(test_dir)
            return True, "Permissions are already sufficient"
        except PermissionError:
            pass  # Expected, will try to fix
        except Exception as e:
            return False, f"Unexpected error: {e}"
        
        # If we don't have admin rights, log the issue but don't crash
        if not self.is_admin:
            print("[ADMIN_ACCESS] Insufficient permissions detected")
            print(f"[ADMIN_ACCESS] Cannot fix permissions for: {target_path}")
            print("[ADMIN_ACCESS] Application will continue with fallback file processing")
            return False, "Administrator privileges required but not available - using fallback processing"
        
        # If we have admin rights, try to fix permissions
        try:
            # Use icacls to grant full control to current user
            user = f"{os.environ.get('USERDOMAIN', os.environ.get('COMPUTERNAME', 'WORKGROUP'))}\\{self.current_user}"
            
            cmd = f'icacls "{target_path}" /grant "{user}:(OI)(CI)F" /T'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Permissions granted to {user}"
            else:
                return False, f"Failed to grant permissions: {result.stderr}"
                
        except Exception as e:
            return False, f"Error fixing permissions: {e}"
    
    def cleanup_elevation_markers(self):
        """Clean up temporary elevation marker files"""
        try:
            marker_pattern = os.path.join(tempfile.gettempdir(), "kmti_elevation_*.json")
            import glob
            for marker in glob.glob(marker_pattern):
                try:
                    os.remove(marker)
                except:
                    pass
        except Exception as e:
            print(f"[ADMIN_ACCESS] Warning: Could not clean elevation markers: {e}")


class AdminLoginElevationHandler:
    """Handles elevation specifically during admin login"""
    
    def __init__(self):
        self.access_manager = WindowsAdminAccessManager()
        
    def handle_admin_login(self, username: str, user_role: str, page=None) -> Tuple[bool, str]:
        """
        Handle admin login with elevation check
        Returns (success, message)
        """
        if user_role.upper() == 'TEAM_LEADER':
            print(f"[ELEVATION] Team Leader login: {username} - bypassing Windows admin elevation")
            return True, "Team Leader login successful - no Windows admin elevation required"
        
        # No elevation required for any users - removed Windows admin access requirement
        if user_role.upper() not in ['REQUIRES_ELEVATION_DISABLED']:
            print(f"[ELEVATION] Elevation disabled for {user_role} users - proceeding without Windows admin privileges")
            return True, "No elevation needed - Windows admin access disabled"
        
        # Windows admin elevation is now disabled - proceeding without elevation checks
        print(f"[ELEVATION] Admin login for {username} ({user_role}) - Windows admin elevation disabled")
        print(f"[ELEVATION] Proceeding without Windows administrator privileges")
        
        return True, "Administrator login successful - Windows admin elevation disabled"
    
    def _test_network_access(self, test_path: str) -> Tuple[bool, str]:
        """Test network access without elevation"""
        try:
            test_dir = os.path.join(test_path, f"access_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(test_dir, exist_ok=True)
            os.rmdir(test_dir)  # Clean up
            return True, "Access available"
        except PermissionError:
            return False, "Access denied"
        except Exception as e:
            return False, f"Network error: {str(e)}"
    
    def create_elevation_dialog_script(self, username: str, user_role: str) -> str:
        """Create a script for elevation dialog"""
        script_content = f'''"""
Elevation Dialog Script for KMTI Admin Login
User: {username} ({user_role})
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    title = "KMTI Administrator Access Required"
    message = f"""Administrator access is required for user: {username}

Role: {user_role}

The KMTI application needs administrator privileges to:
• Access network project directories
• Create team and year folders
• Move approved files to final locations

Click OK to continue with elevation, or Cancel to proceed without elevation.

Note: Without elevation, approved files will be staged for manual processing.
"""
    
    result = messagebox.askyesno(title, message)
    
    if result:
        print("ELEVATION_APPROVED")
        exit_code = 0
    else:
        print("ELEVATION_DECLINED") 
        exit_code = 1
    
    root.destroy()
    exit(exit_code)

if __name__ == "__main__":
    main()
'''
        return script_content
    
    def show_elevation_dialog(self, username: str, user_role: str) -> bool:
        """Show elevation dialog to user"""
        try:
            # Create and run elevation dialog script
            script_content = self.create_elevation_dialog_script(username, user_role)
            script_path = self.access_manager.create_elevated_script(script_content, "elevation_dialog.py")
            
            if not script_path:
                return False
            
            # Run the dialog script
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=60)
            
            # Clean up script
            try:
                os.remove(script_path)
                os.rmdir(os.path.dirname(script_path))
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"[ELEVATION] Error showing elevation dialog: {e}")
            return False


# Global instance
_elevation_handler = None

def get_elevation_handler() -> AdminLoginElevationHandler:
    """Get global elevation handler instance"""
    global _elevation_handler
    if _elevation_handler is None:
        _elevation_handler = AdminLoginElevationHandler()
    return _elevation_handler

def check_admin_elevation_on_login(username: str, user_role: str) -> Tuple[bool, str]:
    """
    Check and request admin elevation during login
    Returns (success, message)
    """
    handler = get_elevation_handler()
    return handler.handle_admin_login(username, user_role)
