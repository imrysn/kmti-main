import json
from typing import Optional

def validate_login(username: str, password: str, is_admin: bool) -> Optional[str]:
    with open("data/users.json", "r") as f:
        users = json.load(f)
    user = users.get(username)
    if user and user["password"] == password:
        return user["role"]
    return None
