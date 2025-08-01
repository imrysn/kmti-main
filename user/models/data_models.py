from typing import List, Dict

class ProjectData:
    """Static data for projects - in a real app this would come from database"""
    
    @staticmethod
    def get_projects() -> List[Dict]:
        return [
            {"name": "AGCC Project", "type": "folder"},
            {"name": "DAIICHI", "type": "folder"},
            {"name": "KMTI PJ", "type": "folder"},
            {"name": "KUSAKABE", "type": "folder"},
            {"name": "Minatogumi", "type": "folder"},
            {"name": "SOLIDWORKS", "type": "folder"},
            {"name": "WINDSMILE", "type": "folder"}
        ]

class UserData:
    """Default user data structure"""
    
    @staticmethod
    def get_default_user() -> Dict:
        return {
            "full_name": "Nicolas Ayin",
            "email": "nicolasayin@gmail.com",
            "role": "User",
            "join_date": "July 16, 2025"
        }