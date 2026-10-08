DROP SCHEMA IF EXISTS nested_query_lab CASCADE;
CREATE SCHEMA nested_query_lab;
SET search_path TO nested_query_lab;

-- PostgreSQL model for studying scalar, correlated, EXISTS, derived-table,
-- and multi-level analytical subqueries.

CREATE TABLE customers (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    customer_tier TEXT NOT NULL
        CHECK (customer_tier IN ('Standard', 'Silver', 'Gold')),
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    product_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('Completed', 'Cancelled', 'Pending')),
    shipping_region TEXT NOT NULL
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_orders_customer_status
    ON orders(customer_id, status);

CREATE INDEX idx_order_items_product
    ON order_items(product_id);

CREATE INDEX idx_products_category_price
    ON products(category, unit_price);

INSERT INTO customers
    (customer_name, region, customer_tier, signup_date)
VALUES
    ('Aarav Mehta', 'North', 'Gold', '2024-01-12'),
    ('Diya Sharma', 'North', 'Silver', '2024-02-10'),
    ('Kabir Singh', 'West', 'Gold', '2024-03-08'),
    ('Meera Iyer', 'South', 'Standard', '2024-04-15'),
    ('Rohan Gupta', 'West', 'Silver', '2024-05-21'),
    ('Ananya Rao', 'South', 'Gold', '2024-06-18'),
    ('Vikram Joshi', 'East', 'Standard', '2024-07-01'),
    ('Sara Khan', 'East', 'Silver', '2024-08-11');

INSERT INTO products
    (product_name, category, unit_price)
VALUES
    ('Laptop Pro', 'Electronics', 1200.00),
    ('Mechanical Keyboard', 'Electronics', 140.00),
    ('Office Chair', 'Furniture', 350.00),
    ('Monitor 27', 'Electronics', 420.00),
    ('Standing Desk', 'Furniture', 650.00),
    ('USB-C Hub', 'Accessories', 80.00),
    ('Webcam', 'Accessories', 110.00);

INSERT INTO orders
    (order_id, customer_id, order_date, status, shipping_region)
VALUES
    (101, 1, '2025-01-05', 'Completed', 'North'),
    (102, 1, '2025-02-11', 'Completed', 'North'),
    (103, 2, '2025-01-20', 'Completed', 'North'),
    (104, 2, '2025-03-14', 'Completed', 'North'),
    (105, 3, '2025-01-22', 'Completed', 'West'),
    (106, 3, '2025-02-25', 'Completed', 'West'),
    (107, 3, '2025-03-02', 'Completed', 'West'),
    (108, 4, '2025-02-02', 'Completed', 'South'),
    (109, 4, '2025-03-19', 'Cancelled', 'South'),
    (110, 5, '2025-01-18', 'Completed', 'West'),
    (111, 5, '2025-03-21', 'Completed', 'West'),
    (112, 6, '2025-01-27', 'Completed', 'South'),
    (113, 6, '2025-02-28', 'Completed', 'South'),
    (114, 7, '2025-02-08', 'Completed', 'East'),
    (115, 8, '2025-03-04', 'Pending', 'East');

INSERT INTO order_items
    (order_id, product_id, quantity, unit_price)
SELECT
    source.order_id,
    source.product_id,
    source.quantity,
    product.unit_price
FROM (
    VALUES
        (101, 1, 1), (101, 2, 1),
        (102, 4, 1), (102, 6, 2),
        (103, 3, 1), (103, 7, 1),
        (104, 2, 2), (104, 6, 1),
        (105, 1, 1), (105, 6, 1),
        (106, 5, 1), (106, 4, 1),
        (107, 1, 1), (107, 7, 2),
        (108, 3, 1), (108, 6, 2),
        (109, 4, 1),
        (110, 5, 1), (110, 2, 1),
        (111, 3, 2), (111, 7, 1),
        (112, 1, 1), (112, 4, 1),
        (113, 5, 1), (113, 6, 2),
        (114, 2, 1), (114, 7, 1),
        (115, 4, 1)
) AS source(order_id, product_id, quantity)
JOIN products product
    ON product.product_id = source.product_id;

-- Scalar subquery:
-- the inner SELECT produces one benchmark value for the outer WHERE clause.
SELECT
    product_name,
    category,
    unit_price
FROM products
WHERE unit_price > (
    SELECT AVG(unit_price)
    FROM products
)
ORDER BY unit_price DESC;

-- IN subquery:
-- the inner query returns a set of customer IDs. The outer query performs
-- membership testing against that set.
SELECT
    customer_id,
    customer_name,
    region
FROM customers
WHERE customer_id IN (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE status = 'Completed'
)
ORDER BY customer_id;

-- EXISTS:
-- only the existence of a matching row matters. SELECT 1 is conventional
-- because the returned value is not consumed by EXISTS.
SELECT
    customer_id,
    customer_name,
    customer_tier
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    JOIN order_items AS oi
        ON oi.order_id = o.order_id
    JOIN products AS p
        ON p.product_id = oi.product_id
    WHERE o.customer_id = c.customer_id
      AND o.status = 'Completed'
      AND p.category = 'Furniture'
)
ORDER BY customer_id;

-- Correlated scalar subquery:
-- the inner query references c.customer_id from the current outer row.
SELECT
    c.customer_id,
    c.customer_name,
    ROUND(
        (
            SELECT AVG(order_total)
            FROM (
                SELECT
                    o.order_id,
                    o.customer_id,
                    SUM(oi.quantity * oi.unit_price) AS order_total
                FROM orders AS o
                JOIN order_items AS oi
                    ON oi.order_id = o.order_id
                WHERE o.status = 'Completed'
                GROUP BY o.order_id, o.customer_id
            ) AS completed_order_totals
            WHERE completed_order_totals.customer_id = c.customer_id
        ),
        2
    ) AS average_order_value
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS activity
    WHERE activity.customer_id = c.customer_id
      AND activity.status = 'Completed'
)
ORDER BY average_order_value DESC;

-- Derived table:
-- the subquery in FROM produces order-level facts that the outer query
-- aggregates by region.
SELECT
    region,
    COUNT(*) AS completed_order_count,
    ROUND(AVG(order_total), 2) AS average_order_value,
    ROUND(MAX(order_total), 2) AS largest_order
FROM (
    SELECT
        o.order_id,
        c.region,
        SUM(oi.quantity * oi.unit_price) AS order_total
    FROM orders AS o
    JOIN customers AS c
        ON c.customer_id = o.customer_id
    JOIN order_items AS oi
        ON oi.order_id = o.order_id
    WHERE o.status = 'Completed'
    GROUP BY o.order_id, c.region
) AS order_summary
GROUP BY region
ORDER BY average_order_value DESC;

-- Multi-level nested aggregation:
-- order totals are transformed into customer revenue, then the average of
-- customer revenue becomes the benchmark for the outer filter.
SELECT
    customer_name,
    customer_revenue
FROM (
    SELECT
        c.customer_id,
        c.customer_name,
        SUM(oi.quantity * oi.unit_price) AS customer_revenue
    FROM customers AS c
    JOIN orders AS o
        ON o.customer_id = c.customer_id
       AND o.status = 'Completed'
    JOIN order_items AS oi
        ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.customer_name
) AS customer_totals
WHERE customer_revenue > (
    SELECT AVG(customer_revenue)
    FROM (
        SELECT
            o.customer_id,
            SUM(oi.quantity * oi.unit_price) AS customer_revenue
        FROM orders AS o
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        WHERE o.status = 'Completed'
        GROUP BY o.customer_id
    ) AS all_customer_totals
)
ORDER BY customer_revenue DESC;

-- Correlated NOT EXISTS:
-- a product is a category leader when no product in the same category has
-- a higher price.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.unit_price
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM products AS competitor
    WHERE competitor.category = p.category
      AND competitor.unit_price > p.unit_price
)
ORDER BY category, unit_price DESC;

-- HAVING with a nested analytical benchmark:
-- category revenue is calculated once in the inner derived table and compared
-- with the average category revenue in the scalar subquery.
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS category_revenue
FROM products AS p
JOIN order_items AS oi
    ON oi.product_id = p.product_id
JOIN orders AS o
    ON o.order_id = oi.order_id
WHERE o.status = 'Completed'
GROUP BY p.category
HAVING SUM(oi.quantity * oi.unit_price) > (
    SELECT AVG(category_revenue)
    FROM (
        SELECT
            p2.category,
            SUM(oi2.quantity * oi2.unit_price) AS category_revenue
        FROM products AS p2
        JOIN order_items AS oi2
            ON oi2.product_id = p2.product_id
        JOIN orders AS o2
            ON o2.order_id = oi2.order_id
        WHERE o2.status = 'Completed'
        GROUP BY p2.category
    ) AS category_totals
)
ORDER BY category_revenue DESC;

-- NOT EXISTS is preferable to NOT IN when the inner expression can contain
-- NULL values, because NOT IN can become UNKNOWN when NULL participates.
SELECT
    c.customer_id,
    c.customer_name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS completed
    WHERE completed.customer_id = c.customer_id
      AND completed.status = 'Completed'
)
AND NOT EXISTS (
    SELECT 1
    FROM orders AS cancelled
    WHERE cancelled.customer_id = c.customer_id
      AND cancelled.status = 'Cancelled'
)
ORDER BY c.customer_id;

-- Parameterized analytical logic:
-- PostgreSQL clients should bind the category parameter rather than construct
-- SQL through string concatenation. This literal example demonstrates the
-- resulting SQL shape.
PREPARE products_above_category_average(text) AS
SELECT
    product_name,
    category,
    unit_price
FROM products
WHERE category = $1
  AND unit_price > (
      SELECT AVG(unit_price)
      FROM products
      WHERE category = $1
  )
ORDER BY unit_price DESC;

EXECUTE products_above_category_average('Electronics');
DEALLOCATE products_above_category_average;

-- Empty scalar subquery:
-- AVG over an empty set returns NULL. The comparison would therefore be
-- UNKNOWN. COALESCE makes the fallback explicit.
SELECT
    product_name,
    unit_price
FROM products
WHERE unit_price > COALESCE(
    (
        SELECT AVG(unit_price)
        FROM products
        WHERE category = 'Nonexistent'
    ),
    0
)
ORDER BY unit_price DESC
LIMIT 5;

-- A transaction demonstrates that nested queries can also participate in
-- data-validation workflows. The INSERT ... SELECT only creates the order
-- when the referenced customer exists.
BEGIN;

INSERT INTO orders (
    order_id,
    customer_id,
    order_date,
    status,
    shipping_region
)
SELECT
    999,
    customer_id,
    DATE '2025-03-25',
    'Pending',
    region
FROM customers
WHERE customer_id = 1;

COMMIT;

SELECT
    order_id,
    customer_id,
    status
FROM orders
WHERE order_id = 999;

-- Query-plan inspection is important for nested queries because correlated
-- execution can become expensive on large tables. PostgreSQL can reveal scan
-- and index choices through EXPLAIN.
EXPLAIN
SELECT
    c.customer_name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'Completed'
);

-- A correlated subquery that calculates the most expensive product per
-- category. The index on (category, unit_price) gives the optimizer a useful
-- access path as data volume increases.
EXPLAIN
SELECT
    p.product_name,
    p.category,
    p.unit_price
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM products AS p2
    WHERE p2.category = p.category
      AND p2.unit_price > p.unit_price
);
