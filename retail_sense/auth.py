"""
RetailSense — 登录/认证/会话管理
Authentication & Session Management
"""
import copy
import json
import os
import re
import tempfile
import time

import streamlit as st

from retail_sense.runtime import is_read_only_demo
from retail_sense.security import hash_password, needs_rehash, verify_password

# ── 文件路径 ──
AUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".auth")
ADMIN_CRED_PATH = os.path.join(AUTH_DIR, "admin_cred.json")
USERS_PATH = os.path.join(AUTH_DIR, "users.json")


def _ensure_dir():
    """确保 .auth 目录存在"""
    os.makedirs(AUTH_DIR, exist_ok=True)
    os.chmod(AUTH_DIR, 0o700)


def _load_json(path: str, default: dict) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else default
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _write_json_secure(path: str, value: dict) -> None:
    """以原子替换方式写入本地敏感配置，并限制为当前用户可读写。"""
    _ensure_dir()
    file_descriptor, temp_path = tempfile.mkstemp(dir=AUTH_DIR, prefix=".tmp-")
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def load_admin() -> dict | None:
    """加载管理员凭证"""
    admin = _load_json(ADMIN_CRED_PATH, {})
    return admin or None


def save_admin(admin: dict) -> None:
    """安全保存管理员凭证。"""
    _write_json_secure(ADMIN_CRED_PATH, admin)


def load_users() -> dict:
    """加载普通用户列表 {username: password_hash}"""
    _ensure_dir()
    return _load_json(USERS_PATH, {})


def save_users(users: dict):
    """保存普通用户列表"""
    _write_json_secure(USERS_PATH, users)


def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    注册普通用户
    返回 (success, message)
    """
    username = username.strip()
    if not username or not password:
        return False, "用户名和密码不能为空 / Username and password cannot be empty"
    if not 2 <= len(username) <= 32:
        return False, "用户名需为 2–32 个字符 / Username must be 2–32 characters"
    if not re.fullmatch(r"[\w.-]+", username, flags=re.UNICODE):
        return False, "用户名仅支持文字、数字、下划线、点和短横线 / Invalid username characters"
    if not 8 <= len(password) <= 128:
        return False, "密码需为 8–128 位 / Password must be 8–128 characters"

    # 不允许注册 admin
    if username.lower() == "admin":
        return False, "该用户名已被保留 / This username is reserved"

    users = load_users()
    if username in users:
        return False, "用户名已存在 / Username already exists"

    users[username] = hash_password(password)
    save_users(users)
    return True, "注册成功！请登录 / Registration successful! Please login"


def check_login(username: str, password: str) -> tuple[bool, str, str]:
    """
    验证登录
    返回 (success, message, role)
    role: "admin" | "user"
    """
    if not username or not password:
        return False, "请输入用户名和密码 / Please enter username and password", ""

    # ── 检查管理员 ──
    admin = load_admin()
    if admin and username == admin.get("username", ""):
        stored_hash = admin.get("password_hash", "")
        if verify_password(password, stored_hash):
            if needs_rehash(stored_hash):
                admin["password_hash"] = hash_password(password)
                save_admin(admin)
            return True, "管理员登录成功 / Admin login successful", "admin"
        return False, "用户名或密码错误 / Incorrect username or password", ""

    # ── 检查普通用户 ──
    users = load_users()
    if username in users:
        stored_hash = users[username]
        if verify_password(password, stored_hash):
            if needs_rehash(stored_hash):
                users[username] = hash_password(password)
                save_users(users)
            return True, "登录成功 / Login successful", "user"
        return False, "用户名或密码错误 / Incorrect username or password", ""

    return False, "用户名或密码错误 / Incorrect username or password", ""


def init_session():
    """初始化登录相关 session state"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"  # "login" | "register"
    if "login_failures" not in st.session_state:
        st.session_state.login_failures = 0
    if "login_locked_until" not in st.session_state:
        st.session_state.login_locked_until = 0.0


def do_login(username: str, password: str) -> tuple[bool, str]:
    """执行登录并设置 session state"""
    now = time.monotonic()
    locked_until = st.session_state.get("login_locked_until", 0.0)
    if now < locked_until:
        remaining = max(1, int(locked_until - now) + 1)
        return False, f"尝试次数过多，请 {remaining} 秒后再试 / Try again in {remaining}s"

    ok, msg, role = check_login(username, password)
    if ok:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = role
        st.session_state.login_failures = 0
        st.session_state.login_locked_until = 0.0
    else:
        failures = st.session_state.get("login_failures", 0) + 1
        st.session_state.login_failures = failures
        if failures >= 5:
            st.session_state.login_locked_until = now + 60
            st.session_state.login_failures = 0
            msg = "尝试次数过多，请 60 秒后再试 / Try again in 60s"
    return ok, msg


def do_logout():
    """退出登录"""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.auth_mode = "login"
    # 保留其他 session state（nav, lang 等）


def is_logged_in() -> bool:
    """检查是否已登录"""
    return st.session_state.get("logged_in", False)


def current_user() -> str:
    """获取当前用户名"""
    return st.session_state.get("username", "")


def current_role() -> str:
    """获取当前用户角色"""
    return st.session_state.get("role", "")


def is_admin() -> bool:
    """检查是否为管理员"""
    return st.session_state.get("role", "") == "admin"


# ── 平台API配置 / Platform API Config ──
PLATFORM_CONFIG_PATH = os.path.join(AUTH_DIR, "platform_config.json")
DEMO_PLATFORM_CONFIG_KEY = "demo_platform_config"


def _default_platform_config() -> dict:
    return {
        "selling_platforms": {
            "shopify": {"store_url": "", "api_key": "", "webhook_secret": ""},
            "etsy": {"store_url": "", "api_key": ""},
            "custom_store": {"webhook_url": "", "webhook_secret": ""},
        },
        "logistics_platforms": {"courier_company": "", "api_key": ""},
    }


def load_platform_config() -> dict:
    """加载平台配置（售卖平台 + 物流API）"""
    default = _default_platform_config()
    if is_read_only_demo():
        if DEMO_PLATFORM_CONFIG_KEY not in st.session_state:
            st.session_state[DEMO_PLATFORM_CONFIG_KEY] = default
        return copy.deepcopy(st.session_state[DEMO_PLATFORM_CONFIG_KEY])

    _ensure_dir()
    return _load_json(PLATFORM_CONFIG_PATH, default)


def save_platform_config(config: dict):
    """保存平台配置"""
    if is_read_only_demo():
        st.session_state[DEMO_PLATFORM_CONFIG_KEY] = copy.deepcopy(config)
        return

    _write_json_secure(PLATFORM_CONFIG_PATH, config)


def require_admin() -> bool:
    """
    管理员权限检查：非管理员时显示友好提示并返回 False。
    调用方应根据返回值决定是否继续执行管理员专属操作。

    返回 True 表示是管理员，可以继续；False 表示被拦截。
    """
    if not is_admin():
        st.warning("🔒 此功能仅限管理员使用 / This feature is admin only")
        return False
    return True


def require_user() -> bool:
    """
    普通用户权限检查：管理员时显示友好提示并返回 False。
    调用方应根据返回值决定是否继续执行员工专属操作。

    返回 True 表示是普通用户，可以继续；False 表示被拦截。
    """
    if is_admin():
        st.warning("🔒 请用员工账号操作 / Please use a staff account")
        return False
    return True
