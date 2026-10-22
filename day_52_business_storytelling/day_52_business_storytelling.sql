DROP SCHEMA IF EXISTS business_storytelling CASCADE;
CREATE SCHEMA business_storytelling;

SET search_path TO business_storytelling;

-- Analytical observations are separated from the narrative layer.
-- This allows the same evidence to support different business stories.

CREATE TYPE metric_direction AS ENUM (
    'improving',
    'declining',
    'stable'
);

CREATE TYPE insight_priority AS ENUM (
    'critical',
    'high',
    'medium',
    'low'
);

CREATE TABLE business_units (
    business_unit_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);

CREATE TABLE metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    business_unit_id BIGINT NOT NULL
        REFERENCES business_units(business_unit_id),
    name TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT '',
    current_value NUMERIC(18,4) NOT NULL,
    previous_value NUMERIC(18,4) NOT NULL,
    target_value NUMERIC(18,4) NOT NULL,
    observed_at DATE NOT NULL,
    CONSTRAINT metrics_name_not_blank
        CHECK (btrim(name) <> ''),
    CONSTRAINT metrics_finite_business_values
        CHECK (
            current_value IS NOT NULL
            AND previous_value IS NOT NULL
            AND target_value IS NOT NULL
        ),
    CONSTRAINT metrics_unique_observation
        UNIQUE (business_unit_id, name, observed_at)
);

CREATE INDEX idx_metrics_unit_date
    ON metrics (business_unit_id, observed_at DESC);

CREATE TABLE insight_stories (
    story_id BIGSERIAL PRIMARY KEY,
    business_unit_id BIGINT NOT NULL
        REFERENCES business_units(business_unit_id),
    title TEXT NOT NULL,
    audience TEXT NOT NULL,
    decision TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT story_title_not_blank
        CHECK (btrim(title) <> ''),
    CONSTRAINT story_audience_not_blank
        CHECK (btrim(audience) <> ''),
    CONSTRAINT story_decision_not_blank
        CHECK (btrim(decision) <> '')
);

CREATE TABLE story_insights (
    story_insight_id BIGSERIAL PRIMARY KEY,
    story_id BIGINT NOT NULL
        REFERENCES insight_stories(story_id)
        ON DELETE CASCADE,
    metric_id BIGINT NOT NULL
        REFERENCES metrics(metric_id),
    priority insight_priority NOT NULL,
    observation TEXT NOT NULL,
    implication TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    CONSTRAINT story_insight_text_valid
        CHECK (
            btrim(observation) <> ''
            AND btrim(implication) <> ''
            AND btrim(recommended_action) <> ''
        ),
    UNIQUE (story_id, metric_id)
);

CREATE TABLE action_tracking (
    action_id BIGSERIAL PRIMARY KEY,
    story_insight_id BIGINT NOT NULL
        REFERENCES story_insights(story_insight_id)
        ON DELETE CASCADE,
    owner TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    due_date DATE,
    CONSTRAINT action_owner_not_blank
        CHECK (btrim(owner) <> ''),
    CONSTRAINT action_status_valid
        CHECK (status IN ('open', 'in_progress', 'completed', 'cancelled'))
);

CREATE OR REPLACE FUNCTION metric_change_percent(
    p_current NUMERIC,
    p_previous NUMERIC
)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_previous = 0 AND p_current = 0 THEN 0::NUMERIC
        WHEN p_previous = 0 THEN NULL
        ELSE ROUND(((p_current - p_previous) / p_previous) * 100, 2)
    END;
$$;

CREATE OR REPLACE FUNCTION metric_direction_for(
    p_current NUMERIC,
    p_previous NUMERIC
)
RETURNS metric_direction
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_current > p_previous THEN 'improving'::metric_direction
        WHEN p_current < p_previous THEN 'declining'::metric_direction
        ELSE 'stable'::metric_direction
    END;
$$;

CREATE OR REPLACE FUNCTION insight_priority_for(
    p_current NUMERIC,
    p_previous NUMERIC
)
RETURNS insight_priority
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT CASE
        WHEN p_previous = 0 AND p_current > 0 THEN 'high'::insight_priority
        WHEN p_previous = 0 THEN 'low'::insight_priority
        WHEN ((p_current - p_previous) / p_previous) * 100 <= -10
            THEN 'critical'::insight_priority
        WHEN ((p_current - p_previous) / p_previous) * 100 < -3
            THEN 'high'::insight_priority
        WHEN ((p_current - p_previous) / p_previous) * 100 >= 10
            THEN 'high'::insight_priority
        WHEN ((p_current - p_previous) / p_previous) * 100 >= 3
            THEN 'medium'::insight_priority
        ELSE 'low'::insight_priority
    END;
$$;

CREATE OR REPLACE VIEW metric_story_signals AS
SELECT
    m.metric_id,
    b.name AS business_unit,
    m.name AS metric,
    m.unit,
    m.current_value,
    m.previous_value,
    m.target_value,
    ROUND(m.current_value - m.previous_value, 4) AS absolute_change,
    metric_change_percent(
        m.current_value,
        m.previous_value
    ) AS change_percent,
    ROUND(m.current_value - m.target_value, 4) AS target_gap,
    metric_direction_for(
        m.current_value,
        m.previous_value
    ) AS direction,
    insight_priority_for(
        m.current_value,
        m.previous_value
    ) AS priority,
    m.observed_at
FROM metrics m
JOIN business_units b
    ON b.business_unit_id = m.business_unit_id;

CREATE OR REPLACE FUNCTION validate_story_business_unit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM business_units b
        WHERE b.business_unit_id = NEW.business_unit_id
    ) THEN
        RAISE EXCEPTION
            'Business unit % does not exist.',
            NEW.business_unit_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_story_business_unit
BEFORE INSERT OR UPDATE ON insight_stories
FOR EACH ROW
EXECUTE FUNCTION validate_story_business_unit();

INSERT INTO business_units (name, description)
VALUES
    (
        'Digital Sales',
        'Online acquisition and conversion performance.'
    ),
    (
        'Customer Success',
        'Retention, service quality, and customer economics.'
    );

INSERT INTO metrics (
    business_unit_id,
    name,
    unit,
    current_value,
    previous_value,
    target_value,
    observed_at
)
VALUES
    (
        1,
        'Revenue',
        'M',
        12.4,
        10.8,
        12.0,
        DATE '2026-10-22'
    ),
    (
        1,
        'Conversion Rate',
        '%',
        4.7,
        5.3,
        5.0,
        DATE '2026-10-22'
    ),
    (
        2,
        'Customer Retention',
        '%',
        91.0,
        88.0,
        90.0,
        DATE '2026-10-22'
    ),
    (
        2,
        'Support Cost',
        'M',
        1.9,
        1.6,
        1.7,
        DATE '2026-10-22'
    ),
    (
        2,
        'Gross Margin',
        '%',
        37.5,
        35.8,
        36.0,
        DATE '2026-10-22'
    );

-- The CTE constructs the analytical evidence first and the narrative second.
WITH signal AS (
    SELECT *
    FROM metric_story_signals
),
narrative AS (
    SELECT
        metric_id,
        metric,
        priority,
        direction,
        change_percent,
        target_gap,
        CASE
            WHEN direction = 'declining'
                THEN metric || ' is moving in an unfavorable direction.'
            WHEN direction = 'improving'
                THEN metric || ' is improving and may contain a scalable opportunity.'
            ELSE
                metric || ' is stable and provides a weaker directional signal.'
        END AS observation,
        CASE
            WHEN priority = 'critical'
                THEN 'The movement may create material business risk.'
            WHEN priority = 'high'
                THEN 'The movement deserves targeted management attention.'
            WHEN priority = 'medium'
                THEN 'The movement should be monitored against the target.'
            ELSE
                'The movement does not currently require primary attention.'
        END AS implication
    FROM signal
)
SELECT
    metric,
    priority,
    direction,
    change_percent,
    target_gap,
    observation,
    implication
FROM narrative
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    ABS(change_percent) DESC;

-- A realistic story records evidence-backed actions rather than only observations.
BEGIN;

INSERT INTO insight_stories (
    business_unit_id,
    title,
    audience,
    decision
)
VALUES (
    1,
    'Digital Sales Performance Story',
    'Executive Leadership',
    'Investigate conversion decline while scaling profitable revenue growth.'
);

WITH selected_metrics AS (
    SELECT
        metric_id,
        name,
        current_value,
        previous_value,
        target_value
    FROM metrics
    WHERE business_unit_id = 1
      AND observed_at = DATE '2026-10-22'
),
story AS (
    SELECT story_id
    FROM insight_stories
    WHERE title = 'Digital Sales Performance Story'
),
generated AS (
    SELECT
        s.story_id,
        m.metric_id,
        insight_priority_for(
            m.current_value,
            m.previous_value
        ) AS priority,
        m.name || ' changed from '
            || m.previous_value || ' to '
            || m.current_value || '.' AS observation,
        CASE
            WHEN m.current_value < m.previous_value
                THEN 'The decline requires investigation of its principal drivers.'
            ELSE
                'The improvement should be tested for repeatability and scale.'
        END AS implication,
        CASE
            WHEN m.current_value < m.previous_value
                THEN 'Segment the metric and identify the largest operational driver.'
            ELSE
                'Identify the behavior producing the improvement and evaluate scale.'
        END AS recommended_action
    FROM selected_metrics m
    CROSS JOIN story s
)
INSERT INTO story_insights (
    story_id,
    metric_id,
    priority,
    observation,
    implication,
    recommended_action
)
SELECT
    story_id,
    metric_id,
    priority,
    observation,
    implication,
    recommended_action
FROM generated;

INSERT INTO action_tracking (
    story_insight_id,
    owner,
    status,
    due_date
)
SELECT
    story_insight_id,
    CASE
        WHEN priority IN ('critical', 'high') THEN 'Commercial Analytics'
        ELSE 'Business Intelligence'
    END,
    'open',
    DATE '2026-10-29'
FROM story_insights
WHERE story_id = (
    SELECT story_id
    FROM insight_stories
    WHERE title = 'Digital Sales Performance Story'
);

COMMIT;

-- Executive reporting query: evidence, interpretation, and action stay connected.
SELECT
    s.title,
    m.name AS metric,
    si.priority,
    si.observation,
    si.implication,
    si.recommended_action,
    a.owner,
    a.status,
    a.due_date
FROM insight_stories s
JOIN story_insights si
    ON si.story_id = s.story_id
JOIN metrics m
    ON m.metric_id = si.metric_id
LEFT JOIN action_tracking a
    ON a.story_insight_id = si.story_insight_id
ORDER BY
    CASE si.priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    m.name;

-- Failure case: this query identifies metrics that are below target
-- and therefore should not be presented as uncomplicated success stories.
SELECT
    business_unit,
    metric,
    current_value,
    target_value,
    target_gap,
    priority
FROM metric_story_signals
WHERE current_value < target_value
ORDER BY target_gap ASC;

-- Portfolio-level aggregation converts individual measurements into
-- a management-level signal without hiding the underlying evidence.
WITH classified AS (
    SELECT
        business_unit,
        direction,
        COUNT(*) AS metric_count
    FROM metric_story_signals
    GROUP BY business_unit, direction
)
SELECT
    business_unit,
    SUM(metric_count) AS total_metrics,
    SUM(metric_count) FILTER (
        WHERE direction = 'improving'
    ) AS improving_metrics,
    SUM(metric_count) FILTER (
        WHERE direction = 'declining'
    ) AS declining_metrics,
    SUM(metric_count) FILTER (
        WHERE direction = 'stable'
    ) AS stable_metrics
FROM classified
GROUP BY business_unit
ORDER BY business_unit;
