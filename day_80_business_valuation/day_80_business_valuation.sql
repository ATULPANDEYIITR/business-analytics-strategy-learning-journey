/*
 BUSINESS VALUATION DATABASE
 PostgreSQL 14+

 Implements:
 - Financial statement storage
 - Capital structure
 - Forecast assumptions
 - Discounted Cash Flow valuation
 - WACC
 - Free Cash Flow to Firm
 - Terminal value
 - Comparable company analysis
 - EV/Revenue
 - EV/EBITDA
 - P/E
 - Sensitivity analysis
 - Scenario management
 - Valuation policies
 - Valuation audit trail
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS valuation;

SET search_path TO valuation, public;

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE valuation.scenario_type AS ENUM (
    'BEAR',
    'BASE',
    'BULL'
);

CREATE TYPE valuation.valuation_method AS ENUM (
    'DCF',
    'EV_REVENUE',
    'EV_EBITDA',
    'PE'
);

CREATE TYPE valuation.valuation_status AS ENUM (
    'DRAFT',
    'CALCULATED',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED'
);

-- ============================================================
-- COMPANY MASTER
-- ============================================================

CREATE TABLE IF NOT EXISTS companies (
    company_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_name VARCHAR(200) NOT NULL,
    industry VARCHAR(120) NOT NULL,
    country_code CHAR(2) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    fiscal_year_end DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_company_name_country
        UNIQUE (company_name, country_code)
);

-- ============================================================
-- FINANCIAL STATEMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS financial_statements (
    statement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    fiscal_year INTEGER NOT NULL,

    revenue NUMERIC(20, 4) NOT NULL,
    ebit NUMERIC(20, 4) NOT NULL,
    depreciation NUMERIC(20, 4) NOT NULL,
    capital_expenditure NUMERIC(20, 4) NOT NULL,
    working_capital_increase NUMERIC(20, 4) NOT NULL DEFAULT 0,

    cash NUMERIC(20, 4) NOT NULL DEFAULT 0,
    debt NUMERIC(20, 4) NOT NULL DEFAULT 0,
    net_income NUMERIC(20, 4),

    tax_rate NUMERIC(10, 6) NOT NULL,
    shares_outstanding NUMERIC(20, 4) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_company_financial_year
        UNIQUE (company_id, fiscal_year),

    CONSTRAINT ck_revenue
        CHECK (revenue > 0),

    CONSTRAINT ck_depreciation
        CHECK (depreciation >= 0),

    CONSTRAINT ck_capex
        CHECK (capital_expenditure >= 0),

    CONSTRAINT ck_cash
        CHECK (cash >= 0),

    CONSTRAINT ck_debt
        CHECK (debt >= 0),

    CONSTRAINT ck_tax_rate
        CHECK (tax_rate >= 0 AND tax_rate < 1),

    CONSTRAINT ck_shares
        CHECK (shares_outstanding > 0)
);

CREATE INDEX IF NOT EXISTS idx_financial_company_year
    ON financial_statements(company_id, fiscal_year DESC);

-- ============================================================
-- CAPITAL STRUCTURE
-- ============================================================

CREATE TABLE IF NOT EXISTS capital_structures (
    capital_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    effective_date DATE NOT NULL,

    cost_of_equity NUMERIC(10, 6) NOT NULL,
    cost_of_debt NUMERIC(10, 6) NOT NULL,

    equity_weight NUMERIC(10, 6) NOT NULL,
    debt_weight NUMERIC(10, 6) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_company_capital_date
        UNIQUE (company_id, effective_date),

    CONSTRAINT ck_cost_of_equity
        CHECK (cost_of_equity >= 0 AND cost_of_equity < 1),

    CONSTRAINT ck_cost_of_debt
        CHECK (cost_of_debt >= 0 AND cost_of_debt < 1),

    CONSTRAINT ck_equity_weight
        CHECK (equity_weight >= 0 AND equity_weight <= 1),

    CONSTRAINT ck_debt_weight
        CHECK (debt_weight >= 0 AND debt_weight <= 1),

    CONSTRAINT ck_capital_weights
        CHECK (ABS(equity_weight + debt_weight - 1) < 0.000001)
);

CREATE INDEX IF NOT EXISTS idx_capital_company_date
    ON capital_structures(company_id, effective_date DESC);

-- ============================================================
-- VALUATION ASSUMPTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS valuation_assumptions (
    assumption_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),

    scenario valuation.scenario_type NOT NULL,

    tax_rate NUMERIC(10, 6) NOT NULL,
    depreciation_rate NUMERIC(10, 6) NOT NULL,
    capex_rate NUMERIC(10, 6) NOT NULL,
    working_capital_rate NUMERIC(10, 6) NOT NULL,
    terminal_growth NUMERIC(10, 6) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_company_scenario
        UNIQUE(company_id, scenario),

    CONSTRAINT ck_assumption_tax
        CHECK (tax_rate >= 0 AND tax_rate < 1),

    CONSTRAINT ck_assumption_depreciation
        CHECK (depreciation_rate >= 0 AND depreciation_rate < 1),

    CONSTRAINT ck_assumption_capex
        CHECK (capex_rate >= 0 AND capex_rate < 1),

    CONSTRAINT ck_assumption_working_capital
        CHECK (working_capital_rate >= 0 AND working_capital_rate < 1),

    CONSTRAINT ck_assumption_growth
        CHECK (terminal_growth >= 0 AND terminal_growth < 1)
);

-- ============================================================
-- FORECAST PERIODS
-- ============================================================

CREATE TABLE IF NOT EXISTS forecast_periods (
    forecast_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    assumption_id BIGINT NOT NULL
        REFERENCES valuation_assumptions(assumption_id)
        ON DELETE CASCADE,

    year_number INTEGER NOT NULL,

    revenue_growth NUMERIC(10, 6) NOT NULL,
    ebit_margin NUMERIC(10, 6) NOT NULL,

    CONSTRAINT uq_forecast_period
        UNIQUE (assumption_id, year_number),

    CONSTRAINT ck_forecast_year
        CHECK (year_number BETWEEN 1 AND 100),

    CONSTRAINT ck_revenue_growth
        CHECK (revenue_growth > -1),

    CONSTRAINT ck_ebit_margin
        CHECK (ebit_margin >= 0 AND ebit_margin < 1)
);

CREATE INDEX IF NOT EXISTS idx_forecast_assumption_year
    ON forecast_periods(assumption_id, year_number);

-- ============================================================
-- VALUATION EXECUTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS valuations (
    valuation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_id BIGINT NOT NULL REFERENCES companies(company_id),

    statement_id BIGINT NOT NULL
        REFERENCES financial_statements(statement_id),

    capital_id BIGINT NOT NULL
        REFERENCES capital_structures(capital_id),

    assumption_id BIGINT NOT NULL
        REFERENCES valuation_assumptions(assumption_id),

    scenario valuation.scenario_type NOT NULL,

    status valuation.valuation_status NOT NULL DEFAULT 'DRAFT',

    wacc NUMERIC(12, 8),
    explicit_period_value NUMERIC(24, 6),
    terminal_value NUMERIC(24, 6),
    terminal_present_value NUMERIC(24, 6),

    enterprise_value NUMERIC(24, 6),
    equity_value NUMERIC(24, 6),
    intrinsic_value_per_share NUMERIC(24, 8),

    terminal_contribution NUMERIC(12, 8),

    calculated_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_valuation_wacc
        CHECK (wacc IS NULL OR wacc > 0),

    CONSTRAINT ck_valuation_terminal_contribution
        CHECK (
            terminal_contribution IS NULL
            OR terminal_contribution >= 0
        ),

    CONSTRAINT ck_valuation_outputs
        CHECK (
            status = 'DRAFT'
            OR (
                wacc IS NOT NULL
                AND explicit_period_value IS NOT NULL
                AND terminal_value IS NOT NULL
                AND terminal_present_value IS NOT NULL
                AND enterprise_value IS NOT NULL
                AND equity_value IS NOT NULL
                AND intrinsic_value_per_share IS NOT NULL
                AND calculated_at IS NOT NULL
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_valuation_company_scenario
    ON valuations(company_id, scenario, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_valuation_status
    ON valuations(status, created_at DESC);

-- ============================================================
-- PROJECTED CASH FLOWS
-- ============================================================

CREATE TABLE IF NOT EXISTS projected_cash_flows (
    cash_flow_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    valuation_id BIGINT NOT NULL
        REFERENCES valuations(valuation_id)
        ON DELETE CASCADE,

    year_number INTEGER NOT NULL,

    revenue NUMERIC(24, 6) NOT NULL,
    ebit NUMERIC(24, 6) NOT NULL,
    nopat NUMERIC(24, 6) NOT NULL,

    depreciation NUMERIC(24, 6) NOT NULL,
    capex NUMERIC(24, 6) NOT NULL,
    working_capital_change NUMERIC(24, 6) NOT NULL,

    fcff NUMERIC(24, 6) NOT NULL,
    discount_factor NUMERIC(18, 12) NOT NULL,
    present_value NUMERIC(24, 6) NOT NULL,

    CONSTRAINT uq_valuation_year
        UNIQUE (valuation_id, year_number),

    CONSTRAINT ck_cash_flow_year
        CHECK (year_number > 0),

    CONSTRAINT ck_projected_revenue
        CHECK (revenue > 0),

    CONSTRAINT ck_discount_factor
        CHECK (discount_factor > 0)
);

-- ============================================================
-- COMPARABLE COMPANIES
-- ============================================================

CREATE TABLE IF NOT EXISTS comparable_companies (
    comparable_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    target_company_id BIGINT NOT NULL REFERENCES companies(company_id),
    peer_company_id BIGINT NOT NULL REFERENCES companies(company_id),

    enterprise_value NUMERIC(24, 6) NOT NULL,
    revenue NUMERIC(24, 6) NOT NULL,
    ebitda NUMERIC(24, 6) NOT NULL,
    net_income NUMERIC(24, 6) NOT NULL,

    observation_date DATE NOT NULL,

    CONSTRAINT uq_target_peer_date
        UNIQUE(target_company_id, peer_company_id, observation_date),

    CONSTRAINT ck_comparable_not_self
        CHECK (target_company_id <> peer_company_id),

    CONSTRAINT ck_comparable_ev
        CHECK (enterprise_value > 0),

    CONSTRAINT ck_comparable_revenue
        CHECK (revenue > 0),

    CONSTRAINT ck_comparable_ebitda
        CHECK (ebitda > 0),

    CONSTRAINT ck_comparable_income
        CHECK (net_income > 0)
);

CREATE INDEX IF NOT EXISTS idx_comparable_target_date
    ON comparable_companies(target_company_id, observation_date DESC);

-- ============================================================
-- VALUATION MULTIPLES
-- ============================================================

CREATE TABLE IF NOT EXISTS comparable_multiples (
    multiple_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    comparable_id BIGINT NOT NULL
        REFERENCES comparable_companies(comparable_id)
        ON DELETE CASCADE,

    ev_revenue NUMERIC(18, 8) NOT NULL,
    ev_ebitda NUMERIC(18, 8) NOT NULL,
    pe_ratio NUMERIC(18, 8) NOT NULL,

    CONSTRAINT uq_comparable_multiple
        UNIQUE(comparable_id),

    CONSTRAINT ck_ev_revenue
        CHECK (ev_revenue > 0),

    CONSTRAINT ck_ev_ebitda
        CHECK (ev_ebitda > 0),

    CONSTRAINT ck_pe_ratio
        CHECK (pe_ratio > 0)
);

-- ============================================================
-- VALUATION POLICY
-- ============================================================

CREATE TABLE IF NOT EXISTS valuation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_id BIGINT NOT NULL REFERENCES companies(company_id),

    maximum_terminal_contribution NUMERIC(10, 6) NOT NULL,
    minimum_wacc NUMERIC(10, 6) NOT NULL,
    maximum_wacc NUMERIC(10, 6) NOT NULL,

    require_positive_equity_value BOOLEAN NOT NULL DEFAULT TRUE,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_policy_terminal
        CHECK (
            maximum_terminal_contribution > 0
            AND maximum_terminal_contribution <= 1
        ),

    CONSTRAINT ck_policy_wacc
        CHECK (
            minimum_wacc > 0
            AND maximum_wacc > minimum_wacc
        )
);

-- ============================================================
-- SENSITIVITY RESULTS
-- ============================================================

CREATE TABLE IF NOT EXISTS valuation_sensitivity (
    sensitivity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    valuation_id BIGINT NOT NULL
        REFERENCES valuations(valuation_id)
        ON DELETE CASCADE,

    adjusted_wacc NUMERIC(12, 8) NOT NULL,
    adjusted_terminal_growth NUMERIC(12, 8) NOT NULL,
    enterprise_value NUMERIC(24, 6) NOT NULL,

    CONSTRAINT uq_sensitivity_case
        UNIQUE (
            valuation_id,
            adjusted_wacc,
            adjusted_terminal_growth
        ),

    CONSTRAINT ck_sensitivity_wacc
        CHECK (adjusted_wacc > 0),

    CONSTRAINT ck_sensitivity_growth
        CHECK (
            adjusted_terminal_growth >= 0
            AND adjusted_terminal_growth < adjusted_wacc
        )
);

-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS valuation_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    valuation_id BIGINT NOT NULL
        REFERENCES valuations(valuation_id),

    previous_status valuation.valuation_status,
    new_status valuation.valuation_status NOT NULL,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT NOT NULL DEFAULT CURRENT_USER
);

-- ============================================================
-- WACC FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_wacc(
    p_cost_of_equity NUMERIC,
    p_cost_of_debt NUMERIC,
    p_equity_weight NUMERIC,
    p_debt_weight NUMERIC,
    p_tax_rate NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_cost_of_equity < 0 OR p_cost_of_debt < 0 THEN
        RAISE EXCEPTION 'Capital costs cannot be negative';
    END IF;

    IF p_tax_rate < 0 OR p_tax_rate >= 1 THEN
        RAISE EXCEPTION 'Invalid tax rate';
    END IF;

    IF ABS(p_equity_weight + p_debt_weight - 1) > 0.000001 THEN
        RAISE EXCEPTION 'Capital weights must sum to 1';
    END IF;

    IF p_equity_weight < 0 OR p_debt_weight < 0 THEN
        RAISE EXCEPTION 'Capital weights cannot be negative';
    END IF;

    RETURN
        p_cost_of_equity * p_equity_weight
        + p_cost_of_debt * p_debt_weight * (1 - p_tax_rate);
END;
$$;

-- ============================================================
-- FCFF FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_fcff(
    p_ebit NUMERIC,
    p_tax_rate NUMERIC,
    p_depreciation NUMERIC,
    p_capex NUMERIC,
    p_working_capital_change NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_tax_rate < 0 OR p_tax_rate >= 1 THEN
        RAISE EXCEPTION 'Invalid tax rate';
    END IF;

    IF p_depreciation < 0 OR p_capex < 0 THEN
        RAISE EXCEPTION 'Depreciation and capex cannot be negative';
    END IF;

    IF p_ebit < 0 THEN
        RAISE EXCEPTION 'Negative EBIT is unsupported by this model';
    END IF;

    RETURN
        p_ebit * (1 - p_tax_rate)
        + p_depreciation
        - p_capex
        - p_working_capital_change;
END;
$$;

-- ============================================================
-- DCF EXECUTION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE run_dcf(
    p_valuation_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_valuation valuations%ROWTYPE;
    v_statement financial_statements%ROWTYPE;
    v_capital capital_structures%ROWTYPE;
    v_assumption valuation_assumptions%ROWTYPE;

    v_wacc NUMERIC;
    v_revenue NUMERIC;
    v_previous_wc NUMERIC;

    v_ebit NUMERIC;
    v_nopat NUMERIC;
    v_depreciation NUMERIC;
    v_capex NUMERIC;
    v_current_wc NUMERIC;
    v_wc_change NUMERIC;
    v_fcff NUMERIC;
    v_discount_factor NUMERIC;

    v_explicit_value NUMERIC := 0;
    v_final_fcff NUMERIC;
    v_terminal_value NUMERIC;
    v_terminal_pv NUMERIC;
    v_enterprise_value NUMERIC;
    v_equity_value NUMERIC;
    v_share_value NUMERIC;

    v_period RECORD;
    v_period_count INTEGER := 0;
BEGIN
    SELECT *
    INTO STRICT v_valuation
    FROM valuations
    WHERE valuation_id = p_valuation_id
    FOR UPDATE;

    IF v_valuation.status <> 'DRAFT' THEN
        RAISE EXCEPTION
            'Only DRAFT valuations can be recalculated';
    END IF;

    SELECT *
    INTO STRICT v_statement
    FROM financial_statements
    WHERE statement_id = v_valuation.statement_id;

    SELECT *
    INTO STRICT v_capital
    FROM capital_structures
    WHERE capital_id = v_valuation.capital_id;

    SELECT *
    INTO STRICT v_assumption
    FROM valuation_assumptions
    WHERE assumption_id = v_valuation.assumption_id;

    IF v_statement.company_id <> v_valuation.company_id
       OR v_capital.company_id <> v_valuation.company_id
       OR v_assumption.company_id <> v_valuation.company_id
       OR v_assumption.scenario <> v_valuation.scenario THEN
        RAISE EXCEPTION
            'Valuation inputs do not belong to the same company and scenario';
    END IF;

    IF v_statement.ebit < 0 THEN
        RAISE EXCEPTION 'Negative EBIT is unsupported';
    END IF;

    v_wacc := calculate_wacc(
        v_capital.cost_of_equity,
        v_capital.cost_of_debt,
        v_capital.equity_weight,
        v_capital.debt_weight,
        v_statement.tax_rate
    );

    IF v_wacc <= 0 OR v_wacc <= v_assumption.terminal_growth THEN
        RAISE EXCEPTION
            'WACC must be positive and greater than terminal growth';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM forecast_periods
        WHERE assumption_id = v_assumption.assumption_id
    ) THEN
        RAISE EXCEPTION 'Forecast periods are missing';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM forecast_periods
        WHERE assumption_id = v_assumption.assumption_id
    ) <> (
        SELECT MAX(year_number)
        FROM forecast_periods
        WHERE assumption_id = v_assumption.assumption_id
    ) THEN
        RAISE EXCEPTION
            'Forecast periods must be continuous and start at year 1';
    END IF;

    DELETE FROM projected_cash_flows
    WHERE valuation_id = p_valuation_id;

    v_revenue := v_statement.revenue;

    v_previous_wc :=
        v_revenue * v_assumption.working_capital_rate;

    FOR v_period IN
        SELECT *
        FROM forecast_periods
        WHERE assumption_id = v_assumption.assumption_id
        ORDER BY year_number
    LOOP
        v_period_count := v_period_count + 1;

        v_revenue :=
            v_revenue * (1 + v_period.revenue_growth);

        v_ebit := v_revenue * v_period.ebit_margin;

        v_nopat :=
            v_ebit * (1 - v_assumption.tax_rate);

        v_depreciation :=
            v_revenue * v_assumption.depreciation_rate;

        v_capex :=
            v_revenue * v_assumption.capex_rate;

        v_current_wc :=
            v_revenue * v_assumption.working_capital_rate;

        v_wc_change := v_current_wc - v_previous_wc;

        v_fcff := calculate_fcff(
            v_ebit,
            v_assumption.tax_rate,
            v_depreciation,
            v_capex,
            v_wc_change
        );

        v_discount_factor :=
            1 / POWER(1 + v_wacc, v_period.year_number);

        INSERT INTO projected_cash_flows (
            valuation_id,
            year_number,
            revenue,
            ebit,
            nopat,
            depreciation,
            capex,
            working_capital_change,
            fcff,
            discount_factor,
            present_value
        )
        VALUES (
            p_valuation_id,
            v_period.year_number,
            v_revenue,
            v_ebit,
            v_nopat,
            v_depreciation,
            v_capex,
            v_wc_change,
            v_fcff,
            v_discount_factor,
            v_fcff * v_discount_factor
        );

        v_explicit_value :=
            v_explicit_value + v_fcff * v_discount_factor;

        v_final_fcff := v_fcff;
        v_previous_wc := v_current_wc;
    END LOOP;

    v_terminal_value :=
        v_final_fcff * (1 + v_assumption.terminal_growth)
        / (v_wacc - v_assumption.terminal_growth);

    v_terminal_pv :=
        v_terminal_value / POWER(1 + v_wacc, v_period_count);

    v_enterprise_value :=
        v_explicit_value + v_terminal_pv;

    v_equity_value :=
        v_enterprise_value
        + v_statement.cash
        - v_statement.debt;

    v_share_value :=
        v_equity_value / v_statement.shares_outstanding;

    UPDATE valuations
    SET
        wacc = v_wacc,
        explicit_period_value = v_explicit_value,
        terminal_value = v_terminal_value,
        terminal_present_value = v_terminal_pv,
        enterprise_value = v_enterprise_value,
        equity_value = v_equity_value,
        intrinsic_value_per_share = v_share_value,
        terminal_contribution =
            v_terminal_pv / NULLIF(v_enterprise_value, 0),
        status = 'CALCULATED',
        calculated_at = CURRENT_TIMESTAMP
    WHERE valuation_id = p_valuation_id;
END;
$$;

-- ============================================================
-- COMPARABLE MULTIPLE CALCULATION TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION populate_comparable_multiples()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO comparable_multiples (
        comparable_id,
        ev_revenue,
        ev_ebitda,
        pe_ratio
    )
    VALUES (
        NEW.comparable_id,
        NEW.enterprise_value / NEW.revenue,
        NEW.enterprise_value / NEW.ebitda,
        NEW.enterprise_value / NEW.net_income
    )
    ON CONFLICT (comparable_id)
    DO UPDATE SET
        ev_revenue = EXCLUDED.ev_revenue,
        ev_ebitda = EXCLUDED.ev_ebitda,
        pe_ratio = EXCLUDED.pe_ratio;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_comparable_multiples
AFTER INSERT OR UPDATE OF enterprise_value, revenue, ebitda, net_income
ON comparable_companies
FOR EACH ROW
EXECUTE FUNCTION populate_comparable_multiples();

-- ============================================================
-- VALUATION STATUS AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION audit_valuation_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO valuation_audit (
            valuation_id,
            previous_status,
            new_status
        )
        VALUES (
            NEW.valuation_id,
            NULL,
            NEW.status
        );

    ELSIF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO valuation_audit (
            valuation_id,
            previous_status,
            new_status
        )
        VALUES (
            NEW.valuation_id,
            OLD.status,
            NEW.status
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_valuation_status_audit
AFTER INSERT OR UPDATE OF status
ON valuations
FOR EACH ROW
EXECUTE FUNCTION audit_valuation_status();

-- ============================================================
-- POLICY EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_valuation_policy(
    p_valuation_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    policy_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_valuation valuations%ROWTYPE;
    v_policy valuation_policies%ROWTYPE;
    v_issues TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT *
    INTO STRICT v_valuation
    FROM valuations
    WHERE valuation_id = p_valuation_id;

    SELECT *
    INTO v_policy
    FROM valuation_policies
    WHERE company_id = v_valuation.company_id
      AND active = TRUE
    ORDER BY created_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'No active valuation policy exists';
        RETURN;
    END IF;

    IF v_valuation.status <> 'CALCULATED' THEN
        v_issues := array_append(
            v_issues,
            'Valuation is not in CALCULATED status'
        );
    END IF;

    IF v_valuation.wacc < v_policy.minimum_wacc THEN
        v_issues := array_append(v_issues, 'WACC below policy');
    END IF;

    IF v_valuation.wacc > v_policy.maximum_wacc THEN
        v_issues := array_append(v_issues, 'WACC above policy');
    END IF;

    IF v_valuation.terminal_contribution >
       v_policy.maximum_terminal_contribution THEN
        v_issues := array_append(
            v_issues,
            'Terminal contribution exceeds policy'
        );
    END IF;

    IF v_policy.require_positive_equity_value
       AND v_valuation.equity_value <= 0 THEN
        v_issues := array_append(
            v_issues,
            'Equity value must be positive'
        );
    END IF;

    RETURN QUERY
    SELECT
        cardinality(v_issues) = 0,
        CASE
            WHEN cardinality(v_issues) = 0
                THEN 'POLICY PASSED'
            ELSE array_to_string(v_issues, '; ')
        END;
END;
$$;

-- ============================================================
-- COMPARABLE MULTIPLE REPORT
-- ============================================================

CREATE OR REPLACE VIEW comparable_valuation_report AS
SELECT
    cc.target_company_id,
    target.company_name AS target_company,
    peer.company_name AS peer_company,
    cc.observation_date,
    cc.enterprise_value,
    cc.revenue,
    cc.ebitda,
    cc.net_income,
    cm.ev_revenue,
    cm.ev_ebitda,
    cm.pe_ratio
FROM comparable_companies cc
JOIN companies target
    ON target.company_id = cc.target_company_id
JOIN companies peer
    ON peer.company_id = cc.peer_company_id
JOIN comparable_multiples cm
    ON cm.comparable_id = cc.comparable_id;

-- ============================================================
-- DCF FORECAST REPORT
-- ============================================================

CREATE OR REPLACE VIEW dcf_forecast_report AS
SELECT
    v.valuation_id,
    c.company_name,
    v.scenario,
    v.wacc,
    p.year_number,
    p.revenue,
    p.ebit,
    p.nopat,
    p.depreciation,
    p.capex,
    p.working_capital_change,
    p.fcff,
    p.discount_factor,
    p.present_value
FROM valuations v
JOIN companies c
    ON c.company_id = v.company_id
JOIN projected_cash_flows p
    ON p.valuation_id = v.valuation_id;

-- ============================================================
-- VALUATION SUMMARY VIEW
-- ============================================================

CREATE OR REPLACE VIEW valuation_summary AS
SELECT
    v.valuation_id,
    c.company_name,
    v.scenario,
    v.status,
    v.wacc,
    v.explicit_period_value,
    v.terminal_value,
    v.terminal_present_value,
    v.enterprise_value,
    v.equity_value,
    v.intrinsic_value_per_share,
    v.terminal_contribution,
    v.calculated_at
FROM valuations v
JOIN companies c
    ON c.company_id = v.company_id;

COMMIT;

-- ============================================================
-- SAMPLE DATA AND EXECUTION
-- ============================================================

BEGIN;

INSERT INTO companies (
    company_name,
    industry,
    country_code,
    currency_code,
    fiscal_year_end
)
VALUES
    ('Target Technologies', 'Software', 'IN', 'INR', '2026-03-31'),
    ('Alpha Technologies', 'Software', 'IN', 'INR', '2026-03-31'),
    ('Beta Systems', 'Software', 'IN', 'INR', '2026-03-31'),
    ('Gamma Digital', 'Software', 'IN', 'INR', '2026-03-31'),
    ('Delta Software', 'Software', 'IN', 'INR', '2026-03-31')
ON CONFLICT (company_name, country_code) DO NOTHING;

-- Financial values are in INR millions.

INSERT INTO financial_statements (
    company_id,
    fiscal_year,
    revenue,
    ebit,
    depreciation,
    capital_expenditure,
    working_capital_increase,
    cash,
    debt,
    net_income,
    tax_rate,
    shares_outstanding
)
SELECT
    company_id,
    2026,
    1000,
    180,
    40,
    55,
    10,
    100,
    300,
    120,
    0.25,
    50
FROM companies
WHERE company_name = 'Target Technologies'
ON CONFLICT (company_id, fiscal_year) DO NOTHING;

INSERT INTO capital_structures (
    company_id,
    effective_date,
    cost_of_equity,
    cost_of_debt,
    equity_weight,
    debt_weight
)
SELECT
    company_id,
    '2026-04-01',
    0.14,
    0.09,
    0.70,
    0.30
FROM companies
WHERE company_name = 'Target Technologies'
ON CONFLICT (company_id, effective_date) DO NOTHING;

-- Bear, base and bull forecast assumptions.

INSERT INTO valuation_assumptions (
    company_id,
    scenario,
    tax_rate,
    depreciation_rate,
    capex_rate,
    working_capital_rate,
    terminal_growth
)
SELECT
    company_id,
    'BEAR',
    0.25,
    0.035,
    0.06,
    0.12,
    0.02
FROM companies
WHERE company_name = 'Target Technologies'
ON CONFLICT (company_id, scenario) DO NOTHING;

INSERT INTO valuation_assumptions (
    company_id,
    scenario,
    tax_rate,
    depreciation_rate,
    capex_rate,
    working_capital_rate,
    terminal_growth
)
SELECT
    company_id,
    'BASE',
    0.25,
    0.04,
    0.055,
    0.10,
    0.03
FROM companies
WHERE company_name = 'Target Technologies'
ON CONFLICT (company_id, scenario) DO NOTHING;

INSERT INTO valuation_assumptions (
    company_id,
    scenario,
    tax_rate,
    depreciation_rate,
    capex_rate,
    working_capital_rate,
    terminal_growth
)
SELECT
    company_id,
    'BULL',
    0.25,
    0.045,
    0.05,
    0.09,
    0.035
FROM companies
WHERE company_name = 'Target Technologies'
ON CONFLICT (company_id, scenario) DO NOTHING;

-- Five-year forecast inputs.

WITH scenario_data AS (
    SELECT
        a.assumption_id,
        a.scenario,
        f.year_number,
        CASE a.scenario
            WHEN 'BEAR' THEN
                ARRAY[0.04, 0.035, 0.03, 0.025, 0.02]::NUMERIC[]
            WHEN 'BASE' THEN
                ARRAY[0.10, 0.09, 0.08, 0.07, 0.06]::NUMERIC[]
            WHEN 'BULL' THEN
                ARRAY[0.16, 0.14, 0.12, 0.10, 0.08]::NUMERIC[]
        END AS growth_array,
        CASE a.scenario
            WHEN 'BEAR' THEN
                ARRAY[0.15, 0.15, 0.155, 0.16, 0.16]::NUMERIC[]
            WHEN 'BASE' THEN
                ARRAY[0.18, 0.19, 0.20, 0.205, 0.21]::NUMERIC[]
            WHEN 'BULL' THEN
                ARRAY[0.20, 0.21, 0.22, 0.23, 0.23]::NUMERIC[]
        END AS margin_array
    FROM valuation_assumptions a
    CROSS JOIN generate_series(1, 5) AS f(year_number)
    JOIN companies c
        ON c.company_id = a.company_id
    WHERE c.company_name = 'Target Technologies'
)
INSERT INTO forecast_periods (
    assumption_id,
    year_number,
    revenue_growth,
    ebit_margin
)
SELECT
    assumption_id,
    year_number,
    growth_array[year_number],
    margin_array[year_number]
FROM scenario_data
ON CONFLICT (assumption_id, year_number) DO NOTHING;

-- Create one valuation for each scenario.

INSERT INTO valuations (
    company_id,
    statement_id,
    capital_id,
    assumption_id,
    scenario
)
SELECT
    c.company_id,
    fs.statement_id,
    cs.capital_id,
    a.assumption_id,
    a.scenario
FROM companies c
JOIN financial_statements fs
    ON fs.company_id = c.company_id
JOIN capital_structures cs
    ON cs.company_id = c.company_id
JOIN valuation_assumptions a
    ON a.company_id = c.company_id
WHERE c.company_name = 'Target Technologies'
  AND fs.fiscal_year = 2026
  AND cs.effective_date = '2026-04-01'
ON CONFLICT DO NOTHING;

COMMIT;

-- Execute DCF valuations atomically.

BEGIN;

DO $$
DECLARE
    v_record RECORD;
BEGIN
    FOR v_record IN
        SELECT valuation_id
        FROM valuations
        WHERE status = 'DRAFT'
        ORDER BY valuation_id
    LOOP
        CALL run_dcf(v_record.valuation_id);
    END LOOP;
END;
$$;

COMMIT;

-- ============================================================
-- COMPARABLE COMPANY SAMPLE DATA
-- ============================================================

BEGIN;

WITH company_ids AS (
    SELECT
        MAX(company_id) FILTER (
            WHERE company_name = 'Target Technologies'
        ) AS target_id,

        MAX(company_id) FILTER (
            WHERE company_name = 'Alpha Technologies'
        ) AS alpha_id,

        MAX(company_id) FILTER (
            WHERE company_name = 'Beta Systems'
        ) AS beta_id,

        MAX(company_id) FILTER (
            WHERE company_name = 'Gamma Digital'
        ) AS gamma_id,

        MAX(company_id) FILTER (
            WHERE company_name = 'Delta Software'
        ) AS delta_id
    FROM companies
)
INSERT INTO comparable_companies (
    target_company_id,
    peer_company_id,
    enterprise_value,
    revenue,
    ebitda,
    net_income,
    observation_date
)
SELECT
    target_id,
    peer_id,
    enterprise_value,
    revenue,
    ebitda,
    net_income,
    '2026-03-31'
FROM company_ids
CROSS JOIN (
    VALUES
        (alpha_id, 1800::NUMERIC, 1200::NUMERIC, 240::NUMERIC, 140::NUMERIC),
        (beta_id, 2100::NUMERIC, 1500::NUMERIC, 300::NUMERIC, 175::NUMERIC),
        (gamma_id, 1650::NUMERIC, 1100::NUMERIC, 220::NUMERIC, 125::NUMERIC),
        (delta_id, 2400::NUMERIC, 1600::NUMERIC, 320::NUMERIC, 190::NUMERIC)
) AS peers(peer_id, enterprise_value, revenue, ebitda, net_income)
WHERE target_id IS NOT NULL
  AND peer_id IS NOT NULL
ON CONFLICT (target_company_id, peer_company_id, observation_date)
DO NOTHING;

COMMIT;

-- ============================================================
-- VALUATION POLICY SAMPLE
-- ============================================================

INSERT INTO valuation_policies (
    company_id,
    maximum_terminal_contribution,
    minimum_wacc,
    maximum_wacc,
    require_positive_equity_value
)
SELECT
    company_id,
    0.85,
    0.01,
    0.30,
    TRUE
FROM companies
WHERE company_name = 'Target Technologies';

-- ============================================================
-- RETRIEVAL AND REPORTING QUERIES
-- ============================================================

-- 1. All completed valuations.

SELECT *
FROM valuation_summary
ORDER BY scenario;

-- 2. Detailed forecast by valuation.

SELECT
    company_name,
    scenario,
    year_number,
    revenue,
    ebit,
    fcff,
    present_value
FROM dcf_forecast_report
ORDER BY scenario, year_number;

-- 3. Enterprise-to-equity reconciliation.

SELECT
    v.valuation_id,
    c.company_name,
    v.enterprise_value,
    fs.cash,
    fs.debt,
    v.enterprise_value + fs.cash - fs.debt
        AS reconciled_equity_value,
    v.equity_value,
    v.intrinsic_value_per_share
FROM valuations v
JOIN companies c
    ON c.company_id = v.company_id
JOIN financial_statements fs
    ON fs.statement_id = v.statement_id
ORDER BY v.valuation_id;

-- 4. Scenario comparison.

SELECT
    company_name,
    scenario,
    enterprise_value,
    equity_value,
    intrinsic_value_per_share,
    terminal_contribution
FROM valuation_summary
WHERE status = 'CALCULATED'
ORDER BY
    CASE scenario
        WHEN 'BEAR' THEN 1
        WHEN 'BASE' THEN 2
        WHEN 'BULL' THEN 3
    END;

-- 5. Comparable company multiples.

SELECT
    target_company,
    peer_company,
    ev_revenue,
    ev_ebitda,
    pe_ratio
FROM comparable_valuation_report
ORDER BY peer_company;

-- 6. Median comparable multiples using a CTE.

WITH peer_multiples AS (
    SELECT
        target_company_id,
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY ev_revenue)
            AS median_ev_revenue,

        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY ev_ebitda)
            AS median_ev_ebitda,

        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY pe_ratio)
            AS median_pe
    FROM comparable_valuation_report
    GROUP BY target_company_id
)
SELECT
    c.company_name,
    p.median_ev_revenue,
    p.median_ev_ebitda,
    p.median_pe
FROM peer_multiples p
JOIN companies c
    ON c.company_id = p.target_company_id;

-- 7. Policy eligibility.

SELECT
    v.valuation_id,
    c.company_name,
    v.scenario,
    p.eligible,
    p.policy_message
FROM valuations v
JOIN companies c
    ON c.company_id = v.company_id
CROSS JOIN LATERAL
    evaluate_valuation_policy(v.valuation_id) p
ORDER BY v.valuation_id;

-- 8. Revenue and FCFF aggregation.

SELECT
    v.scenario,
    SUM(p.revenue) AS cumulative_forecast_revenue,
    SUM(p.fcff) AS cumulative_fcff,
    SUM(p.present_value) AS explicit_cash_flow_value,
    AVG(p.discount_factor) AS average_discount_factor
FROM valuations v
JOIN projected_cash_flows p
    ON p.valuation_id = v.valuation_id
GROUP BY v.scenario
ORDER BY v.scenario;

-- 9. Valuation audit history.

SELECT
    audit_id,
    valuation_id,
    previous_status,
    new_status,
    changed_at,
    changed_by
FROM valuation_audit
ORDER BY changed_at DESC;

-- 10. Input validation query.

SELECT
    fs.statement_id,
    c.company_name,
    fs.revenue,
    fs.ebit,
    fs.depreciation,
    fs.capital_expenditure,
    fs.cash,
    fs.debt,
    fs.tax_rate,
    CASE
        WHEN fs.revenue <= 0 THEN 'INVALID REVENUE'
        WHEN fs.shares_outstanding <= 0 THEN 'INVALID SHARES'
        WHEN fs.tax_rate < 0 OR fs.tax_rate >= 1 THEN 'INVALID TAX'
        WHEN fs.ebit < 0 THEN 'NEGATIVE EBIT'
        ELSE 'VALID'
    END AS validation_status
FROM financial_statements fs
JOIN companies c
    ON c.company_id = fs.company_id;

-- ============================================================
-- SENSITIVITY ANALYSIS
-- ============================================================

-- Calculates enterprise value for a WACC and terminal-growth grid.
-- The projected FCFF amounts remain constant; discount rates change.

WITH base_valuation AS (
    SELECT
        v.valuation_id,
        v.wacc,
        v.terminal_value,
        a.terminal_growth,
        MAX(p.year_number) AS periods,
        MAX(p.fcff) FILTER (
            WHERE p.year_number = (
                SELECT MAX(p2.year_number)
                FROM projected_cash_flows p2
                WHERE p2.valuation_id = v.valuation_id
            )
        ) AS final_fcff
    FROM valuations v
    JOIN valuation_assumptions a
        ON a.assumption_id = v.assumption_id
    JOIN projected_cash_flows p
        ON p.valuation_id = v.valuation_id
    WHERE v.scenario = 'BASE'
      AND v.status = 'CALCULATED'
    GROUP BY
        v.valuation_id,
        v.wacc,
        v.terminal_value,
        a.terminal_growth
),
rate_grid AS (
    SELECT
        b.valuation_id,
        b.periods,
        b.final_fcff,
        b.wacc + w.wacc_change AS adjusted_wacc,
        b.terminal_growth + g.growth_change AS adjusted_growth
    FROM base_valuation b
    CROSS JOIN (
        VALUES
            (-0.01::NUMERIC),
            (0.00::NUMERIC),
            (0.01::NUMERIC)
    ) w(wacc_change)
    CROSS JOIN (
        VALUES
            (-0.01::NUMERIC),
            (0.00::NUMERIC),
            (0.01::NUMERIC)
    ) g(growth_change)
),
explicit_values AS (
    SELECT
        r.valuation_id,
        r.periods,
        r.final_fcff,
        r.adjusted_wacc,
        r.adjusted_growth,
        SUM(
            p.fcff /
            POWER(1 + r.adjusted_wacc, p.year_number)
        ) AS explicit_value
    FROM rate_grid r
    JOIN projected_cash_flows p
        ON p.valuation_id = r.valuation_id
    WHERE r.adjusted_wacc > r.adjusted_growth
      AND r.adjusted_wacc > 0
      AND r.adjusted_growth >= 0
    GROUP BY
        r.valuation_id,
        r.periods,
        r.final_fcff,
        r.adjusted_wacc,
        r.adjusted_growth
)
SELECT
    valuation_id,
    adjusted_wacc,
    adjusted_growth,
    explicit_value
    + (
        final_fcff * (1 + adjusted_growth)
        / (adjusted_wacc - adjusted_growth)
      ) / POWER(1 + adjusted_wacc, periods)
        AS sensitivity_enterprise_value
FROM explicit_values
ORDER BY adjusted_wacc, adjusted_growth;

-- ============================================================
-- FINAL DATABASE INTEGRITY CHECKS
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM valuations
        WHERE status = 'CALCULATED'
          AND ABS(
              equity_value -
              (
                  enterprise_value
                  + (
                      SELECT cash
                      FROM financial_statements
                      WHERE statement_id = valuations.statement_id
                  )
                  - (
                      SELECT debt
                      FROM financial_statements
                      WHERE statement_id = valuations.statement_id
                  )
              )
          ) > 0.01
    ) THEN
        RAISE EXCEPTION
            'Enterprise-to-equity reconciliation failed';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM valuations
        WHERE status = 'CALCULATED'
          AND terminal_value <= 0
    ) THEN
        RAISE EXCEPTION
            'Invalid terminal valuation detected';
    END IF;

    RAISE NOTICE
        'Business valuation database integrity checks passed';
END;
$$;
