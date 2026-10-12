/*
 * SQL Analytics Project: Retail Business Performance
 *
 * PostgreSQL 15+.
 *
 * The model separates transaction facts from customer and product dimensions.
 * Returns are represented as order-level return flags for this learning dataset.
 * In production, partial returns should use a separate return-line fact table.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS retail_analytics;
SET search_path TO retail_analytics, public;

DROP VIEW IF EXISTS customer_lifetime_metrics CASCADE;
DROP VIEW IF EXISTS monthly_sales_metrics CASCADE;
DROP VIEW IF EXISTS regional_sales_metrics CASCADE;
DROP VIEW IF EXISTS category_profitability CASCADE;
DROP VIEW IF EXISTS order_line_metrics CASCADE;

DROP TABLE IF EXISTS retail_orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    customer_segment TEXT NOT NULL DEFAULT 'Unclassified'
        CHECK (customer_segment IN (
            'Unclassified', 'Occasional', 'Regular', 'High Value'
        )),
    signup_date DATE NOT NULL,
    home_region TEXT NOT NULL
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    list_price NUMERIC(12,2) NOT NULL CHECK (list_price >= 0),
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (length(trim(product_name)) > 0),
    CHECK (length(trim(category)) > 0)
);

CREATE TABLE retail_orders (
    order_id TEXT PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    region TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
    discount_rate NUMERIC(5,4) NOT NULL DEFAULT 0
        CHECK (discount_rate BETWEEN 0 AND 1),
    payment_method TEXT NOT NULL
        CHECK (payment_method IN (
            'Card', 'UPI', 'Cash', 'Bank Transfer', 'Wallet'
        )),
    returned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_date
    ON retail_orders (order_date);

CREATE INDEX idx_orders_region_date
    ON retail_orders (region, order_date);

CREATE INDEX idx_orders_customer_date
    ON retail_orders (customer_id, order_date);

CREATE INDEX idx_orders_product_date
    ON retail_orders (product_id, order_date);

INSERT INTO customers (
    customer_id, customer_name, customer_segment, signup_date, home_region
) VALUES
    ('C-101', 'Aarav Sharma', 'Unclassified', '2024-11-15', 'North'),
    ('C-102', 'Meera Iyer', 'Unclassified', '2024-12-03', 'South'),
    ('C-103', 'Kabir Das', 'Unclassified', '2025-01-10', 'East'),
    ('C-104', 'Ananya Rao', 'Unclassified', '2025-01-21', 'West'),
    ('C-105', 'Ishaan Verma', 'Unclassified', '2025-02-05', 'Central'),
    ('C-106', 'Sara Khan', 'Unclassified', '2025-02-12', 'North'),
    ('C-107', 'Rohan Patel', 'Unclassified', '2025-03-01', 'East'),
    ('C-108', 'Diya Nair', 'Unclassified', '2025-03-17', 'West'),
    ('C-109', 'Arjun Mehta', 'Unclassified', '2025-04-04', 'South'),
    ('C-110', 'Tara Singh', 'Unclassified', '2025-04-18', 'Central');

INSERT INTO products (
    product_id, product_name, category, list_price, unit_cost
) VALUES
    ('P-001', 'Laptop', 'Electronics', 850.00, 610.00),
    ('P-002', 'Monitor', 'Electronics', 260.00, 175.00),
    ('P-003', 'Headphones', 'Electronics', 95.00, 48.00),
    ('P-004', 'Office Chair', 'Furniture', 190.00, 118.00),
    ('P-005', 'Desk', 'Furniture', 320.00, 220.00),
    ('P-006', 'Notebook Pack', 'Stationery', 12.00, 4.00),
    ('P-007', 'Printer Paper', 'Stationery', 8.00, 3.20),
    ('P-008', 'Backpack', 'Accessories', 55.00, 24.00),
    ('P-009', 'USB Hub', 'Accessories', 28.00, 11.00);

INSERT INTO retail_orders (
    order_id, order_date, customer_id, product_id, region, quantity,
    unit_price, unit_cost, discount_rate, payment_method, returned
) VALUES
    ('ORD-1001', '2025-01-05', 'C-101', 'P-001', 'North',
        2, 850, 610, 0.05, 'Card', FALSE),
    ('ORD-1002', '2025-01-12', 'C-102', 'P-004', 'South',
        3, 190, 118, 0.10, 'UPI', FALSE),
    ('ORD-1003', '2025-02-03', 'C-101', 'P-002', 'North',
        4, 260, 175, 0.00, 'Card', FALSE),
    ('ORD-1004', '2025-02-18', 'C-103', 'P-006', 'East',
        20, 12, 4, 0.15, 'Cash', FALSE),
    ('ORD-1005', '2025-03-01', 'C-104', 'P-005', 'West',
        1, 320, 220, 0.05, 'Bank Transfer', TRUE),
    ('ORD-1006', '2025-03-20', 'C-102', 'P-001', 'South',
        1, 850, 610, 0.00, 'Card', FALSE),
    ('ORD-1007', '2025-04-07', 'C-105', 'P-008', 'Central',
        5, 55, 24, 0.10, 'Wallet', FALSE),
    ('ORD-1008', '2025-04-22', 'C-106', 'P-001', 'North',
        15, 850, 610, 0.00, 'Card', FALSE),
    ('ORD-1009', '2025-05-08', 'C-107', 'P-004', 'East',
        2, 190, 118, 0.20, 'UPI', FALSE),
    ('ORD-1010', '2025-05-18', 'C-101', 'P-002', 'North',
        3, 260, 175, 0.05, 'Card', FALSE),
    ('ORD-1011', '2025-06-11', 'C-108', 'P-009', 'West',
        10, 28, 11, 0.10, 'Cash', FALSE),
    ('ORD-1012', '2025-06-21', 'C-109', 'P-005', 'South',
        2, 320, 220, 0.00, 'UPI', FALSE),
    ('ORD-1013', '2025-07-02', 'C-103', 'P-003', 'East',
        4, 95, 48, 0.05, 'Wallet', FALSE),
    ('ORD-1014', '2025-07-17', 'C-110', 'P-006', 'Central',
        25, 12, 4, 0.20, 'Cash', FALSE),
    ('ORD-1015', '2025-08-09', 'C-102', 'P-001', 'South',
        2, 850, 610, 0.10, 'Card', FALSE),
    ('ORD-1016', '2025-08-27', 'C-104', 'P-008', 'West',
        3, 55, 24, 0.00, 'UPI', FALSE),
    ('ORD-1017', '2025-09-06', 'C-106', 'P-002', 'North',
        5, 260, 175, 0.10, 'Card', FALSE),
    ('ORD-1018', '2025-09-19', 'C-107', 'P-005', 'East',
        2, 320, 220, 0.15, 'Bank Transfer', FALSE),
    ('ORD-1019', '2025-10-05', 'C-101', 'P-001', 'North',
        1, 850, 610, 0.00, 'Card', FALSE),
    ('ORD-1020', '2025-10-23', 'C-105', 'P-009', 'Central',
        8, 28, 11, 0.05, 'UPI', FALSE),
    ('ORD-1021', '2025-11-04', 'C-108', 'P-001', 'West',
        2, 900, 610, 0.05, 'Card', FALSE),
    ('ORD-1022', '2025-11-15', 'C-109', 'P-004', 'South',
        4, 200, 118, 0.10, 'UPI', FALSE),
    ('ORD-1023', '2025-12-02', 'C-106', 'P-001', 'North',
        3, 900, 610, 0.00, 'Card', FALSE),
    ('ORD-1024', '2025-12-21', 'C-103', 'P-007', 'East',
        30, 8, 3.20, 0.15, 'Cash', FALSE);

COMMIT;

SET search_path TO retail_analytics, public;

CREATE VIEW order_line_metrics AS
SELECT
    o.order_id,
    o.order_date,
    date_trunc('month', o.order_date)::date AS sales_month,
    o.customer_id,
    c.customer_name,
    o.product_id,
    p.product_name,
    p.category,
    o.region,
    o.quantity,
    o.unit_price,
    o.unit_cost,
    o.discount_rate,
    o.payment_method,
    o.returned,
    o.quantity * o.unit_price AS gross_sales,
    o.quantity * o.unit_price * o.discount_rate AS discount_amount,
    CASE
        WHEN o.returned THEN 0::numeric
        ELSE o.quantity * o.unit_price * (1 - o.discount_rate)
    END AS recognized_revenue,
    CASE
        WHEN o.returned THEN 0::numeric
        ELSE o.quantity * o.unit_cost
    END AS recognized_cost,
    CASE
        WHEN o.returned THEN 0::numeric
        ELSE o.quantity * (
            o.unit_price * (1 - o.discount_rate) - o.unit_cost
        )
    END AS contribution_profit
FROM retail_orders AS o
JOIN customers AS c USING (customer_id)
JOIN products AS p USING (product_id);

CREATE VIEW regional_sales_metrics AS
SELECT
    region,
    COUNT(*) AS transaction_count,
    COUNT(*) FILTER (WHERE returned) AS returned_transactions,
    SUM(gross_sales) AS gross_sales,
    SUM(discount_amount) AS discount_amount,
    SUM(recognized_revenue) AS recognized_revenue,
    SUM(recognized_cost) AS recognized_cost,
    SUM(contribution_profit) AS contribution_profit,
    ROUND(
        SUM(contribution_profit) / NULLIF(SUM(recognized_revenue), 0),
        4
    ) AS profit_margin,
    ROUND(AVG(recognized_revenue), 2) AS average_revenue_per_transaction
FROM order_line_metrics
GROUP BY region;

CREATE VIEW monthly_sales_metrics AS
SELECT
    sales_month,
    COUNT(*) AS transaction_count,
    SUM(recognized_revenue) AS recognized_revenue,
    SUM(contribution_profit) AS contribution_profit,
    ROUND(
        SUM(contribution_profit) / NULLIF(SUM(recognized_revenue), 0),
        4
    ) AS profit_margin
FROM order_line_metrics
GROUP BY sales_month;

CREATE VIEW category_profitability AS
SELECT
    category,
    COUNT(*) AS transaction_count,
    SUM(quantity) FILTER (WHERE NOT returned) AS units_sold,
    SUM(recognized_revenue) AS recognized_revenue,
    SUM(recognized_cost) AS recognized_cost,
    SUM(contribution_profit) AS contribution_profit,
    ROUND(
        SUM(contribution_profit) / NULLIF(SUM(recognized_revenue), 0),
        4
    ) AS profit_margin
FROM order_line_metrics
GROUP BY category;

CREATE VIEW customer_lifetime_metrics AS
SELECT
    customer_id,
    customer_name,
    MIN(order_date) AS first_purchase_date,
    MAX(order_date) AS last_purchase_date,
    COUNT(*) AS transaction_count,
    COUNT(*) FILTER (WHERE returned) AS returned_transactions,
    SUM(recognized_revenue) AS lifetime_revenue,
    SUM(contribution_profit) AS lifetime_profit,
    COUNT(DISTINCT product_id) FILTER (WHERE NOT returned)
        AS distinct_products_purchased,
    CASE
        WHEN SUM(recognized_revenue) >= 1500 THEN 'High Value'
        WHEN SUM(recognized_revenue) >= 400 THEN 'Regular'
        ELSE 'Occasional'
    END AS derived_segment
FROM order_line_metrics
GROUP BY customer_id, customer_name;

-- Overall business scorecard.
SELECT
    COUNT(*) AS transactions,
    SUM(gross_sales) AS gross_sales,
    SUM(discount_amount) AS discounts,
    SUM(recognized_revenue) AS revenue,
    SUM(recognized_cost) AS cost,
    SUM(contribution_profit) AS profit,
    ROUND(
        SUM(contribution_profit) / NULLIF(SUM(recognized_revenue), 0),
        4
    ) AS profit_margin,
    ROUND(AVG(recognized_revenue), 2) AS average_revenue_per_transaction
FROM order_line_metrics;

-- Regional comparison ranks markets by revenue and profitability.
SELECT
    region,
    transaction_count,
    recognized_revenue,
    contribution_profit,
    profit_margin,
    DENSE_RANK() OVER (
        ORDER BY recognized_revenue DESC
    ) AS revenue_rank
FROM regional_sales_metrics
ORDER BY revenue_rank, region;

-- Product category contribution helps distinguish volume from profitability.
SELECT *
FROM category_profitability
ORDER BY contribution_profit DESC, category;

-- Monthly movement and a lag-based comparison reveal growth or decline.
WITH month_comparison AS (
    SELECT
        sales_month,
        recognized_revenue,
        contribution_profit,
        LAG(recognized_revenue) OVER (
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_sales_metrics
)
SELECT
    sales_month,
    recognized_revenue,
    previous_month_revenue,
    recognized_revenue - previous_month_revenue AS revenue_change,
    ROUND(
        (recognized_revenue - previous_month_revenue)
        / NULLIF(previous_month_revenue, 0),
        4
    ) AS revenue_growth_rate,
    contribution_profit
FROM month_comparison
ORDER BY sales_month;

-- A rolling average is a baseline, not a seasonality-aware forecast.
SELECT
    sales_month,
    recognized_revenue,
    ROUND(
        AVG(recognized_revenue) OVER (
            ORDER BY sales_month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS three_month_moving_average
FROM monthly_sales_metrics
ORDER BY sales_month;

-- Discount bands help identify whether deeper discounts coincide with
-- lower contribution margins. Correlation alone does not prove causation.
WITH discount_bands AS (
    SELECT
        CASE
            WHEN discount_rate = 0 THEN 'No discount'
            WHEN discount_rate <= 0.05 THEN 'Up to 5%'
            WHEN discount_rate <= 0.10 THEN '6% to 10%'
            WHEN discount_rate <= 0.15 THEN '11% to 15%'
            ELSE 'Above 15%'
        END AS discount_band,
        recognized_revenue,
        contribution_profit,
        returned
    FROM order_line_metrics
)
SELECT
    discount_band,
    COUNT(*) AS transactions,
    SUM(recognized_revenue) AS revenue,
    SUM(contribution_profit) AS profit,
    ROUND(
        SUM(contribution_profit)
        / NULLIF(SUM(recognized_revenue), 0),
        4
    ) AS profit_margin,
    COUNT(*) FILTER (WHERE returned) AS returned_transactions
FROM discount_bands
GROUP BY discount_band
ORDER BY MIN(
    CASE discount_band
        WHEN 'No discount' THEN 1
        WHEN 'Up to 5%' THEN 2
        WHEN '6% to 10%' THEN 3
        WHEN '11% to 15%' THEN 4
        ELSE 5
    END
);

-- Customer value and recency support targeted retention analysis.
SELECT
    customer_id,
    customer_name,
    first_purchase_date,
    last_purchase_date,
    transaction_count,
    lifetime_revenue,
    lifetime_profit,
    derived_segment,
    CURRENT_DATE - last_purchase_date AS days_since_last_purchase
FROM customer_lifetime_metrics
ORDER BY lifetime_revenue DESC;

-- Cohort retention counts customers active in each month after their first
-- purchase. Month zero is the acquisition month.
WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(date_trunc('month', order_date)::date) AS cohort_month
    FROM retail_orders
    GROUP BY customer_id
),
customer_activity AS (
    SELECT DISTINCT
        customer_id,
        date_trunc('month', order_date)::date AS activity_month
    FROM retail_orders
    WHERE NOT returned
),
cohort_activity AS (
    SELECT
        f.cohort_month,
        a.activity_month,
        (
            EXTRACT(YEAR FROM age(a.activity_month, f.cohort_month)) * 12
            + EXTRACT(MONTH FROM age(a.activity_month, f.cohort_month))
        )::integer AS months_since_acquisition,
        COUNT(DISTINCT a.customer_id) AS active_customers
    FROM first_purchase AS f
    JOIN customer_activity AS a USING (customer_id)
    WHERE a.activity_month >= f.cohort_month
    GROUP BY f.cohort_month, a.activity_month
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    ca.activity_month,
    ca.months_since_acquisition,
    cs.cohort_customers,
    ca.active_customers,
    ROUND(
        ca.active_customers::numeric / NULLIF(cs.cohort_customers, 0),
        4
    ) AS retention_rate
FROM cohort_activity AS ca
JOIN cohort_sizes AS cs USING (cohort_month)
ORDER BY ca.cohort_month, ca.months_since_acquisition;

-- The IQR rule identifies unusual order values for investigation.
WITH revenue_distribution AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        recognized_revenue,
        percentile_cont(0.25) WITHIN GROUP (
            ORDER BY recognized_revenue
        ) OVER () AS q1,
        percentile_cont(0.75) WITHIN GROUP (
            ORDER BY recognized_revenue
        ) OVER () AS q3
    FROM order_line_metrics
)
SELECT
    order_id,
    customer_id,
    order_date,
    recognized_revenue,
    q1,
    q3,
    q3 + 1.5 * (q3 - q1) AS upper_iqr_limit
FROM revenue_distribution
WHERE recognized_revenue > q3 + 1.5 * (q3 - q1)
ORDER BY recognized_revenue DESC;

-- A data-quality query exposes impossible discount and price combinations
-- if constraints were disabled or data was imported outside this schema.
SELECT
    order_id,
    quantity,
    unit_price,
    unit_cost,
    discount_rate
FROM retail_orders
WHERE quantity <= 0
   OR unit_price < 0
   OR unit_cost < 0
   OR discount_rate < 0
   OR discount_rate > 1;

-- Return treatment can materially affect reported profitability.
SELECT
    returned,
    COUNT(*) AS transactions,
    SUM(gross_sales) AS gross_sales,
    SUM(recognized_revenue) AS recognized_revenue,
    SUM(contribution_profit) AS contribution_profit
FROM order_line_metrics
GROUP BY returned
ORDER BY returned;

-- Refresh customer segments in one transaction so a failure cannot leave
-- only part of the dimension updated.
BEGIN;

UPDATE customers AS c
SET customer_segment = m.derived_segment
FROM customer_lifetime_metrics AS m
WHERE c.customer_id = m.customer_id;

COMMIT;

-- The updated classifications are visible in the customer dimension.
SELECT customer_id, customer_name, customer_segment
FROM customers
ORDER BY customer_segment, customer_name;

-- Integrity failure demonstration: the transaction is rolled back after
-- attempting to insert a duplicate primary key. Run separately if desired.
-- BEGIN;
-- INSERT INTO retail_orders (
--     order_id, order_date, customer_id, product_id, region, quantity,
--     unit_price, unit_cost, discount_rate, payment_method, returned
-- ) VALUES (
--     'ORD-1001', '2025-12-31', 'C-101', 'P-001', 'North',
--     1, 850, 610, 0, 'Card', FALSE
-- );
-- ROLLBACK;
