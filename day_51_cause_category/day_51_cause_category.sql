DROP SCHEMA IF EXISTS root_cause_analysis CASCADE;
CREATE SCHEMA root_cause_analysis;
SET search_path TO root_cause_analysis;

-- Evidence is stored independently so a diagnosis can distinguish
-- observations from assumptions and record where each observation came from.
CREATE TABLE incidents (
    incident_id          BIGSERIAL PRIMARY KEY,
    incident_key         TEXT NOT NULL UNIQUE,
    title                TEXT NOT NULL,
    description          TEXT NOT NULL,
    severity              TEXT NOT NULL
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status                TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'INVESTIGATING', 'ROOT_CAUSE_FOUND', 'CLOSED')),
    detected_at           TIMESTAMPTZ NOT NULL,
    closed_at             TIMESTAMPTZ,
    CHECK (closed_at IS NULL OR closed_at >= detected_at)
);

CREATE TABLE cause_categories (
    category_code         TEXT PRIMARY KEY,
    category_name         TEXT NOT NULL UNIQUE
);

INSERT INTO cause_categories(category_code, category_name)
VALUES
    ('PEOPLE', 'People'),
    ('PROCESS', 'Process'),
    ('TECHNOLOGY', 'Technology'),
    ('DATA', 'Data'),
    ('ENVIRONMENT', 'Environment'),
    ('MANAGEMENT', 'Management');

CREATE TABLE evidence (
    evidence_id           BIGSERIAL PRIMARY KEY,
    incident_id           BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    observation           TEXT NOT NULL,
    source_name           TEXT NOT NULL,
    strength              SMALLINT NOT NULL
        CHECK (strength BETWEEN 1 AND 3),
    observed_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evidence_incident_strength
    ON evidence(incident_id, strength DESC);

CREATE TABLE causes (
    cause_id              BIGSERIAL PRIMARY KEY,
    incident_id           BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    category_code         TEXT NOT NULL
        REFERENCES cause_categories(category_code),
    parent_cause_id       BIGINT
        REFERENCES causes(cause_id) ON DELETE CASCADE,
    statement             TEXT NOT NULL,
    hypothesis_status     TEXT NOT NULL DEFAULT 'UNTESTED'
        CHECK (hypothesis_status IN (
            'UNTESTED',
            'SUPPORTED',
            'DISPROVED',
            'ROOT_CAUSE'
        )),
    UNIQUE (incident_id, cause_id)
);

CREATE INDEX idx_causes_incident_category
    ON causes(incident_id, category_code);

CREATE TABLE cause_evidence (
    cause_id              BIGINT NOT NULL
        REFERENCES causes(cause_id) ON DELETE CASCADE,
    evidence_id           BIGINT NOT NULL
        REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    PRIMARY KEY (cause_id, evidence_id)
);

CREATE TABLE why_steps (
    why_step_id           BIGSERIAL PRIMARY KEY,
    incident_id           BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    step_number           INTEGER NOT NULL
        CHECK (step_number BETWEEN 1 AND 5),
    question              TEXT NOT NULL,
    answer                TEXT NOT NULL,
    cause_id              BIGINT
        REFERENCES causes(cause_id) ON DELETE SET NULL,
    UNIQUE (incident_id, step_number)
);

CREATE TABLE why_evidence (
    why_step_id           BIGINT NOT NULL
        REFERENCES why_steps(why_step_id) ON DELETE CASCADE,
    evidence_id           BIGINT NOT NULL
        REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    PRIMARY KEY (why_step_id, evidence_id)
);

CREATE TABLE corrective_actions (
    action_id             BIGSERIAL PRIMARY KEY,
    incident_id           BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    cause_id              BIGINT NOT NULL
        REFERENCES causes(cause_id),
    action_name           TEXT NOT NULL,
    owner_name            TEXT NOT NULL,
    target_date           DATE NOT NULL,
    status                TEXT NOT NULL DEFAULT 'PLANNED'
        CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'VERIFIED', 'FAILED')),
    effectiveness_metric TEXT NOT NULL
);

CREATE TABLE measurements (
    measurement_id       BIGSERIAL PRIMARY KEY,
    incident_id           BIGINT NOT NULL
        REFERENCES incidents(incident_id) ON DELETE CASCADE,
    metric_name           TEXT NOT NULL,
    measurement_phase    TEXT NOT NULL
        CHECK (measurement_phase IN ('BEFORE', 'AFTER')),
    metric_value          NUMERIC(18,6) NOT NULL,
    measured_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_measurements_metric_phase
    ON measurements(incident_id, metric_name, measurement_phase);

CREATE OR REPLACE FUNCTION validate_why_step()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.step_number > 1 THEN
        IF NOT EXISTS (
            SELECT 1
            FROM why_steps
            WHERE incident_id = NEW.incident_id
              AND step_number = NEW.step_number - 1
        ) THEN
            RAISE EXCEPTION
                'Why step % requires the previous step for incident %',
                NEW.step_number,
                NEW.incident_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_why_step
BEFORE INSERT OR UPDATE ON why_steps
FOR EACH ROW
EXECUTE FUNCTION validate_why_step();

CREATE OR REPLACE FUNCTION prevent_multiple_root_causes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.hypothesis_status = 'ROOT_CAUSE'
       AND EXISTS (
           SELECT 1
           FROM causes
           WHERE incident_id = NEW.incident_id
             AND hypothesis_status = 'ROOT_CAUSE'
             AND cause_id <> NEW.cause_id
       )
    THEN
        RAISE EXCEPTION
            'An incident can have only one active root cause.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_multiple_root_causes
BEFORE INSERT OR UPDATE ON causes
FOR EACH ROW
EXECUTE FUNCTION prevent_multiple_root_causes();

CREATE OR REPLACE FUNCTION evidence_score(p_cause_id BIGINT)
RETURNS INTEGER
LANGUAGE sql
STABLE
AS $$
    SELECT COALESCE(SUM(e.strength), 0)::INTEGER
    FROM cause_evidence ce
    JOIN evidence e ON e.evidence_id = ce.evidence_id
    WHERE ce.cause_id = p_cause_id;
$$;

CREATE OR REPLACE FUNCTION evaluate_cause(p_cause_id BIGINT)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    score INTEGER;
    source_count INTEGER;
BEGIN
    score := evidence_score(p_cause_id);

    SELECT COUNT(DISTINCT e.source_name)
    INTO source_count
    FROM cause_evidence ce
    JOIN evidence e ON e.evidence_id = ce.evidence_id
    WHERE ce.cause_id = p_cause_id;

    IF score >= 6 AND source_count >= 2 THEN
        RETURN 'SUPPORTED';
    ELSIF score >= 3 THEN
        RETURN 'PLAUSIBLE';
    END IF;

    RETURN 'WEAK';
END;
$$;

CREATE OR REPLACE VIEW cause_diagnostic_report AS
SELECT
    c.cause_id,
    c.incident_id,
    c.category_code,
    cc.category_name,
    c.statement,
    c.hypothesis_status,
    evidence_score(c.cause_id) AS evidence_score,
    COUNT(DISTINCT e.source_name) AS independent_sources
FROM causes c
JOIN cause_categories cc
  ON cc.category_code = c.category_code
LEFT JOIN cause_evidence ce
  ON ce.cause_id = c.cause_id
LEFT JOIN evidence e
  ON e.evidence_id = ce.evidence_id
GROUP BY
    c.cause_id,
    c.incident_id,
    c.category_code,
    cc.category_name,
    c.statement,
    c.hypothesis_status;

CREATE OR REPLACE VIEW why_chain AS
SELECT
    ws.incident_id,
    ws.step_number,
    ws.question,
    ws.answer,
    ws.cause_id,
    c.category_code
FROM why_steps ws
LEFT JOIN causes c
  ON c.cause_id = ws.cause_id;

CREATE OR REPLACE VIEW measurement_comparison AS
WITH averages AS (
    SELECT
        incident_id,
        metric_name,
        measurement_phase,
        AVG(metric_value) AS average_value
    FROM measurements
    GROUP BY incident_id, metric_name, measurement_phase
)
SELECT
    before_values.incident_id,
    before_values.metric_name,
    before_values.average_value AS before_value,
    after_values.average_value AS after_value,
    after_values.average_value < before_values.average_value
        AS decreased
FROM averages before_values
JOIN averages after_values
  ON after_values.incident_id = before_values.incident_id
 AND after_values.metric_name = before_values.metric_name
WHERE before_values.measurement_phase = 'BEFORE'
  AND after_values.measurement_phase = 'AFTER';

INSERT INTO incidents (
    incident_key,
    title,
    description,
    severity,
    status,
    detected_at
)
VALUES (
    'INC-2026-041',
    'Payment API connection exhaustion',
    'Payment requests failed after a deployment because database connections accumulated.',
    'CRITICAL',
    'ROOT_CAUSE_FOUND',
    '2026-10-21 08:15:00+05:30'
);

INSERT INTO evidence (
    incident_id,
    observation,
    source_name,
    strength
)
SELECT
    incident_id,
    item.observation,
    item.source_name,
    item.strength
FROM incidents i
CROSS JOIN (
    VALUES
        (
            'Connection pool utilization reached 100 percent.',
            'application metrics',
            3
        ),
        (
            'Connection count increased after repeated requests.',
            'database telemetry',
            3
        ),
        (
            'The endpoint lacked reliable connection cleanup.',
            'source inspection',
            3
        ),
        (
            'Integration tests covered successful single requests only.',
            'test suite',
            3
        ),
        (
            'No acceptance criterion required resource-lifecycle testing.',
            'release checklist',
            2
        ),
        (
            'Pool saturation was detected only after resource exhaustion.',
            'monitoring configuration',
            2
        )
) AS item(observation, source_name, strength)
WHERE i.incident_key = 'INC-2026-041';

INSERT INTO causes (
    incident_id,
    category_code,
    statement,
    hypothesis_status
)
SELECT
    incident_id,
    'PROCESS',
    'Release acceptance did not require database connection-lifecycle testing.',
    'SUPPORTED'
FROM incidents
WHERE incident_key = 'INC-2026-041';

INSERT INTO causes (
    incident_id,
    category_code,
    statement,
    hypothesis_status
)
SELECT
    incident_id,
    'TECHNOLOGY',
    'A database endpoint allowed connections to remain open until pool exhaustion.',
    'SUPPORTED'
FROM incidents
WHERE incident_key = 'INC-2026-041';

INSERT INTO causes (
    incident_id,
    category_code,
    statement,
    hypothesis_status
)
SELECT
    incident_id,
    'DATA',
    'Monitoring detected saturation but did not detect abnormal connection growth early.',
    'UNTESTED'
FROM incidents
WHERE incident_key = 'INC-2026-041';

INSERT INTO causes (
    incident_id,
    category_code,
    statement,
    hypothesis_status
)
SELECT
    incident_id,
    'MANAGEMENT',
    'Delivery criteria emphasized endpoint functionality without explicit operational-resource acceptance.',
    'UNTESTED'
FROM incidents
WHERE incident_key = 'INC-2026-041';

INSERT INTO cause_evidence (cause_id, evidence_id)
SELECT
    c.cause_id,
    e.evidence_id
FROM causes c
JOIN evidence e
  ON e.incident_id = c.incident_id
WHERE c.category_code = 'PROCESS'
  AND e.source_name IN ('test suite', 'release checklist');

INSERT INTO cause_evidence (cause_id, evidence_id)
SELECT
    c.cause_id,
    e.evidence_id
FROM causes c
JOIN evidence e
  ON e.incident_id = c.incident_id
WHERE c.category_code = 'TECHNOLOGY'
  AND e.source_name IN ('database telemetry', 'source inspection');

INSERT INTO cause_evidence (cause_id, evidence_id)
SELECT
    c.cause_id,
    e.evidence_id
FROM causes c
JOIN evidence e
  ON e.incident_id = c.incident_id
WHERE c.category_code = 'DATA'
  AND e.source_name IN ('application metrics', 'monitoring configuration');

INSERT INTO why_steps (
    incident_id,
    step_number,
    question,
    answer,
    cause_id
)
SELECT
    i.incident_id,
    w.step_number,
    w.question,
    w.answer,
    c.cause_id
FROM incidents i
CROSS JOIN (
    VALUES
        (
            1,
            'Why did payment requests fail?',
            'The payment service exhausted its database connection pool.',
            'TECHNOLOGY'
        ),
        (
            2,
            'Why was the connection pool exhausted?',
            'A new endpoint did not reliably release database connections.',
            'TECHNOLOGY'
        ),
        (
            3,
            'Why could the endpoint reach production with that defect?',
            'Integration tests did not exercise repeated requests under connection pressure.',
            'PROCESS'
        ),
        (
            4,
            'Why did testing omit connection pressure?',
            'Acceptance criteria measured functional responses but not resource lifecycle.',
            'PROCESS'
        ),
        (
            5,
            'Why were resource-lifecycle criteria absent?',
            'The engineering delivery process did not require operational-resource checks for database-backed endpoints.',
            'PROCESS'
        )
) AS w(step_number, question, answer, category_code)
LEFT JOIN causes c
  ON c.incident_id = i.incident_id
 AND c.category_code = w.category_code
WHERE i.incident_key = 'INC-2026-041';

INSERT INTO why_evidence (why_step_id, evidence_id)
SELECT
    ws.why_step_id,
    e.evidence_id
FROM why_steps ws
JOIN evidence e
  ON e.incident_id = ws.incident_id
WHERE ws.incident_id = (
    SELECT incident_id
    FROM incidents
    WHERE incident_key = 'INC-2026-041'
)
AND (
    (ws.step_number = 1 AND e.source_name = 'application metrics')
 OR (ws.step_number = 2 AND e.source_name = 'database telemetry')
 OR (ws.step_number = 3 AND e.source_name = 'test suite')
 OR (ws.step_number = 4 AND e.source_name = 'test suite')
 OR (ws.step_number = 5 AND e.source_name = 'release checklist')
);

INSERT INTO corrective_actions (
    incident_id,
    cause_id,
    action_name,
    owner_name,
    target_date,
    status,
    effectiveness_metric
)
SELECT
    i.incident_id,
    c.cause_id,
    'Add repeated-request connection-lifecycle regression tests',
    'Platform Engineering',
    '2026-10-28',
    'IN_PROGRESS',
    'Average connection count returns to baseline after repeated requests'
FROM incidents i
JOIN causes c
  ON c.incident_id = i.incident_id
 AND c.category_code = 'PROCESS'
WHERE i.incident_key = 'INC-2026-041';

INSERT INTO corrective_actions (
    incident_id,
    cause_id,
    action_name,
    owner_name,
    target_date,
    status,
    effectiveness_metric
)
SELECT
    i.incident_id,
    c.cause_id,
    'Guarantee database resource release through scoped transaction handling',
    'Payments Engineering',
    '2026-10-25',
    'VERIFIED',
    'Connection count remains stable during sustained load'
FROM incidents i
JOIN causes c
  ON c.incident_id = i.incident_id
 AND c.category_code = 'TECHNOLOGY'
WHERE i.incident_key = 'INC-2026-041';

INSERT INTO measurements (
    incident_id,
    metric_name,
    measurement_phase,
    metric_value
)
SELECT
    i.incident_id,
    'database_connection_utilization',
    m.measurement_phase,
    m.metric_value
FROM incidents i
CROSS JOIN (
    VALUES
        ('BEFORE', 99.0),
        ('BEFORE', 103.0),
        ('BEFORE', 101.0),
        ('BEFORE', 100.0),
        ('AFTER', 71.0),
        ('AFTER', 69.0),
        ('AFTER', 73.0),
        ('AFTER', 70.0)
) AS m(measurement_phase, metric_value)
WHERE i.incident_key = 'INC-2026-041';

-- Transactional validation makes the evidence and corrective-action update atomic.
BEGIN;

UPDATE corrective_actions
SET status = 'VERIFIED'
WHERE action_name = 'Add repeated-request connection-lifecycle regression tests'
  AND incident_id = (
      SELECT incident_id
      FROM incidents
      WHERE incident_key = 'INC-2026-041'
  );

UPDATE incidents
SET status = 'CLOSED',
    closed_at = CURRENT_TIMESTAMP
WHERE incident_key = 'INC-2026-041'
  AND NOT EXISTS (
      SELECT 1
      FROM corrective_actions ca
      WHERE ca.incident_id = incidents.incident_id
        AND ca.status <> 'VERIFIED'
  );

COMMIT;

-- Diagnostic report: evidence strength and independent evidence sources.
SELECT *
FROM cause_diagnostic_report
WHERE incident_id = (
    SELECT incident_id
    FROM incidents
    WHERE incident_key = 'INC-2026-041'
)
ORDER BY evidence_score DESC, cause_id;

-- Five-Whys causal chain.
SELECT
    step_number,
    question,
    answer,
    category_code
FROM why_chain
WHERE incident_id = (
    SELECT incident_id
    FROM incidents
    WHERE incident_key = 'INC-2026-041'
)
ORDER BY step_number;

-- Measurement validation tests whether the corrective control changed the metric.
SELECT *
FROM measurement_comparison
WHERE incident_id = (
    SELECT incident_id
    FROM incidents
    WHERE incident_key = 'INC-2026-041'
);

-- Actions still requiring work.
SELECT
    ca.action_name,
    ca.owner_name,
    ca.target_date,
    ca.status,
    ca.effectiveness_metric
FROM corrective_actions ca
WHERE ca.incident_id = (
    SELECT incident_id
    FROM incidents
    WHERE incident_key = 'INC-2026-041'
)
ORDER BY ca.target_date;

-- Category-level diagnostic view for comparing alternative cause classes.
WITH category_scores AS (
    SELECT
        category_code,
        SUM(evidence_score) AS total_evidence,
        COUNT(*) AS hypothesis_count
    FROM cause_diagnostic_report
    WHERE incident_id = (
        SELECT incident_id
        FROM incidents
        WHERE incident_key = 'INC-2026-041'
    )
    GROUP BY category_code
)
SELECT
    cc.category_name,
    cs.total_evidence,
    cs.hypothesis_count
FROM category_scores cs
JOIN cause_categories cc
  ON cc.category_code = cs.category_code
ORDER BY cs.total_evidence DESC;

-- Recursive fishbone traversal demonstrates hierarchical cause relationships.
WITH RECURSIVE cause_tree AS (
    SELECT
        c.cause_id,
        c.parent_cause_id,
        c.statement,
        0 AS depth
    FROM causes c
    WHERE c.incident_id = (
        SELECT incident_id
        FROM incidents
        WHERE incident_key = 'INC-2026-041'
    )
    AND c.parent_cause_id IS NULL

    UNION ALL

    SELECT
        child.cause_id,
        child.parent_cause_id,
        child.statement,
        parent.depth + 1
    FROM causes child
    JOIN cause_tree parent
      ON child.parent_cause_id = parent.cause_id
)
SELECT
    repeat('  ', depth) || statement AS cause_path,
    depth
FROM cause_tree
ORDER BY depth, cause_id;
