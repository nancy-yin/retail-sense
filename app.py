"""
RetailSense v2.5.1 — AI 零售选品与库存决策系统
"""
import base64
import os
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

from retail_sense.agent import VirtualAgent
from retail_sense.agents import SalesPipeline
from retail_sense.auth import (
    current_role,
    current_user,
    do_login,
    do_logout,
    init_session,
    is_admin,
    is_logged_in,
    load_platform_config,
    register_user,
    save_platform_config,
)
from retail_sense.cases import get_cases
from retail_sense.data_persistence import (
    load_allocation_log,
    load_listing_log,
    save_allocation_log,
    save_listing_log,
)
from retail_sense.dataloader import *
from retail_sense.dataloader import get_demo_inventory, get_demo_transactions
from retail_sense.logistics import (
    DELIVERY_PIPELINE,
    allocate_order,
    generate_waybill_no,
    get_logistics_tracking,
    get_mock_orders,
    get_warehouse_inventory,
    simulate_delivery_tracking,
)
from retail_sense.pricing import CostBreakdown, PricingModel
from retail_sense.product_images import (
    get_all_product_keys,
    get_img,
    get_product_display_name,
)
from retail_sense.regions import *
from retail_sense.runtime import is_read_only_demo
from retail_sense.scorer import ProductScorer
from retail_sense.text_safety import csv_safe, escape_html, safe_filename
from retail_sense.ui import (
    UI_THEMES,
    info_strip,
    inject_design_system,
    login_hero,
    nav_group,
    page_header,
    section_label,
    sidebar_brand,
)

st.set_page_config(page_title="RetailSense", page_icon="🐾", layout="wide")

# ── 必须最前：初始化状态 ──
if "font_size" not in st.session_state: st.session_state.font_size = "13px"
if "lang" not in st.session_state: st.session_state.lang = "zh"
if "ui_theme" not in st.session_state: st.session_state.ui_theme = UI_THEMES[0]

# ── 宠物温馨风 CSS ──
fs = int(st.session_state.font_size.replace("px",""))
fs_min = max(10, fs - 2)   # 平板缩小 2px
fs_xs = max(9, fs - 4)     # 手机缩小 4px
st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: {fs}px !important; }}
h1 {{ font-size: {fs+9}px !important; }}
h2 {{ font-size: {fs+4}px !important; }}
h3 {{ font-size: {fs+2}px !important; }}

[data-testid="stButton"] button {{
    border-radius: 6px !important; transition: all 0.2s ease !important; font-weight: 500 !important; font-size: {fs}px !important;
}}
[data-testid="stButton"] button:hover {{ transform: translateY(-1px) !important; box-shadow: 0 3px 10px rgba(0,0,0,0.08) !important; }}
[data-testid="stButton"] button[kind="primary"] {{
    background: linear-gradient(135deg, #FF8C42, #FF6B35) !important; color: white !important; border: none !important;
}}
[data-testid="stButton"] button[kind="primary"]:hover {{ box-shadow: 0 4px 14px rgba(255,107,53,0.25) !important; transform: translateY(-1px) !important; }}

[data-testid="stVerticalBlockBorderWrapper"] > div {{ border-radius: 8px !important; transition: all 0.2s ease !important; }}
[data-testid="stVerticalBlockBorderWrapper"]:hover > div {{ box-shadow: 0 3px 12px rgba(0,0,0,0.06) !important; }}

[data-testid="stMetricValue"] {{ font-size: 18px !important; font-weight: 700 !important; }}
[data-testid="stMetricLabel"] {{ font-size: 11px !important; }}
[data-testid="stMetricDelta"] {{ font-size: 11px !important; }}

[data-testid="stSidebar"] [data-testid="stButton"] button {{
    border-radius: 6px !important; text-align: left !important; padding: 8px 12px !important; margin: 1px 0 !important; font-size: {fs}px !important;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {{ background: linear-gradient(135deg, #FF8C42, #FF6B35) !important; }}
[data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {{ background: transparent !important; border: 1px solid #e0d5cc !important; color: #5a4a3a !important; }}

.card-hover {{ border: 1px solid #e8e0d8; border-radius: 8px; padding: 14px; text-align: center; transition: all 0.2s; background: #fff; }}
.card-hover:hover {{ box-shadow: 0 3px 12px rgba(0,0,0,0.06); transform: translateY(-1px); }}
.card-hover.warn {{ border-left: 3px solid #f4b400; }}
.card-hover.danger {{ border-left: 3px solid #ea4335; }}
.card-hover.ok {{ border-left: 3px solid #34a853; }}

/* ── 响应式适配 / Responsive ── */

/* 平板 (≤768px) */
@media screen and (max-width: 768px) {{
    /* 侧边栏缩小 */
    [data-testid="stSidebar"] {{
        width: 200px !important;
        min-width: 200px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] button {{
        padding: 6px 8px !important;
        font-size: {fs_min}px !important;
    }}

    /* 表格横向滚动 */
    [data-testid="stDataFrame"] > div {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }}
    [data-testid="stTable"] {{
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }}

    /* 卡片全宽 — 强制 columns 内卡片换行 */
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        flex: 1 1 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
    }}

    /* 字体缩小 */
    html, body, [class*="css"] {{ font-size: {fs_min}px !important; }}
    h1 {{ font-size: {fs_min+5}px !important; }}
    h2 {{ font-size: {fs_min+3}px !important; }}
    h3 {{ font-size: {fs_min+1}px !important; }}

    /* 指标字体缩小 */
    [data-testid="stMetricValue"] {{ font-size: 15px !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 10px !important; }}

    /* 登录页容器 */
    .login-container {{
        padding: 20px 12px !important;
    }}
    .login-header {{ font-size: 24px !important; }}
    .login-mascot {{ font-size: 42px !important; }}

    /* 卡片最小高度自适应 */
    .card-hover {{ min-height: 55px !important; padding: 10px !important; }}
}}

/* 手机 (≤480px) */
@media screen and (max-width: 480px) {{
    /* 侧边栏折叠 — 更窄 */
    [data-testid="stSidebar"] {{
        width: 140px !important;
        min-width: 140px !important;
    }}
    [data-testid="stSidebar"] [data-testid="stButton"] button {{
        padding: 4px 6px !important;
        font-size: {fs_xs}px !important;
    }}

    /* 进一步缩小字体 */
    html, body, [class*="css"] {{ font-size: {fs_xs}px !important; }}
    h1 {{ font-size: {fs_xs+4}px !important; }}
    h2 {{ font-size: {fs_xs+2}px !important; }}
    h3 {{ font-size: {fs_xs}px !important; }}

    /* 指标进一步缩小 */
    [data-testid="stMetricValue"] {{ font-size: 13px !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 9px !important; }}
    [data-testid="stMetricDelta"] {{ font-size: 9px !important; }}

    /* 登录页 */
    .login-container {{
        padding: 16px 8px !important;
    }}
    .login-header {{ font-size: 20px !important; }}
    .login-mascot {{ font-size: 36px !important; }}

    /* 卡片更紧凑 */
    .card-hover {{ min-height: 45px !important; padding: 8px !important; }}

    /* 按钮大小 */
    [data-testid="stButton"] button {{
        padding: 4px 10px !important;
        font-size: {fs_xs}px !important;
    }}

    /* 分页按钮紧凑 */
    [data-testid="stHorizontalBlock"] button {{
        padding: 2px 6px !important;
        font-size: {fs_xs}px !important;
    }}

    /* 导出下载区域 */
    .export-download-area {{
        padding: 16px 12px !important;
    }}
    .export-icon {{ font-size: 36px !important; }}
    .export-title {{ font-size: 15px !important; }}
}}
</style>
""", unsafe_allow_html=True)

# Stitch 高保真设计系统（后加载以统一覆盖原生 Streamlit 组件）
inject_design_system(fs, st.session_state.ui_theme)

# ── 登录系统 ──
init_session()

# Streamlit Community Cloud 为公开作品集运行只读演示模式：不创建共享账号，
# 配货和上架等交互仅保存在当前访客的 Session 内存中。
if is_read_only_demo() and not is_logged_in():
    st.session_state.logged_in = True
    st.session_state.username = "演示管理员"
    st.session_state.role = "admin"

if not is_logged_in():
    _is_en = st.session_state.lang == "en"
    _T = lambda cn, en: en if _is_en else cn

    login_visual, login_form = st.columns([1.08, 1])
    with login_visual:
        login_hero(_is_en)

    with login_form:
        st.markdown(
            f"""
            <div class="rs-login-form-title">
              <h2>{_T('欢迎回来', 'Welcome Back')}</h2>
              <p>{_T('登录后继续完成零售决策与运营任务。', 'Sign in to continue your retail decisions and operations.')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        lang_choice = st.selectbox(
            _T("界面语言", "Language"),
            ["中文", "English"],
            index=0 if st.session_state.lang == "zh" else 1,
            key="login_lang_sel",
        )
        new_lang = "en" if lang_choice == "English" else "zh"
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        login_theme_labels_en = {
            "晨雾暖白": "Morning Mist",
            "奶油珊瑚": "Cream Coral",
            "薄荷青灰": "Mint Slate",
        }
        login_theme_choice = st.selectbox(
            _T("界面风格", "Visual style"),
            UI_THEMES,
            index=UI_THEMES.index(st.session_state.ui_theme),
            format_func=lambda value: login_theme_labels_en[value] if _is_en else value,
            key="login_theme_picker",
        )
        if login_theme_choice != st.session_state.ui_theme:
            st.session_state.ui_theme = login_theme_choice
            st.rerun()

        tab_login, tab_register = st.tabs([_T("登录", "Login"), _T("员工注册", "Staff Register")])

        with tab_login:
            show_password = st.checkbox(_T("显示密码", "Show password"), key="show_login_password")
            with st.form("login_form", clear_on_submit=False):
                login_user = st.text_input(
                    _T("用户名", "Username"),
                    key="login_user_field",
                    placeholder=_T("请输入用户名", "Enter your username"),
                )
                login_pass = st.text_input(
                    _T("密码", "Password"),
                    type="default" if show_password else "password",
                    key="login_pass_field",
                    placeholder="••••••••",
                )
                login_submit = st.form_submit_button(
                    _T("登录  →", "Sign In  →"),
                    type="primary",
                    use_container_width=True,
                )
                if login_submit:
                    if not login_user or not login_pass:
                        st.warning(_T("请输入用户名和密码", "Please enter username and password"))
                    else:
                        ok, msg = do_login(login_user, login_pass)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown(
                f"<div style='text-align:center;margin-top:14px;color:var(--rs-muted);font-size:12px'>"
                f"{_T('需要账号？请联系管理员', 'Need an account? Contact the administrator')}</div>",
                unsafe_allow_html=True,
            )

        with tab_register:
            st.caption(_T("用户名支持文字、数字、下划线、点和短横线，共 2–32 个字符。", "Username: 2–32 letters, numbers, underscores, dots or hyphens."))
            with st.form("register_form", clear_on_submit=False):
                reg_user = st.text_input(
                    _T("设置用户名", "Choose Username"),
                    key="reg_user_field",
                    placeholder=_T("2–32 个字符", "2–32 characters"),
                )
                reg_pass = st.text_input(
                    _T("设置密码", "Choose Password"),
                    type="password",
                    key="reg_pass_field",
                    placeholder=_T("8–128 位", "8–128 characters"),
                )
                reg_pass2 = st.text_input(
                    _T("确认密码", "Confirm Password"),
                    type="password",
                    key="reg_pass2_field",
                    placeholder=_T("再次输入密码", "Retype password"),
                )
                register_submit = st.form_submit_button(
                    _T("创建员工账号", "Create Staff Account"),
                    type="primary",
                    use_container_width=True,
                )
                if register_submit:
                    if not reg_user or not reg_pass:
                        st.warning(_T("请填写所有字段", "Please fill all fields"))
                    elif reg_pass != reg_pass2:
                        st.error(_T("两次密码不一致", "Passwords do not match"))
                    else:
                        ok, msg = register_user(reg_user, reg_pass)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

        st.markdown(
            f'<div class="login-footer-text">'
            f'{_T("RetailSense v2.5.1 · 本地演示系统 · 虚拟公司数据", "RetailSense v2.5.1 · Local demo · Virtual company data")}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.stop()

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
DEFAULT_IMAGES = {"banner":os.path.join(IMAGE_DIR,"banner.jpg"),"sidebar":os.path.join(IMAGE_DIR,"sidebar.jpg"),"footer":os.path.join(IMAGE_DIR,"footer.jpg")}
def load_image(key):
    path = st.session_state.get(f"img_{key}", DEFAULT_IMAGES[key])
    if os.path.exists(path): return path
    if path.startswith("http"): return path
    return DEFAULT_IMAGES[key]

for key, img in DEFAULT_IMAGES.items():
    if f"img_{key}" not in st.session_state: st.session_state[f"img_{key}"] = img

if "nav" not in st.session_state: st.session_state.nav = "工作台"
if "use_company" not in st.session_state: st.session_state.use_company = True
if "company_file" not in st.session_state: st.session_state.company_file = "萌爪宠物用品.json"
if "agent_msg" not in st.session_state: st.session_state.agent_msg = []
if "first_visit" not in st.session_state: st.session_state.first_visit = True
if "products" not in st.session_state:
    st.session_state.products = [
        {"name": "刻字狗牌", "name_en": "Engraved Dog Tag", "cost": 2.80, "price": 12.99, "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "img": "dog-tag"},
        {"name": "发光项圈", "name_en": "LED Collar", "cost": 5.50, "price": 24.99, "competitors": 28, "search_growth": 15, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "img": "led-collar"},
        {"name": "珐琅名牌", "name_en": "Enamel Nameplate", "cost": 3.20, "price": 16.99, "competitors": 18, "search_growth": 35, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "img": "enamel-plate"},
        {"name": "牵引绳套装", "name_en": "Leash Set", "cost": 4.50, "price": 22.99, "competitors": 42, "search_growth": 8, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "img": "leash-set"},
        {"name": "宠物领结", "name_en": "Pet Bow Tie", "cost": 1.50, "price": 9.99, "competitors": 55, "search_growth": -5, "trend_up": False, "annual_purchases": 3, "is_consumable": True, "img": "bow-tie"},
        {"name": "亚克力牌", "name_en": "Acrylic Tag", "cost": 1.20, "price": 8.99, "competitors": 22, "search_growth": 18, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "img": "acrylic-tag"},
        {"name": "宠物手链", "name_en": "Pet Bracelet", "cost": 2.00, "price": 14.99, "competitors": 15, "search_growth": 42, "trend_up": True, "annual_purchases": 1, "is_consumable": False, "img": "bracelet"},
        {"name": "换牙零食", "name_en": "Teething Treats", "cost": 3.00, "price": 11.99, "competitors": 30, "search_growth": 28, "trend_up": True, "annual_purchases": 8, "is_consumable": True, "img": "treats"},
    ]


def _get_product_image(key: str) -> str:
    """云端演示优先显示当前访客临时上传的产品图。"""
    if is_read_only_demo():
        return st.session_state.get("demo_product_images", {}).get(key, get_img(key))
    return get_img(key)

# ── 持久化辅助函数 / Persistence Helpers ──
def _persist_allocation():
    """保存当前配货数据到文件 / Save current allocation data to file"""
    cf = st.session_state.get("company_file", "")
    if cf and "alloc_results" in st.session_state:
        save_allocation_log(
            cf,
            st.session_state.alloc_results,
            st.session_state.get("waybill_cache", {}),
            st.session_state.get("ship_timestamps", {}),
        )

def _persist_listing():
    """保存当前上架数据到文件 / Save current listing data to file"""
    cf = st.session_state.get("company_file", "")
    if cf and "listing_records" in st.session_state:
        save_listing_log(
            cf,
            st.session_state.listing_records,
            st.session_state.get("listing_product_status", {}),
        )

is_en = st.session_state.lang == "en"
T = lambda cn, en: en if is_en else cn
def pname(p): return p.get("name_en" if is_en else "name", p.get("name",""))

VERSION = "v2.5.1"
CHANGELOG = """
**v2.5.1 (2026-08-10)** 🔒 核心计算精度、安全边界、虚拟案例口径与测试完善
**v2.4 (2026-08-06)** 🤖 管家v3.0：本地数据查询+操作建议+思考过程
**v2.3 (2026-08-04)** 🆕 卡片库存+搜索置顶+平台配置+产品图
**v2.2 (2026-08-04)** 🆕 案例库+引导+更新日志+悬停
**v2.1 (2026-08-04)** 🤖 多Agent+双语+库存整数化
**v2.0 (2026-08-04)** 📊 仪表盘+区域分析+虚拟管家
"""

# ── 预加载公司数据（侧边栏要用）──
available_companies = list_companies()
current_company_file = st.session_state.company_file if st.session_state.company_file in available_companies else (available_companies[0] if available_companies else "")
company = load_company_data(current_company_file) if st.session_state.use_company and current_company_file else None
inv = get_inventory(company, st.session_state.use_company)
txns = get_transactions(company, st.session_state.use_company)

# 无公司接入时使用示例数据（展示用）
if not inv and not txns:
    inv = get_demo_inventory()
    txns = get_demo_transactions()

# ── 侧边栏 ──
with st.sidebar:
    user = current_user()
    safe_user = escape_html(user)
    role = current_role()
    role_badge = "🛡️" if role == "admin" else "👤"
    role_label = "管理员" if role == "admin" else ("普通用户" if role == "user" else "")
    role_label_en = "Admin" if role == "admin" else ("User" if role == "user" else "")

    sidebar_brand(role_label_en if is_en else role_label)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:9px;padding:9px 11px;
         background:rgba(255,255,255,.04);border-radius:8px;
         margin-bottom:8px;border:1px solid rgba(255,255,255,.08);">
        <span style="font-size:18px;">{role_badge}</span>
        <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:12px;color:var(--rs-text);
                 overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{safe_user}</div>
            <div style="font-size:9px;color:var(--rs-coral-soft);font-weight:600;letter-spacing:.06em;text-transform:uppercase;">
                {role_label_en if is_en else role_label}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_group(T("界面风格", "Visual style"))
    theme_labels_en = {
        "晨雾暖白": "Morning Mist",
        "奶油珊瑚": "Cream Coral",
        "薄荷青灰": "Mint Slate",
    }
    theme_choice = st.selectbox(
        T("选择界面风格", "Choose visual style"),
        UI_THEMES,
        index=UI_THEMES.index(st.session_state.ui_theme),
        format_func=lambda value: theme_labels_en[value] if is_en else value,
        label_visibility="collapsed",
        key="sidebar_theme_picker",
    )
    if theme_choice != st.session_state.ui_theme:
        st.session_state.ui_theme = theme_choice
        st.rerun()

    nav_sections = [
        (T("概览", "Overview"), ["工作台", "案例库"]),
        (T("决策", "Decision"), ["选品评分", "定价模型", "销售自动化"]),
        (T("执行", "Execution"), ["库存监控", "商品上架", "物流配发"]),
        (T("数据", "Data"), ["导出报表"]),
    ]
    for group_label, items in nav_sections:
        nav_group(group_label)
        for name in items:
            kind = "primary" if st.session_state.nav == name else "secondary"
            if st.button(name, width="stretch", type=kind, key=f"nav_{name}"):
                st.session_state.nav = name
                st.rerun()

    nav_group(T("系统", "System"))
    with st.expander(T("设置","Settings")):
        lang = st.selectbox(T("语言","Language"), ["中文","English"], index=0 if st.session_state.lang=="zh" else 1)
        if (lang == "English" and st.session_state.lang != "en") or (lang == "中文" and st.session_state.lang != "zh"):
            st.session_state.lang = "en" if lang == "English" else "zh"; st.rerun()
        st.divider()

        # 字体大小
        font_size = st.select_slider(T("字体大小","Font Size"),
                                     options=["11px","12px","13px","14px","15px","16px"],
                                     value=st.session_state.font_size)
        if font_size != st.session_state.font_size:
            st.session_state.font_size = font_size; st.rerun()

        st.divider()
        # 数据源 — 仅管理员 / Data Source — admin only
        if is_admin():
            st.markdown(T("**数据源**","**Data Source**"))
            use_co = st.checkbox(T("接入公司数据","Connect Company Data"), value=st.session_state.use_company)
            if use_co != st.session_state.use_company:
                st.session_state.use_company = use_co; st.rerun()

            if use_co and available_companies:
                company_names = available_companies
                current_idx = company_names.index(current_company_file) if current_company_file in company_names else 0
                selected = st.selectbox(T("选择公司","Select Company"), company_names, index=current_idx)
                if selected != st.session_state.company_file:
                    # 切换公司前保存当前数据 / Save current data before switching company
                    _persist_allocation()
                    _persist_listing()
                    st.session_state.company_file = selected; st.rerun()

        st.divider()
        # 图片管理 — 仅管理员 / Image Manager — admin only
        if is_admin():
            with st.expander(T("🖼️ 图片管理", "🖼️ Image Manager"), expanded=False):
                st.caption(T("上传本地产品图片以替换默认图（支持 jpg/png/webp）",
                             "Upload local product images to replace defaults (jpg/png/webp)"))
                image_dir = os.path.join(os.path.dirname(__file__), "images", "products")
                demo_images = None
                if is_read_only_demo():
                    demo_images = st.session_state.setdefault("demo_product_images", {})
                else:
                    os.makedirs(image_dir, exist_ok=True)

                for key in get_all_product_keys():
                    display_name = get_product_display_name(key)
                    filepath = os.path.join(image_dir, f"{key}.jpg")

                    c_img, c_upload = st.columns([0.8, 3])
                    with c_img:
                        b64 = _get_product_image(key)
                        if b64:
                            st.markdown(
                                f'<img src="data:image/jpeg;base64,{b64}" '
                                f'style="width:48px;height:48px;border-radius:4px;object-fit:cover;">',
                                unsafe_allow_html=True,
                            )
                    with c_upload:
                        has_custom = key in demo_images if demo_images is not None else os.path.isfile(filepath)
                        status_badge = "🟢 " + T("已自定义", "Custom") if has_custom else "⚪ " + T("默认图", "Default")
                        st.caption(f"**{display_name}** — {status_badge}")
                        uploaded = st.file_uploader(
                            T(f"替换 {display_name}", f"Replace {display_name}"),
                            type=["jpg", "jpeg", "png", "webp"],
                            key=f"img_upload_{key}",
                            label_visibility="collapsed",
                        )
                        if uploaded is not None:
                            if uploaded.size > 5 * 1024 * 1024:
                                st.error(T("图片不能超过 5 MB", "Image must be 5 MB or smaller"))
                            else:
                                try:
                                    image_bytes = uploaded.getvalue()
                                    with Image.open(BytesIO(image_bytes)) as image:
                                        image.verify()
                                    with Image.open(BytesIO(image_bytes)) as image:
                                        converted = image.convert("RGB")
                                        if demo_images is not None:
                                            output = BytesIO()
                                            converted.save(output, "JPEG", quality=90)
                                            demo_images[key] = base64.b64encode(output.getvalue()).decode("ascii")
                                        else:
                                            converted.save(filepath, "JPEG", quality=90)
                                    st.success(T(f"✅ {display_name} 已更新！", f"✅ {display_name} updated!"))
                                    st.rerun()
                                except (UnidentifiedImageError, OSError, ValueError):
                                    st.error(T("文件不是有效图片", "The uploaded file is not a valid image"))

                        # Reset button to remove custom image
                        if has_custom and st.button(T("恢复默认", "Reset"), key=f"img_reset_{key}"):
                            if demo_images is not None:
                                demo_images.pop(key, None)
                            elif os.path.isfile(filepath):
                                os.remove(filepath)
                            st.rerun()

        # 平台管理 — 仅管理员 / Platform Management — admin only
        if is_admin():
            with st.expander(T("🔌 平台管理", "🔌 Platform Management"), expanded=False):
                pconfig = load_platform_config()

                st.markdown(T("### 🛍️ 售卖平台 / Selling Platforms", "### 🛍️ Selling Platforms"))

                # Shopify
                st.markdown(T("**Shopify**", "**Shopify**"))
                sp = pconfig.setdefault("selling_platforms", {}).setdefault("shopify", {})
                sp_url = st.text_input(T("Store URL", "Store URL"), value=sp.get("store_url",""), key="sp_shopify_url", placeholder="https://xxx.myshopify.com")
                sp_key = st.text_input(T("API Key", "API Key"), value=sp.get("api_key",""), key="sp_shopify_key", type="password")
                sp_secret = st.text_input(T("Webhook Secret", "Webhook Secret"), value=sp.get("webhook_secret",""), key="sp_shopify_secret", type="password")

                st.divider()

                # Etsy
                st.markdown(T("**Etsy**", "**Etsy**"))
                ep = pconfig.setdefault("selling_platforms", {}).setdefault("etsy", {})
                ep_url = st.text_input(T("Store URL", "Store URL"), value=ep.get("store_url",""), key="sp_etsy_url", placeholder="https://www.etsy.com/shop/xxx")
                ep_key = st.text_input(T("API Key", "API Key"), value=ep.get("api_key",""), key="sp_etsy_key", type="password")

                st.divider()

                # 独立站
                st.markdown(T("**独立站 / Custom Store**", "**Custom Store**"))
                cp = pconfig.setdefault("selling_platforms", {}).setdefault("custom_store", {})
                cp_url = st.text_input(T("Webhook URL", "Webhook URL"), value=cp.get("webhook_url",""), key="sp_custom_url", placeholder="https://your-store.com/api/webhook")
                cp_secret = st.text_input(T("Webhook Secret", "Webhook Secret"), value=cp.get("webhook_secret",""), key="sp_custom_secret", type="password")

                st.divider()
                st.markdown(T("### 🚚 物流平台 / Logistics Platforms", "### 🚚 Logistics Platforms"))

                lp = pconfig.setdefault("logistics_platforms", {})
                lp_company = st.text_input(T("快递公司", "Courier Company"), value=lp.get("courier_company",""), key="lp_company", placeholder=T("如: 顺丰/圆通/DHL","e.g. SF Express/DHL"))
                lp_key = st.text_input(T("API Key", "API Key"), value=lp.get("api_key",""), key="lp_key", type="password")

                # 保存按钮
                if st.button(T("💾 保存平台配置", "💾 Save Platform Config"), type="primary", key="save_platform_config"):
                    pconfig["selling_platforms"]["shopify"]["store_url"] = sp_url
                    pconfig["selling_platforms"]["shopify"]["api_key"] = sp_key
                    pconfig["selling_platforms"]["shopify"]["webhook_secret"] = sp_secret
                    pconfig["selling_platforms"]["etsy"]["store_url"] = ep_url
                    pconfig["selling_platforms"]["etsy"]["api_key"] = ep_key
                    pconfig["selling_platforms"]["custom_store"]["webhook_url"] = cp_url
                    pconfig["selling_platforms"]["custom_store"]["webhook_secret"] = cp_secret
                    pconfig["logistics_platforms"]["courier_company"] = lp_company
                    pconfig["logistics_platforms"]["api_key"] = lp_key
                    save_platform_config(pconfig)
                    st.success(T("✅ 平台配置已保存！", "✅ Platform config saved!"))
                    st.rerun()
    st.divider()
    with st.expander(T("关于","About")):
        st.markdown(T("**RetailSense** 由一位前瑞幸咖啡店长构建。","**RetailSense** built by a former Luckin Coffee store manager."))
    with st.expander(T(f"更新日志 {VERSION}","Changelog {VERSION}")):
        st.markdown(CHANGELOG)
    if st.button(T("退出登录", "Logout"), use_container_width=True, key="sidebar_logout"):
        do_logout()
        st.rerun()
    st.caption(f"{VERSION} · MIT")

page = st.session_state.nav
agent = VirtualAgent()
# 设置管家上下文
if company:
    agent.context["company"] = company.get("company", "") if st.session_state.lang == "zh" else company.get("company_en", "")

# ══ 工作台 ══
if page == "工作台":
    page_header(
        "P02 · OVERVIEW",
        T("工作台", "Dashboard"),
        T("快速掌握营收、库存风险和下一步运营任务。", "Review revenue, inventory risk and the next operational actions."),
        T("虚拟公司数据", "Virtual company data"),
        "purple",
    )

    today = daily_summary(txns, 1, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    week = daily_summary(txns, 7, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    month = daily_summary(txns, 30, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    inv_summary = inventory_value_summary(inv) if inv else {
        "total_qty": 0, "total_value": 0, "skus": 0, "low_stock": 0,
        "reorder_needed": 0, "out_of_stock": 0, "normal": 0, "total_retail": 0,
    }

    company_name = (
        company.get("company_en" if is_en else "company", "")
        if st.session_state.use_company and company
        else T("内置示例数据", "Built-in demo data")
    )
    st.markdown(
        f"""
        <div class="rs-welcome-panel">
          <span class="rs-badge rs-badge--purple">{T("虚拟公司数据", "Virtual company data")}</span>
          <h2>{T("早上好", "Morning")}, {escape_html(current_user())}</h2>
          <p>{T("当前数据源", "Current source")}：{escape_html(company_name)} ·
          {T("库存状态已完成规则检查，请优先处理低库存与断货 SKU。", "Inventory rules are up to date. Prioritize low-stock and out-of-stock SKUs.")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quick_a, quick_b, quick_c = st.columns(3)
    with quick_a:
        if st.button(T("开始选品  →", "Start scoring  →"), type="primary", use_container_width=True, key="quick_scoring"):
            st.session_state.nav = "选品评分"
            st.rerun()
    with quick_b:
        if st.button(T("计算定价", "Calculate pricing"), use_container_width=True, key="quick_pricing"):
            st.session_state.nav = "定价模型"
            st.rerun()
    with quick_c:
        if st.button(T("查看库存", "View inventory"), use_container_width=True, key="quick_inventory"):
            st.session_state.nav = "库存监控"
            st.rerun()

    dashboard_col, assistant_col = st.columns([2.35, 1], gap="large")
    with dashboard_col:
        section_label(T("关键指标", "Key metrics"))
        metrics = st.columns(4)
        metrics[0].metric(T("今日营收", "Today revenue"), f"¥{today['revenue']:,.0f}", f"{today['orders']}{T(' 单', ' orders')}")
        metrics[1].metric(T("本周营收", "Week revenue"), f"¥{week['revenue']:,.0f}")
        metrics[2].metric(T("本月营收", "Month revenue"), f"¥{month['revenue']:,.0f}")
        metrics[3].metric(T("库存零售价值", "Inventory value"), f"¥{inv_summary['total_retail']:,.0f}", f"{inv_summary['skus']} SKU")

        section_label(T("库存健康", "Inventory health"))
        status_cols = st.columns(3)
        normal_count = inv_summary["normal"]
        low_count = inv_summary["low_stock"] + inv_summary["reorder_needed"]
        status_data = [
            (T("正常", "Healthy"), normal_count, "ok", "#4ae183"),
            (T("低库存 / 建议补货", "Low / Reorder"), low_count, "warn", "#ffd166"),
            (T("断货", "Out of stock"), inv_summary["out_of_stock"], "danger", "#ffb4ab"),
        ]
        for idx, (label, count, css_class, color) in enumerate(status_data):
            with status_cols[idx]:
                st.markdown(
                    f"""
                    <div class="card-hover {css_class}" style="min-height:104px;text-align:left;">
                      <div style="font:700 28px/1.2 Manrope;color:{color};">{count}</div>
                      <div style="font:600 10px/1.35 Geist;color:#b8aaad;margin-top:10px;text-transform:uppercase;letter-spacing:.08em;">{label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        section_label(T("近期出库", "Recent outbound shipments"))
        out_txns = sorted([t for t in txns if t.get("type") == "out"], key=lambda t: t.get("date", ""), reverse=True)[:5]
        if out_txns:
            with st.container(border=True):
                for txn in out_txns:
                    row_date, row_product, row_qty, row_revenue = st.columns([1.15, 2.4, .8, 1.1])
                    row_date.caption(txn.get("date", ""))
                    row_product.markdown(f"**{escape_html(txn.get('product', ''))}**")
                    row_qty.caption(f"× {int(txn.get('qty', 0))}")
                    row_revenue.markdown(f"**¥{float(txn.get('revenue', 0)):,.0f}**")
        else:
            info_strip(T("暂无交易记录，关键指标不显示推测趋势。", "No transactions yet; trend claims are hidden."))

    with assistant_col:
        section_label(T("规则式管家", "Rule-based assistant"))
        with st.container(border=True):
            st.markdown(
                f"### {T('Retail Assistant', 'Retail Assistant')}\n"
                f"<span class='rs-badge'>{T('规则式助手', 'Rule-based')}</span>",
                unsafe_allow_html=True,
            )
            st.caption(T(
                "可查询库存、营收、利润和补货建议；回答来自本地规则与演示数据。",
                "Ask about stock, revenue, profit and restocking. Answers use local rules and demo data.",
            ))

            preset_questions = [
                T("查库存", "Check stock"),
                T("本周营收", "Week revenue"),
                T("利润最高商品", "Top profit item"),
                T("补货建议", "Restock advice"),
            ]
            preset_cols = st.columns(2)
            for idx, question in enumerate(preset_questions):
                with preset_cols[idx % 2]:
                    if st.button(question, key=f"assistant_preset_{idx}", use_container_width=True):
                        st.session_state.agent_query = question
                        st.rerun()

            msg = st.text_input(
                T("向规则式管家提问", "Ask the rule-based assistant"),
                key="agent_query",
                placeholder=T("例如：哪些商品需要补货？", "e.g. Which items need restocking?"),
                label_visibility="collapsed",
            )
            if st.button(T("发送", "Send"), type="primary", use_container_width=True, key="assistant_send") and msg:
                with st.spinner(T("正在分析本地数据…", "Analyzing local data…")):
                    resp = agent.process(
                        msg,
                        company_data=company,
                        transactions=txns,
                        inventory=inv,
                        lang=st.session_state.lang,
                    )
                st.session_state.agent_msg.append(("user", msg))
                st.session_state.agent_msg.append(("agent_v3", resp))

            for entry in st.session_state.agent_msg[-4:]:
                if entry[0] == "user":
                    with st.chat_message("user"):
                        st.write(entry[1])
                elif entry[0] == "agent_v3":
                    resp_obj = entry[1]
                    with st.chat_message("assistant"):
                        if hasattr(resp_obj, "answer"):
                            st.markdown(resp_obj.answer)
                        else:
                            st.write(str(resp_obj))
                        if hasattr(resp_obj, "suggestions") and resp_obj.suggestions:
                            with st.expander(T("操作建议", "Suggestions"), expanded=False):
                                for suggestion in resp_obj.suggestions:
                                    st.caption(f"• {suggestion}")
                elif entry[0] == "agent":
                    with st.chat_message("assistant"):
                        st.write(entry[1])

# ══ 选品评分 ══
elif page == "选品评分":
    page_header(
        "P04 · DECISION",
        T("选品评分模型 P04", "Product Scoring P04"),
        T("用毛利、竞争、趋势与复购四维规则解释商品潜力。", "Explain product potential with margin, competition, trend and repurchase rules."),
        T("规则评分 · 非销量预测", "Rule score · Not a forecast"),
        "coral",
    )

    products = st.session_state.products
    scorer = ProductScorer()
    region = st.radio(
        T("目标市场", "Target market"),
        all_regions(),
        horizontal=True,
        key="sel_region",
    )
    region_data = get_region(region)
    if region_data:
        info_strip(
            T("区域关键词：", "Region signals: ")
            + ", ".join(region_data["countries"][:3])
            + " · "
            + T("平均利润：", "Average margin: ")
            + str(region_data["avg_margin"])
            + " · "
            + T("竞争：", "Competition: ")
            + str(region_data["competition"])
        )

    scoring_input, scoring_result_col = st.columns([1.15, 1.45], gap="large")
    with scoring_input:
        section_label(T("商品与四维输入", "Product and four-factor inputs"))
        selected_index = st.selectbox(
            T("选择商品", "Choose product"),
            range(len(products)),
            format_func=lambda index: pname(products[index]),
            key="scoring_product_index",
        )
        selected_product = products[selected_index]
        b64 = _get_product_image(selected_product.get("img", ""))
        if b64:
            st.markdown(
                f'<img alt="{escape_html(pname(selected_product))}" src="data:image/jpeg;base64,{b64}" '
                f'style="width:100%;max-height:190px;object-fit:contain;border-radius:10px;'
                f'background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);padding:12px;">',
                unsafe_allow_html=True,
            )

        cost_col, price_col = st.columns(2)
        with cost_col:
            score_cost = st.number_input(T("成本", "Cost"), min_value=0.0, value=float(selected_product["cost"]), step=0.10, format="%.2f", key=f"score_cost_{selected_index}")
        with price_col:
            score_price = st.number_input(T("售价", "Price"), min_value=0.01, value=float(selected_product["price"]), step=0.10, format="%.2f", key=f"score_price_{selected_index}")
        score_competitors = st.slider(T("竞品数量 · 权重 25%", "Competitors · Weight 25%"), 0, 100, int(selected_product["competitors"]), key=f"score_comp_{selected_index}")
        score_growth = st.slider(T("搜索增长 · 权重 25%", "Search growth · Weight 25%"), -50, 100, int(selected_product["search_growth"]), key=f"score_growth_{selected_index}")
        score_annual = st.slider(T("年购买次数 · 权重 30%", "Annual purchases · Weight 30%"), 1, 12, int(selected_product["annual_purchases"]), key=f"score_annual_{selected_index}")
        score_consumable = st.checkbox(T("消耗品", "Consumable"), value=bool(selected_product["is_consumable"]), key=f"score_consumable_{selected_index}")

        analyzed_product = {
            **selected_product,
            "cost": score_cost,
            "price": score_price,
            "competitors": score_competitors,
            "search_growth": score_growth,
            "trend_up": score_growth >= 0,
            "annual_purchases": score_annual,
            "is_consumable": score_consumable,
        }
        signature = (
            selected_index, score_cost, score_price, score_competitors,
            score_growth, score_annual, score_consumable, region,
        )
        if st.button(T("计算综合评分  →", "Calculate score  →"), type="primary", use_container_width=True, key="calculate_scoring"):
            st.session_state.scoring_result = {
                "signature": signature,
                "score": scorer.evaluate(analyzed_product),
                "product": analyzed_product,
            }

        if is_admin():
            with st.expander(T("管理员：保存为商品默认值", "Admin: save as product defaults"), expanded=False):
                st.caption(T("仅管理员可修改默认商品数据；普通评分不会覆盖基础数据。", "Only admins can change product defaults; analysis inputs do not overwrite base data."))
                if st.button(T("保存当前输入", "Save current inputs"), key=f"save_scoring_product_{selected_index}"):
                    st.session_state.products[selected_index] = analyzed_product
                    st.success(T("商品默认值已更新。", "Product defaults updated."))
                    st.rerun()

    with scoring_result_col:
        section_label(T("评分结果", "Scoring result"))
        stored = st.session_state.get("scoring_result")
        if stored and stored["signature"] != signature:
            info_strip(T("输入已变化，当前结果待重新计算。", "Inputs changed; recalculate to refresh the result."))
        if stored:
            score = stored["score"]
            score_color = "#4ae183" if score.final_score >= 80 else ("#ffd166" if score.final_score >= 60 else "#ffb4ab")
            recommendation = T("优先测试", "Priority test") if score.final_score >= 80 else (T("小批验证", "Small-batch test") if score.final_score >= 60 else T("谨慎上架", "Use caution"))
            st.markdown(
                f"""
                <div class="card-hover" style="padding:24px!important;text-align:center;">
                  <div style="color:#b8aaad;font:600 10px Geist;text-transform:uppercase;letter-spacing:.12em;">{T("综合得分", "Final score")}</div>
                  <div style="font:800 68px/1 Manrope;color:{score_color};margin:12px 0 4px;">{score.final_score:.0f}</div>
                  <div style="color:#b8aaad;font-size:12px;">/ 100</div>
                  <span class="rs-badge" style="margin-top:14px;color:{score_color};">{recommendation}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            score_dimensions = [
                (T("毛利", "Margin"), score.margin_score, 20, "#ff7f6e"),
                (T("竞争", "Competition"), score.competition_score, 25, "#cebdff"),
                (T("趋势", "Trend"), score.trend_score, 25, "#ffd166"),
                (T("复购", "Repurchase"), score.repurchase_score, 30, "#4ae183"),
            ]
            with st.container(border=True):
                for label, value, weight, color in score_dimensions:
                    st.markdown(
                        f"""
                        <div style="margin:12px 0;">
                          <div style="display:flex;justify-content:space-between;font:600 11px Geist;color:var(--rs-text);">
                            <span>{label} · {weight}%</span><span>{value:.0f}</span>
                          </div>
                          <div style="height:7px;background:#353437;border-radius:99px;margin-top:7px;overflow:hidden;">
                            <div style="width:{max(0, min(100, value))}%;height:100%;background:{color};border-radius:99px;"></div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            region_recommendations = best_region_for_product(stored["product"])
            st.caption(T("区域建议：", "Region suggestions: ") + " · ".join(region_recommendations))
        else:
            info_strip(T("选择商品并计算后显示综合得分、四维子分和解释。", "Choose a product and calculate to see the final score and four sub-scores."))

    section_label(T("选品模拟排名", "Product simulation ranking"))
    if st.button(T("生成批量排名", "Generate ranking"), key="batch_scoring"):
        st.session_state.batch_scoring_results = scorer.rank(products)
    batch_results = st.session_state.get("batch_scoring_results")
    if batch_results:
        ranking_rows = []
        for rank, result in enumerate(batch_results, 1):
            ranking_rows.append({
                T("排名", "Rank"): f"{rank:02d}",
                T("商品", "Product"): result.product_name,
                T("综合得分", "Final score"): round(result.final_score),
                T("毛利", "Margin"): result.margin_score,
                T("竞争", "Competition"): result.competition_score,
                T("趋势", "Trend"): result.trend_score,
                T("复购", "Repurchase"): result.repurchase_score,
            })
        st.dataframe(pd.DataFrame(ranking_rows), width="stretch", hide_index=True)

    with st.expander(T("评分方法论与近期活动", "Methodology and upcoming events"), expanded=False):
        st.markdown(T(
            "**权重：** 毛利 20% · 竞争 25% · 趋势 25% · 复购 30%。分数用于解释规则，不代表真实销量预测。",
            "**Weights:** Margin 20% · Competition 25% · Trend 25% · Repurchase 30%. Scores explain rules and are not sales forecasts.",
        ))
        for event in upcoming_events(region):
            if len(event) == 5:
                month_label, event_name, description, index_label, tip = event
                st.markdown(f"**{month_label} · {event_name}** · {index_label}  \n{description}  \n{tip}")

# ══ 定价模型 ══
elif page == "定价模型":
    page_header(
        "P05 · DECISION",
        T("定价模型", "Pricing Model"),
        T("拆解完整成本，并按目标利润率给出可解释的售价建议。", "Break down full cost and calculate explainable prices from the target margin."),
        T("固定演示汇率", "Fixed demo exchange rate"),
        "green",
    )
    info_strip(T("货币换算使用内置演示汇率，不是实时金融数据。", "Currency conversion uses fixed demo rates, not live financial data."))

    pricing_inputs, pricing_output = st.columns([1.55, 1], gap="large")
    with pricing_inputs:
        section_label(T("成本输入", "Cost inputs"))
        with st.container(border=True):
            input_a, input_b = st.columns(2)
            with input_a:
                raw = st.number_input(T("裸件成本", "Raw material"), min_value=0.0, value=2.80, step=0.10, format="%.2f")
                proc = st.number_input(T("加工费", "Processing"), min_value=0.0, value=1.20, step=0.10, format="%.2f")
                pack = st.number_input(T("包装费", "Packaging"), min_value=0.0, value=0.50, step=0.10, format="%.2f")
            with input_b:
                ship = st.number_input(T("物流费", "Logistics"), min_value=0.0, value=1.50, step=0.10, format="%.2f")
                plat = st.number_input(T("平台费金额", "Platform fee"), min_value=0.0, value=0.85, step=0.10, format="%.2f")
                RATES = {"¥ CNY": 1.0, "$ USD": 0.14, "€ EUR": 0.13, "£ GBP": 0.11, "¥ JPY": 16.0, "A$ AUD": 0.21, "C$ CAD": 0.19}
                currency = st.selectbox(T("显示货币", "Display currency"), list(RATES), index=1 if is_en else 0)

            target = st.slider(T("目标利润率", "Target margin"), 20, 70, 45, 1, format="%d%%")
            if st.button(T("计算建议售价  →", "Calculate price  →"), type="primary", use_container_width=True, key="calculate_pricing"):
                cost = CostBreakdown(raw, proc, pack, ship, plat)
                result = PricingModel().suggest_price(cost, target / 100)
                st.session_state.pricing_result = {
                    **result,
                    "raw": raw,
                    "processing": proc,
                    "packaging": pack,
                    "shipping": ship,
                    "platform": plat,
                    "target": target,
                    "currency": currency,
                    "rate": RATES[currency],
                    "symbol": currency.split()[0],
                }

        with st.expander(T("公式与口径说明", "Formula and definitions"), expanded=False):
            st.markdown(T(
                "- 总成本 = 裸件 + 加工 + 包装 + 物流 + 平台费\n- 建议售价依据目标利润率反推，并保留两位小数。\n- 28% 为项目内置利润率红线。",
                "- Total cost = raw + processing + packaging + logistics + platform fee\n- Suggested price is derived from target margin and shown to two decimals.\n- 28% is the built-in project margin redline.",
            ))

    with pricing_output:
        section_label(T("实时计算结果", "Pricing result"))
        saved_result = st.session_state.get("pricing_result")
        if saved_result:
            symbol = saved_result["symbol"]
            rate = saved_result["rate"]
            convert = lambda value: round(float(value) * rate, 2)
            margin_pct = float(saved_result["margin_rate"]) * 100
            margin_color = "#4ae183" if saved_result["above_redline"] else "#ffb4ab"
            st.markdown(
                f"""
                <div class="card-hover" style="padding:22px!important;">
                  <div style="font:600 10px/1 Geist;color:#b8aaad;text-transform:uppercase;letter-spacing:.10em;">{T("建议零售价", "Suggested retail price")}</div>
                  <div style="font:800 42px/1.15 Manrope;color:var(--rs-coral-soft);margin:10px 0 20px;">{symbol}{convert(saved_result['suggested_price']):,.2f}</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div style="padding:12px;border-radius:8px;background:rgba(255,255,255,.05);">
                      <div style="color:#b8aaad;font-size:10px;">{T("总成本", "Total cost")}</div>
                      <strong>{symbol}{convert(saved_result['total_cost']):,.2f}</strong>
                    </div>
                    <div style="padding:12px;border-radius:8px;background:rgba(74,225,131,.08);">
                      <div style="color:#4ae183;font-size:10px;">{T("单件利润", "Unit profit")}</div>
                      <strong style="color:#4ae183">{symbol}{convert(saved_result['profit']):,.2f}</strong>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="card-hover" style="margin-top:12px;text-align:center;">
                  <div style="width:150px;height:150px;margin:6px auto 16px;border-radius:50%;background:conic-gradient(#ff7f6e 0 20%,#cebdff 20% 38%,#ffd166 38% 55%,#4ae183 55% 72%,#353437 72% 100%);display:grid;place-items:center;">
                    <div style="width:105px;height:105px;border-radius:50%;background:#201f21;display:grid;place-items:center;">
                      <div><span style="display:block;color:#b8aaad;font-size:10px;">{T("实际利润率", "Actual margin")}</span><strong style="font:700 25px Manrope;color:{margin_color};">{margin_pct:.1f}%</strong></div>
                    </div>
                  </div>
                  <span class="rs-badge {'rs-badge--coral' if not saved_result['above_redline'] else ''}">
                    {T("达到 28% 利润红线", "Meets 28% redline") if saved_result['above_redline'] else T("未达到 28% 利润红线", "Below 28% redline")}
                  </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            component_labels = [
                (T("裸件", "Raw"), saved_result["raw"]),
                (T("加工", "Processing"), saved_result["processing"]),
                (T("包装", "Packaging"), saved_result["packaging"]),
                (T("物流", "Logistics"), saved_result["shipping"]),
                (T("平台", "Platform"), saved_result["platform"]),
            ]
            with st.expander(T("成本结构", "Cost breakdown"), expanded=True):
                for label, value in component_labels:
                    st.markdown(f"**{label}** · {symbol}{convert(value):,.2f}")
        else:
            info_strip(T("输入成本并点击“计算建议售价”后显示完整结果。", "Enter costs and calculate to see the full pricing result."))

# ══ 库存监控 ══
elif page == "库存监控":
    page_header(
        "P07 · EXECUTION",
        T("库存监控", "Inventory Monitor"),
        T("实时识别断货、低库存和已到补货点的 SKU。", "Identify out-of-stock, low-stock and reorder-point SKUs."),
        T("虚拟公司数据", "Virtual company data"),
        "purple",
    )
    source_name = (
        company.get("company_en" if is_en else "company", "")
        if st.session_state.use_company and company
        else T("内置示例数据", "Built-in demo data")
    )
    info_strip(T("数据源：", "Data source: ") + source_name + " · " + T("状态由安全库存与补货点规则计算。", "Status is calculated from safety-stock and reorder-point rules."))

    prepared_inventory = []
    for item in inv:
        summary = inventory_item_summary(item)
        prepared_inventory.append((item, summary))

    status_order = ["正常", "建议补货", "低库存", "断货"]
    status_counts = {status: sum(1 for _, summary in prepared_inventory if summary["status"] == status) for status in status_order}
    status_columns = st.columns(4)
    status_meta = [
        ("正常", "Healthy", "#4ae183"),
        ("建议补货", "Reorder", "#cebdff"),
        ("低库存", "Low stock", "#ffd166"),
        ("断货", "Out of stock", "#ffb4ab"),
    ]
    for idx, (status_cn, status_en, color) in enumerate(status_meta):
        with status_columns[idx]:
            st.metric(T(status_cn, status_en), status_counts[status_cn])
            if st.button(T("筛选此状态", "Filter"), key=f"filter_inventory_{status_cn}", use_container_width=True):
                st.session_state.inventory_status_filter = status_cn
                st.rerun()

    search_col, status_col, sort_col = st.columns([2.1, 1, 1])
    with search_col:
        inventory_search = st.text_input(
            T("搜索商品或 SKU", "Search product or SKU"),
            key="inventory_search",
            placeholder=T("输入商品名或 SKU", "Enter product or SKU"),
        )
    status_options = [T("全部状态", "All statuses")] + status_order
    with status_col:
        selected_status = st.selectbox(
            T("状态", "Status"),
            status_options,
            key="inventory_status_filter",
        )
    with sort_col:
        selected_sort = st.selectbox(
            T("排序", "Sort"),
            [T("补货优先级", "Reorder priority"), T("库存量", "Quantity"), T("周转天数", "Turnover days")],
            key="inventory_sort",
        )

    filtered_inventory = []
    for item, summary in prepared_inventory:
        name = pname(item)
        haystack = f"{name} {item.get('sku', '')}".lower()
        if inventory_search and inventory_search.lower() not in haystack:
            continue
        if selected_status not in {status_options[0], summary["status"]}:
            continue
        filtered_inventory.append((item, summary))

    if selected_sort == T("库存量", "Quantity"):
        filtered_inventory.sort(key=lambda pair: int(pair[0].get("qty", 0)))
    elif selected_sort == T("周转天数", "Turnover days"):
        filtered_inventory.sort(key=lambda pair: float(pair[1]["turnover_days"]))
    else:
        priority = {"断货": 0, "低库存": 1, "建议补货": 2, "正常": 3}
        filtered_inventory.sort(key=lambda pair: (priority.get(pair[1]["status"], 9), int(pair[0].get("qty", 0))))

    rows = []
    status_en_map = {"断货": "Out of stock", "低库存": "Low stock", "建议补货": "Reorder", "正常": "Healthy"}
    for item, summary in filtered_inventory:
        daily = float(item.get("daily_avg", 0))
        turnover = T("暂不能计算", "Not available") if daily <= 0 else f"{summary['turnover_days']:.1f} {T('天', 'days')}"
        rows.append({
            T("商品", "Product"): pname(item),
            "SKU": item.get("sku", ""),
            T("当前库存", "Quantity"): int(item.get("qty", 0)),
            T("日均销量", "Daily sales"): daily,
            T("周转天数", "Turnover"): turnover,
            T("安全库存", "Safety stock"): summary["safety_stock"],
            T("补货点", "Reorder point"): summary["reorder_point"],
            T("建议补货量", "Suggested qty"): summary["reorder_quantity"],
            T("状态", "Status"): status_en_map.get(summary["status"], summary["status"]) if is_en else summary["status"],
        })

    section_label(T("库存明细", "Inventory details"))
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.caption(T(f"共 {len(rows)} 条结果；四个状态互斥。", f"{len(rows)} results; inventory statuses are mutually exclusive."))
    else:
        info_strip(T("当前筛选条件下没有库存记录。请清除搜索或状态筛选。", "No inventory matches the current filters. Clear the search or status filter."))
        if st.button(T("清除筛选", "Clear filters"), type="primary", key="clear_inventory_filters"):
            st.session_state.inventory_search = ""
            st.session_state.inventory_status_filter = status_options[0]
            st.rerun()

    with st.expander(T("状态公式与口径", "Status formulas and definitions"), expanded=False):
        st.markdown(T(
            "- 安全库存 = 日均销量 × 7 天\n- 补货点 = 安全库存 + 日均销量 × 交期\n- 建议补货量 = max(0, 补货点 − 当前库存)\n- 日均销量为 0 时不计算周转，避免除零。",
            "- Safety stock = daily sales × 7 days\n- Reorder point = safety stock + daily sales × lead time\n- Suggested quantity = max(0, reorder point − quantity)\n- Turnover is not calculated when daily sales is zero.",
        ))

# ══ 案例库 ══
elif page == "案例库":
    page_header(
        "P03 · OVERVIEW",
        T("案例库", "Case Library"),
        T("用虚拟业务故事说明 RetailSense 的分析与执行能力。", "Virtual business stories that demonstrate RetailSense analysis and execution."),
        T("全部为虚拟演示案例", "All cases are fictional demos"),
        "coral",
    )
    info_strip(T("案例公司、指标、评价和交易数据均为虚拟演示内容。", "Companies, metrics, feedback and transactions are fictional demo content."))

    cases = get_cases()
    filter_region, filter_stage, filter_industry = st.columns(3)
    region_options = [T("全部地区", "All regions")] + sorted({case["region"] for case in cases})
    stage_options = [T("全部阶段", "All stages")] + sorted({case["stage"] for case in cases})
    industry_options = [T("全部行业", "All industries")] + sorted({case["industry"] for case in cases})
    with filter_region:
        selected_region = st.selectbox(T("地区", "Region"), region_options, key="case_region")
    with filter_stage:
        selected_stage = st.selectbox(T("业务阶段", "Business stage"), stage_options, key="case_stage")
    with filter_industry:
        selected_industry = st.selectbox(T("行业", "Industry"), industry_options, key="case_industry")

    all_region = region_options[0]
    all_stage = stage_options[0]
    all_industry = industry_options[0]
    filtered_cases = [
        case for case in cases
        if (selected_region == all_region or case["region"] == selected_region)
        and (selected_stage == all_stage or case["stage"] == selected_stage)
        and (selected_industry == all_industry or case["industry"] == selected_industry)
    ]
    st.caption(T(f"显示 {len(filtered_cases)} 个虚拟案例", f"Showing {len(filtered_cases)} fictional cases"))

    case_images = ["images/banner.jpg", "images/sidebar.jpg", "images/footer.jpg"]
    if not filtered_cases:
        info_strip(T("当前筛选条件下没有案例，请清除筛选后重试。", "No cases match these filters. Clear the filters and try again."))
        if st.button(T("清除筛选", "Clear filters"), type="primary", key="clear_case_filters"):
            st.session_state.case_region = all_region
            st.session_state.case_stage = all_stage
            st.session_state.case_industry = all_industry
            st.rerun()
    else:
        card_columns = st.columns(min(3, len(filtered_cases)), gap="medium")
        for index, case in enumerate(filtered_cases):
            original_index = cases.index(case)
            with card_columns[index % len(card_columns)], st.container(border=True):
                st.image(case_images[original_index % len(case_images)], use_container_width=True)
                st.markdown(
                    f"<span class='rs-badge rs-badge--coral'>{T('虚拟案例', 'Fictional case')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"### {escape_html(case['company'])}")
                st.caption(f"{escape_html(case['industry'])} · {escape_html(case['region'])} · {escape_html(case['stage'])}")
                st.markdown(f"**{T('痛点', 'Problem')}**")
                st.write(case["problem"])
                st.caption(T("使用功能：", "Features: ") + "、".join(case["products_used"]))
                with st.expander(T("查看详情  →", "View details  →"), expanded=False):
                    st.markdown(f"**{T('使用前', 'Before')}**")
                    st.write(case["problem"])
                    st.markdown(f"**{T('解决方案', 'Solution')}**")
                    st.write(case["solution"])
                    metric_cols = st.columns(2)
                    metric_cols[0].metric(T("耗时", "Time"), case["after"]["time"], delta=f"↓ {case['before']['time']}", delta_color="inverse")
                    metric_cols[1].metric(T("成本", "Cost"), case["after"]["cost"], delta=f"↓ {case['before']['cost']}")
                    metric_cols[0].metric(T("人力", "People"), case["after"]["people"], delta=f"↓ {case['before']['people']}", delta_color="inverse")
                    metric_cols[1].metric(T("错误率", "Errors"), case["after"]["error"], delta=f"↓ {case['before']['error']}")
                    st.markdown(T("**虚拟反馈（演示文案）**", "**Fictional feedback (demo copy)**"))
                    st.markdown(
                        f'<div class="rs-case-feedback">“{escape_html(case["testimonial"])}”</div>',
                        unsafe_allow_html=True,
                    )

# ══ 销售自动化 ══
elif page == "销售自动化":
    page_header(
        "P06 · DECISION",
        T("销售自动化", "Sales Automation"),
        T("Scout、Price、Copy、Monitor 四段规则流水线的可追踪执行。", "Track the Scout, Price, Copy and Monitor rule pipeline."),
        T("规则引擎 · 非自治 Agent", "Rule engine · Not autonomous agents"),
        "purple",
    )
    info_strip(T("当前四阶段均由本地规则与模板执行，不调用大模型。", "All four stages currently use local rules and templates; no LLM is called."))

    products_for_pipeline = [
        {"name": "刻字狗牌", "name_en": "Engraved Dog Tag", "cost": 2.80, "price": 12.99, "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "qty": 45, "daily_avg": 9, "img": "dog-tag"},
        {"name": "发光项圈", "name_en": "LED Collar", "cost": 5.50, "price": 24.99, "competitors": 28, "search_growth": 15, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "qty": 12, "daily_avg": 6, "img": "led-collar"},
        {"name": "珐琅名牌", "name_en": "Enamel Nameplate", "cost": 3.20, "price": 16.99, "competitors": 18, "search_growth": 35, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "qty": 120, "daily_avg": 3, "img": "enamel-plate"},
        {"name": "牵引绳套装", "name_en": "Leash Set", "cost": 4.50, "price": 22.99, "competitors": 42, "search_growth": 8, "trend_up": True, "annual_purchases": 2, "is_consumable": False, "qty": 0, "daily_avg": 4, "img": "leash-set"},
        {"name": "换牙零食", "name_en": "Teething Treats", "cost": 3.00, "price": 11.99, "competitors": 30, "search_growth": 28, "trend_up": True, "annual_purchases": 8, "is_consumable": True, "qty": 8, "daily_avg": 15, "img": "treats"},
    ]

    with st.container(border=True):
        parameter_a, parameter_b, parameter_c = st.columns([1, 1, .7])
        with parameter_a:
            target_pct = st.slider(T("目标利润率", "Target margin"), 25, 60, 45, 5, format="%d%%", key="pipeline_margin")
        with parameter_b:
            pipeline_region = st.selectbox(T("目标市场", "Target market"), ["北美", "欧洲", "东南亚", "日韩", "澳洲"], key="pipeline_region")
        with parameter_c:
            st.metric(T("处理商品", "Products"), len(products_for_pipeline))

    section_label(T("执行流", "Execution flow"))
    pipeline_state = st.session_state.get("pipeline_state")
    steps = st.columns(4)
    stage_definitions = [
        ("travel_explore", "Scout", T("评分排序", "Scoring")),
        ("sell", "Price", T("Top 5 定价", "Top 5 pricing")),
        ("edit_note", "Copy", T("SEO / 社交 / 话术", "SEO / social / sales")),
        ("visibility", "Monitor", T("库存与利润异常", "Stock and margin alerts")),
    ]
    for index, (icon, name, description) in enumerate(stage_definitions):
        complete = pipeline_state is not None
        border_color = "#4ae183" if complete else "rgba(255,255,255,.12)"
        status_text = T("完成", "Complete") if complete else T("待执行", "Ready")
        with steps[index]:
            st.markdown(
                f"""
                <div class="card-hover" style="min-height:132px;text-align:center;border-color:{border_color}!important;">
                  <span class="material-symbols-outlined" style="font-size:26px;color:{'#4ae183' if complete else '#b8aaad'};">{icon}</span>
                  <div style="font:700 14px Manrope;margin:10px 0 4px;">{name}</div>
                  <div style="color:#b8aaad;font-size:11px;">{description}</div>
                  <div style="margin-top:11px;color:{'#4ae183' if complete else '#b8aaad'};font:600 9px Geist;text-transform:uppercase;letter-spacing:.10em;">{status_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button(T("启动全流程  →", "Start pipeline  →"), type="primary", use_container_width=True, key="start_pipeline"):
        with st.status(T("正在执行四阶段规则流水线…", "Running the four-stage rule pipeline…"), expanded=True) as status:
            st.write(T("Scout：计算四维评分并排序", "Scout: scoring and ranking"))
            state = SalesPipeline().run(products_for_pipeline, target_pct / 100, pipeline_region)
            st.write(T("Price：按利润目标完成定价", "Price: calculating target-margin prices"))
            st.write(T("Copy：生成 SEO、社交与销售话术模板", "Copy: generating SEO, social and sales templates"))
            st.write(T("Monitor：检查库存与利润异常", "Monitor: checking stock and margin alerts"))
            st.session_state.pipeline_state = state
            st.session_state.pipeline_run_meta = {
                "target_pct": target_pct,
                "region": pipeline_region,
                "products": len(products_for_pipeline),
                "finished_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            }
            status.update(label=T("规则流水线执行完成", "Rule pipeline complete"), state="complete", expanded=False)
        st.rerun()

    pipeline_state = st.session_state.get("pipeline_state")
    if pipeline_state:
        st.progress(1.0, text=T("四个阶段均已完成", "All four stages complete"))
        result_score, result_price, result_copy, result_monitor = st.tabs([
            T("Scout 评分", "Scout scores"),
            T("Price 定价", "Price pricing"),
            T("Copy 文案", "Copy content"),
            T("Monitor 监控", "Monitor alerts"),
        ])
        with result_score:
            if pipeline_state.scored:
                score_rows = [{
                    T("商品", "Product"): result.product_name,
                    T("综合得分", "Final score"): round(result.final_score),
                    T("毛利", "Margin"): result.margin_score,
                    T("竞争", "Competition"): result.competition_score,
                    T("趋势", "Trend"): result.trend_score,
                    T("复购", "Repurchase"): result.repurchase_score,
                } for result in pipeline_state.scored]
                st.dataframe(pd.DataFrame(score_rows), width="stretch", hide_index=True)
        with result_price:
            if pipeline_state.priced:
                price_rows = pd.DataFrame(pipeline_state.priced).rename(columns={
                    "name": T("商品", "Product"),
                    "suggested_price": T("建议售价", "Suggested price"),
                    "profit": T("利润", "Profit"),
                    "margin": T("利润率", "Margin"),
                    "above_redline": T("达到红线", "Meets redline"),
                })
                st.dataframe(price_rows, width="stretch", hide_index=True)
        with result_copy:
            for generated in pipeline_state.copy or []:
                with st.expander(f"{generated['name']} · SEO / Social / Sales", expanded=False):
                    st.markdown(f"**SEO**  \n{generated['seo']}")
                    st.markdown(f"**{T('社交内容', 'Social')}**  \n{generated['social']}")
                    st.markdown(f"**{T('销售话术', 'Sales script')}**  \n{generated['script'].get('开场', '')}")
        with result_monitor:
            if pipeline_state.monitor:
                for monitor_item in pipeline_state.monitor:
                    has_urgent = any("断货" in issue for issue in monitor_item["issues"])
                    (st.error if has_urgent else st.warning)(f"**{monitor_item['name']}** · {'; '.join(monitor_item['issues'])}")
            else:
                st.success(T("所有商品均未触发库存或利润异常。", "No stock or margin alerts were triggered."))

        run_meta = st.session_state.get("pipeline_run_meta", {})
        with st.expander(T("运行摘要与日志", "Run summary and logs"), expanded=False):
            st.json(run_meta)
    else:
        info_strip(T(f"准备处理 {len(products_for_pipeline)} 个商品。启动后将依次执行四个规则阶段。", f"Ready to process {len(products_for_pipeline)} products through four rule stages."))

# ══ 物流配发 ══
elif page == "物流配发":
    if is_admin() and not is_read_only_demo():
        page_header(
            "P09 · EXECUTION",
            T("物流配发", "Logistics & Fulfillment"),
            T("该页面的配货与虚拟发货操作由员工角色执行。", "Allocation and simulated shipping are performed by the staff role."),
            T("当前角色：管理员", "Current role: Admin"),
            "coral",
        )
        info_strip(T("管理员可以查看功能范围，但不能执行配货或虚拟发货。请切换员工账号。", "Admins can review the scope but cannot allocate or simulate shipping. Switch to a staff account."))
        if st.button(T("返回工作台", "Back to dashboard"), type="primary", key="logistics_back_dashboard"):
            st.session_state.nav = "工作台"
            st.rerun()
        st.stop()

    page_header(
        "P09 · EXECUTION",
        T("物流配发", "Logistics & Fulfillment"),
        T("查看虚拟订单、完成配货并追踪六阶段模拟物流。", "Allocate virtual orders and follow the six-stage simulated delivery flow."),
        T("虚拟订单 · 模拟物流", "Virtual orders · Simulated logistics"),
        "green",
    )

    orders = get_mock_orders()
    warehouse = get_warehouse_inventory()

    # ── 初始化 session_state / Init session_state ──
    if "logistics_page" not in st.session_state:
        st.session_state.logistics_page = 1
    if "alloc_results" not in st.session_state:
        # 从文件恢复配货记录 / Restore allocation records from file
        data = load_allocation_log(st.session_state.company_file)
        if data:
            st.session_state.alloc_results = data.get("alloc_results", {})
            st.session_state.waybill_cache = data.get("waybill_cache", {})
            st.session_state.ship_timestamps = data.get("ship_timestamps", {})
        else:
            st.session_state.alloc_results = {}       # {order_id: allocation_result}
            st.session_state.waybill_cache = {}        # {order_id: waybill_no}
            st.session_state.ship_timestamps = {}      # {order_id: ISO datetime}
    if "logistics_expanded" not in st.session_state:
        st.session_state.logistics_expanded = set()  # expanded order_ids
    if "tracking_cache" not in st.session_state:
        st.session_state.tracking_cache = {}       # {order_id: tracking_data}
    if "waybill_cache" not in st.session_state:
        st.session_state.waybill_cache = {}        # already set above if loaded
    if "ship_timestamps" not in st.session_state:
        st.session_state.ship_timestamps = {}      # already set above if loaded
    if "alloc_clicked" not in st.session_state:
        st.session_state.alloc_clicked = set()     # orders where alloc was just triggered

    # ── 顶部总览卡片 ──
    pending = [o for o in orders if o["status"] == "pending"]
    picking = [o for o in orders if o["status"] == "picking"]
    shipped = [o for o in orders if o["status"] == "shipped"]

    mc = st.columns(4)
    mc[0].metric(T("总订单","Total"), len(orders))
    mc[1].metric(T("待处理","Pending"), len(pending),
                delta=T(f"{len(pending)}单待配货",f"{len(pending)} awaiting"))
    mc[2].metric(T("拣货中","Picking"), len(picking))
    mc[3].metric(T("已发货","Shipped"), len(shipped))

    st.divider()

    # ── 分页表格 ──
    PER_PAGE = 10
    total_pages = max(1, (len(orders) + PER_PAGE - 1) // PER_PAGE)

    # 矫正页码
    st.session_state.logistics_page = min(st.session_state.logistics_page, total_pages)
    page = st.session_state.logistics_page

    start = (page - 1) * PER_PAGE
    end = min(start + PER_PAGE, len(orders))
    page_orders = orders[start:end]

    # 表头
    hdr = st.columns([2.2, 1.6, 2.2, 0.7, 1.1, 1.2, 0.8])
    h_labels = [
        T("订单号","Order ID"), T("客户","Customer"),
        T("产品","Product"), T("数量","Qty"),
        T("状态","Status"), T("操作","Action"),
        T("展开","Expand"),
    ]
    for col, lbl in zip(hdr, h_labels):
        with col:
            st.markdown(f"**{lbl}**")
    st.markdown("---")

    # 数据行
    for o in page_orders:
        oid = o["order_id"]
        cust = o.get("customer_en" if is_en else "customer", o.get("customer",""))
        items_text = "、".join([f"{it['name' if not is_en else 'name_en']}×{it['qty']}" for it in o["items"]])
        total_qty = sum(it["qty"] for it in o["items"])

        status_map = {
            "pending": ("🟡 " + T("待处理","Pending"), "#f4b400"),
            "picking": ("🔵 " + T("拣货中","Picking"), "#4285f4"),
            "shipped": ("🟢 " + T("已发货","Shipped"), "#34a853"),
        }
        status_text, status_color = status_map.get(o["status"], ("❓", "#888"))

        row_cols = st.columns([2.2, 1.6, 2.2, 0.7, 1.1, 1.2, 0.8])

        with row_cols[0]:
            priority_badge = " 🔴" if o.get("priority") == "urgent" else ""
            st.markdown(f"`{oid}`{priority_badge}")
            st.caption(o["created_at"])

        with row_cols[1]:
            st.caption(cust)

        with row_cols[2]:
            st.caption(items_text if len(items_text) <= 30 else items_text[:27] + "...")

        with row_cols[3]:
            st.markdown(f"**{total_qty}**")

        with row_cols[4]:
            # ── 虚拟发货订单显示绿色已发货 ──
            is_virtual_shipped = oid in st.session_state.waybill_cache
            display_status = "shipped" if is_virtual_shipped else o["status"]
            vs_text, vs_color = status_map.get(display_status, ("❓", "#888"))
            st.markdown(
                f'<span style="color:{vs_color};font-weight:600;font-size:12px;">{vs_text}</span>',
                unsafe_allow_html=True,
            )

        with row_cols[5]:
            # ── 检查是否通过虚拟系统发货 ──
            is_virtual_shipped = oid in st.session_state.waybill_cache
            effective_status = "shipped" if is_virtual_shipped else o["status"]

            if effective_status == "pending":
                alloc_key = f"alloc_{oid}"
                if st.button(T("配货","Alloc"), key=f"alloc_btn_{oid}", type="primary"):
                    result = allocate_order(o, warehouse)
                    st.session_state.alloc_results[oid] = result
                    st.session_state.logistics_expanded.add(oid)
                    st.session_state.alloc_clicked.add(oid)
                    _persist_allocation()
                    st.rerun()
                # 配货完成后显示确认发货按钮（在展开区域内）
                if (oid in st.session_state.alloc_results and oid in st.session_state.logistics_expanded
                        and st.session_state.alloc_results[oid]["all_ok"]
                        and st.button(T("✅ 确认发货","✅ Confirm Ship"), key=f"confirm_ship_{oid}", type="primary")):
                    waybill = generate_waybill_no()
                    st.session_state.waybill_cache[oid] = waybill
                    st.session_state.ship_timestamps[oid] = datetime.now().isoformat()
                    st.session_state.tracking_cache.pop(oid, None)  # 清除旧缓存
                    _persist_allocation()
                    st.rerun()

            elif effective_status == "shipped":
                if st.button(T("追踪","Track"), key=f"track_btn_{oid}"):
                    if oid in st.session_state.logistics_expanded:
                        st.session_state.logistics_expanded.discard(oid)
                    else:
                        st.session_state.logistics_expanded.add(oid)
                        # 虚拟发货订单用虚拟追踪，否则用旧追踪
                        if oid in st.session_state.waybill_cache:
                            shipped_at = datetime.fromisoformat(st.session_state.ship_timestamps[oid])
                            st.session_state.tracking_cache[oid] = simulate_delivery_tracking(
                                st.session_state.waybill_cache[oid], shipped_at
                            )
                        elif oid not in st.session_state.tracking_cache:
                            st.session_state.tracking_cache[oid] = get_logistics_tracking(o.get("tracking_no",""))
                    st.rerun()
            elif effective_status == "picking":
                st.caption(T("拣货中…","Picking…"))

        with row_cols[6]:
            is_expanded = oid in st.session_state.logistics_expanded
            toggle_label = "▲" if is_expanded else "▼"
            if st.button(toggle_label, key=f"expand_{oid}"):
                if is_expanded:
                    st.session_state.logistics_expanded.discard(oid)
                else:
                    st.session_state.logistics_expanded.add(oid)
                    # 虚拟发货或普通已发货：加载追踪
                    is_vs = oid in st.session_state.waybill_cache
                    if (o["status"] == "shipped" or is_vs) and oid not in st.session_state.tracking_cache:
                        if is_vs:
                            shipped_at = datetime.fromisoformat(st.session_state.ship_timestamps[oid])
                            st.session_state.tracking_cache[oid] = simulate_delivery_tracking(
                                st.session_state.waybill_cache[oid], shipped_at
                            )
                        else:
                            st.session_state.tracking_cache[oid] = get_logistics_tracking(o.get("tracking_no",""))
                st.rerun()

        # ── 行内展开：配货结果 (SKU + 库位 + 数量 + ✅/❌) ──
        is_virtual_shipped = oid in st.session_state.waybill_cache
        effective_status = "shipped" if is_virtual_shipped else o["status"]

        if oid in st.session_state.alloc_results and oid in st.session_state.logistics_expanded:
            result = st.session_state.alloc_results[oid]
            with st.container(border=True):
                if result["all_ok"]:
                    st.success(T("✅ 配货成功 — 库存充足，可立即发货","✅ Allocated — Ready to ship"))
                else:
                    st.error(T("⚠️ 部分缺货 — 请查看明细","⚠️ Partial Shortage — Check details"))
                # ── 配货明细表 (Allocation Detail Table) ──
                for item in result["items"]:
                    icon = "✅" if item["ok"] else "❌"
                    loc_str = f"{item['location']} ({item['zone' if not is_en else 'zone_en']})"
                    if item["ok"]:
                        st.markdown(
                            T(
                                f"{icon} **{item['name']}** (SKU: `{item['sku']}`) — 配 {item['allocated']}/{item['needed']} 件 | 库位: {loc_str}",
                                f"{icon} **{item['name_en']}** (SKU: `{item['sku']}`) — {item['allocated']}/{item['needed']} pcs | Loc: {loc_str}",
                            )
                        )
                    else:
                        st.markdown(
                            T(
                                f"{icon} **{item['name']}** (SKU: `{item['sku']}`) — 缺 {item['shortage']} 件 (需 {item['needed']} / 存 {item['available']}) | 库位: {loc_str}",
                                f"{icon} **{item['name_en']}** (SKU: `{item['sku']}`) — Short {item['shortage']} (need {item['needed']} / avail {item['available']}) | Loc: {loc_str}",
                            )
                        )

        # ── 行内展开：虚拟快递追踪 / 物流追踪 ──
        if (effective_status == "shipped") and oid in st.session_state.logistics_expanded:
            is_virtual = oid in st.session_state.waybill_cache

            if is_virtual:
                # ── 虚拟快递配送管线 (Virtual Delivery Pipeline) ──
                waybill_no = st.session_state.waybill_cache[oid]
                shipped_at = datetime.fromisoformat(st.session_state.ship_timestamps[oid])
                tracking = st.session_state.tracking_cache.get(oid)
                if tracking is None:
                    tracking = simulate_delivery_tracking(waybill_no, shipped_at)
                    st.session_state.tracking_cache[oid] = tracking

                courier = tracking.get("courier_en" if is_en else "courier", tracking.get("courier", ""))
                with st.container(border=True):
                    st.markdown(
                        T(
                            f"🚚 **{courier}** · 运单号: `{waybill_no}` · 发货时间: {tracking['shipped_at']}",
                            f"🚚 **{courier}** · Tracking: `{waybill_no}` · Shipped: {tracking['shipped_at']}",
                        )
                    )
                    # 六阶段进度条
                    stage_count = tracking["total_stages"]
                    stage_labels = [
                        (T(DELIVERY_PIPELINE[i][0], DELIVERY_PIPELINE[i][1]), ["📋","📦","🏭","🚛","🏃","✅"][i])
                        for i in range(stage_count)
                    ]
                    current = tracking["current_stage"]
                    # 两行显示 6 阶段
                    row1_cols = st.columns(3)
                    row2_cols = st.columns(3)
                    for i, (label, icon) in enumerate(stage_labels):
                        if i < 3:
                            with row1_cols[i]:
                                if i < current:
                                    bg, tc = "#34a853", "#fff"
                                elif i == current:
                                    bg, tc = "#FF8C42", "#fff"
                                else:
                                    bg, tc = "#e0e0e0", "#888"
                                st.markdown(f"""<div style="background:{bg};color:{tc};border-radius:6px;padding:4px 2px;text-align:center;font-size:10px;font-weight:600;">
                                    {icon}<br>{label}
                                </div>""", unsafe_allow_html=True)
                        else:
                            with row2_cols[i - 3]:
                                if i < current:
                                    bg, tc = "#34a853", "#fff"
                                elif i == current:
                                    bg, tc = "#FF8C42", "#fff"
                                else:
                                    bg, tc = "#e0e0e0", "#888"
                                st.markdown(f"""<div style="background:{bg};color:{tc};border-radius:6px;padding:4px 2px;text-align:center;font-size:10px;font-weight:600;">
                                    {icon}<br>{label}
                                </div>""", unsafe_allow_html=True)
                    # 轨迹时间线
                    st.markdown("---")
                    for evt in tracking["events"]:
                        icon_map = {
                            "已接单":"📋","配货完成":"📦","已出库":"🏭","运输中":"🚛","派送中":"🏃","已签收":"✅",
                            "Order Accepted":"📋","Allocation Done":"📦","Dispatched":"🏭",
                            "In Transit":"🚛","Out for Delivery":"🏃","Delivered":"✅",
                        }
                        icon = icon_map.get(evt.get("status_cn",""), "📍")
                        st.markdown(
                            f"{icon} **{evt['time']}** — {evt['status_cn' if not is_en else 'status_en']}"
                        )
                        st.caption(evt.get("desc_cn" if not is_en else "desc_en",""))
                    if tracking["eta"]:
                        st.info(T(f"📅 预计到达：{tracking['eta']}",f"📅 ETA: {tracking['eta']}"))
            else:
                # ── 原始物流追踪 (Original 4-stage Tracking) ──
                courier = o.get("courier_en" if is_en else "courier", o.get("courier",""))
                tn = o.get("tracking_no","")
                tracking = st.session_state.tracking_cache.get(oid, get_logistics_tracking(tn))
                with st.container(border=True):
                    st.markdown(
                        T(
                            f"🚚 **{courier}** · 运单号: `{tn}`",
                            f"🚚 **{courier}** · Tracking: `{tn}`",
                        )
                    )
                    step_labels = [
                        (T("待揽收","Await Pickup"), "📋"),
                        (T("运输中","In Transit"), "🚛"),
                        (T("派送中","Out for Delivery"), "🏃"),
                        (T("已签收","Delivered"), "✅"),
                    ]
                    current = tracking["current_step"]
                    pc = st.columns(4)
                    for i, (label, icon) in enumerate(step_labels):
                        with pc[i]:
                            if i < current:
                                bg, tc = "#34a853", "#fff"
                            elif i == current:
                                bg, tc = "#FF8C42", "#fff"
                            else:
                                bg, tc = "#e0e0e0", "#888"
                            st.markdown(f"""<div style="background:{bg};color:{tc};border-radius:6px;padding:6px 2px;text-align:center;font-size:10px;font-weight:600;">
                                {icon}<br>{label}
                            </div>""", unsafe_allow_html=True)
                    st.markdown("---")
                    for evt in tracking["events"]:
                        icon_map = {
                            "待揽收":"📋","运输中":"🚛","派送中":"🏃","已签收":"✅",
                            "Awaiting Pickup":"📋","In Transit":"🚛","Out for Delivery":"🏃","Delivered":"✅",
                        }
                        icon = icon_map.get(evt.get("status_cn",""), "📍")
                        st.markdown(
                            f"{icon} **{evt['time']}** — {evt['status_cn' if not is_en else 'status_en']}"
                        )
                        st.caption(evt.get("desc_cn" if not is_en else "desc_en",""))
                    if tracking["eta"]:
                        st.info(T(f"📅 预计到达：{tracking['eta']}",f"📅 ETA: {tracking['eta']}"))

        # ── 行内展开：拣货中详情 ──
        if effective_status == "picking" and oid in st.session_state.logistics_expanded:
            addr = o.get("address_en" if is_en else "address", o.get("address",""))
            with st.container(border=True):
                st.markdown(
                    T(
                        f"📍 **地址：** {addr}",
                        f"📍 **Address:** {addr}",
                    )
                )
                st.progress(0.65, text=T("拣货中...","Picking..."))
                st.caption(T(f"创建时间：{o['created_at']}",f"Created: {o['created_at']}"))

        st.markdown("---")

    # ── 分页控件 ──
    st.markdown("")  # 间距
    if total_pages > 1:
        # 构建显示页码范围
        show_start = max(1, page - 2)
        show_end = min(total_pages, page + 2)
        # 确保始终显示 5 个（或 total_pages 个）
        if show_end - show_start < 4:
            if show_start == 1:
                show_end = min(total_pages, show_start + 4)
            else:
                show_start = max(1, show_end - 4)
        visible_pages = list(range(show_start, show_end + 1))

        pg_cols = st.columns([2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 2])
        # 上一页
        with pg_cols[0]:
            if st.button(T("← 上一页","← Prev"), disabled=(page <= 1), width="stretch",
                         key="prev_page"):
                st.session_state.logistics_page = page - 1
                st.rerun()
        # 页码按钮
        for i, pn in enumerate(visible_pages):
            col_idx = i + 1
            if col_idx >= len(pg_cols) - 1:
                break
            with pg_cols[col_idx]:
                is_current = pn == page
                btn_type = "primary" if is_current else "secondary"
                if st.button(str(pn), key=f"page_{pn}",
                             type=btn_type, width="stretch",
                             disabled=is_current):
                    st.session_state.logistics_page = pn
                    st.rerun()
        # 下一页
        with pg_cols[-1]:
            if st.button(T("下一页 →","Next →"), disabled=(page >= total_pages), width="stretch",
                         key="next_page"):
                st.session_state.logistics_page = page + 1
                st.rerun()

        st.caption(
            T(
                f"第 {page}/{total_pages} 页 · 共 {len(orders)} 条",
                f"Page {page}/{total_pages} · {len(orders)} total",
            )
        )

    # ── 仓库库存总览 ──
    st.divider()
    st.markdown(T("### 🏭 仓库库存总览","### 🏭 Warehouse Overview"))
    inv_cols = st.columns(min(len(warehouse), 4))
    for idx, inv_item in enumerate(warehouse):
        col_idx = idx % 4
        with inv_cols[col_idx]:
            qty = int(inv_item["qty"])
            status_class = "danger" if qty == 0 else ("warn" if qty < 15 else "ok")
            border_color = "#ea4335" if qty == 0 else ("#f4b400" if qty < 15 else "#34a853")
            st.markdown(f"""<div class="card-hover {status_class}" style="min-height:80px;">
                <div style="font-size:22px;font-weight:800;color:{border_color};">{qty}</div>
                <div style="font-size:12px;font-weight:600;">{inv_item['name' if not is_en else 'name_en']}</div>
                <div style="font-size:10px;color:#888;">{inv_item['sku']} · {inv_item['location']} ({inv_item['zone']})</div>
            </div>""", unsafe_allow_html=True)

    # ── 订单API接入口 (Order API Integration) ──
    st.divider()
    with st.expander(T("🔌 订单API接入口 / Order API Webhook Integration", "🔌 Order API Webhook Integration"), expanded=False):
        st.markdown(T("""
### 📡 Webhook 端点 / Webhook Endpoint

**POST** `/api/orders/webhook`
```
Content-Type: application/json
X-Signature: HMAC-SHA256 (签名验证 / signature verification)
```

#### 订单数据 Schema / Order Data Schema

```json
{{
  "order_id": "EXT-20260806-001",
  "platform": "shopify",
  "customer": {{
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "+86-13800138000"
  }},
  "shipping_address": {{
    "line1": "北京市朝阳区望京SOHO T3-1208",
    "city": "北京",
    "province": "北京市",
    "postal_code": "100102",
    "country": "CN"
  }},
  "items": [
    {{
      "sku": "BP-001",
      "name": "刻字狗牌",
      "qty": 2,
      "unit_price": 12.99
    }}
  ],
  "total": 25.98,
  "currency": "CNY",
  "created_at": "2026-08-06T15:30:00+08:00",
  "notes": "加急处理"
}}
```
""", """
### 📡 Webhook Endpoint

**POST** `/api/orders/webhook`
```
Content-Type: application/json
X-Signature: HMAC-SHA256
```

#### Order Data Schema

```json
{{
  "order_id": "EXT-20260806-001",
  "platform": "shopify",
  "customer": {{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0100"
  }},
  "shipping_address": {{
    "line1": "1000 Lujiazui Ring Rd",
    "city": "Shanghai",
    "province": "Shanghai",
    "postal_code": "200120",
    "country": "CN"
  }},
  "items": [
    {{
      "sku": "BP-001",
      "name": "Engraved Dog Tag",
      "qty": 2,
      "unit_price": 12.99
    }}
  ],
  "total": 25.98,
  "currency": "USD",
  "created_at": "2026-08-06T15:30:00Z",
  "notes": "Urgent"
}}
```
"""))

        st.markdown(T("""
---
### 🛍️ Shopify 接入步骤 / Shopify Integration

| 步骤 | 操作 |
|------|------|
| 1 | Shopify Admin → **Settings** → **Notifications** → **Webhooks** |
| 2 | Create webhook → Event: **Order creation** |
| 3 | Format: **JSON** |
| 4 | URL: `https://your-domain.com/api/orders/webhook` |
| 5 | HMAC 验证: 用 App Secret 计算 `X-Shopify-Hmac-SHA256` 并比对 |

**订单字段映射 / Field Mapping:**
| Shopify | RetailSense |
|---------|-------------|
| `order.id` | `order_id` |
| `line_items[].sku` | `items[].sku` |
| `line_items[].quantity` | `items[].qty` |
| `line_items[].price` | `items[].unit_price` |
| `shipping_address` | `shipping_address` |
| `total_price` | `total` |

---
### 🧶 Etsy / WooCommerce / 独立站接入 / Custom Store

通用流程：将平台订单转换为上述 JSON Schema，POST 到 `/api/orders/webhook`。
推荐在服务端实现幂等去重（按 `order_id`），防止重复 webhook 推送。

**独立站 Python 示例 / Custom Store Python Example:**
```python
import requests, hmac, hashlib, json

WEBHOOK_URL = "https://your-domain.com/api/orders/webhook"
WEBHOOK_SECRET = b"your-secret-key"

order_data = {{"order_id": "...", "platform": "custom", ...}}
body = json.dumps(order_data).encode()
signature = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()

requests.post(WEBHOOK_URL, data=body, headers={{
    "Content-Type": "application/json",
    "X-Signature": signature,
}})
```
""", """
---
### 🛍️ Shopify Integration

| Step | Action |
|------|--------|
| 1 | Shopify Admin → **Settings** → **Notifications** → **Webhooks** |
| 2 | Create webhook → Event: **Order creation** |
| 3 | Format: **JSON** |
| 4 | URL: `https://your-domain.com/api/orders/webhook` |
| 5 | Verify HMAC: compute `X-Shopify-Hmac-SHA256` with App Secret |

**Field Mapping:**
| Shopify | RetailSense |
|---------|-------------|
| `order.id` | `order_id` |
| `line_items[].sku` | `items[].sku` |
| `line_items[].quantity` | `items[].qty` |
| `line_items[].price` | `items[].unit_price` |
| `shipping_address` | `shipping_address` |
| `total_price` | `total` |

---
### 🧶 Etsy / WooCommerce / Custom Store

Convert platform orders to the JSON Schema above, POST to `/api/orders/webhook`.
Implement idempotency by `order_id` to prevent duplicate webhooks.

**Custom Store Python Example:**
```python
import requests, hmac, hashlib, json

WEBHOOK_URL = "https://your-domain.com/api/orders/webhook"
WEBHOOK_SECRET = b"your-secret-key"

order_data = {{"order_id": "...", "platform": "custom", ...}}
body = json.dumps(order_data).encode()
signature = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()

requests.post(WEBHOOK_URL, data=body, headers={{
    "Content-Type": "application/json",
    "X-Signature": signature,
}})
```
"""))

# ══ 商品上架 ══
elif page == "商品上架":
    if is_admin() and not is_read_only_demo():
        page_header(
            "P08 · EXECUTION",
            T("商品上架", "Product Listing"),
            T("该页面的模拟上架操作由员工角色执行。", "Simulated listing is performed by the staff role."),
            T("当前角色：管理员", "Current role: Admin"),
            "coral",
        )
        info_strip(T("管理员可以管理商品和平台配置，但不能执行模拟上架。请切换员工账号。", "Admins can manage products and platform settings but cannot run simulated listings. Switch to a staff account."))
        if st.button(T("返回工作台", "Back to dashboard"), type="primary", key="listing_back_dashboard"):
            st.session_state.nav = "工作台"
            st.rerun()
        st.stop()

    page_header(
        "P08 · EXECUTION",
        T("商品上架", "Product Listing"),
        T("选择商品与平台，检查 Listing 并保存模拟上架记录。", "Select a product and platform, review the listing and save a simulated record."),
        T("模拟上架 · 不调用平台 API", "Simulation · No platform API"),
        "coral",
    )

    # ── 初始化 listing session_state / Init listing session_state ──
    if "listing_records" not in st.session_state:
        # 从文件恢复上架记录 / Restore listing records from file
        data = load_listing_log(st.session_state.company_file)
        if data:
            st.session_state.listing_records = data.get("listing_records", [])
            st.session_state.listing_product_status = data.get("listing_product_status", {})
        else:
            st.session_state.listing_records = []
            st.session_state.listing_product_status = {}

    # ── 上架平台配置 ──
    PLATFORMS = {
        "shopify": {
            "name": "Shopify",
            "icon": "🛍️",
            "desc_cn": "全球独立电商平台，适合品牌化运营",
            "desc_en": "Global e-commerce platform for brand building",
            "domain": "myshopify.com",
            "listing_format": {
                "title_prefix_cn": "Premium",
                "title_prefix_en": "Premium",
                "title_suffix_cn": " — 官方旗舰店正品保障",
                "title_suffix_en": " — Official Store Guaranteed",
            },
        },
        "etsy": {
            "name": "Etsy",
            "icon": "🧶",
            "desc_cn": "手工艺/创意品平台，适合个性化宠物用品",
            "desc_en": "Handmade & creative marketplace for unique pet items",
            "domain": "etsy.com",
            "listing_format": {
                "title_prefix_cn": "手工定制",
                "title_prefix_en": "Handmade Custom",
                "title_suffix_cn": " — 匠心手作·宠物专属",
                "title_suffix_en": " — Artisan Crafted for Your Pet",
            },
        },
        "custom_store": {
            "name": T("独立站","Custom Store"),
            "icon": "🏠",
            "desc_cn": "自建品牌官网，完全掌控品牌与数据",
            "desc_en": "Self-hosted brand site, full control over brand & data",
            "domain": "yourstore.com",
            "listing_format": {
                "title_prefix_cn": "",
                "title_prefix_en": "",
                "title_suffix_cn": " — 品牌直营",
                "title_suffix_en": " — Direct from Brand",
            },
        },
    }

    # ── AI Listing 生成器 ──
    def generate_listing(product, platform_key, lang_z="zh"):
        pf = PLATFORMS[platform_key]
        fmt = pf["listing_format"]
        pn = product.get("name_en" if lang_z == "en" else "name", product.get("name", ""))
        pn_en = product.get("name_en", product.get("name", ""))
        cost = product.get("cost", 0)
        price = product.get("price", 0)
        img_key = product.get("img", "")

        prefix = fmt.get("title_prefix_en" if lang_z == "en" else "title_prefix_cn", "")
        suffix = fmt.get("title_suffix_en" if lang_z == "en" else "title_suffix_cn", "")
        title = f"{prefix} {pn} {suffix}".strip() if prefix else f"{pn}{suffix}"

        desc_templates = {
            "shopify": {
                "zh": (
                    f"✨ **{pn}** — 为您的爱宠打造的高品质选择。\n\n"
                    f"📌 **产品亮点：**\n"
                    f"• 精选材质，安全无毒，宠物放心使用\n"
                    f"• 精致工艺，细节彰显品质\n"
                    f"• 多尺寸可选，适配不同体型宠物\n"
                    f"• 耐用设计，经得起日常使用考验\n\n"
                    f"📦 **规格参数：**\n"
                    f"• 品牌：萌爪宠物用品\n"
                    f"• 材质：高品质环保材料\n"
                    f"• 适用对象：猫/狗通用\n\n"
                    f"🚚 **配送信息：** 下单后24小时内发货，全国包邮。\n"
                    f"💯 **售后保障：** 30天无忧退换，品质问题全额退款。"
                ),
                "en": (
                    f"✨ **{pn_en}** — Premium quality for your beloved pet.\n\n"
                    f"📌 **Key Features:**\n"
                    f"• Premium materials, pet-safe & non-toxic\n"
                    f"• Exquisite craftsmanship, quality in every detail\n"
                    f"• Multiple sizes for different breeds\n"
                    f"• Durable design, built for daily use\n\n"
                    f"📦 **Specifications:**\n"
                    f"• Brand: Pawsitive Pet Supplies\n"
                    f"• Material: High-quality eco-friendly materials\n"
                    f"• Suitable for: Cats & Dogs\n\n"
                    f"🚚 **Shipping:** Ships within 24 hours. Free shipping nationwide.\n"
                    f"💯 **Guarantee:** 30-day hassle-free returns. Full refund on quality issues."
                ),
            },
            "etsy": {
                "zh": (
                    f"🎨 **{pn}** — 每一件都是独一无二的心意之作。\n\n"
                    f"🌟 **为什么选择我们：**\n"
                    f"• 🖐️ 手工打造，每一件都倾注匠心\n"
                    f"• 🎁 支持个性化刻字/定制，独一无二\n"
                    f"• 🌿 环保材料，关爱地球也关爱宠物\n"
                    f"• 📸 实物拍摄，所见即所得\n\n"
                    f"📏 **尺寸说明：** 请参考详情页尺寸图表，选择最适合的规格。\n"
                    f"💌 **定制流程：** 下单 → 留言定制要求 → 3-5个工作日制作 → 发货\n\n"
                    f"🎀 **包装：** 精美礼盒包装，自用送人皆宜。"
                ),
                "en": (
                    f"🎨 **{pn_en}** — Each piece is a unique creation from the heart.\n\n"
                    f"🌟 **Why Choose Us:**\n"
                    f"• 🖐️ Handcrafted with love and attention\n"
                    f"• 🎁 Personalization available — make it truly yours\n"
                    f"• 🌿 Eco-friendly materials, kind to planet & pets\n"
                    f"• 📸 Real product photos, what you see is what you get\n\n"
                    f"📏 **Sizing:** Check our size chart and pick the perfect fit.\n"
                    f"💌 **Custom Order:** Order → Send customization request → 3-5 business days → Ship\n\n"
                    f"🎀 **Packaging:** Beautiful gift box, perfect for gifting."
                ),
            },
            "custom_store": {
                "zh": (
                    f"🏠 **{pn}** — 品牌直营，品质保证。\n\n"
                    f"**产品详情：**\n"
                    f"• 品牌直供，省去中间环节，价格更优\n"
                    f"• 严格品控，每件产品出厂前经过3道检验\n"
                    f"• 专属客服，一对一解答您的疑问\n"
                    f"• 会员专享价，注册即享9折优惠\n\n"
                    f"**规格：** 标准款 / 升级款可选\n"
                    f"**发货：** 48小时内发货，顺丰包邮\n"
                    f"**售后：** 7天无理由退换，1年质保"
                ),
                "en": (
                    f"🏠 **{pn_en}** — Direct from our brand, quality guaranteed.\n\n"
                    f"**Product Details:**\n"
                    f"• Direct from brand, no middlemen, better prices\n"
                    f"• Rigorous QC — 3 inspections before shipping\n"
                    f"• Dedicated support, 1-on-1 assistance\n"
                    f"• Member exclusive: 10% off on registration\n\n"
                    f"**Options:** Standard / Premium\n"
                    f"**Shipping:** Ships in 48h, free express delivery\n"
                    f"**Warranty:** 7-day returns, 1-year guarantee"
                ),
            },
        }
        description = desc_templates.get(platform_key, desc_templates["shopify"]).get(lang_z, desc_templates["shopify"]["zh"])

        stock = product.get("qty", 50)
        safety_stock = max(5, int(stock * 0.15))

        seo_tags_cn = f"{pn},宠物用品,萌爪,{pn_en},宠物"
        seo_tags_en = f"{pn_en},pet supplies,dog,cat,{pn},pawsitive"

        return {
            "title": title,
            "description": description,
            "price": price,
            "cost": cost,
            "stock": stock,
            "safety_stock": safety_stock,
            "img_key": img_key,
            "platform": platform_key,
            "platform_name": pf["name"],
            "platform_icon": pf["icon"],
            "seo_tags": seo_tags_en if lang_z == "en" else seo_tags_cn,
            "listing_url": f"https://{pf['domain']}/products/{pn_en.lower().replace(' ','-')}",
        }

    # ── 产品列表（含上架状态）──
    products_for_listing = []
    for p in st.session_state.products:
        pn = p.get("name", "")
        status = st.session_state.listing_product_status.get(pn, "待上架")
        status_en = "Pending" if status == "待上架" else "Listed"
        products_for_listing.append({**p, "listing_status": status, "listing_status_en": status_en})

    tab_list, tab_history = st.tabs([
        T("📤 上架操作", "📤 List Product"),
        T("📋 上架记录", "📋 Listing History"),
    ])

    with tab_list:
        st.markdown(T("### 🎯 选择产品上架", "### 🎯 Select Product to List"))

        # ── 产品卡片网格 ──
        cols = st.columns(min(len(products_for_listing), 4))
        selected_product_idx = st.session_state.get("listing_selected_idx", 0)

        for i, p in enumerate(products_for_listing):
            col_idx = i % 4
            with cols[col_idx]:
                b64 = _get_product_image(p.get("img", ""))
                status = p["listing_status"]
                is_pending = status == "待上架"
                border = "2px solid #ff7f6e" if i == selected_product_idx else ("1px solid rgba(255,255,255,.12)" if is_pending else "1px solid rgba(74,225,131,.35)")
                bg = "rgba(255,127,110,.08)" if i == selected_product_idx else ("rgba(255,255,255,.045)" if is_pending else "rgba(74,225,131,.06)")

                status_badge_cn = "🟡 待上架" if is_pending else "🟢 已上架"
                status_badge_en = "🟡 Pending" if is_pending else "🟢 Listed"

                card_html = f'''<div style="border:{border};border-radius:8px;padding:10px;text-align:center;background:{bg};min-height:170px;">
                    <span style="font-size:10px;font-weight:600;">{status_badge_en if is_en else status_badge_cn}</span><br>'''
                if b64:
                    card_html += f'<img src="data:image/jpeg;base64,{b64}" style="width:64px;height:64px;border-radius:6px;object-fit:cover;margin:4px 0;"><br>'
                else:
                    card_html += '<span style="font-size:28px;">🐾</span><br>'
                card_html += f'''<div style="font-weight:600;font-size:12px;">{escape_html(pname(p))}</div>
                    <div style="font-size:11px;color:#FF8C42;font-weight:700;">¥{p["price"]:.2f}</div>
                    <div style="font-size:10px;color:#888;">成本 ¥{p["cost"]:.2f}</div></div>'''
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button(T("选择","Select"), key=f"listing_sel_{i}", width="stretch"):
                    st.session_state.listing_selected_idx = i
                    st.rerun()

        st.divider()

        # ── 选中产品详情 ──
        selected = products_for_listing[selected_product_idx]
        sel_pending = selected["listing_status"] == "待上架"

        detail_cols = st.columns([1, 2])
        with detail_cols[0]:
            b64 = _get_product_image(selected.get("img", ""))
            if b64:
                st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:160px;height:160px;border-radius:10px;object-fit:cover;">', unsafe_allow_html=True)

        with detail_cols[1]:
            st.markdown(f"### {pname(selected)}")
            sel_status = selected["listing_status"]
            st.markdown(f'<span style="color:{"#34a853" if sel_status != "待上架" else "#f4b400"};font-weight:600;">{"🟢 " + T("已上架","Listed") if sel_status != "待上架" else "🟡 " + T("待上架","Pending")}</span>', unsafe_allow_html=True)

            mc = st.columns(3)
            mc[0].metric(T("售价","Price"), f"¥{selected['price']:.2f}")
            mc[1].metric(T("成本","Cost"), f"¥{selected['cost']:.2f}")
            mc[2].metric(T("毛利","Margin"), f"¥{selected['price'] - selected['cost']:.2f}",
                        delta=f"{(selected['price'] - selected['cost']) / selected['price'] * 100:.0f}%")

            comp = selected.get("competitors", 0)
            growth = selected.get("search_growth", 0)
            st.caption(T(
                f"竞品数: {comp} · 搜索增长: {growth}% · 复购: {selected.get('annual_purchases',1)}次/年",
                f"Competitors: {comp} · Search Growth: {growth}% · Repurchase: {selected.get('annual_purchases',1)}/yr"
            ))

        st.divider()

        # ── 平台选择 ──
        st.markdown(T("### 🛒 选择上架平台", "### 🛒 Choose Platform"))

        plat_cols = st.columns(3)
        selected_platform = st.session_state.get("listing_selected_platform", "shopify")

        for i, (pkey, pinfo) in enumerate(PLATFORMS.items()):
            with plat_cols[i]:
                is_sel_plat = selected_platform == pkey
                border_p = "2px solid #ff7f6e" if is_sel_plat else "1px solid rgba(255,255,255,.12)"
                bg_p = "rgba(255,127,110,.08)" if is_sel_plat else "rgba(255,255,255,.045)"
                st.markdown(f"""<div style="border:{border_p};border-radius:8px;padding:12px;text-align:center;background:{bg_p};min-height:110px;">
                    <div style="font-size:28px;">{pinfo['icon']}</div>
                    <div style="font-weight:700;font-size:13px;">{pinfo['name']}</div>
                    <div style="font-size:10px;color:#888;">{pinfo['desc_en'] if is_en else pinfo['desc_cn']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(T("选择","Select") + f" {pinfo['name']}", key=f"plat_sel_{pkey}", width="stretch",
                             type="primary" if is_sel_plat else "secondary"):
                    st.session_state.listing_selected_platform = pkey
                    st.rerun()

        st.divider()

        # ── Listing 预览 ──
        listing = generate_listing(selected, selected_platform, "en" if is_en else "zh")

        st.markdown(T("### 📝 Listing 预览", "### 📝 Listing Preview"))
        with st.container(border=True):
            st.markdown(f"**{T('标题','Title')}:** {listing['title']}")
            st.caption(T(f"SEO 标签: {listing['seo_tags']}", f"SEO Tags: {listing['seo_tags']}"))

            lc = st.columns(4)
            lc[0].metric(T("售价","Price"), f"¥{listing['price']:.2f}")
            lc[1].metric(T("成本","Cost"), f"¥{listing['cost']:.2f}")
            lc[2].metric(T("库存","Stock"), int(listing['stock']))
            lc[3].metric(T("安全库存","Safety"), int(listing['safety_stock']))

            with st.expander(T("📄 完整描述", "📄 Full Description"), expanded=True):
                st.markdown(listing["description"])

        st.divider()

        # ── 一键上架按钮 ──
        if sel_pending:
            st.markdown(T("### 确认模拟上架", "### Confirm Simulated Listing"))

            st.markdown(T(
                f"即将为 **{pname(selected)}** 生成 **{listing['platform_icon']} {listing['platform_name']}** Listing，并保存本地模拟记录。",
                f"A **{listing['platform_icon']} {listing['platform_name']}** listing will be generated for **{pname(selected)}** and saved locally."
            ))

            st.caption(T(
                f"模拟链接预览：`{listing['listing_url']}`（不会请求该地址）",
                f"Simulated URL preview: `{listing['listing_url']}` (the address will not be requested)"
            ))

            if st.button(T("确认模拟上架", "Confirm Simulation"), type="primary", width="stretch", key="do_listing"):
                with st.spinner(T("正在生成 Listing 并保存本地记录…", "Generating the listing and saving a local record…")):
                    import time
                    time.sleep(0.6)

                record = {
                    "product": pname(selected),
                    "product_en": selected.get("name_en", ""),
                    "platform": listing["platform"],
                    "platform_name": listing["platform_name"],
                    "platform_icon": listing["platform_icon"],
                    "title": listing["title"],
                    "price": listing["price"],
                    "stock": int(listing["stock"]),
                    "listing_url": listing["listing_url"],
                    "seo_tags": listing["seo_tags"],
                    "listed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "listed_by": current_user(),
                    "status": "success",
                }
                st.session_state.listing_records.insert(0, record)
                st.session_state.listing_product_status[pname(selected)] = "已上架"
                _persist_listing()

                st.success(T(
                    f"✅ **模拟上架成功，已保存本地记录。** 商品：{pname(selected)} · 平台模板：{listing['platform_name']}",
                    f"✅ **Simulated listing complete and saved locally.** Product: {pname(selected)} · Template: {listing['platform_name']}"
                ))
                st.info(T(
                    f"模拟链接：`{listing['listing_url']}`\n\n📅 记录时间：{record['listed_at']}\n👤 操作人：{record['listed_by']}",
                    f"Simulated URL: `{listing['listing_url']}`\n\n📅 Recorded: {record['listed_at']}\n👤 By: {record['listed_by']}"
                ))
                time.sleep(0.5)
                st.rerun()
        else:
            st.info(T(
                f"✅ **{pname(selected)}** 已经上架，如需重新上架到其他平台请先在「上架记录」中删除后重试。",
                f"✅ **{pname(selected)}** is already listed. Remove the existing record in 'Listing History' before re-listing."
            ))

    # ── 上架记录 Tab ──
    with tab_history:
        st.markdown(T("### 📋 上架历史记录", "### 📋 Listing History"))

        records = st.session_state.listing_records
        if not records:
            st.info(T("暂无上架记录。请先在上架操作中完成商品上架。", "No listing records yet. List a product first."))
        else:
            st.caption(T(f"共 {len(records)} 条记录", f"{len(records)} records total"))

            # 统计卡片
            platforms_count = {}
            for r in records:
                pf = r["platform_name"]
                platforms_count[pf] = platforms_count.get(pf, 0) + 1

            stat_cols = st.columns(min(len(platforms_count), 4) if platforms_count else 1)
            for i, (pf, cnt) in enumerate(platforms_count.items()):
                with stat_cols[i % 4]:
                    icon = next((p["icon"] for p in PLATFORMS.values() if p["name"] == pf), "📦")
                    st.markdown(f"""<div class="card-hover ok" style="min-height:60px;text-align:center;">
                        <div style="font-size:20px;">{icon}</div>
                        <div style="font-size:18px;font-weight:700;color:#FF8C42;">{cnt}</div>
                        <div style="font-size:10px;color:#888;">{pf}</div>
                    </div>""", unsafe_allow_html=True)

            st.divider()

            # 记录列表
            for i, r in enumerate(records):
                with st.container(border=True):
                    rc = st.columns([0.8, 2.5, 1.5, 1.5, 1.5, 1.5])
                    with rc[0]:
                        st.markdown(f"{r['platform_icon']}")
                    with rc[1]:
                        st.markdown(f"**{r['product']}**")
                        if r.get("product_en"):
                            st.caption(r["product_en"])
                    with rc[2]:
                        st.markdown(T("平台","Platform"))
                        st.caption(r["platform_name"])
                    with rc[3]:
                        st.markdown(T("售价","Price"))
                        st.caption(f"¥{r['price']:.2f}")
                    with rc[4]:
                        st.markdown(T("库存","Stock"))
                        st.caption(str(int(r.get("stock", 0))))
                    with rc[5]:
                        st.markdown(T("时间","Time"))
                        st.caption(r["listed_at"])

                    with st.expander(T(f"📄 查看 Listing — {r['title'][:40]}...", f"📄 View Listing — {r['title'][:40]}..."), expanded=False):
                        st.markdown(f"**{T('标题','Title')}:** {r['title']}")
                        st.markdown(f"**{T('模拟链接','Simulated URL')}:** `{r['listing_url']}`")
                        st.caption(f"**SEO Tags:** {r.get('seo_tags','')}")
                        st.caption(T(
                            f"上架人: {r.get('listed_by','')} · 状态: {'✅ 成功' if r.get('status') == 'success' else '❌ 失败'}",
                            f"Listed by: {r.get('listed_by','')} · Status: {'✅ Success' if r.get('status') == 'success' else '❌ Failed'}"
                        ))

                    pending_delete = st.session_state.get("listing_delete_confirm_idx") == i
                    if not pending_delete:
                        if st.button(T("删除此记录", "Delete record"), key=f"del_listing_{i}"):
                            st.session_state.listing_delete_confirm_idx = i
                            st.rerun()
                    else:
                        st.warning(T("确认移除这条本地模拟记录？此操作会恢复商品的待上架状态。", "Remove this local simulation record and restore the product to pending?"))
                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            if st.button(T("确认移除", "Confirm removal"), type="primary", key=f"confirm_del_listing_{i}"):
                                product_name = r.get("product", "")
                                if product_name in st.session_state.listing_product_status:
                                    del st.session_state.listing_product_status[product_name]
                                st.session_state.listing_records.pop(i)
                                st.session_state.listing_delete_confirm_idx = None
                                _persist_listing()
                                st.rerun()
                        with cancel_col:
                            if st.button(T("取消", "Cancel"), key=f"cancel_del_listing_{i}"):
                                st.session_state.listing_delete_confirm_idx = None
                                st.rerun()

# ══ 导出报表 ══
elif page == "导出报表":
    page_header(
        "P10 · DATA",
        T("导出报表", "Export Data Reports"),
        T("预览数据摘要，并安全导出营收、库存和产品列表。", "Preview summaries and safely export revenue, inventory and product data."),
        T("虚拟演示数据", "Virtual demo data"),
        "coral",
    )

    # ── 公司信息 ──
    if st.session_state.use_company and company:
        st.success(T(
            f"已接入：{company['company']}",
            f"Connected: {company['company_en']}"
        ))
        co_name = company.get("company", "")
        co_name_en = company.get("company_en", "")
        co_established = company.get("established", "")
        co_currency = company.get("currency", "CNY")
    else:
        st.info(T("手动模式 — 使用默认产品数据", "Manual mode — using default product data"))
        co_name = "萌爪宠物用品（杭州）"
        co_name_en = "Mengzhua Pet Supplies (Hangzhou)"
        co_established = "2023-08"
        co_currency = "CNY"

    # ── 计算数据摘要 ──
    today_data = daily_summary(txns, 1, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    week_data = daily_summary(txns, 7, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    month_data = daily_summary(txns, 30, inventory=inv) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    inv_sum = inventory_value_summary(inv) if inv else {
        "total_qty": 0, "total_value": 0, "total_retail": 0,
        "skus": 0, "low_stock": 0, "reorder_needed": 0,
        "out_of_stock": 0, "normal": 0,
    }

    # ── 数据概览卡片 ──
    st.markdown(T("### 📊 数据概览", "### 📊 Data Overview"))
    cc = st.columns(4)
    cc[0].metric(
        T("今日营收", "Today Revenue"),
        f"¥{today_data['revenue']:,.0f}",
        f"{today_data['orders']}{T('单', ' orders')}",
    )
    cc[1].metric(
        T("本周营收", "Week Revenue"),
        f"¥{week_data['revenue']:,.0f}",
    )
    cc[2].metric(
        T("本月营收", "Month Revenue"),
        f"¥{month_data['revenue']:,.0f}",
    )
    cc[3].metric(
        T("库存总值", "Inventory Value"),
        f"¥{inv_sum['total_retail']:,.0f}",
        f"{inv_sum['skus']} SKU",
    )

    st.divider()

    cc2 = st.columns(4)
    cc2[0].metric(T("总库存量", "Total Qty"), inv_sum["total_qty"])
    cc2[1].metric(T("库存成本", "Inventory Cost"), f"¥{inv_sum['total_value']:,.0f}")
    cc2[2].metric(T("低库存品", "Low Stock"), inv_sum["low_stock"], delta_color="inverse")
    cc2[3].metric(T("断货品", "Out of Stock"), inv_sum["out_of_stock"], delta_color="inverse")

    # ── 产品列表表格 ──
    st.divider()
    st.markdown(T("### 📦 产品列表", "### 📦 Product List"))

    if inv:
        prod_rows = []
        for i in inv:
            qty = int(i.get("qty", 0))
            daily = int(i.get("daily_avg", 1))
            lead = i.get("lead_days", 3)
            safety = max(1, round(daily * 7))
            status_cn = "断货" if qty == 0 else ("低库存" if qty < safety else "正常")
            status_en = "OOS" if qty == 0 else ("Low" if qty < safety else "Normal")
            prod_rows.append({
                T("产品", "Product"): pname(i),
                "SKU": i.get("sku", ""),
                T("库存", "Qty"): qty,
                T("成本", "Cost"): f"¥{i.get('cost', 0):.2f}",
                T("售价", "Price"): f"¥{i.get('price', 0):.2f}",
                T("日均销量", "Daily Avg"): daily,
                T("安全库存", "Safety"): safety,
                T("状态", "Status"): status_en if is_en else status_cn,
            })
        st.dataframe(pd.DataFrame(prod_rows), width="stretch", hide_index=True)
    else:
        # 使用默认产品数据
        default_prods = [
            {"name": "刻字狗牌", "name_en": "Engraved Dog Tag", "qty": 45, "cost": 2.80, "price": 12.99, "daily_avg": 9, "lead_days": 3, "sku": "BP-001"},
            {"name": "发光项圈", "name_en": "LED Collar", "qty": 12, "cost": 5.50, "price": 24.99, "daily_avg": 6, "lead_days": 5, "sku": "BP-002"},
            {"name": "珐琅名牌", "name_en": "Enamel Nameplate", "qty": 120, "cost": 3.20, "price": 16.99, "daily_avg": 3, "lead_days": 3, "sku": "BP-003"},
            {"name": "牵引绳套装", "name_en": "Leash Set", "qty": 0, "cost": 4.50, "price": 22.99, "daily_avg": 4, "lead_days": 4, "sku": "BP-004"},
            {"name": "换牙零食", "name_en": "Teething Treats", "qty": 8, "cost": 3.00, "price": 11.99, "daily_avg": 15, "lead_days": 2, "sku": "BP-005"},
        ]
        default_rows = []
        for i in default_prods:
            qty = i["qty"]
            daily = i["daily_avg"]
            safety = max(1, round(daily * 7))
            status_cn = "断货" if qty == 0 else ("低库存" if qty < safety else "正常")
            status_en = "OOS" if qty == 0 else ("Low" if qty < safety else "Normal")
            default_rows.append({
                T("产品", "Product"): pname(i),
                "SKU": i["sku"],
                T("库存", "Qty"): qty,
                T("成本", "Cost"): f"¥{i['cost']:.2f}",
                T("售价", "Price"): f"¥{i['price']:.2f}",
                T("日均销量", "Daily Avg"): daily,
                T("安全库存", "Safety"): safety,
                T("状态", "Status"): status_en if is_en else status_cn,
            })
        st.dataframe(pd.DataFrame(default_rows), width="stretch", hide_index=True)

    # ── 交易记录（最近10条）──
    if txns:
        st.divider()
        st.markdown(T("### 💰 近期交易记录", "### 💰 Recent Transactions"))
        txn_rows = []
        for t in sorted(txns, key=lambda x: x["date"], reverse=True)[:10]:
            txn_type_cn = "出库" if t["type"] == "out" else "入库"
            txn_type_en = "Out" if t["type"] == "out" else "In"
            txn_rows.append({
                T("日期", "Date"): t["date"],
                T("类型", "Type"): txn_type_en if is_en else txn_type_cn,
                T("产品", "Product"): t.get("product", ""),
                "SKU": t.get("sku", ""),
                T("数量", "Qty"): t["qty"],
                T("金额", "Amount"): f"¥{t['revenue']:,.0f}" if t["type"] == "out" else "—",
            })
        st.dataframe(pd.DataFrame(txn_rows), width="stretch", hide_index=True)

    # ── 导出下载区域 ──
    st.divider()
    st.markdown(T("### 📥 下载导出", "### 📥 Download Export"))

    # ── 构建 CSV 内容 ──
    import csv
    import io

    # --- CSV 模式选择 ---
    export_mode = st.radio(
        T("导出内容", "Export Content"),
        [
            T("📊 完整报告（公司信息 + 营收 + 库存 + 产品列表）", "📊 Full Report (Company + Revenue + Inventory + Products)"),
            T("📦 仅产品列表", "📦 Products Only"),
            T("💰 仅营收汇总", "💰 Revenue Summary Only"),
        ],
        horizontal=True,
    )

    # 构建 CSV
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerow([T("数据说明", "Data notice"), T("虚拟演示数据，仅用于产品原型与求职展示", "Virtual demo data for product prototyping and portfolio demonstration only")])
    csv_writer.writerow([])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = safe_filename(co_name)

    if export_mode.startswith(("📊", "📦")):
        # 写产品列表
        csv_writer.writerow([
            T("公司", "Company"), T("产品", "Product"), "SKU",
            T("库存", "Qty"), T("成本", "Cost"), T("售价", "Price"),
            T("日均销量", "Daily Avg"), T("安全库存", "Safety"), T("状态", "Status"),
        ])
        source = inv if inv else default_prods
        for i in source:
            qty = int(i.get("qty", 0))
            daily = float(i.get("daily_avg", 0))
            item_summary = inventory_item_summary(i)
            safety = item_summary["safety_stock"]
            status_val = {
                "断货": "OOS", "低库存": "Low", "建议补货": "Reorder",
                "滞销": "Stale", "正常": "Normal",
            }.get(item_summary["status"], item_summary["status"])
            csv_writer.writerow([
                csv_safe(co_name),
                csv_safe(pname(i)),
                csv_safe(i.get("sku", "")),
                qty,
                i.get("cost", 0),
                i.get("price", 0),
                daily,
                safety,
                status_val,
            ])

    if export_mode.startswith(("📊", "💰")):
        csv_writer.writerow([])  # 空行分隔
        # 营收汇总
        csv_writer.writerow([
            T("营收指标", "Revenue Metric"), T("金额 (¥)", "Amount (¥)"), T("备注", "Notes"),
        ])
        csv_writer.writerow([T("今日营收", "Today Revenue"), today_data["revenue"], f"{today_data['orders']}{T('单', ' orders')}"])
        csv_writer.writerow([T("本周营收", "Week Revenue"), week_data["revenue"], ""])
        csv_writer.writerow([T("本月营收", "Month Revenue"), month_data["revenue"], ""])
        csv_writer.writerow([T("今日利润", "Today Profit"), today_data["profit"], ""])
        csv_writer.writerow([T("本周利润", "Week Profit"), week_data["profit"], ""])
        csv_writer.writerow([T("本月利润", "Month Profit"), month_data["profit"], ""])
        csv_writer.writerow([])
        # 库存汇总
        csv_writer.writerow([T("库存指标", "Inventory Metric"), T("数值", "Value")])
        csv_writer.writerow([T("总库存量", "Total Qty"), inv_sum["total_qty"]])
        csv_writer.writerow([T("库存成本总值", "Total Cost Value"), inv_sum["total_value"]])
        csv_writer.writerow([T("库存零售总值", "Total Retail Value"), inv_sum["total_retail"]])
        csv_writer.writerow([T("SKU数", "SKU Count"), inv_sum["skus"]])
        csv_writer.writerow([T("低库存SKU", "Low Stock SKUs"), inv_sum["low_stock"]])
        csv_writer.writerow([T("断货SKU", "Out of Stock SKUs"), inv_sum["out_of_stock"]])

    csv_data = csv_buffer.getvalue()

    # ── 文本格式内容 ──
    txt_buffer = io.StringIO()
    txt_buffer.write(f"{'='*60}\n")
    txt_buffer.write(f"{T('公司数据报告', 'Company Data Report')}\n")
    txt_buffer.write(f"{T('虚拟演示数据，仅用于产品原型与求职展示', 'Virtual demo data for product prototyping and portfolio demonstration only')}\n")
    txt_buffer.write(f"{'='*60}\n")
    txt_buffer.write(f"{T('公司名称', 'Company')}: {co_name} / {co_name_en}\n")
    txt_buffer.write(f"{T('成立时间', 'Established')}: {co_established}\n")
    txt_buffer.write(f"{T('导出时间', 'Exported')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    txt_buffer.write(f"\n{'='*60}\n")
    txt_buffer.write(f"{T('营收摘要', 'Revenue Summary')}\n")
    txt_buffer.write(f"{'='*60}\n")
    txt_buffer.write(f"{T('今日营收', 'Today Revenue')}: ¥{today_data['revenue']:,.0f} ({today_data['orders']}{T('单', ' orders')})\n")
    txt_buffer.write(f"{T('本周营收', 'Week Revenue')}: ¥{week_data['revenue']:,.0f}\n")
    txt_buffer.write(f"{T('本月营收', 'Month Revenue')}: ¥{month_data['revenue']:,.0f}\n")
    txt_buffer.write(f"{T('今日利润', 'Today Profit')}: ¥{today_data['profit']:,.0f}\n")
    txt_buffer.write(f"{T('本周利润', 'Week Profit')}: ¥{week_data['profit']:,.0f}\n")
    txt_buffer.write(f"{T('本月利润', 'Month Profit')}: ¥{month_data['profit']:,.0f}\n")
    txt_buffer.write(f"\n{'='*60}\n")
    txt_buffer.write(f"{T('库存摘要', 'Inventory Summary')}\n")
    txt_buffer.write(f"{'='*60}\n")
    txt_buffer.write(f"{T('总库存量', 'Total Qty')}: {inv_sum['total_qty']}\n")
    txt_buffer.write(f"{T('库存成本总值', 'Total Cost')}: ¥{inv_sum['total_value']:,.0f}\n")
    txt_buffer.write(f"{T('库存零售总值', 'Total Retail')}: ¥{inv_sum['total_retail']:,.0f}\n")
    txt_buffer.write(f"{T('SKU数', 'SKUs')}: {inv_sum['skus']}\n")
    txt_buffer.write(f"{T('低库存', 'Low Stock')}: {inv_sum['low_stock']}\n")
    txt_buffer.write(f"{T('断货', 'Out of Stock')}: {inv_sum['out_of_stock']}\n")
    txt_buffer.write(f"\n{'='*60}\n")
    txt_buffer.write(f"{T('产品列表', 'Product List')}\n")
    txt_buffer.write(f"{'='*60}\n")
    txt_buffer.write(f"{'Product':<20} {'SKU':<10} {'Qty':>6} {'Cost':>8} {'Price':>8} {'Status':>10}\n")
    txt_buffer.write(f"{'-'*62}\n")
    source = inv if inv else default_prods
    for i in source:
        qty = int(i.get("qty", 0))
        item_summary = inventory_item_summary(i)
        status_val = {
            "断货": "OOS", "低库存": "Low", "建议补货": "Reorder",
            "滞销": "Stale", "正常": "Normal",
        }.get(item_summary["status"], item_summary["status"])
        txt_buffer.write(
            f"{pname(i):<20} {i.get('sku',''):<10} {qty:>6} "
            f"¥{i.get('cost',0):>7.2f} ¥{i.get('price',0):>7.2f} {status_val:>10}\n"
        )
    txt_buffer.write(f"\n{'='*60}\n")
    txt_buffer.write(f"{T('近期交易', 'Recent Transactions')}\n")
    txt_buffer.write(f"{'='*60}\n")
    if txns:
        for t in sorted(txns, key=lambda x: x["date"], reverse=True)[:10]:
            txn_type = "OUT" if t["type"] == "out" else "IN "
            txt_buffer.write(
                f"{t['date']} | {txn_type} | {t.get('product',''):<12} | "
                f"x{t['qty']:<4} | ¥{t['revenue']:,.0f}\n"
            )
    else:
        txt_buffer.write(T("暂无交易数据", "No transaction data") + "\n")

    txt_data = txt_buffer.getvalue()

    # ── 下载按钮 ──
    st.markdown(f"""
    <style>
    .export-download-area {{
        background: linear-gradient(135deg, #FFF8F0, #FFE8D6);
        border: 2px dashed #FF8C42;
        border-radius: 12px;
        padding: 24px 20px;
        text-align: center;
        margin: 12px 0;
    }}
    .export-download-area:hover {{
        box-shadow: 0 4px 16px rgba(255, 107, 53, 0.15);
    }}
    .export-icon {{
        font-size: 48px;
        margin-bottom: 8px;
    }}
    .export-title {{
        font-size: 18px;
        font-weight: 700;
        color: #FF8C42;
        margin-bottom: 4px;
    }}
    .export-sub {{
        font-size: 12px;
        color: #888;
        margin-bottom: 16px;
    }}
    </style>
    <div class="export-download-area">
        <div class="export-icon">📥</div>
        <div class="export-title">{T('下载公司数据报告', 'Download Company Data Report')}</div>
        <div class="export-sub">{T('选择格式，一键导出当前数据', 'Choose format, one-click export current data')}</div>
    </div>
    """, unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            label=f"📊 {T('下载 CSV 格式', 'Download CSV')}",
            data=csv_data,
            file_name=f"{safe_name}_{T('数据报告','Report')}_{timestamp}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            label=f"📄 {T('下载 文本格式', 'Download Text')}",
            data=txt_data,
            file_name=f"{safe_name}_{T('数据报告','Report')}_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── 预览区域 ──
    st.divider()
    with st.expander(T("👁️ 预览导出内容", "👁️ Preview Export Content"), expanded=False):
        preview_tab1, preview_tab2 = st.tabs(["CSV", T("文本", "Text")])
        with preview_tab1:
            st.code(csv_data[:3000] + ("\n..." if len(csv_data) > 3000 else ""), language="csv")
        with preview_tab2:
            st.code(txt_data[:3000] + ("\n..." if len(txt_data) > 3000 else ""), language="text")

st.markdown(
    f"<div style='margin-top:36px;padding-top:16px;border-top:1px solid rgba(255,255,255,.06);"
    f"display:flex;justify-content:space-between;color:var(--rs-muted);font:600 10px Geist;'>"
    f"<span>RetailSense {VERSION}</span><span>{T('虚拟数据 · 本地规则引擎', 'Virtual data · Local rule engine')}</span></div>",
    unsafe_allow_html=True,
)
