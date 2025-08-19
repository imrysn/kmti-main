"""
Admin Access Request Processor for KMTI File Approval System
Handles manual file movements when admin lacks network access
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from services.enhanced_file_movement_service import get_enhanced_file_movement_service
from utils.path_config import DATA_PATHS
from utils.logger import log_action

class AdminRequestProcessor:
    """Processes admin access requests for manual file movements"""
    
    def __init__(self):
        self.requests_dir = os.path.join(DATA_PATHS.NETWORK_BASE, "admin_access_requests")
        self.movement_service = get_enhanced_file_movement_service()
        
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending access requests"""
        return self.movement_service.get_pending_access_requests()
    
    def display_pending_requests(self):
        """Display pending requests in a user-friendly format"""
        requests = self.get_pending_requests()
        
        if not requests:
            print("✅ No pending access requests found")
            return
        
        print(f"\n📋 Found {len(requests)} pending access requests:")
        print("=" * 80)
        
        for i, request in enumerate(requests, 1):
            file_data = request.get('file_data', {})
            print(f"\n{i}. REQUEST ID: {request.get('request_id', 'Unknown')}")
            print(f"   📁 File: {file_data.get('original_filename', 'Unknown')}")
            print(f"   👤 User: {file_data.get('user_id', 'Unknown')}")
            print(f"   🏢 Team: {file_data.get('user_team', 'Unknown')}")
            print(f"   📅 Created: {request.get('created_date', 'Unknown')}")
            print(f"   🎯 Target: {request.get('target_path', 'Unknown')}")
            print(f"   ❌ Error: {request.get('error_message', 'Unknown')}")
            print(f"   📍 Source: {file_data.get('file_path', 'Unknown')}")
            
            # Check if source file still exists
            source_path = file_data.get('file_path', '')
            if source_path and os.path.exists(source_path):
                print(f"   ✅ Source file exists")
            else:
                print(f"   ❌ Source file missing or moved")
        
        print("\n" + "=" * 80)
    
    def process_request_manually(self, request_id: str, admin_user: str) -> bool:
        """
        Manually process a specific request
        This assumes the admin has manually moved the file and wants to update the status
        """
        try:
            request_file = os.path.join(self.requests_dir, f"{request_id}.json")
            
            if not os.path.exists(request_file):
                print(f"❌ Request file not found: {request_id}")
                return False
            
            # Load request
            with open(request_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            if request_data.get('status') != 'pending_manual_move':
                print(f"❌ Request {request_id} is not in pending status")
                return False
            
            file_data = request_data.get('file_data', {})
            target_path = request_data.get('target_path', '')
            
            # Ask admin to confirm the manual move
            print(f"\n🔄 Processing request: {request_id}")
            print(f"📁 File: {file_data.get('original_filename', 'Unknown')}")
            print(f"🎯 Expected location: {target_path}")
            print(f"📋 Instructions:")
            for key, instruction in request_data.get('instructions', {}).items():
                print(f"   {key}: {instruction}")
            
            confirm = input(f"\n✅ Have you manually moved the file to the correct location? (y/N): ").strip().lower()
            
            if confirm == 'y':
                # Update request status
                request_data['status'] = 'manually_completed'
                request_data['completed_by'] = admin_user
                request_data['completed_date'] = datetime.now().isoformat()
                request_data['completion_method'] = 'manual'
                
                # Save updated request
                with open(request_file, 'w', encoding='utf-8') as f:
                    json.dump(request_data, f, indent=2)
                
                # Log completion
                log_action(admin_user, f"Manually completed file move request: {request_id}")
                
                print(f"✅ Request {request_id} marked as manually completed")
                return True
            else:
                print("❌ Request not processed - admin did not confirm manual move")
                return False
                
        except Exception as e:
            print(f"❌ Error processing request {request_id}: {e}")
            return False
    
    def retry_automatic_move(self, request_id: str, admin_user: str) -> bool:
        """
        Retry automatic move for a request (if admin now has access)
        """
        try:
            request_file = os.path.join(self.requests_dir, f"{request_id}.json")
            
            if not os.path.exists(request_file):
                print(f"❌ Request file not found: {request_id}")
                return False
            
            # Load request
            with open(request_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            file_data = request_data.get('file_data', {})
            
            print(f"\n🔄 Retrying automatic move for: {request_id}")
            print(f"📁 File: {file_data.get('original_filename', 'Unknown')}")
            
            # Try the automatic move again
            move_success, move_message, new_file_path = self.movement_service.move_approved_file_with_access_management(
                file_data, admin_user)
            
            if move_success:
                # Update request status
                request_data['status'] = 'automatically_completed'
                request_data['completed_by'] = admin_user
                request_data['completed_date'] = datetime.now().isoformat()
                request_data['completion_method'] = 'automatic_retry'
                request_data['final_path'] = new_file_path
                request_data['success_message'] = move_message
                
                # Save updated request
                with open(request_file, 'w', encoding='utf-8') as f:
                    json.dump(request_data, f, indent=2)
                
                # Log completion
                log_action(admin_user, f"Successfully retried automatic move for request: {request_id}")
                
                print(f"✅ Automatic move successful: {move_message}")
                return True
            else:
                print(f"❌ Automatic move still failed: {move_message}")
                return False
                
        except Exception as e:
            print(f"❌ Error retrying automatic move for {request_id}: {e}")
            return False
    
    def cleanup_completed_requests(self, days_old: int = 30) -> int:
        """Clean up completed requests older than specified days"""
        try:
            if not os.path.exists(self.requests_dir):
                return 0
            
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for filename in os.listdir(self.requests_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.requests_dir, filename)
                    
                    try:
                        # Check file modification time
                        if os.path.getmtime(file_path) < cutoff_date:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                request_data = json.load(f)
                            
                            # Only delete completed requests
                            if request_data.get('status') in ['manually_completed', 'automatically_completed']:
                                os.remove(file_path)
                                cleaned_count += 1
                                print(f"🗑️ Cleaned up old request: {filename}")
                    
                    except Exception as e:
                        print(f"Warning: Error processing {filename}: {e}")
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up requests: {e}")
            return 0


def main():
    """Main function for interactive processing"""
    processor = AdminRequestProcessor()
    
    print("KMTI Admin Access Request Processor")
    print("=" * 50)
    
    while True:
        print("\n📋 MENU:")
        print("1. 📋 View pending requests")
        print("2. ✅ Mark request as manually completed")
        print("3. 🔄 Retry automatic move")
        print("4. 🗑️ Clean up old completed requests")
        print("5. 🚪 Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            processor.display_pending_requests()
        
        elif choice == '2':
            processor.display_pending_requests()
            requests = processor.get_pending_requests()
            
            if requests:
                request_id = input("\nEnter request ID to mark as completed: ").strip()
                admin_user = input("Enter your admin username: ").strip()
                
                if request_id and admin_user:
                    processor.process_request_manually(request_id, admin_user)
                else:
                    print("❌ Request ID and admin username are required")
        
        elif choice == '3':
            processor.display_pending_requests()
            requests = processor.get_pending_requests()
            
            if requests:
                request_id = input("\nEnter request ID to retry automatic move: ").strip()
                admin_user = input("Enter your admin username: ").strip()
                
                if request_id and admin_user:
                    processor.retry_automatic_move(request_id, admin_user)
                else:
                    print("❌ Request ID and admin username are required")
        
        elif choice == '4':
            days = input("Clean up requests older than how many days? (default: 30): ").strip()
            try:
                days_old = int(days) if days else 30
                cleaned = processor.cleanup_completed_requests(days_old)
                print(f"✅ Cleaned up {cleaned} old completed requests")
            except ValueError:
                print("❌ Invalid number of days")
        
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-5.")


if __name__ == "__main__":
    main()
