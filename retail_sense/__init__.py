"""AI 零售选品与库存决策系统"""
from .scorer import ProductScorer, ProductScore
from .pricing import CostBreakdown, PricingModel
from .inventory import InventoryStatus
from .copywriter import CopyGenerator
from .intent import IntentEngine
from .sales_script import SalesScriptGenerator

__all__ = [
    "ProductScorer", "ProductScore",
    "CostBreakdown", "PricingModel",
    "InventoryStatus",
    "CopyGenerator",
    "IntentEngine",
    "SalesScriptGenerator",
]
