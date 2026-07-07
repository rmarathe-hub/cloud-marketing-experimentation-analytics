# Cost Controls

Rules to keep AWS and infrastructure costs at or near $0 during development.

---

## AWS — Allowed Services

| Service | Purpose |
|---------|---------|
| **S3** | Raw, processed, marts, and export file storage |
| **IAM** | User/role for S3 access |
| **AWS Budgets** | Cost alerts |
| **AWS CLI** | Upload and sync scripts |

## AWS — Explicitly Avoided

| Service | Reason |
|---------|--------|
| Glue | Unnecessary pipeline complexity and cost |
| Lambda | Not needed for this analyst project |
| Redshift | Paid warehouse — using DuckDB locally instead |
| EMR | Overkill for portfolio-scale data |
| Kinesis | Streaming not required |
| Step Functions | Orchestration not required |
| EC2 | No compute instances needed |
| Athena | Optional later; not in initial scope |

---

## S3 Cost-Safety Rules

1. **Use a representative Avazu sample** if the full dataset exceeds free tier storage (5 GB).
2. Store only what is needed: `raw/`, `processed/`, `marts/`, `exports/`.
3. Delete duplicate or intermediate files after validation.
4. Do not store large raw files in Git — S3 is the cloud copy.
5. Set lifecycle rules to expire old exports if desired.

---

## AWS Budget Alerts

Create budget alerts at these thresholds:

| Threshold | Action |
|-----------|--------|
| **$1** | Early warning — review S3 storage and requests |
| **$5** | Investigate unexpected usage |
| **$10** | Hard stop — suspend uploads and audit bucket |

### Setup (manual, one-time)

```bash
# Via AWS Console: Billing → Budgets → Create budget
# Type: Cost budget
# Amount: $10/month
# Alert thresholds: 10%, 50%, 100% ($1, $5, $10)
```

---

## DuckDB — Local, No Cost

- Database file: `data/processed/marketing_analytics.duckdb`
- Runs entirely on local machine
- No server, no credits, no auto-suspend needed
- Parquet input files for fast loading

---

## Environment Safety

- Never commit `.env` — use `.env.example` as template
- Never commit AWS credentials, access keys, or PEM files
- Add `*.duckdb` to `.gitignore` (database stays local)
- Add `data/raw/*` and `data/processed/*` to `.gitignore`

---

## Session Checklist

After each work session:

- [ ] Verify no warehouse or compute services are running (N/A for DuckDB)
- [ ] Confirm S3 bucket has no unexpected large uploads
- [ ] Check AWS Billing dashboard if uploads were made
- [ ] Ensure `.env` is not staged in git
