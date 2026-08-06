"""
RetailSense — 区域市场分析
跨境平台数据 + Top5国家 + 当地活动日历
"""

from __future__ import annotations

REGIONS = {
    "北美": {
        "countries": ["美国","加拿大"],
        "platforms": ["Amazon","Etsy","eBay","Walmart","Shopify"],
        "events": [
            ("11月","Black Friday 黑色星期五","美国最大购物节，全品类爆发","上品指数:95","建议：定制宠物牌/项圈礼盒套装"),
            ("12月","Christmas 圣诞节 12/25","欧美最重要节日，礼品需求峰值","上品指数:90","建议：刻字狗牌作圣诞礼物+节日限定包装"),
            ("7月","Prime Day 亚马逊会员日","Amazon全年最大促销，Prime会员专享","上品指数:88","建议：高折扣引流款+捆绑销售"),
            ("2月","Valentine's Day 情人节 2/14","情侣互赠礼物，宠物配饰需求旺","上品指数:75","建议：心形宠物牌/情侣项圈对装"),
            ("10月","Halloween 万圣节 10/31","北美全民Cosplay，宠物服饰爆发","上品指数:70","建议：万圣节主题宠物领结/围巾"),
        ],
        "trends": "宠物个性化定制需求旺盛，手工刻字狗牌搜索量+35%",
        "avg_margin": "45-65%",
        "competition": "中等",
    },
    "欧洲": {
        "countries": ["英国","德国","法国"],
        "platforms": ["Amazon EU","Etsy","eBay UK","Allegro","Fruugo"],
        "events": [
            ("12月","Christmas 圣诞节 12/25","欧洲最重要节日，家庭聚会送礼高峰","上品指数:92","建议：高端手工宠物牌+礼盒装"),
            ("1月","Winter Sales 冬季大促","欧洲传统打折季，持续3-4周","上品指数:85","建议：清仓款打折+新品预售"),
            ("7月","Summer Sales 夏季大促","欧洲夏季旅游季+打折季重叠","上品指数:78","建议：户外宠物用品（牵引绳/便携水碗）"),
            ("11月","Black Friday 黑五","欧洲版黑五，近年增长迅猛","上品指数:88","建议：英/德/法三语Listing+亚马逊EU多站点"),
        ],
        "trends": "环保材质宠物饰品需求上升，德国市场偏好功能性产品",
        "avg_margin": "40-55%",
        "competition": "较低（语言壁垒）",
    },
    "东南亚": {
        "countries": ["印尼","泰国","越南","菲律宾","马来西亚"],
        "platforms": ["Shopee","Lazada","Tokopedia","TikTok Shop"],
        "events": [
            ("9月","99大促 9.9 Sale","Shopee/Lazada双平台超级购物节","上品指数:95","建议：9.9元引流款+直播间闪购"),
            ("11月","双11 11.11","东南亚最大电商节，堪比中国双11","上品指数:98","建议：全品类参战+多件多折"),
            ("12月","双12 12.12","年末最后大促，清仓+新年备货","上品指数:85","建议：年终清仓+新年限定款"),
            ("1-2月","春节 Chinese New Year","东南亚华人消费高峰","上品指数:72","建议：红色系宠物饰品+吉祥寓意设计"),
            ("4月","泼水节 Songkran（泰国）","泰国新年，全国放假庆祝","上品指数:65","建议：防水材质宠物用品+节日限定色"),
        ],
        "trends": "性价比宠物零食需求大，客单价低但复购率极高",
        "avg_margin": "25-40%",
        "competition": "激烈（价格战）",
    },
    "日韩": {
        "countries": ["日本","韩国"],
        "platforms": ["Amazon Japan","Rakuten","Coupang","Qoo10"],
        "events": [
            ("12月","Christmas 圣诞节","日韩圣诞节商业化程度高，礼物经济","上品指数:85","建议：精致礼盒装+圣诞限定包装"),
            ("1月","新年 Sale 初売り/설날","日韩新年大促，福袋文化盛行","上品指数:90","建议：宠物福袋（随机组合装）+限量发售"),
            ("2月","Valentine's Day 情人节","日韩情人节反向送礼文化（女送男）","上品指数:75","建议：情侣宠物牌对装+心形设计"),
            ("8月","Obon 盂兰盆节（日本）","日本返乡祭祖高峰，出行需求大","上品指数:60","建议：便携宠物出行套装"),
        ],
        "trends": "精致小巧风格受欢迎，宠物服饰品类增速快",
        "avg_margin": "50-70%",
        "competition": "中等偏高",
    },
    "澳洲": {
        "countries": ["澳大利亚","新西兰"],
        "platforms": ["Amazon AU","eBay AU","Trade Me"],
        "events": [
            ("12月","Boxing Day 节礼日 12/26","澳洲最大购物日，线下线上全面促销","上品指数:92","建议：圣诞后清仓+夏季户外用品"),
            ("6月","EOFY 财年末大促","澳洲企业财年末清仓，全品类打折","上品指数:82","建议：批量折扣+企业团购方案"),
            ("11月","Black Friday 黑五","澳洲黑五近年增长最快","上品指数:85","建议：pre-Boxing Day预热+全品类参战"),
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
        return [(m, e, desc, idx, tip) for m, e, desc, idx, tip in events if month_str in m]
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
