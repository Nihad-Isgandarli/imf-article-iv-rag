# Score Validation

## What was checked

All 275 model responses (55 reports × 5 questions) were screened for **internal
consistency** between the assigned 0–10 concern score, the model's own stated
reasoning, and the scoring rubric in `docs/rag_questions.md`. The full answer and
reasoning behind every score are available for inspection in `raw_responses.json`.
This screening was done with AI assistance (Claude) and reviewed by the author.

## Result

| Verdict | Count |
|---------|------:|
| OK (retained) | 274 |
| Unsure (flagged for reconsideration) | 1 |
| Revise | 0 |

The calibration is consistent across every score band: 0–2 scores correspond to
reports described as sustainable / under control, 7–8 to strong-risk language, and
9–10 to crisis-level language. No score plainly contradicts its reasoning.

The single **Unsure** is Ecuador 2024, `q1_fiscal = 6`: the IMF explicitly
classifies the debt risk as "High", so a 7 may fit the rubric better; the 6 is kept
defensible only by the "baseline path" hedge in the reasoning.

## Findings

1. **Per-dimension scores localise the *type* of crisis.** External vulnerability
   (`q5`) is highest for the currency / balance-of-payments crises (Turkey,
   Argentina, Pakistan), while fiscal (`q1`) is highest for the sovereign-debt
   crises (Sri Lanka, Ghana, Zambia, Ecuador). The composite does not just rise
   ahead of crises — it rises in the correct category.

2. **Policy urgency (`q3`) is the weakest discriminator.** It assigns 7–8 even to
   control countries (Korea 2016 = 7, Malaysia 2023 = 8, Poland 2018 = 7) because it
   measures the *forcefulness of IMF language*, which fires on structural-reform
   advocacy regardless of crisis risk. This motivates the robustness check that
   down-weights `q3`/`q4` in favour of the "hard" indicators `q1`/`q2`/`q5`.

3. **The boundary cases are economically justified, not errors.** Controls scoring
   moderately on a hard dimension reflect real issues (Switzerland 2023 = the
   UBS–Credit Suisse merger; Malaysia = post-COVID debt build-up). Treatment
   countries scoring low on a hard dimension *before* their crisis are correct
   dimension-localisation, not missed signals (the currency crises show up in `q5`,
   not in fiscal or banking).

## Limitation

This pass verifies internal consistency (score vs reasoning vs rubric). It does
**not** verify that the model's reasoning faithfully reflects the underlying IMF
report text. For full rigour, a random sample of ~10–15 scored answers should be
checked manually against the source PDFs.
