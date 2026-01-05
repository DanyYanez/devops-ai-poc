"""
Input validation module for user data.
"""

def validate_email(email):
    """Check if email format is valid."""
    if not email:
        return False
    if "@" not in email:
        return False
    if "." not in email.split("@")[1]:
        return False
    return True


def validate_age(age):
    """Check if age is valid."""
    if not isinstance(age, int):
        return False
    if age < 0 or age > 150:
        return False
    return True


def validate_username(username):
    """Check if username meets requirements."""
    if not username:
        return False
    if len(username) < 3:
        return False
    if len(username) > 20:
        return False
    if not username.isalnum():
        return False
    return True