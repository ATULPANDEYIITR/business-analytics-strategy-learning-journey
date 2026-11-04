/*
 * DATA AGGREGATION
 * Grouping, aggregation, conditional aggregation and pivot operations.
 *
 * PostgreSQL 15+
 *
 * Domain: Enterprise sales transaction analytics.
 *
 * Features:
 * - Relational transaction model.
 * - Data validation and integrity.
 * - Grouping and multi-dimensional aggregation.
 * - GROUPING SETS, ROLLUP and CUBE.
 * - FILTER and CASE-based conditional aggregation.
 * - Window-based analytical aggregation.
 * - Pivot and unpivot operations.
 * - Materialized aggregation reporting.
 * - Incremental summary maintenance.
 * - Reconciliation and transaction handling.
 */

DROP SCHEMA IF EXISTS aggregation_lab CASCADE;

CREATE SCHEMA aggregation_lab;

SET search_path TO aggregation_lab, public;

-- ============================================================
-- 1. DOMAIN TABLES
-- ============================================================

CREATE TABLE regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(80) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE product_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL UNIQUE,
    category_id BIGINT NOT NULL
        REFERENCES product_categories(category_id),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE salespeople (
    salesperson_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salesperson_name VARCHAR(120) NOT NULL,
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_reference VARCHAR(60) NOT NULL UNIQUE,
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    salesperson_id BIGINT NOT NULL REFERENCES salespeople(salesperson_id),
    transaction_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14, 2) NOT NULL CHECK (unit_price >= 0),
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('completed', 'pending', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (unit_price * quantity < 1000000000000000)
);

CREATE INDEX idx_transactions_date
    ON transactions(transaction_date);

CREATE INDEX idx_transactions_region_date
    ON transactions(region_id, transaction_date);

CREATE INDEX idx_transactions_product
    ON transactions(product_id);

CREATE INDEX idx_transactions_status_date
    ON transactions(status, transaction_date);

CREATE INDEX idx_transactions_salesperson_date
    ON transactions(salesperson_id, transaction_date);

CREATE INDEX idx_transactions_completed_region
    ON transactions(region_id, product_id)
    WHERE status = 'completed';

-- ============================================================
-- 2. REFERENCE DATA
-- ============================================================

INSERT INTO regions (region_name)
VALUES
    ('North'),
    ('South'),
    ('East'),
    ('West');

INSERT INTO product_categories (category_name)
VALUES
    ('Electronics'),
    ('Furniture');

INSERT INTO products (product_name, category_id)
SELECT
    data.product_name,
    categories.category_id
FROM (
    VALUES
        ('Laptop', 'Electronics'),
        ('Phone', 'Electronics'),
        ('Chair', 'Furniture'),
        ('Table', 'Furniture')
) AS data(product_name, category_name)
JOIN product_categories categories
    ON categories.category_name = data.category_name;

INSERT INTO salespeople (salesperson_name, region_id)
SELECT
    data.salesperson_name,
    regions.region_id
FROM (
    VALUES
        ('Asha', 'North'),
        ('Ravi', 'South'),
        ('Neha', 'East'),
        ('Arun', 'West')
) AS data(salesperson_name, region_name)
JOIN regions
    ON regions.region_name = data.region_name;

-- ============================================================
-- 3. TRANSACTION DATA
-- ============================================================

INSERT INTO transactions (
    external_reference,
    region_id,
    product_id,
    salesperson_id,
    transaction_date,
    quantity,
    unit_price,
    status
)
SELECT
    data.reference,
    regions.region_id,
    products.product_id,
    salespeople.salesperson_id,
    data.transaction_date::DATE,
    data.quantity,
    data.unit_price::NUMERIC(14, 2),
    data.status
FROM (
    VALUES
        ('T001', 'North', 'Laptop', 'Asha', '2026-10-01', 2, 65000.00, 'completed'),
        ('T002', 'North', 'Phone', 'Asha', '2026-10-02', 3, 25000.00, 'completed'),
        ('T003', 'South', 'Chair', 'Ravi', '2026-10-03', 5, 3000.00, 'completed'),
        ('T004', 'South', 'Laptop', 'Ravi', '2026-10-04', 1, 65000.00, 'pending'),
        ('T005', 'East', 'Table', 'Neha', '2026-10-05', 2, 12000.00, 'completed'),
        ('T006', 'East', 'Phone', 'Neha', '2026-10-06', 4, 25000.00, 'cancelled'),
        ('T007', 'West', 'Chair', 'Arun', '2026-10-07', 3, 3000.00, 'completed'),
        ('T008', 'West', 'Laptop', 'Arun', '2026-10-08', 2, 65000.00, 'completed'),
        ('T009', 'North', 'Table', 'Asha', '2026-10-09', 1, 12000.00, 'pending'),
        ('T010', 'South', 'Chair', 'Ravi', '2026-10-10', 2, 3000.00, 'completed')
) AS data(
    reference,
    region_name,
    product_name,
    salesperson_name,
    transaction_date,
    quantity,
    unit_price,
    status
)
JOIN regions
    ON regions.region_name = data.region_name
JOIN products
    ON products.product_name = data.product_name
JOIN salespeople
    ON salespeople.salesperson_name = data.salesperson_name;

-- ============================================================
-- 4. BASE REPORTING VIEW
-- ============================================================

CREATE VIEW transaction_reporting AS
SELECT
    t.transaction_id,
    t.external_reference,
    t.transaction_date,
    r.region_name,
    pc.category_name,
    p.product_name,
    s.salesperson_name,
    t.quantity,
    t.unit_price,
    t.quantity * t.unit_price AS revenue,
    t.status
FROM transactions t
JOIN regions r
    ON r.region_id = t.region_id
JOIN products p
    ON p.product_id = t.product_id
JOIN product_categories pc
    ON pc.category_id = p.category_id
JOIN salespeople s
    ON s.salesperson_id = t.salesperson_id;

-- ============================================================
-- 5. BASIC AGGREGATION
-- ============================================================

-- Aggregation by region.
SELECT
    region_name,
    COUNT(*) AS transaction_count,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS average_transaction_value,
    MIN(revenue) AS minimum_transaction_value,
    MAX(revenue) AS maximum_transaction_value
FROM transaction_reporting
GROUP BY region_name
ORDER BY region_name;

-- Aggregation by region and category.
SELECT
    region_name,
    category_name,
    COUNT(*) AS transaction_count,
    SUM(quantity) AS total_quantity,
    SUM(revenue) AS total_revenue,
    COUNT(DISTINCT product_name) AS distinct_products
FROM transaction_reporting
GROUP BY region_name, category_name
ORDER BY region_name, category_name;

-- Aggregation by three dimensions.
SELECT
    region_name,
    category_name,
    product_name,
    COUNT(*) AS transaction_count,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
GROUP BY region_name, category_name, product_name
ORDER BY region_name, category_name, product_name;

-- ============================================================
-- 6. CONDITIONAL AGGREGATION
-- ============================================================

SELECT
    region_name,
    COUNT(*) AS all_transactions,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_count,
    COUNT(*) FILTER (
        WHERE status = 'pending'
    ) AS pending_count,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_count,
    COALESCE(
        SUM(revenue) FILTER (
            WHERE status = 'completed'
        ),
        0
    ) AS completed_revenue,
    COALESCE(
        SUM(revenue) FILTER (
            WHERE status = 'pending'
        ),
        0
    ) AS pending_revenue,
    COALESCE(
        SUM(revenue) FILTER (
            WHERE status = 'cancelled'
        ),
        0
    ) AS cancelled_revenue
FROM transaction_reporting
GROUP BY region_name
ORDER BY region_name;

-- CASE-based conditional aggregation.
SELECT
    category_name,
    SUM(
        CASE WHEN status = 'completed'
             THEN revenue ELSE 0 END
    ) AS completed_revenue,
    SUM(
        CASE WHEN status = 'pending'
             THEN revenue ELSE 0 END
    ) AS pending_revenue
FROM transaction_reporting
GROUP BY category_name;

-- ============================================================
-- 7. GROUPING SETS, ROLLUP AND CUBE
-- ============================================================

-- Detail, regional subtotal and grand total.
SELECT
    region_name,
    category_name,
    GROUPING(region_name) AS region_is_total,
    GROUPING(category_name) AS category_is_total,
    COUNT(*) AS transaction_count,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
GROUP BY ROLLUP(region_name, category_name)
ORDER BY
    GROUPING(region_name),
    region_name NULLS LAST,
    GROUPING(category_name),
    category_name NULLS LAST;

-- Explicit grouping combinations.
SELECT
    region_name,
    category_name,
    COUNT(*) AS transaction_count,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
GROUP BY GROUPING SETS (
    (region_name, category_name),
    (region_name),
    (category_name),
    ()
);

-- All dimensional combinations.
SELECT
    region_name,
    category_name,
    COUNT(*) AS transaction_count,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
GROUP BY CUBE(region_name, category_name);

-- ============================================================
-- 8. AGGREGATION USING COMMON TABLE EXPRESSIONS
-- ============================================================

WITH regional_totals AS (
    SELECT
        region_name,
        SUM(revenue) AS total_revenue
    FROM transaction_reporting
    WHERE status = 'completed'
    GROUP BY region_name
),
overall_total AS (
    SELECT SUM(total_revenue) AS revenue
    FROM regional_totals
)
SELECT
    r.region_name,
    r.total_revenue,
    ROUND(
        100.0 * r.total_revenue /
        NULLIF(o.revenue, 0),
        2
    ) AS revenue_percentage
FROM regional_totals r
CROSS JOIN overall_total o
ORDER BY r.total_revenue DESC;

-- ============================================================
-- 9. WINDOW-BASED AGGREGATION
-- ============================================================

SELECT
    region_name,
    transaction_date,
    external_reference,
    revenue,
    SUM(revenue) OVER (
        PARTITION BY region_name
        ORDER BY transaction_date, external_reference
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_regional_revenue,
    SUM(revenue) OVER (
        PARTITION BY region_name
    ) AS regional_total,
    ROUND(
        AVG(revenue) OVER (
            PARTITION BY region_name
        ),
        2
    ) AS regional_average
FROM transaction_reporting
WHERE status = 'completed'
ORDER BY region_name, transaction_date;

-- ============================================================
-- 10. PIVOT OPERATION
-- ============================================================

-- Conditional aggregation produces a portable pivot.
SELECT
    region_name,
    SUM(revenue) FILTER (
        WHERE category_name = 'Electronics'
    ) AS electronics_revenue,
    SUM(revenue) FILTER (
        WHERE category_name = 'Furniture'
    ) AS furniture_revenue,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
GROUP BY region_name
ORDER BY region_name;

-- ============================================================
-- 11. GENERIC PIVOT FUNCTION
-- ============================================================

CREATE FUNCTION pivot_sales(
    p_operation TEXT DEFAULT 'sum'
)
RETURNS TABLE (
    region_name TEXT,
    category_name TEXT,
    aggregate_value NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_operation NOT IN (
        'sum',
        'count',
        'average',
        'minimum',
        'maximum',
        'distinct_count'
    ) THEN
        RAISE EXCEPTION
            'Unsupported pivot operation: %',
            p_operation;
    END IF;

    RETURN QUERY
    SELECT
        tr.region_name::TEXT,
        tr.category_name::TEXT,
        CASE p_operation
            WHEN 'sum' THEN SUM(tr.revenue)
            WHEN 'count' THEN COUNT(*)::NUMERIC
            WHEN 'average' THEN AVG(tr.revenue)
            WHEN 'minimum' THEN MIN(tr.revenue)
            WHEN 'maximum' THEN MAX(tr.revenue)
            WHEN 'distinct_count' THEN
                COUNT(DISTINCT tr.product_name)::NUMERIC
        END AS aggregate_value
    FROM transaction_reporting tr
    GROUP BY tr.region_name, tr.category_name
    ORDER BY tr.region_name, tr.category_name;
END;
$$;

SELECT * FROM pivot_sales('sum');
SELECT * FROM pivot_sales('count');
SELECT * FROM pivot_sales('average');
SELECT * FROM pivot_sales('distinct_count');

-- ============================================================
-- 12. UNPIVOT OPERATION
-- ============================================================

WITH pivoted AS (
    SELECT
        region_name,
        SUM(revenue) FILTER (
            WHERE category_name = 'Electronics'
        ) AS electronics,
        SUM(revenue) FILTER (
            WHERE category_name = 'Furniture'
        ) AS furniture
    FROM transaction_reporting
    GROUP BY region_name
)
SELECT
    p.region_name,
    u.category_name,
    u.revenue
FROM pivoted p
CROSS JOIN LATERAL (
    VALUES
        ('Electronics'::TEXT, p.electronics),
        ('Furniture'::TEXT, p.furniture)
) AS u(category_name, revenue)
WHERE u.revenue IS NOT NULL
ORDER BY p.region_name, u.category_name;

-- ============================================================
-- 13. AGGREGATION FUNCTION
-- ============================================================

CREATE FUNCTION regional_sales_summary(
    p_start_date DATE,
    p_end_date DATE,
    p_status TEXT DEFAULT 'completed'
)
RETURNS TABLE (
    region_name TEXT,
    transaction_count BIGINT,
    total_quantity BIGINT,
    total_revenue NUMERIC,
    average_revenue NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_start_date IS NULL OR p_end_date IS NULL THEN
        RAISE EXCEPTION 'Date parameters cannot be null.';
    END IF;

    IF p_start_date > p_end_date THEN
        RAISE EXCEPTION 'Start date cannot exceed end date.';
    END IF;

    IF p_status NOT IN (
        'completed',
        'pending',
        'cancelled',
        'all'
    ) THEN
        RAISE EXCEPTION 'Invalid transaction status.';
    END IF;

    RETURN QUERY
    SELECT
        tr.region_name::TEXT,
        COUNT(*)::BIGINT,
        SUM(tr.quantity)::BIGINT,
        SUM(tr.revenue),
        ROUND(AVG(tr.revenue), 2)
    FROM transaction_reporting tr
    WHERE tr.transaction_date BETWEEN p_start_date AND p_end_date
      AND (
          p_status = 'all'
          OR tr.status = p_status
      )
    GROUP BY tr.region_name
    ORDER BY tr.region_name;
END;
$$;

SELECT *
FROM regional_sales_summary(
    DATE '2026-10-01',
    DATE '2026-10-31',
    'completed'
);

-- ============================================================
-- 14. SUMMARY TABLE
-- ============================================================

CREATE TABLE daily_regional_summary (
    summary_date DATE NOT NULL,
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    transaction_count BIGINT NOT NULL CHECK (transaction_count >= 0),
    total_quantity BIGINT NOT NULL CHECK (total_quantity >= 0),
    total_revenue NUMERIC(20, 2) NOT NULL CHECK (total_revenue >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (summary_date, region_id)
);

CREATE INDEX idx_daily_summary_region_date
    ON daily_regional_summary(region_id, summary_date DESC);

-- ============================================================
-- 15. INCREMENTAL SUMMARY MAINTENANCE
-- ============================================================

CREATE FUNCTION maintain_daily_summary()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    old_revenue NUMERIC(20, 2);
    old_quantity BIGINT;
    old_count BIGINT;
    new_revenue NUMERIC(20, 2);
    new_quantity BIGINT;
    new_count BIGINT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        IF OLD.status = 'completed' THEN
            old_revenue := OLD.quantity * OLD.unit_price;
            old_quantity := OLD.quantity;
            old_count := 1;

            INSERT INTO daily_regional_summary (
                summary_date,
                region_id,
                transaction_count,
                total_quantity,
                total_revenue
            )
            VALUES (
                OLD.transaction_date,
                OLD.region_id,
                0,
                0,
                0
            )
            ON CONFLICT (summary_date, region_id) DO NOTHING;

            UPDATE daily_regional_summary
            SET
                transaction_count = transaction_count - old_count,
                total_quantity = total_quantity - old_quantity,
                total_revenue = total_revenue - old_revenue,
                updated_at = CURRENT_TIMESTAMP
            WHERE summary_date = OLD.transaction_date
              AND region_id = OLD.region_id;
        END IF;
    END IF;

    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        IF NEW.status = 'completed' THEN
            new_revenue := NEW.quantity * NEW.unit_price;
            new_quantity := NEW.quantity;
            new_count := 1;

            INSERT INTO daily_regional_summary (
                summary_date,
                region_id,
                transaction_count,
                total_quantity,
                total_revenue
            )
            VALUES (
                NEW.transaction_date,
                NEW.region_id,
                new_count,
                new_quantity,
                new_revenue
            )
            ON CONFLICT (summary_date, region_id)
            DO UPDATE SET
                transaction_count =
                    daily_regional_summary.transaction_count
                    + EXCLUDED.transaction_count,
                total_quantity =
                    daily_regional_summary.total_quantity
                    + EXCLUDED.total_quantity,
                total_revenue =
                    daily_regional_summary.total_revenue
                    + EXCLUDED.total_revenue,
                updated_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_maintain_daily_summary
AFTER INSERT OR UPDATE OR DELETE
ON transactions
FOR EACH ROW
EXECUTE FUNCTION maintain_daily_summary();

-- Populate the summary for existing sample transactions.
INSERT INTO daily_regional_summary (
    summary_date,
    region_id,
    transaction_count,
    total_quantity,
    total_revenue
)
SELECT
    transaction_date,
    region_id,
    COUNT(*),
    SUM(quantity),
    SUM(quantity * unit_price)
FROM transactions
WHERE status = 'completed'
GROUP BY transaction_date, region_id
ON CONFLICT (summary_date, region_id)
DO UPDATE SET
    transaction_count = EXCLUDED.transaction_count,
    total_quantity = EXCLUDED.total_quantity,
    total_revenue = EXCLUDED.total_revenue,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================
-- 16. SUMMARY RECONCILIATION
-- ============================================================

SELECT
    summary.summary_date,
    summary.region_id,
    summary.total_revenue AS summarized_revenue,
    source.total_revenue AS source_revenue,
    summary.total_revenue - source.total_revenue AS difference
FROM daily_regional_summary summary
JOIN (
    SELECT
        transaction_date,
        region_id,
        SUM(quantity * unit_price) AS total_revenue
    FROM transactions
    WHERE status = 'completed'
    GROUP BY transaction_date, region_id
) source
    ON source.transaction_date = summary.summary_date
   AND source.region_id = summary.region_id
WHERE summary.total_revenue <> source.total_revenue;

-- ============================================================
-- 17. WORKFLOW PROCESSING WITH TRANSACTIONS
-- ============================================================

BEGIN;

-- Insert a valid completed transaction.
INSERT INTO transactions (
    external_reference,
    region_id,
    product_id,
    salesperson_id,
    transaction_date,
    quantity,
    unit_price,
    status
)
SELECT
    'T011',
    r.region_id,
    p.product_id,
    s.salesperson_id,
    DATE '2026-10-11',
    2,
    15000.00,
    'completed'
FROM regions r
JOIN products p
    ON p.product_name = 'Phone'
JOIN salespeople s
    ON s.salesperson_name = 'Asha'
WHERE r.region_name = 'North';

-- Verify transaction visibility and summary maintenance.
SELECT *
FROM transaction_reporting
WHERE external_reference = 'T011';

SELECT *
FROM daily_regional_summary
WHERE summary_date = DATE '2026-10-11';

COMMIT;

-- ============================================================
-- 18. VALIDATION AND FAILURE CASES
-- ============================================================

-- Duplicate reference: the UNIQUE constraint rejects it.
-- Negative quantity: the CHECK constraint rejects it.
-- Unknown region: the FOREIGN KEY constraint rejects it.
-- Invalid status: the CHECK constraint rejects it.

-- Demonstrate failure isolation with a savepoint.
BEGIN;

SAVEPOINT before_invalid_transaction;

DO $$
BEGIN
    BEGIN
        INSERT INTO transactions (
            external_reference,
            region_id,
            product_id,
            salesperson_id,
            transaction_date,
            quantity,
            unit_price,
            status
        )
        VALUES (
            'INVALID-001',
            999999,
            1,
            1,
            CURRENT_DATE,
            1,
            100.00,
            'completed'
        );
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'Rejected invalid foreign key.';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT before_invalid_transaction;
COMMIT;

-- ============================================================
-- 19. ELIGIBILITY AND DATA QUALITY REPORTING
-- ============================================================

-- Identify valid records eligible for completed-sales reporting.
SELECT
    external_reference,
    status,
    quantity,
    unit_price,
    quantity * unit_price AS revenue,
    CASE
        WHEN status = 'completed'
         AND quantity > 0
         AND unit_price >= 0
        THEN TRUE
        ELSE FALSE
    END AS aggregation_eligible
FROM transactions
ORDER BY transaction_id;

-- Data-quality report.
SELECT
    COUNT(*) AS source_records,
    COUNT(DISTINCT external_reference) AS unique_references,
    COUNT(*) FILTER (
        WHERE quantity <= 0
    ) AS invalid_quantities,
    COUNT(*) FILTER (
        WHERE unit_price < 0
    ) AS invalid_prices,
    COUNT(*) FILTER (
        WHERE status NOT IN ('completed', 'pending', 'cancelled')
    ) AS invalid_statuses
FROM transactions;

-- ============================================================
-- 20. PERFORMANCE ANALYSIS
-- ============================================================

ANALYZE transactions;
ANALYZE products;
ANALYZE regions;
ANALYZE product_categories;

EXPLAIN (ANALYZE, BUFFERS)
SELECT
    region_name,
    category_name,
    SUM(revenue) AS total_revenue
FROM transaction_reporting
WHERE status = 'completed'
  AND transaction_date >= DATE '2026-10-01'
  AND transaction_date < DATE '2026-11-01'
GROUP BY region_name, category_name;

-- ============================================================
-- 21. FINAL REPORTING QUERIES
-- ============================================================

-- Top regions by completed revenue.
WITH regional_performance AS (
    SELECT
        region_name,
        SUM(revenue) AS revenue
    FROM transaction_reporting
    WHERE status = 'completed'
    GROUP BY region_name
)
SELECT
    region_name,
    revenue,
    DENSE_RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM regional_performance
ORDER BY revenue_rank, region_name;

-- Product contribution within each category.
WITH product_totals AS (
    SELECT
        category_name,
        product_name,
        SUM(revenue) AS revenue
    FROM transaction_reporting
    WHERE status = 'completed'
    GROUP BY category_name, product_name
)
SELECT
    category_name,
    product_name,
    revenue,
    ROUND(
        100.0 * revenue /
        NULLIF(
            SUM(revenue) OVER (
                PARTITION BY category_name
            ),
            0
        ),
        2
    ) AS category_contribution_percentage
FROM product_totals
ORDER BY category_name, revenue DESC;

-- Final daily summary.
SELECT
    summary.summary_date,
    regions.region_name,
    summary.transaction_count,
    summary.total_quantity,
    summary.total_revenue,
    summary.updated_at
FROM daily_regional_summary summary
JOIN regions
    ON regions.region_id = summary.region_id
ORDER BY summary.summary_date, regions.region_name;
