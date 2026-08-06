"""
RetailSense v2.4 — AI 零售选品与库存决策系统
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from retail_sense.scorer import ProductScorer
from retail_sense.pricing import CostBreakdown, PricingModel
from retail_sense.inventory import InventoryStatus
from retail_sense.copywriter import CopyGenerator
from retail_sense.intent import IntentEngine
from retail_sense.sales_script import SalesScriptGenerator
from retail_sense.dataloader import *
from retail_sense.dataloader import get_demo_transactions, get_demo_inventory
from retail_sense.regions import *
from retail_sense.agent import VirtualAgent, AgentResponse
from retail_sense.agents import SalesPipeline
from retail_sense.cases import get_cases
from retail_sense.product_images import get_img, get_all_product_keys, get_product_display_name
from retail_sense.auth import init_session, is_logged_in, do_login, do_logout, current_user, current_role, is_admin, require_admin, require_user, register_user, load_platform_config, save_platform_config
from retail_sense.logistics import (
    get_mock_orders, get_warehouse_inventory, allocate_order,
    get_logistics_tracking, generate_waybill_no, simulate_delivery_tracking,
    get_courier_info, DELIVERY_PIPELINE, COURIER_PREFIXES, COURIER_NAMES,
)
from retail_sense.data_persistence import (
    load_allocation_log, save_allocation_log,
    load_listing_log, save_listing_log,
)

st.set_page_config(page_title="RetailSense", page_icon="🐾", layout="wide")

# ── 必须最前：初始化状态 ──
if "font_size" not in st.session_state: st.session_state.font_size = "13px"
if "lang" not in st.session_state: st.session_state.lang = "zh"

# ── 宠物温馨风 CSS ──
fs = int(st.session_state.font_size.replace("px",""))
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
</style>
""", unsafe_allow_html=True)

# ── 登录系统 ──
init_session()

if not is_logged_in():
    # 登录/注册页面 CSS
    st.markdown(f"""
    <style>
    .login-container {{
        max-width: 440px;
        margin: 0 auto;
        padding: 40px 24px;
        text-align: center;
    }}
    .login-header {{
        font-size: 30px;
        font-weight: 700;
        color: #FF8C42;
        margin-bottom: 2px;
    }}
    .login-sub {{
        font-size: 13px;
        color: #888;
        margin-bottom: 28px;
    }}
    .login-mascot {{
        font-size: 56px;
        margin-bottom: 8px;
    }}
    .login-footer-text {{
        font-size: 11px;
        color: #aaa;
        margin-top: 28px;
        line-height: 1.6;
    }}
    </style>
    """, unsafe_allow_html=True)

    # 在登录页中定义 T / is_en（此时 lang 已初始化）
    _is_en = st.session_state.lang == "en"
    _T = lambda cn, en: en if _is_en else cn

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # 萌宠图标
        st.markdown('<div class="login-mascot">🐾</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="login-header">RetailSense</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="login-sub">{_T("AI 零售选品与库存决策系统", "AI Retail Selection & Inventory")}</div>',
            unsafe_allow_html=True,
        )

        # 语言切换
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

        st.markdown("---")

        # ── 登录 / 注册 Tab ──
        tab_login, tab_register = st.tabs([_T("🔑 登录", "🔑 Login"), _T("📝 注册", "📝 Register")])

        with tab_login:
            login_user = st.text_input(
                _T("用户名", "Username"),
                key="login_user_field",
                placeholder="admin",
                label_visibility="visible",
            )
            login_pass = st.text_input(
                _T("密码", "Password"),
                type="password",
                key="login_pass_field",
                placeholder="••••••••",
                label_visibility="visible",
            )
            col_btn1, col_btn2 = st.columns([1.2, 1])
            with col_btn1:
                if st.button(_T("🐾 登录", "🐾 Login"), type="primary", use_container_width=True, key="btn_login_main"):
                    if not login_user or not login_pass:
                        st.warning(_T("请输入用户名和密码", "Please enter username and password"))
                    else:
                        ok, msg = do_login(login_user, login_pass)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_register:
            reg_user = st.text_input(
                _T("设置用户名", "Choose Username"),
                key="reg_user_field",
                placeholder=_T("至少2个字符", "Min 2 characters"),
            )
            reg_pass = st.text_input(
                _T("设置密码", "Choose Password"),
                type="password",
                key="reg_pass_field",
                placeholder=_T("至少6位", "Min 6 characters"),
            )
            reg_pass2 = st.text_input(
                _T("确认密码", "Confirm Password"),
                type="password",
                key="reg_pass2_field",
                placeholder=_T("再次输入密码", "Retype password"),
            )
            col_btn1, col_btn2 = st.columns([1.2, 1])
            with col_btn1:
                if st.button(_T("📝 注册", "📝 Register"), type="primary", use_container_width=True, key="btn_register_main"):
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
            f'{_T("RetailSense v2.4 · 宠物温馨风 · 管理员可通过系统预设账号登录", "RetailSense v2.4 · Pet-friendly · Admin login via system preset")}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
DEFAULT_IMAGES = {"banner":os.path.join(IMAGE_DIR,"banner.jpg"),"sidebar":os.path.join(IMAGE_DIR,"sidebar.jpg"),"footer":os.path.join(IMAGE_DIR,"footer.jpg")}
def load_image(key):
    path = st.session_state.get(f"img_{key}", DEFAULT_IMAGES[key])
    if os.path.exists(path): return path
    if path.startswith("http"): return path
    return DEFAULT_IMAGES[key]

for key in DEFAULT_IMAGES:
    if f"img_{key}" not in st.session_state: st.session_state[f"img_{key}"] = DEFAULT_IMAGES[key]

if "nav" not in st.session_state: st.session_state.nav = "工作台"
if "use_company" not in st.session_state: st.session_state.use_company = True
if "company_file" not in st.session_state: st.session_state.company_file = "萌爪宠物用品.json"
if "agent_msg" not in st.session_state: st.session_state.agent_msg = []
if "first_visit" not in st.session_state: st.session_state.first_visit = True

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

VERSION = "v2.4"
CHANGELOG = """
**v2.4 (2026-08-06)** 🤖 管家v3.0：真实数据查询+操作建议+思考过程
**v2.3 (2026-08-04)** 🆕 卡片库存+搜索置顶+真实平台+产品图
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
    # 🐾 当前用户信息
    user = current_user()
    role = current_role()
    role_badge = "🛡️" if role == "admin" else "👤"
    role_label = "管理员" if role == "admin" else ("普通用户" if role == "user" else "")
    role_label_en = "Admin" if role == "admin" else ("User" if role == "user" else "")

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;
         background:linear-gradient(135deg,#FFF8F0,#FFE8D6);border-radius:8px;
         margin-bottom:6px;border:1px solid #f0dcc8;">
        <span style="font-size:22px;">🐾</span>
        <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:13px;color:#5a4a3a;
                 overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{user}</div>
            <div style="font-size:10px;color:#FF8C42;font-weight:500;">
                {role_badge} {role_label_en if is_en else role_label}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 退出按钮
    if st.button(T("🚪 退出登录", "🚪 Logout"), use_container_width=True, key="sidebar_logout"):
        do_logout()
        st.rerun()

    st.divider()
    st.image(load_image("sidebar"), width='stretch')
    for name in ["工作台","案例库","选品评分","定价模型","销售自动化","库存监控","商品上架","物流配发","导出报表"]:
        kind = "primary" if st.session_state.nav == name else "secondary"
        if st.button(name, width='stretch', type=kind):
            st.session_state.nav = name; st.rerun()
    st.divider()
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
                os.makedirs(image_dir, exist_ok=True)

                for key in get_all_product_keys():
                    display_name = get_product_display_name(key)
                    filepath = os.path.join(image_dir, f"{key}.jpg")

                    c_img, c_upload = st.columns([0.8, 3])
                    with c_img:
                        b64 = get_img(key)
                        if b64:
                            st.markdown(
                                f'<img src="data:image/jpeg;base64,{b64}" '
                                f'style="width:48px;height:48px;border-radius:4px;object-fit:cover;">',
                                unsafe_allow_html=True,
                            )
                    with c_upload:
                        has_custom = os.path.isfile(filepath)
                        status_badge = "🟢 " + T("已自定义", "Custom") if has_custom else "⚪ " + T("默认图", "Default")
                        st.caption(f"**{display_name}** — {status_badge}")
                        uploaded = st.file_uploader(
                            T(f"替换 {display_name}", f"Replace {display_name}"),
                            type=["jpg", "jpeg", "png", "webp"],
                            key=f"img_upload_{key}",
                            label_visibility="collapsed",
                        )
                        if uploaded is not None:
                            with open(filepath, "wb") as f:
                                f.write(uploaded.getbuffer())
                            st.success(T(f"✅ {display_name} 已更新！", f"✅ {display_name} updated!"))
                            st.rerun()

                        # Reset button to remove custom image
                        if has_custom:
                            if st.button(T("恢复默认", "Reset"), key=f"img_reset_{key}"):
                                if os.path.isfile(filepath):
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
    st.caption(f"{VERSION} · MIT")

page = st.session_state.nav
agent = VirtualAgent()
# 设置管家上下文
if company:
    agent.context["company"] = company.get("company", "") if st.session_state.lang == "zh" else company.get("company_en", "")

# ══ 工作台 ══
if page == "工作台":
    if st.session_state.first_visit:
        with st.container(border=True):
            st.markdown(T("### 🐾 欢迎使用 RetailSense！\n**三步开始：**\n1. 📈 选品评分 → 2. 🤖 销售自动化 → 3. 📖 案例库","### 🐾 Welcome!\n**Steps:** 1. Scoring → 2. Pipeline → 3. Cases"))
            if st.button(T("开始使用","Get Started"), type="primary"): st.session_state.first_visit = False; st.rerun()

    # 顶部搜索（管家助手）
    with st.container(border=True):
        st.markdown(T(
            "### 🤖 管家助手 (v3.0) / Assistant (v3.0)",
            "### 🤖 Assistant (v3.0)"
        ))
        col_q, col_btn = st.columns([5, 1])
        with col_q:
            msg = st.text_input(
                T("💬 向我提问（查库存/营收/利润/补货建议...）",
                  "💬 Ask me anything (stock/revenue/profit/restock...)"),
                key="agent_input_top",
                placeholder=T(
                    "如：刻字狗牌库存多少 | 本周利润最高产品 | 哪些库存低了 | 建议补货",
                    "e.g. LED collar stock | most profitable product | low stock alert | restock advice"
                ),
                label_visibility="collapsed",
            )
        if msg:
            with st.spinner(T("🤔 管家思考中...", "🤔 Analyzing...")):
                resp = agent.process(
                    msg,
                    company_data=company,
                    transactions=txns,
                    inventory=inv,
                    lang=st.session_state.lang,
                )
            # 存储为结构化数据
            st.session_state.agent_msg.append(("user", msg))
            st.session_state.agent_msg.append(("agent_v3", resp))
        # 渲染消息历史
        for entry in st.session_state.agent_msg[-6:]:
            role = entry[0]
            if role == "user":
                with st.chat_message("user"):
                    st.write(entry[1])
            elif role == "agent_v3":
                resp_obj = entry[1]
                with st.chat_message("assistant"):
                    # 思考过程（可折叠）
                    if hasattr(resp_obj, 'thinking') and resp_obj.thinking:
                        with st.expander(
                            T(f"🧠 思考过程（{len(resp_obj.thinking)}步）",
                              f"🧠 Thinking ({len(resp_obj.thinking)} steps)"),
                            expanded=False,
                        ):
                            for step in resp_obj.thinking:
                                st.caption(step)
                    # 主回答
                    if hasattr(resp_obj, 'answer'):
                        st.markdown(resp_obj.answer)
                    else:
                        st.write(str(resp_obj))
                    # 操作建议
                    if hasattr(resp_obj, 'suggestions') and resp_obj.suggestions:
                        with st.expander(
                            T("💡 操作建议", "💡 Suggestions"),
                            expanded=True,
                        ):
                            for s in resp_obj.suggestions:
                                st.info(s)
            elif role == "agent":
                # 兼容旧版纯文本响应
                with st.chat_message("assistant"):
                    st.write(entry[1])

    st.title("RetailSense")
    st.caption(T("AI 零售选品 · 定价 · 库存 · 出入库仪表盘","AI Retail · Pricing · Inventory · Dashboard"))

    if st.session_state.use_company and company:
        st.success(T(f"已接入：{company['company']}","Connected: "+company['company_en']))
    elif txns and inv:
        st.info(T("手动模式 — 使用示例数据","Manual mode — Demo data"))
    else:
        st.info(T("手动模式 — 暂无数据","Manual mode — No data"))

    today = daily_summary(txns, 1) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    week = daily_summary(txns, 7) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    month = daily_summary(txns, 30) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    inv_summary = inventory_value_summary(inv) if inv else {"total_qty":0,"total_value":0,"skus":0,"low_stock":0,"out_of_stock":0,"total_retail":0}

    c = st.columns(4)
    c[0].metric(T("今日营收","Today"), f"¥{today['revenue']:,.0f}", f"{today['orders']}{T('单',' orders')}")
    c[1].metric(T("本周营收","Week"), f"¥{week['revenue']:,.0f}")
    c[2].metric(T("本月营收","Month"), f"¥{month['revenue']:,.0f}")
    c[3].metric(T("库存价值","Inventory"), f"¥{inv_summary['total_retail']:,.0f}", f"{inv_summary['skus']} SKU")

    # 库存卡片悬停（替代柱状图）
    st.divider()
    st.subheader(T("库存状态","Inventory Status"))
    cards = st.columns(3)
    normal_count = inv_summary['skus'] - inv_summary['low_stock'] - inv_summary['out_of_stock']
    card_data = [
        (T("正常","Normal"), normal_count, "ok", "#34a853"),
        (T("低库存","Low Stock"), inv_summary['low_stock'], "warn", "#f4b400"),
        (T("断货","Out of Stock"), inv_summary['out_of_stock'], "danger", "#ea4335"),
    ]
    for i, (label, count, css_class, color) in enumerate(card_data):
        with cards[i]:
            st.markdown(f"""
            <div class="card-hover {css_class}" style="min-height:80px;">
                <div style="font-size:26px;font-weight:800;color:{color};">{count}</div>
                <div style="font-size:12px;color:#888;margin-top:4px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # 出库趋势（轻量文字+最近3天）
    st.divider()
    st.subheader(T("近期出库","Recent Sales"))
    if txns:
        out_txns = [t for t in txns if t["type"]=="out"]
        recent = sorted(out_txns, key=lambda t: t["date"], reverse=True)[:5]
        out_cols = st.columns(len(recent) if recent else 1)
        for j, txn in enumerate(recent):
            with out_cols[j]:
                st.markdown(f"""<div class="card-hover ok" style="min-height:50px;text-align:center;">
                    <div style="font-size:11px;color:#888;">{txn['date']}</div>
                    <div style="font-size:18px;font-weight:700;color:#FF8C42;">¥{txn['revenue']:,.0f}</div>
                    <div style="font-size:10px;color:#aaa;">{txn.get('product','')}</div></div>""", unsafe_allow_html=True)
    else:
        st.caption(T("暂无数据","No data"))

# ══ 选品评分 ══
elif page == "选品评分":
    st.title(T("产品选品评分","Product Scoring"))

    with st.container(border=True):
        st.markdown(T("**目标市场**","**Target Market**"))
        if "sel_region" not in st.session_state: st.session_state.sel_region = "北美"
        regions_list = all_regions()
        cols = st.columns(len(regions_list))
        region_colors = {"北美":"#1a73e8","欧洲":"#4285f4","东南亚":"#f4b400","日韩":"#ea4335","澳洲":"#34a853"}
        for i, (col, rname) in enumerate(zip(cols, regions_list)):
            with col:
                rd = get_region(rname)
                is_sel = st.session_state.sel_region == rname
                border = f"2px solid {region_colors[rname]}" if is_sel else "1px solid #ddd"
                bg = f"{region_colors[rname]}15" if is_sel else "#fff"
                st.markdown(f"""<div style="border:{border};border-radius:4px;padding:8px;text-align:center;background:{bg};min-height:70px;">
                    <div style="font-weight:600;font-size:12px;">{rname}</div>
                    <div style="font-size:10px;color:#666;margin-top:2px;">{', '.join(rd['countries'][:3]) if rd else ''}</div>
                    <div style="font-size:9px;color:#888;margin-top:1px;">{rd['avg_margin'] if rd else ''}</div></div>""", unsafe_allow_html=True)
                if st.button(T("选择","Select")+rname, key=f"reg_{i}", width='stretch'):
                    st.session_state.sel_region = rname; st.rerun()

        region = st.session_state.sel_region
        rd = get_region(region)
        if rd:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(T(f"**主流平台：** {', '.join(rd['platforms'])}","**Platforms:** "+', '.join(rd['platforms'])))
            with c2:
                st.markdown(T(f"**竞争：** {rd['competition']} · **利润：** {rd['avg_margin']}","**Competition:** {rd['competition']} · **Margin:** {rd['avg_margin']}"))

        with st.expander(T("近期活动与上品建议","Events & Listing Guide"), expanded=True):
            for item in upcoming_events(region):
                if len(item) == 5:
                    m, e, desc, idx, tip = item
                    score = int(idx.replace(T("上品指数:","Listing Index:"),""))
                    color = "#34a853" if score>=90 else ("#f4b400" if score>=80 else "#ea4335")
                    st.markdown(f"""<div style="border-left:3px solid {color};padding:5px 10px;margin:4px 0;background:#fafafa;border-radius:2px;">
                        <span style="font-weight:600;font-size:12px;">{m} · {e}</span>
                        <span style="background:{color};color:white;padding:1px 5px;border-radius:2px;font-size:10px;margin-left:6px;">{idx}</span><br>
                        <span style="font-size:11px;color:#555;">{desc}</span><br>
                        <span style="font-size:11px;color:{color};">{tip}</span></div>""", unsafe_allow_html=True)

    with st.expander(T("评分方法论","Methodology"), expanded=False):
        st.markdown(T("**设计理念**：3年瑞幸200+SKU管理经验 → 真正吃掉利润的是滞销。\n| 维度 | 权重 |\n|------|:---:|\n| 复购 | 30% |\n| 竞争 | 25% |\n| 趋势 | 25% |\n| 毛利 | 20% |",
                      "**Design**: 3yr Luckin, 200+ SKUs → unsold inventory destroys profit.\n| Dim | Weight |\n|------|:---:|\n| Repur | 30% |\n| Comp | 25% |\n| Trend | 25% |\n| Margin | 20% |"))

    # ── 产品数据（admin 可编辑 / editable by admin）──
    if "products" not in st.session_state:
        st.session_state.products = [
            {"name":"刻字狗牌","name_en":"Engraved Dog Tag","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"dog-tag"},
            {"name":"发光项圈","name_en":"LED Collar","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"led-collar"},
            {"name":"珐琅名牌","name_en":"Enamel Nameplate","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"enamel-plate"},
            {"name":"牵引绳套装","name_en":"Leash Set","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"leash-set"},
            {"name":"宠物领结","name_en":"Pet Bow Tie","cost":1.50,"price":9.99,"competitors":55,"search_growth":-5,"trend_up":False,"annual_purchases":3,"is_consumable":True,"img":"bow-tie"},
            {"name":"亚克力牌","name_en":"Acrylic Tag","cost":1.20,"price":8.99,"competitors":22,"search_growth":18,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"acrylic-tag"},
            {"name":"宠物手链","name_en":"Pet Bracelet","cost":2.00,"price":14.99,"competitors":15,"search_growth":42,"trend_up":True,"annual_purchases":1,"is_consumable":False,"img":"bracelet"},
            {"name":"换牙零食","name_en":"Teething Treats","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8,"is_consumable":True,"img":"treats"},
        ]
    PRODUCTS = st.session_state.products

    scorer = ProductScorer()
    for i, p in enumerate(PRODUCTS):
        label = f"🐾 {pname(p)} — ¥{p['price']:.2f}"
        with st.expander(label):
            cimg, c1, c2, c3 = st.columns([0.8, 2, 2, 2])
            with cimg:
                b64 = get_img(p.get("img",""))
                if b64:
                    st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:70px;height:70px;border-radius:6px;object-fit:cover;">', unsafe_allow_html=True)
                else:
                    st.markdown("🐾")
            with c1:
                ps = scorer.evaluate(p)
                # 卡片式评分（替代柱状图）
                scores = [(T("毛利","M"),ps.margin_score,"#FF8C42"),(T("竞争","C"),ps.competition_score,"#4285f4"),(T("趋势","T"),ps.trend_score,"#34a853"),(T("复购","R"),ps.repurchase_score,"#9b59b6")]
                for lbl, val, clr in scores:
                    st.markdown(f"""<div style="display:flex;align-items:center;gap:6px;margin:2px 0;">
                        <span style="font-size:11px;width:24px;color:#888;">{lbl}</span>
                        <div style="flex:1;height:6px;background:#eee;border-radius:3px;"><div style="width:{val}%;height:6px;background:{clr};border-radius:3px;"></div></div>
                        <span style="font-size:11px;font-weight:600;">{val}</span></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(T("**区域推荐**","**Region Recs**"))
                for r in best_region_for_product(p): st.markdown(f"• {r}")
                style = st.selectbox(T("风格","Style"), ["seo","social","sales"], key=f"sty_{i}", label_visibility="collapsed")
                if st.button(T("生成文案","Copy"), key=f"gc_{i}"): st.markdown(CopyGenerator().generate(p, style))
            with c3:
                ie = IntentEngine()
                best = ie.best_angle(p)
                st.caption(f"**{best['angle']}**: {best['pitch']}")

        # ── 管理员产品编辑 / Admin Product Edit ──
        if is_admin():
            with st.expander(T("✏️ 编辑产品信息", "✏️ Edit Product"), expanded=False, key=f"edit_prod_{i}"):
                e_name = st.text_input(T("产品名称", "Product Name"), value=p.get("name",""), key=f"edit_name_{i}")
                e_name_en = st.text_input(T("英文名称", "English Name"), value=p.get("name_en",""), key=f"edit_name_en_{i}")
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_cost = st.number_input(T("成本 ¥", "Cost ¥"), value=float(p.get("cost",0)), step=0.10, format="%.2f", key=f"edit_cost_{i}")
                with ec2:
                    e_price = st.number_input(T("售价 ¥", "Price ¥"), value=float(p.get("price",0)), step=0.10, format="%.2f", key=f"edit_price_{i}")
                ec3, ec4 = st.columns(2)
                with ec3:
                    e_comp = st.number_input(T("竞品数", "Competitors"), value=int(p.get("competitors",0)), step=1, key=f"edit_comp_{i}")
                with ec4:
                    e_growth = st.number_input(T("搜索增长 %", "Search Growth %"), value=int(p.get("search_growth",0)), step=1, key=f"edit_growth_{i}")
                e_annual = st.number_input(T("年均复购次数", "Annual Purchases"), value=int(p.get("annual_purchases",1)), step=1, min_value=1, key=f"edit_annual_{i}")
                e_consumable = st.checkbox(T("消耗品", "Consumable"), value=p.get("is_consumable",False), key=f"edit_consumable_{i}")
                if st.button(T("💾 保存修改", "💾 Save Changes"), type="primary", key=f"save_prod_{i}"):
                    st.session_state.products[i]["name"] = e_name
                    st.session_state.products[i]["name_en"] = e_name_en
                    st.session_state.products[i]["cost"] = e_cost
                    st.session_state.products[i]["price"] = e_price
                    st.session_state.products[i]["competitors"] = e_comp
                    st.session_state.products[i]["search_growth"] = e_growth
                    st.session_state.products[i]["annual_purchases"] = e_annual
                    st.session_state.products[i]["is_consumable"] = e_consumable
                    st.success(T("✅ 产品信息已更新！", "✅ Product updated!"))
                    st.rerun()

    if st.button(T("批量评分排名","Batch Ranking"), type="primary"):
        results = scorer.rank(PRODUCTS)
        rows = []
        for r in results:
            rows.append({T("产品","Product"):r.product_name,T("评分","Score"):f"{r.final_score:.0f}",
                         T("毛利","M"):r.margin_score,T("竞争","C"):r.competition_score,
                         T("趋势","T"):r.trend_score,T("复购","R"):r.repurchase_score})
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

# ══ 定价模型 ══
elif page == "定价模型":
    st.title(T("定价模型","Pricing Model"))
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            raw = st.number_input(T("裸件成本","Raw Material"), value=2.80, step=0.10, format="%.2f")
            proc = st.number_input(T("加工费","Processing"), value=1.20, step=0.10, format="%.2f")
        with c2:
            pack = st.number_input(T("包装费","Packaging"), value=0.50, step=0.10, format="%.2f")
            ship = st.number_input(T("物流费","Shipping"), value=1.50, step=0.10, format="%.2f")
        with c3:
            plat = st.number_input(T("平台费","Platform Fee"), value=0.85, step=0.10, format="%.2f")
            target = st.slider(T("目标利润率","Target Margin"), 20, 70, 45, 5, format="%d%%")

        st.divider()
        cc1, cc2 = st.columns(2)
        with cc1:
            # 汇率：以 ¥1 为基准
            RATES = {"¥ CNY":1.0,"$ USD":0.14,"€ EUR":0.13,"£ GBP":0.11,"¥ JPY":16.0,"A$ AUD":0.21,"C$ CAD":0.19}
            currency = st.selectbox(T("货币单位","Currency"),
                                   list(RATES.keys()),
                                   index=1 if is_en else 0)
            symbol = currency.split()[0]
            rate = RATES[currency]
        with cc2:
            if rate != 1.0:
                st.caption(T(f"汇率 1{chr(165)}={rate:.2f}{symbol}",f"Rate 1{chr(165)}={rate:.2f}{symbol}"))
            else:
                st.caption(T("基准货币 ¥ CNY","Base currency ¥ CNY"))

    if st.button(T("计算定价","Calculate"), type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target/100)

        def c(val): return round(val * rate, 2)

        items = [(T("裸件","Raw"),c(raw)),(T("加工","Proc"),c(proc)),(T("包装","Pack"),c(pack)),(T("物流","Ship"),c(ship)),(T("平台","Plat"),c(plat))]
        cc = st.columns(5)
        for i, (lbl, val) in enumerate(items):
            with cc[i]:
                st.markdown(f"""<div class="card-hover" style="min-height:50px;">
                    <div style="font-size:16px;font-weight:700;color:#FF8C42;">{symbol}{val:.2f}</div>
                    <div style="font-size:10px;color:#888;">{lbl}</div></div>""", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(T("总成本","Total Cost"), f"{symbol}{c(result['total_cost']):.2f}")
        m2.metric(T("建议售价","Price"), f"{symbol}{c(result['suggested_price']):.2f}")
        m3.metric(T("利润","Profit"), f"{symbol}{c(result['profit']):.2f}")
        m4.metric(T("利润率","Margin"), f"{result['margin_rate']:.1%}",
                 delta=T("达标","OK") if result['above_redline'] else T("未达标","Low"),
                 delta_color="normal" if result['above_redline'] else "inverse")

# ══ 库存监控 ══
elif page == "库存监控":
    st.title(T("库存监控","Inventory Monitor"))
    if st.session_state.use_company and company:
        st.success(T(f"数据源：{company['company']}","Source: "+company['company_en']))
    else:
        st.info(T("手动模式 — 使用示例数据","Manual mode — Demo data"))

    # 复用全局已加载的库存数据（公司真实数据或示例数据）
    # inv is already set at module level from company data or demo fallback

    rows = []
    for i in inv:
        qty = int(i.get("qty", 0))
        daily = int(i.get("daily_avg", 1))
        lead = i.get("lead_days", 3)
        safety = max(1, round(daily * 7))
        reorder_qty = max(round(daily), safety + round(daily * lead) - qty) if qty < safety else 0
        status_cn = "断货" if qty == 0 else ("低库存" if qty < safety else "正常")
        status_en = "OOS" if qty == 0 else ("Low" if qty < safety else "Normal")
        status_color = "#ea4335" if qty == 0 else ("#f4b400" if qty < safety else "#34a853")

        rows.append({
            T("产品","Product"): pname(i),
            "SKU": i.get("sku",""),
            T("库存","Qty"): qty,
            T("日均","Daily"): daily,
            T("安全库存","Safety"): safety,
            T("补货","Reorder"): reorder_qty,
            T("状态","Status"): status_en if is_en else status_cn,
        })

    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    # 库存卡片（替代柱状图）
    st.divider()
    st.subheader(T("库存概览","Overview"))
    inv_cards = st.columns(min(len(inv), 5))
    for idx, item in enumerate(inv[:5]):
        with inv_cards[idx]:
            qty = item.get("qty",0)
            status = "ok" if qty>20 else ("warn" if qty>0 else "danger")
            b64 = get_img(item.get("img",""))
            if b64:
                st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:50px;height:50px;border-radius:4px;object-fit:cover;margin-bottom:4px;">', unsafe_allow_html=True)
            st.markdown(f"""<div class="card-hover {status}" style="min-height:50px;">
                <div style="font-size:22px;font-weight:800;">{qty}</div>
                <div style="font-size:11px;color:#888;">{pname(item)}</div></div>""", unsafe_allow_html=True)

# ══ 案例库 ══
elif page == "案例库":
    st.title(T("案例库","Case Studies"))
    st.caption(T("真实商家如何用 RetailSense 降本增效","How real businesses save with RetailSense"))
    cases = get_cases()
    for i, case in enumerate(cases):
        with st.container(border=True):
            c1, c2 = st.columns([2,1])
            with c1:
                st.markdown(f"### {case['company']}")
                st.caption(f"{case['industry']} · {case['region']} · {T('环节：'+case['stage'],'Stage: '+case['stage'])}")
                with st.expander(T("痛点","Problem"), expanded=(i==0)):
                    st.markdown(f"**{T('使用前','Before')}:** {case['problem']}\n\n**{T('解决方案','Solution')}:** {case['solution']}")
                with st.expander(T("效果对比","Results")):
                    b = case['before']; a = case['after']
                    mc = st.columns(4)
                    mc[0].metric(T("耗时","Time"), a['time'], delta=f"↓ {b['time']}", delta_color="inverse")
                    mc[1].metric(T("成本","Cost"), a['cost'], delta=f"↓ {b['cost']}", delta_color="normal")
                    mc[2].metric(T("人力","People"), a['people'], delta=f"↓ {b['people']}", delta_color="inverse")
                    mc[3].metric(T("错误率","Errors"), a['error'], delta=f"↓ {b['error']}", delta_color="normal")
                st.markdown(f"> *{case['testimonial']}*")
            with c2:
                st.markdown(T("**使用产品**","**Products**"))
                for p in case['products_used']: st.markdown(f"• {p}")
                st.divider()
                st.markdown(T("**适用功能**","**Features**"))
                st.markdown(T(f"• {case['stage']}",f"• {case['stage']}"))

# ══ 销售自动化 ══
elif page == "销售自动化":
    st.title(T("多智能体销售自动化","Multi-Agent Sales Pipeline"))
    st.caption(T("Scout选品→Price定价→Copy文案→Monitor监控","Scout→Price→Copy→Monitor Pipeline"))

    with st.expander(T("操作指引","How it works"), expanded=False):
        st.markdown(T("1. Scout选品 → 2. Price定价 → 3. Copy文案 → 4. Monitor监控\n调整利润率→选市场→启动全流程","1. Scout → 2. Price → 3. Copy → 4. Monitor\nAdjust margin→Pick market→Start pipeline"))

    PRODUCTS_A = [
        {"name":"刻字狗牌","name_en":"Engraved Dog Tag","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2,"is_consumable":False,"qty":45,"daily_avg":9,"img":"dog-tag"},
        {"name":"发光项圈","name_en":"LED Collar","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":2,"is_consumable":False,"qty":12,"daily_avg":6,"img":"led-collar"},
        {"name":"珐琅名牌","name_en":"Enamel Nameplate","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2,"is_consumable":False,"qty":120,"daily_avg":3,"img":"enamel-plate"},
        {"name":"牵引绳套装","name_en":"Leash Set","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":2,"is_consumable":False,"qty":0,"daily_avg":4,"img":"leash-set"},
        {"name":"换牙零食","name_en":"Teething Treats","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8,"is_consumable":True,"qty":8,"daily_avg":15,"img":"treats"},
    ]

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            target_pct = st.slider(T("目标利润率","Target Margin"), 25, 60, 45, 5, format="%d%%")
        with c2:
            region = st.selectbox(T("目标市场","Target Market"), ["北美","欧洲","东南亚","日韩","澳洲"])
        st.caption(T(f"{len(PRODUCTS_A)}SKU | 利润目标{target_pct}%",f"{len(PRODUCTS_A)} SKUs | {target_pct}% target"))

    st.markdown(T("**流水线**","**Pipeline**"))
    steps = st.columns(4)
    for i, (icon, lcn, len_, hcn, hen) in enumerate([
        ("🔍","选品侦察","Scout","评分排序","Scoring"),
        ("💰","智能定价","Price","成本+利润","Cost+sim"),
        ("✍️","文案生成","Copy","SEO+社交","SEO+sales"),
        ("📊","库存监控","Monitor","巡检+趋势","Alert+trend"),
    ]):
        with steps[i]:
            st.markdown(f"""<div style="border:1px solid #e0e0e0;border-radius:4px;padding:8px;text-align:center;min-height:75px;">
                <div style="font-size:16px;">{icon}</div><div style="font-weight:600;font-size:11px;">{T(lcn,len_)}</div>
                <div style="font-size:10px;color:#888;">{T(hcn,hen)}</div>
                <span style="background:#e8f5e9;color:#2e7d32;padding:1px 6px;border-radius:2px;font-size:9px;">{T('Agent','Agent')}</span></div>""", unsafe_allow_html=True)

    with st.expander(T("Agent 架构","Agent Architecture"), expanded=False):
        st.caption(T("Scout→Price→Copy→Monitor 四Agent串联 | 当前: 规则引擎 | 完整模式: LLM API",
                     "Scout→Price→Copy→Monitor | Current: rule engine | Full: LLM API"))

    if st.button(T("启动全流程","Start Pipeline"), type="primary", width='stretch'):
        pipeline = SalesPipeline()
        with st.spinner(T("执行中...","Running...")):
            state = pipeline.run(PRODUCTS_A, target_pct/100, region)
        st.success(T("完成！","Complete!"))
        t1,t2,t3,t4 = st.tabs([T("评分","Scoring"),T("定价","Pricing"),T("文案","Copy"),T("监控","Monitor")])
        with t1:
            if state.scored:
                sd = pd.DataFrame([{T("产品","Product"):r.product_name,T("评分","Score"):f"{r.final_score:.0f}",
                                    T("毛利","Margin"):r.margin_score,T("竞争","Comp"):r.competition_score,
                                    T("趋势","Trend"):r.trend_score,T("复购","Repur"):r.repurchase_score} for r in state.scored])
                st.dataframe(sd, width='stretch', hide_index=True)
        with t2:
            if state.priced:
                pd_data = pd.DataFrame(state.priced)
                pd_data_display = pd_data.rename(columns={"name":T("产品","Product"),"suggested_price":T("售价","Price"),
                    "profit":T("利润","Profit"),"margin":T("利润率","Margin"),"above_redline":T("达标","Pass")})
                st.dataframe(pd_data_display, width='stretch', hide_index=True)
                ok = sum(1 for p in state.priced if p["above_redline"])
                st.metric(T("达标率","Pass"), f"{ok}/{len(state.priced)}",
                         delta=T("全部达标" if ok==len(state.priced) else f"{len(state.priced)-ok}个未达标","All" if ok==len(state.priced) else f"{len(state.priced)-ok} below"))
        with t3:
            if state.copy:
                for c in state.copy:
                    with st.expander(f"📝 {c['name']}"):
                        st.markdown(f"**SEO 文案**\n{c['seo']}")
                        st.divider()
                        st.markdown(f"**{T('社交种草','Social')}**\n{c['social']}")
                        st.divider()
                        st.markdown(f"**{T('销售转化','Sales Script')}**\n{c['script'].get('开场','')}")
        with t4:
            if state.monitor:
                for m in state.monitor:
                    with st.container(border=True):
                        has_urgent = any("断货" in i for i in m["issues"])
                        (st.error if has_urgent else st.warning)(f"**{m['name']}**: {'; '.join(m['issues'])}")
            else:
                st.success(T("所有产品正常","All products normal"))

# ══ 物流配发 ══
elif page == "物流配发":
    if not require_user():
        st.stop()

    st.title(T("物流配发","Logistics & Fulfillment"))
    st.caption(T("订单看板 · 智能配货 · 虚拟快递追踪","Order Board · Smart Allocation · Virtual Delivery Tracking"))

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
    if st.session_state.logistics_page > total_pages:
        st.session_state.logistics_page = total_pages
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
                if oid in st.session_state.alloc_results and oid in st.session_state.logistics_expanded:
                    if st.session_state.alloc_results[oid]["all_ok"]:
                        if st.button(T("✅ 确认发货","✅ Confirm Ship"), key=f"confirm_ship_{oid}", type="primary"):
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
    if not require_user():
        st.stop()

    st.title(T("商品上架","Product Listing"))
    st.caption(T("选品 → 一键上架到 Shopify / Etsy / 独立站","Select → List to Shopify / Etsy / Custom Store"))

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
                b64 = get_img(p.get("img", ""))
                status = p["listing_status"]
                is_pending = status == "待上架"
                border = "2px solid #FF8C42" if i == selected_product_idx else ("1px solid #e0d5cc" if is_pending else "1px solid #34a853")
                bg = "#FFF8F0" if i == selected_product_idx else ("#fff" if is_pending else "#f0faf0")

                status_badge_cn = "🟡 待上架" if is_pending else "🟢 已上架"
                status_badge_en = "🟡 Pending" if is_pending else "🟢 Listed"

                card_html = f'''<div style="border:{border};border-radius:8px;padding:10px;text-align:center;background:{bg};min-height:170px;">
                    <span style="font-size:10px;font-weight:600;">{status_badge_en if is_en else status_badge_cn}</span><br>'''
                if b64:
                    card_html += f'<img src="data:image/jpeg;base64,{b64}" style="width:64px;height:64px;border-radius:6px;object-fit:cover;margin:4px 0;"><br>'
                else:
                    card_html += '<span style="font-size:28px;">🐾</span><br>'
                card_html += f'''<div style="font-weight:600;font-size:12px;">{pname(p)}</div>
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
            b64 = get_img(selected.get("img", ""))
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
                border_p = "2px solid #FF8C42" if is_sel_plat else "1px solid #e0d5cc"
                bg_p = "#FFF8F0" if is_sel_plat else "#fff"
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
            st.markdown(T("### 🚀 确认上架", "### 🚀 Confirm Listing"))

            st.markdown(T(
                f"即将将 **{pname(selected)}** 上架到 **{listing['platform_icon']} {listing['platform_name']}**",
                f"About to list **{pname(selected)}** on **{listing['platform_icon']} {listing['platform_name']}**"
            ))

            st.caption(T(
                f"上架链接预览: [{listing['listing_url']}]({listing['listing_url']})",
                f"Listing URL preview: [{listing['listing_url']}]({listing['listing_url']})"
            ))

            if st.button(T("🚀 一键上架", "🚀 List Now"), type="primary", width="stretch", key="do_listing"):
                with st.spinner(T("正在上架到平台...", "Publishing to platform...")):
                    import time
                    time.sleep(1.5)

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
                    f"✅ **{pname(selected)}** 已成功上架到 **{listing['platform_name']}**！",
                    f"✅ **{pname(selected)}** successfully listed on **{listing['platform_name']}**!"
                ))
                st.balloons()
                st.info(T(
                    f"🔗 商品链接: [{listing['listing_url']}]({listing['listing_url']})\n\n📅 上架时间: {record['listed_at']}\n👤 操作人: {record['listed_by']}",
                    f"🔗 Product URL: [{listing['listing_url']}]({listing['listing_url']})\n\n📅 Listed at: {record['listed_at']}\n👤 By: {record['listed_by']}"
                ))
                time.sleep(2)
                st.rerun()
        else:
            st.info(T(
                f"✅ **{pname(selected)}** 已经上架，如需重新上架到其他平台请先在「上架记录」中删除后重试。",
                f"✅ **{pname(selected)}** is already listed. Delete from 'Listing History' to re-list on another platform."
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
                        st.markdown(T(f"平台","Platform"))
                        st.caption(r["platform_name"])
                    with rc[3]:
                        st.markdown(T(f"售价","Price"))
                        st.caption(f"¥{r['price']:.2f}")
                    with rc[4]:
                        st.markdown(T(f"库存","Stock"))
                        st.caption(str(int(r.get("stock", 0))))
                    with rc[5]:
                        st.markdown(T(f"时间","Time"))
                        st.caption(r["listed_at"])

                    with st.expander(T(f"📄 查看 Listing — {r['title'][:40]}...", f"📄 View Listing — {r['title'][:40]}..."), expanded=False):
                        st.markdown(f"**{T('标题','Title')}:** {r['title']}")
                        st.markdown(f"**{T('链接','URL')}:** [{r['listing_url']}]({r['listing_url']})")
                        st.caption(f"**SEO Tags:** {r.get('seo_tags','')}")
                        st.caption(T(
                            f"上架人: {r.get('listed_by','')} · 状态: {'✅ 成功' if r.get('status') == 'success' else '❌ 失败'}",
                            f"Listed by: {r.get('listed_by','')} · Status: {'✅ Success' if r.get('status') == 'success' else '❌ Failed'}"
                        ))

                    if st.button(T("🗑️ 删除此记录", "🗑️ Delete Record"), key=f"del_listing_{i}"):
                        product_name = r.get("product", "")
                        if product_name in st.session_state.listing_product_status:
                            del st.session_state.listing_product_status[product_name]
                        st.session_state.listing_records.pop(i)
                        _persist_listing()
                        st.rerun()

# ══ 导出报表 ══
elif page == "导出报表":
    st.title(T("导出报表", "Export Report"))
    st.caption(T(
        "一键下载公司数据报告（营收 / 库存 / 产品列表）",
        "One-click download company data report (Revenue / Inventory / Product List)"
    ))

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
    today_data = daily_summary(txns, 1) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    week_data = daily_summary(txns, 7) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    month_data = daily_summary(txns, 30) if txns else {"revenue": 0, "orders": 0, "profit": 0, "cost": 0}
    inv_sum = inventory_value_summary(inv) if inv else {
        "total_qty": 0, "total_value": 0, "total_retail": 0,
        "skus": 0, "low_stock": 0, "out_of_stock": 0,
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
    import csv, io

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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = co_name.replace(" ", "_").replace("（", "").replace("）", "")

    if export_mode.startswith("📊") or export_mode.startswith("📦"):
        # 写产品列表
        csv_writer.writerow([
            T("公司", "Company"), T("产品", "Product"), "SKU",
            T("库存", "Qty"), T("成本", "Cost"), T("售价", "Price"),
            T("日均销量", "Daily Avg"), T("安全库存", "Safety"), T("状态", "Status"),
        ])
        source = inv if inv else default_prods
        for i in source:
            qty = int(i.get("qty", 0))
            daily = int(i.get("daily_avg", 1))
            safety = max(1, round(daily * 7))
            status_val = "OOS" if qty == 0 else ("Low" if qty < safety else "Normal")
            csv_writer.writerow([
                co_name,
                pname(i),
                i.get("sku", ""),
                qty,
                i.get("cost", 0),
                i.get("price", 0),
                daily,
                safety,
                status_val,
            ])

    if export_mode.startswith("📊") or export_mode.startswith("💰"):
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
        daily = int(i.get("daily_avg", 1))
        safety = max(1, round(daily * 7))
        status_val = "OOS" if qty == 0 else ("Low" if qty < safety else "Normal")
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

st.divider()
st.image(load_image("footer"), width='stretch')