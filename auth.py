import hashlib

from database import create_user, get_user_by_username


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def signup_user(username: str, password: str):
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    success, _ = create_user(username, hash_password(password))
    if not success:
        return False, "Username already exists."
    return True, "Account created successfully. Please login."


def login_user(username: str, password: str):
    user = get_user_by_username(username.strip())
    if not user:
        return False, None
    if user["password_hash"] != hash_password(password):
        return False, None
    return True, user