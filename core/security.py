from __future__ import annotations

import base64
import os
import secrets
from dataclasses import dataclass
from typing import Optional

import pyotp
import bcrypt as bcrypt_lib  # ← FIXED: Use bcrypt directly
from cryptography.fernet import Fernet

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
LOCAL_DIR = os.path.join(ROOT_DIR, ".local")
KEY_PATH = os.path.join(LOCAL_DIR, "key.key")

def _ensure_key() -> bytes:
    os.makedirs(LOCAL_DIR, exist_ok=True)
    if not os.path.exists(KEY_PATH):
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_PATH, 0o600)
        except Exception:
            # Windows may not support chmod the same way; ok for demo.
            pass
    with open(KEY_PATH, "rb") as f:
        return f.read()

def get_fernet() -> Fernet:
    key = _ensure_key()
    return Fernet(key)

# -------- PIN hashing --------
def hash_pin(pin: str) -> str:
    """Hash a PIN using bcrypt (with automatic salt)"""
    pin_bytes = pin[:72].encode('utf-8')
    hashed = bcrypt_lib.hashpw(pin_bytes, bcrypt_lib.gensalt(rounds=12))
    return hashed.decode('utf-8')

def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify a PIN against its hash"""
    try:
        pin_bytes = pin[:72].encode('utf-8')
        pin_hash_bytes = pin_hash.encode('utf-8')
        return bcrypt_lib.checkpw(pin_bytes, pin_hash_bytes)
    except Exception:
        return False

# -------- encryption for sensitive columns --------
def encrypt_text(plaintext: str) -> bytes:
    f = get_fernet()
    return f.encrypt(plaintext.encode("utf-8"))

def decrypt_text(ciphertext: bytes) -> str:
    f = get_fernet()
    return f.decrypt(ciphertext).decode("utf-8")

# -------- TOTP 2FA --------
def generate_totp_secret() -> str:
    # Base32 secret
    return pyotp.random_base32()

def verify_totp(code: str, secret: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

def totp_uri(display_name: str, secret: str, issuer: str = "CycleSenseLocal") -> str:
    totp = pyotp.TOTP(secret)
    # URI that can be converted to QR later (optional)
    return totp.provisioning_uri(name=display_name, issuer_name=issuer)

# -------- Email OTP (demo-local) --------
@dataclass
class EmailOtp:
    code: str
    expires_in_seconds: int = 300

def generate_email_otp() -> EmailOtp:
    # 6-digit OTP
    code = f"{secrets.randbelow(1_000_000):06d}"
    return EmailOtp(code=code, expires_in_seconds=300)
