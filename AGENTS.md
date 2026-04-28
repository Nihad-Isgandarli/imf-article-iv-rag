# AGENTS.md — Instructions for AI Agents

This document provides guidance for AI agents (Claude Code, Cursor, GitHub Copilot, Codex, etc.) contributing to this project. Human contributors should also read this file.

## Project Context

**Course:** Programming in Finance II — USI Lugano, Spring 2026
**Authors:** Nihad Isgandarli, Alessandro Marcante
**Topic:** RAG-based early warning system using IMF Article IV consultation reports.

We test whether the language and discourse in IMF Article IV reports contain detectable early warning signals of financial crises. We systematically query ~25-30 country-year reports with standardized "concern" questions using Retrieval Augmented Generation (RAG), score the responses, and compare scores to historical crisis dates from the Reinhart-Rogoff database.
## Repository Structure

- `AGENTS.md` — this file, instructions for AI agents
- `README.md` — human-facing project overview
- `requirements.txt` — Python dependencies
- `.env.example` — template for API keys (never commit real `.env`)
- `.gitignore`
- `data/raw/` — downloaded PDFs (gitignored, too large)
- `data/processed/` — extracted text chunks
- `data/countries.csv` — list of analyzed countries with metadata
- `data/crises.csv` — historical crisis dates (Reinhart-Rogoff)
- `src/config.py` — constants, paths, model names
- `src/scraper.py` — download IMF Article IV PDFs
- `src/extractor.py` — extract text from PDFs (pypdf)
- `src/chunker.py` — split text into chunks
- `src/embedder.py` — generate embeddings (sentence-transformers)
- `src/vector_store.py` — ChromaDB ingestion and querying
- `src/llm_query.py` — Gemini API querying with RAG context
- `src/scorer.py` — convert LLM responses to 0-10 concern scores
- `src/analysis.py` — compare concern scores to crisis dates
- `dashboard/app.py` — Streamlit dashboard
- `docs/academic_report.tex` — 5-8 page LaTeX report (iCorsi submission)
- `tests/` — unit tests for all `src/` modules

## Tech Stack

- **Language:** Python 3.13
- **LLM:** Google Gemini API, free tier, model `gemini-1.5-flash`
- **Embeddings:** `sentence-transformers`, model `all-MiniLM-L6-v2` (local, no API needed)
- **Vector DB:** ChromaDB (local, persisted to `./chroma_db/`)
- **Visualization:** Streamlit, matplotlib, pandas
- **PDF parsing:** `pypdf`
- **Web scraping:** `requests`, `beautifulsoup4`

## How We Satisfy the Project Requirements

The professor requires combining at least 3 elements, with at least one advanced. We use:

- **LLM (advanced)** — Google Gemini API for question answering
- **Non-trivial database** — ChromaDB vector store with thousands of embedded chunks
- **Advanced data visualization** — interactive Streamlit dashboard with country and year filtering
- **Required: at least 1 PR by an AI agent** — see "AI Agent Contributions" section below
## Development Workflow

### Branching Strategy

Never commit directly to `main`. Always work on a feature branch.

Branch naming conventions:

- `feature/<name>` — new functionality
- `fix/<name>` — bug fixes
- `docs/<name>` — documentation only
- `refactor/<name>` — code restructure, no behavior change
- `agent/<name>` — branches created by AI agents

### Commit Messages

Use conventional commits format:

- `feat: add PDF scraper for IMF.org`
- `fix: handle missing pages in pypdf extraction`
- `docs: expand README installation section`
- `refactor: split chunker into smaller functions`
- `test: add unit tests for scorer`
- `chore: update dependencies`

When an AI agent makes the commit, prepend `[AI-assisted]`:

- `[AI-assisted] feat: add retry logic to Gemini API client`

### Pull Requests

Every PR must include:

1. **What changed** — bullet list of modifications
2. **Why** — rationale, link to issue if applicable
3. **How tested** — what was run to verify it works
4. **AI involvement** — which AI tools (if any) contributed and how

A PR cannot be merged until at least one human contributor approves it.
## Coding Standards

- Follow PEP 8 for Python style.
- All public functions must have docstrings (Google style).
- Type hints required for function signatures.
- No hardcoded API keys, absolute file paths, or magic numbers — use `src/config.py` and environment variables (`.env`).
- Prefer pure functions: take inputs, return outputs, minimal side effects.
- Each module in `src/` has a single, clear responsibility.
- Maximum function length: ~50 lines. If longer, split it.

## Testing Requirements

- All new functions in `src/` must have at least one unit test in `tests/`.
- Run tests before opening a PR: `pytest tests/`
- For functions that call external APIs (Gemini, IMF.org), mock the responses in tests — never hit live APIs from tests.
## Instructions for AI Agents

### Before Making Any Changes

1. Read this AGENTS.md fully.
2. Check existing modules — do not create duplicate functionality. If something similar already exists, extend or refactor rather than duplicate.
3. Read the relevant module's docstring to understand its purpose before modifying it.

### When Adding New Code

1. Place new code in the correct module (see Repository Structure above).
2. If your change requires a new dependency, add it to `requirements.txt` with a comment explaining why.
3. If your change touches more than one module, split it into multiple atomic commits.
4. Write tests alongside the code, not after.

### When Debugging

1. Reproduce the bug locally first.
2. Add a regression test that fails without the fix and passes with it.
3. Document the root cause in the commit message body.

### When Refactoring

1. Do not refactor and add features in the same commit. Refactor first, then add the feature in a separate commit.
2. Run tests before and after — refactors must not change behavior.

### Constraints

- Never commit secrets (`.env`, API keys, tokens). The `.gitignore` blocks `.env` — do not override it.
- Never modify `chroma_db/` directly — it is a generated artifact. Regenerate it with the ingestion pipeline.
- Never reduce test coverage.
- Do not modify files in `docs/` (LaTeX) without flagging it in the PR — the academic report is hand-curated.
## AI Agent Contributions — Required for the Course

The course rubric requires at least one Pull Request made by an AI agent. We track this here:

| PR # | Agent | Task | Status |
|------|-------|------|--------|
| TBD  | TBD   | TBD  | TBD    |

When an AI agent (Claude Code, Cursor agent mode, GitHub Copilot Workspace, etc.) opens a PR:

- Branch must use `agent/<name>` prefix
- Commit messages must start with `[AI-assisted]`
- A human contributor must review and approve before merge

## Contact

For questions about the project: open a GitHub Issue.
For coordination between contributors: see project board on GitHub.
