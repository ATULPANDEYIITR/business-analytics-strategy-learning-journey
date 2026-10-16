DROP SCHEMA IF EXISTS exploratory_analysis CASCADE;
CREATE SCHEMA exploratory_analysis;

SET search_path TO exploratory_analysis;

CREATE TABLE observations (
    observation_id BIGSERIAL PRIMARY KEY,
    observed_at DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(14, 4) NOT NULL,
    region TEXT NOT NULL,
    category TEXT NOT NULL,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (metric_value IS FINITE),
    CHECK (length(trim(metric_name)) > 0),
    CHECK (length(trim(region)) > 0),
    CHECK (length(trim(category)) > 0),
    CHECK (length(trim(source_system)) > 0)
);

CREATE INDEX idx_observations_metric_date
    ON observations (metric_name, observed_at);

CREATE INDEX idx_observations_region_category
    ON observations (region, category);

CREATE INDEX idx_observations_date_value
    ON observations (observed_at, metric_value);

INSERT INTO observations
    (observed_at, metric_name, metric_value, region, category, source_system)
VALUES
    ('2026-09-01', 'daily_sales', 101, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-02', 'daily_sales', 104, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-03', 'daily_sales', 106, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-04', 'daily_sales', 109, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-05', 'daily_sales', 112, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-06', 'daily_sales', 114, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-07', 'daily_sales', 116, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-08', 'daily_sales', 118, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-09', 'daily_sales', 119, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-10', 'daily_sales', 121, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-11', 'daily_sales', 123, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-12', 'daily_sales', 125, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-13', 'daily_sales', 127, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-14', 'daily_sales', 128, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-15', 'daily_sales', 130, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-16', 'daily_sales', 132, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-17', 'daily_sales', 134, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-18', 'daily_sales', 136, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-19', 'daily_sales', 138, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-20', 'daily_sales', 140, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-21', 'daily_sales', 142, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-22', 'daily_sales', 145, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-23', 'daily_sales', 147, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-24', 'daily_sales', 149, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-25', 'daily_sales', 151, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-26', 'daily_sales', 154, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-27', 'daily_sales', 157, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-28', 'daily_sales', 159, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-29', 'daily_sales', 162, 'North', 'Enterprise', 'sales_platform'),
    ('2026-09-30', 'daily_sales', 220, 'North', 'Enterprise', 'sales_platform'),
    ('2026-10-01', 'daily_sales', 165, 'South', 'SMB', 'sales_platform'),
    ('2026-10-02', 'daily_sales', 168, 'South', 'SMB', 'sales_platform'),
    ('2026-10-03', 'daily_sales', 170, 'South', 'SMB', 'sales_platform'),
    ('2026-10-04', 'daily_sales', 173, 'South', 'SMB', 'sales_platform'),
    ('2026-10-05', 'daily_sales', 176, 'South', 'SMB', 'sales_platform'),
    ('2026-10-06', 'daily_sales', 178, 'South', 'SMB', 'sales_platform'),
    ('2026-10-07', 'daily_sales', 181, 'South', 'SMB', 'sales_platform'),
    ('2026-10-08', 'daily_sales', 184, 'South', 'SMB', 'sales_platform'),
    ('2026-10-09', 'daily_sales', 186, 'South', 'SMB', 'sales_platform'),
    ('2026-10-10', 'daily_sales', 189, 'South', 'SMB', 'sales_platform'),
    ('2026-10-11', 'daily_sales', 191, 'South', 'SMB', 'sales_platform'),
    ('2026-10-12', 'daily_sales', 194, 'South', 'SMB', 'sales_platform'),
    ('2026-10-13', 'daily_sales', 197, 'South', 'SMB', 'sales_platform'),
    ('2026-10-14', 'daily_sales', 199, 'South', 'SMB', 'sales_platform'),
    ('2026-10-15', 'daily_sales', 202, 'South', 'SMB', 'sales_platform'),
    ('2026-10-16', 'daily_sales', 205, 'South', 'SMB', 'sales_platform'),
    ('2026-10-17', 'daily_sales', 207, 'South', 'SMB', 'sales_platform'),
    ('2026-10-18', 'daily_sales', 210, 'South', 'SMB', 'sales_platform'),
    ('2026-10-19', 'daily_sales', 212, 'South', 'SMB', 'sales_platform'),
    ('2026-10-20', 'daily_sales', 215, 'South', 'SMB', 'sales_platform'),
    ('2026-10-21', 'daily_sales', 217, 'South', 'SMB', 'sales_platform'),
    ('2026-10-22', 'daily_sales', 219, 'South', 'SMB', 'sales_platform'),
    ('2026-10-23', 'daily_sales', 222, 'South', 'SMB', 'sales_platform'),
    ('2026-10-24', 'daily_sales', 225, 'South', 'SMB', 'sales_platform'),
    ('2026-10-25', 'daily_sales', 228, 'South', 'SMB', 'sales_platform'),
    ('2026-10-26', 'daily_sales', 230, 'South', 'SMB', 'sales_platform'),
    ('2026-10-27', 'daily_sales', 233, 'South', 'SMB', 'sales_platform'),
    ('2026-10-28', 'daily_sales', 235, 'South', 'SMB', 'sales_platform'),
    ('2026-10-29', 'daily_sales', 238, 'South', 'SMB', 'sales_platform'),
    ('2026-10-30', 'daily_sales', 150, 'South', 'SMB', 'sales_platform');

CREATE OR REPLACE VIEW descriptive_statistics AS
SELECT
    metric_name,
    COUNT(*) AS observation_count,
    AVG(metric_value) AS mean_value,
    percentile_cont(0.50)
        WITHIN GROUP (ORDER BY metric_value) AS median_value,
    MIN(metric_value) AS minimum_value,
    MAX(metric_value) AS maximum_value,
    percentile_cont(0.25)
        WITHIN GROUP (ORDER BY metric_value) AS q1,
    percentile_cont(0.75)
        WITHIN GROUP (ORDER BY metric_value) AS q3,
    STDDEV_SAMP(metric_value) AS sample_standard_deviation
FROM observations
GROUP BY metric_name;

CREATE OR REPLACE VIEW daily_statistics AS
SELECT
    observed_at,
    metric_name,
    COUNT(*) AS observation_count,
    AVG(metric_value) AS daily_mean,
    MIN(metric_value) AS daily_minimum,
    MAX(metric_value) AS daily_maximum,
    STDDEV_SAMP(metric_value) AS daily_stddev
FROM observations
GROUP BY observed_at, metric_name
ORDER BY observed_at;

CREATE OR REPLACE VIEW regional_patterns AS
SELECT
    region,
    category,
    COUNT(*) AS observations,
    AVG(metric_value) AS mean_value,
    MIN(metric_value) AS minimum_value,
    MAX(metric_value) AS maximum_value,
    STDDEV_SAMP(metric_value) AS standard_deviation
FROM observations
GROUP BY region, category;

CREATE OR REPLACE VIEW iqr_anomalies AS
WITH distribution AS (
    SELECT
        metric_name,
        percentile_cont(0.25)
            WITHIN GROUP (ORDER BY metric_value) AS q1,
        percentile_cont(0.75)
            WITHIN GROUP (ORDER BY metric_value) AS q3
    FROM observations
    GROUP BY metric_name
),
limits AS (
    SELECT
        metric_name,
        q1,
        q3,
        q1 - 1.5 * (q3 - q1) AS lower_bound,
        q3 + 1.5 * (q3 - q1) AS upper_bound
    FROM distribution
)
SELECT
    o.observation_id,
    o.observed_at,
    o.metric_value,
    o.region,
    o.category,
    l.q1,
    l.q3,
    l.lower_bound,
    l.upper_bound
FROM observations o
JOIN limits l
    ON l.metric_name = o.metric_name
WHERE o.metric_value < l.lower_bound
   OR o.metric_value > l.upper_bound;

WITH daily AS (
    SELECT
        observed_at,
        AVG(metric_value) AS daily_mean
    FROM observations
    GROUP BY observed_at
),
trend AS (
    SELECT
        regr_slope(
            daily_mean,
            EXTRACT(EPOCH FROM observed_at::timestamp)
        ) AS slope_per_second,
        regr_intercept(
            daily_mean,
            EXTRACT(EPOCH FROM observed_at::timestamp)
        ) AS intercept
    FROM daily
)
SELECT
    slope_per_second,
    slope_per_second * 86400 AS estimated_daily_change,
    intercept
FROM trend;

WITH ordered AS (
    SELECT
        observed_at,
        metric_value,
        LAG(metric_value) OVER (
            ORDER BY observed_at
        ) AS previous_value
    FROM observations
),
changes AS (
    SELECT
        observed_at,
        metric_value,
        previous_value,
        metric_value - previous_value AS absolute_change,
        CASE
            WHEN previous_value = 0 THEN NULL
            ELSE
                (metric_value - previous_value)
                / previous_value * 100
        END AS percentage_change
    FROM ordered
)
SELECT *
FROM changes
WHERE previous_value IS NOT NULL
ORDER BY ABS(percentage_change) DESC
LIMIT 10;

WITH daily AS (
    SELECT
        observed_at,
        AVG(metric_value) AS daily_mean
    FROM observations
    GROUP BY observed_at
),
moving AS (
    SELECT
        observed_at,
        daily_mean,
        AVG(daily_mean) OVER (
            ORDER BY observed_at
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS seven_day_moving_average
    FROM daily
)
SELECT *
FROM moving
ORDER BY observed_at;

WITH ranked AS (
    SELECT
        region,
        category,
        AVG(metric_value) AS mean_value,
        RANK() OVER (
            PARTITION BY category
            ORDER BY AVG(metric_value) DESC
        ) AS category_rank
    FROM observations
    GROUP BY region, category
)
SELECT *
FROM ranked
WHERE category_rank = 1;

SELECT
    metric_name,
    COUNT(*) FILTER (
        WHERE metric_value > (
            SELECT AVG(metric_value)
            FROM observations
        )
    ) AS above_global_mean,
    COUNT(*) FILTER (
        WHERE metric_value <= (
            SELECT AVG(metric_value)
            FROM observations
        )
    ) AS at_or_below_global_mean
FROM observations
GROUP BY metric_name;

BEGIN;

INSERT INTO observations (
    observed_at,
    metric_name,
    metric_value,
    region,
    category,
    source_system
)
VALUES (
    '2026-10-31',
    'daily_sales',
    241,
    'South',
    'SMB',
    'sales_platform'
);

SELECT
    observation_id,
    observed_at,
    metric_value,
    region,
    category
FROM observations
WHERE observed_at = '2026-10-31';

COMMIT;

SELECT
    'Descriptive distribution' AS analysis,
    *
FROM descriptive_statistics;

SELECT
    'Regional and category patterns' AS analysis,
    *
FROM regional_patterns
ORDER BY region, category;

SELECT
    'Detected IQR anomalies' AS analysis,
    *
FROM iqr_anomalies
ORDER BY observed_at;
