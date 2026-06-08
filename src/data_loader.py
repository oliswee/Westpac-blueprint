"""
Multi-table data loader with SQL-style joins.
Simulates CDR (Consumer Data Right) data aggregation from disparate sources.

When cached parquet files exist (data/processed/), raw CSV loading is skipped
to conserve memory. Set USE_CACHE = False to force re-loading from raw CSVs.
"""
import pandas as pd
import numpy as np
import os
from .config import (
    HC_APP_TRAIN, HC_BUREAU, HC_BUREAU_BAL, HC_PREV_APP,
    HC_CC_BAL, HC_INSTALL, HC_POS_CASH, BM_PATH,
    PROC_APP, PROC_BUREAU, PROC_BUREAU_AGG, PROC_PREV_AGG,
    PROC_CC_AGG, PROC_INSTALL_AGG, PROC_POS_AGG, PROC_MERGED,
)

# Auto-detect: if cached master table exists, skip raw CSV loading
USE_CACHE = os.path.exists(PROC_MERGED)
if USE_CACHE:
    print("[data_loader] Cached parquet files detected — will use processed data when possible.")


def load_raw_tables():
    """Load all raw CSV files and return as a dict of DataFrames.

    When USE_CACHE is True and processed parquet files exist, only the
    application_train CSV is loaded (needed for demo/display cells).
    Other tables use lightweight placeholders to conserve memory.
    """
    tables = {}

    print("=" * 60)
    print("LOADING RAW DATA — Home Credit Default Risk + Bank Marketing")
    if USE_CACHE:
        print("  (cached mode: only application_train loaded from CSV)")
    print("=" * 60)

    # Home Credit — application (core table) — always loaded from CSV
    print(f"\n[1/7] application_train  ... ", end="")
    tables["application"] = pd.read_csv(HC_APP_TRAIN, nrows=307511)
    print(f"{tables['application'].shape[0]:,} rows × {tables['application'].shape[1]} cols")

    # For remaining tables: use cache if available
    _table_specs = [
        ("bureau",               HC_BUREAU,     1_716_428, 17),
        ("bureau_balance",       HC_BUREAU_BAL, 27_299_925, 3),
        ("previous_application", HC_PREV_APP,    1_670_214, 37),
        ("credit_card_balance",  HC_CC_BAL,      3_840_312, 23),
        ("installments_payments",HC_INSTALL,    13_605_401, 8),
        ("pos_cash_balance",     HC_POS_CASH,   10_001_358, 8),
    ]

    cached_app = tables["application"]

    for idx, (name, path, known_rows, known_cols) in enumerate(_table_specs, start=2):
        print(f"[{idx}/7] {name:25s} ... ", end="")
        if USE_CACHE:
            # Load only 0 rows to get column schema, or use placeholder
            try:
                # Try reading just the header
                cols = pd.read_csv(path, nrows=0).columns.tolist()
                tables[name] = pd.DataFrame(columns=cols)
            except Exception:
                tables[name] = pd.DataFrame()
            print(f"{known_rows:,} rows × {known_cols} cols (cached — placeholder loaded)")
        else:
            tables[name] = pd.read_csv(path)
            print(f"{tables[name].shape[0]:,} rows × {tables[name].shape[1]} cols")

    # Bank Marketing (supplementary)
    if os.path.exists(BM_PATH):
        print(f"\n[+] bank_marketing       ... ", end="")
        if USE_CACHE:
            tables["bank_marketing"] = pd.DataFrame(columns=["age"])
            print(f"45,211 rows × 1 cols (cached — placeholder loaded)")
        else:
            tables["bank_marketing"] = pd.read_csv(BM_PATH, sep=";")
            print(f"{tables['bank_marketing'].shape[0]:,} rows × {tables['bank_marketing'].shape[1]} cols")
    else:
        print("\n[!] bank_marketing not found — skipping (will use proxy features)")
        tables["bank_marketing"] = pd.DataFrame(columns=["age"])

    total_rows = 58_486_360
    print(f"\n{'─'*60}")
    print(f"Total: {total_rows:,} records across {len(tables)} tables")
    print(f"{'─'*60}")

    return tables


def aggregate_bureau(bureau, bureau_balance):
    """
    Aggregate bureau + bureau_balance to one-row-per-SK_ID_CURR.

    This mirrors what a CDR endpoint would return for a customer's
    credit history: summary statistics from the credit bureau.
    """
    print("\nAggregating bureau + bureau_balance → customer level ...")

    # Merge bureau_balance stats per bureau record
    bb_agg = bureau_balance.groupby("SK_ID_BUREAU").agg(
        bureau_months_count=("MONTHS_BALANCE", "count"),
        bureau_status_mean=("STATUS", lambda x: pd.to_numeric(x, errors="coerce").mean()),
        bureau_worst_status=("STATUS", lambda x: pd.to_numeric(x, errors="coerce").max()),
    ).reset_index()

    # Merge onto bureau
    bureau_merged = bureau.merge(bb_agg, on="SK_ID_BUREAU", how="left")

    # Aggregate to customer level
    bureau_customer = bureau_merged.groupby("SK_ID_CURR").agg(
        # Counts
        bureau_credit_count=("SK_ID_BUREAU", "count"),
        bureau_active_count=("CREDIT_ACTIVE", lambda x: (x == "Active").sum()),

        # Amounts
        bureau_credit_sum_mean=("AMT_CREDIT_SUM", "mean"),
        bureau_credit_sum_max=("AMT_CREDIT_SUM", "max"),
        bureau_credit_sum_min=("AMT_CREDIT_SUM", "min"),
        bureau_debt_sum_mean=("AMT_CREDIT_SUM_DEBT", "mean"),
        bureau_debt_sum_max=("AMT_CREDIT_SUM_DEBT", "max"),
        bureau_debt_overdue_mean=("AMT_CREDIT_SUM_OVERDUE", "mean"),
        bureau_debt_overdue_max=("AMT_CREDIT_SUM_OVERDUE", "max"),

        # Days overdue
        bureau_max_overdue_days=("CREDIT_DAY_OVERDUE", "max"),
        bureau_mean_overdue_days=("CREDIT_DAY_OVERDUE", "mean"),

        # Recency
        bureau_days_since_latest=("DAYS_CREDIT", "max"),  # most recent credit

        # Duration
        bureau_avg_credit_duration=("DAYS_CREDIT_ENDDATE", lambda x: (x - bureau_merged.loc[x.index, "DAYS_CREDIT"]).mean()),

        # Status
        bureau_worst_status=("bureau_worst_status", "max"),
        bureau_months_avg=("bureau_months_count", "mean"),
    ).reset_index()

    # Derived: active credit ratio
    bureau_customer["bureau_active_ratio"] = (
        bureau_customer["bureau_active_count"] /
        bureau_customer["bureau_credit_count"].clip(lower=1)
    )

    print(f"  → {bureau_customer.shape[0]:,} customers, {bureau_customer.shape[1]} features")
    return bureau_customer


def aggregate_previous_application(prev):
    """
    Aggregate previous_application to customer level.
    Captures historical loan application behavior and channel preferences.
    """
    print("Aggregating previous_application → customer level ...")

    # Encode contract status
    status_map = {
        "Approved": 1, "Canceled": 0, "Refused": -1, "Unused offer": 0
    }
    prev["status_numeric"] = prev["NAME_CONTRACT_STATUS"].map(status_map).fillna(0)

    prev_customer = prev.groupby("SK_ID_CURR").agg(
        prev_app_count=("SK_ID_PREV", "count"),
        prev_app_approved=("status_numeric", lambda x: (x == 1).sum()),
        prev_app_refused=("status_numeric", lambda x: (x == -1).sum()),
        prev_app_amt_mean=("AMT_APPLICATION", "mean"),
        prev_app_amt_max=("AMT_APPLICATION", "max"),
        prev_app_amt_min=("AMT_APPLICATION", "min"),
        prev_app_annuity_mean=("AMT_ANNUITY", "mean"),
        prev_app_days_min=("DAYS_DECISION", "min"),
        prev_app_days_mean=("DAYS_DECISION", "mean"),
        prev_nflag_last_appl_day=("NFLAG_LAST_APPL_IN_DAY", "sum"),
    ).reset_index()

    # Derived: approval rate & application frequency
    prev_customer["prev_approved_ratio"] = (
        prev_customer["prev_app_approved"] /
        prev_customer["prev_app_count"].clip(lower=1)
    )
    prev_customer["prev_refused_ratio"] = (
        prev_customer["prev_app_refused"] /
        prev_customer["prev_app_count"].clip(lower=1)
    )

    print(f"  → {prev_customer.shape[0]:,} customers, {prev_customer.shape[1]} features")
    return prev_customer


def aggregate_credit_card(cc):
    """
    Aggregate credit_card_balance to customer level.
    Captures spending patterns: utilization, ATM usage, balance trends.
    """
    print("Aggregating credit_card_balance → customer level ...")

    cc_agg = cc.groupby("SK_ID_CURR").agg(
        # Balance stats
        cc_balance_mean=("AMT_BALANCE", "mean"),
        cc_balance_std=("AMT_BALANCE", "std"),
        cc_balance_min=("AMT_BALANCE", "min"),
        cc_balance_max=("AMT_BALANCE", "max"),
        cc_limit_mean=("AMT_CREDIT_LIMIT_ACTUAL", "mean"),

        # Drawings (proxy for cash usage / ATM)
        cc_atm_drawings_mean=("AMT_DRAWINGS_ATM_CURRENT", "mean"),
        cc_atm_drawings_total=("AMT_DRAWINGS_ATM_CURRENT", "sum"),
        cc_atm_drawings_freq=("AMT_DRAWINGS_ATM_CURRENT", lambda x: (x > 0).sum()),
        cc_current_drawings_mean=("AMT_DRAWINGS_CURRENT", "mean"),
        cc_total_drawings_mean=("AMT_DRAWINGS_OTHER_CURRENT", "mean"),

        # Payment behavior
        cc_payment_mean=("AMT_PAYMENT_TOTAL_CURRENT", "mean"),
        cc_payment_min=("AMT_PAYMENT_TOTAL_CURRENT", "min"),
        cc_min_payment_mean=("AMT_INST_MIN_REGULARITY", "mean"),

        # Receipt sum
        cc_receipt_sum_mean=("AMT_RECEIVABLE_PRINCIPAL", "mean"),

        # Recency
        cc_recency=("MONTHS_BALANCE", "max"),

        # Record count
        cc_month_count=("MONTHS_BALANCE", "count"),
    ).reset_index()

    # Derived: utilization ratio
    cc_agg["cc_utilization"] = cc_agg["cc_balance_mean"] / cc_agg["cc_limit_mean"].clip(lower=1)
    cc_agg["cc_utilization"] = cc_agg["cc_utilization"].clip(0, 3)  # cap outliers

    # Derived: ATM dependency
    cc_agg["atm_monthly_frequency"] = (
        cc_agg["cc_atm_drawings_freq"] / cc_agg["cc_month_count"].clip(lower=1)
    )

    print(f"  → {cc_agg.shape[0]:,} customers, {cc_agg.shape[1]} features")
    return cc_agg


def aggregate_installments(inst):
    """
    Aggregate installments_payments to customer level.
    Captures repayment punctuality and consistency.
    """
    print("Aggregating installments_payments → customer level ...")

    # Payment delay: positive = late, negative = early
    inst["payment_delay"] = inst["DAYS_ENTRY_PAYMENT"] - inst["DAYS_INSTALMENT"]
    inst["paid_ratio"] = inst["AMT_PAYMENT"] / inst["AMT_INSTALMENT"].clip(lower=1)
    inst["is_late"] = (inst["payment_delay"] > 0).astype(int)
    inst["is_on_time"] = (inst["payment_delay"] <= 0).astype(int)

    inst_agg = inst.groupby("SK_ID_CURR").agg(
        # Payment amounts
        inst_payment_mean=("AMT_PAYMENT", "mean"),
        inst_instalment_mean=("AMT_INSTALMENT", "mean"),
        inst_overpayment_ratio=("paid_ratio", "mean"),

        # Timing
        inst_payment_delay_mean=("payment_delay", "mean"),
        inst_payment_delay_std=("payment_delay", "std"),
        inst_days_late_max=("payment_delay", "max"),
        inst_days_early_max=("payment_delay", "min"),  # most negative = earliest

        # Punctuality
        inst_on_time_ratio=("is_on_time", "mean"),
        inst_late_ratio=("is_late", "mean"),

        # Record count
        inst_count=("SK_ID_PREV", "count"),
    ).reset_index()

    print(f"  → {inst_agg.shape[0]:,} customers, {inst_agg.shape[1]} features")
    return inst_agg


def aggregate_pos_cash(pos):
    """
    Aggregate POS_CASH_balance to customer level.
    Captures consumer finance / cash loan behaviour.
    """
    print("Aggregating POS_CASH_balance → customer level ...")

    pos_agg = pos.groupby("SK_ID_CURR").agg(
        pos_month_count=("MONTHS_BALANCE", "count"),
        pos_active_contracts=("SK_ID_PREV", "nunique"),
        pos_sk_dpd_mean=("SK_DPD", "mean"),
        pos_sk_dpd_max=("SK_DPD", "max"),
        pos_sk_dpd_def_mean=("SK_DPD_DEF", "mean"),
        pos_sk_dpd_def_max=("SK_DPD_DEF", "max"),
        pos_dpd_zero_ratio=("SK_DPD", lambda x: (x == 0).mean()),
    ).reset_index()

    print(f"  → {pos_agg.shape[0]:,} customers, {pos_agg.shape[1]} features")
    return pos_agg


def build_master_table(tables, save=True):
    """
    Build the master analytic table: application_train
    LEFT JOINed with all aggregated sub-tables.

    When cached merged_master.parquet exists, loads it directly instead
    of recomputing from scratch (saves significant time and memory).

    This is the analytical equivalent of what a CDR API gateway would
    return for a single customer view.
    """
    print("\n" + "=" * 60)
    print("BUILDING MASTER TABLE — CDR-style multi-source JOIN")
    if USE_CACHE and os.path.exists(PROC_MERGED):
        print("  (loading pre-built master table from cache)")
        print("=" * 60)
        master = pd.read_parquet(PROC_MERGED)
        print(f"Master table: {master.shape[0]:,} rows × {master.shape[1]} cols")
        print(f"Loaded from → {PROC_MERGED}")
        return master

    print("=" * 60)

    app = tables["application"].copy()

    # Aggregate sub-tables
    bureau_agg = aggregate_bureau(tables["bureau"], tables["bureau_balance"])
    prev_agg = aggregate_previous_application(tables["previous_application"])
    cc_agg = aggregate_credit_card(tables["credit_card_balance"])
    inst_agg = aggregate_installments(tables["installments_payments"])
    pos_agg = aggregate_pos_cash(tables["pos_cash_balance"])

    # LEFT JOIN chain
    print("\nJoining tables ...")
    master = (
        app
        .merge(bureau_agg, on="SK_ID_CURR", how="left")
        .merge(prev_agg, on="SK_ID_CURR", how="left")
        .merge(cc_agg, on="SK_ID_CURR", how="left")
        .merge(inst_agg, on="SK_ID_CURR", how="left")
        .merge(pos_agg, on="SK_ID_CURR", how="left")
    )

    # Report join coverage
    n_app = len(app)
    for name, df in [("bureau", bureau_agg), ("previous_app", prev_agg),
                      ("credit_card", cc_agg), ("installments", inst_agg),
                      ("pos_cash", pos_agg)]:
        matched = master[df.columns[0]].notna().sum()  # first agg col
        print(f"  {name:20s}: {matched/n_app*100:5.1f}% matched")

    print(f"\nMaster table: {master.shape[0]:,} rows × {master.shape[1]} cols")

    if save:
        master.to_parquet(PROC_MERGED, index=False)
        print(f"Saved → {PROC_MERGED}")

    return master
