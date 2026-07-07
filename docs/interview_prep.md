# Interview Prep — Talking Points

Structured answers for portfolio reviews, intern interviews, and recruiter screens.

---

## 30-second elevator pitch

> I built a marketing analytics project that combines mobile ad click data and an email A/B experiment. The pipeline runs from Python data cleaning through AWS S3 and DuckDB SQL marts to Tableau and Excel stakeholder deliverables. I measured segment CTR, quantified email lift with statistical significance, and produced scale/pause/retest recommendations with real numbers—500K impressions, 16.4% portfolio CTR, and significant email revenue lift.

---

## Project story (2 minutes)

1. **Business question:** Which ad segments drive engagement, does email treatment lift conversions, and what should marketing scale or pause?
2. **Data:** Avazu mobile clicks (500K rows, single day) + Hillstrom email experiment (64K recipients, 3 arms).
3. **Engineering:** Python profiling/cleaning → S3 zones → DuckDB raw/staging/mart tables → CSV exports.
4. **Analytics:** Campaign KPIs, segment CTR, hourly trends, A/B lift with p-values and CIs, holdout forecast with MAPE.
5. **Delivery:** 10 recommendations, executive summary, 12 dashboard screenshots (Tableau + Excel), 1,700+ pytest tests.

---

## Likely questions & answers

### Why DuckDB instead of Postgres or Snowflake?

Local, zero-cost analytics warehouse for portfolio work. SQL marts mirror cloud warehouse patterns (raw/staging/mart) without running a server. Easy pytest integration with in-process queries.

### How did you validate data quality?

25 checks in `validate_data.py`: row counts, CTR sanity, treatment group balance, mart population, forecast inputs. Lock documents freeze expected production metrics so docs/tests can't drift.

### Walk me through the A/B test.

Hillstrom has control, mens email, and womens email. I used visit as conversion, computed absolute/relative lift, p-values, and incremental revenue vs control. Mens: **+7.66 pp** lift, p ≈ 0. Womens: **+4.52 pp**, also significant. Both are scale recommendations.

### What was your top segment finding?

Device=1, app `07d7df22`, site `f028772b`, banner=1: **25.25% CTR** on **68,033** impressions (~21% of clicks). Clear scale candidate, with caveat that Avazu is a competition subsample.

### Why is MAPE so high on the forecast?

Avazu is a **single-day, hourly** sample. Holdout forecasting on one day is directional only—**314.4% MAPE**. I flagged it as a retest recommendation, not a production forecast.

### Tableau vs screenshots—why not host a live dashboard?

The portfolio artifact is **version-controlled PNG screenshots** built from mart CSV exports. A local `.twbx` may exist but is gitignored. Reviewers see consistent visuals on GitHub without needing Tableau Desktop.

### What would you do next with more time?

- Multi-day Avazu data for reliable hour-of-day and forecast models
- Spend/impression join for true ROAS-based pause rules
- Scheduled S3 → DuckDB refresh and CI smoke tests on pull requests

---

## Metrics to memorize

| Metric | Value |
|--------|-------|
| Impressions | 500,000 |
| Clicks | 82,037 |
| Portfolio CTR | 16.41% |
| Top segment CTR | 25.25% |
| Mens lift | +7.66 pp |
| Womens lift | +4.52 pp |
| Mens incremental $ | ~$16,403 |
| Womens incremental $ | ~$9,077 |
| Recommendations | 10 (6/3/1) |
| Validation checks | 25 passed |

---

## Red flags to avoid in interviews

- Don't claim MAPE forecast is production-ready.
- Don't say Avazu CTR is a live campaign benchmark (single-day subsample).
- Don't overstate AWS usage—S3 upload is implemented with cost controls; default tests skip real AWS.
