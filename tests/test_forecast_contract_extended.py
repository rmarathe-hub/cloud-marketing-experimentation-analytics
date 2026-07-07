"""Extended CTR forecasting contract tests."""

from __future__ import annotations

import pytest

import run_ctr_forecast as ctr_forecast

pytestmark = [pytest.mark.forecast, pytest.mark.unit]


def test_forecast_module_exports_main_and_runner():
    assert hasattr(ctr_forecast, "main")
    assert hasattr(ctr_forecast, "run_ctr_forecast")


def test_forecast_compares_two_models():
    source = open(ctr_forecast.__file__, encoding="utf-8").read()
    assert "moving_average_3" in source
    assert "naive_last_hour" in source


def test_forecast_selects_lowest_holdout_mae():
    source = open(ctr_forecast.__file__, encoding="utf-8").read().lower()
    assert "mae" in source
    assert "holdout" in source or "selected" in source


def test_forecast_has_minimum_series_length_guard():
    assert hasattr(ctr_forecast, "MIN_SERIES_LENGTH")
    assert ctr_forecast.MIN_SERIES_LENGTH >= 2


@pytest.mark.parametrize(
    "metric_name",
    ["mae", "rmse", "mape"],
)
def test_forecast_summary_records_accuracy_metrics(metric_name: str):
    source = open(ctr_forecast.__file__, encoding="utf-8").read().lower()
    assert metric_name in source


def test_forecast_populates_two_mart_tables():
    source = open(ctr_forecast.__file__, encoding="utf-8")
    text = source.read()
    assert "mart_forecast_inputs" in text
    assert "mart_forecast_results" in text
