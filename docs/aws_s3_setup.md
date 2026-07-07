# AWS S3 Setup

This document describes the Day 4 cloud storage setup for the marketing analytics project.

---

## Overview

AWS S3 is used as **private cloud storage** for raw and processed datasets. This project uses **S3 only** — no Glue, Lambda, EC2, Redshift, Athena, or other paid compute services.

```
Local files  →  scripts/upload_to_s3.py  →  Private S3 bucket
```

---

## S3 bucket setup

Create a **private** bucket in `us-east-1`:

| Setting | Value |
|---------|-------|
| **Bucket name** | Globally unique, e.g. `rmarathe-marketing-analytics-2026` |
| **Region** | `us-east-1` |
| **Block Public Access** | All settings enabled |
| **Default encryption** | SSE-S3 enabled |
| **Versioning** | Optional (disabled is fine for portfolio use) |

Do **not** enable public access. This bucket should never be readable from the public internet.

---

## Expected S3 layout

After running the upload script:

```
s3://$S3_BUCKET/
  raw/
    avazu_train.csv
    hillstrom_email.csv
  processed/
    avazu_clean.parquet
    hillstrom_clean.parquet
  marts/       # reserved for later analytics exports
  exports/     # reserved for Tableau/Excel exports
```

The upload script creates `raw/` and `processed/` prefixes automatically. `marts/` and `exports/` are reserved for later project phases.

---

## IAM least-privilege policy

Create a dedicated IAM user (e.g. `marketing-analytics-s3`) with **programmatic access only**.

Attach a bucket-scoped policy like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

This grants access to **one bucket only** — not account-wide S3 or other AWS services.

---

## Budget alerts

Create an AWS Budget to catch unexpected charges early:

| Threshold | Action |
|-----------|--------|
| $1 (10%) | Early warning |
| $5 (50%) | Investigate usage |
| $10 (100%) | Stop and audit bucket |

Configure alerts in: **AWS Console → Billing → Budgets**

---

## AWS CLI configuration

Configure a named profile for this project:

```bash
aws configure --profile marketing-analytics
```

Enter:

- Access Key ID (from IAM user)
- Secret Access Key (from IAM user)
- Default region: `us-east-1`
- Default output format: `json`

Verify access:

```bash
aws s3 ls --profile marketing-analytics
aws s3 ls s3://YOUR-BUCKET-NAME/ --profile marketing-analytics
```

---

## Local `.env` configuration

Copy the example file:

```bash
cp .env.example .env
```

Set these values in `.env`:

```bash
AWS_PROFILE=marketing-analytics
AWS_REGION=us-east-1
S3_BUCKET=your-actual-bucket-name
S3_RAW_PREFIX=raw
S3_PROCESSED_PREFIX=processed
S3_MARTS_PREFIX=marts
S3_EXPORT_PREFIX=exports
```

### Security rules

- **Never commit `.env`** — it is listed in `.gitignore`
- **Never put AWS access keys in `.env`** when using `aws configure` / named profiles
- **Never commit credentials** to GitHub, docs, notebooks, or tests
- **Never enable public bucket access**

---

## Upload workflow

From the project root with your virtual environment active:

```bash
source .venv/bin/activate
python scripts/upload_to_s3.py
```

The script will:

1. Load config from `.env`
2. Verify required local files exist
3. Check bucket access
4. Upload raw and processed files
5. Write `data/processed/s3_upload_summary.json`

Verify uploads:

```bash
aws s3 ls s3://$S3_BUCKET/ --recursive --profile marketing-analytics
```

---

## Cost controls

| Rule | Why |
|------|-----|
| Use a 500k Avazu sample | Keeps storage under free tier |
| Upload only required files | Avoids duplicate storage costs |
| Keep bucket private | Prevents accidental egress/abuse |
| Use budget alerts | Early warning before meaningful charges |
| Delete bucket when project is done | Avoids ongoing storage fees |

Expected cost for this portfolio project:

- **Year 1:** ~$0 on AWS free tier
- **After year 1:** typically pennies to low dollars per month for small data

See also: [cost_controls.md](cost_controls.md)

---

## Services explicitly not used

Do **not** enable these for this analyst project:

| Service | Reason |
|---------|--------|
| Glue | Unnecessary pipeline complexity |
| Lambda | No serverless compute needed |
| EC2 | No servers needed |
| Redshift | Using local DuckDB instead |
| Athena | Not required for Day 4 |
| Kinesis | No streaming data |
| Step Functions | No orchestration needed |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `Missing required environment variables` | Create `.env` from `.env.example` |
| `S3_BUCKET is not configured` | Set real bucket name in `.env` |
| `AWS credentials not found` | Run `aws configure --profile marketing-analytics` |
| `AWS profile not found` | Check `AWS_PROFILE` in `.env` matches configured profile |
| `Access denied for S3 bucket` | Verify IAM policy and bucket name |
| `Missing required local files` | Run download + cleaning scripts first |

---

## Next step

After S3 upload is working, proceed to **Day 5: DuckDB warehouse setup**.

Do not load data into DuckDB until that step begins.
