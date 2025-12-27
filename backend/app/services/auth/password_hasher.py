"""Password hashing + verification with safe fallbacks for production.

Why this exists:
- Render is currently running Python 3.12 with `bcrypt` versions that are not fully
  compatible with `passlib`'s bcrypt backend detection (it triggers a >72-byte test
  password during init and can throw).
- We still need to support legacy password hashes already stored in the DB.

Strategy:
- NEW hashes: `pbkdf2_sha256` (doesn't rely on the bcrypt backend).
- LEGACY verify:
  - `$2...` (bcrypt) via `bcrypt.checkpw()` (with 72-byte truncation).
  - `$bcrypt-sha256$...` (passlib bcrypt_sha256) verified via a lightweight
    re-implementation using stdlib `hmac` + `base64` + `bcrypt.checkpw()`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import bcrypt
from passlib.hash import pbkdf2_sha256

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PasswordHasher:
    """Hash and verify passwords with production-safe defaults."""

    def hash_password(self, password: str) -> str:
        # PBKDF2 is stable on Render/Python 3.12 and doesn't depend on bcrypt backend detection.
        return pbkdf2_sha256.hash(password)

    def verify_and_update_password(self, plain_password: str, hashed_password: str) -> Tuple[bool, Optional[str]]:
        """Verify a password and optionally return an upgraded hash.

        Returns:
          (is_valid, new_hash_or_none)
        """
        if not hashed_password:
            return False, None

        try:
            if hashed_password.startswith("$pbkdf2-sha256$"):
                return pbkdf2_sha256.verify(plain_password, hashed_password), None

            if hashed_password.startswith("$bcrypt-sha256$"):
                ok = self._verify_passlib_bcrypt_sha256(plain_password, hashed_password)
                return (ok, self.hash_password(plain_password)) if ok else (False, None)

            if hashed_password.startswith("$2"):
                ok, upgrade_safe = self._verify_legacy_bcrypt(plain_password, hashed_password)
                if not ok:
                    return False, None
                return (True, self.hash_password(plain_password)) if upgrade_safe else (True, None)
        except Exception as e:
            # Never explode auth flows on hash parsing errors.
            logger.warning("Password verification failed due to exception: %s", e)
            return False, None

        # Unknown/unsupported hash format.
        return False, None

    # ------------------------------------------------------------------
    # Legacy bcrypt ($2a$ / $2b$ / $2y$ ...)
    # ------------------------------------------------------------------

    def _verify_legacy_bcrypt(self, password: str, bcrypt_hash: str) -> Tuple[bool, bool]:
        """Verify a legacy bcrypt hash.

        Returns:
          (ok, upgrade_safe)

        Notes:
        - Bcrypt only considers the first 72 bytes of the password.
        - If user provided a >72-byte password, verification is done against the
          truncated bytes and we *do not* auto-upgrade (suffix ambiguity).
        """
        password_bytes = password.encode("utf-8")
        upgrade_safe = len(password_bytes) <= 72
        if not upgrade_safe:
            password_bytes = password_bytes[:72]

        try:
            ok = bcrypt.checkpw(password_bytes, bcrypt_hash.encode("utf-8"))
            return ok, upgrade_safe
        except ValueError:
            # bcrypt lib raises ValueError on invalid salts/hashes or other parsing issues.
            return False, False

    # ------------------------------------------------------------------
    # Legacy passlib bcrypt_sha256 ($bcrypt-sha256$...)
    # ------------------------------------------------------------------

    def _verify_passlib_bcrypt_sha256(self, password: str, full_hash: str) -> bool:
        """Verify passlib's `$bcrypt-sha256$` hashes without importing passlib bcrypt handlers.

        Passlib algorithm reference (from passlib source):
        - v=1: digest = sha256(password).digest()
        - v=2: digest = HMAC-SHA256(key=salt_string_ascii, msg=password_bytes)
        - key = base64.b64encode(digest)  # 44 bytes
        - bcrypt(key) against the bcrypt salt/checksum embedded in the hash string
        """
        parts = full_hash.split("$")
        # Expected: ['', 'bcrypt-sha256', 'v=2,t=2b,r=12', '<salt>', '<checksum>']
        if len(parts) != 5 or parts[1] != "bcrypt-sha256":
            return False

        params_raw = parts[2]
        salt = parts[3]
        checksum = parts[4]
        params: dict[str, str] = {}
        for kv in params_raw.split(","):
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            params[k.strip()] = v.strip()

        try:
            version = int(params.get("v", "2"))
            bcrypt_type = params.get("t", "2b")
            rounds = int(params.get("r", "12"))
        except ValueError:
            return False

        # Reconstruct bcrypt hash: $2b$12$<salt><checksum>
        dollar = chr(36)
        bcrypt_hash = dollar + bcrypt_type + dollar + f"{rounds:02d}" + dollar + salt + checksum

        secret = password.encode("utf-8")
        if version == 1:
            digest = hashlib.sha256(secret).digest()
        else:
            digest = hmac.new(salt.encode("ascii"), secret, hashlib.sha256).digest()

        key = base64.b64encode(digest)
        try:
            return bcrypt.checkpw(key, bcrypt_hash.encode("ascii"))
        except ValueError:
            return False


