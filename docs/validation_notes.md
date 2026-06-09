# Score Validation

## What was checked

All 275 model responses (55 reports × 5 questions) were screened for **internal
consistency** between the assigned 0–10 concern score, the model's own stated
reasoning, and the rubric in `docs/rag_questions.md`. The full answer and reasoning behind every score are in
`raw_responses.json`.

## Result

| Verdict | Count |
|---------|------:|
| OK (retained) | 274 |
| Unsure (flagged for reconsideration) | 1 |
| Revise | 0 |

The calibration is consistent across every score band: 0–2 entries are described as
sustainable / under control, 7–8 use strong-risk language, and 9–10 use crisis-level
language. No score plainly contradicts its reasoning. The single **Unsure** is
Ecuador 2024, `q1_fiscal = 6`: the IMF explicitly classifies the debt risk as
"High", so a 7 may fit the rubric better; the 6 is kept defensible only by the
"baseline path" hedge in the reasoning.

## Calibration observations

1. **Per-dimension scores localise the *type* of crisis.** External vulnerability
   (`q5`) is highest for the currency / balance-of-payments crises (Turkey,
   Argentina, Pakistan), while fiscal sustainability (`q1`) is highest for the
   sovereign-debt crises (Sri Lanka, Ghana, Zambia, Ecuador).
2. **Banking (`q2`) separates weakly in this sample**, and the scores reflect why:
   only Lebanon is primarily a banking crisis, so banking concern does not rise for
   the (mostly currency / fiscal) treatment group, while controls carry moderate,
   genuine banking concern (e.g. Switzerland 2023 = the UBS–Credit Suisse episode,
   Canada = housing imbalances). The low separation is a feature of the sample, not
   a scoring error.
3. **Policy urgency (`q3`) scores high even for control countries**, because it
   tracks the *forcefulness of IMF language*, which is elevated whenever the Fund
   urges structural reform, crisis or not. Again a calibration caveat, not an error.
4. **Moderate control scores on "hard" dimensions are economically real, not
   noise** (Switzerland banking, Malaysia fiscal).

The *statistical* discriminating power of each dimension is reported in the academic
report. Across the pre-crisis t-test and the next-year ROC, **external vulnerability
(`q5`) is the dominant signal** (t = 6.0, p < 0.001; AUC 0.87), with deterioration
(`q4`) the secondary warning (p = 0.034). Fiscal, banking and policy urgency are not
significant on the pre-crisis test, though banking ranks second on the next-year
AUC (0.78), a small-events artefact (a mean shift and a rank-based classifier need
not agree when there are only ~5–6 crisis events).

## Limitation and manual check

The internal-consistency pass above (score vs reasoning vs rubric) covers all 275
responses. On its own it does **not** verify that the model's reasoning faithfully
reflects the underlying IMF report text, so a random sample of 15 scored answers was
additionally checked manually against the source PDFs; in this sample the assigned
scores were consistent with the report text. This manual check is a spot check, not
a full independent re-scoring of all 275 answers.
