"""
Model training, evaluation, and SHAP explainability.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc,
    classification_report, confusion_matrix, roc_curve, f1_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold
import xgboost as xgb
import lightgbm as lgb

import os
import pickle
from .config import MODELS_DIR


def prepare_model_data(features_df, target_col="TARGET", id_col="SK_ID_CURR",
                       drop_cols=None, test_size=0.2, random_state=42):
    """
    Prepare train/test split from feature table.
    Handles inf/nan, low-variance features, and redundant feature removal.
    """
    if drop_cols is None:
        drop_cols = []

    # Import redundant features list from config
    from .config import DROP_FOR_MODELING

    # Build exclude list: IDs, analysis-only columns + user-supplied + redundant
    base_exclude = [id_col, target_col]
    exclude = base_exclude + drop_cols + DROP_FOR_MODELING
    exclude = [c for c in exclude if c in features_df.columns]
    dropped_redundant = len([c for c in DROP_FOR_MODELING if c in features_df.columns])

    X = features_df.drop(columns=exclude, errors="ignore")
    X = X.select_dtypes(include=[np.number]).copy()
    y = features_df[target_col]

    # Handle inf/nan
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())

    # Drop zero/low-variance columns
    sel = VarianceThreshold(threshold=0.001)
    sel.fit(X)
    kept = [c for c, v in zip(X.columns, sel.get_support()) if v]
    X = X[kept]
    dropped_var = len(X.columns) - len(kept)

    print(f"  Dropped {dropped_redundant} redundant features | Dropped {dropped_var} low-variance")
    print(f"  Features for modeling: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"  Train: {X_train.shape[0]:,} x {X_train.shape[1]} | Test: {X_test.shape[0]:,}")
    print(f"  Target rate: {y_train.mean():.3f} (train) | {y_test.mean():.3f} (test)")

    return X_train, X_test, y_train, y_test, X.columns.tolist()


def train_logistic_regression(X_train, X_test, y_train, y_test):
    """Baseline: Logistic Regression with standard scaling."""
    print("\n── Logistic Regression (Baseline) ──")

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = LogisticRegression(
        max_iter=2000, random_state=42,
        class_weight="balanced", n_jobs=-1
    )
    model.fit(X_train_s, y_train)

    y_pred_proba = model.predict_proba(X_test_s)[:, 1]
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    auc_pr = auc(recall, precision)

    print(f"  Test AUC-ROC: {auc_roc:.4f}")
    print(f"  Test AUC-PR:  {auc_pr:.4f}")

    return {
        "model": model, "scaler": scaler, "name": "LogisticRegression",
        "auc_roc": auc_roc, "auc_pr": auc_pr, "y_pred_proba": y_pred_proba,
    }


def train_xgboost(X_train, X_test, y_train, y_test):
    """
    XGBoost with tuned hyperparameters for imbalanced data.
    Uses scale_pos_weight ≈ negative/positive ratio.
    """
    print("\n── XGBoost (Tuned) ──")

    pos_weight = round((y_train == 0).sum() / (y_train == 1).sum())
    model = xgb.XGBClassifier(
        n_estimators=400, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.7, min_child_weight=5,
        gamma=0.1, reg_alpha=0.1, reg_lambda=1.0,
        scale_pos_weight=pos_weight,
        objective="binary:logistic", eval_metric="auc",
        random_state=42, n_jobs=1,
    )
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    auc_pr = auc(recall, precision)

    print(f"  AUC-ROC: {auc_roc:.4f} | AUC-PR: {auc_pr:.4f}")

    return {
        "model": model, "name": "XGBoost",
        "auc_roc": auc_roc, "auc_pr": auc_pr, "y_pred_proba": y_pred_proba,
    }


def train_lightgbm(X_train, X_test, y_train, y_test):
    """
    LightGBM with tuned hyperparameters.
    Uses class_weight='balanced' for imbalance.
    """
    print("\n── LightGBM (Tuned) ──")

    model = lgb.LGBMClassifier(
        n_estimators=500, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.7, num_leaves=63,
        min_child_samples=50, reg_alpha=0.1, reg_lambda=0.1,
        class_weight="balanced",
        objective="binary", metric="auc",
        random_state=42, n_jobs=1, verbose=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
    )

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    auc_pr = auc(recall, precision)

    print(f"  AUC-ROC: {auc_roc:.4f} | AUC-PR: {auc_pr:.4f}")

    return {
        "model": model, "name": "LightGBM",
        "auc_roc": auc_roc, "auc_pr": auc_pr, "y_pred_proba": y_pred_proba,
    }


def compare_models(*results):
    """Print comparison table for trained models."""
    print("\n" + "=" * 50)
    print("MODEL COMPARISON")
    print("=" * 50)
    for r in sorted(results, key=lambda x: x["auc_roc"], reverse=True):
        print(f"  {r['name']:25s}  AUC-ROC: {r['auc_roc']:.4f}  AUC-PR: {r['auc_pr']:.4f}")


def compute_shap_values(model, X_sample, feature_names):
    """Compute SHAP values for a tree-based model."""
    print(f"\nComputing SHAP values (n={X_sample.shape[0]:,}) ...")
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        print(f"  SHAP matrix shape: {shap_values.shape}")
        return {"shap_values": shap_values, "explainer": explainer, "feature_names": feature_names}
    except ImportError:
        print("  [!] SHAP not installed — skipping")
        return None


def get_top_features(shap_result, top_n=15):
    """Return top N features by mean absolute SHAP value."""
    if shap_result is None:
        return None
    mean_abs_shap = np.abs(shap_result["shap_values"]).mean(axis=0)
    importance = pd.DataFrame({
        "feature": shap_result["feature_names"],
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).head(top_n)
    return importance


def find_best_threshold(y_true, y_pred_proba):
    """Find threshold that maximizes F1 score."""
    best_f1, best_thresh = 0, 0.5
    for t in np.linspace(0.05, 0.7, 65):
        f1 = f1_score(y_true, (y_pred_proba >= t).astype(int))
        if f1 > best_f1:
            best_f1, best_thresh = f1, t
    return best_thresh, best_f1


def save_model(model, filename):
    """Save a trained model to disk."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(MODELS_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved → {path}")


def generate_model_report(results, shap_result, y_test, y_pred_proba,
                          feature_names, save_path=None):
    """Generate a structured model evaluation summary."""
    best = max(results, key=lambda r: r["auc_roc"])
    y_best = best["y_pred_proba"]

    best_thresh, best_f1 = find_best_threshold(y_test, y_best)
    y_binary = (y_best >= best_thresh).astype(int)
    report = classification_report(y_test, y_binary, target_names=["No Default", "Default"])
    cm = confusion_matrix(y_test, y_binary)

    top_f = (get_top_features(shap_result, top_n=10).to_string(index=False)
             if shap_result else "N/A")

    summary = f"""
    MODEL EVALUATION SUMMARY
    {'='*50}

    Best Model: {best['name']}
    AUC-ROC:    {best['auc_roc']:.4f}
    AUC-PR:     {best['auc_pr']:.4f}
    Best F1:    {best_f1:.4f} (threshold = {best_thresh:.2f})

    Confusion Matrix (threshold={best_thresh:.2f}):
      TN={cm[0,0]}  FP={cm[0,1]}
      FN={cm[1,0]}  TP={cm[1,1]}

    Top-10 Features (by SHAP):
    {top_f}

    Classification Report:
    {report}
    """
    print(summary)

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            f.write(summary)
        print(f"Report saved → {save_path}")

    return summary
