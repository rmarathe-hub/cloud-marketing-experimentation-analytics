-- Mart layer: analytical outputs populated in Week 2 analytics scripts.

CREATE TABLE IF NOT EXISTS mart_campaign_kpis (
    event_date DATE,
    impressions BIGINT,
    clicks BIGINT,
    ctr DOUBLE,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS mart_ctr_trends (
    event_date DATE,
    event_hour INTEGER,
    impressions BIGINT,
    clicks BIGINT,
    ctr DOUBLE,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS mart_device_app_performance (
    device_type INTEGER,
    app_category VARCHAR,
    site_category VARCHAR,
    banner_pos INTEGER,
    impressions BIGINT,
    clicks BIGINT,
    ctr DOUBLE,
    click_share DOUBLE,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS mart_ab_test_results (
    treatment_group VARCHAR,
    treatment_label VARCHAR,
    recipients BIGINT,
    conversions BIGINT,
    conversion_rate DOUBLE,
    total_revenue DOUBLE,
    revenue_per_customer DOUBLE,
    control_conversion_rate DOUBLE,
    absolute_lift DOUBLE,
    relative_lift_pct DOUBLE,
    incremental_revenue DOUBLE,
    p_value DOUBLE,
    ci_lower DOUBLE,
    ci_upper DOUBLE,
    statistically_significant BOOLEAN,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS mart_forecast_inputs (
    event_date DATE,
    event_hour INTEGER,
    impressions BIGINT,
    clicks BIGINT,
    ctr DOUBLE,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS mart_forecast_results (
    event_date DATE,
    event_hour INTEGER,
    actual_clicks BIGINT,
    forecast_clicks DOUBLE,
    actual_ctr DOUBLE,
    forecast_ctr DOUBLE,
    model_name VARCHAR,
    mae DOUBLE,
    rmse DOUBLE,
    mape DOUBLE,
    created_at TIMESTAMP DEFAULT current_timestamp
);
