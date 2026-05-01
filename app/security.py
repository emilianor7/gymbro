import hashlib
import hmac
import os
from base64 import b64encode, b64decode

# Implementacion simple sin dependencias externas: PBKDF2-HMAC-SHA256.
# Si despues queres bcrypt o argon2 cambias esto y listo.
_ITERATIONS = 200_000
_SALT_BYTES = 16
_DIGEST = "sha256"


def hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_DIGEST, password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2${_DIGEST}${_ITERATIONS}${b64encode(salt).decode()}${b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, digest, iters, salt_b64, hash_b64 = stored.split("$")
        if scheme != "pbkdf2":
            return False
        salt = b64decode(salt_b64)
        expected = b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac(digest, password.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False
