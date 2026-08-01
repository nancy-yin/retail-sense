"""
RetailSense — AI 文案生成器
支持 SSE 流式输出模式
"""
import time
from dataclasses import dataclass


@dataclass
class CopyTemplate:
    """文案模板"""
    name: str
    style: str           # casual / professional / seo
    sections: list[str]  # 模板段落

# 预设文案模板
COPY_TEMPLATES = {
    "seo": CopyTemplate("SEO优化", "professional", [
        "标题优化: {name} — {hook}",
        "核心卖点: {features}",
        "使用场景: {scenarios}",
        "规格参数: {specs}",
        "购买理由: {reasons}",
        "搜索标签: {tags}",
    ]),
    "social": CopyTemplate("社交种草", "casual", [
        "开头痛点: {pain_point}",
        "产品引入: {name} 解决了这个问题",
        "使用体验: {experience}",
        "效果展示: {result}",
        "行动号召: {cta}",
    ]),
    "sales": CopyTemplate("销售转化", "professional", [
        "限时优惠: {offer}",
        "产品亮点: {highlights}",
        "社会证明: {social_proof}",
        "紧迫感: {urgency}",
        "立即购买: {buy_now}",
    ]),
}


class CopyGenerator:
    """AI 文案生成器"""

    def __init__(self):
        self.templates = COPY_TEMPLATES

    def generate(self, product: dict, style: str = "seo") -> str:
        """生成文案"""
        template = self.templates.get(style, self.templates["seo"])

        name = product.get("name", "")
        price = product.get("price", 0)
        cost = product.get("cost", 0)
        competitors = product.get("competitors", 0)
        is_consumable = product.get("is_consumable", False)

        # 构建文案变量
        margin = int((price - cost) / price * 100) if price > 0 else 0
        hook = f"卖爆了的{name}，回头客都在回购" if is_consumable else f"手工定制{name}，每一件都独一无二"
        features = f"高品质材料 · 精细工艺 · {margin}%超高复购率" if is_consumable else f"SUS304不锈钢 · 激光刻字 · 永不褪色"
        scenarios = "每日遛狗必备" if is_consumable else "送闺蜜/送女友/纪念日礼物首选"
        specs = f"¥{price:.2f} · 美国直邮 · 7天到货"
        reasons = "复购率远超同类产品" if is_consumable else f"手工定制 · 竞品仅{competitors}个 · 蓝海机会"
        tags = "#宠物用品 #手工定制 #原创设计 #宠物饰品"
        pain_point = "每次遛狗都在找零食？" if is_consumable else "市面上的狗牌千篇一律？"
        experience = "我家狗狗超爱吃，每次拆包都摇尾巴" if is_consumable else "刻上毛孩子的名字，从此不再走丢"
        result = "一个月回购3次" if is_consumable else "路人都在问哪里买的"
        cta = "点击链接，给你家毛孩子也来一个"
        offer = f"新店开业 · 首单 8 折 · 仅限前 50 名"
        highlights = f"{name} — {margin}%利润率 · 手工打造 · 美国发货"
        social_proof = "已售 200+ 件 · 4.9星好评"
        urgency = "存货不多，下一批要等 2 周"
        buy_now = "立即下单 →"

        lines = []
        for section in template.sections:
            line = section.format(**locals())
            lines.append(line)

        return "\n".join(lines)

    def stream_generate(self, product: dict, style: str = "seo"):
        """流式生成（模拟 SSE）"""
        content = self.generate(product, style)
        lines = content.split("\n")
        for line in lines:
            time.sleep(0.3)  # 模拟生成延迟
            yield line + "\n"
