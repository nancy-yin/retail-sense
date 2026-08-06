#!/usr/bin/env python3
"""
Admin Credential Manager
========================
Manages admin credentials stored in .auth/admin_cred.json.
Passwords are always SHA-256 hashed — never stored in plaintext.

Usage:
  python3 scripts/auth_manager.py verify <password>
  python3 scripts/auth_manager.py change-password <old_password> <new_password>
  python3 scripts/auth_manager.py set-password <new_password>
  python3 scripts/auth_manager.py show
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Resolve project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRED_FILE = PROJECT_ROOT / ".auth" / "admin_cred.json"
DESKTOP_FILE = Path(os.path.expanduser("~/Desktop/📊日上/账号密码.json"))


def _load_cred() -> dict:
    """Load credentials from the JSON file."""
    if not CRED_FILE.exists():
        raise FileNotFoundError(f"Credential file not found: {CRED_FILE}")
    with open(CRED_FILE, "r") as f:
        return json.load(f)


def _save_cred(cred: dict) -> None:
    """Save credentials to JSON. Writes to both .auth/ and Desktop."""
    tmp = CRED_FILE.with_suffix(".tmp")
    CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w") as f:
        json.dump(cred, f, indent=2)
        f.write("\n")
    os.replace(tmp, CRED_FILE)
    # Sync to Desktop
    DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DESKTOP_FILE, "w") as f:
        json.dump({"admin":{"password":"******","role":"管理员","note":"密码已加密存储在项目 .auth/ 中"}}, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _hash(password: str) -> str:
    """Return SHA-256 hex digest of the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str) -> bool:
    """Check whether `password` matches the stored hash."""
    cred = _load_cred()
    stored_hash = cred.get("password_hash", "")
    return _hash(password) == stored_hash


def change_password(old_password: str, new_password: str) -> bool:
    """
    Change the admin password.
    Requires the current password to proceed. Returns True on success.
    """
    if not verify_password(old_password):
        return False
    cred = _load_cred()
    cred["password_hash"] = _hash(new_password)
    _save_cred(cred)
    return True


def set_password(new_password: str) -> None:
    """Force-set a new password (no old-password check)."""
    cred = _load_cred() if CRED_FILE.exists() else {"username": "admin"}
    cred["password_hash"] = _hash(new_password)
    _save_cred(cred)


def show_info() -> dict:
    """Return credential info (without the hash)."""
    cred = _load_cred()
    return {"username": cred.get("username", "admin")}


# ── CLI ──────────────────────────────────────────────────────────────────────

def _print_usage():
    script = sys.argv[0] if sys.argv else "auth_manager.py"
    print(f"Usage:")
    print(f"  python3 {script} verify <password>")
    print(f"  python3 {script} change-password <old_password> <new_password>")
    print(f"  python3 {script} set-password <new_password>")
    print(f"  python3 {script} show")


def main():
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "verify":
            if len(sys.argv) != 3:
                print("ERROR: 'verify' requires exactly one password argument", file=sys.stderr)
                sys.exit(2)
            ok = verify_password(sys.argv[2])
            if ok:
                print("✓ Password verified successfully.")
            else:
                print("✗ Password does NOT match.")
                sys.exit(1)

        elif cmd == "change-password":
            if len(sys.argv) != 4:
                print("ERROR: 'change-password' requires <old_password> <new_password>", file=sys.stderr)
                sys.exit(2)
            ok = change_password(sys.argv[2], sys.argv[3])
            if ok:
                print("✓ Password changed successfully.")
            else:
                print("✗ Old password is incorrect. Change aborted.", file=sys.stderr)
                sys.exit(1)

        elif cmd == "set-password":
            if len(sys.argv) != 3:
                print("ERROR: 'set-password' requires exactly one password argument", file=sys.stderr)
                sys.exit(2)
            set_password(sys.argv[2])
            print("✓ Password has been set (force).")

        elif cmd == "show":
            info = show_info()
            print(f"Username: {info['username']}")
            print(f"Credential file: {CRED_FILE}")

        else:
            print(f"ERROR: Unknown command '{cmd}'", file=sys.stderr)
            _print_usage()
            sys.exit(2)

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
