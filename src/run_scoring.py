"""Run the full concern-scoring pipeline across all IMF Article IV reports.

For every country-year report in the ChromaDB store, this script asks all
5 standardized questions via the RAG pipeline (rag_query.py) and collects
the concern scores. It produces two output files:
  - data/results/concern_scores.csv  : one row per country-year, with the
    5 question scores plus a total.
  - data/results/raw_responses.json  : the full LLM output for every query,
    kept for transparency and later validation.

Gemini's free tier is rate-limited (10 requests/minute), so the script
pauses briefly between calls to stay under the limit.
"""

import json
import time
import csv
from pathlib import Path

from rag_query import query_country_year, _collection

# --- The 5 standardized questions (Vittoria's finalised spec) ---
# Each has a scoring question (what Gemini answers) and a retrieval query
# (keyword-rich text used to search ChromaDB). Order and labels follow
# docs/rag_questions.md: q1 fiscal, q2 banking, q3 policy, q4 deterioration, q5 external.
QUESTIONS = {
    "q1_fiscal": {
        "scoring": (
            "To what extent does the report express concern about fiscal "
            "sustainability — rising public debt, large or widening fiscal "
            "deficits, or growing gross financing needs?"
        ),
        "retrieval": (
            "public debt sustainability, debt-to-GDP ratio, fiscal deficit, "
            "primary balance, gross financing needs, debt dynamics, fiscal consolidation"
        ),
    },
    "q2_banking": {
        "scoring": (
            "To what extent does the report flag vulnerabilities in the banking "
            "or financial sector — rising non-performing loans, thin capital "
            "buffers, rapid credit growth, or funding/liquidity stress?"
        ),
        "retrieval": (
            "non-performing loans, NPLs, bank capital adequacy, credit growth, "
            "leverage, liquidity, financial stability, deposit outflows"
        ),
    },
    "q3_policy": {
        "scoring": (
            "How urgent is the policy stance — does the report call for immediate, "
            "urgent, or front-loaded action, or warn that delay carries significant risks?"
        ),
        "retrieval": (
            "urgent action, immediate measures, without delay, decisive, "
            "front-loaded, risks of inaction, pressing reforms"
        ),
    },
    "q4_deterioration": {
        "scoring": (
            "Does the report describe a deterioration relative to previous years "
            "in key macro-financial indicators (growth, reserves, fiscal or "
            "external balances, asset quality)?"
        ),
        "retrieval": (
            "deteriorated, worsened, declined, weakened, slowdown, downward "
            "revision, compared with the previous year"
        ),
    },
    "q5_external": {
        "scoring": (
            "To what extent does the report flag external vulnerabilities — "
            "capital outflows or sudden stops, exchange-rate/currency pressure, "
            "low or falling reserves, or current-account / balance-of-payments stress?"
        ),
        "retrieval": (
            "capital outflows, sudden stop, foreign reserves, current account "
            "deficit, balance of payments, exchange-rate pressure, external financing needs"
        ),
    },
}

# --- Paths (same PROJECT_ROOT convention as the other scripts) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
SCORES_CSV = RESULTS_DIR / "concern_scores.csv"
RAW_JSON = RESULTS_DIR / "raw_responses.json"

# --- Rate limiting ---
# Gemini free tier allows ~10 requests/minute. We wait a few seconds between
# calls to stay safely under that limit and avoid rate-limit errors.
SECONDS_BETWEEN_CALLS = 7

def get_all_country_years() -> list[tuple[str, int]]:
    """Find every unique (country, year) pair stored in ChromaDB.

    Reads the metadata of all chunks and returns the distinct country-year
    combinations, sorted, so the scoring runs in a predictable order.

    Returns:
        A sorted list of (country, year) tuples.
    """
    # Pull all stored metadata (no embeddings/documents needed here)
    all_metadata = _collection.get(include=["metadatas"])["metadatas"]

    # Collect unique (country, year) pairs using a set
    pairs = set()
    for meta in all_metadata:
        pairs.add((meta["country"], meta["year"]))

    return sorted(pairs)


def score_one_report(country: str, year: int) -> dict:
    """Ask all 5 questions for one country-year report and collect the scores.

    Args:
        country: The country to score.
        year: The year to score.

    Returns:
        A dict with the 5 scores, the total, and the full responses.
    """
    scores = {}
    full_responses = {}

    for question_key, question_spec in QUESTIONS.items():
        result = query_country_year(
            question_spec["scoring"],
            country,
            year,
            retrieval_query=question_spec["retrieval"],
        )
        scores[question_key] = result["concern_score"]
        full_responses[question_key] = result
        print(f"    {question_key}: {result['concern_score']}/10")
        time.sleep(SECONDS_BETWEEN_CALLS)

    return {"scores": scores, "full_responses": full_responses}

def main() -> None:
    """Score every report on all 5 questions and save the two output files."""

    # 1. Make sure the output folder exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Find all reports to score
    country_years = get_all_country_years()


    print(f"Found {len(country_years)} reports to score.")
    print(f"Total queries: {len(country_years) * len(QUESTIONS)} "
          f"(~{len(country_years) * len(QUESTIONS) * SECONDS_BETWEEN_CALLS // 60} min)\n")

    csv_rows = []
    all_raw = {}

    # 3. Score each report, one by one
    for i, (country, year) in enumerate(country_years, start=1):
        print(f"[{i}/{len(country_years)}] {country} {year}")
        result = score_one_report(country, year)

        scores = result["scores"]
        total = sum(scores.values())

        # Build one CSV row: country, year, the 5 scores, and the total
        row = {"country": country, "year": year}
        row.update(scores)
        row["total_score"] = total
        csv_rows.append(row)

        # Keep the full responses under a "country_year" key
        all_raw[f"{country}_{year}"] = result["full_responses"]

    # 4. Write the CSV file
    fieldnames = ["country", "year"] + list(QUESTIONS.keys()) + ["total_score"]
    with open(SCORES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # 5. Write the raw responses JSON file
    with open(RAW_JSON, "w") as f:
        json.dump(all_raw, f, indent=2)

    print(f"\n--- Done ---")
    print(f"Scored {len(csv_rows)} reports")
    print(f"Scores saved to: {SCORES_CSV}")
    print(f"Raw responses saved to: {RAW_JSON}")


if __name__ == "__main__":
    main()
