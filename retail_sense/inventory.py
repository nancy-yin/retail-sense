"""
RetailSense — 库存预测
周转天数 + 补货建议 + 滞销预警
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class InventoryStatus:
    """库存状态"""
    product_name: str
    current_stock: int
    daily_sales: float         # 日均销量
    lead_days: int = 3         # 进货周期（天）
    safety_days: int = 7       # 安全库存天数
    last_sold: datetime | None = None  # 最后售出日期

    @property
    def turnover_days(self) -> float:
        """剩余周转天数"""
        if self.daily_sales <= 0:
            return float('inf')
        return round(self.current_stock / self.daily_sales, 1)

    @property
    def safety_stock(self) -> int:
        """安全库存量：日均销量 × 安全天数"""
        return max(1, round(self.daily_sales * self.safety_days))

    @property
    def reorder_point(self) -> int:
        """补货触发点：安全库存 + 进货周期内的销量"""
        return self.safety_stock + round(self.daily_sales * self.lead_days)

    @property
    def reorder_quantity(self) -> int:
        """建议补货量：补到触发点以上"""
        if self.current_stock >= self.reorder_point:
            return 0
        qty = self.reorder_point - self.current_stock
        return max(round(self.daily_sales), qty)  # 至少补1天销量

    @property
    def is_stale(self) -> bool:
        """是否滞销（30天未动销）"""
        if self.last_sold is None:
            return False
        return (datetime.now() - self.last_sold).days >= 30

    @property
    def status(self) -> str:
        if self.current_stock == 0:
            return "断货"
        if self.is_stale:
            return "滞销"
        if self.current_stock < self.safety_stock:
            return "低库存"
        if self.current_stock < self.reorder_point:
            return "建议补货"
        return "正常"

    def summary(self) -> str:
        lines = [
            f"📦 {self.product_name} {self.status}",
            f"   库存: {self.current_stock} | 日均销量: {self.daily_sales:.1f}",
            f"   周转: {self.turnover_days}天 | 安全库存: {self.safety_stock}",
            f"   补货触发: {self.reorder_point} | 建议补货: {self.reorder_quantity}",
        ]
        if self.is_stale:
            days = (datetime.now() - self.last_sold).days
            lines.append(f"   ⚠️ 已 {days} 天未动销")
        return "\n".join(lines)
