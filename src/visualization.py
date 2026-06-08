"""
Reusable visualization helpers with consistent Westpac-branded theming.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import pandas as pd
import os

from .config import PALETTE, SEABORN_STYLE, FIGURE_DPI, FIGSIZE_DEFAULT, FIGSIZE_WIDE, FIGURES

# ── Global style ───────────────────────────────────────────────────
sns.set_style(SEABORN_STYLE)
plt.rcParams.update({
    "figure.dpi": FIGURE_DPI,
    "savefig.dpi": 150,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})


def save_figure(fig, filename, close=True):
    """Save figure to outputs/figures/."""
    os.makedirs(FIGURES, exist_ok=True)
    path = os.path.join(FIGURES, filename)
    fig.savefig(path, bbox_inches="tight", dpi=150, facecolor="white")
    if close:
        plt.close(fig)
    print(f"  Figure saved → {path}")


# ── EDA Charts ─────────────────────────────────────────────────────

def plot_age_pyramid(df, age_col="AGE_YEARS", young_cutoff=35, title="Customer Age Distribution"):
    """Horizontal age distribution histogram with Gen Z/Millennial highlight."""
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    young = df[df[age_col] < young_cutoff][age_col]
    mature = df[df[age_col] >= young_cutoff][age_col]

    bins = np.arange(20, 75, 2)
    ax.hist(mature, bins=bins, alpha=0.7, label=f"≥{young_cutoff}", color=PALETTE["mature"], edgecolor="white")
    ax.hist(young, bins=bins, alpha=0.85, label=f"<{young_cutoff} (Gen Z / Millennial)", color=PALETTE["young"], edgecolor="white")

    ax.axvline(young_cutoff, color=PALETTE["primary"], linestyle="--", linewidth=2, label=f"Age {young_cutoff}")
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Customer Count")
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="upper right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    return fig


def plot_income_by_segment(df, segment_col, income_col="income_total",
                           title="Income Distribution by Segment"):
    """Box plot of income by customer segment."""
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    segments = df.groupby(segment_col)[income_col].apply(list).to_dict()
    # Sort by median
    order = sorted(segments, key=lambda k: np.median(segments[k]), reverse=True)

    bp = ax.boxplot([segments[k] for k in order], labels=order, patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], sns.color_palette("Set2", len(order))):
        patch.set_facecolor(color)

    ax.set_ylabel("Annual Income (AUD equivalent)")
    ax.set_title(title, fontweight="bold")
    ax.tick_params(axis="x", rotation=15)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    return fig


def plot_channel_pie(broker_pct, direct_pct, title="Estimated Channel Mix"):
    """Broker vs Direct channel donut chart."""
    fig, ax = plt.subplots(figsize=(6, 6))

    sizes = [broker_pct, direct_pct]
    labels = [f"Broker\n({broker_pct*100:.1f}%)", f"Direct\n({direct_pct*100:.1f}%)"]
    colors = [PALETTE["broker"], PALETTE["direct"]]
    explode = (0.02, 0.02)

    wedges, texts = ax.pie(sizes, labels=labels, colors=colors, explode=explode,
                            startangle=90, textprops={"fontsize": 12, "fontweight": "bold"})
    # Donut hole
    centre = plt.Circle((0, 0), 0.55, fc="white")
    ax.add_artist(centre)
    ax.set_title(title, fontweight="bold", fontsize=13)

    return fig


# ── Feature / Score Charts ─────────────────────────────────────────

def plot_feature_importance(importance_df, title="Feature Importance (SHAP)", top_n=15):
    """Horizontal bar chart of top-N feature importance."""
    fig, ax = plt.subplots(figsize=(8, top_n * 0.35 + 2))

    imp = importance_df.head(top_n).iloc[::-1]  # reverse for horizontal
    bars = ax.barh(imp["feature"], imp["mean_abs_shap"], color=PALETTE["accent"], edgecolor="white")

    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title(title, fontweight="bold")

    return fig


def plot_score_distribution(scores, bins=50, title="Composite Score Distribution"):
    """Histogram of composite scores with tier color bands."""
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    ax.hist(scores, bins=bins, color=PALETTE["primary"], alpha=0.75, edgecolor="white")

    # Tier bands
    for cutoff, color, label in [
        (30, PALETTE["tier_1"], "Exploring"),
        (55, PALETTE["tier_2"], "Building"),
        (75, PALETTE["tier_3"], "Almost Ready"),
    ]:
        ax.axvline(cutoff, color=color, linestyle="--", linewidth=1.5, alpha=0.7)
        ax.text(cutoff + 1, ax.get_ylim()[1] * 0.95, label, color=color, fontsize=9, fontweight="bold")

    ax.set_xlabel("Score (0–100)")
    ax.set_ylabel("Customer Count")
    ax.set_title(title, fontweight="bold")

    return fig


def plot_dimension_radar(dimension_scores, segment_labels=None, title="Dimension Profile"):
    """
    Radar/spider chart of 6 dimension scores.
    dimension_scores: dict of {dimension_name: [values]} or single list of 6 values.
    """
    dimensions = list(dimension_scores.keys())
    N = len(dimensions)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})

    values = [np.mean(v) if isinstance(v, (list, np.ndarray, pd.Series)) else v
              for v in dimension_scores.values()]
    values += values[:1]

    ax.fill(angles, values, alpha=0.25, color=PALETTE["accent"])
    ax.plot(angles, values, "o-", linewidth=2, color=PALETTE["accent"], label=segment_labels or "Overall")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([d.replace("_", " ").title() for d in dimensions], fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
    ax.set_title(title, fontweight="bold", pad=20)

    if segment_labels:
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))

    return fig


# ── Model Evaluation Charts ────────────────────────────────────────

def plot_roc_curves(results_dict, title="ROC Curves"):
    """
    Plot ROC curves for multiple models.
    results_dict: {model_name: {"y_test": ..., "y_pred_proba": ...}, ...}
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_DEFAULT)

    colors = sns.color_palette("Set2", len(results_dict))
    for (name, res), color in zip(results_dict.items(), colors):
        fpr, tpr, _ = roc_curve(res["y_test"], res["y_pred_proba"])
        ax.plot(fpr, tpr, linewidth=2, color=color, label=f"{name} (AUC={res['auc_roc']:.3f})")

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.3, label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="lower right")

    return fig


def plot_confusion_matrix(y_true, y_pred, labels=None, title="Confusion Matrix"):
    """Confusion matrix heatmap."""
    from sklearn.metrics import confusion_matrix as cm

    fig, ax = plt.subplots(figsize=(5, 4))
    cmat = cm(y_true, y_pred)
    sns.heatmap(cmat, annot=True, fmt="d", cmap="Reds", ax=ax,
                xticklabels=labels or ["Pred 0", "Pred 1"],
                yticklabels=labels or ["True 0", "True 1"])
    ax.set_title(title, fontweight="bold")
    ax.set_ylabel("Actual")
    ax.set_xlabel("Predicted")

    return fig


def plot_shap_summary(shap_result, max_display=20, title="SHAP Summary"):
    """SHAP beeswarm summary plot."""
    try:
        import shap

        fig, ax = plt.subplots(figsize=(8, max_display * 0.3 + 2))
        shap.summary_plot(
            shap_result["shap_values"],
            shap_result.get("X_sample"),
            feature_names=shap_result["feature_names"],
            max_display=max_display,
            show=False,
        )
        ax.set_title(title, fontweight="bold")
        return fig
    except Exception:
        return None


# ── Business Charts ────────────────────────────────────────────────

def plot_waterfall(steps, title="Financial Waterfall"):
    """
    Waterfall chart.
    steps: list of (label, value, color) tuples.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    cumulative = 0
    for i, (label, value, color) in enumerate(steps):
        if value >= 0:
            ax.bar(i, value, bottom=cumulative, color=color, edgecolor="white", width=0.6)
        else:
            ax.bar(i, value, bottom=cumulative + value, color=color, edgecolor="white", width=0.6)
        cumulative += value
        ax.text(i, cumulative + (value * 0.02 if value >= 0 else value * 0.1),
                f"${value:+.1f}M" if abs(value) >= 0.01 else "",
                ha="center", fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s[0] for s in steps], rotation=30, ha="right")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("AUD (Millions)")
    ax.set_title(title, fontweight="bold")

    return fig


def plot_sensitivity_tornado(scenarios, metric="ROI", title="Sensitivity Analysis"):
    """
    Tornado chart for sensitivity analysis.
    scenarios: dict of {scenario_name: metric_value}
    """
    fig, ax = plt.subplots(figsize=(7, 0.5 * len(scenarios) + 2))

    items = sorted(scenarios.items(), key=lambda x: x[1])
    labels, values = zip(*items)

    colors = [PALETTE["tier_4"] if v > 1.0 else
              PALETTE["tier_2"] if v > 0.8 else
              PALETTE["tier_1"] for v in values]

    bars = ax.barh(labels, values, color=colors, edgecolor="white")
    ax.axvline(1.0, color="black", linestyle="--", linewidth=1.2, label=f"Breakeven ({metric}=1.0)")
    ax.axvline(values[0] if values else 0, color=PALETTE["accent"], linestyle="--", alpha=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}x", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel(f"{metric} (x)")
    ax.set_title(title, fontweight="bold")
    ax.legend(loc="lower right")

    return fig
