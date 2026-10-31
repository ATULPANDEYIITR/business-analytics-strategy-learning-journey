DROP SCHEMA IF EXISTS business_analytics CASCADE;
CREATE SCHEMA business_analytics;
SET search_path = business_analytics;

CREATE TABLE sales_orders (
    order_id            text PRIMARY KEY,
    order_date          date NOT NULL,
    region              text NOT NULL,
    salesperson         text NOT NULL,
    customer            text NOT NULL,
    product             text NOT NULL,
    units               integer NOT NULL CHECK (units > 0),
    unit_price          numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    discount_rate       numeric(5,4) NOT NULL
                        CHECK (discount_rate >= 0 AND discount_rate <= 1),
    cost_per_unit       numeric(12,2) NOT NULL CHECK (cost_per_unit >= 0),
    created_at          timestamptz NOT NULL DEFAULT now(),
    CHECK (cost_per_unit <= unit_price)
);

CREATE INDEX idx_sales_orders_date
    ON sales_orders(order_date);

CREATE INDEX idx_sales_orders_region_product
    ON sales_orders(region, product);

CREATE INDEX idx_sales_orders_customer
    ON sales_orders(customer);

CREATE TABLE data_quality_events (
    event_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id            text,
    event_type          text NOT NULL,
    event_message       text NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION validate_sales_order()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.units <= 0 THEN
        RAISE EXCEPTION 'Units must be positive for order %', NEW.order_id;
    END IF;

    IF NEW.discount_rate < 0 OR NEW.discount_rate > 1 THEN
        RAISE EXCEPTION 'Discount rate must be between 0 and 1';
    END IF;

    IF NEW.cost_per_unit > NEW.unit_price THEN
        RAISE EXCEPTION
            'Cost per unit cannot exceed unit price for order %',
            NEW.order_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sales_order
BEFORE INSERT OR UPDATE ON sales_orders
FOR EACH ROW
EXECUTE FUNCTION validate_sales_order();

CREATE OR REPLACE FUNCTION net_sales(
    p_units integer,
    p_unit_price numeric,
    p_discount_rate numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT ROUND(
        p_units * p_unit_price * (1 - p_discount_rate),
        2
    );
$$;

CREATE OR REPLACE FUNCTION order_profit(
    p_units integer,
    p_unit_price numeric,
    p_discount_rate numeric,
    p_cost_per_unit numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT ROUND(
        net_sales(p_units, p_unit_price, p_discount_rate)
        - p_units * p_cost_per_unit,
        2
    );
$$;

INSERT INTO sales_orders
(order_id, order_date, region, salesperson, customer, product,
 units, unit_price, discount_rate, cost_per_unit)
VALUES
('O1001', '2026-01-05', 'North', 'Asha', 'Acme', 'Analytics', 12, 850, .05, 510),
('O1002', '2026-01-09', 'South', 'Ravi', 'Beta', 'Automation', 8, 1200, .10, 720),
('O1003', '2026-01-15', 'North', 'Asha', 'Delta', 'Analytics', 5, 850, 0, 510),
('O1004', '2026-02-03', 'West', 'Neha', 'Acme', 'Security', 15, 700, .08, 420),
('O1005', '2026-02-11', 'South', 'Ravi', 'Gamma', 'Analytics', 20, 850, .12, 510),
('O1006', '2026-02-19', 'West', 'Neha', 'Delta', 'Automation', 7, 1200, .05, 720),
('O1007', '2026-03-02', 'North', 'Asha', 'Beta', 'Security', 10, 700, .03, 420),
('O1008', '2026-03-12', 'South', 'Ravi', 'Acme', 'Analytics', 16, 850, .07, 510),
('O1009', '2026-03-20', 'West', 'Neha', 'Gamma', 'Security', 6, 700, .15, 420),
('O1010', '2026-03-25', 'North', 'Asha', 'Delta', 'Automation', 11, 1200, .06, 720);

CREATE VIEW order_metrics AS
SELECT
    order_id,
    order_date,
    region,
    salesperson,
    customer,
    product,
    units,
    unit_price,
    discount_rate,
    cost_per_unit,
    net_sales(units, unit_price, discount_rate) AS net_sales,
    order_profit(
        units,
        unit_price,
        discount_rate,
        cost_per_unit
    ) AS profit,
    ROUND(
        order_profit(
            units,
            unit_price,
            discount_rate,
            cost_per_unit
        ) / NULLIF(
            net_sales(units, unit_price, discount_rate),
            0
        ),
        4
    ) AS margin
FROM sales_orders;

CREATE VIEW regional_performance AS
SELECT
    region,
    COUNT(*) AS orders,
    SUM(units) AS units,
    ROUND(SUM(net_sales), 2) AS sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(SUM(profit) / NULLIF(SUM(net_sales), 0), 4) AS margin
FROM order_metrics
GROUP BY region;

CREATE VIEW product_performance AS
SELECT
    product,
    COUNT(*) AS orders,
    SUM(units) AS units,
    ROUND(SUM(net_sales), 2) AS sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(SUM(profit) / NULLIF(SUM(net_sales), 0), 4) AS margin
FROM order_metrics
GROUP BY product;

CREATE VIEW customer_performance AS
SELECT
    customer,
    COUNT(*) AS orders,
    SUM(units) AS units,
    ROUND(SUM(net_sales), 2) AS sales,
    ROUND(SUM(profit), 2) AS profit,
    ROUND(SUM(profit) / NULLIF(SUM(net_sales), 0), 4) AS margin
FROM order_metrics
GROUP BY customer;

CREATE VIEW customer_segments AS
SELECT
    customer,
    orders,
    units,
    sales,
    profit,
    margin,
    CASE
        WHEN sales >= 15000 AND margin >= .30
            THEN 'High Value'
        WHEN sales >= 10000
            THEN 'Growth'
        WHEN margin < .25
            THEN 'At Risk'
        ELSE 'Standard'
    END AS segment
FROM customer_performance;

-- Core financial KPI query.
SELECT
    COUNT(*) AS orders,
    SUM(units) AS units,
    ROUND(SUM(net_sales), 2) AS total_sales,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(SUM(profit) / NULLIF(SUM(net_sales), 0), 4) AS profit_margin
FROM order_metrics;

-- Regional comparison.
SELECT *
FROM regional_performance
ORDER BY sales DESC;

-- Product profitability.
SELECT *
FROM product_performance
ORDER BY profit DESC;

-- Customer segmentation.
SELECT *
FROM customer_segments
ORDER BY sales DESC;

-- Monthly trend.
SELECT
    date_trunc('month', order_date)::date AS month,
    COUNT(*) AS orders,
    SUM(units) AS units,
    ROUND(SUM(net_sales), 2) AS sales,
    ROUND(SUM(profit), 2) AS profit
FROM order_metrics
GROUP BY 1
ORDER BY 1;

-- Highest-value orders.
SELECT
    order_id,
    customer,
    product,
    net_sales,
    profit,
    margin
FROM order_metrics
ORDER BY net_sales DESC
LIMIT 5;

-- Discount impact: orders receiving at least 10% discount.
SELECT
    order_id,
    customer,
    discount_rate,
    net_sales,
    profit
FROM order_metrics
WHERE discount_rate >= .10
ORDER BY discount_rate DESC, profit;

-- Business-rule validation.
SELECT
    order_id,
    CASE
        WHEN units <= 0 THEN 'Invalid units'
        WHEN discount_rate NOT BETWEEN 0 AND 1 THEN 'Invalid discount'
        WHEN cost_per_unit > unit_price THEN 'Invalid cost'
        WHEN net_sales < 0 THEN 'Negative sales'
        ELSE 'Valid'
    END AS validation_status
FROM sales_orders;

-- CTE for ranking products by profit.
WITH product_ranked AS (
    SELECT
        product,
        SUM(profit) AS total_profit,
        RANK() OVER (ORDER BY SUM(profit) DESC) AS profit_rank
    FROM order_metrics
    GROUP BY product
)
SELECT
    product,
    ROUND(total_profit, 2) AS total_profit,
    profit_rank
FROM product_ranked
ORDER BY profit_rank;

-- Transactional example: insert a valid analytical record and commit it.
BEGIN;

INSERT INTO sales_orders
(order_id, order_date, region, salesperson, customer, product,
 units, unit_price, discount_rate, cost_per_unit)
VALUES
('O1011', '2026-03-29', 'South', 'Ravi', 'Acme',
 'Automation', 4, 1200, .05, 720);

-- The transaction remains valid only if database constraints and trigger
-- validation succeed.
COMMIT;

-- Verify the transaction.
SELECT *
FROM order_metrics
WHERE order_id = 'O1011';
