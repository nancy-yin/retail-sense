"""
RetailSense — AI 零售选品与库存决策系统
"""
import streamlit as st
import pandas as pd
from retail_sense.scorer import ProductScorer
from retail_sense.pricing import CostBreakdown, PricingModel
from retail_sense.inventory import InventoryStatus
from retail_sense.copywriter import CopyGenerator
from retail_sense.intent import IntentEngine
from retail_sense.sales_script import SalesScriptGenerator

st.set_page_config(page_title="RetailSense", page_icon=" ", layout="wide")

# ── 图片配置（支持本地路径 + URL）──
import os
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images")
DEFAULT_IMAGES = {
    "banner": os.path.join(IMAGE_DIR, "banner.jpg"),
    "sidebar": os.path.join(IMAGE_DIR, "sidebar.jpg"),
    "footer": os.path.join(IMAGE_DIR, "footer.jpg"),
}

def load_image(key):
    """加载图片：优先本地，回退URL"""
    path = st.session_state.get(f"img_{key}", DEFAULT_IMAGES[key])
    if os.path.exists(path):
        return path
    if path.startswith("http"):
        return path
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

# ── 侧边栏 ──
with st.sidebar:
    st.image(load_image("sidebar"), use_container_width=True)
    st.markdown("### RetailSense")

    for name in ["工作台","选品评分","定价模型","库存监控"]:
        kind = "primary" if st.session_state.nav == name else "secondary"
        if st.button(name, use_container_width=True, type=kind):
            st.session_state.nav = name
            st.rerun()

    st.divider()
    with st.expander("图片设置"):
        for key, label in [("banner","顶部横幅"),("sidebar","侧边栏"),("footer","底部")]:
            new_url = st.text_input(label, st.session_state[f"img_{key}"], key=f"set_{key}")
            if new_url != st.session_state[f"img_{key}"]:
                st.session_state[f"img_{key}"] = new_url
                st.rerun()

    st.caption("v1.0 · MIT License")

page = st.session_state.nav
scorer = ProductScorer()
copy_gen = CopyGenerator()
intent_engine = IntentEngine()
sales_gen = SalesScriptGenerator()

# ── 工作台 ──
if page == "工作台":
    st.image(load_image("banner"), use_container_width=True)
    st.title("RetailSense")
    st.caption("AI 零售选品 · 定价 · 库存 · 多智能体销售自动化")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("评估产品", "8")
    if st.session_state.scored:
        c2.metric("首选推荐", st.session_state.top_pick.product_name, f"{st.session_state.top_pick.final_score}分")
    else:
        c2.metric("首选推荐", "——")
    c3.metric("库存预警", "0")
    c4.metric("系统状态", "就绪")

    if st.session_state.scored:
        results = scorer.rank(st.session_state.products)
        st.subheader("评分总览")
        chart_data = pd.DataFrame({r.product_name: [r.final_score, r.margin_score, r.competition_score, r.trend_score, r.repurchase_score] for r in results},
                                  index=["总分","毛利","竞争","趋势","复购"]).T
        st.bar_chart(chart_data, use_container_width=True)
    else:
        for name in ["选品评分","定价模型","库存监控"]:
            if st.button(name):
                st.session_state.nav = name
                st.rerun()

# ── 选品评分 ──
elif page == "选品评分":
    st.title("产品选品评分")

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("品类趋势", "上升", "+22%")
        c2.metric("竞争密度", "中等")
        c3.metric("利润空间", "55-70%")
        c4.metric("复购周期", "2-3次/年")

    # 产品表格 — 点击展开分析
    st.subheader("候选产品")
    for i, p in enumerate(st.session_state.products):
        with st.expander(f"{p['name']} — ¥{p['price']}  |  成本 ¥{p['cost']}  |  竞品 {p['competitors']} 个"):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**评分明细**")
                ps = scorer.evaluate(p)
                score_data = pd.DataFrame({
                    "维度": ["毛利率","竞争度","趋势","复购","总分"],
                    "得分": [ps.margin_score, ps.competition_score, ps.trend_score, ps.repurchase_score, ps.final_score]
                })
                st.bar_chart(score_data.set_index("维度"), use_container_width=True)

            with c2:
                st.markdown("**AI 文案生成**")
                style = st.selectbox("文案风格", ["seo","social","sales"], key=f"style_{i}", label_visibility="collapsed")
                if st.button("生成文案", key=f"gen_{i}"):
                    with st.spinner("生成中..."):
                        copy = copy_gen.stream_generate(p, style)
                        placeholder = st.empty()
                        result = ""
                        for chunk in copy:
                            result += chunk
                            placeholder.markdown(result)

                # 促单话术
                st.markdown("**促单话术**")
                script = sales_gen.full_script(p)
                with st.expander("查看话术"):
                    st.markdown(f"**开场**\n{script['开场']}")
                    st.markdown(f"**异议处理**\n{script['异议处理']}")
                    st.markdown(f"**促单**\n{script['促单结束']}")

            with c3:
                st.markdown("**客户意图分析**")
                matches = intent_engine.match(p)
                match_data = pd.DataFrame([{"画像": m["profile"], "匹配度": m["score"], "推荐": m["match_level"]} for m in matches[:3]])
                st.dataframe(match_data, use_container_width=True, hide_index=True)
                best = intent_engine.best_angle(p)
                st.markdown(f"**最佳角度**：{best['angle']}")
                st.caption(best['pitch'])

    st.divider()

    if st.button("批量评分排名", type="primary"):
        results = scorer.rank(st.session_state.products)
        st.session_state.scored = True
        st.session_state.top_pick = results[0]

        st.subheader("综合排名")
        result_data = pd.DataFrame([{
            "产品": r.product_name, "总分": r.final_score,
            "毛利": r.margin_score, "竞争": r.competition_score,
            "趋势": r.trend_score, "复购": r.repurchase_score
        } for r in results])

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(result_data, use_container_width=True, hide_index=True,
                         column_config={"总分": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100)})
        with col2:
            st.bar_chart(result_data.set_index("产品")["总分"], use_container_width=True)

# ── 定价模型 ──
elif page == "定价模型":
    st.title("定价模型")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            raw = st.number_input("裸件成本", value=2.80, step=0.10, format="%.2f")
            proc = st.number_input("加工费", value=1.20, step=0.10, format="%.2f")
        with c2:
            pack = st.number_input("包装费", value=0.50, step=0.10, format="%.2f")
            ship = st.number_input("物流费", value=1.50, step=0.10, format="%.2f")
        with c3:
            plat = st.number_input("平台费", value=0.85, step=0.10, format="%.2f")
            target = st.slider("目标利润率", 0.20, 0.70, 0.45, 0.05, format="%.0f%%")

    if st.button("计算", type="primary"):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)

        # 成本饼图
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.container(border=True):
                st.markdown("**成本结构**")
                cost_data = pd.DataFrame({
                    "项目": ["裸件","加工","包装","物流","平台"],
                    "金额": [raw, proc, pack, ship, plat]
                })
                st.bar_chart(cost_data.set_index("项目"), use_container_width=True)

        with col2:
            with st.container(border=True):
                st.markdown("**定价结果**")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("总成本", f"¥{result['total_cost']:.2f}")
                m2.metric("建议售价", f"¥{result['suggested_price']:.2f}")
                m3.metric("单件利润", f"¥{result['profit']:.2f}")
                m4.metric("利润率", f"{result['margin_rate']:.1%}",
                         delta="达标" if result['above_redline'] else "未达标")

        # 利润模拟线图
        with st.container(border=True):
            st.markdown("**利润模拟**")
            sim = model.profit_simulate(cost, (result['min_price'], result['suggested_price']*1.3))
            sim_data = pd.DataFrame([{"售价":s['price'],"利润":s['profit']} for s in sim])
            st.line_chart(sim_data.set_index("售价"), use_container_width=True)

# ── 库存监控 ──
elif page == "库存监控":
    st.title("库存监控")

    inv_data = [
        InventoryStatus("刻字狗牌",45,8.5,3), InventoryStatus("发光项圈",12,6.2,5),
        InventoryStatus("珐琅名牌",120,3.1,3), InventoryStatus("牵引绳套装",0,4.0,4),
        InventoryStatus("换牙零食",8,15.0,2),
    ]

    rows = [{"产品":i.product_name,"库存":i.current_stock,"日均":f"{i.daily_sales:.1f}","周转":f"{i.turnover_days}天","安全库存":i.safety_stock,"建议补":i.reorder_quantity,"状态":i.status} for i in inv_data]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 库存柱状图
    st.subheader("库存分布")
    chart_data = pd.DataFrame({i.product_name:[i.current_stock] for i in inv_data}, index=["库存"]).T
    st.bar_chart(chart_data, use_container_width=True)

    st.divider()
    st.subheader("建议")
    for inv in inv_data:
        if inv.current_stock == 0:
            with st.container(border=True):
                st.error(f"**{inv.product_name}** 断货 — 补 {inv.reorder_quantity} 件 ({inv.lead_days}天到)")
        elif inv.turnover_days < 3:
            with st.container(border=True):
                st.warning(f"**{inv.product_name}** 仅剩 {inv.turnover_days} 天 — 补 {inv.reorder_quantity} 件")
        elif inv.turnover_days > 30:
            with st.container(border=True):
                st.info(f"**{inv.product_name}** 积压 {inv.turnover_days} 天 — 建议清仓")

st.divider()
st.image(load_image("footer"), use_container_width=True)
