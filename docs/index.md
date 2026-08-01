# 🛒 RetailSense

**AI 零售选品与库存决策系统**

从"凭感觉进货"到"数据驱动决策"——把 3 年瑞幸店长的库存管理经验，AI 化。

## ✨ 核心特性

- 🔍 **智能选品**：多维加权评分（毛利 × 竞争度 × 趋势 × 复购率）
- 💰 **红线定价**：成本拆解 + 28% 利润率红线 + 利润模拟
- 📊 **库存预测**：周转天数 + 安全库存 + 补货建议

## 🚀 安装

```bash
git clone https://github.com/yinqiqi1005-crypto/retail-sense.git
cd retail-sense
pip install -r requirements.txt
```

## 🖥️ 启动

```bash
# Web 面板
streamlit run app.py

# 或命令行
python -c "from tests.test_scorer import test_scorer; test_scorer()"
```
