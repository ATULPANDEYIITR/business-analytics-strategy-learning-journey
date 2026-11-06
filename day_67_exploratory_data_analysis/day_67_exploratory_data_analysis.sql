-- ============================================================
-- EXPLORATORY DATA ANALYSIS
-- PostgreSQL dataset profiling and analytical reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS eda;

SET search_path TO eda, public;

-- ------------------------------------------------------------
-- Dataset registry
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(150) NOT NULL,
    description TEXT,
    source_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    registered_by VARCHAR(100) NOT NULL,
    UNIQUE (dataset_name)
);

CREATE TABLE IF NOT EXISTS dataset_columns (
    column_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    column_name VARCHAR(100) NOT NULL,
    declared_type VARCHAR(30) NOT NULL
        CHECK (declared_type IN (
            'numeric', 'categorical', 'date', 'boolean'
        )),
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (dataset_id, column_name)
);

-- ------------------------------------------------------------
-- Analytical dataset: employee workforce information
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS employee_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    employee_id VARCHAR(30) NOT NULL,
    department VARCHAR(80),
    salary NUMERIC(14, 2),
    experience_years NUMERIC(6, 2),
    performance_rating NUMERIC(4, 2),
    observation_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source_record_id VARCHAR(100),

    CHECK (salary IS NULL OR salary >= 0),
    CHECK (
        experience_years IS NULL OR
        experience_years BETWEEN 0 AND 80
    ),
    CHECK (
        performance_rating IS NULL OR
        performance_rating BETWEEN 0 AND 5
    )
);

CREATE INDEX IF NOT EXISTS idx_employee_dataset
    ON employee_observations(dataset_id);

CREATE INDEX IF NOT EXISTS idx_employee_department
    ON employee_observations(dataset_id, department);

CREATE INDEX IF NOT EXISTS idx_employee_salary
    ON employee_observations(dataset_id, salary)
    WHERE salary IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_employee_source_record
    ON employee_observations(dataset_id, source_record_id);

-- ------------------------------------------------------------
-- Analysis execution tracking
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analysis_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),
    executed_by VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    run_status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (run_status IN (
            'running', 'completed', 'failed'
        )),
    failure_reason TEXT,

    CHECK (
        (run_status = 'running' AND completed_at IS NULL)
        OR
        (run_status IN ('completed', 'failed')
            AND completed_at IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS column_profiles (
    profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    column_name VARCHAR(100) NOT NULL,
    inferred_type VARCHAR(30) NOT NULL,
    total_count BIGINT NOT NULL CHECK (total_count >= 0),
    missing_count BIGINT NOT NULL CHECK (
        missing_count BETWEEN 0 AND total_count
    ),
    unique_count BIGINT NOT NULL CHECK (
        unique_count BETWEEN 0 AND total_count - missing_count
    ),
    minimum_value NUMERIC,
    maximum_value NUMERIC,
    mean_value NUMERIC,
    median_value NUMERIC,
    standard_deviation NUMERIC,
    q1_value NUMERIC,
    q3_value NUMERIC,
    iqr_value NUMERIC,
    UNIQUE (run_id, column_name)
);

CREATE TABLE IF NOT EXISTS quality_issues (
    issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    column_name VARCHAR(100),
    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical')),
    issue_type VARCHAR(50) NOT NULL,
    issue_description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_run_severity
    ON quality_issues(run_id, severity);

-- ------------------------------------------------------------
-- Sample dataset
-- ------------------------------------------------------------

INSERT INTO datasets (
    dataset_name,
    description,
    source_name,
    registered_by
)
VALUES (
    'employee_workforce',
    'Workforce dataset for exploratory statistical analysis.',
    'HR analytics sample',
    'data_analyst'
)
ON CONFLICT (dataset_name) DO NOTHING;

INSERT INTO dataset_columns (
    dataset_id,
    column_name,
    declared_type,
    is_required
)
SELECT
    d.dataset_id,
    v.column_name,
    v.declared_type,
    v.is_required
FROM datasets d
CROSS JOIN (
    VALUES
        ('employee_id', 'categorical', TRUE),
        ('department', 'categorical', FALSE),
        ('salary', 'numeric', FALSE),
        ('experience_years', 'numeric', FALSE),
        ('performance_rating', 'numeric', FALSE)
) AS v(column_name, declared_type, is_required)
WHERE d.dataset_name = 'employee_workforce'
ON CONFLICT (dataset_id, column_name) DO NOTHING;

INSERT INTO employee_observations (
    dataset_id,
    employee_id,
    department,
    salary,
    experience_years,
    performance_rating,
    source_record_id
)
SELECT
    d.dataset_id,
    v.employee_id,
    v.department,
    v.salary,
    v.experience_years,
    v.performance_rating,
    v.source_record_id
FROM datasets d
CROSS JOIN (
    VALUES
        ('E001', 'Engineering', 85000::NUMERIC, 5::NUMERIC, 4.5::NUMERIC, 'SRC001'),
        ('E002', 'Analytics', 72000, 3, 4.2, 'SRC002'),
        ('E003', 'Engineering', 95000, 8, 4.8, 'SRC003'),
        ('E004', 'Operations', 61000, 2, 3.9, 'SRC004'),
        ('E005', 'Analytics', 78000, 4, 4.4, 'SRC005'),
        ('E006', 'Engineering', 110000, 12, 4.9, 'SRC006'),
        ('E007', 'Operations', NULL, 3, 3.7, 'SRC007'),
        ('E008', 'Analytics', 75000, 4, NULL, 'SRC008'),
        ('E009', 'Engineering', 85000, 5, 4.5, 'SRC009'),
        ('E010', 'Operations', 58000, 1, 3.5, 'SRC010'),
        ('E010', 'Operations', 58000, 1, 3.5, 'SRC010')
) AS v(
    employee_id,
    department,
    salary,
    experience_years,
    performance_rating,
    source_record_id
)
WHERE d.dataset_name = 'employee_workforce'
AND NOT EXISTS (
    SELECT 1
    FROM employee_observations existing
    WHERE existing.dataset_id = d.dataset_id
      AND existing.source_record_id = v.source_record_id
      AND existing.employee_id = v.employee_id
);

-- ------------------------------------------------------------
-- Basic dataset retrieval
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_employee_dataset AS
SELECT
    o.observation_id,
    d.dataset_name,
    o.employee_id,
    o.department,
    o.salary,
    o.experience_years,
    o.performance_rating,
    o.observation_date,
    o.source_record_id
FROM employee_observations o
JOIN datasets d USING (dataset_id);

-- ------------------------------------------------------------
-- Dataset-level descriptive statistics
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_numeric_summary AS
SELECT
    dataset_id,
    COUNT(*) AS total_rows,
    COUNT(salary) AS salary_valid_count,
    AVG(salary) AS average_salary,
    PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY salary) AS median_salary,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary,
    STDDEV_SAMP(salary) AS salary_standard_deviation,
    VAR_SAMP(salary) AS salary_variance,
    COUNT(*) FILTER (WHERE salary IS NULL) AS missing_salary,
    COUNT(experience_years) AS valid_experience_count,
    AVG(experience_years) AS average_experience,
    COUNT(performance_rating) AS valid_rating_count,
    AVG(performance_rating) AS average_rating
FROM employee_observations
GROUP BY dataset_id;

-- ------------------------------------------------------------
-- Missing-value analysis
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_missing_value_report AS
SELECT
    dataset_id,
    'department' AS column_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE department IS NULL OR BTRIM(department) = ''
    ) AS missing_count
FROM employee_observations
GROUP BY dataset_id

UNION ALL

SELECT
    dataset_id,
    'salary',
    COUNT(*),
    COUNT(*) FILTER (WHERE salary IS NULL)
FROM employee_observations
GROUP BY dataset_id

UNION ALL

SELECT
    dataset_id,
    'experience_years',
    COUNT(*),
    COUNT(*) FILTER (WHERE experience_years IS NULL)
FROM employee_observations
GROUP BY dataset_id

UNION ALL

SELECT
    dataset_id,
    'performance_rating',
    COUNT(*),
    COUNT(*) FILTER (WHERE performance_rating IS NULL)
FROM employee_observations
GROUP BY dataset_id;

-- ------------------------------------------------------------
-- Duplicate detection
-- Duplicate groups are based on the complete analytical record.
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_duplicate_records AS
SELECT
    dataset_id,
    employee_id,
    department,
    salary,
    experience_years,
    performance_rating,
    source_record_id,
    COUNT(*) AS occurrence_count
FROM employee_observations
GROUP BY
    dataset_id,
    employee_id,
    department,
    salary,
    experience_years,
    performance_rating,
    source_record_id
HAVING COUNT(*) > 1;

-- ------------------------------------------------------------
-- Categorical distribution
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_department_distribution AS
SELECT
    dataset_id,
    department,
    COUNT(*) AS record_count,
    ROUND(
        COUNT(*) * 100.0 /
        NULLIF(SUM(COUNT(*)) OVER (
            PARTITION BY dataset_id
        ), 0),
        2
    ) AS percentage
FROM employee_observations
WHERE department IS NOT NULL
GROUP BY dataset_id, department;

-- ------------------------------------------------------------
-- Outlier detection using the IQR rule.
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_salary_outliers AS
WITH quartiles AS (
    SELECT
        dataset_id,
        PERCENTILE_CONT(0.25)
            WITHIN GROUP (ORDER BY salary) AS q1,
        PERCENTILE_CONT(0.75)
            WITHIN GROUP (ORDER BY salary) AS q3
    FROM employee_observations
    WHERE salary IS NOT NULL
    GROUP BY dataset_id
),
bounds AS (
    SELECT
        dataset_id,
        q1,
        q3,
        q3 - q1 AS iqr,
        q1 - 1.5 * (q3 - q1) AS lower_bound,
        q3 + 1.5 * (q3 - q1) AS upper_bound
    FROM quartiles
)
SELECT
    o.observation_id,
    o.dataset_id,
    o.employee_id,
    o.department,
    o.salary,
    b.q1,
    b.q3,
    b.iqr,
    b.lower_bound,
    b.upper_bound
FROM employee_observations o
JOIN bounds b USING (dataset_id)
WHERE o.salary IS NOT NULL
AND (
    o.salary < b.lower_bound
    OR o.salary > b.upper_bound
);

-- ------------------------------------------------------------
-- Correlation analysis
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_salary_experience_correlation AS
SELECT
    dataset_id,
    COUNT(*) AS paired_observations,
    CORR(salary, experience_years) AS pearson_correlation
FROM employee_observations
WHERE salary IS NOT NULL
AND experience_years IS NOT NULL
GROUP BY dataset_id;

-- ------------------------------------------------------------
-- Grouped analytical reporting
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_department_salary_analysis AS
SELECT
    dataset_id,
    department,
    COUNT(*) AS employee_records,
    COUNT(salary) AS valid_salary_records,
    AVG(salary) AS average_salary,
    PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY salary) AS median_salary,
    MIN(salary) AS minimum_salary,
    MAX(salary) AS maximum_salary,
    STDDEV_SAMP(salary) AS salary_standard_deviation,
    AVG(experience_years) AS average_experience
FROM employee_observations
WHERE department IS NOT NULL
GROUP BY dataset_id, department;

-- ------------------------------------------------------------
-- Reusable analysis execution procedure.
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE run_eda(
    p_dataset_id BIGINT,
    p_executed_by VARCHAR DEFAULT 'data_analyst'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_total BIGINT;
    v_missing BIGINT;
    v_duplicates BIGINT;
    v_q1 NUMERIC;
    v_q3 NUMERIC;
    v_min NUMERIC;
    v_max NUMERIC;
    v_mean NUMERIC;
    v_median NUMERIC;
    v_stddev NUMERIC;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION 'Dataset % does not exist.', p_dataset_id;
    END IF;

    INSERT INTO analysis_runs (
        dataset_id,
        executed_by
    )
    VALUES (
        p_dataset_id,
        p_executed_by
    )
    RETURNING run_id INTO v_run_id;

    BEGIN
        SELECT
            COUNT(*),
            COUNT(*) FILTER (WHERE salary IS NULL),
            PERCENTILE_CONT(0.25)
                WITHIN GROUP (ORDER BY salary),
            PERCENTILE_CONT(0.75)
                WITHIN GROUP (ORDER BY salary),
            MIN(salary),
            MAX(salary),
            AVG(salary),
            PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY salary),
            STDDEV_SAMP(salary)
        INTO
            v_total,
            v_missing,
            v_q1,
            v_q3,
            v_min,
            v_max,
            v_mean,
            v_median,
            v_stddev
        FROM employee_observations
        WHERE dataset_id = p_dataset_id;

        INSERT INTO column_profiles (
            run_id,
            column_name,
            inferred_type,
            total_count,
            missing_count,
            unique_count,
            minimum_value,
            maximum_value,
            mean_value,
            median_value,
            standard_deviation,
            q1_value,
            q3_value,
            iqr_value
        )
        SELECT
            v_run_id,
            'salary',
            'numeric',
            COUNT(*),
            COUNT(*) FILTER (WHERE salary IS NULL),
            COUNT(DISTINCT salary),
            v_min,
            v_max,
            v_mean,
            v_median,
            v_stddev,
            v_q1,
            v_q3,
            v_q3 - v_q1
        FROM employee_observations
        WHERE dataset_id = p_dataset_id;

        INSERT INTO quality_issues (
            run_id,
            column_name,
            severity,
            issue_type,
            issue_description
        )
        SELECT
            v_run_id,
            'salary',
            'warning',
            'missing_values',
            format(
                'Salary is missing in %s of %s records.',
                v_missing,
                v_total
            )
        WHERE v_missing > 0;

        SELECT COALESCE(SUM(occurrence_count - 1), 0)
        INTO v_duplicates
        FROM v_duplicate_records
        WHERE dataset_id = p_dataset_id;

        IF v_duplicates > 0 THEN
            INSERT INTO quality_issues (
                run_id,
                column_name,
                severity,
                issue_type,
                issue_description
            )
            VALUES (
                v_run_id,
                NULL,
                'warning',
                'duplicate_records',
                format(
                    '%s repeated records detected.',
                    v_duplicates
                )
            );
        END IF;

        INSERT INTO quality_issues (
            run_id,
            column_name,
            severity,
            issue_type,
            issue_description
        )
        SELECT
            v_run_id,
            'salary',
            'info',
            'outlier',
            format(
                'Salary value %s for employee %s is outside the IQR bounds.',
                o.salary,
                o.employee_id
            )
        FROM v_salary_outliers o
        WHERE o.dataset_id = p_dataset_id;

        UPDATE analysis_runs
        SET
            run_status = 'completed',
            completed_at = CURRENT_TIMESTAMP
        WHERE run_id = v_run_id;

    EXCEPTION WHEN OTHERS THEN
        UPDATE analysis_runs
        SET
            run_status = 'failed',
            completed_at = CURRENT_TIMESTAMP,
            failure_reason = SQLERRM
        WHERE run_id = v_run_id;

        RAISE;
    END;
END;
$$;

-- ------------------------------------------------------------
-- Trigger: protect analysis-run state transitions.
-- Completed and failed runs are immutable.
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_analysis_run_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.run_status <> 'running' THEN
        RAISE EXCEPTION
            'A finalized analysis run cannot be modified.';
    END IF;

    IF NEW.run_status = 'running' AND NEW.completed_at IS NOT NULL THEN
        RAISE EXCEPTION
            'Running analysis cannot have a completion timestamp.';
    END IF;

    IF NEW.run_status IN ('completed', 'failed')
       AND NEW.completed_at IS NULL THEN
        RAISE EXCEPTION
            'Finalized analysis requires a completion timestamp.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_analysis_run_transition
    ON analysis_runs;

CREATE TRIGGER trg_analysis_run_transition
BEFORE UPDATE ON analysis_runs
FOR EACH ROW
EXECUTE FUNCTION enforce_analysis_run_transition();

-- ------------------------------------------------------------
-- Run the analysis workflow.
-- ------------------------------------------------------------

DO $$
DECLARE
    v_dataset_id BIGINT;
BEGIN
    SELECT dataset_id
    INTO v_dataset_id
    FROM datasets
    WHERE dataset_name = 'employee_workforce';

    CALL run_eda(v_dataset_id, 'eda_operator');
END;
$$;

-- ------------------------------------------------------------
-- Retrieval queries
-- ------------------------------------------------------------

SELECT *
FROM v_employee_dataset
ORDER BY observation_id;

-- ------------------------------------------------------------
-- Descriptive statistics
-- ------------------------------------------------------------

SELECT *
FROM v_numeric_summary;

-- ------------------------------------------------------------
-- Missing-value evaluation
-- ------------------------------------------------------------

SELECT
    column_name,
    total_rows,
    missing_count,
    ROUND(
        missing_count * 100.0 / NULLIF(total_rows, 0),
        2
    ) AS missing_percentage
FROM v_missing_value_report
ORDER BY column_name;

-- ------------------------------------------------------------
-- Duplicate-record evaluation
-- ------------------------------------------------------------

SELECT *
FROM v_duplicate_records
ORDER BY occurrence_count DESC;

-- ------------------------------------------------------------
-- Department aggregation
-- ------------------------------------------------------------

SELECT *
FROM v_department_salary_analysis
ORDER BY average_salary DESC;

-- ------------------------------------------------------------
-- Outlier reporting
-- ------------------------------------------------------------

SELECT *
FROM v_salary_outliers
ORDER BY salary DESC;

-- ------------------------------------------------------------
-- Correlation reporting
-- ------------------------------------------------------------

SELECT *
FROM v_salary_experience_correlation;

-- ------------------------------------------------------------
-- Analysis execution history
-- ------------------------------------------------------------

SELECT
    r.run_id,
    d.dataset_name,
    r.executed_by,
    r.started_at,
    r.completed_at,
    r.run_status,
    r.failure_reason
FROM analysis_runs r
JOIN datasets d USING (dataset_id)
ORDER BY r.run_id DESC;

-- ------------------------------------------------------------
-- Quality issue report
-- ------------------------------------------------------------

SELECT
    r.run_id,
    q.column_name,
    q.severity,
    q.issue_type,
    q.issue_description
FROM quality_issues q
JOIN analysis_runs r USING (run_id)
ORDER BY
    r.run_id,
    CASE q.severity
        WHEN 'critical' THEN 1
        WHEN 'warning' THEN 2
        ELSE 3
    END;

-- ------------------------------------------------------------
-- Eligibility determination:
-- A dataset is eligible for basic exploratory reporting when
-- it contains observations and has no missing employee IDs.
-- This is a reporting rule, not a statistical quality guarantee.
-- ------------------------------------------------------------

SELECT
    d.dataset_name,
    COUNT(o.observation_id) AS total_records,
    COUNT(*) FILTER (
        WHERE o.employee_id IS NULL
        OR BTRIM(o.employee_id) = ''
    ) AS invalid_employee_ids,
    CASE
        WHEN COUNT(o.observation_id) > 0
         AND COUNT(*) FILTER (
             WHERE o.employee_id IS NULL
             OR BTRIM(o.employee_id) = ''
         ) = 0
        THEN 'eligible'
        ELSE 'not_eligible'
    END AS reporting_eligibility
FROM datasets d
LEFT JOIN employee_observations o USING (dataset_id)
GROUP BY d.dataset_id, d.dataset_name;

COMMIT;
