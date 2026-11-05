-- Business visualization data warehouse.
-- PostgreSQL 15+.

CREATE SCHEMA IF NOT EXISTS business_analytics;

SET search_path TO business_analytics, public;

DROP VIEW IF EXISTS monthly_business_dashboard CASCADE;
DROP VIEW IF EXISTS quarterly_business_summary CASCADE;
DROP VIEW IF EXISTS target_performance CASCADE;
DROP TABLE IF EXISTS visualization_audit CASCADE;
DROP TABLE IF EXISTS report_jobs CASCADE;
DROP TABLE IF EXISTS monthly_metrics CASCADE;
DROP TABLE IF EXISTS reporting_periods CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

CREATE TABLE departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reporting_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_name VARCHAR(20) NOT NULL UNIQUE,
    period_start DATE NOT NULL UNIQUE,
    period_end DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    quarter_number INTEGER NOT NULL CHECK (
        quarter_number BETWEEN 1 AND 4
    ),
    CHECK (period_end >= period_start)
);

CREATE TABLE monthly_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    department_id BIGINT NOT NULL
        REFERENCES departments(department_id),

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    revenue NUMERIC(16, 2) NOT NULL CHECK (revenue >= 0),
    expenses NUMERIC(16, 2) NOT NULL CHECK (expenses >= 0),
    orders INTEGER NOT NULL CHECK (orders >= 0),
    customers INTEGER NOT NULL CHECK (customers >= 0),
    revenue_target NUMERIC(16, 2) NOT NULL CHECK (
        revenue_target > 0
    ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_department_period
        UNIQUE (department_id, period_id),

    CONSTRAINT customers_not_exceed_orders
        CHECK (customers <= orders)
);

CREATE TABLE report_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    report_name VARCHAR(150) NOT NULL,
    requested_by VARCHAR(100) NOT NULL,

    report_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (
            report_status IN (
                'PENDING',
                'RUNNING',
                'COMPLETED',
                'FAILED'
            )
        ),

    output_format VARCHAR(10) NOT NULL
        CHECK (output_format IN ('CSV', 'JSON', 'PDF')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CHECK (
        (report_status = 'COMPLETED' AND completed_at IS NOT NULL)
        OR
        (report_status <> 'COMPLETED')
    )
);

CREATE TABLE visualization_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT REFERENCES report_jobs(job_id),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes support department, reporting-period and workflow queries.
CREATE INDEX idx_metrics_period
    ON monthly_metrics(period_id);

CREATE INDEX idx_metrics_department_period
    ON monthly_metrics(department_id, period_id);

CREATE INDEX idx_reporting_fiscal_year
    ON reporting_periods(fiscal_year, quarter_number);

CREATE INDEX idx_report_jobs_status_created
    ON report_jobs(report_status, created_at DESC);

CREATE INDEX idx_visualization_audit_job
    ON visualization_audit(job_id, occurred_at DESC);

-- Update timestamps automatically when business metrics change.
CREATE OR REPLACE FUNCTION update_metric_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_metric_timestamp
BEFORE UPDATE ON monthly_metrics
FOR EACH ROW
EXECUTE FUNCTION update_metric_timestamp();

-- Dashboard view provides the measures needed by business reporting.
CREATE VIEW monthly_business_dashboard AS
SELECT
    d.department_name,
    d.department_code,
    p.period_name,
    p.period_start,
    p.fiscal_year,
    p.quarter_number,

    m.revenue,
    m.expenses,

    m.revenue - m.expenses AS profit,

    ROUND(
        CASE
            WHEN m.revenue = 0 THEN 0
            ELSE
                (m.revenue - m.expenses) / m.revenue * 100
        END,
        2
    ) AS profit_margin,

    m.orders,
    m.customers,

    ROUND(
        CASE
            WHEN m.orders = 0 THEN 0
            ELSE m.customers::NUMERIC / m.orders * 100
        END,
        2
    ) AS customer_order_ratio,

    m.revenue_target,

    ROUND(
        m.revenue / m.revenue_target * 100,
        2
    ) AS target_achievement,

    ROUND(
        CASE
            WHEN m.revenue = 0 THEN 0
            ELSE m.expenses / m.revenue * 100
        END,
        2
    ) AS expense_ratio,

    CASE
        WHEN m.revenue >= m.revenue_target THEN 'ACHIEVED'
        ELSE 'BELOW_TARGET'
    END AS target_status

FROM monthly_metrics m
JOIN departments d
    ON d.department_id = m.department_id
JOIN reporting_periods p
    ON p.period_id = m.period_id;

-- Target evaluation is kept separate from dashboard presentation.
CREATE VIEW target_performance AS
SELECT
    department_name,
    period_name,
    revenue,
    revenue_target,
    target_achievement,
    target_status
FROM monthly_business_dashboard;

-- Quarter-level aggregation supports management reporting.
CREATE VIEW quarterly_business_summary AS
SELECT
    department_name,
    fiscal_year,
    quarter_number,

    SUM(revenue) AS total_revenue,
    SUM(expenses) AS total_expenses,
    SUM(profit) AS total_profit,
    SUM(orders) AS total_orders,
    SUM(customers) AS total_customers,

    ROUND(
        SUM(profit) / NULLIF(SUM(revenue), 0) * 100,
        2
    ) AS profit_margin,

    ROUND(
        SUM(revenue) / NULLIF(SUM(revenue_target), 0) * 100,
        2
    ) AS target_achievement

FROM monthly_business_dashboard
GROUP BY
    department_name,
    fiscal_year,
    quarter_number;

-- Evaluate whether a report can be processed.
CREATE OR REPLACE FUNCTION evaluate_report_eligibility(
    p_job_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    current_status VARCHAR(20);
    has_data BOOLEAN;
BEGIN
    SELECT report_status
    INTO current_status
    FROM report_jobs
    WHERE job_id = p_job_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Report job % does not exist', p_job_id;
    END IF;

    IF current_status <> 'PENDING' THEN
        RETURN FALSE;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM monthly_metrics
    )
    INTO has_data;

    RETURN has_data;
END;
$$;

-- Atomic state transition for report processing.
CREATE OR REPLACE PROCEDURE process_report(
    p_job_id BIGINT,
    p_actor VARCHAR(100)
)
LANGUAGE plpgsql
AS $$
DECLARE
    eligible BOOLEAN;
BEGIN
    eligible := evaluate_report_eligibility(p_job_id);

    IF NOT eligible THEN
        RAISE EXCEPTION
            'Report job % is not eligible for processing',
            p_job_id;
    END IF;

    UPDATE report_jobs
    SET report_status = 'RUNNING'
    WHERE job_id = p_job_id;

    INSERT INTO visualization_audit (
        job_id,
        action,
        actor,
        details
    )
    VALUES (
        p_job_id,
        'REPORT_STARTED',
        p_actor,
        jsonb_build_object(
            'status', 'RUNNING'
        )
    );
END;
$$;

-- Completion operation records successful publication.
CREATE OR REPLACE PROCEDURE complete_report(
    p_job_id BIGINT,
    p_actor VARCHAR(100)
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE report_jobs
    SET
        report_status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP,
        error_message = NULL
    WHERE job_id = p_job_id
      AND report_status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Only running reports can be completed';
    END IF;

    INSERT INTO visualization_audit (
        job_id,
        action,
        actor,
        details
    )
    VALUES (
        p_job_id,
        'REPORT_COMPLETED',
        p_actor,
        jsonb_build_object(
            'status', 'COMPLETED'
        )
    );
END;
$$;

-- Failure operation records the reason without deleting the job.
CREATE OR REPLACE PROCEDURE fail_report(
    p_job_id BIGINT,
    p_actor VARCHAR(100),
    p_reason TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_reason IS NULL OR LENGTH(TRIM(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Failure reason is required';
    END IF;

    UPDATE report_jobs
    SET
        report_status = 'FAILED',
        completed_at = CURRENT_TIMESTAMP,
        error_message = LEFT(p_reason, 2000)
    WHERE job_id = p_job_id
      AND report_status IN ('PENDING', 'RUNNING');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Report cannot transition to FAILED';
    END IF;

    INSERT INTO visualization_audit (
        job_id,
        action,
        actor,
        details
    )
    VALUES (
        p_job_id,
        'REPORT_FAILED',
        p_actor,
        jsonb_build_object(
            'reason', LEFT(p_reason, 500)
        )
    );
END;
$$;

-- Department and period reference data.
INSERT INTO departments (
    department_name,
    department_code
)
VALUES
    ('Retail Sales', 'RETAIL'),
    ('Enterprise Sales', 'ENTERPRISE'),
    ('Digital Commerce', 'DIGITAL');

INSERT INTO reporting_periods (
    period_name,
    period_start,
    period_end,
    fiscal_year,
    quarter_number
)
VALUES
    ('January', '2026-01-01', '2026-01-31', 2026, 1),
    ('February', '2026-02-01', '2026-02-28', 2026, 1),
    ('March', '2026-03-01', '2026-03-31', 2026, 1),
    ('April', '2026-04-01', '2026-04-30', 2026, 2),
    ('May', '2026-05-01', '2026-05-31', 2026, 2),
    ('June', '2026-06-01', '2026-06-30', 2026, 2),
    ('July', '2026-07-01', '2026-07-31', 2026, 3),
    ('August', '2026-08-01', '2026-08-31', 2026, 3),
    ('September', '2026-09-01', '2026-09-30', 2026, 3),
    ('October', '2026-10-01', '2026-10-31', 2026, 4),
    ('November', '2026-11-01', '2026-11-30', 2026, 4),
    ('December', '2026-12-01', '2026-12-31', 2026, 4);

-- Retail department monthly data.
INSERT INTO monthly_metrics (
    department_id,
    period_id,
    revenue,
    expenses,
    orders,
    customers,
    revenue_target
)
SELECT
    d.department_id,
    p.period_id,
    v.revenue,
    v.expenses,
    v.orders,
    v.customers,
    v.target
FROM departments d
CROSS JOIN (
    VALUES
    ('January', 450000, 310000, 420, 350, 430000),
    ('February', 480000, 325000, 450, 370, 450000),
    ('March', 520000, 340000, 490, 395, 500000),
    ('April', 495000, 350000, 465, 380, 510000),
    ('May', 560000, 365000, 530, 425, 530000),
    ('June', 590000, 375000, 560, 445, 550000),
    ('July', 610000, 390000, 580, 460, 580000),
    ('August', 575000, 385000, 550, 440, 590000),
    ('September', 650000, 405000, 610, 490, 620000),
    ('October', 680000, 420000, 640, 510, 650000),
    ('November', 710000, 440000, 670, 535, 680000),
    ('December', 780000, 465000, 740, 590, 720000)
) AS v(period_name, revenue, expenses, orders, customers, target)
JOIN reporting_periods p
    ON p.period_name = v.period_name
WHERE d.department_code = 'RETAIL';

-- Additional department records demonstrate multi-department reporting.
INSERT INTO monthly_metrics (
    department_id,
    period_id,
    revenue,
    expenses,
    orders,
    customers,
    revenue_target
)
SELECT
    d.department_id,
    p.period_id,
    CASE d.department_code
        WHEN 'ENTERPRISE' THEN 850000 + p.period_id * 15000
        ELSE 620000 + p.period_id * 12000
    END,
    CASE d.department_code
        WHEN 'ENTERPRISE' THEN 520000 + p.period_id * 8000
        ELSE 400000 + p.period_id * 6000
    END,
    200 + p.period_id * 12,
    150 + p.period_id * 10,
    CASE d.department_code
        WHEN 'ENTERPRISE' THEN 830000 + p.period_id * 14000
        ELSE 610000 + p.period_id * 11000
    END
FROM departments d
CROSS JOIN reporting_periods p
WHERE d.department_code IN ('ENTERPRISE', 'DIGITAL');

-- Report job examples.
INSERT INTO report_jobs (
    report_name,
    requested_by,
    output_format
)
VALUES
    ('Monthly Executive Dashboard', 'finance_manager', 'CSV'),
    ('Quarterly Sales Report', 'sales_director', 'JSON'),
    ('Profitability Analysis', 'business_analyst', 'PDF'),
    ('Failed Export Simulation', 'system_operator', 'CSV');

-- Retrieval: monthly business dashboard.
SELECT *
FROM monthly_business_dashboard
ORDER BY department_name, period_start;

-- Validation: identify reporting periods below target.
SELECT *
FROM target_performance
WHERE target_status = 'BELOW_TARGET'
ORDER BY target_achievement;

-- Aggregation: quarterly department performance.
SELECT *
FROM quarterly_business_summary
ORDER BY fiscal_year, quarter_number, department_name;

-- Evaluation: weighted business margin and target achievement.
SELECT
    department_name,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND(
        SUM(profit) / NULLIF(SUM(revenue), 0) * 100,
        2
    ) AS weighted_profit_margin,
    ROUND(
        SUM(revenue) / NULLIF(SUM(revenue_target), 0) * 100,
        2
    ) AS weighted_target_achievement
FROM monthly_business_dashboard
GROUP BY department_name;

-- Reporting: rank departments by total revenue.
WITH department_totals AS (
    SELECT
        department_name,
        SUM(revenue) AS total_revenue,
        SUM(profit) AS total_profit
    FROM monthly_business_dashboard
    GROUP BY department_name
)
SELECT
    department_name,
    total_revenue,
    total_profit,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM department_totals;

-- Workflow processing: start, complete and audit a report.
BEGIN;

CALL process_report(1, 'finance_manager');
CALL complete_report(1, 'finance_manager');

COMMIT;

-- Failure simulation for a separate report.
BEGIN;

CALL process_report(4, 'system_operator');
CALL fail_report(
    4,
    'system_operator',
    'Simulated storage write failure'
);

COMMIT;

-- Eligibility determination.
SELECT
    job_id,
    report_name,
    report_status,
    evaluate_report_eligibility(job_id) AS eligible
FROM report_jobs
WHERE report_status = 'PENDING';

-- Report workflow history.
SELECT
    j.report_name,
    j.report_status,
    a.action,
    a.actor,
    a.details,
    a.occurred_at
FROM report_jobs j
LEFT JOIN visualization_audit a
    ON a.job_id = j.job_id
ORDER BY j.job_id, a.occurred_at;

-- Three-month moving average using a window function.
WITH revenue_windows AS (
    SELECT
        department_name,
        period_name,
        period_start,
        revenue,
        AVG(revenue) OVER (
            PARTITION BY department_name
            ORDER BY period_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS moving_average,
        COUNT(*) OVER (
            PARTITION BY department_name
            ORDER BY period_start
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS observations
    FROM monthly_business_dashboard
)
SELECT
    department_name,
    period_name,
    revenue,
    ROUND(moving_average, 2) AS moving_average
FROM revenue_windows
WHERE observations = 3
ORDER BY department_name, period_start;

-- Detect unusually high revenue using population standard deviation.
WITH statistics AS (
    SELECT
        department_name,
        AVG(revenue) AS average_revenue,
        STDDEV_POP(revenue) AS standard_deviation
    FROM monthly_business_dashboard
    GROUP BY department_name
)
SELECT
    b.department_name,
    b.period_name,
    b.revenue,
    ROUND(s.average_revenue, 2) AS average_revenue
FROM monthly_business_dashboard b
JOIN statistics s
    ON s.department_name = b.department_name
WHERE s.standard_deviation > 0
  AND ABS(
      b.revenue - s.average_revenue
  ) > 1.5 * s.standard_deviation
ORDER BY b.department_name, b.period_start;

-- JSON reporting payload.
SELECT jsonb_build_object(
    'generated_at', CURRENT_TIMESTAMP,
    'departments', (
        SELECT jsonb_agg(
            jsonb_build_object(
                'department', department_name,
                'revenue', total_revenue,
                'profit', total_profit,
                'margin', profit_margin,
                'target_achievement', target_achievement
            )
        )
        FROM quarterly_business_summary
        WHERE fiscal_year = 2026
    )
) AS executive_dashboard_json;
