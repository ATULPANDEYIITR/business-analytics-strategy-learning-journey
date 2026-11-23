-- ============================================================
-- CUSTOMER LIFETIME VALUE MANAGEMENT SYSTEM
-- PostgreSQL 15+
--
-- Functional areas:
-- 1. Customer and transaction accounting
-- 2. Historical and predictive CLV
-- 3. Customer acquisition cost
-- 4. Cohort retention
-- 5. Customer segmentation
-- 6. Acquisition channel profitability
-- 7. Strategic retention decisions
-- 8. Campaign management and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS customer_analytics;

SET search_path TO customer_analytics, public;

-- ------------------------------------------------------------
-- 1. REFERENCE DATA
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS acquisition_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name VARCHAR(60) NOT NULL UNIQUE,
    channel_type VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_channel_type CHECK (
        channel_type IN (
            'ORGANIC',
            'PAID',
            'REFERRAL',
            'PARTNERSHIP',
            'DIRECT'
        )
    )
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_customer_id VARCHAR(80) NOT NULL UNIQUE,
    acquisition_channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),
    acquired_at DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    country_code CHAR(2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_customer_status CHECK (
        status IN ('ACTIVE', 'AT_RISK', 'CHURNED')
    )
);

CREATE TABLE IF NOT EXISTS customer_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_transaction_id VARCHAR(100) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    transaction_date DATE NOT NULL,
    revenue NUMERIC(14,2) NOT NULL,
    variable_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    transaction_type VARCHAR(20) NOT NULL DEFAULT 'PURCHASE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonnegative_revenue CHECK (revenue >= 0),
    CONSTRAINT nonnegative_variable_cost CHECK (variable_cost >= 0),
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('PURCHASE', 'REFUND', 'ADJUSTMENT')
    ),
    CONSTRAINT valid_contribution CHECK (
        variable_cost <= revenue
    )
);

CREATE TABLE IF NOT EXISTS acquisition_spend (
    spend_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),
    spend_date DATE NOT NULL,
    campaign_name VARCHAR(150) NOT NULL,
    spend_amount NUMERIC(14,2) NOT NULL,

    CONSTRAINT nonnegative_spend CHECK (spend_amount >= 0),
    CONSTRAINT unique_campaign_spend
        UNIQUE(channel_id, spend_date, campaign_name)
);

-- ------------------------------------------------------------
-- 2. CLV POLICY CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS clv_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    annual_churn_rate NUMERIC(8,6) NOT NULL,
    annual_discount_rate NUMERIC(8,6) NOT NULL,
    default_margin NUMERIC(8,6) NOT NULL,
    maximum_lifetime_years NUMERIC(8,2) NOT NULL,
    effective_from DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_churn CHECK (
        annual_churn_rate > 0 AND annual_churn_rate <= 1
    ),
    CONSTRAINT valid_discount CHECK (
        annual_discount_rate >= 0 AND annual_discount_rate < 1
    ),
    CONSTRAINT valid_margin CHECK (
        default_margin >= 0 AND default_margin <= 1
    ),
    CONSTRAINT valid_lifetime CHECK (
        maximum_lifetime_years > 0
    )
);

-- ------------------------------------------------------------
-- 3. CLV SNAPSHOTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS customer_clv_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    policy_id BIGINT NOT NULL REFERENCES clv_policies(policy_id),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    historical_revenue NUMERIC(14,2) NOT NULL,
    historical_contribution NUMERIC(14,2) NOT NULL,
    acquisition_cost NUMERIC(14,2) NOT NULL,
    gross_margin NUMERIC(8,6) NOT NULL,
    annual_revenue NUMERIC(14,2) NOT NULL,
    expected_lifetime NUMERIC(8,2) NOT NULL,
    projected_clv NUMERIC(14,2) NOT NULL,
    net_clv NUMERIC(14,2) NOT NULL,
    segment VARCHAR(30) NOT NULL,
    confidence VARCHAR(15) NOT NULL,

    CONSTRAINT valid_segment CHECK (
        segment IN (
            'HIGH_VALUE',
            'GROWING',
            'STANDARD',
            'LOW_VALUE',
            'UNPROFITABLE'
        )
    ),
    CONSTRAINT valid_confidence CHECK (
        confidence IN ('LOW', 'MEDIUM', 'HIGH')
    ),
    CONSTRAINT valid_snapshot_amounts CHECK (
        historical_revenue >= 0
        AND acquisition_cost >= 0
        AND gross_margin BETWEEN 0 AND 1
        AND expected_lifetime > 0
    )
);

-- ------------------------------------------------------------
-- 4. RETENTION AND CUSTOMER SEGMENTATION
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS customer_segments (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_name VARCHAR(30) NOT NULL UNIQUE,
    minimum_net_clv NUMERIC(14,2),
    maximum_net_clv NUMERIC(14,2),
    strategic_priority INTEGER NOT NULL,

    CONSTRAINT valid_segment_range CHECK (
        maximum_net_clv IS NULL
        OR minimum_net_clv IS NULL
        OR maximum_net_clv > minimum_net_clv
    )
);

CREATE TABLE IF NOT EXISTS retention_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    observation_period DATE NOT NULL,
    was_active BOOLEAN NOT NULL,
    churn_probability NUMERIC(8,6) NOT NULL,
    engagement_score NUMERIC(8,4),

    CONSTRAINT unique_customer_observation
        UNIQUE(customer_id, observation_period),
    CONSTRAINT valid_churn_probability CHECK (
        churn_probability BETWEEN 0 AND 1
    ),
    CONSTRAINT valid_engagement_score CHECK (
        engagement_score IS NULL
        OR engagement_score BETWEEN 0 AND 100
    )
);

-- ------------------------------------------------------------
-- 5. MARKETING CAMPAIGNS AND DECISIONS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retention_campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_name VARCHAR(150) NOT NULL UNIQUE,
    campaign_type VARCHAR(30) NOT NULL,
    budget NUMERIC(14,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PLANNED',

    CONSTRAINT valid_campaign_budget CHECK (budget >= 0),
    CONSTRAINT valid_campaign_dates CHECK (end_date >= start_date),
    CONSTRAINT valid_campaign_type CHECK (
        campaign_type IN (
            'LOYALTY',
            'WIN_BACK',
            'CROSS_SELL',
            'UPSELL',
            'CHURN_PREVENTION'
        )
    ),
    CONSTRAINT valid_campaign_status CHECK (
        status IN ('PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED')
    )
);

CREATE TABLE IF NOT EXISTS strategic_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    snapshot_id BIGINT NOT NULL
        REFERENCES customer_clv_snapshots(snapshot_id),
    campaign_id BIGINT REFERENCES retention_campaigns(campaign_id),
    decision_type VARCHAR(40) NOT NULL,
    rationale TEXT NOT NULL,
    expected_incremental_value NUMERIC(14,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_decision_type CHECK (
        decision_type IN (
            'PREMIUM_RETENTION',
            'CROSS_SELL',
            'ENGAGEMENT',
            'ACQUISITION_REVIEW',
            'CHURN_INTERVENTION',
            'DATA_COLLECTION'
        )
    )
);

-- ------------------------------------------------------------
-- 6. REVIEW AND REPORTING INDEXES
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_customers_channel
    ON customers(acquisition_channel_id);

CREATE INDEX IF NOT EXISTS idx_customer_transactions_customer_date
    ON customer_transactions(customer_id, transaction_date);

CREATE INDEX IF NOT EXISTS idx_customer_transactions_date
    ON customer_transactions(transaction_date);

CREATE INDEX IF NOT EXISTS idx_clv_customer_calculated
    ON customer_clv_snapshots(customer_id, calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_clv_segment_value
    ON customer_clv_snapshots(segment, net_clv DESC);

CREATE INDEX IF NOT EXISTS idx_retention_period_active
    ON retention_observations(observation_period, was_active);

CREATE INDEX IF NOT EXISTS idx_retention_churn_risk
    ON retention_observations(churn_probability DESC);

CREATE INDEX IF NOT EXISTS idx_spend_channel_date
    ON acquisition_spend(channel_id, spend_date);

-- ------------------------------------------------------------
-- 7. TRANSACTION INTEGRITY TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_customer_transaction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    acquisition_date DATE;
BEGIN
    SELECT acquired_at
    INTO acquisition_date
    FROM customers
    WHERE customer_id = NEW.customer_id
    FOR SHARE;

    IF acquisition_date IS NULL THEN
        RAISE EXCEPTION 'Customer does not exist.';
    END IF;

    IF NEW.transaction_date < acquisition_date THEN
        RAISE EXCEPTION
            'Transaction date cannot precede customer acquisition.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_customer_transaction
ON customer_transactions;

CREATE TRIGGER trg_validate_customer_transaction
BEFORE INSERT OR UPDATE ON customer_transactions
FOR EACH ROW
EXECUTE FUNCTION validate_customer_transaction();

-- ------------------------------------------------------------
-- 8. CLV CALCULATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_customer_clv(
    p_customer_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    customer_id BIGINT,
    historical_revenue NUMERIC,
    historical_contribution NUMERIC,
    acquisition_cost NUMERIC,
    gross_margin NUMERIC,
    annual_revenue NUMERIC,
    expected_lifetime NUMERIC,
    projected_clv NUMERIC,
    net_clv NUMERIC,
    customer_segment VARCHAR,
    confidence VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_churn NUMERIC;
    v_discount NUMERIC;
    v_default_margin NUMERIC;
    v_max_lifetime NUMERIC;
    v_revenue NUMERIC;
    v_contribution NUMERIC;
    v_acquisition NUMERIC;
    v_margin NUMERIC;
    v_annual_revenue NUMERIC;
    v_lifetime NUMERIC;
    v_projected NUMERIC;
    v_net NUMERIC;
    v_count BIGINT;
BEGIN
    SELECT
        annual_churn_rate,
        annual_discount_rate,
        default_margin,
        maximum_lifetime_years
    INTO
        v_churn,
        v_discount,
        v_default_margin,
        v_max_lifetime
    FROM clv_policies
    WHERE policy_id = p_policy_id
      AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active CLV policy not found.';
    END IF;

    SELECT
        COALESCE(SUM(revenue), 0),
        COALESCE(SUM(revenue - variable_cost), 0),
        COUNT(*)
    INTO
        v_revenue,
        v_contribution,
        v_count
    FROM customer_transactions
    WHERE customer_transactions.customer_id = p_customer_id
      AND transaction_type = 'PURCHASE';

    IF NOT EXISTS (
        SELECT 1
        FROM customers
        WHERE customers.customer_id = p_customer_id
    ) THEN
        RAISE EXCEPTION 'Customer not found.';
    END IF;

    SELECT COALESCE(SUM(spend_amount), 0)
    INTO v_acquisition
    FROM acquisition_spend
    WHERE channel_id = (
        SELECT acquisition_channel_id
        FROM customers
        WHERE customers.customer_id = p_customer_id
    )
      AND spend_date = (
        SELECT acquired_at
        FROM customers
        WHERE customers.customer_id = p_customer_id
    );

    v_margin := CASE
        WHEN v_revenue > 0
        THEN v_contribution / v_revenue
        ELSE v_default_margin
    END;

    -- Purchase frequency is annualized using the observed interval.
    SELECT
        CASE
            WHEN COUNT(*) < 2 THEN 0
            WHEN MAX(transaction_date) = MIN(transaction_date)
                THEN COUNT(*)::NUMERIC
            ELSE
                COUNT(*)::NUMERIC /
                (
                    EXTRACT(
                        EPOCH FROM (
                            MAX(transaction_date) -
                            MIN(transaction_date)
                        )
                    ) / 31557600.0
                )
        END
    INTO v_annual_revenue
    FROM customer_transactions
    WHERE customer_transactions.customer_id = p_customer_id
      AND transaction_type = 'PURCHASE';

    SELECT
        v_annual_revenue * v_margin *
        COALESCE(
            v_revenue / NULLIF(v_count, 0),
            0
        )
    INTO v_annual_revenue;

    -- The annualized purchase-frequency calculation is multiplied
    -- by average order value to obtain annual revenue.
    v_lifetime := LEAST(v_max_lifetime, 1 / v_churn);

    IF v_discount = 0 THEN
        v_projected := v_annual_revenue * v_lifetime;
    ELSE
        v_projected :=
            v_annual_revenue *
            (
                1 - POWER(1 + v_discount, -v_lifetime)
            ) / v_discount;
    END IF;

    v_net := v_projected - v_acquisition;

    RETURN QUERY
    SELECT
        p_customer_id,
        v_revenue,
        v_contribution,
        v_acquisition,
        v_margin,
        v_annual_revenue,
        v_lifetime,
        v_projected,
        v_net,
        CASE
            WHEN v_net < 0 THEN 'UNPROFITABLE'
            WHEN v_net >= 10000 THEN 'HIGH_VALUE'
            WHEN v_net >= 5000 THEN 'GROWING'
            WHEN v_net >= 1000 THEN 'STANDARD'
            ELSE 'LOW_VALUE'
        END::VARCHAR,
        CASE
            WHEN v_count >= 5 THEN 'HIGH'
            WHEN v_count >= 2 THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR;
END;
$$;

-- ------------------------------------------------------------
-- 9. SNAPSHOT CREATION PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE refresh_customer_clv(
    p_customer_id BIGINT,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO customer_clv_snapshots (
        customer_id,
        policy_id,
        historical_revenue,
        historical_contribution,
        acquisition_cost,
        gross_margin,
        annual_revenue,
        expected_lifetime,
        projected_clv,
        net_clv,
        segment,
        confidence
    )
    SELECT
        customer_id,
        p_policy_id,
        historical_revenue,
        historical_contribution,
        acquisition_cost,
        gross_margin,
        annual_revenue,
        expected_lifetime,
        projected_clv,
        net_clv,
        customer_segment,
        confidence
    FROM calculate_customer_clv(
        p_customer_id,
        p_policy_id
    );
END;
$$;

-- ------------------------------------------------------------
-- 10. SAMPLE MASTER DATA
-- ------------------------------------------------------------

INSERT INTO acquisition_channels (
    channel_name,
    channel_type
)
VALUES
    ('Organic Search', 'ORGANIC'),
    ('Paid Search', 'PAID'),
    ('Customer Referral', 'REFERRAL'),
    ('Paid Social', 'PAID')
ON CONFLICT (channel_name) DO NOTHING;

INSERT INTO clv_policies (
    policy_name,
    annual_churn_rate,
    annual_discount_rate,
    default_margin,
    maximum_lifetime_years,
    effective_from
)
VALUES (
    'Standard CLV Policy',
    0.20,
    0.10,
    0.60,
    10,
    CURRENT_DATE
)
ON CONFLICT (policy_name) DO NOTHING;

INSERT INTO customers (
    external_customer_id,
    acquisition_channel_id,
    acquired_at,
    status,
    country_code
)
SELECT
    data.external_id,
    channel.channel_id,
    data.acquired_at,
    data.status,
    'IN'
FROM (
    VALUES
        ('C001', 'Organic Search', DATE '2024-01-10', 'ACTIVE'),
        ('C002', 'Paid Search', DATE '2024-03-15', 'ACTIVE'),
        ('C003', 'Customer Referral', DATE '2024-05-20', 'ACTIVE'),
        ('C004', 'Paid Social', DATE '2025-01-05', 'AT_RISK')
) AS data(external_id, channel_name, acquired_at, status)
JOIN acquisition_channels channel
    ON channel.channel_name = data.channel_name
ON CONFLICT (external_customer_id) DO NOTHING;

-- ------------------------------------------------------------
-- 11. TRANSACTION SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO customer_transactions (
    external_transaction_id,
    customer_id,
    transaction_date,
    revenue,
    variable_cost
)
SELECT
    data.transaction_id,
    customer.customer_id,
    data.transaction_date,
    data.revenue,
    data.variable_cost
FROM (
    VALUES
        ('T001', 'C001', DATE '2024-02-01', 5000.00, 1800.00),
        ('T002', 'C001', DATE '2024-05-01', 6500.00, 2200.00),
        ('T003', 'C001', DATE '2024-09-01', 7000.00, 2500.00),
        ('T004', 'C001', DATE '2025-02-01', 8000.00, 2800.00),

        ('T005', 'C002', DATE '2024-04-01', 1500.00, 900.00),
        ('T006', 'C002', DATE '2024-07-01', 1800.00, 1000.00),
        ('T007', 'C002', DATE '2024-10-01', 2000.00, 1100.00),

        ('T008', 'C003', DATE '2024-06-01', 3000.00, 1200.00),
        ('T009', 'C003', DATE '2024-10-01', 4000.00, 1500.00),
        ('T010', 'C003', DATE '2025-03-01', 5000.00, 1800.00),

        ('T011', 'C004', DATE '2025-02-01', 700.00, 500.00),
        ('T012', 'C004', DATE '2025-04-01', 800.00, 600.00)
) AS data(
    transaction_id,
    external_id,
    transaction_date,
    revenue,
    variable_cost
)
JOIN customers customer
    ON customer.external_customer_id = data.external_id
ON CONFLICT (external_transaction_id) DO NOTHING;

-- Acquisition spending is stored separately from transactions.
INSERT INTO acquisition_spend (
    channel_id,
    spend_date,
    campaign_name,
    spend_amount
)
SELECT
    channel_id,
    DATE '2024-01-10',
    'Organic Acquisition Campaign',
    500.00
FROM acquisition_channels
WHERE channel_name = 'Organic Search'
ON CONFLICT DO NOTHING;

INSERT INTO acquisition_spend (
    channel_id,
    spend_date,
    campaign_name,
    spend_amount
)
SELECT
    channel_id,
    DATE '2024-03-15',
    'Paid Search Acquisition Campaign',
    2000.00
FROM acquisition_channels
WHERE channel_name = 'Paid Search'
ON CONFLICT DO NOTHING;

INSERT INTO acquisition_spend (
    channel_id,
    spend_date,
    campaign_name,
    spend_amount
)
SELECT
    channel_id,
    DATE '2024-05-20',
    'Referral Acquisition Campaign',
    300.00
FROM acquisition_channels
WHERE channel_name = 'Customer Referral'
ON CONFLICT DO NOTHING;

INSERT INTO acquisition_spend (
    channel_id,
    spend_date,
    campaign_name,
    spend_amount
)
SELECT
    channel_id,
    DATE '2025-01-05',
    'Paid Social Acquisition Campaign',
    2500.00
FROM acquisition_channels
WHERE channel_name = 'Paid Social'
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 12. RETENTION OBSERVATIONS
-- ------------------------------------------------------------

INSERT INTO retention_observations (
    customer_id,
    observation_period,
    was_active,
    churn_probability,
    engagement_score
)
SELECT
    customer.customer_id,
    data.period,
    data.active,
    data.risk,
    data.engagement
FROM (
    VALUES
        ('C001', DATE '2025-01-01', TRUE, 0.10, 90.00),
        ('C001', DATE '2025-02-01', TRUE, 0.12, 92.00),
        ('C002', DATE '2025-01-01', TRUE, 0.45, 55.00),
        ('C002', DATE '2025-02-01', TRUE, 0.60, 40.00),
        ('C003', DATE '2025-01-01', TRUE, 0.15, 85.00),
        ('C004', DATE '2025-02-01', TRUE, 0.75, 20.00)
) AS data(
    external_id,
    period,
    active,
    risk,
    engagement
)
JOIN customers customer
    ON customer.external_customer_id = data.external_id
ON CONFLICT (customer_id, observation_period) DO NOTHING;

-- ------------------------------------------------------------
-- 13. CAMPAIGN CONFIGURATION
-- ------------------------------------------------------------

INSERT INTO retention_campaigns (
    campaign_name,
    campaign_type,
    budget,
    start_date,
    end_date,
    status
)
VALUES
    (
        'Premium Customer Loyalty',
        'LOYALTY',
        50000,
        DATE '2025-01-01',
        DATE '2025-12-31',
        'ACTIVE'
    ),
    (
        'At Risk Customer Recovery',
        'CHURN_PREVENTION',
        25000,
        DATE '2025-01-01',
        DATE '2025-06-30',
        'ACTIVE'
    ),
    (
        'Customer Expansion',
        'CROSS_SELL',
        30000,
        DATE '2025-01-01',
        DATE '2025-12-31',
        'PLANNED'
    )
ON CONFLICT (campaign_name) DO NOTHING;

COMMIT;

-- ------------------------------------------------------------
-- 14. EXECUTE CLV SNAPSHOT CALCULATIONS
-- ------------------------------------------------------------

DO $$
DECLARE
    customer_record RECORD;
    policy_identifier BIGINT;
BEGIN
    SELECT policy_id
    INTO policy_identifier
    FROM customer_analytics.clv_policies
    WHERE policy_name = 'Standard CLV Policy'
      AND is_active = TRUE;

    FOR customer_record IN
        SELECT customer_id
        FROM customer_analytics.customers
    LOOP
        CALL customer_analytics.refresh_customer_clv(
            customer_record.customer_id,
            policy_identifier
        );
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- 15. CUSTOMER CLV RETRIEVAL
-- ------------------------------------------------------------

SELECT
    c.external_customer_id,
    c.status,
    s.historical_revenue,
    s.historical_contribution,
    s.acquisition_cost,
    s.projected_clv,
    s.net_clv,
    s.segment,
    s.confidence
FROM customers c
JOIN LATERAL (
    SELECT *
    FROM customer_clv_snapshots snapshot
    WHERE snapshot.customer_id = c.customer_id
    ORDER BY snapshot.calculated_at DESC
    LIMIT 1
) s ON TRUE
ORDER BY s.net_clv DESC;

-- ------------------------------------------------------------
-- 16. PORTFOLIO AGGREGATION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW portfolio_clv_report AS
SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(net_clv), 2) AS average_net_clv,
    ROUND(SUM(net_clv), 2) AS total_net_clv,
    ROUND(AVG(gross_margin), 4) AS average_margin,
    ROUND(AVG(expected_lifetime), 2) AS average_lifetime
FROM (
    SELECT DISTINCT ON (customer_id)
        *
    FROM customer_clv_snapshots
    ORDER BY customer_id, calculated_at DESC
) latest
GROUP BY segment;

SELECT *
FROM portfolio_clv_report
ORDER BY total_net_clv DESC;

-- ------------------------------------------------------------
-- 17. ACQUISITION CHANNEL PERFORMANCE
-- ------------------------------------------------------------

WITH customer_economics AS (
    SELECT DISTINCT ON (snapshot.customer_id)
        snapshot.customer_id,
        snapshot.net_clv,
        snapshot.acquisition_cost,
        customer.acquisition_channel_id
    FROM customer_clv_snapshots snapshot
    JOIN customers customer
        ON customer.customer_id = snapshot.customer_id
    ORDER BY
        snapshot.customer_id,
        snapshot.calculated_at DESC
)
SELECT
    channel.channel_name,
    COUNT(economics.customer_id) AS customers,
    ROUND(AVG(economics.net_clv), 2) AS average_net_clv,
    ROUND(SUM(economics.net_clv), 2) AS total_net_clv,
    ROUND(AVG(economics.acquisition_cost), 2) AS average_cac
FROM acquisition_channels channel
LEFT JOIN customer_economics economics
    ON economics.acquisition_channel_id = channel.channel_id
GROUP BY channel.channel_id, channel.channel_name
ORDER BY average_net_clv DESC NULLS LAST;

-- ------------------------------------------------------------
-- 18. CLV TO CAC RATIO
-- ------------------------------------------------------------

WITH channel_customers AS (
    SELECT
        customer.acquisition_channel_id,
        COUNT(*) AS customer_count,
        AVG(snapshot.net_clv) AS average_clv
    FROM customers customer
    JOIN LATERAL (
        SELECT net_clv
        FROM customer_clv_snapshots
        WHERE customer_id = customer.customer_id
        ORDER BY calculated_at DESC
        LIMIT 1
    ) snapshot ON TRUE
    GROUP BY customer.acquisition_channel_id
),
channel_spend AS (
    SELECT
        channel_id,
        SUM(spend_amount) AS total_spend
    FROM acquisition_spend
    GROUP BY channel_id
)
SELECT
    channel.channel_name,
    COALESCE(spend.total_spend, 0) AS total_marketing_spend,
    COALESCE(customers.customer_count, 0) AS acquired_customers,
    ROUND(
        spend.total_spend /
        NULLIF(customers.customer_count, 0),
        2
    ) AS cac,
    ROUND(customers.average_clv, 2) AS average_clv,
    ROUND(
        customers.average_clv /
        NULLIF(
            spend.total_spend /
            NULLIF(customers.customer_count, 0),
            0
        ),
        2
    ) AS clv_cac_ratio
FROM acquisition_channels channel
LEFT JOIN channel_customers customers
    ON customers.acquisition_channel_id = channel.channel_id
LEFT JOIN channel_spend spend
    ON spend.channel_id = channel.channel_id;

-- ------------------------------------------------------------
-- 19. CUSTOMER COHORT RETENTION
-- ------------------------------------------------------------

WITH acquisition_cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', acquired_at)::DATE AS cohort_month
    FROM customers
),
cohort_activity AS (
    SELECT
        cohort.cohort_month,
        observation.observation_period,
        COUNT(DISTINCT cohort.customer_id) AS cohort_size,
        COUNT(DISTINCT cohort.customer_id)
            FILTER (WHERE observation.was_active) AS active_customers
    FROM acquisition_cohorts cohort
    JOIN retention_observations observation
        ON observation.customer_id = cohort.customer_id
    GROUP BY
        cohort.cohort_month,
        observation.observation_period
)
SELECT
    cohort_month,
    observation_period,
    cohort_size,
    active_customers,
    ROUND(
        100.0 * active_customers /
        NULLIF(cohort_size, 0),
        2
    ) AS retention_percentage
FROM cohort_activity
ORDER BY cohort_month, observation_period;

-- ------------------------------------------------------------
-- 20. CHURN RISK AND RETENTION PRIORITIZATION
-- ------------------------------------------------------------

WITH latest_observation AS (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        churn_probability,
        engagement_score,
        observation_period
    FROM retention_observations
    ORDER BY customer_id, observation_period DESC
),
latest_clv AS (
    SELECT DISTINCT ON (customer_id)
        customer_id,
        net_clv,
        segment
    FROM customer_clv_snapshots
    ORDER BY customer_id, calculated_at DESC
)
SELECT
    customer.external_customer_id,
    clv.net_clv,
    clv.segment,
    observation.churn_probability,
    observation.engagement_score,
    CASE
        WHEN clv.net_clv < 0
            THEN 'REVIEW_ACQUISITION_AND_PRICING'
        WHEN observation.churn_probability >= 0.70
            THEN 'URGENT_CHURN_INTERVENTION'
        WHEN clv.segment = 'HIGH_VALUE'
            THEN 'PREMIUM_LOYALTY'
        WHEN clv.segment = 'GROWING'
            THEN 'CROSS_SELL'
        ELSE 'STANDARD_ENGAGEMENT'
    END AS recommended_action
FROM customers customer
JOIN latest_clv clv
    ON clv.customer_id = customer.customer_id
LEFT JOIN latest_observation observation
    ON observation.customer_id = customer.customer_id
ORDER BY
    observation.churn_probability DESC NULLS LAST,
    clv.net_clv DESC;

-- ------------------------------------------------------------
-- 21. STRATEGIC DECISION INSERTION
-- ------------------------------------------------------------

INSERT INTO strategic_decisions (
    customer_id,
    snapshot_id,
    campaign_id,
    decision_type,
    rationale,
    expected_incremental_value
)
SELECT
    snapshot.customer_id,
    snapshot.snapshot_id,
    campaign.campaign_id,
    CASE
        WHEN snapshot.net_clv < 0
            THEN 'ACQUISITION_REVIEW'
        WHEN observation.churn_probability >= 0.70
            THEN 'CHURN_INTERVENTION'
        WHEN snapshot.segment = 'HIGH_VALUE'
            THEN 'PREMIUM_RETENTION'
        WHEN snapshot.segment = 'GROWING'
            THEN 'CROSS_SELL'
        ELSE 'ENGAGEMENT'
    END,
    'Decision derived from current CLV and retention indicators.',
    GREATEST(snapshot.net_clv * 0.10, 0)
FROM customer_clv_snapshots snapshot
LEFT JOIN LATERAL (
    SELECT churn_probability
    FROM retention_observations
    WHERE customer_id = snapshot.customer_id
    ORDER BY observation_period DESC
    LIMIT 1
) observation ON TRUE
LEFT JOIN retention_campaigns campaign
    ON campaign.campaign_type = CASE
        WHEN observation.churn_probability >= 0.70
            THEN 'CHURN_PREVENTION'
        WHEN snapshot.segment = 'HIGH_VALUE'
            THEN 'LOYALTY'
        WHEN snapshot.segment = 'GROWING'
            THEN 'CROSS_SELL'
        ELSE 'CHURN_PREVENTION'
    END
WHERE snapshot.calculated_at = (
    SELECT MAX(current_snapshot.calculated_at)
    FROM customer_clv_snapshots current_snapshot
    WHERE current_snapshot.customer_id = snapshot.customer_id
)
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- 22. VALIDATION AND EXCEPTION REPORTING
-- ------------------------------------------------------------

-- Transactions with negative contribution should not exist.
SELECT
    external_transaction_id,
    revenue,
    variable_cost
FROM customer_transactions
WHERE revenue < variable_cost;

-- Customers with no purchase history.
SELECT
    customer.external_customer_id,
    customer.acquired_at,
    channel.channel_name
FROM customers customer
JOIN acquisition_channels channel
    ON channel.channel_id = customer.acquisition_channel_id
LEFT JOIN customer_transactions transaction
    ON transaction.customer_id = customer.customer_id
WHERE transaction.transaction_id IS NULL;

-- CLV snapshots with limited evidence.
SELECT
    external_customer_id,
    confidence,
    historical_revenue,
    net_clv
FROM customer_clv_snapshots snapshot
JOIN customers customer
    ON customer.customer_id = snapshot.customer_id
WHERE confidence = 'LOW';

-- ------------------------------------------------------------
-- 23. TRANSACTION-SAFE POLICY EVALUATION
-- ------------------------------------------------------------

BEGIN;

-- An alternative policy can be evaluated without replacing
-- existing historical snapshots.

INSERT INTO clv_policies (
    policy_name,
    annual_churn_rate,
    annual_discount_rate,
    default_margin,
    maximum_lifetime_years,
    effective_from
)
VALUES (
    'Conservative CLV Policy',
    0.30,
    0.12,
    0.50,
    8,
    CURRENT_DATE
)
ON CONFLICT (policy_name) DO NOTHING;

-- Compare the active standard policy with the conservative policy.
SELECT
    customer.external_customer_id,
    standard.net_clv AS standard_net_clv,
    conservative.net_clv AS conservative_net_clv,
    ROUND(
        standard.net_clv - conservative.net_clv,
        2
    ) AS valuation_difference
FROM customers customer
CROSS JOIN LATERAL calculate_customer_clv(
    customer.customer_id,
    (
        SELECT policy_id
        FROM clv_policies
        WHERE policy_name = 'Standard CLV Policy'
    )
) standard
CROSS JOIN LATERAL calculate_customer_clv(
    customer.customer_id,
    (
        SELECT policy_id
        FROM clv_policies
        WHERE policy_name = 'Conservative CLV Policy'
    )
) conservative;

COMMIT;

-- ------------------------------------------------------------
-- 24. OPERATIONAL REPORT
-- ------------------------------------------------------------

SELECT
    customer.external_customer_id,
    customer.status,
    channel.channel_name,
    latest.segment,
    latest.net_clv,
    latest.projected_clv,
    latest.acquisition_cost,
    latest.confidence,
    latest.calculated_at
FROM customers customer
JOIN acquisition_channels channel
    ON channel.channel_id = customer.acquisition_channel_id
JOIN LATERAL (
    SELECT *
    FROM customer_clv_snapshots
    WHERE customer_id = customer.customer_id
    ORDER BY calculated_at DESC
    LIMIT 1
) latest ON TRUE
ORDER BY latest.net_clv DESC;
