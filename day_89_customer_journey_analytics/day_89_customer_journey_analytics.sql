-- ============================================================
-- CUSTOMER JOURNEY ANALYTICS
-- PostgreSQL 15+
--
-- Domain:
-- Touchpoints, behavioral analysis, customer identity,
-- sessions, funnels, attribution, cohorts, segmentation,
-- consent enforcement and revenue reporting.
--
-- This script creates a self-contained demonstration schema.
-- ============================================================

BEGIN;

DROP SCHEMA IF EXISTS customer_journey CASCADE;

CREATE SCHEMA customer_journey;

SET search_path TO customer_journey, public;

-- ============================================================
-- 1. DOMAIN TYPES
-- ============================================================

CREATE TYPE consent_status AS ENUM (
    'granted',
    'denied',
    'unknown'
);

CREATE TYPE event_type AS ENUM (
    'ad_impression',
    'ad_click',
    'page_view',
    'product_view',
    'search',
    'add_to_cart',
    'checkout',
    'purchase',
    'signup',
    'support_request'
);

CREATE TYPE acquisition_channel AS ENUM (
    'organic_search',
    'paid_search',
    'social',
    'email',
    'direct',
    'referral',
    'display'
);

CREATE TYPE journey_stage AS ENUM (
    'awareness',
    'consideration',
    'conversion',
    'retention'
);

CREATE TYPE attribution_model AS ENUM (
    'first_touch',
    'last_touch',
    'linear',
    'position_based'
);

-- ============================================================
-- 2. CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_reference VARCHAR(100) NOT NULL UNIQUE,

    consent consent_status NOT NULL DEFAULT 'unknown',

    region VARCHAR(10) NOT NULL DEFAULT 'IN',

    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (LENGTH(external_reference) > 0)
);

CREATE INDEX idx_customers_registration
ON customers (registered_at);

CREATE INDEX idx_customers_consent
ON customers (consent, customer_id);

-- ============================================================
-- 3. CUSTOMER IDENTITY
-- ============================================================

CREATE TABLE customer_identities (
    identity_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    identity_type VARCHAR(30) NOT NULL,

    identity_value VARCHAR(255) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (identity_type, identity_value),

    CHECK (
        identity_type IN (
            'web_cookie',
            'mobile_device',
            'account',
            'anonymous_session'
        )
    )
);

CREATE INDEX idx_customer_identity_owner
ON customer_identities (customer_id);

-- ============================================================
-- 4. CAMPAIGNS
-- ============================================================

CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    campaign_code VARCHAR(100) NOT NULL UNIQUE,

    campaign_name VARCHAR(200) NOT NULL,

    channel acquisition_channel NOT NULL,

    campaign_cost NUMERIC(14,2) NOT NULL DEFAULT 0,

    starts_at TIMESTAMPTZ,

    ends_at TIMESTAMPTZ,

    CHECK (campaign_cost >= 0),

    CHECK (
        ends_at IS NULL
        OR starts_at IS NULL
        OR ends_at >= starts_at
    )
);

-- ============================================================
-- 5. SESSIONS
-- ============================================================

CREATE TABLE sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    session_reference VARCHAR(100) NOT NULL UNIQUE,

    started_at TIMESTAMPTZ NOT NULL,

    last_activity_at TIMESTAMPTZ NOT NULL,

    entry_channel acquisition_channel NOT NULL,

    device_type VARCHAR(30),

    CHECK (last_activity_at >= started_at)
);

CREATE INDEX idx_sessions_customer_start
ON sessions (customer_id, started_at DESC);

CREATE INDEX idx_sessions_entry_channel
ON sessions (entry_channel);

-- ============================================================
-- 6. TOUCHPOINT EVENTS
-- ============================================================

CREATE TABLE touchpoints (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    event_reference UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    session_id BIGINT NOT NULL
        REFERENCES sessions(session_id)
        ON DELETE CASCADE,

    event_type event_type NOT NULL,

    channel acquisition_channel NOT NULL,

    campaign_id BIGINT
        REFERENCES campaigns(campaign_id)
        ON DELETE SET NULL,

    event_timestamp TIMESTAMPTZ NOT NULL,

    page_path VARCHAR(500) NOT NULL,

    product_reference VARCHAR(100),

    monetary_value NUMERIC(14,2) NOT NULL DEFAULT 0,

    properties JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (monetary_value >= 0),

    CHECK (
        event_type <> 'purchase'
        OR monetary_value > 0
    ),

    CHECK (jsonb_typeof(properties) = 'object'),

    CHECK (LENGTH(page_path) > 0)
);

CREATE INDEX idx_touchpoints_customer_time
ON touchpoints (customer_id, event_timestamp);

CREATE INDEX idx_touchpoints_session_time
ON touchpoints (session_id, event_timestamp);

CREATE INDEX idx_touchpoints_type_time
ON touchpoints (event_type, event_timestamp);

CREATE INDEX idx_touchpoints_channel_time
ON touchpoints (channel, event_timestamp);

CREATE INDEX idx_touchpoints_campaign
ON touchpoints (campaign_id)
WHERE campaign_id IS NOT NULL;

CREATE INDEX idx_touchpoints_purchase
ON touchpoints (event_timestamp DESC)
WHERE event_type = 'purchase';

CREATE INDEX idx_touchpoints_properties
ON touchpoints USING GIN (properties);

-- ============================================================
-- 7. REVIEWABLE CONSENT ENFORCEMENT
-- ============================================================

CREATE FUNCTION enforce_analytics_consent()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    customer_consent consent_status;
    session_customer BIGINT;
BEGIN
    SELECT consent
    INTO customer_consent
    FROM customers
    WHERE customer_id = NEW.customer_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer does not exist';
    END IF;

    IF customer_consent <> 'granted' THEN
        RAISE EXCEPTION
            'Analytics ingestion rejected: consent is not granted';
    END IF;

    SELECT customer_id
    INTO session_customer
    FROM sessions
    WHERE session_id = NEW.session_id;

    IF session_customer IS DISTINCT FROM NEW.customer_id THEN
        RAISE EXCEPTION
            'Session does not belong to the specified customer';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_touchpoint_consent
BEFORE INSERT ON touchpoints
FOR EACH ROW
EXECUTE FUNCTION enforce_analytics_consent();

-- ============================================================
-- 8. JOURNEY CLASSIFICATION
-- ============================================================

CREATE FUNCTION classify_journey_stage(
    p_event_type event_type
)
RETURNS journey_stage
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT CASE
        WHEN p_event_type IN (
            'ad_impression',
            'ad_click',
            'page_view'
        )
            THEN 'awareness'::journey_stage

        WHEN p_event_type IN (
            'search',
            'product_view',
            'add_to_cart'
        )
            THEN 'consideration'::journey_stage

        WHEN p_event_type IN (
            'checkout',
            'purchase'
        )
            THEN 'conversion'::journey_stage

        ELSE 'retention'::journey_stage
    END;
$$;

-- ============================================================
-- 9. SESSION ACTIVITY MAINTENANCE
-- ============================================================

CREATE FUNCTION update_session_activity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE sessions
    SET last_activity_at = GREATEST(
        last_activity_at,
        NEW.event_timestamp
    )
    WHERE session_id = NEW.session_id;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_update_session_activity
AFTER INSERT ON touchpoints
FOR EACH ROW
EXECUTE FUNCTION update_session_activity();

-- ============================================================
-- 10. JOURNEY TRANSITIONS
-- ============================================================

CREATE TABLE journey_transitions (
    transition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    event_id BIGINT NOT NULL UNIQUE
        REFERENCES touchpoints(event_id)
        ON DELETE CASCADE,

    stage journey_stage NOT NULL,

    transition_timestamp TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_journey_transitions_customer
ON journey_transitions (customer_id, transition_timestamp);

CREATE FUNCTION record_journey_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO journey_transitions (
        customer_id,
        event_id,
        stage,
        transition_timestamp
    )
    VALUES (
        NEW.customer_id,
        NEW.event_id,
        classify_journey_stage(NEW.event_type),
        NEW.event_timestamp
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_journey_transition
AFTER INSERT ON touchpoints
FOR EACH ROW
EXECUTE FUNCTION record_journey_transition();

-- ============================================================
-- 11. ATTRIBUTION POLICY
-- ============================================================

CREATE TABLE attribution_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(100) NOT NULL UNIQUE,

    model attribution_model NOT NULL,

    first_touch_weight NUMERIC(5,4) NOT NULL DEFAULT 0.4,

    last_touch_weight NUMERIC(5,4) NOT NULL DEFAULT 0.4,

    active BOOLEAN NOT NULL DEFAULT FALSE,

    CHECK (first_touch_weight >= 0),

    CHECK (last_touch_weight >= 0),

    CHECK (
        first_touch_weight + last_touch_weight <= 1
    )
);

CREATE UNIQUE INDEX idx_one_active_attribution_policy
ON attribution_policies (active)
WHERE active = TRUE;

INSERT INTO attribution_policies (
    policy_name,
    model,
    first_touch_weight,
    last_touch_weight,
    active
)
VALUES
    ('First Interaction', 'first_touch', 1, 0, FALSE),
    ('Final Interaction', 'last_touch', 0, 1, FALSE),
    ('Equal Distribution', 'linear', 0.4, 0.4, TRUE),
    ('Position Based', 'position_based', 0.4, 0.4, FALSE);

-- ============================================================
-- 12. ATTRIBUTION FUNCTION
-- ============================================================

CREATE FUNCTION calculate_touchpoint_attribution(
    p_customer_id BIGINT,
    p_purchase_event_id BIGINT,
    p_model attribution_model
)
RETURNS TABLE (
    channel acquisition_channel,
    attributed_weight NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    total_events BIGINT;
    first_channel acquisition_channel;
    last_channel acquisition_channel;
BEGIN
    SELECT COUNT(*)
    INTO total_events
    FROM touchpoints
    WHERE customer_id = p_customer_id
      AND event_timestamp <= (
          SELECT event_timestamp
          FROM touchpoints
          WHERE event_id = p_purchase_event_id
            AND customer_id = p_customer_id
            AND event_type = 'purchase'
      );

    IF total_events = 0 THEN
        RETURN;
    END IF;

    SELECT t.channel
    INTO first_channel
    FROM touchpoints t
    WHERE t.customer_id = p_customer_id
      AND t.event_timestamp <= (
          SELECT event_timestamp
          FROM touchpoints
          WHERE event_id = p_purchase_event_id
      )
    ORDER BY t.event_timestamp, t.event_id
    LIMIT 1;

    SELECT t.channel
    INTO last_channel
    FROM touchpoints t
    WHERE t.customer_id = p_customer_id
      AND t.event_timestamp <= (
          SELECT event_timestamp
          FROM touchpoints
          WHERE event_id = p_purchase_event_id
      )
    ORDER BY t.event_timestamp DESC, t.event_id DESC
    LIMIT 1;

    IF p_model = 'first_touch' THEN
        RETURN QUERY
        SELECT first_channel, 1.0000::NUMERIC;

    ELSIF p_model = 'last_touch' THEN
        RETURN QUERY
        SELECT last_channel, 1.0000::NUMERIC;

    ELSIF p_model = 'linear' THEN
        RETURN QUERY
        SELECT
            t.channel,
            COUNT(*)::NUMERIC / total_events
        FROM touchpoints t
        WHERE t.customer_id = p_customer_id
          AND t.event_timestamp <= (
              SELECT event_timestamp
              FROM touchpoints
              WHERE event_id = p_purchase_event_id
          )
        GROUP BY t.channel;

    ELSIF p_model = 'position_based' THEN
        RETURN QUERY
        WITH ordered AS (
            SELECT
                t.channel,
                ROW_NUMBER() OVER (
                    ORDER BY t.event_timestamp, t.event_id
                ) AS position,
                COUNT(*) OVER () AS total
            FROM touchpoints t
            WHERE t.customer_id = p_customer_id
              AND t.event_timestamp <= (
                  SELECT event_timestamp
                  FROM touchpoints
                  WHERE event_id = p_purchase_event_id
              )
        ),
        weighted AS (
            SELECT
                channel,
                CASE
                    WHEN total = 1 THEN 1.0::NUMERIC
                    WHEN position = 1 THEN 0.4::NUMERIC
                    WHEN position = total THEN 0.4::NUMERIC
                    ELSE 0.2::NUMERIC / (total - 2)
                END AS weight
            FROM ordered
        )
        SELECT
            weighted.channel,
            SUM(weighted.weight)
        FROM weighted
        GROUP BY weighted.channel;
    END IF;
END;
$$;

-- ============================================================
-- 13. REVENUE ATTRIBUTION REPORT
-- ============================================================

CREATE VIEW channel_revenue_report AS
SELECT
    t.channel,
    COUNT(*) AS total_touchpoints,
    COUNT(DISTINCT t.customer_id) AS unique_customers,

    COUNT(*) FILTER (
        WHERE t.event_type = 'purchase'
    ) AS purchase_events,

    COALESCE(
        SUM(t.monetary_value) FILTER (
            WHERE t.event_type = 'purchase'
        ),
        0
    ) AS direct_event_revenue,

    COUNT(DISTINCT t.campaign_id) AS campaigns

FROM touchpoints t
GROUP BY t.channel;

-- ============================================================
-- 14. SESSION REPORTING VIEW
-- ============================================================

CREATE VIEW session_analytics AS
SELECT
    s.session_id,
    s.session_reference,
    s.customer_id,
    s.entry_channel,
    s.started_at,
    s.last_activity_at,

    EXTRACT(
        EPOCH FROM (
            s.last_activity_at - s.started_at
        )
    ) AS duration_seconds,

    COUNT(t.event_id) AS event_count,

    COUNT(*) FILTER (
        WHERE t.event_type = 'purchase'
    ) AS purchase_count

FROM sessions s

LEFT JOIN touchpoints t
    ON t.session_id = s.session_id

GROUP BY
    s.session_id,
    s.session_reference,
    s.customer_id,
    s.entry_channel,
    s.started_at,
    s.last_activity_at;

-- ============================================================
-- 15. FUNNEL ANALYSIS
-- ============================================================

CREATE VIEW customer_funnel AS

WITH customer_stages AS (
    SELECT
        customer_id,

        MIN(event_timestamp) FILTER (
            WHERE event_type = 'page_view'
        ) AS awareness_time,

        MIN(event_timestamp) FILTER (
            WHERE event_type = 'product_view'
        ) AS product_time,

        MIN(event_timestamp) FILTER (
            WHERE event_type = 'add_to_cart'
        ) AS cart_time,

        MIN(event_timestamp) FILTER (
            WHERE event_type = 'checkout'
        ) AS checkout_time,

        MIN(event_timestamp) FILTER (
            WHERE event_type = 'purchase'
        ) AS purchase_time

    FROM touchpoints
    GROUP BY customer_id
)

SELECT
    customer_id,
    awareness_time,

    CASE
        WHEN product_time >= awareness_time
        THEN product_time
    END AS product_time,

    CASE
        WHEN cart_time >= product_time
        THEN cart_time
    END AS cart_time,

    CASE
        WHEN checkout_time >= cart_time
        THEN checkout_time
    END AS checkout_time,

    CASE
        WHEN purchase_time >= checkout_time
        THEN purchase_time
    END AS purchase_time

FROM customer_stages;

-- ============================================================
-- 16. FUNNEL AGGREGATION FUNCTION
-- ============================================================

CREATE FUNCTION get_funnel_metrics()
RETURNS TABLE (
    stage_name TEXT,
    customer_count BIGINT,
    conversion_rate NUMERIC,
    drop_off_rate NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
    WITH stages AS (
        SELECT 1 AS position, 'page_view'::TEXT AS name,
            COUNT(*) FILTER (
                WHERE awareness_time IS NOT NULL
            ) AS customers
        FROM customer_funnel

        UNION ALL

        SELECT 2, 'product_view',
            COUNT(*) FILTER (
                WHERE product_time IS NOT NULL
            )
        FROM customer_funnel

        UNION ALL

        SELECT 3, 'add_to_cart',
            COUNT(*) FILTER (
                WHERE cart_time IS NOT NULL
            )
        FROM customer_funnel

        UNION ALL

        SELECT 4, 'checkout',
            COUNT(*) FILTER (
                WHERE checkout_time IS NOT NULL
            )
        FROM customer_funnel

        UNION ALL

        SELECT 5, 'purchase',
            COUNT(*) FILTER (
                WHERE purchase_time IS NOT NULL
            )
        FROM customer_funnel
    ),
    calculated AS (
        SELECT
            position,
            name,
            customers,
            LAG(customers) OVER (
                ORDER BY position
            ) AS previous_customers
        FROM stages
    )
    SELECT
        name,
        customers,

        CASE
            WHEN position = 1 AND customers > 0 THEN 1.0
            WHEN previous_customers > 0
                THEN ROUND(
                    customers::NUMERIC / previous_customers,
                    4
                )
            ELSE 0
        END,

        CASE
            WHEN position = 1 OR previous_customers IS NULL
                THEN 0
            WHEN previous_customers > 0
                THEN ROUND(
                    1 - customers::NUMERIC / previous_customers,
                    4
                )
            ELSE 0
        END

    FROM calculated
    ORDER BY position;
$$;

-- ============================================================
-- 17. CUSTOMER BEHAVIOR SEGMENTATION
-- ============================================================

CREATE VIEW customer_behavior_profiles AS

WITH behavior AS (
    SELECT
        customer_id,

        COUNT(*) AS event_count,

        COUNT(*) FILTER (
            WHERE event_type = 'purchase'
        ) AS purchases,

        COUNT(*) FILTER (
            WHERE event_type = 'add_to_cart'
        ) AS cart_events,

        COUNT(*) FILTER (
            WHERE event_type = 'support_request'
        ) AS support_requests,

        COALESCE(
            SUM(monetary_value) FILTER (
                WHERE event_type = 'purchase'
            ),
            0
        ) AS revenue

    FROM touchpoints
    GROUP BY customer_id
)

SELECT
    customer_id,
    event_count,
    purchases,
    cart_events,
    support_requests,
    revenue,

    CASE
        WHEN support_requests > 0
            THEN 'support_engaged'

        WHEN purchases > 1
            THEN 'repeat_customer'

        WHEN purchases = 1
            THEN 'converted_customer'

        WHEN cart_events > 0
            THEN 'cart_abandoner'

        WHEN event_count > 3
            THEN 'engaged_visitor'

        ELSE 'visitor'
    END AS customer_segment

FROM behavior;

-- ============================================================
-- 18. COHORT RETENTION
-- ============================================================

CREATE VIEW monthly_cohort_retention AS

WITH customer_cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', registered_at)::DATE AS cohort_month
    FROM customers
),

monthly_activity AS (
    SELECT DISTINCT
        customer_id,
        DATE_TRUNC('month', event_timestamp)::DATE AS activity_month
    FROM touchpoints
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM customer_cohorts
    GROUP BY cohort_month
),

active_cohorts AS (
    SELECT
        c.cohort_month,
        a.activity_month,
        COUNT(DISTINCT a.customer_id) AS active_customers
    FROM customer_cohorts c
    JOIN monthly_activity a
        ON a.customer_id = c.customer_id
       AND a.activity_month >= c.cohort_month
    GROUP BY c.cohort_month, a.activity_month
)

SELECT
    a.cohort_month,
    a.activity_month,
    s.cohort_size,
    a.active_customers,

    ROUND(
        a.active_customers::NUMERIC / s.cohort_size,
        4
    ) AS retention_rate,

    (
        EXTRACT(YEAR FROM AGE(
            a.activity_month,
            a.cohort_month
        )) * 12
        +
        EXTRACT(MONTH FROM AGE(
            a.activity_month,
            a.cohort_month
        ))
    )::INTEGER AS cohort_age_months

FROM active_cohorts a
JOIN cohort_sizes s USING (cohort_month);

-- ============================================================
-- 19. CAMPAIGN PERFORMANCE
-- ============================================================

CREATE VIEW campaign_performance AS
SELECT
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    c.channel,
    c.campaign_cost,

    COUNT(t.event_id) AS touchpoints,

    COUNT(DISTINCT t.customer_id) AS unique_customers,

    COUNT(*) FILTER (
        WHERE t.event_type = 'purchase'
    ) AS purchases,

    COALESCE(
        SUM(t.monetary_value) FILTER (
            WHERE t.event_type = 'purchase'
        ),
        0
    ) AS revenue,

    CASE
        WHEN c.campaign_cost > 0
        THEN ROUND(
            COALESCE(
                SUM(t.monetary_value) FILTER (
                    WHERE t.event_type = 'purchase'
                ),
                0
            ) / c.campaign_cost,
            4
        )
        ELSE NULL
    END AS revenue_to_cost_ratio

FROM campaigns c

LEFT JOIN touchpoints t
    ON t.campaign_id = c.campaign_id

GROUP BY
    c.campaign_id,
    c.campaign_code,
    c.campaign_name,
    c.channel,
    c.campaign_cost;

-- ============================================================
-- 20. SAMPLE DATA
-- ============================================================

INSERT INTO customers (
    external_reference,
    consent,
    region,
    registered_at
)
VALUES
    ('C001', 'granted', 'IN', '2026-10-01 09:00:00+00'),
    ('C002', 'granted', 'IN', '2026-10-02 09:00:00+00'),
    ('C003', 'granted', 'IN', '2026-10-03 09:00:00+00'),
    ('C004', 'granted', 'IN', '2026-10-04 09:00:00+00'),
    ('C005', 'denied', 'IN', '2026-10-05 09:00:00+00');

INSERT INTO customer_identities (
    customer_id,
    identity_type,
    identity_value
)
SELECT customer_id, 'web_cookie', 'COOKIE-' || external_reference
FROM customers
WHERE external_reference IN ('C001', 'C002', 'C003', 'C004');

INSERT INTO campaigns (
    campaign_code,
    campaign_name,
    channel,
    campaign_cost,
    starts_at,
    ends_at
)
VALUES
    (
        'AUTUMN-SEARCH',
        'Autumn Search Campaign',
        'paid_search',
        5000,
        '2026-10-01 00:00:00+00',
        '2026-10-31 23:59:59+00'
    ),
    (
        'AUTUMN-SOCIAL',
        'Autumn Social Campaign',
        'social',
        2500,
        '2026-10-01 00:00:00+00',
        '2026-10-31 23:59:59+00'
    ),
    (
        'AUTUMN-DISPLAY',
        'Autumn Display Campaign',
        'display',
        3000,
        '2026-10-01 00:00:00+00',
        '2026-10-31 23:59:59+00'
    );

INSERT INTO sessions (
    customer_id,
    session_reference,
    started_at,
    last_activity_at,
    entry_channel,
    device_type
)
SELECT
    customer_id,
    'SESSION-' || external_reference,
    registered_at + INTERVAL '1 day',
    registered_at + INTERVAL '1 day',
    CASE external_reference
        WHEN 'C001' THEN 'social'::acquisition_channel
        WHEN 'C002' THEN 'paid_search'::acquisition_channel
        WHEN 'C003' THEN 'direct'::acquisition_channel
        ELSE 'display'::acquisition_channel
    END,
    'desktop'
FROM customers
WHERE consent = 'granted';

-- ============================================================
-- 21. TOUCHPOINT INGESTION
-- ============================================================

INSERT INTO touchpoints (
    customer_id,
    session_id,
    event_type,
    channel,
    campaign_id,
    event_timestamp,
    page_path,
    monetary_value,
    properties
)
SELECT
    s.customer_id,
    s.session_id,
    v.event_type::event_type,
    v.channel::acquisition_channel,
    v.campaign_id,
    s.started_at + v.minute_offset * INTERVAL '1 minute',
    v.page_path,
    v.monetary_value,
    '{"device_type":"desktop","browser":"Chrome"}'::JSONB

FROM sessions s

JOIN customers c USING (customer_id)

JOIN LATERAL (
    SELECT
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    FROM (
        VALUES
        ('ad_click', 'social',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-SOCIAL'),
            0, '/landing', 0::NUMERIC),

        ('page_view', 'organic_search',
            NULL::BIGINT, 2, '/home', 0::NUMERIC),

        ('product_view', 'organic_search',
            NULL::BIGINT, 5, '/product/101', 0::NUMERIC),

        ('add_to_cart', 'organic_search',
            NULL::BIGINT, 10, '/cart', 0::NUMERIC),

        ('checkout', 'organic_search',
            NULL::BIGINT, 15, '/checkout', 0::NUMERIC),

        ('purchase', 'organic_search',
            NULL::BIGINT, 20, '/success', 1499::NUMERIC)
    ) AS journey (
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    )
    WHERE c.external_reference = 'C001'

    UNION ALL

    SELECT
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    FROM (
        VALUES
        ('ad_click', 'paid_search',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-SEARCH'),
            0, '/landing', 0::NUMERIC),

        ('page_view', 'paid_search',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-SEARCH'),
            3, '/home', 0::NUMERIC),

        ('product_view', 'paid_search',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-SEARCH'),
            7, '/product/102', 0::NUMERIC),

        ('add_to_cart', 'paid_search',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-SEARCH'),
            12, '/cart', 0::NUMERIC)
    ) AS journey (
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    )
    WHERE c.external_reference = 'C002'

    UNION ALL

    SELECT
        event_type,
        channel,
        NULL::BIGINT,
        minute_offset,
        page_path,
        monetary_value
    FROM (
        VALUES
        ('page_view', 'direct', 0, '/home', 0::NUMERIC),
        ('product_view', 'direct', 4, '/product/103', 0::NUMERIC),
        ('checkout', 'direct', 8, '/checkout', 0::NUMERIC),
        ('purchase', 'direct', 12, '/success', 1499::NUMERIC)
    ) AS journey (
        event_type,
        channel,
        minute_offset,
        page_path,
        monetary_value
    )
    WHERE c.external_reference = 'C003'

    UNION ALL

    SELECT
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    FROM (
        VALUES
        ('ad_impression', 'display',
            (SELECT campaign_id FROM campaigns
             WHERE campaign_code = 'AUTUMN-DISPLAY'),
            0, '/campaign', 0::NUMERIC),

        ('page_view', 'email',
            NULL::BIGINT, 3, '/home', 0::NUMERIC),

        ('product_view', 'email',
            NULL::BIGINT, 7, '/product/104', 0::NUMERIC)
    ) AS journey (
        event_type,
        channel,
        campaign_id,
        minute_offset,
        page_path,
        monetary_value
    )
    WHERE c.external_reference = 'C004'
) AS v ON TRUE;

-- ============================================================
-- 22. DATA RETRIEVAL
-- ============================================================

-- Customer journey in chronological order.
SELECT
    c.external_reference,
    t.event_type,
    t.channel,
    t.event_timestamp,
    t.page_path,
    t.monetary_value
FROM touchpoints t
JOIN customers c USING (customer_id)
ORDER BY c.external_reference, t.event_timestamp;

-- Customer identity lookup.
SELECT
    c.external_reference,
    i.identity_type,
    i.identity_value
FROM customer_identities i
JOIN customers c USING (customer_id)
ORDER BY c.customer_id;

-- ============================================================
-- 23. BEHAVIORAL AGGREGATION
-- ============================================================

SELECT *
FROM channel_revenue_report
ORDER BY direct_event_revenue DESC;

SELECT *
FROM customer_behavior_profiles
ORDER BY revenue DESC;

SELECT *
FROM session_analytics
ORDER BY started_at;

-- ============================================================
-- 24. FUNNEL EVALUATION
-- ============================================================

SELECT *
FROM get_funnel_metrics();

SELECT
    customer_id,
    awareness_time,
    product_time,
    cart_time,
    checkout_time,
    purchase_time
FROM customer_funnel
ORDER BY customer_id;

-- ============================================================
-- 25. COHORT REPORTING
-- ============================================================

SELECT
    cohort_month,
    activity_month,
    cohort_age_months,
    cohort_size,
    active_customers,
    retention_rate
FROM monthly_cohort_retention
ORDER BY cohort_month, activity_month;

-- ============================================================
-- 26. CAMPAIGN PERFORMANCE
-- ============================================================

SELECT *
FROM campaign_performance
ORDER BY revenue DESC;

-- ============================================================
-- 27. ATTRIBUTION EVALUATION
-- ============================================================

-- Retrieve the attribution distribution for the first customer.
SELECT
    p.external_reference,
    t.event_id,
    t.event_timestamp,
    t.monetary_value,
    attribution.channel,
    attribution.attributed_weight,

    ROUND(
        t.monetary_value * attribution.attributed_weight,
        2
    ) AS allocated_revenue

FROM touchpoints t

JOIN customers p USING (customer_id)

CROSS JOIN LATERAL calculate_touchpoint_attribution(
    t.customer_id,
    t.event_id,
    'linear'
) attribution

WHERE t.event_type = 'purchase'

ORDER BY t.event_timestamp, attribution.channel;

-- ============================================================
-- 28. ELIGIBILITY AND DATA QUALITY CHECKS
-- ============================================================

-- Identify sessions with unusual inactivity.
SELECT
    session_id,
    customer_id,
    last_activity_at - started_at AS session_duration
FROM sessions
WHERE last_activity_at - started_at > INTERVAL '24 hours';

-- Identify customers with no purchase.
SELECT
    c.customer_id,
    c.external_reference,
    COUNT(t.event_id) AS touchpoint_count
FROM customers c
LEFT JOIN touchpoints t USING (customer_id)
GROUP BY c.customer_id, c.external_reference
HAVING COUNT(t.event_id) FILTER (
    WHERE t.event_type = 'purchase'
) = 0;

-- Detect customers with cart abandonment.
SELECT *
FROM customer_behavior_profiles
WHERE customer_segment = 'cart_abandoner';

-- ============================================================
-- 29. CUSTOMER ERASURE PROCEDURE
-- ============================================================

CREATE PROCEDURE erase_customer_analytics(
    p_customer_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM customers
        WHERE customer_id = p_customer_id
    ) THEN
        RAISE EXCEPTION 'Customer does not exist';
    END IF;

    -- Foreign-key cascades remove identities, sessions,
    -- touchpoints and journey transitions.
    DELETE FROM customers
    WHERE customer_id = p_customer_id;
END;
$$;

-- ============================================================
-- 30. EXAMPLE TRANSACTIONAL WORKFLOW
-- ============================================================

-- Demonstrate an isolated transaction and rollback.
-- No production sample data is changed.

SAVEPOINT analytics_validation;

DO $$
DECLARE
    valid_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO valid_count
    FROM touchpoints;

    IF valid_count = 0 THEN
        RAISE EXCEPTION 'No events available for analytics';
    END IF;

    RAISE NOTICE 'Validated % touchpoints', valid_count;
END;
$$;

ROLLBACK TO SAVEPOINT analytics_validation;

COMMIT;

-- ============================================================
-- 31. FINAL REPORTING QUERIES
-- ============================================================

SELECT
    COUNT(*) AS total_events,
    COUNT(DISTINCT customer_id) AS unique_customers,
    COUNT(*) FILTER (
        WHERE event_type = 'purchase'
    ) AS purchase_count,
    COALESCE(
        SUM(monetary_value) FILTER (
            WHERE event_type = 'purchase'
        ),
        0
    ) AS total_revenue
FROM touchpoints;

SELECT
    customer_segment,
    COUNT(*) AS customers,
    SUM(revenue) AS segment_revenue,
    AVG(event_count) AS average_events
FROM customer_behavior_profiles
GROUP BY customer_segment
ORDER BY segment_revenue DESC;

SELECT
    channel,
    SUM(direct_event_revenue) AS revenue,
    SUM(purchase_events) AS purchases,
    SUM(unique_customers) AS channel_customer_counts
FROM channel_revenue_report
GROUP BY channel
ORDER BY revenue DESC;
