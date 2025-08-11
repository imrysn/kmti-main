import flet as ft
import json
import os
from login_window import login_view
from admin_panel import admin_panel
from user.user_panel import user_panel

# Import hybrid backend (but keep simple UI)
try:
    from core.hybrid_manager import KMTIHybridApp
    HYBRID_AVAILABLE = True
    print("✅ Hybrid backend loaded")
except ImportError:
    HYBRID_AVAILABLE = False
    print("❌ Hybrid backend not available - using legacy mode")

# Global hybrid app instance
hybrid_app = None

def initialize_hybrid_backend():
    """Initialize hybrid backend with NAS database"""
    global hybrid_app
    
    if not HYBRID_AVAILABLE:
        return None
    
    try:
        # Database on NAS at \\KMTI-NAS\SHARED\data\
        nas_db_path = "\\\\KMTI-NAS\\SHARED\\data\\kmti.db"
        
        print(f"🔄 Initializing database at: {nas_db_path}")
        hybrid_app = KMTIHybridApp(nas_db_path)
        
        # Auto-migrate if first run
        migration_flag = "\\\\KMTI-NAS\\SHARED\\data\\.migration_done"
        if not os.path.exists(migration_flag):
            print("🔄 First run - migrating data...")
            success = hybrid_app.migrate_existing_data()
            if success:
                # Create migration flag
                os.makedirs(os.path.dirname(migration_flag), exist_ok=True)
                with open(migration_flag, 'w') as f:
                    f.write(f"Migration completed at {os.getcwd()}")
                print("✅ Migration completed")
            else:
                print("⚠️ Migration had warnings")
        
        print("✅ Hybrid backend ready")
        return hybrid_app
        
    except Exception as e:
        print(f"❌ Hybrid backend failed: {e}")
        return None

def restore_session(page: ft.Page):
    """Enhanced session restore with hybrid backend priority (fixed authentication)"""
    
    # Try hybrid session first
    if hybrid_app and hybrid_app.is_session_valid():
        user = hybrid_app.get_current_user()
        if user:
            username = user['username']
            role = user['role']
            
            print(f"✅ Hybrid session restored: {username} ({role})")
            
            # Route based on role
            if role.upper() in ["ADMIN", "TEAM_LEADER"]:
                admin_panel(page, username)
                return True
            else:
                user_panel(page, username)
                return True
    
    # Fallback to legacy session
    session_file = "data/session.json"
    if os.path.exists(session_file):
        try:
            with open(session_file, "r") as f:
                session = json.load(f)
            username = session.get("username")
            role = session.get("role", "USER")
            
            if username:
                print(f"✅ Legacy session restored: {username} ({role})")
                
                # If hybrid is available, try to find this user (without authenticate_user)
                if hybrid_app:
                    try:
                        # Check if user exists in hybrid system
                        if hasattr(hybrid_app, 'user_service'):
                            users = hybrid_app.user_service.get_users()
                            for user in users:
                                if user.get('username') == username:
                                    print(f"🔄 Found user in hybrid system: {username}")
                                    break
                        else:
                            print("⚠️ Hybrid user_service not available")
                    except Exception as e:
                        print(f"⚠️ Could not check hybrid user: {e}")
                
                # Route based on role
                if role.upper() in ["ADMIN", "TEAM_LEADER"]:
                    admin_panel(page, username)
                    return True
                else:
                    user_panel(page, username)
                    return True
                    
        except Exception as e:
            print(f"[DEBUG] Failed to restore legacy session: {e}")
    
    return False

def main(page: ft.Page):
    """Main application with hybrid backend integration"""
    
    # Enhanced window setup
    page.title = "KMTI Data Management System"
    page.window_icon = "assets/kmti.ico"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    
    print("🚀 Starting KMTI Data Management System...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Initialize hybrid backend
    global hybrid_app
    hybrid_app = initialize_hybrid_backend()
    
    # Store hybrid app reference for other modules
    # Multiple storage methods for compatibility
    if hasattr(page, 'session'):
        try:
            page.session.set("hybrid_app", hybrid_app)
            page.session.set("current_user", "admin")  # Set default current user
            print("📦 Hybrid app stored in page.session")
        except Exception as e:
            print(f"⚠️ Could not store in session: {e}")
            # Fallback to page data
            if not hasattr(page, 'data'):
                page.data = {}
            page.data["hybrid_app"] = hybrid_app
            page.data["current_user"] = "admin"
            print("📦 Hybrid app stored in page.data")
    else:
        if not hasattr(page, 'data'):
            page.data = {}
        page.data["hybrid_app"] = hybrid_app
        page.data["current_user"] = "admin"
        print("📦 Hybrid app stored in page.data")
    
    # Show system status
    status_msg = "🔗 NAS Database Connected" if hybrid_app else "📁 Legacy Mode (JSON files)"
    print(f"💾 System Status: {status_msg}")
    
    # Try to restore session, otherwise show login
    if not restore_session(page):
        print("📝 No active session - showing login")
        login_view(page)
    
    page.update()

def get_hybrid_app(page):
    """Get hybrid app instance - multiple fallback methods"""
    global hybrid_app
    
    # Try global first
    if hybrid_app:
        return hybrid_app
    
    # Try page session
    if hasattr(page, 'session'):
        try:
            app = page.session.get("hybrid_app")
            if app:
                return app
        except Exception:
            pass
    
    # Try page data
    try:
        if hasattr(page, 'data') and page.data:
            app = page.data.get("hybrid_app")
            if app:
                return app
    except Exception:
        pass
    
    print("⚠️ Could not retrieve hybrid app instance")
    return None

def cleanup_legacy_session():
    """Clean up legacy session file"""
    try:
        session_file = "data/session.json"
        if os.path.exists(session_file):
            os.remove(session_file)
            print("🗑️ Legacy session cleaned up")
    except Exception as e:
        print(f"⚠️ Could not clean legacy session: {e}")

def save_legacy_session(username: str, role: str):
    """Save legacy session as backup"""
    try:
        os.makedirs("data", exist_ok=True)
        session_data = {
            "username": username,
            "role": role,
            "timestamp": str(os.time.time())
        }
        with open("data/session.json", "w") as f:
            json.dump(session_data, f)
        print(f"💾 Legacy session saved for {username}")
    except Exception as e:
        print(f"⚠️ Could not save legacy session: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🏢 KMTI Data Management System")
    print("=" * 50)
    
    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.AppView.FLET_APP
    )