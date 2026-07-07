# DuckDB Warehouse Setup

Local analytical database for the Cloud Marketing Experimentation & Forecasting Analytics project.

DuckDB runs **entirely on your machine** — no cloud warehouse, no extra AWS cost. See [cost_controls.md](cost_controls.md).

---

## Purpose

Day 5 creates the **empty warehouse schema** only:

- **Raw** tables mirror source CSV shape
- **Staging** tables mirror cleaned Parquet shape
- **Mart** tables are ready for Week 2 analytics outputs

**Day 6** loads data into raw/staging tables and runs validation. Do not load data until that step.

---

## Database file

| Setting | Default |
|---------|---------|
| Path | `data/processed/marketing_analytics.duckdb` |
| Env var | `DUCKDB_PATH` in `.env` |

The `.duckdb` file is **gitignored**. Never commit database files.

---

## Schema layout

| Layer | Tables |
|-------|--------|
| Raw | `raw_avazu_ads`, `raw_hillstrom_email` |
| Staging | `stg_ad_events`, `stg_email_experiment` |
| Mart | `mart_campaign_kpis`, `mart_ctr_trends`, `mart_device_app_performance`, `mart_ab_test_results`, `mart_forecast_inputs`, `mart_forecast_results` |

SQL definitions live in `sql/`:

```
sql/01_raw_tables.sql
sql/02_staging_tables.sql
sql/03_mart_tables.sql
```

Column details: [data_dictionary.md](data_dictionary.md)

---

## Configuration

`.env` field:

```bash
DUCKDB_PATH=data/processed/marketing_analytics.duckdb
```

No AWS credentials are required for DuckDB setup.

---

## Create the database

From the project root with your virtual environment active:

```bash
python scripts/create_duckdb_database.py
```

Expected output:

- Local `.duckdb` file created (or updated safely on rerun)
- 10 empty tables across raw / staging / mart layers
- `data/processed/duckdb_setup_summary.json` written locally (gitignored)

The script is **safe to rerun** — it uses `CREATE TABLE IF NOT EXISTS`.

---

## Verify tables (optional)

```bash
python -c "
import duckdb
con = duckdb.connect('data/processed/marketing_analytics.duckdb', read_only=True)
print(con.execute('SHOW TABLES').fetchdf())
con.close()
"
```

After Day 5, all tables should exist with **0 rows**.

---

## Day 6: Load data + validation

Load local files into raw and staging tables:

```bash
python scripts/load_to_duckdb.py
python scripts/validate_data.py
```

| Source | Target table |
|--------|----------------|
| `data/raw/avazu_train.csv` | `raw_avazu_ads` |
| `data/raw/hillstrom_email.csv` | `raw_hillstrom_email` |
| `data/processed/avazu_clean.parquet` | `stg_ad_events` |
| `data/processed/hillstrom_clean.parquet` | `stg_email_experiment` |

Both scripts are **safe to rerun** — load clears raw/staging tables before reloading.

Validation checks:

- Row counts vs `raw_profile_summary.json` and `cleaning_summary.json`
- Avazu CTR and Hillstrom visit rate vs cleaning summaries
- Hillstrom treatment group counts
- `mart_campaign_kpis` populated with daily CTR after Day 8
- Remaining mart tables empty until their analytics scripts run

Outputs (gitignored):

- `data/processed/duckdb_load_summary.json`
- `data/processed/data_validation_summary.json`

---

## Day 8: Campaign KPI mart

Build daily campaign KPIs from staging ad events:

```bash
python scripts/run_campaign_kpis.py
python scripts/validate_data.py
```

| Source | Target table |
|--------|----------------|
| `stg_ad_events` | `mart_campaign_kpis` |

The script aggregates by `event_date`:

- **Impressions** = `COUNT(*)`
- **Clicks** = `SUM(click)`
- **CTR** = clicks / impressions

Safe to rerun — clears and reloads `mart_campaign_kpis` only.

Output (gitignored):

- `data/processed/campaign_kpi_summary.json`

---

## What Day 5 does NOT do

- Does **not** load CSV or Parquet data (Day 6)
- Does **not** build analytics marts with SQL (Week 2)
- Does **not** upload to S3
- Does **not** require Glue, Lambda, EC2, Redshift, or Athena

---

## Day 9: Funnel + segmentation marts

Build hourly CTR trends and device/app/site segment performance:

```bash
python scripts/run_funnel_segment_analysis.py
python scripts/validate_data.py
```

| Source | Target tables |
|--------|----------------|
| `stg_ad_events` | `mart_ctr_trends`, `mart_device_app_performance` |

`mart_ctr_trends` aggregates by `event_date` + `event_hour`.

`mart_device_app_performance` aggregates by `device_type`, `app_category`,
`site_category`, and `banner_pos`, including click share.

Safe to rerun — clears and reloads both marts only.

Output (gitignored):

- `data/processed/funnel_segment_summary.json`

---

## Next step

Day 9 funnel and segmentation marts are complete. Proceed to **Day 10: A/B test analysis**.
