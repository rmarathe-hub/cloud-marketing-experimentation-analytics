# Project Plan

Build plan for the Cloud Marketing Experimentation & Forecasting Analytics portfolio project.

---

## Phase 1 — Data Foundation + AWS S3 + DuckDB

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 1 | Repo scaffold + business framing | README, docs, project structure |
| 2 | Dataset acquisition + raw profiling | Raw CSVs, profile summary, data quality report |
| 3 | Cleaning pipeline | Cleaned Parquet files, cleaning summary |
| 4 | AWS S3 setup + upload | S3 zones, upload script, cost controls |
| 5 | DuckDB warehouse setup | Schema SQL, database file |
| 6 | Load data + validation | Loaded tables, validation summary |
| 7 | Week 1 tests + docs lock | pytest suite, locked data docs |

## Phase 2 — Marketing Analytics

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 8 | Campaign KPI marts | CTR, impressions, clicks, segment performance |
| 9 | Funnel + segmentation analysis | Hourly engagement, segment marts |
| 10 | A/B testing (Hillstrom) | Lift, p-value, CI, methodology doc |
| 11 | Forecasting / time series | MAE, RMSE, MAPE, forecast marts |
| 12 | Recommendations + executive summary | Scale / pause / retest decisions |
| 13 | Export marts for Tableau + Excel | CSV exports, S3 export upload |
| 14 | Week 2 tests + README update | Analytics tests, updated status |

## Phase 3 — Tableau, Excel, Polish

| Day | Focus | Key Outputs |
|-----|-------|-------------|
| 15–17 | Tableau dashboard (6 pages) | `.twbx` workbook + screenshots |
| 18 | Excel stakeholder workbook | Pivot tables, A/B calculator, recommendation matrix |
| 19 | Final README case study | 5 key findings with real numbers |
| 20 | Final tests + cleanup | Full pytest pass, git hygiene check |
| 21 | Resume bullets + interview prep | Resume, LinkedIn, talking points docs |

---

## Priority Order (if time is tight)

1. A/B testing analysis
2. Tableau dashboard
3. Excel workbook
4. Forecasting
5. S3 cloud layer
6. Tests / docs polish

---

## Deliverables Checklist

- [ ] AWS S3 bucket with raw / processed / marts / exports zones
- [ ] DuckDB analytical database
- [ ] Python cleaning and profiling scripts
- [ ] SQL marts
- [ ] A/B test analysis with statistical significance
- [ ] CTR forecasting with accuracy metrics
- [ ] Tableau dashboard with screenshots
- [ ] Excel executive workbook with screenshots
- [ ] Recommendations and executive summary
- [ ] README case study with key findings
- [ ] pytest test suite

---

## Portfolio Positioning

| Project | Focus | Stack |
|---------|-------|-------|
| Retail Retention & Revenue Intelligence | Cohorts, RFM, retention | Postgres, Power BI |
| **This project** | Campaign analytics, A/B tests, forecasting | DuckDB, Tableau, Excel, AWS S3 |

Non-overlapping tools and business domains for a strong data analyst intern portfolio.
