"""
RetailSense — 定价模型
成本红线 + 利润模拟 + 竞品比价
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CostBreakdown:
    """成本明细"""
    raw_material: float    # 裸件成本
    processing: float = 0  # 加工费（刻字等）
    packaging: float = 0   # 包装费
    shipping: float = 0    # 物流费
    platform_fee: float = 0  # 平台扣点（如 Etsy 6.5%）

    @property
    def total(self) -> float:
        return self.raw_material + self.processing + self.packaging + self.shipping

    @property
    def total_with_fees(self) -> float:
        return self.total + self.platform_fee

    def summary(self) -> str:
        parts = [
            f"裸件: ¥{self.raw_material:.2f}",
        ]
        if self.processing: parts.append(f"加工: ¥{self.processing:.2f}")
        if self.packaging: parts.append(f"包装: ¥{self.packaging:.2f}")
        if self.shipping: parts.append(f"物流: ¥{self.shipping:.2f}")
        parts.append(f"合计: ¥{self.total:.2f}")
        if self.platform_fee:
            parts.append(f"(平台费: ¥{self.platform_fee:.2f})")
        return " | ".join(parts)


class PricingModel:
    """定价模型 — 瑞幸成本率红线思维"""

    MIN_PROFIT_RATE = 0.28  # 最低利润率红线（致敬瑞幸28%）

    def __init__(self, min_profit_rate: float = 0.28):
        self.min_profit_rate = min_profit_rate

    def suggest_price(self, cost: CostBreakdown, target_margin: float = 0.45) -> dict:
        """
        根据成本和目标利润率建议售价。
        采用成本倍率法：建议售价 = 总成本 × (1 / (1 - 目标利润率))
        """
        total = cost.total
        suggested = round(total / (1 - target_margin), 2)
        min_price = round(total / (1 - self.min_profit_rate), 2)
        profit = round(suggested - total - cost.platform_fee, 2)
        actual_margin = round(profit / suggested, 4) if suggested > 0 else 0

        return {
            "cost_breakdown": cost.summary(),
            "total_cost": round(total, 2),
            "platform_fee": round(cost.platform_fee, 2),
            "min_price": min_price,
            "suggested_price": suggested,
            "profit": profit,
            "margin_rate": actual_margin,
            "above_redline": actual_margin >= self.min_profit_rate,
        }

    def profit_simulate(self, cost: CostBreakdown, price_range: tuple) -> list[dict]:
        """利润模拟：遍历不同售价看利润变化"""
        low, high = price_range
        results = []
        step = max(0.5, round((high - low) / 10, 2))
        price = low
        while price <= high:
            profit = round(price - cost.total - cost.platform_fee, 2)
            margin = round(profit / price, 4) if price > 0 else 0
            results.append({
                "price": price,
                "profit": profit,
                "margin": margin,
                "safe": margin >= self.min_profit_rate,
            })
            price = round(price + step, 2)
        return results

    def compare_competitors(self, my_price: float, my_cost: CostBreakdown,
                            competitors: list[dict]) -> list[dict]:
        """竞品比价分析"""
        my_profit = round(my_price - my_cost.total - my_cost.platform_fee, 2)
        results = []
        for comp in competitors:
            gap = round(my_price - comp["price"], 2)
            gap_pct = round(gap / comp["price"] * 100, 1) if comp["price"] > 0 else 0
            results.append({
                "name": comp["name"],
                "their_price": comp["price"],
                "gap": gap,
                "gap_pct": gap_pct,
                "position": "高于" if gap > 0 else ("低于" if gap < 0 else "持平"),
            })
        return results
