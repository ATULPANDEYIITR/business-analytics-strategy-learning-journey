-- ============================================================
-- CAMPAIGN ANALYTICS DATABASE
-- PostgreSQL 15+
--
-- Domain:
-- Campaigns, channels, budgets, advertising activity,
-- conversions, attribution, ROI, ROAS and performance reports.
--
-- Includes:
-- Relational integrity, financial validation, event ingestion,
-- attribution, aggregation, budget governance and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS marketing;

SET search_path TO marketing, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE channel_type AS ENUM (
    'SEARCH',
    'SOCIAL',
    'EMAIL',
    'DISPLAY',
    'AFFILIATE',
    'VIDEO'
);

CREATE TYPE campaign_status AS ENUM (
    'ACTIVE',
    'PAUSED',
    'COMPLETED'
);

CREATE TYPE attribution_model AS ENUM (
    'FIRST_TOUCH',
    'LAST_TOUCH',
    'LINEAR'
);

CREATE TYPE conversion_status AS ENUM (
    'PENDING',
    'CONFIRMED',
    'REFUNDED',
    'CANCELLED'
);

CREATE TYPE performance_category AS ENUM (
    'EXCELLENT',
    'PROFITABLE',
    'BREAK_EVEN',
    'LOSS_MAKING',
    'NO_INVESTMENT'
);

-- ============================================================
-- 2. ORGANIZATIONAL STRUCTURE
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_currency
        CHECK (currency_code ~ '^[A-Z]{3}$')
);

CREATE TABLE marketing_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,

    CONSTRAINT valid_user_role
        CHECK (
            role IN (
                'ADMIN',
                'MANAGER',
                'ANALYST',
                'VIEWER'
            )
        ),

    CONSTRAINT unique_org_email
        UNIQUE (organization_id, email),

    CONSTRAINT unique_org_user
        UNIQUE (organization_id, user_id)
);

CREATE TABLE marketing_channels (
    channel_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code channel_type NOT NULL UNIQUE,
    channel_name VARCHAR(100) NOT NULL
);

-- ============================================================
-- 3. CAMPAIGN MASTER
-- ============================================================

CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    channel_id SMALLINT NOT NULL
        REFERENCES marketing_channels(channel_id),

    manager_id BIGINT,

    campaign_code VARCHAR(50) NOT NULL,
    campaign_name VARCHAR(200) NOT NULL,

    status campaign_status NOT NULL DEFAULT 'ACTIVE',

    budget NUMERIC(16,2) NOT NULL,
    planned_start DATE NOT NULL,
    planned_end DATE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_campaign_budget
        CHECK (budget > 0),

    CONSTRAINT valid_campaign_dates
        CHECK (planned_end >= planned_start),

    CONSTRAINT unique_org_campaign
        UNIQUE (organization_id, campaign_code),

    CONSTRAINT campaign_manager_fk
        FOREIGN KEY (organization_id, manager_id)
        REFERENCES marketing_users(organization_id, user_id)
);

CREATE INDEX idx_campaign_org_status
    ON campaigns(organization_id, status);

CREATE INDEX idx_campaign_dates
    ON campaigns(planned_start, planned_end);

CREATE INDEX idx_campaign_channel
    ON campaigns(channel_id, status);

-- ============================================================
-- 4. DAILY CAMPAIGN PERFORMANCE
-- ============================================================

CREATE TABLE campaign_daily_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_id BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    metric_date DATE NOT NULL,

    impressions BIGINT NOT NULL DEFAULT 0,
    clicks BIGINT NOT NULL DEFAULT 0,
    conversions BIGINT NOT NULL DEFAULT 0,

    spend NUMERIC(16,2) NOT NULL DEFAULT 0,
    attributed_revenue NUMERIC(16,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonnegative_daily_values
        CHECK (
            impressions >= 0
            AND clicks >= 0
            AND conversions >= 0
            AND spend >= 0
            AND attributed_revenue >= 0
        ),

    CONSTRAINT valid_daily_funnel
        CHECK (
            clicks <= impressions
            AND conversions <= clicks
        ),

    CONSTRAINT unique_campaign_day
        UNIQUE (campaign_id, metric_date)
);

CREATE INDEX idx_metrics_date_campaign
    ON campaign_daily_metrics(metric_date, campaign_id);

CREATE INDEX idx_metrics_campaign_date
    ON campaign_daily_metrics(campaign_id, metric_date DESC);

-- ============================================================
-- 5. CONVERSION EVENTS
-- ============================================================

CREATE TABLE conversions (
    conversion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_id BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    external_event_id VARCHAR(150) NOT NULL,

    customer_reference VARCHAR(150),

    conversion_timestamp TIMESTAMPTZ NOT NULL,

    conversion_value NUMERIC(16,2) NOT NULL,

    status conversion_status NOT NULL DEFAULT 'PENDING',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_conversion_value
        CHECK (conversion_value >= 0),

    CONSTRAINT unique_external_event
        UNIQUE (external_event_id)
);

CREATE INDEX idx_conversion_campaign_time
    ON conversions(campaign_id, conversion_timestamp);

CREATE INDEX idx_conversion_status
    ON conversions(status, conversion_timestamp);

-- ============================================================
-- 6. ATTRIBUTION TOUCHPOINTS
-- ============================================================

CREATE TABLE attribution_touchpoints (
    touchpoint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    conversion_id BIGINT NOT NULL
        REFERENCES conversions(conversion_id)
        ON DELETE CASCADE,

    campaign_id BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    touch_position INTEGER NOT NULL,

    touch_timestamp TIMESTAMPTZ NOT NULL,

    CONSTRAINT positive_touch_position
        CHECK (touch_position > 0),

    CONSTRAINT unique_conversion_position
        UNIQUE (conversion_id, touch_position)
);

CREATE INDEX idx_touchpoints_conversion
    ON attribution_touchpoints(conversion_id, touch_position);

-- ============================================================
-- 7. BUDGET GOVERNANCE
-- ============================================================

CREATE TABLE campaign_budget_adjustments (
    adjustment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_id BIGINT NOT NULL
        REFERENCES campaigns(campaign_id),

    approved_by BIGINT NOT NULL
        REFERENCES marketing_users(user_id),

    previous_budget NUMERIC(16,2) NOT NULL,
    revised_budget NUMERIC(16,2) NOT NULL,

    reason TEXT NOT NULL,

    approved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_adjustment_values
        CHECK (
            previous_budget > 0
            AND revised_budget > 0
            AND previous_budget <> revised_budget
        )
);

-- ============================================================
-- 8. CAMPAIGN UPDATE TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_campaign_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_campaign_updated_at
BEFORE UPDATE ON campaigns
FOR EACH ROW
EXECUTE FUNCTION update_campaign_timestamp();

-- ============================================================
-- 9. METRIC CALCULATION VIEW
-- ============================================================

CREATE OR REPLACE VIEW campaign_performance AS
WITH campaign_totals AS (
    SELECT
        c.campaign_id,
        c.organization_id,
        c.campaign_code,
        c.campaign_name,
        c.status,
        c.budget,
        ch.channel_code,

        COALESCE(SUM(m.impressions), 0) AS impressions,
        COALESCE(SUM(m.clicks), 0) AS clicks,
        COALESCE(SUM(m.conversions), 0) AS conversions,

        COALESCE(SUM(m.spend), 0) AS spend,
        COALESCE(SUM(m.attributed_revenue), 0) AS revenue

    FROM campaigns c

    JOIN marketing_channels ch
        ON ch.channel_id = c.channel_id

    LEFT JOIN campaign_daily_metrics m
        ON m.campaign_id = c.campaign_id

    GROUP BY
        c.campaign_id,
        c.organization_id,
        c.campaign_code,
        c.campaign_name,
        c.status,
        c.budget,
        ch.channel_code
)
SELECT
    campaign_id,
    organization_id,
    campaign_code,
    campaign_name,
    channel_code,
    status,

    budget,
    impressions,
    clicks,
    conversions,

    spend,
    revenue,

    revenue - spend AS profit,

    CASE
        WHEN spend > 0
        THEN ROUND(
            ((revenue - spend) / spend) * 100,
            2
        )
        ELSE 0
    END AS roi_percentage,

    CASE
        WHEN spend > 0
        THEN ROUND(revenue / spend, 4)
        ELSE 0
    END AS roas,

    CASE
        WHEN impressions > 0
        THEN ROUND(
            clicks::NUMERIC / impressions * 100,
            2
        )
        ELSE 0
    END AS ctr_percentage,

    CASE
        WHEN clicks > 0
        THEN ROUND(
            conversions::NUMERIC / clicks * 100,
            2
        )
        ELSE 0
    END AS conversion_rate,

    CASE
        WHEN clicks > 0
        THEN ROUND(spend / clicks, 2)
        ELSE 0
    END AS cost_per_click,

    CASE
        WHEN conversions > 0
        THEN ROUND(spend / conversions, 2)
        ELSE 0
    END AS cost_per_acquisition,

    CASE
        WHEN impressions > 0
        THEN ROUND(spend * 1000 / impressions, 2)
        ELSE 0
    END AS cost_per_thousand,

    CASE
        WHEN budget > 0
        THEN ROUND(spend / budget * 100, 2)
        ELSE 0
    END AS budget_utilization

FROM campaign_totals;

-- ============================================================
-- 10. PERFORMANCE CLASSIFICATION
-- ============================================================

CREATE OR REPLACE FUNCTION classify_campaign(
    p_spend NUMERIC,
    p_roi NUMERIC,
    p_roas NUMERIC
)
RETURNS performance_category
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN p_spend = 0
            THEN 'NO_INVESTMENT'::performance_category

        WHEN p_roi > 100 AND p_roas >= 3
            THEN 'EXCELLENT'::performance_category

        WHEN p_roi > 0 AND p_roas > 1
            THEN 'PROFITABLE'::performance_category

        WHEN p_roi = 0
            THEN 'BREAK_EVEN'::performance_category

        ELSE 'LOSS_MAKING'::performance_category
    END;
$$;

CREATE OR REPLACE VIEW campaign_performance_classified AS
SELECT
    p.*,

    classify_campaign(
        p.spend,
        p.roi_percentage,
        p.roas
    ) AS performance_category

FROM campaign_performance p;

-- ============================================================
-- 11. PORTFOLIO REPORT
-- ============================================================

CREATE OR REPLACE VIEW portfolio_performance AS
SELECT
    organization_id,

    COUNT(*) AS campaign_count,

    SUM(spend) AS total_spend,
    SUM(revenue) AS total_revenue,
    SUM(profit) AS total_profit,

    CASE
        WHEN SUM(spend) > 0
        THEN ROUND(
            SUM(profit) / SUM(spend) * 100,
            2
        )
        ELSE 0
    END AS portfolio_roi,

    CASE
        WHEN SUM(spend) > 0
        THEN ROUND(
            SUM(revenue) / SUM(spend),
            4
        )
        ELSE 0
    END AS portfolio_roas

FROM campaign_performance

GROUP BY organization_id;

-- ============================================================
-- 12. CHANNEL PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW channel_performance AS
SELECT
    organization_id,
    channel_code,

    COUNT(*) AS campaign_count,

    SUM(spend) AS spend,
    SUM(revenue) AS revenue,
    SUM(profit) AS profit,

    CASE
        WHEN SUM(spend) > 0
        THEN ROUND(SUM(profit) / SUM(spend) * 100, 2)
        ELSE 0
    END AS roi,

    CASE
        WHEN SUM(spend) > 0
        THEN ROUND(SUM(revenue) / SUM(spend), 4)
        ELSE 0
    END AS roas

FROM campaign_performance

GROUP BY organization_id, channel_code;

-- ============================================================
-- 13. ATTRIBUTION EVALUATION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_attribution(
    p_model attribution_model
)
RETURNS TABLE (
    campaign_id BIGINT,
    attributed_revenue NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    WITH ranked_touches AS (
        SELECT
            tp.conversion_id,
            tp.campaign_id,
            c.conversion_value,

            ROW_NUMBER() OVER (
                PARTITION BY tp.conversion_id
                ORDER BY tp.touch_position ASC
            ) AS first_rank,

            ROW_NUMBER() OVER (
                PARTITION BY tp.conversion_id
                ORDER BY tp.touch_position DESC
            ) AS last_rank,

            COUNT(*) OVER (
                PARTITION BY tp.conversion_id
            ) AS touch_count

        FROM attribution_touchpoints tp

        JOIN conversions c
            ON c.conversion_id = tp.conversion_id

        WHERE c.status = 'CONFIRMED'
    ),

    allocated AS (
        SELECT
            rt.campaign_id,

            CASE
                WHEN p_model = 'FIRST_TOUCH'
                    AND rt.first_rank = 1
                    THEN rt.conversion_value

                WHEN p_model = 'LAST_TOUCH'
                    AND rt.last_rank = 1
                    THEN rt.conversion_value

                WHEN p_model = 'LINEAR'
                    THEN rt.conversion_value /
                        NULLIF(rt.touch_count, 0)

                ELSE 0
            END AS revenue_share

        FROM ranked_touches rt
    )

    SELECT
        a.campaign_id,
        SUM(a.revenue_share)::NUMERIC

    FROM allocated a

    WHERE a.revenue_share > 0

    GROUP BY a.campaign_id;
END;
$$;

-- ============================================================
-- 14. BUDGET ELIGIBILITY
-- ============================================================

CREATE TABLE organization_budget_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    minimum_roas NUMERIC(10,4) NOT NULL DEFAULT 1.5,

    maximum_utilization NUMERIC(10,2) NOT NULL DEFAULT 120,

    reserve_percentage NUMERIC(5,2) NOT NULL DEFAULT 10,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_policy_values
        CHECK (
            minimum_roas >= 0
            AND maximum_utilization > 0
            AND reserve_percentage >= 0
            AND reserve_percentage < 100
        ),

    CONSTRAINT unique_org_policy
        UNIQUE (organization_id)
);

CREATE OR REPLACE VIEW eligible_campaigns AS
SELECT
    p.*,
    policy.minimum_roas,
    policy.maximum_utilization,
    policy.reserve_percentage

FROM campaign_performance p

JOIN organization_budget_policies policy
    ON policy.organization_id = p.organization_id

WHERE
    p.status = 'ACTIVE'
    AND p.roas >= policy.minimum_roas
    AND p.budget_utilization < policy.maximum_utilization
    AND p.spend > 0;

-- ============================================================
-- 15. BUDGET ALLOCATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION recommend_budget_allocation(
    p_organization_id BIGINT,
    p_additional_budget NUMERIC
)
RETURNS TABLE (
    campaign_id BIGINT,
    campaign_name VARCHAR,
    allocated_budget NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_available NUMERIC;
    v_total_spend NUMERIC;
BEGIN
    IF p_additional_budget IS NULL
        OR p_additional_budget < 0
    THEN
        RAISE EXCEPTION
            'Additional budget must be non-negative';
    END IF;

    SELECT
        p_additional_budget *
        (1 - reserve_percentage / 100),

        SUM(e.spend)

    INTO v_available, v_total_spend

    FROM eligible_campaigns e

    JOIN organization_budget_policies policy
        ON policy.organization_id = e.organization_id

    WHERE e.organization_id = p_organization_id

    GROUP BY reserve_percentage;

    IF v_total_spend IS NULL OR v_total_spend = 0 THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        e.campaign_id,
        e.campaign_name::VARCHAR,

        ROUND(
            v_available * e.spend / v_total_spend,
            2
        )

    FROM eligible_campaigns e

    WHERE e.organization_id = p_organization_id

    ORDER BY e.profit DESC;
END;
$$;

-- ============================================================
-- 16. SAMPLE ORGANIZATION AND USERS
-- ============================================================

INSERT INTO organizations (
    organization_name,
    currency_code
)
VALUES
    ('Enterprise Marketing India', 'INR');

INSERT INTO marketing_users (
    organization_id,
    full_name,
    email,
    role
)
VALUES
    (1, 'Campaign Administrator',
        'admin@example.org', 'ADMIN'),

    (1, 'Marketing Manager',
        'manager@example.org', 'MANAGER'),

    (1, 'Marketing Analyst',
        'analyst@example.org', 'ANALYST'),

    (1, 'Reporting Viewer',
        'viewer@example.org', 'VIEWER');

INSERT INTO marketing_channels (
    channel_code,
    channel_name
)
VALUES
    ('SEARCH', 'Paid Search'),
    ('SOCIAL', 'Paid Social'),
    ('EMAIL', 'Email Marketing'),
    ('DISPLAY', 'Display Advertising'),
    ('AFFILIATE', 'Affiliate Marketing'),
    ('VIDEO', 'Video Advertising');

INSERT INTO organization_budget_policies (
    organization_id,
    minimum_roas,
    maximum_utilization,
    reserve_percentage
)
VALUES
    (1, 1.5, 120, 10);

-- ============================================================
-- 17. SAMPLE CAMPAIGNS
-- ============================================================

INSERT INTO campaigns (
    organization_id,
    channel_id,
    manager_id,
    campaign_code,
    campaign_name,
    status,
    budget,
    planned_start,
    planned_end
)
VALUES
    (
        1, 1, 2, 'C001',
        'Search Conversion Campaign',
        'ACTIVE', 50000,
        DATE '2026-11-01', DATE '2026-12-31'
    ),
    (
        1, 2, 2, 'C002',
        'Social Awareness Campaign',
        'ACTIVE', 40000,
        DATE '2026-11-01', DATE '2026-12-31'
    ),
    (
        1, 3, 2, 'C003',
        'Email Retention Campaign',
        'ACTIVE', 20000,
        DATE '2026-11-01', DATE '2026-12-31'
    ),
    (
        1, 4, 2, 'C004',
        'Display Remarketing Campaign',
        'ACTIVE', 30000,
        DATE '2026-11-01', DATE '2026-12-31'
    ),
    (
        1, 5, 2, 'C005',
        'Affiliate Acquisition Campaign',
        'ACTIVE', 25000,
        DATE '2026-11-01', DATE '2026-12-31'
    ),
    (
        1, 6, 2, 'C006',
        'Video Awareness Campaign',
        'PAUSED', 35000,
        DATE '2026-11-01', DATE '2026-12-31'
    );

-- ============================================================
-- 18. DAILY CAMPAIGN DATA
-- ============================================================

INSERT INTO campaign_daily_metrics (
    campaign_id,
    metric_date,
    impressions,
    clicks,
    conversions,
    spend,
    attributed_revenue
)
VALUES
    (1, DATE '2026-11-20', 500000, 25000, 1500, 35000, 140000),
    (2, DATE '2026-11-20', 800000, 16000, 400, 30000, 45000),
    (3, DATE '2026-11-20', 200000, 30000, 2400, 12000, 96000),
    (4, DATE '2026-11-20', 1000000, 10000, 250, 25000, 18000),
    (5, DATE '2026-11-20', 300000, 12000, 900, 15000, 75000),
    (6, DATE '2026-11-20', 0, 0, 0, 0, 0);

-- ============================================================
-- 19. SAMPLE CONVERSION EVENTS
-- ============================================================

INSERT INTO conversions (
    campaign_id,
    external_event_id,
    customer_reference,
    conversion_timestamp,
    conversion_value,
    status
)
VALUES
    (
        1, 'EVENT-001', 'CUSTOMER-001',
        TIMESTAMPTZ '2026-11-20 10:00:00+05:30',
        10000, 'CONFIRMED'
    ),
    (
        1, 'EVENT-002', 'CUSTOMER-002',
        TIMESTAMPTZ '2026-11-20 11:00:00+05:30',
        5000, 'CONFIRMED'
    ),
    (
        3, 'EVENT-003', 'CUSTOMER-003',
        TIMESTAMPTZ '2026-11-20 12:00:00+05:30',
        8000, 'PENDING'
    ),
    (
        4, 'EVENT-004', 'CUSTOMER-004',
        TIMESTAMPTZ '2026-11-20 13:00:00+05:30',
        3000, 'REFUNDED'
    );

INSERT INTO attribution_touchpoints (
    conversion_id,
    campaign_id,
    touch_position,
    touch_timestamp
)
VALUES
    (1, 1, 1, TIMESTAMPTZ '2026-11-18 09:00:00+05:30'),
    (1, 2, 2, TIMESTAMPTZ '2026-11-19 09:00:00+05:30'),
    (1, 3, 3, TIMESTAMPTZ '2026-11-20 09:00:00+05:30'),

    (2, 2, 1, TIMESTAMPTZ '2026-11-18 10:00:00+05:30'),
    (2, 1, 2, TIMESTAMPTZ '2026-11-20 10:30:00+05:30');

COMMIT;

-- ============================================================
-- 20. RETRIEVAL QUERIES
-- ============================================================

-- All campaign performance metrics.
SELECT *
FROM campaign_performance
ORDER BY profit DESC;

-- Detailed classified performance.
SELECT
    campaign_code,
    campaign_name,
    channel_code,
    spend,
    revenue,
    profit,
    roi_percentage,
    roas,
    performance_category
FROM campaign_performance_classified
ORDER BY roi_percentage DESC;

-- ============================================================
-- 21. PORTFOLIO AGGREGATION
-- ============================================================

SELECT *
FROM portfolio_performance;

SELECT *
FROM channel_performance
ORDER BY profit DESC;

-- ============================================================
-- 22. CONVERSION FUNNEL ANALYSIS
-- ============================================================

SELECT
    campaign_code,
    campaign_name,
    impressions,
    clicks,
    conversions,

    ctr_percentage,

    conversion_rate,

    cost_per_click,
    cost_per_acquisition,
    cost_per_thousand

FROM campaign_performance

ORDER BY conversions DESC;

-- ============================================================
-- 23. PERFORMANCE EVALUATION
-- ============================================================

-- Identify loss-making campaigns.
SELECT *
FROM campaign_performance_classified
WHERE performance_category = 'LOSS_MAKING';

-- Identify campaigns exceeding budget.
SELECT *
FROM campaign_performance
WHERE budget_utilization > 100;

-- Identify campaigns with low conversion rates.
SELECT
    campaign_name,
    conversion_rate,
    cost_per_acquisition
FROM campaign_performance
WHERE clicks > 0
  AND conversion_rate < 2;

-- ============================================================
-- 24. ATTRIBUTION MODEL COMPARISON
-- ============================================================

SELECT
    'FIRST_TOUCH' AS model,
    *
FROM calculate_attribution('FIRST_TOUCH')

UNION ALL

SELECT
    'LAST_TOUCH' AS model,
    *
FROM calculate_attribution('LAST_TOUCH')

UNION ALL

SELECT
    'LINEAR' AS model,
    *
FROM calculate_attribution('LINEAR');

-- ============================================================
-- 25. BUDGET OPTIMIZATION
-- ============================================================

SELECT *
FROM eligible_campaigns
ORDER BY profit DESC;

SELECT *
FROM recommend_budget_allocation(1, 100000);

-- ============================================================
-- 26. CAMPAIGN RANKING
-- ============================================================

SELECT
    campaign_id,
    campaign_name,
    profit,
    roi_percentage,
    roas,

    RANK() OVER (
        ORDER BY profit DESC
    ) AS profit_rank,

    DENSE_RANK() OVER (
        ORDER BY roas DESC
    ) AS roas_rank

FROM campaign_performance;

-- ============================================================
-- 27. TRANSACTIONAL DAILY DATA INGESTION
-- ============================================================

-- ON CONFLICT supports idempotent daily imports.
-- Reprocessing a campaign/date replaces the previous snapshot
-- instead of duplicating spend and revenue.

BEGIN;

INSERT INTO campaign_daily_metrics (
    campaign_id,
    metric_date,
    impressions,
    clicks,
    conversions,
    spend,
    attributed_revenue
)
VALUES (
    1,
    DATE '2026-11-21',
    100000,
    5000,
    300,
    7000,
    28000
)
ON CONFLICT (campaign_id, metric_date)
DO UPDATE SET
    impressions = EXCLUDED.impressions,
    clicks = EXCLUDED.clicks,
    conversions = EXCLUDED.conversions,
    spend = EXCLUDED.spend,
    attributed_revenue = EXCLUDED.attributed_revenue;

COMMIT;

-- ============================================================
-- 28. APPROVED BUDGET ADJUSTMENT
-- ============================================================

BEGIN;

WITH adjustment AS (
    SELECT
        campaign_id,
        budget AS old_budget,
        budget + 5000 AS new_budget
    FROM campaigns
    WHERE campaign_code = 'C001'
      AND status = 'ACTIVE'
    FOR UPDATE
),
updated AS (
    UPDATE campaigns c
    SET budget = a.new_budget
    FROM adjustment a
    WHERE c.campaign_id = a.campaign_id
    RETURNING
        c.campaign_id,
        a.old_budget,
        c.budget AS new_budget
)
INSERT INTO campaign_budget_adjustments (
    campaign_id,
    approved_by,
    previous_budget,
    revised_budget,
    reason
)
SELECT
    campaign_id,
    2,
    old_budget,
    new_budget,
    'Approved performance-based budget revision'
FROM updated;

COMMIT;

-- ============================================================
-- 29. VALIDATION QUERIES
-- ============================================================

-- Confirm no invalid funnel records exist.
SELECT *
FROM campaign_daily_metrics
WHERE clicks > impressions
   OR conversions > clicks
   OR spend < 0
   OR attributed_revenue < 0;

-- Identify duplicate external events.
-- The UNIQUE constraint prevents duplicates.
SELECT
    external_event_id,
    COUNT(*)
FROM conversions
GROUP BY external_event_id
HAVING COUNT(*) > 1;

-- Check missing attribution.
SELECT
    c.conversion_id,
    c.external_event_id,
    c.conversion_value
FROM conversions c
LEFT JOIN attribution_touchpoints t
    ON t.conversion_id = c.conversion_id
WHERE c.status = 'CONFIRMED'
GROUP BY
    c.conversion_id,
    c.external_event_id,
    c.conversion_value
HAVING COUNT(t.touchpoint_id) = 0;

-- ============================================================
-- 30. OPERATIONAL REPORTING
-- ============================================================

SELECT
    organization_name,
    currency_code,
    p.campaign_count,
    p.total_spend,
    p.total_revenue,
    p.total_profit,
    p.portfolio_roi,
    p.portfolio_roas

FROM organizations o

JOIN portfolio_performance p
    ON p.organization_id = o.organization_id;

-- Campaign-level budget consumption.
SELECT
    campaign_name,
    budget,
    spend,
    budget - spend AS remaining_budget,
    budget_utilization
FROM campaign_performance
ORDER BY budget_utilization DESC;

-- ============================================================
-- END OF CAMPAIGN ANALYTICS DATABASE
-- ============================================================
