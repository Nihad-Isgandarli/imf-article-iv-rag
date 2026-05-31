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

# --- The 5 standardized questions, one per risk dimension ---
# These map to the 5 score columns. To change a question, edit it here only.
QUESTIONS = {
    "q1_external": (
        "Does the report express concern about the country's external "
        "vulnerabilities, such as capital flows, FX reserves, or the current account?"
    ),
    "q2_banking": (
        "Does the report express concern about the stability of the banking "
        "sector, such as non-performing loans, capital adequacy, or liquidity?"
    ),
    "q3_fiscal": (
        "Does the report express concern about fiscal sustainability, such as "
        "the budget deficit, the public debt trajectory, or debt rollover risk?"
    ),
    "q4_real": (
        "Does the report express concern about the real economy, such as "
        "economic growth, inflation, or unemployment?"
    ),
    "q5_structural": (
        "Does the report express concern about structural or political risks, "
        "such as the quality of institutions, reform momentum, or policy credibility?"
    ),
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

    for question_key, question_text in QUESTIONS.items():
        result = query_country_year(question_text, country, year)
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
