"""
RetailSense — AI 文案生成器 v2
学习Etsy/Amazon Top Seller 文案模式
"""
import time
from dataclasses import dataclass


@dataclass
class CopyTemplate:
    name: str
    style: str
    sections: list[str]


COPY_TEMPLATES = {
    "seo": CopyTemplate("SEO优化", "professional", [
        "标题: {title_hook}",
        "副标题: {subtitle}",
        "核心卖点:\n{material_points}",
        "差异化:\n{differentiation}",
        "规格参数: {specs}",
        "搜索标签: {tags}",
    ]),
    "social": CopyTemplate("社交种草", "casual", [
        "封面句: {hook_line}",
        "痛点引入: {pain_story}",
        "产品登场: {product_intro}",
        "使用场景: {scene_describe}",
        "真实反馈: {social_proof}",
        "行动号召: {cta}",
        "话题标签: {hashtags}",
    ]),
    "sales": CopyTemplate("销售转化", "urgent", [
        "紧迫钩子: {urgency_hook}",
        "信任建立: {trust_builder}",
        "产品亮点: {key_features}",
        "价格锚点: {price_anchor}",
        "风险消除: {risk_reversal}",
        "限时行动: {limited_cta}",
    ]),
}


class CopyGenerator:
    """AI 文案生成器 v2"""

    def __init__(self):
        self.templates = COPY_TEMPLATES

    def generate(self, product: dict, style: str = "seo") -> str:
        name = product.get("name", "")
        price = product.get("price", 0)
        cost = product.get("cost", 0)
        competitors = product.get("competitors", 0)
        is_consumable = product.get("is_consumable", False)
        search_growth = product.get("search_growth", 0)
        margin = int((price - cost) / price * 100) if price > 0 else 0
        annual = product.get("annual_purchases", 1)

        # ── 变量计算 ──
        # 标题钩子
        title_hooks = {
            True: f"【复购率{annual}次/年】{name} — 狗狗吃完摇尾巴的零食",
            False: f"【{margin}%利润率】手工定制{name} — 每个毛孩子都值得独一无二",
        }
        title_hook = title_hooks[is_consumable]

        # 副标题
        subtitles = {
            True: f"月销{int(annual/12*100)}袋 · {search_growth}%增长品类 · 美国直邮",
            False: f"激光刻字 · 永不褪色 · 7天到货 · 满$35包邮",
        }
        subtitle = subtitles[is_consumable]

        # 材质卖点
        material_points = ("• 人食用级原料，无添加防腐剂\n• 独立真空包装，开封30天保鲜\n• 适合3个月以上全犬种" if is_consumable else
                          "• SUS304不锈钢，防水防锈\n• 双面激光刻字，字迹永不磨损\n• 3种尺寸 · 5种颜色可选")

        # 差异化
        differentiation = ("不同：市面零食多用肉粉填充 → 我们用整块鸡胸肉烘干" if is_consumable else
                         f"不同：市面上{competitors}家竞品用亚克力 → 我们用304钢+双面雕刻")

        # 规格
        specs = f"¥{price:.2f} · 美国直邮 · 7-12天到货 · 满$35包邮"

        # 标签
        tags = ("#宠物零食 #狗狗训练奖励 #天然磨牙棒 #美国直邮 #复购王" if is_consumable else
               "#定制狗牌 #宠物ID牌 #刻字项圈 #手工宠物饰品 #防走丢神器")

        # 社交文案
        hook_line = ("每次打开这包零食，我家狗直接从二楼冲下来..." if is_consumable else
                    "自从给毛孩子戴上这个牌，邻居见面第一句话永远是「在哪买的？」")
        pain_story = ("买过不下10种磨牙棒，要么太硬崩牙，要么吃完拉肚子..." if is_consumable else
                     "丢了3个狗牌之后我终于明白——便宜货的刻字两个月就磨没了，根本找不到主人。")
        product_intro = f"直到遇到{name}——{margin}%的复购率不是吹的。" if is_consumable else f"直到入手{name}——激光刻上去的字，洗了半年都跟新的一样。"
        scene_describe = ("遛狗前揣一包，训练时当奖励，坐车时安抚情绪——一包搞定。" if is_consumable else
                         "遛狗、寄养、看病、旅行——任何时候扫一下二维码就能联系到你。")
        social_proof = ("\"我家挑食怪居然主动吃完了\"\"比Petco的好十倍\"——来自真实买家" if is_consumable else
                       "\"刻的字半年了还跟新的一样\"\"路人追着问链接\"——看看他们怎么说")
        cta = "点下方链接，第一包半价试吃 👇" if is_consumable else "点链接定制你的专属狗牌，下单即送刻字服务 👇"
        hashtags = ("#养狗必备 #狗狗零食推荐 #萌宠日常" if is_consumable else
                   "#定制宠物牌 #养宠必备 #铲屎官好物")

        # 销售转化
        urgency_hook = (
            "库存告急！这批{name}只剩最后37袋，下一批要等3周。" if is_consumable else
            f"仅剩8个刻字名额——{name}全手工制作，每天最多接20单。"
        )
        trust_builder = (
            "2000+养狗家庭的选择 · 4.9星好评 · 30天无理由退换" if is_consumable else
            f"已为3000+毛孩子定制专属ID牌 · Etsy {competitors}家竞品中评分最高"
        )
        key_features = material_points
        price_anchor = (
            f"市面同品质零食$18+/袋，我们工厂直供$11.99。省下的钱够你再买一包。" if is_consumable else
            f"宠物店定制狗牌$25起，同款304不锈钢我们$12.99。不是便宜，是没有中间商。"
        )
        risk_reversal = (
            "不吃包退。狗狗不爱吃？全额退款，运费我们出。" if is_consumable else
            "刻错包换。任何质量问题免费重做，邮费我们承担。"
        )
        limited_cta = (
            "👇 点击下单，首单8折，仅限前50包。" if is_consumable else
            "👇 点击开始定制，今天下单送免费刻字。"
        )

        if style == "seo":
            return f"{title_hook}\n{subtitle}\n\n{material_points}\n\n{differentiation}\n\n{specs}\n\n{tags}"
        elif style == "social":
            return f"{hook_line}\n\n{pain_story}\n\n{product_intro}\n\n{scene_describe}\n\n{social_proof}\n\n{cta}\n{hashtags}"
        elif style == "sales":
            return f"⚡ {urgency_hook}\n\n{trust_builder}\n\n{key_features}\n\n{price_anchor}\n\n{risk_reversal}\n\n{limited_cta}"

        return title_hook

    def stream_generate(self, product: dict, style: str = "seo"):
        content = self.generate(product, style)
        lines = content.split("\n")
        for line in lines:
            time.sleep(0.15)
            yield line + "\n"
