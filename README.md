# Westpac Blueprint — 房贷数字化增长探索性数据分析

**端到端数据分析项目 | 为去中介化数字房贷产品提供数据支撑与可行性验证**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Tableau](https://img.shields.io/badge/Tableau-Dashboard-orange.svg)](https://public.tableau.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 项目背景

为 Westpac Blueprint 产品方案提供探索期的数据支撑和可行性验证。在产品团队投入原型设计之前，用数据回答三个核心问题：

1. **年轻客群问题和 Broker 依赖到底有多大？**
2. **哪些行为特征能区分「房贷就绪」和「房贷未就绪」的客户？**
3. **去中介化直营方案在财务上是否可行？**

---

## 数据来源

| 数据集 | 来源 | 规模 | 用途 |
|--------|------|------|------|
| **Home Credit Default Risk** | Kaggle | 7 张关联表，58M+ 行 | 信贷行为主分析库：人口统计、征信快照、还款流水、消费模式、历史申请 |
| **Bank Marketing** | UCI | 45K 行 | 储蓄维度补充：含 `balance` 字段，按年龄-收入段同分布映射后与主画像交叉验证 |

---

## 项目结构

```
├── notebooks/                          # 6 个 Jupyter Notebook (核心交付)
│   ├── 01_data_acquisition.ipynb       # 多源数据接入 + CDR 模拟 + 数据质量
│   ├── 02_eda_user_profiling.ipynb     # EDA + Gen Z 画像 + K-Means 客群分层
│   ├── 03_feature_engineering.ipynb    # 特征工程 + ANOVA 维度验证
│   ├── 04_predictive_modeling.ipynb    # XGBoost/LightGBM + SHAP 解释性
│   ├── 05_business_simulation.ipynb    # 3 年财务模型 + 敏感性分析
│   └── 06_executive_summary.ipynb      # 探索结论 + 产品方向建议
│
├── src/                                # 可复用 Python 模块
│   ├── data_loader.py                  # 7 表多源 JOIN (模拟 CDR 聚合)
│   ├── preprocessing.py                # 数据清洗、缺失值处理、编码
│   ├── features.py                     # 20+ 业务特征工程
│   ├── model.py                        # XGBoost/LightGBM 建模 + SHAP
│   └── visualization.py                # Westpac 主题可视化
│
├── tableau/                            # Tableau 交互看板
│   ├── westpac_blueprint.twb           # 工作簿文件
│   ├── data_exports/                   # 4 个 CSV 数据源
│   └── TABLEAU_SETUP_GUIDE.md          # 建表指南
│
├── outputs/
│   ├── figures/                        # 图表导出
│   ├── models/                         # 训练好的模型
│   └── reports/                        # HTML 报告 + 模型评估
│
├── docs/superpowers/specs/             # 设计文档
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 关键分析成果

### 用户画像与客群分层

聚焦 <35 岁年轻客群，通过 10 维行为特征（还款记录、消费模式、信贷历史）做 K-Means 聚类，识别出 3 类行为模式：

| 客群类型 | 特征 | 产品策略 |
|----------|------|---------|
| **财务焦虑型租房族** | 有还款能力但没首付，决策瘫痪 | 24 个月「用户孵化」核心目标 |
| **数字自信型消费族** | 收入不错但消费支出高 | 游戏化预算管理 + 支出纪律 nudges |
| **保守观望型** | 信用档案薄，传统评分无法评估 | CDR 数据（房租、水电）弥补信用画像 |

**核心结论：** 年轻客群不是「高风险」，而是「未被服务」。

### 行为特征工程与验证

构建 6 组 20+ 业务特征，ANOVA 检验全部对贷款违约具有显著区分力（p < 0.001），为产品 Readiness Score 的特征选型提供数据依据。

| 维度 | 特征示例 | 区分力 |
|------|---------|--------|
| 收入稳定性 | 工作年限、收入-贷款比 | 显著 |
| 储蓄连贯性 | 还款逾期率、零逾期月占比 | **最高** |
| 债务负担 | 债务收入比、活跃信贷笔数 | 强 |
| 支出纪律 | 信用卡利用率、ATM 取现频率 | 中-强 |
| 行为轨迹 | 历史申请通过率、申请频次 | 中 |
| 资产信号 | 是否有房、是否有车 | 辅助 |

### 预测建模与 SHAP 解释性

| 指标 | 值 |
|------|-----|
| 最佳模型 | XGBoost (48 特征，调参后) |
| AUC-ROC | 0.715 |
| 特征工程 | 原始行为特征 + composite scores |

**SHAP 关键发现：** 还款逾期率和历史申请行为模式是最强的违约预测因子，而非传统认知中的收入或资产——验证了动态行为数据比传统静态填表更有预测力。

### 商业可行性测算

| 场景 | 触达率 | NPV | ROI |
|------|--------|-----|-----|
| 悲观 | 8% | ~1，830 万 | 1.12x |
| **基准** | **18%** | **~5，010 万** | **1.84x** |
| 乐观 | 25% | ~7，240 万 | 2.07x |

**结论：** 触达率 ≥ 12% 即可实现正回报，方向可行，建议推进详细产品方案设计。

---

## 依赖与环境

```bash
pip install -r requirements.txt
```

### 数据准备

1. **Home Credit Default Risk** — [Kaggle 链接](https://www.kaggle.com/c/home-credit-default-risk/data)（需接受竞赛规则）→ 解压到 `data/raw/home_credit/`
2. **Bank Marketing** — [UCI 链接](https://archive.ics.uci.edu/ml/datasets/bank+marketing) → 放 `data/raw/bank_marketing/`

### 运行 Notebooks

```bash
jupyter notebook
```

按 01 → 06 顺序执行，或：

```bash
foreach ($nb in @("01","02","03","04","05","06")) { jupyter nbconvert --to notebook --execute notebooks\${nb}_*.ipynb --output-dir notebooks\ --inplace }
```

### Tableau 看板

打开 `tableau/westpac_blueprint.twb` 或参考 `tableau/TABLEAU_SETUP_GUIDE.md` 手动搭建。

---

## 技术栈

| 层 | 工具 |
|----|------|
| 数据处理 | Pandas, NumPy |
| 统计分析 | SciPy (t-test, ANOVA) |
| 机器学习 | Scikit-learn, XGBoost, LightGBM |
| 可解释性 | SHAP |
| 可视化 | Matplotlib, Seaborn, Tableau |
| 环境 | Python 3.10+, Jupyter Notebook |

---

## 关于此项目

本项目是个人作品集项目，目标岗位为**数据运营 / 数据分析师**。它是 Westpac Blueprint 产品方案的前置探索阶段——在产品原型设计之前，用数据验证市场假设和方向可行性。

> 产品方案阶段（Figma 原型、动机设计、Readiness Score 产品引擎、Human-in-the-loop 合规设计）为独立工作，不在此仓库中。
