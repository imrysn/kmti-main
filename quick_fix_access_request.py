"""
Quick Fix Script for Current Access Request
Handles the immediate CP91024U01_PCMU.icd file move issue
"""

import os
import shutil
from datetime import datetime
from services.enhanced_file_movement_service import get_enhanced_file_movement_service
from utils.path_config import DATA_PATHS

def fix_current_request():
    """Fix the current pending request for CP91024U01_PCMU.icd"""
    print("KMTI Quick Fix - Current Access Request")
    print("=" * 50)
    
    # Get pending requests
    service = get_enhanced_file_movement_service()
    requests = service.get_pending_access_requests()
    
    if not requests:
        print("✅ No pending access requests found")
        return
    
    print(f"Found {len(requests)} pending access requests:")
    
    for i, request in enumerate(requests, 1):
        file_data = request.get('file_data', {})
        filename = file_data.get('original_filename', 'Unknown')
        user = file_data.get('user_id', 'Unknown')
        team = file_data.get('user_team', 'Unknown')
        
        print(f"\n{i}. File: {filename}")
        print(f"   User: {user}")
        print(f"   Team: {team}")
        print(f"   Request ID: {request.get('request_id', 'Unknown')}")
        print(f"   Source: {file_data.get('file_path', 'Unknown')}")
        print(f"   Target: {request.get('target_path', 'Unknown')}")
    
    # Focus on the PCMU.icd file if present
    pcmu_request = None
    for request in requests:
        file_data = request.get('file_data', {})
        if 'CP91024U01_PCMU.icd' in file_data.get('original_filename', ''):
            pcmu_request = request
            break
    
    if pcmu_request:
        print(f"\n🎯 Found the CP91024U01_PCMU.icd request!")
        handle_pcmu_request(pcmu_request)
    else:
        print(f"\n❓ CP91024U01_PCMU.icd request not found in pending requests")
        print("The file may have already been processed or the request wasn't created properly")
    
    print("\n" + "=" * 50)
    print("For manual processing of other requests, run:")
    print("python process_admin_requests.py")

def handle_pcmu_request(request):
    """Handle the specific PCMU request"""
    file_data = request.get('file_data', {})
    source_file = file_data.get('file_path', '')
    target_dir = request.get('target_path', '')
    filename = file_data.get('original_filename', '')
    
    print(f"\n📁 Processing: {filename}")
    print(f"🗂️ Source: {source_file}")
    print(f"🎯 Target Directory: {target_dir}")
    
    # Check if source file still exists
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        print("   The file may have already been moved or deleted")
        return
    
    print(f"✅ Source file exists")
    
    # Manual move options
    print(f"\n🔧 MANUAL MOVE OPTIONS:")
    print(f"1. Copy the file manually:")
    print(f"   From: {source_file}")
    print(f"   To: {target_dir}\\{filename}")
    print(f"")
    print(f"2. Alternative: Use fallback directory:")
    fallback_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "approved_files_staging", "KUSAKABE", "2025")
    print(f"   Target: {fallback_dir}\\{filename}")
    
    # Try fallback move automatically
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        fallback_file = os.path.join(fallback_dir, filename)
        
        print(f"\n🔄 Attempting automatic move to fallback directory...")
        shutil.copy2(source_file, fallback_file)
        print(f"✅ Successfully moved to fallback: {fallback_file}")
        
        # Create notification for admin
        create_manual_move_instruction(filename, fallback_file, target_dir)
        
        # Mark original source for cleanup (don't delete yet, just note)
        print(f"📝 Original file remains at: {source_file}")
        print(f"   You can delete it after confirming the fallback copy is good")
        
    except Exception as e:
        print(f"❌ Fallback move failed: {e}")
        print(f"   Manual copy required")

def create_manual_move_instruction(filename, fallback_path, target_dir):
    """Create instruction file for manual move completion"""
    try:
        instructions_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "manual_move_instructions")
        os.makedirs(instructions_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        instruction_file = os.path.join(instructions_dir, f"move_instruction_{timestamp}.txt")
        
        instructions = f"""KMTI Manual File Move Instructions
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

File: {filename}

STEP 1: Verify fallback file exists and is complete
Source: {fallback_path}

STEP 2: Create target directory if needed
Target Directory: {target_dir}

STEP 3: Copy file to final location
Final Location: {target_dir}\\{filename}

STEP 4: Verify file integrity
- Check file size matches original
- Verify file opens correctly

STEP 5: Mark as completed
Run: python process_admin_requests.py
Select option 2 (Mark as manually completed)

STEP 6: Clean up (optional)
- Delete fallback file: {fallback_path}
- Delete original if move was successful
"""
        
        with open(instruction_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print(f"📋 Created instruction file: {instruction_file}")
        
    except Exception as e:
        print(f"Warning: Could not create instruction file: {e}")

if __name__ == "__main__":
    fix_current_request()
