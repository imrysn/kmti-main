#!/usr/bin/env python3
"""
KMTI Test Setup Script
=====================

Prepares the KMTI system for comprehensive testing by:
- Backing up existing data
- Creating clean test environment  
- Verifying system prerequisites
- Initializing test data structures

Run this before executing the test suite for best results.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
import subprocess

class KMTITestSetup:
    """KMTI test environment setup manager"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "test_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_data_dir = self.project_root / "test_data"
        
    def run_setup(self, backup_existing=True, clean_install=False):
        """Run complete test setup process"""
        
        print("🛠️  KMTI Test Environment Setup")
        print("=" * 50)
        
        try:
            # Step 1: Prerequisites check
            if not self._check_prerequisites():
                print("❌ Prerequisites check failed")
                return False
            
            # Step 2: Backup existing data
            if backup_existing:
                if not self._backup_existing_data():
                    print("❌ Backup failed")
                    return False
            
            # Step 3: Clean existing test data
            if clean_install:
                self._clean_test_environment()
            
            # Step 4: Create test directories
            if not self._create_test_directories():
                print("❌ Test directory creation failed") 
                return False
            
            # Step 5: Initialize test data
            if not self._initialize_test_data():
                print("❌ Test data initialization failed")
                return False
            
            # Step 6: Verify setup
            if not self._verify_setup():
                print("❌ Setup verification failed")
                return False
            
            print("\n✅ Test environment setup complete!")
            self._print_next_steps()
            return True
            
        except Exception as e:
            print(f"💥 Setup failed with error: {e}")
            return False
    
    def _check_prerequisites(self):
        """Check system prerequisites"""
        print("\n1. 🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("   ❌ Python 3.8+ required")
            return False
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check required modules
        required_modules = ['json', 'uuid', 'hashlib', 'pathlib', 'datetime', 'concurrent.futures']
        for module in required_modules:
            try:
                __import__(module)
                print(f"   ✅ {module}")
            except ImportError:
                print(f"   ❌ Missing module: {module}")
                return False
        
        # Check disk space (need at least 50MB)
        try:
            total, used, free = shutil.disk_usage(".")
            free_mb = free / (1024 * 1024)
            if free_mb < 50:
                print(f"   ❌ Insufficient disk space: {free_mb:.1f}MB (need 50MB)")
                return False
            print(f"   ✅ Disk space: {free_mb:.1f}MB available")
        except Exception:
            print("   ⚠️  Could not check disk space")
        
        # Check write permissions
        try:
            test_file = Path("setup_test.tmp")
            test_file.write_text("test")
            test_file.unlink()
            print("   ✅ Write permissions")
        except Exception:
            print("   ❌ No write permissions")
            return False
        
        return True
    
    def _backup_existing_data(self):
        """Backup existing data files"""
        print("\n2. 💾 Backing up existing data...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Files to backup
            backup_files = [
                "data/config.json",
                "data/logs/system.log",
                "data/sessions",
                "data/uploads"
            ]
            
            backed_up_count = 0
            for file_path in backup_files:
                source = self.project_root / file_path
                if source.exists():
                    dest = self.backup_dir / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest)
                    
                    backed_up_count += 1
                    print(f"   ✅ Backed up: {file_path}")
            
            if backed_up_count > 0:
                print(f"   📁 Backup location: {self.backup_dir}")
            else:
                print("   ℹ️  No existing data to backup")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Backup error: {e}")
            return False
    
    def _clean_test_environment(self):
        """Clean existing test data"""
        print("\n3. 🧹 Cleaning test environment...")
        
        # Remove existing test data
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
            print("   ✅ Removed existing test data")
        
        # Remove test result files
        result_files = ["kmti_test_results.log", "test_report.txt"]
        for file in result_files:
            file_path = self.project_root / file
            if file_path.exists():
                file_path.unlink()
                print(f"   ✅ Removed: {file}")
    
    def _create_test_directories(self):
        """Create necessary test directories"""
        print("\n4. 📁 Creating test directories...")
        
        try:
            # Main directories
            directories = [
                self.test_data_dir,
                self.test_data_dir / "uploads",
                self.test_data_dir / "logs", 
                self.test_data_dir / "sessions",
                self.test_data_dir / "approvals",
                self.test_data_dir / "approvals" / "archived",
                self.test_data_dir / "user_approvals",
                self.test_data_dir / "test_files",
                self.test_data_dir / "temp"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Created: {directory.name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Directory creation error: {e}")
            return False
    
    def _initialize_test_data(self):
        """Initialize test data structures"""
        print("\n5. 📋 Initializing test data...")
        
        try:
            # Create test users
            test_users = {
                "admin@kmti.test": {
                    "username": "test_admin",
                    "password": hashlib.sha256("admin_password_123".encode()).hexdigest(),
                    "fullname": "Test Administrator", 
                    "role": "ADMIN",
                    "team_tags": ["ALL"]
                },
                "teamlead@kmti.test": {
                    "username": "test_teamlead",
                    "password": hashlib.sha256("tl_password_123".encode()).hexdigest(),
                    "fullname": "Test Team Leader",
                    "role": "TEAM_LEADER", 
                    "team_tags": ["ENGINEERING"]
                },
                "user@kmti.test": {
                    "username": "test_user",
                    "password": hashlib.sha256("user_password_123".encode()).hexdigest(),
                    "fullname": "Test User",
                    "role": "USER",
                    "team_tags": ["ENGINEERING"]
                },
                "user2@kmti.test": {
                    "username": "test_user2", 
                    "password": hashlib.sha256("user2_password_123".encode()).hexdigest(),
                    "fullname": "Test User 2",
                    "role": "USER",
                    "team_tags": ["DESIGN"]
                }
            }
            
            users_file = self.test_data_dir / "test_users.json"
            with open(users_file, 'w') as f:
                json.dump(test_users, f, indent=2)
            print("   ✅ Created test users")
            
            # Create test configuration
            test_config = {
                "base_dir": str(self.test_data_dir),
                "network_base": r"\\TEST-NAS\Shared\data",
                "max_file_size": 100 * 1024 * 1024,  # 100MB
                "allowed_extensions": [".pdf", ".docx", ".dwg", ".png", ".zip", ".txt"],
                "session_timeout": 3600,
                "test_mode": True
            }
            
            config_file = self.test_data_dir / "test_config.json"
            with open(config_file, 'w') as f:
                json.dump(test_config, f, indent=2)
            print("   ✅ Created test configuration")
            
            # Create sample test files
            test_files = {
                "test_document.pdf": b"Mock PDF content for testing purposes",
                "design_file.dwg": b"Mock DWG file content for CAD testing",
                "project_spec.docx": b"Mock DOCX content for document testing", 
                "test_image.png": b"Mock PNG image data for image testing",
                "large_file.zip": b"Large file content for performance testing " * 1000  # ~34KB
            }
            
            test_files_dir = self.test_data_dir / "test_files"
            for filename, content in test_files.items():
                file_path = test_files_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(content)
                print(f"   ✅ Created sample file: {filename}")
            
            # Create empty approval structures
            approval_queue_file = self.test_data_dir / "approvals" / "file_approvals.json"
            with open(approval_queue_file, 'w') as f:
                json.dump({}, f, indent=2)
            print("   ✅ Created approval queue structure")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Test data initialization error: {e}")
            return False
    
    def _verify_setup(self):
        """Verify the setup was successful"""
        print("\n6. ✅ Verifying setup...")
        
        try:
            # Check critical files exist
            critical_files = [
                self.test_data_dir / "test_users.json",
                self.test_data_dir / "test_config.json", 
                self.test_data_dir / "test_files" / "test_document.pdf",
                self.test_data_dir / "approvals" / "file_approvals.json"
            ]
            
            for file_path in critical_files:
                if not file_path.exists():
                    print(f"   ❌ Missing critical file: {file_path}")
                    return False
                print(f"   ✅ Verified: {file_path.name}")
            
            # Check directory structure
            critical_dirs = [
                self.test_data_dir / "uploads",
                self.test_data_dir / "logs",
                self.test_data_dir / "sessions",
                self.test_data_dir / "approvals" / "archived"
            ]
            
            for dir_path in critical_dirs:
                if not dir_path.exists():
                    print(f"   ❌ Missing directory: {dir_path}")
                    return False
                print(f"   ✅ Verified: {dir_path.name}/")
            
            # Test JSON parsing
            with open(self.test_data_dir / "test_users.json", 'r') as f:
                users_data = json.load(f)
            
            if len(users_data) != 4:
                print("   ❌ Test users data incomplete")
                return False
            print("   ✅ Test users data valid")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Verification error: {e}")
            return False
    
    def _print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "=" * 50)
        print("🚀 READY FOR TESTING")
        print("=" * 50)
        
        print("\n📋 Test Environment Summary:")
        print(f"   • Test data directory: {self.test_data_dir}")
        print(f"   • Test users: 4 accounts (admin, team leader, 2 users)")
        print(f"   • Sample files: 5 test files created")
        print(f"   • Backup location: {self.backup_dir}")
        
        print("\n🧪 Recommended Test Sequence:")
        print("   1. python validate_test_suite.py     # Validate setup")
        print("   2. python run_kmti_tests.py --smoke  # Quick smoke test")
        print("   3. python run_kmti_tests.py --quick  # Essential tests")
        print("   4. python run_kmti_tests.py          # Full test suite")
        
        print("\n📊 Test Results Will Be Available In:")
        print("   • Console output (real-time progress)")
        print("   • kmti_test_results.log (detailed log)")
        print("   • test_data/test_report.txt (summary report)")
        
        print("\n🔧 Troubleshooting:")
        print("   • If tests fail, check the detailed log file")
        print("   • Use --verbose flag for additional debugging")
        print("   • Test data can be recreated by re-running this setup")


def main():
    """Main setup function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='KMTI Test Environment Setup')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backing up existing data')
    parser.add_argument('--clean', action='store_true',
                       help='Perform clean installation (remove existing test data)')
    parser.add_argument('--force', action='store_true', 
                       help='Force setup even if validation fails')
    
    args = parser.parse_args()
    
    try:
        setup = KMTITestSetup()
        
        # Run setup
        success = setup.run_setup(
            backup_existing=not args.no_backup,
            clean_install=args.clean
        )
        
        if success:
            print("\n🎉 Setup completed successfully!")
            
            # Offer to run validation
            if not args.force:
                response = input("\nWould you like to run validation now? (y/N): ").strip().lower()
                if response == 'y':
                    print("\n" + "=" * 50)
                    result = subprocess.run([sys.executable, "validate_test_suite.py"], 
                                          capture_output=False)
                    if result.returncode == 0:
                        print("\n🎯 System is ready for testing!")
                    else:
                        print("\n⚠️  Validation found issues - please review")
            
            return 0
        else:
            print("\n❌ Setup failed - please review errors above")
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 Setup error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
