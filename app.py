"""
RetailSense v2.3 — AI 零售选品与库存决策系统
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
from retail_sense.regions import *
from retail_sense.agent import VirtualAgent
from retail_sense.agents import SalesPipeline
from retail_sense.cases import get_cases
from retail_sense.product_images import get_img

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

IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
PRODUCT_IMG_DIR = os.path.join(IMAGE_DIR, "products")
DEFAULT_IMAGES = {"banner":os.path.join(IMAGE_DIR,"banner.jpg"),"sidebar":os.path.join(IMAGE_DIR,"sidebar.jpg"),"footer":os.path.join(IMAGE_DIR,"footer.jpg")}
def load_image(key):
    path = st.session_state.get(f"img_{key}", DEFAULT_IMAGES[key])
    if os.path.exists(path): return path
    if path.startswith("http"): return path
    return DEFAULT_IMAGES[key]
def product_img(name):
    """获取产品图片"""
    mapping = {"刻字狗牌":"dog-tag","发光项圈":"led-collar","珐琅名牌":"enamel-plate","牵引绳套装":"leash-set","宠物领结":"bow-tie","亚克力牌":"acrylic-tag","宠物手链":"bracelet","换牙零食":"treats"}
    fname = mapping.get(name, "")
    path = os.path.join(PRODUCT_IMG_DIR, f"{fname}.jpg")
    return f'<img src="/app/static/{fname}.jpg" style="width:80px;height:80px;border-radius:6px;object-fit:cover;border:1px solid #eee;">' if os.path.exists(path) else "🐾"

for key in DEFAULT_IMAGES:
    if f"img_{key}" not in st.session_state: st.session_state[f"img_{key}"] = DEFAULT_IMAGES[key]

if "nav" not in st.session_state: st.session_state.nav = "工作台"
if "use_company" not in st.session_state: st.session_state.use_company = True
if "company_file" not in st.session_state: st.session_state.company_file = "萌爪宠物用品.json"
if "agent_msg" not in st.session_state: st.session_state.agent_msg = []
if "first_visit" not in st.session_state: st.session_state.first_visit = True

is_en = st.session_state.lang == "en"
T = lambda cn, en: en if is_en else cn
def pname(p): return p.get("name_en" if is_en else "name", p.get("name",""))

VERSION = "v2.3"
CHANGELOG = """
**v2.3 (2026-08-04)** 🆕 卡片库存+搜索置顶+真实平台+产品图
**v2.2 (2026-08-04)** 🆕 案例库+引导+更新日志+悬停
**v2.1 (2026-08-04)** 🤖 多Agent+双语+库存整数化
**v2.0 (2026-08-04)** 📊 仪表盘+区域分析+虚拟管家
"""

# ── 侧边栏 ──
with st.sidebar:
    st.image(load_image("sidebar"), use_container_width=True)
    for name in ["工作台","选品评分","定价模型","库存监控","案例库","销售自动化"]:
        kind = "primary" if st.session_state.nav == name else "secondary"
        if st.button(name, use_container_width=True, type=kind):
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
        st.markdown(T("**数据源**","**Data Source**"))
        use_co = st.checkbox(T("接入公司数据","Connect Company Data"), value=st.session_state.use_company)
        if use_co != st.session_state.use_company:
            st.session_state.use_company = use_co; st.rerun()

        if use_co and available_companies:
            company_names = available_companies
            current_idx = company_names.index(current_company_file) if current_company_file in company_names else 0
            selected = st.selectbox(T("选择公司","Select Company"), company_names, index=current_idx)
            if selected != st.session_state.company_file:
                st.session_state.company_file = selected; st.rerun()
    st.divider()
    with st.expander(T("关于","About")):
        st.markdown(T("**RetailSense** 由一位前瑞幸咖啡店长构建。","**RetailSense** built by a former Luckin Coffee store manager."))
    with st.expander(T(f"更新日志 {VERSION}","Changelog {VERSION}")):
        st.markdown(CHANGELOG)
    st.caption(f"{VERSION} · MIT")

page = st.session_state.nav
# 加载当前选择的公司
available_companies = list_companies()
current_company_file = st.session_state.company_file if st.session_state.company_file in available_companies else (available_companies[0] if available_companies else "")
company = load_company_data(current_company_file) if st.session_state.use_company and current_company_file else None
inv = get_inventory(company, st.session_state.use_company)
txns = get_transactions(company, st.session_state.use_company)
agent = VirtualAgent()

# ══ 工作台 ══
if page == "工作台":
    if st.session_state.first_visit:
        with st.container(border=True):
            st.markdown(T("### 🐾 欢迎使用 RetailSense！\n**三步开始：**\n1. 📈 选品评分 → 2. 🤖 销售自动化 → 3. 📖 案例库","### 🐾 Welcome!\n**Steps:** 1. Scoring → 2. Pipeline → 3. Cases"))
            if st.button(T("开始使用","Get Started"), type="primary"): st.session_state.first_visit = False; st.rerun()

    # 顶部搜索（管家助手）
    with st.container(border=True):
        msg = st.text_input(T("🔍 向管家提问（营收/库存/选品/帮助）","🔍 Ask assistant (revenue/stock/recommend/help)"), key="agent_input_top",
                           placeholder=T("输入命令如：今日营收、库存预警、推荐选品...","e.g. revenue, low stock, top products..."))
        if msg:
            resp = agent.process(msg, company_data=company, transactions=txns, inventory=inv)
            st.session_state.agent_msg.append(("user", msg))
            st.session_state.agent_msg.append(("agent", resp))
        for role, text in st.session_state.agent_msg[-4:]:
            (st.chat_message("user") if role=="user" else st.chat_message("assistant")).write(text)

    st.title("RetailSense")
    st.caption(T("AI 零售选品 · 定价 · 库存 · 出入库仪表盘","AI Retail · Pricing · Inventory · Dashboard"))

    if st.session_state.use_company and company:
        st.success(T(f"已接入：{company['company']}","Connected: "+company['company_en']))
    else:
        st.info(T("手动模式","Manual mode"))

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
                if st.button(T("选择","Select")+rname, key=f"reg_{i}", use_container_width=True):
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

    PRODUCTS = [
        {"name":"刻字狗牌","name_en":"Engraved Dog Tag","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"dog-tag"},
        {"name":"发光项圈","name_en":"LED Collar","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"led-collar"},
        {"name":"珐琅名牌","name_en":"Enamel Nameplate","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"enamel-plate"},
        {"name":"牵引绳套装","name_en":"Leash Set","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"leash-set"},
        {"name":"宠物领结","name_en":"Pet Bow Tie","cost":1.50,"price":9.99,"competitors":55,"search_growth":-5,"trend_up":False,"annual_purchases":3,"is_consumable":True,"img":"bow-tie"},
        {"name":"亚克力牌","name_en":"Acrylic Tag","cost":1.20,"price":8.99,"competitors":22,"search_growth":18,"trend_up":True,"annual_purchases":2,"is_consumable":False,"img":"acrylic-tag"},
        {"name":"宠物手链","name_en":"Pet Bracelet","cost":2.00,"price":14.99,"competitors":15,"search_growth":42,"trend_up":True,"annual_purchases":1,"is_consumable":False,"img":"bracelet"},
        {"name":"换牙零食","name_en":"Teething Treats","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8,"is_consumable":True,"img":"treats"},
    ]

    scorer = ProductScorer()
    for i, p in enumerate(PRODUCTS):
        img_path = os.path.join(PRODUCT_IMG_DIR, f"{p['img']}.jpg") if os.path.exists(os.path.join(PRODUCT_IMG_DIR, f"{p['img']}.jpg")) else ""
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

    if st.button(T("批量评分排名","Batch Ranking"), type="primary"):
        results = scorer.rank(PRODUCTS)
        rows = []
        for r in results:
            rows.append({T("产品","Product"):r.product_name,T("评分","Score"):f"{r.final_score:.0f}",
                         T("毛利","M"):r.margin_score,T("竞争","C"):r.competition_score,
                         T("趋势","T"):r.trend_score,T("复购","R"):r.repurchase_score})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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
            target = st.slider(T("目标利润率","Target Margin"), 0.20, 0.70, 0.45, 0.05, format="%.0f%%")

        st.divider()
        cc1, cc2 = st.columns(2)
        with cc1:
            currency = st.selectbox(T("货币单位","Currency"),
                                   ["¥ CNY","$ USD","€ EUR","£ GBP","¥ JPY","A$ AUD","C$ CAD"],
                                   index=1 if is_en else 0)
            symbol = currency.split()[0]
        with cc2:
            st.caption(T(f"当前单位：{symbol}（数值不换算，纯展示）",
                         f"Unit: {symbol} (no conversion, display only)"))

    if st.button(T("计算定价","Calculate"), type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)

        items = [(T("裸件","Raw"),raw),(T("加工","Proc"),proc),(T("包装","Pack"),pack),(T("物流","Ship"),ship),(T("平台","Plat"),plat)]
        cc = st.columns(5)
        for i, (lbl, val) in enumerate(items):
            with cc[i]:
                st.markdown(f"""<div class="card-hover" style="min-height:50px;">
                    <div style="font-size:16px;font-weight:700;color:#FF8C42;">{symbol}{val:.2f}</div>
                    <div style="font-size:10px;color:#888;">{lbl}</div></div>""", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(T("总成本","Total Cost"), f"{symbol}{result['total_cost']:.2f}")
        m2.metric(T("建议售价","Price"), f"{symbol}{result['suggested_price']:.2f}")
        m3.metric(T("利润","Profit"), f"{symbol}{result['profit']:.2f}")
        m4.metric(T("利润率","Margin"), f"{result['margin_rate']:.1%}",
                 delta=T("达标","OK") if result['above_redline'] else T("未达标","Low"),
                 delta_color="normal" if result['above_redline'] else "inverse")

# ══ 库存监控 ══
elif page == "库存监控":
    st.title(T("库存监控","Inventory Monitor"))
    if st.session_state.use_company and company:
        st.success(T(f"数据源：{company['company']}","Source: "+company['company_en']))
    else:
        st.info(T("手动模式","Manual mode"))
        inv = [
            {"sku":"BP-001","name":"刻字狗牌","name_en":"Engraved Dog Tag","qty":45,"cost":2.80,"price":12.99,"daily_avg":9,"lead_days":3,"img":"dog-tag"},
            {"sku":"BP-002","name":"发光项圈","name_en":"LED Collar","qty":12,"cost":5.50,"price":24.99,"daily_avg":6,"lead_days":5,"img":"led-collar"},
            {"sku":"BP-003","name":"珐琅名牌","name_en":"Enamel Nameplate","qty":120,"cost":3.20,"price":16.99,"daily_avg":3,"lead_days":3,"img":"enamel-plate"},
            {"sku":"BP-004","name":"牵引绳套装","name_en":"Leash Set","qty":0,"cost":4.50,"price":22.99,"daily_avg":4,"lead_days":4,"img":"leash-set"},
            {"sku":"BP-005","name":"换牙零食","name_en":"Teething Treats","qty":8,"cost":3.00,"price":11.99,"daily_avg":15,"lead_days":2,"img":"treats"},
        ]

    rows = []
    for i in inv:
        qty = i.get("qty",0)
        daily = int(i.get("daily_avg",1))
        lead = i.get("lead_days",3)
        safety = max(1, round(daily*7))
        reorder_qty = max(round(daily), safety + round(daily*lead) - qty) if qty < safety else 0
        status_cn = "断货" if qty==0 else ("低库存" if qty<safety else "正常")
        status_en = "OOS" if qty==0 else ("Low" if qty<safety else "Normal")
        status_color = "#ea4335" if qty==0 else ("#f4b400" if qty<safety else "#34a853")

        # 产品图片
        img_html = ""
        img_path = os.path.join(PRODUCT_IMG_DIR, f"{i.get('img','')}.jpg")
        if os.path.exists(img_path):
            img_html = f'<img src="data:image/jpeg;base64,..." style="display:none">'  # placeholder

        rows.append({
            T("产品","Product"): pname(i),
            "SKU": i.get("sku",""),
            T("库存","Qty"): qty,
            T("日均","Daily"): daily,
            T("安全库存","Safety"): safety,
            T("补货","Reorder"): reorder_qty,
            T("状态","Status"): status_en if is_en else status_cn,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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

    if st.button(T("启动全流程","Start Pipeline"), type="primary", use_container_width=True):
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
                st.dataframe(sd, use_container_width=True, hide_index=True)
        with t2:
            if state.priced:
                pd_data = pd.DataFrame(state.priced)
                pd_data_display = pd_data.rename(columns={"name":T("产品","Product"),"suggested_price":T("售价","Price"),
                    "profit":T("利润","Profit"),"margin":T("利润率","Margin"),"above_redline":T("达标","Pass")})
                st.dataframe(pd_data_display, use_container_width=True, hide_index=True)
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

st.divider()
st.image(load_image("footer"), use_container_width=True)
