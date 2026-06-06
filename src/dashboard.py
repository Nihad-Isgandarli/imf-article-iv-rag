"""Interactive dashboard for the IMF Article IV concern scores.

Streamlit app that lets users explore the concern scores by country and year,
visualize how the 5 risk dimensions evolve over time, and see which years
correspond to actual financial crises (shaded in red).

Run with:  streamlit run src/dashboard.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt

# --- Paths (same convention as the other scripts) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORES_CSV = PROJECT_ROOT / "data" / "results" / "concern_scores.csv"
CRISES_CSV = PROJECT_ROOT / "data" / "crises.csv"

# The 5 score columns and friendly labels for the chart
SCORE_COLUMNS = {
    "q1_fiscal": "Fiscal",
    "q2_banking": "Banking",
    "q3_policy": "Policy urgency",
    "q4_deterioration": "Deterioration",
    "q5_external": "External",
}

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load concern scores and crisis data, merge them, and return one table.

    Returns:
        A DataFrame with one row per country-year, the 5 scores, the total,
        and an 'any_crisis' flag (1 if a crisis occurred that year).
    """
    scores = pd.read_csv(SCORES_CSV)
    crises = pd.read_csv(CRISES_CSV)

    # Normalize country names to lowercase in BOTH files so they match
    scores["country"] = scores["country"].str.lower()
    crises["country"] = crises["country"].str.lower()

    # Keep only the columns we need from the crises file
    crises_small = crises[["country", "year", "any_crisis"]]

    # Merge: attach the crisis flag to each country-year score row
    merged = scores.merge(crises_small, on=["country", "year"], how="left")

    # Some score years may have no crisis row → fill those with 0 (no crisis)
    merged["any_crisis"] = merged["any_crisis"].fillna(0).astype(int)

    return merged

# --- Page setup ---
st.set_page_config(page_title="IMF Article IV — Concern Scores", layout="wide")

st.title("IMF Article IV — Crisis Warning Signals")
st.markdown(
    "Concern scores (0–10) extracted from IMF Article IV reports using RAG. "
    "Higher scores mean the IMF expressed more concern. Red bands mark years "
    "with an actual financial crisis."
)

# Load the data once
data = load_data()

# --- Sidebar: country selector ---
st.sidebar.header("Controls")

countries = sorted(data["country"].unique())
selected_country = st.sidebar.selectbox("Select a country", countries)

# Filter the data to just the selected country, sorted by year
country_data = data[data["country"] == selected_country].sort_values("year")

# --- Main chart: concern scores over time ---
st.subheader(f"Concern scores over time — {selected_country.title()}")

# 1. Reshape the data from "wide" to "long" format for Altair.
#    Altair wants one row per (year, dimension, score) instead of one row
#    per year with 5 score columns.
long_data = country_data.melt(
    id_vars=["year"],
    value_vars=list(SCORE_COLUMNS.keys()),
    var_name="dimension",
    value_name="score",
)
# Replace the technical names (q1_external) with friendly labels (External)
long_data["dimension"] = long_data["dimension"].map(SCORE_COLUMNS)

# 2. The line chart: one colored line per risk dimension
lines = alt.Chart(long_data).mark_line(point=True).encode(
    x=alt.X("year:O", title="Year"),
    y=alt.Y("score:Q", title="Concern score (0–10)", scale=alt.Scale(domain=[0, 10])),
    color=alt.Color("dimension:N", title="Risk dimension"),
    tooltip=["year", "dimension", "score"],
)

# 3. The red bands: one vertical rule for each crisis year
crisis_years = country_data[country_data["any_crisis"] == 1]["year"].tolist()
if crisis_years:
    crisis_df = pd.DataFrame({"year": crisis_years})
    bands = alt.Chart(crisis_df).mark_rule(
        color="red", strokeWidth=3, opacity=0.4
    ).encode(x="year:O")
    chart = bands + lines
else:
    chart = lines

st.altair_chart(chart.properties(height=400), width='stretch')

# --- Summary statistics ---
st.subheader("Summary")

col1, col2, col3 = st.columns(3)

avg_total = country_data["total_score"].mean()
col1.metric("Average total score", f"{avg_total:.1f} / 50")

n_crisis_years = int(country_data["any_crisis"].sum())
col2.metric("Crisis years in data", n_crisis_years)

# Compare average total score in crisis years vs non-crisis years
crisis_rows = country_data[country_data["any_crisis"] == 1]
calm_rows = country_data[country_data["any_crisis"] == 0]
if len(crisis_rows) > 0 and len(calm_rows) > 0:
    diff = crisis_rows["total_score"].mean() - calm_rows["total_score"].mean()
    col3.metric("Crisis vs calm (total)", f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}")
else:
    col3.metric("Crisis vs calm (total)", "n/a")

# --- Raw data table ---
st.subheader("Data")
display_cols = ["year"] + list(SCORE_COLUMNS.keys()) + ["total_score", "any_crisis"]
st.dataframe(country_data[display_cols], width='stretch', hide_index=True)