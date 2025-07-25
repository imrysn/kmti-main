import json

def validate_login(username, password):
    with open("data/users.json", "r") as f:
        users = json.load(f)
    user = users.get(username)
    if user and user["password"] == password:
        return user["role"]
    return None
