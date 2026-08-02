"""
RetailSense — 区域市场分析
跨境平台数据 + Top5国家 + 当地活动日历
"""

REGIONS = {
    "北美": {
        "countries": ["美国","加拿大"],
        "platforms": ["Amazon","Etsy","eBay","Walmart","Shopify"],
        "events": [
            ("11月","Black Friday 黑五 11/28"),
            ("12月","Christmas 圣诞节 12/25"),
            ("7月","Prime Day 亚马逊会员日"),
            ("2月","Valentine's Day 情人节 2/14"),
            ("10月","Halloween 万圣节 10/31"),
        ],
        "trends": "宠物个性化定制需求旺盛，手工刻字狗牌搜索量+35%",
        "avg_margin": "45-65%",
        "competition": "中等",
    },
    "欧洲": {
        "countries": ["英国","德国","法国"],
        "platforms": ["Amazon EU","Etsy","eBay UK","Allegro","Fruugo"],
        "events": [
            ("12月","Christmas 圣诞节 12/25"),
            ("1月","Winter Sales 冬季大促"),
            ("7月","Summer Sales 夏季大促"),
            ("11月","Black Friday 黑五"),
        ],
        "trends": "环保材质宠物饰品需求上升，德国市场偏好功能性产品",
        "avg_margin": "40-55%",
        "competition": "较低（语言壁垒）",
    },
    "东南亚": {
        "countries": ["印尼","泰国","越南","菲律宾","马来西亚"],
        "platforms": ["Shopee","Lazada","Tokopedia","TikTok Shop"],
        "events": [
            ("9月","99大促 / 9.9 Sale"),
            ("11月","双11 / 11.11"),
            ("12月","双12 / 12.12"),
            ("1-2月","春节 / Chinese New Year"),
            ("4月","泼水节 Songkran（泰国）"),
        ],
        "trends": "性价比宠物零食需求大，客单价低但复购率极高",
        "avg_margin": "25-40%",
        "competition": "激烈（价格战）",
    },
    "日韩": {
        "countries": ["日本","韩国"],
        "platforms": ["Amazon Japan","Rakuten","Coupang","Qoo10"],
        "events": [
            ("12月","Christmas 圣诞节"),
            ("1月","新年 Sale"),
            ("2月","Valentine's Day 情人节"),
            ("8月","Obon 盂兰盆节（日本）"),
        ],
        "trends": "精致小巧风格受欢迎，宠物服饰品类增速快",
        "avg_margin": "50-70%",
        "competition": "中等偏高",
    },
    "澳洲": {
        "countries": ["澳大利亚","新西兰"],
        "platforms": ["Amazon AU","eBay AU","Trade Me"],
        "events": [
            ("12月","Boxing Day 节礼日 12/26"),
            ("6月","EOFY 财年末大促"),
            ("11月","Black Friday 黑五"),
        ],
        "trends": "户外宠物用品需求大，牵引绳/项圈品类稳定",
        "avg_margin": "45-60%",
        "competition": "较低",
    },
}


def get_region(region_name: str) -> dict | None:
    return REGIONS.get(region_name)


def all_regions() -> list[str]:
    return list(REGIONS.keys())


def upcoming_events(region_name: str, month: int = None) -> list:
    region = REGIONS.get(region_name)
    if not region:
        return []
    events = region["events"]
    if month:
        month_str = f"{month}月"
        return [(m, e) for m, e in events if month_str in m]
    return events


def best_region_for_product(product: dict) -> list[str]:
    """根据产品特征推荐最佳市场"""
    scores = {}
    price = product.get("price", 0)
    is_consumable = product.get("is_consumable", False)

    if is_consumable:
        scores["东南亚"] = 80  # 零食复购率高
        scores["北美"] = 60
    elif price < 10:
        scores["东南亚"] = 75
        scores["欧洲"] = 50
    elif price < 20:
        scores["北美"] = 80
        scores["欧洲"] = 70
        scores["日韩"] = 65
    else:
        scores["日韩"] = 85
        scores["北美"] = 70

    return sorted(scores, key=scores.get, reverse=True)[:3]
