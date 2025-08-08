#!/usr/bin/env python3
"""
KMTI Hybrid Migration Tool - Fixed Version
==========================================

This script migrates your existing KMTI JSON-based data to the new hybrid SQLite architecture.
Fixes for teams.json format and Unicode encoding issues.

Usage:
    python migrate_to_hybrid_fixed.py
"""

import sys
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import traceback

class KMTIMigrator:
    """Handles migration from JSON to hybrid SQLite system - Fixed version"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.data_dir = self.project_root / "data"
        self.backup_dir = None
        self.nas_available = False
        self.migration_log = []
        
        # Check for NAS availability
        self.check_nas_availability()
        
    def check_nas_availability(self):
        """Check if NAS is available for database placement"""
        nas_path = Path("Y:/APP DEVELOPMENT/kmti-main")
        if nas_path.exists() and nas_path.is_dir():
            self.nas_available = True
            self.target_db_path = nas_path / "data" / "kmti_hybrid.db"
            self.log("NAS detected - database will be created on network share")
        else:
            self.target_db_path = self.data_dir / "kmti_hybrid.db"
            self.log("NAS not available - using local database")
    
    def log(self, message: str):
        """Log migration message - Unicode safe"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Remove emoji characters for compatibility
        clean_message = message.replace("🌐", "[NAS]").replace("💽", "[LOCAL]").replace("📦", "[BACKUP]").replace("✅", "[OK]").replace("❌", "[ERROR]").replace("⚠️", "[WARN]").replace("🔄", "[PROCESS]").replace("📊", "[DATA]").replace("👤", "[USER]").replace("🧪", "[TEST]")
        log_entry = f"[{timestamp}] {clean_message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def create_backup(self) -> bool:
        """Create backup of existing data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = self.project_root / f"data_backup_{timestamp}"
            self.backup_dir.mkdir(exist_ok=True)
            
            self.log(f"Creating backup at: {self.backup_dir}")
            
            if not self.data_dir.exists():
                self.log("No existing data directory found")
                return True
            
            # Files to backup
            files_to_backup = [
                "users.json",
                "teams.json", 
                "permissions.json",
                "session.json",
                "config.json",
                "remembered_users.json"
            ]
            
            backup_count = 0
            for filename in files_to_backup:
                source_file = self.data_dir / filename
                if source_file.exists():
                    dest_file = self.backup_dir / filename
                    shutil.copy2(source_file, dest_file)
                    self.log(f"  Backed up {filename}")
                    backup_count += 1
            
            # Backup directories
            dirs_to_backup = ["uploads", "approvals", "approved", "approval_queue", "export", "logs"]
            for dirname in dirs_to_backup:
                source_dir = self.data_dir / dirname
                if source_dir.exists():
                    dest_dir = self.backup_dir / dirname
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
                    self.log(f"  Backed up directory {dirname}")
                    backup_count += 1
            
            self.log(f"Backup complete - {backup_count} items backed up")
            return True
            
        except Exception as e:
            self.log(f"Backup failed: {e}")
            return False
    
    def setup_hybrid_system(self) -> bool:
        """Initialize the hybrid system"""
        try:
            # Create core directory if it doesn't exist
            core_dir = self.project_root / "core"
            core_dir.mkdir(exist_ok=True)
            
            # Check if hybrid_manager.py exists
            hybrid_manager_file = core_dir / "hybrid_manager.py"
            if not hybrid_manager_file.exists():
                self.log("ERROR: hybrid_manager.py not found in core/ directory")
                self.log("   Please copy the hybrid_manager.py file to core/hybrid_manager.py first")
                return False
            
            # Create __init__.py if it doesn't exist
            init_file = core_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                self.log("Created core/__init__.py")
            
            # Import and initialize hybrid system
            sys.path.insert(0, str(self.project_root))
            from core.hybrid_manager import KMTIHybridApp
            
            # Ensure target directory exists
            self.target_db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.hybrid_app = KMTIHybridApp(self.target_db_path)
            self.log(f"Hybrid system initialized - Database: {self.target_db_path}")
            
            return True
            
        except ImportError as e:
            self.log(f"Failed to import hybrid system: {e}")
            self.log("   Make sure hybrid_manager.py is in the core/ directory")
            return False
        except Exception as e:
            self.log(f"Failed to initialize hybrid system: {e}")
            traceback.print_exc()
            return False
    
    def migrate_users(self) -> bool:
        """Migrate users from JSON to SQLite"""
        try:
            users_file = self.data_dir / "users.json"
            if not users_file.exists():
                self.log("No users.json found - skipping user migration")
                return True
            
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            self.log(f"Migrating {len(users_data)} users...")
            
            conn = self.hybrid_app.db_manager.get_connection()
            try:
                migrated_count = 0
                for email, user_data in users_data.items():
                    try:
                        # Insert user
                        conn.execute('''
                            INSERT OR REPLACE INTO users 
                            (email, username, fullname, password_hash, role, team_tags, 
                             join_date, runtime_start, last_login, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            email,
                            user_data.get('username', ''),
                            user_data.get('fullname', ''),
                            user_data.get('password', ''),  # Already hashed
                            user_data.get('role', 'USER'),
                            json.dumps(user_data.get('team_tags', [])),
                            user_data.get('join_date'),
                            user_data.get('runtime_start'),
                            user_data.get('runtime_start'),  # Use as last_login initially
                            True  # is_active
                        ))
                        migrated_count += 1
                    except Exception as e:
                        self.log(f"  Failed to migrate user {email}: {e}")
                
                conn.commit()
                self.log(f"Successfully migrated {migrated_count} users")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.log(f"User migration failed: {e}")
            return False
    
    def migrate_teams(self) -> bool:
        """Migrate teams from JSON to SQLite - Fixed to handle both list and dict formats"""
        try:
            teams_file = self.data_dir / "teams.json"
            if not teams_file.exists():
                self.log("No teams.json found - creating default team")
                # Create default IT team
                conn = self.hybrid_app.db_manager.get_connection()
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO teams (team_id, team_name, description)
                        VALUES (?, ?, ?)
                    ''', ("IT", "IT Department", "Information Technology Department"))
                    conn.commit()
                    self.log("Created default IT team")
                finally:
                    conn.close()
                return True
            
            with open(teams_file, 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
            
            # Handle both list and dictionary formats
            if isinstance(teams_data, list):
                self.log(f"Teams data is a list with {len(teams_data)} items - converting to dict format")
                # Convert list to dictionary format
                teams_dict = {}
                for i, team in enumerate(teams_data):
                    if isinstance(team, dict):
                        # If list contains dicts, use team_id or name as key
                        team_id = team.get('id', team.get('team_id', team.get('name', f'team_{i}')))
                        teams_dict[team_id] = team
                    elif isinstance(team, str):
                        # If list contains strings, use string as both id and name
                        teams_dict[team] = {'name': team, 'description': f'{team} team'}
                    else:
                        # Fallback for other types
                        team_id = f'team_{i}'
                        teams_dict[team_id] = {'name': str(team), 'description': f'{team} team'}
                teams_data = teams_dict
            elif isinstance(teams_data, dict):
                self.log(f"Teams data is a dictionary with {len(teams_data)} items")
            else:
                self.log(f"Unknown teams data format: {type(teams_data)} - creating default team")
                teams_data = {"IT": {"name": "IT Department", "description": "Information Technology Department"}}
            
            self.log(f"Migrating {len(teams_data)} teams...")
            
            conn = self.hybrid_app.db_manager.get_connection()
            try:
                migrated_count = 0
                for team_id, team_info in teams_data.items():
                    try:
                        # Handle different team_info formats
                        if isinstance(team_info, dict):
                            team_name = team_info.get('name', team_id)
                            team_desc = team_info.get('description', f'{team_name} team')
                            is_active = team_info.get('active', True)
                        elif isinstance(team_info, str):
                            team_name = team_info
                            team_desc = f'{team_info} team'
                            is_active = True
                        else:
                            team_name = str(team_info)
                            team_desc = f'{team_name} team'
                            is_active = True
                        
                        conn.execute('''
                            INSERT OR REPLACE INTO teams (team_id, team_name, description, is_active)
                            VALUES (?, ?, ?, ?)
                        ''', (team_id, team_name, team_desc, is_active))
                        migrated_count += 1
                        self.log(f"  Migrated team: {team_id} -> {team_name}")
                    except Exception as e:
                        self.log(f"  Failed to migrate team {team_id}: {e}")
                
                conn.commit()
                self.log(f"Successfully migrated {migrated_count} teams")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.log(f"Team migration failed: {e}")
            traceback.print_exc()
            return False
    
    def migrate_files(self) -> bool:
        """Migrate file metadata to SQLite"""
        try:
            # Check various directories for files
            file_directories = [
                self.data_dir / "uploads",
                self.data_dir / "approvals", 
                self.data_dir / "approved",
                self.data_dir / "approval_queue"
            ]
            
            total_files = 0
            migrated_files = 0
            
            conn = self.hybrid_app.db_manager.get_connection()
            
            try:
                for directory in file_directories:
                    if not directory.exists():
                        continue
                    
                    self.log(f"Scanning {directory.name} directory...")
                    
                    # Look for JSON metadata files
                    for json_file in directory.glob("*.json"):
                        total_files += 1
                        
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                file_data = json.load(f)
                            
                            # Generate file ID if not present
                            file_id = file_data.get('id', f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{total_files}")
                            
                            # Determine approval status based on directory
                            if "approved" in str(directory):
                                approval_status = "approved"
                            elif "approval_queue" in str(directory):
                                approval_status = "pending"
                            else:
                                approval_status = file_data.get('approval_status', 'pending')
                            
                            # Insert file metadata
                            conn.execute('''
                                INSERT OR REPLACE INTO files 
                                (id, filename, file_path, file_size, file_type, team_tags,
                                 approval_status, created_by, description, created_date,
                                 approved_by, approval_date)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                file_id,
                                file_data.get('filename', json_file.name),
                                str(json_file),
                                file_data.get('file_size', 0),
                                file_data.get('file_type', 'unknown'),
                                json.dumps(file_data.get('team_tags', [])),
                                approval_status,
                                file_data.get('created_by', 'system'),
                                file_data.get('description', ''),
                                file_data.get('created_date', datetime.now().isoformat()),
                                file_data.get('approved_by'),
                                file_data.get('approval_date')
                            ))
                            
                            migrated_files += 1
                            
                        except Exception as e:
                            self.log(f"  Failed to migrate file {json_file}: {e}")
                
                conn.commit()
                self.log(f"Successfully migrated {migrated_files}/{total_files} files")
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.log(f"File migration failed: {e}")
            return False
    
    def create_migration_flag(self) -> bool:
        """Create migration completion flag"""
        try:
            migration_flag = self.target_db_path.parent / ".migration_done"
            
            migration_info = {
                "migration_date": datetime.now().isoformat(),
                "migrated_from": str(self.data_dir),
                "database_path": str(self.target_db_path),
                "nas_enabled": self.nas_available,
                "backup_location": str(self.backup_dir) if self.backup_dir else None,
                "migration_log": self.migration_log
            }
            
            with open(migration_flag, 'w', encoding='utf-8') as f:
                json.dump(migration_info, f, indent=2, ensure_ascii=False)
            
            self.log(f"Created migration flag: {migration_flag}")
            return True
            
        except Exception as e:
            self.log(f"Failed to create migration flag: {e}")
            return False
    
    def test_hybrid_system(self) -> bool:
        """Test the migrated hybrid system"""
        try:
            self.log("Testing hybrid system...")
            
            # Test database connection
            conn = self.hybrid_app.db_manager.get_connection()
            try:
                # Count migrated data
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM teams")  
                team_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM files")
                file_count = cursor.fetchone()[0]
                
                self.log(f"  Database contains:")
                self.log(f"    - {user_count} users")
                self.log(f"    - {team_count} teams")
                self.log(f"    - {file_count} files")
                
                # Test authentication with existing admin user
                cursor = conn.execute("SELECT * FROM users WHERE role = 'ADMIN' LIMIT 1")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    admin_dict = dict(admin_user)
                    self.log(f"  Found admin user: {admin_dict['username']}")
                    
                    # Show sample of teams
                    cursor = conn.execute("SELECT team_id, team_name FROM teams LIMIT 5")
                    teams = cursor.fetchall()
                    self.log(f"  Sample teams:")
                    for team in teams:
                        self.log(f"    - {team[0]}: {team[1]}")
                        
                else:
                    self.log("  WARNING: No admin users found")
                
                return True
                
            finally:
                conn.close()
                
        except Exception as e:
            self.log(f"System test failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate migration report - Unicode safe"""
        report = []
        report.append("=" * 60)
        report.append("KMTI HYBRID MIGRATION REPORT")
        report.append("=" * 60)
        report.append(f"Migration Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Database Location: {self.target_db_path}")
        report.append(f"NAS Available: {'Yes' if self.nas_available else 'No'}")
        
        if self.backup_dir:
            report.append(f"Backup Location: {self.backup_dir}")
        
        report.append("")
        report.append("MIGRATION LOG:")
        report.append("-" * 40)
        
        for log_entry in self.migration_log:
            report.append(log_entry)
        
        report.append("")
        report.append("NEXT STEPS:")
        report.append("-" * 40)
        report.append("1. Update your main.py to use the hybrid system")
        report.append("2. Test login functionality")
        report.append("3. Verify file approval workflow")
        report.append("4. Train team leaders on new features")
        
        if self.nas_available:
            report.append("5. Monitor NAS performance and connectivity")
        
        return "\n".join(report)
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        self.log("Starting KMTI Hybrid Migration")
        self.log("=" * 50)
        
        # Step 1: Create backup
        if not self.create_backup():
            self.log("Migration aborted - backup failed")
            return False
        
        # Step 2: Setup hybrid system
        if not self.setup_hybrid_system():
            self.log("Migration aborted - hybrid system setup failed")
            return False
        
        # Step 3: Migrate data
        migration_steps = [
            ("users", self.migrate_users),
            ("teams", self.migrate_teams), 
            ("files", self.migrate_files)
        ]
        
        for step_name, step_function in migration_steps:
            self.log(f"Starting {step_name} migration...")
            if not step_function():
                self.log(f"Migration failed at step: {step_name}")
                return False
        
        # Step 4: Create migration flag
        if not self.create_migration_flag():
            self.log("Migration completed but flag creation failed")
        
        # Step 5: Test system
        if not self.test_hybrid_system():
            self.log("Migration completed but system test failed")
        
        self.log("Migration completed successfully!")
        return True

def main():
    """Main migration function"""
    print("KMTI Hybrid Migration Tool - Fixed Version")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("ERROR: Please run this script from the KMTI project root directory")
        print("   (The directory containing main.py)")
        return False
    
    # Check if hybrid_manager.py exists
    if not Path("core/hybrid_manager.py").exists():
        print("ERROR: hybrid_manager.py not found")
        print("   Please copy hybrid_manager.py to the core/ directory first")
        return False
    
    # Show current teams.json format
    teams_file = Path("data/teams.json")
    if teams_file.exists():
        try:
            with open(teams_file, 'r', encoding='utf-8') as f:
                teams_data = json.load(f)
            print(f"\nDETECTED: teams.json format: {type(teams_data).__name__}")
            if isinstance(teams_data, list):
                print(f"   Contains {len(teams_data)} items (list format)")
                if teams_data:
                    print(f"   Sample item: {teams_data[0]}")
            elif isinstance(teams_data, dict):
                print(f"   Contains {len(teams_data)} items (dict format)")
                if teams_data:
                    sample_key = list(teams_data.keys())[0]
                    print(f"   Sample: {sample_key} -> {teams_data[sample_key]}")
        except Exception as e:
            print(f"   Could not read teams.json: {e}")
    
    # Confirm migration
    response = input("\nThis will migrate your KMTI system to hybrid architecture. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled by user")
        return False
    
    # Run migration
    migrator = KMTIMigrator()
    success = migrator.run_migration()
    
    # Generate and save report
    report_content = migrator.generate_report()
    
    # Save report to file with UTF-8 encoding
    try:
        report_file = Path("migration_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"\nMigration report saved to: {report_file}")
    except Exception as e:
        print(f"\nFailed to save report: {e}")
        # Try to save without problematic characters
        try:
            with open(report_file, 'w', encoding='ascii', errors='replace') as f:
                f.write(report_content)
            print(f"Report saved with ASCII encoding: {report_file}")
        except Exception as e2:
            print(f"Could not save report at all: {e2}")
    
    # Display summary
    print("\n" + "=" * 60)
    if success:
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("\nYour KMTI system is now ready to use hybrid architecture")
        print("\nNext steps:")
        print("   1. Replace your main.py with the hybrid version")
        print("   2. Test user login functionality")  
        print("   3. Verify admin panel and file approval features")
        print("   4. Train team leaders on new role-based access")
        
        if migrator.nas_available:
            print("   5. Monitor NAS connectivity and performance")
    else:
        print("MIGRATION FAILED")
        print("\nPlease check the error messages above")
        print("   Your original data remains unchanged in the backup")
        print("   You can safely retry the migration after fixing issues")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user (Ctrl+C)")
        exit_code = 2
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        exit_code = 3
    
    input("\nPress Enter to exit...")
    sys.exit(exit_code)