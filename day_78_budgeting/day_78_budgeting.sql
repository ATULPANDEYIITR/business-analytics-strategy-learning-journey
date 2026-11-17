/*
===============================================================================
BUDGET PREPARATION AND VARIANCE ANALYSIS
PostgreSQL 14+

Financial planning and performance management database.

Includes:
- Department and account master data
- Fiscal periods
- Budget preparation and revisions
- Budget line items
- Approval workflow
- Actual financial transactions
- Static and flexible budget calculations
- Variance classification
- Budget utilization
- Rolling forecasts
- Audit events
- Constraints and indexes
- Stored functions and procedures
- Reporting views
- Transaction handling

Currency amounts use NUMERIC, never FLOAT or REAL.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS budgeting;

SET search_path TO budgeting, public;

-- ============================================================================
-- 1. ENUMERATIONS
-- ============================================================================

CREATE TYPE account_type AS ENUM (
    'REVENUE',
    'EXPENSE'
);

CREATE TYPE cost_behavior AS ENUM (
    'FIXED',
    'VARIABLE',
    'MIXED'
);

CREATE TYPE budget_status AS ENUM (
    'DRAFT',
    'SUBMITTED',
    'APPROVED',
    'REJECTED',
    'CLOSED'
);

CREATE TYPE budget_type AS ENUM (
    'STATIC',
    'FLEXIBLE',
    'ROLLING'
);

CREATE TYPE approval_decision AS ENUM (
    'APPROVED',
    'REJECTED'
);

CREATE TYPE variance_status AS ENUM (
    'FAVORABLE',
    'UNFAVORABLE',
    'ON_TARGET'
);

-- ============================================================================
-- 2. MASTER DATA
-- ============================================================================

CREATE TABLE departments (
    department_id VARCHAR(15) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    annual_spending_limit NUMERIC(18,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_department_limit
        CHECK (annual_spending_limit >= 0)
);

CREATE TABLE employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    employee_role VARCHAR(40) NOT NULL,
    department_id VARCHAR(15)
        REFERENCES departments(department_id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_employee_role
        CHECK (
            employee_role IN (
                'DEPARTMENT_MANAGER',
                'FINANCE_MANAGER',
                'FINANCE_CONTROLLER',
                'CFO',
                'ACCOUNTANT',
                'AUDITOR'
            )
        )
);

CREATE TABLE accounts (
    account_code VARCHAR(20) PRIMARY KEY,
    account_name VARCHAR(150) NOT NULL,
    account_type account_type NOT NULL,
    cost_behavior cost_behavior NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_revenue_behavior
        CHECK (
            account_type <> 'REVENUE'
            OR cost_behavior = 'FIXED'
        )
);

CREATE TABLE fiscal_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fiscal_year INTEGER NOT NULL,
    period_number SMALLINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_fiscal_period
        UNIQUE (fiscal_year, period_number),

    CONSTRAINT chk_period_number
        CHECK (period_number BETWEEN 1 AND 12),

    CONSTRAINT chk_fiscal_dates
        CHECK (end_date >= start_date)
);

-- ============================================================================
-- 3. BUDGET MASTER
-- ============================================================================

CREATE TABLE budgets (
    budget_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    budget_code VARCHAR(40) NOT NULL UNIQUE,
    fiscal_year INTEGER NOT NULL,
    budget_name VARCHAR(150) NOT NULL,
    budget_type budget_type NOT NULL DEFAULT 'STATIC',
    status budget_status NOT NULL DEFAULT 'DRAFT',
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    revision_number INTEGER NOT NULL DEFAULT 1,
    parent_budget_id BIGINT REFERENCES budgets(budget_id),
    created_by BIGINT NOT NULL REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,

    CONSTRAINT chk_budget_year
        CHECK (fiscal_year BETWEEN 2000 AND 2200),

    CONSTRAINT chk_revision
        CHECK (revision_number > 0),

    CONSTRAINT chk_currency
        CHECK (currency_code ~ '^[A-Z]{3}$'),

    CONSTRAINT chk_budget_dates
        CHECK (
            (status <> 'APPROVED' OR approved_at IS NOT NULL)
            AND
            (status <> 'CLOSED' OR closed_at IS NOT NULL)
        )
);

CREATE TABLE budget_lines (
    budget_line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    budget_id BIGINT NOT NULL REFERENCES budgets(budget_id),
    account_code VARCHAR(20) NOT NULL REFERENCES accounts(account_code),
    department_id VARCHAR(15) NOT NULL
        REFERENCES departments(department_id),

    fixed_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    variable_rate NUMERIC(18,4) NOT NULL DEFAULT 0,
    planned_activity NUMERIC(18,2) NOT NULL DEFAULT 0,

    annual_budget_amount NUMERIC(18,2)
        GENERATED ALWAYS AS (
            CASE
                WHEN (
                    SELECT NULL::NUMERIC
                ) IS NULL THEN fixed_amount
                ELSE fixed_amount
            END
        ) STORED,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_budget_account_department
        UNIQUE (budget_id, account_code, department_id),

    CONSTRAINT chk_fixed_amount
        CHECK (fixed_amount >= 0),

    CONSTRAINT chk_variable_rate
        CHECK (variable_rate >= 0),

    CONSTRAINT chk_planned_activity
        CHECK (planned_activity >= 0)
);

-- A generated column cannot reference account master data.
-- The budget amount is therefore calculated through a function and view.
ALTER TABLE budget_lines
    DROP COLUMN annual_budget_amount;

-- ============================================================================
-- 4. APPROVAL WORKFLOW
-- ============================================================================

CREATE TABLE budget_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    budget_id BIGINT NOT NULL REFERENCES budgets(budget_id),
    approver_id BIGINT NOT NULL REFERENCES employees(employee_id),
    decision approval_decision NOT NULL,
    comments TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_budget_approver
        UNIQUE (budget_id, approver_id)
);

-- ============================================================================
-- 5. ACTUAL TRANSACTION LEDGER
-- ============================================================================

CREATE TABLE actual_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transaction_reference VARCHAR(60) NOT NULL UNIQUE,
    budget_id BIGINT NOT NULL REFERENCES budgets(budget_id),
    budget_line_id BIGINT NOT NULL REFERENCES budget_lines(budget_line_id),
    period_id BIGINT NOT NULL REFERENCES fiscal_periods(period_id),
    transaction_date DATE NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    activity_units NUMERIC(18,2) NOT NULL DEFAULT 0,
    description VARCHAR(250) NOT NULL,
    entered_by BIGINT NOT NULL REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_actual_amount
        CHECK (amount >= 0),

    CONSTRAINT chk_actual_activity
        CHECK (activity_units >= 0)
);

-- ============================================================================
-- 6. AUDIT EVENTS
-- ============================================================================

CREATE TABLE budget_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    budget_id BIGINT NOT NULL REFERENCES budgets(budget_id),
    action VARCHAR(50) NOT NULL,
    actor_id BIGINT REFERENCES employees(employee_id),
    previous_status budget_status,
    new_status budget_status,
    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE budget_forecasts (
    forecast_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    budget_id BIGINT NOT NULL REFERENCES budgets(budget_id),
    period_id BIGINT NOT NULL REFERENCES fiscal_periods(period_id),
    budget_line_id BIGINT NOT NULL REFERENCES budget_lines(budget_line_id),
    forecast_amount NUMERIC(18,2) NOT NULL,
    forecast_method VARCHAR(40) NOT NULL,
    created_by BIGINT NOT NULL REFERENCES employees(employee_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_forecast_version
        UNIQUE (budget_id, period_id, budget_line_id, forecast_method),

    CONSTRAINT chk_forecast_amount
        CHECK (forecast_amount >= 0)
);

-- ============================================================================
-- 7. PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX idx_budget_year_status
    ON budgets(fiscal_year, status);

CREATE INDEX idx_budget_lines_department
    ON budget_lines(department_id, budget_id);

CREATE INDEX idx_budget_lines_account
    ON budget_lines(account_code);

CREATE INDEX idx_actual_budget_period
    ON actual_transactions(budget_id, period_id);

CREATE INDEX idx_actual_budget_line
    ON actual_transactions(budget_line_id, period_id);

CREATE INDEX idx_actual_date
    ON actual_transactions(transaction_date);

CREATE INDEX idx_approval_budget
    ON budget_approvals(budget_id, decision);

CREATE INDEX idx_audit_budget_time
    ON budget_audit_log(budget_id, event_time DESC);

CREATE INDEX idx_forecast_budget_period
    ON budget_forecasts(budget_id, period_id);

-- ============================================================================
-- 8. FINANCIAL CALCULATION FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_budget_amount(
    p_budget_line_id BIGINT
)
RETURNS NUMERIC(18,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT ROUND(
        CASE
            WHEN a.account_type = 'REVENUE'
                THEN bl.fixed_amount

            WHEN a.cost_behavior = 'FIXED'
                THEN bl.fixed_amount

            WHEN a.cost_behavior = 'VARIABLE'
                THEN bl.variable_rate * bl.planned_activity

            WHEN a.cost_behavior = 'MIXED'
                THEN bl.fixed_amount +
                     bl.variable_rate * bl.planned_activity
        END,
        2
    )
    FROM budget_lines bl
    JOIN accounts a
      ON a.account_code = bl.account_code
    WHERE bl.budget_line_id = p_budget_line_id;
$$;

CREATE OR REPLACE FUNCTION calculate_flexible_budget(
    p_budget_line_id BIGINT,
    p_activity NUMERIC
)
RETURNS NUMERIC(18,2)
LANGUAGE PLPGSQL
STABLE
AS $$
DECLARE
    v_behavior cost_behavior;
    v_account_type account_type;
    v_fixed NUMERIC(18,2);
    v_rate NUMERIC(18,4);
BEGIN
    IF p_activity IS NULL OR p_activity < 0 THEN
        RAISE EXCEPTION 'Activity must be non-negative.';
    END IF;

    SELECT a.cost_behavior,
           a.account_type,
           bl.fixed_amount,
           bl.variable_rate
    INTO v_behavior,
         v_account_type,
         v_fixed,
         v_rate
    FROM budget_lines bl
    JOIN accounts a
      ON a.account_code = bl.account_code
    WHERE bl.budget_line_id = p_budget_line_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Budget line not found: %', p_budget_line_id;
    END IF;

    IF v_account_type <> 'EXPENSE' THEN
        RAISE EXCEPTION 'Flexible expense calculation requires expense account.';
    END IF;

    RETURN ROUND(
        CASE
            WHEN v_behavior = 'FIXED'
                THEN v_fixed
            WHEN v_behavior = 'VARIABLE'
                THEN v_rate * p_activity
            ELSE v_fixed + v_rate * p_activity
        END,
        2
    );
END;
$$;

CREATE OR REPLACE FUNCTION classify_variance(
    p_account_type account_type,
    p_variance NUMERIC
)
RETURNS variance_status
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_variance = 0
            THEN 'ON_TARGET'::variance_status

        WHEN p_account_type = 'REVENUE'
             AND p_variance > 0
            THEN 'FAVORABLE'::variance_status

        WHEN p_account_type = 'REVENUE'
             AND p_variance < 0
            THEN 'UNFAVORABLE'::variance_status

        WHEN p_account_type = 'EXPENSE'
             AND p_variance < 0
            THEN 'FAVORABLE'::variance_status

        ELSE 'UNFAVORABLE'::variance_status
    END;
$$;

-- ============================================================================
-- 9. AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION log_budget_status_change()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO budget_audit_log (
            budget_id,
            action,
            previous_status,
            new_status,
            event_details
        )
        VALUES (
            NEW.budget_id,
            'STATUS_CHANGE',
            OLD.status,
            NEW.status,
            jsonb_build_object(
                'budget_code', NEW.budget_code,
                'revision', NEW.revision_number
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_budget_status_audit
AFTER UPDATE OF status ON budgets
FOR EACH ROW
EXECUTE FUNCTION log_budget_status_change();

-- ============================================================================
-- 10. BUDGET LINE INTEGRITY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_budget_line_editability()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_budget_id BIGINT;
    v_status budget_status;
    v_account_type account_type;
BEGIN
    v_budget_id := COALESCE(NEW.budget_id, OLD.budget_id);

    SELECT status
    INTO v_status
    FROM budgets
    WHERE budget_id = v_budget_id
    FOR UPDATE;

    IF v_status <> 'DRAFT' THEN
        RAISE EXCEPTION
            'Budget lines can only be modified while the budget is in DRAFT status.';
    END IF;

    SELECT account_type
    INTO v_account_type
    FROM accounts
    WHERE account_code = COALESCE(
        NEW.account_code,
        OLD.account_code
    );

    IF v_account_type = 'REVENUE' THEN
        IF EXISTS (
            SELECT 1
            FROM accounts
            WHERE account_code = NEW.account_code
              AND cost_behavior <> 'FIXED'
        ) THEN
            RAISE EXCEPTION
                'Revenue lines must use fixed revenue planning.';
        END IF;
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_budget_line_integrity
BEFORE INSERT OR UPDATE OR DELETE ON budget_lines
FOR EACH ROW
EXECUTE FUNCTION enforce_budget_line_editability();

-- ============================================================================
-- 11. ACTUAL TRANSACTION INTEGRITY
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_actual_transaction()
RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_budget_status budget_status;
    v_line_budget BIGINT;
    v_fiscal_year INTEGER;
    v_transaction_year INTEGER;
BEGIN
    SELECT status, fiscal_year
    INTO v_budget_status, v_fiscal_year
    FROM budgets
    WHERE budget_id = NEW.budget_id
    FOR UPDATE;

    IF v_budget_status <> 'APPROVED' THEN
        RAISE EXCEPTION
            'Actual transactions require an approved budget.';
    END IF;

    SELECT budget_id
    INTO v_line_budget
    FROM budget_lines
    WHERE budget_line_id = NEW.budget_line_id;

    IF v_line_budget IS DISTINCT FROM NEW.budget_id THEN
        RAISE EXCEPTION
            'Actual transaction and budget line belong to different budgets.';
    END IF;

    SELECT fiscal_year
    INTO v_transaction_year
    FROM fiscal_periods
    WHERE period_id = NEW.period_id
      AND NEW.transaction_date BETWEEN start_date AND end_date;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Transaction date does not belong to the selected fiscal period.';
    END IF;

    IF v_transaction_year <> v_fiscal_year THEN
        RAISE EXCEPTION
            'Transaction fiscal year does not match budget fiscal year.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_actual_validation
BEFORE INSERT OR UPDATE ON actual_transactions
FOR EACH ROW
EXECUTE FUNCTION validate_actual_transaction();

-- ============================================================================
-- 12. BUDGET SUBMISSION AND APPROVAL PROCEDURES
-- ============================================================================

CREATE OR REPLACE PROCEDURE submit_budget(
    p_budget_id BIGINT,
    p_actor_id BIGINT
)
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_status budget_status;
    v_line_count INTEGER;
    v_budget_year INTEGER;
    v_department RECORD;
BEGIN
    SELECT status, fiscal_year
    INTO v_status, v_budget_year
    FROM budgets
    WHERE budget_id = p_budget_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Budget not found.';
    END IF;

    IF v_status <> 'DRAFT' THEN
        RAISE EXCEPTION 'Only draft budgets can be submitted.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = p_actor_id
          AND is_active
          AND employee_role IN (
              'DEPARTMENT_MANAGER',
              'FINANCE_MANAGER'
          )
    ) THEN
        RAISE EXCEPTION 'User is not authorized to submit budgets.';
    END IF;

    SELECT COUNT(*)
    INTO v_line_count
    FROM budget_lines
    WHERE budget_id = p_budget_id;

    IF v_line_count = 0 THEN
        RAISE EXCEPTION 'Budget cannot be empty.';
    END IF;

    FOR v_department IN
        SELECT
            d.department_id,
            d.annual_spending_limit,
            SUM(calculate_budget_amount(bl.budget_line_id))
                AS planned_expense
        FROM budget_lines bl
        JOIN departments d
          ON d.department_id = bl.department_id
        JOIN accounts a
          ON a.account_code = bl.account_code
        WHERE bl.budget_id = p_budget_id
          AND a.account_type = 'EXPENSE'
        GROUP BY
            d.department_id,
            d.annual_spending_limit
    LOOP
        IF v_department.planned_expense >
           v_department.annual_spending_limit THEN
            RAISE EXCEPTION
                'Department % exceeds annual spending limit.',
                v_department.department_id;
        END IF;
    END LOOP;

    UPDATE budgets
    SET status = 'SUBMITTED',
        submitted_at = CURRENT_TIMESTAMP
    WHERE budget_id = p_budget_id;
END;
$$;

CREATE OR REPLACE PROCEDURE approve_budget(
    p_budget_id BIGINT,
    p_approver_id BIGINT,
    p_comments TEXT DEFAULT NULL
)
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_status budget_status;
    v_role VARCHAR(40);
BEGIN
    SELECT status
    INTO v_status
    FROM budgets
    WHERE budget_id = p_budget_id
    FOR UPDATE;

    IF NOT FOUND OR v_status <> 'SUBMITTED' THEN
        RAISE EXCEPTION 'Budget is not awaiting approval.';
    END IF;

    SELECT employee_role
    INTO v_role
    FROM employees
    WHERE employee_id = p_approver_id
      AND is_active;

    IF v_role NOT IN ('FINANCE_CONTROLLER', 'CFO') THEN
        RAISE EXCEPTION 'Approver lacks approval authority.';
    END IF;

    INSERT INTO budget_approvals (
        budget_id,
        approver_id,
        decision,
        comments
    )
    VALUES (
        p_budget_id,
        p_approver_id,
        'APPROVED',
        p_comments
    );

    UPDATE budgets
    SET status = 'APPROVED',
        approved_at = CURRENT_TIMESTAMP
    WHERE budget_id = p_budget_id;
END;
$$;

CREATE OR REPLACE PROCEDURE reject_budget(
    p_budget_id BIGINT,
    p_approver_id BIGINT,
    p_reason TEXT
)
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_status budget_status;
    v_role VARCHAR(40);
BEGIN
    IF p_reason IS NULL OR LENGTH(TRIM(p_reason)) = 0 THEN
        RAISE EXCEPTION 'Rejection reason is required.';
    END IF;

    SELECT status
    INTO v_status
    FROM budgets
    WHERE budget_id = p_budget_id
    FOR UPDATE;

    IF NOT FOUND OR v_status <> 'SUBMITTED' THEN
        RAISE EXCEPTION 'Budget is not awaiting approval.';
    END IF;

    SELECT employee_role
    INTO v_role
    FROM employees
    WHERE employee_id = p_approver_id
      AND is_active;

    IF v_role NOT IN ('FINANCE_CONTROLLER', 'CFO') THEN
        RAISE EXCEPTION 'User cannot reject budgets.';
    END IF;

    INSERT INTO budget_approvals (
        budget_id,
        approver_id,
        decision,
        comments
    )
    VALUES (
        p_budget_id,
        p_approver_id,
        'REJECTED',
        p_reason
    );

    UPDATE budgets
    SET status = 'REJECTED'
    WHERE budget_id = p_budget_id;
END;
$$;

-- ============================================================================
-- 13. REPORTING VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW v_budget_line_details AS
SELECT
    b.budget_id,
    b.budget_code,
    b.fiscal_year,
    b.status,
    b.revision_number,
    d.department_id,
    d.department_name,
    a.account_code,
    a.account_name,
    a.account_type,
    a.cost_behavior,
    bl.budget_line_id,
    bl.fixed_amount,
    bl.variable_rate,
    bl.planned_activity,
    calculate_budget_amount(bl.budget_line_id)
        AS planned_amount
FROM budgets b
JOIN budget_lines bl
  ON bl.budget_id = b.budget_id
JOIN departments d
  ON d.department_id = bl.department_id
JOIN accounts a
  ON a.account_code = bl.account_code;

CREATE OR REPLACE VIEW v_actual_summary AS
SELECT
    at.budget_id,
    at.budget_line_id,
    at.period_id,
    SUM(at.amount)::NUMERIC(18,2) AS actual_amount,
    SUM(at.activity_units)::NUMERIC(18,2) AS actual_activity,
    COUNT(*) AS transaction_count
FROM actual_transactions at
GROUP BY
    at.budget_id,
    at.budget_line_id,
    at.period_id;

CREATE OR REPLACE VIEW v_annual_variance AS
SELECT
    bd.budget_id,
    bd.budget_code,
    bd.fiscal_year,
    bd.department_id,
    bd.department_name,
    bd.account_code,
    bd.account_name,
    bd.account_type,
    bd.planned_amount AS budget_amount,
    COALESCE(actual.total_actual, 0)::NUMERIC(18,2)
        AS actual_amount,

    (
        COALESCE(actual.total_actual, 0) -
        bd.planned_amount
    )::NUMERIC(18,2) AS variance_amount,

    CASE
        WHEN bd.planned_amount = 0 THEN 0
        ELSE ROUND(
            (
                COALESCE(actual.total_actual, 0) -
                bd.planned_amount
            ) / bd.planned_amount * 100,
            2
        )
    END AS variance_percentage,

    classify_variance(
        bd.account_type,
        COALESCE(actual.total_actual, 0) -
        bd.planned_amount
    ) AS variance_classification

FROM v_budget_line_details bd

LEFT JOIN LATERAL (
    SELECT SUM(at.amount) AS total_actual
    FROM actual_transactions at
    WHERE at.budget_id = bd.budget_id
      AND at.budget_line_id = bd.budget_line_id
) actual ON TRUE

WHERE bd.status IN ('APPROVED', 'CLOSED');

CREATE OR REPLACE VIEW v_department_budget_summary AS
SELECT
    budget_id,
    budget_code,
    fiscal_year,
    department_id,
    department_name,

    SUM(
        CASE WHEN account_type = 'REVENUE'
            THEN budget_amount ELSE 0 END
    ) AS planned_revenue,

    SUM(
        CASE WHEN account_type = 'EXPENSE'
            THEN budget_amount ELSE 0 END
    ) AS planned_expenses,

    SUM(
        CASE WHEN account_type = 'REVENUE'
            THEN actual_amount ELSE 0 END
    ) AS actual_revenue,

    SUM(
        CASE WHEN account_type = 'EXPENSE'
            THEN actual_amount ELSE 0 END
    ) AS actual_expenses,

    SUM(
        CASE WHEN account_type = 'REVENUE'
            THEN budget_amount ELSE -budget_amount END
    ) AS planned_contribution

FROM v_annual_variance
GROUP BY
    budget_id,
    budget_code,
    fiscal_year,
    department_id,
    department_name;

-- ============================================================================
-- 14. MONTHLY VARIANCE REPORTING
-- ============================================================================

CREATE OR REPLACE FUNCTION monthly_variance_report(
    p_budget_id BIGINT,
    p_period_number SMALLINT
)
RETURNS TABLE (
    department_id VARCHAR,
    account_code VARCHAR,
    account_name VARCHAR,
    account_type account_type,
    monthly_budget NUMERIC,
    actual_amount NUMERIC,
    variance_amount NUMERIC,
    variance_percentage NUMERIC,
    classification variance_status
)
LANGUAGE PLPGSQL
STABLE
AS $$
BEGIN
    IF p_period_number NOT BETWEEN 1 AND 12 THEN
        RAISE EXCEPTION 'Period must be between 1 and 12.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM budgets
        WHERE budget_id = p_budget_id
          AND status IN ('APPROVED', 'CLOSED')
    ) THEN
        RAISE EXCEPTION 'Approved budget not found.';
    END IF;

    RETURN QUERY
    SELECT
        bd.department_id::VARCHAR,
        bd.account_code::VARCHAR,
        bd.account_name::VARCHAR,
        bd.account_type,

        ROUND(bd.planned_amount / 12, 2)::NUMERIC
            AS monthly_budget,

        COALESCE(actual.actual_amount, 0)::NUMERIC
            AS actual_amount,

        (
            COALESCE(actual.actual_amount, 0) -
            ROUND(bd.planned_amount / 12, 2)
        )::NUMERIC AS variance_amount,

        CASE
            WHEN ROUND(bd.planned_amount / 12, 2) = 0
                THEN 0::NUMERIC
            ELSE ROUND(
                (
                    COALESCE(actual.actual_amount, 0) -
                    ROUND(bd.planned_amount / 12, 2)
                ) / ROUND(bd.planned_amount / 12, 2) * 100,
                2
            )
        END::NUMERIC AS variance_percentage,

        classify_variance(
            bd.account_type,
            COALESCE(actual.actual_amount, 0) -
            ROUND(bd.planned_amount / 12, 2)
        ) AS classification

    FROM v_budget_line_details bd

    LEFT JOIN LATERAL (
        SELECT SUM(at.amount) AS actual_amount
        FROM actual_transactions at
        JOIN fiscal_periods fp
          ON fp.period_id = at.period_id
        WHERE at.budget_id = bd.budget_id
          AND at.budget_line_id = bd.budget_line_id
          AND fp.period_number = p_period_number
    ) actual ON TRUE

    WHERE bd.budget_id = p_budget_id;
END;
$$;

-- ============================================================================
-- 15. FLEXIBLE BUDGET VARIANCE
-- ============================================================================

CREATE OR REPLACE FUNCTION flexible_variance_report(
    p_budget_id BIGINT,
    p_period_id BIGINT
)
RETURNS TABLE (
    department_id VARCHAR,
    account_code VARCHAR,
    planned_activity NUMERIC,
    actual_activity NUMERIC,
    flexible_budget NUMERIC,
    actual_expense NUMERIC,
    spending_variance NUMERIC,
    classification variance_status
)
LANGUAGE PLPGSQL
STABLE
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM budgets
        WHERE budget_id = p_budget_id
          AND status IN ('APPROVED', 'CLOSED')
    ) THEN
        RAISE EXCEPTION 'Approved budget required.';
    END IF;

    RETURN QUERY
    SELECT
        bd.department_id::VARCHAR,
        bd.account_code::VARCHAR,
        bd.planned_activity,

        COALESCE(actual.actual_activity, 0)::NUMERIC,

        calculate_flexible_budget(
            bd.budget_line_id,
            COALESCE(actual.actual_activity, 0)
        )::NUMERIC,

        COALESCE(actual.actual_amount, 0)::NUMERIC,

        (
            COALESCE(actual.actual_amount, 0) -
            calculate_flexible_budget(
                bd.budget_line_id,
                COALESCE(actual.actual_activity, 0)
            )
        )::NUMERIC,

        classify_variance(
            'EXPENSE',
            COALESCE(actual.actual_amount, 0) -
            calculate_flexible_budget(
                bd.budget_line_id,
                COALESCE(actual.actual_activity, 0)
            )
        )

    FROM v_budget_line_details bd

    LEFT JOIN LATERAL (
        SELECT
            SUM(at.amount) AS actual_amount,
            SUM(at.activity_units) AS actual_activity
        FROM actual_transactions at
        WHERE at.budget_id = bd.budget_id
          AND at.budget_line_id = bd.budget_line_id
          AND at.period_id = p_period_id
    ) actual ON TRUE

    WHERE bd.budget_id = p_budget_id
      AND bd.account_type = 'EXPENSE';
END;
$$;

-- ============================================================================
-- 16. BUDGET UTILIZATION
-- ============================================================================

CREATE OR REPLACE VIEW v_budget_utilization AS
SELECT
    budget_id,
    budget_code,
    fiscal_year,
    department_id,
    department_name,
    account_code,
    account_name,
    budget_amount,
    actual_amount,

    CASE
        WHEN budget_amount = 0 THEN NULL
        ELSE ROUND(
            actual_amount / budget_amount * 100,
            2
        )
    END AS utilization_percentage,

    CASE
        WHEN budget_amount = 0 AND actual_amount > 0
            THEN 'UNBUDGETED_SPENDING'
        WHEN budget_amount = 0
            THEN 'NO_ALLOCATION'
        WHEN actual_amount > budget_amount
            THEN 'OVER_BUDGET'
        ELSE 'WITHIN_BUDGET'
    END AS utilization_status

FROM v_annual_variance
WHERE account_type = 'EXPENSE';

-- ============================================================================
-- 17. ROLLING FORECAST PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE create_run_rate_forecast(
    p_budget_id BIGINT,
    p_actor_id BIGINT,
    p_elapsed_periods INTEGER
)
LANGUAGE PLPGSQL
AS $$
DECLARE
    v_line RECORD;
    v_ytd NUMERIC(18,2);
    v_forecast NUMERIC(18,2);
    v_remaining INTEGER;
BEGIN
    IF p_elapsed_periods NOT BETWEEN 1 AND 12 THEN
        RAISE EXCEPTION 'Elapsed periods must be 1 through 12.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM budgets
        WHERE budget_id = p_budget_id
          AND status = 'APPROVED'
    ) THEN
        RAISE EXCEPTION 'Approved budget required.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM employees
        WHERE employee_id = p_actor_id
          AND is_active
          AND employee_role IN (
              'FINANCE_MANAGER',
              'FINANCE_CONTROLLER',
              'CFO'
          )
    ) THEN
        RAISE EXCEPTION 'Forecast creation is not authorized.';
    END IF;

    v_remaining := 12 - p_elapsed_periods;

    FOR v_line IN
        SELECT budget_line_id
        FROM budget_lines
        WHERE budget_id = p_budget_id
    LOOP
        SELECT COALESCE(SUM(at.amount), 0)
        INTO v_ytd
        FROM actual_transactions at
        JOIN fiscal_periods fp
          ON fp.period_id = at.period_id
        WHERE at.budget_id = p_budget_id
          AND at.budget_line_id = v_line.budget_line_id
          AND fp.period_number <= p_elapsed_periods;

        v_forecast := ROUND(
            v_ytd * 12 / p_elapsed_periods,
            2
        );

        -- Store one run-rate forecast for the last fiscal period.
        INSERT INTO budget_forecasts (
            budget_id,
            period_id,
            budget_line_id,
            forecast_amount,
            forecast_method,
            created_by
        )
        SELECT
            p_budget_id,
            fp.period_id,
            v_line.budget_line_id,
            v_forecast,
            'YTD_RUN_RATE',
            p_actor_id
        FROM fiscal_periods fp
        JOIN budgets b
          ON b.fiscal_year = fp.fiscal_year
        WHERE b.budget_id = p_budget_id
          AND fp.period_number = 12
        ON CONFLICT (
            budget_id,
            period_id,
            budget_line_id,
            forecast_method
        )
        DO UPDATE SET
            forecast_amount = EXCLUDED.forecast_amount,
            created_by = EXCLUDED.created_by,
            created_at = CURRENT_TIMESTAMP;
    END LOOP;
END;
$$;

-- ============================================================================
-- 18. SAMPLE MASTER RECORDS
-- ============================================================================

INSERT INTO departments (
    department_id,
    department_name,
    annual_spending_limit
)
VALUES
    ('FIN', 'Finance', 500000),
    ('OPS', 'Operations', 900000),
    ('IT', 'Information Technology', 600000);

INSERT INTO employees (
    employee_name,
    email,
    employee_role,
    department_id
)
VALUES
    (
        'Finance Manager',
        'finance.manager@example.org',
        'FINANCE_MANAGER',
        'FIN'
    ),
    (
        'Operations Manager',
        'operations.manager@example.org',
        'DEPARTMENT_MANAGER',
        'OPS'
    ),
    (
        'Finance Controller',
        'controller@example.org',
        'FINANCE_CONTROLLER',
        'FIN'
    ),
    (
        'Chief Financial Officer',
        'cfo@example.org',
        'CFO',
        'FIN'
    ),
    (
        'Finance Auditor',
        'auditor@example.org',
        'AUDITOR',
        'FIN'
    );

INSERT INTO accounts (
    account_code,
    account_name,
    account_type,
    cost_behavior
)
VALUES
    ('REV001', 'Service Revenue', 'REVENUE', 'FIXED'),
    ('EXP001', 'Employee Salaries', 'EXPENSE', 'FIXED'),
    ('EXP002', 'Production Materials', 'EXPENSE', 'VARIABLE'),
    ('EXP003', 'IT Infrastructure', 'EXPENSE', 'MIXED'),
    ('EXP004', 'Office Utilities', 'EXPENSE', 'VARIABLE');

-- Twelve monthly periods for fiscal year 2027.
INSERT INTO fiscal_periods (
    fiscal_year,
    period_number,
    start_date,
    end_date
)
SELECT
    2027,
    month_number,
    MAKE_DATE(2027, month_number, 1),
    (MAKE_DATE(2027, month_number, 1)
        + INTERVAL '1 month - 1 day')::DATE
FROM GENERATE_SERIES(1, 12) AS month_number;

-- ============================================================================
-- 19. SAMPLE BUDGET
-- ============================================================================

INSERT INTO budgets (
    budget_code,
    fiscal_year,
    budget_name,
    budget_type,
    created_by
)
VALUES (
    'BUDGET-2027',
    2027,
    'Annual Operating Budget',
    'FLEXIBLE',
    1
);

INSERT INTO budget_lines (
    budget_id,
    account_code,
    department_id,
    fixed_amount,
    variable_rate,
    planned_activity
)
SELECT
    b.budget_id,
    sample.account_code,
    sample.department_id,
    sample.fixed_amount,
    sample.variable_rate,
    sample.planned_activity
FROM budgets b
CROSS JOIN (
    VALUES
        (
            'REV001',
            'FIN',
            3000000::NUMERIC,
            0::NUMERIC,
            0::NUMERIC
        ),
        (
            'EXP001',
            'FIN',
            360000::NUMERIC,
            0::NUMERIC,
            0::NUMERIC
        ),
        (
            'EXP002',
            'OPS',
            0::NUMERIC,
            120::NUMERIC,
            5000::NUMERIC
        ),
        (
            'EXP003',
            'IT',
            180000::NUMERIC,
            20::NUMERIC,
            5000::NUMERIC
        )
) AS sample(
    account_code,
    department_id,
    fixed_amount,
    variable_rate,
    planned_activity
)
WHERE b.budget_code = 'BUDGET-2027';

-- ============================================================================
-- 20. SUBMISSION AND APPROVAL
-- ============================================================================

CALL submit_budget(1, 2);

CALL approve_budget(
    1,
    3,
    'Annual operating budget reviewed and approved.'
);

-- ============================================================================
-- 21. ACTUAL TRANSACTION RECORDS
-- ============================================================================

INSERT INTO actual_transactions (
    transaction_reference,
    budget_id,
    budget_line_id,
    period_id,
    transaction_date,
    amount,
    activity_units,
    description,
    entered_by
)
SELECT
    sample.reference,
    b.budget_id,
    bl.budget_line_id,
    fp.period_id,
    sample.transaction_date,
    sample.amount,
    sample.activity_units,
    sample.description,
    1
FROM budgets b
JOIN (
    VALUES
        (
            'TX001',
            'REV001',
            'FIN',
            DATE '2027-04-15',
            280000::NUMERIC,
            0::NUMERIC,
            'April service revenue'
        ),
        (
            'TX002',
            'EXP001',
            'FIN',
            DATE '2027-04-20',
            30000::NUMERIC,
            0::NUMERIC,
            'April employee salaries'
        ),
        (
            'TX003',
            'EXP002',
            'OPS',
            DATE '2027-04-21',
            55000::NUMERIC,
            450::NUMERIC,
            'April production materials'
        ),
        (
            'TX004',
            'EXP003',
            'IT',
            DATE '2027-04-25',
            19000::NUMERIC,
            500::NUMERIC,
            'April infrastructure'
        )
) AS sample(
    reference,
    account_code,
    department_id,
    transaction_date,
    amount,
    activity_units,
    description
)
ON b.budget_code = 'BUDGET-2027'

JOIN budget_lines bl
  ON bl.budget_id = b.budget_id
 AND bl.account_code = sample.account_code
 AND bl.department_id = sample.department_id

JOIN fiscal_periods fp
  ON fp.fiscal_year = b.fiscal_year
 AND fp.period_number = 1;

-- ============================================================================
-- 22. REPORTING QUERIES
-- ============================================================================

-- Query A: Annual budget and actual variance.
SELECT *
FROM v_annual_variance
WHERE budget_code = 'BUDGET-2027'
ORDER BY department_id, account_code;

-- Query B: Monthly budget comparison.
SELECT *
FROM monthly_variance_report(1, 1)
ORDER BY department_id, account_code;

-- Query C: Flexible budget evaluation.
SELECT *
FROM flexible_variance_report(1, 1)
ORDER BY department_id, account_code;

-- Query D: Department-level reporting.
SELECT *
FROM v_department_budget_summary
ORDER BY department_id;

-- Query E: Budget utilization.
SELECT *
FROM v_budget_utilization
ORDER BY department_id, account_code;

-- Query F: Favorable and unfavorable variance counts.
SELECT
    variance_classification,
    COUNT(*) AS account_count,
    SUM(ABS(variance_amount)) AS total_absolute_variance
FROM v_annual_variance
GROUP BY variance_classification
ORDER BY variance_classification;

-- Query G: Budget expenditure CTE.
WITH department_actuals AS (
    SELECT
        bd.department_id,
        bd.department_name,
        SUM(bd.budget_amount) AS annual_budget,
        SUM(bd.actual_amount) AS actual_spending
    FROM v_annual_variance bd
    WHERE bd.account_type = 'EXPENSE'
    GROUP BY
        bd.department_id,
        bd.department_name
)
SELECT
    department_id,
    department_name,
    annual_budget,
    actual_spending,
    actual_spending - annual_budget AS spending_variance,
    CASE
        WHEN annual_budget = 0 THEN NULL
        ELSE ROUND(actual_spending / annual_budget * 100, 2)
    END AS utilization_percentage
FROM department_actuals
ORDER BY utilization_percentage DESC NULLS LAST;

-- Query H: Approval history.
SELECT
    b.budget_code,
    e.employee_name,
    e.employee_role,
    ba.decision,
    ba.comments,
    ba.decided_at
FROM budget_approvals ba
JOIN budgets b
  ON b.budget_id = ba.budget_id
JOIN employees e
  ON e.employee_id = ba.approver_id
ORDER BY ba.decided_at;

-- Query I: Audit history.
SELECT
    b.budget_code,
    al.action,
    al.previous_status,
    al.new_status,
    al.event_details,
    al.event_time
FROM budget_audit_log al
JOIN budgets b
  ON b.budget_id = al.budget_id
ORDER BY al.event_time;

-- ============================================================================
-- 23. ROLLING FORECAST EXAMPLE
-- ============================================================================

CALL create_run_rate_forecast(
    1,
    1,
    1
);

SELECT
    b.budget_code,
    bl.account_code,
    bf.forecast_method,
    bf.forecast_amount,
    bf.created_at
FROM budget_forecasts bf
JOIN budgets b
  ON b.budget_id = bf.budget_id
JOIN budget_lines bl
  ON bl.budget_line_id = bf.budget_line_id
WHERE b.budget_code = 'BUDGET-2027';

-- ============================================================================
-- 24. VALIDATION EXAMPLES
-- ============================================================================

-- A transaction with an incorrect budget-line relationship is rejected
-- by trg_actual_validation.
--
-- A transaction against a draft or rejected budget is rejected.
--
-- A budget exceeding department limits cannot be submitted.
--
-- Duplicate transaction references are rejected by the unique constraint.
--
-- A second approval from the same approver is rejected.
--
-- Budget lines cannot be edited after submission.

-- ============================================================================
-- 25. TRANSACTIONAL EXAMPLE
-- ============================================================================

-- Demonstrates atomic forecast recalculation.
-- The changes are committed together.

SAVEPOINT before_forecast_refresh;

UPDATE budget_forecasts
SET created_at = CURRENT_TIMESTAMP
WHERE budget_id = 1
  AND forecast_method = 'YTD_RUN_RATE';

-- In a production workflow, validation should run before COMMIT.
-- This demonstration retains the forecast records.

COMMIT;

-- ============================================================================
-- 26. OPERATIONAL QUERY EXAMPLES
-- ============================================================================

-- Locate the largest unfavorable expense variances.
SELECT
    department_name,
    account_code,
    account_name,
    budget_amount,
    actual_amount,
    variance_amount,
    variance_percentage
FROM v_annual_variance
WHERE account_type = 'EXPENSE'
  AND variance_classification = 'UNFAVORABLE'
ORDER BY variance_amount DESC;

-- Identify unbudgeted expenditure.
SELECT *
FROM v_budget_utilization
WHERE utilization_status = 'UNBUDGETED_SPENDING';

-- Review departments with expenditure above their budget.
SELECT
    department_id,
    department_name,
    SUM(budget_amount) AS budgeted_amount,
    SUM(actual_amount) AS actual_amount
FROM v_annual_variance
WHERE account_type = 'EXPENSE'
GROUP BY department_id, department_name
HAVING SUM(actual_amount) > SUM(budget_amount);

-- Inspect active budget approval requirements and outcomes.
SELECT
    b.budget_code,
    b.status,
    COUNT(ba.approval_id) AS approval_records,
    COUNT(*) FILTER (
        WHERE ba.decision = 'APPROVED'
    ) AS approvals,
    COUNT(*) FILTER (
        WHERE ba.decision = 'REJECTED'
    ) AS rejections
FROM budgets b
LEFT JOIN budget_approvals ba
  ON ba.budget_id = b.budget_id
GROUP BY b.budget_code, b.status;

-- ============================================================================
-- END OF BUDGETING DATABASE
-- ============================================================================
