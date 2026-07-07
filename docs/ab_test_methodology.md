# A/B Test Methodology (Hillstrom Email Experiment)

Statistical approach for comparing email treatments against the holdout control group.

---

## Experiment design

| Group | `treatment_group` | Description |
|-------|-------------------|-------------|
| Control | `control` | No email sent |
| Mens treatment | `mens_email` | Male-targeted email |
| Womens treatment | `womens_email` | Female-targeted email |

Analysis uses cleaned staging data in `stg_email_experiment`.

---

## Primary outcome

| Field | Definition |
|-------|------------|
| `converted` | Visit indicator (`converted = visit` in cleaning pipeline) |
| `conversion_rate` | `SUM(converted) / COUNT(*)` per group |
| `revenue` | Spend per recipient (`revenue = spend` in cleaning pipeline) |

Visit rate and conversion rate in profiling docs refer to different raw fields.
The A/B mart uses **`converted`** as the primary binary outcome because that is the
field used for lift and significance testing in this project.

---

## Lift metrics

For each treatment vs control:

| Metric | Formula |
|--------|---------|
| Absolute lift | `treatment_rate - control_rate` |
| Relative lift % | `(treatment_rate - control_rate) / control_rate * 100` |
| Incremental revenue | `(treatment_revenue_per_customer - control_revenue_per_customer) * treatment_recipients` |

Control rows store `0` lift and `NULL` p-value.

---

## Significance testing

| Setting | Value |
|---------|-------|
| Test | Two-proportion z-test (`statsmodels.stats.proportion.proportions_ztest`) |
| Alpha | 0.05 |
| Confidence interval | 95% normal approximation on conversion-rate difference |

A treatment is marked `statistically_significant = true` when `p_value < 0.05`.

---

## Outputs

| Artifact | Location |
|----------|----------|
| Mart table | `mart_ab_test_results` |
| Run summary | `data/processed/ab_test_summary.json` |
| Builder script | `scripts/run_ab_test_analysis.py` |

---

## Interpretation guardrails

- Real experiment data only; no synthetic augmentation.
- Check both statistical significance **and** practical lift magnitude before scaling.
- Inconclusive results (`p >= 0.05`) should map to **retest**, not scale.

See [metric_definitions.md](metric_definitions.md) for metric formulas used in Tableau and Excel.
