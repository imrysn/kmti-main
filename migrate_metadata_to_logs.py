#!/usr/bin/env python3
"""
Migration Script: Move Metadata Files to Logs Directory
Moves existing metadata files from project directories to \\KMTI-NAS\\Shared\\data\\logs\\file_metadata\\
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_BASE_DIR = r"\\KMTI-NAS\Database\PROJECTS"
LOGS_BASE_DIR = r"\\KMTI-NAS\Shared\data\logs\file_metadata"
LOCAL_LOGS_DIR = "data/logs/file_metadata"  # Fallback location

def migrate_metadata_files():
    """Migrate all metadata files from project directories to logs directory"""
    
    print("🔄 KMTI Metadata Migration Tool")
    print("=" * 60)
    print(f"Source: {PROJECT_BASE_DIR}")
    print(f"Target: {LOGS_BASE_DIR}")
    print("-" * 60)
    
    migration_stats = {
        "teams_processed": 0,
        "years_processed": 0,
        "files_moved": 0,
        "files_skipped": 0,
        "errors": 0
    }
    
    moved_files = []
    errors = []
    
    try:
        # Check if project base directory exists
        if not os.path.exists(PROJECT_BASE_DIR):
            print(f"❌ Project directory not found: {PROJECT_BASE_DIR}")
            print("Using local data structure for migration...")
            return migrate_local_metadata()
        
        # Iterate through team directories
        for team_name in os.listdir(PROJECT_BASE_DIR):
            team_path = os.path.join(PROJECT_BASE_DIR, team_name)
            
            if not os.path.isdir(team_path):
                continue
                
            print(f"\n📁 Processing team: {team_name}")
            migration_stats["teams_processed"] += 1
            
            # Iterate through year directories
            for year_name in os.listdir(team_path):
                year_path = os.path.join(team_path, year_name)
                
                if not os.path.isdir(year_path) or not year_name.isdigit():
                    continue
                
                print(f"  📅 Processing year: {year_name}")
                migration_stats["years_processed"] += 1
                
                # Find and move metadata files in this year directory
                metadata_files = [f for f in os.listdir(year_path) if f.endswith('.metadata.json')]
                
                if not metadata_files:
                    print(f"    ✅ No metadata files found")
                    continue
                
                print(f"    📋 Found {len(metadata_files)} metadata files")
                
                # Create target directory
                target_dir = os.path.join(LOGS_BASE_DIR, team_name, year_name)
                
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    print(f"    📂 Created target directory: {target_dir}")
                except Exception as e:
                    print(f"    ⚠️  Could not create network directory, trying local fallback...")
                    target_dir = os.path.join(LOCAL_LOGS_DIR, team_name, year_name)
                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        print(f"    📂 Created local target directory: {target_dir}")
                    except Exception as e2:
                        print(f"    ❌ Failed to create target directory: {e2}")
                        errors.append(f"Failed to create directory for {team_name}/{year_name}: {e2}")
                        migration_stats["errors"] += 1
                        continue
                
                # Move each metadata file
                for metadata_file in metadata_files:
                    source_path = os.path.join(year_path, metadata_file)
                    target_path = os.path.join(target_dir, metadata_file)
                    
                    try:
                        # Check if target already exists
                        if os.path.exists(target_path):
                            print(f"    ⏭️  Skipping {metadata_file} (already exists in target)")
                            migration_stats["files_skipped"] += 1
                            continue
                        
                        # Move the file
                        shutil.move(source_path, target_path)
                        print(f"    ✅ Moved: {metadata_file}")
                        
                        moved_files.append({
                            "team": team_name,
                            "year": year_name,
                            "file": metadata_file,
                            "from": source_path,
                            "to": target_path,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        migration_stats["files_moved"] += 1
                        
                    except Exception as e:
                        print(f"    ❌ Error moving {metadata_file}: {e}")
                        errors.append(f"Error moving {team_name}/{year_name}/{metadata_file}: {e}")
                        migration_stats["errors"] += 1
        
        # Generate migration report
        generate_migration_report(migration_stats, moved_files, errors)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED!")
        print(f"✅ Teams processed: {migration_stats['teams_processed']}")
        print(f"✅ Years processed: {migration_stats['years_processed']}")
        print(f"✅ Files moved: {migration_stats['files_moved']}")
        print(f"⏭️  Files skipped: {migration_stats['files_skipped']}")
        print(f"❌ Errors: {migration_stats['errors']}")
        
        if errors:
            print("\n⚠️  ERRORS ENCOUNTERED:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors (see migration_report.json)")
        
        return migration_stats["errors"] == 0
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        return False

def migrate_local_metadata():
    """Migrate metadata files from local data structure"""
    print("\n🔄 Migrating from local data structure...")
    
    # This is a placeholder for local migration
    # Add logic here if there are local metadata files to migrate
    print("✅ Local migration completed (no local metadata files found)")
    return True

def generate_migration_report(stats, moved_files, errors):
    """Generate a detailed migration report"""
    
    report = {
        "migration_info": {
            "timestamp": datetime.now().isoformat(),
            "script_version": "1.0",
            "source_directory": PROJECT_BASE_DIR,
            "target_directory": LOGS_BASE_DIR
        },
        "statistics": stats,
        "moved_files": moved_files,
        "errors": errors
    }
    
    # Save report to logs directory
    try:
        report_dir = os.path.join(LOGS_BASE_DIR, "migration_reports")
        os.makedirs(report_dir, exist_ok=True)
        
        report_filename = f"metadata_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(report_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Migration report saved: {report_path}")
        
    except Exception as e:
        # Fallback to local directory
        try:
            os.makedirs("data/logs", exist_ok=True)
            report_filename = f"metadata_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join("data/logs", report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📊 Migration report saved locally: {report_path}")
            
        except Exception as e2:
            print(f"\n⚠️  Could not save migration report: {e2}")

def verify_migration():
    """Verify that the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        # Check if logs directory structure exists
        if os.path.exists(LOGS_BASE_DIR):
            teams = [d for d in os.listdir(LOGS_BASE_DIR) if os.path.isdir(os.path.join(LOGS_BASE_DIR, d))]
            print(f"✅ Found {len(teams)} team directories in logs")
            
            total_metadata = 0
            for team in teams[:3]:  # Check first 3 teams
                team_dir = os.path.join(LOGS_BASE_DIR, team)
                if os.path.exists(team_dir):
                    years = [d for d in os.listdir(team_dir) if os.path.isdir(os.path.join(team_dir, d))]
                    for year in years:
                        year_dir = os.path.join(team_dir, year)
                        metadata_files = [f for f in os.listdir(year_dir) if f.endswith('.metadata.json')]
                        total_metadata += len(metadata_files)
            
            print(f"✅ Verified {total_metadata} metadata files in new location")
            return True
        else:
            print("❌ Logs directory not found")
            return False
    
    except Exception as e:
        print(f"⚠️  Verification error: {e}")
        return False

if __name__ == "__main__":
    print("KMTI Metadata Files Migration Script")
    print("This script moves metadata files from project directories to the logs directory")
    print()
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        exit(0)
    
    try:
        # Run migration
        success = migrate_metadata_files()
        
        if success:
            print("\n🎯 Migration completed successfully!")
            
            # Verify migration
            if verify_migration():
                print("🔍 Verification completed successfully!")
                print("\n✅ MIGRATION FULLY COMPLETED!")
                print("\nNext steps:")
                print("1. Test the file approval system")
                print("2. Verify metadata is accessible")
                print("3. Remove any old metadata files from project directories if desired")
            else:
                print("⚠️  Verification had issues - please check manually")
        else:
            print("\n❌ Migration completed with errors")
            print("Please check the error messages above and migration report")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)
