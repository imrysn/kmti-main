#!/usr/bin/env python3
"""
User Role Diagnostic Script

This script helps diagnose role-related issues by:
1. Checking which users file exists
2. Listing all users and their roles  
3. Testing role validation for a specific user
4. Providing role normalization debug info
"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_users_files():
    """Check which users files exist and their contents"""
    print("🔍 Checking Users Files...\n")
    
    # Possible users file locations
    possible_paths = [
        r"\\KMTI-NAS\Shared\data\users.json",  # Network path (from auth.py)
        "data/users.json",  # Local path (fallback)
        os.path.abspath("data/users.json"),  # Absolute local path
    ]
    
    for path in possible_paths:
        print(f"Checking: {path}")
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    users = json.load(f)
                print(f"  ✅ EXISTS - {len(users)} users found")
                print(f"  📁 Path: {os.path.abspath(path)}")
                
                # Show users and roles
                print(f"  👥 Users:")
                for email, data in users.items():
                    username = data.get('username', 'N/A')
                    role = data.get('role', 'N/A')
                    print(f"    • {username} ({email}): {role}")
                
            except Exception as e:
                print(f"  ❌ ERROR reading file: {e}")
        else:
            print(f"  ❌ NOT FOUND")
        print()

def test_user_role(test_username):
    """Test role validation for specific user"""
    print(f"🧪 Testing Role Validation for: {test_username}\n")
    
    try:
        from utils.auth import load_users, validate_login
        
        print("Loading users...")
        users = load_users()
        print(f"Loaded {len(users)} users from load_users()")
        
        # Find user
        found_user = None
        for email, data in users.items():
            if data.get('username') == test_username:
                found_user = (email, data)
                break
        
        if found_user:
            email, data = found_user
            raw_role = data.get('role', 'N/A')
            normalized_role = raw_role.upper()
            
            print(f"✅ User found:")
            print(f"  Email: {email}")
            print(f"  Username: {data.get('username')}")
            print(f"  Raw role: '{raw_role}'")
            print(f"  Uppercase role: '{normalized_role}'")
            
            # Test role normalization
            if normalized_role == "TEAM LEADER":
                final_role = "TEAM_LEADER"
            else:
                final_role = normalized_role
            print(f"  Final normalized role: '{final_role}'")
            
            # Test login validation  
            print(f"\n🔑 Testing login validation:")
            test_passwords = ["tl123", "password123"]  # Common test passwords
            
            for pwd in test_passwords:
                try:
                    admin_result = validate_login(test_username, pwd, True)
                    user_result = validate_login(test_username, pwd, False)
                    print(f"  Password '{pwd}':")
                    print(f"    Admin login: {admin_result}")
                    print(f"    User login: {user_result}")
                    
                    if admin_result or user_result:
                        print(f"    ✅ Login works with password: {pwd}")
                        break
                except Exception as e:
                    print(f"    ❌ Login error: {e}")
                    
        else:
            print(f"❌ User '{test_username}' not found")
            print("Available usernames:")
            for email, data in users.items():
                print(f"  • {data.get('username', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error testing user role: {e}")
        import traceback
        traceback.print_exc()

def check_role_normalization():
    """Test role normalization logic"""
    print("🔧 Testing Role Normalization Logic...\n")
    
    test_roles = [
        "ADMIN",
        "USER", 
        "TEAM_LEADER",
        "TEAM LEADER",
        "team_leader",
        "team leader",
        "Team Leader",
        "TeamLeader"
    ]
    
    for role in test_roles:
        upper_role = role.upper()
        if upper_role == "TEAM LEADER":
            normalized = "TEAM_LEADER"
        else:
            normalized = upper_role
            
        print(f"'{role}' → '{upper_role}' → '{normalized}'")

def create_test_user():
    """Create a test TEAM_LEADER user for debugging"""
    print("🛠️ Creating Test TEAM_LEADER User...\n")
    
    try:
        # Use the same USERS_FILE as auth.py
        from utils.auth import load_users, hash_password
        
        users = load_users()
        
        test_user = {
            "username": "testTL",
            "password": hash_password("test123"),
            "fullname": "Test Team Leader",
            "role": "TEAM_LEADER",
            "team_tags": ["KUSAKABE"],
            "created_date": "2025-01-15T10:00:00"
        }
        
        users["testtl@kmti.com"] = test_user
        
        # Try to save to the same file that load_users() reads from
        USERS_FILE = r"\\KMTI-NAS\Shared\data\users.json"
        
        try:
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f, indent=4)
            print(f"✅ Created test user in: {USERS_FILE}")
        except Exception as e:
            # Fallback to local file
            local_file = "data/users.json"
            os.makedirs("data", exist_ok=True)
            with open(local_file, 'w') as f:
                json.dump(users, f, indent=4)
            print(f"✅ Created test user in: {local_file}")
            print(f"⚠️  Could not write to network path: {e}")
        
        print("Test user credentials:")
        print("  Username: testTL")  
        print("  Password: test123")
        print("  Role: TEAM_LEADER")
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")

if __name__ == "__main__":
    print("🔧 User Role Diagnostic Tool\n")
    print("="*50)
    
    check_users_files()
    print("="*50)
    
    check_role_normalization()
    print("="*50)
    
    # Test the specific user that's having issues
    test_user_role("tl")
    print("="*50)
    
    # Offer to create a test user
    create_test = input("Create test TEAM_LEADER user? (y/n): ")
    if create_test.lower() == 'y':
        create_test_user()
        
    print("\n🎯 Summary:")
    print("1. Check if your user exists in the correct users.json file")
    print("2. Verify the role is exactly 'TEAM_LEADER' (with underscore)")  
    print("3. Test login with the credentials you created")
    print("4. If issues persist, use the test user: testTL/test123")
