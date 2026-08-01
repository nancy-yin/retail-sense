# 快速开始

## 命令行使用

```python
from retail_sense import ProductScorer

scorer = ProductScorer()
products = [
    {
        "name": "刻字狗牌",
        "cost": 2.80,        # 成本
        "price": 12.99,      # 售价
        "competitors": 35,   # 竞品数量
        "search_growth": 22, # 搜索增长率(%)
        "trend_up": True,    # 趋势方向
        "annual_purchases": 2.5, # 年购买次数
        "is_consumable": False,  # 是否耗材
    },
]
results = scorer.rank(products)
for r in results:
    print(f"{r.product_name}: {r.final_score}分")
```

## Web 面板

```bash
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501`，即可看到选品评分和定价模型面板。
