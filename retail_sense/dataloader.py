"""
RetailSense — 数据加载器
支持手动数据 或 接入外部公司库存（多公司切换）
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timedelta

# 公司数据目录：优先使用本地 data/ 目录，兼容 Desktop 旧路径
_LEGACY_DIR = os.path.expanduser("~/Desktop/宠物饰品公司案例")
_PROJECT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
COMPANIES_DIR = _PROJECT_DIR if os.path.isdir(_PROJECT_DIR) else _LEGACY_DIR
DEFAULT_COMPANY = "萌爪宠物用品.json"

# 发现所有可用公司
def list_companies() -> list[str]:
    """列出所有可用公司文件"""
    if not os.path.exists(COMPANIES_DIR):
        return []
    files = sorted([f for f in os.listdir(COMPANIES_DIR) if f.endswith('.json')])
    return files

def load_company_data(company_file: str = None) -> dict | None:
    """加载公司库存数据"""
    path = os.path.join(COMPANIES_DIR, company_file or DEFAULT_COMPANY)
    if os.path.exists(path):
        with open(path) as f:
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

def daily_summary(transactions: list[dict], days: int = 1, reference_date: str = None) -> dict:
    """汇总交易数据 — 按天/周/月聚合营收。

    Args:
        transactions: 交易记录列表
        days: 统计天数（1=今日/最新交易日, 7=周, 30=月）
        reference_date: 参考日期；为 None 时自动取最新交易日期（days=1）/当前日期（days>1）
    """
    if not transactions:
        return {
            "revenue": 0, "orders": 0, "out_qty": 0,
            "cost": 0, "in_qty": 0, "profit": 0, "margin": 0,
        }
    # "今日" = 最新交易日，非系统日期
    if days == 1 and reference_date is None:
        reference_date = max(t["date"] for t in transactions)
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    ref_dt = datetime.strptime(reference_date, "%Y-%m-%d")
    since = (ref_dt - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    filtered = [t for t in transactions if since <= t["date"] <= reference_date]
    out_total = sum(t["revenue"] for t in filtered if t["type"] == "out")
    out_qty = sum(t["qty"] for t in filtered if t["type"] == "out")
    in_total = sum(abs(t["revenue"]) for t in filtered if t["type"] == "in")
    order_count = len([t for t in filtered if t["type"] == "out"])
    return {
        "revenue": out_total,
        "orders": order_count,
        "out_qty": out_qty,
        "cost": in_total,
        "in_qty": sum(t["qty"] for t in filtered if t["type"] == "in"),
        "profit": out_total - in_total,
        "margin": (out_total - in_total) / out_total if out_total > 0 else 0,
    }

def inventory_value_summary(inventory: list[dict]) -> dict:
    total_value = sum(i["qty"] * i["cost"] for i in inventory)
    total_retail = sum(i["qty"] * i["price"] for i in inventory)
    total_qty = sum(i["qty"] for i in inventory)
    low_stock = [i for i in inventory if i["qty"] < i.get("daily_avg",1) * 7]
    out_of_stock = [i for i in inventory if i["qty"] == 0]
    return {
        "total_qty": total_qty,
        "total_value": total_value,
        "total_retail": total_retail,
        "skus": len(inventory),
        "low_stock": len(low_stock),
        "out_of_stock": len(out_of_stock),
    }
