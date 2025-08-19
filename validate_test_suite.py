#!/usr/bin/env python3
"""
KMTI Test Suite Validator
========================

Quick validation script to verify the test suite is properly set up and functional.
Run this before running the main test suite to catch configuration issues early.
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from datetime import datetime

def validate_test_environment():
    """Validate that the test environment is properly configured"""
    
    print("🔍 KMTI Test Suite Validator")
    print("=" * 50)
    
    issues = []
    warnings = []
    
    # Check 1: Python version
    print("1. Checking Python version...")
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ required")
        print("   ❌ Python version too old")
    else:
        print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check 2: Required files exist
    print("\n2. Checking test files...")
    required_files = [
        "kmti_comprehensive_test.py",
        "run_kmti_tests.py", 
        "TESTING_GUIDE.md"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            issues.append(f"Missing required file: {file}")
            print(f"   ❌ {file}")
    
    # Check 3: Main system files
    print("\n3. Checking main system files...")
    system_files = [
        "main.py",
        "utils/auth.py",
        "utils/file_manager.py",
        "services/approval_service.py",
        "admin/components/data_managers.py",
        "user/services/file_service.py"
    ]
    
    for file in system_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            warnings.append(f"System file not found: {file}")
            print(f"   ⚠️  {file}")
    
    # Check 4: Try importing key modules
    print("\n4. Checking module imports...")
    test_imports = [
        ("json", "JSON support"),
        ("uuid", "UUID generation"),
        ("hashlib", "Password hashing"),
        ("threading", "Threading support"),
        ("concurrent.futures", "Concurrent execution"),
        ("pathlib", "Path handling"),
        ("tempfile", "Temporary files"),
        ("unittest.mock", "Mocking support")
    ]
    
    for module, description in test_imports:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            issues.append(f"Missing required module: {module}")
            print(f"   ❌ {module} - {description}")
    
    # Check 5: Disk space
    print("\n5. Checking disk space...")
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_mb = free / (1024 * 1024)
        
        if free_mb < 100:
            warnings.append(f"Low disk space: {free_mb:.1f}MB available")
            print(f"   ⚠️  {free_mb:.1f}MB available (recommend 100MB+)")
        else:
            print(f"   ✅ {free_mb:.1f}MB available")
    except Exception as e:
        warnings.append(f"Could not check disk space: {e}")
        print(f"   ⚠️  Could not check disk space")
    
    # Check 6: Write permissions
    print("\n6. Checking write permissions...")
    try:
        test_file = Path("test_write_check.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("   ✅ Write permissions OK")
    except Exception as e:
        issues.append(f"No write permissions: {e}")
        print("   ❌ Write permissions failed")
    
    # Check 7: Test suite syntax
    print("\n7. Checking test suite syntax...")
    try:
        import ast
        
        test_files = ["kmti_comprehensive_test.py", "run_kmti_tests.py"]
        for test_file in test_files:
            if Path(test_file).exists():
                try:
                    with open(test_file, 'r') as f:
                        content = f.read()
                    ast.parse(content)
                    print(f"   ✅ {test_file} syntax OK")
                except SyntaxError as e:
                    issues.append(f"Syntax error in {test_file}: {e}")
                    print(f"   ❌ {test_file} syntax error")
    except Exception as e:
        warnings.append(f"Could not check syntax: {e}")
        print("   ⚠️  Could not check syntax")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    if not issues:
        print("✅ All critical checks passed!")
        if warnings:
            print(f"⚠️  {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"   • {warning}")
        else:
            print("✅ No warnings detected!")
        
        print("\n🚀 Test suite is ready to run!")
        print("\nNext steps:")
        print("  python run_kmti_tests.py --smoke      # Quick smoke test")
        print("  python run_kmti_tests.py --quick      # Essential tests") 
        print("  python run_kmti_tests.py              # Full test suite")
        return True
        
    else:
        print(f"❌ {len(issues)} critical issue(s) found:")
        for issue in issues:
            print(f"   • {issue}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"   • {warning}")
        
        print("\n🔧 Please fix the critical issues before running tests.")
        return False


def run_basic_test():
    """Run a very basic test to verify functionality"""
    
    print("\n🧪 Running Basic Functionality Test...")
    print("-" * 40)
    
    try:
        # Test 1: JSON handling
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        assert parsed_data["test"] == "data"
        print("   ✅ JSON handling works")
        
        # Test 2: File operations
        test_file = Path("basic_test.tmp")
        test_file.write_text("test content")
        content = test_file.read_text()
        test_file.unlink()
        assert content == "test content"
        print("   ✅ File operations work")
        
        # Test 3: Directory operations
        test_dir = Path("basic_test_dir")
        test_dir.mkdir(exist_ok=True)
        assert test_dir.exists()
        test_dir.rmdir()
        print("   ✅ Directory operations work")
        
        # Test 4: Hash generation (like password hashing)
        import hashlib
        test_hash = hashlib.sha256("test".encode()).hexdigest()
        assert len(test_hash) == 64
        print("   ✅ Hash generation works")
        
        print("\n✅ Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic functionality test failed: {e}")
        return False


def main():
    """Main validation function"""
    
    try:
        # Run validation
        validation_passed = validate_test_environment()
        
        if validation_passed:
            # Run basic test
            basic_test_passed = run_basic_test()
            
            if basic_test_passed:
                print(f"\n🎉 VALIDATION COMPLETE - All systems ready!")
                print(f"📅 Validated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return 0
            else:
                print(f"\n⚠️  Environment OK but basic functionality failed")
                return 2
        else:
            print(f"\n❌ Environment validation failed")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n❌ Validation interrupted by user")
        return 3
    except Exception as e:
        print(f"\n💥 Validation error: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
