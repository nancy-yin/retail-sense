# RetailSense v2.5.1 修复版 — 项目清单

> 备份文件：`RetailSense_v2.5_20260806_final.bundle` (801KB)  
> 恢复命令：`git clone RetailSense_v2.5_20260806_final.bundle retail-sense`

---

## 📊 项目概况

| 项目 | 数据 |
|------|------|
| 名称 | RetailSense — AI 零售选品与库存决策系统 |
| 版本 | v2.5.1 |
| 语言 | Python 3.11 + Streamlit |
| 代码量 | 当前本地副本 26 个 .py 文件；主程序与包约 6,300 行 |
| 开发时长 | 作者记录 15.5 小时（4天，未独立验证） |
| Git 提交 | 当前 HEAD 可核验为 46 commits |
| GitHub | github.com/yinqiqi1005-crypto/retail-sense |
| 公网 | 历史演示地址（当前可用性待确认） |

---

## 🏗 模块架构

```
retail-sense/
├── app.py                       # Streamlit 主程序 (1900+行)
├── retail_sense/
│   ├── scorer.py                # 选品评分引擎 (100行)
│   ├── pricing.py               # 定价模型 + 28%红线 (100行)
│   ├── inventory.py             # 库存计算 (80行)
│   ├── copywriter.py            # 文案生成器 v3: 8品×3风格 (380行)
│   ├── sales_script.py          # 销售话术生成 (170行)
│   ├── intent.py                # 客户意图分析 (130行)
│   ├── agents.py                # 4Agent流水线 (200行)
│   ├── logistics.py             # 物流配发模块 (300行)
│   ├── dataloader.py            # 多公司数据接入 (130行)
│   ├── data_persistence.py      # 数据持久化 (80行)
│   ├── regions.py               # 5大市场区域数据 (130行)
│   ├── cases.py                 # 案例库 (60行)
│   ├── agent.py                 # 智能管家v3 (1100行)
│   ├── auth.py                  # 登录认证+角色权限 (200行)
│   ├── security.py              # PBKDF2 密码哈希与旧哈希迁移
│   ├── text_safety.py           # HTML/CSV/文件名安全处理
│   ├── i18n.py                  # 中英双语字典 (170行)
│   └── product_images.py        # 产品图base64 (168KB)
├── images/products/             # 8张产品图 (200×200)
├── scripts/
│   ├── auth_manager.py          # 管理员密码管理
│   └── generate_product_images.py # 产品图生成脚本
├── .auth/                       # 凭证+配置 (gitignore)
├── data/                        # 公司数据 (gitignore)
├── requirements.txt
├── requirements-dev.txt         # 测试与静态检查依赖
├── tests/                       # 13 项核心回归测试
├── RetailSense.command          # 桌面启动脚本
└── RetailSense_v2.5_20260806_final.bundle  # Git备份
```

---

## 📋 功能清单

| # | 页面 | 功能 |
|---|------|------|
| 1 | 工作台 | 出入库仪表盘 + 智能管家 + 库存健康卡片 |
| 2 | 案例库 | 3家虚拟业务案例（萌爪宠物/PawStyle/Bark&Co），指标与评价均为演示设定 |
| 3 | 选品评分 | 4维加权评分 + 5大市场区域分析 + 内置活动日历 |
| 4 | 定价模型 | 成本拆解 + 7种货币内置演示汇率换算 |
| 5 | 销售自动化 | Scout→Price→Copy→Monitor 四Agent流水线 |
| 6 | 库存监控 | 分页表格 + 库存概览卡片 |
| 7 | 商品上架 | Shopify/Etsy/独立站模拟上架与本地记录 |
| 8 | 物流配发 | 34单模拟 + 配货 + 虚拟快递6阶段追踪 |
| 9 | 导出报表 | CSV/文本格式一键下载 |
| + | 登录系统 | admin/user 角色权限分离 |

---

## 📁 数据文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 公司数据 | `~/Desktop/宠物饰品公司案例/` | 3家虚拟公司 JSON |
| 账号密码 | `~/Desktop/📊日上/账号密码.json` | 可视凭证文件 |
| 管理员凭证 | `.auth/admin_cred.json` | 加盐 PBKDF2 哈希存储（兼容旧哈希自动迁移） |
| 平台配置 | `.auth/platform_config.json` | Shopify/Etsy/物流 API |
| 配货记录 | `.auth/allocation_log.json` | 持久化 |
| 上架记录 | `.auth/listing_log.json` | 持久化 |
| Git 备份 | `RetailSense_v2.5_20260806_final.bundle` | 801KB |

---

## 🔐 登录凭证

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | 本地设置，不在文档中提供 |
| 员工 | 自行注册 | 自设 |

---

## 🚀 启动方式

```bash
# 方式1：命令行
cd ~/projects/retail-sense
streamlit run app.py

# 方式2：桌面双击
~/Desktop/RetailSense.command

# 方式3：公网访问（需保持本机运行）
# 先用 ssh -R 80:localhost:8501 serveo.net 建立隧道
```

---

## 🔄 恢复备份

```bash
git clone ~/projects/retail-sense/RetailSense_v2.5_20260806_final.bundle retail-sense-restored
```

---

---

## 🎤 面试介绍话术

### 这是什么类型的软件？

**Web 应用（SaaS 工具）—— 不是传统 App。**

| 传统软件 | RetailSense |
|------|------|
| 下载 .exe / 去 App Store | ❌ 不用 |
| 交开发者年费上架 | ❌ 免了 |
| 不同系统装不同版本 | ❌ 不需要 |
| **浏览器打开即用** | ✅ |
| **手机电脑平板全兼容** | ✅ |
| **独立登录系统 + 权限管理** | ✅ |
| **规则式虚拟管家辅助决策** | ✅ |

### 30秒电梯演讲

> 「RetailSense 是面向宠物饰品零售的本地演示型 SaaS 原型。打开浏览器即可使用，覆盖选品评分、多币种演示定价、库存监控和模拟物流追踪，并通过规则式助手给出可解释的运营建议，支持中英双语。」

### 类比

就像 **Notion、飞书文档、ChatGPT** 那样——打开网址，登录，直接工作。但它是专门给宠物跨境零售用的。

### 版本信息

- **当前 v2.5.1**（2026-08-10）：计算与安全修复版
- 8 个业务模块 + 登录认证 + 数据持久化
- GitHub 开源：github.com/yinqiqi1005-crypto/retail-sense

---

*2026-08-06 · 15.5h 开发 · 7,000行代码 · 30+ commits*
