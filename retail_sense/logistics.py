"""
RetailSense — 物流配发模块 v1.0
Order Management + Smart Allocation + Logistics Tracking
"""

from __future__ import annotations
from datetime import datetime, timedelta
import random

random.seed(42)

# ── 模拟库存（含库位）──
def get_warehouse_inventory() -> list[dict]:
    """返回仓库库存，含库位标注"""
    return [
        {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag",
         "qty": 45, "location": "A-03-12", "zone": "A区"},
        {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar",
         "qty": 12, "location": "B-01-05", "zone": "B区"},
        {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate",
         "qty": 120, "location": "A-02-08", "zone": "A区"},
        {"sku": "BP-004", "name": "牵引绳套装", "name_en": "Leash Set",
         "qty": 0, "location": "C-01-03", "zone": "C区"},
        {"sku": "BP-005", "name": "换牙零食", "name_en": "Teething Treats",
         "qty": 8, "location": "D-02-01", "zone": "D区"},
        {"sku": "BP-006", "name": "宠物领结", "name_en": "Pet Bow Tie",
         "qty": 30, "location": "B-03-06", "zone": "B区"},
        {"sku": "BP-007", "name": "亚克力牌", "name_en": "Acrylic Tag",
         "qty": 55, "location": "A-01-04", "zone": "A区"},
        {"sku": "BP-008", "name": "宠物手链", "name_en": "Pet Bracelet",
         "qty": 18, "location": "C-02-02", "zone": "C区"},
    ]

# ── 模拟订单 ──
def get_mock_orders() -> list[dict]:
    """返回模拟订单列表"""
    now = datetime.now()
    return [
        {
            "order_id": "ORD-20260801-001",
            "customer": "张先生",
            "customer_en": "Mr. Zhang",
            "items": [
                {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag", "qty": 2},
                {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar", "qty": 1},
            ],
            "status": "pending",  # pending / picking / shipped
            "created_at": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": "北京市朝阳区望京SOHO T3-1208",
            "address_en": "Wangjing SOHO T3-1208, Chaoyang, Beijing",
        },
        {
            "order_id": "ORD-20260801-002",
            "customer": "李女士",
            "customer_en": "Ms. Li",
            "items": [
                {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate", "qty": 1},
            ],
            "status": "pending",
            "created_at": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            "priority": "urgent",
            "address": "上海市浦东新区陆家嘴环路1000号",
            "address_en": "1000 Lujiazui Ring Rd, Pudong, Shanghai",
        },
        {
            "order_id": "ORD-20260801-003",
            "customer": "王小姐",
            "customer_en": "Ms. Wang",
            "items": [
                {"sku": "BP-005", "name": "换牙零食", "name_en": "Teething Treats", "qty": 3},
                {"sku": "BP-006", "name": "宠物领结", "name_en": "Pet Bow Tie", "qty": 1},
            ],
            "status": "picking",
            "created_at": (now - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": "广州市天河区天河路385号太古汇",
            "address_en": "Taikoo Hui, 385 Tianhe Rd, Tianhe, Guangzhou",
        },
        {
            "order_id": "ORD-20260731-004",
            "customer": "赵先生",
            "customer_en": "Mr. Zhao",
            "items": [
                {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag", "qty": 1},
                {"sku": "BP-007", "name": "亚克力牌", "name_en": "Acrylic Tag", "qty": 2},
            ],
            "status": "picking",
            "created_at": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": "深圳市南山区科技园南路88号",
            "address_en": "88 Tech Park South Rd, Nanshan, Shenzhen",
        },
        {
            "order_id": "ORD-20260730-005",
            "customer": "陈女士",
            "customer_en": "Ms. Chen",
            "items": [
                {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar", "qty": 1},
                {"sku": "BP-008", "name": "宠物手链", "name_en": "Pet Bracelet", "qty": 1},
            ],
            "status": "shipped",
            "created_at": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": "杭州市西湖区文三路478号",
            "address_en": "478 Wensan Rd, Xihu, Hangzhou",
            "courier": "顺丰速运",
            "courier_en": "SF Express",
            "tracking_no": "SF1234567890",
        },
        {
            "order_id": "ORD-20260729-006",
            "customer": "吴先生",
            "customer_en": "Mr. Wu",
            "items": [
                {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate", "qty": 2},
            ],
            "status": "shipped",
            "created_at": (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": "成都市锦江区春熙路99号",
            "address_en": "99 Chunxi Rd, Jinjiang, Chengdu",
            "courier": "中通快递",
            "courier_en": "ZTO Express",
            "tracking_no": "ZTO9876543210",
        },
    ]


# ── 智能配货 ──
def allocate_order(order: dict, inventory: list[dict]) -> dict:
    """为订单智能匹配库存，返回配货结果"""
    results = []
    all_ok = True

    for item in order["items"]:
        # 查找匹配的库存
        matched = None
        for inv_item in inventory:
            if inv_item["sku"] == item["sku"]:
                matched = inv_item
                break

        if matched is None:
            results.append({
                "sku": item["sku"],
                "name": item.get("name", item.get("name_en", "")),
                "name_en": item.get("name_en", item.get("name", "")),
                "needed": item["qty"],
                "available": 0,
                "allocated": 0,
                "shortage": item["qty"],
                "location": "—",
                "zone": "—",
                "ok": False,
            })
            all_ok = False
        elif matched["qty"] >= item["qty"]:
            results.append({
                "sku": item["sku"],
                "name": matched["name"],
                "name_en": matched["name_en"],
                "needed": item["qty"],
                "available": matched["qty"],
                "allocated": item["qty"],
                "shortage": 0,
                "location": matched["location"],
                "zone": matched["zone"],
                "ok": True,
            })
        else:
            results.append({
                "sku": item["sku"],
                "name": matched["name"],
                "name_en": matched["name_en"],
                "needed": item["qty"],
                "available": matched["qty"],
                "allocated": matched["qty"],
                "shortage": item["qty"] - matched["qty"],
                "location": matched["location"],
                "zone": matched["zone"],
                "ok": False,
            })
            all_ok = False

    return {"order_id": order["order_id"], "items": results, "all_ok": all_ok}


# ── 物流追踪 ──
LOGISTICS_STATUSES = [
    ("待揽收", "Awaiting Pickup", "快递员已接单，等待上门取件", "Courier accepted, awaiting pickup"),
    ("运输中", "In Transit", "包裹在干线运输途中", "Package in transit on main route"),
    ("派送中", "Out for Delivery", "快递员正在派送，请保持电话畅通", "Courier delivering, keep phone accessible"),
    ("已签收", "Delivered", "包裹已由收件人签收", "Package signed by recipient"),
]

def get_logistics_tracking(tracking_no: str) -> list[dict]:
    """模拟物流轨迹"""
    now = datetime.now()
    # 基于 tracking_no 确定性生成轨迹
    seed = sum(ord(c) for c in tracking_no)
    rng = random.Random(seed)

    # 随机决定当前到哪一步
    steps_count = rng.randint(1, 4)
    events = []

    for i in range(steps_count):
        cn_status, en_status, cn_desc, en_desc = LOGISTICS_STATUSES[i]
        hours_ago = (steps_count - i) * rng.randint(4, 24)
        ts = (now - timedelta(hours=hours_ago)).strftime("%m-%d %H:%M")
        events.append({
            "time": ts,
            "status_cn": cn_status,
            "status_en": en_status,
            "desc_cn": cn_desc,
            "desc_en": en_desc,
        })

    # 计算预计到达
    current_step = steps_count - 1
    if current_step < 3:
        eta_hours = (3 - current_step) * rng.randint(12, 24)
        eta = now + timedelta(hours=eta_hours)
        eta_str = eta.strftime("%m-%d %H:%M")
    else:
        eta_str = None  # 已签收

    return {"events": events, "current_status_cn": LOGISTICS_STATUSES[current_step][0],
            "current_status_en": LOGISTICS_STATUSES[current_step][1],
            "eta": eta_str, "current_step": current_step, "total_steps": 4}
