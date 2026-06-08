"""
Feature engineering: construct 20+ business features across 6 dimensions.
Each dimension maps to a candidate input for mortgage readiness assessment.
"""
import pandas as pd
import numpy as np
from .config import ALL_FEATURE_GROUPS


def build_all_features(master_df, save=True):
    """
    Build all feature groups and return a wide-format DataFrame
    with ID columns, raw features, and engineered features.

    Parameters
    ----------
    master_df : pd.DataFrame
        The merged master table from data_loader.build_master_table()
    save : bool
        If True, save to processed folder.

    Returns
    -------
    pd.DataFrame with SK_ID_CURR, TARGET, and all engineered features.
    """
    print("=" * 60)
    print("FEATURE ENGINEERING — 6 Dimension Groups")
    print("=" * 60)

    df = master_df.copy()
    features = pd.DataFrame({"SK_ID_CURR": df["SK_ID_CURR"]})
    if "TARGET" in df.columns:
        features["TARGET"] = df["TARGET"]

    # ── 1. Income Stability ──────────────────────────────────────
    print("\n[1/6] Income Stability ...")
    features = build_income_stability(df, features)

    # ── 2. Spending Discipline ───────────────────────────────────
    print("[2/6] Spending Discipline ...")
    features = build_spending_discipline(df, features)

    # ── 3. Savings Consistency ───────────────────────────────────
    print("[3/6] Savings Consistency ...")
    features = build_savings_consistency(df, features)

    # ── 4. Debt Burden ───────────────────────────────────────────
    print("[4/6] Debt Burden ...")
    features = build_debt_burden(df, features)

    # ── 5. Asset Signal ──────────────────────────────────────────
    print("[5/6] Asset Signal ...")
    features = build_asset_signal(df, features)

    # ── 6. Behavioral ────────────────────────────────────────────
    print("[6/6] Behavioral ...")
    features = build_behavioral(df, features)

    # ── Demographics (for analysis reference, not scored) ────────
    features["AGE_YEARS"] = df["AGE_YEARS"] if "AGE_YEARS" in df.columns else np.nan
    features["IS_YOUNG"] = df["IS_YOUNG"] if "IS_YOUNG" in df.columns else np.nan
    features["CNT_CHILDREN"] = df["CNT_CHILDREN"] if "CNT_CHILDREN" in df.columns else 0

    # ── Clean up ─────────────────────────────────────────────────
    # Replace inf with NA, then fill with median
    features = features.replace([np.inf, -np.inf], np.nan)
    for col in features.select_dtypes(include=[np.number]).columns:
        if col in ("SK_ID_CURR", "TARGET"):
            continue
        features[col] = features[col].fillna(features[col].median())

    print(f"\nFinal feature table: {features.shape[0]:,} rows × {features.shape[1]} cols")

    if save:
        from .config import PROC_FEATURES
        features.to_parquet(PROC_FEATURES, index=False)
        print(f"Saved → {PROC_FEATURES}")

    return features


# ── Individual dimension builders ─────────────────────────────────

def build_income_stability(df, features):
    """Income stability: variability, recency of job change, ratio to credit."""

    # Coefficient of variation proxy (if multiple income columns exist)
    features["income_total"] = df["AMT_INCOME_TOTAL"].fillna(df["AMT_INCOME_TOTAL"].median())
    features["income_to_credit"] = (
        df["AMT_INCOME_TOTAL"] / df["AMT_CREDIT"].clip(lower=1)
    ).clip(0, 20)

    # Annuity burden
    if "AMT_ANNUITY" in df.columns:
        annuity = df["AMT_ANNUITY"].fillna(0).clip(lower=0)
        features["income_to_annuity"] = (
            df["AMT_INCOME_TOTAL"] / annuity.clip(lower=1)
        ).clip(0, 100)
        features["annuity_income_ratio"] = (
            annuity / df["AMT_INCOME_TOTAL"].clip(lower=1)
        ).clip(0, 1)
    else:
        features["income_to_annuity"] = np.nan
        features["annuity_income_ratio"] = np.nan

    # Job stability (handle both recoded and raw DAYS_EMPLOYED)
    if "YEARS_EMPLOYED" in df.columns:
        features["years_employed"] = df["YEARS_EMPLOYED"].fillna(0)
    elif "DAYS_EMPLOYED" in df.columns:
        days = df["DAYS_EMPLOYED"].copy()
        # Recode: 365243 = unemployed/pensioner flag
        unemployed = days >= 365243
        days = days.abs()
        days[unemployed] = np.nan
        features["years_employed"] = (days / 365.25).fillna(0)
    else:
        features["years_employed"] = 0
    features["years_employed"] = features["years_employed"].clip(0, 50)

    if "IS_UNEMPLOYED" in df.columns:
        features["is_unemployed"] = df["IS_UNEMPLOYED"].fillna(0)
    else:
        features["is_unemployed"] = 0
    features["job_stability_score"] = np.where(
        features["years_employed"] < 1, 0,
        np.where(features["years_employed"] < 3, 1,
                 np.where(features["years_employed"] < 7, 2, 3))
    )

    # Income bracket (ordinal, for stratification)
    features["income_bracket"] = pd.cut(
        features["income_total"],
        bins=[0, 50000, 100000, 150000, 200000, 300000, 1e9],
        labels=[0, 1, 2, 3, 4, 5]
    ).astype(float)

    # Income-to-family-size ratio
    # Family size (different column names in raw vs cleaned)
    if "CNT_FAM_MEMBERS" in df.columns:
        family_size = df["CNT_CHILDREN"].fillna(0) + df["CNT_FAM_MEMBERS"].fillna(1)
    else:
        family_size = df["CNT_CHILDREN"].fillna(0) + 1
    family_size = family_size.clip(lower=1)
    features["income_per_family_member"] = features["income_total"] / family_size
    family_size = family_size.clip(lower=1)
    features["income_per_family_member"] = features["income_total"] / family_size

    features["income_stability_score"] = (
        (features["job_stability_score"] / 3) * 0.5 +
        (1 - features["annuity_income_ratio"].fillna(0)) * 0.3 +
        (features["income_bracket"].fillna(0) / 5) * 0.2
    )

    return features


def build_spending_discipline(df, features):
    """Spending discipline: ATM usage, credit utilization, draw patterns."""

    # ATM withdrawal frequency
    if "atm_monthly_frequency" in df.columns:
        features["atm_monthly_freq"] = df["atm_monthly_frequency"].clip(0, 30)
    else:
        features["atm_monthly_freq"] = 0

    # Credit utilization
    if "cc_utilization" in df.columns:
        features["credit_utilization"] = df["cc_utilization"].clip(0, 2)
    else:
        features["credit_utilization"] = 0

    # Spending volatility: std/mean of credit card balance
    if "cc_balance_std" in df.columns and "cc_balance_mean" in df.columns:
        features["spending_volatility"] = (
            df["cc_balance_std"] / df["cc_balance_mean"].clip(lower=1)
        ).clip(0, 10)
    else:
        features["spending_volatility"] = 0

    # ATM dependency vs POS utilization (cash-heavy = less trackable spending)
    if "cc_atm_drawings_mean" in df.columns:
        atm_total = df["cc_atm_drawings_total"].fillna(0)
        cc_limit = df["cc_limit_mean"].fillna(1).clip(lower=1)
        features["atm_dependency_ratio"] = (atm_total / cc_limit).clip(0, 5)
    else:
        features["atm_dependency_ratio"] = 0

    # Composite spending discipline score (0–1)
    features["spending_discipline_score"] = (
        (1 - features["credit_utilization"]) * 0.35 +
        (1 - np.clip(features["atm_monthly_freq"] / 10, 0, 1)) * 0.25 +
        (1 - np.clip(features["spending_volatility"] / 5, 0, 1)) * 0.25 +
        (1 - np.clip(features["atm_dependency_ratio"] / 3, 0, 1)) * 0.15
    ).clip(0, 1)

    return features


def build_savings_consistency(df, features):
    """Savings consistency: DPD-free months, installment punctuality, surplus."""

    # DPD-free months ratio (from POS cash — no overdue)
    if "pos_dpd_zero_ratio" in df.columns:
        features["dpd_free_ratio"] = df["pos_dpd_zero_ratio"].fillna(1)
    else:
        features["dpd_free_ratio"] = 1

    # Installment punctuality: on-time payment ratio
    if "inst_on_time_ratio" in df.columns:
        features["installment_punctuality"] = df["inst_on_time_ratio"].fillna(0)
    else:
        features["installment_punctuality"] = 0

    # Payment delay: average days late (negative = early = good)
    if "inst_payment_delay_mean" in df.columns:
        delay = df["inst_payment_delay_mean"].fillna(0)
        # Convert to score: early (-30) → 1, on-time (0) → 0.8, late (+30) → 0
        features["payment_delay_score"] = np.clip(1 - (delay + 30) / 60, 0, 1)
    else:
        features["payment_delay_score"] = 0.5

    # Max DPD from POS
    if "pos_sk_dpd_max" in df.columns:
        features["max_dpd_pos"] = df["pos_sk_dpd_max"].fillna(0).clip(0, 365)
    else:
        features["max_dpd_pos"] = 0

    # Estimated monthly surplus proxy:
    # (income - annuity - credit card avg payment) / income
    income = features["income_total"].clip(lower=1)
    annuity_pct = df["AMT_ANNUITY"].fillna(0) / 12 / income * 100 if "AMT_ANNUITY" in df.columns else 20
    cc_payment_ratio = (df["cc_payment_mean"].fillna(0) / income * 100) if "cc_payment_mean" in df.columns else 10
    features["estimated_surplus_pct"] = np.clip(1 - annuity_pct/100 - cc_payment_ratio/100, 0, 1)

    # Composite savings consistency score
    features["savings_consistency_score"] = (
        features["dpd_free_ratio"] * 0.30 +
        features["installment_punctuality"] * 0.30 +
        features["payment_delay_score"] * 0.25 +
        features["estimated_surplus_pct"] * 0.15
    ).clip(0, 1)

    return features


def build_debt_burden(df, features):
    """Debt burden: DTI, active credits, overdue history."""

    # Debt-to-income ratio from bureau
    if "bureau_debt_sum_mean" in df.columns:
        features["debt_to_income"] = (
            df["bureau_debt_sum_mean"] / features["income_total"].clip(lower=1)
        ).clip(0, 20)
    else:
        # Fallback: credit amount / income
        features["debt_to_income"] = (
            df["AMT_CREDIT"] / features["income_total"].clip(lower=1)
        ).clip(0, 20)

    # Active credits count
    features["active_credits"] = df["bureau_active_count"].fillna(0) if "bureau_active_count" in df.columns else 0
    features["total_credits"] = df["bureau_credit_count"].fillna(0) if "bureau_credit_count" in df.columns else 0

    # Max DPD ever
    features["max_overdue_days"] = df["bureau_max_overdue_days"].fillna(0) if "bureau_max_overdue_days" in df.columns else 0
    features["mean_overdue_days"] = df["bureau_mean_overdue_days"].fillna(0) if "bureau_mean_overdue_days" in df.columns else 0

    # Credit inquiry recency
    features["days_since_latest_credit"] = df["bureau_days_since_latest"].fillna(-9999) if "bureau_days_since_latest" in df.columns else -9999

    # Composite debt burden score (higher = better = less burden)
    features["debt_burden_score"] = (
        (1 - np.clip(features["debt_to_income"] / 5, 0, 1)) * 0.40 +
        (1 - np.clip(features["active_credits"] / 10, 0, 1)) * 0.25 +
        (1 - np.clip(features["max_overdue_days"] / 365, 0, 1)) * 0.35
    ).clip(0, 1)

    return features


def build_asset_signal(df, features):
    """Asset signals: car ownership, property ownership, income level."""

    features["owns_car"] = (df["FLAG_OWN_CAR"].fillna("N").map({"Y": 1, "N": 0, 1: 1, 0: 0}).astype(int)
                            if "FLAG_OWN_CAR" in df.columns else 0)
    features["owns_realty"] = (df["FLAG_OWN_REALTY"].fillna("N").map({"Y": 1, "N": 0, 1: 1, 0: 0}).astype(int)
                               if "FLAG_OWN_REALTY" in df.columns else 0)

    # Housing type → ordinal signal
    if "NAME_HOUSING_TYPE" in df.columns:
        housing_rank = {
            "Co-op apartment": 0.3,
            "With parents": 0.1,
            "Municipal apartment": 0.4,
            "House / apartment": 0.7,
            "Rented apartment": 0.2,
            "Office apartment": 0.3,
        }
        features["housing_type_score"] = df["NAME_HOUSING_TYPE"].map(housing_rank).fillna(0.3)
    else:
        features["housing_type_score"] = 0.3

    # Education → ordinal
    if "NAME_EDUCATION_TYPE" in df.columns:
        edu_rank = {
            "Lower secondary": 0.1,
            "Secondary / secondary special": 0.3,
            "Incomplete higher": 0.5,
            "Higher education": 0.7,
            "Academic degree": 0.9,
        }
        features["education_score"] = df["NAME_EDUCATION_TYPE"].map(edu_rank).fillna(0.3)
    else:
        features["education_score"] = 0.3

    # Composite asset signal
    features["asset_signal_score"] = (
        features["owns_realty"] * 0.35 +
        features["owns_car"] * 0.15 +
        features["housing_type_score"] * 0.25 +
        features["education_score"] * 0.15 +
        (features["income_bracket"].fillna(0) / 5) * 0.10
    ).clip(0, 1)

    return features


def build_behavioral(df, features):
    """Behavioral: application frequency, diversity, approval history."""

    # Application count & frequency
    features["prev_app_count"] = df["prev_app_count"].fillna(0) if "prev_app_count" in df.columns else 0
    features["prev_approved_ratio"] = df["prev_approved_ratio"].fillna(0) if "prev_approved_ratio" in df.columns else 0
    features["prev_refused_ratio"] = df["prev_refused_ratio"].fillna(0) if "prev_refused_ratio" in df.columns else 0

    # Application recency
    features["prev_app_amt_mean"] = df["prev_app_amt_mean"].fillna(0) if "prev_app_amt_mean" in df.columns else 0

    # Contract type diversity proxy (just count types from bureau)
    features["credit_type_count"] = df["bureau_credit_count"].fillna(0) if "bureau_credit_count" in df.columns else 0

    # Behavioral score: favors people who apply selectively and get approved
    features["behavioral_score"] = (
        features["prev_approved_ratio"] * 0.45 +
        (1 - features["prev_refused_ratio"]) * 0.30 +
        (1 - np.clip(features["prev_app_count"] / 20, 0, 1)) * 0.25
    ).clip(0, 1)

    return features


# ── Composite Score Builder ────────────────────────────────────────

def build_composite_score(features_df, weights=None):
    """
    Build a composite "mortgage readiness indicator" from the 6 dimension
    scores. This is an EXPLORATORY indicator to verify whether the 6
    dimensions have discriminative power — NOT a production scoring engine.

    Parameters
    ----------
    features_df : pd.DataFrame
        Output of build_all_features()
    weights : dict, optional
        Dimension weights. If None, uses equal weights.

    Returns
    -------
    pd.Series of composite scores (0–100).
    """
    if weights is None:
        weights = {
            "income_stability_score":    1/6,
            "spending_discipline_score": 1/6,
            "savings_consistency_score": 1/6,
            "debt_burden_score":         1/6,
            "asset_signal_score":        1/6,
            "behavioral_score":          1/6,
        }

    composite = pd.Series(0.0, index=features_df.index)
    for col, w in weights.items():
        if col in features_df.columns:
            composite += features_df[col].fillna(0) * w

    return (composite * 100).clip(0, 100)


def append_raw_features(master_df, features_df):
    """
    Append raw behavioral features from master table alongside composites.
    These carry more signal than composite scores alone.
    Only adds columns not already in features_df.
    """
    existing = set(features_df.columns)
    raw = pd.DataFrame({"SK_ID_CURR": features_df["SK_ID_CURR"]})

    raw_cols = {
        # Bureau
        "bureau_credit_count", "bureau_active_count",
        "bureau_debt_sum_max", "bureau_max_overdue_days",
        "bureau_mean_overdue_days", "bureau_days_since_latest",
        # Installments
        "inst_payment_delay_mean", "inst_payment_delay_std",
        "inst_late_ratio", "inst_count", "inst_days_late_max",
        "inst_payment_mean",
        # Credit card (non-duplicate)
        "cc_balance_mean", "cc_balance_std",
        "cc_atm_drawings_mean", "cc_atm_drawings_total",
        "cc_payment_mean", "cc_min_payment_mean",
        "cc_limit_mean", "cc_month_count",
        # Previous apps (non-duplicate)
        "prev_app_approved", "prev_app_refused",
        "prev_app_amt_max", "prev_app_annuity_mean",
        "prev_app_days_mean", "prev_nflag_last_appl_day",
        # POS
        "pos_month_count", "pos_active_contracts",
        "pos_sk_dpd_max",
    }

    for col in raw_cols:
        if col in existing:
            continue
        raw[col] = master_df[col].fillna(0) if col in master_df.columns else 0

    raw = raw.drop(columns=["SK_ID_CURR"])
    result = pd.concat([features_df, raw], axis=1)
    return result


def bin_composite_score(score_series):
    """
    Bin composite scores into 4 exploration tiers.

    These are NOT product Readiness Score tiers — they are analytical
    bins used to test whether the features can stratify customers by
    observed loan outcomes.
    """
    bins = [0, 30, 55, 75, 100]
    labels = ["Exploring", "Building", "Almost Ready", "Ready"]
    return pd.cut(score_series, bins=bins, labels=labels, include_lowest=True)
