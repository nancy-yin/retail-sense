"""
RetailSense — 数据加载器
支持手动数据 或 接入外部公司库存（多公司切换）
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

from retail_sense.inventory import InventoryStatus

# 虚拟公司数据目录：只读取仓库内的演示数据，避免依赖本机桌面路径。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_PROJECT_DIR = os.path.join(_PROJECT_ROOT, "data")
_PROJECT_CASE_DIR = os.path.join(_PROJECT_ROOT, "宠物饰品公司案例")


def _find_companies_dir() -> str:
    for candidate in (_PROJECT_DIR, _PROJECT_CASE_DIR):
        if os.path.isdir(candidate) and any(
            name.endswith(".json") for name in os.listdir(candidate)
        ):
            return candidate
    return _PROJECT_DIR


COMPANIES_DIR = _find_companies_dir()
DEFAULT_COMPANY = "萌爪宠物用品.json"

# 发现所有可用公司
def list_companies() -> list[str]:
    """列出所有可用公司文件"""
    if not os.path.exists(COMPANIES_DIR):
        return []
    files = sorted([f for f in os.listdir(COMPANIES_DIR) if f.endswith('.json')])
    return files

def load_company_data(company_file: str | None = None) -> dict | None:
    """加载虚拟公司库存数据。只允许读取已发现的 JSON 文件。"""
    filename = company_file or DEFAULT_COMPANY
    if filename not in list_companies():
        return None
    path = os.path.join(COMPANIES_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None

def get_inventory(data: dict, use_company: bool = True) -> list[dict]:
    if use_company and data:
        return data.get("inventory", [])
    return []

def get_transactions(data: dict, use_company: bool = True) -> list[dict]:
    if use_company and data:
        return data.get("transactions", [])
    return []


def get_demo_transactions() -> list[dict]:
    """生成示例交易数据（日期基于当前日期，用于无公司接入时的展示）"""
    now = datetime.now()
    dates = [(now - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(30, -1, -1)]
    import random
    rng = random.Random(42)  # 固定种子保证可重现

    products = [
        ("BP-001", "刻字狗牌", 12.99), ("BP-002", "发光项圈", 24.99),
        ("BP-003", "珐琅名牌", 16.99), ("BP-004", "牵引绳套装", 22.99),
        ("BP-005", "换牙零食", 11.99), ("BP-006", "亚克力牌", 8.99),
        ("BP-007", "宠物领结", 9.99),
    ]
    txns = []
    for date in dates:
        # 每天 1-4 笔出货
        for _ in range(rng.randint(1, 4)):
            sku, name, price = rng.choice(products)
            qty = rng.randint(1, 8)
            txns.append({
                "date": date, "type": "out", "sku": sku,
                "product": name, "qty": qty, "revenue": round(qty * price, 2),
            })
        # 偶尔入库
        if rng.random() < 0.15:
            sku, name, _ = rng.choice(products)
            txns.append({
                "date": date, "type": "in", "sku": sku,
                "product": name, "qty": rng.randint(20, 100), "revenue": 0,
            })
    return txns


def get_demo_inventory() -> list[dict]:
    """生成示例库存数据（用于无公司接入时的展示）"""
    return [
        {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag",
         "qty": 45, "cost": 2.80, "price": 12.99, "daily_avg": 9, "lead_days": 3},
        {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar",
         "qty": 12, "cost": 5.50, "price": 24.99, "daily_avg": 6, "lead_days": 5},
        {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate",
         "qty": 120, "cost": 3.20, "price": 16.99, "daily_avg": 3, "lead_days": 3},
        {"sku": "BP-004", "name": "牵引绳套装", "name_en": "Leash Set",
         "qty": 0, "cost": 4.50, "price": 22.99, "daily_avg": 4, "lead_days": 4},
        {"sku": "BP-005", "name": "换牙零食", "name_en": "Teething Treats",
         "qty": 8, "cost": 3.00, "price": 11.99, "daily_avg": 15, "lead_days": 2},
        {"sku": "BP-006", "name": "亚克力牌", "name_en": "Acrylic Tag",
         "qty": 200, "cost": 1.20, "price": 8.99, "daily_avg": 20, "lead_days": 2},
        {"sku": "BP-007", "name": "宠物领结", "name_en": "Pet Bow Tie",
         "qty": 55, "cost": 1.50, "price": 9.99, "daily_avg": 7, "lead_days": 3},
    ]

def inventory_item_summary(item: dict) -> dict:
    """使用同一库存模型计算单个 SKU 的状态与补货建议。"""
    status = InventoryStatus(
        product_name=item.get("name", item.get("sku", "")),
        current_stock=int(item.get("qty", 0)),
        daily_sales=float(item.get("daily_avg", 0)),
        lead_days=int(item.get("lead_days", 3)),
        safety_days=int(item.get("safety_days", 7)),
    )
    return {
        "turnover_days": status.turnover_days,
        "safety_stock": status.safety_stock,
        "reorder_point": status.reorder_point,
        "reorder_quantity": status.reorder_quantity,
        "status": status.status,
    }


def daily_summary(
    transactions: list[dict],
    days: int = 1,
    reference_date: str | None = None,
    inventory: list[dict] | None = None,
) -> dict:
    """汇总交易数据 — 按天/周/月聚合营收。

    Args:
        transactions: 交易记录列表
        days: 统计天数（1=今日/最新交易日, 7=周, 30=月）
        reference_date: 参考日期；为 None 时自动取最新交易日期
        inventory: 库存列表；用于按 SKU/商品名匹配单位成本并计算销售成本
    """
    if days < 1:
        raise ValueError("统计天数必须至少为 1")
    if not transactions:
        return {
            "revenue": 0, "orders": 0, "out_qty": 0,
            "cost": 0, "purchase_spend": 0, "in_qty": 0,
            "profit": 0, "margin": 0,
        }
    # 虚拟数据统一以最新交易日为统计锚点，避免历史数据的周/月汇总变成 0。
    if reference_date is None:
        reference_date = max(t["date"] for t in transactions)

    ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
    since = (ref_dt - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    filtered = [t for t in transactions if since <= t["date"] <= reference_date]
    outbound = [t for t in filtered if t.get("type") == "out"]
    inbound = [t for t in filtered if t.get("type") == "in"]
    out_total = sum(float(t.get("revenue", 0)) for t in outbound)
    out_qty = sum(t.get("qty", 0) for t in outbound)
    purchase_spend = sum(abs(float(t.get("revenue", 0))) for t in inbound)

    cost_by_sku = {}
    cost_by_name = {}
    for item in inventory or []:
        unit_cost = float(item.get("cost", 0))
        if item.get("sku"):
            cost_by_sku[item["sku"]] = unit_cost
        if item.get("name"):
            cost_by_name[item["name"]] = unit_cost

    cost_of_goods = 0.0
    for transaction in outbound:
        unit_cost = transaction.get("unit_cost", transaction.get("cost"))
        if unit_cost is None:
            unit_cost = cost_by_sku.get(
                transaction.get("sku"),
                cost_by_name.get(transaction.get("product"), 0),
            )
        cost_of_goods += float(transaction.get("qty", 0)) * float(unit_cost)

    profit = out_total - cost_of_goods
    return {
        "revenue": out_total,
        "orders": len(outbound),
        "out_qty": out_qty,
        "cost": cost_of_goods,
        "purchase_spend": purchase_spend,
        "in_qty": sum(t.get("qty", 0) for t in inbound),
        "profit": profit,
        "margin": profit / out_total if out_total > 0 else 0,
    }

def inventory_value_summary(inventory: list[dict]) -> dict:
    total_value = sum(float(i.get("qty", 0)) * float(i.get("cost", 0)) for i in inventory)
    total_retail = sum(float(i.get("qty", 0)) * float(i.get("price", 0)) for i in inventory)
    total_qty = sum(int(i.get("qty", 0)) for i in inventory)
    statuses = [inventory_item_summary(item)["status"] for item in inventory]
    out_of_stock = statuses.count("断货")
    low_stock = statuses.count("低库存")
    reorder_needed = statuses.count("建议补货")
    normal = statuses.count("正常") + statuses.count("滞销")
    return {
        "total_qty": total_qty,
        "total_value": total_value,
        "total_retail": total_retail,
        "skus": len(inventory),
        "low_stock": low_stock,
        "reorder_needed": reorder_needed,
        "out_of_stock": out_of_stock,
        "normal": normal,
    }
