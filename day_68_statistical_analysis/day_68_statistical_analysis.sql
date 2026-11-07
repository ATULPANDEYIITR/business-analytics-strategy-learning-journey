-- ============================================================
-- STATISTICAL ANALYSIS DATABASE
-- PostgreSQL statistical calculations and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS statistical_analysis;

SET search_path TO statistical_analysis, public;

-- ------------------------------------------------------------
-- 1. ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE dataset_status AS ENUM (
    'draft',
    'validated',
    'processing',
    'completed',
    'failed'
);

CREATE TYPE observation_quality AS ENUM (
    'valid',
    'suspected_outlier',
    'excluded'
);

-- ------------------------------------------------------------
-- 2. DATASET MANAGEMENT
-- ------------------------------------------------------------

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    measurement_unit VARCHAR(50) NOT NULL,
    status dataset_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT dataset_name_not_empty
        CHECK (length(trim(dataset_name)) > 0),

    CONSTRAINT measurement_unit_not_empty
        CHECK (length(trim(measurement_unit)) > 0)
);

-- ------------------------------------------------------------
-- 3. OBSERVATION RECORDS
-- ------------------------------------------------------------

CREATE TABLE observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,

    subject_reference VARCHAR(100) NOT NULL,
    observation_value NUMERIC(18, 6) NOT NULL,
    quality observation_quality NOT NULL DEFAULT 'valid',
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT observation_reference_not_empty
        CHECK (length(trim(subject_reference)) > 0),

    CONSTRAINT valid_observation_value
        CHECK (
            observation_value > -1000000000000
            AND observation_value < 1000000000000
        ),

    CONSTRAINT unique_dataset_subject
        UNIQUE (dataset_id, subject_reference)
);

CREATE INDEX idx_observations_dataset
    ON observations(dataset_id);

CREATE INDEX idx_observations_dataset_value
    ON observations(dataset_id, observation_value)
    WHERE quality = 'valid';

CREATE INDEX idx_observations_date
    ON observations(observed_at);

-- ------------------------------------------------------------
-- 4. ANALYSIS EXECUTION HISTORY
-- ------------------------------------------------------------

CREATE TABLE analysis_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),

    status dataset_status NOT NULL DEFAULT 'processing',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    error_message TEXT,

    CONSTRAINT valid_run_timestamps
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE INDEX idx_analysis_runs_dataset
    ON analysis_runs(dataset_id, started_at DESC);

-- ------------------------------------------------------------
-- 5. STATISTICAL RESULT STORAGE
-- ------------------------------------------------------------

CREATE TABLE statistical_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES analysis_runs(run_id)
        ON DELETE CASCADE,

    sample_size INTEGER NOT NULL,
    mean_value NUMERIC(18, 6),
    median_value NUMERIC(18, 6),
    minimum_value NUMERIC(18, 6),
    maximum_value NUMERIC(18, 6),
    sample_variance NUMERIC(24, 8),
    population_variance NUMERIC(24, 8),
    sample_stddev NUMERIC(18, 6),
    population_stddev NUMERIC(18, 6),
    q1 NUMERIC(18, 6),
    q3 NUMERIC(18, 6),
    outlier_count INTEGER NOT NULL DEFAULT 0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_sample_size
        CHECK (sample_size >= 2),

    CONSTRAINT valid_outlier_count
        CHECK (
            outlier_count >= 0
            AND outlier_count <= sample_size
        )
);

CREATE INDEX idx_statistical_results_run
    ON statistical_results(run_id);

-- ------------------------------------------------------------
-- 6. UPDATE TIMESTAMP TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_dataset_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_dataset_timestamp
BEFORE UPDATE ON datasets
FOR EACH ROW
EXECUTE FUNCTION update_dataset_timestamp();

-- ------------------------------------------------------------
-- 7. INSERT SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO datasets (
    dataset_name,
    description,
    measurement_unit,
    status
)
VALUES
(
    'Examination Scores',
    'Student examination performance observations',
    'marks',
    'validated'
),
(
    'Study Hours and Performance',
    'Relationship between study time and examination performance',
    'hours',
    'validated'
);

INSERT INTO observations (
    dataset_id,
    subject_reference,
    observation_value,
    quality
)
SELECT
    1,
    'STUDENT-' || lpad(n::text, 3, '0'),
    score,
    'valid'
FROM unnest(
    ARRAY[
        45, 52, 56, 60, 62, 65, 67, 68,
        70, 72, 72, 75, 78, 80, 82, 85,
        88, 90, 92, 95, 98, 100, 105, 150
    ]::NUMERIC[]
) WITH ORDINALITY AS source(score, n);

INSERT INTO observations (
    dataset_id,
    subject_reference,
    observation_value,
    quality
)
SELECT
    2,
    'STUDENT-' || lpad(n::text, 3, '0'),
    study_hours,
    'valid'
FROM unnest(
    ARRAY[
        1, 2, 2, 3, 3, 4, 4, 5,
        5, 6, 6, 7, 7, 8, 8, 9
    ]::NUMERIC[]
) WITH ORDINALITY AS source(study_hours, n);

-- ------------------------------------------------------------
-- 8. DESCRIPTIVE STATISTICS FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_descriptive_statistics(
    p_dataset_id BIGINT
)
RETURNS TABLE (
    observation_count BIGINT,
    mean_value NUMERIC,
    median_value NUMERIC,
    minimum_value NUMERIC,
    maximum_value NUMERIC,
    range_value NUMERIC,
    sample_variance NUMERIC,
    population_variance NUMERIC,
    sample_stddev NUMERIC,
    population_stddev NUMERIC,
    first_quartile NUMERIC,
    third_quartile NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION
            'Dataset % does not exist', p_dataset_id;
    END IF;

    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT,
        AVG(o.observation_value),
        percentile_cont(0.50)
            WITHIN GROUP (
                ORDER BY o.observation_value
            )::NUMERIC,
        MIN(o.observation_value),
        MAX(o.observation_value),
        MAX(o.observation_value) - MIN(o.observation_value),
        VAR_SAMP(o.observation_value)::NUMERIC,
        VAR_POP(o.observation_value)::NUMERIC,
        STDDEV_SAMP(o.observation_value)::NUMERIC,
        STDDEV_POP(o.observation_value)::NUMERIC,
        percentile_cont(0.25)
            WITHIN GROUP (
                ORDER BY o.observation_value
            )::NUMERIC,
        percentile_cont(0.75)
            WITHIN GROUP (
                ORDER BY o.observation_value
            )::NUMERIC
    FROM observations o
    WHERE o.dataset_id = p_dataset_id
      AND o.quality = 'valid';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Unable to calculate statistics for dataset %',
            p_dataset_id;
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 9. FREQUENCY DISTRIBUTION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW observation_frequency AS
SELECT
    dataset_id,
    observation_value,
    COUNT(*) AS frequency,
    ROUND(
        COUNT(*)::NUMERIC /
        SUM(COUNT(*)) OVER (
            PARTITION BY dataset_id
        ) * 100,
        2
    ) AS percentage
FROM observations
WHERE quality = 'valid'
GROUP BY dataset_id, observation_value;

-- ------------------------------------------------------------
-- 10. OUTLIER DETECTION USING IQR
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW statistical_outliers AS
WITH quartile_values AS (
    SELECT
        dataset_id,
        percentile_cont(0.25)
            WITHIN GROUP (
                ORDER BY observation_value
            ) AS q1,
        percentile_cont(0.75)
            WITHIN GROUP (
                ORDER BY observation_value
            ) AS q3
    FROM observations
    WHERE quality = 'valid'
    GROUP BY dataset_id
),
limits AS (
    SELECT
        dataset_id,
        q1,
        q3,
        q3 - q1 AS iqr,
        q1 - 1.5 * (q3 - q1) AS lower_limit,
        q3 + 1.5 * (q3 - q1) AS upper_limit
    FROM quartile_values
)
SELECT
    o.observation_id,
    o.dataset_id,
    o.subject_reference,
    o.observation_value,
    l.q1,
    l.q3,
    l.lower_limit,
    l.upper_limit
FROM observations o
JOIN limits l
    ON l.dataset_id = o.dataset_id
WHERE o.quality = 'valid'
  AND (
      o.observation_value < l.lower_limit
      OR o.observation_value > l.upper_limit
  );

-- ------------------------------------------------------------
-- 11. PEARSON CORRELATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_correlation(
    p_first_dataset BIGINT,
    p_second_dataset BIGINT
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result NUMERIC;
    first_count BIGINT;
    second_count BIGINT;
BEGIN
    SELECT COUNT(*) INTO first_count
    FROM observations
    WHERE dataset_id = p_first_dataset
      AND quality = 'valid';

    SELECT COUNT(*) INTO second_count
    FROM observations
    WHERE dataset_id = p_second_dataset
      AND quality = 'valid';

    IF first_count <> second_count OR first_count < 2 THEN
        RAISE EXCEPTION
            'Datasets require equal observation counts of at least two';
    END IF;

    SELECT CORR(a.observation_value, b.observation_value)
    INTO result
    FROM observations a
    JOIN observations b
        ON a.subject_reference = b.subject_reference
    WHERE a.dataset_id = p_first_dataset
      AND b.dataset_id = p_second_dataset
      AND a.quality = 'valid'
      AND b.quality = 'valid';

    IF result IS NULL THEN
        RAISE EXCEPTION
            'Correlation is undefined for these datasets';
    END IF;

    RETURN result;
END;
$$;

-- ------------------------------------------------------------
-- 12. SIMPLE LINEAR REGRESSION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_regression(
    p_first_dataset BIGINT,
    p_second_dataset BIGINT
)
RETURNS TABLE (
    slope NUMERIC,
    intercept NUMERIC,
    r_squared NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    observations_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO observations_count
    FROM observations a
    JOIN observations b
        ON a.subject_reference = b.subject_reference
    WHERE a.dataset_id = p_first_dataset
      AND b.dataset_id = p_second_dataset
      AND a.quality = 'valid'
      AND b.quality = 'valid';

    IF observations_count < 2 THEN
        RAISE EXCEPTION
            'Regression requires at least two paired observations';
    END IF;

    IF (
        SELECT VAR_SAMP(observation_value)
        FROM observations
        WHERE dataset_id = p_first_dataset
          AND quality = 'valid'
    ) = 0 THEN
        RAISE EXCEPTION
            'Independent variable has no variation';
    END IF;

    RETURN QUERY
    SELECT
        REGR_SLOPE(b.observation_value, a.observation_value)::NUMERIC,
        REGR_INTERCEPT(
            b.observation_value,
            a.observation_value
        )::NUMERIC,
        POWER(
            CORR(a.observation_value, b.observation_value),
            2
        )::NUMERIC
    FROM observations a
    JOIN observations b
        ON a.subject_reference = b.subject_reference
    WHERE a.dataset_id = p_first_dataset
      AND b.dataset_id = p_second_dataset
      AND a.quality = 'valid'
      AND b.quality = 'valid';
END;
$$;

-- ------------------------------------------------------------
-- 13. CONFIDENCE INTERVAL USING NORMAL APPROXIMATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_mean_confidence_interval(
    p_dataset_id BIGINT,
    p_z_score NUMERIC DEFAULT 1.96
)
RETURNS TABLE (
    sample_mean NUMERIC,
    standard_error NUMERIC,
    lower_bound NUMERIC,
    upper_bound NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_z_score IS NULL OR p_z_score <= 0 THEN
        RAISE EXCEPTION
            'Z-score must be positive';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM observations
        WHERE dataset_id = p_dataset_id
          AND quality = 'valid'
    ) < 2 THEN
        RAISE EXCEPTION
            'At least two observations are required';
    END IF;

    RETURN QUERY
    SELECT
        AVG(observation_value),
        STDDEV_SAMP(observation_value) /
            SQRT(COUNT(*)::NUMERIC),
        AVG(observation_value) -
            p_z_score *
            STDDEV_SAMP(observation_value) /
            SQRT(COUNT(*)::NUMERIC),
        AVG(observation_value) +
            p_z_score *
            STDDEV_SAMP(observation_value) /
            SQRT(COUNT(*)::NUMERIC)
    FROM observations
    WHERE dataset_id = p_dataset_id
      AND quality = 'valid';
END;
$$;

-- ------------------------------------------------------------
-- 14. ANALYSIS WORKFLOW PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE process_dataset(
    p_dataset_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_count BIGINT;
    v_mean NUMERIC;
    v_median NUMERIC;
    v_min NUMERIC;
    v_max NUMERIC;
    v_sample_variance NUMERIC;
    v_population_variance NUMERIC;
    v_sample_stddev NUMERIC;
    v_population_stddev NUMERIC;
    v_q1 NUMERIC;
    v_q3 NUMERIC;
    v_outliers INTEGER;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM datasets
        WHERE dataset_id = p_dataset_id
    ) THEN
        RAISE EXCEPTION
            'Dataset % does not exist', p_dataset_id;
    END IF;

    INSERT INTO analysis_runs (
        dataset_id,
        status
    )
    VALUES (
        p_dataset_id,
        'processing'
    )
    RETURNING run_id INTO v_run_id;

    UPDATE datasets
    SET status = 'processing'
    WHERE dataset_id = p_dataset_id;

    SELECT
        observation_count,
        mean_value,
        median_value,
        minimum_value,
        maximum_value,
        sample_variance,
        population_variance,
        sample_stddev,
        population_stddev,
        first_quartile,
        third_quartile
    INTO
        v_count,
        v_mean,
        v_median,
        v_min,
        v_max,
        v_sample_variance,
        v_population_variance,
        v_sample_stddev,
        v_population_stddev,
        v_q1,
        v_q3
    FROM calculate_descriptive_statistics(p_dataset_id);

    IF v_count < 2 THEN
        RAISE EXCEPTION
            'Dataset requires at least two valid observations';
    END IF;

    SELECT COUNT(*)::INTEGER
    INTO v_outliers
    FROM statistical_outliers
    WHERE dataset_id = p_dataset_id;

    INSERT INTO statistical_results (
        run_id,
        sample_size,
        mean_value,
        median_value,
        minimum_value,
        maximum_value,
        sample_variance,
        population_variance,
        sample_stddev,
        population_stddev,
        q1,
        q3,
        outlier_count
    )
    VALUES (
        v_run_id,
        v_count,
        v_mean,
        v_median,
        v_min,
        v_max,
        v_sample_variance,
        v_population_variance,
        v_sample_stddev,
        v_population_stddev,
        v_q1,
        v_q3,
        v_outliers
    );

    UPDATE analysis_runs
    SET
        status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE run_id = v_run_id;

    UPDATE datasets
    SET status = 'completed'
    WHERE dataset_id = p_dataset_id;

EXCEPTION
    WHEN OTHERS THEN
        UPDATE analysis_runs
        SET
            status = 'failed',
            completed_at = CURRENT_TIMESTAMP,
            error_message = SQLERRM
        WHERE run_id = v_run_id;

        UPDATE datasets
        SET status = 'failed'
        WHERE dataset_id = p_dataset_id;

        RAISE;
END;
$$;

-- ------------------------------------------------------------
-- 15. EXECUTE ANALYSIS TRANSACTIONS
-- ------------------------------------------------------------

CALL process_dataset(1);
CALL process_dataset(2);

-- ------------------------------------------------------------
-- 16. RETRIEVAL REPORT
-- ------------------------------------------------------------

SELECT
    dataset_name,
    measurement_unit,
    status,
    created_at
FROM datasets
ORDER BY dataset_id;

-- ------------------------------------------------------------
-- 17. DESCRIPTIVE STATISTICAL REPORT
-- ------------------------------------------------------------

SELECT *
FROM calculate_descriptive_statistics(1);

-- ------------------------------------------------------------
-- 18. FREQUENCY REPORT
-- ------------------------------------------------------------

SELECT *
FROM observation_frequency
WHERE dataset_id = 1
ORDER BY observation_value;

-- ------------------------------------------------------------
-- 19. OUTLIER REPORT
-- ------------------------------------------------------------

SELECT *
FROM statistical_outliers
ORDER BY dataset_id, observation_value;

-- ------------------------------------------------------------
-- 20. CORRELATION REPORT
-- ------------------------------------------------------------

SELECT calculate_correlation(2, 1)
    AS study_hours_performance_correlation;

-- ------------------------------------------------------------
-- 21. REGRESSION REPORT
-- ------------------------------------------------------------

SELECT *
FROM calculate_regression(2, 1);

-- ------------------------------------------------------------
-- 22. CONFIDENCE INTERVAL REPORT
-- ------------------------------------------------------------

SELECT *
FROM calculate_mean_confidence_interval(1, 1.96);

-- ------------------------------------------------------------
-- 23. ANALYSIS HISTORY
-- ------------------------------------------------------------

SELECT
    d.dataset_name,
    r.run_id,
    r.status,
    r.started_at,
    r.completed_at,
    r.error_message
FROM analysis_runs r
JOIN datasets d
    ON d.dataset_id = r.dataset_id
ORDER BY r.started_at DESC;

-- ------------------------------------------------------------
-- 24. STORED RESULT REPORT
-- ------------------------------------------------------------

SELECT
    d.dataset_name,
    ar.run_id,
    sr.sample_size,
    sr.mean_value,
    sr.median_value,
    sr.sample_stddev,
    sr.q1,
    sr.q3,
    sr.outlier_count,
    sr.calculated_at
FROM statistical_results sr
JOIN analysis_runs ar
    ON ar.run_id = sr.run_id
JOIN datasets d
    ON d.dataset_id = ar.dataset_id
ORDER BY sr.calculated_at DESC;

-- ------------------------------------------------------------
-- 25. VALIDATION REPORT
-- ------------------------------------------------------------

SELECT
    dataset_id,
    COUNT(*) AS total_observations,
    COUNT(*) FILTER (
        WHERE quality = 'valid'
    ) AS valid_observations,
    COUNT(*) FILTER (
        WHERE quality = 'suspected_outlier'
    ) AS suspected_outliers,
    COUNT(*) FILTER (
        WHERE quality = 'excluded'
    ) AS excluded_observations
FROM observations
GROUP BY dataset_id;

-- ------------------------------------------------------------
-- 26. CTE-BASED DATA QUALITY REPORT
-- ------------------------------------------------------------

WITH dataset_quality AS (
    SELECT
        dataset_id,
        COUNT(*) AS total_count,
        COUNT(*) FILTER (
            WHERE quality = 'valid'
        ) AS valid_count,
        COUNT(*) FILTER (
            WHERE quality = 'excluded'
        ) AS excluded_count
    FROM observations
    GROUP BY dataset_id
)
SELECT
    d.dataset_name,
    q.total_count,
    q.valid_count,
    q.excluded_count,
    ROUND(
        q.valid_count::NUMERIC /
        NULLIF(q.total_count, 0) * 100,
        2
    ) AS valid_percentage,
    CASE
        WHEN q.valid_count >= 2 THEN 'eligible'
        ELSE 'insufficient_data'
    END AS analysis_eligibility
FROM dataset_quality q
JOIN datasets d
    ON d.dataset_id = q.dataset_id;

-- ------------------------------------------------------------
-- 27. TRANSACTIONAL DATA QUALITY EXAMPLE
-- ------------------------------------------------------------

-- A suspected outlier is classified separately.
-- The original observation remains preserved.

BEGIN;

UPDATE observations
SET quality = 'suspected_outlier'
WHERE dataset_id = 1
  AND subject_reference = 'STUDENT-024';

-- Verify the classification before committing.
SELECT
    subject_reference,
    observation_value,
    quality
FROM observations
WHERE dataset_id = 1
  AND subject_reference = 'STUDENT-024';

COMMIT;

-- Re-run the analysis using the remaining valid observations.
-- The dataset must still contain at least two valid observations.

CALL process_dataset(1);

-- ------------------------------------------------------------
-- 28. OPERATIONAL PERFORMANCE REPORT
-- ------------------------------------------------------------

SELECT
    dataset_id,
    COUNT(*) AS observation_count,
    MIN(observed_at) AS first_observation,
    MAX(observed_at) AS last_observation
FROM observations
GROUP BY dataset_id
ORDER BY dataset_id;

-- ============================================================
-- END OF STATISTICAL ANALYSIS DATABASE
-- ============================================================

COMMIT;
