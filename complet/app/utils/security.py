import secrets
import string


def generate_temp_password(length=10):
    """Generate a random temporary password for newly created accounts."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
