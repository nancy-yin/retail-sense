"""
RetailSense — 数据持久化模块 / Data Persistence Module
========================================================
将配货记录、上架记录等 session_state 数据持久化到 .auth/ 目录下的 JSON 文件。
刷新页面或切换公司不丢失数据。

Persists allocation records, listing records, and other session_state data
to JSON files under .auth/ directory. Survives page refresh and company switch.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime

# ── 文件路径 / File Paths ──
AUTH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".auth")
ALLOCATION_LOG_PATH = os.path.join(AUTH_DIR, "allocation_log.json")
LISTING_LOG_PATH = os.path.join(AUTH_DIR, "listing_log.json")


def _ensure_dir():
    """确保 .auth 目录存在 / Ensure .auth directory exists"""
    os.makedirs(AUTH_DIR, exist_ok=True)
    os.chmod(AUTH_DIR, 0o700)


# ═══════════════════════════════════════════════════════════
# 配货记录持久化 / Allocation Log Persistence
# ═══════════════════════════════════════════════════════════

def save_allocation_log(
    company_file: str,
    alloc_results: dict,
    waybill_cache: dict,
    ship_timestamps: dict,
) -> None:
    """保存配货记录到文件 / Save allocation records to file

    Args:
        company_file: 公司文件名（如 "萌爪宠物用品.json"）/ Company file name
        alloc_results: {order_id: allocation_result}
        waybill_cache: {order_id: waybill_no}
        ship_timestamps: {order_id: ISO datetime string}
    """
    _ensure_dir()
    all_data = _load_json(ALLOCATION_LOG_PATH) or {}

    # 将 set 转为 list 以便 JSON 序列化
    # Convert set to list for JSON serialization
    serializable_alloc = {}
    for oid, result in alloc_results.items():
        serializable_alloc[oid] = result

    all_data[company_file] = {
        "alloc_results": serializable_alloc,
        "waybill_cache": dict(waybill_cache),
        "ship_timestamps": dict(ship_timestamps),
        "updated_at": datetime.now().isoformat(),
    }

    _save_json(ALLOCATION_LOG_PATH, all_data)


def load_allocation_log(company_file: str) -> dict | None:
    """从文件加载配货记录 / Load allocation records from file

    Args:
        company_file: 公司文件名 / Company file name

    Returns:
        {"alloc_results": {...}, "waybill_cache": {...}, "ship_timestamps": {...}}
        or None if no records found
    """
    _ensure_dir()
    all_data = _load_json(ALLOCATION_LOG_PATH) or {}
    return all_data.get(company_file)


# ═══════════════════════════════════════════════════════════
# 上架记录持久化 / Listing Log Persistence
# ═══════════════════════════════════════════════════════════

def save_listing_log(
    company_file: str,
    listing_records: list[dict],
    listing_product_status: dict[str, str],
) -> None:
    """保存上架记录到文件 / Save listing records to file

    Args:
        company_file: 公司文件名 / Company file name
        listing_records: 上架记录列表 / List of listing records
        listing_product_status: {product_name: "待上架" | "已上架"}
    """
    _ensure_dir()
    all_data = _load_json(LISTING_LOG_PATH) or {}

    all_data[company_file] = {
        "listing_records": listing_records,
        "listing_product_status": dict(listing_product_status),
        "updated_at": datetime.now().isoformat(),
    }

    _save_json(LISTING_LOG_PATH, all_data)


def load_listing_log(company_file: str) -> dict | None:
    """从文件加载上架记录 / Load listing records from file

    Args:
        company_file: 公司文件名 / Company file name

    Returns:
        {"listing_records": [...], "listing_product_status": {...}}
        or None if no records found
    """
    _ensure_dir()
    all_data = _load_json(LISTING_LOG_PATH) or {}
    return all_data.get(company_file)


# ═══════════════════════════════════════════════════════════
# 通用 JSON 读写工具 / Generic JSON I/O Helpers
# ═══════════════════════════════════════════════════════════

def _load_json(path: str) -> dict | None:
    """加载 JSON 文件（容错）/ Load JSON file (fault-tolerant)"""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _save_json(path: str, data: dict) -> None:
    """原子保存 JSON 文件并限制文件权限 / Atomically save with private permissions"""
    _ensure_dir()
    file_descriptor, temp_path = tempfile.mkstemp(dir=AUTH_DIR, prefix=".tmp-")
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2, default=str)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise
