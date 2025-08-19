"""
Status Fix Script for KMTI File Approval System
Fixes inconsistent file statuses and ensures proper workflow
"""

import os
import json
from datetime import datetime
from utils.path_config import DATA_PATHS

def fix_approval_queue_statuses():
    """Fix inconsistent statuses in the approval queue"""
    print("=== FIXING APPROVAL QUEUE STATUSES ===")
    
    queue_file = DATA_PATHS.file_approvals_file
    
    if not os.path.exists(queue_file):
        print("❌ Approval queue file does not exist")
        return
    
    try:
        # Load current queue
        with open(queue_file, 'r', encoding='utf-8') as f:
            queue = json.load(f)
        
        print(f"Found {len(queue)} files in approval queue")
        
        changes_made = 0
        
        for file_id, file_data in queue.items():
            current_status = file_data.get('status', '')
            original_status = current_status
            
            # Fix inconsistent statuses
            if current_status == 'pending':
                # Determine correct status based on workflow stage
                if file_data.get('tl_approved_by'):
                    # Already approved by TL, should be pending admin
                    file_data['status'] = 'pending_admin'
                    print(f"  Fixed: {file_data.get('original_filename', 'Unknown')} - 'pending' -> 'pending_admin'")
                    changes_made += 1
                else:
                    # Not yet approved by TL, should be pending team leader
                    file_data['status'] = 'pending_team_leader'
                    print(f"  Fixed: {file_data.get('original_filename', 'Unknown')} - 'pending' -> 'pending_team_leader'")
                    changes_made += 1
            
            # Ensure file has required fields
            required_fields = {
                'file_id': file_id,
                'status_history': [],
                'admin_comments': [],
                'tl_comments': []
            }
            
            for field, default_value in required_fields.items():
                if field not in file_data:
                    file_data[field] = default_value
                    changes_made += 1
            
            # Add status history entry if missing
            if not file_data.get('status_history'):
                file_data['status_history'] = [{
                    'status': file_data['status'],
                    'timestamp': file_data.get('submission_date', datetime.now().isoformat()),
                    'comment': 'Status normalized by fix script'
                }]
                changes_made += 1
        
        if changes_made > 0:
            # Save updated queue
            backup_file = f"{queue_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2)
            print(f"  Created backup: {backup_file}")
            
            # Save updated queue
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2)
            
            print(f"✅ Made {changes_made} fixes to approval queue")
        else:
            print("✅ No fixes needed in approval queue")
            
    except Exception as e:
        print(f"❌ Error fixing approval queue: {e}")

def fix_user_approval_statuses():
    """Fix user approval status files"""
    print("\n=== FIXING USER APPROVAL STATUSES ===")
    
    user_approvals_dir = DATA_PATHS.user_approvals_dir
    
    if not os.path.exists(user_approvals_dir):
        print("❌ User approvals directory does not exist")
        return
    
    try:
        users = [d for d in os.listdir(user_approvals_dir) 
                if os.path.isdir(os.path.join(user_approvals_dir, d))]
        
        print(f"Found {len(users)} user approval directories")
        
        total_changes = 0
        
        for username in users:
            user_approval_file = DATA_PATHS.get_user_approval_status_file(username)
            
            if not os.path.exists(user_approval_file):
                print(f"  {username}: No approval status file")
                continue
            
            try:
                with open(user_approval_file, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                user_changes = 0
                
                for filename, file_data in user_data.items():
                    current_status = file_data.get('status', '')
                    
                    # Fix inconsistent user statuses
                    if current_status == 'pending':
                        file_data['status'] = 'pending_team_leader'
                        user_changes += 1
                    elif current_status == 'not_submitted' and file_data.get('submitted_for_approval'):
                        file_data['status'] = 'pending_team_leader'
                        user_changes += 1
                    
                    # Ensure required fields exist
                    required_fields = {
                        'admin_comments': [],
                        'team_leader_comments': [],
                        'status_history': []
                    }
                    
                    for field, default_value in required_fields.items():
                        if field not in file_data:
                            file_data[field] = default_value
                            user_changes += 1
                
                if user_changes > 0:
                    # Save updated user data
                    with open(user_approval_file, 'w', encoding='utf-8') as f:
                        json.dump(user_data, f, indent=2)
                    
                    print(f"  {username}: Made {user_changes} fixes")
                    total_changes += user_changes
                
            except Exception as e:
                print(f"  {username}: Error - {e}")
        
        print(f"✅ Made {total_changes} total fixes to user approval files")
        
    except Exception as e:
        print(f"❌ Error fixing user approval statuses: {e}")

def verify_workflow_consistency():
    """Verify that the workflow is consistent between global queue and user files"""
    print("\n=== VERIFYING WORKFLOW CONSISTENCY ===")
    
    # Load global queue
    queue_file = DATA_PATHS.file_approvals_file
    if not os.path.exists(queue_file):
        print("❌ No global queue to verify")
        return
    
    try:
        with open(queue_file, 'r', encoding='utf-8') as f:
            global_queue = json.load(f)
        
        print(f"Verifying {len(global_queue)} files in global queue")
        
        inconsistencies = 0
        
        for file_id, queue_data in global_queue.items():
            username = queue_data.get('user_id')
            filename = queue_data.get('original_filename')
            queue_status = queue_data.get('status')
            
            if not username or not filename:
                continue
            
            # Check user's approval status file
            user_approval_file = DATA_PATHS.get_user_approval_status_file(username)
            
            if os.path.exists(user_approval_file):
                try:
                    with open(user_approval_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    if filename in user_data:
                        user_status = user_data[filename].get('status')
                        
                        # Check for inconsistencies
                        if queue_status != user_status:
                            print(f"  ❌ {username}/{filename}: Queue='{queue_status}', User='{user_status}'")
                            inconsistencies += 1
                            
                            # Auto-fix: Update user status to match queue
                            user_data[filename]['status'] = queue_status
                            user_data[filename]['last_sync'] = datetime.now().isoformat()
                            
                            with open(user_approval_file, 'w', encoding='utf-8') as f:
                                json.dump(user_data, f, indent=2)
                            
                            print(f"    ✅ Fixed: Updated user status to '{queue_status}'")
                    
                except Exception as e:
                    print(f"  Error checking {username}: {e}")
        
        if inconsistencies == 0:
            print("✅ All files are consistent between global queue and user files")
        else:
            print(f"✅ Fixed {inconsistencies} inconsistencies")
        
    except Exception as e:
        print(f"❌ Error verifying workflow consistency: {e}")

def create_missing_directories():
    """Create any missing directories"""
    print("\n=== CREATING MISSING DIRECTORIES ===")
    
    try:
        DATA_PATHS.ensure_network_dirs()
        DATA_PATHS.ensure_local_dirs()
        print("✅ All directories ensured")
    except Exception as e:
        print(f"❌ Error creating directories: {e}")

def main():
    """Main fix function"""
    print("KMTI File Approval System - Status Fix Script")
    print("=" * 50)
    
    # Check network availability first
    if not DATA_PATHS.is_network_available():
        print("❌ Network directory not accessible!")
        print("Please check network connectivity before running fixes.")
        return
    
    # Create missing directories
    create_missing_directories()
    
    # Run fixes
    fix_approval_queue_statuses()
    fix_user_approval_statuses()
    verify_workflow_consistency()
    
    print("\n" + "=" * 50)
    print("STATUS FIXES COMPLETE")
    print("\nNext steps:")
    print("1. Test the TL Panel - should now show pending files")
    print("2. Test the Admin Panel - should show files pending admin review")
    print("3. Run debug_approval_workflow.py to verify everything is working")

if __name__ == "__main__":
    main()
