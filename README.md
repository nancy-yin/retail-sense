# RetailSense 🛒

[![CI](https://github.com/yinqiqi1005-crypto/retail-sense/actions/workflows/test.yml/badge.svg)](https://github.com/yinqiqi1005-crypto/retail-sense/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)]()

> AI 零售选品与库存决策系统 — 从"凭感觉"到"看数据"

## ✨ 核心特性

- 🔍 **智能选品**：多维评分引擎（毛利率 × 竞争度 × 搜索趋势 × 复购率）
- 💰 **红线定价**：成本拆解 + 最低利润率预警（致敬瑞幸 28% 成本率红线）
- 📊 **库存预测**：周转天数 + 安全库存 + 补货建议 + 滞销预警

## 🚀 快速开始

```bash
git clone https://github.com/yinqiqi1005-crypto/retail-sense.git
cd retail-sense
pip install -r requirements.txt
python tests/test_scorer.py
```

## 📖 使用示例

```python
from retail_sense import ProductScorer

scorer = ProductScorer()
products = [
    {"name": "刻字狗牌", "cost": 2.80, "price": 12.99, "competitors": 35, "search_growth": 22, "trend_up": True, "annual_purchases": 2.5, "is_consumable": False},
]
results = scorer.rank(products)
for r in results:
    print(f"{r.product_name}: {r.final_score}分")
```

## 🏗️ 项目结构

```
retail-sense/
├── retail_sense/
│   ├── scorer.py      # 选品评分引擎
│   ├── pricing.py     # 定价模型 + 利润模拟
│   └── inventory.py   # 库存预测 + 补货建议
├── tests/
│   └── test_scorer.py # 宠物饰品 8 SKU 验证
└── examples/
    └── pet_accessories/
```

## 👤 作者

Nancy — 3年瑞幸店长 × AI 工具链  
「零售运营的 AI 系统化」

## 📄 License

MIT
