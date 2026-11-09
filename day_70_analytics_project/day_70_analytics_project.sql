/*
===============================================================================
COMPLETE BUSINESS ANALYTICS DATABASE
Domain: Retail Sales and Business Performance Analytics
Database: PostgreSQL 14+
Currency: INR

Features:
- Transaction and customer management
- Product and regional dimensions
- Financial calculations
- Data quality enforcement
- Sales aggregation
- Monthly performance reporting
- Customer segmentation
- Revenue trend analysis
- Business policy configuration
- Automated transaction audit
- Analytical views and functions
- Transaction-safe processing
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS business_analytics;

SET search_path TO business_analytics, public;

-- ============================================================================
-- 1. DOMAIN TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(30) PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE,
    region VARCHAR(50) NOT NULL,
    registration_date DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT customer_name_valid
        CHECK (length(trim(customer_name)) > 0),

    CONSTRAINT customer_region_valid
        CHECK (length(trim(region)) > 0)
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(30) PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category VARCHAR(60) NOT NULL,
    unit_cost NUMERIC(14,2) NOT NULL,
    selling_price NUMERIC(14,2) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT product_cost_nonnegative
        CHECK (unit_cost >= 0),

    CONSTRAINT product_price_positive
        CHECK (selling_price > 0),

    CONSTRAINT product_margin_valid
        CHECK (selling_price >= unit_cost)
);

CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_reference VARCHAR(60) NOT NULL UNIQUE,
    customer_id VARCHAR(30) NOT NULL
        REFERENCES customers(customer_id),
    transaction_date DATE NOT NULL,
    region VARCHAR(50) NOT NULL,
    transaction_status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT transaction_status_valid
        CHECK (
            transaction_status IN (
                'PENDING',
                'COMPLETED',
                'CANCELLED',
                'REJECTED'
            )
        )
);

CREATE TABLE IF NOT EXISTS sales_items (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_id BIGINT NOT NULL
        REFERENCES sales_transactions(transaction_id)
        ON DELETE CASCADE,
    product_id VARCHAR(30) NOT NULL
        REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL,
    unit_cost NUMERIC(14,2) NOT NULL,

    CONSTRAINT quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT item_price_positive
        CHECK (unit_price > 0),

    CONSTRAINT item_cost_nonnegative
        CHECK (unit_cost >= 0),

    CONSTRAINT item_margin_valid
        CHECK (unit_price >= unit_cost),

    CONSTRAINT transaction_product_unique
        UNIQUE (transaction_id, product_id)
);

CREATE TABLE IF NOT EXISTS business_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    minimum_gross_margin NUMERIC(6,2) NOT NULL,
    minimum_repeat_rate NUMERIC(6,2) NOT NULL,
    minimum_transactions INTEGER NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT margin_policy_valid
        CHECK (
            minimum_gross_margin >= 0
            AND minimum_gross_margin <= 100
        ),

    CONSTRAINT repeat_policy_valid
        CHECK (
            minimum_repeat_rate >= 0
            AND minimum_repeat_rate <= 100
        ),

    CONSTRAINT transaction_policy_valid
        CHECK (minimum_transactions > 0)
);

CREATE TABLE IF NOT EXISTS transaction_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    action VARCHAR(30) NOT NULL,
    audit_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    database_user TEXT NOT NULL DEFAULT CURRENT_USER,
    transaction_reference VARCHAR(60)
);

CREATE TABLE IF NOT EXISTS analytics_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_count INTEGER NOT NULL,
    total_revenue NUMERIC(16,2) NOT NULL,
    gross_profit NUMERIC(16,2) NOT NULL,
    gross_margin NUMERIC(8,2) NOT NULL,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT analytics_run_status_valid
        CHECK (status IN ('SUCCESS', 'WARNING', 'FAILED'))
);

CREATE TABLE IF NOT EXISTS policy_findings (
    finding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES analytics_runs(run_id)
        ON DELETE CASCADE,
    policy_id BIGINT
        REFERENCES business_policies(policy_id),
    finding_code VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,

    CONSTRAINT finding_severity_valid
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH'))
);

-- ============================================================================
-- 2. PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON sales_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_date
    ON sales_transactions(customer_id, transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_region_date
    ON sales_transactions(region, transaction_date);

CREATE INDEX IF NOT EXISTS idx_transactions_completed
    ON sales_transactions(transaction_date)
    WHERE transaction_status = 'COMPLETED';

CREATE INDEX IF NOT EXISTS idx_items_product
    ON sales_items(product_id);

CREATE INDEX IF NOT EXISTS idx_items_transaction
    ON sales_items(transaction_id);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

CREATE INDEX IF NOT EXISTS idx_findings_run
    ON policy_findings(run_id);

-- ============================================================================
-- 3. TRANSACTION AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_sales_transaction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO transaction_audit (
        transaction_id,
        action,
        transaction_reference
    )
    VALUES (
        NEW.transaction_id,
        'INSERT',
        NEW.external_reference
    );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sales_transaction_audit
ON sales_transactions;

CREATE TRIGGER trg_sales_transaction_audit
AFTER INSERT ON sales_transactions
FOR EACH ROW
EXECUTE FUNCTION audit_sales_transaction();

-- ============================================================================
-- 4. FINANCIAL CALCULATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_transaction_revenue(
    p_transaction_id BIGINT
)
RETURNS NUMERIC(16,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(
        SUM(quantity * unit_price),
        0
    )::NUMERIC(16,2)
    FROM sales_items
    WHERE transaction_id = p_transaction_id;
$$;

CREATE OR REPLACE FUNCTION calculate_transaction_profit(
    p_transaction_id BIGINT
)
RETURNS NUMERIC(16,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(
        SUM(quantity * (unit_price - unit_cost)),
        0
    )::NUMERIC(16,2)
    FROM sales_items
    WHERE transaction_id = p_transaction_id;
$$;

-- ============================================================================
-- 5. ANALYTICAL VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW completed_sales_detail AS
SELECT
    st.transaction_id,
    st.external_reference,
    st.transaction_date,
    st.customer_id,
    c.customer_name,
    st.region,
    si.product_id,
    p.product_name,
    p.category,
    si.quantity,
    si.unit_price,
    si.unit_cost,

    si.quantity * si.unit_price AS revenue,

    si.quantity * si.unit_cost AS cost,

    si.quantity * (si.unit_price - si.unit_cost) AS gross_profit

FROM sales_transactions st

JOIN customers c
    ON c.customer_id = st.customer_id

JOIN sales_items si
    ON si.transaction_id = st.transaction_id

JOIN products p
    ON p.product_id = si.product_id

WHERE st.transaction_status = 'COMPLETED';

CREATE OR REPLACE VIEW monthly_sales_performance AS
SELECT
    DATE_TRUNC('month', transaction_date)::DATE AS sales_month,
    COUNT(DISTINCT transaction_id) AS transaction_count,
    SUM(revenue)::NUMERIC(16,2) AS total_revenue,
    SUM(cost)::NUMERIC(16,2) AS total_cost,
    SUM(gross_profit)::NUMERIC(16,2) AS gross_profit,
    ROUND(
        100.0 * SUM(gross_profit)
        / NULLIF(SUM(revenue), 0),
        2
    ) AS gross_margin_percent,
    SUM(quantity) AS total_units

FROM completed_sales_detail

GROUP BY DATE_TRUNC('month', transaction_date)::DATE;

CREATE OR REPLACE VIEW category_performance AS
SELECT
    category,
    COUNT(DISTINCT transaction_id) AS transactions,
    SUM(quantity) AS units_sold,
    SUM(revenue)::NUMERIC(16,2) AS revenue,
    SUM(gross_profit)::NUMERIC(16,2) AS profit,
    ROUND(
        100.0 * SUM(gross_profit)
        / NULLIF(SUM(revenue), 0),
        2
    ) AS margin_percent

FROM completed_sales_detail

GROUP BY category;

CREATE OR REPLACE VIEW regional_performance AS
SELECT
    region,
    COUNT(DISTINCT transaction_id) AS transactions,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(revenue)::NUMERIC(16,2) AS revenue,
    SUM(gross_profit)::NUMERIC(16,2) AS profit

FROM completed_sales_detail

GROUP BY region;

-- ============================================================================
-- 6. CUSTOMER ANALYTICS FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION customer_analytics(
    p_reference_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    customer_id VARCHAR(30),
    customer_name VARCHAR(120),
    frequency BIGINT,
    monetary_value NUMERIC(16,2),
    recency_days INTEGER,
    customer_segment TEXT
)
LANGUAGE SQL
STABLE
AS $$
    WITH customer_metrics AS (
        SELECT
            c.customer_id,
            c.customer_name,
            COUNT(DISTINCT d.transaction_id) AS frequency,
            COALESCE(SUM(d.revenue), 0)::NUMERIC(16,2)
                AS monetary_value,
            MAX(d.transaction_date) AS last_purchase

        FROM customers c

        LEFT JOIN completed_sales_detail d
            ON d.customer_id = c.customer_id
           AND d.transaction_date <= p_reference_date

        GROUP BY c.customer_id, c.customer_name
    ),

    scored AS (
        SELECT
            customer_id,
            customer_name,
            frequency,
            monetary_value,
            CASE
                WHEN last_purchase IS NULL THEN NULL
                ELSE p_reference_date - last_purchase
            END AS recency_days

        FROM customer_metrics
    )

    SELECT
        customer_id,
        customer_name,
        frequency,
        monetary_value,
        recency_days,

        CASE
            WHEN frequency >= 5
             AND monetary_value >= 50000
             AND recency_days <= 90
                THEN 'High Value'

            WHEN frequency >= 3
             AND recency_days <= 180
                THEN 'Regular'

            WHEN last_purchase IS NULL
                THEN 'No Purchase'

            WHEN recency_days > 180
                THEN 'At Risk'

            ELSE 'Occasional'
        END AS customer_segment

    FROM scored
    ORDER BY monetary_value DESC;
$$;

-- ============================================================================
-- 7. MONTHLY REVENUE FORECAST
-- ============================================================================

CREATE OR REPLACE FUNCTION forecast_monthly_revenue()
RETURNS TABLE (
    forecast_method TEXT,
    historical_months BIGINT,
    trend_slope NUMERIC,
    forecast_revenue NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
    WITH monthly AS (
        SELECT
            ROW_NUMBER() OVER (ORDER BY sales_month)::NUMERIC AS x,
            total_revenue::NUMERIC AS y

        FROM monthly_sales_performance
    ),

    averages AS (
        SELECT
            COUNT(*)::BIGINT AS n,
            AVG(x) AS x_mean,
            AVG(y) AS y_mean
        FROM monthly
    ),

    coefficients AS (
        SELECT
            a.n,
            COALESCE(
                SUM((m.x - a.x_mean) * (m.y - a.y_mean))
                / NULLIF(
                    SUM(POWER(m.x - a.x_mean, 2)),
                    0
                ),
                0
            ) AS slope,
            a.y_mean,
            a.x_mean

        FROM averages a
        LEFT JOIN monthly m ON TRUE

        GROUP BY a.n, a.x_mean, a.y_mean
    )

    SELECT
        'Ordinary Least Squares'::TEXT,
        n,
        ROUND(slope, 2),
        GREATEST(
            0,
            ROUND(
                y_mean + slope * (n + 1 - x_mean),
                2
            )
        )

    FROM coefficients;
$$;

-- ============================================================================
-- 8. BUSINESS POLICY EVALUATION PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE evaluate_business_policies(
    p_run_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_revenue NUMERIC(16,2);
    v_profit NUMERIC(16,2);
    v_margin NUMERIC(8,2);
    v_repeat_rate NUMERIC(8,2);
    v_customer_count BIGINT;
    v_repeat_count BIGINT;
    v_transaction_count BIGINT;
    v_policy RECORD;
BEGIN
    SELECT
        COUNT(DISTINCT transaction_id),
        COALESCE(SUM(revenue), 0),
        COALESCE(SUM(gross_profit), 0)

    INTO
        v_transaction_count,
        v_revenue,
        v_profit

    FROM completed_sales_detail;

    v_margin := CASE
        WHEN v_revenue > 0
            THEN ROUND(100 * v_profit / v_revenue, 2)
        ELSE 0
    END;

    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE frequency > 1)

    INTO
        v_customer_count,
        v_repeat_count

    FROM (
        SELECT customer_id, COUNT(DISTINCT transaction_id) AS frequency
        FROM completed_sales_detail
        GROUP BY customer_id
    ) customer_frequency;

    v_repeat_rate := CASE
        WHEN v_customer_count > 0
            THEN ROUND(
                100.0 * v_repeat_count / v_customer_count,
                2
            )
        ELSE 0
    END;

    FOR v_policy IN
        SELECT *
        FROM business_policies
        WHERE enabled = TRUE
    LOOP

        IF v_transaction_count < v_policy.minimum_transactions THEN
            INSERT INTO policy_findings (
                run_id,
                policy_id,
                finding_code,
                severity,
                description
            )
            VALUES (
                p_run_id,
                v_policy.policy_id,
                'INSUFFICIENT_TRANSACTIONS',
                'HIGH',
                'Transaction volume is below the configured threshold.'
            );
        END IF;

        IF v_margin < v_policy.minimum_gross_margin THEN
            INSERT INTO policy_findings (
                run_id,
                policy_id,
                finding_code,
                severity,
                description
            )
            VALUES (
                p_run_id,
                v_policy.policy_id,
                'LOW_GROSS_MARGIN',
                'HIGH',
                'Gross margin is below the configured threshold.'
            );
        END IF;

        IF v_repeat_rate < v_policy.minimum_repeat_rate THEN
            INSERT INTO policy_findings (
                run_id,
                policy_id,
                finding_code,
                severity,
                description
            )
            VALUES (
                p_run_id,
                v_policy.policy_id,
                'LOW_REPEAT_RATE',
                'MEDIUM',
                'Customer repeat-purchase rate is below target.'
            );
        END IF;

    END LOOP;
END;
$$;

-- ============================================================================
-- 9. SAMPLE MASTER DATA
-- ============================================================================

INSERT INTO customers (
    customer_id,
    customer_name,
    email,
    region,
    registration_date
)
VALUES
    ('C001', 'Aarav Sharma', 'aarav@example.com', 'North', '2024-01-10'),
    ('C002', 'Priya Verma', 'priya@example.com', 'South', '2024-02-15'),
    ('C003', 'Rahul Singh', 'rahul@example.com', 'East', '2024-03-20'),
    ('C004', 'Ananya Gupta', 'ananya@example.com', 'West', '2024-04-12'),
    ('C005', 'Vikram Mehta', 'vikram@example.com', 'Central', '2024-05-08'),
    ('C006', 'Meera Joshi', 'meera@example.com', 'North', '2024-06-18'),
    ('C007', 'Arjun Rao', 'arjun@example.com', 'South', '2024-07-22'),
    ('C008', 'Neha Kapoor', 'neha@example.com', 'East', '2024-08-10')

ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO products (
    product_id,
    product_name,
    category,
    unit_cost,
    selling_price
)
VALUES
    ('P001', 'Business Laptop', 'Electronics', 18000, 25000),
    ('P002', 'Office Monitor', 'Electronics', 8500, 12000),
    ('P003', 'Office Desk', 'Furniture', 12000, 18000),
    ('P004', 'Office Chair', 'Furniture', 5200, 8000),
    ('P005', 'Formal Shirt', 'Clothing', 1200, 2500),
    ('P006', 'Casual T-Shirt', 'Clothing', 700, 1500),
    ('P007', 'Food Package', 'Groceries', 650, 900),
    ('P008', 'Daily Essentials', 'Groceries', 350, 500)

ON CONFLICT (product_id) DO NOTHING;

INSERT INTO business_policies (
    policy_name,
    minimum_gross_margin,
    minimum_repeat_rate,
    minimum_transactions
)
VALUES (
    'Standard Retail Performance Policy',
    20,
    30,
    10
)
ON CONFLICT (policy_name) DO NOTHING;

-- ============================================================================
-- 10. SAMPLE SALES TRANSACTIONS
-- ============================================================================

INSERT INTO sales_transactions (
    external_reference,
    customer_id,
    transaction_date,
    region,
    transaction_status
)
VALUES
    ('ORD-2025-001', 'C001', '2025-01-10', 'North', 'COMPLETED'),
    ('ORD-2025-002', 'C001', '2025-02-10', 'North', 'COMPLETED'),
    ('ORD-2025-003', 'C001', '2025-03-10', 'North', 'COMPLETED'),
    ('ORD-2025-004', 'C001', '2025-04-10', 'North', 'COMPLETED'),
    ('ORD-2025-005', 'C001', '2025-05-10', 'North', 'COMPLETED'),
    ('ORD-2025-006', 'C002', '2025-01-15', 'South', 'COMPLETED'),
    ('ORD-2025-007', 'C002', '2025-03-15', 'South', 'COMPLETED'),
    ('ORD-2025-008', 'C003', '2025-02-18', 'East', 'COMPLETED'),
    ('ORD-2025-009', 'C004', '2025-04-20', 'West', 'COMPLETED'),
    ('ORD-2025-010', 'C005', '2025-05-22', 'Central', 'COMPLETED'),
    ('ORD-2025-011', 'C006', '2025-06-10', 'North', 'COMPLETED'),
    ('ORD-2025-012', 'C007', '2025-07-12', 'South', 'COMPLETED'),
    ('ORD-2025-013', 'C008', '2025-08-15', 'East', 'PENDING'),
    ('ORD-2025-014', 'C003', '2025-09-10', 'East', 'COMPLETED'),
    ('ORD-2025-015', 'C004', '2025-10-10', 'West', 'COMPLETED'),
    ('ORD-2025-016', 'C005', '2025-11-10', 'Central', 'CANCELLED'),
    ('ORD-2025-017', 'C006', '2025-12-10', 'North', 'COMPLETED')

ON CONFLICT (external_reference) DO NOTHING;

INSERT INTO sales_items (
    transaction_id,
    product_id,
    quantity,
    unit_price,
    unit_cost
)
SELECT
    st.transaction_id,
    data.product_id,
    data.quantity,
    p.selling_price,
    p.unit_cost

FROM (
    VALUES
        ('ORD-2025-001', 'P001', 2),
        ('ORD-2025-002', 'P002', 2),
        ('ORD-2025-003', 'P003', 1),
        ('ORD-2025-004', 'P001', 1),
        ('ORD-2025-005', 'P004', 2),
        ('ORD-2025-006', 'P005', 4),
        ('ORD-2025-007', 'P006', 3),
        ('ORD-2025-008', 'P001', 1),
        ('ORD-2025-009', 'P003', 2),
        ('ORD-2025-010', 'P007', 5),
        ('ORD-2025-011', 'P002', 1),
        ('ORD-2025-012', 'P008', 4),
        ('ORD-2025-013', 'P001', 1),
        ('ORD-2025-014', 'P004', 2),
        ('ORD-2025-015', 'P005', 3),
        ('ORD-2025-016', 'P003', 1),
        ('ORD-2025-017', 'P002', 2)
) AS data(reference, product_id, quantity)

JOIN sales_transactions st
    ON st.external_reference = data.reference

JOIN products p
    ON p.product_id = data.product_id

WHERE st.transaction_status = 'COMPLETED'

ON CONFLICT (transaction_id, product_id) DO NOTHING;

-- ============================================================================
-- 11. VALIDATION AND RETRIEVAL QUERIES
-- ============================================================================

-- Transaction-level revenue and profitability.

SELECT
    transaction_id,
    external_reference,
    calculate_transaction_revenue(transaction_id) AS revenue,
    calculate_transaction_profit(transaction_id) AS profit

FROM sales_transactions
WHERE transaction_status = 'COMPLETED'
ORDER BY transaction_date;

-- Data quality: completed transactions without line items.

SELECT
    st.transaction_id,
    st.external_reference

FROM sales_transactions st

LEFT JOIN sales_items si
    ON si.transaction_id = st.transaction_id

WHERE st.transaction_status = 'COMPLETED'

GROUP BY st.transaction_id, st.external_reference

HAVING COUNT(si.item_id) = 0;

-- ============================================================================
-- 12. CATEGORY AND REGIONAL REPORTING
-- ============================================================================

SELECT *
FROM category_performance
ORDER BY revenue DESC;

SELECT *
FROM regional_performance
ORDER BY revenue DESC;

SELECT *
FROM monthly_sales_performance
ORDER BY sales_month;

-- ============================================================================
-- 13. CUSTOMER SEGMENTATION
-- ============================================================================

SELECT *
FROM customer_analytics(DATE '2025-12-31');

-- Segment-level customer counts and monetary contribution.

SELECT
    customer_segment,
    COUNT(*) AS customer_count,
    SUM(monetary_value)::NUMERIC(16,2) AS segment_revenue

FROM customer_analytics(DATE '2025-12-31')

GROUP BY customer_segment

ORDER BY segment_revenue DESC;

-- ============================================================================
-- 14. MONTH-OVER-MONTH GROWTH USING A WINDOW FUNCTION
-- ============================================================================

WITH monthly AS (
    SELECT
        sales_month,
        total_revenue,
        LAG(total_revenue) OVER (
            ORDER BY sales_month
        ) AS previous_revenue

    FROM monthly_sales_performance
)

SELECT
    sales_month,
    total_revenue,
    previous_revenue,

    ROUND(
        100.0 * (total_revenue - previous_revenue)
        / NULLIF(previous_revenue, 0),
        2
    ) AS growth_percent

FROM monthly

ORDER BY sales_month;

-- ============================================================================
-- 15. PRODUCT RANKING
-- ============================================================================

SELECT
    product_id,
    product_name,
    category,
    revenue,
    gross_profit,

    RANK() OVER (
        PARTITION BY category
        ORDER BY revenue DESC
    ) AS category_rank

FROM (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        SUM(d.revenue) AS revenue,
        SUM(d.gross_profit) AS gross_profit

    FROM products p

    JOIN completed_sales_detail d
        ON d.product_id = p.product_id

    GROUP BY p.product_id, p.product_name, p.category
) product_totals

ORDER BY category, category_rank;

-- ============================================================================
-- 16. REVENUE FORECAST
-- ============================================================================

SELECT *
FROM forecast_monthly_revenue();

-- ============================================================================
-- 17. EXECUTABLE BUSINESS REPORTING WORKFLOW
-- ============================================================================

DO $$
DECLARE
    v_run_id BIGINT;
    v_count INTEGER;
    v_revenue NUMERIC(16,2);
    v_profit NUMERIC(16,2);
    v_margin NUMERIC(8,2);
    v_status VARCHAR(20);
BEGIN
    SELECT
        COUNT(DISTINCT transaction_id),
        COALESCE(SUM(revenue), 0),
        COALESCE(SUM(gross_profit), 0)

    INTO
        v_count,
        v_revenue,
        v_profit

    FROM completed_sales_detail;

    v_margin := CASE
        WHEN v_revenue > 0
            THEN ROUND(100 * v_profit / v_revenue, 2)
        ELSE 0
    END;

    v_status := CASE
        WHEN v_count = 0 THEN 'FAILED'
        WHEN v_margin < 20 THEN 'WARNING'
        ELSE 'SUCCESS'
    END;

    INSERT INTO analytics_runs (
        transaction_count,
        total_revenue,
        gross_profit,
        gross_margin,
        status
    )
    VALUES (
        v_count,
        v_revenue,
        v_profit,
        v_margin,
        v_status
    )
    RETURNING run_id INTO v_run_id;

    CALL evaluate_business_policies(v_run_id);

    RAISE NOTICE
        'Analytics run % completed with status %',
        v_run_id,
        v_status;
END;
$$;

-- ============================================================================
-- 18. FINAL BUSINESS REPORT
-- ============================================================================

SELECT
    run_id,
    run_timestamp,
    transaction_count,
    total_revenue,
    gross_profit,
    gross_margin,
    status

FROM analytics_runs

ORDER BY run_timestamp DESC;

SELECT
    pf.finding_id,
    pf.finding_code,
    pf.severity,
    pf.description,
    ar.run_timestamp

FROM policy_findings pf

JOIN analytics_runs ar
    ON ar.run_id = pf.run_id

ORDER BY pf.finding_id;

SELECT
    COUNT(*) AS audited_transactions
FROM transaction_audit;

-- ============================================================================
-- 19. TRANSACTION AND FAILURE-HANDLING DEMONSTRATION
-- ============================================================================

-- Invalid product pricing is rejected by the table constraints.
-- Execute this independently to observe the constraint failure:
--
-- INSERT INTO products (
--     product_id, product_name, category, unit_cost, selling_price
-- )
-- VALUES ('INVALID01', 'Invalid Product', 'Test', 2000, 1000);
--
-- Duplicate external references are rejected by the unique constraint.
--
-- The following transaction demonstrates rollback without leaving
-- test records in the database.

DO $$
BEGIN
    BEGIN
        INSERT INTO customers (
            customer_id,
            customer_name,
            email,
            region,
            registration_date
        )
        VALUES (
            'ROLLBACK_TEST',
            'Transaction Test',
            'rollback@example.com',
            'North',
            CURRENT_DATE
        );

        RAISE EXCEPTION 'Demonstration rollback';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'Demonstration rollback' THEN
                RAISE NOTICE
                    'Test transaction rolled back successfully.';
            ELSE
                RAISE;
            END IF;
    END;
END;
$$;

COMMIT;
