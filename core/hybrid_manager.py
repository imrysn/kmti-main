import sqlite3
import json
import os
import getpass
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SessionManager:
    """Enhanced session manager with local storage"""
    
    def __init__(self):
        # Store sessions locally for better performance and offline capability
        self.app_data = Path(os.getenv('APPDATA', '.')) / 'KMTI'
        self.app_data.mkdir(exist_ok=True)
        self.username = getpass.getuser()
        self.session_file = self.app_data / f"session_{self.username}.json"
        logger.info(f"Session manager initialized for user: {self.username}")
    
    def save_session(self, user_data: Dict) -> None:
        """Save user session locally"""
        session_data = {
            'user_id': user_data.get('email', user_data.get('username')),
            'username': user_data['username'],
            'fullname': user_data.get('fullname', ''),
            'email': user_data.get('email', ''),
            'role': user_data['role'],
            'team_tags': user_data.get('team_tags', []),
            'login_time': datetime.now().isoformat(),
            'machine_id': os.environ.get('COMPUTERNAME', 'unknown'),
            'session_token': hashlib.sha256(f"{user_data['username']}{datetime.now()}".encode()).hexdigest()[:16]
        }
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved for {user_data['username']}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self) -> Optional[Dict]:
        """Load current user session"""
        if not self.session_file.exists():
            return None
        
        try:
            with open(self.session_file, 'r') as f:
                session = json.load(f)
                logger.info(f"Session loaded for {session.get('username')}")
                return session
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load session: {e}")
            return None
    
    def clear_session(self) -> None:
        """Clear current session"""
        if self.session_file.exists():
            self.session_file.unlink()
            logger.info("Session cleared")
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        session = self.load_session()
        if not session:
            return False
        
        # Check if session is not too old (24 hours)
        try:
            login_time = datetime.fromisoformat(session['login_time'])
            time_diff = datetime.now() - login_time
            return time_diff.total_seconds() < 86400  # 24 hours
        except:
            return False

class DatabaseManager:
    """Hybrid database manager that works with both local and NAS storage"""
    
    def __init__(self, db_path: Union[str, Path] = None):
        if db_path is None:
            # Default to current data directory, will be moved to NAS later
            self.db_path = Path("data/kmti_hybrid.db")
        else:
            self.db_path = Path(db_path)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
        logger.info(f"Database initialized at: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings for NAS compatibility"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # 30 second timeout for network operations
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row  # Dict-like access
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/performance
        return conn
    
    def init_database(self) -> None:
        """Initialize database schema"""
        conn = self.get_connection()
        try:
            # Users table - enhanced from existing JSON structure
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    fullname TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'USER',
                    team_tags TEXT DEFAULT '[]',  -- JSON array
                    join_date DATE DEFAULT CURRENT_DATE,
                    last_login DATETIME,
                    runtime_start DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Files metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    original_path TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    team_tags TEXT DEFAULT '[]',  -- JSON array
                    approval_status TEXT DEFAULT 'pending',
                    created_by TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    modified_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved_by TEXT,
                    approval_date DATETIME,
                    description TEXT,
                    metadata TEXT DEFAULT '{}',  -- JSON object for extra metadata
                    FOREIGN KEY (created_by) REFERENCES users (email),
                    FOREIGN KEY (approved_by) REFERENCES users (email)
                )
            ''')
            
            # Teams table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    team_name TEXT NOT NULL,
                    description TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Permissions table for granular access control
            conn.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    resource_type TEXT,  -- 'file', 'team', 'system'
                    resource_id TEXT,
                    permission_type TEXT,  -- 'read', 'write', 'delete', 'approve'
                    granted_by TEXT,
                    granted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES users (email),
                    FOREIGN KEY (granted_by) REFERENCES users (email)
                )
            ''')
            
            # Notifications table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT DEFAULT 'info',
                    is_read BOOLEAN DEFAULT 0,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES users (email)
                )
            ''')
            
            # Activity log for audit trail
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_email) REFERENCES users (email)
                )
            ''')
            
            # Create indexes for performance
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_users_role ON users (role)',
                'CREATE INDEX IF NOT EXISTS idx_users_team_tags ON users (team_tags)',
                'CREATE INDEX IF NOT EXISTS idx_files_team_tags ON files (team_tags)',
                'CREATE INDEX IF NOT EXISTS idx_files_approval_status ON files (approval_status)',
                'CREATE INDEX IF NOT EXISTS idx_files_created_by ON files (created_by)',
                'CREATE INDEX IF NOT EXISTS idx_permissions_user ON permissions (user_email)',
                'CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications (user_email)',
                'CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log (user_email)'
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            conn.close()
    
    def migrate_from_json(self, json_data_path: Path = None) -> bool:
        """Migrate existing JSON data to SQLite"""
        if json_data_path is None:
            json_data_path = Path("data")
        
        logger.info(f"Starting migration from {json_data_path}")
        
        try:
            # Migrate users
            users_file = json_data_path / "users.json"
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                
                conn = self.get_connection()
                try:
                    for email, user_data in users_data.items():
                        conn.execute('''
                            INSERT OR REPLACE INTO users 
                            (email, username, fullname, password_hash, role, team_tags, 
                             join_date, runtime_start, last_login)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            email,
                            user_data['username'],
                            user_data['fullname'],
                            user_data['password'],
                            user_data['role'],
                            json.dumps(user_data.get('team_tags', [])),
                            user_data.get('join_date'),
                            user_data.get('runtime_start'),
                            user_data.get('runtime_start')  # Use runtime_start as last_login
                        ))
                    
                    conn.commit()
                    logger.info(f"Migrated {len(users_data)} users")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to migrate users: {e}")
                    return False
                finally:
                    conn.close()
            
            # Migrate teams
            teams_file = json_data_path / "teams.json"
            if teams_file.exists():
                with open(teams_file, 'r') as f:
                    teams_data = json.load(f)
                
                conn = self.get_connection()
                try:
                    for team_id, team_info in teams_data.items():
                        conn.execute('''
                            INSERT OR REPLACE INTO teams (team_id, team_name, description)
                            VALUES (?, ?, ?)
                        ''', (team_id, team_info.get('name', team_id), team_info.get('description', '')))
                    
                    conn.commit()
                    logger.info(f"Migrated {len(teams_data)} teams")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to migrate teams: {e}")
                    return False
                finally:
                    conn.close()
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

class RBACManager:
    """Enhanced Role-Based Access Control Manager"""
    
    def __init__(self, session_manager: SessionManager, db_manager: DatabaseManager):
        self.session_manager = session_manager
        self.db_manager = db_manager
        logger.info("RBAC Manager initialized")
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current logged-in user with database info"""
        session = self.session_manager.load_session()
        if not session:
            return None
        
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (session['user_id'],)
            )
            user_row = cursor.fetchone()
            if user_row:
                user_dict = dict(user_row)
                user_dict['team_tags'] = json.loads(user_dict['team_tags'])
                return user_dict
            return None
        except Exception as e:
            logger.error(f"Error fetching current user: {e}")
            return None
        finally:
            conn.close()
    
    def can_access_file(self, file_metadata: Dict) -> bool:
        """Check if current user can access a file"""
        user = self.get_current_user()
        if not user:
            return False
        
        user_role = user['role']
        user_teams = set(user['team_tags'])
        file_teams = set(json.loads(file_metadata.get('team_tags', '[]')))
        
        # Admin can access everything
        if user_role == 'ADMIN':
            return True
        
        # Team leaders can access files from their teams
        if user_role == 'TEAM_LEADER':
            return bool(user_teams & file_teams) or len(file_teams) == 0
        
        # Regular users can access files from their teams
        if user_role == 'USER':
            return bool(user_teams & file_teams) or len(file_teams) == 0
        
        return False
    
    def can_access_admin_panel(self) -> bool:
        """Check if user can access admin panel"""
        user = self.get_current_user()
        return user and user['role'] in ['ADMIN', 'TEAM_LEADER']
    
    def get_admin_tabs(self) -> List[str]:
        """Get available admin tabs for current user"""
        user = self.get_current_user()
        if not user:
            return []
        
        role = user['role']
        if role == 'ADMIN':
            return ['file_approval', 'user_management', 'system_config', 'team_management']
        elif role == 'TEAM_LEADER':
            return ['file_approval']  # Only File Approval tab
        
        return []
    
    def log_activity(self, action: str, resource_type: str = None, 
                    resource_id: str = None, details: str = None) -> None:
        """Log user activity for audit trail"""
        user = self.get_current_user()
        if not user:
            return
        
        conn = self.db_manager.get_connection()
        try:
            conn.execute('''
                INSERT INTO activity_log 
                (user_email, action, resource_type, resource_id, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['email'], action, resource_type, resource_id, details))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
        finally:
            conn.close()

class HybridFileService:
    """Enhanced file service with hybrid database + filesystem storage"""
    
    def __init__(self, db_manager: DatabaseManager, rbac_manager: RBACManager):
        self.db_manager = db_manager
        self.rbac_manager = rbac_manager
        
        # File storage paths - will be on NAS eventually
        self.base_path = Path("Y:/APP DEVELOPMENT/kmti-main/data") if Path("Y:/").exists() else Path("data")
        self.documents_path = self.base_path / "documents"
        self.temp_path = self.base_path / "temp"
        
        # Create directories
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"File service initialized with base path: {self.base_path}")
    
    def add_file(self, filename: str, file_content: bytes, 
                 team_tags: List[str] = None, description: str = "",
                 file_type: str = None) -> str:
        """Add new file to system"""
        user = self.rbac_manager.get_current_user()
        if not user:
            raise PermissionError("User not logged in")
        
        # Generate file ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_id = f"file_{timestamp}_{hash(filename) % 10000:04d}"
        
        # Determine file path
        file_path = self.documents_path / f"{file_id}_{filename}"
        
        try:
            # Save physical file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Save metadata to database
            conn = self.db_manager.get_connection()
            try:
                conn.execute('''
                    INSERT INTO files (
                        id, filename, file_path, file_size, file_type, 
                        team_tags, created_by, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id, filename, str(file_path), len(file_content),
                    file_type or self._detect_file_type(filename),
                    json.dumps(team_tags or []), user['email'], description
                ))
                conn.commit()
                
                # Log activity
                self.rbac_manager.log_activity(
                    "FILE_UPLOAD", "file", file_id, 
                    f"Uploaded {filename} ({len(file_content)} bytes)"
                )
                
                logger.info(f"File added: {filename} ({file_id})")
                return file_id
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            # Clean up physical file if database insert fails
            if file_path.exists():
                file_path.unlink()
            logger.error(f"Failed to add file: {e}")
            raise
    
    def get_files_for_approval(self, team_filter: List[str] = None) -> List[Dict]:
        """Get files pending approval, filtered by user access"""
        user = self.rbac_manager.get_current_user()
        if not user:
            return []
        
        conn = self.db_manager.get_connection()
        try:
            # Build query based on user role
            if user['role'] == 'ADMIN':
                # Admins see all pending files
                cursor = conn.execute('''
                    SELECT f.*, u.fullname as creator_name 
                    FROM files f
                    LEFT JOIN users u ON f.created_by = u.email
                    WHERE f.approval_status = 'pending'
                    ORDER BY f.created_date DESC
                ''')
            else:
                # Team leaders see only their team's files
                user_teams = user['team_tags']
                if not user_teams:
                    return []
                
                # Create placeholders for team filtering
                team_conditions = []
                params = ['pending']
                
                for team in user_teams:
                    team_conditions.append("f.team_tags LIKE ?")
                    params.append(f'%"{team}"%')
                
                query = f'''
                    SELECT f.*, u.fullname as creator_name 
                    FROM files f
                    LEFT JOIN users u ON f.created_by = u.email
                    WHERE f.approval_status = ? AND ({' OR '.join(team_conditions)})
                    ORDER BY f.created_date DESC
                '''
                
                cursor = conn.execute(query, params)
            
            files = []
            for row in cursor.fetchall():
                file_data = dict(row)
                file_data['team_tags'] = json.loads(file_data['team_tags'])
                files.append(file_data)
            
            return files
            
        except Exception as e:
            logger.error(f"Error fetching files for approval: {e}")
            return []
        finally:
            conn.close()
    
    def approve_file(self, file_id: str, approved: bool = True, 
                    comments: str = "") -> bool:
        """Approve or reject a file"""
        user = self.rbac_manager.get_current_user()
        if not user:
            raise PermissionError("User not logged in")
        
        if user['role'] not in ['ADMIN', 'TEAM_LEADER']:
            raise PermissionError("Insufficient permissions for file approval")
        
        conn = self.db_manager.get_connection()
        try:
            # First check if user can access this file
            cursor = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            file_data = cursor.fetchone()
            
            if not file_data:
                raise FileNotFoundError(f"File {file_id} not found")
            
            file_dict = dict(file_data)
            if not self.rbac_manager.can_access_file(file_dict):
                raise PermissionError("Access denied to this file")
            
            # Update approval status
            status = 'approved' if approved else 'rejected'
            conn.execute('''
                UPDATE files 
                SET approval_status = ?, approved_by = ?, approval_date = ?,
                    metadata = json_set(COALESCE(metadata, '{}'), '$.approval_comments', ?)
                WHERE id = ?
            ''', (status, user['email'], datetime.now().isoformat(), comments, file_id))
            
            conn.commit()
            
            # Log activity
            action = "FILE_APPROVED" if approved else "FILE_REJECTED"
            self.rbac_manager.log_activity(
                action, "file", file_id, 
                f"File {file_dict['filename']} {status}. Comments: {comments}"
            )
            
            logger.info(f"File {file_id} {status} by {user['username']}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to approve file: {e}")
            raise
        finally:
            conn.close()
    
    def search_files(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search files with advanced filtering"""
        user = self.rbac_manager.get_current_user()
        if not user:
            return []
        
        conn = self.db_manager.get_connection()
        try:
            base_query = '''
                SELECT f.*, u.fullname as creator_name 
                FROM files f
                LEFT JOIN users u ON f.created_by = u.email
                WHERE (f.filename LIKE ? OR f.description LIKE ?)
            '''
            
            params = [f'%{query}%', f'%{query}%']
            
            # Add team filtering for non-admin users
            if user['role'] != 'ADMIN':
                user_teams = user['team_tags']
                if user_teams:
                    team_conditions = []
                    for team in user_teams:
                        team_conditions.append("f.team_tags LIKE ?")
                        params.append(f'%"{team}"%')
                    
                    if team_conditions:
                        base_query += f" AND ({' OR '.join(team_conditions)})"
                else:
                    return []  # User has no teams, can't see any files
            
            # Add additional filters
            if filters:
                if 'approval_status' in filters:
                    base_query += " AND f.approval_status = ?"
                    params.append(filters['approval_status'])
                
                if 'file_type' in filters:
                    base_query += " AND f.file_type = ?"
                    params.append(filters['file_type'])
                
                if 'created_by' in filters:
                    base_query += " AND f.created_by = ?"
                    params.append(filters['created_by'])
            
            base_query += " ORDER BY f.modified_date DESC LIMIT 100"
            
            cursor = conn.execute(base_query, params)
            
            files = []
            for row in cursor.fetchall():
                file_data = dict(row)
                file_data['team_tags'] = json.loads(file_data['team_tags'])
                if file_data.get('metadata'):
                    file_data['metadata'] = json.loads(file_data['metadata'])
                files.append(file_data)
            
            return files
            
        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return []
        finally:
            conn.close()
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension"""
        ext = Path(filename).suffix.lower()
        type_mapping = {
            '.pdf': 'document',
            '.doc': 'document', '.docx': 'document',
            '.xls': 'spreadsheet', '.xlsx': 'spreadsheet',
            '.ppt': 'presentation', '.pptx': 'presentation',
            '.txt': 'text', '.md': 'text',
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.mp4': 'video', '.avi': 'video', '.mov': 'video',
            '.mp3': 'audio', '.wav': 'audio',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive'
        }
        return type_mapping.get(ext, 'other')

class HybridUserService:
    """Enhanced user service with hybrid backend"""
    
    def __init__(self, db_manager: DatabaseManager, rbac_manager: RBACManager):
        self.db_manager = db_manager
        self.rbac_manager = rbac_manager
        logger.info("User service initialized")
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user login with enhanced security"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = self.db_manager.get_connection()
        try:
            # Try to authenticate by username or email
            cursor = conn.execute('''
                SELECT * FROM users 
                WHERE (username = ? OR email = ?) AND password_hash = ? AND is_active = 1
            ''', (username, username, password_hash))
            
            user_row = cursor.fetchone()
            if user_row:
                user_dict = dict(user_row)
                user_dict['team_tags'] = json.loads(user_dict['team_tags'])
                
                # Update last login
                conn.execute('''
                    UPDATE users SET last_login = ? WHERE email = ?
                ''', (datetime.now().isoformat(), user_dict['email']))
                conn.commit()
                
                logger.info(f"User authenticated: {username}")
                return user_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def create_user(self, email: str, username: str, fullname: str, 
                   password: str, role: str = 'USER', 
                   team_tags: List[str] = None) -> bool:
        """Create new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = self.db_manager.get_connection()
        try:
            conn.execute('''
                INSERT INTO users (email, username, fullname, password_hash, role, team_tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (email, username, fullname, password_hash, role, json.dumps(team_tags or [])))
            
            conn.commit()
            logger.info(f"User created: {username} ({role})")
            return True
            
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed - duplicate: {e}")
            return False
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return False
        finally:
            conn.close()
    
    def get_users(self, role_filter: str = None) -> List[Dict]:
        """Get all users with optional role filtering"""
        conn = self.db_manager.get_connection()
        try:
            if role_filter:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY fullname",
                    (role_filter,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE is_active = 1 ORDER BY fullname"
                )
            
            users = []
            for row in cursor.fetchall():
                user_dict = dict(row)
                user_dict['team_tags'] = json.loads(user_dict['team_tags'])
                # Don't include password hash in returned data
                user_dict.pop('password_hash', None)
                users.append(user_dict)
            
            return users
            
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
        finally:
            conn.close()

# Main Application Integration Class
class KMTIHybridApp:
    """Main application class that integrates with existing KMTI Flet app"""
    
    def __init__(self, db_path: Union[str, Path] = None):
        # Initialize all components
        self.session_manager = SessionManager()
        self.db_manager = DatabaseManager(db_path)
        self.rbac_manager = RBACManager(self.session_manager, self.db_manager)
        self.file_service = HybridFileService(self.db_manager, self.rbac_manager)
        self.user_service = HybridUserService(self.db_manager, self.rbac_manager)
        
        logger.info("KMTI Hybrid App initialized")
    
    def migrate_existing_data(self) -> bool:
        """Migrate existing JSON data to hybrid system"""
        return self.db_manager.migrate_from_json()
    
    def login(self, username: str, password: str) -> bool:
        """Handle user login"""
        user = self.user_service.authenticate(username, password)
        if user:
            self.session_manager.save_session(user)
            return True
        return False
    
    def logout(self):
        """Handle user logout"""
        user = self.rbac_manager.get_current_user()
        if user:
            self.rbac_manager.log_activity("LOGOUT", details="User logged out")
        self.session_manager.clear_session()
    
    def get_current_user(self):
        """Get current logged-in user"""
        return self.rbac_manager.get_current_user()
    
    def can_access_admin_panel(self) -> bool:
        """Check admin panel access"""
        return self.rbac_manager.can_access_admin_panel()
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid"""
        return self.session_manager.is_session_valid()

# Compatibility layer for existing KMTI code
def restore_session_hybrid(page, hybrid_app: KMTIHybridApp):
    """Enhanced session restore function for existing main.py integration"""
    if hybrid_app.is_session_valid():
        user = hybrid_app.get_current_user()
        if user:
            username = user['username']
            role = user['role']
            
            # Import existing panels
            from admin_panel import admin_panel
            from user.user_panel import user_panel
            
            if role.upper() in ["ADMIN", "TEAM_LEADER"]:
                admin_panel(page, username)
                return True
            else:
                user_panel(page, username)
                return True
    return False

if __name__ == "__main__":
    # Test the hybrid system
    app = KMTIHybridApp()
    
    # Migrate existing data
    print("Migrating existing data...")
    if app.migrate_existing_data():
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed or no data to migrate")
    
    # Test authentication
    print("\nTesting authentication...")
    if app.login("admin", "admin"):
        print("✅ Admin login successful")
        user = app.get_current_user()
        print(f"Current user: {user['fullname']} ({user['role']})")
        print(f"Can access admin panel: {app.can_access_admin_panel()}")
        app.logout()
    else:
        print("❌ Login failed")
    
    print("\n🎉 KMTI Hybrid Architecture is ready!")