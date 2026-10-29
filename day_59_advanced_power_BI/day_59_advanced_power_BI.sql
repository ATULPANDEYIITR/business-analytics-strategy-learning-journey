DROP SCHEMA IF EXISTS powerbi_analytics CASCADE;
CREATE SCHEMA powerbi_analytics;
SET search_path = powerbi_analytics, public;

-- The relational model intentionally separates dimensions, transactional facts,
-- reviewable calculations, and semi-additive inventory snapshots.

CREATE TABLE dim_date (
    date_key date PRIMARY KEY,
    year integer NOT NULL CHECK (year BETWEEN 2000 AND 2100),
    quarter integer NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month integer NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name text NOT NULL,
    month_start date NOT NULL,
    month_end date NOT NULL
);

CREATE TABLE dim_region (
    region_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name text NOT NULL UNIQUE
);

CREATE TABLE dim_product (
    product_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name text NOT NULL UNIQUE,
    category text NOT NULL
);

CREATE TABLE dim_channel (
    channel_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name text NOT NULL UNIQUE
);

CREATE TABLE dim_customer (
    customer_id integer PRIMARY KEY,
    customer_name text NOT NULL,
    customer_segment text NOT NULL
);

CREATE TABLE fact_sales (
    sale_id bigint PRIMARY KEY,
    sale_date date NOT NULL REFERENCES dim_date(date_key),
    region_id integer NOT NULL REFERENCES dim_region(region_id),
    product_id integer NOT NULL REFERENCES dim_product(product_id),
    channel_id integer NOT NULL REFERENCES dim_channel(channel_id),
    customer_id integer NOT NULL REFERENCES dim_customer(customer_id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(14,2) NOT NULL CHECK (unit_price >= 0),
    unit_cost numeric(14,2) NOT NULL CHECK (unit_cost >= 0)
);

CREATE TABLE fact_inventory_snapshot (
    snapshot_date date NOT NULL REFERENCES dim_date(date_key),
    region_id integer NOT NULL REFERENCES dim_region(region_id),
    product_id integer NOT NULL REFERENCES dim_product(product_id),
    units integer NOT NULL CHECK (units >= 0),
    PRIMARY KEY (snapshot_date, region_id, product_id)
);

CREATE INDEX ix_sales_date ON fact_sales (sale_date);
CREATE INDEX ix_sales_product_date ON fact_sales (product_id, sale_date);
CREATE INDEX ix_sales_region_date ON fact_sales (region_id, sale_date);
CREATE INDEX ix_sales_customer ON fact_sales (customer_id);

INSERT INTO dim_date (
    date_key, year, quarter, month, month_name, month_start, month_end
)
SELECT
    d::date,
    EXTRACT(YEAR FROM d)::integer,
    EXTRACT(QUARTER FROM d)::integer,
    EXTRACT(MONTH FROM d)::integer,
    TO_CHAR(d, 'FMMonth'),
    DATE_TRUNC('month', d)::date,
    (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::date
FROM generate_series(
    DATE '2026-01-01',
    DATE '2026-03-31',
    INTERVAL '1 day'
) AS g(d);

INSERT INTO dim_region(region_name)
VALUES ('North'), ('South'), ('West');

INSERT INTO dim_product(product_name, category)
VALUES
    ('Laptop', 'Computing'),
    ('Monitor', 'Display'),
    ('Keyboard', 'Accessories');

INSERT INTO dim_channel(channel_name)
VALUES ('Online'), ('Retail'), ('Partner');

INSERT INTO dim_customer(customer_id, customer_name, customer_segment)
VALUES
    (501, 'Customer 501', 'Enterprise'),
    (502, 'Customer 502', 'SMB'),
    (503, 'Customer 503', 'Enterprise'),
    (504, 'Customer 504', 'SMB'),
    (505, 'Customer 505', 'Enterprise'),
    (506, 'Customer 506', 'Consumer'),
    (507, 'Customer 507', 'SMB'),
    (508, 'Customer 508', 'Consumer'),
    (509, 'Customer 509', 'Enterprise'),
    (510, 'Customer 510', 'SMB'),
    (511, 'Customer 511', 'Enterprise'),
    (512, 'Customer 512', 'Consumer'),
    (513, 'Customer 513', 'Enterprise'),
    (514, 'Customer 514', 'SMB'),
    (515, 'Customer 515', 'Consumer'),
    (516, 'Customer 516', 'Enterprise');

INSERT INTO fact_sales (
    sale_id, sale_date, region_id, product_id, channel_id,
    customer_id, quantity, unit_price, unit_cost
)
SELECT
    v.sale_id,
    v.sale_date,
    r.region_id,
    p.product_id,
    c.channel_id,
    v.customer_id,
    v.quantity,
    v.unit_price,
    v.unit_cost
FROM (
    VALUES
    (1001, DATE '2026-01-02', 'North', 'Laptop', 'Online', 501, 2, 1200.00, 800.00),
    (1002, DATE '2026-01-04', 'North', 'Monitor', 'Retail', 502, 4, 300.00, 180.00),
    (1003, DATE '2026-01-08', 'South', 'Laptop', 'Partner', 503, 1, 1250.00, 800.00),
    (1004, DATE '2026-01-12', 'North', 'Keyboard', 'Online', 501, 5, 80.00, 35.00),
    (1005, DATE '2026-01-18', 'South', 'Monitor', 'Retail', 504, 3, 310.00, 180.00),
    (1006, DATE '2026-01-23', 'West', 'Laptop', 'Online', 505, 1, 1190.00, 800.00),
    (1007, DATE '2026-01-28', 'North', 'Laptop', 'Online', 506, 1, 1210.00, 800.00),
    (1008, DATE '2026-02-02', 'North', 'Monitor', 'Retail', 507, 5, 305.00, 180.00),
    (1009, DATE '2026-02-07', 'South', 'Laptop', 'Online', 503, 2, 1240.00, 800.00),
    (1010, DATE '2026-02-11', 'West', 'Keyboard', 'Partner', 508, 8, 82.00, 35.00),
    (1011, DATE '2026-02-16', 'North', 'Laptop', 'Online', 509, 1, 1230.00, 800.00),
    (1012, DATE '2026-02-20', 'South', 'Monitor', 'Retail', 510, 4, 315.00, 180.00),
    (1013, DATE '2026-02-24', 'West', 'Laptop', 'Partner', 511, 2, 1180.00, 800.00),
    (1014, DATE '2026-02-27', 'North', 'Keyboard', 'Online', 512, 10, 78.00, 35.00),
    (1015, DATE '2026-03-02', 'South', 'Laptop', 'Online', 513, 2, 1260.00, 800.00),
    (1016, DATE '2026-03-05', 'North', 'Monitor', 'Retail', 514, 6, 310.00, 180.00),
    (1017, DATE '2026-03-10', 'West', 'Keyboard', 'Partner', 515, 7, 85.00, 35.00),
    (1018, DATE '2026-03-14', 'South', 'Laptop', 'Online', 516, 1, 1270.00, 800.00)
) AS v(
    sale_id, sale_date, region_name, product_name, channel_name,
    customer_id, quantity, unit_price, unit_cost
)
JOIN dim_region r ON r.region_name = v.region_name
JOIN dim_product p ON p.product_name = v.product_name
JOIN dim_channel c ON c.channel_name = v.channel_name;

INSERT INTO fact_inventory_snapshot (
    snapshot_date, region_id, product_id, units
)
SELECT
    v.snapshot_date,
    r.region_id,
    p.product_id,
    v.units
FROM (
    VALUES
    (DATE '2026-01-31', 'North', 'Laptop', 42),
    (DATE '2026-01-31', 'North', 'Monitor', 70),
    (DATE '2026-01-31', 'South', 'Laptop', 31),
    (DATE '2026-02-28', 'North', 'Laptop', 37),
    (DATE '2026-02-28', 'North', 'Monitor', 64),
    (DATE '2026-02-28', 'South', 'Laptop', 26),
    (DATE '2026-02-28', 'West', 'Keyboard', 90),
    (DATE '2026-03-15', 'North', 'Laptop', 34),
    (DATE '2026-03-15', 'North', 'Monitor', 58),
    (DATE '2026-03-15', 'South', 'Laptop', 24),
    (DATE '2026-03-15', 'West', 'Keyboard', 82)
) AS v(snapshot_date, region_name, product_name, units)
JOIN dim_region r ON r.region_name = v.region_name
JOIN dim_product p ON p.product_name = v.product_name;

CREATE OR REPLACE FUNCTION fn_sale_margin(
    p_quantity integer,
    p_unit_price numeric,
    p_unit_cost numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT ROUND(
        (p_quantity * p_unit_price) -
        (p_quantity * p_unit_cost),
        2
    );
$$;

CREATE OR REPLACE FUNCTION fn_validate_sale()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.unit_cost > NEW.unit_price THEN
        RAISE EXCEPTION
            'Unit cost % exceeds unit price % for sale %',
            NEW.unit_cost, NEW.unit_price, NEW.sale_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sale
BEFORE INSERT OR UPDATE ON fact_sales
FOR EACH ROW
EXECUTE FUNCTION fn_validate_sale();

CREATE OR REPLACE VIEW v_sales_measures AS
SELECT
    s.sale_id,
    s.sale_date,
    r.region_name,
    p.product_name,
    p.category,
    c.channel_name,
    s.customer_id,
    s.quantity,
    s.quantity * s.unit_price AS revenue,
    s.quantity * s.unit_cost AS cost,
    fn_sale_margin(
        s.quantity,
        s.unit_price,
        s.unit_cost
    ) AS margin
FROM fact_sales s
JOIN dim_region r ON r.region_id = s.region_id
JOIN dim_product p ON p.product_id = s.product_id
JOIN dim_channel c ON c.channel_id = s.channel_id;

-- Base measures and derived analytical measures.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', sale_date)::date AS month_start,
        SUM(revenue) AS revenue,
        SUM(cost) AS cost,
        SUM(margin) AS margin,
        COUNT(DISTINCT customer_id) AS distinct_customers,
        COUNT(DISTINCT sale_id) AS orders
    FROM v_sales_measures
    GROUP BY DATE_TRUNC('month', sale_date)
),
with_previous AS (
    SELECT
        *,
        LAG(revenue) OVER (
            ORDER BY month_start
        ) AS previous_month_revenue
    FROM monthly
)
SELECT
    month_start,
    revenue,
    cost,
    margin,
    ROUND(100 * margin / NULLIF(revenue, 0), 2) AS margin_pct,
    distinct_customers,
    ROUND(revenue / NULLIF(orders, 0), 2) AS average_order_value,
    previous_month_revenue,
    ROUND(
        100 * (revenue - previous_month_revenue) /
        NULLIF(previous_month_revenue, 0),
        2
    ) AS month_over_month_pct
FROM with_previous
ORDER BY month_start;

-- Product ranking is evaluated within the selected February period.
WITH product_revenue AS (
    SELECT
        product_name,
        SUM(revenue) AS revenue
    FROM v_sales_measures
    WHERE sale_date >= DATE '2026-02-01'
      AND sale_date < DATE '2026-03-01'
    GROUP BY product_name
)
SELECT
    product_name,
    revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
    ROUND(
        100 * revenue / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS percent_of_selected_total
FROM product_revenue
ORDER BY revenue_rank, product_name;

-- Region contribution demonstrates the difference between a filtered
-- numerator and a denominator with the region filter removed.
WITH region_sales AS (
    SELECT
        region_name,
        SUM(revenue) AS revenue
    FROM v_sales_measures
    WHERE sale_date >= DATE '2026-02-01'
      AND sale_date < DATE '2026-03-01'
    GROUP BY region_name
)
SELECT
    region_name,
    revenue,
    ROUND(
        100 * revenue / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS percent_of_month_total
FROM region_sales
ORDER BY revenue DESC;

-- Rolling seven-day revenue. The calendar table ensures missing transaction
-- days remain part of the analytical window.
SELECT
    d.date_key,
    COALESCE(SUM(v.revenue), 0) AS daily_revenue,
    ROUND(
        SUM(COALESCE(SUM(v.revenue), 0)) OVER (
            ORDER BY d.date_key
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_7_day_revenue
FROM dim_date d
LEFT JOIN v_sales_measures v
    ON v.sale_date = d.date_key
WHERE d.date_key BETWEEN DATE '2026-02-01' AND DATE '2026-03-15'
GROUP BY d.date_key
ORDER BY d.date_key;

-- Semi-additive inventory measure:
-- inventory is summed across products for the latest available snapshot,
-- not summed across all historical snapshots.
WITH latest AS (
    SELECT MAX(snapshot_date) AS latest_date
    FROM fact_inventory_snapshot
)
SELECT
    latest.latest_date,
    SUM(i.units) AS latest_inventory_units
FROM latest
JOIN fact_inventory_snapshot i
    ON i.snapshot_date = latest.latest_date
GROUP BY latest.latest_date;

-- Product margin contribution by region.
SELECT
    region_name,
    product_name,
    SUM(revenue) AS revenue,
    SUM(cost) AS cost,
    SUM(margin) AS margin,
    ROUND(
        100 * SUM(margin) / NULLIF(SUM(revenue), 0),
        2
    ) AS margin_pct
FROM v_sales_measures
GROUP BY region_name, product_name
ORDER BY region_name, revenue DESC;

-- Validation query for impossible negative-margin records.
SELECT
    sale_id,
    sale_date,
    revenue,
    cost,
    margin
FROM v_sales_measures
WHERE margin < 0
ORDER BY sale_id;

-- Transactional integrity demonstration. The insert is rolled back after
-- exercising the database-level validation path.
BEGIN;

INSERT INTO fact_sales (
    sale_id,
    sale_date,
    region_id,
    product_id,
    channel_id,
    customer_id,
    quantity,
    unit_price,
    unit_cost
)
VALUES (
    9001,
    DATE '2026-03-20',
    (SELECT region_id FROM dim_region WHERE region_name = 'North'),
    (SELECT product_id FROM dim_product WHERE product_name = 'Laptop'),
    (SELECT channel_id FROM dim_channel WHERE channel_name = 'Online'),
    501,
    1,
    100.00,
    60.00
);

ROLLBACK;

-- A reusable reporting function keeps business rules in one database object.
CREATE OR REPLACE FUNCTION fn_monthly_metrics(
    p_month_start date
)
RETURNS TABLE (
    revenue numeric,
    cost numeric,
    margin numeric,
    margin_pct numeric,
    distinct_customers bigint,
    average_order_value numeric
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        ROUND(COALESCE(SUM(v.revenue), 0), 2),
        ROUND(COALESCE(SUM(v.cost), 0), 2),
        ROUND(COALESCE(SUM(v.margin), 0), 2),
        ROUND(
            100 * COALESCE(SUM(v.margin), 0) /
            NULLIF(SUM(v.revenue), 0),
            2
        ),
        COUNT(DISTINCT v.customer_id),
        ROUND(
            COALESCE(SUM(v.revenue), 0) /
            NULLIF(COUNT(DISTINCT v.sale_id), 0),
            2
        )
    FROM v_sales_measures v
    WHERE v.sale_date >= p_month_start
      AND v.sale_date < p_month_start + INTERVAL '1 month';
$$;

SELECT *
FROM fn_monthly_metrics(DATE '2026-02-01');

-- The following query identifies customers who contributed to more than one
-- product, a useful analytical segmentation for customer-level measures.
SELECT
    customer_id,
    COUNT(DISTINCT product_name) AS products_purchased,
    SUM(revenue) AS customer_revenue,
    SUM(margin) AS customer_margin
FROM v_sales_measures
GROUP BY customer_id
HAVING COUNT(DISTINCT product_name) > 1
ORDER BY customer_revenue DESC;
