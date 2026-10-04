-- GROUP BY: Segmenting and Aggregating Business Data
--
-- PostgreSQL-compatible executable script.
--
-- The schema models a sales analytics workload in which transactions are
-- segmented by region, channel, product category, and customer segment.
-- Constraints protect the source data before GROUP BY queries consume it.

DROP SCHEMA IF EXISTS business_group_by_demo CASCADE;

CREATE SCHEMA business_group_by_demo;

SET search_path TO business_group_by_demo;

CREATE TABLE regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE customer_segments (
    customer_segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category_id BIGINT NOT NULL
        REFERENCES categories(category_id)
);

CREATE TABLE sales (
    sale_id BIGINT PRIMARY KEY,
    sale_date DATE NOT NULL,
    region_id BIGINT NOT NULL
        REFERENCES regions(region_id),
    channel_id BIGINT NOT NULL
        REFERENCES channels(channel_id),
    category_id BIGINT NOT NULL
        REFERENCES categories(category_id),
    product_id BIGINT NOT NULL
        REFERENCES products(product_id),
    customer_segment_id BIGINT NOT NULL
        REFERENCES customer_segments(customer_segment_id),
    units INTEGER NOT NULL CHECK (units > 0),
    revenue NUMERIC(14, 2) NOT NULL CHECK (revenue >= 0),
    cost NUMERIC(14, 2) NOT NULL CHECK (cost >= 0),
    discount NUMERIC(5, 4) NOT NULL CHECK (discount BETWEEN 0 AND 1),
    CHECK (cost <= revenue)
);

INSERT INTO regions (region_name)
VALUES ('North'), ('South'), ('East'), ('West');

INSERT INTO channels (channel_name)
VALUES ('Online'), ('Retail'), ('Partner');

INSERT INTO customer_segments (segment_name)
VALUES ('Consumer'), ('SMB'), ('Enterprise');

INSERT INTO categories (category_name)
VALUES ('Electronics'), ('Office'), ('Software');

INSERT INTO products (product_name, category_id)
SELECT 'Laptop', category_id
FROM categories
WHERE category_name = 'Electronics';

INSERT INTO products (product_name, category_id)
SELECT 'Phone', category_id
FROM categories
WHERE category_name = 'Electronics';

INSERT INTO products (product_name, category_id)
SELECT 'Monitor', category_id
FROM categories
WHERE category_name = 'Office';

INSERT INTO products (product_name, category_id)
SELECT 'Chair', category_id
FROM categories
WHERE category_name = 'Office';

INSERT INTO products (product_name, category_id)
SELECT 'Desk', category_id
FROM categories
WHERE category_name = 'Office';

INSERT INTO products (product_name, category_id)
SELECT 'CRM', category_id
FROM categories
WHERE category_name = 'Software';

INSERT INTO products (product_name, category_id)
SELECT 'Analytics', category_id
FROM categories
WHERE category_name = 'Software';


INSERT INTO sales (
    sale_id,
    sale_date,
    region_id,
    channel_id,
    category_id,
    product_id,
    customer_segment_id,
    units,
    revenue,
    cost,
    discount
)
SELECT
    v.sale_id,
    v.sale_date::DATE,
    r.region_id,
    ch.channel_id,
    c.category_id,
    p.product_id,
    cs.customer_segment_id,
    v.units,
    v.revenue,
    v.cost,
    v.discount
FROM (
    VALUES
        (1001, '2026-01-05', 'North', 'Online', 'Electronics', 'Laptop', 'Enterprise', 4, 4800.00, 3600.00, 0.05),
        (1002, '2026-01-08', 'North', 'Retail', 'Office', 'Monitor', 'SMB', 10, 3000.00, 2100.00, 0.00),
        (1003, '2026-01-12', 'South', 'Online', 'Electronics', 'Phone', 'Consumer', 15, 9000.00, 6300.00, 0.10),
        (1004, '2026-01-15', 'West', 'Partner', 'Software', 'Analytics', 'Enterprise', 3, 7500.00, 2250.00, 0.15),
        (1005, '2026-01-20', 'East', 'Retail', 'Office', 'Chair', 'SMB', 20, 4000.00, 2600.00, 0.05),
        (1006, '2026-02-02', 'North', 'Online', 'Software', 'CRM', 'Enterprise', 5, 10000.00, 3000.00, 0.08),
        (1007, '2026-02-05', 'South', 'Retail', 'Electronics', 'Laptop', 'Consumer', 3, 3600.00, 2700.00, 0.03),
        (1008, '2026-02-11', 'West', 'Online', 'Office', 'Desk', 'SMB', 12, 4800.00, 3000.00, 0.00),
        (1009, '2026-02-17', 'East', 'Partner', 'Software', 'Analytics', 'Enterprise', 4, 10000.00, 3000.00, 0.12),
        (1010, '2026-02-22', 'North', 'Retail', 'Electronics', 'Phone', 'Consumer', 8, 4800.00, 3360.00, 0.07),
        (1011, '2026-03-03', 'South', 'Online', 'Software', 'CRM', 'SMB', 7, 8400.00, 2800.00, 0.05),
        (1012, '2026-03-07', 'West', 'Partner', 'Electronics', 'Laptop', 'Enterprise', 6, 7200.00, 5400.00, 0.10),
        (1013, '2026-03-10', 'East', 'Retail', 'Office', 'Monitor', 'Consumer', 14, 4200.00, 2940.00, 0.04),
        (1014, '2026-03-18', 'North', 'Online', 'Software', 'Analytics', 'Enterprise', 2, 5000.00, 1500.00, 0.20),
        (1015, '2026-03-24', 'South', 'Partner', 'Office', 'Chair', 'SMB', 25, 5000.00, 3250.00, 0.06)
) AS v(
    sale_id,
    sale_date,
    region_name,
    channel_name,
    category_name,
    product_name,
    segment_name,
    units,
    revenue,
    cost,
    discount
)
JOIN regions r
    ON r.region_name = v.region_name
JOIN channels ch
    ON ch.channel_name = v.channel_name
JOIN categories c
    ON c.category_name = v.category_name
JOIN products p
    ON p.product_name = v.product_name
JOIN customer_segments cs
    ON cs.segment_name = v.segment_name;


-- Basic one-dimensional segmentation.
-- Each region becomes one output row and revenue is summed inside that group.

SELECT
    r.region_name,
    COUNT(*) AS transaction_count,
    SUM(s.units) AS total_units,
    SUM(s.revenue) AS total_revenue,
    AVG(s.revenue) AS average_transaction_value,
    MIN(s.revenue) AS minimum_transaction_value,
    MAX(s.revenue) AS maximum_transaction_value,
    SUM(s.revenue - s.cost) AS total_profit,
    ROUND(
        SUM(s.revenue - s.cost) / NULLIF(SUM(s.revenue), 0) * 100,
        2
    ) AS margin_percent
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
ORDER BY total_revenue DESC;


-- Multi-dimensional segmentation.
-- GROUP BY region, channel creates a distinct segment for each combination.

SELECT
    r.region_name,
    ch.channel_name,
    COUNT(*) AS transaction_count,
    SUM(s.units) AS total_units,
    SUM(s.revenue) AS total_revenue,
    SUM(s.revenue - s.cost) AS total_profit
FROM sales s
JOIN regions r ON r.region_id = s.region_id
JOIN channels ch ON ch.channel_id = s.channel_id
GROUP BY
    r.region_name,
    ch.channel_name
ORDER BY
    r.region_name,
    total_revenue DESC;


-- Category and customer-segment intersection.
-- This answers which customer types generate revenue for each category.

SELECT
    c.category_name,
    cs.segment_name,
    COUNT(*) AS transactions,
    SUM(s.revenue) AS revenue,
    SUM(s.revenue - s.cost) AS profit
FROM sales s
JOIN categories c ON c.category_id = s.category_id
JOIN customer_segments cs
    ON cs.customer_segment_id = s.customer_segment_id
GROUP BY
    c.category_name,
    cs.segment_name
ORDER BY
    c.category_name,
    revenue DESC;


-- Conditional aggregation.
-- FILTER keeps all regional rows in the grouping while selectively feeding
-- rows into individual aggregate expressions.

SELECT
    r.region_name,
    SUM(s.revenue) AS total_revenue,
    SUM(s.revenue) FILTER (WHERE ch.channel_name = 'Online')
        AS online_revenue,
    SUM(s.revenue) FILTER (WHERE c.category_name = 'Software')
        AS software_revenue,
    COUNT(*) FILTER (
        WHERE cs.segment_name = 'Enterprise'
    ) AS enterprise_transactions
FROM sales s
JOIN regions r ON r.region_id = s.region_id
JOIN channels ch ON ch.channel_id = s.channel_id
JOIN categories c ON c.category_id = s.category_id
JOIN customer_segments cs
    ON cs.customer_segment_id = s.customer_segment_id
GROUP BY r.region_name
ORDER BY r.region_name;


-- HAVING filters completed groups.
-- WHERE would filter source rows before aggregation; HAVING evaluates the
-- aggregate result itself.

SELECT
    r.region_name,
    COUNT(*) AS transaction_count,
    SUM(s.revenue) AS revenue
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name
HAVING SUM(s.revenue) >= 15000
ORDER BY revenue DESC;


-- Time segmentation by month.
-- date_trunc creates a stable time bucket that can itself be grouped.

SELECT
    DATE_TRUNC('month', s.sale_date)::DATE AS month,
    ch.channel_name,
    COUNT(*) AS transactions,
    SUM(s.units) AS units,
    SUM(s.revenue) AS revenue
FROM sales s
JOIN channels ch ON ch.channel_id = s.channel_id
GROUP BY
    DATE_TRUNC('month', s.sale_date),
    ch.channel_name
ORDER BY
    month,
    ch.channel_name;


-- Quarterly category profitability.

SELECT
    DATE_TRUNC('quarter', s.sale_date)::DATE AS quarter,
    c.category_name,
    SUM(s.revenue) AS revenue,
    SUM(s.revenue - s.cost) AS profit,
    ROUND(
        SUM(s.revenue - s.cost) / NULLIF(SUM(s.revenue), 0) * 100,
        2
    ) AS margin_percent
FROM sales s
JOIN categories c ON c.category_id = s.category_id
GROUP BY
    DATE_TRUNC('quarter', s.sale_date),
    c.category_name
ORDER BY
    quarter,
    profit DESC;


-- Distinct-count segmentation.
-- COUNT(DISTINCT ...) measures the number of unique products represented
-- within each customer segment rather than the number of transactions.

SELECT
    cs.segment_name,
    COUNT(*) AS transactions,
    COUNT(DISTINCT s.product_id) AS distinct_products,
    SUM(s.revenue) AS revenue
FROM sales s
JOIN customer_segments cs
    ON cs.customer_segment_id = s.customer_segment_id
GROUP BY cs.segment_name
ORDER BY revenue DESC;


-- A reusable view for regional performance.

CREATE VIEW regional_performance AS
SELECT
    r.region_name,
    COUNT(*) AS transactions,
    SUM(s.units) AS units,
    SUM(s.revenue) AS revenue,
    SUM(s.revenue - s.cost) AS profit,
    ROUND(
        SUM(s.revenue - s.cost) / NULLIF(SUM(s.revenue), 0) * 100,
        2
    ) AS margin_percent
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY r.region_name;


SELECT *
FROM regional_performance
ORDER BY revenue DESC;


-- Common Table Expression for ranking business segments.
-- Aggregation happens first; ranking then operates on the grouped result.

WITH category_profit AS (
    SELECT
        c.category_name,
        SUM(s.revenue) AS revenue,
        SUM(s.revenue - s.cost) AS profit
    FROM sales s
    JOIN categories c ON c.category_id = s.category_id
    GROUP BY c.category_name
)
SELECT
    category_name,
    revenue,
    profit,
    RANK() OVER (ORDER BY profit DESC) AS profit_rank
FROM category_profit
ORDER BY profit_rank;


-- GROUPING SETS can calculate multiple business aggregation levels in one
-- statement: regional totals, category totals, and the grand total.

SELECT
    r.region_name,
    c.category_name,
    SUM(s.revenue) AS revenue
FROM sales s
JOIN regions r ON r.region_id = s.region_id
JOIN categories c ON c.category_id = s.category_id
GROUP BY GROUPING SETS (
    (r.region_name),
    (c.category_name),
    ()
)
ORDER BY
    r.region_name NULLS LAST,
    c.category_name NULLS LAST;


-- ROLLUP produces hierarchical subtotals.
-- The grouping flag distinguishes a real NULL dimension from a subtotal.

SELECT
    r.region_name,
    ch.channel_name,
    SUM(s.revenue) AS revenue,
    GROUPING(r.region_name) AS region_subtotal,
    GROUPING(ch.channel_name) AS channel_subtotal
FROM sales s
JOIN regions r ON r.region_id = s.region_id
JOIN channels ch ON ch.channel_id = s.channel_id
GROUP BY ROLLUP (
    r.region_name,
    ch.channel_name
)
ORDER BY
    r.region_name NULLS LAST,
    ch.channel_name NULLS LAST;


-- Performance indexes.
-- These indexes support common filtering and join paths. PostgreSQL still
-- evaluates the complete query plan and may choose sequential scans when
-- the table is small or a scan is cheaper.

CREATE INDEX idx_sales_sale_date
    ON sales (sale_date);

CREATE INDEX idx_sales_region_channel
    ON sales (region_id, channel_id);

CREATE INDEX idx_sales_category_segment
    ON sales (category_id, customer_segment_id);


-- Transactional integrity demonstration.
-- The invalid INSERT is intentionally wrapped in a transaction and rolled
-- back. PostgreSQL rejects it because cost > revenue violates the CHECK
-- constraint.

BEGIN;

INSERT INTO sales (
    sale_id,
    sale_date,
    region_id,
    channel_id,
    category_id,
    product_id,
    customer_segment_id,
    units,
    revenue,
    cost,
    discount
)
VALUES (
    9999,
    DATE '2026-04-01',
    (SELECT region_id FROM regions WHERE region_name = 'North'),
    (SELECT channel_id FROM channels WHERE channel_name = 'Online'),
    (SELECT category_id FROM categories WHERE category_name = 'Software'),
    (SELECT product_id FROM products WHERE product_name = 'CRM'),
    (SELECT customer_segment_id
     FROM customer_segments
     WHERE segment_name = 'Enterprise'),
    1,
    100.00,
    125.00,
    0.05
);

ROLLBACK;


-- Final integrity query.
-- The result should contain zero rows because the constraints prevent the
-- invalid transaction from becoming persistent data.

SELECT
    sale_id,
    revenue,
    cost
FROM sales
WHERE cost > revenue;


-- A deliberately useful aggregate validation query.
-- It verifies that the sum of regional revenue equals the overall revenue.

WITH regional_totals AS (
    SELECT
        region_id,
        SUM(revenue) AS region_revenue
    FROM sales
    GROUP BY region_id
),
overall_total AS (
    SELECT SUM(revenue) AS overall_revenue
    FROM sales
)
SELECT
    (
        SELECT SUM(region_revenue)
        FROM regional_totals
    ) AS revenue_from_regions,
    overall_revenue,
    (
        SELECT SUM(region_revenue)
        FROM regional_totals
    ) = overall_revenue AS aggregation_reconciles
FROM overall_total;
