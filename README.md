# RetailSense 🛒

[![CI](https://github.com/yinqiqi1005-crypto/retail-sense/actions/workflows/test.yml/badge.svg)](https://github.com/yinqiqi1005-crypto/retail-sense/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)

> **前瑞幸咖啡店长 × AI 零售全链路决策系统**  
> 3年200+SKU管理经验AI化 — 从选品评分到物流配发，4个Agent自动跑完

---

## 📋 功能总览

| 模块 | 功能 | 说明 |
|------|------|------|
| 📊 工作台 | 出入库仪表盘 + 智能管家 | 今日/本周/本月营收KPI，库存健康度卡片 |
| 📖 案例库 | 3家真实公司案例 | 萌爪宠物/PawStyle/Bark&Co，含前后对比数据 |
| 📈 选品评分 | 8维加权评分 + 区域市场 | 5大市场(北美/欧洲/东南亚/日韩/澳洲)，实时活动日历 |
| 💰 定价模型 | 成本拆解 + 7种货币换算 | 28%红线利润模型，实时汇率 |
| 🤖 销售自动化 | Scout→Price→Copy→Monitor | 4Agent全自动流水线，一键上品 |
| 📦 库存监控 | 周转天数 + 安全库存 + 补货 | 分页表格，实时预警 |
| 📤 商品上架 | 一键上架 Shopify/Etsy/独立站 | 自动生成完整Listing，上架记录管理 |
| 🚚 物流配发 | 34单模拟 + 虚拟快递追踪 | 接单→配货→出库→运输→签收，6阶段追踪 |
| 📥 导出报表 | CSV/文本格式 | 一键下载产品清单+营收报告 |

---

## 🚀 快速开始

```bash
# 1. 克隆
git clone https://github.com/yinqiqi1005-crypto/retail-sense.git
cd retail-sense

# 2. 安装
pip install -r requirements.txt

# 3. 启动
streamlit run app.py
```

或双击桌面 **RetailSense.command** 一键启动。

---

## 🔐 登录系统

| 角色 | 账号 | 权限 |
|------|------|------|
| 管理员 | `admin` | 平台API配置、图片管理、公司设置 |
| 员工 | 自行注册 | 物流配发、商品上架、日常运营 |

---

## 🏗 技术架构

```
RetailSense
├── app.py               # Streamlit 主程序
├── retail_sense/
│   ├── scorer.py         # 多维评分引擎
│   ├── pricing.py        # 定价模型（28%红线）
│   ├── inventory.py      # 库存计算
│   ├── copywriter.py     # 8品×3风格文案
│   ├── sales_script.py   # 销售话术
│   ├── agents.py         # 4Agent流水线
│   ├── logistics.py      # 物流配发
│   ├── dataloader.py     # 多公司数据接入
│   ├── regions.py        # 5大市场区域数据
│   ├── cases.py          # 案例库
│   ├── agent.py          # 智能管家v3
│   ├── auth.py           # 登录认证+角色权限
│   └── data_persistence.py # 数据持久化
└── images/products/      # 8张产品图
```

---

## 👤 作者

**Nancy** — 前瑞幸咖啡店长(3年)，200+SKU管理经验  
将零售一线经验AI系统化，构建跨境电商全链路决策工具

---

*Built with Streamlit + Python · MIT License*
