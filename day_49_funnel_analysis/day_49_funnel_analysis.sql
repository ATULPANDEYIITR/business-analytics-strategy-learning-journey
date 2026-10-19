DROP SCHEMA IF EXISTS funnel_analysis CASCADE;
CREATE SCHEMA funnel_analysis;

SET search_path TO funnel_analysis;

-- A funnel is represented as an ordered business definition rather than
-- assuming that every customer must reach every stage.
CREATE TABLE funnels (
    funnel_id BIGSERIAL PRIMARY KEY,
    funnel_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE funnel_stages (
    stage_id BIGSERIAL PRIMARY KEY,
    funnel_id BIGINT NOT NULL REFERENCES funnels(funnel_id) ON DELETE CASCADE,
    stage_key TEXT NOT NULL,
    stage_name TEXT NOT NULL,
    stage_order INTEGER NOT NULL CHECK (stage_order > 0),
    UNIQUE (funnel_id, stage_key),
    UNIQUE (funnel_id, stage_order)
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    external_customer_key TEXT NOT NULL UNIQUE,
    segment TEXT NOT NULL CHECK (btrim(segment) <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE customer_events (
    event_id BIGSERIAL PRIMARY KEY,
    funnel_id BIGINT NOT NULL REFERENCES funnels(funnel_id) ON DELETE CASCADE,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    stage_id BIGINT NOT NULL REFERENCES funnel_stages(stage_id) ON DELETE RESTRICT,
    occurred_at TIMESTAMPTZ NOT NULL,
    revenue_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (revenue_amount >= 0),
    UNIQUE (funnel_id, customer_id, stage_id)
);

CREATE TABLE purchases (
    purchase_id BIGSERIAL PRIMARY KEY,
    funnel_id BIGINT NOT NULL REFERENCES funnels(funnel_id) ON DELETE CASCADE,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    purchase_event_id BIGINT NOT NULL UNIQUE
        REFERENCES customer_events(event_id) ON DELETE RESTRICT,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    purchased_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_customer_events_funnel_stage_time
    ON customer_events (funnel_id, stage_id, occurred_at);

CREATE INDEX idx_customer_events_customer_time
    ON customer_events (customer_id, occurred_at);

CREATE INDEX idx_customers_segment
    ON customers (segment);

INSERT INTO funnels (funnel_name, description)
VALUES (
    'Ecommerce Purchase Funnel',
    'Landing page through product discovery, cart creation, checkout, and purchase'
);

INSERT INTO funnel_stages
    (funnel_id, stage_key, stage_name, stage_order)
SELECT
    funnel_id,
    stage_key,
    stage_name,
    stage_order
FROM funnels
CROSS JOIN (
    VALUES
        ('landing', 'Visited Landing Page', 1),
        ('product', 'Viewed Product', 2),
        ('cart', 'Added to Cart', 3),
        ('checkout', 'Started Checkout', 4),
        ('purchase', 'Purchased', 5)
) AS stages(stage_key, stage_name, stage_order)
WHERE funnel_name = 'Ecommerce Purchase Funnel';

INSERT INTO customers (external_customer_key, segment)
VALUES
    ('C001', 'mobile'),
    ('C002', 'mobile'),
    ('C003', 'desktop'),
    ('C004', 'desktop'),
    ('C005', 'mobile'),
    ('C006', 'desktop'),
    ('C007', 'tablet'),
    ('C008', 'tablet'),
    ('C009', 'mobile'),
    ('C010', 'desktop');

-- The event table preserves partial journeys. A missing event is meaningful:
-- it represents a customer who stopped before that stage.
WITH funnel AS (
    SELECT funnel_id
    FROM funnels
    WHERE funnel_name = 'Ecommerce Purchase Funnel'
),
stage_map AS (
    SELECT stage_id, stage_key
    FROM funnel_stages
    WHERE funnel_id = (SELECT funnel_id FROM funnel)
)
INSERT INTO customer_events
    (funnel_id, customer_id, stage_id, occurred_at, revenue_amount)
SELECT
    f.funnel_id,
    c.customer_id,
    sm.stage_id,
    e.occurred_at,
    e.revenue_amount
FROM (
    VALUES
        ('C001', 'landing',  '2026-10-01 09:00:00+00'::timestamptz, 0),
        ('C001', 'product',  '2026-10-01 09:04:00+00'::timestamptz, 0),
        ('C001', 'cart',     '2026-10-01 09:09:00+00'::timestamptz, 0),
        ('C001', 'checkout', '2026-10-01 09:15:00+00'::timestamptz, 0),
        ('C001', 'purchase', '2026-10-01 09:23:00+00'::timestamptz, 129),

        ('C002', 'landing',  '2026-10-01 09:01:00+00'::timestamptz, 0),
        ('C002', 'product',  '2026-10-01 09:06:00+00'::timestamptz, 0),
        ('C002', 'cart',     '2026-10-01 09:12:00+00'::timestamptz, 0),
        ('C002', 'checkout', '2026-10-01 09:21:00+00'::timestamptz, 0),

        ('C003', 'landing',  '2026-10-01 09:02:00+00'::timestamptz, 0),
        ('C003', 'product',  '2026-10-01 09:05:00+00'::timestamptz, 0),
        ('C003', 'cart',     '2026-10-01 09:14:00+00'::timestamptz, 0),
        ('C003', 'checkout', '2026-10-01 09:20:00+00'::timestamptz, 0),
        ('C003', 'purchase', '2026-10-01 09:32:00+00'::timestamptz, 249),

        ('C004', 'landing',  '2026-10-01 09:03:00+00'::timestamptz, 0),
        ('C004', 'product',  '2026-10-01 09:08:00+00'::timestamptz, 0),

        ('C005', 'landing',  '2026-10-01 09:10:00+00'::timestamptz, 0),
        ('C005', 'product',  '2026-10-01 09:14:00+00'::timestamptz, 0),
        ('C005', 'cart',     '2026-10-01 09:19:00+00'::timestamptz, 0),

        ('C006', 'landing',  '2026-10-01 09:11:00+00'::timestamptz, 0),
        ('C006', 'product',  '2026-10-01 09:16:00+00'::timestamptz, 0),
        ('C006', 'cart',     '2026-10-01 09:22:00+00'::timestamptz, 0),
        ('C006', 'checkout', '2026-10-01 09:30:00+00'::timestamptz, 0),
        ('C006', 'purchase', '2026-10-01 09:41:00+00'::timestamptz, 89),

        ('C007', 'landing',  '2026-10-01 09:13:00+00'::timestamptz, 0),
        ('C007', 'product',  '2026-10-01 09:18:00+00'::timestamptz, 0),
        ('C007', 'cart',     '2026-10-01 09:26:00+00'::timestamptz, 0),
        ('C007', 'checkout', '2026-10-01 09:40:00+00'::timestamptz, 0),

        ('C008', 'landing',  '2026-10-01 09:15:00+00'::timestamptz, 0),
        ('C008', 'product',  '2026-10-01 09:21:00+00'::timestamptz, 0),

        ('C009', 'landing',  '2026-10-01 09:18:00+00'::timestamptz, 0),
        ('C009', 'product',  '2026-10-01 09:23:00+00'::timestamptz, 0),
        ('C009', 'cart',     '2026-10-01 09:31:00+00'::timestamptz, 0),
        ('C009', 'checkout', '2026-10-01 09:37:00+00'::timestamptz, 0),
        ('C009', 'purchase', '2026-10-01 09:48:00+00'::timestamptz, 159),

        ('C010', 'landing',  '2026-10-01 09:20:00+00'::timestamptz, 0),
        ('C010', 'product',  '2026-10-01 09:24:00+00'::timestamptz, 0),
        ('C010', 'cart',     '2026-10-01 09:30:00+00'::timestamptz, 0)
) AS e(customer_key, stage_key, occurred_at, revenue_amount)
JOIN customers c
    ON c.external_customer_key = e.customer_key
CROSS JOIN funnel f
JOIN stage_map sm
    ON sm.stage_key = e.stage_key;

INSERT INTO purchases
    (funnel_id, customer_id, purchase_event_id, amount, purchased_at)
SELECT
    ce.funnel_id,
    ce.customer_id,
    ce.event_id,
    ce.revenue_amount,
    ce.occurred_at
FROM customer_events ce
JOIN funnel_stages fs
    ON fs.stage_id = ce.stage_id
WHERE fs.stage_key = 'purchase'
  AND ce.revenue_amount > 0;

-- Stage-level funnel counts.
WITH stage_counts AS (
    SELECT
        fs.stage_order,
        fs.stage_name,
        COUNT(DISTINCT ce.customer_id) AS reached_users
    FROM funnel_stages fs
    LEFT JOIN customer_events ce
        ON ce.stage_id = fs.stage_id
    GROUP BY fs.stage_order, fs.stage_name
),
with_previous AS (
    SELECT
        stage_order,
        stage_name,
        reached_users,
        LAG(reached_users) OVER (
            ORDER BY stage_order
        ) AS previous_users,
        FIRST_VALUE(reached_users) OVER (
            ORDER BY stage_order
        ) AS entry_users
    FROM stage_counts
)
SELECT
    stage_name,
    reached_users,
    previous_users,
    ROUND(
        100.0 * reached_users /
        NULLIF(previous_users, 0),
        2
    ) AS conversion_from_previous_pct,
    ROUND(
        100.0 * reached_users /
        NULLIF(entry_users, 0),
        2
    ) AS conversion_from_entry_pct,
    ROUND(
        100.0 -
        100.0 * reached_users /
        NULLIF(previous_users, 0),
        2
    ) AS drop_off_pct
FROM with_previous
ORDER BY stage_order;

-- Segment conversion reveals whether aggregate funnel performance hides
-- materially different customer behavior.
WITH segment_totals AS (
    SELECT
        c.segment,
        COUNT(DISTINCT c.customer_id) AS users
    FROM customers c
    JOIN customer_events ce
        ON ce.customer_id = c.customer_id
    GROUP BY c.segment
),
segment_converters AS (
    SELECT
        c.segment,
        COUNT(DISTINCT c.customer_id) AS converters
    FROM customers c
    JOIN customer_events ce
        ON ce.customer_id = c.customer_id
    JOIN funnel_stages fs
        ON fs.stage_id = ce.stage_id
    WHERE fs.stage_key = 'purchase'
    GROUP BY c.segment
)
SELECT
    st.segment,
    st.users,
    COALESCE(sc.converters, 0) AS converters,
    ROUND(
        100.0 * COALESCE(sc.converters, 0) /
        NULLIF(st.users, 0),
        2
    ) AS conversion_rate_pct
FROM segment_totals st
LEFT JOIN segment_converters sc
    ON sc.segment = st.segment
ORDER BY conversion_rate_pct DESC;

-- Identify the largest stage loss using the stage counts already calculated.
WITH stage_counts AS (
    SELECT
        fs.stage_order,
        fs.stage_name,
        COUNT(DISTINCT ce.customer_id) AS reached_users
    FROM funnel_stages fs
    LEFT JOIN customer_events ce
        ON ce.stage_id = fs.stage_id
    GROUP BY fs.stage_order, fs.stage_name
),
losses AS (
    SELECT
        stage_name,
        reached_users,
        LAG(reached_users) OVER (ORDER BY stage_order) AS previous_users
    FROM stage_counts
)
SELECT
    stage_name,
    previous_users,
    reached_users,
    ROUND(
        100.0 * (
            1.0 -
            reached_users::numeric /
            NULLIF(previous_users, 0)
        ),
        2
    ) AS drop_off_pct
FROM losses
WHERE previous_users IS NOT NULL
ORDER BY drop_off_pct DESC
LIMIT 1;

-- Median time from landing to purchase for completed journeys.
WITH journey_times AS (
    SELECT
        ce.customer_id,
        MIN(ce.occurred_at) FILTER (
            WHERE fs.stage_key = 'landing'
        ) AS landing_at,
        MIN(ce.occurred_at) FILTER (
            WHERE fs.stage_key = 'purchase'
        ) AS purchase_at
    FROM customer_events ce
    JOIN funnel_stages fs
        ON fs.stage_id = ce.stage_id
    GROUP BY ce.customer_id
)
SELECT
    COUNT(*) AS completed_journeys,
    ROUND(
        (
            EXTRACT(
                EPOCH FROM
                percentile_cont(0.5) WITHIN GROUP (
                    ORDER BY purchase_at - landing_at
                )
            ) / 60
        )::numeric,
        2
    ) AS median_minutes_to_conversion
FROM journey_times
WHERE landing_at IS NOT NULL
  AND purchase_at IS NOT NULL;

-- Revenue analysis is limited to completed purchases rather than counting
-- abandoned-cart amounts as realized revenue.
SELECT
    COUNT(*) AS purchases,
    SUM(amount) AS total_revenue,
    ROUND(AVG(amount), 2) AS average_order_value
FROM purchases;

-- A path analysis shows where customers actually stopped instead of
-- pretending that every journey follows the complete funnel.
WITH customer_stage_paths AS (
    SELECT
        c.external_customer_key,
        c.segment,
        string_agg(
            fs.stage_key,
            ' -> '
            ORDER BY fs.stage_order
        ) AS path
    FROM customers c
    JOIN customer_events ce
        ON ce.customer_id = c.customer_id
    JOIN funnel_stages fs
        ON fs.stage_id = ce.stage_id
    GROUP BY c.external_customer_key, c.segment
)
SELECT
    path,
    COUNT(*) AS customers
FROM customer_stage_paths
GROUP BY path
ORDER BY customers DESC, path;

-- Database-level validation example:
-- This statement is intentionally commented because executing it would
-- violate the uniqueness rule for a customer's funnel stage.
--
-- INSERT INTO customer_events
--     (funnel_id, customer_id, stage_id, occurred_at)
-- VALUES
--     (1, 1, 1, '2026-10-01 09:30:00+00');

-- Transactional workflow for registering a purchase while preserving
-- referential integrity. The purchase is created only from an existing
-- purchase-stage event.
BEGIN;

INSERT INTO purchases
    (funnel_id, customer_id, purchase_event_id, amount, purchased_at)
SELECT
    ce.funnel_id,
    ce.customer_id,
    ce.event_id,
    ce.revenue_amount,
    ce.occurred_at
FROM customer_events ce
JOIN funnel_stages fs
    ON fs.stage_id = ce.stage_id
LEFT JOIN purchases p
    ON p.purchase_event_id = ce.event_id
WHERE fs.stage_key = 'purchase'
  AND p.purchase_event_id IS NULL
  AND ce.revenue_amount > 0;

COMMIT;

-- The final view provides a reusable reporting surface for dashboards.
CREATE OR REPLACE VIEW funnel_conversion_summary AS
WITH stage_counts AS (
    SELECT
        fs.funnel_id,
        fs.stage_order,
        fs.stage_name,
        COUNT(DISTINCT ce.customer_id) AS reached_users
    FROM funnel_stages fs
    LEFT JOIN customer_events ce
        ON ce.stage_id = fs.stage_id
    GROUP BY
        fs.funnel_id,
        fs.stage_order,
        fs.stage_name
)
SELECT
    funnel_id,
    stage_order,
    stage_name,
    reached_users,
    LAG(reached_users) OVER (
        PARTITION BY funnel_id
        ORDER BY stage_order
    ) AS previous_stage_users,
    ROUND(
        100.0 *
        reached_users /
        NULLIF(
            FIRST_VALUE(reached_users) OVER (
                PARTITION BY funnel_id
                ORDER BY stage_order
            ),
            0
        ),
        2
    ) AS conversion_from_entry_pct
FROM stage_counts;

SELECT *
FROM funnel_conversion_summary
ORDER BY funnel_id, stage_order;
