# Westpac Blueprint — Tableau Dashboard Setup Guide

**3-pg Interactive Dashboard** | Data source: `tableau/data_exports/*.csv`

---

## 0. 准备工作

**下载 Tableau Public（免费）**
https://public.tableau.com/app/discover → 下载安装

**4 个数据文件**
```
tableau/data_exports/
├── dim_customer_profile.csv         # 客群画像 (307K rows)
├── fact_behavioral_features.csv     # 行为评分 (307K rows)  
├── agg_financial_projection.csv     # 财务预测 (9 rows, 3 scenarios × 3 years)
└── agg_channel_analysis.csv         # 渠道对比 (2 rows)
```

---

## 1. 连接数据

1. 打开 Tableau Public
2. **Data → New Data Source → Text file**
3. 选 `dim_customer_profile.csv` → 会创建第一个连接
4. **Data → New Data Source → Text file** → 选 `fact_behavioral_features.csv`
5. 重复，加载全部 4 个文件

**建立关联关系（Relationships）：**
- **Data → Edit Relationships**
- 在 `dim_customer_profile` 和 `fact_behavioral_features` 之间：
  - `dim_customer_profile.SK_ID_CURR` ↔ `fact_behavioral_features.SK_ID_CURR`
- 其他表是聚合表，不需要关联（详情里单独使用）

> **Tip:** 如果你用的是 Tableau 2020.2+，默认用 Relationships（逻辑层）——比 Blends 灵活。在 Data pane 里把 `SK_ID_CURR` 从一张表拖到另一张表上也能建立关联。

---

## 2. 创建计算字段

**Data pane → 右键 → Create Calculated Field**

### 2.1 客群标签（Customer Segment Label）
```
Name: SegmentLabel
Formula:
IF [IS_YOUNG] = 1 AND [owns_realty] = 0 THEN "Young Renter"
ELSEIF [IS_YOUNG] = 0 AND [owns_realty] = 1 THEN "Mature Homeowner"
ELSEIF [IS_YOUNG] = 1 AND [owns_realty] = 1 THEN "Young Homeowner"
ELSE "Mature Renter"
END
```

### 2.2 收入等级（Income Band Label）
```
Name: IncomeBand
Formula:
IF [income_total] < 50000 THEN "Low (<50K)"
ELSEIF [income_total] < 100000 THEN "Medium (50K-100K)"
ELSEIF [income_total] < 200000 THEN "High (100K-200K)"
ELSE "Very High (>200K)"
END
```

### 2.3 ROI 仪表盘颜色（ROI Color）
```
Name: ROIColor
Formula:
IF [ROI] >= 2.0 THEN "🟢 Strong"
ELSEIF [ROI] >= 1.0 THEN "🟡 Positive"
ELSE "🔴 Below Breakeven"
END
```

---

## 3. Dashboard 1：客群洞察（Customer Intelligence）

**布局：一张大看板，分 4 个区域**

### Sheet 1.1：年龄分布直方图
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `AGE_YEARS` (bin → 右键 Create Bins, size=2) |
| 拖到 Rows | `COUNTD(SK_ID_CURR)` |
| 拖到 Color | `IS_YOUNG` (调色：红色=1, 灰色=0) |
| 拖到 Label | `COUNTD(SK_ID_CURR)` |
| 拖到 Filter | `AGE_YEARS` → Range 18-70 |
| Title | "Age Distribution — Young vs Mature" |

**可视化优化：**
- Marks 选 Bar
- Color: 编辑颜色 → 红色 = `#DA291C`, 灰色 = `#6C757D`
- 把 `IS_YOUNG` 改名为显示标签 "Cohort"（右键 → Aliases: 1="Gen Z / Millennial", 0="Mature"）

### Sheet 1.2：收入 × 职业热力图
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `IncomeBand` (刚刚创建的计算字段) |
| 拖到 Rows | `SegmentLabel` |
| 拖到 Color | `AVG(composite_score)` |
| 拖到 Label | `AVG(composite_score)` → Format → Number → Decimal 1 |
| Title | "Score × Income × Segment Matrix" |

**可视化优化：**
- Marks: Square
- Color: 选 Red-Green Diverging → 编辑 → Stepped Color 2 steps
- 调整透明度到 80%

### Sheet 1.3：客群占比饼图
| 设置 | 值 |
|------|-----|
| 拖到 Rows | `SegmentLabel` |
| 拖到 Column | `COUNTD(SK_ID_CURR)` |
| Title | "Customer Segment Mix" |

**可视化优化：**
- Marks: Pie
- Label: `COUNTD(SK_ID_CURR)` → Quick Table Calculation → Percent of Total
- Format: 显示百分比 + 数量
- Color: 选 Tableau 10 或手动调色

### Sheet 1.4：渠道对比条形图
| 设置 | 值 |
|------|-----|
| 数据源 | `agg_channel_analysis` |
| 拖到 Columns | `Estimated_Share` |
| 拖到 Rows | `Channel` |
| 拖到 Color | `Channel` → 编辑：Broker=红色, Direct=绿色 |
| 拖到 Label | `Estimated_Share` → Format → Percentage |
| Title | "Broker vs Direct Channel Mix" |

**可视化优化：**
- Marks: Bar
- 添加参考线：Analytics → Constant Line → 值 0.5 → Label "50%"
- 显示轴标签为百分比

### Dashboard 1 布局

```
┌──────────────────────────────────────────────┐
│          Customer Intelligence                │
├──────────────┬───────────────────────────────┤
│  Age Pyramid │  Score × Income Matrix        │
│  (Sheet 1.1) │  (Sheet 1.2)                  │
├──────────────┼───────────────────────────────┤
│ Segment Mix  │  KPI Cards + Channel Chart    │
│ (Sheet 1.3)  │  (Sheet 1.4)                  │
├──────────────┴───────────────────────────────┤
│  Float 4 KPI cards on top:                   │
│  Total Customers | Avg Score | % Young |     │
│  % Broker-dep                                 │
└──────────────────────────────────────────────┘
```

**仪表盘操作：**
- 新建 Dashboard → 改名为 "1. Customer Intelligence"
- Size: 选择 "Fixed Size" → 1000 x 800 或 "Automatic"
- 把 Sheet 1.1-1.4 拖进去
- **添加 4 个浮动 KPI**：
  1. New Worksheet → 只拖 `COUNTD(SK_ID_CURR)` → 改标题 "Total Customers"
  2. 同理做 "Avg Score" (AVG composite_score), "% Young", "% Own Home"
  3. 在 Dashboards 里设为 Floating，放在顶部
- **添加筛选器（用作全局过滤）**：
  - 把 `SegmentLabel` 拖到 Dashboard 空白区 → 作为 Filter
  - 右键 Filter → Apply to Worksheets → All on Dashboard
  - 这样点击某个客群，所有 sheet 同步过滤

---

## 4. Dashboard 2：行为特征与评分（Behavioral Features）

### Sheet 2.1：6 个维度雷达图/并行坐标图

**方法：用条形图展示各维度平均值（更清晰）**
| 设置 | 值 |
|------|-----|
| 数据源 | `fact_behavioral_features` |
| 拖到 Columns | 6 个 score 字段一起选中 → Measure Values |
| 拖到 Rows | `Measure Names` → 排序手动 |
| Title | "6 Dimensions — Average Score Profile" |

**可视化优化：**
- Marks: Bar
- Color: 区分度越高颜色越深（手动调 6 色）
- Show marks labels: 显示平均值

**或者做并行图（更有"雷达"感）：**
- Columns: Measure Names (6 scores) + Measure Values
- Rows: AVG(score)
- Marks: Line (选 2-3 条代表性客群线来对比)

### Sheet 2.2：Readiness Score 分布
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `tier` |
| 拖到 Rows | `COUNTD(SK_ID_CURR)` |
| 拖到 Color | `tier` → 4 colors |
| 拖到 Label | `COUNTD(SK_ID_CURR)` |

**可视化优化：**
- Marks: Bar
- Color 调色：
  - Exploring → `#FFD43B` (黄)
  - Building → `#FF922B` (橙)
  - Almost Ready → `#339AF0` (蓝)
  - Ready → `#40C057` (绿)
- Sort: 手动排序 (Exploring → Building → Almost Ready → Ready)
- 添加参考线：Analytics → Distribution Band → 显示平均值

### Sheet 2.3：SHAP 特征重要性（Top 10）

**用 `fact_behavioral_features` + `dim_customer_profile` 关联**
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `AVG(composite_score)` |
| 拖到 Rows | `tier` |
| 拖到 Detail | `SK_ID_CURR` |
| Title | "Score Distribution by Tier" |

**可视化优化：**
- Marks: Box-and-Whisker (箱线图)
- 显示离群点

### Sheet 2.4：特征与评分相关性矩阵
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `Measure Names` (只选 6 个 score + composite) |
| 拖到 Rows | `Measure Names` |
| 拖到 Color | `CORR(Measure Value, composite_score)` |
| Title | "Feature Correlation Matrix" |

### Dashboard 2 布局

```
┌──────────────────────────────────────────────┐
│         Behavioral Features                   │
├──────────────────┬───────────────────────────┤
│  6 Dimensions    │  Score Distribution        │
│  Profile Bar     │  by Tier                   │
│  (Sheet 2.1)     │  (Sheet 2.2)               │
├──────────────────┼───────────────────────────┤
│  Score Boxplot   │  Feature Correlation       │
│  (Sheet 2.3)     │  (Sheet 2.4)               │
├──────────────────┴───────────────────────────┤
│  Floating KPI:                                │
│  Avg Score | Highest Dim | Lowest Dim |       │
│  Ready %                                       │
└──────────────────────────────────────────────┘
```

---

## 5. Dashboard 3：财务影响（Financial Impact）

### Sheet 3.1：3 年瀑布图
| 设置 | 值 |
|------|-----|
| 数据源 | `agg_financial_projection` |
| Filter | `Scenario` = "baseline" |
| 拖到 Columns | `Year` (离散) |
| 拖到 Rows | `SUM(Net_Benefit_M)` |
| 拖到 Color | `SUM(Net_Benefit_M)` → 正/负区分 |
| Title | "3-Year P&L — Baseline Scenario" |

**可视化优化：**
- Marks: Gantt Bar (瀑布图)
- 参考：添加 Total 列（3 年累计）
- Label: 显示具体数值，格式 `$XX.XM`

### Sheet 3.2：场景对比条形图
| 设置 | 值 |
|------|-----|
| 拖到 Columns | `Scenario` |
| 拖到 Rows | `SUM(NPV_M)` |
| 拖到 Color | `ROI` → 编辑颜色（Auto = 渐变色） |
| 拖到 Label | `SUM(NPV_M)` + `SUM(ROI)` |
| Title | "NPV by Scenario ($M)" |

### Sheet 3.3：敏感性龙卷风图

**用参数模拟敏感性分析：**
| 设置 | 值 |
|------|-----|
| Data → Create Parameter | `p_penetration` |
| Parameter Type | Float → Range 0.08-0.25, Step 0.01 |
| Show Parameter Control | ✓ (显示为滑块) |
| Title | "Sensitivity: Penetration Rate Effect" |

**公式（创建计算字段）**：
```
EstimatedCommissionSaved = [Target_Market_Size] * [p_penetration] * 0.06 * 450000 * 0.0075
```
(简化的公式示意——实际在每个 Parameter 取值下模拟计算)

**也可以简化：用现有的 `agg_financial_projection` 做 3 场景对比**

### Sheet 3.4：ROI 仪表盘
| 设置 | 值 |
|------|-----|
| 拖到 Angle | `SUM(ROI)` |
| 拖到 Label | `SUM(ROI)` → Format `0.0"x"` |
| 拖到 Color | `ROIColor` |
| Filter | `Scenario` = "baseline" |
| Title | "ROI: Baseline Scenario" |

**可视化优化：**
- Marks: Pie → 改 Gauge: 用两个 180° semicircles
- 或者简单用 Big Number：
  - 只拖 `AVG(ROI)` → 改字体大小 48pt
  - 添加副标题 "Baseline Scenario ROI"

### Dashboard 3 布局

```
┌──────────────────────────────────────────────┐
│         Financial Impact — 3-Year Model       │
├──────────────────┬───────────────────────────┤
│  3-Year P&L      │  Scenario Comparison      │
│  Waterfall       │  Bar Chart                │
│  (Sheet 3.1)     │  (Sheet 3.2)              │
├──────────────────┼───────────────────────────┤
│  ROI Gauge       │  Key Numbers              │
│  (Sheet 3.4)     │  Target Market: 1.1M      │
│                  │  Avg Loan: $450K          │
├──────────────────┴───────────────────────────┤
│  Filter: Scenario selector → use Scenario    │
│         字段或 Parameter                       │
└──────────────────────────────────────────────┘
```

---

## 6. 配色方案（Westpac 主题）

| 用途 | 颜色 | HEX |
|------|------|-----|
| 主色（Westpac 红） | Red | `#DA291C` |
| 强调色（信任蓝） | Blue | `#0077C8` |
| 年轻客群 | Red | `#DA291C` |
| 成熟客群 | Gray | `#6C757D` |
| Broker 渠道 | Light Red | `#FF6B6B` |
| Direct 渠道 | Green | `#51CF66` |
| Tier 1 (Exploring) | Yellow | `#FFD43B` |
| Tier 2 (Building) | Orange | `#FF922B` |
| Tier 3 (Almost Ready) | Blue | `#339AF0` |
| Tier 4 (Ready) | Green | `#40C057` |

**在 Tableau 中设置配色：**
1. 右下角 Color 图例 → 右键 → Edit Colors
2. 逐个输入以上 HEX 值
3. 保存为自定义配色：复制到 `My Tableau Repository\Preferences.tps`

---

## 7. 仪表盘交互（重要）

### 添加仪表盘操作（Dashboards → Actions）

**Action 1：筛选联动（Filter Action）**
- Source Sheets: Sheet 1.1, 1.2, 1.3
- Target Sheets: All (将此链接应用到所有工作表)
- Run On: Select
- 勾选 "Show All Values When Clearing Selection"

**Action 2：跳转看板（Go to Sheet Action）**
- Source: Dashboard 1 中的 "View Details" 文本/标记
- Target: Dashboard 2
- Run On: Menu 或 Select

**Action 3：URL 链接（如果有外部资源）**
- 可选：链接到 Tableau Public 在线版本

---

## 8. 发布

1. **File → Save to Tableau Public As...**
2. 登录 Tableau Public 账号（免费注册）
3. 填写标题：`Westpac Blueprint — Mortgage Digital Growth Analytics`
4. 添加描述（从 README.md 复制）
5. 发布后获取可分享链接

---

## 9. 快速检查清单

- [ ] 4 个 CSV 都已连接
- [ ] dim ↔ fact 关联建立
- [ ] 3 个计算字段已创建
- [ ] Dashboard 1 完成（年龄金字塔 + 矩阵 + 饼图 + 渠道图）
- [ ] Dashboard 2 完成（6 维度 + 评分分布 + 箱线图 + 相关性）
- [ ] Dashboard 3 完成（瀑布图 + 场景对比 + ROI + 关键数字）
- [ ] 配色调整为 Westpac 主题
- [ ] 仪表盘操作筛选已设置
- [ ] 已保存/发布
