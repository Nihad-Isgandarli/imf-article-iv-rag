# IMF Article IV RAG

A RAG pipeline that reads IMF Article IV reports, scores how worried each report sounds about different financial risks, and checks whether those scores line up with crises that actually happened.

**Course:** Programming in Finance II — USI Lugano, Spring 2026
**Topic:** 2.5 LLMs and RAG
**Team:** Nihad Isgandarli, Alessandro Marcante, Vittoria Zupi

---

## The question

Do IMF Article IV reports contain early warning signals of financial crises?

Most crisis-prediction research uses numbers (debt ratios, reserves, deficits). The actual text of IMF reports is rarely analyzed at scale. We use RAG + an LLM to score the text and see if the warning was already there in the IMF's own words.

Anchor example: IMF Greece 2009 report -> Greek debt crisis in 2010.

---

## How it works

```
IMF PDFs -> extract text -> split into chunks -> embed -> store in ChromaDB
                                                              |
                                          ask 5 "concern" questions per report
                                                              |
                                          Gemini gives a 0-10 score for each
                                                              |
                                          compare scores with real crisis dates
                                                              |
                                          t-tests, ROC curve, country charts
```

---

## Data

- 55 IMF Article IV PDFs, 14 countries, 2014-2025
- **Crisis countries (10):** Turkey, Argentina, Sri Lanka, Lebanon, Zambia, Pakistan, Ghana, Egypt, Ecuador
- **Control countries (5):** Switzerland, Canada, Korea, Poland, Malaysia
- Crisis dates: Reinhart-Rogoff data (up to 2016) + manual additions for recent crises. The source of each row is marked in `data/crises.csv`.

We kept the sample small (14 countries) on purpose so we could look at each country closely and stay inside Gemini's free-tier limits.

---

## The 5 concern questions

Each report is scored 0-10 on:

1. External vulnerability (capital flows, reserves, current account)
2. Banking sector (NPLs, capital, liquidity)
3. Fiscal sustainability (deficit, debt)
4. Real sector (growth, inflation, unemployment)
5. Structural / political (institutions, reforms)

---

## Folders

```
data/
  countries.csv          # country list + treatment/control
  article_iv_links.csv   # report URLs
  crises.csv             # crisis dates with source column
  raw/                   # the PDFs (not in git)
src/
  extractor.py           # PDF -> text
  chunker.py             # text -> chunks
  embedder.py            # chunks -> embeddings
  explore_links.py       # find report links on imf.org
  download_pdfs.py       # download the PDFs
  build_crises_csv.py    # build crises.csv
  build_vectordb.py      # load chunks into ChromaDB
  rag_query.py           # ask Gemini a question about a report
  run_scoring.py         # score all reports
  statistical_analysis.py# t-tests, ROC, charts
  dashboard.py           # Streamlit dashboard
```

---

## Tools we used

Python, Playwright (to download from imf.org, which blocks normal requests), pypdf, sentence-transformers (local embeddings), ChromaDB (vector store), Google Gemini (free tier), scipy + scikit-learn (stats), matplotlib + Streamlit (charts).

---

## Setup

```bash
git clone https://github.com/Nihad-Isgandarli/imf-article-iv-rag.git
cd imf-article-iv-rag

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# add your free Gemini key from https://aistudio.google.com/app/apikey
echo "GOOGLE_API_KEY=your_key_here" > .env
```

---

## How to run

```bash
python src/download_pdfs.py        # get the PDFs
python src/fetch_lebanon_2018.py   # special case (no PDF, uses IMF statements)
python src/build_crises_csv.py     # build crisis data
python src/build_vectordb.py       # load into ChromaDB
python src/run_scoring.py          # score the reports
python src/statistical_analysis.py # stats + charts
streamlit run src/dashboard.py     # dashboard
```

---

## Who did what

- **Nihad** - data collection (scraping), Reinhart-Rogoff crisis data, statistical analysis
- **Alessandro** - ChromaDB, RAG querying, scoring system, Streamlit dashboard
- **Vittoria** - the 5 questions, score validation, LaTeX report

---

## A note on AI

We used AI (Claude and Cursor) to help write the code. Each of us understands and can explain our own part. See `AGENTS.md` for how we organized AI contributions.

---

## License

MIT
