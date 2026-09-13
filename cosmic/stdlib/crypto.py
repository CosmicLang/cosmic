"""Cosmic Standard Library — crypto module."""
from __future__ import annotations
import hashlib
import hmac as _hmac
import secrets
import base64
import uuid
from typing import Any


def md5(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()


def sha1(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha1(data).hexdigest()


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def sha512(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha512(data).hexdigest()


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = generate_salt(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, hashed)


def generate_salt(length: int = 16) -> str:
    return secrets.token_hex(length)


def hmac_sha256(key: str | bytes, message: str | bytes) -> str:
    if isinstance(key, str):
        key = key.encode('utf-8')
    if isinstance(message, str):
        message = message.encode('utf-8')
    return _hmac.new(key, message, hashlib.sha256).hexdigest()


def random_bytes(n: int) -> bytes:
    return secrets.token_bytes(n)


def random_int(min_val: int = 0, max_val: int = 2**32 - 1) -> int:
    return secrets.randbelow(max_val - min_val + 1) + min_val


def random_string(length: int = 16, alphabet: str | None = None) -> str:
    if alphabet is None:
        alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def uuid4() -> str:
    return str(uuid.uuid4())


def base64_encode(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def base64_decode(data: str) -> bytes:
    return base64.b64decode(data)


def hex_encode(data: bytes) -> str:
    return data.hex()


def hex_decode(data: str) -> bytes:
    return bytes.fromhex(data)


def constant_time_compare(a: str | bytes, b: str | bytes) -> bool:
    if isinstance(a, str):
        a = a.encode('utf-8')
    if isinstance(b, str):
        b = b.encode('utf-8')
    return secrets.compare_digest(a, b)


def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def tokenize(data: str, key: str) -> str:
    import hmac as _hmac
    import hashlib
    sig = _hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}:{sig}"


def detokenize(token: str, key: str) -> str | None:
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
