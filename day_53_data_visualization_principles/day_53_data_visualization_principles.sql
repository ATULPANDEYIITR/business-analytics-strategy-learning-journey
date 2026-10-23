DROP SCHEMA IF EXISTS visualization_principles CASCADE;
CREATE SCHEMA visualization_principles;
SET search_path TO visualization_principles;

-- The relational model separates analytical intent, data characteristics,
-- candidate chart structures, and evaluation results. This prevents a chart
-- recommendation from being stored as an unexplained categorical label.

CREATE TYPE analytical_intent AS ENUM (
    'comparison',
    'ranking',
    'relationship',
    'distribution',
    'composition',
    'trend',
    'matrix'
);

CREATE TYPE chart_type AS ENUM (
    'horizontal_bar',
    'dot_plot',
    'scatter_plot',
    'histogram',
    'box_plot',
    'stacked_bar',
    'pie',
    'line',
    'heatmap'
);

CREATE TYPE evaluation_state AS ENUM (
    'proposed',
    'validated',
    'rejected'
);

CREATE TABLE datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    dataset_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    observation_count INTEGER NOT NULL CHECK (observation_count > 0),
    numeric_measure_count INTEGER NOT NULL CHECK (numeric_measure_count > 0),
    category_count INTEGER NOT NULL DEFAULT 0 CHECK (category_count >= 0),
    ordered_observations BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analytical_requests (
    request_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    intent analytical_intent NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    state evaluation_state NOT NULL DEFAULT 'proposed'
);

CREATE TABLE chart_types (
    chart_id SMALLSERIAL PRIMARY KEY,
    chart chart_type NOT NULL UNIQUE,
    supports_comparison BOOLEAN NOT NULL DEFAULT FALSE,
    supports_relationship BOOLEAN NOT NULL DEFAULT FALSE,
    supports_distribution BOOLEAN NOT NULL DEFAULT FALSE,
    supports_composition BOOLEAN NOT NULL DEFAULT FALSE,
    supports_trend BOOLEAN NOT NULL DEFAULT FALSE,
    supports_matrix BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO chart_types (
    chart,
    supports_comparison,
    supports_relationship,
    supports_distribution,
    supports_composition,
    supports_trend,
    supports_matrix
)
VALUES
    ('horizontal_bar', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
    ('dot_plot', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE),
    ('scatter_plot', FALSE, TRUE, FALSE, FALSE, FALSE, FALSE),
    ('histogram', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE),
    ('box_plot', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE),
    ('stacked_bar', FALSE, FALSE, FALSE, TRUE, FALSE, FALSE),
    ('pie', FALSE, FALSE, FALSE, TRUE, FALSE, FALSE),
    ('line', FALSE, FALSE, FALSE, FALSE, TRUE, FALSE),
    ('heatmap', FALSE, FALSE, FALSE, FALSE, FALSE, TRUE);

CREATE TABLE chart_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL REFERENCES analytical_requests(request_id)
        ON DELETE CASCADE,
    chart_id SMALLINT NOT NULL REFERENCES chart_types(chart_id),
    score NUMERIC(4,3) NOT NULL CHECK (score BETWEEN 0 AND 1),
    rationale TEXT NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (request_id, chart_id)
);

CREATE TABLE evaluation_warnings (
    warning_id BIGSERIAL PRIMARY KEY,
    evaluation_id BIGINT NOT NULL REFERENCES chart_evaluations(evaluation_id)
        ON DELETE CASCADE,
    warning_text TEXT NOT NULL CHECK (length(trim(warning_text)) > 0)
);

CREATE TABLE observations (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    category TEXT,
    x_value NUMERIC,
    y_value NUMERIC,
    measure NUMERIC,
    observed_at DATE,
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    UNIQUE (dataset_id, row_number)
);

CREATE TABLE matrix_cells (
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,
    row_key TEXT NOT NULL,
    column_key TEXT NOT NULL,
    cell_value NUMERIC NOT NULL,
    PRIMARY KEY (dataset_id, row_key, column_key)
);

CREATE INDEX idx_requests_intent
    ON analytical_requests(intent);

CREATE INDEX idx_evaluations_request_score
    ON chart_evaluations(request_id, score DESC);

CREATE INDEX idx_observations_dataset_category
    ON observations(dataset_id, category);

CREATE INDEX idx_observations_dataset_date
    ON observations(dataset_id, observed_at)
    WHERE observed_at IS NOT NULL;

INSERT INTO datasets (
    dataset_name,
    description,
    observation_count,
    numeric_measure_count,
    category_count,
    ordered_observations
)
VALUES
(
    'service_demand',
    'Operational demand by service category.',
    5,
    1,
    5,
    FALSE
),
(
    'incident_relationship',
    'Response hours and observed incident counts.',
    8,
    2,
    0,
    FALSE
),
(
    'monthly_demand',
    'Ordered monthly demand measurements.',
    12,
    1,
    0,
    TRUE
),
(
    'resource_composition',
    'Allocation percentages across organizational functions.',
    4,
    1,
    4,
    FALSE
),
(
    'performance_matrix',
    'Performance measurements across teams and periods.',
    12,
    1,
    0,
    FALSE
);

INSERT INTO observations (
    dataset_id,
    category,
    measure,
    row_number
)
SELECT
    d.dataset_id,
    v.category,
    v.measure,
    v.row_number
FROM datasets d
JOIN (
    VALUES
        ('service_demand', 'Cloud', 1840::numeric, 1),
        ('service_demand', 'Security', 1320::numeric, 2),
        ('service_demand', 'Data', 1610::numeric, 3),
        ('service_demand', 'Networking', 940::numeric, 4),
        ('service_demand', 'Applications', 2110::numeric, 5)
) AS v(dataset_name, category, measure, row_number)
ON d.dataset_name = v.dataset_name;

INSERT INTO observations (
    dataset_id,
    x_value,
    y_value,
    row_number
)
SELECT
    d.dataset_id,
    v.x_value,
    v.y_value,
    v.row_number
FROM datasets d
JOIN (
    VALUES
        ('incident_relationship', 12::numeric, 17::numeric, 1),
        ('incident_relationship', 18::numeric, 15::numeric, 2),
        ('incident_relationship', 21::numeric, 14::numeric, 3),
        ('incident_relationship', 27::numeric, 12::numeric, 4),
        ('incident_relationship', 30::numeric, 11::numeric, 5),
        ('incident_relationship', 35::numeric, 9::numeric, 6),
        ('incident_relationship', 41::numeric, 8::numeric, 7),
        ('incident_relationship', 48::numeric, 6::numeric, 8)
) AS v(dataset_name, x_value, y_value, row_number)
ON d.dataset_name = v.dataset_name;

INSERT INTO observations (
    dataset_id,
    measure,
    observed_at,
    row_number
)
SELECT
    d.dataset_id,
    v.measure,
    v.observed_at::date,
    v.row_number
FROM datasets d
JOIN (
    VALUES
        ('monthly_demand', 82::numeric, '2026-01-01', 1),
        ('monthly_demand', 91::numeric, '2026-02-01', 2),
        ('monthly_demand', 88::numeric, '2026-03-01', 3),
        ('monthly_demand', 105::numeric, '2026-04-01', 4),
        ('monthly_demand', 113::numeric, '2026-05-01', 5),
        ('monthly_demand', 121::numeric, '2026-06-01', 6),
        ('monthly_demand', 117::numeric, '2026-07-01', 7),
        ('monthly_demand', 129::numeric, '2026-08-01', 8),
        ('monthly_demand', 138::numeric, '2026-09-01', 9),
        ('monthly_demand', 145::numeric, '2026-10-01', 10),
        ('monthly_demand', 141::numeric, '2026-11-01', 11),
        ('monthly_demand', 154::numeric, '2026-12-01', 12)
) AS v(dataset_name, measure, observed_at, row_number)
ON d.dataset_name = v.dataset_name;

INSERT INTO observations (
    dataset_id,
    category,
    measure,
    row_number
)
SELECT
    d.dataset_id,
    v.category,
    v.measure,
    v.row_number
FROM datasets d
JOIN (
    VALUES
        ('resource_composition', 'Product', 52::numeric, 1),
        ('resource_composition', 'Support', 21::numeric, 2),
        ('resource_composition', 'Operations', 17::numeric, 3),
        ('resource_composition', 'Other', 10::numeric, 4)
) AS v(dataset_name, category, measure, row_number)
ON d.dataset_name = v.dataset_name;

INSERT INTO matrix_cells (
    dataset_id,
    row_key,
    column_key,
    cell_value
)
SELECT
    d.dataset_id,
    v.row_key,
    v.column_key,
    v.cell_value
FROM datasets d
JOIN (
    VALUES
        ('performance_matrix', 'Team A', 'Q1', 92::numeric),
        ('performance_matrix', 'Team A', 'Q2', 84::numeric),
        ('performance_matrix', 'Team A', 'Q3', 76::numeric),
        ('performance_matrix', 'Team B', 'Q1', 71::numeric),
        ('performance_matrix', 'Team B', 'Q2', 88::numeric),
        ('performance_matrix', 'Team B', 'Q3', 94::numeric),
        ('performance_matrix', 'Team C', 'Q1', 63::numeric),
        ('performance_matrix', 'Team C', 'Q2', 79::numeric),
        ('performance_matrix', 'Team C', 'Q3', 91::numeric),
        ('performance_matrix', 'Team D', 'Q1', 55::numeric),
        ('performance_matrix', 'Team D', 'Q2', 68::numeric),
        ('performance_matrix', 'Team D', 'Q3', 83::numeric)
) AS v(dataset_name, row_key, column_key, cell_value)
ON d.dataset_name = v.dataset_name;

CREATE OR REPLACE FUNCTION validate_request(p_request_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    request_record analytical_requests%ROWTYPE;
    dataset_record datasets%ROWTYPE;
    invalid_reason TEXT;
BEGIN
    SELECT *
    INTO request_record
    FROM analytical_requests
    WHERE request_id = p_request_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Request % does not exist', p_request_id;
    END IF;

    SELECT *
    INTO dataset_record
    FROM datasets
    WHERE dataset_id = request_record.dataset_id;

    invalid_reason := NULL;

    IF request_record.intent IN ('comparison', 'ranking', 'composition')
       AND dataset_record.category_count = 0
    THEN
        invalid_reason :=
            'This analytical intent requires categorical observations.';
    END IF;

    IF request_record.intent = 'trend'
       AND NOT dataset_record.ordered_observations
    THEN
        invalid_reason :=
            'Trend analysis requires an explicitly ordered observation sequence.';
    END IF;

    IF invalid_reason IS NOT NULL THEN
        UPDATE analytical_requests
        SET state = 'rejected'
        WHERE request_id = p_request_id;

        RAISE EXCEPTION '%', invalid_reason;
    END IF;

    UPDATE analytical_requests
    SET state = 'validated'
    WHERE request_id = p_request_id;
END;
$$;

CREATE OR REPLACE FUNCTION best_chart(p_request_id BIGINT)
RETURNS TABLE (
    chart chart_type,
    score NUMERIC,
    rationale TEXT
)
LANGUAGE sql
AS $$
    SELECT
        ct.chart,
        ce.score,
        ce.rationale
    FROM chart_evaluations ce
    JOIN chart_types ct
      ON ct.chart_id = ce.chart_id
    WHERE ce.request_id = p_request_id
    ORDER BY ce.score DESC
    LIMIT 1;
$$;

CREATE VIEW chart_evaluation_report AS
SELECT
    r.request_id,
    d.dataset_name,
    r.intent,
    r.state,
    ct.chart,
    ce.score,
    ce.rationale,
    ce.evaluated_at
FROM analytical_requests r
JOIN datasets d
  ON d.dataset_id = r.dataset_id
JOIN chart_evaluations ce
  ON ce.request_id = r.request_id
JOIN chart_types ct
  ON ct.chart_id = ce.chart_id;

CREATE VIEW dataset_statistics AS
SELECT
    d.dataset_name,
    COUNT(o.observation_id) AS observations,
    MIN(o.measure) AS minimum_measure,
    MAX(o.measure) AS maximum_measure,
    AVG(o.measure) AS mean_measure,
    percentile_cont(0.5)
        WITHIN GROUP (ORDER BY o.measure) AS median_measure
FROM datasets d
LEFT JOIN observations o
  ON o.dataset_id = d.dataset_id
WHERE o.measure IS NOT NULL
GROUP BY d.dataset_name;

BEGIN;

INSERT INTO analytical_requests (dataset_id, intent)
SELECT dataset_id, 'ranking'
FROM datasets
WHERE dataset_name = 'service_demand'
RETURNING request_id;

COMMIT;

BEGIN;

WITH request_data AS (
    SELECT
        request_id,
        dataset_id,
        intent
    FROM analytical_requests
    WHERE intent = 'ranking'
      AND state = 'proposed'
    ORDER BY request_id DESC
    LIMIT 1
)
INSERT INTO chart_evaluations (
    request_id,
    chart_id,
    score,
    rationale
)
SELECT
    rd.request_id,
    ct.chart_id,
    CASE ct.chart
        WHEN 'horizontal_bar' THEN 0.960
        WHEN 'dot_plot' THEN 0.910
        ELSE 0.200
    END,
    CASE ct.chart
        WHEN 'horizontal_bar'
            THEN 'A common quantitative axis makes category magnitudes directly comparable.'
        WHEN 'dot_plot'
            THEN 'Position on a shared scale supports precise comparison.'
        ELSE 'The structure is not the preferred representation for category ranking.'
    END
FROM request_data rd
JOIN chart_types ct
  ON ct.chart IN ('horizontal_bar', 'dot_plot');

COMMIT;

BEGIN;

INSERT INTO analytical_requests (dataset_id, intent)
SELECT dataset_id, 'relationship'
FROM datasets
WHERE dataset_name = 'incident_relationship';

INSERT INTO analytical_requests (dataset_id, intent)
SELECT dataset_id, 'trend'
FROM datasets
WHERE dataset_name = 'monthly_demand';

INSERT INTO analytical_requests (dataset_id, intent)
SELECT dataset_id, 'composition'
FROM datasets
WHERE dataset_name = 'resource_composition';

INSERT INTO analytical_requests (dataset_id, intent)
SELECT dataset_id, 'matrix'
FROM datasets
WHERE dataset_name = 'performance_matrix';

COMMIT;

-- The relationship request receives a scatter plot because both dimensions
-- are numeric and each observation must remain visible.
INSERT INTO chart_evaluations (
    request_id,
    chart_id,
    score,
    rationale
)
SELECT
    r.request_id,
    c.chart_id,
    0.980,
    'Each observation remains visible for relationship and outlier analysis.'
FROM analytical_requests r
JOIN chart_types c ON c.chart = 'scatter_plot'
WHERE r.intent = 'relationship';

INSERT INTO chart_evaluations (
    request_id,
    chart_id,
    score,
    rationale
)
SELECT
    r.request_id,
    c.chart_id,
    0.980,
    'Connected observations emphasize ordered change and turning points.'
FROM analytical_requests r
JOIN chart_types c ON c.chart = 'line'
WHERE r.intent = 'trend';

INSERT INTO chart_evaluations (
    request_id,
    chart_id,
    score,
    rationale
)
SELECT
    r.request_id,
    c.chart_id,
    0.950,
    'A common baseline makes component proportions easier to compare.'
FROM analytical_requests r
JOIN chart_types c ON c.chart = 'stacked_bar'
WHERE r.intent = 'composition';

INSERT INTO chart_evaluations (
    request_id,
    chart_id,
    score,
    rationale
)
SELECT
    r.request_id,
    c.chart_id,
    0.970,
    'Color intensity compactly represents values across two dimensions.'
FROM analytical_requests r
JOIN chart_types c ON c.chart = 'heatmap'
WHERE r.intent = 'matrix';

UPDATE analytical_requests
SET state = 'validated'
WHERE state = 'proposed';

INSERT INTO evaluation_warnings (evaluation_id, warning_text)
SELECT
    ce.evaluation_id,
    'Correlation does not establish causation.'
FROM chart_evaluations ce
JOIN chart_types ct ON ct.chart_id = ce.chart_id
WHERE ct.chart = 'scatter_plot';

INSERT INTO evaluation_warnings (evaluation_id, warning_text)
SELECT
    ce.evaluation_id,
    'Only connect observations when their ordering represents meaningful continuity.'
FROM chart_evaluations ce
JOIN chart_types ct ON ct.chart_id = ce.chart_id
WHERE ct.chart = 'line';

INSERT INTO evaluation_warnings (evaluation_id, warning_text)
SELECT
    ce.evaluation_id,
    'Use a perceptually ordered scale and annotate cells when exact values matter.'
FROM chart_evaluations ce
JOIN chart_types ct ON ct.chart_id = ce.chart_id
WHERE ct.chart = 'heatmap';

-- CTE-based reporting identifies the strongest structure for each analytical
-- request without storing a duplicated "winner" column.
WITH ranked AS (
    SELECT
        request_id,
        chart_id,
        score,
        ROW_NUMBER() OVER (
            PARTITION BY request_id
            ORDER BY score DESC
        ) AS position
    FROM chart_evaluations
)
SELECT
    r.request_id,
    d.dataset_name,
    r.intent,
    r.state,
    ct.chart AS recommended_chart,
    ranked.score
FROM ranked
JOIN analytical_requests r
  ON r.request_id = ranked.request_id
JOIN datasets d
  ON d.dataset_id = r.dataset_id
JOIN chart_types ct
  ON ct.chart_id = ranked.chart_id
WHERE ranked.position = 1
ORDER BY r.request_id;

-- Distribution statistics demonstrate a quantitative structure that can
-- support a histogram or box plot.
SELECT
    dataset_name,
    observations,
    ROUND(minimum_measure, 2) AS minimum_measure,
    ROUND(maximum_measure, 2) AS maximum_measure,
    ROUND(mean_measure, 2) AS mean_measure,
    ROUND(median_measure, 2) AS median_measure
FROM dataset_statistics
ORDER BY dataset_name;

-- Time-series retrieval preserves chronological order for line-chart input.
SELECT
    o.observed_at,
    o.measure,
    o.measure - LAG(o.measure) OVER (
        ORDER BY o.observed_at
    ) AS change_from_previous_period
FROM observations o
JOIN datasets d
  ON d.dataset_id = o.dataset_id
WHERE d.dataset_name = 'monthly_demand'
ORDER BY o.observed_at;

-- Composition validation shows why negative values are unsuitable for
-- part-to-whole encodings.
SELECT
    d.dataset_name,
    SUM(o.measure) AS total,
    BOOL_AND(o.measure >= 0) AS all_parts_non_negative,
    CASE
        WHEN SUM(o.measure) > 0
             AND BOOL_AND(o.measure >= 0)
        THEN 'valid for part-to-whole encoding'
        ELSE 'invalid for part-to-whole encoding'
    END AS composition_status
FROM datasets d
JOIN observations o
  ON o.dataset_id = d.dataset_id
WHERE d.dataset_name = 'resource_composition'
GROUP BY d.dataset_name;

-- Relationship input remains in paired rows rather than being reduced to
-- aggregates, because a scatter plot needs observation-level coordinates.
SELECT
    o.row_number,
    o.x_value,
    o.y_value
FROM observations o
JOIN datasets d
  ON d.dataset_id = o.dataset_id
WHERE d.dataset_name = 'incident_relationship'
ORDER BY o.row_number;

-- Matrix retrieval produces the rectangular structure expected by a heatmap.
SELECT
    row_key,
    column_key,
    cell_value
FROM matrix_cells mc
JOIN datasets d
  ON d.dataset_id = mc.dataset_id
WHERE d.dataset_name = 'performance_matrix'
ORDER BY row_key, column_key;

-- The function is evaluated after transactionally populated recommendations.
SELECT *
FROM best_chart(
    (
        SELECT request_id
        FROM analytical_requests
        WHERE intent = 'ranking'
        ORDER BY request_id DESC
        LIMIT 1
    )
);

SELECT *
FROM chart_evaluation_report
ORDER BY request_id, score DESC;
