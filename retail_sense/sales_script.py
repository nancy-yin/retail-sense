"""
RetailSense — 智能促单话术生成器
Hybrid: 规则引擎 + 模板组合
"""


class SalesScriptGenerator:
    """促单话术生成器"""

    # 话术模板库
    OPENINGS = {
        "痛点开场": "你是不是也在为{problem}而烦恼？",
        "好奇开场": "你知道吗？{fact}",
        "故事开场": "上个月有个客户{story}",
        "直接开场": "给你看个好东西——{name}",
    }

    OBJECTION_HANDLERS = {
        "太贵了": [
            "贵有贵的道理：{name}用的是{quality}，用上{time}年没问题，平均下来一天才¥{daily_price:.2f}。",
            "我理解你的顾虑。但你算一下，便宜的用{competitor_time}就得换，我们的一件顶{multiplier}件。",
        ],
        "再看看": [
            "当然可以。不过这个价格是限时的，现在下单还送{gift}。",
            "没问题！我把链接发你，随时可以回来看看。（附上好评截图）",
        ],
        "不需要": [
            "理解。但{trigger_scenario}的时候，你会希望手边有{name}。",
            "很多客户一开始也这么说，但用过之后都说{testimonial}。",
        ],
        "有更好的": [
            "你指的哪一家？我帮你对比一下。{name}的优势是{advantage}。",
            "当然市面选择很多。但{name}用了{quality}，这个价位找不到第二家。",
        ],
    }

    CLOSERS = [
        "今天下单，{benefit}。",
        "现在买还送{gift}，数量有限。",
        "要不要先拿一件试试？不满意包退。",
        "你看选哪个颜色/尺寸？我帮你下单。",
    ]

    def generate_opening(self, product: dict, style: str = "痛点开场") -> str:
        """生成开场话术"""
        name = product.get("name", "")
        template = self.OPENINGS.get(style, self.OPENINGS["直接开场"])

        problems = {
            True: "狗狗零食消耗太快，每次都要临时买",
            False: "市面上的宠物牌千篇一律，没有个性",
        }
        facts = {
            True: "80%的狗狗家长每月在零食上花超过200元",
            False: f"手工定制{name}在美国Etsy上月搜索量增长35%",
        }
        stories = {
            True: "买了3次便宜零食都不爱吃，直到试了我们的",
            False: "刻了毛孩子名字的牌子丢了，邻居居然通过牌子送回来了",
        }

        problem = problems.get(product.get("is_consumable", False), problems[False])
        fact = facts.get(product.get("is_consumable", False), facts[False])
        story = stories.get(product.get("is_consumable", False), stories[False])

        return template.format(name=name, problem=problem, fact=fact, story=story)

    def handle_objection(self, product: dict, objection: str) -> str:
        """处理客户异议"""
        name = product.get("name", "")
        price = product.get("price", 0)
        is_consumable = product.get("is_consumable", False)

        handlers = self.OBJECTION_HANDLERS.get(objection, self.OBJECTION_HANDLERS["再看看"])
        template = handlers[0]

        return template.format(
            name=name,
            quality="食品级材料" if is_consumable else "SUS304不锈钢",
            time=2 if is_consumable else 5,
            daily_price=round(price / (60 if is_consumable else 365), 2),
            competitor_time="2周" if is_consumable else "1年",
            multiplier="3" if is_consumable else "5",
            gift="小包装试用装" if is_consumable else "刻字服务",
            trigger_scenario="加班到家想犒劳毛孩子" if is_consumable else "毛孩子走丢时",
            testimonial="再也不吃别家了" if is_consumable else "路人都在问哪里买的",
            advantage="手工定制" if not is_consumable else "配方天然",
        )

    def generate_closer(self, product: dict) -> str:
        """生成促单结束语"""
        import random
        template = random.choice(self.CLOSERS)
        name = product.get("name", "")
        is_consumable = product.get("is_consumable", False)

        return template.format(
            name=name,
            benefit="首单8折+包邮" if not is_consumable else "买三送一",
            gift="免费刻字服务" if not is_consumable else "试吃装",
        )

    def full_script(self, product: dict, style: str = "痛点开场",
                    objection: str = "再看看") -> dict:
        """生成完整促单话术"""
        return {
            "开场": self.generate_opening(product, style),
            "卖点说明": f"{product['name']} — ¥{product['price']:.2f} · 高品质 · 手工定制",
            "异议处理": self.handle_objection(product, objection),
            "促单结束": self.generate_closer(product),
        }
