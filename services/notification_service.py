import os
import json
from datetime import datetime
from typing import Dict, List

class NotificationService:
    """Service to handle notifications between admin and users"""
    
    def __init__(self):
        self.notifications_dir = "data/notifications"
        os.makedirs(self.notifications_dir, exist_ok=True)
    
    def notify_approval_status(self, username: str, filename: str, status: str, admin_id: str, reason: str = ""):
        """Send approval status notification to user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            # Load existing notifications
            notifications = []
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    data = json.load(f)
                    notifications = data if isinstance(data, list) else []
            
            # Create notification
            notification = {
                'type': 'approval_status',
                'filename': filename,
                'status': status,
                'admin_id': admin_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }
            
            # Add to beginning of list
            notifications.insert(0, notification)
            
            # Keep only last 100 notifications
            notifications = notifications[:100]
            
            # Save notifications
            os.makedirs(user_folder, exist_ok=True)
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            print(f"Notification sent to {username}: {filename} - {status}")
            return True
            
        except Exception as e:
            print(f"Error sending notification to {username}: {e}")
            return False
    
    def notify_comment_added(self, username: str, filename: str, admin_id: str, comment: str):
        """Send comment notification to user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            # Load existing notifications
            notifications = []
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    data = json.load(f)
                    notifications = data if isinstance(data, list) else []
            
            # Create notification
            notification = {
                'type': 'comment_added',
                'filename': filename,
                'admin_id': admin_id,
                'comment': comment,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }
            
            # Add to beginning of list
            notifications.insert(0, notification)
            
            # Keep only last 100 notifications
            notifications = notifications[:100]
            
            # Save notifications
            os.makedirs(user_folder, exist_ok=True)
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            print(f"Comment notification sent to {username}: {comment[:50]}...")
            return True
            
        except Exception as e:
            print(f"Error sending comment notification to {username}: {e}")
            return False
    
    def get_user_notifications(self, username: str) -> List[Dict]:
        """Get all notifications for a user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            
        except Exception as e:
            print(f"Error getting notifications for {username}: {e}")
        
        return []
    
    def mark_notification_read(self, username: str, notification_index: int) -> bool:
        """Mark a specific notification as read"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                    if isinstance(notifications, list) and 0 <= notification_index < len(notifications):
                        notifications[notification_index]['read'] = True
                        
                        with open(notifications_file, 'w') as f:
                            json.dump(notifications, f, indent=2)
                        
                        return True
            
        except Exception as e:
            print(f"Error marking notification as read for {username}: {e}")
        
        return False
    
    def mark_all_notifications_read(self, username: str) -> bool:
        """Mark all notifications as read for a user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                    if isinstance(notifications, list):
                        for notification in notifications:
                            notification['read'] = True
                        
                        with open(notifications_file, 'w') as f:
                            json.dump(notifications, f, indent=2)
                        
                        return True
            
        except Exception as e:
            print(f"Error marking all notifications as read for {username}: {e}")
        
        return False
    
    def get_unread_count(self, username: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            notifications = self.get_user_notifications(username)
            return len([n for n in notifications if not n.get('read', False)])
        except Exception as e:
            print(f"Error getting unread count for {username}: {e}")
            return 0
    
    def send_system_notification(self, username: str, title: str, message: str, notification_type: str = "system"):
        """Send a system notification to a user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            # Load existing notifications
            notifications = []
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    data = json.load(f)
                    notifications = data if isinstance(data, list) else []
            
            # Create system notification
            notification = {
                'type': notification_type,
                'title': title,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }
            
            # Add to beginning of list
            notifications.insert(0, notification)
            
            # Keep only last 100 notifications
            notifications = notifications[:100]
            
            # Save notifications
            os.makedirs(user_folder, exist_ok=True)
            with open(notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            print(f"System notification sent to {username}: {title}")
            return True
            
        except Exception as e:
            print(f"Error sending system notification to {username}: {e}")
            return False
    
    def broadcast_notification(self, title: str, message: str, notification_type: str = "broadcast"):
        """Send notification to all users"""
        try:
            users_file = "data/users.json"
            if not os.path.exists(users_file):
                return False
            
            with open(users_file, 'r') as f:
                users = json.load(f)
            
            success_count = 0
            for email, user_data in users.items():
                username = user_data.get('username')
                if username:
                    if self.send_system_notification(username, title, message, notification_type):
                        success_count += 1
            
            print(f"Broadcast notification sent to {success_count} users")
            return success_count > 0
            
        except Exception as e:
            print(f"Error broadcasting notification: {e}")
            return False
    
    def cleanup_old_notifications(self, username: str, days: int = 30) -> bool:
        """Clean up old notifications for a user"""
        try:
            user_folder = f"data/uploads/{username}"
            notifications_file = os.path.join(user_folder, "approval_notifications.json")
            
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                    if isinstance(notifications, list):
                        cutoff_date = datetime.now()
                        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
                        
                        # Filter out old notifications
                        filtered_notifications = []
                        for notification in notifications:
                            try:
                                timestamp = datetime.fromisoformat(notification['timestamp'])
                                if timestamp >= cutoff_date:
                                    filtered_notifications.append(notification)
                            except:
                                # Keep notifications with invalid timestamps
                                filtered_notifications.append(notification)
                        
                        if len(filtered_notifications) != len(notifications):
                            with open(notifications_file, 'w') as f:
                                json.dump(filtered_notifications, f, indent=2)
                            print(f"Cleaned up {len(notifications) - len(filtered_notifications)} old notifications for {username}")
                        
                        return True
            
        except Exception as e:
            print(f"Error cleaning up notifications for {username}: {e}")
        
        return False
    
    def get_notification_summary(self, username: str) -> Dict:
        """Get summary of notifications for a user"""
        try:
            notifications = self.get_user_notifications(username)
            
            summary = {
                'total': len(notifications),
                'unread': 0,
                'approval_status': 0,
                'comments': 0,
                'system': 0
            }
            
            for notification in notifications:
                if not notification.get('read', False):
                    summary['unread'] += 1
                
                notification_type = notification.get('type', 'system')
                if notification_type == 'approval_status':
                    summary['approval_status'] += 1
                elif notification_type == 'comment_added':
                    summary['comments'] += 1
                else:
                    summary['system'] += 1
            
            return summary
            
        except Exception as e:
            print(f"Error getting notification summary for {username}: {e}")
            return {'total': 0, 'unread': 0, 'approval_status': 0, 'comments': 0, 'system': 0}
