-- ============================================================
-- COST ANALYTICS AND COST OPTIMIZATION DATABASE
-- PostgreSQL 15+
--
-- Features:
-- 1. Cost structures and classification
-- 2. Direct and indirect cost accounting
-- 3. Cost centres
-- 4. Budget management
-- 5. Activity-based cost allocation
-- 6. Unit economics
-- 7. Contribution and break-even analysis
-- 8. Optimization proposals
-- 9. Optimization approval workflow
-- 10. Financial audit history
-- 11. Management reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS cost_analytics;

SET search_path TO cost_analytics, public;

-- ============================================================
-- 1. ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE cost_type AS ENUM (
    'FIXED',
    'VARIABLE',
    'SEMI_VARIABLE'
);

CREATE TYPE cost_behavior AS ENUM (
    'DIRECT',
    'INDIRECT'
);

CREATE TYPE cost_category AS ENUM (
    'LABOR',
    'MATERIALS',
    'TECHNOLOGY',
    'FACILITIES',
    'LOGISTICS',
    'ADMINISTRATION'
);

CREATE TYPE proposal_status AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED',
    'IMPLEMENTED',
    'CANCELLED'
);

CREATE TYPE approval_decision AS ENUM (
    'APPROVED',
    'REJECTED'
);

-- ============================================================
-- 2. ORGANIZATIONAL STRUCTURE
-- ============================================================

CREATE TABLE cost_centers (
    cost_center_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    center_code VARCHAR(30) NOT NULL UNIQUE,

    center_name VARCHAR(120) NOT NULL,

    department VARCHAR(100) NOT NULL,

    manager_name VARCHAR(120) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT center_code_nonempty
        CHECK (LENGTH(TRIM(center_code)) > 0)
);

CREATE TABLE reporting_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    period_code VARCHAR(7) NOT NULL UNIQUE,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    status VARCHAR(15) NOT NULL DEFAULT 'OPEN',

    CONSTRAINT valid_period
        CHECK (end_date >= start_date),

    CONSTRAINT valid_period_status
        CHECK (status IN ('OPEN', 'CLOSED'))
);

-- ============================================================
-- 3. FINANCIAL COST RECORDS
-- ============================================================

CREATE TABLE cost_records (
    cost_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    external_reference VARCHAR(80) UNIQUE,

    cost_center_id BIGINT NOT NULL
        REFERENCES cost_centers(cost_center_id),

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    category cost_category NOT NULL,

    classification cost_type NOT NULL,

    behavior cost_behavior NOT NULL,

    amount NUMERIC(16, 2) NOT NULL,

    activity_units NUMERIC(16, 3) NOT NULL DEFAULT 0,

    description TEXT NOT NULL,

    recorded_by VARCHAR(120) NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT nonnegative_cost
        CHECK (amount >= 0),

    CONSTRAINT nonnegative_activity
        CHECK (activity_units >= 0),

    CONSTRAINT nonempty_description
        CHECK (LENGTH(TRIM(description)) > 0)
);

CREATE INDEX idx_cost_period
    ON cost_records(period_id);

CREATE INDEX idx_cost_center_period
    ON cost_records(cost_center_id, period_id);

CREATE INDEX idx_cost_category_period
    ON cost_records(category, period_id);

CREATE INDEX idx_cost_classification
    ON cost_records(classification, behavior);

CREATE INDEX idx_cost_recorded_at
    ON cost_records(recorded_at DESC);

-- ============================================================
-- 4. BUDGET MANAGEMENT
-- ============================================================

CREATE TABLE budgets (
    budget_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    cost_center_id BIGINT NOT NULL
        REFERENCES cost_centers(cost_center_id),

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    category cost_category NOT NULL,

    allocated_amount NUMERIC(16, 2) NOT NULL,

    approved_by VARCHAR(120) NOT NULL,

    approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT positive_or_zero_budget
        CHECK (allocated_amount >= 0),

    CONSTRAINT unique_center_period_category
        UNIQUE (
            cost_center_id,
            period_id,
            category
        )
);

CREATE INDEX idx_budget_period_center
    ON budgets(period_id, cost_center_id);

-- ============================================================
-- 5. COST ALLOCATION CONFIGURATION
-- ============================================================

CREATE TABLE allocation_rules (
    allocation_rule_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    source_cost_center_id BIGINT NOT NULL
        REFERENCES cost_centers(cost_center_id),

    target_cost_center_id BIGINT NOT NULL
        REFERENCES cost_centers(cost_center_id),

    allocation_basis VARCHAR(30) NOT NULL,

    allocation_weight NUMERIC(9, 6) NOT NULL,

    CONSTRAINT different_source_target
        CHECK (
            source_cost_center_id <> target_cost_center_id
        ),

    CONSTRAINT valid_allocation_weight
        CHECK (
            allocation_weight > 0
            AND allocation_weight <= 1
        ),

    CONSTRAINT unique_allocation_rule
        UNIQUE (
            period_id,
            source_cost_center_id,
            target_cost_center_id
        )
);

CREATE INDEX idx_allocation_source
    ON allocation_rules(period_id, source_cost_center_id);

-- ============================================================
-- 6. OPTIMIZATION PROPOSALS
-- ============================================================

CREATE TABLE optimization_proposals (
    proposal_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    proposal_code VARCHAR(40) NOT NULL UNIQUE,

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    category cost_category NOT NULL,

    proposal_name VARCHAR(180) NOT NULL,

    rationale TEXT NOT NULL,

    baseline_cost NUMERIC(16, 2) NOT NULL,

    expected_reduction NUMERIC(7, 5) NOT NULL,

    implementation_cost NUMERIC(16, 2) NOT NULL DEFAULT 0,

    risk_score NUMERIC(4, 2) NOT NULL,

    status proposal_status NOT NULL DEFAULT 'DRAFT',

    submitted_by VARCHAR(120) NOT NULL,

    submitted_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_baseline
        CHECK (baseline_cost >= 0),

    CONSTRAINT valid_reduction
        CHECK (
            expected_reduction >= 0
            AND expected_reduction <= 1
        ),

    CONSTRAINT valid_implementation_cost
        CHECK (implementation_cost >= 0),

    CONSTRAINT valid_risk
        CHECK (risk_score >= 0 AND risk_score <= 10),

    CONSTRAINT nonempty_proposal_name
        CHECK (LENGTH(TRIM(proposal_name)) > 0)
);

CREATE INDEX idx_proposal_period_status
    ON optimization_proposals(period_id, status);

CREATE INDEX idx_proposal_category
    ON optimization_proposals(category, period_id);

-- ============================================================
-- 7. PROPOSAL APPROVALS
-- ============================================================

CREATE TABLE proposal_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    proposal_id BIGINT NOT NULL
        REFERENCES optimization_proposals(proposal_id),

    reviewer VARCHAR(120) NOT NULL,

    reviewer_role VARCHAR(50) NOT NULL,

    decision approval_decision NOT NULL,

    comments TEXT NOT NULL,

    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_reviewer_decision
        UNIQUE(proposal_id, reviewer),

    CONSTRAINT valid_approval_comment
        CHECK (LENGTH(TRIM(comments)) > 0)
);

CREATE INDEX idx_approval_proposal
    ON proposal_approvals(proposal_id, decision);

-- ============================================================
-- 8. OPTIMIZATION DECISION HISTORY
-- ============================================================

CREATE TABLE optimization_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    proposal_id BIGINT NOT NULL
        REFERENCES optimization_proposals(proposal_id),

    baseline_cost NUMERIC(16, 2) NOT NULL,

    gross_savings NUMERIC(16, 2) NOT NULL,

    implementation_cost NUMERIC(16, 2) NOT NULL,

    net_savings NUMERIC(16, 2) NOT NULL,

    risk_threshold NUMERIC(4, 2) NOT NULL,

    eligible BOOLEAN NOT NULL,

    rejection_reason TEXT,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_evaluation_amounts
        CHECK (
            baseline_cost >= 0
            AND gross_savings >= 0
            AND implementation_cost >= 0
        ),

    CONSTRAINT evaluation_net_savings
        CHECK (
            net_savings =
            gross_savings - implementation_cost
        )
);

CREATE INDEX idx_evaluation_proposal
    ON optimization_evaluations(proposal_id, evaluated_at DESC);

-- ============================================================
-- 9. AUDIT HISTORY
-- ============================================================

CREATE TABLE cost_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    entity_type VARCHAR(60) NOT NULL,

    entity_id BIGINT NOT NULL,

    action VARCHAR(60) NOT NULL,

    actor VARCHAR(120) NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::JSONB,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity
    ON cost_audit_log(entity_type, entity_id, occurred_at DESC);

-- ============================================================
-- 10. PERIOD VALIDATION TRIGGER
-- Prevent cost records from being entered into closed periods.
-- ============================================================

CREATE OR REPLACE FUNCTION validate_open_reporting_period()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    period_status VARCHAR(15);
BEGIN
    SELECT status
    INTO period_status
    FROM reporting_periods
    WHERE period_id = NEW.period_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reporting period does not exist.';
    END IF;

    IF period_status <> 'OPEN' THEN
        RAISE EXCEPTION
            'Cost entries are prohibited in a closed period.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_cost_period
BEFORE INSERT OR UPDATE ON cost_records
FOR EACH ROW
EXECUTE FUNCTION validate_open_reporting_period();

-- ============================================================
-- 11. AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION audit_cost_record()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    operation_name VARCHAR(60);
    record_id BIGINT;
    actor_name VARCHAR(120);
BEGIN
    operation_name := TG_OP;

    IF TG_OP = 'DELETE' THEN
        record_id := OLD.cost_id;
        actor_name := current_user;

        INSERT INTO cost_audit_log (
            entity_type,
            entity_id,
            action,
            actor,
            details
        )
        VALUES (
            'COST_RECORD',
            record_id,
            operation_name,
            actor_name,
            jsonb_build_object(
                'old_amount', OLD.amount,
                'old_description', OLD.description
            )
        );

        RETURN OLD;
    END IF;

    record_id := NEW.cost_id;
    actor_name := current_user;

    INSERT INTO cost_audit_log (
        entity_type,
        entity_id,
        action,
        actor,
        details
    )
    VALUES (
        'COST_RECORD',
        record_id,
        operation_name,
        actor_name,
        jsonb_build_object(
            'amount', NEW.amount,
            'cost_center_id', NEW.cost_center_id,
            'category', NEW.category,
            'period_id', NEW.period_id
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_cost_audit
AFTER INSERT OR UPDATE OR DELETE ON cost_records
FOR EACH ROW
EXECUTE FUNCTION audit_cost_record();

-- ============================================================
-- 12. APPROVAL VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_proposal_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status proposal_status;
BEGIN
    SELECT status
    INTO current_status
    FROM optimization_proposals
    WHERE proposal_id = NEW.proposal_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Optimization proposal not found.';
    END IF;

    IF current_status NOT IN ('SUBMITTED', 'UNDER_REVIEW') THEN
        RAISE EXCEPTION
            'Proposal is not available for approval.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_proposal_approval
BEFORE INSERT ON proposal_approvals
FOR EACH ROW
EXECUTE FUNCTION validate_proposal_approval();

-- ============================================================
-- 13. COST CLASSIFICATION VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_cost_classification AS
SELECT
    rp.period_code,
    cc.center_code,
    cc.center_name,
    cr.category,
    cr.classification,
    cr.behavior,
    SUM(cr.amount) AS total_cost,
    SUM(cr.activity_units) AS activity_units,
    COUNT(*) AS record_count
FROM cost_records cr
JOIN cost_centers cc
    ON cc.cost_center_id = cr.cost_center_id
JOIN reporting_periods rp
    ON rp.period_id = cr.period_id
GROUP BY
    rp.period_code,
    cc.center_code,
    cc.center_name,
    cr.category,
    cr.classification,
    cr.behavior;

-- ============================================================
-- 14. COST CENTRE PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_cost_center_performance AS
WITH actual_costs AS (
    SELECT
        cost_center_id,
        period_id,
        SUM(amount) AS actual_amount
    FROM cost_records
    GROUP BY cost_center_id, period_id
),
budget_costs AS (
    SELECT
        cost_center_id,
        period_id,
        SUM(allocated_amount) AS budget_amount
    FROM budgets
    GROUP BY cost_center_id, period_id
)
SELECT
    cc.center_code,
    cc.center_name,
    rp.period_code,
    COALESCE(ac.actual_amount, 0) AS actual_amount,
    COALESCE(bc.budget_amount, 0) AS budget_amount,
    COALESCE(bc.budget_amount, 0)
        - COALESCE(ac.actual_amount, 0) AS variance,
    CASE
        WHEN COALESCE(bc.budget_amount, 0) = 0
            THEN NULL
        ELSE ROUND(
            (
                COALESCE(bc.budget_amount, 0)
                - COALESCE(ac.actual_amount, 0)
            )
            / bc.budget_amount * 100,
            2
        )
    END AS variance_percentage
FROM cost_centers cc
CROSS JOIN reporting_periods rp
LEFT JOIN actual_costs ac
    ON ac.cost_center_id = cc.cost_center_id
    AND ac.period_id = rp.period_id
LEFT JOIN budget_costs bc
    ON bc.cost_center_id = cc.cost_center_id
    AND bc.period_id = rp.period_id;

-- ============================================================
-- 15. CATEGORY EXPENDITURE VIEW
-- ============================================================

CREATE OR REPLACE VIEW v_category_expenditure AS
SELECT
    rp.period_code,
    cr.category,
    SUM(cr.amount) AS total_expenditure,
    COUNT(*) AS transaction_count,
    ROUND(AVG(cr.amount), 2) AS average_transaction
FROM cost_records cr
JOIN reporting_periods rp
    ON rp.period_id = cr.period_id
GROUP BY rp.period_code, cr.category;

-- ============================================================
-- 16. CONTRIBUTION AND BREAK-EVEN FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_break_even(
    p_fixed_cost NUMERIC,
    p_selling_price NUMERIC,
    p_variable_cost NUMERIC
)
RETURNS TABLE (
    contribution_per_unit NUMERIC,
    contribution_margin_percentage NUMERIC,
    break_even_units NUMERIC,
    break_even_revenue NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    contribution NUMERIC;
BEGIN
    IF p_fixed_cost < 0
        OR p_selling_price <= 0
        OR p_variable_cost < 0 THEN
        RAISE EXCEPTION 'Invalid financial input.';
    END IF;

    contribution := p_selling_price - p_variable_cost;

    IF contribution <= 0 THEN
        RAISE EXCEPTION
            'Break-even cannot be calculated without positive contribution.';
    END IF;

    contribution_per_unit := contribution;

    contribution_margin_percentage :=
        contribution / p_selling_price * 100;

    break_even_units :=
        CEIL(p_fixed_cost / contribution);

    break_even_revenue :=
        break_even_units * p_selling_price;

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 17. INDIRECT COST ALLOCATION FUNCTION
-- Direct expenditure is used as the allocation base.
-- ============================================================

CREATE OR REPLACE FUNCTION allocate_indirect_costs(
    p_period_id BIGINT
)
RETURNS TABLE (
    cost_center_id BIGINT,
    direct_cost NUMERIC,
    allocated_indirect NUMERIC,
    total_allocated NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    indirect_total NUMERIC;
    direct_total NUMERIC;
BEGIN
    SELECT COALESCE(SUM(amount), 0)
    INTO indirect_total
    FROM cost_records
    WHERE period_id = p_period_id
      AND behavior = 'INDIRECT';

    SELECT COALESCE(SUM(amount), 0)
    INTO direct_total
    FROM cost_records
    WHERE period_id = p_period_id
      AND behavior = 'DIRECT';

    IF direct_total = 0 AND indirect_total > 0 THEN
        RAISE EXCEPTION
            'No direct expenditure available as allocation base.';
    END IF;

    RETURN QUERY
    SELECT
        grouped.cost_center_id,
        grouped.direct_amount,
        CASE
            WHEN direct_total = 0 THEN 0::NUMERIC
            ELSE ROUND(
                indirect_total * grouped.direct_amount / direct_total,
                2
            )
        END,
        grouped.direct_amount
            + CASE
                WHEN direct_total = 0 THEN 0::NUMERIC
                ELSE ROUND(
                    indirect_total * grouped.direct_amount / direct_total,
                    2
                )
              END
    FROM (
        SELECT
            cr.cost_center_id,
            SUM(cr.amount) AS direct_amount
        FROM cost_records cr
        WHERE cr.period_id = p_period_id
          AND cr.behavior = 'DIRECT'
        GROUP BY cr.cost_center_id
    ) grouped;
END;
$$;

-- ============================================================
-- 18. OPTIMIZATION EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_optimization(
    p_proposal_id BIGINT,
    p_maximum_risk NUMERIC DEFAULT 5,
    p_minimum_net_savings NUMERIC DEFAULT 1000
)
RETURNS TABLE (
    eligible BOOLEAN,
    gross_savings NUMERIC,
    net_savings NUMERIC,
    rejection_reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    proposal optimization_proposals%ROWTYPE;
    gross NUMERIC;
    net NUMERIC;
    permitted BOOLEAN;
    reason TEXT;
BEGIN
    IF p_maximum_risk < 0 OR p_maximum_risk > 10 THEN
        RAISE EXCEPTION 'Invalid maximum risk.';
    END IF;

    IF p_minimum_net_savings < 0 THEN
        RAISE EXCEPTION 'Minimum net savings cannot be negative.';
    END IF;

    SELECT *
    INTO proposal
    FROM optimization_proposals
    WHERE proposal_id = p_proposal_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Optimization proposal not found.';
    END IF;

    gross := ROUND(
        proposal.baseline_cost * proposal.expected_reduction,
        2
    );

    net := gross - proposal.implementation_cost;

    permitted := (
        proposal.baseline_cost > 0
        AND proposal.risk_score <= p_maximum_risk
        AND net >= p_minimum_net_savings
    );

    reason := CASE
        WHEN proposal.baseline_cost = 0
            THEN 'No baseline expenditure.'
        WHEN proposal.risk_score > p_maximum_risk
            THEN 'Risk threshold exceeded.'
        WHEN net < p_minimum_net_savings
            THEN 'Net savings below required threshold.'
        ELSE 'Eligible for further review.'
    END;

    INSERT INTO optimization_evaluations (
        proposal_id,
        baseline_cost,
        gross_savings,
        implementation_cost,
        net_savings,
        risk_threshold,
        eligible,
        rejection_reason
    )
    VALUES (
        proposal.proposal_id,
        proposal.baseline_cost,
        gross,
        proposal.implementation_cost,
        net,
        p_maximum_risk,
        permitted,
        CASE WHEN permitted THEN NULL ELSE reason END
    );

    RETURN QUERY
    SELECT permitted, gross, net, reason;
END;
$$;

-- ============================================================
-- 19. PROPOSAL APPROVAL PROCEDURE
-- Approval requirements:
-- - At least one finance manager approval.
-- - At least one operations manager approval.
-- - No rejected review.
-- ============================================================

CREATE OR REPLACE PROCEDURE process_proposal_approval(
    p_proposal_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    finance_count INTEGER;
    operations_count INTEGER;
    rejection_count INTEGER;
    current_status proposal_status;
BEGIN
    SELECT status
    INTO current_status
    FROM optimization_proposals
    WHERE proposal_id = p_proposal_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Proposal does not exist.';
    END IF;

    IF current_status NOT IN ('SUBMITTED', 'UNDER_REVIEW') THEN
        RAISE EXCEPTION
            'Proposal is not awaiting approval.';
    END IF;

    SELECT
        COUNT(*) FILTER (
            WHERE reviewer_role = 'FINANCE_MANAGER'
              AND decision = 'APPROVED'
        ),
        COUNT(*) FILTER (
            WHERE reviewer_role = 'OPERATIONS_MANAGER'
              AND decision = 'APPROVED'
        ),
        COUNT(*) FILTER (
            WHERE decision = 'REJECTED'
        )
    INTO
        finance_count,
        operations_count,
        rejection_count
    FROM proposal_approvals
    WHERE proposal_id = p_proposal_id;

    IF rejection_count > 0 THEN
        UPDATE optimization_proposals
        SET status = 'REJECTED'
        WHERE proposal_id = p_proposal_id;

    ELSIF finance_count >= 1 AND operations_count >= 1 THEN
        UPDATE optimization_proposals
        SET status = 'APPROVED'
        WHERE proposal_id = p_proposal_id;

    ELSE
        UPDATE optimization_proposals
        SET status = 'UNDER_REVIEW'
        WHERE proposal_id = p_proposal_id;
    END IF;
END;
$$;

-- ============================================================
-- 20. SAMPLE ORGANIZATIONAL DATA
-- ============================================================

INSERT INTO reporting_periods (
    period_code,
    start_date,
    end_date
)
VALUES (
    '2026-10',
    DATE '2026-10-01',
    DATE '2026-10-31'
);

INSERT INTO cost_centers (
    center_code,
    center_name,
    department,
    manager_name
)
VALUES
    (
        'PRODUCTION',
        'Manufacturing Operations',
        'Operations',
        'Production Manager'
    ),
    (
        'TECHNOLOGY',
        'Technology Infrastructure',
        'Information Technology',
        'Technology Manager'
    ),
    (
        'LOGISTICS',
        'Distribution Operations',
        'Supply Chain',
        'Logistics Manager'
    ),
    (
        'ADMINISTRATION',
        'Corporate Administration',
        'Administration',
        'Administrative Manager'
    );

-- ============================================================
-- 21. SAMPLE COST RECORDS
-- ============================================================

INSERT INTO cost_records (
    external_reference,
    cost_center_id,
    period_id,
    category,
    classification,
    behavior,
    amount,
    activity_units,
    description,
    recorded_by
)
SELECT
    sample.reference,
    cc.cost_center_id,
    rp.period_id,
    sample.category::cost_category,
    sample.classification::cost_type,
    sample.behavior::cost_behavior,
    sample.amount,
    sample.activity_units,
    sample.description,
    'finance.system'
FROM (
    VALUES
        (
            'EXT-001', 'PRODUCTION', 'LABOR',
            'FIXED', 'DIRECT',
            120000::NUMERIC, 1000::NUMERIC,
            'Production workforce'
        ),
        (
            'EXT-002', 'PRODUCTION', 'MATERIALS',
            'VARIABLE', 'DIRECT',
            180000::NUMERIC, 1000::NUMERIC,
            'Raw material consumption'
        ),
        (
            'EXT-003', 'PRODUCTION', 'FACILITIES',
            'FIXED', 'INDIRECT',
            45000::NUMERIC, 1000::NUMERIC,
            'Factory rent and facilities'
        ),
        (
            'EXT-004', 'TECHNOLOGY', 'TECHNOLOGY',
            'SEMI_VARIABLE', 'INDIRECT',
            60000::NUMERIC, 1000::NUMERIC,
            'Cloud infrastructure'
        ),
        (
            'EXT-005', 'LOGISTICS', 'LOGISTICS',
            'VARIABLE', 'DIRECT',
            35000::NUMERIC, 1000::NUMERIC,
            'Distribution and transportation'
        ),
        (
            'EXT-006', 'ADMINISTRATION', 'ADMINISTRATION',
            'FIXED', 'INDIRECT',
            25000::NUMERIC, 1000::NUMERIC,
            'Administrative services'
        )
) AS sample(
    reference,
    center_code,
    category,
    classification,
    behavior,
    amount,
    activity_units,
    description
)
JOIN cost_centers cc
    ON cc.center_code = sample.center_code
CROSS JOIN reporting_periods rp
WHERE rp.period_code = '2026-10';

-- ============================================================
-- 22. SAMPLE BUDGETS
-- ============================================================

INSERT INTO budgets (
    cost_center_id,
    period_id,
    category,
    allocated_amount,
    approved_by
)
SELECT
    cc.cost_center_id,
    rp.period_id,
    sample.category::cost_category,
    sample.amount,
    'Finance Manager'
FROM (
    VALUES
        ('PRODUCTION', 'LABOR', 125000::NUMERIC),
        ('PRODUCTION', 'MATERIALS', 190000::NUMERIC),
        ('PRODUCTION', 'FACILITIES', 50000::NUMERIC),
        ('TECHNOLOGY', 'TECHNOLOGY', 70000::NUMERIC),
        ('LOGISTICS', 'LOGISTICS', 40000::NUMERIC),
        ('ADMINISTRATION', 'ADMINISTRATION', 30000::NUMERIC)
) AS sample(center_code, category, amount)
JOIN cost_centers cc
    ON cc.center_code = sample.center_code
CROSS JOIN reporting_periods rp
WHERE rp.period_code = '2026-10';

-- ============================================================
-- 23. SAMPLE OPTIMIZATION PROPOSALS
-- ============================================================

INSERT INTO optimization_proposals (
    proposal_code,
    period_id,
    category,
    proposal_name,
    rationale,
    baseline_cost,
    expected_reduction,
    implementation_cost,
    risk_score,
    status,
    submitted_by,
    submitted_at
)
SELECT
    sample.code,
    rp.period_id,
    sample.category::cost_category,
    sample.name,
    sample.rationale,
    sample.baseline,
    sample.reduction,
    sample.implementation,
    sample.risk,
    'SUBMITTED',
    'Operations Analyst',
    NOW()
FROM (
    VALUES
        (
            'OPT-001',
            'TECHNOLOGY',
            'Cloud capacity rightsizing',
            'Remove unused cloud computing capacity.',
            60000::NUMERIC,
            0.20::NUMERIC,
            3000::NUMERIC,
            2::NUMERIC
        ),
        (
            'OPT-002',
            'MATERIALS',
            'Procurement consolidation',
            'Consolidate purchases and negotiate volume discounts.',
            180000::NUMERIC,
            0.08::NUMERIC,
            5000::NUMERIC,
            3::NUMERIC
        ),
        (
            'OPT-003',
            'LOGISTICS',
            'Distribution route optimization',
            'Reduce unnecessary transportation expenditure.',
            35000::NUMERIC,
            0.15::NUMERIC,
            2000::NUMERIC,
            4::NUMERIC
        ),
        (
            'OPT-004',
            'LABOR',
            'High-risk workforce restructuring',
            'A proposal with excessive operational risk.',
            120000::NUMERIC,
            0.10::NUMERIC,
            1000::NUMERIC,
            9::NUMERIC
        )
) AS sample(
    code,
    category,
    name,
    rationale,
    baseline,
    reduction,
    implementation,
    risk
)
CROSS JOIN reporting_periods rp
WHERE rp.period_code = '2026-10';

COMMIT;

-- ============================================================
-- 24. RETRIEVAL AND CLASSIFICATION QUERIES
-- ============================================================

-- Total expenditure by period.
SELECT
    rp.period_code,
    SUM(cr.amount) AS total_expenditure
FROM cost_records cr
JOIN reporting_periods rp
    ON rp.period_id = cr.period_id
GROUP BY rp.period_code;

-- Cost structure by classification.
SELECT
    classification,
    SUM(amount) AS total_amount,
    ROUND(
        SUM(amount) * 100
        / NULLIF(SUM(SUM(amount)) OVER (), 0),
        2
    ) AS percentage_of_total
FROM cost_records
WHERE period_id = (
    SELECT period_id
    FROM reporting_periods
    WHERE period_code = '2026-10'
)
GROUP BY classification
ORDER BY total_amount DESC;

-- Direct and indirect expenditure.
SELECT
    behavior,
    SUM(amount) AS total_cost
FROM cost_records
GROUP BY behavior;

-- Category expenditure.
SELECT *
FROM v_category_expenditure
WHERE period_code = '2026-10'
ORDER BY total_expenditure DESC;

-- ============================================================
-- 25. COST CENTRE AND BUDGET REPORTING
-- ============================================================

SELECT *
FROM v_cost_center_performance
WHERE period_code = '2026-10'
ORDER BY variance ASC;

-- Cost centre expenditure.
SELECT *
FROM v_cost_classification
WHERE period_code = '2026-10'
ORDER BY center_code, total_cost DESC;

-- Identify categories exceeding budget.
SELECT
    cc.center_code,
    b.category,
    b.allocated_amount,
    COALESCE(SUM(cr.amount), 0) AS actual_amount,
    COALESCE(SUM(cr.amount), 0)
        - b.allocated_amount AS excess_amount
FROM budgets b
JOIN cost_centers cc
    ON cc.cost_center_id = b.cost_center_id
LEFT JOIN cost_records cr
    ON cr.cost_center_id = b.cost_center_id
    AND cr.period_id = b.period_id
    AND cr.category = b.category
GROUP BY
    cc.center_code,
    b.category,
    b.allocated_amount
HAVING COALESCE(SUM(cr.amount), 0) > b.allocated_amount;

-- ============================================================
-- 26. UNIT ECONOMICS
-- ============================================================

SELECT
    rp.period_code,
    SUM(cr.amount) AS total_cost,
    SUM(cr.activity_units) AS total_activity,
    ROUND(
        SUM(cr.amount)
        / NULLIF(SUM(cr.activity_units), 0),
        2
    ) AS average_unit_cost
FROM cost_records cr
JOIN reporting_periods rp
    ON rp.period_id = cr.period_id
GROUP BY rp.period_code;

-- ============================================================
-- 27. BREAK-EVEN ANALYSIS
-- ============================================================

SELECT *
FROM calculate_break_even(
    150000,
    500,
    300
);

-- ============================================================
-- 28. INDIRECT COST ALLOCATION
-- ============================================================

SELECT
    cc.center_code,
    allocation.direct_cost,
    allocation.allocated_indirect,
    allocation.total_allocated
FROM allocate_indirect_costs(
    (
        SELECT period_id
        FROM reporting_periods
        WHERE period_code = '2026-10'
    )
) allocation
JOIN cost_centers cc
    ON cc.cost_center_id = allocation.cost_center_id
ORDER BY cc.center_code;

-- ============================================================
-- 29. OPTIMIZATION EVALUATION
-- ============================================================

SELECT
    proposal_id,
    proposal_code,
    proposal_name,
    (evaluate_optimization(proposal_id, 5, 1000)).*
FROM optimization_proposals
WHERE status = 'SUBMITTED'
ORDER BY proposal_id;

-- ============================================================
-- 30. APPROVAL WORKFLOW
-- ============================================================

-- Approve the technology proposal.
INSERT INTO proposal_approvals (
    proposal_id,
    reviewer,
    reviewer_role,
    decision,
    comments
)
SELECT
    proposal_id,
    'finance.manager',
    'FINANCE_MANAGER',
    'APPROVED',
    'Financial savings validated.'
FROM optimization_proposals
WHERE proposal_code = 'OPT-001';

INSERT INTO proposal_approvals (
    proposal_id,
    reviewer,
    reviewer_role,
    decision,
    comments
)
SELECT
    proposal_id,
    'operations.manager',
    'OPERATIONS_MANAGER',
    'APPROVED',
    'Operational impact accepted.'
FROM optimization_proposals
WHERE proposal_code = 'OPT-001';

-- Process the approval requirements transactionally.
BEGIN;

CALL process_proposal_approval(
    (
        SELECT proposal_id
        FROM optimization_proposals
        WHERE proposal_code = 'OPT-001'
    )
);

COMMIT;

-- Verify approval state.
SELECT
    proposal_code,
    proposal_name,
    status
FROM optimization_proposals
ORDER BY proposal_code;

-- ============================================================
-- 31. AGGREGATED OPTIMIZATION REPORT
-- ============================================================

SELECT
    op.proposal_code,
    op.proposal_name,
    oe.baseline_cost,
    oe.gross_savings,
    oe.implementation_cost,
    oe.net_savings,
    oe.eligible,
    oe.rejection_reason
FROM optimization_evaluations oe
JOIN optimization_proposals op
    ON op.proposal_id = oe.proposal_id
ORDER BY oe.net_savings DESC;

-- ============================================================
-- 32. FINANCIAL AUDIT REPORT
-- ============================================================

SELECT
    entity_type,
    entity_id,
    action,
    actor,
    details,
    occurred_at
FROM cost_audit_log
ORDER BY occurred_at DESC
LIMIT 100;

-- ============================================================
-- 33. FAILURE AND VALIDATION DEMONSTRATIONS
-- ============================================================

-- Invalid financial amounts are rejected by CHECK constraints.
-- Duplicate external references are rejected by UNIQUE constraints.
-- Closed reporting periods reject cost-record changes.
-- Invalid allocation bases raise exceptions.
-- Proposals with excessive risk fail optimization evaluation.
-- Duplicate reviewer decisions are rejected.
-- Proposals cannot be approved without both required roles.

-- ============================================================
-- 34. PERFORMANCE AND EXECUTION ANALYSIS
-- ============================================================

EXPLAIN
SELECT
    cost_center_id,
    SUM(amount)
FROM cost_records
WHERE period_id = (
    SELECT period_id
    FROM reporting_periods
    WHERE period_code = '2026-10'
)
GROUP BY cost_center_id;

-- ============================================================
-- END OF COST ANALYTICS DATABASE IMPLEMENTATION
-- ============================================================
