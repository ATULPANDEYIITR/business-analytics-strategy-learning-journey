DROP SCHEMA IF EXISTS powerbi_model CASCADE;

CREATE SCHEMA powerbi_model;

SET search_path TO powerbi_model, public;

-- Dimension tables contain descriptive attributes used for filtering,
-- slicing and grouping. FactSales stores measurable business events.

CREATE TABLE dim_date (
    date_key        integer PRIMARY KEY,
    calendar_date   date NOT NULL UNIQUE,
    year_number     integer NOT NULL CHECK (year_number BETWEEN 1900 AND 2200),
    quarter_number  integer NOT NULL CHECK (quarter_number BETWEEN 1 AND 4),
    month_number    integer NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    month_name      text NOT NULL,
    day_of_month    integer NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    is_weekend      boolean NOT NULL
);

CREATE TABLE dim_customer (
    customer_key    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     text NOT NULL UNIQUE,
    customer_name   text NOT NULL,
    segment         text NOT NULL CHECK (
        segment IN ('Enterprise', 'Mid-Market', 'SMB')
    ),
    region          text NOT NULL CHECK (
        region IN ('North', 'South', 'East', 'West')
    )
);

CREATE TABLE dim_product (
    product_key     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id      text NOT NULL UNIQUE,
    product_name    text NOT NULL,
    category        text NOT NULL CHECK (
        category IN ('Software', 'Hardware', 'Services')
    ),
    subcategory    text NOT NULL
);

CREATE TABLE fact_sales (
    sales_key       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    date_key        integer NOT NULL REFERENCES dim_date(date_key),
    customer_key    bigint NOT NULL REFERENCES dim_customer(customer_key),
    product_key     bigint NOT NULL REFERENCES dim_product(product_key),
    order_id        text NOT NULL,
    quantity        integer NOT NULL CHECK (quantity > 0),
    unit_price      numeric(14,2) NOT NULL CHECK (unit_price >= 0),
    discount_rate   numeric(5,4) NOT NULL CHECK (
        discount_rate >= 0 AND discount_rate <= 1
    ),
    created_at      timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (order_id, product_key)
);

-- These indexes support common dimensional filtering and foreign-key joins.
CREATE INDEX idx_fact_sales_date
    ON fact_sales(date_key);

CREATE INDEX idx_fact_sales_customer
    ON fact_sales(customer_key);

CREATE INDEX idx_fact_sales_product
    ON fact_sales(product_key);

CREATE INDEX idx_customer_region_segment
    ON dim_customer(region, segment);

CREATE INDEX idx_product_category_subcategory
    ON dim_product(category, subcategory);

INSERT INTO dim_date (
    date_key,
    calendar_date,
    year_number,
    quarter_number,
    month_number,
    month_name,
    day_of_month,
    is_weekend
)
VALUES
    (20260105, DATE '2026-01-05', 2026, 1, 1, 'January', 5, false),
    (20260118, DATE '2026-01-18', 2026, 1, 1, 'January', 18, true),
    (20260207, DATE '2026-02-07', 2026, 1, 2, 'February', 7, true),
    (20260221, DATE '2026-02-21', 2026, 1, 2, 'February', 21, true),
    (20260312, DATE '2026-03-12', 2026, 1, 3, 'March', 12, false),
    (20260328, DATE '2026-03-28', 2026, 1, 3, 'March', 28, true),
    (20260409, DATE '2026-04-09', 2026, 2, 4, 'April', 9, false),
    (20260425, DATE '2026-04-25', 2026, 2, 4, 'April', 25, true);

INSERT INTO dim_customer (
    customer_id,
    customer_name,
    segment,
    region
)
VALUES
    ('C001', 'Apex Systems', 'Enterprise', 'North'),
    ('C002', 'Blue Retail', 'SMB', 'West'),
    ('C003', 'Cedar Health', 'Enterprise', 'South'),
    ('C004', 'Delta Labs', 'Mid-Market', 'East');

INSERT INTO dim_product (
    product_id,
    product_name,
    category,
    subcategory
)
VALUES
    ('P001', 'Analytics Platform', 'Software', 'Analytics'),
    ('P002', 'Security Suite', 'Software', 'Security'),
    ('P003', 'Cloud Appliance', 'Hardware', 'Infrastructure'),
    ('P004', 'Support Contract', 'Services', 'Support');

INSERT INTO fact_sales (
    date_key,
    customer_key,
    product_key,
    order_id,
    quantity,
    unit_price,
    discount_rate
)
SELECT
    v.date_key,
    c.customer_key,
    p.product_key,
    v.order_id,
    v.quantity,
    v.unit_price,
    v.discount_rate
FROM (
    VALUES
        (20260105, 'C001', 'P001', 'SO1001', 3, 1200.00::numeric, 0.05::numeric),
        (20260118, 'C002', 'P002', 'SO1002', 2, 800.00::numeric, 0.00::numeric),
        (20260207, 'C003', 'P003', 'SO1003', 1, 4500.00::numeric, 0.10::numeric),
        (20260221, 'C004', 'P004', 'SO1004', 5, 300.00::numeric, 0.05::numeric),
        (20260312, 'C001', 'P002', 'SO1005', 4, 800.00::numeric, 0.10::numeric),
        (20260328, 'C002', 'P001', 'SO1006', 1, 1200.00::numeric, 0.00::numeric),
        (20260409, 'C003', 'P004', 'SO1007', 8, 300.00::numeric, 0.00::numeric),
        (20260425, 'C004', 'P003', 'SO1008', 2, 4500.00::numeric, 0.15::numeric)
) AS v(
    date_key,
    customer_id,
    product_id,
    order_id,
    quantity,
    unit_price,
    discount_rate
)
JOIN dim_customer c
    ON c.customer_id = v.customer_id
JOIN dim_product p
    ON p.product_id = v.product_id;

-- The view represents the denormalized analytical shape consumed by
-- reporting logic while preserving a normalized relational source model.
CREATE VIEW vw_sales_model AS
SELECT
    f.sales_key,
    f.order_id,
    d.calendar_date,
    d.year_number,
    d.quarter_number,
    d.month_number,
    d.month_name,
    c.customer_id,
    c.customer_name,
    c.segment,
    c.region,
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    f.quantity,
    f.unit_price,
    f.discount_rate,
    f.quantity * f.unit_price AS gross_sales,
    f.quantity * f.unit_price * f.discount_rate AS discount_amount,
    f.quantity * f.unit_price *
        (1 - f.discount_rate) AS net_sales
FROM fact_sales f
JOIN dim_date d
    ON d.date_key = f.date_key
JOIN dim_customer c
    ON c.customer_key = f.customer_key
JOIN dim_product p
    ON p.product_key = f.product_key;

-- Validate the star-schema relationships.
CREATE OR REPLACE FUNCTION validate_fact_relationships()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM dim_date
        WHERE date_key = NEW.date_key
    ) THEN
        RAISE EXCEPTION
            'Invalid date_key % for fact row', NEW.date_key;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM dim_customer
        WHERE customer_key = NEW.customer_key
    ) THEN
        RAISE EXCEPTION
            'Invalid customer_key % for fact row', NEW.customer_key;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM dim_product
        WHERE product_key = NEW.product_key
    ) THEN
        RAISE EXCEPTION
            'Invalid product_key % for fact row', NEW.product_key;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_fact_relationships
BEFORE INSERT OR UPDATE ON fact_sales
FOR EACH ROW
EXECUTE FUNCTION validate_fact_relationships();

-- Reusable measure function for report-style aggregation.
CREATE OR REPLACE FUNCTION calculate_net_sales(
    p_year integer DEFAULT NULL,
    p_region text DEFAULT NULL,
    p_category text DEFAULT NULL
)
RETURNS numeric(18,2)
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(
        SUM(
            f.quantity *
            f.unit_price *
            (1 - f.discount_rate)
        ),
        0
    )::numeric(18,2)
    FROM fact_sales f
    JOIN dim_date d
        ON d.date_key = f.date_key
    JOIN dim_customer c
        ON c.customer_key = f.customer_key
    JOIN dim_product p
        ON p.product_key = f.product_key
    WHERE (p_year IS NULL OR d.year_number = p_year)
      AND (p_region IS NULL OR c.region = p_region)
      AND (p_category IS NULL OR p.category = p_category);
$$;

-- Transactional integrity example: a new order is inserted only after
-- its dimensional references have been resolved.
BEGIN;

WITH selected_dimensions AS (
    SELECT
        d.date_key,
        c.customer_key,
        p.product_key
    FROM dim_date d
    CROSS JOIN dim_customer c
    CROSS JOIN dim_product p
    WHERE d.date_key = 20260425
      AND c.customer_id = 'C001'
      AND p.product_id = 'P004'
)
INSERT INTO fact_sales (
    date_key,
    customer_key,
    product_key,
    order_id,
    quantity,
    unit_price,
    discount_rate
)
SELECT
    date_key,
    customer_key,
    product_key,
    'SO1009',
    2,
    300.00,
    0.00
FROM selected_dimensions;

COMMIT;

-- Basic retrieval: analytical rows with dimensional attributes.
SELECT *
FROM vw_sales_model
ORDER BY calendar_date, order_id;

-- Measure evaluation after dimensional filtering.
SELECT calculate_net_sales(2026, NULL, NULL) AS total_2026_net_sales;

SELECT calculate_net_sales(2026, 'North', NULL)
    AS north_2026_net_sales;

SELECT calculate_net_sales(2026, NULL, 'Software')
    AS software_2026_net_sales;

-- Aggregation by product category.
SELECT
    category,
    COUNT(*) AS fact_rows,
    SUM(quantity) AS units,
    ROUND(SUM(net_sales), 2) AS net_sales
FROM vw_sales_model
GROUP BY category
ORDER BY net_sales DESC;

-- Aggregation by customer region and segment.
SELECT
    region,
    segment,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(SUM(net_sales), 2) AS net_sales
FROM vw_sales_model
GROUP BY region, segment
ORDER BY region, segment;

-- Time-based aggregation using the dedicated date dimension.
SELECT
    year_number,
    quarter_number,
    month_number,
    month_name,
    ROUND(SUM(net_sales), 2) AS net_sales
FROM vw_sales_model
GROUP BY
    year_number,
    quarter_number,
    month_number,
    month_name
ORDER BY
    year_number,
    month_number;

-- CTE for ranking products by net sales.
WITH product_sales AS (
    SELECT
        product_id,
        product_name,
        category,
        SUM(net_sales) AS net_sales
    FROM vw_sales_model
    GROUP BY product_id, product_name, category
),
ranked_products AS (
    SELECT
        *,
        RANK() OVER (ORDER BY net_sales DESC) AS sales_rank
    FROM product_sales
)
SELECT
    product_id,
    product_name,
    category,
    ROUND(net_sales, 2) AS net_sales,
    sales_rank
FROM ranked_products
ORDER BY sales_rank, product_id;

-- Relationship quality check: every fact row should resolve to exactly
-- one row in each dimension.
SELECT
    COUNT(*) AS fact_rows,
    COUNT(d.date_key) AS matched_dates,
    COUNT(c.customer_key) AS matched_customers,
    COUNT(p.product_key) AS matched_products
FROM fact_sales f
LEFT JOIN dim_date d
    ON d.date_key = f.date_key
LEFT JOIN dim_customer c
    ON c.customer_key = f.customer_key
LEFT JOIN dim_product p
    ON p.product_key = f.product_key;

-- Failure case: this statement is intentionally prevented by the
-- foreign-key constraint and should not be executed as part of a
-- successful deployment.
-- INSERT INTO fact_sales (
--     date_key, customer_key, product_key, order_id,
--     quantity, unit_price, discount_rate
-- )
-- VALUES (
--     99999999, 1, 1, 'INVALID-FK', 1, 100.00, 0.00
-- );
