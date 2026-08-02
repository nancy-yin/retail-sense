"""
RetailSense — 数据加载器
支持手动数据 或 接入外部公司库存
"""
import json
import os
from datetime import datetime, timedelta

COMPANY_PATH = os.path.expanduser("~/Desktop/示例宠物用品公司/inventory.json")


def load_company_data(path: str = None) -> dict | None:
    """加载公司库存数据"""
    path = path or COMPANY_PATH
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def get_inventory(data: dict, use_company: bool = True) -> list[dict]:
    """获取库存列表"""
    if use_company and data:
        return data.get("inventory", [])
    return []


def get_transactions(data: dict, use_company: bool = True) -> list[dict]:
    """获取交易记录"""
    if use_company and data:
        return data.get("transactions", [])
    return []


def daily_summary(transactions: list[dict], days: int = 1) -> dict:
    """计算日/周/月汇总"""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    filtered = [t for t in transactions if t["date"] >= since]

    out_total = sum(t["revenue"] for t in filtered if t["type"] == "out")
    out_qty = sum(t["qty"] for t in filtered if t["type"] == "out")
    in_total = sum(abs(t["revenue"]) for t in filtered if t["type"] == "in")
    in_qty = sum(t["qty"] for t in filtered if t["type"] == "in")
    order_count = len([t for t in filtered if t["type"] == "out"])

    return {
        "revenue": out_total,
        "orders": order_count,
        "out_qty": out_qty,
        "cost": in_total,
        "in_qty": in_qty,
        "profit": out_total - in_total,
        "margin": (out_total - in_total) / out_total if out_total > 0 else 0,
    }


def inventory_value_summary(inventory: list[dict]) -> dict:
    """库存价值汇总"""
    total_value = sum(i["qty"] * i["cost"] for i in inventory)
    total_retail = sum(i["qty"] * i["price"] for i in inventory)
    total_qty = sum(i["qty"] for i in inventory)
    low_stock = [i for i in inventory if i["qty"] < i["daily_avg"] * 7]
    out_of_stock = [i for i in inventory if i["qty"] == 0]

    return {
        "total_qty": total_qty,
        "total_value": total_value,
        "total_retail": total_retail,
        "skus": len(inventory),
        "low_stock": len(low_stock),
        "out_of_stock": len(out_of_stock),
    }
