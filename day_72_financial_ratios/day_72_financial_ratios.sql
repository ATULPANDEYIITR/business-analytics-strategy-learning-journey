/*
===============================================================================
FINANCIAL RATIOS
Profitability, Liquidity, Leverage and Efficiency Analysis
PostgreSQL 14+

Includes:
- Relational financial statement storage
- Company and reporting-period management
- Financial statement validation
- Ratio calculations
- Historical analysis
- Policy-based ratio evaluation
- Triggers and audit logging
- Aggregation and reporting
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS financial_analysis;

SET search_path TO financial_analysis, public;

-- ============================================================================
-- 1. REFERENCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS companies (
    company_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_name VARCHAR(200) NOT NULL UNIQUE,

    industry VARCHAR(100) NOT NULL,

    country_code CHAR(2) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_company_name
        CHECK (length(trim(company_name)) > 0),

    CONSTRAINT valid_country_code
        CHECK (country_code ~ '^[A-Z]{2}$')
);

CREATE TABLE IF NOT EXISTS reporting_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    period_name VARCHAR(30) NOT NULL UNIQUE,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    CONSTRAINT valid_reporting_dates
        CHECK (end_date >= start_date)
);

-- ============================================================================
-- 2. FINANCIAL STATEMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_statements (
    statement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_id BIGINT NOT NULL
        REFERENCES companies(company_id),

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    currency CHAR(3) NOT NULL DEFAULT 'INR',

    revenue NUMERIC(20, 2) NOT NULL DEFAULT 0,

    cost_of_goods_sold NUMERIC(20, 2) NOT NULL DEFAULT 0,

    operating_expenses NUMERIC(20, 2) NOT NULL DEFAULT 0,

    operating_income NUMERIC(20, 2) NOT NULL DEFAULT 0,

    net_income NUMERIC(20, 2) NOT NULL DEFAULT 0,

    total_assets NUMERIC(20, 2) NOT NULL DEFAULT 0,

    current_assets NUMERIC(20, 2) NOT NULL DEFAULT 0,

    inventory NUMERIC(20, 2) NOT NULL DEFAULT 0,

    cash NUMERIC(20, 2) NOT NULL DEFAULT 0,

    accounts_receivable NUMERIC(20, 2) NOT NULL DEFAULT 0,

    total_liabilities NUMERIC(20, 2) NOT NULL DEFAULT 0,

    current_liabilities NUMERIC(20, 2) NOT NULL DEFAULT 0,

    total_debt NUMERIC(20, 2) NOT NULL DEFAULT 0,

    shareholders_equity NUMERIC(20, 2) NOT NULL DEFAULT 0,

    interest_expense NUMERIC(20, 2) NOT NULL DEFAULT 0,

    inventory_beginning NUMERIC(20, 2) NOT NULL DEFAULT 0,

    inventory_ending NUMERIC(20, 2) NOT NULL DEFAULT 0,

    receivables_beginning NUMERIC(20, 2) NOT NULL DEFAULT 0,

    receivables_ending NUMERIC(20, 2) NOT NULL DEFAULT 0,

    statement_status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_company_period
        UNIQUE(company_id, period_id),

    CONSTRAINT valid_currency
        CHECK (currency ~ '^[A-Z]{3}$'),

    CONSTRAINT nonnegative_financial_values
        CHECK (
            revenue >= 0
            AND cost_of_goods_sold >= 0
            AND operating_expenses >= 0
            AND operating_income >= 0
            AND net_income >= 0
            AND total_assets >= 0
            AND current_assets >= 0
            AND inventory >= 0
            AND cash >= 0
            AND accounts_receivable >= 0
            AND total_liabilities >= 0
            AND current_liabilities >= 0
            AND total_debt >= 0
            AND shareholders_equity >= 0
            AND interest_expense >= 0
            AND inventory_beginning >= 0
            AND inventory_ending >= 0
            AND receivables_beginning >= 0
            AND receivables_ending >= 0
        ),

    CONSTRAINT valid_asset_relationships
        CHECK (
            current_assets <= total_assets
            AND cash <= current_assets
            AND inventory <= current_assets
            AND accounts_receivable <= current_assets
        ),

    CONSTRAINT valid_liability_relationships
        CHECK (
            current_liabilities <= total_liabilities
            AND total_debt <= total_liabilities
        ),

    CONSTRAINT valid_statement_status
        CHECK (
            statement_status IN (
                'DRAFT',
                'VALIDATED',
                'APPROVED',
                'REJECTED'
            )
        )
);

-- ============================================================================
-- 3. RATIO POLICY MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS ratio_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL UNIQUE,

    ratio_name VARCHAR(100) NOT NULL,

    minimum_value NUMERIC(20, 6),

    maximum_value NUMERIC(20, 6),

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_policy_range
        CHECK (
            minimum_value IS NULL
            OR maximum_value IS NULL
            OR minimum_value <= maximum_value
        )
);

-- ============================================================================
-- 4. RATIO RESULTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ratio_results (
    ratio_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    statement_id BIGINT NOT NULL
        REFERENCES financial_statements(statement_id)
        ON DELETE CASCADE,

    ratio_name VARCHAR(100) NOT NULL,

    category VARCHAR(30) NOT NULL,

    ratio_value NUMERIC(24, 8),

    unit VARCHAR(15) NOT NULL,

    interpretation TEXT NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_statement_ratio
        UNIQUE(statement_id, ratio_name),

    CONSTRAINT valid_ratio_category
        CHECK (
            category IN (
                'PROFITABILITY',
                'LIQUIDITY',
                'LEVERAGE',
                'EFFICIENCY'
            )
        )
);

CREATE TABLE IF NOT EXISTS ratio_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    ratio_id BIGINT NOT NULL
        REFERENCES ratio_results(ratio_id)
        ON DELETE CASCADE,

    policy_id BIGINT NOT NULL
        REFERENCES ratio_policies(policy_id),

    evaluation_status VARCHAR(20) NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_ratio_policy_evaluation
        UNIQUE(ratio_id, policy_id),

    CONSTRAINT valid_evaluation_status
        CHECK (
            evaluation_status IN (
                'PASS',
                'FAIL',
                'UNDEFINED'
            )
        )
);

-- ============================================================================
-- 5. AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS financial_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    statement_id BIGINT,

    operation VARCHAR(20) NOT NULL,

    old_status VARCHAR(20),

    new_status VARCHAR(20),

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    changed_by TEXT NOT NULL DEFAULT CURRENT_USER
);

-- ============================================================================
-- 6. PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_statements_company
    ON financial_statements(company_id, period_id);

CREATE INDEX IF NOT EXISTS idx_statements_status
    ON financial_statements(statement_status);

CREATE INDEX IF NOT EXISTS idx_ratio_category
    ON ratio_results(category, ratio_name);

CREATE INDEX IF NOT EXISTS idx_ratio_value
    ON ratio_results(ratio_name, ratio_value);

CREATE INDEX IF NOT EXISTS idx_audit_statement
    ON financial_audit(statement_id, changed_at DESC);

-- ============================================================================
-- 7. FINANCIAL STATEMENT VALIDATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_financial_statement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.current_assets > NEW.total_assets THEN
        RAISE EXCEPTION
            'Current assets cannot exceed total assets';
    END IF;

    IF NEW.current_liabilities > NEW.total_liabilities THEN
        RAISE EXCEPTION
            'Current liabilities cannot exceed total liabilities';
    END IF;

    IF NEW.total_debt > NEW.total_liabilities THEN
        RAISE EXCEPTION
            'Total debt cannot exceed total liabilities';
    END IF;

    IF NEW.cash > NEW.current_assets THEN
        RAISE EXCEPTION
            'Cash cannot exceed current assets';
    END IF;

    IF NEW.inventory > NEW.current_assets THEN
        RAISE EXCEPTION
            'Inventory cannot exceed current assets';
    END IF;

    IF NEW.accounts_receivable > NEW.current_assets THEN
        RAISE EXCEPTION
            'Receivables cannot exceed current assets';
    END IF;

    IF NEW.statement_status = 'APPROVED'
       AND NEW.revenue = 0 THEN
        RAISE EXCEPTION
            'An approved statement must contain revenue';
    END IF;

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_financial_statement
ON financial_statements;

CREATE TRIGGER trg_validate_financial_statement
BEFORE INSERT OR UPDATE
ON financial_statements
FOR EACH ROW
EXECUTE FUNCTION validate_financial_statement();

-- ============================================================================
-- 8. AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_statement_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO financial_audit (
            statement_id,
            operation,
            new_status
        )
        VALUES (
            NEW.statement_id,
            'INSERT',
            NEW.statement_status
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO financial_audit (
            statement_id,
            operation,
            old_status,
            new_status
        )
        VALUES (
            NEW.statement_id,
            'UPDATE',
            OLD.statement_status,
            NEW.statement_status
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO financial_audit (
            statement_id,
            operation,
            old_status
        )
        VALUES (
            OLD.statement_id,
            'DELETE',
            OLD.statement_status
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_financial_statement
ON financial_statements;

CREATE TRIGGER trg_audit_financial_statement
AFTER INSERT OR UPDATE OR DELETE
ON financial_statements
FOR EACH ROW
EXECUTE FUNCTION audit_statement_changes();

-- ============================================================================
-- 9. FINANCIAL RATIO CALCULATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION safe_ratio(
    numerator NUMERIC,
    denominator NUMERIC
)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
PARALLEL SAFE
AS $$
    SELECT CASE
        WHEN denominator IS NULL OR denominator = 0
        THEN NULL
        ELSE ROUND(numerator / denominator, 8)
    END;
$$;

-- ============================================================================
-- 10. FINANCIAL RATIO VIEW
-- ============================================================================

CREATE OR REPLACE VIEW financial_ratio_report AS

WITH base AS (
    SELECT
        s.statement_id,
        c.company_name,
        c.industry,
        p.period_name,
        p.start_date,
        p.end_date,

        s.revenue,
        s.cost_of_goods_sold,
        s.operating_income,
        s.net_income,

        s.total_assets,
        s.current_assets,
        s.inventory,
        s.cash,
        s.total_liabilities,
        s.current_liabilities,
        s.total_debt,
        s.shareholders_equity,
        s.interest_expense,

        (s.inventory_beginning + s.inventory_ending)
            / 2.0 AS average_inventory,

        (s.receivables_beginning + s.receivables_ending)
            / 2.0 AS average_receivables

    FROM financial_statements s

    JOIN companies c
        ON c.company_id = s.company_id

    JOIN reporting_periods p
        ON p.period_id = s.period_id

    WHERE s.statement_status IN (
        'VALIDATED',
        'APPROVED'
    )
),

ratios AS (
    SELECT
        statement_id,
        company_name,
        industry,
        period_name,

        'Gross Profit Margin'::VARCHAR AS ratio_name,
        'PROFITABILITY'::VARCHAR AS category,

        safe_ratio(
            revenue - cost_of_goods_sold,
            revenue
        ) * 100 AS ratio_value,

        '%'::VARCHAR AS unit

    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Operating Profit Margin',
        'PROFITABILITY',
        safe_ratio(operating_income, revenue) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Net Profit Margin',
        'PROFITABILITY',
        safe_ratio(net_income, revenue) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Return on Assets',
        'PROFITABILITY',
        safe_ratio(net_income, total_assets) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Return on Equity',
        'PROFITABILITY',
        safe_ratio(net_income, shareholders_equity) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Current Ratio',
        'LIQUIDITY',
        safe_ratio(current_assets, current_liabilities),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Quick Ratio',
        'LIQUIDITY',
        safe_ratio(
            current_assets - inventory,
            current_liabilities
        ),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Cash Ratio',
        'LIQUIDITY',
        safe_ratio(cash, current_liabilities),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Debt-to-Equity Ratio',
        'LEVERAGE',
        safe_ratio(total_debt, shareholders_equity),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Debt-to-Assets Ratio',
        'LEVERAGE',
        safe_ratio(total_debt, total_assets) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Debt Ratio',
        'LEVERAGE',
        safe_ratio(total_liabilities, total_assets) * 100,
        '%'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Interest Coverage Ratio',
        'LEVERAGE',
        safe_ratio(operating_income, interest_expense),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Inventory Turnover',
        'EFFICIENCY',
        safe_ratio(cost_of_goods_sold, average_inventory),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Receivables Turnover',
        'EFFICIENCY',
        safe_ratio(revenue, average_receivables),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Total Asset Turnover',
        'EFFICIENCY',
        safe_ratio(revenue, total_assets),
        'x'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Days Sales Outstanding',
        'EFFICIENCY',
        safe_ratio(
            average_receivables * 365,
            revenue
        ),
        'days'
    FROM base

    UNION ALL

    SELECT
        statement_id,
        company_name,
        industry,
        period_name,
        'Days Inventory Outstanding',
        'EFFICIENCY',
        safe_ratio(
            average_inventory * 365,
            cost_of_goods_sold
        ),
        'days'
    FROM base
)

SELECT *
FROM ratios;

-- ============================================================================
-- 11. RATIO PROCESSING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE calculate_statement_ratios(
    p_statement_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status VARCHAR(20);
BEGIN
    SELECT statement_status
    INTO v_status
    FROM financial_statements
    WHERE statement_id = p_statement_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Financial statement % does not exist',
            p_statement_id;
    END IF;

    IF v_status NOT IN ('VALIDATED', 'APPROVED') THEN
        RAISE EXCEPTION
            'Statement must be validated before calculation';
    END IF;

    DELETE FROM ratio_results
    WHERE statement_id = p_statement_id;

    INSERT INTO ratio_results (
        statement_id,
        ratio_name,
        category,
        ratio_value,
        unit,
        interpretation
    )
    SELECT
        statement_id,
        ratio_name,
        category,
        ratio_value,
        unit,

        CASE ratio_name
            WHEN 'Gross Profit Margin'
                THEN 'Gross profitability after direct costs.'
            WHEN 'Operating Profit Margin'
                THEN 'Operating income relative to revenue.'
            WHEN 'Net Profit Margin'
                THEN 'Net profitability relative to revenue.'
            WHEN 'Return on Assets'
                THEN 'Profitability relative to total assets.'
            WHEN 'Return on Equity'
                THEN 'Profitability relative to shareholders equity.'
            WHEN 'Current Ratio'
                THEN 'Short-term asset coverage.'
            WHEN 'Quick Ratio'
                THEN 'Liquid asset coverage excluding inventory.'
            WHEN 'Cash Ratio'
                THEN 'Immediate cash coverage.'
            WHEN 'Debt-to-Equity Ratio'
                THEN 'Debt financing relative to equity.'
            WHEN 'Debt-to-Assets Ratio'
                THEN 'Asset financing provided by debt.'
            WHEN 'Debt Ratio'
                THEN 'Asset financing provided by liabilities.'
            WHEN 'Interest Coverage Ratio'
                THEN 'Operating income available for interest.'
            WHEN 'Inventory Turnover'
                THEN 'Inventory replacement frequency.'
            WHEN 'Receivables Turnover'
                THEN 'Receivables collection efficiency.'
            WHEN 'Total Asset Turnover'
                THEN 'Revenue generated by total assets.'
            WHEN 'Days Sales Outstanding'
                THEN 'Estimated receivables collection period.'
            WHEN 'Days Inventory Outstanding'
                THEN 'Estimated inventory holding period.'
            ELSE 'Financial performance indicator.'
        END

    FROM financial_ratio_report
    WHERE statement_id = p_statement_id;

    -- Evaluate every enabled policy against the new ratio results.
    INSERT INTO ratio_evaluations (
        ratio_id,
        policy_id,
        evaluation_status
    )
    SELECT
        r.ratio_id,
        p.policy_id,

        CASE
            WHEN r.ratio_value IS NULL
                THEN 'UNDEFINED'

            WHEN p.minimum_value IS NOT NULL
                 AND r.ratio_value < p.minimum_value
                THEN 'FAIL'

            WHEN p.maximum_value IS NOT NULL
                 AND r.ratio_value > p.maximum_value
                THEN 'FAIL'

            ELSE 'PASS'
        END

    FROM ratio_results r

    CROSS JOIN ratio_policies p

    WHERE r.statement_id = p_statement_id
      AND p.enabled = TRUE
      AND p.ratio_name = r.ratio_name

    ON CONFLICT (ratio_id, policy_id)
    DO UPDATE SET
        evaluation_status = EXCLUDED.evaluation_status,
        evaluated_at = CURRENT_TIMESTAMP;

END;
$$;

-- ============================================================================
-- 12. SAMPLE COMPANIES AND REPORTING PERIODS
-- ============================================================================

INSERT INTO companies (
    company_name,
    industry,
    country_code
)
VALUES
    ('Apex Manufacturing Ltd.', 'Manufacturing', 'IN'),
    ('Vertex Technologies Ltd.', 'Technology', 'IN'),
    ('Horizon Retail Ltd.', 'Retail', 'IN')
ON CONFLICT (company_name) DO NOTHING;

INSERT INTO reporting_periods (
    period_name,
    start_date,
    end_date
)
VALUES
    ('FY2025-26', '2025-04-01', '2026-03-31'),
    ('FY2024-25', '2024-04-01', '2025-03-31')
ON CONFLICT (period_name) DO NOTHING;

-- ============================================================================
-- 13. SAMPLE FINANCIAL DATA
-- ============================================================================

INSERT INTO financial_statements (
    company_id,
    period_id,
    currency,

    revenue,
    cost_of_goods_sold,
    operating_expenses,
    operating_income,
    net_income,

    total_assets,
    current_assets,
    inventory,
    cash,
    accounts_receivable,

    total_liabilities,
    current_liabilities,
    total_debt,
    shareholders_equity,

    interest_expense,

    inventory_beginning,
    inventory_ending,

    receivables_beginning,
    receivables_ending,

    statement_status
)
SELECT
    c.company_id,
    p.period_id,
    'INR',

    12000000,
    7200000,
    2400000,
    2400000,
    1500000,

    10000000,
    4000000,
    1200000,
    800000,
    1000000,

    5000000,
    2000000,
    3000000,
    5000000,

    400000,

    1000000,
    1200000,

    800000,
    1000000,

    'VALIDATED'

FROM companies c
CROSS JOIN reporting_periods p

WHERE c.company_name = 'Apex Manufacturing Ltd.'
  AND p.period_name = 'FY2025-26'

ON CONFLICT (company_id, period_id) DO NOTHING;

-- Technology company: high profitability and low inventory.
INSERT INTO financial_statements (
    company_id,
    period_id,
    revenue,
    cost_of_goods_sold,
    operating_expenses,
    operating_income,
    net_income,
    total_assets,
    current_assets,
    inventory,
    cash,
    accounts_receivable,
    total_liabilities,
    current_liabilities,
    total_debt,
    shareholders_equity,
    interest_expense,
    inventory_beginning,
    inventory_ending,
    receivables_beginning,
    receivables_ending,
    statement_status
)
SELECT
    c.company_id,
    p.period_id,
    15000000,
    4500000,
    6000000,
    4500000,
    3300000,
    18000000,
    9000000,
    500000,
    3500000,
    2500000,
    6000000,
    3000000,
    3500000,
    12000000,
    300000,
    400000,
    500000,
    2000000,
    2500000,
    'VALIDATED'
FROM companies c
CROSS JOIN reporting_periods p
WHERE c.company_name = 'Vertex Technologies Ltd.'
  AND p.period_name = 'FY2025-26'
ON CONFLICT (company_id, period_id) DO NOTHING;

-- Retail company: high inventory and weaker liquidity.
INSERT INTO financial_statements (
    company_id,
    period_id,
    revenue,
    cost_of_goods_sold,
    operating_expenses,
    operating_income,
    net_income,
    total_assets,
    current_assets,
    inventory,
    cash,
    accounts_receivable,
    total_liabilities,
    current_liabilities,
    total_debt,
    shareholders_equity,
    interest_expense,
    inventory_beginning,
    inventory_ending,
    receivables_beginning,
    receivables_ending,
    statement_status
)
SELECT
    c.company_id,
    p.period_id,
    8000000,
    6000000,
    1500000,
    500000,
    200000,
    9000000,
    2500000,
    1500000,
    200000,
    500000,
    6500000,
    3000000,
    4500000,
    2500000,
    300000,
    1400000,
    1500000,
    400000,
    500000,
    'VALIDATED'
FROM companies c
CROSS JOIN reporting_periods p
WHERE c.company_name = 'Horizon Retail Ltd.'
  AND p.period_name = 'FY2025-26'
ON CONFLICT (company_id, period_id) DO NOTHING;

-- ============================================================================
-- 14. SAMPLE RATIO POLICIES
-- ============================================================================

INSERT INTO ratio_policies (
    policy_name,
    ratio_name,
    minimum_value,
    maximum_value,
    enabled
)
VALUES
    ('Minimum Current Ratio', 'Current Ratio', 1.50, NULL, TRUE),
    ('Minimum Quick Ratio', 'Quick Ratio', 1.00, NULL, TRUE),
    ('Minimum Interest Coverage', 'Interest Coverage Ratio', 2.00, NULL, TRUE),
    ('Maximum Debt Equity', 'Debt-to-Equity Ratio', NULL, 2.00, TRUE),
    ('Minimum Net Margin', 'Net Profit Margin', 5.00, NULL, TRUE)
ON CONFLICT (policy_name) DO NOTHING;

-- ============================================================================
-- 15. EXECUTE RATIO CALCULATIONS
-- ============================================================================

DO $$
DECLARE
    record_row RECORD;
BEGIN
    FOR record_row IN
        SELECT statement_id
        FROM financial_statements
        WHERE statement_status = 'VALIDATED'
    LOOP
        CALL calculate_statement_ratios(
            record_row.statement_id
        );
    END LOOP;
END;
$$;

-- ============================================================================
-- 16. RETRIEVAL QUERIES
-- ============================================================================

-- All calculated ratios.
SELECT
    company_name,
    period_name,
    category,
    ratio_name,
    ratio_value,
    unit
FROM financial_ratio_report
ORDER BY company_name, category, ratio_name;

-- Profitability ratios only.
SELECT
    company_name,
    period_name,
    ratio_name,
    ratio_value,
    unit
FROM financial_ratio_report
WHERE category = 'PROFITABILITY'
ORDER BY company_name, ratio_name;

-- ============================================================================
-- 17. VALIDATION QUERIES
-- ============================================================================

-- Detect statements with zero denominators for important ratios.
SELECT
    company_name,
    period_name,
    ratio_name
FROM financial_ratio_report
WHERE ratio_value IS NULL
ORDER BY company_name, ratio_name;

-- Identify potentially weak liquidity.
SELECT
    company_name,
    ratio_value AS current_ratio
FROM financial_ratio_report
WHERE ratio_name = 'Current Ratio'
  AND ratio_value < 1.00;

-- ============================================================================
-- 18. AGGREGATION AND INDUSTRY ANALYSIS
-- ============================================================================

SELECT
    industry,
    ratio_name,
    ROUND(AVG(ratio_value), 4) AS industry_average,
    ROUND(MIN(ratio_value), 4) AS minimum_value,
    ROUND(MAX(ratio_value), 4) AS maximum_value,
    COUNT(ratio_value) AS observations
FROM financial_ratio_report
GROUP BY industry, ratio_name
ORDER BY industry, ratio_name;

-- ============================================================================
-- 19. POLICY EVALUATION REPORT
-- ============================================================================

SELECT
    c.company_name,
    p.period_name,
    r.ratio_name,
    r.ratio_value,
    rp.policy_name,
    e.evaluation_status
FROM ratio_evaluations e
JOIN ratio_results r
    ON r.ratio_id = e.ratio_id
JOIN ratio_policies rp
    ON rp.policy_id = e.policy_id
JOIN financial_statements s
    ON s.statement_id = r.statement_id
JOIN companies c
    ON c.company_id = s.company_id
JOIN reporting_periods p
    ON p.period_id = s.period_id
ORDER BY c.company_name, rp.policy_name;

-- ============================================================================
-- 20. COMPANY FINANCIAL PERFORMANCE REPORT
-- ============================================================================

WITH company_metrics AS (
    SELECT
        company_name,
        category,
        ratio_name,
        ratio_value
    FROM financial_ratio_report
)
SELECT
    company_name,

    COUNT(*) AS total_ratios,

    COUNT(ratio_value) AS defined_ratios,

    COUNT(*) - COUNT(ratio_value) AS undefined_ratios,

    ROUND(
        AVG(ratio_value) FILTER (
            WHERE category = 'PROFITABILITY'
        ),
        4
    ) AS average_profitability_indicator,

    ROUND(
        AVG(ratio_value) FILTER (
            WHERE category = 'LIQUIDITY'
        ),
        4
    ) AS average_liquidity_indicator,

    ROUND(
        AVG(ratio_value) FILTER (
            WHERE category = 'LEVERAGE'
        ),
        4
    ) AS average_leverage_indicator

FROM company_metrics
GROUP BY company_name
ORDER BY company_name;

-- ============================================================================
-- 21. AUDIT HISTORY
-- ============================================================================

SELECT
    audit_id,
    statement_id,
    operation,
    old_status,
    new_status,
    changed_at,
    changed_by
FROM financial_audit
ORDER BY changed_at DESC;

-- ============================================================================
-- 22. TRANSACTIONAL VALIDATION EXAMPLE
-- ============================================================================

-- This transaction demonstrates rollback after an invalid update.
-- The existing statement remains unchanged.

DO $$
DECLARE
    v_statement_id BIGINT;
BEGIN
    SELECT statement_id
    INTO v_statement_id
    FROM financial_statements
    WHERE statement_status = 'VALIDATED'
    ORDER BY statement_id
    LIMIT 1;

    IF v_statement_id IS NOT NULL THEN
        BEGIN
            UPDATE financial_statements
            SET current_assets = total_assets + 100
            WHERE statement_id = v_statement_id;

        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE
                'Invalid update rejected and rolled back: %',
                SQLERRM;
        END;
    END IF;
END;
$$;

COMMIT;
