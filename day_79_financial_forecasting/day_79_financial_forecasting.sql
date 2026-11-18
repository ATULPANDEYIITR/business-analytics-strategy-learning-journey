/*
 * FINANCIAL FORECASTING DATABASE
 *
 * PostgreSQL 15+
 *
 * Covers:
 * - Financial entities and reporting periods
 * - Revenue, expense and cash-flow records
 * - Revenue and expense categories
 * - Historical financial observations
 * - Forecast versions and scenarios
 * - Forecast assumptions
 * - Budget allocation and variance
 * - Cash-flow projections
 * - Financial validation
 * - Scenario comparisons
 * - Forecast audit history
 * - Forecast approval and access governance
 *
 * Monetary amounts use NUMERIC, not floating-point types.
 *
 * Execute using psql:
 *   psql -v ON_ERROR_STOP=1 -d financial_db -f financial_forecasting.sql
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS finance;

SET search_path TO finance, public;

CREATE TABLE IF NOT EXISTS organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT organization_name_unique
        UNIQUE (organization_name),

    CONSTRAINT currency_code_valid
        CHECK (currency_code ~ '^[A-Z]{3}$')
);

CREATE TABLE IF NOT EXISTS financial_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    period_status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    CONSTRAINT valid_period_dates
        CHECK (period_end >= period_start),

    CONSTRAINT valid_period_status
        CHECK (
            period_status IN (
                'OPEN',
                'CLOSED',
                'LOCKED'
            )
        ),

    CONSTRAINT unique_organization_period
        UNIQUE (organization_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS financial_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    category_name VARCHAR(120) NOT NULL,

    category_type VARCHAR(20) NOT NULL,

    is_recurring BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT category_type_valid
        CHECK (
            category_type IN (
                'REVENUE',
                'OPERATING_EXPENSE',
                'INVESTING_EXPENSE',
                'FINANCING'
            )
        ),

    CONSTRAINT unique_category
        UNIQUE (
            organization_id,
            category_name,
            category_type
        )
);

CREATE TABLE IF NOT EXISTS financial_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    period_id BIGINT NOT NULL
        REFERENCES financial_periods(period_id),

    category_id BIGINT NOT NULL
        REFERENCES financial_categories(category_id),

    amount NUMERIC(18,2) NOT NULL,

    transaction_reference VARCHAR(100),

    source_type VARCHAR(30) NOT NULL DEFAULT 'ACTUAL',

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    recorded_by VARCHAR(120) NOT NULL,

    CONSTRAINT observation_amount_nonnegative
        CHECK (amount >= 0),

    CONSTRAINT source_type_valid
        CHECK (
            source_type IN (
                'ACTUAL',
                'ADJUSTMENT',
                'ACCRUAL'
            )
        ),

    CONSTRAINT transaction_reference_unique
        UNIQUE (organization_id, transaction_reference)
);

CREATE INDEX IF NOT EXISTS idx_observations_period
    ON financial_observations (
        organization_id,
        period_id
    );

CREATE INDEX IF NOT EXISTS idx_observations_category_period
    ON financial_observations (
        category_id,
        period_id
    );

CREATE TABLE IF NOT EXISTS cash_balances (
    cash_balance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    period_id BIGINT NOT NULL
        REFERENCES financial_periods(period_id),

    opening_cash NUMERIC(18,2) NOT NULL,
    closing_cash NUMERIC(18,2) NOT NULL,

    verified BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT cash_opening_nonnegative
        CHECK (opening_cash >= 0),

    CONSTRAINT unique_cash_period
        UNIQUE (organization_id, period_id)
);

CREATE TABLE IF NOT EXISTS forecast_runs (
    forecast_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    forecast_name VARCHAR(150) NOT NULL,

    scenario VARCHAR(20) NOT NULL,

    forecast_status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    historical_cutoff DATE NOT NULL,

    forecast_horizon INTEGER NOT NULL,

    moving_average_window INTEGER NOT NULL DEFAULT 3,

    source_revision BIGINT NOT NULL DEFAULT 1,

    created_by VARCHAR(120) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    approved_by VARCHAR(120),

    approved_at TIMESTAMPTZ,

    CONSTRAINT scenario_valid
        CHECK (
            scenario IN (
                'BASE',
                'OPTIMISTIC',
                'PESSIMISTIC',
                'STRESS'
            )
        ),

    CONSTRAINT forecast_status_valid
        CHECK (
            forecast_status IN (
                'DRAFT',
                'CALCULATED',
                'UNDER_REVIEW',
                'APPROVED',
                'REJECTED',
                'SUPERSEDED'
            )
        ),

    CONSTRAINT forecast_horizon_valid
        CHECK (forecast_horizon BETWEEN 1 AND 120),

    CONSTRAINT moving_average_valid
        CHECK (moving_average_window BETWEEN 1 AND 120),

    CONSTRAINT approval_fields_consistent
        CHECK (
            (
                forecast_status = 'APPROVED'
                AND approved_by IS NOT NULL
                AND approved_at IS NOT NULL
            )
            OR
            (
                forecast_status <> 'APPROVED'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_forecast_organization_status
    ON forecast_runs (
        organization_id,
        forecast_status,
        created_at DESC
    );

CREATE TABLE IF NOT EXISTS forecast_assumptions (
    assumption_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    forecast_id BIGINT NOT NULL
        REFERENCES forecast_runs(forecast_id)
        ON DELETE CASCADE,

    assumption_name VARCHAR(100) NOT NULL,

    assumption_value NUMERIC(14,6) NOT NULL,

    description TEXT,

    CONSTRAINT assumption_name_unique
        UNIQUE (forecast_id, assumption_name),

    CONSTRAINT assumption_value_finite_range
        CHECK (
            assumption_value BETWEEN -0.95 AND 10
        )
);

CREATE TABLE IF NOT EXISTS forecast_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    forecast_id BIGINT NOT NULL
        REFERENCES forecast_runs(forecast_id)
        ON DELETE CASCADE,

    forecast_period DATE NOT NULL,

    revenue NUMERIC(18,2) NOT NULL,

    operating_expenses NUMERIC(18,2) NOT NULL,

    investing_expenses NUMERIC(18,2) NOT NULL,

    financing_cash_flow NUMERIC(18,2) NOT NULL DEFAULT 0,

    operating_profit NUMERIC(18,2)
        GENERATED ALWAYS AS (
            revenue - operating_expenses
        ) STORED,

    net_cash_flow NUMERIC(18,2)
        GENERATED ALWAYS AS (
            revenue
            - operating_expenses
            - investing_expenses
            + financing_cash_flow
        ) STORED,

    opening_cash NUMERIC(18,2) NOT NULL,

    closing_cash NUMERIC(18,2) NOT NULL,

    profit_margin NUMERIC(12,6),

    cash_status VARCHAR(20) NOT NULL,

    CONSTRAINT forecast_result_unique
        UNIQUE (forecast_id, forecast_period),

    CONSTRAINT result_amounts_valid
        CHECK (
            revenue >= 0
            AND operating_expenses >= 0
            AND investing_expenses >= 0
            AND opening_cash >= 0
        ),

    CONSTRAINT profit_margin_valid
        CHECK (
            profit_margin IS NULL
            OR profit_margin BETWEEN -100 AND 1
        ),

    CONSTRAINT cash_status_valid
        CHECK (
            cash_status IN (
                'HEALTHY',
                'LOW_CASH',
                'NEGATIVE_CASH'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_forecast_results_period
    ON forecast_results (
        forecast_period,
        forecast_id
    );

CREATE TABLE IF NOT EXISTS budgets (
    budget_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    category_id BIGINT NOT NULL
        REFERENCES financial_categories(category_id),

    period_id BIGINT NOT NULL
        REFERENCES financial_periods(period_id),

    budget_amount NUMERIC(18,2) NOT NULL,

    budget_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    created_by VARCHAR(120) NOT NULL,

    CONSTRAINT budget_amount_nonnegative
        CHECK (budget_amount >= 0),

    CONSTRAINT budget_status_valid
        CHECK (
            budget_status IN (
                'ACTIVE',
                'REVISED',
                'CLOSED'
            )
        ),

    CONSTRAINT unique_category_budget
        UNIQUE (organization_id, category_id, period_id)
);

CREATE TABLE IF NOT EXISTS forecast_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    forecast_id BIGINT
        REFERENCES forecast_runs(forecast_id),

    event_type VARCHAR(50) NOT NULL,

    actor VARCHAR(120) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forecast_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    forecast_id BIGINT NOT NULL
        REFERENCES forecast_runs(forecast_id),

    reviewer VARCHAR(120) NOT NULL,

    approval_status VARCHAR(20) NOT NULL,

    comments TEXT,

    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT approval_status_valid
        CHECK (
            approval_status IN (
                'APPROVED',
                'REJECTED',
                'CHANGES_REQUESTED'
            )
        ),

    CONSTRAINT unique_forecast_reviewer
        UNIQUE (forecast_id, reviewer)
);


/* ---------------------------------------------------------
   ORGANIZATION AND CATEGORY INTEGRITY
   --------------------------------------------------------- */

CREATE OR REPLACE FUNCTION finance.validate_observation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    period_org BIGINT;
    category_org BIGINT;
    category_type_value VARCHAR(20);
    period_status_value VARCHAR(20);
BEGIN
    SELECT organization_id, period_status
    INTO period_org, period_status_value
    FROM financial_periods
    WHERE period_id = NEW.period_id;

    SELECT organization_id, category_type
    INTO category_org, category_type_value
    FROM financial_categories
    WHERE category_id = NEW.category_id;

    IF period_org IS NULL OR category_org IS NULL THEN
        RAISE EXCEPTION
            'Observation references an invalid period or category.';
    END IF;

    IF NEW.organization_id <> period_org
       OR NEW.organization_id <> category_org THEN
        RAISE EXCEPTION
            'Observation organization does not match its references.';
    END IF;

    IF period_status_value <> 'OPEN' THEN
        RAISE EXCEPTION
            'Financial observations can only be added to OPEN periods.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_observation
ON financial_observations;

CREATE TRIGGER trg_validate_observation
BEFORE INSERT OR UPDATE
ON financial_observations
FOR EACH ROW
EXECUTE FUNCTION finance.validate_observation();


/* ---------------------------------------------------------
   FORECAST RESULT VALIDATION
   --------------------------------------------------------- */

CREATE OR REPLACE FUNCTION finance.validate_forecast_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    previous_cash NUMERIC(18,2);
    expected_cash NUMERIC(18,2);
    previous_period DATE;
    run_status VARCHAR(20);
    result_count INTEGER;
BEGIN
    SELECT forecast_status
    INTO run_status
    FROM forecast_runs
    WHERE forecast_id = NEW.forecast_id
    FOR UPDATE;

    IF run_status NOT IN ('DRAFT', 'CALCULATED') THEN
        RAISE EXCEPTION
            'Results cannot be changed after forecast review begins.';
    END IF;

    IF NEW.revenue < 0
       OR NEW.operating_expenses < 0
       OR NEW.investing_expenses < 0
       OR NEW.opening_cash < 0 THEN
        RAISE EXCEPTION
            'Forecast monetary inputs cannot be negative.';
    END IF;

    expected_cash :=
        NEW.opening_cash
        + NEW.net_cash_flow;

    IF ABS(NEW.closing_cash - expected_cash) > 0.01 THEN
        RAISE EXCEPTION
            'Cash reconciliation failed. Expected %, received %.',
            expected_cash,
            NEW.closing_cash;
    END IF;

    IF NEW.profit_margin IS NOT NULL
       AND NEW.revenue > 0
       AND ABS(
           NEW.profit_margin -
           NEW.operating_profit / NEW.revenue
       ) > 0.000001 THEN
        RAISE EXCEPTION
            'Profit margin does not reconcile with revenue and profit.';
    END IF;

    IF NEW.revenue = 0 AND NEW.profit_margin IS NOT NULL THEN
        RAISE EXCEPTION
            'Profit margin must be NULL when revenue is zero.';
    END IF;

    IF NEW.closing_cash < 0
       AND NEW.cash_status <> 'NEGATIVE_CASH' THEN
        RAISE EXCEPTION
            'Negative closing cash requires NEGATIVE_CASH status.';
    END IF;

    IF NEW.closing_cash >= 0
       AND NEW.cash_status = 'NEGATIVE_CASH' THEN
        RAISE EXCEPTION
            'Cash status conflicts with closing cash.';
    END IF;

    SELECT COUNT(*), MAX(forecast_period)
    INTO result_count, previous_period
    FROM forecast_results
    WHERE forecast_id = NEW.forecast_id
      AND forecast_period < NEW.forecast_period;

    IF result_count > 0 THEN
        SELECT closing_cash
        INTO previous_cash
        FROM forecast_results
        WHERE forecast_id = NEW.forecast_id
          AND forecast_period = previous_period;

        IF NEW.opening_cash <> previous_cash THEN
            RAISE EXCEPTION
                'Opening cash does not match preceding closing cash.';
        END IF;

        IF NEW.forecast_period <> (
            previous_period + INTERVAL '1 month'
        )::DATE THEN
            RAISE EXCEPTION
                'Forecast periods must be consecutive.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_forecast_result
ON forecast_results;

CREATE TRIGGER trg_validate_forecast_result
BEFORE INSERT OR UPDATE
ON forecast_results
FOR EACH ROW
EXECUTE FUNCTION finance.validate_forecast_result();


/* ---------------------------------------------------------
   AUDIT EVENT TRIGGER
   --------------------------------------------------------- */

CREATE OR REPLACE FUNCTION finance.audit_forecast_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    event_action VARCHAR(50);
    target_id BIGINT;
    actor_name VARCHAR(120);
BEGIN
    IF TG_OP = 'INSERT' THEN
        event_action := 'CREATED';
        target_id := NEW.forecast_id;
        actor_name := NEW.created_by;

    ELSIF TG_OP = 'UPDATE' THEN
        event_action := 'UPDATED';
        target_id := NEW.forecast_id;
        actor_name := COALESCE(NEW.approved_by, NEW.created_by);

    ELSE
        event_action := 'DELETED';
        target_id := OLD.forecast_id;
        actor_name := 'SYSTEM';
    END IF;

    INSERT INTO forecast_audit (
        forecast_id,
        event_type,
        actor,
        event_details
    )
    VALUES (
        target_id,
        event_action,
        actor_name,
        jsonb_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME
        )
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_forecast_audit
ON forecast_runs;

CREATE TRIGGER trg_forecast_audit
AFTER INSERT OR UPDATE OR DELETE
ON forecast_runs
FOR EACH ROW
EXECUTE FUNCTION finance.audit_forecast_changes();


/* ---------------------------------------------------------
   FINANCIAL REPORTING VIEWS
   --------------------------------------------------------- */

CREATE OR REPLACE VIEW finance.actuals_by_period AS
SELECT
    o.organization_id,
    p.period_start,
    p.period_end,

    SUM(
        CASE
            WHEN c.category_type = 'REVENUE'
            THEN o.amount ELSE 0
        END
    ) AS revenue,

    SUM(
        CASE
            WHEN c.category_type = 'OPERATING_EXPENSE'
            THEN o.amount ELSE 0
        END
    ) AS operating_expenses,

    SUM(
        CASE
            WHEN c.category_type = 'INVESTING_EXPENSE'
            THEN o.amount ELSE 0
        END
    ) AS investing_expenses,

    SUM(
        CASE
            WHEN c.category_type = 'FINANCING'
            THEN o.amount ELSE 0
        END
    ) AS financing_cash_flow,

    SUM(
        CASE
            WHEN c.category_type = 'REVENUE'
            THEN o.amount ELSE 0
        END
    )
    -
    SUM(
        CASE
            WHEN c.category_type = 'OPERATING_EXPENSE'
            THEN o.amount ELSE 0
        END
    ) AS operating_profit

FROM financial_observations o

JOIN financial_periods p
    ON p.period_id = o.period_id

JOIN financial_categories c
    ON c.category_id = o.category_id

GROUP BY
    o.organization_id,
    p.period_start,
    p.period_end;


CREATE OR REPLACE VIEW finance.forecast_summary AS
SELECT
    f.forecast_id,
    f.organization_id,
    f.forecast_name,
    f.scenario,
    f.forecast_status,

    COUNT(r.result_id) AS forecast_periods,

    COALESCE(SUM(r.revenue), 0) AS total_revenue,

    COALESCE(
        SUM(r.operating_expenses),
        0
    ) AS total_operating_expenses,

    COALESCE(
        SUM(r.operating_profit),
        0
    ) AS total_operating_profit,

    COALESCE(
        SUM(r.net_cash_flow),
        0
    ) AS total_net_cash_flow,

    (
        SELECT closing_cash
        FROM forecast_results latest
        WHERE latest.forecast_id = f.forecast_id
        ORDER BY latest.forecast_period DESC
        LIMIT 1
    ) AS ending_cash

FROM forecast_runs f

LEFT JOIN forecast_results r
    ON r.forecast_id = f.forecast_id

GROUP BY
    f.forecast_id;


CREATE OR REPLACE VIEW finance.budget_variance_report AS
WITH actual_totals AS (
    SELECT
        organization_id,
        period_id,
        category_id,
        SUM(amount) AS actual_amount
    FROM financial_observations
    WHERE source_type IN ('ACTUAL', 'ADJUSTMENT')
    GROUP BY
        organization_id,
        period_id,
        category_id
)
SELECT
    b.budget_id,
    b.organization_id,
    b.period_id,
    c.category_name,
    c.category_type,
    b.budget_amount,

    COALESCE(a.actual_amount, 0) AS actual_amount,

    COALESCE(a.actual_amount, 0)
        - b.budget_amount AS variance,

    CASE
        WHEN b.budget_amount = 0 THEN NULL
        ELSE ROUND(
            (
                COALESCE(a.actual_amount, 0)
                - b.budget_amount
            ) / b.budget_amount * 100,
            2
        )
    END AS variance_percentage

FROM budgets b

JOIN financial_categories c
    ON c.category_id = b.category_id

LEFT JOIN actual_totals a
    ON a.organization_id = b.organization_id
    AND a.period_id = b.period_id
    AND a.category_id = b.category_id;


/* ---------------------------------------------------------
   SCENARIO GENERATION FUNCTION
   --------------------------------------------------------- */

CREATE OR REPLACE FUNCTION finance.calculate_forecast(
    p_forecast_id BIGINT
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    forecast_record forecast_runs%ROWTYPE;

    latest_period DATE;

    historical_revenue NUMERIC(18,2);
    historical_expenses NUMERIC(18,2);
    historical_investments NUMERIC(18,2);

    first_revenue NUMERIC(18,2);
    last_revenue NUMERIC(18,2);

    first_expense NUMERIC(18,2);
    last_expense NUMERIC(18,2);

    revenue_growth NUMERIC(14,8);
    expense_growth NUMERIC(14,8);

    revenue_adjustment NUMERIC(14,8) := 0;
    expense_adjustment NUMERIC(14,8) := 0;

    projected_revenue NUMERIC(18,2);
    projected_expenses NUMERIC(18,2);
    projected_investments NUMERIC(18,2);

    opening_cash NUMERIC(18,2);
    operating_profit NUMERIC(18,2);
    net_cash_flow NUMERIC(18,2);
    closing_cash NUMERIC(18,2);
    profit_margin NUMERIC(12,6);

    cash_status_value VARCHAR(20);

    forecast_date DATE;
    records_count INTEGER;

    i INTEGER;
BEGIN
    SELECT *
    INTO forecast_record
    FROM forecast_runs
    WHERE forecast_id = p_forecast_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Forecast % does not exist.',
            p_forecast_id;
    END IF;

    IF forecast_record.forecast_status NOT IN (
        'DRAFT',
        'CALCULATED'
    ) THEN
        RAISE EXCEPTION
            'Forecast cannot be recalculated in status %.',
            forecast_record.forecast_status;
    END IF;

    /*
     * Use the latest configured historical observations.
     * Closed periods provide the historical source.
     */
    WITH historical AS (
        SELECT
            a.period_start,
            a.revenue,
            a.operating_expenses,
            a.investing_expenses
        FROM actuals_by_period a
        JOIN financial_periods p
            ON p.organization_id = a.organization_id
            AND p.period_start = a.period_start
        WHERE a.organization_id =
            forecast_record.organization_id
          AND a.period_start <=
            forecast_record.historical_cutoff
          AND p.period_status = 'CLOSED'
        ORDER BY a.period_start DESC
        LIMIT forecast_record.moving_average_window
    ),
    chronological AS (
        SELECT *
        FROM historical
        ORDER BY period_start
    )
    SELECT
        COUNT(*),
        AVG(revenue),
        AVG(operating_expenses),
        AVG(investing_expenses),
        (ARRAY_AGG(revenue ORDER BY period_start))[1],
        (ARRAY_AGG(revenue ORDER BY period_start))[
            COUNT(*)::INTEGER
        ],
        (ARRAY_AGG(operating_expenses ORDER BY period_start))[1],
        (ARRAY_AGG(operating_expenses ORDER BY period_start))[
            COUNT(*)::INTEGER
        ],
        MAX(period_start)
    INTO
        records_count,
        historical_revenue,
        historical_expenses,
        historical_investments,
        first_revenue,
        last_revenue,
        first_expense,
        last_expense,
        latest_period
    FROM chronological;

    IF records_count < forecast_record.moving_average_window THEN
        RAISE EXCEPTION
            'Insufficient closed historical periods: expected %, found %.',
            forecast_record.moving_average_window,
            records_count;
    END IF;

    /*
     * Calculate compound growth.
     * When the starting amount is zero, use zero growth
     * rather than an undefined division.
     */
    IF first_revenue > 0 THEN
        revenue_growth :=
            POWER(
                last_revenue / first_revenue,
                1.0 / (records_count - 1)
            ) - 1;
    ELSE
        revenue_growth := 0;
    END IF;

    IF first_expense > 0 THEN
        expense_growth :=
            POWER(
                last_expense / first_expense,
                1.0 / (records_count - 1)
            ) - 1;
    ELSE
        expense_growth := 0;
    END IF;

    IF forecast_record.scenario = 'OPTIMISTIC' THEN
        revenue_adjustment := 0.05;

    ELSIF forecast_record.scenario = 'PESSIMISTIC' THEN
        revenue_adjustment := -0.05;
        expense_adjustment := 0.02;

    ELSIF forecast_record.scenario = 'STRESS' THEN
        revenue_adjustment := -0.15;
        expense_adjustment := 0.08;
    END IF;

    revenue_growth := GREATEST(
        -0.95,
        LEAST(1.0, revenue_growth + revenue_adjustment)
    );

    expense_growth := GREATEST(
        -0.95,
        LEAST(1.0, expense_growth + expense_adjustment)
    );

    projected_revenue := historical_revenue;
    projected_expenses := historical_expenses;
    projected_investments := historical_investments;

    /*
     * Opening cash comes from the latest verified cash balance.
     * The latest actual cash balance is not inferred from revenue.
     */
    SELECT closing_cash
    INTO opening_cash
    FROM cash_balances cb
    JOIN financial_periods fp
        ON fp.period_id = cb.period_id
    WHERE cb.organization_id =
        forecast_record.organization_id
      AND fp.period_start <= latest_period
      AND cb.verified = TRUE
    ORDER BY fp.period_start DESC
    LIMIT 1;

    IF opening_cash IS NULL THEN
        RAISE EXCEPTION
            'No verified opening cash balance is available.';
    END IF;

    forecast_date :=
        (latest_period + INTERVAL '1 month')::DATE;

    DELETE FROM forecast_results
    WHERE forecast_id = p_forecast_id;

    FOR i IN 1..forecast_record.forecast_horizon LOOP

        projected_revenue := ROUND(
            projected_revenue * (1 + revenue_growth),
            2
        );

        projected_expenses := ROUND(
            projected_expenses * (1 + expense_growth),
            2
        );

        operating_profit :=
            projected_revenue - projected_expenses;

        /*
         * Investing expenses are held constant in this model.
         * Financing cash flow is assumed to be zero.
         */
        net_cash_flow :=
            operating_profit - projected_investments;

        closing_cash := opening_cash + net_cash_flow;

        profit_margin := CASE
            WHEN projected_revenue > 0
            THEN operating_profit / projected_revenue
            ELSE NULL
        END;

        cash_status_value := CASE
            WHEN closing_cash < 0
            THEN 'NEGATIVE_CASH'

            WHEN closing_cash < projected_expenses
            THEN 'LOW_CASH'

            ELSE 'HEALTHY'
        END;

        INSERT INTO forecast_results (
            forecast_id,
            forecast_period,
            revenue,
            operating_expenses,
            investing_expenses,
            financing_cash_flow,
            opening_cash,
            closing_cash,
            profit_margin,
            cash_status
        )
        VALUES (
            p_forecast_id,
            forecast_date,
            projected_revenue,
            projected_expenses,
            projected_investments,
            0,
            opening_cash,
            closing_cash,
            profit_margin,
            cash_status_value
        );

        opening_cash := closing_cash;

        forecast_date :=
            (forecast_date + INTERVAL '1 month')::DATE;
    END LOOP;

    UPDATE forecast_runs
    SET forecast_status = 'CALCULATED'
    WHERE forecast_id = p_forecast_id;

    RETURN forecast_record.forecast_horizon;
END;
$$;


/* ---------------------------------------------------------
   FORECAST APPROVAL PROCEDURE
   --------------------------------------------------------- */

CREATE OR REPLACE PROCEDURE finance.approve_forecast(
    p_forecast_id BIGINT,
    p_approver VARCHAR(120),
    p_required_approvals INTEGER DEFAULT 2
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status VARCHAR(20);
    approval_count INTEGER;
    result_count INTEGER;
BEGIN
    IF p_approver IS NULL OR LENGTH(TRIM(p_approver)) = 0 THEN
        RAISE EXCEPTION 'Approver is required.';
    END IF;

    IF p_required_approvals < 1 THEN
        RAISE EXCEPTION
            'At least one approval is required.';
    END IF;

    SELECT forecast_status
    INTO current_status
    FROM forecast_runs
    WHERE forecast_id = p_forecast_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Forecast does not exist.';
    END IF;

    IF current_status NOT IN (
        'CALCULATED',
        'UNDER_REVIEW'
    ) THEN
        RAISE EXCEPTION
            'Forecast is not eligible for approval.';
    END IF;

    SELECT COUNT(*)
    INTO result_count
    FROM forecast_results
    WHERE forecast_id = p_forecast_id;

    IF result_count = 0 THEN
        RAISE EXCEPTION
            'Forecast cannot be approved without results.';
    END IF;

    SELECT COUNT(*)
    INTO approval_count
    FROM forecast_approvals
    WHERE forecast_id = p_forecast_id
      AND approval_status = 'APPROVED';

    IF approval_count < p_required_approvals THEN
        RAISE EXCEPTION
            'Insufficient approvals: required %, found %.',
            p_required_approvals,
            approval_count;
    END IF;

    UPDATE forecast_runs
    SET
        forecast_status = 'APPROVED',
        approved_by = p_approver,
        approved_at = CURRENT_TIMESTAMP
    WHERE forecast_id = p_forecast_id;
END;
$$;


/* ---------------------------------------------------------
   SAMPLE ORGANIZATION
   --------------------------------------------------------- */

INSERT INTO organizations (
    organization_name,
    currency_code
)
VALUES (
    'Northstar Enterprise',
    'INR'
)
ON CONFLICT (organization_name) DO NOTHING;


INSERT INTO financial_periods (
    organization_id,
    period_start,
    period_end,
    period_status
)
SELECT
    o.organization_id,
    dates.period_start,
    (
        dates.period_start
        + INTERVAL '1 month'
        - INTERVAL '1 day'
    )::DATE,
    'CLOSED'
FROM organizations o
CROSS JOIN (
    VALUES
        ('2026-01-01'::DATE),
        ('2026-02-01'::DATE),
        ('2026-03-01'::DATE),
        ('2026-04-01'::DATE),
        ('2026-05-01'::DATE),
        ('2026-06-01'::DATE)
) AS dates(period_start)
WHERE o.organization_name = 'Northstar Enterprise'
ON CONFLICT (
    organization_id,
    period_start,
    period_end
) DO NOTHING;


INSERT INTO financial_categories (
    organization_id,
    category_name,
    category_type,
    is_recurring
)
SELECT
    o.organization_id,
    categories.category_name,
    categories.category_type,
    categories.is_recurring
FROM organizations o
CROSS JOIN (
    VALUES
        ('Product Sales', 'REVENUE', TRUE),
        ('Service Revenue', 'REVENUE', TRUE),
        ('Employee Costs', 'OPERATING_EXPENSE', TRUE),
        ('Infrastructure', 'OPERATING_EXPENSE', TRUE),
        ('Equipment', 'INVESTING_EXPENSE', FALSE),
        ('Loan Repayment', 'FINANCING', FALSE)
) AS categories(
    category_name,
    category_type,
    is_recurring
)
WHERE o.organization_name = 'Northstar Enterprise'
ON CONFLICT (
    organization_id,
    category_name,
    category_type
) DO NOTHING;


/* ---------------------------------------------------------
   HISTORICAL FINANCIAL OBSERVATIONS
   --------------------------------------------------------- */

WITH monthly_data (
    period_start,
    revenue,
    operating_expenses,
    investing_expenses,
    financing_cash_flow
) AS (
    VALUES
        ('2026-01-01'::DATE, 850000, 520000, 65000, 20000),
        ('2026-02-01'::DATE, 875000, 530000, 70000, 0),
        ('2026-03-01'::DATE, 900000, 540000, 60000, -10000),
        ('2026-04-01'::DATE, 925000, 555000, 75000, 15000),
        ('2026-05-01'::DATE, 960000, 565000, 80000, 0),
        ('2026-06-01'::DATE, 990000, 580000, 70000, 10000)
),
components AS (
    SELECT
        o.organization_id,
        p.period_id,
        c.category_id,
        m.revenue AS amount,
        'Product Sales' AS category_name,
        'ACTUAL' AS source_type
    FROM monthly_data m
    CROSS JOIN organizations o
    JOIN financial_periods p
        ON p.organization_id = o.organization_id
        AND p.period_start = m.period_start
    JOIN financial_categories c
        ON c.organization_id = o.organization_id
        AND c.category_name = 'Product Sales'

    UNION ALL

    SELECT
        o.organization_id,
        p.period_id,
        c.category_id,
        m.operating_expenses,
        'Employee Costs',
        'ACTUAL'
    FROM monthly_data m
    CROSS JOIN organizations o
    JOIN financial_periods p
        ON p.organization_id = o.organization_id
        AND p.period_start = m.period_start
    JOIN financial_categories c
        ON c.organization_id = o.organization_id
        AND c.category_name = 'Employee Costs'

    UNION ALL

    SELECT
        o.organization_id,
        p.period_id,
        c.category_id,
        m.investing_expenses,
        'Equipment',
        'ACTUAL'
    FROM monthly_data m
    CROSS JOIN organizations o
    JOIN financial_periods p
        ON p.organization_id = o.organization_id
        AND p.period_start = m.period_start
    JOIN financial_categories c
        ON c.organization_id = o.organization_id
        AND c.category_name = 'Equipment'

    UNION ALL

    SELECT
        o.organization_id,
        p.period_id,
        c.category_id,
        ABS(m.financing_cash_flow),
        'Loan Repayment',
        'ACTUAL'
    FROM monthly_data m
    CROSS JOIN organizations o
    JOIN financial_periods p
        ON p.organization_id = o.organization_id
        AND p.period_start = m.period_start
    JOIN financial_categories c
        ON c.organization_id = o.organization_id
        AND c.category_name = 'Loan Repayment'
    WHERE m.financing_cash_flow < 0
)
INSERT INTO financial_observations (
    organization_id,
    period_id,
    category_id,
    amount,
    transaction_reference,
    source_type,
    recorded_by
)
SELECT
    organization_id,
    period_id,
    category_id,
    amount,
    'HIST-' || period_id || '-' || category_id,
    source_type,
    'finance.system'
FROM components
ON CONFLICT (
    organization_id,
    transaction_reference
) DO NOTHING;


/* ---------------------------------------------------------
   HISTORICAL CASH BALANCES
   --------------------------------------------------------- */

INSERT INTO cash_balances (
    organization_id,
    period_id,
    opening_cash,
    closing_cash,
    verified
)
SELECT
    o.organization_id,
    p.period_id,

    data.opening_cash,

    data.opening_cash
    + data.revenue
    - data.operating_expenses
    - data.investing_expenses
    + data.financing_cash_flow,

    TRUE

FROM (
    VALUES
        ('2026-01-01'::DATE, 300000, 850000, 520000, 65000, 20000),
        ('2026-02-01'::DATE, 595000, 875000, 530000, 70000, 0),
        ('2026-03-01'::DATE, 870000, 900000, 540000, 60000, -10000),
        ('2026-04-01'::DATE, 1160000, 925000, 555000, 75000, 15000),
        ('2026-05-01'::DATE, 1470000, 960000, 565000, 80000, 0),
        ('2026-06-01'::DATE, 1785000, 990000, 580000, 70000, 10000)
) AS data(
    period_start,
    opening_cash,
    revenue,
    operating_expenses,
    investing_expenses,
    financing_cash_flow
)

CROSS JOIN organizations o

JOIN financial_periods p
    ON p.organization_id = o.organization_id
    AND p.period_start = data.period_start

WHERE o.organization_name = 'Northstar Enterprise'

ON CONFLICT (
    organization_id,
    period_id
) DO NOTHING;


/* ---------------------------------------------------------
   SAMPLE BUDGETS
   --------------------------------------------------------- */

INSERT INTO budgets (
    organization_id,
    category_id,
    period_id,
    budget_amount,
    created_by
)
SELECT
    o.organization_id,
    c.category_id,
    p.period_id,
    CASE
        WHEN c.category_type = 'REVENUE'
            THEN 1000000
        WHEN c.category_type = 'OPERATING_EXPENSE'
            THEN 600000
        WHEN c.category_type = 'INVESTING_EXPENSE'
            THEN 75000
        ELSE 20000
    END,
    'finance.controller'
FROM organizations o
JOIN financial_categories c
    ON c.organization_id = o.organization_id
JOIN financial_periods p
    ON p.organization_id = o.organization_id
    AND p.period_start = '2026-06-01'
WHERE o.organization_name = 'Northstar Enterprise'
  AND c.category_name IN (
      'Product Sales',
      'Employee Costs',
      'Equipment'
  )
ON CONFLICT (
    organization_id,
    category_id,
    period_id
) DO NOTHING;


/* ---------------------------------------------------------
   FORECAST DEFINITIONS
   --------------------------------------------------------- */

INSERT INTO forecast_runs (
    organization_id,
    forecast_name,
    scenario,
    forecast_status,
    historical_cutoff,
    forecast_horizon,
    moving_average_window,
    created_by
)
SELECT
    organization_id,
    'FY2026 Base Forecast',
    'BASE',
    'DRAFT',
    '2026-06-30',
    6,
    3,
    'finance.analyst'
FROM organizations
WHERE organization_name = 'Northstar Enterprise'
AND NOT EXISTS (
    SELECT 1
    FROM forecast_runs existing
    WHERE existing.organization_id =
        organizations.organization_id
      AND existing.forecast_name =
        'FY2026 Base Forecast'
);


INSERT INTO forecast_runs (
    organization_id,
    forecast_name,
    scenario,
    forecast_status,
    historical_cutoff,
    forecast_horizon,
    moving_average_window,
    created_by
)
SELECT
    organization_id,
    'FY2026 Optimistic Forecast',
    'OPTIMISTIC',
    'DRAFT',
    '2026-06-30',
    6,
    3,
    'finance.analyst'
FROM organizations
WHERE organization_name = 'Northstar Enterprise'
AND NOT EXISTS (
    SELECT 1
    FROM forecast_runs existing
    WHERE existing.organization_id =
        organizations.organization_id
      AND existing.forecast_name =
        'FY2026 Optimistic Forecast'
);


INSERT INTO forecast_runs (
    organization_id,
    forecast_name,
    scenario,
    forecast_status,
    historical_cutoff,
    forecast_horizon,
    moving_average_window,
    created_by
)
SELECT
    organization_id,
    'FY2026 Pessimistic Forecast',
    'PESSIMISTIC',
    'DRAFT',
    '2026-06-30',
    6,
    3,
    'finance.analyst'
FROM organizations
WHERE organization_name = 'Northstar Enterprise'
AND NOT EXISTS (
    SELECT 1
    FROM forecast_runs existing
    WHERE existing.organization_id =
        organizations.organization_id
      AND existing.forecast_name =
        'FY2026 Pessimistic Forecast'
);


/* ---------------------------------------------------------
   FORECAST ASSUMPTIONS
   --------------------------------------------------------- */

INSERT INTO forecast_assumptions (
    forecast_id,
    assumption_name,
    assumption_value,
    description
)
SELECT
    forecast_id,
    'REVENUE_ADJUSTMENT',
    CASE scenario
        WHEN 'OPTIMISTIC' THEN 0.05
        WHEN 'PESSIMISTIC' THEN -0.05
        ELSE 0
    END,
    'Revenue growth scenario adjustment'
FROM forecast_runs
WHERE forecast_name IN (
    'FY2026 Base Forecast',
    'FY2026 Optimistic Forecast',
    'FY2026 Pessimistic Forecast'
)
ON CONFLICT (forecast_id, assumption_name) DO NOTHING;


/* ---------------------------------------------------------
   TRANSACTIONAL FORECAST CALCULATION
   --------------------------------------------------------- */

DO $$
DECLARE
    forecast_record RECORD;
    generated_periods INTEGER;
BEGIN
    FOR forecast_record IN
        SELECT forecast_id, forecast_name
        FROM forecast_runs
        WHERE forecast_status = 'DRAFT'
        ORDER BY forecast_id
    LOOP
        generated_periods :=
            finance.calculate_forecast(
                forecast_record.forecast_id
            );

        RAISE NOTICE
            'Generated % periods for %.',
            generated_periods,
            forecast_record.forecast_name;
    END LOOP;
END;
$$;


/* ---------------------------------------------------------
   SAMPLE APPROVAL DECISIONS
   --------------------------------------------------------- */

INSERT INTO forecast_approvals (
    forecast_id,
    reviewer,
    approval_status,
    comments
)
SELECT
    f.forecast_id,
    reviewers.reviewer,
    'APPROVED',
    reviewers.comments
FROM forecast_runs f
CROSS JOIN (
    VALUES
        (
            'finance.manager',
            'Reviewed assumptions and reconciled cash flow.'
        ),
        (
            'finance.controller',
            'Reviewed historical inputs and forecast methodology.'
        )
) AS reviewers(reviewer, comments)
WHERE f.forecast_name = 'FY2026 Base Forecast'
ON CONFLICT (forecast_id, reviewer) DO NOTHING;


/*
 * The base forecast is approved only after two distinct
 * approval records exist.
 *
 * This sample demonstrates a controlled approval transition.
 */
DO $$
DECLARE
    base_forecast_id BIGINT;
BEGIN
    SELECT forecast_id
    INTO base_forecast_id
    FROM forecast_runs
    WHERE forecast_name = 'FY2026 Base Forecast';

    CALL finance.approve_forecast(
        base_forecast_id,
        'chief.financial.officer',
        2
    );
END;
$$;


/* ---------------------------------------------------------
   QUERY 1: HISTORICAL FINANCIAL PERFORMANCE
   --------------------------------------------------------- */

SELECT
    organization_id,
    period_start,
    revenue,
    operating_expenses,
    investing_expenses,
    financing_cash_flow,
    operating_profit
FROM actuals_by_period
ORDER BY period_start;


/* ---------------------------------------------------------
   QUERY 2: MONTHLY PROFIT MARGIN
   --------------------------------------------------------- */

SELECT
    organization_id,
    period_start,
    revenue,
    operating_profit,

    ROUND(
        operating_profit / NULLIF(revenue, 0) * 100,
        2
    ) AS profit_margin_percentage

FROM actuals_by_period
ORDER BY period_start;


/* ---------------------------------------------------------
   QUERY 3: MONTH-OVER-MONTH REVENUE CHANGE
   --------------------------------------------------------- */

WITH monthly_revenue AS (
    SELECT
        organization_id,
        period_start,
        revenue,

        LAG(revenue) OVER (
            PARTITION BY organization_id
            ORDER BY period_start
        ) AS previous_revenue

    FROM actuals_by_period
)
SELECT
    period_start,
    revenue,
    previous_revenue,

    ROUND(
        (
            revenue - previous_revenue
        ) / NULLIF(previous_revenue, 0) * 100,
        2
    ) AS revenue_growth_percentage

FROM monthly_revenue
ORDER BY period_start;


/* ---------------------------------------------------------
   QUERY 4: BUDGET VARIANCE REPORT
   --------------------------------------------------------- */

SELECT
    category_name,
    category_type,
    budget_amount,
    actual_amount,
    variance,
    variance_percentage,

    CASE
        WHEN category_type = 'REVENUE' AND variance >= 0
            THEN 'FAVORABLE'
        WHEN category_type = 'REVENUE'
            THEN 'UNFAVORABLE'

        WHEN category_type IN (
            'OPERATING_EXPENSE',
            'INVESTING_EXPENSE'
        ) AND variance <= 0
            THEN 'FAVORABLE'

        ELSE 'UNFAVORABLE'
    END AS financial_assessment

FROM budget_variance_report
ORDER BY category_type, category_name;


/* ---------------------------------------------------------
   QUERY 5: FORECAST SCENARIO COMPARISON
   --------------------------------------------------------- */

SELECT
    forecast_name,
    scenario,
    forecast_status,
    forecast_periods,
    total_revenue,
    total_operating_expenses,
    total_operating_profit,
    total_net_cash_flow,
    ending_cash
FROM forecast_summary
ORDER BY scenario;


/* ---------------------------------------------------------
   QUERY 6: PERIOD-BY-PERIOD CASH-FLOW PROJECTION
   --------------------------------------------------------- */

SELECT
    f.forecast_name,
    r.forecast_period,
    r.opening_cash,
    r.revenue,
    r.operating_expenses,
    r.investing_expenses,
    r.net_cash_flow,
    r.closing_cash,
    r.cash_status
FROM forecast_results r
JOIN forecast_runs f
    ON f.forecast_id = r.forecast_id
ORDER BY
    f.forecast_name,
    r.forecast_period;


/* ---------------------------------------------------------
   QUERY 7: CASH RISK IDENTIFICATION
   --------------------------------------------------------- */

SELECT
    f.forecast_name,
    r.forecast_period,
    r.closing_cash,
    r.operating_expenses,

    ROUND(
        r.closing_cash /
        NULLIF(r.operating_expenses, 0),
        2
    ) AS expense_coverage_ratio,

    r.cash_status

FROM forecast_results r

JOIN forecast_runs f
    ON f.forecast_id = r.forecast_id

WHERE r.closing_cash < r.operating_expenses
   OR r.closing_cash < 0

ORDER BY
    r.forecast_period,
    f.forecast_name;


/* ---------------------------------------------------------
   QUERY 8: FORECAST APPROVAL AUDIT
   --------------------------------------------------------- */

SELECT
    f.forecast_name,
    a.reviewer,
    a.approval_status,
    a.comments,
    a.reviewed_at

FROM forecast_approvals a

JOIN forecast_runs f
    ON f.forecast_id = a.forecast_id

ORDER BY
    f.forecast_id,
    a.reviewed_at;


/* ---------------------------------------------------------
   QUERY 9: FORECAST ELIGIBILITY VALIDATION
   --------------------------------------------------------- */

WITH approval_counts AS (
    SELECT
        forecast_id,

        COUNT(*) FILTER (
            WHERE approval_status = 'APPROVED'
        ) AS approvals,

        COUNT(*) FILTER (
            WHERE approval_status = 'REJECTED'
        ) AS rejections

    FROM forecast_approvals
    GROUP BY forecast_id
),
result_counts AS (
    SELECT
        forecast_id,
        COUNT(*) AS result_count,

        COUNT(*) FILTER (
            WHERE cash_status = 'NEGATIVE_CASH'
        ) AS negative_cash_periods

    FROM forecast_results
    GROUP BY forecast_id
)
SELECT
    f.forecast_name,
    f.forecast_status,

    COALESCE(a.approvals, 0) AS approvals,

    COALESCE(a.rejections, 0) AS rejections,

    COALESCE(r.result_count, 0) AS result_count,

    COALESCE(r.negative_cash_periods, 0)
        AS negative_cash_periods,

    CASE
        WHEN f.forecast_status = 'APPROVED'
         AND COALESCE(a.approvals, 0) >= 2
         AND COALESCE(a.rejections, 0) = 0
         AND COALESCE(r.result_count, 0) =
            f.forecast_horizon
        THEN 'APPROVED_AND_COMPLETE'

        WHEN f.forecast_status = 'REJECTED'
        THEN 'REJECTED'

        WHEN f.forecast_status IN (
            'CALCULATED',
            'UNDER_REVIEW'
        )
        THEN 'AWAITING_APPROVAL'

        ELSE 'NOT_ELIGIBLE'
    END AS eligibility_status

FROM forecast_runs f

LEFT JOIN approval_counts a
    ON a.forecast_id = f.forecast_id

LEFT JOIN result_counts r
    ON r.forecast_id = f.forecast_id

ORDER BY f.forecast_id;


/* ---------------------------------------------------------
   QUERY 10: FINANCIAL RISK AND PROFITABILITY DASHBOARD
   --------------------------------------------------------- */

SELECT
    f.scenario,

    COUNT(*) AS forecast_periods,

    ROUND(AVG(r.profit_margin) * 100, 2)
        AS average_profit_margin_percentage,

    ROUND(SUM(r.operating_profit), 2)
        AS cumulative_operating_profit,

    ROUND(SUM(r.net_cash_flow), 2)
        AS cumulative_net_cash_flow,

    MIN(r.closing_cash) AS minimum_projected_cash,

    MAX(r.closing_cash) AS maximum_projected_cash,

    COUNT(*) FILTER (
        WHERE r.cash_status = 'NEGATIVE_CASH'
    ) AS negative_cash_periods

FROM forecast_results r

JOIN forecast_runs f
    ON f.forecast_id = r.forecast_id

GROUP BY f.scenario

ORDER BY f.scenario;


/* ---------------------------------------------------------
   QUERY 11: FORECAST AUDIT HISTORY
   --------------------------------------------------------- */

SELECT
    f.forecast_name,
    a.event_type,
    a.actor,
    a.event_details,
    a.event_timestamp

FROM forecast_audit a

LEFT JOIN forecast_runs f
    ON f.forecast_id = a.forecast_id

ORDER BY a.event_timestamp DESC;


/* ---------------------------------------------------------
   QUERY 12: VALIDATION OF HISTORICAL CASH BALANCES
   --------------------------------------------------------- */

SELECT
    o.organization_name,
    p.period_start,
    cb.opening_cash,
    ap.revenue,
    ap.operating_expenses,
    ap.investing_expenses,
    ap.financing_cash_flow,
    cb.closing_cash,

    cb.opening_cash
    + COALESCE(ap.revenue, 0)
    - COALESCE(ap.operating_expenses, 0)
    - COALESCE(ap.investing_expenses, 0)
    + COALESCE(ap.financing_cash_flow, 0)
    AS calculated_closing_cash,

    CASE
        WHEN ABS(
            cb.closing_cash
            - (
                cb.opening_cash
                + COALESCE(ap.revenue, 0)
                - COALESCE(ap.operating_expenses, 0)
                - COALESCE(ap.investing_expenses, 0)
                + COALESCE(ap.financing_cash_flow, 0)
            )
        ) <= 0.01
        THEN 'RECONCILED'
        ELSE 'REQUIRES_INVESTIGATION'
    END AS reconciliation_status

FROM cash_balances cb

JOIN organizations o
    ON o.organization_id = cb.organization_id

JOIN financial_periods p
    ON p.period_id = cb.period_id

LEFT JOIN actuals_by_period ap
    ON ap.organization_id = cb.organization_id
    AND ap.period_start = p.period_start

ORDER BY p.period_start;


/*
 * Production security:
 * - Use separate database roles for analysts, reviewers and approvers.
 * - Grant EXECUTE on controlled procedures instead of unrestricted
 *   table updates.
 * - Apply row-level security for multi-organization deployments.
 * - Keep database credentials outside SQL source files.
 * - Use an external authorization layer to establish reviewer identity.
 * - Record immutable external audit events for regulated operations.
 *
 * The sample approval records demonstrate workflow data, not
 * authentication or proof of reviewer identity.
 */

COMMIT;
