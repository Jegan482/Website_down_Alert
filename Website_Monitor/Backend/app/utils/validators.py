# app/utils/validators.py

import re

# Simple mail format check
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email: str) -> bool:
    """
    Basic email validation.
    Example valid:
        user@example.com
        test.user123@gmail.com
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email))
