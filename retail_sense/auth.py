"""
RetailSense — 登录/认证/会话管理
Authentication & Session Management
"""
import hashlib
import json
import os
import streamlit as st

# ── 文件路径 ──
AUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".auth")
ADMIN_CRED_PATH = os.path.join(AUTH_DIR, "admin_cred.json")
USERS_PATH = os.path.join(AUTH_DIR, "users.json")


def _ensure_dir():
    """确保 .auth 目录存在"""
    os.makedirs(AUTH_DIR, exist_ok=True)


def hash_password(password: str) -> str:
    """SHA-256 哈希密码"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_admin() -> dict | None:
    """加载管理员凭证"""
    if os.path.exists(ADMIN_CRED_PATH):
        with open(ADMIN_CRED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_users() -> dict:
    """加载普通用户列表 {username: password_hash}"""
    _ensure_dir()
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """保存普通用户列表"""
    _ensure_dir()
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    注册普通用户
    返回 (success, message)
    """
    if not username or not password:
        return False, "用户名和密码不能为空 / Username and password cannot be empty"
    if len(username) < 2:
        return False, "用户名至少 2 个字符 / Username must be at least 2 characters"
    if len(password) < 6:
        return False, "密码至少 6 位 / Password must be at least 6 characters"

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
        if hash_password(password) == admin.get("password_hash", ""):
            return True, "管理员登录成功 / Admin login successful", "admin"
        else:
            return False, "密码错误 / Incorrect password", ""

    # ── 检查普通用户 ──
    users = load_users()
    if username in users:
        if users[username] == hash_password(password):
            return True, "登录成功 / Login successful", "user"
        else:
            return False, "密码错误 / Incorrect password", ""

    return False, "用户不存在 / User not found", ""


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


def do_login(username: str, password: str) -> tuple[bool, str]:
    """执行登录并设置 session state"""
    ok, msg, role = check_login(username, password)
    if ok:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = role
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


def load_platform_config() -> dict:
    """加载平台配置（售卖平台 + 物流API）"""
    _ensure_dir()
    if os.path.exists(PLATFORM_CONFIG_PATH):
        with open(PLATFORM_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "selling_platforms": {
            "shopify": {"store_url": "", "api_key": "", "webhook_secret": ""},
            "etsy": {"store_url": "", "api_key": ""},
            "custom_store": {"webhook_url": "", "webhook_secret": ""},
        },
        "logistics_platforms": {"courier_company": "", "api_key": ""},
    }


def save_platform_config(config: dict):
    """保存平台配置"""
    _ensure_dir()
    with open(PLATFORM_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


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
