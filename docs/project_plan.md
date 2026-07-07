# Project Plan

Build plan for the Cloud Marketing Experimentation & Forecasting Analytics portfolio project.

**Status:** All phases complete (Days 1–21).

---

## Phase 1 — Data Foundation + AWS S3 + DuckDB ✅

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 1 | Repo scaffold + business framing | README, docs, project structure |
| 2 | Dataset acquisition + raw profiling | Raw CSVs, profile summary, data quality report |
| 3 | Cleaning pipeline | Cleaned Parquet files, cleaning summary |
| 4 | AWS S3 setup + upload | S3 zones, upload script, cost controls |
| 5 | DuckDB warehouse setup | Schema SQL, database file |
| 6 | Load data + validation | Loaded tables, validation summary |
| 7 | Week 1 tests + docs lock | pytest suite, locked data docs |

## Phase 2 — Marketing Analytics ✅

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 8 | Campaign KPI marts | CTR, impressions, clicks, segment performance |
| 9 | Funnel + segmentation analysis | Hourly engagement, segment marts |
| 10 | A/B testing (Hillstrom) | Lift, p-value, CI, methodology doc |
| 11 | Forecasting / time series | MAE, RMSE, MAPE, forecast marts |
| 12 | Recommendations + executive summary | Scale / pause / retest decisions |
| 13 | Export marts for Tableau + Excel | CSV exports, S3 export upload |
| 14 | Week 2 tests + README update | Analytics tests, updated status |

## Phase 3 — Tableau, Excel, Polish ✅

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 15–17 | Tableau dashboard (6 pages) | Screenshot PNGs in `tableau/screenshots/` |
| 18 | Excel stakeholder workbook | Screenshot PNGs in `excel/screenshots/` |
| 19 | Final README case study | 5 key findings with real numbers |
| 20 | Final tests + cleanup | Full pytest pass, portfolio completion doc |
| 21 | Resume bullets + interview prep | Resume, LinkedIn, talking points docs |

---

## Deliverables Checklist

- [x] AWS S3 bucket with raw / processed / marts / exports zones
- [x] DuckDB analytical database
- [x] Python cleaning and profiling scripts
- [x] SQL marts
- [x] A/B test analysis with statistical significance
- [x] CTR forecasting with accuracy metrics
- [x] Tableau dashboard with screenshots
- [x] Excel executive workbook with screenshots
- [x] Recommendations and executive summary
- [x] README case study with key findings
- [x] pytest test suite
- [x] Portfolio completion + interview prep docs

---

## Portfolio Positioning

| Project | Focus | Stack |
|---------|-------|-------|
| Retail Retention & Revenue Intelligence | Cohorts, RFM, retention | Postgres, Power BI |
| **This project** | Campaign analytics, A/B tests, forecasting | DuckDB, Tableau, Excel, AWS S3 |

Non-overlapping tools and business domains for a strong data analyst intern portfolio.

See [portfolio_completion.md](portfolio_completion.md) for final validation commands.
