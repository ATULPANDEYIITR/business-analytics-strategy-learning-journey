-- ============================================================
-- UNIT ECONOMICS ANALYTICS DATABASE
-- PostgreSQL 14+
--
-- Domain:
-- Customer Acquisition Cost
-- Lifetime Value
-- Contribution Margin
-- CAC Payback
-- Cohort Analysis
-- Acquisition Channel Performance
-- Unit Economics Policy Evaluation
--
-- Currency: INR
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS unit_economics;

SET search_path TO unit_economics, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE acquisition_channel AS ENUM (
    'organic',
    'paid_search',
    'social',
    'referral',
    'partnership'
);

CREATE TYPE customer_status AS ENUM (
    'active',
    'churned',
    'suspended'
);

CREATE TYPE evaluation_status AS ENUM (
    'profitable',
    'unprofitable',
    'negative_contribution',
    'payback_exceeds_lifetime',
    'insufficient_data'
);

CREATE TYPE campaign_status AS ENUM (
    'planned',
    'active',
    'completed',
    'paused'
);

-- ============================================================
-- 2. ORGANIZATIONS AND ACQUISITION CHANNELS
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (currency_code ~ '^[A-Z]{3}$')
);

CREATE TABLE acquisition_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code acquisition_channel NOT NULL UNIQUE,
    channel_description TEXT NOT NULL
);

INSERT INTO acquisition_channels (
    channel_code,
    channel_description
)
VALUES
    ('organic', 'Unpaid search and direct acquisition'),
    ('paid_search', 'Paid search advertisements'),
    ('social', 'Paid social media acquisition'),
    ('referral', 'Customer referral acquisition'),
    ('partnership', 'Partner-driven acquisition');

-- ============================================================
-- 3. CAMPAIGNS AND ACQUISITION EXPENDITURE
-- ============================================================

CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),
    campaign_name VARCHAR(200) NOT NULL,
    campaign_status campaign_status NOT NULL DEFAULT 'planned',
    start_date DATE NOT NULL,
    end_date DATE,

    UNIQUE (organization_id, campaign_name),

    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE acquisition_periods (
    acquisition_period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(campaign_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    advertising_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    sales_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    marketing_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    new_customers INTEGER NOT NULL,

    CHECK (period_end >= period_start),
    CHECK (advertising_cost >= 0),
    CHECK (sales_cost >= 0),
    CHECK (marketing_cost >= 0),
    CHECK (new_customers > 0),

    UNIQUE (campaign_id, period_start, period_end)
);

CREATE INDEX idx_acquisition_period_campaign
    ON acquisition_periods(campaign_id, period_start);

-- ============================================================
-- 4. CUSTOMER AND COHORT MANAGEMENT
-- ============================================================

CREATE TABLE customer_cohorts (
    cohort_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    cohort_name VARCHAR(50) NOT NULL,
    cohort_start DATE NOT NULL,
    cohort_end DATE,

    UNIQUE (organization_id, cohort_name),

    CHECK (cohort_end IS NULL OR cohort_end >= cohort_start)
);

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    cohort_id BIGINT NOT NULL
        REFERENCES customer_cohorts(cohort_id),
    acquisition_period_id BIGINT NOT NULL
        REFERENCES acquisition_periods(acquisition_period_id),
    external_customer_reference VARCHAR(100) NOT NULL,
    acquisition_date DATE NOT NULL,
    status customer_status NOT NULL DEFAULT 'active',

    UNIQUE (organization_id, external_customer_reference)
);

CREATE INDEX idx_customers_cohort
    ON customers(cohort_id);

CREATE INDEX idx_customers_acquisition_period
    ON customers(acquisition_period_id);

CREATE INDEX idx_customers_status
    ON customers(status);

-- ============================================================
-- 5. RECURRING REVENUE AND VARIABLE COSTS
-- ============================================================

CREATE TABLE customer_monthly_economics (
    monthly_economics_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    reporting_month DATE NOT NULL,
    revenue NUMERIC(14,2) NOT NULL,
    variable_cost NUMERIC(14,2) NOT NULL,
    refunds NUMERIC(14,2) NOT NULL DEFAULT 0,
    service_credits NUMERIC(14,2) NOT NULL DEFAULT 0,

    net_revenue NUMERIC(14,2)
        GENERATED ALWAYS AS (revenue - refunds - service_credits) STORED,

    contribution NUMERIC(14,2)
        GENERATED ALWAYS AS (
            revenue - refunds - service_credits - variable_cost
        ) STORED,

    UNIQUE (customer_id, reporting_month),

    CHECK (revenue >= 0),
    CHECK (variable_cost >= 0),
    CHECK (refunds >= 0),
    CHECK (service_credits >= 0),
    CHECK (refunds + service_credits <= revenue),
    CHECK (reporting_month = date_trunc('month', reporting_month)::date)
);

CREATE INDEX idx_monthly_economics_month
    ON customer_monthly_economics(reporting_month);

CREATE INDEX idx_monthly_economics_customer_month
    ON customer_monthly_economics(customer_id, reporting_month);

-- ============================================================
-- 6. LIFETIME AND CHURN ASSUMPTIONS
-- ============================================================

CREATE TABLE customer_lifetime_assumptions (
    assumption_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    channel_id BIGINT REFERENCES acquisition_channels(channel_id),
    expected_lifetime_months NUMERIC(8,2) NOT NULL,
    monthly_churn_rate NUMERIC(8,6) NOT NULL,
    effective_from DATE NOT NULL,
    effective_until DATE,

    CHECK (expected_lifetime_months > 0),
    CHECK (monthly_churn_rate >= 0 AND monthly_churn_rate < 1),
    CHECK (effective_until IS NULL OR effective_until >= effective_from)
);

-- ============================================================
-- 7. UNIT ECONOMICS POLICIES
-- ============================================================

CREATE TABLE economics_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    policy_name VARCHAR(150) NOT NULL,
    minimum_ltv_cac_ratio NUMERIC(10,4) NOT NULL DEFAULT 3,
    maximum_payback_months NUMERIC(10,2) NOT NULL DEFAULT 12,
    minimum_contribution_margin NUMERIC(8,4) NOT NULL DEFAULT 0.50,
    effective_from DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (minimum_ltv_cac_ratio > 0),
    CHECK (maximum_payback_months > 0),
    CHECK (
        minimum_contribution_margin >= 0
        AND minimum_contribution_margin <= 1
    ),

    UNIQUE (organization_id, policy_name)
);

CREATE INDEX idx_active_economics_policy
    ON economics_policies(organization_id, effective_from)
    WHERE active = TRUE;

-- ============================================================
-- 8. UNIT ECONOMICS EVALUATION RESULTS
-- ============================================================

CREATE TABLE unit_economics_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    acquisition_period_id BIGINT NOT NULL
        REFERENCES acquisition_periods(acquisition_period_id),
    policy_id BIGINT REFERENCES economics_policies(policy_id),
    evaluation_date DATE NOT NULL DEFAULT CURRENT_DATE,

    cac NUMERIC(14,2) NOT NULL,
    monthly_contribution NUMERIC(14,2) NOT NULL,
    contribution_margin NUMERIC(10,6) NOT NULL,
    gross_ltv NUMERIC(14,2) NOT NULL,
    contribution_ltv NUMERIC(14,2) NOT NULL,
    ltv_cac_ratio NUMERIC(14,4),
    payback_months NUMERIC(12,4),

    status evaluation_status NOT NULL,

    CHECK (cac >= 0),
    CHECK (gross_ltv >= 0),
    CHECK (contribution_margin >= -1),
    CHECK (contribution_margin <= 1),
    CHECK (payback_months IS NULL OR payback_months >= 0),

    UNIQUE (customer_id, acquisition_period_id, evaluation_date)
);

CREATE INDEX idx_evaluations_status
    ON unit_economics_evaluations(status, evaluation_date);

CREATE INDEX idx_evaluations_ratio
    ON unit_economics_evaluations(ltv_cac_ratio DESC);

-- ============================================================
-- 9. AUDIT LOG
-- ============================================================

CREATE TABLE economics_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    record_id BIGINT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    database_user TEXT NOT NULL DEFAULT CURRENT_USER
);

-- ============================================================
-- 10. AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION audit_economics_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    affected_id BIGINT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        affected_id := OLD.monthly_economics_id;
    ELSE
        affected_id := NEW.monthly_economics_id;
    END IF;

    INSERT INTO economics_audit_log (
        table_name,
        operation,
        record_id
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        affected_id
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_monthly_economics_audit
AFTER INSERT OR UPDATE OR DELETE
ON customer_monthly_economics
FOR EACH ROW
EXECUTE FUNCTION audit_economics_change();

-- ============================================================
-- 11. METRIC CALCULATION FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_cac(
    p_campaign_id BIGINT
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    total_cost NUMERIC;
    total_customers BIGINT;
BEGIN
    SELECT
        COALESCE(SUM(
            advertising_cost + sales_cost + marketing_cost
        ), 0),
        COALESCE(SUM(new_customers), 0)
    INTO total_cost, total_customers
    FROM acquisition_periods
    WHERE campaign_id = p_campaign_id;

    IF total_customers = 0 THEN
        RAISE EXCEPTION 'CAC cannot be calculated without customers';
    END IF;

    RETURN ROUND(total_cost / total_customers, 2);
END;
$$;

CREATE OR REPLACE FUNCTION calculate_contribution_margin(
    p_revenue NUMERIC,
    p_variable_cost NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_revenue < 0 OR p_variable_cost < 0 THEN
        RAISE EXCEPTION 'Financial values cannot be negative';
    END IF;

    IF p_revenue = 0 THEN
        IF p_variable_cost > 0 THEN
            RAISE EXCEPTION 'Variable cost without revenue';
        END IF;

        RETURN 0;
    END IF;

    RETURN ROUND(
        (p_revenue - p_variable_cost) / p_revenue,
        6
    );
END;
$$;

CREATE OR REPLACE FUNCTION calculate_payback(
    p_cac NUMERIC,
    p_monthly_contribution NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_cac < 0 OR p_monthly_contribution < 0 THEN
        RAISE EXCEPTION 'Invalid CAC or contribution';
    END IF;

    IF p_monthly_contribution = 0 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND(p_cac / p_monthly_contribution, 4);
END;
$$;

-- ============================================================
-- 12. COHORT REPORTING VIEW
-- ============================================================

CREATE OR REPLACE VIEW cohort_economics AS
SELECT
    cc.cohort_id,
    cc.cohort_name,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COALESCE(SUM(me.revenue), 0) AS total_revenue,
    COALESCE(SUM(me.variable_cost), 0) AS total_variable_cost,
    COALESCE(SUM(me.contribution), 0) AS total_contribution,

    CASE
        WHEN SUM(me.revenue) > 0
        THEN ROUND(
            SUM(me.contribution) / SUM(me.revenue) * 100,
            2
        )
        ELSE 0
    END AS contribution_margin_percent

FROM customer_cohorts cc
LEFT JOIN customers c
    ON c.cohort_id = cc.cohort_id
LEFT JOIN customer_monthly_economics me
    ON me.customer_id = c.customer_id
GROUP BY cc.cohort_id, cc.cohort_name;

-- ============================================================
-- 13. CHANNEL PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW channel_acquisition_performance AS
SELECT
    ac.channel_code,
    SUM(ap.advertising_cost) AS advertising_cost,
    SUM(ap.sales_cost) AS sales_cost,
    SUM(ap.marketing_cost) AS marketing_cost,
    SUM(ap.new_customers) AS acquired_customers,

    ROUND(
        SUM(
            ap.advertising_cost +
            ap.sales_cost +
            ap.marketing_cost
        ) / NULLIF(SUM(ap.new_customers), 0),
        2
    ) AS cac

FROM acquisition_channels ac
JOIN campaigns cp
    ON cp.channel_id = ac.channel_id
JOIN acquisition_periods ap
    ON ap.campaign_id = cp.campaign_id
GROUP BY ac.channel_code;

-- ============================================================
-- 14. CUSTOMER ECONOMICS REPORTING VIEW
-- ============================================================

CREATE OR REPLACE VIEW customer_economics_report AS
WITH acquisition AS (
    SELECT
        c.customer_id,
        c.organization_id,
        c.cohort_id,
        c.acquisition_period_id,
        ap.new_customers,

        (
            ap.advertising_cost +
            ap.sales_cost +
            ap.marketing_cost
        ) / ap.new_customers AS cac

    FROM customers c
    JOIN acquisition_periods ap
        ON ap.acquisition_period_id = c.acquisition_period_id
),
monthly AS (
    SELECT
        customer_id,
        AVG(net_revenue) AS average_monthly_revenue,
        AVG(variable_cost) AS average_monthly_variable_cost,
        AVG(contribution) AS average_monthly_contribution
    FROM customer_monthly_economics
    GROUP BY customer_id
),
lifetime AS (
    SELECT DISTINCT ON (organization_id, channel_id)
        organization_id,
        channel_id,
        expected_lifetime_months,
        monthly_churn_rate
    FROM customer_lifetime_assumptions
    ORDER BY organization_id, channel_id, effective_from DESC
)
SELECT
    a.customer_id,
    a.organization_id,
    a.cohort_id,
    a.cac,
    m.average_monthly_revenue,
    m.average_monthly_variable_cost,
    m.average_monthly_contribution,
    l.expected_lifetime_months,
    l.monthly_churn_rate,

    m.average_monthly_contribution *
        l.expected_lifetime_months AS contribution_ltv,

    CASE
        WHEN m.average_monthly_revenue > 0
        THEN ROUND(
            m.average_monthly_contribution /
            m.average_monthly_revenue * 100,
            2
        )
        ELSE 0
    END AS contribution_margin_percent,

    CASE
        WHEN a.cac > 0
        THEN ROUND(
            (
                m.average_monthly_contribution *
                l.expected_lifetime_months
            ) / a.cac,
            4
        )
        ELSE NULL
    END AS ltv_cac_ratio,

    CASE
        WHEN m.average_monthly_contribution > 0
        THEN ROUND(
            a.cac / m.average_monthly_contribution,
            4
        )
        ELSE NULL
    END AS payback_months

FROM acquisition a
JOIN monthly m
    ON m.customer_id = a.customer_id
JOIN lifetime l
    ON l.organization_id = a.organization_id;

-- ============================================================
-- 15. POLICY EVALUATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_unit_economics(
    p_customer_id BIGINT,
    p_acquisition_period_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    cac NUMERIC,
    monthly_contribution NUMERIC,
    contribution_margin NUMERIC,
    gross_ltv NUMERIC,
    contribution_ltv NUMERIC,
    ltv_cac_ratio NUMERIC,
    payback_months NUMERIC,
    result_status evaluation_status
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_customer customers%ROWTYPE;
    v_period acquisition_periods%ROWTYPE;
    v_policy economics_policies%ROWTYPE;
    v_assumption customer_lifetime_assumptions%ROWTYPE;

    v_monthly_revenue NUMERIC;
    v_variable_cost NUMERIC;
    v_contribution NUMERIC;
    v_cac NUMERIC;
    v_margin NUMERIC;
    v_gross_ltv NUMERIC;
    v_contribution_ltv NUMERIC;
    v_ratio NUMERIC;
    v_payback NUMERIC;
BEGIN
    SELECT * INTO v_customer
    FROM customers
    WHERE customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found: %', p_customer_id;
    END IF;

    SELECT * INTO v_period
    FROM acquisition_periods
    WHERE acquisition_period_id = p_acquisition_period_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Acquisition period not found';
    END IF;

    SELECT * INTO v_policy
    FROM economics_policies
    WHERE policy_id = p_policy_id
      AND organization_id = v_customer.organization_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active policy for organization';
    END IF;

    SELECT *
    INTO v_assumption
    FROM customer_lifetime_assumptions
    WHERE organization_id = v_customer.organization_id
      AND channel_id = (
          SELECT channel_id
          FROM campaigns
          WHERE campaign_id = v_period.campaign_id
      )
      AND effective_from <= CURRENT_DATE
      AND (effective_until IS NULL OR effective_until >= CURRENT_DATE)
    ORDER BY effective_from DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Lifetime assumptions unavailable';
    END IF;

    IF v_period.new_customers <= 0 THEN
        RAISE EXCEPTION 'Invalid acquisition denominator';
    END IF;

    SELECT
        AVG(net_revenue),
        AVG(variable_cost),
        AVG(contribution)
    INTO
        v_monthly_revenue,
        v_variable_cost,
        v_contribution
    FROM customer_monthly_economics
    WHERE customer_id = p_customer_id;

    IF v_contribution IS NULL THEN
        RAISE EXCEPTION 'Customer has no financial observations';
    END IF;

    v_cac := (
        v_period.advertising_cost +
        v_period.sales_cost +
        v_period.marketing_cost
    ) / v_period.new_customers;

    v_margin := CASE
        WHEN v_monthly_revenue > 0
        THEN v_contribution / v_monthly_revenue
        ELSE 0
    END;

    v_gross_ltv :=
        v_monthly_revenue * v_assumption.expected_lifetime_months;

    v_contribution_ltv :=
        v_contribution * v_assumption.expected_lifetime_months;

    v_ratio := CASE
        WHEN v_cac > 0 THEN v_contribution_ltv / v_cac
        ELSE NULL
    END;

    v_payback := calculate_payback(v_cac, v_contribution);

    IF v_contribution <= 0 THEN
        result_status := 'negative_contribution';

    ELSIF v_ratio <= 1 THEN
        result_status := 'unprofitable';

    ELSIF v_ratio < v_policy.minimum_ltv_cac_ratio
       OR v_margin < v_policy.minimum_contribution_margin THEN
        result_status := 'unprofitable';

    ELSIF v_payback IS NULL
       OR v_payback > v_policy.maximum_payback_months
       OR v_payback > v_assumption.expected_lifetime_months THEN
        result_status := 'payback_exceeds_lifetime';

    ELSE
        result_status := 'profitable';
    END IF;

    cac := ROUND(v_cac, 2);
    monthly_contribution := ROUND(v_contribution, 2);
    contribution_margin := ROUND(v_margin, 6);
    gross_ltv := ROUND(v_gross_ltv, 2);
    contribution_ltv := ROUND(v_contribution_ltv, 2);
    ltv_cac_ratio := ROUND(v_ratio, 4);
    payback_months := v_payback;

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 16. TRANSACTIONAL EVALUATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE process_customer_economics(
    p_customer_id BIGINT,
    p_acquisition_period_id BIGINT,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
BEGIN
    SELECT *
    INTO v_result
    FROM evaluate_unit_economics(
        p_customer_id,
        p_acquisition_period_id,
        p_policy_id
    );

    INSERT INTO unit_economics_evaluations (
        customer_id,
        acquisition_period_id,
        policy_id,
        evaluation_date,
        cac,
        monthly_contribution,
        contribution_margin,
        gross_ltv,
        contribution_ltv,
        ltv_cac_ratio,
        payback_months,
        status
    )
    VALUES (
        p_customer_id,
        p_acquisition_period_id,
        p_policy_id,
        CURRENT_DATE,
        v_result.cac,
        v_result.monthly_contribution,
        v_result.contribution_margin,
        v_result.gross_ltv,
        v_result.contribution_ltv,
        v_result.ltv_cac_ratio,
        v_result.payback_months,
        v_result.result_status
    )
    ON CONFLICT (
        customer_id,
        acquisition_period_id,
        evaluation_date
    )
    DO UPDATE SET
        policy_id = EXCLUDED.policy_id,
        cac = EXCLUDED.cac,
        monthly_contribution = EXCLUDED.monthly_contribution,
        contribution_margin = EXCLUDED.contribution_margin,
        gross_ltv = EXCLUDED.gross_ltv,
        contribution_ltv = EXCLUDED.contribution_ltv,
        ltv_cac_ratio = EXCLUDED.ltv_cac_ratio,
        payback_months = EXCLUDED.payback_months,
        status = EXCLUDED.status;
END;
$$;

-- ============================================================
-- 17. SAMPLE ORGANIZATION
-- ============================================================

INSERT INTO organizations (
    organization_name,
    currency_code
)
VALUES ('Acme Subscription Analytics', 'INR');

INSERT INTO customer_cohorts (
    organization_id,
    cohort_name,
    cohort_start,
    cohort_end
)
SELECT organization_id, '2026-Q1', '2026-01-01', '2026-03-31'
FROM organizations
WHERE organization_name = 'Acme Subscription Analytics';

INSERT INTO campaigns (
    organization_id,
    channel_id,
    campaign_name,
    campaign_status,
    start_date,
    end_date
)
SELECT
    o.organization_id,
    ac.channel_id,
    'January Paid Search',
    'completed',
    '2026-01-01',
    '2026-01-31'
FROM organizations o
JOIN acquisition_channels ac
    ON ac.channel_code = 'paid_search'
WHERE o.organization_name = 'Acme Subscription Analytics';

INSERT INTO campaigns (
    organization_id,
    channel_id,
    campaign_name,
    campaign_status,
    start_date,
    end_date
)
SELECT
    o.organization_id,
    ac.channel_id,
    'January Social Campaign',
    'completed',
    '2026-01-01',
    '2026-01-31'
FROM organizations o
JOIN acquisition_channels ac
    ON ac.channel_code = 'social'
WHERE o.organization_name = 'Acme Subscription Analytics';

INSERT INTO acquisition_periods (
    campaign_id,
    period_start,
    period_end,
    advertising_cost,
    sales_cost,
    marketing_cost,
    new_customers
)
SELECT
    campaign_id,
    '2026-01-01',
    '2026-01-31',
    30000,
    10000,
    10000,
    100
FROM campaigns
WHERE campaign_name = 'January Paid Search';

INSERT INTO acquisition_periods (
    campaign_id,
    period_start,
    period_end,
    advertising_cost,
    sales_cost,
    marketing_cost,
    new_customers
)
SELECT
    campaign_id,
    '2026-01-01',
    '2026-01-31',
    18000,
    6000,
    6000,
    120
FROM campaigns
WHERE campaign_name = 'January Social Campaign';

INSERT INTO customer_lifetime_assumptions (
    organization_id,
    channel_id,
    expected_lifetime_months,
    monthly_churn_rate,
    effective_from
)
SELECT
    o.organization_id,
    ac.channel_id,
    18,
    0.04,
    '2026-01-01'
FROM organizations o
CROSS JOIN acquisition_channels ac
WHERE o.organization_name = 'Acme Subscription Analytics'
  AND ac.channel_code = 'paid_search';

INSERT INTO customer_lifetime_assumptions (
    organization_id,
    channel_id,
    expected_lifetime_months,
    monthly_churn_rate,
    effective_from
)
SELECT
    o.organization_id,
    ac.channel_id,
    15,
    0.05,
    '2026-01-01'
FROM organizations o
CROSS JOIN acquisition_channels ac
WHERE o.organization_name = 'Acme Subscription Analytics'
  AND ac.channel_code = 'social';

INSERT INTO economics_policies (
    organization_id,
    policy_name,
    minimum_ltv_cac_ratio,
    maximum_payback_months,
    minimum_contribution_margin,
    effective_from
)
SELECT
    organization_id,
    'Standard Growth Policy',
    3,
    12,
    0.50,
    '2026-01-01'
FROM organizations
WHERE organization_name = 'Acme Subscription Analytics';

-- ============================================================
-- 18. SAMPLE CUSTOMERS
-- ============================================================

INSERT INTO customers (
    organization_id,
    cohort_id,
    acquisition_period_id,
    external_customer_reference,
    acquisition_date,
    status
)
SELECT
    o.organization_id,
    cc.cohort_id,
    ap.acquisition_period_id,
    'CUSTOMER-001',
    '2026-01-10',
    'active'
FROM organizations o
JOIN customer_cohorts cc
    ON cc.organization_id = o.organization_id
JOIN campaigns cp
    ON cp.organization_id = o.organization_id
   AND cp.campaign_name = 'January Paid Search'
JOIN acquisition_periods ap
    ON ap.campaign_id = cp.campaign_id
WHERE o.organization_name = 'Acme Subscription Analytics';

INSERT INTO customers (
    organization_id,
    cohort_id,
    acquisition_period_id,
    external_customer_reference,
    acquisition_date,
    status
)
SELECT
    o.organization_id,
    cc.cohort_id,
    ap.acquisition_period_id,
    'CUSTOMER-002',
    '2026-01-15',
    'active'
FROM organizations o
JOIN customer_cohorts cc
    ON cc.organization_id = o.organization_id
JOIN campaigns cp
    ON cp.organization_id = o.organization_id
   AND cp.campaign_name = 'January Social Campaign'
JOIN acquisition_periods ap
    ON ap.campaign_id = cp.campaign_id
WHERE o.organization_name = 'Acme Subscription Analytics';

-- ============================================================
-- 19. CUSTOMER FINANCIAL OBSERVATIONS
-- ============================================================

INSERT INTO customer_monthly_economics (
    customer_id,
    reporting_month,
    revenue,
    variable_cost,
    refunds,
    service_credits
)
SELECT
    customer_id,
    '2026-01-01',
    1000,
    300,
    0,
    0
FROM customers
WHERE external_customer_reference = 'CUSTOMER-001';

INSERT INTO customer_monthly_economics (
    customer_id,
    reporting_month,
    revenue,
    variable_cost,
    refunds,
    service_credits
)
SELECT
    customer_id,
    '2026-02-01',
    1050,
    320,
    50,
    0
FROM customers
WHERE external_customer_reference = 'CUSTOMER-001';

INSERT INTO customer_monthly_economics (
    customer_id,
    reporting_month,
    revenue,
    variable_cost,
    refunds,
    service_credits
)
SELECT
    customer_id,
    '2026-01-01',
    800,
    280,
    0,
    0
FROM customers
WHERE external_customer_reference = 'CUSTOMER-002';

-- ============================================================
-- 20. RETRIEVAL QUERIES
-- ============================================================

-- Acquisition costs by campaign.
SELECT
    cp.campaign_name,
    ac.channel_code,
    ap.period_start,
    ap.period_end,
    ap.new_customers,
    ap.advertising_cost + ap.sales_cost + ap.marketing_cost
        AS total_acquisition_cost,
    calculate_cac(cp.campaign_id) AS campaign_cac
FROM campaigns cp
JOIN acquisition_channels ac
    ON ac.channel_id = cp.channel_id
JOIN acquisition_periods ap
    ON ap.campaign_id = cp.campaign_id
ORDER BY campaign_cac;

-- Customer-level financial observations.
SELECT
    c.external_customer_reference,
    me.reporting_month,
    me.net_revenue,
    me.variable_cost,
    me.contribution
FROM customers c
JOIN customer_monthly_economics me
    ON me.customer_id = c.customer_id
ORDER BY c.customer_id, me.reporting_month;

-- ============================================================
-- 21. AGGREGATION AND REPORTING
-- ============================================================

SELECT * FROM channel_acquisition_performance
ORDER BY cac;

SELECT * FROM cohort_economics
ORDER BY cohort_name;

SELECT
    COUNT(*) AS evaluated_customers,
    AVG(cac) AS average_cac,
    AVG(contribution_ltv) AS average_contribution_ltv,
    AVG(ltv_cac_ratio) AS average_ltv_cac,
    AVG(payback_months) AS average_payback
FROM customer_economics_report;

-- ============================================================
-- 22. VALIDATION QUERIES
-- ============================================================

-- Revenue observations with zero contribution.
SELECT
    customer_id,
    reporting_month,
    revenue,
    variable_cost,
    contribution
FROM customer_monthly_economics
WHERE contribution <= 0;

-- Customers missing financial observations.
SELECT c.customer_id, c.external_customer_reference
FROM customers c
LEFT JOIN customer_monthly_economics me
    ON me.customer_id = c.customer_id
WHERE me.customer_id IS NULL;

-- Customer acquisition records without corresponding evaluations.
SELECT c.customer_id
FROM customers c
LEFT JOIN unit_economics_evaluations e
    ON e.customer_id = c.customer_id
WHERE e.evaluation_id IS NULL;

-- ============================================================
-- 23. EVALUATION WORKFLOW
-- ============================================================

DO $$
DECLARE
    v_customer_id BIGINT;
    v_period_id BIGINT;
    v_policy_id BIGINT;
BEGIN
    SELECT customer_id INTO v_customer_id
    FROM customers
    WHERE external_customer_reference = 'CUSTOMER-001';

    SELECT acquisition_period_id INTO v_period_id
    FROM acquisition_periods ap
    JOIN campaigns cp
        ON cp.campaign_id = ap.campaign_id
    WHERE cp.campaign_name = 'January Paid Search';

    SELECT policy_id INTO v_policy_id
    FROM economics_policies
    WHERE policy_name = 'Standard Growth Policy';

    CALL process_customer_economics(
        v_customer_id,
        v_period_id,
        v_policy_id
    );
END;
$$;

-- ============================================================
-- 24. EVALUATION RESULTS
-- ============================================================

SELECT
    e.evaluation_id,
    c.external_customer_reference,
    e.cac,
    e.monthly_contribution,
    e.contribution_margin,
    e.gross_ltv,
    e.contribution_ltv,
    e.ltv_cac_ratio,
    e.payback_months,
    e.status
FROM unit_economics_evaluations e
JOIN customers c
    ON c.customer_id = e.customer_id
ORDER BY e.evaluation_date DESC;

-- ============================================================
-- 25. SENSITIVITY ANALYSIS
-- ============================================================

WITH scenarios AS (
    SELECT *
    FROM (
        VALUES
            (-0.20::NUMERIC),
            (-0.10::NUMERIC),
            (0.00::NUMERIC),
            (0.10::NUMERIC),
            (0.20::NUMERIC)
    ) AS s(revenue_change)
),
baseline AS (
    SELECT
        1000::NUMERIC AS monthly_revenue,
        300::NUMERIC AS variable_cost,
        18::NUMERIC AS lifetime_months,
        500::NUMERIC AS cac
)
SELECT
    s.revenue_change * 100 AS revenue_change_percent,
    b.monthly_revenue * (1 + s.revenue_change)
        AS adjusted_revenue,

    b.monthly_revenue * (1 + s.revenue_change)
        - b.variable_cost AS adjusted_contribution,

    (
        b.monthly_revenue * (1 + s.revenue_change)
        - b.variable_cost
    ) * b.lifetime_months AS contribution_ltv,

    CASE
        WHEN b.cac > 0 THEN ROUND(
            (
                (
                    b.monthly_revenue * (1 + s.revenue_change)
                    - b.variable_cost
                ) * b.lifetime_months
            ) / b.cac,
            2
        )
        ELSE NULL
    END AS ltv_cac_ratio

FROM scenarios s
CROSS JOIN baseline b
ORDER BY s.revenue_change;

-- ============================================================
-- 26. AUDIT RETRIEVAL
-- ============================================================

SELECT *
FROM economics_audit_log
ORDER BY changed_at DESC;

COMMIT;

-- ============================================================
-- 27. OPERATIONAL NOTES
-- ============================================================
--
-- 1. CAC allocation must use a consistent acquisition period.
-- 2. Campaign-level CAC is an aggregate, not necessarily an
--    individually observed customer cost.
-- 3. Contribution LTV is distinct from revenue-based gross LTV.
-- 4. Churn-based lifetime estimates require statistical validation.
-- 5. Monthly economics should be measured using consistent periods.
-- 6. Policy thresholds are business decisions, not universal laws.
-- 7. Production deployments should restrict permissions on
--    evaluation and audit tables.
-- 8. Large installations should partition monthly observations
--    by reporting_month and monitor query plans.
-- 9. Financial data should use a controlled currency conversion
--    policy before aggregating across currencies.
-- 10. This demonstration uses expected lifetime assumptions.
--     It does not claim that every customer remains active for
--     the assumed number of months.
