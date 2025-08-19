#!/usr/bin/env python3
"""
TL Panel Files Debug Script

Quick script to debug why files aren't showing in TL Panel
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_tl_files():
    """Debug TL panel file visibility"""
    print("🔍 Debugging TL Panel Files...\n")
    
    try:
        from admin.components.team_leader_service import get_team_leader_service
        
        # Test with TL username
        tl_username = "tl"  # The user you created
        tl_service = get_team_leader_service()
        
        print(f"Testing with TL username: {tl_username}")
        print("-" * 50)
        
        # Get team
        team = tl_service.get_user_team(tl_username)
        print(f"Team Leader team: {team}")
        
        # Load queue directly
        queue = tl_service.load_global_queue()
        print(f"Total files in queue: {len(queue)}")
        
        # Show all files and their status/team
        print(f"\n📋 All Files in Queue:")
        for file_id, file_data in queue.items():
            filename = file_data.get('original_filename', 'Unknown')
            status = file_data.get('status', 'Unknown')
            file_team = file_data.get('user_team', 'Unknown')
            user = file_data.get('user_id', 'Unknown')
            
            # Check if this file should be visible to TL
            should_be_visible = (
                (status in ['pending_team_leader', 'pending']) and 
                file_team == team
            )
            
            visibility = "✅ VISIBLE" if should_be_visible else "❌ HIDDEN"
            
            print(f"  • {filename}")
            print(f"    Status: {status}")
            print(f"    Team: {file_team}")  
            print(f"    User: {user}")
            print(f"    {visibility} to TL '{tl_username}'")
            print()
        
        # Test the service function
        print(f"🧪 Testing TL Service Function...")
        pending_files = tl_service.get_pending_files_for_team_leader(tl_username)
        print(f"Files returned by service: {len(pending_files)}")
        
        for file_data in pending_files:
            filename = file_data.get('original_filename', 'Unknown')
            print(f"  • {filename}")
        
        # Get file counts
        print(f"\n📊 File Counts:")
        counts = tl_service.get_file_counts_for_team_leader(tl_username)
        for key, count in counts.items():
            print(f"  {key}: {count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def show_quick_fix():
    """Show quick fix instructions"""
    print(f"\n{'='*60}")
    print("🔧 QUICK FIXES")
    print(f"{'='*60}")
    print("1. RUN MIGRATION (Recommended):")
    print("   python migrate_file_statuses.py")
    print()
    print("2. OR TEST WITH NEW FILES:")
    print("   - Login as a USER")
    print("   - Upload new files") 
    print("   - Submit them for approval")
    print("   - They will have 'pending_team_leader' status")
    print()
    print("3. VERIFY TL SERVICE:")
    print("   - Check debug output above")
    print("   - Files with status 'pending' should now be visible")

if __name__ == "__main__":
    debug_tl_files()
    show_quick_fix()
