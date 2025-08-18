"""
Debug script to verify file approval workflow
Checks paths, data consistency, and service coordination
"""

import os
import json
from datetime import datetime
from utils.path_config import DATA_PATHS
from services.file_movement_service import get_file_movement_service
from admin.components.team_leader_service import get_team_leader_service

def check_network_connectivity():
    """Check if network directories are accessible"""
    print("=== NETWORK CONNECTIVITY CHECK ===")
    
    network_available = DATA_PATHS.is_network_available()
    print(f"Network base directory accessible: {network_available}")
    print(f"Network base: {DATA_PATHS.NETWORK_BASE}")
    
    if network_available:
        print("✅ Network connectivity OK")
        
        # Check specific directories
        dirs_to_check = [
            DATA_PATHS.approvals_dir,
            DATA_PATHS.uploads_dir,
            DATA_PATHS.user_approvals_dir,
            DATA_PATHS.users_file
        ]
        
        for dir_path in dirs_to_check:
            exists = os.path.exists(dir_path)
            print(f"  {dir_path}: {'✅' if exists else '❌'}")
    else:
        print("❌ Network connectivity FAILED")
        print("  Check network connection and permissions")
    
    return network_available

def check_approval_queue():
    """Check the approval queue file"""
    print("\n=== APPROVAL QUEUE CHECK ===")
    
    queue_file = DATA_PATHS.file_approvals_file
    print(f"Queue file path: {queue_file}")
    
    if os.path.exists(queue_file):
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
            
            print(f"✅ Queue file exists with {len(queue)} entries")
            
            # Analyze queue contents
            status_counts = {}
            team_counts = {}
            
            for file_id, file_data in queue.items():
                status = file_data.get('status', 'unknown')
                team = file_data.get('user_team', 'unknown')
                
                status_counts[status] = status_counts.get(status, 0) + 1
                team_counts[team] = team_counts.get(team, 0) + 1
            
            print("  Status breakdown:")
            for status, count in status_counts.items():
                print(f"    {status}: {count}")
            
            print("  Team breakdown:")
            for team, count in team_counts.items():
                print(f"    {team}: {count}")
            
            # Show recent files
            print("  Recent submissions (last 3):")
            recent_files = sorted(queue.values(), 
                                key=lambda x: x.get('submission_date', ''), 
                                reverse=True)[:3]
            
            for i, file_data in enumerate(recent_files, 1):
                print(f"    {i}. {file_data.get('original_filename', 'Unknown')} ")
                print(f"       Status: {file_data.get('status', 'unknown')}")
                print(f"       User: {file_data.get('user_id', 'unknown')}")
                print(f"       Team: {file_data.get('user_team', 'unknown')}")
                print(f"       Submitted: {file_data.get('submission_date', 'unknown')}")
                
        except Exception as e:
            print(f"❌ Error reading queue file: {e}")
    else:
        print("❌ Queue file does not exist")
        print("  Creating empty queue file...")
        try:
            os.makedirs(os.path.dirname(queue_file), exist_ok=True)
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
            print("✅ Created empty queue file")
        except Exception as e:
            print(f"❌ Failed to create queue file: {e}")

def check_team_leader_service():
    """Test team leader service functionality"""
    print("\n=== TEAM LEADER SERVICE CHECK ===")
    
    try:
        tl_service = get_team_leader_service()
        print("✅ Team leader service initialized")
        
        # Test with a known user (you'll need to replace with actual username)
        test_username = input("Enter a team leader username to test (or press Enter to skip): ").strip()
        
        if test_username:
            user_team = tl_service.get_user_team(test_username)
            print(f"  User '{test_username}' team: {user_team}")
            
            pending_files = tl_service.get_pending_files_for_team_leader(test_username)
            print(f"  Pending files for TL: {len(pending_files)}")
            
            if pending_files:
                print("  Recent pending files:")
                for file_data in pending_files[:3]:
                    print(f"    - {file_data.get('original_filename', 'Unknown')}")
                    print(f"      Status: {file_data.get('status', 'unknown')}")
                    print(f"      User: {file_data.get('user_id', 'unknown')}")
            
            file_counts = tl_service.get_file_counts_for_team_leader(test_username)
            print(f"  File counts: {file_counts}")
        
    except Exception as e:
        print(f"❌ Team leader service error: {e}")

def check_file_movement_service():
    """Test file movement service"""
    print("\n=== FILE MOVEMENT SERVICE CHECK ===")
    
    try:
        movement_service = get_file_movement_service()
        print("✅ File movement service initialized")
        
        project_base = movement_service.project_base
        print(f"Project base directory: {project_base}")
        
        if os.path.exists(project_base):
            print("✅ Project base directory accessible")
            
            # Get team directories
            teams = movement_service.get_team_directories()
            print(f"  Available team directories: {teams}")
            
            # Test directory creation
            test_team = "TEST_TEAM"
            success, path = movement_service.ensure_project_directory(test_team)
            if success:
                print(f"✅ Successfully created/verified test directory: {path}")
                # Clean up test directory
                try:
                    os.rmdir(path)  # Remove if empty
                    os.rmdir(os.path.dirname(path))  # Remove team dir if empty
                    print("  Cleaned up test directory")
                except:
                    pass
            else:
                print(f"❌ Failed to create test directory: {path}")
        else:
            print(f"❌ Project base directory not accessible: {project_base}")
            
    except Exception as e:
        print(f"❌ File movement service error: {e}")

def check_user_uploads():
    """Check user upload directories"""
    print("\n=== USER UPLOADS CHECK ===")
    
    uploads_dir = DATA_PATHS.uploads_dir
    print(f"Uploads directory: {uploads_dir}")
    
    if os.path.exists(uploads_dir):
        print("✅ Uploads directory exists")
        
        try:
            users = os.listdir(uploads_dir)
            print(f"  User directories: {len(users)}")
            
            for user in users[:5]:  # Show first 5 users
                user_dir = os.path.join(uploads_dir, user)
                if os.path.isdir(user_dir):
                    try:
                        files = [f for f in os.listdir(user_dir) 
                                if os.path.isfile(os.path.join(user_dir, f)) 
                                and not f.startswith('.') 
                                and f not in ['files_metadata.json', 'profile.json']]
                        print(f"    {user}: {len(files)} files")
                    except Exception as e:
                        print(f"    {user}: Error reading directory - {e}")
                        
        except Exception as e:
            print(f"❌ Error reading uploads directory: {e}")
    else:
        print("❌ Uploads directory does not exist")

def create_test_data():
    """Create test data for debugging"""
    print("\n=== CREATE TEST DATA ===")
    
    create_test = input("Create test submission? (y/N): ").strip().lower()
    if create_test != 'y':
        return
    
    # This would create test data - implementation depends on your needs
    print("Test data creation not implemented in this debug version")
    print("To create test data:")
    print("1. Login as a user")
    print("2. Upload a file")
    print("3. Submit it for approval")
    print("4. Check this debug script again")

def main():
    """Main debug function"""
    print("KMTI File Approval System - Debug & Verification Script")
    print("=" * 60)
    
    # Check network connectivity first
    network_ok = check_network_connectivity()
    
    if not network_ok:
        print("\n❌ CRITICAL: Network connectivity failed")
        print("Please check network connection before proceeding")
        return
    
    # Check each component
    check_approval_queue()
    check_team_leader_service()
    check_file_movement_service()
    check_user_uploads()
    
    # Optional test data creation
    create_test_data()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("\nIf issues persist:")
    print("1. Check network connectivity and permissions")
    print("2. Verify users.json exists and has correct team_tags")
    print("3. Check that services are using network paths consistently")
    print("4. Test the workflow: User upload -> TL approval -> Admin approval")

if __name__ == "__main__":
    main()
