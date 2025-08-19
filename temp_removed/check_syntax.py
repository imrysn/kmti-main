#!/usr/bin/env python3
"""
Syntax Checker for KMTI Metadata Relocation Files
Validates Python syntax for all modified files
"""

import ast
import os
import sys

def check_python_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        return True, "✅ Syntax OK"
        
    except SyntaxError as e:
        return False, f"❌ Syntax Error: {e.msg} (line {e.lineno})"
    except Exception as e:
        return False, f"❌ Error reading file: {e}"

def main():
    """Check syntax of all metadata relocation related files"""
    
    print("🔍 KMTI Metadata Relocation - Syntax Check")
    print("=" * 60)
    
    files_to_check = [
        "utils/metadata_manager.py",
        "services/file_movement_service.py", 
        "services/enhanced_file_movement_service.py",
        "migrate_metadata_to_logs.py",
        "test_metadata_relocation.py"
    ]
    
    all_valid = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            valid, message = check_python_syntax(file_path)
            print(f"\n📄 {file_path}")
            print(f"   {message}")
            
            if not valid:
                all_valid = False
        else:
            print(f"\n📄 {file_path}")
            print(f"   ⚠️  File not found")
    
    print("\n" + "=" * 60)
    
    if all_valid:
        print("🎉 ALL FILES HAVE VALID SYNTAX!")
        print("✅ Ready to run metadata relocation")
        print("\nNext steps:")
        print("1. Run: python test_metadata_relocation.py")
        print("2. Run: python migrate_metadata_to_logs.py")
        return True
    else:
        print("❌ SYNTAX ERRORS DETECTED")
        print("Please fix the syntax errors before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
