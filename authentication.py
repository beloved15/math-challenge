"""
authentication.py
------------------
Handles password hashing/verification and login/registration validation
logic. Kept separate from the UI so it can be unit-tested independently.
"""

import re
import hashlib
import hmac
import os

import database_manager as db

# Admin credentials are configurable via environment variables so they are
# never hard-coded in source control for a real deployment.
ADMIN_USERNAME = os.environ.get("QUIZ_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("QUIZ_ADMIN_PASSWORD", "admin123")


def hash_password(password: str) -> str:
    """Salt + hash a password using PBKDF2-HMAC-SHA256.
    Format stored: salt_hex$hash_hex"""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${hashed.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a plaintext password against a stored salt$hash string."""
    try:
        salt_hex, hash_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(candidate, expected)
    except (ValueError, AttributeError):
        return False


def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email or "") is not None


def is_valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", phone or "")
    return 7 <= len(digits) <= 15


def is_strong_password(password: str) -> bool:
    """Require at least 6 characters. Kept simple/friendly for a quiz app."""
    return bool(password) and len(password) >= 6


def register_user(username, full_name, email, phone, password, confirm_password):
    """Validate registration inputs and create the user.
    Returns (success: bool, message: str)."""
    username = (username or "").strip()
    full_name = (full_name or "").strip()
    email = (email or "").strip()
    phone = (phone or "").strip()

    if not username or not full_name or not email or not phone or not password:
        return False, "Please fill in all fields."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return False, "Username may only contain letters, numbers, and underscores."
    if db.username_exists(username):
        return False, "That username is already taken. Please choose another."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    if db.email_exists(email):
        return False, "An account with that email already exists."
    if not is_valid_phone(phone):
        return False, "Please enter a valid phone number."
    if not is_strong_password(password):
        return False, "Password must be at least 6 characters long."
    if password != confirm_password:
        return False, "Passwords do not match."

    db.create_user(username, full_name, email, phone, hash_password(password))
    return True, "Registration successful! You can now log in."


def login_user(username, password):
    """Validate login credentials.
    Returns (success: bool, message: str, user_row or None)."""
    if not username or not password:
        return False, "Please enter both username and password.", None

    user = db.get_user(username)
    if user is None:
        return False, "No account found with that username.", None
    if not verify_password(password, user["Password"]):
        return False, "Incorrect password. Please try again.", None
    return True, "Login successful!", user


def login_admin(username, password):
    """Simple, separate admin login check."""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, "Admin login successful!"
    return False, "Invalid admin credentials."
