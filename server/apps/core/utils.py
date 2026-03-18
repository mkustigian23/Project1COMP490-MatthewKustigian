import re

def is_valid_email(email):
    """
    Check if the given email address is valid.

    Parameters:
    - email (str): The email address to validate.

    Returns:
    - bool: True if the email is valid, False otherwise.
    """
    # Regular expression for a valid email address
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Use re.match() to check if the email matches the pattern
    if re.match(email_regex, email):
        return True
    else:
        return False
