"""
RetailSense — 虚拟管家
简单的规则引擎智能体，不依赖外部模型
"""

COMMANDS = {
    "hello": ["你好！我是 RetailSense 管家。你可以问我：\n- 今日营收\n- 库存预警\n- 推荐选品\n- 定价建议 [产品名]\n- 切换地区 [地区名]"],
    "今日营收": ["正在查询今日营收..."],
    "营收": ["正在查询今日营收..."],
    "库存预警": ["正在扫描库存..."],
    "低库存": ["正在扫描低库存产品..."],
    "推荐选品": ["正在分析最佳选品..."],
    "定价建议": ["正在计算定价建议..."],
    "help": ["支持的命令：\n- 今日营收 / 库存预警 / 推荐选品 / 定价建议/帮助"],
    "帮助": ["支持的命令：\n- 今日营收 / 库存预警 / 推荐选品 / 定价建议 / 帮助"],
}


class VirtualAgent:
    """虚拟管家智能体"""

    def __init__(self):
        self.context = {}

    def process(self, user_input: str, company_data: dict = None,
                transactions: list = None, inventory: list = None) -> str:
        """处理用户输入并返回响应"""
        inp = user_input.strip().lower()

        # 基础对话
        for cmd, responses in COMMANDS.items():
            if cmd.lower() in inp:
                return responses[0]

        # 今日营收
        if any(w in inp for w in ["营收","收入","赚了多少","revenue"]):
            if not transactions:
                return "暂无交易数据。请先接入公司库存或手动录入。"
            from .dataloader import daily_summary
            today = daily_summary(transactions, 1)
            week = daily_summary(transactions, 7)
            return (f"今日营收：¥{today['revenue']:,.2f}（{today['orders']}单）\n"
                    f"本周营收：¥{week['revenue']:,.2f}\n"
                    f"今日成本：¥{today['cost']:,.2f} | 利润：¥{today['profit']:,.2f}")

        # 库存预警
        if any(w in inp for w in ["库存","预警","缺货","断货","低库存"]):
            if not inventory:
                return "暂无库存数据。"
            from .dataloader import inventory_value_summary
            summary = inventory_value_summary(inventory)
            return (f"总SKU：{summary['skus']} | 总库存：{summary['total_qty']}件\n"
                    f"库存价值：¥{summary['total_value']:,.2f}（零售价 ¥{summary['total_retail']:,.2f}）\n"
                    f"低库存：{summary['low_stock']}个 | 断货：{summary['out_of_stock']}个")

        # 推荐选品
        if any(w in inp for w in ["选品","推荐","recommend","best"]):
            if not inventory:
                return "暂无产品数据。"
            # 按利润率+流速排序
            scored = []
            for i in inventory:
                margin = (i["price"] - i["cost"]) / i["price"]
                velocity = i["daily_avg"] / max(1, i["qty"])
                score = margin * 0.5 + velocity * 0.5
                scored.append((i["name"], score, margin, i["daily_avg"]))
            scored.sort(key=lambda x: x[1], reverse=True)
            top = scored[:3]
            lines = ["推荐选品 TOP3："]
            for name, s, m, d in top:
                lines.append(f"  {name} — 利润率 {m:.0%} · 日销 {d:.1f}件")
            return "\n".join(lines)

        # 默认
        return "请输入命令（营收/库存/选品/帮助）或直接描述你的需求。"