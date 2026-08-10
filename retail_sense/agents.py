"""
RetailSense — 多智能体销售流程自动化
Scout → Price → Copy → Monitor 四Agent流水线
"""
from dataclasses import dataclass, field
from datetime import datetime

from .copywriter import CopyGenerator
from .intent import IntentEngine
from .inventory import InventoryStatus
from .pricing import CostBreakdown, PricingModel
from .sales_script import SalesScriptGenerator
from .scorer import ProductScorer


@dataclass
class WorkflowState:
    """工作流状态：Agent之间传递的上下文"""
    products: list[dict] = field(default_factory=list)
    scored: list = field(default_factory=list)
    priced: list[dict] = field(default_factory=list)
    copy: list[dict] = field(default_factory=list)
    monitor: list[dict] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    region: str = "北美"
    started_at: str = ""
    completed_at: str = ""

    def log(self, agent: str, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] [{agent}] {msg}")


class ScoutAgent:
    """选品侦察 Agent — 扫描产品池，多维评分排序"""

    def __init__(self):
        self.scorer = ProductScorer()

    def run(self, state: WorkflowState) -> WorkflowState:
        state.log("Scout", f"开始扫描 {len(state.products)} 个产品...")
        results = self.scorer.rank(state.products)
        state.scored = results
        state.log("Scout", f"评分完成，TOP3: {', '.join(r.product_name for r in results[:3])}")
        return state


class PriceAgent:
    """定价 Agent — 为选中产品计算最优售价"""

    def __init__(self):
        self.model = PricingModel()

    def run(self, state: WorkflowState, target_margin: float = 0.45) -> WorkflowState:
        if not state.scored:
            state.log("Price", "无评分数据，跳过定价")
            return state

        top = state.scored[:5]
        state.log("Price", f"为TOP{len(top)}产品计算定价（目标利润{target_margin:.0%}）...")

        for r in top:
            # 从原始数据找产品
            prod = next((p for p in state.products if p["name"] == r.product_name), None)
            if not prod:
                continue

            cost = CostBreakdown(
                prod["cost"],
                packaging=0.50,
                shipping=1.50,
                platform_fee=0.85,
            )
            result = self.model.suggest_price(cost, target_margin)

            state.priced.append({
                "name": r.product_name,
                "cost": result["total_cost"],
                "suggested_price": result["suggested_price"],
                "profit": result["profit"],
                "margin": result["margin_rate"],
                "above_redline": result["above_redline"],
            })
            state.log("Price", f"  {r.product_name}: ¥{result['suggested_price']:.2f} (利润率 {result['margin_rate']:.1%})")

        return state


class CopyAgent:
    """文案 Agent — 为定价后的产品生成营销内容"""

    def __init__(self):
        self.copywriter = CopyGenerator()
        self.intent = IntentEngine()
        self.script = SalesScriptGenerator()

    def run(self, state: WorkflowState) -> WorkflowState:
        if not state.priced:
            state.log("Copy", "无定价数据，跳过文案生成")
            return state

        state.log("Copy", f"为{len(state.priced)}个产品生成营销内容...")

        for item in state.priced:
            prod = next((p for p in state.products if p["name"] == item["name"]), {})
            seo = self.copywriter.generate(prod, "seo")
            social = self.copywriter.generate(prod, "social")
            angle = self.intent.best_angle(prod)
            script = self.script.full_script(prod)

            state.copy.append({
                "name": item["name"],
                "seo": seo,
                "social": social,
                "angle": angle,
                "script": script,
            })
            state.log("Copy", f"  {item['name']}: SEO+社交+话术 三件套完成")

        return state


class MonitorAgent:
    """监控 Agent — 巡检库存和销售异常"""

    def run(self, state: WorkflowState) -> WorkflowState:
        state.log("Monitor", "开始巡检库存与销售状态...")

        alerts = []
        for prod in state.products:
            issues = []
            # 从 data 中检查库存
            qty = prod.get("qty", prod.get("current_stock", 999))
            daily = prod.get("daily_avg", prod.get("daily_sales", 1))
            inventory_status = InventoryStatus(
                product_name=prod["name"],
                current_stock=int(qty),
                daily_sales=float(daily),
                lead_days=int(prod.get("lead_days", 3)),
            )

            if inventory_status.status == "断货":
                issues.append("断货！需立即补货")
            elif inventory_status.status in {"低库存", "建议补货"}:
                issues.append(
                    f"{inventory_status.status}（仅{qty}件，补货点"
                    f"{inventory_status.reorder_point}件）"
                )
            elif daily <= 0 and qty > 0:
                issues.append("无日均销量，暂不能计算周转")
            elif daily > 0 and qty > daily * 60:
                issues.append(f"库存积压（{qty}件，可支撑{int(qty/daily)}天）")

            # 检查定价是否合理
            priced_item = next((p for p in state.priced if p["name"] == prod["name"]), None)
            if priced_item and not priced_item["above_redline"]:
                issues.append("定价利润率不达标")

            if issues:
                alerts.append({"name": prod["name"], "issues": issues})

        state.monitor = alerts
        if alerts:
            state.log("Monitor", f"发现 {len(alerts)} 个产品异常")
            for a in alerts:
                state.log("Monitor", f"  {a['name']}: {'; '.join(a['issues'])}")
        else:
            state.log("Monitor", "所有产品状态正常")

        return state


class SalesPipeline:
    """销售流程编排器 — 串联四个Agent"""

    def __init__(self):
        self.scout = ScoutAgent()
        self.price = PriceAgent()
        self.copy = CopyAgent()
        self.monitor = MonitorAgent()

    def run(self, products: list[dict], target_margin: float = 0.45,
            region: str = "北美") -> WorkflowState:
        """执行完整销售流程"""
        state = WorkflowState(
            products=products,
            region=region,
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # Step 1: Scout
        state = self.scout.run(state)

        # Step 2: Price
        state = self.price.run(state, target_margin)

        # Step 3: Copy
        state = self.copy.run(state)

        # Step 4: Monitor
        state = self.monitor.run(state)

        state.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state.log("Pipeline", f"全流程完成，耗时4步，处理{len(products)}个产品")

        return state
