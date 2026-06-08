# Westpac Blueprint — 房贷数字化增长探索性数据分析

## Project Spec (Design Document)

**Date:** 2026-06-08
**Role:** Westpac 房贷数字化增长与产品创新 — 产品出方案前的探索性数据分析阶段
**Skill target:** 数据运营 / 数据分析师
**Estimated effort:** 20–30 hours

---

## 1. 项目定位

### 1.1 在 Blueprint 整体方案中的位置

```
┌─────────────────────────────────────────────────────────────┐
│  Westpac Blueprint 完整项目流程                               │
│                                                             │
│  [本项目的范围]          →    [后续的产品设计阶段]              │
│  探索性数据分析              产品方案与原型设计                 │
│  (Exploration Phase)        (Product Design Phase)           │
│                                                             │
│  • 多源数据接入与清洗         • Westpac Blueprint 概念应用      │
│  • 用户画像与客群分层         • 动机设计与 3D 游戏化             │
│  • 行为特征维度验证           • Readiness Score 评分引擎        │
│  • 预测建模（意向/违约）      • AI 实时计算与 T+1 反馈          │
│  • 渠道依赖量化分析           • Human-in-the-loop 合规审批      │
│  • 财务可行性测算             • 商业方案交付                    │
│                                                             │
│  ★ 回答：问题是什么？           ★ 回答：方案怎么做？             │
│     数据支撑什么洞察？                                        │
│     值不值得投入资源？                                        │
└─────────────────────────────────────────────────────────────┘
```

**本项目的核心命题**：在产品团队投入原型设计和工程资源之前，用数据回答三个问题：

> 1. **客群问题到底有多大？** — 年轻客群在流失吗？Broker 依赖到什么程度？数据怎么说？
> 2. **哪些行为特征能区分"房贷 ready"和"not ready"的客户？** — 如果未来要设计 Readiness Score，应该看哪些维度？
> 3. **值得做吗？** — 粗略算下来，去中介直营的财务可能性有多大？天花板在哪？

**本项目的产出不是产品方案**（那是后续阶段），**而是支撑产品决策的数据洞察和方向建议。**

### 1.2 数据分析能力展示

| 能力维度 | 具体体现 |
|----------|---------|
| **多表数据整合** | Home Credit 6-7 表 JOIN，模拟 CDR 协议下的多源数据聚合 |
| **数据清洗与质量** | 缺失值策略、异常值处理、编码转换 |
| **用户画像与分层** | 人口统计 + 行为聚类的客群分析，Gen Z/Millennial 专题 |
| **特征工程** | 构造 20+ 业务特征（收入稳定性、支出纪律、储蓄连贯性等） |
| **预测建模** | 违约风险模型 + 行为特征对贷款转化的预测力验证 |
| **商业测算** | 3 年财务模型（双层成本结构 + NPV + 敏感性分析） |
| **可视化沟通** | Python (Matplotlib/Seaborn) + Tableau 交互看板 |

---

## 2. 数据源

| 数据集 | 来源 | 规模 | 核心字段 |
|--------|------|------|---------|
| Home Credit application_train | Kaggle | 307K 条 | TARGET, AMT_INCOME_TOTAL, AMT_CREDIT, DAYS_BIRTH, NAME_EDUCATION_TYPE, OCCUPATION_TYPE, FLAG_OWN_CAR, FLAG_OWN_REALTY, CNT_CHILDREN, NAME_HOUSING_TYPE, ... |
| Home Credit bureau | Kaggle | 1.7M 条 | SK_ID_CURR, DAYS_CREDIT, CREDIT_DAY_OVERDUE, AMT_CREDIT_SUM, ... |
| Home Credit bureau_balance | Kaggle | 27M 条 | SK_ID_BUREAU, MONTHS_BALANCE, STATUS |
| Home Credit previous_application | Kaggle | 1.6M 条 | SK_ID_CURR, NAME_CONTRACT_TYPE, AMT_APPLICATION, NAME_CONTRACT_STATUS, ... |
| Home Credit credit_card_balance | Kaggle | 3.8M 条 | SK_ID_CURR, MONTHS_BALANCE, AMT_BALANCE, AMT_DRAWINGS_ATM_CURRENT, ... |
| Home Credit installments_payments | Kaggle | 13.6M 条 | SK_ID_CURR, DAYS_ENTRY_PAYMENT, AMT_PAYMENT, AMT_INSTALMENT, ... |
| Home Credit POS_CASH_balance | Kaggle | 10M 条 | SK_ID_CURR, MONTHS_BALANCE, SK_DPD, SK_DPD_DEF, ... |
| Bank Marketing | UCI/Kaggle | 45K 条 | age, job, balance, housing, loan, deposit (target) |

**数据映射逻辑（与 CDR 的对应关系）**：

| 数据表 | 类比 CDR 数据端点 | 分析用途 |
|--------|-------------------|---------|
| application_train | 贷款申请主表 | 客户人口统计 + 资产画像 + 申请决策 |
| bureau + bureau_balance | 征信局月度快照 | 历史信用行为、逾期模式 |
| credit_card_balance | 信用卡月度账单（交易侧） | 消费模式、非必要支出识别 |
| installments_payments | 还款流水 | 还款纪律、现金流稳定性 |
| POS_CASH_balance | 消费贷/现金贷流水 | 日常消费行为、资金需求频率 |
| previous_application | 历史贷款申请记录 | 客户贷款行为轨迹、渠道偏好（Broker vs Direct 代理变量） |
| Bank Marketing | 储蓄账户余额（补充维度） | 资产累积信号、储蓄行为参考 |

---

## 3. 项目架构

```
Homeloan_DA/
├── data/
│   ├── raw/
│   │   ├── home_credit/              # Kaggle 7 张原始 CSV
│   │   └── bank_marketing/           # UCI 原始 CSV
│   └── processed/                    # 清洗后的 Parquet/CSV 中间文件
│
├── notebooks/
│   ├── 01_data_acquisition.ipynb     # 多表接入 + 数据质量 + CDR 类比
│   ├── 02_eda_user_profiling.ipynb   # EDA + 客群分层 + Gen Z 画像
│   ├── 03_feature_engineering.ipynb  # 特征工程 + 维度验证
│   ├── 04_predictive_modeling.ipynb  # 预测建模 + SHAP 解释
│   ├── 05_business_simulation.ipynb  # 3 年财务测算 + 敏感性分析
│   └── 06_executive_summary.ipynb    # 全链路结论 + 产品方向建议
│
├── src/
│   ├── __init__.py
│   ├── config.py                     # 路径、常量、特征清单
│   ├── data_loader.py                # SQL 风格多表 JOIN
│   ├── preprocessing.py              # 清洗：缺失值、异常值、编码
│   ├── features.py                   # 特征工程 Pipeline
│   ├── model.py                      # 模型训练、交叉验证、超参调优
│   └── visualization.py              # 复用图表配置（主题、色板、尺寸）
│
├── tableau/
│   ├── westpac_blueprint_dashboard.twbx
│   └── data_exports/
│       ├── dim_customer_profile.csv        # 客群画像维度表
│       ├── fact_behavioral_features.csv    # 行为特征事实表
│       ├── agg_financial_projection.csv    # 财务预测汇总
│       └── agg_channel_analysis.csv        # 渠道对比汇总
│
├── outputs/
│   ├── figures/
│   ├── models/
│   └── reports/
│
├── requirements.txt
├── README.md
└── .gitignore
```

**环境依赖**：
```
Python 3.10+
pandas, numpy, scipy
scikit-learn, xgboost, lightgbm
matplotlib, seaborn, plotly
jupyter, ipykernel
Tableau Public 2024+（看板）
```

---

## 4. Notebook 设计（6 个）

### Notebook 01 — Data Acquisition & CDR Simulation

**目的**：接入全部数据源，评估数据质量，通过多表整合模拟 CDR 数据采集流程。

**内容**：
1. 原始 CSV 读取，报告各表行数、列数、Schema
2. 数据质量报告：各列缺失率、基数、偏度
3. **CDR 类比图示**：标注每张表在 CDR 协议下的对应数据端点
4. 核心 JOIN 链：application_train ← bureau ← bureau_balance ← previous_application → installments → credit_card
5. Bank Marketing 按人口特征对齐合并，补充储蓄余额维度
6. 导出清洗后数据至 `data/processed/`

**产出**：数据质量摘要表、合并后数据集、缺失值处理策略说明

---

### Notebook 02 — EDA & User Profiling

**目的**：探索数据分布，构建客群分层，专题分析年轻客群画像，量化 Broker 依赖程度。

**内容**：
1. **人口统计全景**：年龄金字塔、收入 × 学历分布、职业热力图
2. **Gen Z / Millennial 专题**：筛选 <35 岁客群 vs ≥35 岁对比（房屋拥有率、收入水平、负债比、贷款审批率）
3. **行为聚类**：在消费/还款/负债特征上做 K-Means → 3–4 个客群原型
4. **客群命名与解读**（示例）：
   - "财务焦虑型租房族" — 低收入、高消费波动、无房产、频繁小额贷款
   - "高负债信心型" — 高收入、多笔贷款、按时还款、有房产
   - "被动储蓄观望型" — 稳定收入、低消费、无贷款记录
5. **Broker 依赖量化**：利用 `previous_application` 的渠道相关字段，估算 Broker vs 直营占比，跨客群对比

**产出**：年龄金字塔、收入箱线图、聚类雷达图、渠道占比图、Gen Z vs 其他代际对比表

---

### Notebook 03 — Feature Engineering & Dimension Validation

**目的**：构造 6 组 20+ 业务特征，通过统计检验和无监督分层验证这些维度是否能区分不同"房贷就绪程度"的客群。

**核心思路**（与产品 Readiness Score 的关系）：
> 产品方案中需要的 Readiness Score，它的**特征维度选型依据**应该来自数据。这个 Notebook 的工作就是做这个依据——
> **不是"建一个评分引擎"，而是"验证哪些维度在数据中确实有区分力"。**

**特征组设计**：

| 维度组 | 具体特征（示例） | 数据来源 |
|--------|-----------------|---------|
| **收入稳定性** | 收入变异系数、最近工作变动距今时长、收入-贷款比 | application, bureau |
| **支出纪律** | 非必要支出占比、ATM 取现频次、信用卡额度使用率趋势 | credit_card, POS_CASH |
| **储蓄连贯性** | 估计月度盈余、零逾期月份占比、分期还款准时率 | installments, bureau_balance |
| **债务负担** | 负债收入比、活跃信贷笔数、历史最高逾期天数 | bureau, previous_application |
| **资产信号** | 是否有车、是否有房、Bank Marketing 余额代理变量 | application, bank_marketing |
| **行为轨迹** | 贷款申请频次、征信查询近期度、合同类型多样性 | previous_application, bureau |

**验证方法**：
1. 对各特征在 <35 vs ≥35、有房 vs 无房、贷款获批 vs 被拒子群间做 ANOVA / Kruskal-Wallis 检验
2. 将 6 组特征分箱 → 基于分位数构建简易分层 → 观察各层在"历史贷款获批率"上的差异
3. 输出**特征区分力排名**：哪些维度在数据中确实能区分"更可能获批贷款"的客户

**结论示例（期待产出的洞察）**：
> "在 <35 岁无房客群中，储蓄连贯性（零逾期月份占比）和收入稳定性（CV）是对贷款获批预测力最强的两个维度——这为后续产品中的 Readiness Score 特征选型提供了数据依据。"

**产出**：特征区分力排名表、分层客群 vs 贷款获批率的柱状图、各维度 ANOVA 显著性汇总

---

### Notebook 04 — Predictive Modeling

**目的**：通过 ML 建模验证行为特征对贷款决策的预测力，并用 SHAP 做可解释性分析——帮助理解"如果未来产品需要 AI 引擎，哪些特征最该被监控"。

**建模目标**：
- **Model A（违约风险）**：预测 Home Credit `TARGET`（是否违约）→ 回答"能不能还？"
- **Model B（贷款转化）**：基于已有的获批/拒绝标签，分析特征对审批结果的预测贡献 → 回答"什么行为模式更可能获批？"

**方法**：
1. Train/val/test 分层划分
2. 基线：Logistic Regression
3. XGBoost + LightGBM，5 折交叉验证
4. 超参调优（RandomizedSearchCV）
5. 评估：AUC-ROC、Precision-Recall、Confusion Matrix
6. SHAP 分析：全局特征重要性 + 单样本决策路径

**SHAP 的价值（对齐后续产品叙事）**：
> SHAP 输出揭示了"哪些行为变动对贷款获批概率影响最大"——这些就是未来 Readiness Score 中应该被监控的核心信号，也是产品中"T+1 即时正反馈"的数据基础。

**产出**：ROC 曲线、SHAP Summary Plot、特征重要性排行、混淆矩阵

---

### Notebook 05 — Business Simulation

**目的**：在分析结论基础上做粗略的商业可行性测算——"如果基于这些洞察去推进直营方案，账算得过来吗？"

**关键区分**：
> 这个模型不是给行方看的 final business case，而是**exploration 阶段的可行性校验**——回答"值得继续投入资源做详细方案吗？"

**模型假设与输入**：

| 参数 | 取值 | 来源/说明 |
|------|------|-----------|
| 目标市场（<35 澳洲租房者） | 1.1M | ABS 住房数据引用 |
| 预期触达率 | 8%–25%（基准 18%） | 基于客群分层中"可转化"占比 |
| 平均贷款额 | AUD 450,000 | 行业均值 |
| Broker 佣金（upfront + trail） | 0.60% + 0.15% | 澳洲行业公开数据 |
| 折现率 | 4% | RBA 现金利率参考 |

**双层成本结构**：

*固定成本（年化）：*

| 科目 | 金额 | 说明 |
|------|------|------|
| 技术平台建设摊销 | 1.2M | 3 年摊销 |
| 合规法务 | 0.5M | 监管审核 + 文档 |
| 数据分析团队 | 0.8M | 2-3 人 |
| **固定成本合计** | **2.5M / 年** | |

*变动成本：* AUD 50 / 活跃用户 / 年（数字营销获客 + 运营维护）

**3 年 P&L（基准场景，触达率 18%）**：

| | Y1 | Y2 | Y3 |
|---|----|----|-----|
| 活跃用户（累计） | 40K | 80K | 120K |
| 贷款转化数 | 2.4K | 6K | 10.8K |
| 贷款发放额 (M) | 1,080 | 2,700 | 4,860 |
| (+) 佣金节省 (M) | 8.1 | 20.3 | 36.5 |
| (-) 固定成本 (M) | 2.5 | 2.5 | 2.5 |
| (-) 变动成本 (M) | 2.0 | 4.0 | 6.0 |
| **(=) 净收益 (M)** | **3.6** | **13.8** | **28.0** |

**DCF 计算**：
```
NPV (r=4%) = 3.6 + 13.8/1.04 + 28.0/1.04² ≈ 42.0M
总投资 = 2.5×3 + 2.0+4.0+6.0 = 19.5M
ROI = 42.0 / 19.5 ≈ 2.2x（累计 NPV / 累计投资）
```

**敏感性分析**：

| 场景 | 触达率 | ROI | 评估 |
|------|--------|-----|------|
| 悲观 | 8% | 0.8x | 触达不足，需重构增长策略 |
| 基准 | 18% | 2.2x | 可行，但需要验证触达假设 |
| 乐观 | 25% | 3.5x | 强吸引力，值得推进详细方案 |

**结论形式**（关键——不是说"这个项目能赚 5000 万"，而是）：
> 在保守假设（触达 18%、折现 4%）下，3 年累计净现值约 4200 万澳元，ROI 约 2.2 倍。敏感性分析表明，只要触达率不低于 12%，项目在经济上具备可行性。**建议：推进详细产品方案设计。**

**产出**：3 年费用-收益瀑布图、敏感性龙卷风图、盈亏平衡时间线

---

### Notebook 06 — Executive Summary

**目的**：整合全部分析结论，输出一份可供内部决策的探索性分析简报。

**结构**（一页式故事线）：

1. **我们发现了什么问题？**
   - 一张图：<35 客群房屋拥有率 vs Broker 依赖度的交叉分析
   - 一句话：年轻客群想买房但被传统流程卡住，银行在为他们付费给 Broker

2. **数据支撑的关键洞察**
   - 一张图：6 个行为特征维度 × 贷款获批率的区分力矩阵
   - 一句话：储蓄连贯性和收入稳定性是最强的两个区分维度，但它们不是你申请表上填的那些字段

3. **如果推进直营方案，可能的路径？**
   - 一张图：客群分层 → 差异化策略建议（哪些该被"孵化"，哪些该被"即时转化"）
   - 一句话：至少 X% 的年轻客群行为模式显示他们是"可培养的潜在房贷客户"

4. **从账上来看值不值得？**
   - 一张图：基准 + 乐观 + 悲观三场景下的 ROI 对比
   - 一句话：基准场景下 3 年 NPV ~4200 万，触达率是关键杠杆

5. **建议与风险**
   - 建议：推进产品方案设计，优先验证触达假设
   - 风险：触达率不确定性、CDR 合规成本、Broker 渠道反弹

**产出**：一张 A4 篇幅的结构化结论摘要（Markdown 表格 + 关键图表嵌入）

---

## 5. Tableau 看板设计（3 页）

### Dashboard 1：客群洞察
- 年龄分布直方图（高亮 <35 区域）
- 收入 × 职业热力图
- 客群聚类概览（小多图 bar chart）
- KPI 卡片：分析客户总数、Gen Z 占比、Broker 依赖度、平均触达预期

### Dashboard 2：行为特征与预测
- 6 个特征维度的区分力排名（横向柱状图）
- SHAP Top-10 特征重要性
- 特征分层 → 贷款获批率的漏斗/桑基图
- 分层客群数量 × 预期转化率的散点图

### Dashboard 3：财务可行性
- 3 年瀑布图（成本 → 节省 → 净收益）
- ROI 仪表盘（标注 2.2x 基准值）
- 敏感性滑块：触达率 8%–25% → 自动刷新 ROI
- 盈亏平衡月标记

### 数据导出策略
Python 输出 4 张 CSV → Tableau 接入：

| CSV | 内容 | 粒度 |
|-----|------|------|
| `dim_customer_profile.csv` | customer_id, age, income, education, cluster, feature_scores | 客户级 |
| `fact_behavioral_features.csv` | customer_id, 6 个维度分数, model_prediction, shap_top_feature | 客户级 |
| `agg_financial_projection.csv` | scenario, year, cohort_size, converted_loans, costs, savings, net | 年 × 场景 |
| `agg_channel_analysis.csv` | channel, customer_segment, volume, avg_commission, conversion_rate | 渠道 × 客群 |

---

## 6. 实施路线

### Phase 1：数据基础（Notebook 01–02）
- 搭建项目目录和 src 模块
- 下载数据集，加载，清洗
- EDA + 客群分层
- **🚩 Checkpoint**：数据清洗完成，初步图表产出

### Phase 2：分析核心（Notebook 03–04）
- 特征工程 Pipeline
- 维度验证（统计检验 + 分层分析）
- 预测模型训练与评估
- SHAP 可解释性
- **🚩 Checkpoint**：特征区分力排名产出，模型 AUC > 0.75

### Phase 3：商业与输出（Notebook 05–06）
- 双层成本财务模型
- 敏感性分析
- 导出 Tableau CSVs
- 完成探索结论简报
- **🚩 Checkpoint**：全部分析数字与叙事对齐

### Phase 4：看板（Tableau）
- 搭建 3 页交互看板
- 接入导出数据
- 打磨交互与 tooltip
- 打包 .twbx
- **🚩 Checkpoint**：看板交付物完成

---

## 7. 范围边界

| 不在本次范围 | 原因 |
|-------------|------|
| Readiness Score 产品引擎 | 数据探索阶段只做维度验证，评分引擎属于后续产品设计 |
| 3D 游戏化原型 / Figma 交互 | 已完成，属于产品设计阶段 |
| ASIC/APRA 详细合规审查 | 无公开数据集支撑，属于法务团队工作 |
| AI Agent / RAG 合规审核 | 独立项目，后续单独做 |
| A/B 测试实验设计 | 无实时流量和对照组数据 |
| 实时数据管道 / 流处理 | 探索阶段用历史数据即可 |

---

## 8. 成功标准

- [ ] 6 个 Notebook 端到端无报错可运行
- [ ] 6 个行为特征维度完成区分力验证，产出排名
- [ ] 至少一个预测模型 AUC > 0.75
- [ ] SHAP 分析产出可解释的特征贡献列表
- [ ] 财务模型含双层成本 + NPV + 3 场景敏感性分析
- [ ] Tableau 看板含 3+ 交互元素
- [ ] 探索结论清晰回答"三个核心问题"（见 Section 1.1）
- [ ] README 叙事可让面试官 5 分钟内理解项目故事线
