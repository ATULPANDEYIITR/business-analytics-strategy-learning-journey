/*
    MARKETING ANALYTICS
    PostgreSQL 15+

    Covers:
    - Marketing campaigns and channels
    - Campaign expenditure and budget control
    - Impressions, clicks, and conversions
    - Customer acquisition and lifetime value
    - Marketing touchpoints and attribution
    - Conversion funnels
    - Campaign performance reporting
    - Channel comparisons
    - Data validation and workflow processing
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS marketing;

SET search_path TO marketing, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE campaign_status AS ENUM (
    'planned',
    'active',
    'paused',
    'completed'
);

CREATE TYPE channel_type AS ENUM (
    'search',
    'social',
    'email',
    'display',
    'affiliate',
    'referral'
);

CREATE TYPE event_type AS ENUM (
    'impression',
    'click',
    'conversion'
);

CREATE TYPE attribution_model AS ENUM (
    'first_touch',
    'last_touch',
    'linear'
);

-- ============================================================
-- 2. CORE TABLES
-- ============================================================

CREATE TABLE channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name channel_type NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_customer_id VARCHAR(100) NOT NULL UNIQUE,
    acquisition_date DATE NOT NULL,
    acquisition_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
    lifetime_revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
    customer_segment VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT customer_cost_nonnegative
        CHECK (acquisition_cost >= 0),

    CONSTRAINT customer_revenue_nonnegative
        CHECK (lifetime_revenue >= 0)
);

CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_code VARCHAR(40) NOT NULL UNIQUE,
    campaign_name VARCHAR(200) NOT NULL,
    channel_id BIGINT NOT NULL REFERENCES channels(channel_id),
    objective VARCHAR(100) NOT NULL,
    status campaign_status NOT NULL DEFAULT 'planned',
    budget NUMERIC(14,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT campaign_budget_nonnegative
        CHECK (budget >= 0),

    CONSTRAINT campaign_date_valid
        CHECK (end_date >= start_date)
);

CREATE TABLE campaign_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id BIGINT NOT NULL REFERENCES campaigns(campaign_id),
    reporting_date DATE NOT NULL,
    impressions BIGINT NOT NULL DEFAULT 0,
    clicks BIGINT NOT NULL DEFAULT 0,
    conversions BIGINT NOT NULL DEFAULT 0,
    spend NUMERIC(14,2) NOT NULL DEFAULT 0,
    revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT metric_unique_day
        UNIQUE (campaign_id, reporting_date),

    CONSTRAINT metric_nonnegative
        CHECK (
            impressions >= 0
            AND clicks >= 0
            AND conversions >= 0
            AND spend >= 0
            AND revenue >= 0
        ),

    CONSTRAINT metric_click_limit
        CHECK (clicks <= impressions),

    CONSTRAINT metric_conversion_limit
        CHECK (conversions <= clicks)
);

CREATE TABLE marketing_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_event_id VARCHAR(120) NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    campaign_id BIGINT NOT NULL REFERENCES campaigns(campaign_id),
    event_type event_type NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    revenue NUMERIC(14,2) NOT NULL DEFAULT 0,
    source_system VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT event_revenue_nonnegative
        CHECK (revenue >= 0),

    CONSTRAINT revenue_only_for_conversion
        CHECK (
            event_type = 'conversion'
            OR revenue = 0
        )
);

CREATE TABLE attribution_results (
    attribution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    campaign_id BIGINT NOT NULL REFERENCES campaigns(campaign_id),
    model attribution_model NOT NULL,
    attributed_revenue NUMERIC(14,2) NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT attributed_revenue_nonnegative
        CHECK (attributed_revenue >= 0)
);

-- ============================================================
-- 3. INDEXES
-- ============================================================

CREATE INDEX idx_campaign_channel_status
    ON campaigns(channel_id, status);

CREATE INDEX idx_campaign_date_range
    ON campaigns(start_date, end_date);

CREATE INDEX idx_metrics_campaign_date
    ON campaign_metrics(campaign_id, reporting_date DESC);

CREATE INDEX idx_events_customer_time
    ON marketing_events(customer_id, event_timestamp);

CREATE INDEX idx_events_campaign_type
    ON marketing_events(campaign_id, event_type);

CREATE INDEX idx_events_conversion
    ON marketing_events(event_timestamp)
    WHERE event_type = 'conversion';

CREATE INDEX idx_customers_segment
    ON customers(customer_segment);

CREATE INDEX idx_attribution_customer_model
    ON attribution_results(customer_id, model);

-- ============================================================
-- 4. CAMPAIGN STATE VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_campaign_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'completed' AND NEW.status <> 'completed' THEN
        RAISE EXCEPTION 'Completed campaigns cannot be reopened.';
    END IF;

    IF OLD.status = 'planned'
       AND NEW.status NOT IN ('planned', 'active', 'completed') THEN
        RAISE EXCEPTION 'Invalid planned campaign transition.';
    END IF;

    IF OLD.status = 'active'
       AND NEW.status NOT IN ('active', 'paused', 'completed') THEN
        RAISE EXCEPTION 'Invalid active campaign transition.';
    END IF;

    IF OLD.status = 'paused'
       AND NEW.status NOT IN ('paused', 'active', 'completed') THEN
        RAISE EXCEPTION 'Invalid paused campaign transition.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_campaign_transition
BEFORE UPDATE OF status ON campaigns
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION validate_campaign_transition();

-- ============================================================
-- 5. CAMPAIGN BUDGET CONTROL
-- ============================================================

CREATE OR REPLACE FUNCTION validate_campaign_spend()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    approved_budget NUMERIC(14,2);
    accumulated_spend NUMERIC(14,2);
BEGIN
    SELECT budget
    INTO approved_budget
    FROM campaigns
    WHERE campaign_id = NEW.campaign_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign does not exist.';
    END IF;

    SELECT COALESCE(SUM(spend), 0)
    INTO accumulated_spend
    FROM campaign_metrics
    WHERE campaign_id = NEW.campaign_id
      AND metric_id <> COALESCE(NEW.metric_id, -1);

    IF accumulated_spend + NEW.spend > approved_budget THEN
        RAISE EXCEPTION
            'Campaign budget exceeded. Budget: %, proposed spend: %',
            approved_budget,
            accumulated_spend + NEW.spend;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_campaign_spend
BEFORE INSERT OR UPDATE OF spend, campaign_id
ON campaign_metrics
FOR EACH ROW
EXECUTE FUNCTION validate_campaign_spend();

-- ============================================================
-- 6. MARKETING EVENT VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_marketing_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status campaign_status;
BEGIN
    SELECT status
    INTO current_status
    FROM campaigns
    WHERE campaign_id = NEW.campaign_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Campaign does not exist.';
    END IF;

    IF current_status <> 'active' THEN
        RAISE EXCEPTION
            'Events cannot be assigned to inactive campaigns.';
    END IF;

    IF NEW.event_timestamp::date < (
        SELECT start_date
        FROM campaigns
        WHERE campaign_id = NEW.campaign_id
    ) OR NEW.event_timestamp::date > (
        SELECT end_date
        FROM campaigns
        WHERE campaign_id = NEW.campaign_id
    ) THEN
        RAISE EXCEPTION 'Event timestamp falls outside campaign dates.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_marketing_event
BEFORE INSERT ON marketing_events
FOR EACH ROW
EXECUTE FUNCTION validate_marketing_event();

-- ============================================================
-- 7. REUSABLE METRIC FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION safe_divide(
    numerator NUMERIC,
    denominator NUMERIC
)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
PARALLEL SAFE
AS $$
    SELECT CASE
        WHEN denominator IS NULL OR denominator = 0 THEN 0
        ELSE numerator / denominator
    END;
$$;

-- ============================================================
-- 8. CAMPAIGN PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW campaign_performance AS
WITH totals AS (
    SELECT
        c.campaign_id,
        c.campaign_code,
        c.campaign_name,
        ch.channel_name,
        c.budget,
        c.status,
        COALESCE(SUM(m.impressions), 0) AS impressions,
        COALESCE(SUM(m.clicks), 0) AS clicks,
        COALESCE(SUM(m.conversions), 0) AS conversions,
        COALESCE(SUM(m.spend), 0) AS spend,
        COALESCE(SUM(m.revenue), 0) AS revenue
    FROM campaigns c
    JOIN channels ch
        ON ch.channel_id = c.channel_id
    LEFT JOIN campaign_metrics m
        ON m.campaign_id = c.campaign_id
    GROUP BY
        c.campaign_id,
        c.campaign_code,
        c.campaign_name,
        ch.channel_name,
        c.budget,
        c.status
)
SELECT
    *,
    ROUND(
        safe_divide(clicks * 100, impressions), 2
    ) AS ctr_percent,

    ROUND(
        safe_divide(conversions * 100, clicks), 2
    ) AS conversion_rate_percent,

    ROUND(
        safe_divide(spend, clicks), 2
    ) AS cpc,

    ROUND(
        safe_divide(spend, conversions), 2
    ) AS cpa,

    ROUND(
        safe_divide(revenue, spend), 2
    ) AS roas,

    ROUND(
        safe_divide((revenue - spend) * 100, spend), 2
    ) AS roi_percent,

    ROUND(
        budget - spend, 2
    ) AS remaining_budget
FROM totals;

-- ============================================================
-- 9. CONVERSION FUNNEL VIEW
-- ============================================================

CREATE OR REPLACE VIEW conversion_funnel AS
SELECT
    COALESCE(SUM(impressions), 0) AS impressions,
    COALESCE(SUM(clicks), 0) AS clicks,
    COALESCE(SUM(conversions), 0) AS conversions,

    ROUND(
        safe_divide(SUM(clicks) * 100, SUM(impressions)), 2
    ) AS impression_to_click_percent,

    ROUND(
        safe_divide(SUM(conversions) * 100, SUM(clicks)), 2
    ) AS click_to_conversion_percent,

    ROUND(
        safe_divide(SUM(conversions) * 100, SUM(impressions)), 2
    ) AS impression_to_conversion_percent
FROM campaign_metrics;

-- ============================================================
-- 10. CHANNEL PERFORMANCE VIEW
-- ============================================================

CREATE OR REPLACE VIEW channel_performance AS
SELECT
    channel_name,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(spend) AS spend,
    SUM(revenue) AS revenue,

    ROUND(
        safe_divide(SUM(revenue), SUM(spend)), 2
    ) AS roas,

    ROUND(
        safe_divide(SUM(spend), SUM(conversions)), 2
    ) AS cpa

FROM campaign_performance
GROUP BY channel_name;

-- ============================================================
-- 11. CUSTOMER ACQUISITION REPORT
-- ============================================================

CREATE OR REPLACE VIEW customer_acquisition_report AS
SELECT
    COUNT(*) AS customers,
    ROUND(AVG(acquisition_cost), 2) AS average_cac,
    ROUND(AVG(lifetime_revenue), 2) AS average_ltv,

    ROUND(
        safe_divide(
            AVG(lifetime_revenue),
            AVG(acquisition_cost)
        ), 2
    ) AS ltv_to_cac

FROM customers;

-- ============================================================
-- 12. ATTRIBUTION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_attribution(
    p_customer_id BIGINT,
    p_model attribution_model
)
RETURNS TABLE (
    campaign_id BIGINT,
    attributed_revenue NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    total_revenue NUMERIC(14,2);
    touch_count BIGINT;
BEGIN
    SELECT lifetime_revenue
    INTO total_revenue
    FROM customers
    WHERE customers.customer_id = p_customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer not found.';
    END IF;

    SELECT COUNT(*)
    INTO touch_count
    FROM marketing_events
    WHERE marketing_events.customer_id = p_customer_id
      AND event_type IN ('click', 'conversion');

    IF touch_count = 0 THEN
        RETURN;
    END IF;

    IF p_model = 'first_touch' THEN
        RETURN QUERY
        SELECT e.campaign_id, total_revenue
        FROM marketing_events e
        WHERE e.customer_id = p_customer_id
          AND e.event_type IN ('click', 'conversion')
        ORDER BY e.event_timestamp, e.event_id
        LIMIT 1;

    ELSIF p_model = 'last_touch' THEN
        RETURN QUERY
        SELECT e.campaign_id, total_revenue
        FROM marketing_events e
        WHERE e.customer_id = p_customer_id
          AND e.event_type IN ('click', 'conversion')
        ORDER BY e.event_timestamp DESC, e.event_id DESC
        LIMIT 1;

    ELSIF p_model = 'linear' THEN
        RETURN QUERY
        SELECT
            e.campaign_id,
            SUM(total_revenue / touch_count)::NUMERIC(14,2)
        FROM marketing_events e
        WHERE e.customer_id = p_customer_id
          AND e.event_type IN ('click', 'conversion')
        GROUP BY e.campaign_id;
    END IF;
END;
$$;

-- ============================================================
-- 13. ATTRIBUTION PROCESSING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE refresh_attribution(
    p_customer_id BIGINT,
    p_model attribution_model
)
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM attribution_results
    WHERE customer_id = p_customer_id
      AND model = p_model;

    INSERT INTO attribution_results (
        customer_id,
        campaign_id,
        model,
        attributed_revenue
    )
    SELECT
        p_customer_id,
        a.campaign_id,
        p_model,
        a.attributed_revenue
    FROM calculate_attribution(p_customer_id, p_model) a;
END;
$$;

-- ============================================================
-- 14. SAMPLE DATA
-- ============================================================

INSERT INTO channels (channel_name, description)
VALUES
    ('search', 'Search engine advertising'),
    ('social', 'Social media advertising'),
    ('email', 'Email marketing'),
    ('display', 'Display advertising'),
    ('affiliate', 'Affiliate marketing'),
    ('referral', 'Referral marketing');

INSERT INTO customers (
    external_customer_id,
    acquisition_date,
    acquisition_cost,
    lifetime_revenue,
    customer_segment
)
VALUES
    ('U001', '2026-02-10', 500, 3000, 'Premium'),
    ('U002', '2026-03-15', 400, 2500, 'Standard'),
    ('U003', '2026-04-20', 600, 4200, 'Premium');

INSERT INTO campaigns (
    campaign_code,
    campaign_name,
    channel_id,
    objective,
    status,
    budget,
    start_date,
    end_date
)
SELECT
    sample.campaign_code,
    sample.campaign_name,
    ch.channel_id,
    sample.objective,
    'planned',
    sample.budget,
    DATE '2026-01-01',
    DATE '2026-12-31'
FROM (
    VALUES
        ('C001', 'Search Acquisition', 'Customer Acquisition',
         'search'::channel_type, 50000::NUMERIC),
        ('C002', 'Social Awareness', 'Brand Awareness',
         'social'::channel_type, 40000::NUMERIC),
        ('C003', 'Email Retention', 'Customer Retention',
         'email'::channel_type, 20000::NUMERIC)
) AS sample(
    campaign_code,
    campaign_name,
    objective,
    channel_name,
    budget
)
JOIN channels ch
    ON ch.channel_name = sample.channel_name;

UPDATE campaigns
SET status = 'active'
WHERE campaign_code IN ('C001', 'C002', 'C003');

INSERT INTO campaign_metrics (
    campaign_id,
    reporting_date,
    impressions,
    clicks,
    conversions,
    spend,
    revenue
)
SELECT
    c.campaign_id,
    sample.reporting_date,
    sample.impressions,
    sample.clicks,
    sample.conversions,
    sample.spend,
    sample.revenue
FROM (
    VALUES
        ('C001', DATE '2026-02-01', 100000::BIGINT,
         8000::BIGINT, 640::BIGINT, 40000::NUMERIC, 240000::NUMERIC),
        ('C002', DATE '2026-02-01', 150000::BIGINT,
         6000::BIGINT, 240::BIGINT, 30000::NUMERIC, 90000::NUMERIC),
        ('C003', DATE '2026-02-01', 50000::BIGINT,
         10000::BIGINT, 1200::BIGINT, 15000::NUMERIC, 180000::NUMERIC)
) AS sample(
    campaign_code,
    reporting_date,
    impressions,
    clicks,
    conversions,
    spend,
    revenue
)
JOIN campaigns c
    ON c.campaign_code = sample.campaign_code;

INSERT INTO marketing_events (
    external_event_id,
    customer_id,
    campaign_id,
    event_type,
    event_timestamp,
    revenue,
    source_system
)
SELECT
    sample.external_event_id,
    customer.customer_id,
    campaign.campaign_id,
    sample.event_type,
    sample.event_timestamp,
    sample.revenue,
    'website'
FROM (
    VALUES
        ('E001', 'U001', 'C002', 'impression'::event_type,
         TIMESTAMPTZ '2026-02-01 10:00:00+00', 0::NUMERIC),
        ('E002', 'U001', 'C002', 'click'::event_type,
         TIMESTAMPTZ '2026-02-01 10:05:00+00', 0::NUMERIC),
        ('E003', 'U001', 'C001', 'impression'::event_type,
         TIMESTAMPTZ '2026-02-02 10:00:00+00', 0::NUMERIC),
        ('E004', 'U001', 'C001', 'click'::event_type,
         TIMESTAMPTZ '2026-02-02 10:05:00+00', 0::NUMERIC),
        ('E005', 'U001', 'C001', 'conversion'::event_type,
         TIMESTAMPTZ '2026-02-02 11:00:00+00', 3000::NUMERIC),
        ('E006', 'U002', 'C003', 'click'::event_type,
         TIMESTAMPTZ '2026-03-14 15:00:00+00', 0::NUMERIC)
) AS sample(
    external_event_id,
    customer_code,
    campaign_code,
    event_type,
    event_timestamp,
    revenue
)
JOIN customers customer
    ON customer.external_customer_id = sample.customer_code
JOIN campaigns campaign
    ON campaign.campaign_code = sample.campaign_code;

COMMIT;

-- ============================================================
-- 15. CAMPAIGN RETRIEVAL
-- ============================================================

SELECT *
FROM campaign_performance
ORDER BY roas DESC;

-- ============================================================
-- 16. FUNNEL ANALYSIS
-- ============================================================

SELECT *
FROM conversion_funnel;

-- ============================================================
-- 17. CHANNEL COMPARISON
-- ============================================================

SELECT
    channel_name,
    spend,
    revenue,
    conversions,
    roas,
    cpa
FROM channel_performance
ORDER BY roas DESC;

-- ============================================================
-- 18. CUSTOMER ACQUISITION ANALYSIS
-- ============================================================

SELECT *
FROM customer_acquisition_report;

-- ============================================================
-- 19. CUSTOMER JOURNEY RETRIEVAL
-- ============================================================

SELECT
    customer.external_customer_id,
    campaign.campaign_code,
    campaign.campaign_name,
    event.event_type,
    event.event_timestamp,
    event.revenue
FROM marketing_events event
JOIN customers customer
    ON customer.customer_id = event.customer_id
JOIN campaigns campaign
    ON campaign.campaign_id = event.campaign_id
ORDER BY customer.customer_id, event.event_timestamp;

-- ============================================================
-- 20. ATTRIBUTION PROCESSING
-- ============================================================

CALL refresh_attribution(
    (SELECT customer_id
     FROM customers
     WHERE external_customer_id = 'U001'),
    'first_touch'
);

CALL refresh_attribution(
    (SELECT customer_id
     FROM customers
     WHERE external_customer_id = 'U001'),
    'last_touch'
);

CALL refresh_attribution(
    (SELECT customer_id
     FROM customers
     WHERE external_customer_id = 'U001'),
    'linear'
);

SELECT
    customer.external_customer_id,
    campaign.campaign_code,
    attribution.model,
    attribution.attributed_revenue
FROM attribution_results attribution
JOIN customers customer
    ON customer.customer_id = attribution.customer_id
JOIN campaigns campaign
    ON campaign.campaign_id = attribution.campaign_id
ORDER BY customer.customer_id, attribution.model, campaign.campaign_code;

-- ============================================================
-- 21. CAMPAIGN PERFORMANCE EVALUATION
-- ============================================================

SELECT
    campaign_code,
    campaign_name,
    channel_name,
    ctr_percent,
    conversion_rate_percent,
    cpa,
    roas,
    roi_percent,
    CASE
        WHEN roas >= 5 THEN 'High Performance'
        WHEN roas >= 2 THEN 'Moderate Performance'
        ELSE 'Needs Review'
    END AS performance_category
FROM campaign_performance
ORDER BY roas DESC;

-- ============================================================
-- 22. BUDGET UTILIZATION
-- ============================================================

SELECT
    campaign_code,
    budget,
    spend,
    remaining_budget,
    ROUND(safe_divide(spend * 100, budget), 2)
        AS budget_utilization_percent
FROM campaign_performance
ORDER BY budget_utilization_percent DESC;

-- ============================================================
-- 23. DAILY PERFORMANCE AGGREGATION
-- ============================================================

SELECT
    reporting_date,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(conversions) AS conversions,
    SUM(spend) AS spend,
    SUM(revenue) AS revenue,
    ROUND(
        safe_divide(SUM(revenue), SUM(spend)), 2
    ) AS daily_roas
FROM campaign_metrics
GROUP BY reporting_date
ORDER BY reporting_date;

-- ============================================================
-- 24. DATA QUALITY VALIDATION
-- ============================================================

SELECT
    campaign_id,
    reporting_date,
    impressions,
    clicks,
    conversions
FROM campaign_metrics
WHERE clicks > impressions
   OR conversions > clicks
   OR spend < 0
   OR revenue < 0;

-- Check event IDs and customer references.
SELECT
    COUNT(*) AS total_events,
    COUNT(DISTINCT external_event_id) AS unique_events
FROM marketing_events;

-- ============================================================
-- 25. TRANSACTIONAL CAMPAIGN PROCESSING EXAMPLE
-- ============================================================

BEGIN;

UPDATE campaigns
SET status = 'paused'
WHERE campaign_code = 'C002'
  AND status = 'active';

-- The transaction can be committed after validation.
COMMIT;

/*
    Invalid sample cases are deliberately not inserted into the
    production sample transaction:

    - Negative campaign budget.
    - Clicks exceeding impressions.
    - Conversions exceeding clicks.
    - Spend exceeding the approved campaign budget.
    - Duplicate event identifiers.
    - Marketing events assigned to inactive campaigns.
    - Campaign events outside the campaign date range.

    Database constraints and triggers reject these operations.
*/
