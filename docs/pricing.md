# 定价模型

## 成本拆解

```python
from retail_sense.pricing import CostBreakdown

cost = CostBreakdown(
    raw_material=2.80,  # 裸件
    processing=1.20,    # 加工
    packaging=0.50,     # 包装
    shipping=1.50,      # 物流
    platform_fee=0.85,  # 平台费
)
print(cost.summary())
```

## 红线定价

- **28% 红线**：致敬瑞幸食材成本率 28% 红线
- **建议售价**：采用成本倍率法，默认 45% 目标利润
- **利润模拟**：模拟不同售价下的利润变化
