#!/usr/bin/env python3
"""
File Status Migration Script

This script migrates existing files from the old workflow to the new 3-role workflow:
- Updates 'pending' status to 'pending_team_leader' 
- Adds proper status history
- Preserves all existing data

Before: my_files → pending → approved
After:  my_files → pending_team_leader → pending_admin → approved
"""

import os
import json
from datetime import datetime
from typing import Dict

def migrate_file_statuses():
    """Migrate files from old workflow to new workflow."""
    print("🔄 Starting File Status Migration...\n")
    
    file_approvals_path = "data/approvals/file_approvals.json"
    
    if not os.path.exists(file_approvals_path):
        print(f"❌ File not found: {file_approvals_path}")
        print("No files to migrate.")
        return
    
    try:
        # Load existing files
        with open(file_approvals_path, 'r', encoding='utf-8') as f:
            queue = json.load(f)
        
        print(f"📁 Loaded {len(queue)} files from approval queue")
        
        # Track changes
        migrated_count = 0
        skipped_count = 0
        
        # Process each file
        for file_id, file_data in queue.items():
            current_status = file_data.get('status', '')
            filename = file_data.get('original_filename', 'Unknown')
            user = file_data.get('user_id', 'Unknown')
            
            print(f"\n📄 Processing: {filename} (User: {user})")
            print(f"   Current status: '{current_status}'")
            
            if current_status == 'pending':
                # Migrate to new workflow
                file_data['status'] = 'pending_team_leader'
                
                # Update status history
                if 'status_history' not in file_data:
                    file_data['status_history'] = []
                
                # Add migration note to status history
                file_data['status_history'].append({
                    'status': 'pending_team_leader',
                    'timestamp': datetime.now().isoformat(),
                    'comment': 'Migrated from old workflow - ready for team leader review'
                })
                
                print(f"   ✅ Migrated: 'pending' → 'pending_team_leader'")
                migrated_count += 1
                
            elif current_status in ['pending_team_leader', 'pending_admin', 'approved', 'rejected_team_leader', 'rejected_admin']:
                print(f"   ⏭️  Already using new workflow, skipping")
                skipped_count += 1
                
            else:
                print(f"   ⚠️  Unknown status '{current_status}', skipping")
                skipped_count += 1
        
        # Save updated queue
        if migrated_count > 0:
            # Create backup first
            backup_path = f"{file_approvals_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2)
            print(f"\n💾 Created backup: {backup_path}")
            
            # Save updated queue
            with open(file_approvals_path, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2)
            
            print(f"💾 Saved updated approval queue")
        
        # Summary
        print(f"\n{'='*50}")
        print("📊 MIGRATION SUMMARY")
        print(f"{'='*50}")
        print(f"✅ Migrated files: {migrated_count}")
        print(f"⏭️  Skipped files: {skipped_count}")
        print(f"📁 Total files: {len(queue)}")
        
        if migrated_count > 0:
            print(f"\n🎉 Migration completed successfully!")
            print(f"Files with 'pending' status have been updated to 'pending_team_leader'")
            print(f"Team Leaders can now see and approve these files.")
        else:
            print(f"\n✅ No migration needed - all files already use the new workflow.")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()

def verify_migration():
    """Verify the migration results."""
    print(f"\n🔍 Verifying Migration Results...\n")
    
    file_approvals_path = "data/approvals/file_approvals.json"
    
    try:
        with open(file_approvals_path, 'r', encoding='utf-8') as f:
            queue = json.load(f)
        
        status_counts = {}
        team_counts = {}
        
        for file_id, file_data in queue.items():
            status = file_data.get('status', 'unknown')
            team = file_data.get('user_team', 'unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            team_counts[team] = team_counts.get(team, 0) + 1
        
        print("📊 Status Distribution:")
        for status, count in status_counts.items():
            print(f"   {status}: {count} files")
        
        print(f"\n👥 Team Distribution:")
        for team, count in team_counts.items():
            print(f"   {team}: {count} files")
        
        print(f"\n✅ Verification complete!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    print("🚀 File Status Migration Tool")
    print("="*50)
    
    # Show current status first
    verify_migration()
    
    print("="*50)
    proceed = input("\nProceed with migration? (y/N): ").lower().strip()
    
    if proceed == 'y':
        migrate_file_statuses()
        print("\n" + "="*50)
        verify_migration()
    else:
        print("Migration cancelled.")
