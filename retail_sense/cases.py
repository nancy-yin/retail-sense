"""RetailSense — 虚拟业务案例库（公司、评价和效果数据均为演示设定）。"""
CASES = [
    {
        "is_virtual": True,
        "company": "萌爪宠物用品（杭州）",
        "industry": "宠物饰品跨境电商",
        "problem": "8个SKU手工管理库存，漏单率12%，选品靠老板直觉，年亏$4,200囤货成本",
        "solution": "接入 RetailSense 选品评分+库存监控。自动识别珐琅名牌为TOP1（评分62分），清退宠物领结（评分<50）。补货触发从人工记忆→自动预警。",
        "before": {"time":"日均3.5h盘点","cost":"囤货损失$4,200","people":"1人","error":"漏单率12%"},
        "after": {"time":"日均10min监控","cost":"囤货损失$680","people":"0人","error":"漏单率0%"},
        "region": "北美",
        "products_used": ["珐琅名牌","亚克力牌","牵引绳套装"],
        "testimonial": "以前每天花3小时对库存，现在RetailSense 10分钟搞定。珐琅名牌评分最高、利润率81%，果断加库存——黑五卖了300单。",
        "stage": "选品+库存",
    },
    {
        "is_virtual": True,
        "company": "PawStyle Studio (上海)",
        "industry": "宠物配饰设计品牌",
        "problem": "定价凭感觉，8个产品利润率从15%到55%参差不齐。发光项圈定价$24.99实际毛利不到30%，低于28%红线。",
        "solution": "接入定价模型计算每个SKU的最优售价。发光项圈建议提价至$29.99（利润率45%），宠物领结从$9.99→$12.99。自动生成三套营销文案上架。",
        "before": {"time":"每天2h算价","cost":"利润率32%","people":"1人","error":"漏算平台费"},
        "after": {"time":"一键生成方案","cost":"利润率51%","people":"0人","error":"0误差"},
        "region": "日韩",
        "products_used": ["发光项圈","宠物领结","宠物手链","换牙零食"],
        "testimonial": "RetailSense告诉我发光项圈该卖$29.99的时候我还犹豫——怕太贵没人买。结果Etsy上$29.99的销量比$24.99多了30%，因为价格本身就是品质暗示。",
        "stage": "定价",
    },
    {
        "is_virtual": True,
        "company": "Bark & Co. (加州)",
        "industry": "宠物食品+饰品",
        "problem": "准备在黑五前上新品，但不知道5个候选产品中哪个最强。Etsy/Amazon竞品数据太多，做决策要花一周。",
        "solution": "启用销售自动化Pipeline：Scout选品评分→Price定价→Copy文案→Monitor监控。5个产品全流程自动化，定位换牙零食为黑五爆款（复购率8次/年+利润率75%）。",
        "before": {"time":"选品1周","cost":"翻车率40%","people":"2人","error":"手动竞品分析"},
        "after": {"time":"Agent全流程","cost":"翻车率8%","people":"0人","error":"实时竞品数据"},
        "region": "北美",
        "products_used": ["换牙零食","刻字狗牌","珐琅名牌","发光项圈","牵引绳套装"],
        "testimonial": "黑五前跑了一遍Pipeline，Agent直接告诉我换牙零食TOP1——复购率8次是杀手锏。当天备了500单，黑五第一天卖空。这个系统就是我的选品大脑。",
        "stage": "销售自动化",
    },
]


def get_cases() -> list[dict]:
    return CASES


def case_summary(case: dict) -> str:
    return f"""{case['company']}
行业：{case['industry']}
痛点：{case['problem'][:80]}...
解决：{case['solution'][:80]}...
效果：成本从{case['before']['cost']} → {case['after']['cost']}"""
