"""Cryptographic hashing, password hashing, encoding, and secure random utilities for the Cosmic Standard Library."""
from __future__ import annotations
import hashlib
import hmac as _hmac
import secrets
import base64
import uuid
from typing import Any


def md5(data: str | bytes) -> str:
    """Return the MD5 hex digest of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()


def sha1(data: str | bytes) -> str:
    """Return the SHA-1 hex digest of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha1(data).hexdigest()


def sha256(data: str | bytes) -> str:
    """Return the SHA-256 hex digest of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def sha512(data: str | bytes) -> str:
    """Return the SHA-512 hex digest of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha512(data).hexdigest()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with PBKDF2 and return (hash, salt)."""
    if salt is None:
        salt = generate_salt(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash and salt."""
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, hashed)


def generate_salt(length: int = 16) -> str:
    """Generate a random hex salt of the given length."""
    return secrets.token_hex(length)


def hmac_sha256(key: str | bytes, message: str | bytes) -> str:
    """Return the HMAC-SHA256 hex digest."""
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(message, str):
        message = message.encode('utf-8')
    return _hmac.new(key, message, hashlib.sha256).hexdigest()


def random_bytes(n: int) -> bytes:
    """Generate n cryptographically random bytes."""
    return secrets.token_bytes(n)


def random_int(min_val: int = 0, max_val: int = 2**32 - 1) -> int:
    """Generate a cryptographically secure random integer in range."""
    if min_val > max_val:
        raise ValueError(f"random_int: min_val ({min_val}) must be <= max_val ({max_val})")
    return secrets.randbelow(max_val - min_val + 1) + min_val


def random_string(length: int = 16, alphabet: str | None = None) -> str:
    """Generate a random string of the given length from the alphabet."""
    if alphabet is None:
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def uuid4() -> str:
    """Return a random UUID4 string."""
    return str(uuid.uuid4())


def base64_encode(data: str | bytes) -> str:
    """Base64-encode data and return the ASCII string."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def base64_decode(data: str) -> bytes:
    """Base64-decode the string and return bytes."""
    return base64.b64decode(data)


def hex_encode(data: bytes) -> str:
    """Encode bytes as a hex string."""
    return data.hex()


def hex_decode(data: str) -> bytes:
    """Decode a hex string to bytes."""
    return bytes.fromhex(data)


def constant_time_compare(a: str | bytes, b: str | bytes) -> bool:
    """Compare two values in constant time to prevent timing attacks."""
    if isinstance(a, str):
        a = a.encode('utf-8')
    if isinstance(b, str):
        b = b.encode('utf-8')
    return secrets.compare_digest(a, b)


def xor_bytes(a: bytes, b: bytes) -> bytes:
    """XOR two byte sequences together."""
    return bytes(x ^ y for x, y in zip(a, b))


def tokenize(data: str, key: str) -> str:
    """Create an HMAC-signed token from data and key."""
    import hmac as _hmac
    import hashlib
    sig = _hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}:{sig}"


def detokenize(token: str, key: str) -> str | None:
    """Verify and extract data from an HMAC-signed token."""
    import hmac as _hmac
    import hashlib
    parts = token.rsplit(':', 1)
    if len(parts) != 2:
        return None
    data, sig = parts
    expected = _hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    if _hmac.compare_digest(sig, expected):
        return data
    return None
