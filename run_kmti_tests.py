#!/usr/bin/env python3
"""
KMTI Test Runner - Simplified Test Interface
==========================================

Quick and easy way to run KMTI system tests with preset configurations.

Usage Examples:
  python run_kmti_tests.py                    # Run all tests
  python run_kmti_tests.py --quick            # Run essential tests only  
  python run_kmti_tests.py --component auth   # Test specific component
  python run_kmti_tests.py --smoke            # Basic smoke tests
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main test runner with simplified options"""
    
    # Get script directory
    script_dir = Path(__file__).parent
    main_test_script = script_dir / "kmti_comprehensive_test.py"
    
    if not main_test_script.exists():
        print("❌ Main test script not found: kmti_comprehensive_test.py")
        sys.exit(1)
    
    # Parse simple command line arguments
    args = sys.argv[1:]
    
    if not args or args[0] in ['-h', '--help', 'help']:
        print_help()
        return
    
    # Build command based on preset configurations
    cmd = [sys.executable, str(main_test_script)]
    
    if args[0] == '--quick':
        # Essential tests only
        cmd.extend(['--categories', 'auth_tests', 'file_management_tests', 'user_panel_tests'])
        print("🚀 Running QUICK test suite (essential functionality)...")
        
    elif args[0] == '--smoke':
        # Basic smoke tests
        cmd.extend(['--categories', 'auth_tests', 'data_integrity_tests'])  
        print("🔍 Running SMOKE tests (basic system health)...")
        
    elif args[0] == '--security':
        # Security-focused tests
        cmd.extend(['--categories', 'auth_tests', 'security_tests', 'error_handling_tests'])
        print("🔒 Running SECURITY tests...")
        
    elif args[0] == '--workflow':
        # Workflow-focused tests
        cmd.extend(['--categories', 'approval_workflow_tests', 'integration_tests'])
        print("🔄 Running WORKFLOW tests...")
        
    elif args[0] == '--performance':
        # Performance tests
        cmd.extend(['--categories', 'performance_tests', 'file_management_tests'])
        print("⚡ Running PERFORMANCE tests...")
        
    elif args[0] == '--admin':
        # Admin functionality
        cmd.extend(['--categories', 'admin_panel_tests', 'user_panel_tests', 'team_leader_tests'])
        print("👨‍💼 Running ADMIN functionality tests...")
        
    elif args[0] == '--component':
        if len(args) < 2:
            print("❌ --component requires component name")
            print("   Available: auth, files, approval, admin, teamlead, user")
            sys.exit(1)
        
        component = args[1].lower()
        component_map = {
            'auth': ['auth_tests', 'security_tests'],
            'files': ['file_management_tests'],
            'approval': ['approval_workflow_tests'], 
            'admin': ['admin_panel_tests'],
            'teamlead': ['team_leader_tests'],
            'user': ['user_panel_tests']
        }
        
        if component not in component_map:
            print(f"❌ Unknown component: {component}")
            print("   Available: auth, files, approval, admin, teamlead, user")
            sys.exit(1)
        
        cmd.extend(['--categories'] + component_map[component])
        print(f"🧩 Running {component.upper()} component tests...")
        
    elif args[0] == '--full':
        # Full comprehensive test suite
        print("🎯 Running FULL comprehensive test suite...")
        
    else:
        # Default: run all tests
        print("🎯 Running ALL tests (full comprehensive suite)...")
    
    # Add verbose flag if requested
    if '--verbose' in args or '-v' in args:
        cmd.append('--verbose')
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(3)


def print_help():
    """Print help information"""
    help_text = """
KMTI Test Runner - Simplified Test Interface
==========================================

USAGE:
  python run_kmti_tests.py [PRESET] [OPTIONS]

TEST PRESETS:
  --quick      Run essential tests only (~2-5 minutes)
               Tests: Authentication, File Management, User Panel
               
  --smoke      Basic smoke tests (~1-2 minutes)  
               Tests: Authentication, Data Integrity
               
  --security   Security-focused tests (~3-5 minutes)
               Tests: Authentication, Security, Error Handling
               
  --workflow   Approval workflow tests (~3-7 minutes)
               Tests: Approval Workflow, Integration
               
  --performance Performance tests (~5-10 minutes)
               Tests: Performance, File Management
               
  --admin      Admin functionality tests (~5-8 minutes)
               Tests: Admin Panel, User Panel, Team Leader
               
  --component  Test specific component
               Usage: --component [auth|files|approval|admin|teamlead|user]
               
  --full       Full comprehensive test suite (~15-30 minutes)
               Tests: All available test categories
               
  (no preset) Same as --full

OPTIONS:
  --verbose, -v    Verbose output with detailed logs
  --help, -h       Show this help message

EXAMPLES:
  python run_kmti_tests.py                    # Run all tests
  python run_kmti_tests.py --quick           # Quick essential tests
  python run_kmti_tests.py --component auth  # Just authentication tests  
  python run_kmti_tests.py --security -v     # Security tests with verbose output

TEST CATEGORIES:
  • Authentication Tests       - Login, password security, session management
  • File Management Tests      - Upload, download, metadata, security
  • Approval Workflow Tests    - Submission, team leader approval, admin approval
  • Admin Panel Tests          - User management, activity logs, system stats
  • Team Leader Tests          - Team file visibility, approval authority
  • User Panel Tests           - File listing, profile management, notifications
  • Data Integrity Tests       - Data consistency, backup integrity
  • Performance Tests          - Large files, concurrent users, query performance
  • Security Tests             - Path traversal, input validation, authentication
  • Error Handling Tests       - File system errors, database corruption, validation
  • Integration Tests          - End-to-end workflows, system startup/shutdown

OUTPUT:
  • Console output with real-time test progress
  • Detailed log file: kmti_test_results.log  
  • Test report: test_data/test_report.txt
  • Test data: test_data/ directory

For more detailed options, use the main test script directly:
  python kmti_comprehensive_test.py --help
"""
    print(help_text)


if __name__ == "__main__":
    main()
