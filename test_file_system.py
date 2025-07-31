#!/usr/bin/env python3
"""
Test script to verify file management system functionality
"""

import os
import sys

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user.services.file_service import FileService

def test_file_service():
    """Test the file service functionality"""
    print("🧪 Testing File Management System...")
    print("=" * 50)
    
    # Create test file service
    test_username = "test_user"
    test_folder = os.path.join("data", "uploads", test_username)
    
    # Ensure test folder exists
    os.makedirs(test_folder, exist_ok=True)
    
    file_service = FileService(test_folder, test_username)
    
    # Test 1: Get files (should be empty initially)
    print("📁 Test 1: Getting initial files...")
    files = file_service.get_files()
    print(f"   Found {len(files)} files")
    
    # Test 2: Create a dummy test file
    print("\n📄 Test 2: Creating test file...")
    test_file_path = os.path.join(test_folder, "test_document.txt")
    with open(test_file_path, 'w') as f:
        f.write("This is a test file for the KMTI file management system.")
    print(f"   Created: {test_file_path}")
    
    # Test 3: Scan for files
    print("\n🔍 Test 3: Scanning for files...")
    files = file_service.get_files()
    print(f"   Found {len(files)} files")
    for file_info in files:
        print(f"   - {file_info['name']} ({file_info['type']}, {file_info['size']})")
    
    # Test 4: Update file metadata
    if files:
        print("\n✏️  Test 4: Updating file metadata...")
        success = file_service.update_file_metadata(
            files[0]['name'], 
            "Test file for KMTI system verification",
            ["test", "demo", "verification"]
        )
        print(f"   Metadata update: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 5: Get file info
    if files:
        print("\n📊 Test 5: Getting detailed file info...")
        file_info = file_service.get_file_info(files[0]['name'])
        if file_info:
            print(f"   Name: {file_info['name']}")
            print(f"   Type: {file_info['type']}")
            print(f"   Size: {file_info['size']}")
            print(f"   Description: {file_info['description']}")
            print(f"   Tags: {', '.join(file_info['tags'])}")
        else:
            print("   ❌ Failed to get file info")
    
    print("\n🎉 File Management System Test Complete!")
    print("=" * 50)
    
    return len(files) > 0

if __name__ == "__main__":
    test_file_service()
