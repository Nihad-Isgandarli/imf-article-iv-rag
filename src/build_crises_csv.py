"""Build a clean crises.csv from Reinhart-Rogoff + manual additions.

Output: data/crises.csv with one row per country-year for our 12 countries.
Columns: country, year, banking, currency, inflation, sovereign_debt, any_crisis

R-R covers 1800-2016 for 10 of our countries; Lebanon and Pakistan are
added manually. Post-2016 crisis events are added manually for all
countries (R-R data ends in 2016).
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CRISES_XLSX = DATA_DIR / "crises_raw.xlsx"
COUNTRIES_CSV = DATA_DIR / "countries.csv"
OUT_CSV = DATA_DIR / "crises.csv"


# Our 12 countries
OUR_COUNTRIES = [
    "Turkey", "Argentina", "Sri Lanka", "Lebanon", "Zambia", "Pakistan",
    "Ghana", "Egypt", "Ecuador", "Switzerland", "Canada", "Korea",
    "Poland", "Malaysia",
]

# Year range we care about for analysis
YEAR_START = 2010
YEAR_END = 2024


def load_rr() -> pd.DataFrame:
    """Load R-R Excel and drop the 'x' indicator row right after the header."""
    df = pd.read_excel(CRISES_XLSX, sheet_name="Sheet1", header=0)
    df = df.iloc[1:].reset_index(drop=True)
    return df


def extract_country_from_rr(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """Pull rows for one country and select the crisis columns we need."""
    sub = df[df["Country"] == country].copy()
    sub["Year"] = pd.to_numeric(sub["Year"], errors="coerce")
    sub = sub.dropna(subset=["Year"])
    sub["Year"] = sub["Year"].astype(int)

    # Pick relevant columns; R-R column 18 = External Debt Default 1 (no official)
    ext_debt_col = [c for c in df.columns if "SOVEREIGN EXTERNAL DEBT 1" in str(c)][0]

    out = pd.DataFrame({
        "country": country,
        "year": sub["Year"],
        "banking": pd.to_numeric(sub["Banking Crisis "], errors="coerce").fillna(0).astype(int),
        "currency": pd.to_numeric(sub["Currency Crises"], errors="coerce").fillna(0).astype(int),
        "inflation": pd.to_numeric(sub["Inflation Crises"], errors="coerce").fillna(0).astype(int),
        "sovereign_debt": pd.to_numeric(sub[ext_debt_col], errors="coerce").fillna(0).astype(int),
    })
    return out


# Manual additions for countries / years not covered by R-R (post-2016 or missing)
# Source: well-documented public events (IMF program announcements, news, Laeven-Valencia 2020)
MANUAL_CRISES = pd.DataFrame([
    # country, year, banking, currency, inflation, sovereign_debt
    # Lebanon — banking + sovereign crisis from 2019
    ("Lebanon", 2019, 1, 1, 0, 0),
    ("Lebanon", 2020, 1, 1, 1, 1),
    ("Lebanon", 2021, 1, 1, 1, 1),
    ("Lebanon", 2022, 1, 1, 1, 1),
    ("Lebanon", 2023, 1, 1, 1, 1),
    ("Lebanon", 2024, 1, 0, 1, 1),

    # Pakistan — recurring IMF programs, 2018 + 2022 currency stress
    ("Pakistan", 2018, 0, 1, 0, 0),
    ("Pakistan", 2022, 0, 1, 1, 0),
    ("Pakistan", 2023, 0, 1, 1, 0),

    # Sri Lanka — 2022 sovereign default
    ("Sri Lanka", 2022, 0, 1, 1, 1),
    ("Sri Lanka", 2023, 0, 1, 1, 1),

    # Ghana — 2022 sovereign debt restructuring
    ("Ghana", 2022, 0, 1, 1, 1),
    ("Ghana", 2023, 0, 0, 1, 1),

    # Zambia — 2020 sovereign default
    ("Zambia", 2020, 0, 1, 0, 1),
    ("Zambia", 2021, 0, 0, 0, 1),
    ("Zambia", 2022, 0, 0, 0, 1),

    # Ecuador — 2020 sovereign default during pandemic
    ("Ecuador", 2020, 0, 0, 0, 1),

    # Argentina — 2018 currency crisis + 2020 sovereign restructuring
    ("Argentina", 2018, 0, 1, 0, 0),
    ("Argentina", 2019, 0, 1, 1, 0),
    ("Argentina", 2020, 0, 1, 1, 1),
    ("Argentina", 2022, 0, 1, 1, 0),
    ("Argentina", 2023, 0, 1, 1, 0),

    # Turkey — 2018 lira crisis, 2021 again
    ("Turkey", 2018, 0, 1, 0, 0),
    ("Turkey", 2021, 0, 1, 1, 0),
    ("Turkey", 2022, 0, 1, 1, 0),
    ("Turkey", 2023, 0, 1, 1, 0),

    # Egypt — 2016 devaluation, 2022-2023 currency stress
    ("Egypt", 2016, 0, 1, 0, 0),
    ("Egypt", 2022, 0, 1, 1, 0),
    ("Egypt", 2023, 0, 1, 1, 0),
], columns=["country", "year", "banking", "currency", "inflation", "sovereign_debt"])


def main() -> None:
    print("Loading R-R Excel...")
    rr = load_rr()

    # Pull each available country from R-R
    rr_parts = []
    for country in OUR_COUNTRIES:
        if country in rr["Country"].values:
            part = extract_country_from_rr(rr, country)
            part = part[(part["year"] >= YEAR_START) & (part["year"] <= YEAR_END)]
            rr_parts.append(part)

    rr_df = pd.concat(rr_parts, ignore_index=True)
    print(f"  Pulled {len(rr_df)} country-years from R-R")

    # Merge with manual additions (manual overrides R-R for the same country-year)
    combined = pd.concat([rr_df, MANUAL_CRISES], ignore_index=True)
    # If duplicates exist (same country, year), keep the manual one (it's last)
    combined = combined.drop_duplicates(subset=["country", "year"], keep="last")

    # Ensure every country-year in our window exists, even with all zeros
    all_rows = []
    for country in OUR_COUNTRIES:
        for year in range(YEAR_START, YEAR_END + 1):
            existing = combined[(combined["country"] == country) & (combined["year"] == year)]
            if not existing.empty:
                all_rows.append(existing.iloc[0].to_dict())
            else:
                all_rows.append({
                    "country": country, "year": year,
                    "banking": 0, "currency": 0, "inflation": 0, "sovereign_debt": 0,
                })
    final = pd.DataFrame(all_rows)

    # Add any_crisis column = OR of all four
    final["any_crisis"] = (
        (final["banking"] == 1) | (final["currency"] == 1) |
        (final["inflation"] == 1) | (final["sovereign_debt"] == 1)
    ).astype(int)

    final = final.sort_values(["country", "year"]).reset_index(drop=True)
    final.to_csv(OUT_CSV, index=False)

    print(f"\nWrote {len(final)} rows to {OUT_CSV}")
    print(f"\n=== Sample (countries with any crisis years) ===")
    crisis_summary = final.groupby("country")["any_crisis"].sum()
    print(crisis_summary.to_string())


if __name__ == "__main__":
    main()