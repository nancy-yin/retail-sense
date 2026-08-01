"""
RetailSense — AI 零售选品与库存决策系统
"""
import streamlit as st
import pandas as pd
import os
from retail_sense.scorer import ProductScorer
from retail_sense.pricing import CostBreakdown, PricingModel
from retail_sense.inventory import InventoryStatus
from retail_sense.copywriter import CopyGenerator
from retail_sense.intent import IntentEngine
from retail_sense.sales_script import SalesScriptGenerator
from retail_sense.i18n import t

st.set_page_config(page_title="RetailSense", page_icon=" ", layout="wide")

# ── 初始化 ──
if "lang" not in st.session_state: st.session_state.lang = "zh"

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

# ── 产品数据（中英双语）──
PRODUCTS = [
    {"name": "刻字狗牌", "name_en": "Engraved Dog Tag", "cost": 2.80, "price": 12.99,
     "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2.5, "is_consumable": False},
    {"name": "发光项圈", "name_en": "LED Collar", "cost": 5.50, "price": 24.99,
     "competitors": 28, "search_growth": 15, "trend_up": True, "annual_purchases": 1.5, "is_consumable": False},
    {"name": "珐琅名牌", "name_en": "Enamel Nameplate", "cost": 3.20, "price": 16.99,
     "competitors": 18, "search_growth": 35, "trend_up": True, "annual_purchases": 2.0, "is_consumable": False},
    {"name": "牵引绳套装", "name_en": "Leash Set", "cost": 4.50, "price": 22.99,
     "competitors": 42, "search_growth": 8, "trend_up": True, "annual_purchases": 1.8, "is_consumable": False},
    {"name": "宠物领结", "name_en": "Pet Bow Tie", "cost": 1.50, "price": 9.99,
     "competitors": 55, "search_growth": -5, "trend_up": False, "annual_purchases": 3.0, "is_consumable": True},
    {"name": "亚克力牌", "name_en": "Acrylic Tag", "cost": 1.20, "price": 8.99,
     "competitors": 22, "search_growth": 18, "trend_up": True, "annual_purchases": 2.0, "is_consumable": False},
    {"name": "宠物手链", "name_en": "Pet Bracelet", "cost": 2.00, "price": 14.99,
     "competitors": 15, "search_growth": 42, "trend_up": True, "annual_purchases": 1.2, "is_consumable": False},
    {"name": "换牙零食", "name_en": "Teething Treats", "cost": 3.00, "price": 11.99,
     "competitors": 30, "search_growth": 28, "trend_up": True, "annual_purchases": 8.0, "is_consumable": True},
]

INVENTORY_DATA = [
    ("刻字狗牌", "Engraved Dog Tag", 45, 8.5, 3),
    ("发光项圈", "LED Collar", 12, 6.2, 5),
    ("珐琅名牌", "Enamel Nameplate", 120, 3.1, 3),
    ("牵引绳套装", "Leash Set", 0, 4.0, 4),
    ("换牙零食", "Teething Treats", 8, 15.0, 2),
]

if "nav" not in st.session_state: st.session_state.nav = "工作台"
if "scored" not in st.session_state: st.session_state.scored = False
if "top_pick" not in st.session_state: st.session_state.top_pick = None

# ── 侧边栏 ──
with st.sidebar:
    st.image(load_image("sidebar"), use_container_width=True)
    for name in ["工作台","选品评分","定价模型","库存监控"]:
        kind = "primary" if st.session_state.nav == name else "secondary"
        if st.button(name, use_container_width=True, type=kind):
            st.session_state.nav = name; st.rerun()
    st.divider()
    with st.expander("Settings"):
        lang = st.selectbox("Language", ["中文","English"], index=0 if st.session_state.lang=="zh" else 1)
        new_lang = "zh" if lang=="中文" else "en"
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang; st.rerun()
    st.caption("v1.0 · MIT")

page = st.session_state.nav
is_en = st.session_state.lang == "en"

def pname(p):
    return p.get("name_en" if is_en else "name", p["name"])

T = lambda cn,en: en if is_en else cn

# ═══════════════════════════════════════════
# 工作台
# ═══════════════════════════════════════════
if page == "工作台":
    st.image(load_image("banner"), use_container_width=True)
    st.title("RetailSense")
    st.caption(T("AI 零售选品 · 定价 · 库存决策系统","AI Retail Selection · Pricing · Inventory"))

    c = st.columns(4)
    c[0].metric(T("评估产品","Products"), "8")
    if st.session_state.scored:
        c[1].metric(T("首选推荐","Top Pick"),
                    pname(st.session_state.products[0]) if hasattr(st.session_state.top_pick,'product_name')
                    else st.session_state.top_pick.product_name if st.session_state.top_pick else "—")
    else:
        c[1].metric(T("首选推荐","Top Pick"), "—")
    c[2].metric(T("库存预警","Alerts"), "0")
    c[3].metric(T("系统","System"), T("就绪","Ready"))

    if st.session_state.scored:
        scorer = ProductScorer()
        results = scorer.rank(PRODUCTS)
        chart = {r.product_name: [r.final_score,r.margin_score,r.competition_score,r.trend_score,r.repurchase_score] for r in results}
        st.bar_chart(pd.DataFrame(chart, index=["Score","Margin","Competition","Trend","Repurchase"]).T, use_container_width=True)

# ═══════════════════════════════════════════
# 选品评分
# ═══════════════════════════════════════════
elif page == "选品评分":
    st.title(T("产品选品评分","Product Scoring"))
    st.caption(T("多维度加权评分 | 复购率权重 30% | 基于市场数据",
                 "Multi-dimensional scoring | 30% repurchase weight | Data-driven"))

    with st.container(border=True):
        st.markdown(T("**市场背景**","**Market Overview**"))
        c = st.columns(4)
        c[0].metric(T("品类趋势","Trend"), "+22%", T("上升","Up"))
        c[1].metric(T("竞争密度","Competition"), T("中等","Medium"))
        c[2].metric(T("利润空间","Margin"), "55-70%")
        c[3].metric(T("复购周期","Repurchase"), "2-3/year")

    st.subheader(T("候选产品","Product Catalog"))
    df = pd.DataFrame(PRODUCTS)
    disp = df[["name","name_en","cost","price","competitors","search_growth","annual_purchases"]]
    disp.columns = ["产品","Product","Cost","Price","Rivals","Trend%","Repurchase/yr"]
    st.dataframe(disp if is_en else disp[["产品","Cost","Price","Rivals","Trend%","Repurchase/yr"]],
                 use_container_width=True, hide_index=True)

    scorer = ProductScorer()
    for i, p in enumerate(PRODUCTS):
        label = f"{pname(p)} — ¥{p['price']} | ¥{p['cost']} | {p['competitors']} rivals"
        with st.expander(label):
            c1, c2, c3 = st.columns(3)
            with c1:
                ps = scorer.evaluate(p)
                st.bar_chart(pd.DataFrame({"Score":[ps.margin_score,ps.competition_score,ps.trend_score,ps.repurchase_score]},
                                          index=["Margin","Competition","Trend","Repurchase"]), use_container_width=True)

            with c2:
                style = st.selectbox(T("风格","Style"), ["seo","social","sales"], key=f"sty_{i}", label_visibility="collapsed")
                if st.button(T("生成文案","Generate Copy"), key=f"gc_{i}"):
                    cg = CopyGenerator()
                    result = cg.generate(p, style)
                    st.markdown(result)

                sg = SalesScriptGenerator()
                script = sg.full_script(p)
                with st.expander(T("促单话术","Sales Script")):
                    st.markdown(f"**Opening:** {script['开场']}")
                    st.markdown(f"**Objection:** {script['异议处理']}")
                    st.markdown(f"**Close:** {script['促单结束']}")

            with c3:
                ie = IntentEngine()
                matches = ie.match(p)
                st.dataframe(pd.DataFrame([{"Profile":m["profile"],"Score":m["score"],"Level":m["match_level"]} for m in matches[:3]]),
                             use_container_width=True, hide_index=True)
                best = ie.best_angle(p)
                st.caption(f"**{best['angle']}**: {best['pitch']}")

    if st.button(T("批量评分排名","Batch Ranking"), type="primary"):
        results = scorer.rank(PRODUCTS)
        st.session_state.scored = True
        st.session_state.top_pick = results[0]
        st.session_state.products = PRODUCTS

        rd = pd.DataFrame([{
            "Product": r.product_name, "Score": r.final_score,
            "Margin": r.margin_score, "Comp": r.competition_score,
            "Trend": r.trend_score, "Repur": r.repurchase_score
        } for r in results])
        c1, c2 = st.columns([2, 1])
        c1.dataframe(rd, use_container_width=True, hide_index=True,
                     column_config={"Score": st.column_config.ProgressColumn(format="%.1f",min_value=0,max_value=100)})
        c2.bar_chart(rd.set_index("Product")["Score"], use_container_width=True)

# ═══════════════════════════════════════════
# 定价模型
# ═══════════════════════════════════════════
elif page == "定价模型":
    st.title(T("定价模型","Pricing Model"))
    st.caption(T("成本逐项拆解 | 28% 红线 | 利润模拟",
                 "Cost Breakdown | 28% Redline | Profit Simulation"))

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

    if st.button(T("计算","Calculate"), type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)

        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown(T("**成本结构**","**Cost Structure**"))
                st.bar_chart(pd.DataFrame({"Item":["Raw","Proc","Pack","Ship","Platform"],"Amount":[raw,proc,pack,ship,plat]}).set_index("Item"), use_container_width=True)

        with col2:
            with st.container(border=True):
                st.markdown(T("**定价结果**","**Pricing Result**"))
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(T("总成本","Total"), f"¥{result['total_cost']:.2f}")
                m2.metric(T("建议售价","Price"), f"¥{result['suggested_price']:.2f}")
                m3.metric(T("利润","Profit"), f"¥{result['profit']:.2f}")
                m4.metric(T("利润率","Margin"), f"{result['margin_rate']:.1%}",
                         delta=T("达标","OK") if result['above_redline'] else T("未达标","Low"),
                         delta_color="normal" if result['above_redline'] else "inverse")

                if result['above_redline']:
                    st.success(T(f"利润率达标，建议售价 ¥{result['suggested_price']:.2f}",
                                f"Above redline. Suggested price: ¥{result['suggested_price']:.2f}"))
                else:
                    st.error(T(f"利润率 {result['margin_rate']:.1%} 低于 28%，建议提价至 ¥{result['min_price']:.2f}",
                              f"Margin {result['margin_rate']:.1%} below 28%. Raise to ¥{result['min_price']:.2f}"))

        with st.container(border=True):
            st.markdown(T("**利润模拟**","**Profit Simulation**"))
            sim = model.profit_simulate(cost, (result['min_price'], result['suggested_price']*1.3))
            sd = pd.DataFrame([{"Price":s['price'],"Profit":s['profit']} for s in sim])
            st.line_chart(sd.set_index("Price"), use_container_width=True)

# ═══════════════════════════════════════════
# 库存监控
# ═══════════════════════════════════════════
elif page == "库存监控":
    st.title(T("库存监控","Inventory Monitor"))
    st.caption(T("周转天数 · 安全库存 · 补货建议 · 滞销预警",
                 "Turnover Days · Safety Stock · Reorder · Stale Alert"))

    inv_list = []
    for zh, en, qty, daily, lead in INVENTORY_DATA:
        name = en if is_en else zh
        inv_list.append(InventoryStatus(name, qty, daily, lead))

    rows = [{
        "Product": i.product_name, "Stock": i.current_stock,
        "Daily Avg": f"{i.daily_sales:.1f}", "Turnover": f"{i.turnover_days}d",
        "Safety Stock": i.safety_stock, "Suggested Reorder": i.reorder_quantity,
        "Status": ("OOS" if i.current_stock==0 else "Low" if i.turnover_days<3 else "Overstock" if i.turnover_days>30 else "Normal")
    } for i in inv_list]

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.bar_chart(pd.DataFrame({i.product_name: [i.current_stock] for i in inv_list}, index=["Qty"]).T, use_container_width=True)

    st.divider()
    st.subheader(T("建议","Recommendations"))
    for inv in inv_list:
        if inv.current_stock == 0:
            with st.container(border=True):
                st.error(f"{inv.product_name} — {T('断货 · 建议立即补货','OOS · Reorder Immediately')} {inv.reorder_quantity} {T('件','units')} ({inv.lead_days}{T('天','d')} lead)")
        elif inv.turnover_days < 3:
            with st.container(border=True):
                st.warning(f"{inv.product_name} — {T('低库存 · 仅剩','Low · Only')} {inv.turnover_days}{T('天','d')} | {T('补货','Reorder')} {inv.reorder_quantity}")
        elif inv.turnover_days > 30:
            with st.container(border=True):
                st.info(f"{inv.product_name} — {T('积压 ·','Overstock ·')} {inv.turnover_days}{T('天','d')} | {T('建议促销清仓','Clearance suggested')}")

st.divider()
st.image(load_image("footer"), use_container_width=True)
