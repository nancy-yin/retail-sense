import hashlib
import json
import os

from retail_sense import auth
from retail_sense.security import hash_password, needs_rehash, verify_password
from retail_sense.text_safety import csv_safe, escape_html, safe_filename


def test_password_hash_is_salted_and_legacy_hash_is_supported():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    legacy = hashlib.sha256(b"legacy-password").hexdigest()

    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong", first)
    assert verify_password("legacy-password", legacy)
    assert needs_rehash(legacy)
    assert not needs_rehash(first)


def test_registration_rejects_markup_and_securely_saves_credentials(tmp_path, monkeypatch):
    auth_dir = tmp_path / ".auth"
    monkeypatch.setattr(auth, "AUTH_DIR", str(auth_dir))
    monkeypatch.setattr(auth, "ADMIN_CRED_PATH", str(auth_dir / "admin_cred.json"))
    monkeypatch.setattr(auth, "USERS_PATH", str(auth_dir / "users.json"))
    monkeypatch.setattr(auth, "PLATFORM_CONFIG_PATH", str(auth_dir / "platform_config.json"))

    ok, _ = auth.register_user("<b>name</b>", "valid-password")
    assert not ok

    ok, _ = auth.register_user("nancy.user", "valid-password")
    assert ok
    login_ok, _, role = auth.check_login("nancy.user", "valid-password")
    assert login_ok and role == "user"

    stored = json.loads((auth_dir / "users.json").read_text(encoding="utf-8"))
    assert stored["nancy.user"].startswith("pbkdf2_sha256$")

    legacy_admin_hash = hashlib.sha256(b"legacy-admin-password").hexdigest()
    auth.save_admin({"username": "admin", "password_hash": legacy_admin_hash})
    admin_ok, _, admin_role = auth.check_login("admin", "legacy-admin-password")
    migrated_admin = json.loads(
        (auth_dir / "admin_cred.json").read_text(encoding="utf-8")
    )
    assert admin_ok and admin_role == "admin"
    assert migrated_admin["password_hash"].startswith("pbkdf2_sha256$")

    assert os.stat(auth_dir).st_mode & 0o777 == 0o700
    assert os.stat(auth_dir / "users.json").st_mode & 0o777 == 0o600


def test_output_safety_helpers():
    assert escape_html('<img src=x onerror="alert(1)">').startswith("&lt;img")
    assert csv_safe("=HYPERLINK(\"bad\")").startswith("'")
    assert csv_safe("  +1+1").startswith("'")
    assert csv_safe("普通商品") == "普通商品"
    assert "/" not in safe_filename("../危险/报告")
