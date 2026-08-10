"""
RetailSense — 虚拟管家 v3.0
规则引擎 + 数据分析智能体，不依赖外部模型
支持：本地虚拟数据查询、产品匹配、操作建议、思考过程展示、全中英双语
"""

from __future__ import annotations
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re

# ═══════════════════════════════════════════════════════════════
# 旧版命令兼容（保留原 COMMANDS 字典）
# ═══════════════════════════════════════════════════════════════

COMMANDS = {
    "hello": ["你好！我是 RetailSense 管家。你可以问我：\n- 今日营收\n- 库存预警\n- 推荐选品\n- 定价建议 [产品名]\n- 切换地区 [地区名]"],
    "help": ["支持的命令：\n- 今日营收 / 库存预警 / 推荐选品 / 定价建议/帮助"],
    "帮助": ["支持的命令：\n- 今日营收 / 库存预警 / 推荐选品 / 定价建议 / 帮助"],
}


# ═══════════════════════════════════════════════════════════════
# 意图识别规则
# ═══════════════════════════════════════════════════════════════

INTENT_RULES = {
    "stock_query": {
        "zh": ["库存", "还有多少", "剩多少", "有多少", "数量", "几个", "件", "存量", "备货"],
        "en": ["stock", "how many", "quantity", "qty", "left", "remaining", "inventory for", "units"],
    },
    "profit_query": {
        "zh": ["利润", "最赚钱", "最赚", "毛利率", "利润率", "盈利", "净赚", "收益最高", "margin"],
        "en": ["profit", "margin", "most profitable", "highest profit", "best margin", "earnings"],
    },
    "revenue_query": {
        "zh": ["营收", "收入", "赚了多少", "销售额", "流水", "营业额", "revenue", "今天卖了", "本周卖", "这周卖", "本月卖", "这个月卖", "今日", "昨天", "本周", "这周", "本月", "这个月"],
        "en": ["revenue", "sales", "income", "today", "yesterday", "this week", "this month", "earnings"],
    },
    "low_stock_alert": {
        "zh": ["库存预警", "低库存", "预警", "缺货", "断货", "不够", "快没了", "库存不足", "库存低了", "告急", "紧缺", "库存警告"],
        "en": ["low stock", "stock alert", "alert", "out of stock", "running low", "shortage", "critical", "insufficient", "stock warning"],
    },
    "restock_advice": {
        "zh": ["补货", "进货", "需要进", "采购", "进多少", "该补", "要补", "restock", "建议补"],
        "en": ["restock", "replenish", "reorder", "order more", "buy more", "should order"],
    },
    "product_recommend": {
        "zh": ["推荐", "选品", "好卖", "热卖", "爆款", "best", "top", "recommend"],
        "en": ["recommend", "best", "top", "popular", "pick", "selection"],
    },
    "product_list": {
        "zh": ["有哪些", "所有产品", "产品列表", "全部", "list", "都有什么", "清单", "目录"],
        "en": ["list", "all products", "catalog", "what do you have", "everything", "show me all"],
    },
    "help": {
        "zh": ["帮助", "help", "命令", "怎么用", "功能", "能做什么", "使用说明"],
        "en": ["help", "commands", "how to", "what can you do", "usage"],
    },
    "greeting": {
        "zh": ["你好", "hello", "hi", "hey", "嗨", "在吗"],
        "en": ["hello", "hi", "hey", "greetings"],
    },
}

# 时间范围关键词
TIME_RANGE_ZH = {"今日": 1, "今天": 1, "昨天": 1, "昨日": 1,
                  "本周": 7, "这周": 7, "最近一周": 7, "近一周": 7,
                  "本月": 30, "这个月": 30, "最近一月": 30, "近一月": 30}
TIME_RANGE_EN = {"today": 1, "yesterday": 1,
                  "this week": 7, "week": 7,
                  "this month": 30, "month": 30}

# 操作建议模板
SUGGESTION_TEMPLATES_ZH = {
    "out_of_stock": "⚠️ {name} 已断货！建议立即补货 {qty} 件（补到安全库存 {safety} 件以上）。",
    "low_stock": "⚡ {name} 库存仅剩 {current} 件（低于安全库存 {safety} 件），建议补货 {reorder} 件。周转天数：{turnover} 天。",
    "restock": "📦 {name} 当前库存 {current} 件，已接近补货触发点 {reorder_point} 件。建议补货 {reorder} 件。",
    "overstock": "📊 {name} 库存 {current} 件，周转 {turnover} 天，可能存在积压风险。建议考虑促销或减少进货。",
    "high_margin": "💎 {name} 利润率 {margin:.0%}，日销 {daily} 件，高利润产品，建议加大推广力度。",
    "stale": "⏰ {name} 已 {days} 天未动销，建议降价促销或下架处理。",
}

SUGGESTION_TEMPLATES_EN = {
    "out_of_stock": "⚠️ {name} is OUT OF STOCK! Restock {qty} units immediately (above safety stock of {safety}).",
    "low_stock": "⚡ {name} only {current} units left (below safety stock of {safety}). Suggest restock {reorder} units. Turnover: {turnover} days.",
    "restock": "📦 {name} has {current} units, near reorder point ({reorder_point}). Suggest restock {reorder} units.",
    "overstock": "📊 {name} has {current} units, {turnover} days turnover. Risk of overstock. Consider promotion or reduce purchasing.",
    "high_margin": "💎 {name} margin {margin:.0%}, daily sales {daily} units. High-profit item — increase promotion.",
    "stale": "⏰ {name} hasn't sold in {days} days. Consider markdown or delisting.",
}


# ═══════════════════════════════════════════════════════════════
# 响应结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgentResponse:
    """Agent 响应结构"""
    thinking: list[str] = field(default_factory=list)     # 思考步骤（中英双语）
    answer: str = ""                                        # 最终答案
    suggestions: list[str] = field(default_factory=list)    # 操作建议
    intent: str = "unknown"                                 # 识别到的意图


# ═══════════════════════════════════════════════════════════════
# VirtualAgent v3.0
# ═══════════════════════════════════════════════════════════════

class VirtualAgent:
    """虚拟管家智能体 v3.0 — 规则引擎 + 数据分析"""

    def __init__(self):
        self.context = {}

    # ── 产品模糊匹配 ──

    def _fuzzy_match_product(self, query: str, inventory: list[dict]) -> dict | None:
        """模糊匹配用户查询中的产品名到实际库存"""
        best_score = 0
        best_item = None
        query_lower = query.lower()

        for item in inventory:
            name = item.get("name", "")
            name_en = item.get("name_en", "")
            sku = item.get("sku", "")
            score = 0

            # 精确匹配（中文名或英文名或SKU）
            if name and name in query:
                score = 100
            elif name_en and name_en.lower() in query_lower:
                score = 95
            elif sku and sku.lower() in query_lower:
                score = 90

            # 部分匹配：产品名中的关键词出现在查询中
            if score == 0:
                # 拆产品名中的关键词（2字以上）
                for kw in self._extract_keywords(name):
                    if kw in query:
                        score += 30
                for kw in self._extract_keywords(name_en):
                    if kw.lower() in query_lower:
                        score += 25
                # 反过来：查询中的词在产品名中
                for qw in query.split():
                    if len(qw) >= 2:
                        if name and qw in name:
                            score += 15
                        if name_en and qw.lower() in name_en.lower():
                            score += 12

            if score > best_score:
                best_score = score
                best_item = item

        # 阈值：至少要有一定匹配度
        if best_score >= 20 and best_item:
            return best_item
        return None

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """从文本中提取关键词（2字及以上）"""
        if not text:
            return []
        # 中文：用常见分隔词切割
        words = re.split(r'[，,、\s()（）\-—/]+', text)
        keywords = []
        for w in words:
            w = w.strip()
            if len(w) >= 2:
                keywords.append(w)
            # 再加单字组合
            if len(w) == 3:
                keywords.append(w[:2])
                keywords.append(w[1:])
            elif len(w) == 4:
                keywords.append(w[:2])
                keywords.append(w[1:3])
                keywords.append(w[2:])
        return [k for k in keywords if len(k) >= 2]

    # ── 意图识别 ──

    def _detect_intent(self, user_input: str, inventory: list[dict], transactions: list[dict]) -> tuple[str, float]:
        """识别用户意图，返回 (意图, 置信度)"""
        inp = user_input.lower().strip()
        scores = {}

        for intent, triggers in INTENT_RULES.items():
            score = 0
            for lang in ("zh", "en"):
                for kw in triggers[lang]:
                    kw_lower = kw.lower()
                    if kw_lower in inp:
                        # 完整关键词匹配：≥2字符给完整权重，单字给半权重
                        score += 30 if len(kw_lower) >= 2 else 15
                    # 部分匹配
                    elif len(kw_lower) >= 4 and any(part in inp for part in kw_lower.split()):
                        score += 10
            if score > 0:
                scores[intent] = score

        # ── 后处理：特定场景提升 ──
        # 预警类关键词强提升 low_stock_alert
        alert_boost_words = ["预警", "低库存", "断货", "缺货", "库存预警", "库存不足", "库存低了", "告急", "紧缺", "alert", "out of stock"]
        if any(kw in inp for kw in alert_boost_words):
            scores["low_stock_alert"] = scores.get("low_stock_alert", 0) + 40

        # 如果有产品名出现在查询中，提升 stock_query 权重
        if self._fuzzy_match_product(user_input, inventory):
            if "stock_query" not in scores:
                scores["stock_query"] = 15  # 提到产品名默认查库存
            else:
                scores["stock_query"] += 20

        # 如果完全没有交易数据，降低 revenue/profit 权重
        if not transactions:
            scores.pop("revenue_query", None)
            scores.pop("profit_query", None)

        if not scores:
            return "unknown", 0.0

        best = max(scores, key=scores.get)
        return best, scores[best]

    # ── 提取时间范围 ──

    @staticmethod
    def _extract_time_range(user_input: str) -> int:
        """从查询中提取时间范围天数"""
        inp = user_input.lower()
        for kw, days in TIME_RANGE_ZH.items():
            if kw in inp:
                return days
        for kw, days in TIME_RANGE_EN.items():
            if kw in inp:
                return days
        return 1  # 默认今天

    # ── 检查语言偏好 ──

    @staticmethod
    def _is_english(user_input: str) -> bool:
        """判断用户是否在用英文提问"""
        # 如果输入主要是 ASCII 字符，判断为英文
        ascii_count = sum(1 for c in user_input if ord(c) < 128)
        total = len(user_input.strip())
        if total == 0:
            return False
        return ascii_count / total > 0.7

    # ═══════════════════════════════════════════════════════════
    # 核心处理方法
    # ═══════════════════════════════════════════════════════════

    def process(self, user_input: str, company_data: dict = None,
                transactions: list = None, inventory: list = None,
                lang: str = "zh") -> AgentResponse:
        """处理用户输入并返回 AgentResponse

        返回 AgentResponse 包含 thinking steps、answer 和 suggestions。
        兼容旧版：也可通过 .answer 属性获取纯文本。
        """
        transactions = transactions or []
        inventory = inventory or []
        is_en = lang == "en" or self._is_english(user_input)

        # 步骤追踪
        thinking = []

        # ── 第0步：旧版命令兼容 ──
        inp_lower = user_input.strip().lower()
        for cmd, responses in COMMANDS.items():
            if cmd.lower() in inp_lower:
                thinking.append(
                    "🔍 匹配到旧版命令: {}".format(cmd) if not is_en
                    else "🔍 Matched legacy command: {}".format(cmd)
                )
                return AgentResponse(
                    thinking=thinking,
                    answer=responses[0],
                    intent="legacy_command",
                )

        # ── 第1步：意图识别 ──
        thinking.append(
            "🧠 正在分析您的查询意图..." if not is_en
            else "🧠 Analyzing your query intent..."
        )
        intent, confidence = self._detect_intent(user_input, inventory, transactions)

        if intent == "unknown":
            thinking.append(
                "⚠️ 未能识别到明确的查询意图" if not is_en
                else "⚠️ Could not identify clear query intent"
            )
            help_text = (
                "请输入命令或直接描述您的需求。我可以帮您：\n"
                "📦 查询库存 — 如「刻字狗牌库存多少」\n"
                "💰 查询营收 — 如「今日营收」「本周利润最高产品」\n"
                "⚠️ 库存预警 — 如「哪些产品库存低了」\n"
                "🛒 补货建议 — 如「建议补货」\n"
                "⭐ 推荐选品 — 如「推荐产品」\n"
                "📋 产品列表 — 如「有哪些产品」"
            ) if not is_en else (
                "Please enter a command or describe your needs. I can help with:\n"
                "📦 Stock check — e.g. 'How many engraved dog tags left'\n"
                "💰 Revenue — e.g. 'Today's revenue', 'Highest profit product'\n"
                "⚠️ Low stock alert — e.g. 'Which products are low stock'\n"
                "🛒 Restock advice — e.g. 'What should I restock'\n"
                "⭐ Recommendations — e.g. 'Top products'\n"
                "📋 Product list — e.g. 'List all products'"
            )
            return AgentResponse(
                thinking=thinking,
                answer=help_text,
                intent="unknown",
            )

        # ── 第2步：按意图处理 ──
        thinking.append(
            f"✅ 识别意图: {intent} (置信度: {confidence})" if not is_en
            else f"✅ Intent: {intent} (confidence: {confidence})"
        )

        if intent == "greeting":
            return self._handle_greeting(thinking, is_en)

        elif intent == "help":
            return self._handle_help(thinking, is_en)

        elif intent == "product_list":
            return self._handle_product_list(thinking, inventory, is_en)

        elif intent == "stock_query":
            return self._handle_stock_query(thinking, user_input, inventory, is_en)

        elif intent == "revenue_query":
            return self._handle_revenue_query(
                thinking, user_input, transactions, inventory, is_en
            )

        elif intent == "profit_query":
            return self._handle_profit_query(thinking, user_input, transactions, inventory, is_en)

        elif intent == "low_stock_alert":
            return self._handle_low_stock_alert(thinking, inventory, is_en)

        elif intent == "restock_advice":
            return self._handle_restock_advice(thinking, user_input, inventory, is_en)

        elif intent == "product_recommend":
            return self._handle_product_recommend(thinking, inventory, transactions, is_en)

        return AgentResponse(
            thinking=thinking,
            answer=(
                "请输入命令或直接描述您的需求（营收/库存/选品/帮助）" if not is_en
                else "Enter a command (revenue/stock/recommend/help) or describe your needs."
            ),
            intent=intent,
        )

    # ═══════════════════════════════════════════════════════════
    # 各意图处理方法
    # ═══════════════════════════════════════════════════════════

    def _handle_greeting(self, thinking: list, is_en: bool) -> AgentResponse:
        thinking.append("👋 问候模式" if not is_en else "👋 Greeting mode")
        company_name = self.context.get("company", "")
        name_line = f"，{company_name}" if company_name else ""
        return AgentResponse(
            thinking=thinking,
            answer=(
                f"🐾 你好{name_line}！我是 RetailSense 管家。我可以帮你：\n"
                f"📦 查库存 | 💰 查营收 | ⚠️ 库存预警 | 🛒 补货建议 | ⭐ 推荐选品\n"
                f"直接输入问题即可，如「刻字狗牌库存多少」「本周利润最高的产品」"
            ) if not is_en else (
                f"🐾 Hello{name_line}! I'm your RetailSense assistant. I can help with:\n"
                f"📦 Stock | 💰 Revenue | ⚠️ Alerts | 🛒 Restock | ⭐ Recommendations\n"
                f"Just ask, e.g. 'How many LED collars left', 'Most profitable product'"
            ),
            intent="greeting",
        )

    def _handle_help(self, thinking: list, is_en: bool) -> AgentResponse:
        thinking.append("📖 帮助模式" if not is_en else "📖 Help mode")
        return AgentResponse(
            thinking=thinking,
            answer=(
                "🐾 **RetailSense 管家助手**\n\n"
                "**查询类：**\n"
                "• 查库存：`[产品名]库存多少` — 如「刻字狗牌库存多少」\n"
                "• 查营收：`今日营收` `本周营收` — 查看销售额\n"
                "• 查利润：`本周利润最高产品` — 按利润排名\n"
                "• 产品列表：`有哪些产品` — 查看所有产品\n\n"
                "**建议类：**\n"
                "• 库存预警：`哪些库存低了` — 低库存/断货提醒\n"
                "• 补货建议：`建议补货` `[产品名]该补货吗` — 补货量建议\n"
                "• 推荐选品：`推荐产品` — 按利润+流速排名\n\n"
                "**其他：**`帮助` `你好`"
            ) if not is_en else (
                "🐾 **RetailSense Assistant**\n\n"
                "**Queries:**\n"
                "• Stock: `[product] stock` — e.g. 'LED collar stock'\n"
                "• Revenue: `today revenue` `week revenue`\n"
                "• Profit: `most profitable product`\n"
                "• Catalog: `list all products`\n\n"
                "**Advice:**\n"
                "• Alerts: `low stock alert`\n"
                "• Restock: `what to restock` `[product] restock`\n"
                "• Picks: `top products` `recommend`\n\n"
                "**Other:** `help` `hello`"
            ),
            intent="help",
        )

    def _handle_product_list(self, thinking: list, inventory: list, is_en: bool) -> AgentResponse:
        thinking.append("📋 正在读取产品列表..." if not is_en else "📋 Loading product catalog...")
        if not inventory:
            return AgentResponse(
                thinking=thinking,
                answer=("暂无产品数据。" if not is_en else "No product data available."),
                intent="product_list",
            )

        lines = [
            "📋 **产品列表** ({})".format(len(inventory)) if not is_en
            else "📋 **Product Catalog** ({})".format(len(inventory))
        ]
        for item in inventory:
            name = item.get("name_en" if is_en else "name", item.get("name", ""))
            qty = int(item.get("qty", 0))
            price = item.get("price", 0)
            daily = item.get("daily_avg", 1)

            # 库存状态标记
            if qty == 0:
                status = "🔴 " + ("断货" if not is_en else "OOS")
            elif qty < daily * 7:
                status = "🟡 " + ("低库存" if not is_en else "Low")
            else:
                status = "🟢 " + ("正常" if not is_en else "OK")

            lines.append(
                f"  {status} **{name}** — "
                + ("库存 {qty}件 · ¥{price} · 日销 {daily}件").format(qty=qty, price=price, daily=daily)
                if not is_en else
                f"  {status} **{name}** — {qty} units · ${price} · {daily}/day"
            )

        thinking.append(
            f"✅ 共找到 {len(inventory)} 个产品" if not is_en
            else f"✅ Found {len(inventory)} products"
        )
        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            intent="product_list",
        )

    def _handle_stock_query(self, thinking: list, user_input: str,
                            inventory: list, is_en: bool) -> AgentResponse:
        thinking.append(
            "🔍 正在匹配产品名称..." if not is_en
            else "🔍 Matching product name..."
        )

        if not inventory:
            return AgentResponse(
                thinking=thinking,
                answer=("暂无库存数据。" if not is_en else "No inventory data available."),
                intent="stock_query",
            )

        matched = self._fuzzy_match_product(user_input, inventory)

        if not matched:
            thinking.append(
                "⚠️ 未找到匹配产品，尝试列出所有产品" if not is_en
                else "⚠️ No product match, showing all"
            )
            names = [i.get("name_en" if is_en else "name", i.get("name", "")) for i in inventory]
            return AgentResponse(
                thinking=thinking,
                answer=(
                    "未找到对应产品。您可以查询：\n" + "\n".join(f"  • {n}" for n in names)
                    if not is_en else
                    "Product not found. Available products:\n" + "\n".join(f"  • {n}" for n in names)
                ),
                intent="stock_query",
            )

        name = matched.get("name_en" if is_en else "name", matched.get("name", ""))
        qty = int(matched.get("qty", 0))
        price = matched.get("price", 0)
        cost = matched.get("cost", 0)
        daily = max(float(matched.get("daily_avg", 1)), 0.01)
        lead_days = int(matched.get("lead_days", 3))
        sku = matched.get("sku", "")

        # 计算周转天数、安全库存、补货触发点
        safety_days = 7
        turnover = round(qty / daily, 1) if daily > 0 else float('inf')
        safety_stock = max(1, round(daily * safety_days))
        reorder_point = safety_stock + round(daily * lead_days)
        reorder_qty = max(round(daily), reorder_point - qty) if qty < reorder_point else 0

        thinking.append(
            f"✅ 匹配到: {name} (SKU: {sku})" if not is_en
            else f"✅ Matched: {name} (SKU: {sku})"
        )
        thinking.append(
            "📊 正在计算库存状态..." if not is_en
            else "📊 Computing stock status..."
        )

        # 确定库存状态
        suggestions = []
        if qty == 0:
            status_icon = "🔴"
            status_text = "断货 / OUT OF STOCK"
            template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
            suggestions.append(
                template["out_of_stock"].format(name=name, qty=max(round(daily), safety_stock), safety=safety_stock)
            )
        elif qty < safety_stock:
            status_icon = "🟡"
            status_text = "低库存 / LOW STOCK"
            template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
            suggestions.append(
                template["low_stock"].format(name=name, current=qty, safety=safety_stock,
                                             reorder=reorder_qty, turnover=turnover)
            )
        elif qty < reorder_point:
            status_icon = "🟠"
            status_text = "建议补货 / RESTOCK ADVISED"
            template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
            suggestions.append(
                template["restock"].format(name=name, current=qty, reorder_point=reorder_point,
                                           reorder=reorder_qty)
            )
        elif turnover > 60 and daily > 0:
            status_icon = "🔵"
            status_text = "正常(积压风险) / NORMAL(Overstock Risk)"
            template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
            suggestions.append(
                template["overstock"].format(name=name, current=qty, turnover=turnover)
            )
        else:
            status_icon = "🟢"
            status_text = "正常 / NORMAL"
            # 高利润产品给推广建议
            margin = (price - cost) / price if price > 0 else 0
            if margin > 0.5:
                template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
                suggestions.append(
                    template["high_margin"].format(name=name, margin=margin, daily=daily)
                )

        lines = [
            f"{status_icon} **{name}** — {status_text}",
            "",
            ("📦 当前库存：**{qty} 件**" if not is_en else "📦 Current Stock: **{qty} units**").format(qty=qty),
            ("💰 零售价：¥{price} | 成本：¥{cost} | 利润率：{margin:.0%}").format(price=price, cost=cost, margin=(price-cost)/price if price>0 else 0)
            if not is_en else
            ("💰 Price: ${price} | Cost: ${cost} | Margin: {margin:.0%}").format(price=price, cost=cost, margin=(price-cost)/price if price>0 else 0),
            ("📈 日均销量：{daily:.1f} 件/天").format(daily=daily)
            if not is_en else
            ("📈 Daily Sales: {daily:.1f} units/day").format(daily=daily),
            ("⏱ 周转天数：{turnover} 天" if turnover < float('inf') else "⏱ 周转天数：∞（无动销）").format(turnover=turnover)
            if not is_en else
            ("⏱ Turnover: {turnover} days" if turnover < float('inf') else "⏱ Turnover: ∞ (no sales)").format(turnover=turnover),
            ("🛡 安全库存：{safety} 件 | 补货触发点：{point} 件").format(safety=safety_stock, point=reorder_point)
            if not is_en else
            ("🛡 Safety Stock: {safety} units | Reorder Point: {point} units").format(safety=safety_stock, point=reorder_point),
            ("📦 SKU: {sku} | 进货周期: {lead}天").format(sku=sku, lead=lead_days)
            if not is_en else
            ("📦 SKU: {sku} | Lead Time: {lead} days").format(sku=sku, lead=lead_days),
        ]

        answer = "\n".join(lines)
        return AgentResponse(
            thinking=thinking,
            answer=answer,
            suggestions=suggestions,
            intent="stock_query",
        )

    def _handle_revenue_query(self, thinking: list, user_input: str,
                              transactions: list, inventory: list,
                              is_en: bool) -> AgentResponse:
        thinking.append(
            "💰 正在统计营收数据..." if not is_en
            else "💰 Computing revenue..."
        )

        if not transactions:
            return AgentResponse(
                thinking=thinking,
                answer=(
                    "暂无交易数据。请先接入公司数据。" if not is_en
                    else "No transaction data. Please connect company data first."
                ),
                intent="revenue_query",
            )

        days = self._extract_time_range(user_input)
        label = {1: ("今日" if not is_en else "Today"),
                  7: ("本周" if not is_en else "This Week"),
                  30: ("本月" if not is_en else "This Month")}.get(days, "")

        from .dataloader import daily_summary
        summary = daily_summary(transactions, days, inventory=inventory)

        thinking.append(
            f"✅ {label}统计完成：{summary['orders']}单，¥{summary['revenue']:,.2f}"
            if not is_en else
            f"✅ {label} summary: {summary['orders']} orders, ${summary['revenue']:,.2f}"
        )

        lines = [
            f"💰 **{label}{'营收' if not is_en else ' Revenue'}**",
            "",
            ("📊 销售额：**¥{revenue:,.2f}**").format(revenue=summary['revenue'])
            if not is_en else
            ("📊 Sales: **${revenue:,.2f}**").format(revenue=summary['revenue']),
            ("📦 订单数：**{orders} 单**").format(orders=summary['orders'])
            if not is_en else
            ("📦 Orders: **{orders}**").format(orders=summary['orders']),
            ("📤 出库量：{qty} 件").format(qty=summary['out_qty'])
            if not is_en else
            ("📤 Outbound: {qty} units").format(qty=summary['out_qty']),
            ("💸 成本：¥{cost:,.2f}").format(cost=summary['cost'])
            if not is_en else
            ("💸 Cost: ${cost:,.2f}").format(cost=summary['cost']),
            ("✅ 利润：**¥{profit:,.2f}** ({margin:.1%})").format(profit=summary['profit'], margin=summary['margin'])
            if not is_en else
            ("✅ Profit: **${profit:,.2f}** ({margin:.1%})").format(profit=summary['profit'], margin=summary['margin']),
        ]

        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            intent="revenue_query",
        )

    def _handle_profit_query(self, thinking: list, user_input: str,
                             transactions: list, inventory: list, is_en: bool) -> AgentResponse:
        thinking.append(
            "💎 正在计算各产品利润..." if not is_en
            else "💎 Computing profit per product..."
        )

        if not transactions:
            return AgentResponse(
                thinking=thinking,
                answer=(
                    "暂无交易数据。" if not is_en else "No transaction data."
                ),
                intent="profit_query",
            )

        days = self._extract_time_range(user_input)
        label = {1: ("今日" if not is_en else "Today"),
                  7: ("本周" if not is_en else "This Week"),
                  30: ("本月" if not is_en else "This Month")}.get(days, "")

        # 按产品聚合交易
        reference_date = max(t["date"] for t in transactions)
        reference_dt = datetime.strptime(reference_date, "%Y-%m-%d")
        since = (reference_dt - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        product_profit = {}
        for t in transactions:
            if not since <= t["date"] <= reference_date:
                continue
            if t["type"] == "out":
                pname = t.get("product", "Unknown")
                sku = t.get("sku", "")
                if pname not in product_profit:
                    product_profit[pname] = {"revenue": 0, "qty": 0, "sku": sku}
                product_profit[pname]["revenue"] += t["revenue"]
                product_profit[pname]["qty"] += t["qty"]

        if not product_profit:
            return AgentResponse(
                thinking=thinking,
                answer=(
                    f"{label}暂无销售数据。" if not is_en
                    else f"No sales data for {label.lower()}."
                ),
                intent="profit_query",
            )

        # 匹配成本数据
        inv_map = {i.get("name", ""): i for i in inventory}
        inv_map.update({i.get("name_en", ""): i for i in inventory})
        inv_map.update({i.get("sku", ""): i for i in inventory})

        scored = []
        for pname, data in product_profit.items():
            # 尝试匹配库存以获取成本
            item = inv_map.get(pname)
            # 也尝试模糊匹配
            if not item:
                for inv_item in inventory:
                    if inv_item.get("name") in pname or pname in inv_item.get("name", ""):
                        item = inv_item
                        break
            cost = item.get("cost", 0) if item else 0
            total_cost = cost * data["qty"]
            profit = data["revenue"] - total_cost
            margin = profit / data["revenue"] if data["revenue"] > 0 else 0
            scored.append((pname, profit, margin, data["revenue"], data["qty"]))

        scored.sort(key=lambda x: x[1], reverse=True)

        thinking.append(
            f"✅ 共分析 {len(scored)} 个产品" if not is_en
            else f"✅ Analyzed {len(scored)} products"
        )

        lines = [
            f"💎 **{label}{'利润排名' if not is_en else ' Profit Ranking'}**",
            "",
        ]
        for rank, (name, profit, margin, rev, qty) in enumerate(scored[:5], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
            lines.append(
                f"{medal} **{name}** — "
                + ("利润 ¥{profit:,.2f} | 利润率 {margin:.0%} | 销{qty}件").format(profit=profit, margin=margin, qty=qty)
                if not is_en else
                f"{medal} **{name}** — profit ${profit:,.2f} | margin {margin:.0%} | {qty} sold"
            )

        # 操作建议：最高利润产品
        if scored:
            top_name, top_profit, top_margin, _, _ = scored[0]
            if top_margin > 0.4:
                lines.append("")
                lines.append(
                    "💡 建议：{}利润率高达 {:.0%}，建议加大推广和库存投入".format(top_name, top_margin)
                    if not is_en else
                    "💡 Tip: {} has {:.0%} margin — increase promotion and stock".format(top_name, top_margin)
                )

        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            intent="profit_query",
        )

    def _handle_low_stock_alert(self, thinking: list, inventory: list, is_en: bool) -> AgentResponse:
        thinking.append(
            "⚠️ 正在扫描低库存产品..." if not is_en
            else "⚠️ Scanning for low stock items..."
        )

        if not inventory:
            return AgentResponse(
                thinking=thinking,
                answer=("暂无库存数据。" if not is_en else "No inventory data."),
                intent="low_stock_alert",
            )

        low_stock = []
        out_of_stock = []
        suggestions = []

        for item in inventory:
            name = item.get("name_en" if is_en else "name", item.get("name", ""))
            qty = int(item.get("qty", 0))
            daily = max(float(item.get("daily_avg", 1)), 0.01)
            safety_days = 7
            safety_stock = max(1, round(daily * safety_days))
            lead_days = int(item.get("lead_days", 3))
            reorder_point = safety_stock + round(daily * lead_days)
            turnover = round(qty / daily, 1)

            if qty == 0:
                out_of_stock.append({
                    "name": name, "qty": 0, "daily": daily,
                    "safety": safety_stock, "reorder": max(round(daily), safety_stock),
                })
            elif qty < safety_stock:
                reorder_qty = max(round(daily), reorder_point - qty)
                low_stock.append({
                    "name": name, "qty": qty, "daily": daily,
                    "safety": safety_stock, "reorder": reorder_qty, "turnover": turnover,
                })

        thinking.append(
            f"⚠️ 断货: {len(out_of_stock)} | 低库存: {len(low_stock)} | 正常: {len(inventory) - len(out_of_stock) - len(low_stock)}"
            if not is_en else
            f"⚠️ Out of stock: {len(out_of_stock)} | Low: {len(low_stock)} | OK: {len(inventory) - len(out_of_stock) - len(low_stock)}"
        )

        # 构建响应
        template_zh = SUGGESTION_TEMPLATES_ZH
        template_en = SUGGESTION_TEMPLATES_EN

        lines = []
        if not is_en:
            lines.append("⚠️ **库存预警报告**")
        else:
            lines.append("⚠️ **Stock Alert Report**")
        lines.append("")

        if out_of_stock:
            lines.append("🔴 **{}**".format("断货产品" if not is_en else "Out of Stock"))
            for item in out_of_stock:
                lines.append(f"  • {item['name']} — 库存为0，日均销 {item['daily']:.1f} 件")
                suggestions.append(
                    template_zh["out_of_stock"].format(
                        name=item['name'], qty=item['reorder'], safety=item['safety']
                    ) if not is_en else
                    template_en["out_of_stock"].format(
                        name=item['name'], qty=item['reorder'], safety=item['safety']
                    )
                )
            lines.append("")

        if low_stock:
            lines.append("🟡 **{}**".format("低库存产品" if not is_en else "Low Stock"))
            for item in low_stock:
                lines.append(
                    f"  • {item['name']} — 仅剩 {item['qty']} 件 (安全库存 {item['safety']} 件)，周转 {item['turnover']} 天"
                )
                suggestions.append(
                    template_zh["low_stock"].format(
                        name=item['name'], current=item['qty'], safety=item['safety'],
                        reorder=item['reorder'], turnover=item['turnover']
                    ) if not is_en else
                    template_en["low_stock"].format(
                        name=item['name'], current=item['qty'], safety=item['safety'],
                        reorder=item['reorder'], turnover=item['turnover']
                    )
                )
            lines.append("")

        if not out_of_stock and not low_stock:
            lines.append(
                "✅ 所有产品库存正常！" if not is_en
                else "✅ All products have healthy stock levels!"
            )
        else:
            lines.append(
                f"📋 共 {len(out_of_stock) + len(low_stock)} 个产品需要关注"
                if not is_en else
                f"📋 {len(out_of_stock) + len(low_stock)} products need attention"
            )

        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            suggestions=suggestions,
            intent="low_stock_alert",
        )

    def _handle_restock_advice(self, thinking: list, user_input: str,
                               inventory: list, is_en: bool) -> AgentResponse:
        thinking.append(
            "🛒 正在分析补货需求..." if not is_en
            else "🛒 Analyzing restock needs..."
        )

        if not inventory:
            return AgentResponse(
                thinking=thinking,
                answer=("暂无库存数据。" if not is_en else "No inventory data."),
                intent="restock_advice",
            )

        # 检查是否针对特定产品
        matched = self._fuzzy_match_product(user_input, inventory)

        if matched:
            # 单产品补货建议
            return self._single_product_restock(thinking, matched, is_en)
        else:
            # 全局补货建议
            return self._global_restock_advice(thinking, inventory, is_en)

    def _single_product_restock(self, thinking: list, item: dict, is_en: bool) -> AgentResponse:
        name = item.get("name_en" if is_en else "name", item.get("name", ""))
        qty = int(item.get("qty", 0))
        daily = max(float(item.get("daily_avg", 1)), 0.01)
        safety_days = 7
        safety_stock = max(1, round(daily * safety_days))
        lead_days = int(item.get("lead_days", 3))
        reorder_point = safety_stock + round(daily * lead_days)
        reorder_qty = 0 if qty >= reorder_point else max(round(daily), reorder_point - qty)

        thinking.append(
            f"✅ 分析 {name}：当前{qty}件，补货触发点{reorder_point}件"
            if not is_en else
            f"✅ Analyzing {name}: {qty} units, reorder point {reorder_point}"
        )

        if reorder_qty == 0:
            return AgentResponse(
                thinking=thinking,
                answer=(
                    f"✅ **{name}** 库存充足（{qty} 件），暂不需要补货。\n"
                    f"补货触发点：{reorder_point} 件 | 安全库存：{safety_stock} 件"
                    if not is_en else
                    f"✅ **{name}** stock is sufficient ({qty} units), no restock needed.\n"
                    f"Reorder point: {reorder_point} | Safety stock: {safety_stock}"
                ),
                intent="restock_advice",
            )

        template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
        if qty == 0:
            suggestion = template["out_of_stock"].format(name=name, qty=reorder_qty, safety=safety_stock)
        elif qty < safety_stock:
            turnover = round(qty / daily, 1)
            suggestion = template["low_stock"].format(
                name=name, current=qty, safety=safety_stock, reorder=reorder_qty, turnover=turnover
            )
        else:
            suggestion = template["restock"].format(
                name=name, current=qty, reorder_point=reorder_point, reorder=reorder_qty
            )

        return AgentResponse(
            thinking=thinking,
            answer=suggestion,
            suggestions=[suggestion],
            intent="restock_advice",
        )

    def _global_restock_advice(self, thinking: list, inventory: list, is_en: bool) -> AgentResponse:
        needs_restock = []
        suggestions = []

        for item in inventory:
            name = item.get("name_en" if is_en else "name", item.get("name", ""))
            qty = int(item.get("qty", 0))
            daily = max(float(item.get("daily_avg", 1)), 0.01)
            safety_days = 7
            safety_stock = max(1, round(daily * safety_days))
            lead_days = int(item.get("lead_days", 3))
            reorder_point = safety_stock + round(daily * lead_days)
            reorder_qty = 0 if qty >= reorder_point else max(round(daily), reorder_point - qty)

            if reorder_qty > 0:
                turnover = round(qty / daily, 1) if daily > 0 else float('inf')
                needs_restock.append({
                    "name": name, "qty": qty, "reorder": reorder_qty,
                    "safety": safety_stock, "reorder_point": reorder_point,
                    "turnover": turnover, "daily": daily,
                })

        thinking.append(
            f"📊 需要补货的产品: {len(needs_restock)} 个" if not is_en
            else f"📊 Products needing restock: {len(needs_restock)}"
        )

        if not needs_restock:
            return AgentResponse(
                thinking=thinking,
                answer=(
                    "✅ 所有产品库存充足，无需补货！" if not is_en
                    else "✅ All products well-stocked, no restock needed!"
                ),
                intent="restock_advice",
            )

        template_zh = SUGGESTION_TEMPLATES_ZH
        template_en = SUGGESTION_TEMPLATES_EN

        # 按紧急程度排序：断货 > 低库存 > 建议补货
        needs_restock.sort(key=lambda x: (x["qty"] == 0, x["qty"] < x["safety"], -x["daily"]), reverse=True)

        lines = [
            "🛒 **{}**".format("补货建议" if not is_en else "Restock Recommendations"),
            "",
        ]
        total_reorder = 0
        for item in needs_restock:
            icon = "🔴" if item["qty"] == 0 else ("🟡" if item["qty"] < item["safety"] else "🟠")
            lines.append(
                f"{icon} **{item['name']}** — "
                + ("当前 {qty} 件 → 建议补货 **{reorder} 件**").format(qty=item['qty'], reorder=item['reorder'])
                if not is_en else
                f"{icon} **{item['name']}** — {item['qty']} units → restock **{item['reorder']} units**"
            )
            total_reorder += item["reorder"]

            if item["qty"] == 0:
                suggestions.append(
                    template_zh["out_of_stock"].format(name=item['name'], qty=item['reorder'], safety=item['safety'])
                    if not is_en else
                    template_en["out_of_stock"].format(name=item['name'], qty=item['reorder'], safety=item['safety'])
                )
            elif item["qty"] < item["safety"]:
                suggestions.append(
                    template_zh["low_stock"].format(
                        name=item['name'], current=item['qty'], safety=item['safety'],
                        reorder=item['reorder'], turnover=item['turnover']
                    ) if not is_en else
                    template_en["low_stock"].format(
                        name=item['name'], current=item['qty'], safety=item['safety'],
                        reorder=item['reorder'], turnover=item['turnover']
                    )
                )

        lines.append("")
        lines.append(
            f"📦 合计建议补货：**{total_reorder} 件**" if not is_en
            else f"📦 Total suggested restock: **{total_reorder} units**"
        )

        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            suggestions=suggestions,
            intent="restock_advice",
        )

    def _handle_product_recommend(self, thinking: list, inventory: list,
                                  transactions: list, is_en: bool) -> AgentResponse:
        thinking.append(
            "⭐ 正在计算产品综合评分..." if not is_en
            else "⭐ Computing product scores..."
        )

        if not inventory:
            return AgentResponse(
                thinking=thinking,
                answer=("暂无产品数据。" if not is_en else "No products available."),
                intent="product_recommend",
            )

        # 综合评分：利润率 + 流速 + 库存健康度
        scored = []
        suggestions = []
        for item in inventory:
            name = item.get("name_en" if is_en else "name", item.get("name", ""))
            qty = int(item.get("qty", 0))
            price = item.get("price", 0)
            cost = item.get("cost", 0)
            daily = max(float(item.get("daily_avg", 1)), 0.01)

            margin = (price - cost) / price if price > 0 else 0
            velocity = min(daily / 20, 1.0)  # 归一化到0-1
            stock_health = 1.0 if qty >= daily * 7 else (qty / max(daily * 7, 1))

            # 加权评分：利润率40% + 流速35% + 库存健康25%
            score = margin * 0.4 + velocity * 0.35 + stock_health * 0.25

            scored.append((name, score, margin, daily, qty))
            if margin > 0.5:
                template = SUGGESTION_TEMPLATES_ZH if not is_en else SUGGESTION_TEMPLATES_EN
                suggestions.append(
                    template["high_margin"].format(name=name, margin=margin, daily=daily)
                )

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]

        thinking.append(
            f"✅ 完成排序，TOP1: {top[0][0]} (评分 {top[0][1]:.2f})" if not is_en
            else f"✅ Ranking complete, TOP1: {top[0][0]} (score {top[0][1]:.2f})"
        )

        lines = [
            "⭐ **{}**".format("推荐选品 TOP5" if not is_en else "Top 5 Product Picks"),
            "",
        ]
        for rank, (name, score, margin, daily, qty) in enumerate(top, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
            stock_note = (
                " ⚠️库存低" if qty < daily * 7 and qty > 0
                else " 🔴断货" if qty == 0
                else ""
            )
            lines.append(
                f"{medal} **{name}** — 评分 {score:.2f} | 利润率 {margin:.0%} | 日销 {daily:.1f}件{stock_note}"
                if not is_en else
                f"{medal} **{name}** — Score {score:.2f} | Margin {margin:.0%} | {daily:.1f}/day{stock_note}"
            )

        # 综合操作建议
        if suggestions:
            lines.append("")
            lines.append(
                "💡 **操作建议：**" if not is_en else "💡 **Action Items:**"
            )
            for s in suggestions[:3]:
                lines.append(f"  {s}")

        return AgentResponse(
            thinking=thinking,
            answer="\n".join(lines),
            suggestions=suggestions[:3],
            intent="product_recommend",
        )
