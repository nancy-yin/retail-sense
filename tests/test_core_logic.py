import math

import pytest

from retail_sense.agents import SalesPipeline
from retail_sense.cases import get_cases
from retail_sense.dataloader import (
    daily_summary,
    inventory_item_summary,
    inventory_value_summary,
    list_companies,
    load_company_data,
)
from retail_sense.pricing import CostBreakdown, PricingModel
from retail_sense.scorer import ProductScore, ProductScorer


def test_pricing_includes_every_cost_and_meets_margin_after_cent_rounding():
    cost = CostBreakdown(2.80, 1.20, 0.50, 1.50, 0.85)
    result = PricingModel(0.28).suggest_price(cost, 0.45)

    assert result["total_cost"] == 6.85
    assert result["suggested_price"] == 12.46
    assert result["min_price"] == 9.52
    assert result["profit"] == 5.61
    assert result["margin_rate"] >= 0.45
    min_margin = (result["min_price"] - result["total_cost"]) / result["min_price"]
    assert min_margin >= 0.28


@pytest.mark.parametrize("margin", [-0.01, 1, 1.2])
def test_pricing_rejects_invalid_margin(margin):
    with pytest.raises(ValueError):
        PricingModel().suggest_price(CostBreakdown(1), margin)


def test_daily_summary_uses_cogs_not_purchase_spend_and_latest_date_anchor():
    inventory = [{"sku": "A", "name": "商品A", "cost": 4}]
    transactions = [
        {"date": "2024-01-01", "type": "in", "sku": "A", "qty": 20, "revenue": -80},
        {"date": "2024-01-06", "type": "out", "sku": "A", "qty": 2, "revenue": 20},
        {"date": "2024-01-07", "type": "out", "sku": "A", "qty": 3, "revenue": 30},
    ]

    week = daily_summary(transactions, 7, inventory=inventory)
    day = daily_summary(transactions, 1, inventory=inventory)

    assert week["revenue"] == 50
    assert week["cost"] == 20
    assert week["purchase_spend"] == 80
    assert week["profit"] == 30
    assert math.isclose(week["margin"], 0.6)
    assert day["revenue"] == 30
    assert day["cost"] == 12


def test_inventory_statuses_are_disjoint_and_use_reorder_point():
    inventory = [
        {"name": "断货", "qty": 0, "cost": 1, "price": 2, "daily_avg": 5, "lead_days": 3},
        {"name": "低库存", "qty": 30, "cost": 1, "price": 2, "daily_avg": 5, "lead_days": 3},
        {"name": "需补货", "qty": 49, "cost": 1, "price": 2, "daily_avg": 5, "lead_days": 3},
        {"name": "正常", "qty": 50, "cost": 1, "price": 2, "daily_avg": 5, "lead_days": 3},
    ]

    item = inventory_item_summary(inventory[2])
    summary = inventory_value_summary(inventory)

    assert item["safety_stock"] == 35
    assert item["reorder_point"] == 50
    assert item["reorder_quantity"] == 5
    assert item["status"] == "建议补货"
    assert summary["out_of_stock"] == 1
    assert summary["low_stock"] == 1
    assert summary["reorder_needed"] == 1
    assert summary["normal"] == 1
    assert sum(summary[key] for key in ("out_of_stock", "low_stock", "reorder_needed", "normal")) == summary["skus"]


def test_scoring_is_clamped_and_declining_trend_never_exceeds_range():
    score = ProductScore("异常输入", 200, 200, 200, 200)
    scorer = ProductScorer()

    assert score.final_score == 100
    assert scorer.score_trend(100, False) == 50
    assert scorer.score_trend(-100, False) == 0


def test_virtual_company_files_are_discoverable_and_traversal_is_rejected():
    companies = list_companies()

    assert len(companies) == 3
    assert all(load_company_data(filename) for filename in companies)
    assert load_company_data("../README.md") is None
    assert all(case.get("is_virtual") is True for case in get_cases())


def test_pipeline_uses_all_in_cost_and_handles_zero_daily_sales():
    product = {
        "name": "测试商品", "cost": 2.8, "price": 12.99,
        "competitors": 5, "search_growth": 20, "trend_up": True,
        "annual_purchases": 2, "is_consumable": False,
        "qty": 10, "daily_avg": 0,
    }

    state = SalesPipeline().run([product])

    assert state.priced[0]["cost"] == 5.65
    assert any("无日均销量" in issue for issue in state.monitor[0]["issues"])
