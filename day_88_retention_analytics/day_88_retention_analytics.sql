-- ============================================================
-- RETENTION ANALYTICS DATABASE
-- Customer Churn, Retention, and Loyalty Management
--
-- PostgreSQL 15+
--
-- Database capabilities:
-- 1. Customer lifecycle management
-- 2. Behavioral event tracking
-- 3. Purchase and subscription history
-- 4. RFM segmentation
-- 5. Churn risk assessment
-- 6. Cohort retention analytics
-- 7. Loyalty tiers and rewards
-- 8. Campaign targeting and conversion
-- 9. Customer lifetime value
-- 10. Governance and reporting
--
-- The script creates an independent schema and sample dataset.
-- ============================================================


-- ============================================================
-- 1. SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS retention;

SET search_path TO retention, public;


-- ============================================================
-- 2. ENUMERATIONS
-- ============================================================

CREATE TYPE customer_status AS ENUM (
    'active',
    'at_risk',
    'churned',
    'reactivated'
);

CREATE TYPE event_type AS ENUM (
    'purchase',
    'login',
    'support',
    'email_open',
    'email_click',
    'subscription',
    'refund'
);

CREATE TYPE loyalty_tier AS ENUM (
    'bronze',
    'silver',
    'gold',
    'platinum'
);

CREATE TYPE risk_level AS ENUM (
    'low',
    'medium',
    'high'
);

CREATE TYPE campaign_type AS ENUM (
    'discount',
    'loyalty_reward',
    'reactivation',
    'personalized_offer'
);

CREATE TYPE campaign_status AS ENUM (
    'draft',
    'active',
    'paused',
    'completed'
);


-- ============================================================
-- 3. CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_customer_id VARCHAR(50) NOT NULL UNIQUE,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(254) NOT NULL UNIQUE,

    acquisition_date DATE NOT NULL,

    region VARCHAR(50) NOT NULL,

    monthly_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,

    status customer_status NOT NULL DEFAULT 'active',

    loyalty_tier loyalty_tier NOT NULL DEFAULT 'bronze',

    loyalty_points BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT customer_email_format
        CHECK (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'),

    CONSTRAINT customer_revenue_nonnegative
        CHECK (monthly_revenue >= 0),

    CONSTRAINT customer_points_nonnegative
        CHECK (loyalty_points >= 0)
);


-- ============================================================
-- 4. CUSTOMER EVENTS
-- ============================================================

CREATE TABLE customer_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_event_id VARCHAR(100) NOT NULL UNIQUE,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id)
        ON DELETE RESTRICT,

    event_type event_type NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL,

    amount NUMERIC(14,2) NOT NULL DEFAULT 0,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT event_amount_nonnegative
        CHECK (amount >= 0),

    CONSTRAINT event_amount_type
        CHECK (
            event_type IN ('purchase', 'subscription')
            OR amount = 0
        ),

    CONSTRAINT event_metadata_object
        CHECK (jsonb_typeof(metadata) = 'object')
);


-- ============================================================
-- 5. LOYALTY POLICY
-- ============================================================

CREATE TABLE loyalty_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    tier loyalty_tier NOT NULL UNIQUE,

    minimum_spend NUMERIC(14,2) NOT NULL,

    points_multiplier NUMERIC(6,3) NOT NULL,

    benefits_description TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT loyalty_minimum_nonnegative
        CHECK (minimum_spend >= 0),

    CONSTRAINT loyalty_multiplier_positive
        CHECK (points_multiplier > 0)
);

INSERT INTO loyalty_policies (
    tier,
    minimum_spend,
    points_multiplier,
    benefits_description
)
VALUES
    ('bronze', 0, 1.0, 'Standard rewards'),
    ('silver', 2000, 1.25, 'Enhanced rewards'),
    ('gold', 5000, 1.50, 'Premium rewards'),
    ('platinum', 10000, 2.0, 'Maximum rewards');


-- ============================================================
-- 6. CHURN POLICIES
-- ============================================================

CREATE TABLE churn_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(100) NOT NULL UNIQUE,

    medium_threshold NUMERIC(5,4) NOT NULL,

    high_threshold NUMERIC(5,4) NOT NULL,

    purchase_inactivity_days INTEGER NOT NULL DEFAULT 30,

    engagement_inactivity_days INTEGER NOT NULL DEFAULT 45,

    policy_weights JSONB NOT NULL DEFAULT '{}'::jsonb,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT churn_threshold_range
        CHECK (
            medium_threshold >= 0
            AND high_threshold <= 1
            AND medium_threshold < high_threshold
        ),

    CONSTRAINT churn_days_positive
        CHECK (
            purchase_inactivity_days > 0
            AND engagement_inactivity_days > 0
        )
);

INSERT INTO churn_policies (
    policy_name,
    medium_threshold,
    high_threshold,
    purchase_inactivity_days,
    engagement_inactivity_days,
    policy_weights
)
VALUES (
    'standard_churn_policy',
    0.35,
    0.60,
    30,
    45,
    '{
        "purchase_30_days": 0.20,
        "purchase_60_days": 0.20,
        "purchase_90_days": 0.20,
        "low_engagement": 0.15,
        "no_purchase": 0.15,
        "support_interactions": 0.10
    }'::jsonb
);


-- ============================================================
-- 7. CUSTOMER CHURN ASSESSMENTS
-- ============================================================

CREATE TABLE churn_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    policy_id BIGINT NOT NULL
        REFERENCES churn_policies(policy_id),

    churn_probability NUMERIC(5,4) NOT NULL,

    risk risk_level NOT NULL,

    contributing_factors JSONB NOT NULL DEFAULT '[]'::jsonb,

    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT churn_probability_range
        CHECK (
            churn_probability >= 0
            AND churn_probability <= 1
        ),

    CONSTRAINT churn_factors_array
        CHECK (jsonb_typeof(contributing_factors) = 'array')
);


-- ============================================================
-- 8. RFM ANALYSIS
-- ============================================================

CREATE TABLE rfm_snapshots (
    snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    reference_date DATE NOT NULL,

    recency_days INTEGER NOT NULL,

    frequency INTEGER NOT NULL,

    monetary_value NUMERIC(14,2) NOT NULL,

    rfm_score NUMERIC(7,2) NOT NULL,

    segment VARCHAR(40) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT rfm_unique_snapshot
        UNIQUE(customer_id, reference_date),

    CONSTRAINT rfm_nonnegative
        CHECK (
            recency_days >= 0
            AND frequency >= 0
            AND monetary_value >= 0
            AND rfm_score BETWEEN 0 AND 100
        )
);


-- ============================================================
-- 9. RETENTION CAMPAIGNS
-- ============================================================

CREATE TABLE retention_campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_code VARCHAR(50) NOT NULL UNIQUE,

    campaign_name VARCHAR(150) NOT NULL,

    campaign_type campaign_type NOT NULL,

    status campaign_status NOT NULL DEFAULT 'draft',

    target_status customer_status NOT NULL,

    budget NUMERIC(14,2) NOT NULL,

    cost_per_contact NUMERIC(12,2) NOT NULL,

    revenue_per_conversion NUMERIC(14,2) NOT NULL DEFAULT 0,

    start_date DATE,

    end_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT campaign_budget_nonnegative
        CHECK (budget >= 0),

    CONSTRAINT campaign_cost_nonnegative
        CHECK (cost_per_contact >= 0),

    CONSTRAINT campaign_revenue_nonnegative
        CHECK (revenue_per_conversion >= 0),

    CONSTRAINT campaign_date_validity
        CHECK (
            end_date IS NULL
            OR start_date IS NULL
            OR end_date >= start_date
        )
);


-- ============================================================
-- 10. CAMPAIGN ASSIGNMENTS
-- ============================================================

CREATE TABLE campaign_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_id BIGINT NOT NULL
        REFERENCES retention_campaigns(campaign_id),

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    converted_at TIMESTAMPTZ,

    attributed_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,

    CONSTRAINT campaign_customer_unique
        UNIQUE(campaign_id, customer_id),

    CONSTRAINT assignment_revenue_nonnegative
        CHECK (attributed_revenue >= 0),

    CONSTRAINT conversion_timestamp_valid
        CHECK (
            converted_at IS NULL
            OR converted_at >= assigned_at
        )
);


-- ============================================================
-- 11. LOYALTY REWARD TRANSACTIONS
-- ============================================================

CREATE TABLE loyalty_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    event_id BIGINT
        REFERENCES customer_events(event_id),

    points_change BIGINT NOT NULL,

    transaction_type VARCHAR(30) NOT NULL,

    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT loyalty_transaction_type
        CHECK (
            transaction_type IN (
                'earned',
                'redeemed',
                'adjustment',
                'expired'
            )
        ),

    CONSTRAINT loyalty_event_unique
        UNIQUE(event_id)
);


-- ============================================================
-- 12. PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_events_customer_time
    ON customer_events(customer_id, occurred_at DESC);

CREATE INDEX idx_events_type_time
    ON customer_events(event_type, occurred_at DESC);

CREATE INDEX idx_events_purchase_customer
    ON customer_events(customer_id, occurred_at DESC)
    WHERE event_type = 'purchase';

CREATE INDEX idx_customer_status
    ON customers(status);

CREATE INDEX idx_customer_region
    ON customers(region);

CREATE INDEX idx_customer_acquisition
    ON customers(acquisition_date);

CREATE INDEX idx_churn_customer_date
    ON churn_assessments(customer_id, assessed_at DESC);

CREATE INDEX idx_churn_high_risk
    ON churn_assessments(assessed_at DESC, customer_id)
    WHERE risk = 'high';

CREATE INDEX idx_campaign_status
    ON retention_campaigns(status);

CREATE INDEX idx_campaign_assignments
    ON campaign_assignments(campaign_id, customer_id);

CREATE INDEX idx_event_metadata
    ON customer_events USING GIN(metadata);


-- ============================================================
-- 13. CUSTOMER TIMESTAMP TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_customer_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_customer_timestamp
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_customer_timestamp();


-- ============================================================
-- 14. EVENT TYPE AND CUSTOMER VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_customer_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    acquisition DATE;
BEGIN

    SELECT acquisition_date
    INTO acquisition
    FROM customers
    WHERE customer_id = NEW.customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer does not exist';
    END IF;

    IF NEW.occurred_at::date < acquisition THEN
        RAISE EXCEPTION
            'Event cannot precede customer acquisition';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_customer_event
BEFORE INSERT ON customer_events
FOR EACH ROW
EXECUTE FUNCTION validate_customer_event();


-- ============================================================
-- 15. CAMPAIGN BUDGET ENFORCEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_campaign_budget()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    available_budget NUMERIC(14,2);
    contact_cost NUMERIC(12,2);
    campaign_state campaign_status;
    assigned_count BIGINT;
    customer_current_status customer_status;
BEGIN

    -- Serialize assignments for the same campaign to prevent
    -- concurrent transactions from exceeding the budget.

    SELECT budget, cost_per_contact, status
    INTO available_budget, contact_cost, campaign_state
    FROM retention_campaigns
    WHERE campaign_id = NEW.campaign_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign does not exist';
    END IF;

    IF campaign_state <> 'active' THEN
        RAISE EXCEPTION 'Campaign is not active';
    END IF;

    SELECT status
    INTO customer_current_status
    FROM customers
    WHERE customer_id = NEW.customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer does not exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM retention_campaigns
        WHERE campaign_id = NEW.campaign_id
          AND target_status = customer_current_status
    ) THEN
        RAISE EXCEPTION 'Customer is not campaign eligible';
    END IF;

    SELECT COUNT(*)
    INTO assigned_count
    FROM campaign_assignments
    WHERE campaign_id = NEW.campaign_id;

    IF (assigned_count + 1) * contact_cost > available_budget THEN
        RAISE EXCEPTION 'Campaign budget exceeded';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_campaign_budget
BEFORE INSERT ON campaign_assignments
FOR EACH ROW
EXECUTE FUNCTION enforce_campaign_budget();


-- ============================================================
-- 16. LOYALTY BALANCE ENFORCEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION apply_loyalty_transaction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_balance BIGINT;
BEGIN

    SELECT loyalty_points
    INTO current_balance
    FROM customers
    WHERE customer_id = NEW.customer_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer does not exist';
    END IF;

    IF current_balance + NEW.points_change < 0 THEN
        RAISE EXCEPTION 'Insufficient loyalty points';
    END IF;

    UPDATE customers
    SET loyalty_points =
        loyalty_points + NEW.points_change
    WHERE customer_id = NEW.customer_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_apply_loyalty_transaction
BEFORE INSERT ON loyalty_transactions
FOR EACH ROW
EXECUTE FUNCTION apply_loyalty_transaction();


-- ============================================================
-- 17. CUSTOMER ANALYTICS FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_customer_rfm(
    p_customer_id BIGINT,
    p_reference_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    customer_id BIGINT,
    recency_days INTEGER,
    frequency BIGINT,
    monetary_value NUMERIC,
    rfm_score NUMERIC,
    segment TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    acquisition DATE;
    last_purchase DATE;
    v_recency INTEGER;
    v_frequency BIGINT;
    v_monetary NUMERIC;
    v_score NUMERIC;
    v_segment TEXT;
BEGIN

    SELECT acquisition_date
    INTO acquisition
    FROM customers
    WHERE customers.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found';
    END IF;

    SELECT
        MAX(occurred_at::date),
        COUNT(*),
        COALESCE(SUM(amount), 0)
    INTO
        last_purchase,
        v_frequency,
        v_monetary
    FROM customer_events
    WHERE customer_events.customer_id = p_customer_id
      AND event_type = 'purchase'
      AND occurred_at::date <= p_reference_date;

    v_recency := GREATEST(
        0,
        p_reference_date - COALESCE(last_purchase, acquisition)
    );

    v_score := (
        GREATEST(
            0,
            1 - LEAST(v_recency, 180)::NUMERIC / 180
        ) * 0.40

        + LEAST(v_frequency::NUMERIC / 12, 1) * 0.30

        + LEAST(v_monetary / 12000, 1) * 0.30
    ) * 100;

    IF v_frequency = 0 THEN
        v_segment := 'non_purchasing';
    ELSIF v_recency <= 30 AND v_score >= 65 THEN
        v_segment := 'champions';
    ELSIF v_recency <= 60 THEN
        v_segment := 'loyal';
    ELSIF v_recency <= 90 THEN
        v_segment := 'at_risk';
    ELSE
        v_segment := 'hibernating';
    END IF;

    RETURN QUERY
    SELECT
        p_customer_id,
        v_recency,
        v_frequency,
        v_monetary,
        ROUND(v_score, 2),
        v_segment;
END;
$$;


-- ============================================================
-- 18. CHURN ASSESSMENT FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION assess_customer_churn(
    p_customer_id BIGINT,
    p_reference_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    customer_id BIGINT,
    churn_probability NUMERIC,
    risk risk_level,
    factors JSONB
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    acquisition DATE;
    last_purchase DATE;
    last_activity DATE;

    purchase_count BIGINT;
    support_count BIGINT;

    purchase_inactivity INTEGER;
    engagement_inactivity INTEGER;

    probability NUMERIC := 0.05;
    reasons JSONB := '[]'::jsonb;

    policy churn_policies%ROWTYPE;
BEGIN

    SELECT *
    INTO policy
    FROM churn_policies
    WHERE is_active = TRUE
    ORDER BY policy_id DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active churn policy exists';
    END IF;

    SELECT acquisition_date
    INTO acquisition
    FROM customers
    WHERE customers.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found';
    END IF;

    SELECT
        MAX(occurred_at::date) FILTER (
            WHERE event_type = 'purchase'
              AND occurred_at::date <= p_reference_date
        ),

        MAX(occurred_at::date) FILTER (
            WHERE occurred_at::date <= p_reference_date
        ),

        COUNT(*) FILTER (
            WHERE event_type = 'purchase'
              AND occurred_at::date <= p_reference_date
        ),

        COUNT(*) FILTER (
            WHERE event_type = 'support'
              AND occurred_at::date > p_reference_date - 30
              AND occurred_at::date <= p_reference_date
        )

    INTO
        last_purchase,
        last_activity,
        purchase_count,
        support_count

    FROM customer_events
    WHERE customer_events.customer_id = p_customer_id;

    purchase_inactivity := p_reference_date
        - COALESCE(last_purchase, acquisition);

    engagement_inactivity := p_reference_date
        - COALESCE(last_activity, acquisition);

    IF purchase_inactivity > 30 THEN
        probability := probability + 0.20;
        reasons := reasons || '["purchase_inactivity_30_days"]'::jsonb;
    END IF;

    IF purchase_inactivity > 60 THEN
        probability := probability + 0.20;
        reasons := reasons || '["purchase_inactivity_60_days"]'::jsonb;
    END IF;

    IF purchase_inactivity > 90 THEN
        probability := probability + 0.20;
        reasons := reasons || '["purchase_inactivity_90_days"]'::jsonb;
    END IF;

    IF engagement_inactivity > policy.engagement_inactivity_days THEN
        probability := probability + 0.15;
        reasons := reasons || '["low_engagement"]'::jsonb;
    END IF;

    IF purchase_count = 0 THEN
        probability := probability + 0.15;
        reasons := reasons || '["no_purchase_history"]'::jsonb;
    END IF;

    IF support_count >= 3 THEN
        probability := probability + 0.10;
        reasons := reasons || '["repeated_support_interactions"]'::jsonb;
    END IF;

    probability := LEAST(probability, 0.99);

    RETURN QUERY
    SELECT
        p_customer_id,
        probability,
        CASE
            WHEN probability >= policy.high_threshold
                THEN 'high'::risk_level
            WHEN probability >= policy.medium_threshold
                THEN 'medium'::risk_level
            ELSE 'low'::risk_level
        END,
        reasons;
END;
$$;


-- ============================================================
-- 19. COHORT RETENTION VIEW
-- ============================================================

CREATE OR REPLACE VIEW cohort_retention AS
WITH cohort_members AS (
    SELECT
        customer_id,
        DATE_TRUNC(
            'month',
            acquisition_date
        )::date AS cohort_month
    FROM customers
),
activity AS (
    SELECT DISTINCT
        customer_id,
        DATE_TRUNC(
            'month',
            occurred_at
        )::date AS activity_month
    FROM customer_events
    WHERE event_type IN ('purchase', 'login')
),
cohort_activity AS (
    SELECT
        cm.cohort_month,
        (
            EXTRACT(YEAR FROM age(
                a.activity_month,
                cm.cohort_month
            )) * 12
            +
            EXTRACT(MONTH FROM age(
                a.activity_month,
                cm.cohort_month
            ))
        )::INTEGER AS period_number,
        cm.customer_id
    FROM cohort_members cm
    JOIN activity a
      ON a.customer_id = cm.customer_id
    WHERE a.activity_month >= cm.cohort_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM cohort_members
    GROUP BY cohort_month
),
period_activity AS (
    SELECT
        cohort_month,
        period_number,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_activity
    GROUP BY cohort_month, period_number
)
SELECT
    pa.cohort_month,
    cs.cohort_size,
    pa.period_number,
    pa.active_customers,
    ROUND(
        pa.active_customers::NUMERIC
        / NULLIF(cs.cohort_size, 0) * 100,
        2
    ) AS retention_percentage
FROM period_activity pa
JOIN cohort_sizes cs
  ON cs.cohort_month = pa.cohort_month;


-- ============================================================
-- 20. CUSTOMER ANALYTICS VIEW
-- ============================================================

CREATE OR REPLACE VIEW customer_analytics AS
SELECT
    c.customer_id,
    c.external_customer_id,
    c.full_name,
    c.region,
    c.status,
    c.loyalty_tier,
    c.acquisition_date,

    COUNT(e.event_id) FILTER (
        WHERE e.event_type = 'purchase'
    ) AS purchase_count,

    COALESCE(
        SUM(e.amount) FILTER (
            WHERE e.event_type = 'purchase'
        ),
        0
    ) AS lifetime_purchase_value,

    MAX(e.occurred_at) FILTER (
        WHERE e.event_type = 'purchase'
    ) AS last_purchase_at,

    MAX(e.occurred_at) AS last_activity_at

FROM customers c
LEFT JOIN customer_events e
    ON e.customer_id = c.customer_id

GROUP BY
    c.customer_id,
    c.external_customer_id,
    c.full_name,
    c.region,
    c.status,
    c.loyalty_tier,
    c.acquisition_date;


-- ============================================================
-- 21. LOYALTY TIER UPDATE FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_customer_loyalty_tier(
    p_customer_id BIGINT
)
RETURNS loyalty_tier
LANGUAGE plpgsql
AS $$
DECLARE
    lifetime_spend NUMERIC;
    selected_tier loyalty_tier;
BEGIN

    SELECT COALESCE(SUM(amount), 0)
    INTO lifetime_spend
    FROM customer_events
    WHERE customer_id = p_customer_id
      AND event_type = 'purchase';

    SELECT tier
    INTO selected_tier
    FROM loyalty_policies
    WHERE is_active = TRUE
      AND minimum_spend <= lifetime_spend
    ORDER BY minimum_spend DESC
    LIMIT 1;

    IF selected_tier IS NULL THEN
        RAISE EXCEPTION 'No matching loyalty policy';
    END IF;

    UPDATE customers
    SET loyalty_tier = selected_tier
    WHERE customer_id = p_customer_id;

    RETURN selected_tier;
END;
$$;


-- ============================================================
-- 22. CAMPAIGN PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW campaign_performance AS
SELECT
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    c.status,

    COUNT(a.assignment_id) AS contacted,

    COUNT(a.assignment_id) FILTER (
        WHERE a.converted_at IS NOT NULL
    ) AS converted,

    COALESCE(
        SUM(c.cost_per_contact),
        0
    ) AS total_campaign_cost,

    COALESCE(
        SUM(a.attributed_revenue),
        0
    ) AS attributed_revenue,

    ROUND(
        COUNT(a.assignment_id) FILTER (
            WHERE a.converted_at IS NOT NULL
        )::NUMERIC
        / NULLIF(COUNT(a.assignment_id), 0) * 100,
        2
    ) AS conversion_rate,

    ROUND(
        (
            COALESCE(SUM(a.attributed_revenue), 0)
            -
            COALESCE(SUM(c.cost_per_contact), 0)
        )
        /
        NULLIF(SUM(c.cost_per_contact), 0)
        * 100,
        2
    ) AS roi_percentage

FROM retention_campaigns c

LEFT JOIN campaign_assignments a
    ON a.campaign_id = c.campaign_id

GROUP BY
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    c.status;


-- ============================================================
-- 23. SAMPLE CUSTOMER RECORDS
-- ============================================================

INSERT INTO customers (
    external_customer_id,
    full_name,
    email,
    acquisition_date,
    region,
    monthly_revenue
)
VALUES
(
    'C001',
    'Aarav Sharma',
    'aarav@example.com',
    '2026-01-10',
    'North',
    999
),
(
    'C002',
    'Priya Verma',
    'priya@example.com',
    '2026-02-15',
    'South',
    1499
),
(
    'C003',
    'Rahul Singh',
    'rahul@example.com',
    '2026-03-20',
    'West',
    799
),
(
    'C004',
    'Ananya Gupta',
    'ananya@example.com',
    '2026-04-05',
    'East',
    1999
),
(
    'C005',
    'Vikram Rao',
    'vikram@example.com',
    '2026-05-12',
    'North',
    499
);


-- ============================================================
-- 24. SAMPLE BEHAVIORAL EVENTS
-- ============================================================

INSERT INTO customer_events (
    external_event_id,
    customer_id,
    event_type,
    occurred_at,
    amount,
    metadata
)
SELECT
    event.external_event_id,
    customer.customer_id,
    event.event_type::event_type,
    TIMESTAMPTZ '2026-11-27 00:00:00+00'
        - event.days_ago * INTERVAL '1 day',
    event.amount,
    event.metadata::jsonb

FROM (
    VALUES
        ('E001', 'C001', 'purchase', 5, 3000::NUMERIC, '{}'),
        ('E002', 'C001', 'purchase', 35, 2500, '{}'),
        ('E003', 'C001', 'login', 1, 0, '{}'),

        ('E004', 'C002', 'purchase', 15, 1500, '{}'),
        ('E005', 'C002', 'login', 2, 0, '{}'),

        ('E006', 'C003', 'purchase', 110, 700, '{}'),

        ('E007', 'C004', 'purchase', 80, 8000, '{}'),
        ('E008', 'C004', 'support', 10, 0, '{}'),
        ('E009', 'C004', 'support', 8, 0, '{}'),
        ('E010', 'C004', 'support', 5, 0, '{}'),

        ('E011', 'C005', 'purchase', 3, 600, '{}'),
        ('E012', 'C005', 'login', 1, 0, '{}')
) AS event(
    external_event_id,
    external_customer_id,
    event_type,
    days_ago,
    amount,
    metadata
)
JOIN customers customer
    ON customer.external_customer_id =
       event.external_customer_id;


-- ============================================================
-- 25. TRANSACTIONAL LOYALTY UPDATES
-- ============================================================

BEGIN;

SELECT update_customer_loyalty_tier(customer_id)
FROM customers;

COMMIT;


-- ============================================================
-- 26. CHURN ASSESSMENT SNAPSHOTS
-- ============================================================

INSERT INTO churn_assessments (
    customer_id,
    policy_id,
    churn_probability,
    risk,
    contributing_factors,
    assessed_at
)
SELECT
    assessment.customer_id,
    policy.policy_id,
    assessment.churn_probability,
    assessment.risk,
    assessment.factors,
    TIMESTAMPTZ '2026-11-27 00:00:00+00'

FROM customers customer

CROSS JOIN LATERAL assess_customer_churn(
    customer.customer_id,
    DATE '2026-11-27'
) assessment

JOIN churn_policies policy
    ON policy.is_active = TRUE
    AND policy.policy_name = 'standard_churn_policy';


-- ============================================================
-- 27. RFM SNAPSHOT PROCESSING
-- ============================================================

INSERT INTO rfm_snapshots (
    customer_id,
    reference_date,
    recency_days,
    frequency,
    monetary_value,
    rfm_score,
    segment
)
SELECT
    customer_id,
    DATE '2026-11-27',
    recency_days,
    frequency,
    monetary_value,
    rfm_score,
    segment

FROM customers customer

CROSS JOIN LATERAL calculate_customer_rfm(
    customer.customer_id,
    DATE '2026-11-27'
);


-- ============================================================
-- 28. CUSTOMER STATUS TRANSITION
-- ============================================================

UPDATE customers customer
SET status = CASE
    WHEN assessment.risk = 'high'
        THEN 'at_risk'::customer_status

    WHEN assessment.risk = 'low'
         AND customer.status = 'at_risk'
        THEN 'active'::customer_status

    ELSE customer.status
END

FROM churn_assessments assessment

WHERE assessment.customer_id = customer.customer_id
  AND assessment.assessed_at =
      TIMESTAMPTZ '2026-11-27 00:00:00+00';


-- ============================================================
-- 29. SAMPLE RETENTION CAMPAIGN
-- ============================================================

INSERT INTO retention_campaigns (
    campaign_code,
    campaign_name,
    campaign_type,
    status,
    target_status,
    budget,
    cost_per_contact,
    revenue_per_conversion,
    start_date,
    end_date
)
VALUES (
    'CMP001',
    'November Customer Reactivation',
    'reactivation',
    'active',
    'at_risk',
    1000,
    50,
    1500,
    '2026-11-01',
    '2026-11-30'
);


-- ============================================================
-- 30. CAMPAIGN TARGET ASSIGNMENT
-- ============================================================

INSERT INTO campaign_assignments (
    campaign_id,
    customer_id
)
SELECT
    campaign.campaign_id,
    customer.customer_id

FROM retention_campaigns campaign

JOIN customers customer
    ON customer.status = campaign.target_status

WHERE campaign.campaign_code = 'CMP001'

ORDER BY customer.customer_id

LIMIT 20;


-- ============================================================
-- 31. SAMPLE CAMPAIGN CONVERSION
-- ============================================================

UPDATE campaign_assignments
SET
    converted_at = assigned_at + INTERVAL '2 days',
    attributed_revenue = 1500

WHERE assignment_id = (
    SELECT assignment_id
    FROM campaign_assignments
    ORDER BY assignment_id
    LIMIT 1
);


-- ============================================================
-- 32. LOYALTY POINT EARNING
-- ============================================================

BEGIN;

WITH eligible_purchase AS (
    SELECT
        event.event_id,
        event.customer_id,
        event.amount,
        policy.points_multiplier

    FROM customer_events event

    JOIN customers customer
        ON customer.customer_id = event.customer_id

    JOIN loyalty_policies policy
        ON policy.tier = customer.loyalty_tier
       AND policy.is_active = TRUE

    WHERE event.external_event_id = 'E001'
      AND event.event_type = 'purchase'
)
INSERT INTO loyalty_transactions (
    customer_id,
    event_id,
    points_change,
    transaction_type,
    description
)
SELECT
    customer_id,
    event_id,
    FLOOR(amount * points_multiplier)::BIGINT,
    'earned',
    'Purchase loyalty reward'
FROM eligible_purchase
ON CONFLICT (event_id) DO NOTHING;

COMMIT;


-- ============================================================
-- 33. CUSTOMER RETENTION REPORT
-- ============================================================

SELECT
    COUNT(*) AS total_customers,

    COUNT(*) FILTER (
        WHERE status = 'active'
    ) AS active_customers,

    COUNT(*) FILTER (
        WHERE status = 'at_risk'
    ) AS at_risk_customers,

    COUNT(*) FILTER (
        WHERE status = 'churned'
    ) AS churned_customers,

    COUNT(*) FILTER (
        WHERE status = 'reactivated'
    ) AS reactivated_customers,

    ROUND(
        COUNT(*) FILTER (
            WHERE status = 'active'
        )::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS active_customer_percentage

FROM customers;


-- ============================================================
-- 34. CUSTOMER RISK REPORT
-- ============================================================

SELECT
    customer.external_customer_id,
    customer.full_name,
    customer.region,
    assessment.churn_probability,
    assessment.risk,
    assessment.contributing_factors

FROM churn_assessments assessment

JOIN customers customer
    ON customer.customer_id = assessment.customer_id

WHERE assessment.assessed_at =
      TIMESTAMPTZ '2026-11-27 00:00:00+00'

ORDER BY
    assessment.churn_probability DESC,
    customer.customer_id;


-- ============================================================
-- 35. RFM SEGMENT REPORT
-- ============================================================

SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(rfm_score), 2) AS average_score,
    ROUND(AVG(monetary_value), 2) AS average_spend,
    ROUND(AVG(recency_days), 2) AS average_recency

FROM rfm_snapshots

WHERE reference_date = DATE '2026-11-27'

GROUP BY segment

ORDER BY customer_count DESC;


-- ============================================================
-- 36. COHORT RETENTION REPORT
-- ============================================================

SELECT
    cohort_month,
    cohort_size,
    period_number,
    active_customers,
    retention_percentage

FROM cohort_retention

ORDER BY cohort_month, period_number;


-- ============================================================
-- 37. LOYALTY DISTRIBUTION
-- ============================================================

SELECT
    loyalty_tier,
    COUNT(*) AS customer_count,
    SUM(loyalty_points) AS total_points,
    ROUND(
        AVG(monthly_revenue),
        2
    ) AS average_monthly_revenue

FROM customers

GROUP BY loyalty_tier

ORDER BY
    CASE loyalty_tier
        WHEN 'bronze' THEN 1
        WHEN 'silver' THEN 2
        WHEN 'gold' THEN 3
        WHEN 'platinum' THEN 4
    END;


-- ============================================================
-- 38. CAMPAIGN PERFORMANCE REPORT
-- ============================================================

SELECT *
FROM campaign_performance
ORDER BY campaign_id;


-- ============================================================
-- 39. CUSTOMER LIFETIME VALUE REPORT
-- ============================================================

SELECT
    customer_id,
    external_customer_id,
    full_name,
    monthly_revenue,
    monthly_revenue * 0.65 / 0.04 AS estimated_clv

FROM customers

ORDER BY estimated_clv DESC;


-- ============================================================
-- 40. CUSTOMER ELIGIBILITY DETERMINATION
-- ============================================================

SELECT
    customer.external_customer_id,
    customer.full_name,

    assessment.churn_probability,

    CASE
        WHEN customer.status = 'at_risk'
             AND assessment.risk = 'high'
            THEN 'eligible_for_reactivation'

        WHEN customer.status = 'active'
             AND customer.loyalty_tier IN ('gold', 'platinum')
            THEN 'eligible_for_loyalty_rewards'

        WHEN customer.status = 'active'
            THEN 'eligible_for_engagement_campaign'

        ELSE 'manual_review_required'
    END AS campaign_eligibility

FROM customers customer

JOIN LATERAL assess_customer_churn(
    customer.customer_id,
    DATE '2026-11-27'
) assessment ON TRUE

ORDER BY assessment.churn_probability DESC;


-- ============================================================
-- 41. REGIONAL RETENTION ANALYTICS
-- ============================================================

SELECT
    region,
    COUNT(*) AS total_customers,

    COUNT(*) FILTER (
        WHERE status = 'active'
    ) AS active_customers,

    COUNT(*) FILTER (
        WHERE status = 'at_risk'
    ) AS at_risk_customers,

    ROUND(
        COUNT(*) FILTER (
            WHERE status = 'at_risk'
        )::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS regional_risk_percentage,

    ROUND(
        AVG(monthly_revenue),
        2
    ) AS average_monthly_revenue

FROM customers

GROUP BY region

ORDER BY regional_risk_percentage DESC;


-- ============================================================
-- 42. AUTOMATED CHURN RISK QUEUE
-- ============================================================

SELECT
    customer.external_customer_id,
    customer.full_name,
    customer.email,
    customer.region,
    assessment.churn_probability,
    assessment.contributing_factors

FROM customers customer

JOIN churn_assessments assessment
    ON assessment.customer_id = customer.customer_id

WHERE customer.status = 'at_risk'
  AND assessment.risk = 'high'

ORDER BY assessment.churn_probability DESC

LIMIT 100;


-- ============================================================
-- 43. DATA QUALITY VALIDATION
-- ============================================================

SELECT
    'duplicate_external_customer_ids' AS validation,
    COUNT(*) AS failures

FROM (
    SELECT external_customer_id
    FROM customers
    GROUP BY external_customer_id
    HAVING COUNT(*) > 1
) duplicates

UNION ALL

SELECT
    'negative_purchase_amounts',
    COUNT(*)

FROM customer_events

WHERE event_type = 'purchase'
  AND amount < 0

UNION ALL

SELECT
    'events_before_acquisition',
    COUNT(*)

FROM customer_events event

JOIN customers customer
    ON customer.customer_id = event.customer_id

WHERE event.occurred_at::date < customer.acquisition_date;


-- ============================================================
-- 44. TRANSACTIONAL CAMPAIGN PROCESSING EXAMPLE
-- ============================================================

BEGIN;

-- Lock the campaign before modifying campaign state.
SELECT campaign_id
FROM retention_campaigns
WHERE campaign_code = 'CMP001'
FOR UPDATE;

-- Mark the campaign as completed after processing.
UPDATE retention_campaigns
SET status = 'completed'
WHERE campaign_code = 'CMP001'
  AND status = 'active';

COMMIT;


-- ============================================================
-- 45. OPERATIONAL QUERY PLAN
-- ============================================================

EXPLAIN
SELECT
    customer_id,
    occurred_at,
    amount

FROM customer_events

WHERE customer_id = 1
  AND event_type = 'purchase'

ORDER BY occurred_at DESC;


-- ============================================================
-- END OF RETENTION ANALYTICS DATABASE SCRIPT
-- ============================================================
