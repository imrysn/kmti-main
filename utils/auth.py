"""
Enhanced auth.py - Adds input validation and security logging to your existing authentication.
Maintains backward compatibility with your existing functions while adding security features.
"""

import json
import os
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import defaultdict

# Your existing constants - kept unchanged
USERS_FILE = r"\\KMTI-NAS\Shared\data\users.json"

# New security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
FAILED_ATTEMPTS_FILE = "data/logs/failed_attempts.json"

# Setup logging
logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Custom exception for authentication security issues"""
    pass

class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    pass

def hash_password(password: str | None) -> str:
    """Your existing hash_password function - kept unchanged for backward compatibility"""
    if password is None:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_plain_passwords(users):
    """Your existing migrate_plain_passwords function - kept unchanged"""
    changed = False
    for email, data in users.items():
        pw = data.get("password", "")
        # Check if password looks like a SHA-256 hash
        if len(pw) != 64 or not all(c in "0123456789abcdef" for c in pw.lower()):
            # Plain text password: hash it
            data["password"] = hash_password(pw)
            changed = True
    return changed

def load_users():
    """Your existing load_users function - kept unchanged for backward compatibility"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    # Auto-migrate plain text passwords
    if migrate_plain_passwords(users):
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

    return users

def validate_login(username_or_email: str, password: str, is_admin_login: bool) -> str | None:
    """Your existing validate_login function - kept unchanged for backward compatibility"""
    users = load_users()
    entered_hash = hash_password(password)

    for email, data in users.items():
        stored_hash = data.get("password", "")

        # Allow login by either username or email
        if username_or_email == email or username_or_email == data.get("username", ""):
            # Compare hashed password (support migration)
            if entered_hash == stored_hash or password == stored_hash:
                role = data.get("role", "")
                # Normalize role to uppercase for consistency
                return role.upper()
    return None

class EnhancedAuthenticator:
    """
    Enhanced authentication system that extends your existing auth with security features.
    """
    
    def __init__(self):
        # Input validation patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.username_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
        self.password_pattern = re.compile(r'^.{8,128}$')  # At least 8 chars, max 128
        
        # Load failed attempts tracking
        self.failed_attempts = self._load_failed_attempts()
        
        logger.debug("Enhanced authenticator initialized")
    
    def _load_failed_attempts(self) -> Dict:
        """Load failed login attempts from file"""
        if os.path.exists(FAILED_ATTEMPTS_FILE):
            try:
                with open(FAILED_ATTEMPTS_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {}
    
    def _save_failed_attempts(self):
        """Save failed login attempts to file"""
        os.makedirs(os.path.dirname(FAILED_ATTEMPTS_FILE), exist_ok=True)
        with open(FAILED_ATTEMPTS_FILE, "w") as f:
            json.dump(self.failed_attempts, f, indent=2)
    
    def sanitize_username(self, username: str) -> str:
        """
        Sanitize username input for security.
        
        Args:
            username: Raw username input
            
        Returns:
            Sanitized username
            
        Raises:
            SecurityError: If username is invalid
        """
        if not username or not isinstance(username, str):
            raise SecurityError("Invalid username provided")
        
        username = username.strip().lower()
        
        # Check length
        if len(username) < 3 or len(username) > 50:
            raise SecurityError("Username must be between 3 and 50 characters")
        
        # Check for dangerous characters
        if not self.username_pattern.match(username):
            raise SecurityError("Username contains invalid characters")
        
        return username
    
    def sanitize_email(self, email: str) -> str:
        """
        Sanitize email input for security.
        
        Args:
            email: Raw email input
            
        Returns:
            Sanitized email
            
        Raises:
            SecurityError: If email is invalid
        """
        if not email or not isinstance(email, str):
            raise SecurityError("Invalid email provided")
        
        email = email.strip().lower()
        
        # Check length
        if len(email) > 254:  # RFC 5321 limit
            raise SecurityError("Email address too long")
        
        # Validate email format
        if not self.email_pattern.match(email):
            raise SecurityError("Invalid email format")
        
        return email
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements
            
        Raises:
            SecurityError: If password doesn't meet requirements
        """
        if not password or not isinstance(password, str):
            raise SecurityError("Invalid password provided")
        
        # Check length
        if not self.password_pattern.match(password):
            raise SecurityError("Password must be between 8 and 128 characters")
        
        # Check for at least one letter and one number
        has_letter = bool(re.search(r'[a-zA-Z]', password))
        has_number = bool(re.search(r'[0-9]', password))
        
        if not (has_letter and has_number):
            raise SecurityError("Password must contain at least one letter and one number")
        
        return True
    
    def is_account_locked(self, username: str, ip_address: str = None) -> bool:
        """
        Check if account or IP is locked due to failed attempts.
        
        Args:
            username: Username to check
            ip_address: IP address to check (optional)
            
        Returns:
            True if account/IP is locked
        """
        current_time = datetime.now()
        lockout_cutoff = current_time - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        
        # Check username-based lockout
        username_key = f"user:{username}"
        if username_key in self.failed_attempts:
            attempts = self.failed_attempts[username_key]
            recent_attempts = [
                attempt for attempt in attempts 
                if datetime.fromisoformat(attempt['timestamp']) > lockout_cutoff
            ]
            
            if len(recent_attempts) >= MAX_LOGIN_ATTEMPTS:
                return True
        
        # Check IP-based lockout
        if ip_address:
            ip_key = f"ip:{ip_address}"
            if ip_key in self.failed_attempts:
                attempts = self.failed_attempts[ip_key]
                recent_attempts = [
                    attempt for attempt in attempts 
                    if datetime.fromisoformat(attempt['timestamp']) > lockout_cutoff
                ]
                
                if len(recent_attempts) >= MAX_LOGIN_ATTEMPTS * 2:  # Higher threshold for IP
                    return True
        
        return False
    
    def record_failed_attempt(self, username: str, ip_address: str = None, details: Dict = None):
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed
            ip_address: IP address of attempt (optional)
            details: Additional failure details
        """
        current_time = datetime.now()
        attempt_record = {
            'timestamp': current_time.isoformat(),
            'details': details or {}
        }
        
        # Record by username
        username_key = f"user:{username}"
        if username_key not in self.failed_attempts:
            self.failed_attempts[username_key] = []
        self.failed_attempts[username_key].append(attempt_record)
        
        # Record by IP address
        if ip_address:
            ip_key = f"ip:{ip_address}"
            if ip_key not in self.failed_attempts:
                self.failed_attempts[ip_key] = []
            self.failed_attempts[ip_key].append(attempt_record)
        
        # Clean old attempts (older than 24 hours)
        cleanup_cutoff = current_time - timedelta(hours=24)
        for key in list(self.failed_attempts.keys()):
            self.failed_attempts[key] = [
                attempt for attempt in self.failed_attempts[key]
                if datetime.fromisoformat(attempt['timestamp']) > cleanup_cutoff
            ]
            if not self.failed_attempts[key]:
                del self.failed_attempts[key]
        
        self._save_failed_attempts()
        
        # Log security event
        from utils.logger import log_security_event
        log_security_event(
            username=username,
            event_type="FAILED_LOGIN_ATTEMPT",
            details={
                "ip_address": ip_address or "unknown",
                "attempt_count": len(self.failed_attempts.get(username_key, [])),
                **details
            },
            severity="WARNING"
        )
    
    def clear_failed_attempts(self, username: str):
        """Clear failed attempts for successful login"""
        username_key = f"user:{username}"
        if username_key in self.failed_attempts:
            del self.failed_attempts[username_key]
            self._save_failed_attempts()
    
    def secure_validate_login(self, username_or_email: str, password: str, 
                            is_admin_login: bool, ip_address: str = None) -> str | None:
        """
        Enhanced login validation with security features.
        
        Args:
            username_or_email: Username or email for login
            password: Password for login
            is_admin_login: Whether this is an admin login attempt
            ip_address: IP address of login attempt (optional)
            
        Returns:
            Role if login successful, None if failed
            
        Raises:
            SecurityError: If security validation fails
            AuthenticationError: If authentication fails
        """
        try:
            # Sanitize inputs
            if '@' in username_or_email:
                safe_input = self.sanitize_email(username_or_email)
            else:
                safe_input = self.sanitize_username(username_or_email)
            
            # Check for account lockout
            if self.is_account_locked(safe_input, ip_address):
                self.record_failed_attempt(
                    safe_input, ip_address, 
                    {"reason": "account_locked", "is_admin_login": is_admin_login}
                )
                raise AuthenticationError("Account temporarily locked due to failed attempts")
            
            # Use your existing validation function
            role = validate_login(safe_input, password, is_admin_login)
            
            if role:
                # Successful login
                self.clear_failed_attempts(safe_input)
                
                # Log successful login
                from utils.logger import log_security_event
                log_security_event(
                    username=safe_input,
                    event_type="SUCCESSFUL_LOGIN",
                    details={
                        "role": role,
                        "is_admin_login": is_admin_login,
                        "ip_address": ip_address or "unknown"
                    },
                    severity="INFO"
                )
                
                logger.info(f"Successful login: {safe_input} as {role}")
                return role
            else:
                # Failed login
                self.record_failed_attempt(
                    safe_input, ip_address,
                    {"reason": "invalid_credentials", "is_admin_login": is_admin_login}
                )
                raise AuthenticationError("Invalid credentials")
                
        except SecurityError as e:
            # Input validation failed
            self.record_failed_attempt(
                username_or_email, ip_address,
                {"reason": "input_validation_failed", "error": str(e)}
            )
            logger.warning(f"Security error in login: {e}")
            raise
        
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in secure login: {e}")
            raise AuthenticationError("Login system error")
    
    def create_user_safely(self, email: str, username: str, password: str, 
                          fullname: str, role: str) -> bool:
        """
        Create user with input validation and security checks.
        
        Args:
            email: User's email address
            username: User's username
            password: User's password
            fullname: User's full name
            role: User's role
            
        Returns:
            True if user created successfully
            
        Raises:
            SecurityError: If validation fails
        """
        try:
            # Sanitize and validate inputs
            safe_email = self.sanitize_email(email)
            safe_username = self.sanitize_username(username)
            safe_fullname = fullname.strip()[:100]  # Limit length
            safe_role = role.strip().upper()
            
            # Validate password strength
            self.validate_password_strength(password)
            
            # Check if user already exists
            users = load_users()
            if safe_email in users:
                raise SecurityError("Email already registered")
            
            for existing_email, data in users.items():
                if data.get("username") == safe_username:
                    raise SecurityError("Username already taken")
            
            # Create user
            users[safe_email] = {
                "username": safe_username,
                "password": hash_password(password),
                "fullname": safe_fullname,
                "role": safe_role
            }
            
            # Save users file
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, "w") as f:
                json.dump(users, f, indent=4)
            
            # Log user creation
            from utils.logger import log_security_event
            log_security_event(
                username=safe_username,
                event_type="USER_CREATED",
                details={
                    "email": safe_email,
                    "role": safe_role,
                    "created_by": "system"
                },
                severity="INFO"
            )
            
            logger.info(f"User created: {safe_username} ({safe_email})")
            return True
            
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise SecurityError(f"Failed to create user: {e}")
    
    def get_security_stats(self) -> Dict:
        """Get authentication security statistics"""
        current_time = datetime.now()
        last_24h = current_time - timedelta(hours=24)
        
        stats = {
            "total_failed_attempts": 0,
            "unique_users_with_failures": 0,
            "unique_ips_with_failures": 0,
            "locked_accounts": 0,
            "recent_attempts_24h": 0
        }
        
        locked_users = set()
        recent_attempts = 0
        
        for key, attempts in self.failed_attempts.items():
            stats["total_failed_attempts"] += len(attempts)
            
            # Count recent attempts
            recent_count = sum(
                1 for attempt in attempts
                if datetime.fromisoformat(attempt['timestamp']) > last_24h
            )
            recent_attempts += recent_count
            
            # Check if locked
            if key.startswith("user:"):
                username = key[5:]  # Remove "user:" prefix
                stats["unique_users_with_failures"] += 1
                if self.is_account_locked(username):
                    locked_users.add(username)
            elif key.startswith("ip:"):
                stats["unique_ips_with_failures"] += 1
        
        stats["locked_accounts"] = len(locked_users)
        stats["recent_attempts_24h"] = recent_attempts
        
        return stats

# Global enhanced authenticator instance
_enhanced_auth_instance = None

def get_enhanced_authenticator() -> EnhancedAuthenticator:
    """Get global enhanced authenticator instance"""
    global _enhanced_auth_instance
    if _enhanced_auth_instance is None:
        _enhanced_auth_instance = EnhancedAuthenticator()
    return _enhanced_auth_instance

# Enhanced convenience functions that extend your existing API
def secure_validate_login(username_or_email: str, password: str, is_admin_login: bool, 
                         ip_address: str = None) -> str | None:
    """
    Enhanced version of validate_login with security features.
    Drop-in replacement that adds input validation and attempt tracking.
    """
    enhanced_auth = get_enhanced_authenticator()
    return enhanced_auth.secure_validate_login(username_or_email, password, is_admin_login, ip_address)

def create_user_safely(email: str, username: str, password: str, fullname: str, role: str) -> bool:
    """Create user with comprehensive input validation"""
    enhanced_auth = get_enhanced_authenticator()
    return enhanced_auth.create_user_safely(email, username, password, fullname, role)

def is_account_locked(username: str, ip_address: str = None) -> bool:
    """Check if account is locked due to failed attempts"""
    enhanced_auth = get_enhanced_authenticator()
    return enhanced_auth.is_account_locked(username, ip_address)

def get_auth_security_stats() -> Dict:
    """Get authentication security statistics"""
    enhanced_auth = get_enhanced_authenticator()
    return enhanced_auth.get_security_stats()