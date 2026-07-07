-- Raw layer: source-shaped tables loaded from CSV in Day 6.

CREATE TABLE IF NOT EXISTS raw_avazu_ads (
    id VARCHAR,
    click INTEGER,
    hour BIGINT,
    c1 BIGINT,
    banner_pos INTEGER,
    site_id VARCHAR,
    site_domain VARCHAR,
    site_category VARCHAR,
    app_id VARCHAR,
    app_domain VARCHAR,
    app_category VARCHAR,
    device_id VARCHAR,
    device_ip VARCHAR,
    device_model VARCHAR,
    device_type INTEGER,
    device_conn_type INTEGER,
    c14 DOUBLE,
    c15 DOUBLE,
    c16 DOUBLE,
    c17 DOUBLE,
    c18 DOUBLE,
    c19 DOUBLE,
    c20 DOUBLE,
    c21 DOUBLE
);

CREATE TABLE IF NOT EXISTS raw_hillstrom_email (
    recency INTEGER,
    history_segment VARCHAR,
    history DOUBLE,
    mens INTEGER,
    womens INTEGER,
    zip_code VARCHAR,
    newbie INTEGER,
    channel VARCHAR,
    segment VARCHAR,
    visit INTEGER,
    conversion INTEGER,
    spend DOUBLE
);
