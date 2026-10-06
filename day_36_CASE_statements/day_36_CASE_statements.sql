-- CASE Statements: Creating Business Logic Using SQL
-- PostgreSQL-compatible executable script.
--
-- CASE is an expression. It derives a value from ordered conditions or
-- exact value matches. It is useful for classification, pricing,
-- conditional aggregation, status mapping, reporting, and policy logic.
--
-- The schema deliberately separates source facts from derived business
-- classifications. This makes it possible to change CASE rules without
-- rewriting the underlying transactional data.

DROP SCHEMA IF EXISTS case_business_logic CASCADE;
CREATE SCHEMA case_business_logic;
SET search_path TO case_business_logic;

CREATE TABLE customers (
    customer_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name     TEXT NOT NULL,
    country_code      CHAR(2) NOT NULL,
    lifetime_value    NUMERIC(14, 2) NOT NULL CHECK (lifetime_value >= 0),
    account_status    TEXT NOT NULL
        CHECK (account_status IN ('active', 'suspended'))
);

CREATE TABLE orders (
    order_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id       BIGINT NOT NULL
        REFERENCES customers(customer_id),
    subtotal          NUMERIC(14, 2) NOT NULL CHECK (subtotal >= 0),
    shipping_amount   NUMERIC(14, 2) NOT NULL CHECK (shipping_amount >= 0),
    payment_status    TEXT NOT NULL
        CHECK (payment_status IN ('paid', 'pending', 'failed', 'refunded')),
    order_status      TEXT NOT NULL
        CHECK (order_status IN ('confirmed', 'cancelled')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_customer
    ON orders(customer_id);

CREATE INDEX idx_orders_payment_status
    ON orders(payment_status);

CREATE INDEX idx_customers_account_status
    ON customers(account_status);

INSERT INTO customers
    (customer_name, country_code, lifetime_value, account_status)
VALUES
    ('Aarav Labs', 'IN', 125000.00, 'active'),
    ('Northwind', 'US', 62000.00, 'active'),
    ('BerlinWorks', 'DE', 18000.00, 'active'),
    ('SmallMart', 'IN', 2400.00, 'active'),
    ('RiskAccount', 'US', 200000.00, 'suspended'),
    ('Tokyo Systems', 'JP', 75000.00, 'active');

INSERT INTO orders
    (customer_id, subtotal, shipping_amount, payment_status, order_status)
VALUES
    (1, 12000.00, 250.00, 'paid', 'confirmed'),
    (2, 7000.00, 200.00, 'paid', 'confirmed'),
    (3, 3000.00, 150.00, 'pending', 'confirmed'),
    (4, 850.00, 80.00, 'failed', 'cancelled'),
    (5, 15000.00, 250.00, 'paid', 'confirmed'),
    (6, 5000.00, 150.00, 'paid', 'confirmed');

-- Searched CASE:
-- Each WHEN is an independent Boolean condition.
-- Branch order is significant because the first true condition wins.
SELECT
    customer_id,
    customer_name,
    lifetime_value,
    account_status,
    CASE
        WHEN account_status = 'suspended' THEN 'RESTRICTED'
        WHEN lifetime_value >= 100000 THEN 'PLATINUM'
        WHEN lifetime_value >= 50000 THEN 'GOLD'
        WHEN lifetime_value >= 10000 THEN 'SILVER'
        ELSE 'STANDARD'
    END AS customer_segment
FROM customers
ORDER BY customer_id;

-- Simple CASE:
-- One expression is compared with multiple possible values.
SELECT
    order_id,
    payment_status,
    CASE payment_status
        WHEN 'paid' THEN 'SETTLED'
        WHEN 'pending' THEN 'AWAITING PAYMENT'
        WHEN 'failed' THEN 'PAYMENT FAILED'
        WHEN 'refunded' THEN 'REFUNDED'
        ELSE 'UNKNOWN PAYMENT STATE'
    END AS payment_label
FROM orders
ORDER BY order_id;

-- CASE can derive a monetary business result.
-- The suspended-account rule is evaluated before the discount tiers.
SELECT
    o.order_id,
    c.customer_name,
    o.subtotal + o.shipping_amount AS gross_amount,
    CASE
        WHEN o.payment_status <> 'paid' THEN 0.00
        WHEN c.account_status = 'suspended' THEN 0.00
        WHEN c.lifetime_value >= 100000
             AND o.subtotal + o.shipping_amount >= 5000
            THEN 0.15
        WHEN c.lifetime_value >= 50000 THEN 0.10
        WHEN o.subtotal + o.shipping_amount >= 10000 THEN 0.08
        WHEN o.subtotal + o.shipping_amount >= 5000 THEN 0.05
        ELSE 0.00
    END AS discount_rate
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
ORDER BY o.order_id;

-- A CASE expression can calculate the final amount directly.
SELECT
    o.order_id,
    c.customer_name,
    ROUND(
        (
            o.subtotal + o.shipping_amount
        ) * (
            1 -
            CASE
                WHEN o.payment_status <> 'paid' THEN 0.00
                WHEN c.account_status = 'suspended' THEN 0.00
                WHEN c.lifetime_value >= 100000
                     AND o.subtotal + o.shipping_amount >= 5000
                    THEN 0.15
                WHEN c.lifetime_value >= 50000 THEN 0.10
                WHEN o.subtotal + o.shipping_amount >= 10000 THEN 0.08
                WHEN o.subtotal + o.shipping_amount >= 5000 THEN 0.05
                ELSE 0.00
            END
        ),
        2
    ) AS net_amount
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
ORDER BY o.order_id;

-- CASE is especially useful for conditional aggregation.
-- SUM(CASE ...) converts qualifying rows into values that can be aggregated.
SELECT
    COUNT(*) AS total_orders,
    COUNT(
        CASE
            WHEN payment_status = 'paid' THEN 1
        END
    ) AS paid_orders,
    COUNT(
        CASE
            WHEN payment_status = 'pending' THEN 1
        END
    ) AS pending_orders,
    COUNT(
        CASE
            WHEN payment_status = 'failed' THEN 1
        END
    ) AS failed_orders,
    SUM(
        CASE
            WHEN payment_status = 'paid'
                THEN subtotal + shipping_amount
            ELSE 0
        END
    ) AS paid_gross_value
FROM orders;

-- Multiple CASE expressions can classify different dimensions without
-- collapsing those dimensions into one generic category.
SELECT
    o.order_id,
    c.customer_name,
    CASE
        WHEN c.account_status = 'suspended' THEN 'RESTRICTED'
        WHEN c.lifetime_value >= 100000 THEN 'PLATINUM'
        WHEN c.lifetime_value >= 50000 THEN 'GOLD'
        WHEN c.lifetime_value >= 10000 THEN 'SILVER'
        ELSE 'STANDARD'
    END AS customer_segment,
    CASE
        WHEN o.order_status = 'cancelled' THEN 'DO NOT SHIP'
        WHEN o.payment_status <> 'paid' THEN 'HOLD'
        WHEN o.subtotal + o.shipping_amount >= 10000 THEN 'URGENT'
        WHEN o.subtotal + o.shipping_amount >= 5000 THEN 'HIGH'
        ELSE 'NORMAL'
    END AS shipping_priority
FROM orders AS o
JOIN customers AS c
    ON c.customer_id = o.customer_id
ORDER BY o.order_id;

-- CASE can normalize categorical data for reporting.
SELECT
    customer_id,
    customer_name,
    country_code,
    CASE
        WHEN country_code IN ('IN', 'JP', 'SG') THEN 'APAC'
        WHEN country_code IN ('DE', 'FR', 'GB') THEN 'EUROPE'
        WHEN country_code IN ('US', 'CA') THEN 'NORTH_AMERICA'
        ELSE 'OTHER'
    END AS reporting_region
FROM customers
ORDER BY customer_id;

-- NULL behavior:
-- When lifetime_value is NULL, "lifetime_value >= 50000" is UNKNOWN,
-- not TRUE. Therefore the ELSE branch is selected unless NULL is tested
-- explicitly.
SELECT
    customer_id,
    customer_name,
    CASE
        WHEN lifetime_value IS NULL THEN 'MISSING VALUE'
        WHEN lifetime_value >= 50000 THEN 'HIGH VALUE'
        ELSE 'STANDARD VALUE'
    END AS null_aware_classification
FROM customers;

-- Demonstrate a view where CASE becomes reusable reporting logic.
CREATE OR REPLACE VIEW customer_business_classification AS
SELECT
    customer_id,
    customer_name,
    country_code,
    lifetime_value,
    account_status,
    CASE
        WHEN account_status = 'suspended' THEN 'RESTRICTED'
        WHEN lifetime_value >= 100000 THEN 'PLATINUM'
        WHEN lifetime_value >= 50000 THEN 'GOLD'
        WHEN lifetime_value >= 10000 THEN 'SILVER'
        ELSE 'STANDARD'
    END AS customer_segment
FROM customers;

SELECT *
FROM customer_business_classification
ORDER BY customer_id;

-- CASE does not replace integrity constraints.
-- The following invalid operation is intentionally commented out because
-- the executable script should complete successfully:
--
-- INSERT INTO orders
--     (customer_id, subtotal, shipping_amount, payment_status, order_status)
-- VALUES
--     (999999, 10.00, 0.00, 'paid', 'confirmed');
--
-- PostgreSQL would reject it through the FOREIGN KEY before a CASE expression
-- could meaningfully classify the resulting row.

-- CASE can also expose data-quality conditions without changing the data.
SELECT
    order_id,
    CASE
        WHEN payment_status = 'paid'
             AND order_status = 'cancelled'
            THEN 'REVIEW: PAID AND CANCELLED'
        WHEN payment_status = 'failed'
             AND order_status = 'confirmed'
            THEN 'REVIEW: FAILED PAYMENT'
        WHEN payment_status = 'pending'
             AND order_status = 'confirmed'
            THEN 'AWAITING PAYMENT'
        WHEN payment_status = 'paid'
             AND order_status = 'confirmed'
            THEN 'READY'
        ELSE 'OTHER'
    END AS operational_state
FROM orders
ORDER BY order_id;

-- Conditional aggregation by customer segment.
WITH classified AS (
    SELECT
        c.customer_id,
        c.customer_name,
        CASE
            WHEN c.account_status = 'suspended' THEN 'RESTRICTED'
            WHEN c.lifetime_value >= 100000 THEN 'PLATINUM'
            WHEN c.lifetime_value >= 50000 THEN 'GOLD'
            WHEN c.lifetime_value >= 10000 THEN 'SILVER'
            ELSE 'STANDARD'
        END AS segment
    FROM customers AS c
)
SELECT
    segment,
    COUNT(*) AS customer_count
FROM classified
GROUP BY segment
ORDER BY
    CASE segment
        WHEN 'PLATINUM' THEN 1
        WHEN 'GOLD' THEN 2
        WHEN 'SILVER' THEN 3
        WHEN 'STANDARD' THEN 4
        WHEN 'RESTRICTED' THEN 5
        ELSE 6
    END;

-- A transaction demonstrates that CASE participates in data-changing
-- workflows, but transactional atomicity comes from BEGIN/COMMIT rather
-- than from CASE itself.
BEGIN;

WITH eligible AS (
    SELECT
        o.order_id,
        CASE
            WHEN o.payment_status = 'paid'
                 AND o.order_status = 'confirmed'
                THEN 'READY_FOR_FULFILLMENT'
            WHEN o.payment_status = 'pending'
                 AND o.order_status = 'confirmed'
                THEN 'PAYMENT_REQUIRED'
            WHEN o.order_status = 'cancelled'
                THEN 'CANCELLED'
            ELSE 'REVIEW'
        END AS fulfillment_state
    FROM orders AS o
)
SELECT *
FROM eligible
ORDER BY order_id;

COMMIT;
