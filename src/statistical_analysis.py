"""Statistical analysis of IMF concern scores vs crisis events.

Reads:
  - data/results/concern_scores.csv  (produced by Vittoria's run_scoring.py)
  - data/crises.csv                  (R-R + manual crisis flags)
  - data/countries.csv               (treatment/control groups)

Produces:
  - data/results/ttest_results.csv             (crisis vs control t-tests)
  - data/figures/roc_curve.png                 (predictive power per dimension)
  - data/figures/{country}_timeseries.png      (per-country score evolution)
  - data/figures/summary_comparison.png        (group-level bar chart)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_auc_score, roc_curve


# ===== Paths =====
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"

SCORES_CSV = RESULTS_DIR / "concern_scores.csv"
CRISES_CSV = DATA_DIR / "crises.csv"
COUNTRIES_CSV = DATA_DIR / "countries.csv"

TTEST_OUT = RESULTS_DIR / "ttest_results.csv"

DIMENSIONS = ["q1_fiscal", "q2_banking", "q3_policy", "q4_deterioration", "q5_external"]


def load_data() -> pd.DataFrame:
    """Merge scores + crisis flags + group labels into one analysis frame."""
    if not SCORES_CSV.exists():
        raise FileNotFoundError(
            f"{SCORES_CSV} not found yet. Scoring needs to run first."
        )

    scores = pd.read_csv(SCORES_CSV)
    crises = pd.read_csv(CRISES_CSV)
    countries = pd.read_csv(COUNTRIES_CSV)[["country", "group"]]

   
    for d in (scores, crises, countries):
        d["country"] = (
            d["country"].str.strip().str.replace("_", " ", regex=False).str.title()
        )
    

    # Merge on (country, year)
    df = scores.merge(crises, on=["country", "year"], how="left")
    df = df.merge(countries, on="country", how="left")
    return df


#Analysis 1: T-tests 
def add_precrisis_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Mark country-years that fall 1-2 years BEFORE a crisis."""
    df = df.sort_values(["country", "year"]).copy()
    df["any_crisis"] = df["any_crisis"].fillna(0)

    
    df["crisis_t1"] = df.groupby("country")["any_crisis"].shift(-1).fillna(0)
    df["crisis_t2"] = df.groupby("country")["any_crisis"].shift(-2).fillna(0)
    df["pre_crisis"] = ((df["crisis_t1"] == 1) | (df["crisis_t2"] == 1)).astype(int)
    return df


def run_ttests(df: pd.DataFrame) -> pd.DataFrame:
    """Compare PRE-CRISIS scores (1-2 yrs before a crisis) vs calm years."""
    df = add_precrisis_flag(df)

    results = []
    for dim in DIMENSIONS:
        if dim not in df.columns:
            print(f"  WARN: column '{dim}' not in scores — skipping")
            continue
        pre = df[df["pre_crisis"] == 1][dim].dropna()
        calm = df[df["pre_crisis"] == 0][dim].dropna()

        if len(pre) < 2 or len(calm) < 2:
            print(f"  WARN: not enough data for '{dim}' (pre={len(pre)}, calm={len(calm)})")
            continue

        t_stat, p_value = stats.ttest_ind(pre, calm, equal_var=False)
        u_stat, u_pvalue = stats.mannwhitneyu(pre, calm, alternative="two-sided")

        results.append({
            "dimension": dim,
            "n_precrisis": len(pre),
            "n_calm": len(calm),
            "mean_precrisis": round(pre.mean(), 2),
            "mean_calm": round(calm.mean(), 2),
            "diff": round(pre.mean() - calm.mean(), 2),
            "t_stat": round(t_stat, 3),
            "t_pvalue": round(p_value, 4),
            "mannwhitney_pvalue": round(u_pvalue, 4),
            "significant_005": p_value < 0.05,
        })

    return pd.DataFrame(results)




#Analysis 2: ROC curves 
def plot_roc_curves(df: pd.DataFrame, out_path: Path) -> None:
    """Plot ROC curves for each dimension's ability to predict next-year crisis."""
    fig, ax = plt.subplots(figsize=(8, 7))

    df = df.sort_values(["country", "year"]).copy()
    # any_crisis at t+1 = next year's crisis flag
    df["crisis_next_year"] = df.groupby("country")["any_crisis"].shift(-1)

    plotted = 0
    for dim in DIMENSIONS:
        if dim not in df.columns:
            continue
        sub = df.dropna(subset=[dim, "crisis_next_year"])
        if sub["crisis_next_year"].nunique() < 2:
            print(f"  WARN: '{dim}' has no variation in crisis_next_year, skipping ROC")
            continue
        y_true = sub["crisis_next_year"].astype(int)
        y_score = sub[dim]
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auc = roc_auc_score(y_true, y_score)
        ax.plot(fpr, tpr, label=f"{dim.capitalize()} (AUC = {auc:.2f})", linewidth=2)
        plotted += 1

    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Random (AUC = 0.50)")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC: IMF Concern Scores Predicting Next-Year Crisis")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  Saved ROC curve ({plotted} dimensions plotted)")


#  Analysis 3: Per-country time series
def plot_country_timeseries(df: pd.DataFrame, country: str, out_path: Path) -> None:
    """Plot all 5 concern dimensions over years for one country, with crisis shading."""
    sub = df[df["country"] == country].sort_values("year").copy()
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each dimension
    palette = sns.color_palette("husl", len(DIMENSIONS))
    for color, dim in zip(palette, DIMENSIONS):
        if dim in sub.columns:
            ax.plot(sub["year"], sub[dim], marker="o", label=dim.capitalize(),
                    color=color, linewidth=2)

    # Shade crisis years
    crisis_years = sub[sub["any_crisis"] == 1]["year"].tolist()
    for year in crisis_years:
        ax.axvspan(year - 0.5, year + 0.5, color="red", alpha=0.15, zorder=0)

    ax.set_xlabel("Year")
    ax.set_ylabel("Concern Score (0-10)")
    ax.set_title(f"{country}: IMF Concern Scores Over Time\n"
                 f"(Red shading = crisis year per Reinhart-Rogoff / manual coding)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 10.5)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


# Analysis 4: Summary comparison 
def plot_summary(df: pd.DataFrame, out_path: Path) -> None:
    """Bar chart: average score per dimension, treatment vs control vs crisis years."""
    fig, ax = plt.subplots(figsize=(10, 6))

    rows = []
    for dim in DIMENSIONS:
        if dim not in df.columns:
            continue
        rows.append({
            "dimension": dim.capitalize(),
            "Treatment (no crisis yr)": df[(df["group"] == "treatment") & (df["any_crisis"] == 0)][dim].mean(),
            "Crisis year": df[df["any_crisis"] == 1][dim].mean(),
            "Control": df[df["group"] == "control"][dim].mean(),
        })

    plot_df = pd.DataFrame(rows).set_index("dimension")
    plot_df.plot(kind="bar", ax=ax, width=0.75)

    ax.set_ylabel("Average Concern Score (0-10)")
    ax.set_title("Average IMF Concern Scores by Country Group and Crisis Status")
    ax.set_ylim(0, 10)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


# Main
def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    df = load_data()
    print(f"  Loaded {len(df)} country-year rows")
    print(f"  Countries: {df['country'].nunique()}")
    print(f"  Crisis years total: {int(df['any_crisis'].sum())}")

    print("\n=== Analysis 1: T-tests (crisis vs normal) ===")
    ttest_df = run_ttests(df)
    if not ttest_df.empty:
        print(ttest_df.to_string(index=False))
        ttest_df.to_csv(TTEST_OUT, index=False)
        print(f"  Saved to {TTEST_OUT}")

    print("\n=== Analysis 2: ROC curves ===")
    plot_roc_curves(df, FIGURES_DIR / "roc_curve.png")

    print("\n=== Analysis 3: Per-country time series ===")
    for country in df["country"].unique():
        out = FIGURES_DIR / f"{country.lower().replace(' ', '_')}_timeseries.png"
        plot_country_timeseries(df, country, out)
    print(f"  Saved {df['country'].nunique()} country plots to {FIGURES_DIR}")

    print("\n=== Analysis 4: Summary comparison ===")
    plot_summary(df, FIGURES_DIR / "summary_comparison.png")
    print(f"  Saved summary_comparison.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
    