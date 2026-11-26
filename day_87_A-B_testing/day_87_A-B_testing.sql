-- ============================================================
-- A/B TESTING: EXPERIMENT DESIGN AND STATISTICAL COMPARISON
-- PostgreSQL 15+
-- ============================================================

CREATE SCHEMA IF NOT EXISTS ab_testing;

SET search_path TO ab_testing, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

DO $$
BEGIN
    CREATE TYPE experiment_status AS ENUM (
        'draft',
        'approved',
        'running',
        'completed',
        'stopped'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE variant_type AS ENUM (
        'control',
        'treatment'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE design_review_status AS ENUM (
        'pending',
        'approved',
        'rejected'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
-- 2. EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_key VARCHAR(100) NOT NULL UNIQUE,

    experiment_name VARCHAR(250) NOT NULL,

    hypothesis TEXT NOT NULL,

    primary_metric VARCHAR(100) NOT NULL,

    baseline_conversion_rate NUMERIC(12,8) NOT NULL,

    minimum_detectable_effect NUMERIC(12,8) NOT NULL,

    significance_level NUMERIC(8,6) NOT NULL DEFAULT 0.05,

    statistical_power NUMERIC(8,6) NOT NULL DEFAULT 0.80,

    allocation_ratio NUMERIC(8,6) NOT NULL DEFAULT 0.50,

    planned_sample_size INTEGER NOT NULL,

    minimum_duration_days INTEGER NOT NULL DEFAULT 7,

    status experiment_status NOT NULL DEFAULT 'draft',

    design_review design_review_status NOT NULL DEFAULT 'pending',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_by VARCHAR(150) NOT NULL,

    CONSTRAINT valid_baseline_rate
        CHECK (
            baseline_conversion_rate > 0
            AND baseline_conversion_rate < 1
        ),

    CONSTRAINT valid_effect
        CHECK (
            minimum_detectable_effect > 0
            AND baseline_conversion_rate + minimum_detectable_effect < 1
        ),

    CONSTRAINT valid_alpha
        CHECK (significance_level > 0 AND significance_level < 1),

    CONSTRAINT valid_power
        CHECK (statistical_power > 0 AND statistical_power < 1),

    CONSTRAINT valid_allocation
        CHECK (allocation_ratio > 0 AND allocation_ratio < 1),

    CONSTRAINT valid_sample_size
        CHECK (planned_sample_size > 0),

    CONSTRAINT valid_duration
        CHECK (minimum_duration_days > 0),

    CONSTRAINT valid_experiment_dates
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        )
);

-- ------------------------------------------------------------
-- 3. EXPERIMENT VARIANTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_variants (
    variant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    variant_name VARCHAR(100) NOT NULL,

    variant_type variant_type NOT NULL,

    allocation_weight NUMERIC(8,6) NOT NULL,

    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT unique_experiment_variant
        UNIQUE (experiment_id, variant_name),

    CONSTRAINT unique_variant_type
        UNIQUE (experiment_id, variant_type),

    CONSTRAINT valid_variant_weight
        CHECK (
            allocation_weight > 0
            AND allocation_weight <= 1
        )
);

CREATE INDEX IF NOT EXISTS idx_variants_experiment
    ON experiment_variants(experiment_id);

-- ------------------------------------------------------------
-- 4. PARTICIPANTS AND RANDOMIZATION ASSIGNMENTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS participants (
    participant_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_participant_key VARCHAR(150) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    participant_id BIGINT NOT NULL
        REFERENCES participants(participant_id),

    variant_id BIGINT NOT NULL
        REFERENCES experiment_variants(variant_id),

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    assignment_bucket INTEGER NOT NULL,

    CONSTRAINT unique_experiment_participant
        UNIQUE (experiment_id, participant_id),

    CONSTRAINT valid_assignment_bucket
        CHECK (assignment_bucket >= 0 AND assignment_bucket < 1000000)
);

CREATE INDEX IF NOT EXISTS idx_assignments_experiment_variant
    ON experiment_assignments(experiment_id, variant_id);

CREATE INDEX IF NOT EXISTS idx_assignments_assigned_at
    ON experiment_assignments(assigned_at);

-- ------------------------------------------------------------
-- 5. EXPERIMENT OUTCOMES
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_outcomes (
    outcome_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    assignment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiment_assignments(assignment_id),

    converted BOOLEAN NOT NULL,

    revenue NUMERIC(14,2) NOT NULL DEFAULT 0,

    session_count INTEGER NOT NULL DEFAULT 1,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_revenue
        CHECK (revenue >= 0),

    CONSTRAINT valid_session_count
        CHECK (session_count >= 0),

    CONSTRAINT revenue_conversion_consistency
        CHECK (converted OR revenue = 0)
);

CREATE INDEX IF NOT EXISTS idx_outcomes_recorded_at
    ON experiment_outcomes(recorded_at);

-- ------------------------------------------------------------
-- 6. GUARDRAIL METRICS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS guardrail_observations (
    guardrail_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    assignment_id BIGINT NOT NULL
        REFERENCES experiment_assignments(assignment_id),

    metric_name VARCHAR(100) NOT NULL,

    metric_value NUMERIC(16,6) NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_assignment_guardrail
        UNIQUE (assignment_id, metric_name)
);

-- ------------------------------------------------------------
-- 7. EXPERIMENT DESIGN APPROVALS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS design_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    reviewer VARCHAR(150) NOT NULL,

    decision VARCHAR(20) NOT NULL,

    comments TEXT,

    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_design_decision
        CHECK (decision IN ('approved', 'rejected')),

    CONSTRAINT unique_design_reviewer
        UNIQUE (experiment_id, reviewer)
);

-- ------------------------------------------------------------
-- 8. EXPERIMENT AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    action VARCHAR(100) NOT NULL,

    actor VARCHAR(150) NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_experiment_date
    ON experiment_audit_log(experiment_id, created_at DESC);

-- ------------------------------------------------------------
-- 9. VALIDATE VARIANT CONFIGURATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_variant_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_status_value experiment_status;
    total_weight NUMERIC;
BEGIN
    SELECT status
    INTO experiment_status_value
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    IF experiment_status_value <> 'draft' THEN
        RAISE EXCEPTION 'Variants cannot change after experiment approval.';
    END IF;

    SELECT COALESCE(SUM(allocation_weight), 0)
    INTO total_weight
    FROM experiment_variants
    WHERE experiment_id = NEW.experiment_id
      AND variant_id <> COALESCE(NEW.variant_id, -1);

    IF total_weight + NEW.allocation_weight > 1 THEN
        RAISE EXCEPTION 'Total allocation weight cannot exceed one.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_variants
    ON experiment_variants;

CREATE TRIGGER trg_validate_variants
BEFORE INSERT OR UPDATE
ON experiment_variants
FOR EACH ROW
EXECUTE FUNCTION validate_variant_configuration();

-- ------------------------------------------------------------
-- 10. VALIDATE ASSIGNMENT INTEGRITY
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
    variant_experiment_id BIGINT;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF current_status <> 'running' THEN
        RAISE EXCEPTION 'Assignments require a running experiment.';
    END IF;

    SELECT experiment_id
    INTO variant_experiment_id
    FROM experiment_variants
    WHERE variant_id = NEW.variant_id;

    IF variant_experiment_id IS DISTINCT FROM NEW.experiment_id THEN
        RAISE EXCEPTION 'Variant belongs to another experiment.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_assignment
    ON experiment_assignments;

CREATE TRIGGER trg_validate_assignment
BEFORE INSERT OR UPDATE
ON experiment_assignments
FOR EACH ROW
EXECUTE FUNCTION validate_assignment();

-- ------------------------------------------------------------
-- 11. VALIDATE OUTCOME INTEGRITY
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_outcome()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    assignment_experiment BIGINT;
    current_status experiment_status;
BEGIN
    SELECT experiment_id
    INTO assignment_experiment
    FROM experiment_assignments
    WHERE assignment_id = NEW.assignment_id;

    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = assignment_experiment;

    IF current_status <> 'running' THEN
        RAISE EXCEPTION 'Outcomes require a running experiment.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_outcome
    ON experiment_outcomes;

CREATE TRIGGER trg_validate_outcome
BEFORE INSERT OR UPDATE
ON experiment_outcomes
FOR EACH ROW
EXECUTE FUNCTION validate_outcome();

-- ------------------------------------------------------------
-- 12. APPROVAL PROCESS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION approve_experiment(
    p_experiment_id BIGINT,
    p_reviewer VARCHAR,
    p_decision VARCHAR,
    p_comments TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    IF p_decision NOT IN ('approved', 'rejected') THEN
        RAISE EXCEPTION 'Invalid design decision.';
    END IF;

    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF current_status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft experiments can be reviewed.';
    END IF;

    INSERT INTO design_approvals (
        experiment_id,
        reviewer,
        decision,
        comments
    )
    VALUES (
        p_experiment_id,
        p_reviewer,
        p_decision,
        p_comments
    )
    ON CONFLICT (experiment_id, reviewer)
    DO UPDATE SET
        decision = EXCLUDED.decision,
        comments = EXCLUDED.comments,
        reviewed_at = NOW();

    UPDATE experiments
    SET design_review = CASE
        WHEN EXISTS (
            SELECT 1
            FROM design_approvals
            WHERE experiment_id = p_experiment_id
              AND decision = 'rejected'
        )
        THEN 'rejected'::design_review_status

        WHEN EXISTS (
            SELECT 1
            FROM design_approvals
            WHERE experiment_id = p_experiment_id
              AND decision = 'approved'
        )
        THEN 'approved'::design_review_status

        ELSE 'pending'::design_review_status
    END
    WHERE experiment_id = p_experiment_id;

    INSERT INTO experiment_audit_log (
        experiment_id,
        action,
        actor,
        details
    )
    VALUES (
        p_experiment_id,
        'design_review',
        p_reviewer,
        jsonb_build_object(
            'decision', p_decision,
            'comments', p_comments
        )
    );
END;
$$;

-- ------------------------------------------------------------
-- 13. EXPERIMENT STATE TRANSITIONS
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
    review_status design_review_status;
    total_weight NUMERIC;
    variant_count INTEGER;
BEGIN
    SELECT status, design_review
    INTO current_status, review_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF current_status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft experiments can start.';
    END IF;

    IF review_status <> 'approved' THEN
        RAISE EXCEPTION 'Experiment design requires approval.';
    END IF;

    SELECT
        COUNT(*),
        COALESCE(SUM(allocation_weight), 0)
    INTO variant_count, total_weight
    FROM experiment_variants
    WHERE experiment_id = p_experiment_id;

    IF variant_count < 2 OR ABS(total_weight - 1) > 0.000001 THEN
        RAISE EXCEPTION 'Two or more variants must total 100%% allocation.';
    END IF;

    UPDATE experiments
    SET status = 'running',
        started_at = NOW()
    WHERE experiment_id = p_experiment_id;

    INSERT INTO experiment_audit_log (
        experiment_id,
        action,
        actor
    )
    VALUES (
        p_experiment_id,
        'experiment_started',
        CURRENT_USER
    );
END;
$$;

CREATE OR REPLACE PROCEDURE close_experiment(
    p_experiment_id BIGINT,
    p_final_status experiment_status
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_final_status NOT IN ('completed', 'stopped') THEN
        RAISE EXCEPTION 'Final state must be completed or stopped.';
    END IF;

    UPDATE experiments
    SET status = p_final_status,
        completed_at = NOW()
    WHERE experiment_id = p_experiment_id
      AND status = 'running';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment cannot transition to requested state.';
    END IF;

    INSERT INTO experiment_audit_log (
        experiment_id,
        action,
        actor
    )
    VALUES (
        p_experiment_id,
        'experiment_' || p_final_status::TEXT,
        CURRENT_USER
    );
END;
$$;

-- ------------------------------------------------------------
-- 14. EXPERIMENT SAMPLE SIZE CALCULATOR
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION required_sample_size(
    p_baseline NUMERIC,
    p_effect NUMERIC,
    p_alpha NUMERIC DEFAULT 0.05,
    p_power NUMERIC DEFAULT 0.80
)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    p_treatment NUMERIC;
    pooled NUMERIC;
    z_alpha NUMERIC;
    z_beta NUMERIC;
    numerator NUMERIC;
BEGIN
    p_treatment := p_baseline + p_effect;

    IF p_baseline <= 0 OR p_baseline >= 1 THEN
        RAISE EXCEPTION 'Invalid baseline rate.';
    END IF;

    IF p_effect <= 0 OR p_treatment >= 1 THEN
        RAISE EXCEPTION 'Invalid minimum detectable effect.';
    END IF;

    IF p_alpha <= 0 OR p_alpha >= 1
       OR p_power <= 0 OR p_power >= 1 THEN
        RAISE EXCEPTION 'Invalid statistical parameters.';
    END IF;

    -- PostgreSQL inverse normal approximation through
    -- the inverse complementary error function.
    -- This approximation is implemented using a rational
    -- inverse-normal algorithm.

    z_alpha := inverse_standard_normal(1 - p_alpha / 2);
    z_beta := inverse_standard_normal(p_power);

    pooled := (p_baseline + p_treatment) / 2;

    numerator := POWER(
        z_alpha * SQRT(2 * pooled * (1 - pooled)) +
        z_beta * SQRT(
            p_baseline * (1 - p_baseline) +
            p_treatment * (1 - p_treatment)
        ),
        2
    );

    RETURN CEIL(numerator / POWER(p_effect, 2))::INTEGER;
END;
$$;

CREATE OR REPLACE FUNCTION inverse_standard_normal(p DOUBLE PRECISION)
RETURNS DOUBLE PRECISION
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    a DOUBLE PRECISION[] := ARRAY[
        -39.6968302866538, 220.946098424521,
        -275.928510446969, 138.357751867269,
        -30.6647980661472, 2.50662827745924
    ];

    b DOUBLE PRECISION[] := ARRAY[
        -54.4760987982241, 161.585836858041,
        -155.698979859887, 66.8013118877197,
        -13.2806815528857
    ];

    c DOUBLE PRECISION[] := ARRAY[
        -0.00778489400243029, -0.322396458041136,
        -2.40075827716184, -2.54973253934373,
        4.37466414146497, 2.93816398269878
    ];

    d DOUBLE PRECISION[] := ARRAY[
        0.00778469570904146, 0.32246712907004,
        2.445134137143, 3.75440866190742
    ];

    q DOUBLE PRECISION;
    r DOUBLE PRECISION;
    result DOUBLE PRECISION;
BEGIN
    IF p <= 0 OR p >= 1 THEN
        RAISE EXCEPTION 'Probability must be between zero and one.';
    END IF;

    IF p < 0.02425 THEN
        q := SQRT(-2 * LN(p));

        result := (
            (((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6])
            /
            ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)
        );

    ELSIF p > 0.97575 THEN
        q := SQRT(-2 * LN(1-p));

        result := -(
            (((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6])
            /
            ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1)
        );

    ELSE
        q := p - 0.5;
        r := q * q;

        result := (
            (((((a[1]*r+a[2])*r+a[3])*r+a[4])*r+a[5])*r+a[6])*q
        ) / (
            ((((b[1]*r+b[2])*r+b[3])*r+b[4])*r+b[5])*r+1
        );
    END IF;

    RETURN result;
END;
$$;

-- ------------------------------------------------------------
-- 15. STATISTICAL ANALYSIS FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION analyze_experiment(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    variant_name VARCHAR,
    participants BIGINT,
    conversions BIGINT,
    conversion_rate NUMERIC,
    total_revenue NUMERIC,
    average_revenue NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.variant_name,
        COUNT(o.outcome_id),
        COUNT(o.outcome_id) FILTER (WHERE o.converted),
        COALESCE(
            COUNT(o.outcome_id) FILTER (WHERE o.converted)::NUMERIC /
            NULLIF(COUNT(o.outcome_id), 0),
            0
        ),
        COALESCE(SUM(o.revenue), 0),
        COALESCE(AVG(o.revenue), 0)
    FROM experiment_variants v
    LEFT JOIN experiment_assignments a
        ON a.variant_id = v.variant_id
       AND a.experiment_id = p_experiment_id
    LEFT JOIN experiment_outcomes o
        ON o.assignment_id = a.assignment_id
    WHERE v.experiment_id = p_experiment_id
    GROUP BY v.variant_id, v.variant_name, v.variant_type
    ORDER BY v.variant_type;
END;
$$;

-- ------------------------------------------------------------
-- 16. STATISTICAL COMPARISON AND CONFIDENCE INTERVAL
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION compare_experiment(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    control_rate NUMERIC,
    treatment_rate NUMERIC,
    absolute_lift NUMERIC,
    relative_lift NUMERIC,
    z_score NUMERIC,
    p_value NUMERIC,
    confidence_lower NUMERIC,
    confidence_upper NUMERIC,
    statistically_significant BOOLEAN,
    practically_significant BOOLEAN
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    c_n BIGINT;
    t_n BIGINT;
    c_x BIGINT;
    t_x BIGINT;

    p1 NUMERIC;
    p2 NUMERIC;
    pooled NUMERIC;
    lift NUMERIC;
    se NUMERIC;
    ci_se NUMERIC;
    z NUMERIC;
    pv NUMERIC;
    critical NUMERIC;
    alpha_value NUMERIC;
    effect_value NUMERIC;
BEGIN
    SELECT
        COUNT(*) FILTER (WHERE v.variant_type = 'control'),
        COUNT(*) FILTER (WHERE v.variant_type = 'treatment'),
        COUNT(*) FILTER (
            WHERE v.variant_type = 'control' AND o.converted
        ),
        COUNT(*) FILTER (
            WHERE v.variant_type = 'treatment' AND o.converted
        )
    INTO c_n, t_n, c_x, t_x
    FROM experiment_assignments a
    JOIN experiment_variants v
        ON v.variant_id = a.variant_id
    JOIN experiment_outcomes o
        ON o.assignment_id = a.assignment_id
    WHERE a.experiment_id = p_experiment_id;

    IF c_n = 0 OR t_n = 0 THEN
        RAISE EXCEPTION 'Both variants require observed outcomes.';
    END IF;

    SELECT significance_level, minimum_detectable_effect
    INTO alpha_value, effect_value
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    p1 := c_x::NUMERIC / c_n;
    p2 := t_x::NUMERIC / t_n;
    lift := p2 - p1;

    pooled := (c_x + t_x)::NUMERIC / (c_n + t_n);

    se := SQRT(
        pooled * (1 - pooled) *
        (1.0 / c_n + 1.0 / t_n)
    );

    IF se = 0 THEN
        z := 0;
        pv := 1;
    ELSE
        z := lift / se;
        pv := ERFC(ABS(z) / SQRT(2));
    END IF;

    ci_se := SQRT(
        p1 * (1 - p1) / c_n +
        p2 * (1 - p2) / t_n
    );

    critical := inverse_standard_normal(
        1 - alpha_value / 2
    );

    RETURN QUERY SELECT
        p1,
        p2,
        lift,
        CASE WHEN p1 = 0 THEN 0 ELSE lift / p1 END,
        z,
        pv,
        lift - critical * ci_se,
        lift + critical * ci_se,
        pv < alpha_value,
        lift >= effect_value;
END;
$$;

-- ------------------------------------------------------------
-- 17. SAMPLE RATIO MISMATCH REPORT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_sample_ratio(
    p_experiment_id BIGINT,
    p_expected_control_ratio NUMERIC DEFAULT 0.5
)
RETURNS TABLE (
    observed_control_ratio NUMERIC,
    chi_square NUMERIC,
    p_value NUMERIC,
    mismatch_detected BOOLEAN
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    control_count BIGINT;
    treatment_count BIGINT;
    total_count BIGINT;
    expected_control NUMERIC;
    expected_treatment NUMERIC;
    statistic NUMERIC;
BEGIN
    IF p_expected_control_ratio <= 0
       OR p_expected_control_ratio >= 1 THEN
        RAISE EXCEPTION 'Invalid expected ratio.';
    END IF;

    SELECT
        COUNT(*) FILTER (WHERE v.variant_type = 'control'),
        COUNT(*) FILTER (WHERE v.variant_type = 'treatment')
    INTO control_count, treatment_count
    FROM experiment_assignments a
    JOIN experiment_variants v
        ON v.variant_id = a.variant_id
    WHERE a.experiment_id = p_experiment_id;

    total_count := control_count + treatment_count;

    IF total_count = 0 THEN
        RAISE EXCEPTION 'No assignments available.';
    END IF;

    expected_control := total_count * p_expected_control_ratio;
    expected_treatment := total_count * (1-p_expected_control_ratio);

    statistic :=
        POWER(control_count - expected_control, 2) / expected_control +
        POWER(treatment_count - expected_treatment, 2) / expected_treatment;

    RETURN QUERY SELECT
        control_count::NUMERIC / total_count,
        statistic,
        ERFC(SQRT(statistic / 2)),
        ERFC(SQRT(statistic / 2)) < 0.001;
END;
$$;

-- ------------------------------------------------------------
-- 18. GUARDRAIL AGGREGATION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW variant_guardrail_summary AS
SELECT
    a.experiment_id,
    v.variant_type,
    g.metric_name,
    COUNT(*) AS observation_count,
    AVG(g.metric_value) AS average_value,
    MIN(g.metric_value) AS minimum_value,
    MAX(g.metric_value) AS maximum_value
FROM guardrail_observations g
JOIN experiment_assignments a
    ON a.assignment_id = g.assignment_id
JOIN experiment_variants v
    ON v.variant_id = a.variant_id
GROUP BY
    a.experiment_id,
    v.variant_type,
    g.metric_name;

-- ------------------------------------------------------------
-- 19. OPERATIONAL REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_performance_report AS
SELECT
    e.experiment_id,
    e.experiment_key,
    e.experiment_name,
    e.status,
    v.variant_name,
    v.variant_type,
    COUNT(DISTINCT a.assignment_id) AS assigned_participants,
    COUNT(DISTINCT o.outcome_id) AS observed_participants,
    COUNT(o.outcome_id) FILTER (WHERE o.converted) AS conversions,
    ROUND(
        COUNT(o.outcome_id) FILTER (WHERE o.converted)::NUMERIC /
        NULLIF(COUNT(o.outcome_id), 0),
        6
    ) AS conversion_rate,
    COALESCE(SUM(o.revenue), 0) AS total_revenue
FROM experiments e
JOIN experiment_variants v
    ON v.experiment_id = e.experiment_id
LEFT JOIN experiment_assignments a
    ON a.variant_id = v.variant_id
LEFT JOIN experiment_outcomes o
    ON o.assignment_id = a.assignment_id
GROUP BY
    e.experiment_id,
    e.experiment_key,
    e.experiment_name,
    e.status,
    v.variant_id,
    v.variant_name,
    v.variant_type;

-- ============================================================
-- 20. SAMPLE EXPERIMENT
-- ============================================================

INSERT INTO experiments (
    experiment_key,
    experiment_name,
    hypothesis,
    primary_metric,
    baseline_conversion_rate,
    minimum_detectable_effect,
    significance_level,
    statistical_power,
    allocation_ratio,
    planned_sample_size,
    minimum_duration_days,
    created_by
)
VALUES (
    'checkout-redesign-2026',
    'Checkout Conversion Optimization',
    'A redesigned checkout button increases completed purchases.',
    'conversion_rate',
    0.10,
    0.02,
    0.05,
    0.80,
    0.50,
    20000,
    7,
    'product-analytics-team'
)
ON CONFLICT (experiment_key) DO NOTHING;

INSERT INTO experiment_variants (
    experiment_id,
    variant_name,
    variant_type,
    allocation_weight,
    configuration
)
SELECT
    experiment_id,
    'Original Checkout',
    'control',
    0.50,
    '{"button_color":"blue","layout":"original"}'::JSONB
FROM experiments
WHERE experiment_key = 'checkout-redesign-2026'
ON CONFLICT (experiment_id, variant_name) DO NOTHING;

INSERT INTO experiment_variants (
    experiment_id,
    variant_name,
    variant_type,
    allocation_weight,
    configuration
)
SELECT
    experiment_id,
    'Redesigned Checkout',
    'treatment',
    0.50,
    '{"button_color":"green","layout":"redesigned"}'::JSONB
FROM experiments
WHERE experiment_key = 'checkout-redesign-2026'
ON CONFLICT (experiment_id, variant_name) DO NOTHING;

-- ------------------------------------------------------------
-- 21. DESIGN APPROVAL
-- ------------------------------------------------------------

DO $$
DECLARE
    experiment_identifier BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_identifier
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026';

    IF NOT EXISTS (
        SELECT 1
        FROM design_approvals
        WHERE experiment_id = experiment_identifier
          AND reviewer = 'analytics-lead'
    ) THEN
        PERFORM approve_experiment(
            experiment_identifier,
            'analytics-lead',
            'approved',
            'Randomization, primary metric and sample size reviewed.'
        );
    END IF;
END $$;

-- ------------------------------------------------------------
-- 22. START EXPERIMENT
-- ------------------------------------------------------------

DO $$
DECLARE
    experiment_identifier BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_identifier
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026';

    IF EXISTS (
        SELECT 1
        FROM experiments
        WHERE experiment_id = experiment_identifier
          AND status = 'draft'
    ) THEN
        CALL start_experiment(experiment_identifier);
    END IF;
END $$;

-- ------------------------------------------------------------
-- 23. SIMULATED PARTICIPANTS
-- ------------------------------------------------------------

-- Generate reproducible assignments.
-- MD5-based buckets are suitable for this demonstration,
-- not for security-sensitive randomization.

INSERT INTO participants (external_participant_key)
SELECT 'customer-' || generate_series
FROM generate_series(1, 20000)
ON CONFLICT (external_participant_key) DO NOTHING;

WITH experiment_data AS (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026'
),
variant_data AS (
    SELECT variant_id, variant_type
    FROM experiment_variants
    WHERE experiment_id = (
        SELECT experiment_id FROM experiment_data
    )
),
participant_data AS (
    SELECT
        p.participant_id,
        p.external_participant_key,
        (('x' || SUBSTRING(
            MD5(
                'checkout-redesign-2026:' ||
                p.external_participant_key
            ),
            1,
            8
        ))::BIT(32)::BIGINT % 1000000) AS bucket
    FROM participants p
    WHERE p.external_participant_key LIKE 'customer-%'
),
assignment_data AS (
    SELECT
        pd.participant_id,
        CASE
            WHEN pd.bucket < 500000 THEN (
                SELECT variant_id
                FROM variant_data
                WHERE variant_type = 'control'
            )
            ELSE (
                SELECT variant_id
                FROM variant_data
                WHERE variant_type = 'treatment'
            )
        END AS variant_id,
        pd.bucket
    FROM participant_data pd
)
INSERT INTO experiment_assignments (
    experiment_id,
    participant_id,
    variant_id,
    assignment_bucket
)
SELECT
    (SELECT experiment_id FROM experiment_data),
    participant_id,
    variant_id,
    bucket::INTEGER
FROM assignment_data
ON CONFLICT (experiment_id, participant_id) DO NOTHING;

-- ------------------------------------------------------------
-- 24. SIMULATED CONVERSION OUTCOMES
-- ------------------------------------------------------------

-- Outcome probabilities are deterministic for repeatable testing.
-- The hash is only a simulation mechanism, not a production
-- randomization or cryptographic security mechanism.

INSERT INTO experiment_outcomes (
    assignment_id,
    converted,
    revenue,
    session_count
)
SELECT
    a.assignment_id,

    CASE
        WHEN v.variant_type = 'control'
        THEN (
            ('x' || SUBSTRING(
                MD5('conversion:' || p.external_participant_key),
                1,
                8
            ))::BIT(32)::BIGINT % 10000 < 1000
        )
        ELSE (
            ('x' || SUBSTRING(
                MD5('conversion:' || p.external_participant_key),
                1,
                8
            ))::BIT(32)::BIGINT % 10000 < 1200
        )
    END AS converted,

    CASE
        WHEN v.variant_type = 'control'
             AND (
                ('x' || SUBSTRING(
                    MD5('conversion:' || p.external_participant_key),
                    1,
                    8
                ))::BIT(32)::BIGINT % 10000 < 1000
             )
        THEN 75.00

        WHEN v.variant_type = 'treatment'
             AND (
                ('x' || SUBSTRING(
                    MD5('conversion:' || p.external_participant_key),
                    1,
                    8
                ))::BIT(32)::BIGINT % 10000 < 1200
             )
        THEN 85.00

        ELSE 0.00
    END,

    1
FROM experiment_assignments a
JOIN participants p
    ON p.participant_id = a.participant_id
JOIN experiment_variants v
    ON v.variant_id = a.variant_id
WHERE a.experiment_id = (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026'
)
ON CONFLICT (assignment_id) DO NOTHING;

-- ------------------------------------------------------------
-- 25. SAMPLE GUARDRAIL DATA
-- ------------------------------------------------------------

INSERT INTO guardrail_observations (
    assignment_id,
    metric_name,
    metric_value
)
SELECT
    a.assignment_id,
    'checkout_latency_ms',
    CASE
        WHEN v.variant_type = 'control' THEN 450
        ELSE 430
    END
FROM experiment_assignments a
JOIN experiment_variants v
    ON v.variant_id = a.variant_id
WHERE a.experiment_id = (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026'
)
ON CONFLICT (assignment_id, metric_name) DO NOTHING;

-- ------------------------------------------------------------
-- 26. CLOSE THE EXPERIMENT
-- ------------------------------------------------------------

DO $$
DECLARE
    experiment_identifier BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_identifier
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026';

    IF EXISTS (
        SELECT 1
        FROM experiments
        WHERE experiment_id = experiment_identifier
          AND status = 'running'
    ) THEN
        CALL close_experiment(
            experiment_identifier,
            'completed'
        );
    END IF;
END $$;

-- ============================================================
-- 27. RETRIEVAL AND REPORTING QUERIES
-- ============================================================

-- Experiment inventory.
SELECT
    experiment_key,
    experiment_name,
    status,
    design_review,
    created_by
FROM experiments
ORDER BY created_at DESC;

-- Variant-level performance.
SELECT *
FROM experiment_performance_report
WHERE experiment_key = 'checkout-redesign-2026'
ORDER BY variant_type;

-- Detailed statistical comparison.
SELECT *
FROM compare_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_key = 'checkout-redesign-2026'
    )
);

-- Sample ratio mismatch evaluation.
SELECT *
FROM check_sample_ratio(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_key = 'checkout-redesign-2026'
    ),
    0.50
);

-- Guardrail reporting.
SELECT *
FROM variant_guardrail_summary
WHERE experiment_id = (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026'
);

-- Required sample size for a planned experiment.
SELECT required_sample_size(
    0.10,
    0.02,
    0.05,
    0.80
) AS required_participants_per_group;

-- Missing outcome monitoring.
SELECT
    e.experiment_key,
    v.variant_type,
    COUNT(a.assignment_id) AS assigned,
    COUNT(o.outcome_id) AS observed,
    COUNT(a.assignment_id) - COUNT(o.outcome_id) AS missing_outcomes
FROM experiments e
JOIN experiment_variants v
    ON v.experiment_id = e.experiment_id
LEFT JOIN experiment_assignments a
    ON a.variant_id = v.variant_id
LEFT JOIN experiment_outcomes o
    ON o.assignment_id = a.assignment_id
WHERE e.experiment_key = 'checkout-redesign-2026'
GROUP BY e.experiment_key, v.variant_type;

-- Audit trail.
SELECT
    action,
    actor,
    details,
    created_at
FROM experiment_audit_log
WHERE experiment_id = (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026'
)
ORDER BY created_at;

-- ============================================================
-- 28. TRANSACTIONAL FAILURE-HANDLING EXAMPLE
-- ============================================================

-- Demonstrates atomic assignment insertion.
-- Either all operations succeed or the transaction is rolled back.

BEGIN;

DO $$
DECLARE
    experiment_identifier BIGINT;
    participant_identifier BIGINT;
    control_variant_identifier BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_identifier
    FROM experiments
    WHERE experiment_key = 'checkout-redesign-2026';

    SELECT participant_id
    INTO participant_identifier
    FROM participants
    WHERE external_participant_key = 'transaction-test-customer';

    IF participant_identifier IS NULL THEN
        INSERT INTO participants (external_participant_key)
        VALUES ('transaction-test-customer')
        RETURNING participant_id INTO participant_identifier;
    END IF;

    SELECT variant_id
    INTO control_variant_identifier
    FROM experiment_variants
    WHERE experiment_id = experiment_identifier
      AND variant_type = 'control';

    INSERT INTO experiment_assignments (
        experiment_id,
        participant_id,
        variant_id,
        assignment_bucket
    )
    VALUES (
        experiment_identifier,
        participant_identifier,
        control_variant_identifier,
        100
    )
    ON CONFLICT (experiment_id, participant_id) DO NOTHING;
END $$;

ROLLBACK;

-- The transaction test customer is not retained after rollback.

-- ============================================================
-- END OF A/B TESTING DATABASE IMPLEMENTATION
-- ============================================================
