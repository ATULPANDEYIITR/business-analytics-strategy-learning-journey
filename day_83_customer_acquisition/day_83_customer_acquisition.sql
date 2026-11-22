-- ================================================================
-- CUSTOMER ACQUISITION: CHANNEL MANAGEMENT AND CAC ANALYSIS
-- PostgreSQL 15+
--
-- Models:
-- 1. Acquisition channels and marketing campaigns
-- 2. Campaign expenditure and conversion funnels
-- 3. Customer acquisition and attribution
-- 4. Customer lifetime value and gross margin
-- 5. Channel-level CAC and ROAS
-- 6. Acquisition policies and budget allocation
-- 7. Campaign lifecycle and data integrity
--
-- Monetary values are stored using NUMERIC.
-- Reporting currency in this demonstration: INR.
-- ================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS acquisition;

SET search_path TO acquisition, public;

-- ================================================================
-- 1. DOMAIN TYPES
-- ================================================================

CREATE TYPE channel_type AS ENUM (
    'paid_search',
    'paid_social',
    'organic_search',
    'email',
    'referral',
    'affiliate',
    'content',
    'events',
    'direct'
);

CREATE TYPE campaign_status AS ENUM (
    'draft',
    'active',
    'paused',
    'completed'
);

CREATE TYPE attribution_model AS ENUM (
    'first_touch',
    'last_touch',
    'linear'
);

CREATE TYPE decision_type AS ENUM (
    'scale',
    'optimize',
    'reduce',
    'insufficient_data'
);

-- ================================================================
-- 2. ACQUISITION CHANNELS
-- ================================================================

CREATE TABLE acquisition_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code channel_type NOT NULL UNIQUE,
    channel_name VARCHAR(100) NOT NULL,
    channel_description TEXT NOT NULL,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO acquisition_channels (
    channel_code,
    channel_name,
    channel_description,
    is_paid
)
VALUES
    ('paid_search', 'Paid Search', 'Search engine advertising.', TRUE),
    ('paid_social', 'Paid Social', 'Paid social network campaigns.', TRUE),
    ('organic_search', 'Organic Search', 'Unpaid search engine acquisition.', FALSE),
    ('email', 'Email Marketing', 'Permission-based email acquisition.', FALSE),
    ('referral', 'Referral', 'Customer and partner referrals.', FALSE),
    ('affiliate', 'Affiliate', 'Commission-based partner acquisition.', TRUE),
    ('content', 'Content Marketing', 'Content-led acquisition.', FALSE),
    ('events', 'Events', 'Events and conferences.', TRUE),
    ('direct', 'Direct', 'Direct and unclassified visits.', FALSE);

-- ================================================================
-- 3. CAMPAIGNS
-- ================================================================

CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_code VARCHAR(40) NOT NULL UNIQUE,
    campaign_name VARCHAR(200) NOT NULL,

    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    budget NUMERIC(16,2) NOT NULL,
    spend NUMERIC(16,2) NOT NULL DEFAULT 0,
    revenue NUMERIC(16,2) NOT NULL DEFAULT 0,

    impressions BIGINT NOT NULL DEFAULT 0,
    clicks BIGINT NOT NULL DEFAULT 0,
    leads BIGINT NOT NULL DEFAULT 0,
    conversions BIGINT NOT NULL DEFAULT 0,

    status campaign_status NOT NULL DEFAULT 'draft',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT campaign_name_nonempty
        CHECK (LENGTH(TRIM(campaign_name)) > 0),

    CONSTRAINT valid_campaign_dates
        CHECK (end_date >= start_date),

    CONSTRAINT valid_campaign_budget
        CHECK (budget >= 0 AND spend >= 0 AND revenue >= 0),

    CONSTRAINT spend_within_budget
        CHECK (spend <= budget),

    CONSTRAINT valid_funnel_metrics
        CHECK (
            impressions >= clicks
            AND clicks >= leads
            AND leads >= conversions
        )
);

CREATE INDEX idx_campaign_channel
    ON campaigns(channel_id);

CREATE INDEX idx_campaign_status_dates
    ON campaigns(status, start_date, end_date);

CREATE INDEX idx_campaign_code
    ON campaigns(campaign_code);

-- ================================================================
-- 4. CUSTOMER RECORDS
-- ================================================================

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_customer_id VARCHAR(100) NOT NULL UNIQUE,

    acquired_by_campaign BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    acquisition_channel BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),

    acquisition_date DATE NOT NULL,

    first_purchase_revenue NUMERIC(16,2) NOT NULL,
    monthly_revenue NUMERIC(16,2) NOT NULL DEFAULT 0,

    gross_margin_rate NUMERIC(6,5) NOT NULL,
    monthly_retention_rate NUMERIC(6,5) NOT NULL DEFAULT 0.90,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_customer_revenue
        CHECK (
            first_purchase_revenue >= 0
            AND monthly_revenue >= 0
        ),

    CONSTRAINT valid_gross_margin
        CHECK (gross_margin_rate BETWEEN 0 AND 1),

    CONSTRAINT valid_retention
        CHECK (monthly_retention_rate BETWEEN 0 AND 1)
);

CREATE INDEX idx_customer_campaign
    ON customers(acquired_by_campaign);

CREATE INDEX idx_customer_channel_date
    ON customers(acquisition_channel, acquisition_date);

CREATE INDEX idx_customer_acquisition_date
    ON customers(acquisition_date);

-- ================================================================
-- 5. CUSTOMER TOUCHPOINTS
-- ================================================================

CREATE TABLE customer_touchpoints (
    touchpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id) ON DELETE CASCADE,

    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),

    campaign_id BIGINT
        REFERENCES campaigns(campaign_id),

    occurred_at TIMESTAMPTZ NOT NULL,

    touchpoint_type VARCHAR(50) NOT NULL,

    source_reference VARCHAR(200),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_touchpoints_customer_time
    ON customer_touchpoints(customer_id, occurred_at);

CREATE INDEX idx_touchpoints_channel_time
    ON customer_touchpoints(channel_id, occurred_at);

-- ================================================================
-- 6. ATTRIBUTION RESULTS
-- ================================================================

CREATE TABLE customer_attribution (
    attribution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id) ON DELETE CASCADE,

    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),

    attribution_method attribution_model NOT NULL,

    attribution_weight NUMERIC(8,7) NOT NULL,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_attribution_weight
        CHECK (attribution_weight BETWEEN 0 AND 1),

    CONSTRAINT unique_customer_channel_model
        UNIQUE (
            customer_id,
            channel_id,
            attribution_method
        )
);

CREATE INDEX idx_attribution_channel_method
    ON customer_attribution(channel_id, attribution_method);

-- ================================================================
-- 7. CAMPAIGN SPEND TRANSACTIONS
-- ================================================================

CREATE TABLE campaign_spend_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_id BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    transaction_reference VARCHAR(100) NOT NULL UNIQUE,

    amount NUMERIC(16,2) NOT NULL,

    expense_date DATE NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_spend_amount
        CHECK (amount > 0)
);

CREATE INDEX idx_spend_campaign_date
    ON campaign_spend_transactions(campaign_id, expense_date);

-- ================================================================
-- 8. ACQUISITION POLICY
-- ================================================================

CREATE TABLE acquisition_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(150) NOT NULL UNIQUE,

    minimum_customers INTEGER NOT NULL DEFAULT 10,

    minimum_ltv_cac NUMERIC(10,4) NOT NULL DEFAULT 3.0,

    maximum_cac NUMERIC(16,2) NOT NULL DEFAULT 1000,

    minimum_roas NUMERIC(10,4) NOT NULL DEFAULT 1.0,

    projection_months INTEGER NOT NULL DEFAULT 24,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (minimum_customers >= 1),
    CHECK (minimum_ltv_cac > 0),
    CHECK (maximum_cac > 0),
    CHECK (minimum_roas >= 0),
    CHECK (projection_months >= 1)
);

INSERT INTO acquisition_policies (
    policy_name,
    minimum_customers,
    minimum_ltv_cac,
    maximum_cac,
    minimum_roas,
    projection_months
)
VALUES (
    'Standard Acquisition Policy',
    2,
    3.0,
    1000,
    1.0,
    24
);

-- ================================================================
-- 9. CHANNEL BUDGET ALLOCATION
-- ================================================================

CREATE TABLE channel_budget_allocations (
    allocation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),

    allocation_period DATE NOT NULL,

    approved_budget NUMERIC(16,2) NOT NULL,

    allocated_budget NUMERIC(16,2) NOT NULL DEFAULT 0,

    expected_cac NUMERIC(16,2) NOT NULL,

    approved_by VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_allocation_amounts
        CHECK (
            approved_budget >= 0
            AND allocated_budget >= 0
            AND allocated_budget <= approved_budget
            AND expected_cac > 0
        ),

    UNIQUE(channel_id, allocation_period)
);

-- ================================================================
-- 10. CAMPAIGN STATE TRANSITION FUNCTION
-- ================================================================

CREATE OR REPLACE FUNCTION validate_campaign_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'draft' AND NEW.status = 'active')
        OR
        (OLD.status = 'active' AND NEW.status IN ('paused', 'completed'))
        OR
        (OLD.status = 'paused' AND NEW.status IN ('active', 'completed'))
    ) THEN
        RAISE EXCEPTION
            'Invalid campaign transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    NEW.updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_campaign_state_transition
BEFORE UPDATE OF status ON campaigns
FOR EACH ROW
EXECUTE FUNCTION validate_campaign_transition();

-- ================================================================
-- 11. CUSTOMER REGISTRATION VALIDATION
-- ================================================================

CREATE OR REPLACE FUNCTION validate_customer_acquisition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    campaign_record RECORD;
BEGIN
    SELECT
        c.channel_id,
        c.start_date,
        c.end_date,
        c.status
    INTO campaign_record
    FROM campaigns c
    WHERE c.campaign_id = NEW.acquired_by_campaign;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign does not exist.';
    END IF;

    IF campaign_record.status <> 'active' THEN
        RAISE EXCEPTION 'Customer cannot be acquired through an inactive campaign.';
    END IF;

    IF campaign_record.channel_id <> NEW.acquisition_channel THEN
        RAISE EXCEPTION 'Customer acquisition channel does not match campaign.';
    END IF;

    IF NEW.acquisition_date NOT BETWEEN
        campaign_record.start_date AND campaign_record.end_date THEN
        RAISE EXCEPTION 'Customer acquisition date is outside campaign period.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_customer_acquisition
BEFORE INSERT ON customers
FOR EACH ROW
EXECUTE FUNCTION validate_customer_acquisition();

-- ================================================================
-- 12. SPEND TRANSACTION FUNCTION
-- ================================================================

CREATE OR REPLACE FUNCTION record_campaign_spend(
    p_campaign_id BIGINT,
    p_reference VARCHAR(100),
    p_amount NUMERIC(16,2),
    p_expense_date DATE,
    p_description TEXT DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    current_spend NUMERIC(16,2);
    current_budget NUMERIC(16,2);
    new_transaction_id BIGINT;
BEGIN
    IF p_amount IS NULL OR p_amount <= 0 THEN
        RAISE EXCEPTION 'Spend amount must be positive.';
    END IF;

    -- Lock the campaign row to prevent concurrent overspending.
    SELECT spend, budget
    INTO current_spend, current_budget
    FROM campaigns
    WHERE campaign_id = p_campaign_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign not found.';
    END IF;

    IF current_spend + p_amount > current_budget THEN
        RAISE EXCEPTION 'Campaign budget limit exceeded.';
    END IF;

    INSERT INTO campaign_spend_transactions (
        campaign_id,
        transaction_reference,
        amount,
        expense_date,
        description
    )
    VALUES (
        p_campaign_id,
        p_reference,
        p_amount,
        p_expense_date,
        p_description
    )
    RETURNING transaction_id INTO new_transaction_id;

    UPDATE campaigns
    SET spend = spend + p_amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE campaign_id = p_campaign_id;

    RETURN new_transaction_id;
END;
$$;

-- ================================================================
-- 13. LIFETIME VALUE FUNCTION
-- ================================================================

CREATE OR REPLACE FUNCTION calculate_customer_ltv(
    p_customer_id BIGINT,
    p_months INTEGER
)
RETURNS NUMERIC(16,2)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    customer_record RECORD;
    retained NUMERIC;
    recurring_profit NUMERIC := 0;
    initial_profit NUMERIC;
    monthly_profit NUMERIC;
    month_number INTEGER;
BEGIN
    IF p_months < 1 OR p_months > 600 THEN
        RAISE EXCEPTION 'Projection months must be between 1 and 600.';
    END IF;

    SELECT
        first_purchase_revenue,
        monthly_revenue,
        gross_margin_rate,
        monthly_retention_rate
    INTO customer_record
    FROM customers
    WHERE customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found.';
    END IF;

    initial_profit :=
        customer_record.first_purchase_revenue
        * customer_record.gross_margin_rate;

    monthly_profit :=
        customer_record.monthly_revenue
        * customer_record.gross_margin_rate;

    retained := 1;

    FOR month_number IN 1..p_months LOOP
        retained :=
            retained * customer_record.monthly_retention_rate;

        recurring_profit :=
            recurring_profit + retained * monthly_profit;
    END LOOP;

    RETURN ROUND(initial_profit + recurring_profit, 2);
END;
$$;

-- ================================================================
-- 14. CAMPAIGN PERFORMANCE VIEW
-- ================================================================

CREATE OR REPLACE VIEW campaign_performance AS
SELECT
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    ac.channel_name,
    c.status,
    c.budget,
    c.spend,
    c.revenue,
    c.impressions,
    c.clicks,
    c.leads,
    c.conversions,

    ROUND(
        100.0 * c.clicks / NULLIF(c.impressions, 0),
        2
    ) AS ctr_percent,

    ROUND(
        100.0 * c.leads / NULLIF(c.clicks, 0),
        2
    ) AS lead_conversion_percent,

    ROUND(
        100.0 * c.conversions / NULLIF(c.leads, 0),
        2
    ) AS customer_conversion_percent,

    ROUND(
        c.spend / NULLIF(c.conversions, 0),
        2
    ) AS cac,

    ROUND(
        c.spend / NULLIF(c.clicks, 0),
        2
    ) AS cost_per_click,

    ROUND(
        c.spend / NULLIF(c.leads, 0),
        2
    ) AS cost_per_lead,

    ROUND(
        c.revenue / NULLIF(c.spend, 0),
        4
    ) AS roas

FROM campaigns c
JOIN acquisition_channels ac
    ON ac.channel_id = c.channel_id;

-- ================================================================
-- 15. CUSTOMER LIFETIME VALUE VIEW
-- ================================================================

CREATE OR REPLACE VIEW customer_lifetime_value AS
SELECT
    c.customer_id,
    c.external_customer_id,
    c.acquired_by_campaign,
    c.acquisition_channel,
    ac.channel_name,
    c.acquisition_date,
    c.first_purchase_revenue,
    c.gross_margin_rate,

    ROUND(
        c.first_purchase_revenue * c.gross_margin_rate,
        2
    ) AS initial_gross_profit,

    calculate_customer_ltv(c.customer_id, 24) AS projected_ltv_24m

FROM customers c
JOIN acquisition_channels ac
    ON ac.channel_id = c.acquisition_channel;

-- ================================================================
-- 16. CHANNEL-LEVEL CAC AND LTV ANALYSIS
-- ================================================================

CREATE OR REPLACE VIEW channel_performance AS
WITH campaign_totals AS (
    SELECT
        channel_id,
        SUM(spend) AS total_spend,
        SUM(revenue) AS total_revenue,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        SUM(leads) AS total_leads
    FROM campaigns
    GROUP BY channel_id
),
customer_totals AS (
    SELECT
        acquisition_channel AS channel_id,
        COUNT(*) AS total_customers,
        SUM(first_purchase_revenue) AS initial_revenue,
        SUM(calculate_customer_ltv(customer_id, 24)) AS total_projected_profit
    FROM customers
    GROUP BY acquisition_channel
)
SELECT
    ac.channel_id,
    ac.channel_name,
    ac.is_paid,

    COALESCE(ct.total_spend, 0) AS total_spend,
    COALESCE(ut.total_customers, 0) AS total_customers,

    ROUND(
        ct.total_spend / NULLIF(ut.total_customers, 0),
        2
    ) AS cac,

    ROUND(
        ut.total_projected_profit /
        NULLIF(ut.total_customers, 0),
        2
    ) AS average_ltv,

    ROUND(
        (
            ut.total_projected_profit /
            NULLIF(ut.total_customers, 0)
        ) /
        NULLIF(
            ct.total_spend /
            NULLIF(ut.total_customers, 0),
            0
        ),
        2
    ) AS ltv_cac_ratio,

    ROUND(
        ct.total_revenue / NULLIF(ct.total_spend, 0),
        4
    ) AS roas,

    ROUND(
        100.0 * ct.total_clicks /
        NULLIF(ct.total_impressions, 0),
        2
    ) AS ctr_percent

FROM acquisition_channels ac
LEFT JOIN campaign_totals ct
    ON ct.channel_id = ac.channel_id
LEFT JOIN customer_totals ut
    ON ut.channel_id = ac.channel_id;

-- ================================================================
-- 17. ATTRIBUTION VALIDATION FUNCTION
-- ================================================================

CREATE OR REPLACE FUNCTION validate_attribution_weights(
    p_customer_id BIGINT,
    p_model attribution_model
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    total_weight NUMERIC;
BEGIN
    SELECT COALESCE(SUM(attribution_weight), 0)
    INTO total_weight
    FROM customer_attribution
    WHERE customer_id = p_customer_id
      AND attribution_method = p_model;

    RETURN ABS(total_weight - 1.0) < 0.00001;
END;
$$;

-- ================================================================
-- 18. ATTRIBUTION REPORT
-- ================================================================

CREATE OR REPLACE VIEW attribution_performance AS
SELECT
    ca.attribution_method,
    ac.channel_name,
    COUNT(DISTINCT ca.customer_id) AS attributed_customers,

    ROUND(
        SUM(ca.attribution_weight),
        4
    ) AS weighted_customer_credit

FROM customer_attribution ca
JOIN acquisition_channels ac
    ON ac.channel_id = ca.channel_id

GROUP BY
    ca.attribution_method,
    ac.channel_name;

-- ================================================================
-- 19. ACQUISITION DECISION FUNCTION
-- ================================================================

CREATE OR REPLACE FUNCTION evaluate_channel(
    p_channel_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    channel_name VARCHAR,
    customer_count BIGINT,
    calculated_cac NUMERIC,
    calculated_ltv NUMERIC,
    ltv_cac NUMERIC,
    decision decision_type
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    policy RECORD;
    metrics RECORD;
    calculated_ratio NUMERIC;
    selected_decision decision_type;
BEGIN
    SELECT *
    INTO policy
    FROM acquisition_policies
    WHERE policy_id = p_policy_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active acquisition policy not found.';
    END IF;

    SELECT
        ac.channel_name,
        COUNT(DISTINCT c.customer_id) AS customer_count,
        COALESCE(SUM(DISTINCT ca.spend), 0) AS unused_spend
    INTO metrics
    FROM acquisition_channels ac
    LEFT JOIN customers c
        ON c.acquisition_channel = ac.channel_id
    LEFT JOIN campaigns ca
        ON ca.channel_id = ac.channel_id
    WHERE ac.channel_id = p_channel_id
    GROUP BY ac.channel_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Channel not found.';
    END IF;

    SELECT
        COALESCE(SUM(spend), 0)
    INTO metrics.unused_spend
    FROM campaigns
    WHERE channel_id = p_channel_id;

    IF metrics.customer_count = 0 THEN
        RETURN QUERY
        SELECT
            metrics.channel_name,
            0::BIGINT,
            NULL::NUMERIC,
            NULL::NUMERIC,
            NULL::NUMERIC,
            'insufficient_data'::decision_type;

        RETURN;
    END IF;

    RETURN QUERY
    WITH customer_economics AS (
        SELECT
            AVG(
                calculate_customer_ltv(
                    customer_id,
                    policy.projection_months
                )
            ) AS average_ltv
        FROM customers
        WHERE acquisition_channel = p_channel_id
    ),
    channel_spend AS (
        SELECT COALESCE(SUM(spend), 0) AS total_spend
        FROM campaigns
        WHERE channel_id = p_channel_id
    )
    SELECT
        metrics.channel_name,
        metrics.customer_count,

        ROUND(
            cs.total_spend / NULLIF(metrics.customer_count, 0),
            2
        ),

        ROUND(ce.average_ltv, 2),

        ROUND(
            ce.average_ltv /
            NULLIF(
                cs.total_spend /
                NULLIF(metrics.customer_count, 0),
                0
            ),
            2
        ),

        CASE
            WHEN metrics.customer_count < policy.minimum_customers
                THEN 'insufficient_data'::decision_type

            WHEN cs.total_spend = 0
                THEN 'insufficient_data'::decision_type

            WHEN ce.average_ltv /
                 NULLIF(
                     cs.total_spend /
                     NULLIF(metrics.customer_count, 0),
                     0
                 ) >= policy.minimum_ltv_cac

                 AND cs.total_spend /
                     NULLIF(metrics.customer_count, 0)
                     <= policy.maximum_cac
                THEN 'scale'::decision_type

            WHEN ce.average_ltv /
                 NULLIF(
                     cs.total_spend /
                     NULLIF(metrics.customer_count, 0),
                     0
                 ) >= 1
                THEN 'optimize'::decision_type

            ELSE 'reduce'::decision_type
        END

    FROM customer_economics ce
    CROSS JOIN channel_spend cs;
END;
$$;

-- ================================================================
-- 20. SAMPLE CAMPAIGN DATA
-- ================================================================

INSERT INTO campaigns (
    campaign_code,
    campaign_name,
    channel_id,
    start_date,
    end_date,
    budget,
    spend,
    revenue,
    impressions,
    clicks,
    leads,
    conversions,
    status
)
SELECT
    data.campaign_code,
    data.campaign_name,
    ac.channel_id,
    DATE '2026-01-01',
    DATE '2026-12-31',
    data.budget,
    data.spend,
    data.revenue,
    data.impressions,
    data.clicks,
    data.leads,
    data.conversions,
    'active'::campaign_status
FROM (
    VALUES
        (
            'C001', 'Google Search Acquisition',
            'paid_search'::channel_type,
            50000::NUMERIC, 42000::NUMERIC, 180000::NUMERIC,
            500000::BIGINT, 25000::BIGINT, 5000::BIGINT, 1000::BIGINT
        ),
        (
            'C002', 'Social Media Acquisition',
            'paid_social'::channel_type,
            40000::NUMERIC, 36000::NUMERIC, 90000::NUMERIC,
            800000::BIGINT, 40000::BIGINT, 6000::BIGINT, 600::BIGINT
        ),
        (
            'C003', 'Organic Search Program',
            'organic_search'::channel_type,
            20000::NUMERIC, 15000::NUMERIC, 150000::NUMERIC,
            600000::BIGINT, 30000::BIGINT, 4500::BIGINT, 900::BIGINT
        ),
        (
            'C004', 'Referral Program',
            'referral'::channel_type,
            15000::NUMERIC, 12000::NUMERIC, 140000::NUMERIC,
            100000::BIGINT, 10000::BIGINT, 3000::BIGINT, 750::BIGINT
        ),
        (
            'C005', 'Email Acquisition',
            'email'::channel_type,
            10000::NUMERIC, 7000::NUMERIC, 110000::NUMERIC,
            200000::BIGINT, 12000::BIGINT, 3600::BIGINT, 720::BIGINT
        )
) AS data(
    campaign_code,
    campaign_name,
    channel_code,
    budget,
    spend,
    revenue,
    impressions,
    clicks,
    leads,
    conversions
)
JOIN acquisition_channels ac
    ON ac.channel_code = data.channel_code;

-- ================================================================
-- 21. SAMPLE CUSTOMER DATA
-- ================================================================

INSERT INTO customers (
    external_customer_id,
    acquired_by_campaign,
    acquisition_channel,
    acquisition_date,
    first_purchase_revenue,
    monthly_revenue,
    gross_margin_rate,
    monthly_retention_rate
)
SELECT
    data.external_id,
    c.campaign_id,
    ac.channel_id,
    DATE '2026-06-15',
    data.first_purchase,
    100,
    data.gross_margin,
    data.retention
FROM (
    VALUES
        ('U001', 'C001', 'paid_search'::channel_type, 120::NUMERIC, 0.75::NUMERIC, 0.92::NUMERIC),
        ('U002', 'C001', 'paid_search'::channel_type, 150::NUMERIC, 0.75::NUMERIC, 0.92::NUMERIC),
        ('U003', 'C002', 'paid_social'::channel_type, 90::NUMERIC, 0.65::NUMERIC, 0.90::NUMERIC),
        ('U004', 'C002', 'paid_social'::channel_type, 110::NUMERIC, 0.65::NUMERIC, 0.90::NUMERIC),
        ('U005', 'C003', 'organic_search'::channel_type, 140::NUMERIC, 0.80::NUMERIC, 0.93::NUMERIC),
        ('U006', 'C003', 'organic_search'::channel_type, 160::NUMERIC, 0.80::NUMERIC, 0.93::NUMERIC),
        ('U007', 'C004', 'referral'::channel_type, 180::NUMERIC, 0.82::NUMERIC, 0.94::NUMERIC),
        ('U008', 'C004', 'referral'::channel_type, 170::NUMERIC, 0.82::NUMERIC, 0.94::NUMERIC),
        ('U009', 'C005', 'email'::channel_type, 130::NUMERIC, 0.78::NUMERIC, 0.92::NUMERIC),
        ('U010', 'C005', 'email'::channel_type, 125::NUMERIC, 0.78::NUMERIC, 0.92::NUMERIC)
) AS data(
    external_id,
    campaign_code,
    channel_code,
    first_purchase,
    gross_margin,
    retention
)
JOIN campaigns c
    ON c.campaign_code = data.campaign_code
JOIN acquisition_channels ac
    ON ac.channel_code = data.channel_code;

-- ================================================================
-- 22. SAMPLE CUSTOMER TOUCHPOINTS
-- ================================================================

INSERT INTO customer_touchpoints (
    customer_id,
    channel_id,
    occurred_at,
    touchpoint_type,
    source_reference
)
SELECT
    c.customer_id,
    ac.channel_id,
    TIMESTAMPTZ '2026-06-01 10:00:00+05:30',
    'website_visit',
    'INITIAL-TOUCH'
FROM customers c
JOIN acquisition_channels ac
    ON ac.channel_code = 'paid_social'
WHERE c.external_customer_id IN ('U001', 'U002');

INSERT INTO customer_touchpoints (
    customer_id,
    channel_id,
    occurred_at,
    touchpoint_type,
    source_reference
)
SELECT
    c.customer_id,
    ac.channel_id,
    TIMESTAMPTZ '2026-06-05 10:00:00+05:30',
    'organic_visit',
    'SECOND-TOUCH'
FROM customers c
JOIN acquisition_channels ac
    ON ac.channel_code = 'organic_search'
WHERE c.external_customer_id IN ('U001', 'U002');

-- ================================================================
-- 23. SAMPLE ATTRIBUTION RESULTS
-- ================================================================

INSERT INTO customer_attribution (
    customer_id,
    channel_id,
    attribution_method,
    attribution_weight
)
SELECT
    c.customer_id,
    ac.channel_id,
    'linear'::attribution_model,
    0.5
FROM customers c
JOIN acquisition_channels ac
    ON ac.channel_code IN ('paid_social', 'organic_search')
WHERE c.external_customer_id IN ('U001', 'U002');

-- ================================================================
-- 24. SAMPLE BUDGET APPROVALS
-- ================================================================

INSERT INTO channel_budget_allocations (
    channel_id,
    allocation_period,
    approved_budget,
    allocated_budget,
    expected_cac,
    approved_by
)
SELECT
    ac.channel_id,
    DATE '2026-07-01',
    data.approved_budget,
    data.allocated_budget,
    data.expected_cac,
    'Marketing Finance'
FROM (
    VALUES
        ('paid_search'::channel_type, 30000::NUMERIC, 25000::NUMERIC, 42::NUMERIC),
        ('paid_social'::channel_type, 25000::NUMERIC, 20000::NUMERIC, 60::NUMERIC),
        ('organic_search'::channel_type, 20000::NUMERIC, 18000::NUMERIC, 30::NUMERIC),
        ('referral'::channel_type, 15000::NUMERIC, 12000::NUMERIC, 25::NUMERIC),
        ('email'::channel_type, 10000::NUMERIC, 8000::NUMERIC, 20::NUMERIC)
) AS data(
    channel_code,
    approved_budget,
    allocated_budget,
    expected_cac
)
JOIN acquisition_channels ac
    ON ac.channel_code = data.channel_code;

-- ================================================================
-- 25. CAMPAIGN PERFORMANCE RETRIEVAL
-- ================================================================

SELECT
    campaign_name,
    channel_name,
    spend,
    conversions,
    ctr_percent,
    cac,
    roas
FROM campaign_performance
ORDER BY cac ASC NULLS LAST;

-- ================================================================
-- 26. CHANNEL CAC AND LTV REPORT
-- ================================================================

SELECT
    channel_name,
    total_spend,
    total_customers,
    cac,
    average_ltv,
    ltv_cac_ratio,
    roas
FROM channel_performance
ORDER BY cac ASC NULLS LAST;

-- ================================================================
-- 27. CUSTOMER-LEVEL LTV RETRIEVAL
-- ================================================================

SELECT
    external_customer_id,
    channel_name,
    first_purchase_revenue,
    initial_gross_profit,
    projected_ltv_24m
FROM customer_lifetime_value
ORDER BY projected_ltv_24m DESC;

-- ================================================================
-- 28. ATTRIBUTION REPORT
-- ================================================================

SELECT
    attribution_method,
    channel_name,
    attributed_customers,
    weighted_customer_credit
FROM attribution_performance
ORDER BY attribution_method, weighted_customer_credit DESC;

-- ================================================================
-- 29. ATTRIBUTION WEIGHT VALIDATION
-- ================================================================

SELECT
    c.external_customer_id,
    validate_attribution_weights(
        c.customer_id,
        'linear'
    ) AS attribution_is_valid
FROM customers c
WHERE EXISTS (
    SELECT 1
    FROM customer_attribution ca
    WHERE ca.customer_id = c.customer_id
      AND ca.attribution_method = 'linear'
);

-- ================================================================
-- 30. ACQUISITION POLICY EVALUATION
-- ================================================================

SELECT
    ac.channel_name,
    evaluation.customer_count,
    evaluation.calculated_cac,
    evaluation.calculated_ltv,
    evaluation.ltv_cac,
    evaluation.decision
FROM acquisition_channels ac
CROSS JOIN LATERAL evaluate_channel(
    ac.channel_id,
    1
) AS evaluation
ORDER BY evaluation.calculated_cac ASC NULLS LAST;

-- ================================================================
-- 31. CHANNEL SPEND AGGREGATION
-- ================================================================

WITH monthly_spend AS (
    SELECT
        c.channel_id,
        ac.channel_name,
        DATE_TRUNC('month', s.expense_date)::DATE AS expense_month,
        SUM(s.amount) AS total_spend
    FROM campaign_spend_transactions s
    JOIN campaigns c
        ON c.campaign_id = s.campaign_id
    JOIN acquisition_channels ac
        ON ac.channel_id = c.channel_id
    GROUP BY
        c.channel_id,
        ac.channel_name,
        DATE_TRUNC('month', s.expense_date)
)
SELECT *
FROM monthly_spend
ORDER BY expense_month, total_spend DESC;

-- ================================================================
-- 32. CAMPAIGN BUDGET UTILIZATION
-- ================================================================

SELECT
    campaign_name,
    budget,
    spend,
    budget - spend AS remaining_budget,
    ROUND(
        100 * spend / NULLIF(budget, 0),
        2
    ) AS utilization_percent
FROM campaigns
ORDER BY utilization_percent DESC NULLS LAST;

-- ================================================================
-- 33. TRANSACTIONAL SPEND RECORDING EXAMPLE
--
-- The savepoint demonstrates rollback of an individual operation
-- without losing unrelated work in the outer transaction.
-- ================================================================

SAVEPOINT before_spend_recording;

SELECT record_campaign_spend(
    (SELECT campaign_id FROM campaigns WHERE campaign_code = 'C001'),
    'SPEND-2026-001',
    1000.00,
    DATE '2026-07-01',
    'Additional search advertising expenditure'
);

RELEASE SAVEPOINT before_spend_recording;

-- ================================================================
-- 34. VALIDATION EXAMPLE: ZERO-CUSTOMER CHANNELS
-- ================================================================

SELECT
    channel_name,
    total_spend,
    total_customers,
    cac,
    CASE
        WHEN total_customers = 0 THEN 'NO ACQUISITION DATA'
        WHEN cac IS NULL THEN 'CAC UNAVAILABLE'
        ELSE 'CAC AVAILABLE'
    END AS data_quality_status
FROM channel_performance;

-- ================================================================
-- 35. VALIDATION EXAMPLE: CAMPAIGN FUNNEL
-- ================================================================

SELECT
    campaign_code,
    impressions,
    clicks,
    leads,
    conversions,
    CASE
        WHEN clicks > impressions THEN 'INVALID'
        WHEN leads > clicks THEN 'INVALID'
        WHEN conversions > leads THEN 'INVALID'
        ELSE 'VALID'
    END AS funnel_status
FROM campaigns;

-- ================================================================
-- 36. CHANNEL PERFORMANCE RANKING
-- ================================================================

SELECT
    channel_name,
    cac,
    average_ltv,
    ltv_cac_ratio,
    DENSE_RANK() OVER (
        ORDER BY ltv_cac_ratio DESC NULLS LAST
    ) AS channel_rank
FROM channel_performance;

-- ================================================================
-- 37. CUSTOMER ACQUISITION COHORT REPORT
-- ================================================================

SELECT
    DATE_TRUNC('month', acquisition_date)::DATE AS acquisition_month,
    channel_name,
    COUNT(*) AS acquired_customers,
    SUM(first_purchase_revenue) AS initial_revenue,
    AVG(gross_margin_rate) AS average_gross_margin
FROM customers c
JOIN acquisition_channels ac
    ON ac.channel_id = c.acquisition_channel
GROUP BY
    DATE_TRUNC('month', acquisition_date),
    channel_name
ORDER BY acquisition_month, acquired_customers DESC;

-- ================================================================
-- 38. DATA ACCESS CONTROL EXAMPLE
--
-- A production deployment should use dedicated roles and grants.
-- Do not grant unrestricted access to customer-level records.
-- ================================================================

COMMIT;

-- ================================================================
-- END OF CUSTOMER ACQUISITION DATABASE
-- ================================================================
