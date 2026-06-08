"""
Project-wide configuration: paths, constants, feature definitions.
"""
import os

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUTS = os.path.join(PROJECT_ROOT, "outputs")
FIGURES = os.path.join(OUTPUTS, "figures")
MODELS_DIR = os.path.join(OUTPUTS, "models")
REPORTS = os.path.join(OUTPUTS, "reports")
TABLEAU_EXPORTS = os.path.join(PROJECT_ROOT, "tableau", "data_exports")

# ── Home Credit data paths ─────────────────────────────────────────
HC_APP_TRAIN      = os.path.join(DATA_RAW, "home_credit", "application_train.csv")
HC_APP_TEST       = os.path.join(DATA_RAW, "home_credit", "application_test.csv")
HC_BUREAU         = os.path.join(DATA_RAW, "home_credit", "bureau.csv")
HC_BUREAU_BAL     = os.path.join(DATA_RAW, "home_credit", "bureau_balance.csv")
HC_PREV_APP       = os.path.join(DATA_RAW, "home_credit", "previous_application.csv")
HC_CC_BAL         = os.path.join(DATA_RAW, "home_credit", "credit_card_balance.csv")
HC_INSTALL        = os.path.join(DATA_RAW, "home_credit", "installments_payments.csv")
HC_POS_CASH       = os.path.join(DATA_RAW, "home_credit", "POS_CASH_balance.csv")

# Bank Marketing
BM_PATH           = os.path.join(DATA_RAW, "bank_marketing", "bank-additional-full.csv")

# ── Processed outputs ──────────────────────────────────────────────
PROC_APP          = os.path.join(DATA_PROCESSED, "application_cleaned.parquet")
PROC_BUREAU       = os.path.join(DATA_PROCESSED, "bureau_cleaned.parquet")
PROC_BUREAU_AGG   = os.path.join(DATA_PROCESSED, "bureau_aggregated.parquet")
PROC_PREV_AGG     = os.path.join(DATA_PROCESSED, "previous_aggregated.parquet")
PROC_CC_AGG       = os.path.join(DATA_PROCESSED, "credit_card_aggregated.parquet")
PROC_INSTALL_AGG  = os.path.join(DATA_PROCESSED, "installments_aggregated.parquet")
PROC_POS_AGG      = os.path.join(DATA_PROCESSED, "pos_cash_aggregated.parquet")
PROC_MERGED       = os.path.join(DATA_PROCESSED, "merged_master.parquet")
PROC_FEATURES     = os.path.join(DATA_PROCESSED, "features_wide.parquet")

# ── Age cohort definition (for Gen Z / Millennial analysis) ───────
YOUNG_AGE_MAX = 35  # <35 = "young cohort" (= Gen Z + younger Millennials)

# ── Feature group definitions ──────────────────────────────────────
# Each group maps to a Readiness Score dimension candidate.
# After exploration, these are validated for discriminative power.

INCOME_STABILITY_FEATURES = [
    "income_stability_cv",           # Coefficient of variation of income across sources
    "days_since_last_job_change",    # DAYS_EMPLOYED recoded
    "income_to_credit_ratio",        # AMT_INCOME_TOTAL / AMT_CREDIT
    "income_to_annuity_ratio",       # AMT_INCOME_TOTAL / AMT_ANNUITY
]

SPENDING_DISCIPLINE_FEATURES = [
    "non_essential_spending_ratio",  # Proxy via ATM / POS patterns
    "atm_withdrawal_frequency",      # ATM usage frequency
    "credit_utilization_trend",      # Month-over-month utilization change
    "credit_utilization_mean",       # Average utilization rate
]

SAVINGS_CONSISTENCY_FEATURES = [
    "estimated_monthly_surplus",     # Income – estimated obligations
    "dpd_free_months_ratio",         # Fraction of months with zero DPD
    "installment_punctuality",       # Mean days before/after due date
    "months_since_last_overdue",     # Recency of last missed payment
]

DEBT_BURDEN_FEATURES = [
    "debt_to_income_ratio",          # Total active credit / income
    "active_credit_count",           # Number of open credits (bureau)
    "max_dpd_ever",                  # Worst overdue ever
    "credit_inquiry_recency",        # Days since latest inquiry
]

ASSET_SIGNAL_FEATURES = [
    "owns_car",                      # FLAG_OWN_CAR
    "owns_realty",                   # FLAG_OWN_REALTY
    "income_band",                   # Ordinal income bracket
    "balance_proxy",                 # From bank_marketing merge (if available)
]

BEHAVIORAL_FEATURES = [
    "application_frequency",         # Previous applications per year
    "contract_type_diversity",       # Unique contract types used
    "approved_ratio",                # Share of previous apps approved
    "refused_ratio",                 # Share refused
]

ALL_FEATURE_GROUPS = {
    "income_stability":       INCOME_STABILITY_FEATURES,
    "spending_discipline":    SPENDING_DISCIPLINE_FEATURES,
    "savings_consistency":    SAVINGS_CONSISTENCY_FEATURES,
    "debt_burden":            DEBT_BURDEN_FEATURES,
    "asset_signal":           ASSET_SIGNAL_FEATURES,
    "behavioral":             BEHAVIORAL_FEATURES,
}

# ── Feature selection for modeling ──────────────────────────────────
# Redundant features to drop before model training.
# These duplicate information already captured by higher-SHAP raw features.
DROP_FOR_MODELING = [
    # Duplicates of years_employed
    "job_stability_score", "is_unemployed", "income_per_family_member",
    "income_bracket",
    # Duplicates of income_to_credit
    "income_to_annuity",
    # Duplicates of atm_monthly_frequency
    "atm_dependency_ratio", "atm_monthly_freq",
    # Duplicates of inst_late_ratio / inst_on_time_ratio
    "installment_punctuality", "payment_delay_score",
    # Duplicates of debt_to_income
    "debt_burden_score",
    # Duplicates of max_overdue_days
    "mean_overdue_days",
    # Duplicates of bureau_days_since_latest
    "days_since_latest_credit",
    # Duplicates of total_credits
    "credit_type_count", "bureau_credit_count",
    # Duplicates of pos_sk_dpd_max
    "max_dpd_pos",
    # Composite scores (raw features are strictly better for modeling)
    "income_stability_score", "spending_discipline_score",
    "savings_consistency_score", "asset_signal_score", "behavioral_score",
    # Demographics with low prediction value
    "AGE_YEARS", "IS_YOUNG", "CNT_CHILDREN",
    # Analysis-only fields
    "composite_score", "tier",
]

# ── Business simulation constants ───────────────────────────────────
# Australian market context
TARGET_MARKET_SIZE      = 1_100_000    # <35 renters (ABS sourced estimate)
AVG_LOAN_SIZE_AUD        = 450_000      # Average mortgage size
BROKER_COMM_UPFRONT      = 0.0060       # 0.60% upfront
BROKER_COMM_TRAIL        = 0.0015       # 0.15% trail
DISCOUNT_RATE            = 0.04         # RBA cash rate proxy

# Cost assumptions
FIXED_COST_ANNUAL        = 2_500_000    # Tech + Compliance + Data team
VARIABLE_COST_PER_USER   = 50           # Digital marketing + servicing

# Penetration scenarios
PENETRATION_SCENARIOS = {
    "pessimistic": 0.08,
    "baseline":    0.18,
    "optimistic":  0.25,
}

# ── Visualization ───────────────────────────────────────────────────
# Consistent colour palette for Westpac-branded look
PALETTE = {
    "primary":      "#DA291C",   # Westpac red
    "secondary":    "#1C1C1C",   # Near black
    "accent":       "#0077C8",   # Trust blue
    "young":        "#DA291C",   # Gen Z cohort highlight
    "mature":       "#6C757D",   # Older cohort
    "broker":       "#FF6B6B",   # Broker channel
    "direct":       "#51CF66",   # Direct channel
    "tier_1":       "#FFD43B",   # Exploring
    "tier_2":       "#FF922B",   # Building
    "tier_3":       "#339AF0",   # Almost Ready
    "tier_4":       "#40C057",   # Ready
}

SEABORN_STYLE = "whitegrid"
FIGURE_DPI = 150
FIGSIZE_DEFAULT = (10, 6)
FIGSIZE_WIDE = (14, 6)
