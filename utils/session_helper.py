def safe_session_get(page, key, default=None):
    """Safely get session value with default fallback for older Flet versions"""
    try:
        # Try newer API first
        return page.session.get(key, default)
    except TypeError:
        # Fallback for older Flet versions
        try:
            value = page.session.get(key)
            return value if value is not None else default
        except:
            return default

def safe_session_set(page, key, value):
    """Safely set session value"""
    try:
        page.session.set(key, value)
        return True
    except Exception as e:
        print(f"Warning: Failed to set session key {key}: {e}")
        return False

def safe_session_contains(page, key):
    """Check if session contains key"""
    try:
        return page.session.contains_key(key)
    except:
        # Fallback - try to get the value
        try:
            value = page.session.get(key)
            return value is not None
        except:
            return False