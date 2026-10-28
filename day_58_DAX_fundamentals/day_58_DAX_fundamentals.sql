DROP SCHEMA IF EXISTS dax_fundamentals CASCADE;
CREATE SCHEMA dax_fundamentals;

SET search_path TO dax_fundamentals;

-- A star-style model keeps transactional facts separate from descriptive
-- dimensions. Measures aggregate facts while dimensions establish context.

CREATE TABLE dim_region (
    region_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name text NOT NULL UNIQUE
);

CREATE TABLE dim_category (
    category_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name text NOT NULL UNIQUE
);

CREATE TABLE dim_product (
    product_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name text NOT NULL UNIQUE,
    category_id integer NOT NULL
        REFERENCES dim_category(category_id)
);

CREATE TABLE dim_date (
    date_key date PRIMARY KEY,
    calendar_year integer NOT NULL,
    calendar_month integer NOT NULL CHECK (calendar_month BETWEEN 1 AND 12),
    month_name text NOT NULL
);

CREATE TABLE fact_sales (
    order_id bigint PRIMARY KEY,
    order_date date NOT NULL
        REFERENCES dim_date(date_key),
    region_id integer NOT NULL
        REFERENCES dim_region(region_id),
    product_id integer NOT NULL
        REFERENCES dim_product(product_id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    unit_cost numeric(12,2) NOT NULL CHECK (unit_cost >= 0),
    CHECK (unit_cost <= unit_price)
);

CREATE TABLE branchless_measure_policy (
    policy_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name text NOT NULL UNIQUE,
    high_sales_threshold numeric(12,2) NOT NULL CHECK (high_sales_threshold > 0),
    medium_sales_threshold numeric(12,2) NOT NULL CHECK (
        medium_sales_threshold > 0
        AND medium_sales_threshold < high_sales_threshold
    )
);

INSERT INTO dim_region (region_name)
VALUES
    ('North'),
    ('South'),
    ('West');

INSERT INTO dim_category (category_name)
VALUES
    ('Technology'),
    ('Furniture');

INSERT INTO dim_product (product_name, category_id)
SELECT
    p.product_name,
    c.category_id
FROM (
    VALUES
        ('Laptop', 'Technology'),
        ('Monitor', 'Technology'),
        ('Desk', 'Furniture'),
        ('Chair', 'Furniture')
) AS p(product_name, category_name)
JOIN dim_category c
    ON c.category_name = p.category_name;

INSERT INTO dim_date (
    date_key,
    calendar_year,
    calendar_month,
    month_name
)
VALUES
    ('2026-01-05', 2026, 1, 'January'),
    ('2026-01-07', 2026, 1, 'January'),
    ('2026-01-09', 2026, 1, 'January'),
    ('2026-01-12', 2026, 1, 'January'),
    ('2026-01-15', 2026, 1, 'January'),
    ('2026-01-19', 2026, 1, 'January'),
    ('2026-01-23', 2026, 1, 'January'),
    ('2026-01-27', 2026, 1, 'January');

INSERT INTO fact_sales (
    order_id,
    order_date,
    region_id,
    product_id,
    quantity,
    unit_price,
    unit_cost
)
SELECT
    v.order_id,
    v.order_date,
    r.region_id,
    p.product_id,
    v.quantity,
    v.unit_price,
    v.unit_cost
FROM (
    VALUES
        (1001, '2026-01-05'::date, 'North', 'Laptop', 2, 1200.00, 850.00),
        (1002, '2026-01-07'::date, 'South', 'Monitor', 4, 350.00, 220.00),
        (1003, '2026-01-09'::date, 'North', 'Desk', 3, 500.00, 310.00),
        (1004, '2026-01-12'::date, 'West', 'Laptop', 1, 1500.00, 980.00),
        (1005, '2026-01-15'::date, 'South', 'Chair', 8, 180.00, 110.00),
        (1006, '2026-01-19'::date, 'West', 'Desk', 2, 550.00, 320.00),
        (1007, '2026-01-23'::date, 'North', 'Monitor', 5, 325.00, 200.00),
        (1008, '2026-01-27'::date, 'South', 'Laptop', 3, 1100.00, 790.00)
) AS v(
    order_id,
    order_date,
    region_name,
    product_name,
    quantity,
    unit_price,
    unit_cost
)
JOIN dim_region r
    ON r.region_name = v.region_name
JOIN dim_product p
    ON p.product_name = v.product_name;

INSERT INTO branchless_measure_policy (
    policy_name,
    high_sales_threshold,
    medium_sales_threshold
)
VALUES (
    'Standard Sales Band',
    5000.00,
    2000.00
);

-- Indexes support the common dimension-to-fact filtering paths.
CREATE INDEX idx_fact_sales_date
    ON fact_sales(order_date);

CREATE INDEX idx_fact_sales_region
    ON fact_sales(region_id);

CREATE INDEX idx_fact_sales_product
    ON fact_sales(product_id);

CREATE INDEX idx_product_category
    ON dim_product(category_id);

-- A calculated-column-style view exposes row-level values.
CREATE VIEW calculated_sales_columns AS
SELECT
    f.order_id,
    f.order_date,
    r.region_name,
    p.product_name,
    c.category_name,
    f.quantity,
    f.unit_price,
    f.unit_cost,
    f.quantity * f.unit_price AS sales_amount,
    f.quantity * f.unit_cost AS cost_amount,
    f.quantity * (f.unit_price - f.unit_cost) AS profit_amount,
    CASE
        WHEN f.quantity * f.unit_price = 0 THEN 0::numeric
        ELSE
            (
                f.quantity * (f.unit_price - f.unit_cost)
            )
            /
            (f.quantity * f.unit_price)
    END AS profit_margin,
    CASE
        WHEN f.quantity * f.unit_price >= 5000 THEN 'High'
        WHEN f.quantity * f.unit_price >= 2000 THEN 'Medium'
        ELSE 'Low'
    END AS sales_band
FROM fact_sales f
JOIN dim_region r
    ON r.region_id = f.region_id
JOIN dim_product p
    ON p.product_id = f.product_id
JOIN dim_category c
    ON c.category_id = p.category_id;

-- Measure-style query: aggregation occurs after the current context
-- established by the selected dimensions.
SELECT
    SUM(quantity * unit_price) AS total_sales,
    SUM(quantity * unit_cost) AS total_cost,
    SUM(quantity * (unit_price - unit_cost)) AS total_profit,
    CASE
        WHEN SUM(quantity * unit_price) = 0 THEN 0::numeric
        ELSE
            SUM(quantity * (unit_price - unit_cost))
            / SUM(quantity * unit_price)
    END AS profit_margin
FROM fact_sales;

-- Region filter context.
SELECT
    r.region_name,
    COUNT(*) AS order_count,
    SUM(f.quantity * f.unit_price) AS total_sales,
    SUM(f.quantity * (f.unit_price - f.unit_cost)) AS total_profit,
    CASE
        WHEN SUM(f.quantity * f.unit_price) = 0 THEN 0::numeric
        ELSE
            SUM(f.quantity * (f.unit_price - f.unit_cost))
            / SUM(f.quantity * f.unit_price)
    END AS profit_margin
FROM fact_sales f
JOIN dim_region r
    ON r.region_id = f.region_id
GROUP BY r.region_name
ORDER BY r.region_name;

-- Category filter context.
SELECT
    c.category_name,
    COUNT(*) AS order_count,
    SUM(f.quantity * f.unit_price) AS total_sales,
    SUM(f.quantity * (f.unit_price - f.unit_cost)) AS total_profit
FROM fact_sales f
JOIN dim_product p
    ON p.product_id = f.product_id
JOIN dim_category c
    ON c.category_id = p.category_id
GROUP BY c.category_name
ORDER BY total_sales DESC;

-- Combined context: region + category.
SELECT
    r.region_name,
    c.category_name,
    SUM(f.quantity * f.unit_price) AS total_sales,
    SUM(f.quantity * (f.unit_price - f.unit_cost)) AS total_profit
FROM fact_sales f
JOIN dim_region r
    ON r.region_id = f.region_id
JOIN dim_product p
    ON p.product_id = f.product_id
JOIN dim_category c
    ON c.category_id = p.category_id
WHERE r.region_name = 'South'
  AND c.category_name = 'Technology'
GROUP BY r.region_name, c.category_name;

-- CTE-based ranking provides a TOPN-style analytical operation.
WITH product_totals AS (
    SELECT
        p.product_name,
        SUM(f.quantity * f.unit_price) AS total_sales
    FROM fact_sales f
    JOIN dim_product p
        ON p.product_id = f.product_id
    GROUP BY p.product_name
),
ranked_products AS (
    SELECT
        product_name,
        total_sales,
        RANK() OVER (
            ORDER BY total_sales DESC
        ) AS sales_rank
    FROM product_totals
)
SELECT
    product_name,
    total_sales,
    sales_rank
FROM ranked_products
WHERE sales_rank <= 3
ORDER BY sales_rank, product_name;

-- A measure function provides reusable DIVIDE-like semantics.
CREATE OR REPLACE FUNCTION safe_divide(
    numerator numeric,
    denominator numeric
)
RETURNS numeric
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT
        CASE
            WHEN denominator = 0 THEN 0::numeric
            ELSE numerator / denominator
        END;
$$;

-- Reusable analytical function with explicit filter arguments.
CREATE OR REPLACE FUNCTION sales_measure(
    requested_region text DEFAULT NULL,
    requested_category text DEFAULT NULL
)
RETURNS TABLE (
    total_sales numeric,
    total_cost numeric,
    total_profit numeric,
    profit_margin numeric
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        COALESCE(SUM(f.quantity * f.unit_price), 0)::numeric,
        COALESCE(SUM(f.quantity * f.unit_cost), 0)::numeric,
        COALESCE(
            SUM(f.quantity * (f.unit_price - f.unit_cost)),
            0
        )::numeric,
        safe_divide(
            COALESCE(
                SUM(f.quantity * (f.unit_price - f.unit_cost)),
                0
            ),
            COALESCE(
                SUM(f.quantity * f.unit_price),
                0
            )
        )
    FROM fact_sales f
    JOIN dim_region r
        ON r.region_id = f.region_id
    JOIN dim_product p
        ON p.product_id = f.product_id
    JOIN dim_category c
        ON c.category_id = p.category_id
    WHERE
        (
            requested_region IS NULL
            OR r.region_name = requested_region
        )
        AND (
            requested_category IS NULL
            OR c.category_name = requested_category
        );
$$;

SELECT *
FROM sales_measure();

SELECT *
FROM sales_measure('North', NULL);

SELECT *
FROM sales_measure('South', 'Technology');

-- Transactional integrity demonstration.
BEGIN;

INSERT INTO fact_sales (
    order_id,
    order_date,
    region_id,
    product_id,
    quantity,
    unit_price,
    unit_cost
)
SELECT
    1099,
    '2026-01-27',
    region_id,
    product_id,
    1,
    100.00,
    70.00
FROM dim_region
CROSS JOIN dim_product
WHERE region_name = 'West'
  AND product_name = 'Monitor';

-- The inserted row is intentionally rolled back so the analytical
-- baseline remains deterministic for repeated executions.
ROLLBACK;

-- Validation query for expected totals.
WITH totals AS (
    SELECT
        SUM(quantity * unit_price) AS sales,
        SUM(quantity * (unit_price - unit_cost)) AS profit
    FROM fact_sales
)
SELECT
    sales,
    profit,
    CASE
        WHEN sales = 10555.00
         AND profit = 3405.00
        THEN 'PASS'
        ELSE 'FAIL'
    END AS validation_status
FROM totals;

-- Failure-case validation. This statement is inside a savepoint so a
-- rejected business condition does not damage the surrounding transaction.
BEGIN;

SAVEPOINT invalid_sales;

-- This violates CHECK (unit_cost <= unit_price).
-- It is handled by rolling back the savepoint before the transaction ends.
DO $$
BEGIN
    BEGIN
        INSERT INTO fact_sales (
            order_id,
            order_date,
            region_id,
            product_id,
            quantity,
            unit_price,
            unit_cost
        )
        SELECT
            9000,
            '2026-01-27',
            region_id,
            product_id,
            1,
            100.00,
            150.00
        FROM dim_region
        CROSS JOIN dim_product
        WHERE region_name = 'North'
          AND product_name = 'Laptop';

        RAISE EXCEPTION 'Expected constraint violation did not occur';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid cost/price combination rejected as expected';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_sales;
COMMIT;
