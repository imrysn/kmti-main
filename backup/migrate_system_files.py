import os
import json
import shutil
from datetime import datetime

def migrate_system_files():
    """
    Migration script to move system files from user upload folders to data folder
    This will clean up the system files showing in your user file view
    """
    print("🔧 Starting system file migration...")
    
    uploads_dir = "data/uploads"
    if not os.path.exists(uploads_dir):
        print("❌ No uploads directory found. Nothing to migrate.")
        return
    
    migration_log = []
    
    try:
        # Get list of all user folders
        user_folders = []
        for item in os.listdir(uploads_dir):
            user_path = os.path.join(uploads_dir, item)
            if os.path.isdir(user_path):
                user_folders.append((item, user_path))
        
        print(f"📁 Found {len(user_folders)} user folders to check")
        
        for username, user_folder in user_folders:
            print(f"\n👤 Processing user: {username}")
            
            # Create new system data folder
            system_data_folder = os.path.join("data", "user_approvals", username)
            os.makedirs(system_data_folder, exist_ok=True)
            
            # Files to migrate
            system_files_to_migrate = [
                "file_approval_status.json",
                "approval_notifications.json"
            ]
            
            migrated_files = []
            
            for system_file in system_files_to_migrate:
                old_path = os.path.join(user_folder, system_file)
                new_path = os.path.join(system_data_folder, system_file)
                
                if os.path.exists(old_path):
                    try:
                        # Move file to new location
                        if os.path.exists(new_path):
                            # If file already exists in new location, backup the old one
                            backup_path = f"{old_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            os.rename(old_path, backup_path)
                            print(f"  📦 Backed up existing {system_file} to {os.path.basename(backup_path)}")
                        else:
                            # Move to new location
                            shutil.move(old_path, new_path)
                            migrated_files.append(system_file)
                            print(f"  ✅ Moved {system_file} to data folder")
                    
                    except Exception as e:
                        print(f"  ❌ Error migrating {system_file}: {e}")
                        migration_log.append(f"Error migrating {username}/{system_file}: {e}")
                else:
                    print(f"  ℹ️  No {system_file} found (nothing to migrate)")
            
            if migrated_files:
                migration_log.append(f"Successfully migrated {username}: {', '.join(migrated_files)}")
                print(f"  🎉 Migration completed for {username}")
            else:
                print(f"  ℹ️  No files to migrate for {username}")
        
        print(f"\n📊 Migration Summary:")
        print(f"   - Processed {len(user_folders)} user folders")
        print(f"   - Migration events: {len(migration_log)}")
        
        # Create migration log file
        log_file = os.path.join("data", f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs("data", exist_ok=True)
        with open(log_file, 'w') as f:
            f.write(f"System File Migration Log - {datetime.now()}\n")
            f.write("="*50 + "\n\n")
            for entry in migration_log:
                f.write(f"{entry}\n")
        
        print(f"📝 Migration log saved to: {log_file}")
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")


def cleanup_user_folders():
    """
    Additional cleanup to remove any remaining system files from user folders
    """
    print("\n🧹 Starting user folder cleanup...")
    
    uploads_dir = "data/uploads"
    if not os.path.exists(uploads_dir):
        print("❌ No uploads directory found.")
        return
    
    system_files_to_remove = [
        "file_approval_status.json",
        "approval_notifications.json"
    ]
    
    try:
        for username in os.listdir(uploads_dir):
            user_folder = os.path.join(uploads_dir, username)
            if not os.path.isdir(user_folder):
                continue
            
            print(f"🧹 Cleaning {username}...")
            
            for system_file in system_files_to_remove:
                old_file_path = os.path.join(user_folder, system_file)
                
                if os.path.exists(old_file_path):
                    try:
                        # Create backup before removal
                        backup_dir = os.path.join("data", "cleanup_backup", username)
                        os.makedirs(backup_dir, exist_ok=True)
                        backup_path = os.path.join(backup_dir, f"{system_file}.backup")
                        
                        # Move to backup (don't just delete)
                        shutil.move(old_file_path, backup_path)
                        print(f"  📦 Moved {system_file} to backup")
                        
                    except Exception as e:
                        print(f"  ❌ Error cleaning {system_file}: {e}")
        
        print("✅ Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def verify_migration():
    """
    Verify that migration was successful
    """
    print("\n🔍 Verifying migration...")
    
    uploads_dir = "data/uploads"
    approvals_dir = "data/user_approvals"
    
    if not os.path.exists(uploads_dir):
        print("❌ No uploads directory found.")
        return
    
    issues_found = []
    success_count = 0
    
    try:
        # Check each user folder
        for username in os.listdir(uploads_dir):
            user_folder = os.path.join(uploads_dir, username)
            if not os.path.isdir(user_folder):
                continue
            
            # Check for remaining system files in user folder
            system_files_in_user_folder = []
            for file in os.listdir(user_folder):
                if file in ["file_approval_status.json", "approval_notifications.json"]:
                    system_files_in_user_folder.append(file)
            
            if system_files_in_user_folder:
                issues_found.append(f"{username}: Still has {', '.join(system_files_in_user_folder)} in upload folder")
            
            # Check if system files exist in new location
            system_data_folder = os.path.join(approvals_dir, username)
            if os.path.exists(system_data_folder):
                migrated_files = []
                for file in ["file_approval_status.json", "approval_notifications.json"]:
                    if os.path.exists(os.path.join(system_data_folder, file)):
                        migrated_files.append(file)
                
                if migrated_files:
                    print(f"  ✅ {username}: System files properly located in data folder: {', '.join(migrated_files)}")
                    success_count += 1
        
        if issues_found:
            print(f"\n⚠️  Issues found:")
            for issue in issues_found:
                print(f"   - {issue}")
        else:
            print(f"✅ Migration verification passed! All system files are properly located.")
            print(f"✅ Successfully processed {success_count} users.")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")


if __name__ == "__main__":
    print("🚀 KMTI System File Migration Tool")
    print("="*40)
    
    # Step 1: Migrate system files to proper location
    migrate_system_files()
    
    # Step 2: Clean up any remaining files
    cleanup_user_folders()
    
    # Step 3: Verify migration
    verify_migration()
    
    print("\n" + "="*40)
    print("🎉 Migration process completed!")
    print("💡 System files should no longer appear in your user file view.")
    print("📝 Check the migration log file for detailed results.")
    print("\n💾 To revert changes, restore from the backup folders created.")
