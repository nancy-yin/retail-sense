"""密码哈希与校验工具。兼容旧 SHA-256 哈希以支持平滑迁移。"""

from __future__ import annotations

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """使用随机盐和 PBKDF2-HMAC-SHA256 生成版本化密码哈希。"""
    if not isinstance(password, str) or not password:
        raise ValueError("密码不能为空")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def _is_legacy_hash(stored_hash: str) -> bool:
    return len(stored_hash) == 64 and all(
        character in "0123456789abcdef" for character in stored_hash.lower()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """校验新版 PBKDF2 哈希或项目旧版无盐 SHA-256 哈希。"""
    if not password or not stored_hash:
        return False
    if _is_legacy_hash(stored_hash):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored_hash.lower())
    try:
        algorithm, iteration_text, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != ALGORITHM:
            return False
        iterations = int(iteration_text)
        if iterations <= 0:
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """旧格式、弱迭代次数或损坏格式均需重新生成哈希。"""
    try:
        algorithm, iteration_text, _, _ = stored_hash.split("$", 3)
        return algorithm != ALGORITHM or int(iteration_text) < ITERATIONS
    except (AttributeError, ValueError):
        return True
