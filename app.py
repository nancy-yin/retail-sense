"""
RetailSense — Streamlit Web 面板
选品评分 + 定价模型 一站式操作
"""
import streamlit as st
from retail_sense.scorer import ProductScorer
from retail_sense.pricing import CostBreakdown, PricingModel

st.set_page_config(page_title="RetailSense 🛒", page_icon="🛒", layout="wide")

st.title("🛒 RetailSense — AI 零售选品与定价")
st.caption("从「凭感觉」到「看数据」")

tab1, tab2 = st.tabs(["🔍 选品评分", "💰 定价模型"])

# ─── 选品评分 ───
with tab1:
    st.header("产品选品评分")
    st.write("输入产品数据 → 多维加权评分 → 排名推荐")

    default_products = [
        {"name": "刻字狗牌（不锈钢）", "cost": 2.80, "price": 12.99, "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2.5, "is_consumable": False},
        {"name": "发光项圈", "cost": 5.50, "price": 24.99, "competitors": 28, "search_growth": 15, "trend_up": True, "annual_purchases": 1.5, "is_consumable": False},
        {"name": "宠物名牌（珐琅）", "cost": 3.20, "price": 16.99, "competitors": 18, "search_growth": 35, "trend_up": True, "annual_purchases": 2.0, "is_consumable": False},
        {"name": "换牙零食包", "cost": 3.00, "price": 11.99, "competitors": 30, "search_growth": 28, "trend_up": True, "annual_purchases": 8, "is_consumable": True},
    ]

    if st.button("🎯 开始评分", use_container_width=True):
        scorer = ProductScorer()
        results = scorer.rank(default_products)

        for i, r in enumerate(results, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            cols = st.columns([1, 3, 2, 2, 2, 2])
            cols[0].markdown(f"### {medal}")
            cols[1].markdown(f"**{r.product_name}**")
            cols[2].metric("总分", f"{r.final_score}")
            cols[3].metric("毛利", f"{r.margin_score}")
            cols[4].metric("竞争", f"{r.competition_score}")
            cols[5].metric("复购", f"{r.repurchase_score}")
            st.progress(r.final_score / 100)

# ─── 定价模型 ───
with tab2:
    st.header("定价模型")
    st.write("成本拆解 → 建议售价 → 利润模拟")

    col1, col2 = st.columns(2)
    with col1:
        raw = st.number_input("裸件成本 (¥)", value=2.80, step=0.10)
        proc = st.number_input("加工费 (¥)", value=1.20, step=0.10)
        pack = st.number_input("包装费 (¥)", value=0.50, step=0.10)
    with col2:
        ship = st.number_input("物流费 (¥)", value=1.50, step=0.10)
        plat = st.number_input("平台费 (¥)", value=0.85, step=0.10)
        target = st.slider("目标利润率", 0.25, 0.70, 0.45, 0.05)

    if st.button("💰 计算定价", use_container_width=True):
        cost = CostBreakdown(raw, proc, pack, ship, plat)
        model = PricingModel()
        result = model.suggest_price(cost, target)

        cols = st.columns(4)
        cols[0].metric("总成本", f"¥{result['total_cost']:.2f}")
        cols[1].metric("建议售价", f"¥{result['suggested_price']:.2f}")
        cols[2].metric("利润/件", f"¥{result['profit']:.2f}")
        cols[3].metric("利润率", f"{result['margin_rate']:.1%}")
        st.caption(cost.summary())

        if result['above_redline']:
            st.success("✅ 高于28%红线，可以上架")
        else:
            st.error("🔴 低于28%红线，建议提价或降成本")
