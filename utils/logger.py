
import json
import logging
import logging.handlers
from datetime import datetime
import os
from typing import Dict, Optional, List
from pathlib import Path

# Your existing constants - kept unchanged
LOG_FILE = "data/logs/activity.log"
METADATA_FILE = "data/logs/activity_logs.json"
USERS_FILE = "data/users.json"

# New security audit log file
SECURITY_LOG_FILE = "data/logs/security_audit.log"
PERFORMANCE_LOG_FILE = "data/logs/performance.log"

def _get_user_details(username: str):
    """Your existing function - kept unchanged for backward compatibility"""
    if not os.path.exists(USERS_FILE):
        return {"fullname": username, "email": "", "role": ""}

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for email, data in users.items():
        if data.get("username") == username:
            return {
                "fullname": data.get("fullname", username),
                "email": email,
                "role": data.get("role", "")
            }
    return {"fullname": username, "email": "", "role": ""}

def log_action(username: str, activity: str):
    """
    Your existing log_action function - kept unchanged for backward compatibility.
    Logs activity to both:
    - A plain text log file (activity.log)
    - A unified JSON metadata file (activity_logs.json)
    """
    details = _get_user_details(username)
    log_line = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
        f"{details['fullname']} ({details['email']}, {details['role']}) - {activity}\n"
    )

    # Plain text log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    # Save to structured JSON file
    meta_entry = {
        "username": username,
        "fullname": details["fullname"],
        "email": details["email"],
        "role": details["role"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "activity": activity,
    }

    meta_data = []
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            try:
                meta_data = json.load(f)
            except json.JSONDecodeError:
                meta_data = []

    meta_data.append(meta_entry)
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(meta_data, f, indent=4)

class EnhancedLogger:
    """
    Enhanced logging system that extends your existing logging with security and performance tracking.
    """
    
    def __init__(self):
        self.setup_enhanced_logging()
        
        # Create specialized loggers
        self.general_logger = logging.getLogger('general')
        self.security_logger = logging.getLogger('security')
        self.performance_logger = logging.getLogger('performance')
        self.file_ops_logger = logging.getLogger('file_operations')
    
    def setup_enhanced_logging(self):
        """Setup enhanced logging with rotation and different levels"""
        # Ensure log directory exists
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            "data/logs/system.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    def log_activity_enhanced(self, username: str, activity: str, activity_type: str = "GENERAL"):
        """
        Enhanced activity logging that extends your existing log_action function.
        
        Args:
            username: User performing the activity
            activity: Description of activity
            activity_type: Type of activity (GENERAL, SECURITY, FILE_OP, etc.)
        """
        # Use your existing logging function for backward compatibility
        log_action(username, activity)
        
        # Add enhanced logging with categorization
        if activity_type == "SECURITY":
            self.security_logger.warning(f"User {username}: {activity}")
        elif activity_type == "FILE_OP":
            self.file_ops_logger.info(f"User {username}: {activity}")
        else:
            self.general_logger.info(f"User {username}: {activity}")
    
    def log_security_event(self, username: str, event_type: str, details: Dict, severity: str = "WARNING"):
        """
        Log security-related events with detailed tracking.
        
        Args:
            username: User involved in security event
            event_type: Type of security event (LOGIN_ATTEMPT, PATH_VIOLATION, etc.)
            details: Dictionary with event details
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        """
        user_details = _get_user_details(username)
        
        security_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "fullname": user_details["fullname"],
            "email": user_details["email"],
            "role": user_details["role"],
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "ip_address": details.get("ip_address", "unknown")
        }
        
        # Log to security audit file
        security_log_data = []
        if os.path.exists(SECURITY_LOG_FILE):
            try:
                with open(SECURITY_LOG_FILE, "r") as f:
                    security_log_data = json.load(f)
            except json.JSONDecodeError:
                security_log_data = []
        
        security_log_data.append(security_entry)
        
        # Keep only last 1000 security events to manage file size
        if len(security_log_data) > 1000:
            security_log_data = security_log_data[-1000:]
        
        with open(SECURITY_LOG_FILE, "w") as f:
            json.dump(security_log_data, f, indent=2)
        
        # Also log to system logger
        log_level = getattr(logging, severity, logging.WARNING)
        self.security_logger.log(
            log_level,
            f"SECURITY_EVENT - {event_type} - User: {username}, Details: {details}"
        )
        
        # For critical security events, also use your existing activity log
        if severity in ["ERROR", "CRITICAL"]:
            log_action(username, f"SECURITY ALERT: {event_type} - {details.get('message', '')}")
    
    def log_file_operation(self, username: str, operation: str, file_path: str, 
                          result: str, details: Optional[Dict] = None):
        """
        Log file operations with security tracking.
        
        Args:
            username: User performing operation
            operation: Type of operation (UPLOAD, DOWNLOAD, DELETE, APPROVE, etc.)
            file_path: Path of file involved
            result: Result of operation (SUCCESS, FAILED, BLOCKED)
            details: Additional operation details
        """
        details = details or {}
        
        file_op_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "operation": operation,
            "file_path": str(file_path),
            "result": result,
            "details": details
        }
        
        # Log to file operations logger
        self.file_ops_logger.info(
            f"FILE_OP - {operation} - User: {username}, File: {file_path}, Result: {result}"
        )
        
        # If operation failed due to security, log as security event
        if result in ["BLOCKED", "SECURITY_VIOLATION"]:
            self.log_security_event(
                username=username,
                event_type="FILE_SECURITY_VIOLATION",
                details={
                    "operation": operation,
                    "file_path": str(file_path),
                    "result": result,
                    **details
                },
                severity="WARNING"
            )
        
        # Use your existing activity logging for important file operations
        if operation in ["APPROVE", "REJECT", "DELETE"]:
            activity_msg = f"{operation} file: {Path(file_path).name} - {result}"
            log_action(username, activity_msg)
    
    def log_approval_action(self, admin_user: str, target_user: str, file_id: str, 
                           action: str, reason: str = None):
        """
        Log file approval/rejection actions.
        
        Args:
            admin_user: Admin performing the action
            target_user: User whose file is being acted upon
            file_id: ID of file being acted upon
            action: Action taken (APPROVE, REJECT, COMMENT)
            reason: Optional reason for action
        """
        details = {
            "target_user": target_user,
            "file_id": file_id,
            "action": action,
            "reason": reason or "None provided"
        }
        
        # Log as security event for audit trail
        self.log_security_event(
            username=admin_user,
            event_type="APPROVAL_ACTION",
            details=details,
            severity="INFO"
        )
        
        # Use your existing activity logging
        activity_msg = f"{action} file {file_id} for user {target_user}"
        if reason:
            activity_msg += f" - Reason: {reason}"
        log_action(admin_user, activity_msg)
    
    def log_performance_metric(self, component: str, operation: str, 
                             duration_ms: float, details: Optional[Dict] = None):
        """
        Log performance metrics for optimization tracking.
        
        Args:
            component: Component being measured
            operation: Operation being measured
            duration_ms: Duration in milliseconds
            details: Additional performance details
        """
        perf_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "operation": operation,
            "duration_ms": duration_ms,
            "details": details or {}
        }
        
        # Log to performance file
        perf_log_data = []
        if os.path.exists(PERFORMANCE_LOG_FILE):
            try:
                with open(PERFORMANCE_LOG_FILE, "r") as f:
                    perf_log_data = json.load(f)
            except json.JSONDecodeError:
                perf_log_data = []
        
        perf_log_data.append(perf_entry)
        
        # Keep only last 500 performance entries
        if len(perf_log_data) > 500:
            perf_log_data = perf_log_data[-500:]
        
        with open(PERFORMANCE_LOG_FILE, "w") as f:
            json.dump(perf_log_data, f, indent=2)
        
        # Log to performance logger
        self.performance_logger.info(
            f"PERF - {component}.{operation} - Duration: {duration_ms:.2f}ms - {details}"
        )
    
    def get_security_events(self, username: str = None, event_type: str = None, 
                           hours_back: int = 24) -> List[Dict]:
        """
        Retrieve security events for analysis.
        
        Args:
            username: Filter by username (optional)
            event_type: Filter by event type (optional)
            hours_back: How many hours back to search (default 24)
            
        Returns:
            List of security events matching criteria
        """
        if not os.path.exists(SECURITY_LOG_FILE):
            return []
        
        try:
            with open(SECURITY_LOG_FILE, "r") as f:
                security_events = json.load(f)
        except json.JSONDecodeError:
            return []
        
        # Filter events
        filtered_events = []
        cutoff_time = datetime.now() - datetime.timedelta(hours=hours_back)
        
        for event in security_events:
            try:
                event_time = datetime.fromisoformat(event["timestamp"])
                if event_time < cutoff_time:
                    continue
                
                if username and event.get("username") != username:
                    continue
                
                if event_type and event.get("event_type") != event_type:
                    continue
                
                filtered_events.append(event)
                
            except (ValueError, KeyError):
                continue
        
        return filtered_events

# Global enhanced logger instance
_enhanced_logger_instance = None

def get_enhanced_logger() -> EnhancedLogger:
    """Get global enhanced logger instance"""
    global _enhanced_logger_instance
    if _enhanced_logger_instance is None:
        _enhanced_logger_instance = EnhancedLogger()
    return _enhanced_logger_instance

# Convenience functions that extend your existing API
def log_security_event(username: str, event_type: str, details: Dict, severity: str = "WARNING"):
    """Convenience function for security event logging"""
    enhanced_logger = get_enhanced_logger()
    enhanced_logger.log_security_event(username, event_type, details, severity)

def log_file_operation(username: str, operation: str, file_path: str, result: str, details: Dict = None):
    """Convenience function for file operation logging"""
    enhanced_logger = get_enhanced_logger()
    enhanced_logger.log_file_operation(username, operation, file_path, result, details)

def log_approval_action(admin_user: str, target_user: str, file_id: str, action: str, reason: str = None):
    """Convenience function for approval action logging"""
    enhanced_logger = get_enhanced_logger()
    enhanced_logger.log_approval_action(admin_user, target_user, file_id, action, reason)

def log_performance_metric(component: str, operation: str, duration_ms: float, details: Dict = None):
    """Convenience function for performance metric logging"""
    enhanced_logger = get_enhanced_logger()
    enhanced_logger.log_performance_metric(component, operation, duration_ms, details)

# Context manager for performance timing
class PerformanceTimer:
    """Context manager for automatic performance timing"""
    
    def __init__(self, component: str, operation: str, details: Dict = None):
        self.component = component
        self.operation = operation
        self.details = details or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
            log_performance_metric(self.component, self.operation, duration_ms, self.details)

# Example usage:
# with PerformanceTimer("FileResolver", "resolve_path", {"user_id": "john"}):
#     # Your code here
#     pass