"""
Migration script for KMTI Data Management System
Migrates existing data from local directories to network directories
"""

import os
import shutil
import json
from datetime import datetime
from utils.path_config import DATA_PATHS

def log_migration(message):
    """Log migration messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] MIGRATION: {message}")

def backup_file(source_path, backup_dir):
    """Create a backup of a file before migration"""
    if not os.path.exists(source_path):
        return None
    
    filename = os.path.basename(source_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{filename}.backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(source_path, backup_path)
    return backup_path

def migrate_approvals_data():
    """Migrate approval data from local to network"""
    log_migration("Starting approval data migration...")
    
    old_approvals_dir = "data/approvals"
    new_approvals_dir = DATA_PATHS.approvals_dir
    
    if not os.path.exists(old_approvals_dir):
        log_migration("No local approval data found to migrate")
        return
    
    # Create backup directory
    backup_dir = os.path.join("backup", "migration", "approvals")
    
    try:
        # Ensure network directory exists
        os.makedirs(new_approvals_dir, exist_ok=True)
        
        # Migrate files
        for filename in os.listdir(old_approvals_dir):
            old_file = os.path.join(old_approvals_dir, filename)
            new_file = os.path.join(new_approvals_dir, filename)
            
            if os.path.isfile(old_file):
                # Create backup
                backup_path = backup_file(old_file, backup_dir)
                log_migration(f"Created backup: {backup_path}")
                
                # Copy to network location
                shutil.copy2(old_file, new_file)
                log_migration(f"Migrated: {filename}")
                
                # Remove old file
                os.remove(old_file)
                log_migration(f"Removed old file: {old_file}")
        
        # Remove old directory if empty
        try:
            os.rmdir(old_approvals_dir)
            log_migration(f"Removed empty directory: {old_approvals_dir}")
        except OSError:
            log_migration(f"Directory not empty, keeping: {old_approvals_dir}")
            
    except Exception as e:
        log_migration(f"Error migrating approval data: {e}")

def migrate_user_data():
    """Migrate user upload and approval data"""
    log_migration("Starting user data migration...")
    
    old_uploads_dir = "data/uploads"
    old_user_approvals_dir = "data/user_approvals"
    
    # Migrate uploads
    if os.path.exists(old_uploads_dir):
        new_uploads_dir = DATA_PATHS.uploads_dir
        backup_dir = os.path.join("backup", "migration", "uploads")
        
        try:
            os.makedirs(new_uploads_dir, exist_ok=True)
            
            for username in os.listdir(old_uploads_dir):
                old_user_dir = os.path.join(old_uploads_dir, username)
                new_user_dir = os.path.join(new_uploads_dir, username)
                
                if os.path.isdir(old_user_dir):
                    # Create backup
                    user_backup_dir = os.path.join(backup_dir, username)
                    os.makedirs(user_backup_dir, exist_ok=True)
                    shutil.copytree(old_user_dir, os.path.join(user_backup_dir, "uploads"), dirs_exist_ok=True)
                    
                    # Migrate to network
                    if not os.path.exists(new_user_dir):
                        shutil.copytree(old_user_dir, new_user_dir)
                        log_migration(f"Migrated user uploads: {username}")
                    else:
                        log_migration(f"User directory already exists: {username}")
                    
                    # Remove old directory
                    shutil.rmtree(old_user_dir)
                    log_migration(f"Removed old user directory: {old_user_dir}")
            
            # Remove old uploads directory if empty
            try:
                os.rmdir(old_uploads_dir)
                log_migration(f"Removed empty directory: {old_uploads_dir}")
            except OSError:
                log_migration(f"Directory not empty, keeping: {old_uploads_dir}")
                
        except Exception as e:
            log_migration(f"Error migrating user uploads: {e}")
    
    # Migrate user approvals
    if os.path.exists(old_user_approvals_dir):
        new_user_approvals_dir = DATA_PATHS.user_approvals_dir
        backup_dir = os.path.join("backup", "migration", "user_approvals")
        
        try:
            os.makedirs(new_user_approvals_dir, exist_ok=True)
            
            for username in os.listdir(old_user_approvals_dir):
                old_user_approval_dir = os.path.join(old_user_approvals_dir, username)
                new_user_approval_dir = os.path.join(new_user_approvals_dir, username)
                
                if os.path.isdir(old_user_approval_dir):
                    # Create backup
                    user_backup_dir = os.path.join(backup_dir, username)
                    os.makedirs(user_backup_dir, exist_ok=True)
                    shutil.copytree(old_user_approval_dir, os.path.join(user_backup_dir, "approvals"), dirs_exist_ok=True)
                    
                    # Migrate to network
                    if not os.path.exists(new_user_approval_dir):
                        shutil.copytree(old_user_approval_dir, new_user_approval_dir)
                        log_migration(f"Migrated user approval data: {username}")
                    else:
                        log_migration(f"User approval directory already exists: {username}")
                    
                    # Remove old directory
                    shutil.rmtree(old_user_approval_dir)
                    log_migration(f"Removed old user approval directory: {old_user_approval_dir}")
            
            # Remove old user_approvals directory if empty
            try:
                os.rmdir(old_user_approvals_dir)
                log_migration(f"Removed empty directory: {old_user_approvals_dir}")
            except OSError:
                log_migration(f"Directory not empty, keeping: {old_user_approvals_dir}")
                
        except Exception as e:
            log_migration(f"Error migrating user approval data: {e}")

def migrate_cache_data():
    """Migrate cache data"""
    log_migration("Starting cache data migration...")
    
    old_cache_dir = "data/cache"
    
    if os.path.exists(old_cache_dir):
        new_cache_dir = DATA_PATHS.cache_dir
        backup_dir = os.path.join("backup", "migration", "cache")
        
        try:
            # Create backup
            if os.listdir(old_cache_dir):  # Only if not empty
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copytree(old_cache_dir, os.path.join(backup_dir, "cache"), dirs_exist_ok=True)
                log_migration(f"Created cache backup")
            
            # Migrate to network
            os.makedirs(new_cache_dir, exist_ok=True)
            for item in os.listdir(old_cache_dir):
                old_item = os.path.join(old_cache_dir, item)
                new_item = os.path.join(new_cache_dir, item)
                
                if os.path.isfile(old_item):
                    shutil.copy2(old_item, new_item)
                    os.remove(old_item)
                    log_migration(f"Migrated cache file: {item}")
                elif os.path.isdir(old_item):
                    shutil.copytree(old_item, new_item, dirs_exist_ok=True)
                    shutil.rmtree(old_item)
                    log_migration(f"Migrated cache directory: {item}")
            
            # Remove old cache directory if empty
            try:
                os.rmdir(old_cache_dir)
                log_migration(f"Removed empty directory: {old_cache_dir}")
            except OSError:
                log_migration(f"Directory not empty, keeping: {old_cache_dir}")
                
        except Exception as e:
            log_migration(f"Error migrating cache data: {e}")

def create_migration_summary():
    """Create a summary of the migration"""
    summary = {
        "migration_date": datetime.now().isoformat(),
        "network_base": DATA_PATHS.NETWORK_BASE,
        "local_base": DATA_PATHS.LOCAL_BASE,
        "migrated_directories": [
            "data/approvals -> network/approvals",
            "data/uploads -> network/uploads", 
            "data/user_approvals -> network/user_approvals",
            "data/cache -> network/cache"
        ],
        "preserved_local": [
            "data/sessions (kept local)",
            "data/logs (kept local)",
            "data/config.json (local config)"
        ],
        "backup_location": "backup/migration/"
    }
    
    summary_file = os.path.join("backup", "migration", "migration_summary.json")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    log_migration(f"Created migration summary: {summary_file}")

def run_migration():
    """Run the complete migration process"""
    log_migration("=== STARTING KMTI DATA MIGRATION ===")
    log_migration(f"Network directory: {DATA_PATHS.NETWORK_BASE}")
    log_migration(f"Local directory: {DATA_PATHS.LOCAL_BASE}")
    
    # Check if network is available
    if not DATA_PATHS.is_network_available():
        log_migration(f"ERROR: Network directory {DATA_PATHS.NETWORK_BASE} is not accessible!")
        log_migration("Migration aborted. Please ensure network connectivity.")
        return False
    
    try:
        # Run migrations
        migrate_approvals_data()
        migrate_user_data()
        migrate_cache_data()
        
        # Create summary
        create_migration_summary()
        
        log_migration("=== MIGRATION COMPLETED SUCCESSFULLY ===")
        log_migration("All data has been migrated to the network directory.")
        log_migration("Backups have been created in the backup/migration/ directory.")
        log_migration("Sessions and logs remain in the local data directory as intended.")
        
        return True
        
    except Exception as e:
        log_migration(f"CRITICAL ERROR during migration: {e}")
        log_migration("Migration failed. Please check the error and try again.")
        return False

if __name__ == "__main__":
    print("KMTI Data Migration Script")
    print("=" * 50)
    print(f"This script will migrate data from local directories to:")
    print(f"Network: {DATA_PATHS.NETWORK_BASE}")
    print(f"Local data will remain at: {DATA_PATHS.LOCAL_BASE}")
    print()
    
    # Check network availability
    if not DATA_PATHS.is_network_available():
        print(f"ERROR: Network directory {DATA_PATHS.NETWORK_BASE} is not accessible!")
        print("Please ensure:")
        print("1. Network connectivity is working")
        print("2. You have access to the KMTI-NAS shared folder")
        print("3. The path is correct and accessible")
        exit(1)
    
    response = input("Do you want to proceed with the migration? (yes/no): ").lower().strip()
    
    if response == 'yes':
        success = run_migration()
        if success:
            print("\nMigration completed successfully!")
            print("You can now run the application with the new network data structure.")
        else:
            print("\nMigration failed. Please check the error messages above.")
            exit(1)
    else:
        print("Migration cancelled.")
        exit(0)
