"""
RetailSense — 客户意图分析引擎
基于产品特征匹配目标客户画像
"""

from dataclasses import dataclass


@dataclass
class CustomerProfile:
    """客户画像"""
    name: str               # 画像名称
    traits: list[str]       # 特征标签
    needs: list[str]        # 需求
    budget: str             # 预算区间
    triggers: list[str]     # 购买触发点


# 预设客户画像
CUSTOMER_PROFILES = [
    CustomerProfile(
        "新手铲屎官", ["首次养宠", "年轻", "社交活跃"],
        ["安全可靠", "新手友好", "颜值高"], "¥50-200",
        ["刚接毛孩子回家", "刷到小红书种草", "朋友推荐"]
    ),
    CustomerProfile(
        "精致养宠人", ["中高收入", "品质导向", "品牌敏感"],
        ["个性化定制", "高品质材料", "送礼体面"], "¥100-500",
        ["节日送礼", "宠物生日", "追求独一无二"]
    ),
    CustomerProfile(
        "性价比猎人", ["价格敏感", "多宠家庭", "高频复购"],
        ["便宜耐用", "批量优惠", "消耗品"], "¥10-80",
        ["消耗完了要补货", "打折促销", "组合套餐"]
    ),
    CustomerProfile(
        "礼物购买者", ["非养宠人", "送礼需求", "一次性购买"],
        ["包装精美", "寓意好", "不怕选错"], "¥80-300",
        ["朋友宠物生日", "节日送礼", "不知道买什么"]
    ),
]


class IntentEngine:
    """意图分析引擎"""

    def __init__(self, profiles: list[CustomerProfile] = None):
        self.profiles = profiles or CUSTOMER_PROFILES

    def match(self, product: dict) -> list[dict]:
        """将产品匹配到目标客户画像"""
        results = []
        is_consumable = product.get("is_consumable", False)
        price = product.get("price", 0)
        name = product.get("name", "")

        for profile in self.profiles:
            score = 0
            reasons = []

            # 耗材类 → 性价比猎人 + 新手
            if is_consumable:
                if "性价比猎人" in profile.name or "新手" in profile.name:
                    score += 30
                    reasons.append("耗材属性匹配高复购需求")

            # 高价定制 → 精致养宠 + 送礼
            if price > 15 and not is_consumable:
                if "精致" in profile.name or "礼物" in profile.name:
                    score += 25
                    reasons.append(f"¥{price:.0f} 定价匹配中高端消费")

            # 低价 → 性价比
            if price < 10:
                if "性价比" in profile.name:
                    score += 20
                    reasons.append("亲民价格匹配预算敏感群体")

            # 个性化类 → 送礼 + 精致
            if "名牌" in name or "定制" in name or "刻字" in name:
                if "礼物" in profile.name or "精致" in profile.name:
                    score += 20
                    reasons.append("定制化属性匹配送礼/个性化需求")

            # 零食/食品 → 新手 + 性价比
            if "零食" in name or "食品" in name:
                if "新手" in profile.name or "性价比" in profile.name:
                    score += 15
                    reasons.append("食品类适合入门试购")

            results.append({
                "profile": profile.name,
                "score": score,
                "match_level": "强烈推荐" if score >= 50 else ("推荐" if score >= 30 else ("一般" if score >= 15 else "不推荐")),
                "reasons": reasons,
                "triggers": profile.triggers,
                "budget": profile.budget,
            })

        return sorted(results, key=lambda r: r["score"], reverse=True)

    def best_angle(self, product: dict) -> dict:
        """找到最佳销售角度"""
        matches = self.match(product)
        if not matches:
            return {"angle": "通用推荐", "audience": "所有用户", "pitch": "高品质宠物用品"}

        best = matches[0]
        profile_name = best["profile"]
        product_name = product.get("name", "")

        angles = {
            "新手铲屎官": {
                "angle": "第一次买就选对",
                "pitch": f"不知道给毛孩子买什么？{product_name} 是 90% 新手的第一选择。安全、好看、不踩坑。"
            },
            "精致养宠人": {
                "angle": "独一无二的专属感",
                "pitch": f"每一件 {product_name} 都是手工定制，刻上毛孩子的名字，这是专属于你们的仪式感。"
            },
            "性价比猎人": {
                "angle": "同样的品质，更低的价格",
                "pitch": f"买得多省得多。{product_name} 工厂直供，省去中间商，品质不输大牌，价格只有一半。"
            },
            "礼物购买者": {
                "angle": "送礼送到心坎里",
                "pitch": f"不确定朋友喜欢什么？{product_name} 是永远不会出错的礼物——实用、精致、有你心意在里面。"
            },
        }

        ang = angles.get(profile_name, angles["新手铲屎官"])
        return {"angle": ang["angle"], "audience": profile_name, "pitch": ang["pitch"], "triggers": best["triggers"]}
