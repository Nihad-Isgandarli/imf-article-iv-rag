"""Build a clean crises.csv from Reinhart-Rogoff + manual additions.

Output: data/crises.csv with one row per country-year for our countries.
Columns: country, year, banking, currency, inflation, sovereign_debt,
         any_crisis, source

R-R covers 1800-2016 for 10 of our countries; Lebanon and Pakistan are
added manually. Post-2016 crisis events are added manually for all
countries (R-R data ends in 2016). The 'source' column makes the
attribution explicit for academic honesty.
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CRISES_XLSX = DATA_DIR / "crises_raw.xlsx"
COUNTRIES_CSV = DATA_DIR / "countries.csv"
OUT_CSV = DATA_DIR / "crises.csv"


OUR_COUNTRIES = [
    "Turkey", "Argentina", "Sri Lanka", "Lebanon", "Zambia", "Pakistan",
    "Ghana", "Egypt", "Ecuador", "Switzerland", "Canada", "Korea",
    "Poland", "Malaysia",
]

YEAR_START = 2010
YEAR_END = 2024

SOURCE_RR = "Reinhart-Rogoff 2016 (HBS Global Crises Data)"
SOURCE_MANUAL = "Manual: post-2016 (IMF press releases + news)"
SOURCE_NONE = "No R-R coverage (Lebanon/Pakistan absent from R-R)"


def load_rr() -> pd.DataFrame:
    df = pd.read_excel(CRISES_XLSX, sheet_name="Sheet1", header=0)
    df = df.iloc[1:].reset_index(drop=True)
    return df


def extract_country_from_rr(df: pd.DataFrame, country: str) -> pd.DataFrame:
    sub = df[df["Country"] == country].copy()
    sub["Year"] = pd.to_numeric(sub["Year"], errors="coerce")
    sub = sub.dropna(subset=["Year"])
    sub["Year"] = sub["Year"].astype(int)

    ext_debt_col = [c for c in df.columns if "SOVEREIGN EXTERNAL DEBT 1" in str(c)][0]

    out = pd.DataFrame({
        "country": country,
        "year": sub["Year"],
        "banking": pd.to_numeric(sub["Banking Crisis "], errors="coerce").fillna(0).astype(int),
        "currency": pd.to_numeric(sub["Currency Crises"], errors="coerce").fillna(0).astype(int),
        "inflation": pd.to_numeric(sub["Inflation Crises"], errors="coerce").fillna(0).astype(int),
        "sovereign_debt": pd.to_numeric(sub[ext_debt_col], errors="coerce").fillna(0).astype(int),
        "source": SOURCE_RR,
    })
    return out


# Manual additions for countries / years not covered by R-R (post-2016 or missing)
MANUAL_CRISES = pd.DataFrame([
    # Lebanon — banking + sovereign crisis from 2019
    ("Lebanon", 2019, 1, 1, 0, 0),
    ("Lebanon", 2020, 1, 1, 1, 1),
    ("Lebanon", 2021, 1, 1, 1, 1),
    ("Lebanon", 2022, 1, 1, 1, 1),
    ("Lebanon", 2023, 1, 1, 1, 1),
    ("Lebanon", 2024, 1, 0, 1, 1),

    # Pakistan
    ("Pakistan", 2018, 0, 1, 0, 0),
    ("Pakistan", 2022, 0, 1, 1, 0),
    ("Pakistan", 2023, 0, 1, 1, 0),

    # Sri Lanka
    ("Sri Lanka", 2022, 0, 1, 1, 1),
    ("Sri Lanka", 2023, 0, 1, 1, 1),

    # Ghana
    ("Ghana", 2022, 0, 1, 1, 1),
    ("Ghana", 2023, 0, 0, 1, 1),

    # Zambia
    ("Zambia", 2020, 0, 1, 0, 1),
    ("Zambia", 2021, 0, 0, 0, 1),
    ("Zambia", 2022, 0, 0, 0, 1),

    # Ecuador
    ("Ecuador", 2020, 0, 0, 0, 1),

    # Argentina
    ("Argentina", 2018, 0, 1, 0, 0),
    ("Argentina", 2019, 0, 1, 1, 0),
    ("Argentina", 2020, 0, 1, 1, 1),
    ("Argentina", 2022, 0, 1, 1, 0),
    ("Argentina", 2023, 0, 1, 1, 0),

    # Turkey
    ("Turkey", 2018, 0, 1, 0, 0),
    ("Turkey", 2021, 0, 1, 1, 0),
    ("Turkey", 2022, 0, 1, 1, 0),
    ("Turkey", 2023, 0, 1, 1, 0),

    # Egypt
    ("Egypt", 2016, 0, 1, 0, 0),
    ("Egypt", 2022, 0, 1, 1, 0),
    ("Egypt", 2023, 0, 1, 1, 0),
], columns=["country", "year", "banking", "currency", "inflation", "sovereign_debt"])

MANUAL_CRISES["source"] = SOURCE_MANUAL


def main() -> None:
    print("Loading R-R Excel...")
    rr = load_rr()

    rr_parts = []
    for country in OUR_COUNTRIES:
        if country in rr["Country"].values:
            part = extract_country_from_rr(rr, country)
            part = part[(part["year"] >= YEAR_START) & (part["year"] <= YEAR_END)]
            rr_parts.append(part)

    rr_df = pd.concat(rr_parts, ignore_index=True)
    print(f"  Pulled {len(rr_df)} country-years from R-R")

    combined = pd.concat([rr_df, MANUAL_CRISES], ignore_index=True)
    combined = combined.drop_duplicates(subset=["country", "year"], keep="last")

    all_rows = []
    for country in OUR_COUNTRIES:
        for year in range(YEAR_START, YEAR_END + 1):
            existing = combined[(combined["country"] == country) & (combined["year"] == year)]
            if not existing.empty:
                all_rows.append(existing.iloc[0].to_dict())
            else:
                # No record at all → either R-R has no coverage for this country
                # (Lebanon, Pakistan) or it's a post-2016 zero we haven't manually added
                is_uncovered = country in {"Lebanon", "Pakistan"} and year <= 2016
                source = SOURCE_NONE if is_uncovered else SOURCE_MANUAL
                all_rows.append({
                    "country": country, "year": year,
                    "banking": 0, "currency": 0, "inflation": 0, "sovereign_debt": 0,
                    "source": source,
                })
    final = pd.DataFrame(all_rows)

    final["any_crisis"] = (
        (final["banking"] == 1) | (final["currency"] == 1) |
        (final["inflation"] == 1) | (final["sovereign_debt"] == 1)
    ).astype(int)

    # Reorder columns
    final = final[["country", "year", "banking", "currency", "inflation",
                   "sovereign_debt", "any_crisis", "source"]]

    final = final.sort_values(["country", "year"]).reset_index(drop=True)
    final.to_csv(OUT_CSV, index=False)

    print(f"\nWrote {len(final)} rows to {OUT_CSV}")
    print(f"\n=== Source breakdown ===")
    print(final["source"].value_counts().to_string())


if __name__ == "__main__":
    main()