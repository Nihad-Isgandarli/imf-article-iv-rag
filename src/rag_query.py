"""Query a single IMF Article IV report using RAG (Retrieval-Augmented Generation).

Given a question, a country, and a year, this module:
  1. Retrieves the most relevant text chunks from ChromaDB (filtered by
     country + year, using the metadata stored in build_vectordb.py),
  2. Sends those chunks to Google Gemini together with the question,
  3. Returns a structured result: a one-paragraph answer, a 0-10 concern
     score, and a short reasoning for that score.
"""

import os
import json
from pathlib import Path

import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

from embedder import load_embedding_model, embed_chunks

# --- Paths and constants (same convention as build_vectordb.py) ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "imf_article_iv"

GEMINI_MODEL_NAME = "gemini-3.1-flash-lite"

TOP_K = 5  # how many chunks to retrieve per query

# --- Load the Gemini API key from the .env file ---
load_dotenv(PROJECT_ROOT / ".env")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found. Check your .env file.")
genai.configure(api_key=api_key)

# --- Open ChromaDB and load the embedding model ONCE ---
# These are created when the module is first imported, so they are reused
# across every query instead of being reloaded each time (which would be slow).
_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
_collection = _client.get_collection(COLLECTION_NAME)
_embedding_model = load_embedding_model()

def retrieve_chunks(retrieval_query: str, country: str, year: int, top_k: int = TOP_K) -> list[str]:
    """Retrieve the most relevant chunks for a retrieval query from one country-year report.

    Args:
        retrieval_query: The keyword-rich query used to search ChromaDB.
        country: Country to filter by (e.g. "turkey").
        year: Year to filter by (e.g. 2018).
        top_k: How many chunks to return.

    Returns:
        A list of the top_k most relevant chunk texts.
    """
    # 1. Turn the retrieval query into a vector (same model used for the chunks)
    question_embedding = embed_chunks([retrieval_query], _embedding_model)

    # 2. Search ChromaDB, but ONLY within this country + year
    results = _collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=top_k,
        where={"$and": [{"country": country}, {"year": year}]},
    )

    # 3. Extract just the chunk texts from the result structure
    chunks = results["documents"][0]
    return chunks

def build_prompt(question: str, country: str, year: int, chunks: list[str]) -> str:
    """Build the prompt sent to Gemini, asking for a structured JSON answer.

    Args:
        question: The scoring question to answer.
        country: The country the report is about.
        year: The year of the report.
        chunks: The retrieved text chunks to ground the answer in.

    Returns:
        A single prompt string.
    """
    # Join the retrieved chunks into one block of context
    context = "\n\n---\n\n".join(chunks)

    prompt = f"""You are a financial economist analyzing an IMF Article IV \
consultation report for {country.title()} ({year}).

Answer the question using ONLY the excerpts provided below. Do not use outside \
knowledge. If the excerpts do not contain enough information, say so in your answer \
and assign a low concern score.

QUESTION:
{question}

SCORING RUBRIC (0-10):
- 0-2: Not raised, or explicitly reassuring / under control
- 3-4: Mild, routine concern; risks noted but described as manageable
- 5-6: Moderate concern; clear risks, monitoring or gradual action advised
- 7-8: High concern; prominent risks, strong language, significant vulnerabilities
- 9-10: Severe/acute concern; crisis-level language, imminent threat, urgent action demanded

REPORT EXCERPTS:
{context}

Respond with ONLY a valid JSON object, no other text, in exactly this format:
{{
  "answer": "<one paragraph answering the question based on the excerpts>",
  "concern_score": <integer from 0 to 10, following the rubric above>,
  "reasoning": "<one or two sentences explaining why you chose that score>"
}}"""

    return prompt

def query_country_year(question: str, country: str, year: int, retrieval_query: str = None) -> dict:
    """Run the full RAG pipeline for one question on one country-year report.

    Args:
        question: The scoring question Gemini answers.
        country: Country to query (e.g. "turkey").
        year: Year to query (e.g. 2018).
        retrieval_query: Keyword-rich query used to search ChromaDB. If not
            given, the scoring question itself is used for retrieval.

    Returns:
        A dict with keys: country, year, question, answer, concern_score,
        reasoning, n_chunks.
    """
    # If no separate retrieval query is given, fall back to the question
    if retrieval_query is None:
        retrieval_query = question

    # 1. RETRIEVAL: get the most relevant chunks for this report
    chunks = retrieve_chunks(retrieval_query, country, year)

    # 2. Build the prompt grounded in those chunks
    prompt = build_prompt(question, country, year, chunks)

    # 3. GENERATION: send the prompt to Gemini (low temperature = more consistent)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2},
    )

    # 4. Parse Gemini's JSON answer into a Python dict
    raw_text = response.text.strip()
    # Gemini sometimes wraps JSON in ```json ... ``` fences; remove them if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[len("json"):]
        raw_text = raw_text.strip()

    # Try to parse the JSON. If Gemini returned malformed output, don't crash:
    # record a placeholder score of -1 and keep the raw text for inspection.
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"      WARNING: could not parse JSON for {country} {year}. "
              f"Recording score -1.")
        parsed = {
            "answer": f"PARSE_ERROR. Raw response: {raw_text}",
            "concern_score": -1,
            "reasoning": "Response was not valid JSON.",
        }


    # 5. Assemble the final structured result
    return {
        "country": country,
        "year": year,
        "question": question,
        "answer": parsed["answer"],
        "concern_score": parsed["concern_score"],
        "reasoning": parsed["reasoning"],
        "n_chunks": len(chunks),
    }

def main() -> None:
    """Quick test: run one question on one country-year report."""
    test_question = (
        "To what extent does the report flag external vulnerabilities — "
        "capital outflows or sudden stops, exchange-rate/currency pressure, "
        "low or falling reserves, or current-account stress?"
    )
    test_retrieval = (
        "capital outflows, sudden stop, foreign reserves, current account "
        "deficit, balance of payments, exchange-rate pressure, external financing needs"
    )
    test_country = "turkey"
    test_year = 2016

    print(f"Question: {test_question}")
    print(f"Report:   {test_country.title()} {test_year}\n")

    result = query_country_year(test_question, test_country, test_year, test_retrieval)