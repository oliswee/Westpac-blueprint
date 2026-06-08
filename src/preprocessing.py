"""
Preprocessing: missing value imputation, outlier handling, encoding.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer


def data_quality_report(df, top_n=15):
    """
    Generate a data quality summary: missing %, cardinality, dtype, skew.
    """
    n = len(df)
    report = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.values.astype(str),
        "missing_pct": (df.isnull().sum() / n * 100).values,
        "missing_n": df.isnull().sum().values,
        "cardinality": [df[c].nunique() for c in df.columns],
    })

    # Skew only for numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    skew_vals = df[numeric_cols].skew()
    report["skew"] = report["column"].map(skew_vals)

    report = report.sort_values("missing_pct", ascending=False).reset_index(drop=True)
    return report


def recode_days_employed(df, col="DAYS_EMPLOYED"):
    """
    Recode DAYS_EMPLOYED: 365243 = unemployed/pensioner → NaN,
    then convert negative days to positive years.
    """
    df = df.copy()
    mask_unemployed = df[col] >= 365243  # anomaly flag in Home Credit
    df.loc[mask_unemployed, col] = np.nan

    # Negative values = days employed → make positive
    df[col] = df[col].abs()
    df["YEARS_EMPLOYED"] = df[col] / 365.25
    df["IS_UNEMPLOYED"] = mask_unemployed.astype(int)

    return df


def recode_days_birth(df, col="DAYS_BIRTH"):
    """Convert negative DAYS_BIRTH to positive age in years."""
    df = df.copy()
    df["AGE_YEARS"] = df[col].abs() / 365.25
    df["IS_YOUNG"] = (df["AGE_YEARS"] < 35).astype(int)
    return df


def handle_missing_values(df, strategy="auto"):
    """
    Handle missing values:
    - Numeric columns: median imputation
    - Categorical columns: mode imputation + flag column
    - If >80% missing, drop the column.
    """
    df = df.copy()
    n = len(df)

    # Drop columns with >80% missing
    threshold = 0.80
    high_missing = [c for c in df.columns if df[c].isnull().mean() > threshold]
    if high_missing:
        print(f"  Dropping {len(high_missing)} columns with >{threshold*100:.0f}% missing")
        df = df.drop(columns=high_missing)

    # Numeric → median
    num_cols = df.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        if df[c].isnull().sum() > 0:
            df[c] = df[c].fillna(df[c].median())

    # Categorical → mode
    cat_cols = df.select_dtypes(include=["object", "category"]).columns
    for c in cat_cols:
        if df[c].isnull().sum() > 0:
            df[c] = df[c].fillna(df[c].mode()[0] if len(df[c].mode()) > 0 else "MISSING")

    return df


def encode_categoricals(df, cols=None, method="label"):
    """
    Encode categorical columns.
    - method='label': LabelEncoder per column
    - method='onehot': pd.get_dummies (use with caution on high-cardinality)
    """
    df = df.copy()
    if cols is None:
        cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if method == "label":
        for c in cols:
            if c in df.columns:
                le = LabelEncoder()
                df[c + "_enc"] = le.fit_transform(df[c].astype(str))
        # Drop original categorical columns after encoding
        df = df.drop(columns=[c for c in cols if c in df.columns], errors="ignore")

    elif method == "onehot":
        df = pd.get_dummies(df, columns=cols, drop_first=True)

    return df


def clean_application(df):
    """
    Full cleaning pipeline for application_train.
    """
    print("Cleaning application_train ...")

    df = df.copy()

    # Recode DAYS_EMPLOYED & DAYS_BIRTH
    df = recode_days_employed(df)
    df = recode_days_birth(df)

    # Drop original DAYS_* columns (keep recoded versions)
    df = df.drop(columns=["DAYS_EMPLOYED", "DAYS_BIRTH"], errors="ignore")

    # Recode gender
    if "CODE_GENDER" in df.columns:
        df["IS_FEMALE"] = (df["CODE_GENDER"] == "F").astype(int)
        df = df.drop(columns=["CODE_GENDER"])

    # Handle anomalous FLAG_DOCUMENT columns
    doc_cols = [c for c in df.columns if c.startswith("FLAG_DOCUMENT_")]
    if doc_cols:
        # Some have value 3 — treat as 1 (submitted)
        for c in doc_cols:
            df[c] = df[c].clip(0, 1)

    # Convert FLAG_OWN_CAR / FLAG_OWN_REALTY from Y/N strings to int
    for col in ["FLAG_OWN_CAR", "FLAG_OWN_REALTY"]:
        if col in df.columns:
            # Force conversion regardless of dtype (handles ArrowStringArray in pandas 3.0)
            df[col] = df[col].astype(str).map({"Y": 1, "N": 0, "1": 1, "0": 0}).fillna(0).astype(int)
            df[col] = df[col].astype(int)

    # Replace inf
    df = df.replace([np.inf, -np.inf], np.nan)

    # General missing value handling
    df = handle_missing_values(df)

    print(f"  → Cleaned: {df.shape[0]:,} × {df.shape[1]}")
    return df


def remove_outliers_iqr(df, cols, factor=3.0):
    """
    Cap outliers using IQR method: values beyond Q1 - factor*IQR
    and Q3 + factor*IQR are clipped (not dropped).
    """
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            continue
        q1 = df[c].quantile(0.25)
        q3 = df[c].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - factor * iqr, q3 + factor * iqr
        n_clipped = ((df[c] < lo) | (df[c] > hi)).sum()
        if n_clipped > 0:
            df[c] = df[c].clip(lo, hi)
            print(f"  {c}: clipped {n_clipped} values to [{lo:.2f}, {hi:.2f}]")
    return df
