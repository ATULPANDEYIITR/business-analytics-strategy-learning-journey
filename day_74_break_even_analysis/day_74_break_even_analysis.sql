/*
===============================================================================
BREAK-EVEN ANALYSIS MANAGEMENT DATABASE
PostgreSQL 14+

Domain:
- Cost classification
- Products and pricing
- Fixed and variable costs
- Contribution margin
- Break-even analysis
- Target-profit calculations
- Multi-product sales mix
- Financial scenarios
- Profitability policy evaluation
- Audit history

All monetary values use NUMERIC rather than FLOAT.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS break_even;

SET search_path TO break_even, public;

-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE cost_category AS ENUM (
    'FIXED',
    'VARIABLE'
);

CREATE TYPE scenario_status AS ENUM (
    'DRAFT',
    'EVALUATED',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE decision_status AS ENUM (
    'APPROVED',
    'REJECTED',
    'WARNING'
);

-- ============================================================================
-- 2. ORGANIZATION AND COST CENTRES
-- ============================================================================

CREATE TABLE organization (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cost_center (
    cost_center_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    center_name VARCHAR(120) NOT NULL,
    UNIQUE (organization_id, center_name)
);

-- ============================================================================
-- 3. PRODUCTS
-- ============================================================================

CREATE TABLE product (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    product_code VARCHAR(40) NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    selling_price NUMERIC(18,2) NOT NULL,
    variable_cost_per_unit NUMERIC(18,2) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_selling_price
        CHECK (selling_price > 0),

    CONSTRAINT nonnegative_variable_cost
        CHECK (variable_cost_per_unit >= 0),

    CONSTRAINT positive_contribution
        CHECK (selling_price > variable_cost_per_unit),

    UNIQUE (organization_id, product_code)
);

CREATE INDEX idx_product_organization
    ON product(organization_id);

CREATE INDEX idx_product_active
    ON product(organization_id, active);

-- ============================================================================
-- 4. COST REGISTER
-- ============================================================================

CREATE TABLE cost_item (
    cost_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    cost_center_id BIGINT
        REFERENCES cost_center(cost_center_id),
    cost_name VARCHAR(150) NOT NULL,
    category cost_category NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (amount >= 0),

    CHECK (
        effective_to IS NULL
        OR effective_to >= effective_from
    )
);

CREATE INDEX idx_cost_organization_category
    ON cost_item(organization_id, category);

CREATE INDEX idx_cost_effective_dates
    ON cost_item(organization_id, effective_from, effective_to);

-- ============================================================================
-- 5. SALES MIX
-- ============================================================================

CREATE TABLE sales_mix (
    mix_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    product_id BIGINT NOT NULL
        REFERENCES product(product_id),
    mix_percentage NUMERIC(9,6) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,

    CHECK (
        mix_percentage > 0
        AND mix_percentage <= 100
    ),

    CHECK (
        effective_to IS NULL
        OR effective_to >= effective_from
    ),

    UNIQUE (organization_id, product_id, effective_from)
);

CREATE INDEX idx_sales_mix_organization
    ON sales_mix(organization_id, effective_from);

-- ============================================================================
-- 6. ANALYSIS RECORDS
-- ============================================================================

CREATE TABLE analysis (
    analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    analysis_name VARCHAR(150) NOT NULL,
    analysis_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_units BIGINT NOT NULL DEFAULT 0,
    target_profit NUMERIC(18,2) NOT NULL DEFAULT 0,
    status scenario_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (expected_units >= 0),
    CHECK (target_profit >= 0)
);

CREATE INDEX idx_analysis_organization_date
    ON analysis(organization_id, analysis_date DESC);

-- ============================================================================
-- 7. PRODUCT ANALYSIS SNAPSHOTS
-- ============================================================================

CREATE TABLE analysis_product (
    analysis_product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id BIGINT NOT NULL
        REFERENCES analysis(analysis_id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL
        REFERENCES product(product_id),
    sales_mix_percentage NUMERIC(9,6) NOT NULL,
    selling_price NUMERIC(18,2) NOT NULL,
    variable_cost NUMERIC(18,2) NOT NULL,

    CHECK (sales_mix_percentage > 0),
    CHECK (selling_price > variable_cost),
    CHECK (variable_cost >= 0),

    UNIQUE (analysis_id, product_id)
);

-- ============================================================================
-- 8. ANALYSIS RESULTS
-- ============================================================================

CREATE TABLE analysis_result (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id BIGINT NOT NULL UNIQUE
        REFERENCES analysis(analysis_id) ON DELETE CASCADE,
    fixed_costs NUMERIC(18,2) NOT NULL,
    variable_cost_per_unit NUMERIC(18,2) NOT NULL,
    selling_price NUMERIC(18,2) NOT NULL,
    contribution_per_unit NUMERIC(18,2) NOT NULL,
    contribution_margin_ratio NUMERIC(12,8) NOT NULL,
    break_even_units NUMERIC(20,6) NOT NULL,
    practical_break_even_units BIGINT NOT NULL,
    break_even_revenue NUMERIC(20,2) NOT NULL,
    actual_revenue NUMERIC(20,2) NOT NULL,
    actual_profit NUMERIC(20,2) NOT NULL,
    margin_of_safety_units NUMERIC(20,6) NOT NULL,
    margin_of_safety_ratio NUMERIC(12,8),
    target_profit_units BIGINT NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (fixed_costs >= 0),
    CHECK (variable_cost_per_unit >= 0),
    CHECK (selling_price > variable_cost_per_unit),
    CHECK (contribution_per_unit > 0),
    CHECK (contribution_margin_ratio > 0),
    CHECK (break_even_units >= 0),
    CHECK (practical_break_even_units >= 0),
    CHECK (break_even_revenue >= 0),
    CHECK (target_profit_units >= 0)
);

-- ============================================================================
-- 9. PROFITABILITY POLICIES
-- ============================================================================

CREATE TABLE profitability_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organization(organization_id),
    policy_name VARCHAR(150) NOT NULL,
    minimum_margin_of_safety NUMERIC(8,6) NOT NULL DEFAULT 0,
    minimum_contribution_ratio NUMERIC(8,6) NOT NULL DEFAULT 0,
    reject_operating_loss BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (
        minimum_margin_of_safety BETWEEN 0 AND 1
    ),

    CHECK (
        minimum_contribution_ratio BETWEEN 0 AND 1
    ),

    UNIQUE (organization_id, policy_name)
);

CREATE TABLE policy_evaluation (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id BIGINT NOT NULL
        REFERENCES analysis(analysis_id),
    policy_id BIGINT NOT NULL
        REFERENCES profitability_policy(policy_id),
    status decision_status NOT NULL,
    violations JSONB NOT NULL DEFAULT '[]'::JSONB,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (analysis_id, policy_id)
);

-- ============================================================================
-- 10. SCENARIO ANALYSIS
-- ============================================================================

CREATE TABLE financial_scenario (
    scenario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id BIGINT NOT NULL
        REFERENCES analysis(analysis_id) ON DELETE CASCADE,
    scenario_name VARCHAR(120) NOT NULL,
    price_change_percentage NUMERIC(9,6) NOT NULL DEFAULT 0,
    variable_cost_change_percentage NUMERIC(9,6) NOT NULL DEFAULT 0,
    fixed_cost_change_percentage NUMERIC(9,6) NOT NULL DEFAULT 0,
    scenario_break_even_units NUMERIC(20,6),
    scenario_break_even_revenue NUMERIC(20,2),
    status scenario_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (price_change_percentage > -100),
    CHECK (variable_cost_change_percentage > -100),
    CHECK (fixed_cost_change_percentage > -100),

    UNIQUE (analysis_id, scenario_name)
);

-- ============================================================================
-- 11. AUDIT LOG
-- ============================================================================

CREATE TABLE financial_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id BIGINT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    database_user TEXT NOT NULL DEFAULT CURRENT_USER,
    old_values JSONB,
    new_values JSONB
);

CREATE INDEX idx_audit_changed_at
    ON financial_audit(changed_at DESC);

-- ============================================================================
-- 12. COST AGGREGATION VIEW
-- ============================================================================

CREATE VIEW organization_cost_summary AS
SELECT
    organization_id,
    COALESCE(
        SUM(amount) FILTER (
            WHERE category = 'FIXED'
        ), 0
    ) AS total_fixed_costs,

    COALESCE(
        SUM(amount) FILTER (
            WHERE category = 'VARIABLE'
        ), 0
    ) AS total_variable_costs,

    COUNT(*) AS cost_item_count

FROM cost_item

WHERE effective_from <= CURRENT_DATE
  AND (
      effective_to IS NULL
      OR effective_to >= CURRENT_DATE
  )

GROUP BY organization_id;

-- ============================================================================
-- 13. CONTRIBUTION MARGIN VIEW
-- ============================================================================

CREATE VIEW product_contribution_report AS
SELECT
    product_id,
    organization_id,
    product_code,
    product_name,
    selling_price,
    variable_cost_per_unit,

    selling_price - variable_cost_per_unit
        AS contribution_per_unit,

    ROUND(
        (
            selling_price - variable_cost_per_unit
        ) / selling_price,
        6
    ) AS contribution_margin_ratio

FROM product
WHERE active = TRUE;

-- ============================================================================
-- 14. COST CLASSIFICATION VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_cost_center_organization()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    center_organization BIGINT;
BEGIN
    IF NEW.cost_center_id IS NOT NULL THEN
        SELECT organization_id
        INTO center_organization
        FROM cost_center
        WHERE cost_center_id = NEW.cost_center_id;

        IF center_organization IS DISTINCT FROM
            NEW.organization_id THEN
            RAISE EXCEPTION
                'Cost center belongs to a different organization.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_cost_center
BEFORE INSERT OR UPDATE ON cost_item
FOR EACH ROW
EXECUTE FUNCTION validate_cost_center_organization();

-- ============================================================================
-- 15. PRODUCT ORGANIZATION VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_sales_mix_organization()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    product_organization BIGINT;
BEGIN
    SELECT organization_id
    INTO product_organization
    FROM product
    WHERE product_id = NEW.product_id;

    IF product_organization IS DISTINCT FROM
        NEW.organization_id THEN
        RAISE EXCEPTION
            'Product and sales mix organizations must match.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sales_mix
BEFORE INSERT OR UPDATE ON sales_mix
FOR EACH ROW
EXECUTE FUNCTION validate_sales_mix_organization();

-- ============================================================================
-- 16. ANALYSIS PRODUCT VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_analysis_product_organization()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    analysis_organization BIGINT;
    product_organization BIGINT;
BEGIN
    SELECT organization_id
    INTO analysis_organization
    FROM analysis
    WHERE analysis_id = NEW.analysis_id;

    SELECT organization_id
    INTO product_organization
    FROM product
    WHERE product_id = NEW.product_id;

    IF analysis_organization IS DISTINCT FROM
        product_organization THEN
        RAISE EXCEPTION
            'Analysis and product organizations must match.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_analysis_product
BEFORE INSERT OR UPDATE ON analysis_product
FOR EACH ROW
EXECUTE FUNCTION validate_analysis_product_organization();

-- ============================================================================
-- 17. COST AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_cost_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO financial_audit (
            table_name,
            operation,
            record_id,
            new_values
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.cost_id,
            TO_JSONB(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO financial_audit (
            table_name,
            operation,
            record_id,
            old_values,
            new_values
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            NEW.cost_id,
            TO_JSONB(OLD),
            TO_JSONB(NEW)
        );

        RETURN NEW;

    ELSE
        INSERT INTO financial_audit (
            table_name,
            operation,
            record_id,
            old_values
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            OLD.cost_id,
            TO_JSONB(OLD)
        );

        RETURN OLD;
    END IF;
END;
$$;

CREATE TRIGGER trg_audit_cost
AFTER INSERT OR UPDATE OR DELETE ON cost_item
FOR EACH ROW
EXECUTE FUNCTION audit_cost_changes();

-- ============================================================================
-- 18. BREAK-EVEN CALCULATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_break_even(
    p_fixed_costs NUMERIC,
    p_selling_price NUMERIC,
    p_variable_cost NUMERIC
)
RETURNS TABLE (
    contribution_per_unit NUMERIC,
    contribution_margin_ratio NUMERIC,
    break_even_units NUMERIC,
    practical_break_even_units BIGINT,
    break_even_revenue NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_contribution NUMERIC;
    v_margin_ratio NUMERIC;
    v_units NUMERIC;
BEGIN
    IF p_fixed_costs IS NULL
        OR p_selling_price IS NULL
        OR p_variable_cost IS NULL THEN
        RAISE EXCEPTION
            'Financial inputs cannot be NULL.';
    END IF;

    IF p_fixed_costs < 0
        OR p_variable_cost < 0
        OR p_selling_price <= 0 THEN
        RAISE EXCEPTION
            'Invalid financial input values.';
    END IF;

    v_contribution :=
        p_selling_price - p_variable_cost;

    IF v_contribution <= 0 THEN
        RAISE EXCEPTION
            'Contribution margin must be positive.';
    END IF;

    v_margin_ratio :=
        v_contribution / p_selling_price;

    v_units :=
        p_fixed_costs / v_contribution;

    RETURN QUERY
    SELECT
        v_contribution,
        v_margin_ratio,
        v_units,
        CEIL(v_units)::BIGINT,
        p_fixed_costs / v_margin_ratio;
END;
$$;

-- ============================================================================
-- 19. TARGET PROFIT FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_target_profit_units(
    p_fixed_costs NUMERIC,
    p_target_profit NUMERIC,
    p_selling_price NUMERIC,
    p_variable_cost NUMERIC
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    v_contribution NUMERIC;
BEGIN
    IF p_fixed_costs < 0
        OR p_target_profit < 0
        OR p_selling_price <= 0
        OR p_variable_cost < 0 THEN
        RAISE EXCEPTION
            'Invalid target-profit inputs.';
    END IF;

    v_contribution :=
        p_selling_price - p_variable_cost;

    IF v_contribution <= 0 THEN
        RAISE EXCEPTION
            'Target-profit analysis requires positive contribution.';
    END IF;

    RETURN CEIL(
        (p_fixed_costs + p_target_profit)
        / v_contribution
    )::BIGINT;
END;
$$;

-- ============================================================================
-- 20. OPERATING PROFIT FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_operating_profit(
    p_units BIGINT,
    p_fixed_costs NUMERIC,
    p_selling_price NUMERIC,
    p_variable_cost NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_units < 0 THEN
        RAISE EXCEPTION 'Sales units cannot be negative.';
    END IF;

    IF p_fixed_costs < 0
        OR p_selling_price <= 0
        OR p_variable_cost < 0
        OR p_variable_cost >= p_selling_price THEN
        RAISE EXCEPTION 'Invalid financial parameters.';
    END IF;

    RETURN (
        p_units * p_selling_price
        - p_units * p_variable_cost
        - p_fixed_costs
    );
END;
$$;

-- ============================================================================
-- 21. MULTI-PRODUCT BREAK-EVEN FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_weighted_break_even(
    p_organization_id BIGINT,
    p_fixed_costs NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_total_mix NUMERIC;
    v_weighted_contribution NUMERIC;
BEGIN
    IF p_fixed_costs < 0 THEN
        RAISE EXCEPTION 'Fixed costs cannot be negative.';
    END IF;

    SELECT
        SUM(sm.mix_percentage),
        SUM(
            (
                sm.mix_percentage
                / 100.0
            ) *
            (
                p.selling_price
                - p.variable_cost_per_unit
            )
        )
    INTO
        v_total_mix,
        v_weighted_contribution

    FROM sales_mix sm

    JOIN product p
        ON p.product_id = sm.product_id

    WHERE sm.organization_id = p_organization_id
      AND sm.effective_from <= CURRENT_DATE
      AND (
          sm.effective_to IS NULL
          OR sm.effective_to >= CURRENT_DATE
      )
      AND p.active = TRUE;

    IF COALESCE(v_total_mix, 0) = 0 THEN
        RAISE EXCEPTION
            'No active sales mix available.';
    END IF;

    IF ABS(v_total_mix - 100) > 0.000001 THEN
        RAISE EXCEPTION
            'Active sales mix must total 100 percent. Current: %',
            v_total_mix;
    END IF;

    IF v_weighted_contribution <= 0 THEN
        RAISE EXCEPTION
            'Weighted contribution must be positive.';
    END IF;

    RETURN p_fixed_costs / v_weighted_contribution;
END;
$$;

-- ============================================================================
-- 22. PROFITABILITY POLICY EVALUATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION evaluate_profitability_policy(
    p_analysis_id BIGINT,
    p_policy_id BIGINT
)
RETURNS decision_status
LANGUAGE plpgsql
AS $$
DECLARE
    v_result analysis_result%ROWTYPE;
    v_policy profitability_policy%ROWTYPE;
    v_status decision_status := 'APPROVED';
    v_violations JSONB := '[]'::JSONB;
BEGIN
    SELECT *
    INTO v_result
    FROM analysis_result
    WHERE analysis_id = p_analysis_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Analysis result does not exist.';
    END IF;

    SELECT *
    INTO v_policy
    FROM profitability_policy
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Active profitability policy does not exist.';
    END IF;

    IF v_policy.organization_id <> (
        SELECT organization_id
        FROM analysis
        WHERE analysis_id = p_analysis_id
    ) THEN
        RAISE EXCEPTION
            'Policy and analysis organizations do not match.';
    END IF;

    IF v_policy.reject_operating_loss
        AND v_result.actual_profit < 0 THEN

        v_violations :=
            v_violations ||
            '["OPERATING_LOSS"]'::JSONB;
    END IF;

    IF v_result.margin_of_safety_ratio IS NULL
        OR v_result.margin_of_safety_ratio <
            v_policy.minimum_margin_of_safety THEN

        v_violations :=
            v_violations ||
            '["LOW_MARGIN_OF_SAFETY"]'::JSONB;
    END IF;

    IF v_result.contribution_margin_ratio <
        v_policy.minimum_contribution_ratio THEN

        v_violations :=
            v_violations ||
            '["LOW_CONTRIBUTION_MARGIN"]'::JSONB;
    END IF;

    IF JSONB_ARRAY_LENGTH(v_violations) > 0 THEN
        v_status := 'REJECTED';
    END IF;

    INSERT INTO policy_evaluation (
        analysis_id,
        policy_id,
        status,
        violations
    )
    VALUES (
        p_analysis_id,
        p_policy_id,
        v_status,
        v_violations
    )
    ON CONFLICT (analysis_id, policy_id)
    DO UPDATE SET
        status = EXCLUDED.status,
        violations = EXCLUDED.violations,
        evaluated_at = CURRENT_TIMESTAMP;

    RETURN v_status;
END;
$$;

-- ============================================================================
-- 23. ANALYSIS PROCESSING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE process_break_even_analysis(
    p_analysis_id BIGINT,
    p_selling_price NUMERIC,
    p_variable_cost NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_fixed_costs NUMERIC;
    v_expected_units BIGINT;
    v_target_profit NUMERIC;
    v_contribution NUMERIC;
    v_margin_ratio NUMERIC;
    v_bep NUMERIC;
    v_revenue NUMERIC;
    v_profit NUMERIC;
    v_margin_safety NUMERIC;
BEGIN
    -- Lock the analysis to prevent concurrent processing.
    SELECT expected_units, target_profit
    INTO v_expected_units, v_target_profit
    FROM analysis
    WHERE analysis_id = p_analysis_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Analysis record % does not exist.',
            p_analysis_id;
    END IF;

    SELECT COALESCE(SUM(amount), 0)
    INTO v_fixed_costs
    FROM cost_item
    WHERE organization_id = (
        SELECT organization_id
        FROM analysis
        WHERE analysis_id = p_analysis_id
    )
      AND category = 'FIXED'
      AND effective_from <= CURRENT_DATE
      AND (
          effective_to IS NULL
          OR effective_to >= CURRENT_DATE
      );

    IF p_selling_price <= 0
        OR p_variable_cost < 0
        OR p_variable_cost >= p_selling_price THEN
        RAISE EXCEPTION
            'Invalid selling price or variable cost.';
    END IF;

    v_contribution :=
        p_selling_price - p_variable_cost;

    v_margin_ratio :=
        v_contribution / p_selling_price;

    v_bep :=
        v_fixed_costs / v_contribution;

    v_revenue :=
        v_expected_units * p_selling_price;

    v_profit :=
        v_expected_units * v_contribution
        - v_fixed_costs;

    v_margin_safety :=
        v_expected_units - v_bep;

    INSERT INTO analysis_result (
        analysis_id,
        fixed_costs,
        variable_cost_per_unit,
        selling_price,
        contribution_per_unit,
        contribution_margin_ratio,
        break_even_units,
        practical_break_even_units,
        break_even_revenue,
        actual_revenue,
        actual_profit,
        margin_of_safety_units,
        margin_of_safety_ratio,
        target_profit_units
    )
    VALUES (
        p_analysis_id,
        v_fixed_costs,
        p_variable_cost,
        p_selling_price,
        v_contribution,
        v_margin_ratio,
        v_bep,
        CEIL(v_bep)::BIGINT,
        v_fixed_costs / v_margin_ratio,
        v_revenue,
        v_profit,
        v_margin_safety,
        CASE
            WHEN v_expected_units > 0
            THEN v_margin_safety / v_expected_units
            ELSE NULL
        END,
        calculate_target_profit_units(
            v_fixed_costs,
            v_target_profit,
            p_selling_price,
            p_variable_cost
        )
    )
    ON CONFLICT (analysis_id)
    DO UPDATE SET
        fixed_costs = EXCLUDED.fixed_costs,
        variable_cost_per_unit = EXCLUDED.variable_cost_per_unit,
        selling_price = EXCLUDED.selling_price,
        contribution_per_unit = EXCLUDED.contribution_per_unit,
        contribution_margin_ratio =
            EXCLUDED.contribution_margin_ratio,
        break_even_units = EXCLUDED.break_even_units,
        practical_break_even_units =
            EXCLUDED.practical_break_even_units,
        break_even_revenue = EXCLUDED.break_even_revenue,
        actual_revenue = EXCLUDED.actual_revenue,
        actual_profit = EXCLUDED.actual_profit,
        margin_of_safety_units =
            EXCLUDED.margin_of_safety_units,
        margin_of_safety_ratio =
            EXCLUDED.margin_of_safety_ratio,
        target_profit_units = EXCLUDED.target_profit_units,
        calculated_at = CURRENT_TIMESTAMP;

    UPDATE analysis
    SET status = 'EVALUATED'
    WHERE analysis_id = p_analysis_id;

END;
$$;

-- ============================================================================
-- 24. SAMPLE ORGANIZATION
-- ============================================================================

INSERT INTO organization (
    organization_name,
    currency_code
)
VALUES (
    'Apex Manufacturing Pvt Ltd',
    'INR'
);

INSERT INTO cost_center (
    organization_id,
    center_name
)
VALUES
    (1, 'Manufacturing'),
    (1, 'Administration'),
    (1, 'Operations');

-- ============================================================================
-- 25. SAMPLE PRODUCTS
-- ============================================================================

INSERT INTO product (
    organization_id,
    product_code,
    product_name,
    selling_price,
    variable_cost_per_unit
)
VALUES
    (1, 'STD-001', 'Standard Product', 1000, 400),
    (1, 'PRE-001', 'Premium Product', 1500, 650),
    (1, 'ECO-001', 'Economy Product', 800, 500);

-- ============================================================================
-- 26. SAMPLE FIXED AND VARIABLE COSTS
-- ============================================================================

INSERT INTO cost_item (
    organization_id,
    cost_center_id,
    cost_name,
    category,
    amount,
    effective_from
)
VALUES
    (1, 1, 'Factory Rent', 'FIXED', 80000, CURRENT_DATE),
    (1, 2, 'Administrative Salaries', 'FIXED', 120000, CURRENT_DATE),
    (1, 3, 'Insurance', 'FIXED', 20000, CURRENT_DATE),
    (1, 1, 'Raw Materials', 'VARIABLE', 250, CURRENT_DATE),
    (1, 1, 'Packaging', 'VARIABLE', 50, CURRENT_DATE),
    (1, 1, 'Direct Labour', 'VARIABLE', 100, CURRENT_DATE);

-- ============================================================================
-- 27. SAMPLE SALES MIX
-- ============================================================================

INSERT INTO sales_mix (
    organization_id,
    product_id,
    mix_percentage,
    effective_from
)
VALUES
    (1, 1, 60, CURRENT_DATE),
    (1, 2, 40, CURRENT_DATE);

-- ============================================================================
-- 28. SAMPLE FINANCIAL ANALYSES
-- ============================================================================

INSERT INTO analysis (
    organization_id,
    analysis_name,
    expected_units,
    target_profit
)
VALUES
    (1, 'Base Production Plan', 600, 200000),
    (1, 'Low Demand Scenario', 200, 100000),
    (1, 'High Demand Scenario', 1000, 300000),
    (1, 'Zero Sales Scenario', 0, 0);

-- ============================================================================
-- 29. SAMPLE POLICIES
-- ============================================================================

INSERT INTO profitability_policy (
    organization_id,
    policy_name,
    minimum_margin_of_safety,
    minimum_contribution_ratio,
    reject_operating_loss
)
VALUES (
    1,
    'Standard Profitability Policy',
    0.15,
    0.40,
    TRUE
);

-- ============================================================================
-- 30. PROCESS FINANCIAL ANALYSES
-- ============================================================================

CALL process_break_even_analysis(1, 1000, 400);
CALL process_break_even_analysis(2, 1000, 400);
CALL process_break_even_analysis(3, 1000, 400);
CALL process_break_even_analysis(4, 1000, 400);

-- ============================================================================
-- 31. POLICY EVALUATIONS
-- ============================================================================

SELECT evaluate_profitability_policy(1, 1);
SELECT evaluate_profitability_policy(2, 1);
SELECT evaluate_profitability_policy(3, 1);
SELECT evaluate_profitability_policy(4, 1);

-- ============================================================================
-- 32. SCENARIO RECORDS
-- ============================================================================

INSERT INTO financial_scenario (
    analysis_id,
    scenario_name,
    price_change_percentage,
    variable_cost_change_percentage
)
VALUES
    (1, 'Price Reduction', -10, 0),
    (1, 'Price Increase', 10, 0),
    (1, 'Variable Cost Reduction', 0, -10),
    (1, 'Variable Cost Increase', 0, 10);

-- ============================================================================
-- 33. BREAK-EVEN RETRIEVAL
-- ============================================================================

SELECT
    analysis_id,
    fixed_costs,
    selling_price,
    variable_cost_per_unit,
    contribution_per_unit,
    contribution_margin_ratio,
    break_even_units,
    practical_break_even_units,
    break_even_revenue
FROM analysis_result
ORDER BY analysis_id;

-- ============================================================================
-- 34. COST CLASSIFICATION REPORT
-- ============================================================================

SELECT
    organization_id,
    total_fixed_costs,
    total_variable_costs,
    cost_item_count
FROM organization_cost_summary;

-- ============================================================================
-- 35. PRODUCT CONTRIBUTION REPORT
-- ============================================================================

SELECT
    product_name,
    selling_price,
    variable_cost_per_unit,
    contribution_per_unit,
    contribution_margin_ratio
FROM product_contribution_report
ORDER BY contribution_per_unit DESC;

-- ============================================================================
-- 36. PROFIT AND MARGIN REPORT
-- ============================================================================

SELECT
    a.analysis_name,
    a.expected_units,
    r.actual_revenue,
    r.actual_profit,
    r.break_even_units,
    r.margin_of_safety_units,
    r.margin_of_safety_ratio,
    CASE
        WHEN r.actual_profit > 0 THEN 'PROFIT'
        WHEN r.actual_profit = 0 THEN 'BREAK-EVEN'
        ELSE 'LOSS'
    END AS financial_position
FROM analysis a
JOIN analysis_result r
    ON r.analysis_id = a.analysis_id
ORDER BY a.analysis_id;

-- ============================================================================
-- 37. TARGET-PROFIT REPORT
-- ============================================================================

SELECT
    a.analysis_name,
    a.target_profit,
    r.target_profit_units,
    r.practical_break_even_units,
    r.target_profit_units -
        r.practical_break_even_units
        AS additional_units_required
FROM analysis a
JOIN analysis_result r
    ON r.analysis_id = a.analysis_id;

-- ============================================================================
-- 38. MULTI-PRODUCT WEIGHTED CONTRIBUTION
-- ============================================================================

SELECT
    p.product_name,
    sm.mix_percentage,
    p.selling_price - p.variable_cost_per_unit
        AS contribution_per_unit,
    (
        sm.mix_percentage / 100.0
    ) * (
        p.selling_price - p.variable_cost_per_unit
    ) AS weighted_contribution
FROM sales_mix sm
JOIN product p
    ON p.product_id = sm.product_id
WHERE sm.organization_id = 1
  AND sm.effective_from <= CURRENT_DATE
  AND (
      sm.effective_to IS NULL
      OR sm.effective_to >= CURRENT_DATE
  );

SELECT calculate_weighted_break_even(
    1,
    220000
) AS weighted_break_even_units;

-- ============================================================================
-- 39. SCENARIO EVALUATION QUERY
-- ============================================================================

WITH base AS (
    SELECT
        r.analysis_id,
        r.fixed_costs,
        r.selling_price,
        r.variable_cost_per_unit
    FROM analysis_result r
    WHERE r.analysis_id = 1
),
adjusted AS (
    SELECT
        s.scenario_name,

        b.fixed_costs *
            (1 + s.fixed_cost_change_percentage / 100.0)
            AS adjusted_fixed,

        b.selling_price *
            (1 + s.price_change_percentage / 100.0)
            AS adjusted_price,

        b.variable_cost_per_unit *
            (1 + s.variable_cost_change_percentage / 100.0)
            AS adjusted_variable

    FROM financial_scenario s
    JOIN base b
        ON b.analysis_id = s.analysis_id
),
evaluated AS (
    SELECT
        scenario_name,
        adjusted_fixed,
        adjusted_price,
        adjusted_variable,
        adjusted_price - adjusted_variable
            AS adjusted_contribution
    FROM adjusted
)
SELECT
    scenario_name,
    adjusted_fixed,
    adjusted_price,
    adjusted_variable,
    adjusted_contribution,

    CASE
        WHEN adjusted_contribution > 0
        THEN adjusted_fixed / adjusted_contribution
        ELSE NULL
    END AS scenario_break_even_units,

    CASE
        WHEN adjusted_contribution > 0
        THEN adjusted_fixed /
            (
                adjusted_contribution /
                adjusted_price
            )
        ELSE NULL
    END AS scenario_break_even_revenue,

    CASE
        WHEN adjusted_contribution <= 0
        THEN 'INVALID'
        ELSE 'VALID'
    END AS scenario_status

FROM evaluated;

-- ============================================================================
-- 40. POLICY REPORT
-- ============================================================================

SELECT
    a.analysis_name,
    pp.policy_name,
    pe.status,
    pe.violations,
    pe.evaluated_at
FROM policy_evaluation pe
JOIN analysis a
    ON a.analysis_id = pe.analysis_id
JOIN profitability_policy pp
    ON pp.policy_id = pe.policy_id
ORDER BY pe.evaluated_at DESC;

-- ============================================================================
-- 41. VALIDATION QUERIES
-- ============================================================================

-- Products with contribution margins below 40%.
SELECT
    product_name,
    selling_price,
    variable_cost_per_unit,
    contribution_margin_ratio
FROM product_contribution_report
WHERE contribution_margin_ratio < 0.40;

-- Analyses operating below break-even.
SELECT
    a.analysis_name,
    r.actual_profit,
    r.margin_of_safety_units
FROM analysis a
JOIN analysis_result r
    ON r.analysis_id = a.analysis_id
WHERE r.actual_profit < 0;

-- Cost audit history.
SELECT
    table_name,
    operation,
    record_id,
    changed_at,
    old_values,
    new_values
FROM financial_audit
ORDER BY changed_at DESC;

-- ============================================================================
-- 42. CTE: ORGANIZATION FINANCIAL PERFORMANCE
-- ============================================================================

WITH performance AS (
    SELECT
        a.organization_id,
        COUNT(*) AS analysis_count,
        SUM(r.actual_revenue) AS total_revenue,
        SUM(r.actual_profit) AS total_profit,
        AVG(r.margin_of_safety_ratio)
            FILTER (
                WHERE r.margin_of_safety_ratio IS NOT NULL
            ) AS average_margin_of_safety
    FROM analysis a
    JOIN analysis_result r
        ON r.analysis_id = a.analysis_id
    GROUP BY a.organization_id
)
SELECT
    o.organization_name,
    p.analysis_count,
    p.total_revenue,
    p.total_profit,
    p.average_margin_of_safety
FROM performance p
JOIN organization o
    ON o.organization_id = p.organization_id;

-- ============================================================================
-- 43. TRANSACTION AND ROLLBACK DEMONSTRATION
-- ============================================================================

-- This block demonstrates that an invalid financial operation
-- can be rolled back without leaving partial database changes.

DO $$
BEGIN
    BEGIN
        PERFORM calculate_break_even(
            220000,
            100,
            100
        );

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE
            'Expected financial validation failure: %',
            SQLERRM;
    END;
END;
$$;

-- ============================================================================
-- 44. FUNCTIONAL EDGE-CASE TESTS
-- ============================================================================

DO $$
DECLARE
    v_result RECORD;
    v_profit NUMERIC;
BEGIN
    SELECT *
    INTO v_result
    FROM calculate_break_even(
        220000,
        1000,
        400
    );

    IF v_result.contribution_per_unit <> 600 THEN
        RAISE EXCEPTION
            'Contribution assertion failed.';
    END IF;

    IF v_result.practical_break_even_units <> 367 THEN
        RAISE EXCEPTION
            'Break-even assertion failed.';
    END IF;

    v_profit := calculate_operating_profit(
        600,
        220000,
        1000,
        400
    );

    IF v_profit <> 140000 THEN
        RAISE EXCEPTION
            'Operating profit assertion failed.';
    END IF;

    IF calculate_target_profit_units(
        220000,
        200000,
        1000,
        400
    ) <> 700 THEN
        RAISE EXCEPTION
            'Target-profit assertion failed.';
    END IF;

    RAISE NOTICE
        'All break-even database assertions passed.';
END;
$$;

COMMIT;

/*
Production considerations:
1. Restrict table permissions through database roles.
2. Use organization-scoped authorization in application services.
3. Store immutable financial snapshots for historical reproducibility.
4. Use controlled effective-date changes for cost and pricing records.
5. Avoid treating historical analyses as recalculated live reports.
6. Run large reporting workloads against suitable indexes or summaries.
7. Use serializable transactions where strict concurrent financial
   consistency is required.
*/
