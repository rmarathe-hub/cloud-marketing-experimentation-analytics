# Data Quality Report

Generated: 2026-07-07T03:06:00.187903+00:00

## Summary

| Dataset | Rows | Key Metric |
|---------|------|------------|
| Avazu mobile ads | 500,000 | CTR: 16.4074% |
| Hillstrom email experiment | 64,000 | Visit rate: 14.6781% |

## Avazu — Mobile Ad Click Data

- **File:** `data/raw/avazu_train.csv`
- **Rows:** 500,000
- **Date range:** 2014-10-21 to 2014-10-21 (1 distinct days)
- **CTR:** 16.4074% (82,037 clicks / 500,000 impressions)

### Click distribution

| Outcome | Count |
|---------|-------|
| No click (0) | 417,963 |
| Click (1) | 82,037 |
| Invalid | 0 |

### Unique entity counts

| Entity | Unique values |
|--------|---------------|
| device_id | 41,413 |
| device_type | 4 |
| app_id | 1,641 |
| app_category | 20 |
| site_id | 1,704 |
| site_category | 21 |
| banner_pos | 6 |

### Missing values

No missing values detected.

## Hillstrom — Email A/B Experiment

- **File:** `data/raw/hillstrom_email.csv`
- **Rows:** 64,000
- **Overall visit rate:** 14.6781%
- **Overall conversion rate:** 0.9031%

### Treatment / control counts

| Segment | Recipients |
|---------|------------|
| Womens E-Mail | 21,387 |
| Mens E-Mail | 21,307 |
| No E-Mail | 21,306 |

### Segment performance (raw)

| Segment | Recipients | Visits | Visit rate | Conversions | Conversion rate | Revenue/customer |
|---------|------------|--------|------------|-------------|-----------------|------------------|
| Mens E-Mail | 21,307 | 3,894 | 18.2757% | 267 | 1.2531% | $1.42 |
| No E-Mail | 21,306 | 2,262 | 10.6167% | 122 | 0.5726% | $0.65 |
| Womens E-Mail | 21,387 | 3,238 | 15.1400% | 189 | 0.8837% | $1.08 |

### Revenue distribution

- Min: $0.00
- Max: $499.00
- Mean: $1.05
- Median: $0.00

### Missing values

No missing values detected.

## Initial quality notes

- Avazu `click` should be validated as binary (0/1) during cleaning.
- Avazu `hour` field will be parsed into `event_date` and `event_hour`.
- Hillstrom experiment groups should map to standardized treatment labels.
- Revenue/spend contains many zero values; analyze lift with and without buyers.
