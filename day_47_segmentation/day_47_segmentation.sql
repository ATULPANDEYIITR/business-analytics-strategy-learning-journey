DROP SCHEMA IF EXISTS customer_segmentation CASCADE;
CREATE SCHEMA customer_segmentation;
SET search_path TO customer_segmentation;

-- Customer segmentation uses customer attributes such as age, income,
-- loyalty tier, acquisition channel, and preferred category.
CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 18),
    annual_income NUMERIC(14,2) NOT NULL CHECK (annual_income >= 0),
    loyalty_tier VARCHAR(20) NOT NULL
        CHECK (loyalty_tier IN ('SILVER', 'GOLD', 'PLATINUM')),
    acquisition_channel VARCHAR(30) NOT NULL,
    preferred_category VARCHAR(50) NOT NULL
);

-- Geographic segmentation is represented separately so geography is not
-- confused with demographic or behavioral attributes.
CREATE TABLE geographic_locations (
    location_id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id)
        ON DELETE CASCADE,
    country VARCHAR(80) NOT NULL,
    region VARCHAR(80) NOT NULL,
    city VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    UNIQUE (customer_id)
);

-- Product segmentation focuses on product characteristics and economics.
CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    product_family VARCHAR(80) NOT NULL,
    price NUMERIC(14,2) NOT NULL CHECK (price >= 0),
    margin_rate NUMERIC(5,4) NOT NULL
        CHECK (margin_rate >= 0 AND margin_rate <= 1),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Transactions provide the behavioral evidence from which frequency,
-- recency, monetary value, category diversity, and channel usage can be
-- calculated.
CREATE TABLE purchases (
    purchase_id BIGSERIAL PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    product_id VARCHAR(20) NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    purchase_date DATE NOT NULL,
    sales_channel VARCHAR(30) NOT NULL,
    CHECK (quantity * unit_price >= 0)
);

CREATE INDEX idx_purchases_customer_date
    ON purchases(customer_id, purchase_date DESC);

CREATE INDEX idx_purchases_product
    ON purchases(product_id);

CREATE INDEX idx_customers_region
    ON geographic_locations(region, city);

CREATE INDEX idx_products_category
    ON products(category);

INSERT INTO customers (
    customer_id,
    full_name,
    age,
    annual_income,
    loyalty_tier,
    acquisition_channel,
    preferred_category
) VALUES
('C001', 'Aarav Sharma', 27, 90000, 'GOLD', 'Digital', 'Electronics'),
('C002', 'Meera Kapoor', 42, 145000, 'PLATINUM', 'Referral', 'Home'),
('C003', 'Rohan Das', 31, 42000, 'SILVER', 'Search', 'Household'),
('C004', 'Nisha Rao', 55, 70000, 'GOLD', 'Retail', 'Electronics'),
('C005', 'Kabir Singh', 23, 52000, 'SILVER', 'Social', 'Fashion'),
('C006', 'Ananya Iyer', 38, 160000, 'PLATINUM', 'Referral', 'Electronics');

INSERT INTO geographic_locations (
    customer_id,
    country,
    region,
    city,
    postal_code
) VALUES
('C001', 'India', 'North', 'Delhi', '110001'),
('C002', 'India', 'West', 'Mumbai', '400001'),
('C003', 'India', 'East', 'Kolkata', '700001'),
('C004', 'India', 'South', 'Bengaluru', '560001'),
('C005', 'India', 'North', 'Lucknow', '226001'),
('C006', 'India', 'West', 'Pune', '411001');

INSERT INTO products (
    product_id,
    product_name,
    category,
    product_family,
    price,
    margin_rate
) VALUES
('P001', 'Enterprise Laptop', 'Electronics', 'Premium', 120000, 0.22),
('P002', 'Smart Home Hub', 'Home', 'Household', 18000, 0.35),
('P003', 'Household Essentials Pack', 'Household', 'Essential', 3500, 0.42),
('P004', 'Premium Apparel Set', 'Fashion', 'Lifestyle', 6500, 0.48),
('P005', 'Professional Monitor', 'Electronics', 'Premium', 42000, 0.31);

INSERT INTO purchases (
    customer_id,
    product_id,
    quantity,
    unit_price,
    purchase_date,
    sales_channel
) VALUES
('C001', 'P005', 1, 42000, '2026-10-05', 'ONLINE'),
('C001', 'P003', 3, 3500, '2026-09-20', 'ONLINE'),
('C001', 'P002', 2, 18000, '2026-08-12', 'MOBILE'),
('C002', 'P001', 1, 120000, '2026-10-10', 'ONLINE'),
('C002', 'P002', 3, 18000, '2026-09-11', 'STORE'),
('C002', 'P005', 1, 42000, '2026-07-01', 'ONLINE'),
('C003', 'P003', 4, 3500, '2026-10-01', 'ONLINE'),
('C004', 'P002', 2, 18000, '2026-07-05', 'STORE'),
('C005', 'P004', 1, 6500, '2026-10-03', 'MOBILE'),
('C006', 'P001', 1, 120000, '2026-09-30', 'ONLINE'),
('C006', 'P005', 2, 42000, '2026-08-29', 'ONLINE'),
('C006', 'P002', 1, 18000, '2026-08-15', 'MOBILE');

-- Customer segmentation: compare customers with the portfolio median income.
WITH income_median AS (
    SELECT percentile_cont(0.5)
        WITHIN GROUP (ORDER BY annual_income) AS median_income
    FROM customers
)
SELECT
    c.customer_id,
    c.full_name,
    c.age,
    c.annual_income,
    CASE
        WHEN c.age <= 34
             AND c.annual_income >= m.median_income
            THEN 'YOUNG_HIGH_INCOME'
        WHEN c.age >= 35
             AND c.annual_income > m.median_income
            THEN 'ESTABLISHED_HIGH_INCOME'
        WHEN c.annual_income < m.median_income
            THEN 'VALUE_CONSCIOUS'
        ELSE 'MIDDLE_INCOME'
    END AS customer_segment
FROM customers c
CROSS JOIN income_median m
ORDER BY c.customer_id;

-- Product segmentation: price and margin are product attributes, not
-- customer behaviors.
WITH price_median AS (
    SELECT percentile_cont(0.5)
        WITHIN GROUP (ORDER BY price) AS median_price
    FROM products
)
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.price,
    p.margin_rate,
    CASE
        WHEN p.price > m.median_price
            THEN 'PREMIUM'
        ELSE 'STANDARD'
    END AS price_segment,
    CASE
        WHEN p.margin_rate >= 0.30
            THEN 'HIGH_MARGIN'
        ELSE 'NORMAL_MARGIN'
    END AS margin_segment
FROM products p
CROSS JOIN price_median m
ORDER BY p.price DESC;

-- Geographic segmentation groups customers by actual location.
SELECT
    gl.region,
    gl.city,
    COUNT(*) AS customer_count,
    ROUND(AVG(c.annual_income), 2) AS average_income
FROM geographic_locations gl
JOIN customers c ON c.customer_id = gl.customer_id
GROUP BY gl.region, gl.city
ORDER BY gl.region, gl.city;

-- Behavioral segmentation uses transaction evidence. Recency is calculated
-- against a fixed reference date to make the example reproducible.
WITH behavioral_metrics AS (
    SELECT
        c.customer_id,
        COUNT(p.purchase_id) AS frequency,
        COALESCE(SUM(p.quantity * p.unit_price), 0) AS monetary,
        COALESCE(
            DATE '2026-10-17' - MAX(p.purchase_date),
            999999
        ) AS recency
    FROM customers c
    LEFT JOIN purchases p
        ON p.customer_id = c.customer_id
    GROUP BY c.customer_id
),
thresholds AS (
    SELECT
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY frequency) AS frequency_median,
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY monetary) AS monetary_median
    FROM behavioral_metrics
)
SELECT
    b.customer_id,
    b.frequency,
    b.monetary,
    b.recency,
    CASE
        WHEN b.frequency >= t.frequency_median
             AND b.monetary >= t.monetary_median
            THEN 'LOYAL_HIGH_VALUE'
        WHEN b.recency <= 30
             AND b.frequency < t.frequency_median
            THEN 'RECENT_LOW_FREQUENCY'
        WHEN b.recency > 60
            THEN 'AT_RISK'
        ELSE 'DEVELOPING'
    END AS behavioral_segment
FROM behavioral_metrics b
CROSS JOIN thresholds t
ORDER BY b.customer_id;

-- Connect product performance with behavioral evidence without turning
-- product segmentation into customer segmentation.
SELECT
    p.category,
    COUNT(DISTINCT pu.customer_id) AS unique_customers,
    SUM(pu.quantity) AS units_sold,
    SUM(pu.quantity * pu.unit_price) AS revenue,
    ROUND(
        SUM(pu.quantity * pu.unit_price * p.margin_rate),
        2
    ) AS estimated_gross_margin
FROM purchases pu
JOIN products p ON p.product_id = pu.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- Behavioral category diversity identifies customers who purchase across
-- multiple product categories rather than merely spending more.
SELECT
    pu.customer_id,
    COUNT(DISTINCT p.category) AS category_count,
    COUNT(DISTINCT pu.sales_channel) AS channel_count,
    SUM(pu.quantity * pu.unit_price) AS monetary_value
FROM purchases pu
JOIN products p ON p.product_id = pu.product_id
GROUP BY pu.customer_id
HAVING COUNT(DISTINCT p.category) >= 2
ORDER BY category_count DESC, monetary_value DESC;

-- This query identifies geographic markets where premium-product demand
-- is concentrated.
SELECT
    gl.region,
    COUNT(*) AS premium_orders,
    SUM(pu.quantity * pu.unit_price) AS premium_revenue
FROM purchases pu
JOIN products p ON p.product_id = pu.product_id
JOIN geographic_locations gl ON gl.customer_id = pu.customer_id
WHERE p.price > (
    SELECT percentile_cont(0.5)
        WITHIN GROUP (ORDER BY price)
    FROM products
)
GROUP BY gl.region
ORDER BY premium_revenue DESC;

-- Database-level transactional validation demonstrates that segmentation
-- should consume trusted relational facts rather than silently accepting
-- orphaned or invalid transactions.
BEGIN;

INSERT INTO purchases (
    customer_id,
    product_id,
    quantity,
    unit_price,
    purchase_date,
    sales_channel
)
VALUES (
    'C001',
    'P003',
    2,
    3500,
    '2026-10-16',
    'MOBILE'
);

COMMIT;

-- The foreign key prevents an unknown customer from entering the behavioral
-- dataset. The following statement is intentionally commented out because
-- it would fail with a foreign-key violation.
-- INSERT INTO purchases (
--     customer_id, product_id, quantity, unit_price, purchase_date, sales_channel
-- ) VALUES ('UNKNOWN', 'P001', 1, 120000, '2026-10-17', 'ONLINE');

-- Product-level contribution by customer segment connects two distinct
-- dimensions: customer attributes remain separate from product economics.
WITH customer_segments AS (
    SELECT
        c.customer_id,
        CASE
            WHEN c.age <= 34 AND c.annual_income >=
                (SELECT percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY annual_income)
                 FROM customers)
                THEN 'YOUNG_HIGH_INCOME'
            WHEN c.age >= 35 AND c.annual_income >
                (SELECT percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY annual_income)
                 FROM customers)
                THEN 'ESTABLISHED_HIGH_INCOME'
            WHEN c.annual_income <
                (SELECT percentile_cont(0.5)
                    WITHIN GROUP (ORDER BY annual_income)
                 FROM customers)
                THEN 'VALUE_CONSCIOUS'
            ELSE 'MIDDLE_INCOME'
        END AS customer_segment
    FROM customers c
)
SELECT
    cs.customer_segment,
    p.category,
    SUM(pu.quantity * pu.unit_price) AS revenue
FROM purchases pu
JOIN customer_segments cs
    ON cs.customer_id = pu.customer_id
JOIN products p
    ON p.product_id = pu.product_id
GROUP BY cs.customer_segment, p.category
ORDER BY cs.customer_segment, revenue DESC;
