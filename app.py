"""
RetailSense v2.0 — AI 零售选品与库存决策系统
新增：出入库仪表盘 · 区域市场分析 · 公司库存接入 · 虚拟管家
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

st.set_page_config(page_title="RetailSense", page_icon=" ", layout="wide")

# ── 基础状态 ──
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
DEFAULT_IMAGES = {
    "banner": os.path.join(IMAGE_DIR, "banner.jpg"),
    "sidebar": os.path.join(IMAGE_DIR, "sidebar.jpg"),
    "footer": os.path.join(IMAGE_DIR, "footer.jpg"),
}
def load_image(key):
    path = st.session_state.get(f"img_{key}", DEFAULT_IMAGES[key])
    if os.path.exists(path): return path
    if path.startswith("http"): return path
    return DEFAULT_IMAGES[key]
for key in DEFAULT_IMAGES:
    if f"img_{key}" not in st.session_state:
        st.session_state[f"img_{key}"] = DEFAULT_IMAGES[key]

if "lang" not in st.session_state: st.session_state.lang = "zh"
if "nav" not in st.session_state: st.session_state.nav = "工作台"
if "use_company" not in st.session_state: st.session_state.use_company = True
if "company_data" not in st.session_state:
    st.session_state.company_data = load_company_data()
if "agent_msg" not in st.session_state: st.session_state.agent_msg = []

is_en = st.session_state.lang == "en"
T = lambda cn, en: en if is_en else cn
def pname(p): return p.get("name_en" if is_en else "name", p.get("name",""))

# ── 侧边栏 ──
with st.sidebar:
    st.image(load_image("sidebar"), use_container_width=True)
    for name in ["工作台","选品评分","定价模型","库存监控","销售自动化"]:
        kind = "primary" if st.session_state.nav == name else "secondary"
        if st.button(name, use_container_width=True, type=kind):
            st.session_state.nav = name; st.rerun()
    st.divider()
    with st.expander("Settings"):
        lang = st.selectbox("Language", ["中文","English"], index=0 if st.session_state.lang=="zh" else 1)
        if (lang == "English" and st.session_state.lang != "en") or (lang == "中文" and st.session_state.lang != "zh"):
            st.session_state.lang = "en" if lang == "English" else "zh"; st.rerun()

        st.divider()
        st.markdown(T("**数据源**","**Data Source**"))
        use_co = st.checkbox(T("接入示例宠物用品公司","Connect Demo Pet Supplies Co."), value=st.session_state.use_company)
        if use_co != st.session_state.use_company:
            st.session_state.use_company = use_co
            st.rerun()

    st.divider()
    with st.expander("About"):
        st.markdown(T("""
        **RetailSense** 由一位前瑞幸咖啡店长构建。
        3年200+SKU管理经验AI化。
        [GitHub](https://github.com/yinqiqi1005-crypto/retail-sense)
        ""","""
        **RetailSense** built by a former Luckin Coffee store manager.
        3 years managing 200+ SKUs.
        [GitHub](https://github.com/yinqiqi1005-crypto/retail-sense)
        """))
    st.caption("v2.0 · MIT")

page = st.session_state.nav
company = st.session_state.company_data if st.session_state.use_company else None
inv = get_inventory(company, st.session_state.use_company)
txns = get_transactions(company, st.session_state.use_company)
agent = VirtualAgent()

# ═══════════════════════════════════════════
# 工作台 — 出入库仪表盘
# ═══════════════════════════════════════════
if page == "工作台":
    st.title("RetailSense")
    st.caption(T("AI 零售选品 · 定价 · 库存 · 出入库仪表盘",
                 "AI Retail · Pricing · Inventory · Dashboard"))

    # 数据源状态
    if st.session_state.use_company and company:
        st.success(T(f"已接入：{company['company']}","Connected: "+company['company_en']))
    else:
        st.info(T("手动模式：可自行录入数据","Manual mode: Enter data manually"))

    # KPI行
    today = daily_summary(txns, 1) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    week = daily_summary(txns, 7) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    month = daily_summary(txns, 30) if txns else {"revenue":0,"orders":0,"profit":0,"cost":0}
    inv_summary = inventory_value_summary(inv) if inv else {"total_qty":0,"total_value":0,"skus":0,"low_stock":0,"out_of_stock":0}

    c = st.columns(4)
    c[0].metric(T("今日营收","Today"), f"¥{today['revenue']:,.0f}", f"{today['orders']}单")
    c[1].metric(T("本周营收","Week"), f"¥{week['revenue']:,.0f}")
    c[2].metric(T("本月营收","Month"), f"¥{month['revenue']:,.0f}")
    c[3].metric(T("库存价值","Inventory"), f"¥{inv_summary['total_retail']:,.0f}", f"{inv_summary['skus']}SKU")

    st.divider()

    # 出入库趋势图
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(T("近期出库","Recent Sales"))
        if txns:
            out_txns = [t for t in txns if t["type"]=="out"]
            dates = sorted(set(t["date"] for t in out_txns))[-7:]
            chart = {}
            for d in dates:
                chart[d] = sum(t["revenue"] for t in out_txns if t["date"]==d)
            st.bar_chart(pd.DataFrame({"营收":chart}), use_container_width=True)
        else:
            st.caption(T("暂无数据","No data"))
    with col2:
        st.subheader(T("库存健康度","Inventory Health"))
        if inv:
            health = pd.DataFrame({
                T("状态","Status"):[T("正常","Normal"),T("低库存","Low"),T("断货","OOS")],
                T("数量","Qty"):[inv_summary['skus']-inv_summary['low_stock']-inv_summary['out_of_stock'],
                               inv_summary['low_stock'], inv_summary['out_of_stock']]
            }).set_index(T("状态","Status"))
            st.bar_chart(health, use_container_width=True)

    # 虚拟管家
    st.divider()
    st.subheader(T("管家助手","Assistant"))
    msg = st.text_input(T("输入命令（营收/库存/选品/帮助）","Command (revenue/stock/recommend/help)"), key="agent_input")
    if msg:
        resp = agent.process(msg, company_data=company, transactions=txns, inventory=inv)
        st.session_state.agent_msg.append(("user", msg))
        st.session_state.agent_msg.append(("agent", resp))

    for role, text in st.session_state.agent_msg[-4:]:
        if role == "user":
            st.chat_message("user").write(text)
        else:
            st.chat_message("assistant").write(text)

# ═══════════════════════════════════════════
# 选品评分 + 区域分析
# ═══════════════════════════════════════════
elif page == "选品评分":
    st.title(T("产品选品评分","Product Scoring"))

    # 区域选择 — 卡片式
    with st.container(border=True):
        st.markdown(T("**目标市场**","**Target Market**"))
        if "sel_region" not in st.session_state:
            st.session_state.sel_region = "北美"

        regions_list = all_regions()
        cols = st.columns(len(regions_list))
        region_colors = {"北美":"#1a73e8","欧洲":"#4285f4","东南亚":"#f4b400","日韩":"#ea4335","澳洲":"#34a853"}
        for i, (col, rname) in enumerate(zip(cols, regions_list)):
            with col:
                rd = get_region(rname)
                is_sel = st.session_state.sel_region == rname
                border = f"2px solid {region_colors[rname]}" if is_sel else "1px solid #ddd"
                bg = f"{region_colors[rname]}15" if is_sel else "#fff"
                st.markdown(f"""
                <div style="border:{border};border-radius:4px;padding:10px;text-align:center;background:{bg};cursor:pointer;min-height:90px;">
                    <div style="font-weight:600;font-size:14px;">{rname}</div>
                    <div style="font-size:11px;color:#666;margin-top:4px;">{', '.join(rd['countries'][:3]) if rd else ''}</div>
                    <div style="font-size:10px;color:#888;margin-top:2px;">{rd['avg_margin'] if rd else ''}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"选择{rname}", key=f"reg_{i}", use_container_width=True):
                    st.session_state.sel_region = rname
                    st.rerun()

        region = st.session_state.sel_region
        rd = get_region(region)
        if rd:
            c1, c2, c3 = st.columns(3)
            c1.metric(T("平台","Platforms"), len(rd["platforms"]))
            c2.metric(T("利润率","Margin"), rd["avg_margin"])
            c3.metric(T("竞争度","Comp"), rd["competition"])

        with st.expander(T("近期活动与上品建议","Events & Listing Guide"), expanded=True):
            for item in upcoming_events(region):
                if len(item) == 5:
                    m, e, desc, idx, tip = item
                    score = int(idx.replace("上品指数:",""))
                    color = "#34a853" if score>=90 else ("#f4b400" if score>=80 else "#ea4335")
                    st.markdown(f"""
                    <div style="border-left:3px solid {color};padding:6px 12px;margin:6px 0;background:#fafafa;border-radius:2px;">
                        <span style="font-weight:600;font-size:13px;">{m} · {e}</span>
                        <span style="background:{color};color:white;padding:1px 6px;border-radius:2px;font-size:11px;margin-left:8px;">{idx}</span><br>
                        <span style="font-size:12px;color:#555;">{desc}</span><br>
                        <span style="font-size:12px;color:{color};">{tip}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # 方法论
    with st.expander(T("评分方法论与数据来源","Methodology"), expanded=False):
        st.markdown(T("""
        **设计理念**：3年瑞幸200+SKU管理经验 → 真正吃掉利润的是滞销，不是成本。
        | 维度 | 权重 | 理由 |
        |------|:---:|------|
        | 复购率 | 30% | 高复购 > 高毛利 |
        | 竞争度 | 25% | 定价权决定利润 |
        | 趋势 | 25% | 上升期自带流量 |
        | 毛利 | 20% | 重要但不唯一 |
        ""","""
        **Design**: 3yr Luckin, 200+ SKUs → unsold inventory destroys profit.
        | Dimension | Weight | Rationale |
        |-----------|:---:|------|
        | Repurchase | 30% | High-repeat > high-margin |
        | Competition | 25% | Fewer rivals = pricing power |
        | Trend | 25% | Rising categories bring organic traffic |
        | Margin | 20% | Important but not decisive |
        """))

    # 产品列表
    PRODUCTS = [
        {"name":"刻字狗牌","name_en":"Engraved Dog Tag","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2.5,"is_consumable":False},
        {"name":"发光项圈","name_en":"LED Collar","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":1.5,"is_consumable":False},
        {"name":"珐琅名牌","name_en":"Enamel Nameplate","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2.0,"is_consumable":False},
        {"name":"牵引绳套装","name_en":"Leash Set","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":1.8,"is_consumable":False},
        {"name":"宠物领结","name_en":"Pet Bow Tie","cost":1.50,"price":9.99,"competitors":55,"search_growth":-5,"trend_up":False,"annual_purchases":3.0,"is_consumable":True},
        {"name":"亚克力牌","name_en":"Acrylic Tag","cost":1.20,"price":8.99,"competitors":22,"search_growth":18,"trend_up":True,"annual_purchases":2.0,"is_consumable":False},
        {"name":"宠物手链","name_en":"Pet Bracelet","cost":2.00,"price":14.99,"competitors":15,"search_growth":42,"trend_up":True,"annual_purchases":1.2,"is_consumable":False},
        {"name":"换牙零食","name_en":"Teething Treats","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8.0,"is_consumable":True},
    ]

    scorer = ProductScorer()
    for i, p in enumerate(PRODUCTS):
        label = f"{pname(p)} — ¥{p['price']} | ¥{p['cost']} | {p['competitors']} rivals"
        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            with c1:
                ps = scorer.evaluate(p)
                st.bar_chart(pd.DataFrame({"Score":[ps.margin_score,ps.competition_score,ps.trend_score,ps.repurchase_score]},
                                          index=["Margin","Comp","Trend","Repur"]), use_container_width=True)

            with c2:
                st.markdown(T("**区域推荐**","**Region Recs**"))
                for r in best_region_for_product(p):
                    st.markdown(f"- {r}")

                style = st.selectbox(T("风格","Style"), ["seo","social","sales"], key=f"sty_{i}", label_visibility="collapsed")
                if st.button(T("生成文案","Copy"), key=f"gc_{i}"):
                    st.markdown(CopyGenerator().generate(p, style))

            with c3:
                ie = IntentEngine()
                best = ie.best_angle(p)
                st.caption(f"**{best['angle']}**: {best['pitch']}")

    if st.button(T("批量评分排名","Batch Ranking"), type="primary"):
        results = scorer.rank(PRODUCTS)
        rd = pd.DataFrame([{"Product":r.product_name,"Score":r.final_score,
                            "Margin":r.margin_score,"Comp":r.competition_score,
                            "Trend":r.trend_score,"Repur":r.repurchase_score} for r in results])
        c1, c2 = st.columns([2,1])
        c1.dataframe(rd, use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(format="%.1f",min_value=0,max_value=100)})
        c2.bar_chart(rd.set_index("Product")["Score"], use_container_width=True)

# ═══════════════════════════════════════════
# 定价模型
# ═══════════════════════════════════════════
elif page == "定价模型":
    st.title(T("定价模型","Pricing Model"))

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            raw = st.number_input(T("裸件成本","Raw"), value=2.80, step=0.10, format="%.2f")
            proc = st.number_input(T("加工费","Proc"), value=1.20, step=0.10, format="%.2f")
        with c2:
            pack = st.number_input(T("包装费","Pack"), value=0.50, step=0.10, format="%.2f")
            ship = st.number_input(T("物流费","Ship"), value=1.50, step=0.10, format="%.2f")
        with c3:
            plat = st.number_input(T("平台费","Platform"), value=0.85, step=0.10, format="%.2f")
            target = st.slider(T("目标利润率","Target"), 0.20, 0.70, 0.45, 0.05, format="%.0f%%")

    if st.button(T("计算","Calculate"), type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(pd.DataFrame({"Item":["Raw","Proc","Pack","Ship","Plat"],"Amount":[raw,proc,pack,ship,plat]}).set_index("Item"), use_container_width=True)
        with col2:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(T("总成本","Cost"), f"¥{result['total_cost']:.2f}")
            m2.metric(T("建议售价","Price"), f"¥{result['suggested_price']:.2f}")
            m3.metric(T("利润","Profit"), f"¥{result['profit']:.2f}")
            m4.metric(T("利润率","Margin"), f"{result['margin_rate']:.1%}",
                     delta=T("达标","OK") if result['above_redline'] else T("低","Low"),
                     delta_color="normal" if result['above_redline'] else "inverse")

        with st.container(border=True):
            sim = model.profit_simulate(cost, (result['min_price'], result['suggested_price']*1.3))
            st.line_chart(pd.DataFrame([{"Price":s['price'],"Profit":s['profit']} for s in sim]).set_index("Price"), use_container_width=True)

# ═══════════════════════════════════════════
# 库存监控
# ═══════════════════════════════════════════
elif page == "库存监控":
    st.title(T("库存监控","Inventory Monitor"))

    if st.session_state.use_company and company:
        st.success(T(f"数据源：{company['company']}","Source: "+company['company_en']))
    else:
        st.info(T("手动模式","Manual mode"))
        inv = [
            {"sku":"BP-001","name":"刻字狗牌","name_en":"Engraved Dog Tag","qty":45,"cost":2.80,"price":12.99,"daily_avg":8.5,"lead_days":3},
            {"sku":"BP-002","name":"发光项圈","name_en":"LED Collar","qty":12,"cost":5.50,"price":24.99,"daily_avg":6.2,"lead_days":5},
            {"sku":"BP-003","name":"珐琅名牌","name_en":"Enamel Nameplate","qty":120,"cost":3.20,"price":16.99,"daily_avg":3.1,"lead_days":3},
            {"sku":"BP-004","name":"牵引绳套装","name_en":"Leash Set","qty":0,"cost":4.50,"price":22.99,"daily_avg":4.0,"lead_days":4},
            {"sku":"BP-005","name":"换牙零食","name_en":"Teething Treats","qty":8,"cost":3.00,"price":11.99,"daily_avg":15.0,"lead_days":2},
        ]

    rows = []
    for i in inv:
        qty = i.get("qty", i.get("current_stock",0))
        daily = i.get("daily_avg", i.get("daily_sales",1))
        lead = i.get("lead_days",3)
        safety = max(1, round(daily*7))
        reorder_pt = safety + round(daily*lead)
        reorder_qty = max(round(daily), reorder_pt - qty) if qty < reorder_pt else 0

        status_cn = "断货" if qty==0 else ("低库存" if qty<safety else "正常")
        status_en = "OOS" if qty==0 else ("Low" if qty<safety else "Normal")

        rows.append({
            T("产品","Product"): pname(i),
            "SKU": i.get("sku",""),
            T("库存","Qty"): qty,
            T("日均","Daily"): f"{daily:.0f}",
            T("安全库存","Safety"): safety,
            T("建议补货","Reorder"): reorder_qty,
            T("状态","Status"): status_en if is_en else status_cn,
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.bar_chart(pd.DataFrame({pname(i):[i.get("qty",0)] for i in inv}, index=[T("库存","Qty")]).T, use_container_width=True)

# ═══════════════════════════════════════════
# 销售自动化 — 多Agent流水线
# ═══════════════════════════════════════════
elif page == "销售自动化":
    st.title(T("多智能体销售自动化","Multi-Agent Sales Pipeline"))
    st.caption(T("Scout选品→Price定价→Copy文案→Monitor监控 四Agent流水线","Scout→Price→Copy→Monitor Pipeline"))

    # 操作指引
    with st.expander(T("操作指引","How it works"), expanded=False):
        st.markdown(T("""
        **流程说明：**
        1. **Scout 选品侦察** — 自动扫描产品池，多维度评分排序，找出最优选品
        2. **Price 智能定价** — 为TOP5产品计算成本拆解+建议售价+利润模拟
        3. **Copy 文案生成** — 为定价后的产品生成SEO/社交/促销三套营销文案
        4. **Monitor 库存监控** — 巡检库存状态，标注断货/低库存/利润率不达标
        
        **操作步骤：**
        - 调整目标利润率（建议45%起步）
        - 选择目标市场（影响区域化建议）
        - 点击「启动全流程」→ 等待4个Agent依次执行
        - 查看结果Tabs：评分→定价→文案→监控
        """,
        """
        **How it works:**
        1. **Scout** — Auto-scan products, multi-dimension scoring & ranking
        2. **Price** — Cost breakdown + suggested price + profit simulation for TOP5
        3. **Copy** — Generate SEO/social/sales copy for priced products
        4. **Monitor** — Check inventory health, flag issues
        
        **Steps:**
        - Adjust target margin (recommend 45%)
        - Select target market (affects regional suggestions)
        - Click Start → wait for 4 agents to execute
        - Check result tabs: Scoring→Pricing→Copy→Monitor
        """))

    # 产品池
    PRODUCTS = [
        {"name":"刻字狗牌","name_en":"Engraved Dog Tag","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2.5,"is_consumable":False,"qty":45,"daily_avg":8.5},
        {"name":"发光项圈","name_en":"LED Collar","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":1.5,"is_consumable":False,"qty":12,"daily_avg":6.2},
        {"name":"珐琅名牌","name_en":"Enamel Nameplate","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2.0,"is_consumable":False,"qty":120,"daily_avg":3.1},
        {"name":"牵引绳套装","name_en":"Leash Set","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":1.8,"is_consumable":False,"qty":0,"daily_avg":4.0},
        {"name":"换牙零食","name_en":"Teething Treats","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8.0,"is_consumable":True,"qty":8,"daily_avg":15.0},
    ]

    # 控制面板
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            target_pct = st.slider(T("目标利润率","Target Margin"), 25, 60, 45, 5,
                                  format="%d%%",
                                  help=T("建议45%起步，确保高于28%红线","Start at 45%, stay above 28% redline"))
        with c2:
            region = st.selectbox(T("目标市场","Target Market"), ["北美","欧洲","东南亚","日韩","澳洲"])
        st.caption(T(f"当前产品池：{len(PRODUCTS)}个SKU | 利润率目标：{target_pct}%",
                     f"Product pool: {len(PRODUCTS)} SKUs | Target margin: {target_pct}%"))

    # 流水线预览 — 标注Agent接入点
    st.markdown(T("**流水线**","**Pipeline**"))
    steps = st.columns(4)
    for i, (name, icon, label_cn, label_en, hint_cn, hint_en) in enumerate([
        ("Scout","🔍","选品侦察","Scout","多维评分排序","Multi-dim scoring"),
        ("Price","💰","智能定价","Price","成本拆解+利润模拟","Cost breakdown+sim"),
        ("Copy","✍️","文案生成","Copy","SEO+社交+促销","SEO+social+sales"),
        ("Monitor","📊","库存监控","Monitor","异常巡检+趋势预测","Alert+trade forecast"),
    ]):
        with steps[i]:
            st.markdown(f"""
            <div style="border:1px solid #e0e0e0;border-radius:4px;padding:12px;text-align:center;min-height:90px;">
                <div style="font-size:20px;">{icon}</div>
                <div style="font-weight:600;font-size:13px;margin-top:4px;">{T(label_cn, label_en)}</div>
                <div style="font-size:11px;color:#888;margin-top:2px;">{T(hint_cn, hint_en)}</div>
                <div style="margin-top:6px;">
                    <span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:2px;font-size:10px;font-weight:500;">
                        {T('可接入Agent','Agent Ready')}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Agent架构说明
    with st.expander(T("Agent 架构说明","Agent Architecture"), expanded=False):
        st.markdown(T("""
        ```
        ┌─────────────────────────────────────────────────┐
        │           RetailSense Agent 架构                 │
        ├─────────────────────────────────────────────────┤
        │  Scout Agent ←─ 接入 DeepSeek/Claude API        │
        │     ↓ 传递评分结果                               │
        │  Price Agent ←─ 接入定价模型 + 实时汇率          │
        │     ↓ 传递定价方案                               │
        │  Copy Agent ←─ 接入 LLM 流式生成                 │
        │     ↓ 传递营销内容                               │
        │  Monitor Agent ←─ 接入库存系统 + 趋势预测        │
        └─────────────────────────────────────────────────┘
        ```
        
        **当前状态**：规则引擎模式（演示/测试用）
        **完整模式**：每个 Agent 可接入独立 LLM（DeepSeek/Claude/GPT），实现真正的自主决策
        
        > 接入方式：替换 `SalesPipeline` 中各 Agent 的 `run()` 方法为 API 调用即可
        """,
        """
        ```
        ┌─────────────────────────────────────────────────┐
        │         RetailSense Agent Architecture           │
        ├─────────────────────────────────────────────────┤
        │  Scout Agent ←─ Connect DeepSeek/Claude API     │
        │     ↓ passes scoring results                    │
        │  Price Agent ←─ Connect pricing + live FX        │
        │     ↓ passes pricing plan                       │
        │  Copy Agent ←─ Connect LLM streaming             │
        │     ↓ passes marketing content                  │
        │  Monitor Agent ←─ Connect inventory + forecast  │
        └─────────────────────────────────────────────────┘
        ```
        
        **Current**: Rule engine mode (demo/testing)
        **Full mode**: Each Agent can connect to independent LLM for autonomous decisions
        
        > To enable: replace `run()` in each Agent with API calls
        """))

    # 执行
    if st.button(T("启动全流程","Start Pipeline"), type="primary", use_container_width=True):
        pipeline = SalesPipeline()
        with st.spinner(T("Agent流水线执行中...","Pipeline running...")):
            state = pipeline.run(PRODUCTS, target_pct/100, region)

        st.success(T(f"全流程完成！({state.started_at} → {state.completed_at})",
                     f"Pipeline complete! ({state.started_at} → {state.completed_at})"))

        tab1, tab2, tab3, tab4 = st.tabs([
            T("选品评分","Scoring"),T("定价方案","Pricing"),
            T("营销内容","Copy"),T("监控报告","Monitor")])

        with tab1:
            if state.scored:
                sd = pd.DataFrame([{"Product":r.product_name,"Score":r.final_score,
                                    "Margin":r.margin_score,"Comp":r.competition_score,
                                    "Trend":r.trend_score,"Repur":r.repurchase_score} for r in state.scored])
                st.dataframe(sd, use_container_width=True, hide_index=True,
                            column_config={"Score":st.column_config.ProgressColumn(format="%.1f",min_value=0,max_value=100)})
                st.bar_chart(sd.set_index("Product")["Score"], use_container_width=True)

        with tab2:
            if state.priced:
                pd_data = pd.DataFrame(state.priced)
                st.dataframe(pd_data, use_container_width=True, hide_index=True,
                            column_config={"margin":st.column_config.ProgressColumn(format="%.1%",min_value=0,max_value=1)})
                # 利润率达标状态
                ok = sum(1 for p in state.priced if p["above_redline"])
                st.metric(T("达标率","Pass Rate"), f"{ok}/{len(state.priced)}",
                         delta=T("全部达标" if ok==len(state.priced) else f"{len(state.priced)-ok}个未达标","All pass" if ok==len(state.priced) else f"{len(state.priced)-ok} below"),
                         delta_color="normal" if ok==len(state.priced) else "inverse")

        with tab3:
            if state.copy:
                for c in state.copy:
                    with st.expander(c["name"]):
                        st.markdown(f"**SEO**\n{c['seo']}")
                        st.divider()
                        st.markdown(f"**社交种草**\n{c['social']}")
                        st.divider()
                        st.markdown(f"**销售转化**\n{c['script']['开场']}")

        with tab4:
            if state.monitor:
                for m in state.monitor:
                    with st.container(border=True):
                        # 标记严重程度
                        has_urgent = any("断货" in i or "OOS" in i or "不达标" in i for i in m["issues"])
                        if has_urgent:
                            st.error(f"**{m['name']}**")
                        else:
                            st.warning(f"**{m['name']}**")
                        for issue in m["issues"]:
                            st.markdown(f"- {issue}")

                        # 趋势建议（联动选品评分）
                        prod = next((p for p in PRODUCTS if p["name"]==m["name"]), None)
                        if prod:
                            scorer = ProductScorer()
                            ps = scorer.evaluate(prod)
                            if ps.final_score >= 70:
                                st.success(T(f"评分{ps.final_score}分 → 建议保留并优先补货","Score {ps.final_score} → Keep & prioritize restock"))
                            elif ps.final_score >= 50:
                                st.info(T(f"评分{ps.final_score}分 → 维持现有库存，观察2周趋势","Score {ps.final_score} → Maintain stock, observe 2-week trend"))
                            else:
                                st.error(T(f"评分{ps.final_score}分 → 建议降价清仓或退市","Score {ps.final_score} → Suggest clearance or delist"))
            else:
                st.success(T("所有产品正常","All products normal"))

        with st.expander(T("执行日志","Execution Log")):
            for log in state.logs:
                st.markdown(f"`{log}`")

st.divider()
st.image(load_image("footer"), use_container_width=True)
