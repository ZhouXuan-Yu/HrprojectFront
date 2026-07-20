"""AES-256-GCM encryption for sensitive config values."""
import os
import hashlib
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _derive_key(secret_key: str) -> bytes:
    return hashlib.sha256(secret_key.encode()).digest()


def encrypt(plaintext: str, secret_key: str) -> str:
    key = _derive_key(secret_key)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    # Return hex-encoded nonce + ciphertext
    return (nonce + ciphertext).hex()


def decrypt(hex_value: str, secret_key: str) -> str:
    key = _derive_key(secret_key)
    raw = bytes.fromhex(hex_value)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
