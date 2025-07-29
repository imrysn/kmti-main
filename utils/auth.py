import json
import os
import hashlib

USERS_FILE = "data/users.json"

def hash_password(password: str | None) -> str:
    """Return the SHA-256 hash of a password."""
    if password is None:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_plain_passwords(users):
    """
    If any stored password is plain text (not a 64-char SHA256 hex), convert it to hash.
    """
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
    """Load users from JSON file, migrate if necessary."""
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
    """
    Validate login credentials.
    Returns "admin", "user", or None if invalid.
    """
    users = load_users()
    entered_hash = hash_password(password)

    for email, data in users.items():
        stored_hash = data.get("password", "")

        # Allow login by either username or email
        if username_or_email == email or username_or_email == data.get("username", ""):
            # Compare hashed password (support migration)
            if entered_hash == stored_hash or password == stored_hash:
                role = data.get("role", "").lower()
                return role
    return None
