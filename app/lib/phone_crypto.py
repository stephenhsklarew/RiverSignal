"""AES-GCM encryption for phone numbers at rest.

Phone numbers are PII with regulatory implications under both US TCPA
and Canadian CASL. We store ciphertext in users.phone_number_e164_encrypted
and reconstruct the plain-text only at the moment of SMS dispatch.

Key management:
  - 32-byte (AES-256) key stored as Secret Manager secret SMS_ENCRYPTION_KEY
  - Loaded once at process start via env var SMS_ENCRYPTION_KEY (base64 or hex)
  - Rotation: bump key version in Secret Manager, redeploy. Old ciphertexts
    can be migrated by a one-off rotation script (deferred until needed).

Format:
  ciphertext = nonce (12 bytes) || aesgcm_encrypted_payload
  Stored as raw bytes in a `bytea` column.
"""
from __future__ import annotations

import base64
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_NONCE_LEN = 12  # AES-GCM standard nonce length


@lru_cache(maxsize=1)
def _key() -> bytes:
    """Load the AES key from env at first access. Cached for process lifetime."""
    raw = os.environ.get("SMS_ENCRYPTION_KEY")
    if not raw:
        raise RuntimeError(
            "SMS_ENCRYPTION_KEY env var is missing. Set it from Secret Manager."
        )
    # Accept either hex or base64 encoding. Both produce 32 bytes for AES-256.
    raw = raw.strip()
    try:
        if len(raw) == 64:  # hex
            key = bytes.fromhex(raw)
        else:                # base64
            key = base64.b64decode(raw)
    except Exception as exc:
        raise RuntimeError(
            "SMS_ENCRYPTION_KEY must be 32 bytes encoded as hex (64 chars) or base64."
        ) from exc
    if len(key) != 32:
        raise RuntimeError(
            f"SMS_ENCRYPTION_KEY decoded to {len(key)} bytes; expected 32 (AES-256)."
        )
    return key


def encrypt_phone(phone_e164: str) -> bytes:
    """Encrypt a +1NXXNXXXXXX phone number to opaque ciphertext bytes."""
    if not phone_e164:
        raise ValueError("phone_e164 must be non-empty")
    aesgcm = AESGCM(_key())
    nonce = os.urandom(_NONCE_LEN)
    ct = aesgcm.encrypt(nonce, phone_e164.encode("utf-8"), None)
    return nonce + ct


def decrypt_phone(blob: bytes) -> str:
    """Decrypt a ciphertext produced by encrypt_phone back to its E.164 string."""
    if not blob or len(blob) <= _NONCE_LEN:
        raise ValueError("blob is too short to contain nonce + ciphertext")
    nonce, ct = blob[:_NONCE_LEN], blob[_NONCE_LEN:]
    aesgcm = AESGCM(_key())
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


def hash_phone_for_lookup(phone_e164: str) -> bytes:
    """Produce a deterministic, key-bound hash of a phone for lookup queries.

    AES-GCM is non-deterministic (random nonce), so two encryptions of the
    same number produce different ciphertexts. To query "is this phone
    already registered?", we need a deterministic value. SHA-256(key || phone)
    is collision-resistant and key-bound so different deployments can't
    cross-reference, but is consistent within the same deployment.
    """
    import hashlib
    h = hashlib.sha256()
    h.update(_key())
    h.update(b":")
    h.update(phone_e164.encode("utf-8"))
    return h.digest()
