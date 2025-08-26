import json
import os
from datetime import datetime

LOG_FILE = r"\\KMTI-NAS\Shared\data\logs\activity_metadata.json"
USERS_FILE = r"\\KMTI-NAS\Shared\data\users.json"
SESSION_ROOT = "/data/sessions"  


# --------------------------
# Session management helpers
# --------------------------

def save_session(username: str, session_data: dict):
    """
    Save session data in session/<username>/session.json.
    """
    user_session_dir = os.path.join(SESSION_ROOT, username)
    os.makedirs(user_session_dir, exist_ok=True)
    session_file = os.path.join(user_session_dir, "session.json")

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=4)


def load_session(username: str):
    """
    Load session for a given username.
    Returns dict if session exists, else None.
    """
    session_file = os.path.join(SESSION_ROOT, username, "session.json")
    if not os.path.exists(session_file):
        return None
    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def clear_session(username: str):
    """
    Remove a user's session.json file.
    """
    session_file = os.path.join(SESSION_ROOT, username, "session.json")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
        except Exception:
            pass


# --------------------------
# Logging helpers
# --------------------------

def get_fullname(username: str) -> str:
    """
    Get fullname from users.json using username.
    If not found, return username.
    """
    if not os.path.exists(USERS_FILE):
        return username
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        for email, data in users.items():
            if data.get("username") == username:
                return data.get("fullname", username)
    except Exception:
        pass
    return username


def _load_logs():
    """Load log records safely."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_logs(logs):
    """Save log records safely."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def log_login(username: str, role: str):
    """
    Record a login entry for a user with login_time and fullname.
    If the user already has an open session (no logout_time), close it before adding new login.
    """
    logs = _load_logs()

    # Close any unfinished session for this user/role
    for record in reversed(logs):
        if record["username"] == username and record["role"] == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")
            # Compute runtime for that old session
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    # Add a fresh login entry
    now = datetime.now()
    entry = {
        "username": username,
        "fullname": get_fullname(username),
        "role": role,
        "login_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "logout_time": None,
        "runtime": None,
        "date": now.strftime("%Y-%m-%d")
    }
    logs.append(entry)
    _save_logs(logs)


def log_logout(username: str, role: str):
    """
    Updates the last login record of the user with logout_time and runtime.
    """
    logs = _load_logs()

    # Find the latest login for this username and role that has no logout_time
    for record in reversed(logs):
        if record["username"] == username and record["role"] == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")

            # Calculate runtime
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    _save_logs(logs)


def get_active_sessions():
    """
    Returns a dictionary of currently logged-in users (no logout_time).
    Structure:
    {
        "username:role": {
            "username": "...",
            "role": "...",
            "login_time": "...",
            "fullname": "..."
        }
    }
    """
    logs = _load_logs()
    active = {}

    for record in logs:
        if record.get("logout_time") is None:
            uname = record["username"]
            role = record["role"]
            key = f"{uname}:{role}"
            active[key] = {
                "username": uname,
                "role": role,
                "login_time": record["login_time"],
                "fullname": record.get("fullname", uname),
            }

    return active


def get_last_runtime(username: str) -> str:
    """
    Get the last recorded runtime from activity_metadata.json for a logged-out user.
    """
    logs = _load_logs()
    for record in reversed(logs):
        if record["username"] == username and record.get("logout_time"):
            return record.get("runtime") or "-"
    return "-"


# --------------------------------------------------------------------
# Unified log_activity function for admin/user actions
# --------------------------------------------------------------------

def log_activity(username: str, description: str):
    """
    Record an admin/user action (not tied to login sessions).
    Format is unified with logger.py:
    - activity
    - date
    """
    log_file = r"\\KMTI-NAS\Shared\data\logs\activity_logs.json"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Load existing logs
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    entry = {
        "username": username,
        "fullname": get_fullname(username),
        "activity": description,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    logs.append(entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)


def log_panel_access(username: str, role: str, panel: str, login_type: str):
    """
    Log specific panel access for Team Leaders to track which panel they accessed.
    This helps with activity metadata tracking for dual access roles.
    """
    panel_description = {
        "user": "User Panel (file upload/management)",
        "admin": "Team Leader Panel (file review/approval)" if role == "TEAM_LEADER" else "Admin Panel"
    }.get(panel, f"{panel} Panel")
    
    login_method = "Admin Login" if login_type == "admin" else "User Login"
    
    description = f"Accessed {panel_description} via {login_method}"
    log_activity(username, description)


# --------------------------
# 🚨 NEW: Centralized Comment Functions for All Panels
# --------------------------

def load_comments_from_centralized_files(file_id: str) -> list:
    """🚨 SHARED UTILITY: Load comments for a specific file ID from centralized JSON files.
    This function should be used by ALL panels (Admin, TL, User) for consistency.
    """
    try:
        import os
        import json
        from utils.path_config import DATA_PATHS
        
        comments = []
        
        # Load from approval_comments.json
        approval_comments_file = os.path.join(DATA_PATHS.approvals_dir, "approval_comments.json")
        if os.path.exists(approval_comments_file):
            try:
                with open(approval_comments_file, 'r', encoding='utf-8') as f:
                    approval_comments = json.load(f)
                    if file_id in approval_comments:
                        for comment in approval_comments[file_id]:
                            # Add source identifier
                            comment['source'] = 'approval'
                            comments.append(comment)
            except Exception as e:
                print(f"Error loading approval_comments.json: {e}")
        
        # Load from comments.json  
        comments_file = os.path.join(DATA_PATHS.approvals_dir, "comments.json")
        if os.path.exists(comments_file):
            try:
                with open(comments_file, 'r', encoding='utf-8') as f:
                    general_comments = json.load(f)
                    if file_id in general_comments:
                        for comment in general_comments[file_id]:
                            # Add source identifier
                            comment['source'] = 'general'
                            comments.append(comment)
            except Exception as e:
                print(f"Error loading comments.json: {e}")
        
        # Sort comments by timestamp
        comments.sort(key=lambda x: x.get('timestamp', ''), reverse=False)
        
        print(f"[DEBUG] Loaded {len(comments)} centralized comments for file {file_id}")
        return comments
        
    except Exception as e:
        print(f"Error loading centralized comments for file {file_id}: {e}")
        return []

def load_centralized_comments() -> dict:
    """Load all centralized comments from approval JSON files."""
    comments = {}
    
    try:
        import os
        import json
        
        approvals_dir = r"\\KMTI-NAS\Shared\data\approvals"
        
        # Load approval_comments.json
        approval_comments_file = os.path.join(approvals_dir, "approval_comments.json")
        if os.path.exists(approval_comments_file):
            try:
                with open(approval_comments_file, 'r', encoding='utf-8') as f:
                    approval_comments = json.load(f)
                    for file_id, file_comments in approval_comments.items():
                        if file_id not in comments:
                            comments[file_id] = []
                        for comment in file_comments:
                            comment['source'] = 'approval'
                            comments[file_id].append(comment)
            except Exception as e:
                print(f"Error loading approval_comments.json: {e}")
        
        # Load comments.json
        comments_file = os.path.join(approvals_dir, "comments.json")
        if os.path.exists(comments_file):
            try:
                with open(comments_file, 'r', encoding='utf-8') as f:
                    general_comments = json.load(f)
                    for file_id, file_comments in general_comments.items():
                        if file_id not in comments:
                            comments[file_id] = []
                        for comment in file_comments:
                            comment['source'] = 'general'
                            comments[file_id].append(comment)
            except Exception as e:
                print(f"Error loading comments.json: {e}")
        
        print(f"[DEBUG] Loaded centralized comments for {len(comments)} files")
        return comments
        
    except Exception as e:
        print(f"Error loading centralized comments: {e}")
        return {}


def get_comment_metadata_for_monitoring() -> dict:
    """Get metadata about comments for monitoring new additions."""
    try:
        import os
        import json
        
        approvals_dir = r"\\KMTI-NAS\Shared\data\approvals"
        comment_metadata = {}
        
        # Check approval_comments.json metadata
        approval_comments_file = os.path.join(approvals_dir, "approval_comments.json")
        if os.path.exists(approval_comments_file):
            try:
                stat = os.stat(approval_comments_file)
                comment_metadata['approval_comments_modified'] = stat.st_mtime
                
                with open(approval_comments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    comment_metadata['approval_comments_count'] = sum(len(comments) for comments in data.values())
            except Exception as e:
                print(f"Error getting approval_comments.json metadata: {e}")
                comment_metadata['approval_comments_modified'] = 0
                comment_metadata['approval_comments_count'] = 0
        else:
            comment_metadata['approval_comments_modified'] = 0
            comment_metadata['approval_comments_count'] = 0
        
        # Check comments.json metadata
        comments_file = os.path.join(approvals_dir, "comments.json")
        if os.path.exists(comments_file):
            try:
                stat = os.stat(comments_file)
                comment_metadata['comments_modified'] = stat.st_mtime
                
                with open(comments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    comment_metadata['comments_count'] = sum(len(comments) for comments in data.values())
            except Exception as e:
                print(f"Error getting comments.json metadata: {e}")
                comment_metadata['comments_modified'] = 0
                comment_metadata['comments_count'] = 0
        else:
            comment_metadata['comments_modified'] = 0
            comment_metadata['comments_count'] = 0
        
        return comment_metadata
        
    except Exception as e:
        print(f"Error getting comment metadata: {e}")
        return {
            'approval_comments_modified': 0,
            'approval_comments_count': 0,
            'comments_modified': 0,
            'comments_count': 0
        }


def detect_new_comments_for_user(username: str, last_check_metadata: dict) -> list:
    """Detect new comments for a specific user since last check."""
    try:
        from services.approval_service import ApprovalFileService
        from utils.path_config import DATA_PATHS
        
        # Get current comment metadata
        current_metadata = get_comment_metadata_for_monitoring()
        
        # If no previous metadata or no changes, return empty
        if not last_check_metadata:
            return []
        
        # Check if files were modified
        approval_modified = (current_metadata.get('approval_comments_modified', 0) > 
                           last_check_metadata.get('approval_comments_modified', 0))
        comments_modified = (current_metadata.get('comments_modified', 0) > 
                           last_check_metadata.get('comments_modified', 0))
        
        if not approval_modified and not comments_modified:
            return []
        
        # Get user's submitted files to check for relevant comments
        user_folder = DATA_PATHS.get_user_upload_dir(username)
        if not os.path.exists(user_folder):
            return []
        
        approval_service = ApprovalFileService(user_folder, username)
        user_files = approval_service.get_uploaded_files()
        
        # Get user's file IDs from their approval status
        user_file_ids = set()
        for file_info in user_files:
            if file_info.get('submitted_for_approval'):
                approval_data = approval_service.get_file_approval_status(file_info['filename'])
                file_id = approval_data.get('file_id')
                if file_id:
                    user_file_ids.add(file_id)
        
        if not user_file_ids:
            return []
        
        # Load current comments and find new ones
        all_comments = load_centralized_comments()
        new_comments = []
        
        for file_id in user_file_ids:
            if file_id in all_comments:
                for comment in all_comments[file_id]:
                    # Check if comment is newer than last check
                    try:
                        comment_time = comment.get('timestamp', '')
                        if comment_time:
                            from datetime import datetime
                            comment_dt = datetime.fromisoformat(comment_time.replace('Z', '+00:00'))
                            
                            # Use file modification time as proxy for "last check"
                            last_check_time = max(
                                last_check_metadata.get('approval_comments_modified', 0),
                                last_check_metadata.get('comments_modified', 0)
                            )
                            
                            if comment_dt.timestamp() > last_check_time:
                                # Find the filename for this file_id
                                filename = None
                                for file_info in user_files:
                                    approval_data = approval_service.get_file_approval_status(file_info['filename'])
                                    if approval_data.get('file_id') == file_id:
                                        filename = file_info['filename']
                                        break
                                
                                if filename:
                                    # 🚨 ENHANCED: Better comment author and text extraction
                                    comment_author = comment.get('admin_id') or comment.get('tl_id') or comment.get('user_id') or 'Unknown'
                                    comment_text = comment.get('comment') or comment.get('text') or 'No comment text'
                                    
                                    # 🚨 FIXED: Don't notify user about their own comments
                                    if comment_author != username:
                                        new_comments.append({
                                            'file_id': file_id,
                                            'filename': filename,
                                            'comment': comment,
                                            'comment_author': comment_author,
                                            'comment_text': comment_text
                                        })
                    except Exception as e:
                        print(f"Error processing comment timestamp: {e}")
                        continue
        
        # 🚨 ENHANCED: Additional debug information
        if new_comments:
            print(f"[DEBUG] Found {len(new_comments)} new comments for user {username}:")
            for comment_info in new_comments[:3]:  # Show first 3 for debugging
                author = comment_info.get('comment_author', 'Unknown')
                filename = comment_info.get('filename', 'Unknown')
                text_preview = comment_info.get('comment_text', '')[:50] + '...' if len(comment_info.get('comment_text', '')) > 50 else comment_info.get('comment_text', '')
                print(f"  - {author} on {filename}: {text_preview}")
        else:
            print(f"[DEBUG] No new comments found for user {username}")
        
        return new_comments
        
    except Exception as e:
        print(f"Error detecting new comments for {username}: {e}")
        return []
