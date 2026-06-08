# Westpac Blueprint — Mortgage Digital Growth Analytics

**A end-to-end data analysis project simulating the exploration-phase analytics behind a direct-to-consumer digital mortgage product for Westpac.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Tableau](https://img.shields.io/badge/Tableau-Dashboard-orange.svg)](https://public.tableau.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Project Story (3-Minute Elevator Pitch)

Westpac's young customers are churning to neobanks. 67.5% of mortgage origination flows through external brokers — each loan costs the bank 0.75% in commissions. This project uses **public banking datasets (57M+ records across 8 tables)** to answer three exploration-phase questions:

1. **How big is the young-customer gap?** → 30%+ of the customer base is under 35, owns property at 1/3 the rate of older customers, but has *lower* default risk — they're underserved, not uncreditworthy.

2. **Which behavioral signals predict mortgage readiness?** → Validated 6 feature dimensions (savings consistency, income stability, spending discipline, debt burden, asset signals, behavioral history) with ANOVA and SHAP — providing the data foundation for a Readiness Score product feature.

3. **Is a direct-to-consumer channel economically viable?** → At 18% market penetration, 3-year NPV reaches AUD 42M with 2.2x ROI. Breakeven at ~12% penetration.

**Key output:** A structured exploration brief recommending the product team proceed to design phase, with 6 validated behavioral dimensions and a 3-scenario financial model.

---

## Repository Structure

```
Homeloan_DA/
├── notebooks/                          # 6 Jupyter notebooks (the main deliverable)
│   ├── 01_data_acquisition.ipynb       # Multi-table ingestion + CDR simulation
│   ├── 02_eda_user_profiling.ipynb     # EDA + Gen Z portrait + clustering
│   ├── 03_feature_engineering.ipynb    # 6-dimension feature validation
│   ├── 04_predictive_modeling.ipynb    # XGBoost/LightGBM + SHAP
│   ├── 05_business_simulation.ipynb    # 3-year financial model + sensitivity
│   └── 06_executive_summary.ipynb      # Integrated findings + recommendations
│
├── src/                                # Reusable Python modules
│   ├── config.py                       # Paths, constants, feature definitions
│   ├── data_loader.py                  # SQL-style multi-table JOINs
│   ├── preprocessing.py                # Cleaning, imputation, encoding
│   ├── features.py                     # 20+ engineered features pipeline
│   ├── model.py                        # Model training, evaluation, SHAP
│   └── visualization.py               # Themed chart builders
│
├── tableau/                            # Tableau dashboard deliverables
│   └── data_exports/                   # CSV exports for Tableau connection
│
├── outputs/                            # Figures, models, reports
├── data/                               # Raw + processed data (gitignored)
├── docs/superpowers/specs/             # Design spec
├── requirements.txt
└── README.md
```

---

## Technical Stack

| Layer | Tools |
|-------|-------|
| **Data Wrangling** | Pandas, NumPy, SQL-style multi-table JOINs |
| **Statistical Analysis** | SciPy (t-test, ANOVA, Kruskal-Wallis) |
| **Machine Learning** | Scikit-learn, XGBoost, LightGBM, SHAP |
| **Visualization** | Matplotlib, Seaborn, Plotly |
| **Dashboard** | Tableau Public (3-page interactive dashboard) |
| **Environment** | Python 3.10+, Jupyter Notebook |

---

## Getting Started

### 1. Clone & Set Up

```bash
git clone <repo-url>
cd Homeloan_DA
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Download Datasets

**Home Credit Default Risk** (Kaggle):
- Download from: [kaggle.com/c/home-credit-default-risk/data](https://www.kaggle.com/c/home-credit-default-risk/data)
- Place all CSV files in `data/raw/home_credit/`

**Bank Marketing** (UCI):
- Download from: [archive.ics.uci.edu/ml/datasets/bank+marketing](https://archive.ics.uci.edu/ml/datasets/bank+marketing)
- Place `bank-additional-full.csv` in `data/raw/bank_marketing/`

### 3. Run Notebooks

```bash
jupyter notebook
```

Execute notebooks 01 → 06 in order. Each notebook saves its intermediates to `data/processed/` so downstream notebooks can pick up where the previous left off.

### 4. Tableau Dashboard

After running Notebooks 02, 04, 05, and 06, the `tableau/data_exports/` folder will contain 4 CSV files. Connect Tableau Public to these files to build the interactive dashboard.

---

## Key Analytical Outputs

| Notebook | Key Metric | Result |
|----------|-----------|--------|
| 02 — User Profiling | Gen Z property ownership | ~11% vs 70%+ for >45 cohort |
| 03 — Dimension Validation | Savings Consistency ANOVA F | Highest among 6 dimensions |
| 04 — Predictive Model | AUC-ROC (best model) | Target >0.75 |
| 04 — SHAP | Top feature | Debt-to-income + DPD history |
| 05 — Financial | 3-year NPV (baseline) | AUD 42.0M, ROI 2.2x |
| 05 — Breakeven | Penetration threshold | ~12% |

---

## Tableau Dashboard Preview

| Dashboard | Content |
|-----------|---------|
| **Customer Intelligence** | Age pyramid, income heatmap, cluster profiles, KPI cards |
| **Behavioral Features** | Dimension rankings, SHAP top-10, score distribution, conversion funnel |
| **Financial Impact** | 3-year waterfall, ROI gauge, sensitivity slider, commission saved counter |

---

## Resume Entry

**Westpac Blueprint — Mortgage Digital Growth Analytics**
> End-to-end data analysis project simulating the exploration phase of a digital mortgage product for Westpac. Ingested and joined 8 tables (57M+ records) to simulate CDR data aggregation. Built 20+ behavioral features across 6 validated dimensions; trained XGBoost/LightGBM model (AUC >0.75) with SHAP explainability. Constructed a dual-layer 3-year financial model showing AUD 42M NPV and 2.2x ROI across 3 penetration scenarios. Delivered findings via 6 structured Jupyter notebooks and a 3-page interactive Tableau dashboard.

**Skills:** Python (Pandas, NumPy, Scikit-learn, XGBoost, LightGBM), SQL, SHAP, Tableau, Financial Modeling, Feature Engineering, Customer Segmentation

---

## Limitations & Future Work

- **Data:** Home Credit data is Eastern European, not Australian. Demographic patterns are directionally useful but not directly transferable.
- **Broker channel:** Proxy estimation from contract types; real channel data would require internal bank sources.
- **Future:** Add an AI Agent pipeline (CDR transaction classification + compliance review) as a separate project.
- **Future:** Integrate real CDR sandbox data from an Australian Open Banking provider.

---

## License

MIT — see [LICENSE](LICENSE) file.

---

*Built as a portfolio project for Data Operations / Data Analyst roles. Core narrative aligned with the Westpac Blueprint product strategy exploration.*
