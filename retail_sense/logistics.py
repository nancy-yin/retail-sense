"""
RetailSense — 物流配发模块 v2.0
Order Management + Smart Allocation + Logistics Tracking
30+ 订单 · 爆货场景 · 双语
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

random.seed(42)

# ── 模拟库存（含库位）──
def get_warehouse_inventory() -> list[dict]:
    """返回仓库库存，含库位标注"""
    return [
        {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag",
         "qty": 45, "location": "A-03-12", "zone": "A区", "zone_en": "Zone A"},
        {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar",
         "qty": 12, "location": "B-01-05", "zone": "B区", "zone_en": "Zone B"},
        {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate",
         "qty": 120, "location": "A-02-08", "zone": "A区", "zone_en": "Zone A"},
        {"sku": "BP-004", "name": "牵引绳套装", "name_en": "Leash Set",
         "qty": 0, "location": "C-01-03", "zone": "C区", "zone_en": "Zone C"},
        {"sku": "BP-005", "name": "换牙零食", "name_en": "Teething Treats",
         "qty": 8, "location": "D-02-01", "zone": "D区", "zone_en": "Zone D"},
        {"sku": "BP-006", "name": "宠物领结", "name_en": "Pet Bow Tie",
         "qty": 30, "location": "B-03-06", "zone": "B区", "zone_en": "Zone B"},
        {"sku": "BP-007", "name": "亚克力牌", "name_en": "Acrylic Tag",
         "qty": 55, "location": "A-01-04", "zone": "A区", "zone_en": "Zone A"},
        {"sku": "BP-008", "name": "宠物手链", "name_en": "Pet Bracelet",
         "qty": 18, "location": "C-02-02", "zone": "C区", "zone_en": "Zone C"},
    ]


# ── 客户数据池 ──
CUSTOMERS = [
    ("张先生", "Mr. Zhang"), ("李女士", "Ms. Li"), ("王小姐", "Ms. Wang"),
    ("赵先生", "Mr. Zhao"), ("陈女士", "Ms. Chen"), ("吴先生", "Mr. Wu"),
    ("刘女士", "Ms. Liu"), ("周先生", "Mr. Zhou"), ("黄小姐", "Ms. Huang"),
    ("孙先生", "Mr. Sun"), ("马女士", "Ms. Ma"), ("朱先生", "Mr. Zhu"),
    ("胡女士", "Ms. Hu"), ("郭先生", "Mr. Guo"), ("林小姐", "Ms. Lin"),
    ("何先生", "Mr. He"), ("罗女士", "Ms. Luo"), ("梁先生", "Mr. Liang"),
    ("宋女士", "Ms. Song"), ("郑先生", "Mr. Zheng"),
]

ADDRESSES = [
    ("北京市朝阳区望京SOHO T3-1208", "Wangjing SOHO T3-1208, Chaoyang, Beijing"),
    ("上海市浦东新区陆家嘴环路1000号", "1000 Lujiazui Ring Rd, Pudong, Shanghai"),
    ("广州市天河区天河路385号太古汇", "Taikoo Hui, 385 Tianhe Rd, Tianhe, Guangzhou"),
    ("深圳市南山区科技园南路88号", "88 Tech Park South Rd, Nanshan, Shenzhen"),
    ("杭州市西湖区文三路478号", "478 Wensan Rd, Xihu, Hangzhou"),
    ("成都市锦江区春熙路99号", "99 Chunxi Rd, Jinjiang, Chengdu"),
    ("武汉市洪山区珞喻路1037号", "1037 Luoyu Rd, Hongshan, Wuhan"),
    ("南京市鼓楼区汉中路88号", "88 Hanzhong Rd, Gulou, Nanjing"),
    ("重庆市渝中区解放碑步行街12号", "12 Jiefangbei Pedestrian St, Yuzhong, Chongqing"),
    ("西安市雁塔区小寨路99号", "99 Xiaozhai Rd, Yanta, Xi'an"),
    ("长沙市岳麓区麓山南路932号", "932 Lushan South Rd, Yuelu, Changsha"),
    ("天津市和平区南京路181号", "181 Nanjing Rd, Heping, Tianjin"),
    ("苏州市工业园区星湖街328号", "328 Xinghu St, SIP, Suzhou"),
    ("厦门市思明区鹭江道100号", "100 Lujiang Rd, Siming, Xiamen"),
    ("青岛区崂山区海尔路1号", "1 Haier Rd, Laoshan, Qingdao"),
    ("大连市中山区人民路55号", "55 Renmin Rd, Zhongshan, Dalian"),
]

COURIERS = [
    ("顺丰速运", "SF Express"),
    ("中通快递", "ZTO Express"),
    ("圆通速递", "YTO Express"),
    ("韵达快递", "Yunda Express"),
    ("京东物流", "JD Logistics"),
    ("极兔速递", "J&T Express"),
    ("德邦快递", "Deppon Express"),
]

ALL_PRODUCTS = [
    {"sku": "BP-001", "name": "刻字狗牌", "name_en": "Engraved Dog Tag"},
    {"sku": "BP-002", "name": "发光项圈", "name_en": "LED Collar"},
    {"sku": "BP-003", "name": "珐琅名牌", "name_en": "Enamel Nameplate"},
    {"sku": "BP-004", "name": "牵引绳套装", "name_en": "Leash Set"},
    {"sku": "BP-005", "name": "换牙零食", "name_en": "Teething Treats"},
    {"sku": "BP-006", "name": "宠物领结", "name_en": "Pet Bow Tie"},
    {"sku": "BP-007", "name": "亚克力牌", "name_en": "Acrylic Tag"},
    {"sku": "BP-008", "name": "宠物手链", "name_en": "Pet Bracelet"},
]


def _pick_order_items(rng: random.Random, max_items: int = 3) -> list[dict]:
    """为订单随机选择商品及数量，覆盖全部 SKU"""
    n = rng.randint(1, min(max_items, len(ALL_PRODUCTS)))
    selected = rng.sample(ALL_PRODUCTS, n)
    items = []
    for p in selected:
        # 爆货场景：10% 概率生成大批量订单 (5-12件)
        if rng.random() < 0.10:
            qty = rng.randint(5, 12)
        else:
            qty = rng.randint(1, 4)
        items.append({**p, "qty": qty})
    return items


# ── 30+ 模拟订单 ──
def get_mock_orders() -> list[dict]:
    """返回 34 单模拟订单（待处理 17 + 拣货中 9 + 已发货 8），覆盖全部 8 个产品"""
    now = datetime.now()
    rng = random.Random(42)

    orders: list[dict] = []

    # ── 待处理 17 单 ──
    pending_configs = [
        # (customer_idx, hours_ago, priority, address_idx, max_items)
        (0, 0.5, "urgent", 0, 2),   # 紧急
        (1, 1, "normal", 1, 1),
        (2, 1.5, "urgent", 2, 3),  # 紧急 + 多商品
        (3, 2, "normal", 3, 2),
        (4, 2.5, "normal", 4, 2),
        (5, 3, "urgent", 5, 1),    # 紧急
        (6, 3.5, "normal", 6, 2),
        (7, 4, "normal", 7, 1),
        (8, 4.5, "normal", 8, 2),
        (9, 5, "urgent", 9, 3),    # 紧急 + 多商品（爆货）
        (10, 5.5, "normal", 10, 2),
        (11, 6, "normal", 11, 1),
        (12, 6.5, "normal", 12, 2),
        (13, 7, "normal", 13, 1),
        (14, 7.5, "urgent", 14, 3), # 紧急
        (15, 8, "normal", 15, 2),
        (16, 8.5, "normal", 0, 2),
    ]

    for idx, (ci, hrs, pri, ai, mi) in enumerate(pending_configs):
        cust_cn, cust_en = CUSTOMERS[ci]
        addr_cn, addr_en = ADDRESSES[ai]
        items = _pick_order_items(rng, mi)
        orders.append({
            "order_id": f"ORD-20260806-{idx+1:03d}",
            "customer": cust_cn,
            "customer_en": cust_en,
            "items": items,
            "status": "pending",
            "created_at": (now - timedelta(hours=hrs)).strftime("%Y-%m-%d %H:%M"),
            "priority": pri,
            "address": addr_cn,
            "address_en": addr_en,
        })

    # ── 拣货中 9 单 ──
    picking_configs = [
        (17, 10, "normal", 5, 2),
        (2, 12, "urgent", 3, 3),
        (18, 14, "normal", 7, 2),
        (0, 16, "normal", 1, 1),
        (19, 18, "normal", 9, 2),
        (4, 20, "urgent", 4, 3),
        (7, 22, "normal", 11, 2),
        (10, 24, "normal", 6, 1),
        (13, 26, "normal", 14, 2),
    ]

    for idx, (ci, hrs, pri, ai, mi) in enumerate(picking_configs):
        cust_cn, cust_en = CUSTOMERS[ci]
        addr_cn, addr_en = ADDRESSES[ai]
        items = _pick_order_items(rng, mi)
        orders.append({
            "order_id": f"ORD-20260805-{idx+1:03d}",
            "customer": cust_cn,
            "customer_en": cust_en,
            "items": items,
            "status": "picking",
            "created_at": (now - timedelta(hours=hrs)).strftime("%Y-%m-%d %H:%M"),
            "priority": pri,
            "address": addr_cn,
            "address_en": addr_en,
        })

    # ── 已发货 8 单 ──
    shipped_configs = [
        (1, 36, 0, 0),
        (5, 48, 1, 1),
        (8, 56, 2, 2),
        (11, 64, 3, 3),
        (14, 72, 4, 4),
        (3, 80, 5, 5),
        (6, 88, 6, 6),
        (9, 96, 7, 6),
    ]

    for idx, (ci, hrs, ai, couri) in enumerate(shipped_configs):
        cust_cn, cust_en = CUSTOMERS[ci]
        addr_cn, addr_en = ADDRESSES[ai]
        items = _pick_order_items(rng, rng.randint(1, 3))
        courier_cn, courier_en = COURIERS[couri]
        tracking_prefix = f"SF{10+idx:02d}" if couri < 3 else f"ZTO{10+idx:02d}"
        orders.append({
            "order_id": f"ORD-20260804-{idx+1:03d}",
            "customer": cust_cn,
            "customer_en": cust_en,
            "items": items,
            "status": "shipped",
            "created_at": (now - timedelta(hours=hrs)).strftime("%Y-%m-%d %H:%M"),
            "priority": "normal",
            "address": addr_cn,
            "address_en": addr_en,
            "courier": courier_cn,
            "courier_en": courier_en,
            "tracking_no": f"{tracking_prefix}{100000 + idx * 137:06d}",
        })

    return orders


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
                "zone_en": "—",
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
                "zone_en": matched.get("zone_en", matched["zone"]),
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
                "zone_en": matched.get("zone_en", matched["zone"]),
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

def get_logistics_tracking(tracking_no: str) -> dict:
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


# ═══════════════════════════════════════════════════════════
# 虚拟快递系统 (Virtual Express Delivery System)
# 模拟: 接单→配货→出库→物流追踪 全流程
# ═══════════════════════════════════════════════════════════

COURIER_PREFIXES = ["SF", "YT", "DB", "ZTO", "JD"]
COURIER_NAMES = {
    "SF": ("顺丰速运", "SF Express"),
    "YT": ("圆通速递", "YTO Express"),
    "ZTO": ("中通快递", "ZTO Express"),
    "DB": ("德邦快递", "Deppon Express"),
    "JD": ("京东物流", "JD Logistics"),
}

# 虚拟配送六阶段 (Virtual delivery pipeline — 6 stages)
DELIVERY_PIPELINE = [
    ("已接单", "Order Accepted", "订单已进入系统，等待仓库配货", "Order entered system, awaiting warehouse allocation"),
    ("配货完成", "Allocation Done", "库存匹配完成，商品已拣货下架", "Inventory matched, items picked from shelves"),
    ("已出库", "Dispatched", "包裹已出库并交接快递公司", "Package dispatched and handed to courier"),
    ("运输中", "In Transit", "包裹在干线运输途中", "Package in transit on main route"),
    ("派送中", "Out for Delivery", "快递员正在派送，请保持电话畅通", "Courier delivering, keep phone accessible"),
    ("已签收", "Delivered", "包裹已由收件人签收", "Package signed by recipient"),
]


def generate_waybill_no(prefix: str | None = None) -> str:
    """生成虚拟快递单号 / Generate virtual waybill number

    格式: <prefix><timestamp><seq>
    示例: SF08061530234567, YT08061530234567, DB08061530234567
    """
    if prefix is None:
        prefix = random.choice(COURIER_PREFIXES)
    ts = datetime.now().strftime("%m%d%H%M")
    seq = random.randint(100000, 999999)
    return f"{prefix}{ts}{seq}"


def get_courier_info(waybill: str) -> tuple[str, str, str]:
    """根据运单号前缀获取快递公司信息 / Get courier info from waybill prefix

    Returns: (中文名, English name, prefix)
    """
    for prefix in sorted(COURIER_PREFIXES, key=len, reverse=True):
        if waybill.startswith(prefix):
            cn, en = COURIER_NAMES.get(prefix, ("未知快递", "Unknown Courier"))
            return (cn, en, prefix)
    return ("未知快递", "Unknown Courier", "??")


def simulate_delivery_tracking(
    waybill_no: str,
    shipped_at: datetime | None = None,
    rng_seed: int | None = None,
) -> dict:
    """模拟快递全流程追踪 / Simulate full delivery tracking pipeline

    根据发货后经过的时间自动推进配送阶段:
    - 0~5分钟:  已接单
    - 5~15分钟: 配货完成
    - 15~30分钟: 已出库
    - 30~120分钟: 运输中
    - 120~180分钟: 派送中
    - 180分钟+:  已签收

    Returns:
        waybill_no, courier, courier_en, events[], current_stage, total_stages,
        current_status_cn, current_status_en, eta, shipped_at
    """
    now = datetime.now()
    if shipped_at is None:
        shipped_at = now

    if rng_seed is not None:
        rng = random.Random(rng_seed)
    else:
        rng = random.Random(sum(ord(c) for c in waybill_no))

    elapsed_minutes = max(0, (now - shipped_at).total_seconds() / 60)

    # 根据经过的时间决定当前阶段
    if elapsed_minutes < 5:
        current_stage = 0   # 已接单
    elif elapsed_minutes < 15:
        current_stage = 1   # 配货完成
    elif elapsed_minutes < 30:
        current_stage = 2   # 已出库
    elif elapsed_minutes < 120:
        current_stage = 3   # 运输中
    elif elapsed_minutes < 180:
        current_stage = 4   # 派送中
    else:
        current_stage = 5   # 已签收

    events = []
    for i in range(current_stage + 1):
        cn_status, en_status, cn_desc, en_desc = DELIVERY_PIPELINE[i]
        # 每个阶段的时间偏移（分钟）
        if i == 0:
            stage_offset = 0
        elif i <= 2:
            stage_offset = i * rng.randint(3, 8)
        else:
            stage_offset = i * rng.randint(15, 45)
        ts = (shipped_at + timedelta(minutes=stage_offset)).strftime("%m-%d %H:%M")
        events.append({
            "time": ts,
            "status_cn": cn_status,
            "status_en": en_status,
            "desc_cn": cn_desc,
            "desc_en": en_desc,
        })

    # 预计到达时间
    if current_stage < len(DELIVERY_PIPELINE) - 1:
        remaining_stages = len(DELIVERY_PIPELINE) - 1 - current_stage
        eta_minutes = remaining_stages * rng.randint(20, 60)
        eta = now + timedelta(minutes=eta_minutes)
        eta_str = eta.strftime("%m-%d %H:%M")
    else:
        eta_str = None  # 已签收，无预计到达

    courier_cn, courier_en, _ = get_courier_info(waybill_no)

    return {
        "waybill_no": waybill_no,
        "courier": courier_cn,
        "courier_en": courier_en,
        "events": events,
        "current_stage": current_stage,
        "total_stages": len(DELIVERY_PIPELINE),
        "current_status_cn": DELIVERY_PIPELINE[current_stage][0],
        "current_status_en": DELIVERY_PIPELINE[current_stage][1],
        "eta": eta_str,
        "shipped_at": shipped_at.strftime("%Y-%m-%d %H:%M"),
    }


# ═══════════════════════════════════════════════════════════
# 订单 API 接入口 (Order API Webhook Integration)
# ═══════════════════════════════════════════════════════════

# Webhook 端点: POST /api/orders/webhook
# Content-Type: application/json
# 签名验证: HMAC-SHA256 (Shopify) 或自定义 header
#
# 订单数据 Schema:
API_ORDER_SCHEMA = {
    "order_id": "str (必填) — 外部订单号，幂等去重",
    "platform": "str — 'shopify' | 'etsy' | 'woocommerce' | 'custom'",
    "customer": {
        "name": "str",
        "email": "str",
        "phone": "str (可选)",
    },
    "shipping_address": {
        "line1": "str",
        "city": "str",
        "province": "str",
        "postal_code": "str",
        "country": "str (ISO 3166-1 alpha-2)",
    },
    "items": [
        {
            "sku": "str (必填) — 与仓库 SKU 匹配",
            "name": "str",
            "qty": "int (必填)",
            "unit_price": "float",
        }
    ],
    "total": "float",
    "currency": "str — 'CNY' | 'USD' | 'EUR' | ...",
    "created_at": "str — ISO 8601",
    "notes": "str (可选)",
}

# Shopify Webhook 接入步骤:
SHOPIFY_INTEGRATION_GUIDE = """
## Shopify 接入 / Shopify Integration

### 1. Shopify 后台设置 / Shopify Admin Setup
- 进入 Settings → Notifications → Webhooks
- Create webhook → Event: "Order creation"
- Format: JSON
- URL: https://your-domain.com/api/orders/webhook

### 2. HMAC 签名验证 / HMAC Verification
Shopify 在每个 webhook 请求头中附带 X-Shopify-Hmac-SHA256，
用你的 Shopify App Secret 计算 HMAC 并与请求头比对。

### 3. 订单映射 / Order Mapping
Shopify order → RetailSense order:
- order.id → order_id
- line_items[].sku → items[].sku
- line_items[].quantity → items[].qty
- shipping_address → shipping_address

### 4. 独立站通用 Webhook / Custom Store Webhook
通用 JSON 格式同上 API_ORDER_SCHEMA，POST 到同一端点。
需实现签名验证（推荐 HMAC-SHA256 或 API Key header）。
"""
