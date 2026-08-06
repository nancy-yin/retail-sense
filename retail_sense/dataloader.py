"""
RetailSense — 数据加载器
支持手动数据 或 接入外部公司库存（多公司切换）
"""
import json
import os
from datetime import datetime, timedelta

COMPANIES_DIR = os.path.expanduser("~/Desktop/宠物饰品公司案例")
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

def daily_summary(transactions: list[dict], days: int = 1) -> dict:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filtered = [t for t in transactions if t["date"] >= since]
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
