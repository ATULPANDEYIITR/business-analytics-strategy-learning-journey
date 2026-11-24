/*
    CONVERSION ANALYTICS AND FUNNEL OPTIMIZATION
    PostgreSQL 15+

    Relational workflow:
    Event collection
        -> Identity and session attribution
        -> Funnel reconstruction
        -> Conversion measurement
        -> Channel and campaign reporting
        -> Cohort analysis
        -> A/B experiment evaluation
        -> Optimization decisions

    The script is self-contained and creates a dedicated schema.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS conversion_analytics;

SET search_path TO conversion_analytics, public;


-- =========================================================
-- 1. ENUMERATED DOMAIN TYPES
-- =========================================================

CREATE TYPE event_type AS ENUM (
    'visit',
    'product_view',
    'add_to_cart',
    'checkout',
    'purchase'
);

CREATE TYPE experiment_variant AS ENUM (
    'control',
    'treatment'
);

CREATE TYPE optimization_priority AS ENUM (
    'low',
    'medium',
    'high'
);


-- =========================================================
-- 2. CUSTOMER AND ACQUISITION TABLES
-- =========================================================

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_user_key VARCHAR(128) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT customer_key_nonempty
        CHECK (length(trim(external_user_key)) > 0)
);


CREATE TABLE acquisition_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name VARCHAR(80) NOT NULL UNIQUE,
    channel_category VARCHAR(50) NOT NULL,

    CONSTRAINT channel_name_nonempty
        CHECK (length(trim(channel_name)) > 0)
);


CREATE TABLE campaigns (
    campaign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_name VARCHAR(120) NOT NULL,
    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),
    start_date DATE,
    end_date DATE,
    budget NUMERIC(14, 2) NOT NULL DEFAULT 0,

    UNIQUE (campaign_name, channel_id),

    CHECK (budget >= 0),

    CHECK (
        end_date IS NULL OR
        start_date IS NULL OR
        end_date >= start_date
    )
);


-- =========================================================
-- 3. EXPERIMENTS
-- =========================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name VARCHAR(150) NOT NULL UNIQUE,
    hypothesis TEXT NOT NULL,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ,
    minimum_sample_size INTEGER NOT NULL DEFAULT 1000,
    significance_threshold NUMERIC(5, 4) NOT NULL DEFAULT 0.05,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (minimum_sample_size > 0),

    CHECK (
        significance_threshold > 0 AND
        significance_threshold < 1
    ),

    CHECK (end_at IS NULL OR end_at > start_at)
);


-- =========================================================
-- 4. SESSION MANAGEMENT
-- =========================================================

CREATE TABLE sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    channel_id BIGINT NOT NULL
        REFERENCES acquisition_channels(channel_id),
    campaign_id BIGINT
        REFERENCES campaigns(campaign_id),
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    landing_page TEXT NOT NULL,

    CHECK (ended_at IS NULL OR ended_at >= started_at)
);

CREATE INDEX idx_sessions_customer_time
    ON sessions(customer_id, started_at DESC);

CREATE INDEX idx_sessions_channel_time
    ON sessions(channel_id, started_at DESC);

CREATE INDEX idx_sessions_campaign
    ON sessions(campaign_id)
    WHERE campaign_id IS NOT NULL;


-- =========================================================
-- 5. EXPERIMENT ASSIGNMENTS
-- =========================================================

CREATE TABLE experiment_assignments (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),
    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),
    variant experiment_variant NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (experiment_id, customer_id)
);


-- =========================================================
-- 6. RAW EVENT COLLECTION
-- =========================================================

CREATE TABLE events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_event_id VARCHAR(150) NOT NULL UNIQUE,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    session_id BIGINT NOT NULL
        REFERENCES sessions(session_id),

    event_name event_type NOT NULL,

    occurred_at TIMESTAMPTZ NOT NULL,

    revenue NUMERIC(14, 2) NOT NULL DEFAULT 0,

    event_properties JSONB NOT NULL DEFAULT '{}'::JSONB,

    experiment_id BIGINT,

    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT event_external_id_nonempty
        CHECK (length(trim(external_event_id)) > 0),

    CONSTRAINT event_revenue_nonnegative
        CHECK (revenue >= 0),

    CONSTRAINT event_revenue_purchase_only
        CHECK (
            event_name = 'purchase' OR revenue = 0
        ),

    CONSTRAINT event_properties_object
        CHECK (
            jsonb_typeof(event_properties) = 'object'
        ),

    CONSTRAINT event_experiment_fk
        FOREIGN KEY (experiment_id)
        REFERENCES experiments(experiment_id)
);


CREATE INDEX idx_events_customer_time
    ON events(customer_id, occurred_at);

CREATE INDEX idx_events_session_time
    ON events(session_id, occurred_at);

CREATE INDEX idx_events_type_time
    ON events(event_name, occurred_at);

CREATE INDEX idx_events_purchase
    ON events(occurred_at DESC, customer_id)
    WHERE event_name = 'purchase';

CREATE INDEX idx_events_properties
    ON events USING GIN(event_properties);


-- =========================================================
-- 7. ANALYTICS CONFIGURATION AND OPTIMIZATION RECORDS
-- =========================================================

CREATE TABLE funnel_definitions (
    funnel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    funnel_name VARCHAR(120) NOT NULL UNIQUE,
    attribution_window INTERVAL NOT NULL DEFAULT INTERVAL '7 days',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (attribution_window > INTERVAL '0 seconds')
);


CREATE TABLE funnel_stages (
    funnel_id BIGINT NOT NULL
        REFERENCES funnel_definitions(funnel_id)
        ON DELETE CASCADE,

    stage_order INTEGER NOT NULL,
    event_name event_type NOT NULL,
    stage_label VARCHAR(100) NOT NULL,

    PRIMARY KEY (funnel_id, stage_order),

    UNIQUE (funnel_id, event_name),

    CHECK (stage_order > 0)
);


CREATE TABLE optimization_actions (
    action_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    funnel_id BIGINT
        REFERENCES funnel_definitions(funnel_id),

    stage_name VARCHAR(100) NOT NULL,

    priority optimization_priority NOT NULL,

    observation TEXT NOT NULL,

    proposed_change TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    validated BOOLEAN NOT NULL DEFAULT FALSE
);


-- =========================================================
-- 8. DATA INTEGRITY TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION validate_event_session()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    session_customer BIGINT;
    session_start TIMESTAMPTZ;
    session_end TIMESTAMPTZ;
BEGIN
    SELECT customer_id, started_at, ended_at
    INTO session_customer, session_start, session_end
    FROM sessions
    WHERE session_id = NEW.session_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Session % does not exist', NEW.session_id;
    END IF;

    IF session_customer <> NEW.customer_id THEN
        RAISE EXCEPTION
            'Event customer does not match session customer';
    END IF;

    IF NEW.occurred_at < session_start THEN
        RAISE EXCEPTION
            'Event cannot occur before session start';
    END IF;

    IF session_end IS NOT NULL AND NEW.occurred_at > session_end THEN
        RAISE EXCEPTION
            'Event cannot occur after session end';
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_validate_event_session
BEFORE INSERT OR UPDATE ON events
FOR EACH ROW
EXECUTE FUNCTION validate_event_session();


-- =========================================================
-- 9. FUNNEL CONFIGURATION
-- =========================================================

INSERT INTO funnel_definitions (
    funnel_name,
    attribution_window
)
VALUES (
    'Ecommerce Purchase Funnel',
    INTERVAL '7 days'
);


INSERT INTO funnel_stages (
    funnel_id,
    stage_order,
    event_name,
    stage_label
)
SELECT
    funnel_id,
    stage_order,
    event_name,
    stage_label
FROM funnel_definitions
CROSS JOIN (
    VALUES
        (1, 'visit'::event_type, 'Website Visit'),
        (2, 'product_view'::event_type, 'Product View'),
        (3, 'add_to_cart'::event_type, 'Add to Cart'),
        (4, 'checkout'::event_type, 'Checkout'),
        (5, 'purchase'::event_type, 'Purchase')
) AS stage_data(stage_order, event_name, stage_label)
WHERE funnel_name = 'Ecommerce Purchase Funnel';


-- =========================================================
-- 10. ACQUISITION SAMPLE DATA
-- =========================================================

INSERT INTO acquisition_channels (
    channel_name,
    channel_category
)
VALUES
    ('organic', 'search'),
    ('paid', 'advertising'),
    ('social', 'social_media'),
    ('referral', 'partnership');


INSERT INTO campaigns (
    campaign_name,
    channel_id,
    start_date,
    end_date,
    budget
)
SELECT
    campaign_name,
    channel_id,
    DATE '2026-11-01',
    DATE '2026-11-30',
    budget
FROM (
    VALUES
        ('seo', 'organic', 0::NUMERIC),
        ('search_ads', 'paid', 50000::NUMERIC),
        ('social_ads', 'social', 30000::NUMERIC),
        ('partner', 'referral', 10000::NUMERIC)
) AS source(campaign_name, channel_name, budget)
JOIN acquisition_channels USING (channel_name);


INSERT INTO experiments (
    experiment_name,
    hypothesis,
    start_at,
    end_at,
    minimum_sample_size
)
VALUES (
    'Checkout Simplification',
    'Reducing checkout form friction increases purchase conversion.',
    TIMESTAMPTZ '2026-11-01 00:00:00+00',
    TIMESTAMPTZ '2026-12-01 00:00:00+00',
    1000
);


-- =========================================================
-- 11. CUSTOMER AND SESSION SAMPLE DATA
-- =========================================================

INSERT INTO customers (external_user_key)
SELECT 'user-' || number
FROM generate_series(1, 10) AS number;


INSERT INTO sessions (
    customer_id,
    channel_id,
    campaign_id,
    started_at,
    ended_at,
    landing_page
)
SELECT
    customer.customer_id,
    channel.channel_id,
    campaign.campaign_id,
    TIMESTAMPTZ '2026-11-01 10:00:00+00'
        + (customer.customer_id - 1) * INTERVAL '20 minutes',
    TIMESTAMPTZ '2026-11-01 12:00:00+00'
        + (customer.customer_id - 1) * INTERVAL '20 minutes',
    '/landing/' || customer.customer_id
FROM customers customer
JOIN (
    VALUES
        (1, 'organic', 'seo'),
        (2, 'paid', 'search_ads'),
        (3, 'organic', 'seo'),
        (4, 'social', 'social_ads'),
        (5, 'paid', 'search_ads'),
        (6, 'social', 'social_ads'),
        (7, 'organic', 'seo'),
        (8, 'paid', 'search_ads'),
        (9, 'referral', 'partner'),
        (10, 'organic', 'seo')
) AS assignment(customer_number, channel_name, campaign_name)
    ON assignment.customer_number =
       customer.customer_id
JOIN acquisition_channels channel
    ON channel.channel_name = assignment.channel_name
JOIN campaigns campaign
    ON campaign.campaign_name = assignment.campaign_name
   AND campaign.channel_id = channel.channel_id;


-- =========================================================
-- 12. EXPERIMENT ASSIGNMENTS
-- =========================================================

INSERT INTO experiment_assignments (
    experiment_id,
    customer_id,
    variant,
    assigned_at
)
SELECT
    experiment.experiment_id,
    customer.customer_id,
    CASE
        WHEN customer.customer_id % 2 = 0
            THEN 'treatment'::experiment_variant
        ELSE 'control'::experiment_variant
    END,
    TIMESTAMPTZ '2026-11-01 09:00:00+00'
FROM experiments experiment
CROSS JOIN customers customer
WHERE experiment.experiment_name = 'Checkout Simplification';


-- =========================================================
-- 13. REALISTIC EVENT DATA
-- =========================================================

WITH journey_data AS (
    SELECT *
    FROM (
        VALUES
            (1, ARRAY['visit','product_view','add_to_cart','checkout','purchase']::event_type[], 2500::NUMERIC),
            (2, ARRAY['visit','product_view','add_to_cart','checkout']::event_type[], 0::NUMERIC),
            (3, ARRAY['visit','product_view','add_to_cart','purchase']::event_type[], 1800::NUMERIC),
            (4, ARRAY['visit','product_view']::event_type[], 0::NUMERIC),
            (5, ARRAY['visit','product_view','add_to_cart','checkout','purchase']::event_type[], 3200::NUMERIC),
            (6, ARRAY['visit','product_view']::event_type[], 0::NUMERIC),
            (7, ARRAY['visit','product_view','add_to_cart','checkout','purchase']::event_type[], 1500::NUMERIC),
            (8, ARRAY['visit','product_view','add_to_cart']::event_type[], 0::NUMERIC),
            (9, ARRAY['visit']::event_type[], 0::NUMERIC),
            (10, ARRAY['visit','product_view','add_to_cart','checkout','purchase']::event_type[], 4100::NUMERIC)
    ) AS data(customer_number, stages, total_revenue)
),
expanded_events AS (
    SELECT
        customer.customer_id,
        session.session_id,
        journey.stages[stage_number] AS event_name,
        TIMESTAMPTZ '2026-11-01 10:00:00+00'
            + (journey.customer_number - 1) * INTERVAL '20 minutes'
            + (stage_number - 1) * INTERVAL '5 minutes'
            AS occurred_at,
        journey.total_revenue,
        stage_number
    FROM journey_data journey
    JOIN customers customer
        ON customer.customer_id = journey.customer_number
    JOIN sessions session
        ON session.customer_id = customer.customer_id
    CROSS JOIN LATERAL generate_subscripts(
        journey.stages,
        1
    ) AS stage_number
)
INSERT INTO events (
    external_event_id,
    customer_id,
    session_id,
    event_name,
    occurred_at,
    revenue,
    event_properties,
    experiment_id
)
SELECT
    'evt-' || expanded.customer_id || '-' || expanded.stage_number,
    expanded.customer_id,
    expanded.session_id,
    expanded.event_name,
    expanded.occurred_at,
    CASE
        WHEN expanded.event_name = 'purchase'
            THEN expanded.total_revenue
        ELSE 0
    END,
    jsonb_build_object(
        'source', 'sample_dataset',
        'device', 'desktop',
        'stage_order', expanded.stage_number
    ),
    experiment.experiment_id
FROM expanded_events expanded
CROSS JOIN experiments experiment
WHERE experiment.experiment_name = 'Checkout Simplification';


-- =========================================================
-- 14. REUSABLE CONVERSION METRIC FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION calculate_conversion_rate(
    converted BIGINT,
    eligible BIGINT
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF converted < 0 OR eligible < 0 THEN
        RAISE EXCEPTION 'Counts cannot be negative';
    END IF;

    IF converted > eligible THEN
        RAISE EXCEPTION
            'Conversions cannot exceed eligible users';
    END IF;

    IF eligible = 0 THEN
        RETURN 0;
    END IF;

    RETURN ROUND(
        100.0 * converted / eligible,
        2
    );
END;
$$;


-- =========================================================
-- 15. FUNNEL RECONSTRUCTION VIEW
-- =========================================================

CREATE OR REPLACE VIEW user_funnel_progress AS
WITH user_stage_times AS (
    SELECT
        customer_id,
        event_name,
        MIN(occurred_at) AS first_occurrence
    FROM events
    GROUP BY customer_id, event_name
),
user_progress AS (
    SELECT
        customer_id,

        MAX(first_occurrence) FILTER (
            WHERE event_name = 'visit'
        ) AS visit_at,

        MAX(first_occurrence) FILTER (
            WHERE event_name = 'product_view'
        ) AS product_view_at,

        MAX(first_occurrence) FILTER (
            WHERE event_name = 'add_to_cart'
        ) AS add_to_cart_at,

        MAX(first_occurrence) FILTER (
            WHERE event_name = 'checkout'
        ) AS checkout_at,

        MAX(first_occurrence) FILTER (
            WHERE event_name = 'purchase'
        ) AS purchase_at

    FROM user_stage_times
    GROUP BY customer_id
)
SELECT
    customer_id,

    visit_at,
    product_view_at,
    add_to_cart_at,
    checkout_at,
    purchase_at,

    (
        visit_at IS NOT NULL
        AND product_view_at >= visit_at
    ) AS reached_product_view,

    (
        visit_at IS NOT NULL
        AND product_view_at >= visit_at
        AND add_to_cart_at >= product_view_at
    ) AS reached_add_to_cart,

    (
        visit_at IS NOT NULL
        AND product_view_at >= visit_at
        AND add_to_cart_at >= product_view_at
        AND checkout_at >= add_to_cart_at
    ) AS reached_checkout,

    (
        visit_at IS NOT NULL
        AND product_view_at >= visit_at
        AND add_to_cart_at >= product_view_at
        AND checkout_at >= add_to_cart_at
        AND purchase_at >= checkout_at
    ) AS reached_purchase

FROM user_progress;


-- =========================================================
-- 16. FUNNEL PERFORMANCE FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION get_funnel_report(
    selected_funnel BIGINT,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ
)
RETURNS TABLE (
    stage_order INTEGER,
    stage_name TEXT,
    users BIGINT,
    previous_users BIGINT,
    conversion_rate NUMERIC,
    drop_off_rate NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF start_time >= end_time THEN
        RAISE EXCEPTION 'Invalid reporting interval';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM funnel_definitions
        WHERE funnel_id = selected_funnel
    ) THEN
        RAISE EXCEPTION 'Unknown funnel ID';
    END IF;

    RETURN QUERY
    WITH stage_population AS (
        SELECT
            definition.stage_order,
            definition.event_name,
            definition.stage_label,

            COUNT(DISTINCT CASE
                WHEN definition.event_name = 'visit'
                    AND progress.visit_at IS NOT NULL
                    THEN progress.customer_id

                WHEN definition.event_name = 'product_view'
                    AND progress.reached_product_view
                    THEN progress.customer_id

                WHEN definition.event_name = 'add_to_cart'
                    AND progress.reached_add_to_cart
                    THEN progress.customer_id

                WHEN definition.event_name = 'checkout'
                    AND progress.reached_checkout
                    THEN progress.customer_id

                WHEN definition.event_name = 'purchase'
                    AND progress.reached_purchase
                    THEN progress.customer_id
            END) AS stage_users

        FROM funnel_stages definition

        LEFT JOIN user_funnel_progress progress
            ON progress.visit_at >= start_time
           AND progress.visit_at < end_time

        WHERE definition.funnel_id = selected_funnel

        GROUP BY
            definition.stage_order,
            definition.event_name,
            definition.stage_label
    ),
    previous_counts AS (
        SELECT
            stage_order,
            event_name,
            stage_label,
            stage_users,

            LAG(stage_users, 1) OVER (
                ORDER BY stage_order
            ) AS previous_stage_users

        FROM stage_population
    )
    SELECT
        stage_order,
        stage_label::TEXT,
        stage_users,

        COALESCE(
            previous_stage_users,
            stage_users
        ),

        calculate_conversion_rate(
            stage_users,
            COALESCE(previous_stage_users, stage_users)
        ),

        ROUND(
            100 - calculate_conversion_rate(
                stage_users,
                COALESCE(previous_stage_users, stage_users)
            ),
            2
        )

    FROM previous_counts
    ORDER BY stage_order;
END;
$$;


-- =========================================================
-- 17. CHANNEL ATTRIBUTION VIEW
-- =========================================================

CREATE OR REPLACE VIEW channel_conversion_report AS
WITH visitors AS (
    SELECT
        channel.channel_id,
        COUNT(DISTINCT session.customer_id) AS visitor_count
    FROM sessions session
    JOIN acquisition_channels channel
        ON channel.channel_id = session.channel_id
    GROUP BY channel.channel_id
),
purchases AS (
    SELECT
        session.channel_id,
        COUNT(DISTINCT event.customer_id) AS buyer_count,
        SUM(event.revenue) AS total_revenue
    FROM events event
    JOIN sessions session
        ON session.session_id = event.session_id
    WHERE event.event_name = 'purchase'
    GROUP BY session.channel_id
)
SELECT
    channel.channel_name,

    COALESCE(visitor.visitor_count, 0) AS visitors,

    COALESCE(purchase.buyer_count, 0) AS conversions,

    calculate_conversion_rate(
        COALESCE(purchase.buyer_count, 0),
        COALESCE(visitor.visitor_count, 0)
    ) AS conversion_rate,

    COALESCE(purchase.total_revenue, 0) AS revenue,

    CASE
        WHEN COALESCE(visitor.visitor_count, 0) = 0
            THEN 0
        ELSE ROUND(
            COALESCE(purchase.total_revenue, 0)
            / visitor.visitor_count,
            2
        )
    END AS revenue_per_visitor

FROM acquisition_channels channel

LEFT JOIN visitors visitor
    ON visitor.channel_id = channel.channel_id

LEFT JOIN purchases purchase
    ON purchase.channel_id = channel.channel_id;


-- =========================================================
-- 18. CAMPAIGN PERFORMANCE
-- =========================================================

CREATE OR REPLACE VIEW campaign_conversion_report AS
SELECT
    campaign.campaign_id,
    campaign.campaign_name,
    channel.channel_name,

    COUNT(DISTINCT session.customer_id) AS visitors,

    COUNT(DISTINCT event.customer_id) FILTER (
        WHERE event.event_name = 'purchase'
    ) AS conversions,

    calculate_conversion_rate(
        COUNT(DISTINCT event.customer_id) FILTER (
            WHERE event.event_name = 'purchase'
        ),
        COUNT(DISTINCT session.customer_id)
    ) AS conversion_rate,

    COALESCE(
        SUM(event.revenue) FILTER (
            WHERE event.event_name = 'purchase'
        ),
        0
    ) AS revenue,

    campaign.budget

FROM campaigns campaign

JOIN acquisition_channels channel
    ON channel.channel_id = campaign.channel_id

LEFT JOIN sessions session
    ON session.campaign_id = campaign.campaign_id

LEFT JOIN events event
    ON event.session_id = session.session_id

GROUP BY
    campaign.campaign_id,
    campaign.campaign_name,
    channel.channel_name,
    campaign.budget;


-- =========================================================
-- 19. COHORT CONVERSION REPORT
-- =========================================================

CREATE OR REPLACE VIEW monthly_cohort_report AS
WITH first_visits AS (
    SELECT
        customer_id,
        DATE_TRUNC(
            'month',
            MIN(occurred_at)
        )::DATE AS cohort_month
    FROM events
    WHERE event_name = 'visit'
    GROUP BY customer_id
),
buyers AS (
    SELECT DISTINCT customer_id
    FROM events
    WHERE event_name = 'purchase'
)
SELECT
    cohort.cohort_month,

    COUNT(*) AS cohort_users,

    COUNT(buyer.customer_id) AS converted_users,

    calculate_conversion_rate(
        COUNT(buyer.customer_id),
        COUNT(*)
    ) AS conversion_rate

FROM first_visits cohort

LEFT JOIN buyers buyer
    ON buyer.customer_id = cohort.customer_id

GROUP BY cohort.cohort_month;


-- =========================================================
-- 20. A/B EXPERIMENT REPORT
-- =========================================================

CREATE OR REPLACE VIEW experiment_conversion_report AS
SELECT
    experiment.experiment_id,
    experiment.experiment_name,
    assignment.variant,

    COUNT(DISTINCT assignment.customer_id) AS assigned_users,

    COUNT(DISTINCT event.customer_id) FILTER (
        WHERE event.event_name = 'purchase'
    ) AS converted_users,

    calculate_conversion_rate(
        COUNT(DISTINCT event.customer_id) FILTER (
            WHERE event.event_name = 'purchase'
        ),
        COUNT(DISTINCT assignment.customer_id)
    ) AS conversion_rate

FROM experiments experiment

JOIN experiment_assignments assignment
    ON assignment.experiment_id = experiment.experiment_id

LEFT JOIN events event
    ON event.customer_id = assignment.customer_id
   AND event.experiment_id = experiment.experiment_id

GROUP BY
    experiment.experiment_id,
    experiment.experiment_name,
    assignment.variant;


-- =========================================================
-- 21. FUNNEL BOTTLENECK REPORT
-- =========================================================

CREATE OR REPLACE FUNCTION identify_funnel_bottleneck(
    selected_funnel BIGINT,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ
)
RETURNS TABLE (
    stage_name TEXT,
    stage_users BIGINT,
    drop_off_rate NUMERIC
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        report.stage_name,
        report.users,
        report.drop_off_rate
    FROM get_funnel_report(
        selected_funnel,
        start_time,
        end_time
    ) report
    ORDER BY report.drop_off_rate DESC
    LIMIT 1;
$$;


-- =========================================================
-- 22. EXPERIMENT STATISTICAL EVALUATION
-- =========================================================

CREATE OR REPLACE FUNCTION evaluate_ab_test(
    control_conversions BIGINT,
    control_users BIGINT,
    treatment_conversions BIGINT,
    treatment_users BIGINT
)
RETURNS TABLE (
    control_rate NUMERIC,
    treatment_rate NUMERIC,
    absolute_lift NUMERIC,
    relative_lift NUMERIC,
    z_score NUMERIC,
    p_value NUMERIC,
    significant BOOLEAN
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    p1 DOUBLE PRECISION;
    p2 DOUBLE PRECISION;
    pooled DOUBLE PRECISION;
    standard_error DOUBLE PRECISION;
    z DOUBLE PRECISION;
    probability DOUBLE PRECISION;
    t DOUBLE PRECISION;
    erf_value DOUBLE PRECISION;
BEGIN
    IF
        control_users <= 0 OR
        treatment_users <= 0 OR
        control_conversions < 0 OR
        treatment_conversions < 0 OR
        control_conversions > control_users OR
        treatment_conversions > treatment_users
    THEN
        RAISE EXCEPTION 'Invalid experiment sample';
    END IF;

    p1 := control_conversions::DOUBLE PRECISION / control_users;

    p2 := treatment_conversions::DOUBLE PRECISION / treatment_users;

    pooled :=
        (control_conversions + treatment_conversions)::DOUBLE PRECISION
        / (control_users + treatment_users);

    standard_error := SQRT(
        pooled * (1 - pooled) *
        (
            1.0 / control_users +
            1.0 / treatment_users
        )
    );

    z := CASE
        WHEN standard_error = 0 THEN 0
        ELSE (p2 - p1) / standard_error
    END;

    -- Abramowitz-Stegun approximation of the error function.
    t := 1.0 / (
        1.0 + 0.3275911 * ABS(z) / SQRT(2.0)
    );

    erf_value :=
        1 - (
            (
                (
                    (
                        1.061405429 * t
                        - 1.453152027
                    ) * t
                    + 1.421413741
                ) * t
                - 0.284496736
            ) * t
            + 0.254829592
        ) * t * EXP(
            -POWER(ABS(z) / SQRT(2.0), 2)
        );

    probability := 1 - erf_value;

    RETURN QUERY
    SELECT
        ROUND((p1 * 100)::NUMERIC, 2),
        ROUND((p2 * 100)::NUMERIC, 2),

        ROUND(((p2 - p1) * 100)::NUMERIC, 2),

        CASE
            WHEN p1 = 0 THEN NULL
            ELSE ROUND(
                (((p2 - p1) / p1) * 100)::NUMERIC,
                2
            )
        END,

        ROUND(z::NUMERIC, 4),

        ROUND(probability::NUMERIC, 6),

        probability < 0.05;
END;
$$;


-- =========================================================
-- 23. OPTIMIZATION ACTION PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE record_funnel_optimization(
    selected_funnel BIGINT,
    selected_stage VARCHAR,
    selected_priority optimization_priority,
    selected_observation TEXT,
    selected_change TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM funnel_stages
        WHERE funnel_id = selected_funnel
          AND stage_label = selected_stage
    ) THEN
        RAISE EXCEPTION
            'Stage does not belong to the selected funnel';
    END IF;

    IF
        length(trim(selected_observation)) = 0 OR
        length(trim(selected_change)) = 0
    THEN
        RAISE EXCEPTION
            'Observation and proposed change are required';
    END IF;

    INSERT INTO optimization_actions (
        funnel_id,
        stage_name,
        priority,
        observation,
        proposed_change
    )
    VALUES (
        selected_funnel,
        selected_stage,
        selected_priority,
        selected_observation,
        selected_change
    );
END;
$$;


-- =========================================================
-- 24. TRANSACTIONAL EVENT INGESTION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION ingest_analytics_event(
    external_id VARCHAR,
    selected_customer BIGINT,
    selected_session BIGINT,
    selected_type event_type,
    selected_time TIMESTAMPTZ,
    selected_revenue NUMERIC DEFAULT 0,
    selected_properties JSONB DEFAULT '{}'::JSONB
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    inserted_count INTEGER;
BEGIN
    INSERT INTO events (
        external_event_id,
        customer_id,
        session_id,
        event_name,
        occurred_at,
        revenue,
        event_properties
    )
    VALUES (
        external_id,
        selected_customer,
        selected_session,
        selected_type,
        selected_time,
        selected_revenue,
        selected_properties
    )
    ON CONFLICT (external_event_id) DO NOTHING;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;

    RETURN inserted_count = 1;
END;
$$;


-- =========================================================
-- 25. REPORTING AND VALIDATION QUERIES
-- =========================================================

-- A. Overall funnel performance.
SELECT *
FROM get_funnel_report(
    (
        SELECT funnel_id
        FROM funnel_definitions
        WHERE funnel_name = 'Ecommerce Purchase Funnel'
    ),
    TIMESTAMPTZ '2026-11-01 00:00:00+00',
    TIMESTAMPTZ '2026-12-01 00:00:00+00'
);


-- B. Identify the largest drop-off stage.
SELECT *
FROM identify_funnel_bottleneck(
    (
        SELECT funnel_id
        FROM funnel_definitions
        WHERE funnel_name = 'Ecommerce Purchase Funnel'
    ),
    TIMESTAMPTZ '2026-11-01 00:00:00+00',
    TIMESTAMPTZ '2026-12-01 00:00:00+00'
);


-- C. Channel-level conversion performance.
SELECT *
FROM channel_conversion_report
ORDER BY conversion_rate DESC;


-- D. Campaign-level acquisition performance.
SELECT *
FROM campaign_conversion_report
ORDER BY conversion_rate DESC;


-- E. Monthly customer cohort conversion.
SELECT *
FROM monthly_cohort_report
ORDER BY cohort_month;


-- F. Experiment performance by variant.
SELECT *
FROM experiment_conversion_report
ORDER BY experiment_name, variant;


-- G. Statistical evaluation of a sample experiment.
SELECT *
FROM evaluate_ab_test(
    120,
    2000,
    150,
    2000
);


-- H. Total revenue and average order value.
SELECT
    COUNT(*) AS purchase_events,
    COUNT(DISTINCT customer_id) AS purchasing_customers,
    COALESCE(SUM(revenue), 0) AS total_revenue,

    ROUND(
        COALESCE(
            SUM(revenue) / NULLIF(COUNT(*), 0),
            0
        ),
        2
    ) AS average_order_value

FROM events
WHERE event_name = 'purchase';


-- I. Validate duplicate external event IDs.
SELECT
    external_event_id,
    COUNT(*) AS occurrence_count
FROM events
GROUP BY external_event_id
HAVING COUNT(*) > 1;


-- J. Inspect malformed journey sequences.
SELECT
    customer_id,
    visit_at,
    product_view_at,
    add_to_cart_at,
    checkout_at,
    purchase_at
FROM user_funnel_progress
WHERE
    (
        product_view_at IS NOT NULL
        AND (
            visit_at IS NULL OR
            product_view_at < visit_at
        )
    )
    OR
    (
        add_to_cart_at IS NOT NULL
        AND (
            product_view_at IS NULL OR
            add_to_cart_at < product_view_at
        )
    )
    OR
    (
        checkout_at IS NOT NULL
        AND (
            add_to_cart_at IS NULL OR
            checkout_at < add_to_cart_at
        )
    )
    OR
    (
        purchase_at IS NOT NULL
        AND (
            checkout_at IS NULL OR
            purchase_at < checkout_at
        )
    );


-- K. Revenue by acquisition channel.
SELECT
    channel_name,
    visitors,
    conversions,
    conversion_rate,
    revenue,
    revenue_per_visitor
FROM channel_conversion_report
ORDER BY revenue DESC;


-- L. Event volume by day and event type.
SELECT
    DATE_TRUNC('day', occurred_at)::DATE AS event_date,
    event_name,
    COUNT(*) AS event_count,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM events
GROUP BY
    DATE_TRUNC('day', occurred_at)::DATE,
    event_name
ORDER BY event_date, event_name;


-- =========================================================
-- 26. RECORD AN OPTIMIZATION ACTION
-- =========================================================

CALL record_funnel_optimization(
    (
        SELECT funnel_id
        FROM funnel_definitions
        WHERE funnel_name = 'Ecommerce Purchase Funnel'
    ),
    'Product View',
    'high',
    'A significant proportion of visitors do not progress to cart activity.',
    'Evaluate product-page clarity, pricing visibility and purchase intent.'
);


-- =========================================================
-- 27. OPTIMIZATION REPORT
-- =========================================================

SELECT
    action_id,
    stage_name,
    priority,
    observation,
    proposed_change,
    validated
FROM optimization_actions
ORDER BY
    CASE priority
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        ELSE 3
    END,
    created_at DESC;


-- =========================================================
-- 28. TRANSACTIONAL DUPLICATE INGESTION TEST
-- =========================================================

DO $$
DECLARE
    first_result BOOLEAN;
    second_result BOOLEAN;
BEGIN
    first_result := ingest_analytics_event(
        'manual-validation-event-001',
        1,
        (
            SELECT session_id
            FROM sessions
            WHERE customer_id = 1
            LIMIT 1
        ),
        'visit',
        TIMESTAMPTZ '2026-11-01 10:00:00+00',
        0,
        '{"test": true}'::JSONB
    );

    second_result := ingest_analytics_event(
        'manual-validation-event-001',
        1,
        (
            SELECT session_id
            FROM sessions
            WHERE customer_id = 1
            LIMIT 1
        ),
        'visit',
        TIMESTAMPTZ '2026-11-01 10:00:00+00',
        0,
        '{"test": true}'::JSONB
    );

    IF first_result IS NOT TRUE THEN
        RAISE EXCEPTION 'Initial ingestion failed';
    END IF;

    IF second_result IS NOT FALSE THEN
        RAISE EXCEPTION 'Duplicate event was not rejected';
    END IF;

    RAISE NOTICE 'Idempotent ingestion validation passed';
END;
$$;


-- =========================================================
-- 29. TRANSACTION COMPLETION
-- =========================================================

COMMIT;

-- Operational notes:
-- 1. Event ingestion should be idempotent.
-- 2. Reporting timestamps should use explicit time zones.
-- 3. Large event tables should be considered for time partitioning.
-- 4. Historical attribution logic should be versioned.
-- 5. Raw events should be retained separately from derived reports.
-- 6. Production ingestion should enforce authenticated event sources.
