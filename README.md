# RetailSense 🛒

[![CI](https://github.com/yinqiqi1005-crypto/retail-sense/actions/workflows/test.yml/badge.svg)](https://github.com/yinqiqi1005-crypto/retail-sense/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)]()

> AI 零售选品与库存决策系统 — 从 3 年瑞幸店长经验中生长出来的工具

## 设计理念

在瑞幸管理 200+ SKU 和 28% 食材成本率红线的 3 年中，我发现：

**真正吃掉利润的不是成本，而是滞销。**

一个毛利 70% 但年销 1 次的 SKU，不如毛利 35% 但月销 3 次的耗材。

RetailSense 把这一洞察 AI 化——让每一个小卖家也能用数据做决策，而不是凭感觉。

## 核心特性

- 🔍 **智能选品**：多维加权评分引擎（复购率权重最高 30%，致敬瑞幸经验）
- 💰 **红线定价**：成本逐项拆解 + 28% 利润率红线 + 利润模拟
- 📊 **库存预测**：周转天数 + 安全库存 + 补货建议 + 滞销预警
- ✍️ **AI 文案生成**：3 种风格（SEO / 社交种草 / 销售转化），支持流式输出
- 🎯 **客户意图分析**：匹配 4 类客户画像，自动推荐最佳销售角度
- 💬 **促单话术生成**：开场 + 异议处理 + 促单，Hybrid Rule + LLM

## 评分方法

| 维度 | 权重 | 业务逻辑 |
|------|:---:|------|
| 复购率 | 30% | 高复购 > 高毛利。耗材类产品长期价值远超一次性爆品 |
| 竞争度 | 25% | 竞品越少，定价权越大。45% 的利润流失来自价格战 |
| 搜索趋势 | 25% | 上升期品类自带 30-50% 自然流量红利 |
| 毛利率 | 20% | 重要但不唯一。高毛利低流速 = 库存积压 = 隐性亏损 |

## 快速开始

```bash
git clone https://github.com/yinqiqi1005-crypto/retail-sense.git
cd retail-sense
pip install -r requirements.txt
streamlit run app.py
```

## 项目结构

```
retail-sense/
├── retail_sense/
│   ├── scorer.py        # 选品评分引擎
│   ├── pricing.py       # 定价模型 + 利润模拟
│   ├── inventory.py     # 库存预测 + 补货建议
│   ├── copywriter.py    # AI 文案生成器
│   ├── intent.py        # 客户意图分析
│   └── sales_script.py  # 促单话术生成
├── app.py               # Streamlit Web 面板
├── images/              # 本地图片（可替换）
└── docs/                # MkDocs 文档
```

## 作者

Nancy — 3 年瑞幸店长 × AI 工具链  
「零售运营的 AI 系统化」

## License

MIT
