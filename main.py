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
                with open(migration_flag, 'w') as f:
                    f.write("Migration completed")
                print("✅ Migration completed")
            else:
                print("⚠️ Migration had warnings")
        
        print("✅ Hybrid backend ready")
        return hybrid_app
        
    except Exception as e:
        print(f"❌ Hybrid backend failed: {e}")
        return None

def restore_session(page: ft.Page):
    """Simple session restore with hybrid backend"""
    
    # Try hybrid session first
    if hybrid_app and hybrid_app.is_session_valid():
        user = hybrid_app.get_current_user()
        if user:
            username = user['username']
            role = user['role']
            
            print(f"✅ Session restored: {username} ({role})")
            
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
            role = session.get("role", "user")
            if username:
                print(f"✅ Legacy session restored: {username}")
                if role.upper() == "ADMIN":
                    admin_panel(page, username)
                    return True
                else:
                    user_panel(page, username)
                    return True
        except Exception as e:
            print(f"[DEBUG] Failed to restore legacy session: {e}")
    
    return False

def main(page: ft.Page):
    """Main application - simple UI"""
    
    # Simple window setup
    page.title = "KMTI Data Management System"
    page.window_icon = "assets/kmti.ico"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height =800
    
    print("🚀 Starting KMTI...")
    
    # Initialize hybrid backend
    global hybrid_app
    hybrid_app = initialize_hybrid_backend()
    
    # Store hybrid app for other modules to use
    if hasattr(page, 'session'):
        try:
            page.session.set("hybrid_app", hybrid_app)
        except:
            # Store in page data as fallback
            page.data = {"hybrid_app": hybrid_app}
    else:
        page.data = {"hybrid_app": hybrid_app}
    
    # Try to restore session, otherwise show login
    if not restore_session(page):
        print("📝 No session - showing login")
        login_view(page)
    
    page.update()

# Helper function for other modules
def get_hybrid_app(page):
    """Get hybrid app instance"""
    global hybrid_app
    if hybrid_app:
        return hybrid_app
    
    # Try to get from page session
    try:
        return page.session.get("hybrid_app")
    except:
        return getattr(page, 'data', {}).get("hybrid_app")

if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.AppView.FLET_APP
    )
