DROP SCHEMA IF EXISTS business_charts CASCADE;
CREATE SCHEMA business_charts;

SET search_path TO business_charts, public;

CREATE TABLE regions (
    region_id BIGSERIAL PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE sales_months (
    month_id BIGSERIAL PRIMARY KEY,
    month_start DATE NOT NULL UNIQUE,
    CHECK (month_start = date_trunc('month', month_start)::date)
);

CREATE TABLE sales (
    sale_id BIGSERIAL PRIMARY KEY,
    month_id BIGINT NOT NULL REFERENCES sales_months(month_id),
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    revenue NUMERIC(14,2) NOT NULL CHECK (revenue >= 0),
    orders INTEGER NOT NULL CHECK (orders >= 0),
    marketing_spend NUMERIC(14,2) NOT NULL CHECK (marketing_spend >= 0),
    delivery_days NUMERIC(8,2) NOT NULL CHECK (delivery_days >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_month_region
    ON sales(month_id, region_id);

CREATE INDEX idx_sales_region
    ON sales(region_id);

CREATE INDEX idx_sales_revenue
    ON sales(revenue);

CREATE TABLE chart_definitions (
    chart_type TEXT PRIMARY KEY,
    minimum_observations INTEGER NOT NULL CHECK (minimum_observations > 0),
    purpose TEXT NOT NULL
);

INSERT INTO regions (region_name)
VALUES
    ('North'),
    ('South'),
    ('West');

INSERT INTO sales_months (month_start)
VALUES
    ('2026-01-01'),
    ('2026-02-01'),
    ('2026-03-01'),
    ('2026-04-01'),
    ('2026-05-01'),
    ('2026-06-01');

INSERT INTO chart_definitions (
    chart_type,
    minimum_observations,
    purpose
)
VALUES
    (
        'bar',
        1,
        'Compare magnitude across discrete business categories'
    ),
    (
        'line',
        2,
        'Show change across an ordered business dimension'
    ),
    (
        'scatter',
        2,
        'Evaluate association between two quantitative variables'
    ),
    (
        'histogram',
        2,
        'Show the distribution of a quantitative variable'
    ),
    (
        'box',
        5,
        'Show distribution, quartiles, spread, and outliers'
    );

CREATE OR REPLACE FUNCTION validate_sale()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.revenue < 0 THEN
        RAISE EXCEPTION 'Revenue cannot be negative';
    END IF;

    IF NEW.orders < 0 THEN
        RAISE EXCEPTION 'Orders cannot be negative';
    END IF;

    IF NEW.marketing_spend < 0 THEN
        RAISE EXCEPTION 'Marketing spend cannot be negative';
    END IF;

    IF NEW.delivery_days < 0 THEN
        RAISE EXCEPTION 'Delivery days cannot be negative';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sale
BEFORE INSERT OR UPDATE ON sales
FOR EACH ROW
EXECUTE FUNCTION validate_sale();

INSERT INTO sales (
    month_id,
    region_id,
    revenue,
    orders,
    marketing_spend,
    delivery_days
)
SELECT
    sm.month_id,
    r.region_id,
    data.revenue,
    data.orders,
    data.marketing_spend,
    data.delivery_days
FROM (
    VALUES
        ('2026-01-01'::date, 'North', 72000, 410, 11000, 3.2),
        ('2026-01-01'::date, 'South', 64000, 390, 9500, 4.1),
        ('2026-01-01'::date, 'West', 81000, 450, 12500, 2.8),
        ('2026-02-01'::date, 'North', 76000, 425, 11500, 3.4),
        ('2026-02-01'::date, 'South', 68000, 402, 10200, 4.0),
        ('2026-02-01'::date, 'West', 87000, 478, 13100, 2.6),
        ('2026-03-01'::date, 'North', 83000, 440, 12000, 3.6),
        ('2026-03-01'::date, 'South', 70000, 410, 10500, 4.4),
        ('2026-03-01'::date, 'West', 92000, 495, 13800, 2.9),
        ('2026-04-01'::date, 'North', 88000, 462, 12700, 3.5),
        ('2026-04-01'::date, 'South', 73000, 421, 10800, 4.2),
        ('2026-04-01'::date, 'West', 97000, 510, 14500, 2.7),
        ('2026-05-01'::date, 'North', 91000, 475, 13000, 3.8),
        ('2026-05-01'::date, 'South', 76000, 430, 11100, 4.5),
        ('2026-05-01'::date, 'West', 103000, 535, 15100, 2.5),
        ('2026-06-01'::date, 'North', 96000, 490, 13600, 3.7),
        ('2026-06-01'::date, 'South', 79000, 442, 11400, 4.3),
        ('2026-06-01'::date, 'West', 108000, 552, 15700, 2.8),
        ('2026-06-01'::date, 'West', 155000, 600, 22000, 9.5)
) AS data(
    month_start,
    region_name,
    revenue,
    orders,
    marketing_spend,
    delivery_days
)
JOIN sales_months sm
    ON sm.month_start = data.month_start
JOIN regions r
    ON r.region_name = data.region_name;

CREATE VIEW revenue_by_region AS
SELECT
    r.region_name,
    SUM(s.revenue) AS total_revenue,
    SUM(s.orders) AS total_orders,
    SUM(s.marketing_spend) AS total_marketing_spend
FROM sales s
JOIN regions r
    ON r.region_id = s.region_id
GROUP BY r.region_name;

CREATE VIEW monthly_revenue AS
SELECT
    sm.month_start,
    SUM(s.revenue) AS total_revenue,
    SUM(s.orders) AS total_orders
FROM sales s
JOIN sales_months sm
    ON sm.month_id = s.month_id
GROUP BY sm.month_start;

CREATE VIEW scatter_data AS
SELECT
    s.sale_id,
    s.marketing_spend,
    s.revenue,
    s.orders,
    s.delivery_days
FROM sales s;

CREATE VIEW revenue_distribution AS
SELECT
    width_bucket(
        revenue,
        0,
        180000,
        9
    ) AS bucket,
    COUNT(*) AS observation_count,
    MIN(revenue) AS bucket_minimum,
    MAX(revenue) AS bucket_maximum
FROM sales
GROUP BY bucket
ORDER BY bucket;

CREATE VIEW delivery_box_statistics AS
WITH quartiles AS (
    SELECT
        percentile_cont(0.25)
            WITHIN GROUP (ORDER BY delivery_days) AS q1,
        percentile_cont(0.50)
            WITHIN GROUP (ORDER BY delivery_days) AS median,
        percentile_cont(0.75)
            WITHIN GROUP (ORDER BY delivery_days) AS q3
    FROM sales
),
fences AS (
    SELECT
        q1,
        median,
        q3,
        q1 - 1.5 * (q3 - q1) AS lower_fence,
        q3 + 1.5 * (q3 - q1) AS upper_fence
    FROM quartiles
)
SELECT
    q1,
    median,
    q3,
    lower_fence,
    upper_fence,
    MIN(
        CASE
            WHEN s.delivery_days BETWEEN f.lower_fence AND f.upper_fence
            THEN s.delivery_days
        END
    ) AS whisker_minimum,
    MAX(
        CASE
            WHEN s.delivery_days BETWEEN f.lower_fence AND f.upper_fence
            THEN s.delivery_days
        END
    ) AS whisker_maximum,
    ARRAY_AGG(
        s.delivery_days
        ORDER BY s.delivery_days
    ) FILTER (
        WHERE s.delivery_days < f.lower_fence
           OR s.delivery_days > f.upper_fence
    ) AS outliers
FROM sales s
CROSS JOIN fences f
GROUP BY
    q1,
    median,
    q3,
    lower_fence,
    upper_fence;

CREATE OR REPLACE FUNCTION chart_eligibility(
    requested_chart TEXT
)
RETURNS TABLE (
    chart_type TEXT,
    eligible BOOLEAN,
    observation_count BIGINT,
    minimum_required INTEGER,
    reason TEXT
)
LANGUAGE sql
AS $$
    SELECT
        d.chart_type,
        COUNT(s.sale_id) >= d.minimum_observations,
        COUNT(s.sale_id),
        d.minimum_observations,
        CASE
            WHEN COUNT(s.sale_id) >= d.minimum_observations
            THEN 'Sufficient observations'
            ELSE 'Insufficient observations'
        END
    FROM chart_definitions d
    LEFT JOIN sales s ON TRUE
    WHERE d.chart_type = requested_chart
    GROUP BY
        d.chart_type,
        d.minimum_observations;
$$;

CREATE OR REPLACE FUNCTION revenue_summary()
RETURNS TABLE (
    total_revenue NUMERIC,
    average_revenue NUMERIC,
    median_revenue NUMERIC,
    total_orders BIGINT
)
LANGUAGE sql
AS $$
    SELECT
        SUM(revenue),
        ROUND(AVG(revenue), 2),
        percentile_cont(0.50)
            WITHIN GROUP (ORDER BY revenue),
        SUM(orders)
    FROM sales;
$$;

BEGIN;

SELECT *
FROM revenue_by_region
ORDER BY total_revenue DESC;

SELECT *
FROM monthly_revenue
ORDER BY month_start;

SELECT *
FROM scatter_data
ORDER BY sale_id;

SELECT *
FROM revenue_distribution;

SELECT *
FROM delivery_box_statistics;

SELECT *
FROM chart_eligibility('bar');

SELECT *
FROM chart_eligibility('line');

SELECT *
FROM chart_eligibility('scatter');

SELECT *
FROM chart_eligibility('histogram');

SELECT *
FROM chart_eligibility('box');

SELECT *
FROM revenue_summary();

-- A window calculation exposes month-over-month movement
-- without changing the underlying transactional data.
WITH monthly AS (
    SELECT
        month_start,
        total_revenue
    FROM monthly_revenue
)
SELECT
    month_start,
    total_revenue,
    LAG(total_revenue)
        OVER (ORDER BY month_start) AS previous_month,
    total_revenue
        - LAG(total_revenue)
          OVER (ORDER BY month_start) AS revenue_change
FROM monthly
ORDER BY month_start;

-- A CTE identifies unusually long delivery observations
-- using the same IQR rule used by the box-plot model.
WITH quartiles AS (
    SELECT
        percentile_cont(0.25)
            WITHIN GROUP (ORDER BY delivery_days) AS q1,
        percentile_cont(0.75)
            WITHIN GROUP (ORDER BY delivery_days) AS q3
    FROM sales
),
thresholds AS (
    SELECT
        q1,
        q3,
        q1 - 1.5 * (q3 - q1) AS lower_fence,
        q3 + 1.5 * (q3 - q1) AS upper_fence
    FROM quartiles
)
SELECT
    s.sale_id,
    r.region_name,
    sm.month_start,
    s.delivery_days
FROM sales s
JOIN regions r
    ON r.region_id = s.region_id
JOIN sales_months sm
    ON sm.month_id = s.month_id
CROSS JOIN thresholds t
WHERE s.delivery_days < t.lower_fence
   OR s.delivery_days > t.upper_fence
ORDER BY s.delivery_days DESC;

COMMIT;
