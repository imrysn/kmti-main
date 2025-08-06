import flet as ft
from flet import Icons, Colors, FontWeight, TextAlign
import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from utils.approval import get_pending_files, approve_file, reject_file, add_comment, APPROVAL_QUEUE, APPROVED_DB, METADATA_FILE

class FileApprovalPanel:
    """File approval panel for reviewing and managing user file submissions"""
    
    def __init__(self, page: ft.Page, admin_username: str):
        self.page = page
        self.admin_username = admin_username
        self.approval_queue_path = APPROVAL_QUEUE
        self.approved_path = APPROVED_DB
        self.metadata_path = METADATA_FILE
        
        # Ensure directories exist
        os.makedirs(self.approval_queue_path, exist_ok=True)
        os.makedirs(self.approved_path, exist_ok=True)
        
        # Load metadata
        self.metadata = self.load_metadata()
        
        # Admin team tags
        self.admin_teams = self.get_admin_teams()
        
    def load_metadata(self) -> Dict:
        """Load approval metadata from JSON"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_metadata(self):
        """Save approval metadata to JSON"""
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f)
            
    def get_admin_teams(self) -> List[str]:
        """Get team tags for the current admin"""
        try:
            with open("data/users.json", "r") as f:
                users = json.load(f)
                for email, data in users.items():
                    if data.get("username") == self.admin_username:
                        return data.get("team_tags", [])
        except:
            return []
        return []
    
    def can_review_file(self, user_teams: List[str]) -> bool:
        """Check if admin can review files from this user based on team tags"""
        # Super admin can review all files
        if "SUPER_ADMIN" in self.admin_teams:
            return True
            
        # Check for team tag match
        return bool(set(self.admin_teams) & set(user_teams))
        
    def get_user_teams(self, username: str) -> List[str]:
        """Get team tags for a user"""
        try:
            with open("data/users.json", "r") as f:
                users = json.load(f)
                for email, data in users.items():
                    if data.get("username") == username:
                        return data.get("team_tags", [])
        except:
            return []
        return []

    def add_comment(self, file_id: str, comment: str):
        """Add a review comment to a file"""
        if file_id not in self.metadata:
            self.metadata[file_id] = {
                "comments": [],
                "status": "pending"
            }
            
        self.metadata[file_id]["comments"].append({
            "comment": comment,
            "admin": self.admin_username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_metadata()

    def approve_file(self, filename: str, user_folder: str):
        """Approve and move file to public database"""
        src_path = os.path.join(self.approval_queue_path, user_folder, filename)
        
        try:
            # Check if this is a profile image
            file_id = f"{user_folder}/{filename}"
            metadata = self.metadata.get(file_id, {})
            is_profile = metadata.get("is_profile", False)
            
            if is_profile:
                # For profile images, move to profiles subdirectory
                dst_path = os.path.join(self.approved_path, "profiles", filename)
            else:
                # For regular files, move to public database root
                dst_path = os.path.join(self.approved_path, filename)
            
            # Move file to approved directory
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            os.rename(src_path, dst_path)
            
            # Update metadata
            if file_id not in self.metadata:
                self.metadata[file_id] = {}
            
            self.metadata[file_id].update({
                "status": "approved",
                "approved_by": self.admin_username,
                "approved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "approved_path": dst_path
            })
            self.save_metadata()
            return True
            
        except Exception as e:
            print(f"Error approving file: {e}")
            return False

    def reject_file(self, filename: str, user_folder: str, reason: str):
        """Reject file with reason"""
        file_id = f"{user_folder}/{filename}"
        if file_id not in self.metadata:
            self.metadata[file_id] = {}
            
        self.metadata[file_id].update({
            "status": "rejected",
            "rejected_by": self.admin_username,
            "rejected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rejection_reason": reason
        })
        self.save_metadata()

    def create_file_card(self, filename: str, user_folder: str) -> ft.Card:
        """Create a card view for a file pending approval"""
        file_id = f"{user_folder}/{filename}"
        metadata = self.metadata.get(file_id, {})
        
        # Check if this is a profile image
        is_profile = metadata.get("is_profile", False)
        file_type = metadata.get("type", "file")
        
        icon = Icons.ACCOUNT_CIRCLE if is_profile else Icons.INSERT_DRIVE_FILE
        type_badge = "(Profile Image)" if is_profile else f"({file_type})"
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # File info header
                    ft.Row([
                        ft.Icon(icon, color=Colors.BLUE_600 if is_profile else Colors.GREY_700),
                        ft.Text(filename, weight=ft.FontWeight.BOLD),
                        ft.Text(type_badge, color=Colors.GREY_700, italic=True),
                        ft.Text(f"Uploaded by: {user_folder}", color=Colors.GREY_700)
                    ]),
                    
                    # Comments section
                    ft.Column([
                        ft.Text("Comments:", weight=ft.FontWeight.BOLD),
                        ft.ListView([
                            ft.Text(f"{c['admin']}: {c['comment']}", size=12) 
                            for c in metadata.get("comments", [])
                        ], height=100, spacing=5)
                    ]),
                    
                    # Comment input
                    ft.TextField(
                        hint_text="Add comment...",
                        on_submit=lambda e: self.add_comment(file_id, e.control.value)
                    ),
                    
                    # Action buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "Open File",
                            icon=Icons.OPEN_IN_NEW,
                            on_click=lambda _: os.startfile(
                                os.path.join(self.approval_queue_path, user_folder, filename)
                            )
                        ),
                        ft.ElevatedButton(
                            "Approve",
                            icon=Icons.CHECK_CIRCLE,
                            bgcolor=Colors.GREEN,
                            color=Colors.WHITE,
                            on_click=lambda _: self.approve_file(filename, user_folder)
                        ),
                        ft.ElevatedButton(
                            "Reject",
                            icon=Icons.CANCEL,
                            bgcolor=Colors.RED,
                            color=Colors.WHITE,
                            on_click=lambda _: self.reject_file(filename, user_folder, 
                                "Rejected by " + self.admin_username)
                        )
                    ], alignment=ft.MainAxisAlignment.END)
                ]),
                padding=20
            )
        )

    def build(self):
        """Build the file approval panel UI"""
        pending_files = []
        
        # Scan approval queue directory
        for user_folder in os.listdir(self.approval_queue_path):
            user_path = os.path.join(self.approval_queue_path, user_folder)
            if os.path.isdir(user_path):
                # Check team tag access
                user_teams = self.get_user_teams(user_folder)
                if not self.can_review_file(user_teams):
                    continue
                    
                # List user's pending files
                for filename in os.listdir(user_path):
                    if os.path.isfile(os.path.join(user_path, filename)):
                        pending_files.append(self.create_file_card(filename, user_folder))
        
        if not pending_files:
            return ft.Container(
                content=ft.Text("No files pending approval", italic=True),
                padding=20
            )
            
        return ft.Container(
            content=ft.Column([
                ft.Text("Files Pending Approval", size=24, weight=ft.FontWeight.BOLD),
                ft.Column(pending_files, scroll=ft.ScrollMode.AUTO)
            ]),
            padding=20
        )
