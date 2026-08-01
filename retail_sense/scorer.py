"""
RetailSense — 选品评分引擎
基于多维数据对候选产品进行综合评分。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProductScore:
    """产品评分结果"""
    product_name: str
    margin_score: float      # 毛利率得分 (0-100)
    competition_score: float  # 竞争度得分 (0-100，越高=竞争越低)
    trend_score: float        # 搜索趋势得分 (0-100)
    repurchase_score: float   # 复购率得分 (0-100)
    final_score: float = 0    # 加权总分

    def __post_init__(self):
        # 加权公式：毛利20% + 竞争度25% + 趋势25% + 复购30%
        # 复购权重最高——来自瑞幸经验：高复购 > 高毛利
        self.final_score = round(
            self.margin_score * 0.20 +
            self.competition_score * 0.25 +
            self.trend_score * 0.25 +
            self.repurchase_score * 0.30, 2
        )


class ProductScorer:
    """产品选品评分器"""

    def score_margin(self, cost: float, price: float) -> float:
        """毛利率得分：成本率越低分越高"""
        if price <= 0:
            return 0
        margin_rate = (price - cost) / price
        # 参考瑞幸28%红线：>30%就及格，>50%优秀
        if margin_rate >= 0.70: return 95
        if margin_rate >= 0.50: return 85
        if margin_rate >= 0.40: return 75
        if margin_rate >= 0.30: return 60
        if margin_rate >= 0.20: return 40
        return max(0, int(margin_rate * 100))

    def score_competition(self, competitor_count: int) -> float:
        """竞争度得分：竞品越少分越高"""
        if competitor_count == 0: return 100
        if competitor_count <= 5:  return 90
        if competitor_count <= 10: return 75
        if competitor_count <= 20: return 55
        if competitor_count <= 50: return 35
        return max(0, 100 - competitor_count)

    def score_trend(self, search_growth: float, is_up: bool) -> float:
        """搜索趋势得分：增长率越高越好"""
        if not is_up:
            return max(0, 50 + search_growth)  # 下降趋势最高50分
        if search_growth >= 50: return 95
        if search_growth >= 30: return 85
        if search_growth >= 15: return 70
        if search_growth >= 5:  return 55
        return 40

    def score_repurchase(self, annual_purchases: float, is_consumable: bool) -> float:
        """复购率得分：年购买次数越多分越高"""
        base = 40 if is_consumable else 25
        if annual_purchases >= 6:  return 95
        if annual_purchases >= 4:  return 85
        if annual_purchases >= 2:  return 70
        if annual_purchases >= 1:  return 55
        return base

    def evaluate(self, product: dict) -> ProductScore:
        """综合评估一个产品"""
        return ProductScore(
            product_name=product["name"],
            margin_score=self.score_margin(product["cost"], product["price"]),
            competition_score=self.score_competition(product.get("competitors", 10)),
            trend_score=self.score_trend(
                product.get("search_growth", 0),
                product.get("trend_up", True)
            ),
            repurchase_score=self.score_repurchase(
                product.get("annual_purchases", 1),
                product.get("is_consumable", False)
            ),
        )

    def rank(self, products: list[dict]) -> list[ProductScore]:
        """批量评估并排序"""
        scores = [self.evaluate(p) for p in products]
        return sorted(scores, key=lambda s: s.final_score, reverse=True)
