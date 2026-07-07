"""generate_recommendations.py and recommendations doc contract tests."""

from __future__ import annotations

import json

import duckdb
import pandas as pd
import pytest

import create_duckdb_database as db_setup
import generate_recommendations as recommendations
import run_ab_test_analysis as ab_test
import run_campaign_kpis as campaign_kpis
import run_ctr_forecast as ctr_forecast
import run_funnel_segment_analysis as funnel_segment
import load_to_duckdb as loader
from clean_avazu_ads import clean_avazu_ads
from clean_hillstrom_email import clean_hillstrom_email
from helpers import (
    DOCS_DIR,
    run_implemented_week2_analytics,
    tiny_avazu_dataframe,
    tiny_hillstrom_dataframe,
)
from paths import SQL_DIR

pytestmark = [pytest.mark.docs, pytest.mark.unit]


def _build_full_tiny_bundle(tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    docs = tmp_path / "docs"
    raw_dir.mkdir(parents=True)
    processed.mkdir(parents=True)
    docs.mkdir(parents=True)

    avazu_raw = raw_dir / "avazu_train.csv"
    hillstrom_raw = raw_dir / "hillstrom_email.csv"
    tiny_avazu_dataframe().to_csv(avazu_raw, index=False)
    tiny_hillstrom_dataframe().to_csv(hillstrom_raw, index=False)

    avazu_clean, _ = clean_avazu_ads(pd.read_csv(avazu_raw))
    hillstrom_clean, _ = clean_hillstrom_email(pd.read_csv(hillstrom_raw))
    avazu_parquet = processed / "avazu_clean.parquet"
    hillstrom_parquet = processed / "hillstrom_clean.parquet"
    avazu_clean.to_parquet(avazu_parquet, index=False)
    hillstrom_clean.to_parquet(hillstrom_parquet, index=False)

    config = db_setup.DatabaseConfig(database_path=processed / "marketing_analytics.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)
    loader.load_data(
        config=config,
        targets=loader.get_load_targets(
            avazu_raw=avazu_raw,
            hillstrom_raw=hillstrom_raw,
            avazu_clean=avazu_parquet,
            hillstrom_clean=hillstrom_parquet,
        ),
        summary_path=processed / "duckdb_load_summary.json",
    )
    run_implemented_week2_analytics(config, processed)
    return {"config": config, "processed": processed, "docs": docs}


def test_generate_recommendations_module_exports_main():
    assert hasattr(recommendations, "main")
    assert hasattr(recommendations, "generate_recommendations")


def test_build_recommendations_includes_scale_pause_retest():
    payload = {
        "overall_ctr": 0.10,
        "impressions": 1000,
        "clicks": 100,
        "hourly_rows": [
            {"event_hour": 8, "impressions": 400, "clicks": 60, "ctr": 0.15},
            {"event_hour": 9, "impressions": 600, "clicks": 40, "ctr": 0.067},
        ],
        "top_segments": [
            {
                "device_type": 1,
                "app_category": "app_a",
                "site_category": "site_a",
                "banner_pos": 0,
                "impressions": 5000,
                "clicks": 1000,
                "ctr": 0.20,
                "click_share": 0.5,
            }
        ],
        "bottom_segments": [
            {
                "device_type": 1,
                "app_category": "app_b",
                "site_category": "site_b",
                "banner_pos": 1,
                "impressions": 5000,
                "clicks": 50,
                "ctr": 0.01,
                "click_share": 0.05,
            }
        ],
        "ab_results": [
            {
                "treatment_group": "control",
                "treatment_label": "Control",
                "recipients": 100,
                "conversions": 10,
                "conversion_rate": 0.10,
                "absolute_lift": 0.0,
                "relative_lift_pct": 0.0,
                "incremental_revenue": 0.0,
                "p_value": None,
                "statistically_significant": False,
            },
            {
                "treatment_group": "mens_email",
                "treatment_label": "Mens E-Mail",
                "recipients": 100,
                "conversions": 20,
                "conversion_rate": 0.20,
                "absolute_lift": 0.10,
                "relative_lift_pct": 100.0,
                "incremental_revenue": 500.0,
                "p_value": 0.01,
                "statistically_significant": True,
            },
        ],
        "forecast": {"model_name": "moving_average_3", "mae": 10.0, "rmse": 12.0, "mape": 150.0},
    }
    recs = recommendations.build_recommendations(payload)
    actions = {item.action for item in recs}
    assert "Scale" in actions
    assert "Pause" in actions
    assert "Retest" in actions


def test_generate_recommendations_writes_docs(tmp_path):
    bundle = _build_full_tiny_bundle(tmp_path)
    rec_path = bundle["docs"] / "recommendations.md"
    exec_path = bundle["docs"] / "executive_summary.md"
    summary_path = bundle["processed"] / "recommendations_summary.json"

    result = recommendations.generate_recommendations(
        config=bundle["config"],
        recommendations_path=rec_path,
        executive_path=exec_path,
        summary_path=summary_path,
    )

    assert result["success"] is True
    assert rec_path.exists()
    assert exec_path.exists()
    rec_text = rec_path.read_text(encoding="utf-8")
    exec_text = exec_path.read_text(encoding="utf-8")
    assert "Scale" in rec_text
    assert "Pause" in rec_text
    assert "Retest" in rec_text
    assert "Executive Summary" in exec_text
    payload = json.loads(summary_path.read_text())
    assert payload["recommendation_count"] >= 1


def test_generate_recommendations_fails_without_marts(tmp_path):
    processed = tmp_path / "processed"
    processed.mkdir()
    config = db_setup.DatabaseConfig(database_path=processed / "empty.duckdb")
    db_setup.create_database(config=config, sql_dir=SQL_DIR)

    with pytest.raises(RuntimeError, match="not fully populated"):
        recommendations.generate_recommendations(
            config=config,
            recommendations_path=tmp_path / "recommendations.md",
            executive_path=tmp_path / "executive_summary.md",
            summary_path=tmp_path / "summary.json",
        )


def test_recommendations_docs_exist_in_repo():
    assert (DOCS_DIR / "recommendations.md").is_file()
    assert (DOCS_DIR / "executive_summary.md").is_file()


def test_executive_summary_doc_references_recommendations_matrix():
    exec_doc = DOCS_DIR / "executive_summary.md"
    rec_doc = DOCS_DIR / "recommendations.md"
    if exec_doc.exists() and rec_doc.exists():
        assert "recommendations.md" in exec_doc.read_text(encoding="utf-8")
        assert "Scale" in rec_doc.read_text(encoding="utf-8")
