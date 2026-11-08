/*
    BUSINESS ANALYTICS AUTOMATION
    PostgreSQL 15+

    Relational business analytics workflow:
    1. Sales transaction ingestion.
    2. Data quality validation.
    3. Duplicate prevention.
    4. Analytics job management.
    5. Automated KPI aggregation.
    6. Regional, product and monthly reporting.
    7. Anomaly detection.
    8. Report persistence.
    9. Audit logging.
    10. Transaction-safe processing.

    Execute using psql.
*/

DROP SCHEMA IF EXISTS business_analytics CASCADE;

CREATE SCHEMA business_analytics;

SET search_path TO business_analytics, public;

-- =========================================================
-- 1. DOMAIN TYPES
-- =========================================================

CREATE TYPE job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed'
);

CREATE TYPE record_status AS ENUM (
    'pending',
    'accepted',
    'rejected',
    'duplicate'
);

CREATE TYPE report_status AS ENUM (
    'generated',
    'published',
    'archived'
);

-- =========================================================
-- 2. MASTER DATA
-- =========================================================

CREATE TABLE regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
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
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE business_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    role_name VARCHAR(30) NOT NULL
        CHECK (
            role_name IN (
                'analyst',
                'manager',
                'administrator',
                'viewer'
            )
        ),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- =========================================================
-- 3. SOURCE TRANSACTION DATA
-- =========================================================

CREATE TABLE sales_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_transaction_id VARCHAR(100) NOT NULL UNIQUE,

    transaction_date DATE NOT NULL,

    region_id BIGINT NOT NULL
        REFERENCES regions(region_id),

    product_id BIGINT NOT NULL
        REFERENCES products(product_id),

    quantity INTEGER NOT NULL
        CHECK (quantity >= 0),

    unit_price NUMERIC(14, 2) NOT NULL
        CHECK (unit_price >= 0),

    cost_per_unit NUMERIC(14, 2) NOT NULL
        CHECK (cost_per_unit >= 0),

    revenue NUMERIC(18, 2)
        GENERATED ALWAYS AS (
            quantity * unit_price
        ) STORED,

    total_cost NUMERIC(18, 2)
        GENERATED ALWAYS AS (
            quantity * cost_per_unit
        ) STORED,

    profit NUMERIC(18, 2)
        GENERATED ALWAYS AS (
            quantity * (unit_price - cost_per_unit)
        ) STORED,

    source_system VARCHAR(100) NOT NULL DEFAULT 'manual_import',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (quantity = 0 OR unit_price > 0)
);

CREATE INDEX idx_sales_date
    ON sales_transactions(transaction_date);

CREATE INDEX idx_sales_region_date
    ON sales_transactions(region_id, transaction_date);

CREATE INDEX idx_sales_product_date
    ON sales_transactions(product_id, transaction_date);

CREATE INDEX idx_sales_profit
    ON sales_transactions(profit);

-- =========================================================
-- 4. DATA INGESTION AND QUALITY TRACKING
-- =========================================================

CREATE TABLE ingestion_batches (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_name VARCHAR(150) NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    total_records INTEGER NOT NULL DEFAULT 0
        CHECK (total_records >= 0),

    accepted_records INTEGER NOT NULL DEFAULT 0
        CHECK (accepted_records >= 0),

    rejected_records INTEGER NOT NULL DEFAULT 0
        CHECK (rejected_records >= 0),

    duplicate_records INTEGER NOT NULL DEFAULT 0
        CHECK (duplicate_records >= 0),

    CHECK (
        accepted_records + rejected_records <= total_records
    )
);

CREATE TABLE ingestion_errors (
    error_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    batch_id BIGINT NOT NULL
        REFERENCES ingestion_batches(batch_id),

    source_row_number INTEGER NOT NULL,

    external_transaction_id VARCHAR(100),

    error_code VARCHAR(50) NOT NULL,

    error_message TEXT NOT NULL,

    rejected_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ingestion_errors_batch
    ON ingestion_errors(batch_id, created_at);

-- =========================================================
-- 5. ANALYTICS JOB MANAGEMENT
-- =========================================================

CREATE TABLE analytics_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_name VARCHAR(150) NOT NULL,

    requested_by BIGINT NOT NULL
        REFERENCES business_users(user_id),

    status job_status NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    records_processed INTEGER NOT NULL DEFAULT 0
        CHECK (records_processed >= 0),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        completed_at IS NULL OR started_at IS NOT NULL
    )
);

CREATE INDEX idx_jobs_status_created
    ON analytics_jobs(status, created_at DESC);

-- =========================================================
-- 6. AUTOMATION POLICIES
-- =========================================================

CREATE TABLE analytics_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL UNIQUE,

    minimum_profit_margin NUMERIC(8, 2) NOT NULL
        CHECK (
            minimum_profit_margin >= -100
            AND minimum_profit_margin <= 100
        ),

    maximum_anomaly_z_score NUMERIC(8, 3) NOT NULL
        CHECK (maximum_anomaly_z_score > 0),

    minimum_transaction_count INTEGER NOT NULL DEFAULT 1
        CHECK (minimum_transaction_count >= 1),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 7. KPI RESULTS
-- =========================================================

CREATE TABLE analytics_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES analytics_jobs(job_id),

    metric_name VARCHAR(100) NOT NULL,

    dimension_type VARCHAR(50) NOT NULL
        CHECK (
            dimension_type IN (
                'overall',
                'region',
                'product',
                'category',
                'month'
            )
        ),

    dimension_value VARCHAR(150) NOT NULL DEFAULT 'ALL',

    transaction_count INTEGER NOT NULL
        CHECK (transaction_count >= 0),

    units_sold BIGINT NOT NULL
        CHECK (units_sold >= 0),

    total_revenue NUMERIC(18, 2) NOT NULL,

    total_cost NUMERIC(18, 2) NOT NULL,

    total_profit NUMERIC(18, 2) NOT NULL,

    profit_margin NUMERIC(8, 2) NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        job_id,
        metric_name,
        dimension_type,
        dimension_value
    )
);

CREATE INDEX idx_results_job_dimension
    ON analytics_results(job_id, dimension_type);

-- =========================================================
-- 8. ANOMALY MANAGEMENT
-- =========================================================

CREATE TABLE analytics_anomalies (
    anomaly_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES analytics_jobs(job_id),

    transaction_id BIGINT NOT NULL
        REFERENCES sales_transactions(transaction_id),

    observed_revenue NUMERIC(18, 2) NOT NULL,

    z_score NUMERIC(12, 4) NOT NULL,

    anomaly_reason TEXT NOT NULL,

    is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,

    reviewed_by BIGINT
        REFERENCES business_users(user_id),

    reviewed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(job_id, transaction_id),

    CHECK (
        (is_reviewed = FALSE AND reviewed_at IS NULL)
        OR
        (is_reviewed = TRUE AND reviewed_at IS NOT NULL
            AND reviewed_by IS NOT NULL)
    )
);

-- =========================================================
-- 9. REPORT MANAGEMENT
-- =========================================================

CREATE TABLE analytics_reports (
    report_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_id BIGINT NOT NULL
        REFERENCES analytics_jobs(job_id),

    report_name VARCHAR(200) NOT NULL,

    report_format VARCHAR(20) NOT NULL
        CHECK (report_format IN ('json', 'csv')),

    report_data JSONB NOT NULL,

    status report_status NOT NULL DEFAULT 'generated',

    generated_by BIGINT NOT NULL
        REFERENCES business_users(user_id),

    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    published_at TIMESTAMPTZ,

    UNIQUE(job_id, report_name),

    CHECK (
        status <> 'published' OR published_at IS NOT NULL
    )
);

CREATE INDEX idx_reports_generated
    ON analytics_reports(generated_at DESC);

-- =========================================================
-- 10. AUDIT LOG
-- =========================================================

CREATE TABLE analytics_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    entity_type VARCHAR(100) NOT NULL,

    entity_id BIGINT,

    action VARCHAR(100) NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    executed_by TEXT NOT NULL DEFAULT CURRENT_USER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_entity
    ON analytics_audit(entity_type, entity_id, created_at DESC);

-- =========================================================
-- 11. JOB STATE VALIDATION
-- =========================================================

CREATE OR REPLACE FUNCTION validate_job_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'pending'
       AND NEW.status NOT IN ('running', 'failed') THEN
        RAISE EXCEPTION 'Invalid pending job transition';
    END IF;

    IF OLD.status = 'running'
       AND NEW.status NOT IN ('completed', 'failed') THEN
        RAISE EXCEPTION 'Invalid running job transition';
    END IF;

    IF OLD.status IN ('completed', 'failed')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'Terminal job state cannot be changed';
    END IF;

    IF NEW.status = 'running' AND NEW.started_at IS NULL THEN
        NEW.started_at := CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('completed', 'failed') THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_job_transition
BEFORE UPDATE OF status
ON analytics_jobs
FOR EACH ROW
EXECUTE FUNCTION validate_job_transition();

-- =========================================================
-- 12. AUDIT TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION audit_analytics_job()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO analytics_audit (
        entity_type,
        entity_id,
        action,
        details
    )
    VALUES (
        'analytics_job',
        NEW.job_id,
        'JOB_STATUS_CHANGED',
        jsonb_build_object(
            'old_status', OLD.status,
            'new_status', NEW.status,
            'job_name', NEW.job_name
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_job
AFTER UPDATE OF status
ON analytics_jobs
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION audit_analytics_job();

-- =========================================================
-- 13. KPI CALCULATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION calculate_sales_kpis(
    p_start_date DATE,
    p_end_date DATE
)
RETURNS TABLE (
    transaction_count BIGINT,
    units_sold BIGINT,
    total_revenue NUMERIC,
    total_cost NUMERIC,
    total_profit NUMERIC,
    profit_margin NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_start_date IS NULL
       OR p_end_date IS NULL
       OR p_start_date > p_end_date THEN
        RAISE EXCEPTION 'Invalid reporting date range';
    END IF;

    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT,
        COALESCE(SUM(s.quantity), 0)::BIGINT,
        COALESCE(SUM(s.revenue), 0),
        COALESCE(SUM(s.total_cost), 0),
        COALESCE(SUM(s.profit), 0),
        ROUND(
            COALESCE(
                SUM(s.profit) * 100.0 /
                NULLIF(SUM(s.revenue), 0),
                0
            ),
            2
        )
    FROM sales_transactions s
    WHERE s.transaction_date BETWEEN p_start_date AND p_end_date;
END;
$$;

-- =========================================================
-- 14. REGIONAL ANALYTICS VIEW
-- =========================================================

CREATE OR REPLACE VIEW regional_sales_performance AS
SELECT
    r.region_name,

    COUNT(s.transaction_id) AS transaction_count,

    COALESCE(SUM(s.quantity), 0) AS units_sold,

    COALESCE(SUM(s.revenue), 0) AS revenue,

    COALESCE(SUM(s.total_cost), 0) AS total_cost,

    COALESCE(SUM(s.profit), 0) AS profit,

    ROUND(
        COALESCE(
            SUM(s.profit) * 100.0 /
            NULLIF(SUM(s.revenue), 0),
            0
        ),
        2
    ) AS profit_margin_percent

FROM regions r
LEFT JOIN sales_transactions s
    ON s.region_id = r.region_id

GROUP BY r.region_id, r.region_name;

-- =========================================================
-- 15. PRODUCT ANALYTICS VIEW
-- =========================================================

CREATE OR REPLACE VIEW product_sales_performance AS
SELECT
    p.product_name,
    c.category_name,

    COUNT(s.transaction_id) AS transaction_count,

    COALESCE(SUM(s.quantity), 0) AS units_sold,

    COALESCE(SUM(s.revenue), 0) AS revenue,

    COALESCE(SUM(s.profit), 0) AS profit

FROM products p

JOIN product_categories c
    ON c.category_id = p.category_id

LEFT JOIN sales_transactions s
    ON s.product_id = p.product_id

GROUP BY
    p.product_id,
    p.product_name,
    c.category_name;

-- =========================================================
-- 16. MONTHLY ANALYTICS VIEW
-- =========================================================

CREATE OR REPLACE VIEW monthly_sales_performance AS
SELECT
    DATE_TRUNC('month', transaction_date)::DATE AS month,

    COUNT(*) AS transaction_count,

    SUM(quantity) AS units_sold,

    SUM(revenue) AS revenue,

    SUM(total_cost) AS total_cost,

    SUM(profit) AS profit,

    ROUND(
        SUM(profit) * 100.0 /
        NULLIF(SUM(revenue), 0),
        2
    ) AS margin_percent

FROM sales_transactions

GROUP BY DATE_TRUNC('month', transaction_date);

-- =========================================================
-- 17. AUTOMATED ANALYTICS PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE execute_analytics_job(
    p_job_id BIGINT,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job analytics_jobs%ROWTYPE;
    v_policy analytics_policies%ROWTYPE;
    v_start_date DATE;
    v_end_date DATE;
    v_count INTEGER;
    v_margin NUMERIC;
BEGIN
    SELECT *
    INTO v_job
    FROM analytics_jobs
    WHERE job_id = p_job_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Analytics job does not exist';
    END IF;

    IF v_job.status <> 'pending' THEN
        RAISE EXCEPTION 'Only pending jobs can be executed';
    END IF;

    SELECT *
    INTO v_policy
    FROM analytics_policies
    WHERE policy_id = p_policy_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active analytics policy not found';
    END IF;

    SELECT MIN(transaction_date), MAX(transaction_date)
    INTO v_start_date, v_end_date
    FROM sales_transactions;

    IF v_start_date IS NULL THEN
        RAISE EXCEPTION 'No sales data available';
    END IF;

    UPDATE analytics_jobs
    SET status = 'running'
    WHERE job_id = p_job_id;

    -- Overall KPI.
    INSERT INTO analytics_results (
        job_id,
        metric_name,
        dimension_type,
        dimension_value,
        transaction_count,
        units_sold,
        total_revenue,
        total_cost,
        total_profit,
        profit_margin
    )
    SELECT
        p_job_id,
        'sales_performance',
        'overall',
        'ALL',
        COUNT(*)::INTEGER,
        COALESCE(SUM(quantity), 0),
        COALESCE(SUM(revenue), 0),
        COALESCE(SUM(total_cost), 0),
        COALESCE(SUM(profit), 0),
        ROUND(
            COALESCE(
                SUM(profit) * 100.0 /
                NULLIF(SUM(revenue), 0),
                0
            ),
            2
        )
    FROM sales_transactions;

    -- Regional KPIs.
    INSERT INTO analytics_results (
        job_id,
        metric_name,
        dimension_type,
        dimension_value,
        transaction_count,
        units_sold,
        total_revenue,
        total_cost,
        total_profit,
        profit_margin
    )
    SELECT
        p_job_id,
        'sales_performance',
        'region',
        r.region_name,
        COUNT(s.transaction_id)::INTEGER,
        COALESCE(SUM(s.quantity), 0),
        COALESCE(SUM(s.revenue), 0),
        COALESCE(SUM(s.total_cost), 0),
        COALESCE(SUM(s.profit), 0),
        ROUND(
            COALESCE(
                SUM(s.profit) * 100.0 /
                NULLIF(SUM(s.revenue), 0),
                0
            ),
            2
        )
    FROM regions r
    JOIN sales_transactions s
        ON s.region_id = r.region_id
    GROUP BY r.region_id, r.region_name;

    -- Product KPIs.
    INSERT INTO analytics_results (
        job_id,
        metric_name,
        dimension_type,
        dimension_value,
        transaction_count,
        units_sold,
        total_revenue,
        total_cost,
        total_profit,
        profit_margin
    )
    SELECT
        p_job_id,
        'sales_performance',
        'product',
        p.product_name,
        COUNT(s.transaction_id)::INTEGER,
        COALESCE(SUM(s.quantity), 0),
        COALESCE(SUM(s.revenue), 0),
        COALESCE(SUM(s.total_cost), 0),
        COALESCE(SUM(s.profit), 0),
        ROUND(
            COALESCE(
                SUM(s.profit) * 100.0 /
                NULLIF(SUM(s.revenue), 0),
                0
            ),
            2
        )
    FROM products p
    JOIN sales_transactions s
        ON s.product_id = p.product_id
    GROUP BY p.product_id, p.product_name;

    -- Monthly KPIs.
    INSERT INTO analytics_results (
        job_id,
        metric_name,
        dimension_type,
        dimension_value,
        transaction_count,
        units_sold,
        total_revenue,
        total_cost,
        total_profit,
        profit_margin
    )
    SELECT
        p_job_id,
        'sales_performance',
        'month',
        TO_CHAR(transaction_date, 'YYYY-MM'),
        COUNT(*)::INTEGER,
        SUM(quantity),
        SUM(revenue),
        SUM(total_cost),
        SUM(profit),
        ROUND(
            COALESCE(
                SUM(profit) * 100.0 /
                NULLIF(SUM(revenue), 0),
                0
            ),
            2
        )
    FROM sales_transactions
    GROUP BY TO_CHAR(transaction_date, 'YYYY-MM');

    -- Apply minimum-volume policy to overall KPI.
    SELECT
        transaction_count,
        profit_margin
    INTO v_count, v_margin
    FROM analytics_results
    WHERE job_id = p_job_id
      AND dimension_type = 'overall';

    IF v_count < v_policy.minimum_transaction_count THEN
        RAISE EXCEPTION
            'Insufficient transactions for analytics policy';
    END IF;

    -- Record the job outcome.
    UPDATE analytics_jobs
    SET
        status = 'completed',
        records_processed = v_count
    WHERE job_id = p_job_id;

EXCEPTION
    WHEN OTHERS THEN
        -- Re-raise so the calling transaction can roll back
        -- partially written analytics results.
        RAISE;
END;
$$;

-- =========================================================
-- 18. SAMPLE MASTER DATA
-- =========================================================

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
SELECT 'Laptop', category_id
FROM product_categories
WHERE category_name = 'Electronics';

INSERT INTO products (product_name, category_id)
SELECT 'Phone', category_id
FROM product_categories
WHERE category_name = 'Electronics';

INSERT INTO products (product_name, category_id)
SELECT 'Desk', category_id
FROM product_categories
WHERE category_name = 'Furniture';

INSERT INTO products (product_name, category_id)
SELECT 'Chair', category_id
FROM product_categories
WHERE category_name = 'Furniture';

INSERT INTO business_users (username, role_name)
VALUES
    ('sales_analyst', 'analyst'),
    ('business_manager', 'manager'),
    ('system_admin', 'administrator'),
    ('report_viewer', 'viewer');

INSERT INTO analytics_policies (
    policy_name,
    minimum_profit_margin,
    maximum_anomaly_z_score,
    minimum_transaction_count
)
VALUES (
    'Standard Sales Analytics Policy',
    10.00,
    2.000,
    3
);

-- =========================================================
-- 19. SAMPLE TRANSACTION DATA
-- =========================================================

INSERT INTO sales_transactions (
    external_transaction_id,
    transaction_date,
    region_id,
    product_id,
    quantity,
    unit_price,
    cost_per_unit,
    source_system
)
SELECT
    data.external_id,
    data.transaction_date::DATE,
    r.region_id,
    p.product_id,
    data.quantity,
    data.unit_price,
    data.cost_per_unit,
    'sample_import'
FROM (
    VALUES
        ('T001', '2026-01-05', 'North', 'Laptop', 3, 75000, 60000),
        ('T002', '2026-01-08', 'South', 'Phone', 8, 25000, 18000),
        ('T003', '2026-01-12', 'East', 'Desk', 5, 12000, 8000),
        ('T004', '2026-02-03', 'West', 'Laptop', 4, 75000, 60000),
        ('T005', '2026-02-09', 'North', 'Chair', 10, 5000, 3000),
        ('T006', '2026-02-15', 'South', 'Phone', 12, 25000, 18000),
        ('T007', '2026-03-02', 'East', 'Desk', 7, 12000, 8000),
        ('T008', '2026-03-10', 'West', 'Laptop', 2, 75000, 60000),
        ('T009', '2026-03-18', 'North', 'Phone', 15, 25000, 18000),
        ('T010', '2026-03-22', 'South', 'Chair', 9, 5000, 3000),
        ('T011', '2026-04-04', 'East', 'Laptop', 30, 75000, 60000),
        ('T012', '2026-04-12', 'West', 'Desk', 6, 12000, 8000)
) AS data(
    external_id,
    transaction_date,
    region,
    product,
    quantity,
    unit_price,
    cost_per_unit
)
JOIN regions r
    ON r.region_name = data.region
JOIN products p
    ON p.product_name = data.product;

-- =========================================================
-- 20. SAMPLE INGESTION BATCH
-- =========================================================

INSERT INTO ingestion_batches (
    source_name,
    total_records,
    accepted_records,
    rejected_records,
    duplicate_records,
    completed_at
)
VALUES (
    'monthly_sales_import.csv',
    12,
    12,
    0,
    0,
    CURRENT_TIMESTAMP
);

-- =========================================================
-- 21. SAMPLE ANALYTICS JOB
-- =========================================================

INSERT INTO analytics_jobs (
    job_name,
    requested_by
)
SELECT
    'Quarterly Sales Performance Analysis',
    user_id
FROM business_users
WHERE username = 'sales_analyst';

-- =========================================================
-- 22. EXECUTE AUTOMATED ANALYTICS
-- =========================================================

BEGIN;

CALL execute_analytics_job(
    (
        SELECT job_id
        FROM analytics_jobs
        WHERE job_name = 'Quarterly Sales Performance Analysis'
    ),
    (
        SELECT policy_id
        FROM analytics_policies
        WHERE policy_name = 'Standard Sales Analytics Policy'
    )
);

COMMIT;

-- =========================================================
-- 23. RETRIEVAL: OVERALL KPIs
-- =========================================================

SELECT *
FROM calculate_sales_kpis(
    DATE '2026-01-01',
    DATE '2026-12-31'
);

-- =========================================================
-- 24. RETRIEVAL: REGIONAL PERFORMANCE
-- =========================================================

SELECT *
FROM regional_sales_performance
ORDER BY revenue DESC;

-- =========================================================
-- 25. RETRIEVAL: PRODUCT PERFORMANCE
-- =========================================================

SELECT *
FROM product_sales_performance
ORDER BY revenue DESC;

-- =========================================================
-- 26. MONTHLY REVENUE AND MOVING AVERAGE
-- =========================================================

WITH monthly AS (
    SELECT
        DATE_TRUNC('month', transaction_date)::DATE AS month,
        SUM(revenue) AS monthly_revenue
    FROM sales_transactions
    GROUP BY 1
),
trends AS (
    SELECT
        month,
        monthly_revenue,
        AVG(monthly_revenue) OVER (
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS moving_average
    FROM monthly
)
SELECT
    month,
    monthly_revenue,
    ROUND(moving_average, 2) AS moving_average
FROM trends
ORDER BY month;

-- =========================================================
-- 27. VALIDATION: NEGATIVE PROFIT TRANSACTIONS
-- =========================================================

SELECT
    external_transaction_id,
    transaction_date,
    profit
FROM sales_transactions
WHERE profit < 0
ORDER BY profit;

-- =========================================================
-- 28. EVALUATION: PROFITABILITY POLICY
-- =========================================================

SELECT
    r.region_name,
    r.profit_margin_percent,
    p.minimum_profit_margin,
    CASE
        WHEN r.transaction_count < p.minimum_transaction_count
            THEN 'INSUFFICIENT DATA'
        WHEN r.profit_margin_percent < p.minimum_profit_margin
            THEN 'REVIEW REQUIRED'
        ELSE 'POLICY PASSED'
    END AS evaluation_status
FROM regional_sales_performance r
CROSS JOIN analytics_policies p
WHERE p.is_active = TRUE;

-- =========================================================
-- 29. REPORT AGGREGATION
-- =========================================================

SELECT
    j.job_id,
    j.job_name,
    j.status,
    jsonb_agg(
        jsonb_build_object(
            'dimension', ar.dimension_type,
            'value', ar.dimension_value,
            'revenue', ar.total_revenue,
            'profit', ar.total_profit,
            'margin', ar.profit_margin
        )
        ORDER BY ar.dimension_type, ar.dimension_value
    ) AS analytics_data
FROM analytics_jobs j
JOIN analytics_results ar
    ON ar.job_id = j.job_id
GROUP BY j.job_id, j.job_name, j.status;

-- =========================================================
-- 30. PERSIST GENERATED REPORT
-- =========================================================

INSERT INTO analytics_reports (
    job_id,
    report_name,
    report_format,
    report_data,
    generated_by
)
SELECT
    j.job_id,
    'Sales Performance Report',
    'json',
    jsonb_build_object(
        'job_name', j.job_name,
        'status', j.status,
        'generated_at', CURRENT_TIMESTAMP,
        'metrics',
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'dimension', dimension_type,
                    'name', dimension_value,
                    'revenue', total_revenue,
                    'profit', total_profit,
                    'margin', profit_margin
                )
            )
            FROM analytics_results ar
            WHERE ar.job_id = j.job_id
        )
    ),
    j.requested_by
FROM analytics_jobs j
WHERE j.status = 'completed';

-- =========================================================
-- 31. REPORT PUBLICATION
-- =========================================================

UPDATE analytics_reports
SET
    status = 'published',
    published_at = CURRENT_TIMESTAMP
WHERE report_name = 'Sales Performance Report'
  AND status = 'generated';

-- =========================================================
-- 32. MANAGEMENT DASHBOARD QUERY
-- =========================================================

SELECT
    COUNT(*) AS total_transactions,
    SUM(quantity) AS units_sold,
    SUM(revenue) AS total_revenue,
    SUM(total_cost) AS total_cost,
    SUM(profit) AS total_profit,
    ROUND(
        SUM(profit) * 100.0 /
        NULLIF(SUM(revenue), 0),
        2
    ) AS profit_margin_percent
FROM sales_transactions;

-- =========================================================
-- 33. DATA QUALITY REPORT
-- =========================================================

SELECT
    COUNT(*) AS accepted_transactions,
    COUNT(DISTINCT external_transaction_id) AS unique_transactions,
    COUNT(*) FILTER (WHERE quantity < 0) AS invalid_quantities,
    COUNT(*) FILTER (WHERE unit_price < 0) AS invalid_prices,
    COUNT(*) FILTER (WHERE profit < 0) AS loss_transactions
FROM sales_transactions;

-- =========================================================
-- 34. JOB EXECUTION HISTORY
-- =========================================================

SELECT
    job_id,
    job_name,
    status,
    records_processed,
    started_at,
    completed_at,
    error_message
FROM analytics_jobs
ORDER BY created_at DESC;

-- =========================================================
-- 35. AUDIT HISTORY
-- =========================================================

SELECT
    entity_type,
    entity_id,
    action,
    details,
    executed_by,
    created_at
FROM analytics_audit
ORDER BY created_at DESC;

-- =========================================================
-- 36. AUTOMATED REPORT HISTORY
-- =========================================================

SELECT
    report_id,
    report_name,
    report_format,
    status,
    generated_at,
    published_at
FROM analytics_reports
ORDER BY generated_at DESC;

-- =========================================================
-- 37. FAILURE CASE: INVALID DUPLICATE TRANSACTION
-- =========================================================

-- Run independently to observe the unique constraint.
-- The following statement is intentionally not executed.

-- INSERT INTO sales_transactions (
--     external_transaction_id,
--     transaction_date,
--     region_id,
--     product_id,
--     quantity,
--     unit_price,
--     cost_per_unit
-- )
-- SELECT
--     'T001',
--     CURRENT_DATE,
--     r.region_id,
--     p.product_id,
--     1,
--     100,
--     50
-- FROM regions r
-- CROSS JOIN products p
-- WHERE r.region_name = 'North'
--   AND p.product_name = 'Laptop';

-- =========================================================
-- 38. FAILURE CASE: INVALID JOB TRANSITION
-- =========================================================

-- A completed job cannot be reopened by changing its status.
-- The trigger rejects such a transition.

-- UPDATE analytics_jobs
-- SET status = 'running'
-- WHERE status = 'completed';

-- =========================================================
-- 39. ANOMALY SCREENING QUERY
-- =========================================================

WITH revenue_statistics AS (
    SELECT
        AVG(revenue) AS average_revenue,
        STDDEV_POP(revenue) AS standard_deviation
    FROM sales_transactions
)
SELECT
    s.external_transaction_id,
    s.revenue,
    ROUND(
        (
            s.revenue - r.average_revenue
        ) / NULLIF(r.standard_deviation, 0),
        3
    ) AS z_score
FROM sales_transactions s
CROSS JOIN revenue_statistics r
WHERE r.standard_deviation > 0
  AND ABS(
      (s.revenue - r.average_revenue) /
      r.standard_deviation
  ) >= 2
ORDER BY ABS(
    (s.revenue - r.average_revenue) /
    r.standard_deviation
) DESC;

-- =========================================================
-- END OF BUSINESS ANALYTICS AUTOMATION SCRIPT
-- =========================================================
