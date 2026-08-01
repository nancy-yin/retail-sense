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

# ── 语言 ──
if "lang" not in st.session_state:
    st.session_state.lang = "zh"

# ── 图片配置 ──
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

# ── 产品数据 ──
DEFAULT_PRODUCTS = [
    {"name":"刻字狗牌","cost":2.80,"price":12.99,"competitors":35,"search_growth":22,"trend_up":True,"annual_purchases":2.5,"is_consumable":False},
    {"name":"发光项圈","cost":5.50,"price":24.99,"competitors":28,"search_growth":15,"trend_up":True,"annual_purchases":1.5,"is_consumable":False},
    {"name":"珐琅名牌","cost":3.20,"price":16.99,"competitors":18,"search_growth":35,"trend_up":True,"annual_purchases":2.0,"is_consumable":False},
    {"name":"牵引绳套装","cost":4.50,"price":22.99,"competitors":42,"search_growth":8,"trend_up":True,"annual_purchases":1.8,"is_consumable":False},
    {"name":"宠物领结","cost":1.50,"price":9.99,"competitors":55,"search_growth":-5,"trend_up":False,"annual_purchases":3.0,"is_consumable":True},
    {"name":"亚克力牌","cost":1.20,"price":8.99,"competitors":22,"search_growth":18,"trend_up":True,"annual_purchases":2.0,"is_consumable":False},
    {"name":"宠物手链","cost":2.00,"price":14.99,"competitors":15,"search_growth":42,"trend_up":True,"annual_purchases":1.2,"is_consumable":False},
    {"name":"换牙零食","cost":3.00,"price":11.99,"competitors":30,"search_growth":28,"trend_up":True,"annual_purchases":8.0,"is_consumable":True},
]

for key in ["products","scored","top_pick","nav"]:
    if key not in st.session_state:
        st.session_state[key] = DEFAULT_PRODUCTS if key == "products" else (False if key == "scored" else (None if key == "top_pick" else "工作台"))

# ── 侧边栏（仅导航）──
with st.sidebar:
    st.image(load_image("sidebar"), use_container_width=True)

    pages_map = {"工作台":"nav.dashboard","选品评分":"nav.scoring","定价模型":"nav.pricing","库存监控":"nav.inventory"}
    for zh_name, key in pages_map.items():
        kind = "primary" if st.session_state.nav == zh_name else "secondary"
        if st.button(zh_name, use_container_width=True, type=kind):
            st.session_state.nav = zh_name
            st.rerun()

    st.divider()
    st.caption("v1.0 · MIT License")

# ── 顶部设置栏 ──
col_set = st.columns([8, 1])[1]
with col_set:
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if st.button("设置" if not st.session_state.show_settings else "关闭", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings
        st.rerun()

if st.session_state.show_settings:
    with st.container(border=True):
        st.markdown("#### 系统设置")
        c1, c2 = st.columns(2)
        with c1:
            lang = st.selectbox("语言 / Language", ["中文", "English"], index=0 if st.session_state.lang=="zh" else 1)
            new_lang = "zh" if lang == "中文" else "en"
            if new_lang != st.session_state.lang:
                st.session_state.lang = new_lang
                st.rerun()
        st.divider()
        st.caption("图片设置")
        c3, c4, c5 = st.columns(3)
        for col, key, label in [(c3,"banner","顶部横幅"),(c4,"sidebar","侧边栏"),(c5,"footer","底部")]:
            with col:
                new_url = st.text_input(label, st.session_state[f"img_{key}"], key=f"set_{key}")
                if new_url != st.session_state[f"img_{key}"]:
                    st.session_state[f"img_{key}"] = new_url
                    st.rerun()

page = st.session_state.nav
scorer = ProductScorer()
copy_gen = CopyGenerator()
intent_engine = IntentEngine()
sales_gen = SalesScriptGenerator()

# ── 工作台 ──
if page == "工作台":
    st.image(load_image("banner"), use_container_width=True)
    st.title(t("dashboard.title"))
    st.caption(t("app.caption"))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("dashboard.products"), "8")
    if st.session_state.scored:
        c2.metric(t("dashboard.recommend"), st.session_state.top_pick.product_name)
    else:
        c2.metric(t("dashboard.recommend"), t("dashboard.not_scored"))
    c3.metric(t("dashboard.stock"), "0")
    c4.metric(t("dashboard.status"), t("dashboard.ready"))

    if st.session_state.scored:
        results = scorer.rank(st.session_state.products)
        st.subheader(t("global.progress"))
        chart_data = pd.DataFrame({r.product_name: [r.final_score, r.margin_score, r.competition_score, r.trend_score, r.repurchase_score] for r in results},
                                  index=["Score","Margin","Competition","Trend","Repurchase"]).T
        st.bar_chart(chart_data, use_container_width=True)
    else:
        for btn, nav_key in [(t("dashboard.scoring_btn"),"选品评分"),(t("dashboard.pricing_btn"),"定价模型"),(t("dashboard.inventory_btn"),"库存监控")]:
            if st.button(btn):
                st.session_state.nav = nav_key
                st.rerun()

# ── 选品评分 ──
elif page == "选品评分":
    st.title(t("scoring.title"))
    st.caption(t("scoring.caption"))

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("scoring.trend"), "Up", "+22%")
        c2.metric(t("scoring.competition"), "Medium")
        c3.metric(t("scoring.margin"), "55-70%")
        c4.metric(t("scoring.repurchase"), "2-3/yr")

    st.subheader(t("scoring.products"))
    for i, p in enumerate(st.session_state.products):
        label = f"{p['name']} — ¥{p['price']} | ¥{p['cost']} | {p['competitors']} rivals"
        with st.expander(label):
            c1, c2, c3 = st.columns(3)

            with c1:
                ps = scorer.evaluate(p)
                score_data = pd.DataFrame({"Dimension":["Margin","Competition","Trend","Repurchase","Score"],
                                           "Score":[ps.margin_score,ps.competition_score,ps.trend_score,ps.repurchase_score,ps.final_score]})
                st.bar_chart(score_data.set_index("Dimension"), use_container_width=True)

            with c2:
                style = st.selectbox(t("scoring.copy_style"), ["seo","social","sales"], key=f"style_{i}", label_visibility="collapsed")
                if st.button(t("scoring.gen_copy"), key=f"gen_{i}"):
                    with st.spinner("..."):
                        copy = copy_gen.stream_generate(p, style)
                        placeholder = st.empty()
                        result = ""
                        for chunk in copy:
                            result += chunk
                            placeholder.markdown(result)

                script = sales_gen.full_script(p)
                with st.expander(t("scoring.sales_script")):
                    st.markdown(script["开场"])
                    st.markdown(script["异议处理"])
                    st.markdown(script["促单结束"])

            with c3:
                matches = intent_engine.match(p)
                match_data = pd.DataFrame([{"Profile":m["profile"],"Score":m["score"],"Level":m["match_level"]} for m in matches[:3]])
                st.dataframe(match_data, use_container_width=True, hide_index=True)
                best = intent_engine.best_angle(p)
                st.caption(f"{best['angle']}: {best['pitch']}")

    if st.button(t("global.batch"), type="primary"):
        results = scorer.rank(st.session_state.products)
        st.session_state.scored = True
        st.session_state.top_pick = results[0]
        result_data = pd.DataFrame([{"Product":r.product_name,"Score":r.final_score,"Margin":r.margin_score,"Comp":r.competition_score,"Trend":r.trend_score,"Repur":r.repurchase_score} for r in results])
        col1, col2 = st.columns([2,1])
        col1.dataframe(result_data, use_container_width=True, hide_index=True,
                       column_config={"Score": st.column_config.ProgressColumn(format="%.1f",min_value=0,max_value=100)})
        col2.bar_chart(result_data.set_index("Product")["Score"], use_container_width=True)

# ── 定价模型 ──
elif page == "定价模型":
    st.title(t("pricing.title"))
    st.caption(t("pricing.caption"))

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            raw = st.number_input(t("pricing.raw"), value=2.80, step=0.10, format="%.2f")
            proc = st.number_input(t("pricing.process"), value=1.20, step=0.10, format="%.2f")
        with c2:
            pack = st.number_input(t("pricing.pack"), value=0.50, step=0.10, format="%.2f")
            ship = st.number_input(t("pricing.ship"), value=1.50, step=0.10, format="%.2f")
        with c3:
            plat = st.number_input(t("pricing.plat"), value=0.85, step=0.10, format="%.2f")
            target = st.slider(t("pricing.target"), 0.20, 0.70, 0.45, 0.05, format="%.0f%%")

    if st.button(t("pricing.calc"), type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                cost_data = pd.DataFrame({"Item":["Raw","Proc","Pack","Ship","Plat"],"Amount":[raw,proc,pack,ship,plat]})
                st.bar_chart(cost_data.set_index("Item"), use_container_width=True)
        with col2:
            with st.container(border=True):
                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("pricing.total"), f"¥{result['total_cost']:.2f}")
                m2.metric(t("pricing.suggested"), f"¥{result['suggested_price']:.2f}")
                m3.metric(t("pricing.profit"), f"¥{result['profit']:.2f}")
                m4.metric(t("pricing.rate"), f"{result['margin_rate']:.1%}",
                         delta=t("pricing.pass") if result['above_redline'] else t("pricing.fail"),
                         delta_color="normal" if result['above_redline'] else "inverse")
        with st.container(border=True):
            st.subheader(t("pricing.sim"))
            sim = model.profit_simulate(cost, (result['min_price'], result['suggested_price']*1.3))
            sim_data = pd.DataFrame([{"Price":s['price'],"Profit":s['profit']} for s in sim])
            st.line_chart(sim_data.set_index("Price"), use_container_width=True)

# ── 库存监控 ──
elif page == "库存监控":
    st.title(t("inventory.title"))
    st.caption(t("inventory.caption"))

    is_en = st.session_state.lang == "en"
    names_zh = ["刻字狗牌","发光项圈","珐琅名牌","牵引绳套装","换牙零食"]
    names_en = ["Dog Tag","LED Collar","Enamel Plate","Leash Set","Snack"]

    inv_data = [
        InventoryStatus(names_en[0] if is_en else names_zh[0],45,8.5,3),
        InventoryStatus(names_en[1] if is_en else names_zh[1],12,6.2,5),
        InventoryStatus(names_en[2] if is_en else names_zh[2],120,3.1,3),
        InventoryStatus(names_en[3] if is_en else names_zh[3],0,4.0,4),
        InventoryStatus(names_en[4] if is_en else names_zh[4],8,15.0,2),
    ]

    rows = [{
        "Product": i.product_name, "Stock": i.current_stock,
        "Daily": f"{i.daily_sales:.1f}", "Turnover": f"{i.turnover_days}d",
        "Safety": i.safety_stock, "Reorder": i.reorder_quantity, "Status": i.status
    } for i in inv_data]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader(t("inventory.stock_dist"))
    st.bar_chart(pd.DataFrame({i.product_name: [i.current_stock] for i in inv_data}, index=["Stock"]).T, use_container_width=True)

    st.subheader(t("inventory.advice"))
    for inv in inv_data:
        if inv.current_stock == 0:
            with st.container(border=True):
                st.error(f"{inv.product_name} — {'Out of Stock' if is_en else '缺货'} — {'Reorder' if is_en else '建议补货'} {inv.reorder_quantity} {'units' if is_en else '件'} ({inv.lead_days}{'d' if is_en else '天到'})")
        elif inv.turnover_days < 3:
            with st.container(border=True):
                st.warning(f"{inv.product_name} — {'Low Stock' if is_en else '仅剩'} {inv.turnover_days}{'d' if is_en else '天'} — {'Reorder' if is_en else '补货'} {inv.reorder_quantity} {'units' if is_en else '件'}")
        elif inv.turnover_days > 30:
            with st.container(border=True):
                st.info(f"{inv.product_name} — {'Overstocked' if is_en else '积压'} {inv.turnover_days}{'d' if is_en else '天'} — {'Clearance suggested' if is_en else '建议清仓'}")
        else:
            with st.container(border=True):
                st.success(f"{inv.product_name} — {'Normal' if is_en else '正常'} ({inv.turnover_days}{'d' if is_en else '天'} — {inv.current_stock} {'in stock' if is_en else '库存'})")

st.divider()
st.image(load_image("footer"), use_container_width=True)
