"""
测试选品评分引擎 — 用宠物饰品真实数据验证
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from retail_sense.scorer import ProductScorer


def test_scorer():
    scorer = ProductScorer()

    # 宠物饰品 8 SKU 数据
    pet_products = [
        {"name": "刻字狗牌（不锈钢）", "cost": 2.80, "price": 12.99, "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2.5, "is_consumable": False},
        {"name": "发光项圈", "cost": 5.50, "price": 24.99, "competitors": 28, "search_growth": 15, "trend_up": True, "annual_purchases": 1.5, "is_consumable": False},
        {"name": "宠物名牌（珐琅）", "cost": 3.20, "price": 16.99, "competitors": 18, "search_growth": 35, "trend_up": True, "annual_purchases": 2.0, "is_consumable": False},
        {"name": "牵引绳套装", "cost": 4.50, "price": 22.99, "competitors": 42, "search_growth": 8, "trend_up": True, "annual_purchases": 1.8, "is_consumable": False},
        {"name": "宠物领结", "cost": 1.50, "price": 9.99, "competitors": 55, "search_growth": -5, "trend_up": False, "annual_purchases": 3.0, "is_consumable": True},
        {"name": "身份牌（亚克力）", "cost": 1.20, "price": 8.99, "competitors": 22, "search_growth": 18, "trend_up": True, "annual_purchases": 2.0, "is_consumable": False},
        {"name": "宠物手链", "cost": 2.00, "price": 14.99, "competitors": 15, "search_growth": 42, "trend_up": True, "annual_purchases": 1.2, "is_consumable": False},
        {"name": "换牙零食包", "cost": 3.00, "price": 11.99, "competitors": 30, "search_growth": 28, "trend_up": True, "annual_purchases": 8, "is_consumable": True},
    ]

    results = scorer.rank(pet_products)

    print("🏆 宠物饰品选品评分排名")
    print("=" * 50)
    for i, r in enumerate(results, 1):
        bar = "█" * int(r.final_score / 5)
        print(f"{i:>2}. {r.product_name:<16} {r.final_score:>6.1f}分 {bar}")

    # 验证
    assert len(results) == 8, "应有8个产品"
    assert results[0].final_score >= results[-1].final_score, "第一名应 >= 最后一名"
    assert all(0 <= r.final_score <= 100 for r in results), "分数应在0-100之间"
    print("\n✅ 所有断言通过")

    return results


if __name__ == "__main__":
    test_scorer()
