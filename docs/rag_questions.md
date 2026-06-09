# The 5 RAG Questions — Finalised Specification

*Definition of the five questions used to score each IMF Article IV report on a 0–10 concern
scale, with retrieval queries and scoring rubric. Reusable as a section of the report.*

## Rationale

The five questions are not arbitrary: each maps to one of the standard categories used in
the **early-warning-system (EWS) literature** on financial crises (fiscal, financial-sector,
external, momentum, and policy stance). Together they give a structured, theory-grounded
basis for an aggregate "concern score" rather than an ad-hoc keyword search.

Each question plays two roles in the pipeline:
- **Retrieval query** — the text embedded and matched against report chunks in ChromaDB.
- **Scoring question** — the instruction the language model follows to rate concern 0–10 on
  the retrieved chunks.

The five score columns are labelled `q1` fiscal, `q2` banking, `q3` policy urgency,
`q4` deterioration, `q5` external.

---

## Q1 — Fiscal & sovereign-debt sustainability

- **Scoring question:** *To what extent does the report express concern about fiscal
  sustainability — rising public debt, large or widening fiscal deficits, or growing gross
  financing needs?*
- **Retrieval query:** public debt sustainability, debt-to-GDP ratio, fiscal deficit,
  primary balance, gross financing needs, debt dynamics, fiscal consolidation
- **Dimension:** Fiscal / sovereign solvency (e.g. Sri Lanka 2022, Ghana 2022, Zambia 2020,
  Ecuador 2020 — the sovereign-debt cases in our sample).

## Q2 — Banking & financial-sector vulnerabilities

- **Scoring question:** *To what extent does the report flag vulnerabilities in the banking
  or financial sector — rising non-performing loans, thin capital buffers, rapid credit
  growth, or funding/liquidity stress?*
- **Retrieval query:** non-performing loans, NPLs, bank capital adequacy, credit growth,
  leverage, liquidity, financial stability, deposit outflows
- **Dimension:** Financial-sector soundness — the project's core signal (banking crises,
  e.g. Lebanon 2019 in our sample).

## Q3 — Urgency of the policy stance

- **Scoring question:** *How urgent is the policy stance — does the report call for
  immediate, urgent, or front-loaded action, or warn that delay carries significant risks?*
- **Retrieval query:** urgent action, immediate measures, without delay, decisive,
  front-loaded, risks of inaction, pressing reforms
- **Dimension:** Policy stance / intensity — a *meta-signal*. It measures the tone and
  forcefulness of IMF advice rather than a single indicator, on the premise that the IMF
  intensifies its language when risk is elevated.

## Q4 — Deterioration relative to previous years

- **Scoring question:** *Does the report describe a deterioration relative to previous years
  in key macro-financial indicators (growth, reserves, fiscal or external balances, asset
  quality)?*
- **Retrieval query:** deteriorated, worsened, declined, weakened, slowdown, downward
  revision, compared with the previous year
- **Dimension:** Momentum / trend — crises are typically preceded by visible deterioration
  in the year(s) before they break out.

## Q5 — External vulnerabilities

- **Scoring question:** *To what extent does the report flag external vulnerabilities —
  capital outflows or sudden stops, exchange-rate/currency pressure, low or falling
  reserves, or current-account / balance-of-payments stress?*
- **Retrieval query:** capital outflows, sudden stop, foreign reserves, current account
  deficit, balance of payments, exchange-rate pressure, external financing needs
- **Dimension:** External / currency (e.g. Turkey 2018, Argentina 2018, Egypt 2016,
  Pakistan 2018 — the currency / balance-of-payments cases in our sample).

---

## Scoring rubric (applies to every question)

| Score | Meaning |
|------:|---------|
| 0–2 | Not raised, or explicitly reassuring / under control |
| 3–4 | Mild, routine concern; risks noted but described as manageable |
| 5–6 | Moderate concern; clear risks, monitoring or gradual action advised |
| 7–8 | High concern; prominent risks, strong language, significant vulnerabilities |
| 9–10 | Severe/acute concern; crisis-level language, imminent threat, urgent action demanded |

## Aggregation

The five per-question scores (each 0–10) are **summed** into an overall
**Concern Score on a 0–50 scale** per country-report (equivalently, divide by
five for a 0–10 average). Equal weighting is the default; the report should note
a robustness check with alternative weights (e.g. emphasising Q1/Q2/Q5 — fiscal,
banking, external, the "hard" indicators — over Q3/Q4).

## Implementation note

For each report and each question: embed the retrieval query → fetch top-k chunks from
ChromaDB → pass chunks + scoring question + rubric to the language model → require a
structured reply, e.g. `{"score": 0-10, "justification": "...", "evidence_quote": "..."}`.
Store all five scores plus the aggregate. The crisis-vs-control comparison and the ROC curve
are computed on these scores using the crisis/control labels in `data/countries.csv`.
