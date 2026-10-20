DROP SCHEMA IF EXISTS pareto_business CASCADE;
CREATE SCHEMA pareto_business;
SET search_path TO pareto_business;

-- Business measures are modeled as measurable units of value.
-- Pareto analysis is then performed over the selected measure rather
-- than assuming that every business problem uses revenue.

CREATE TYPE item_status AS ENUM (
    'ACTIVE',
    'INACTIVE'
);

CREATE TYPE priority_class AS ENUM (
    'CORE',
    'THRESHOLD',
    'REMAINDER'
);

CREATE TABLE business_category (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE business_item (
    item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id BIGINT NOT NULL
        REFERENCES business_category(category_id),
    item_name TEXT NOT NULL,
    measured_value NUMERIC(18,2) NOT NULL
        CHECK (measured_value >= 0),
    status item_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (category_id, item_name)
);

CREATE INDEX idx_business_item_active_value
    ON business_item (measured_value DESC)
    WHERE status = 'ACTIVE';

CREATE TABLE pareto_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    target_share NUMERIC(6,5) NOT NULL
        CHECK (target_share > 0 AND target_share <= 1),
    maximum_focus_items INTEGER NOT NULL DEFAULT 0
        CHECK (maximum_focus_items >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pareto_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_id BIGINT NOT NULL
        REFERENCES pareto_policy(policy_id),
    total_value NUMERIC(18,2) NOT NULL
        CHECK (total_value > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pareto_result (
    run_id BIGINT NOT NULL
        REFERENCES pareto_run(run_id)
        ON DELETE CASCADE,
    item_id BIGINT NOT NULL
        REFERENCES business_item(item_id),
    rank_position INTEGER NOT NULL
        CHECK (rank_position > 0),
    value_share NUMERIC(12,8) NOT NULL
        CHECK (value_share >= 0 AND value_share <= 1),
    cumulative_share NUMERIC(12,8) NOT NULL
        CHECK (cumulative_share >= 0 AND cumulative_share <= 1),
    priority priority_class NOT NULL,
    PRIMARY KEY (run_id, item_id),
    UNIQUE (run_id, rank_position)
);

CREATE INDEX idx_pareto_result_priority
    ON pareto_result (run_id, priority);

CREATE TABLE analysis_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES pareto_run(run_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO business_category (category_name)
VALUES
    ('Customers'),
    ('Operations'),
    ('Technology'),
    ('Marketing'),
    ('People');

INSERT INTO business_item (
    category_id,
    item_name,
    measured_value
)
SELECT
    category_id,
    source.item_name,
    source.measured_value
FROM (
    VALUES
        ('Customers', 'Enterprise accounts', 420000.00),
        ('Customers', 'SMB accounts', 160000.00),
        ('Operations', 'Support tickets', 90000.00),
        ('Technology', 'Cloud infrastructure', 75000.00),
        ('Marketing', 'Marketing campaigns', 60000.00),
        ('People', 'Training programs', 40000.00),
        ('Technology', 'Internal tooling', 25000.00),
        ('Operations', 'Legacy reporting', 15000.00),
        ('Operations', 'Office services', 10000.00),
        ('Operations', 'Other requests', 5000.00)
) AS source(category_name, item_name, measured_value)
JOIN business_category
    ON business_category.category_name = source.category_name;

INSERT INTO pareto_policy (
    policy_name,
    target_share,
    maximum_focus_items
)
VALUES
    ('Standard 80 percent prioritization', 0.80000, 0),
    ('Executive five-item capacity', 0.80000, 5);

CREATE OR REPLACE FUNCTION validate_business_item()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF btrim(NEW.item_name) = '' THEN
        RAISE EXCEPTION 'Business item name cannot be empty';
    END IF;

    IF NEW.measured_value < 0 THEN
        RAISE EXCEPTION 'Business value cannot be negative';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_business_item
BEFORE INSERT OR UPDATE ON business_item
FOR EACH ROW
EXECUTE FUNCTION validate_business_item();

CREATE OR REPLACE FUNCTION run_pareto_analysis(
    p_policy_id BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_total NUMERIC(18,2);
    v_target NUMERIC(6,5);
BEGIN
    SELECT target_share
    INTO v_target
    FROM pareto_policy
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Active policy % does not exist',
            p_policy_id;
    END IF;

    SELECT COALESCE(SUM(measured_value), 0)
    INTO v_total
    FROM business_item
    WHERE status = 'ACTIVE';

    IF v_total <= 0 THEN
        RAISE EXCEPTION
            'Active business items have no measurable value';
    END IF;

    INSERT INTO pareto_run (
        policy_id,
        total_value
    )
    VALUES (
        p_policy_id,
        v_total
    )
    RETURNING run_id INTO v_run_id;

    WITH ranked AS (
        SELECT
            item_id,
            measured_value,
            measured_value / v_total AS value_share,
            SUM(measured_value) OVER (
                ORDER BY measured_value DESC, item_id
                ROWS BETWEEN UNBOUNDED PRECEDING
                AND CURRENT ROW
            ) / v_total AS cumulative_share
        FROM business_item
        WHERE status = 'ACTIVE'
    ),
    classified AS (
        SELECT
            item_id,
            value_share,
            cumulative_share,
            CASE
                WHEN cumulative_share - value_share < v_target
                    THEN CASE
                        WHEN cumulative_share >= v_target
                            THEN 'THRESHOLD'::priority_class
                        ELSE 'CORE'::priority_class
                    END
                ELSE 'REMAINDER'::priority_class
            END AS priority
        FROM ranked
    )
    INSERT INTO pareto_result (
        run_id,
        item_id,
        rank_position,
        value_share,
        cumulative_share,
        priority
    )
    SELECT
        v_run_id,
        classified.item_id,
        ROW_NUMBER() OVER (
            ORDER BY ranked.measured_value DESC,
                     ranked.item_id
        ),
        classified.value_share,
        classified.cumulative_share,
        classified.priority
    FROM classified
    JOIN ranked
        ON ranked.item_id = classified.item_id;

    INSERT INTO analysis_event (
        run_id,
        event_type,
        event_payload
    )
    VALUES (
        v_run_id,
        'ANALYSIS_COMPLETED',
        jsonb_build_object(
            'target_share', v_target,
            'total_value', v_total
        )
    );

    RETURN v_run_id;
END;
$$;

CREATE OR REPLACE VIEW pareto_analysis_report AS
SELECT
    pr.run_id,
    pr.rank_position,
    bi.item_name,
    bc.category_name,
    bi.measured_value,
    ROUND(pr.value_share * 100, 2) AS share_percent,
    ROUND(pr.cumulative_share * 100, 2)
        AS cumulative_percent,
    pr.priority
FROM pareto_result pr
JOIN business_item bi
    ON bi.item_id = pr.item_id
JOIN business_category bc
    ON bc.category_id = bi.category_id;

CREATE OR REPLACE VIEW category_contribution AS
SELECT
    bc.category_name,
    SUM(bi.measured_value) AS category_value,
    ROUND(
        SUM(bi.measured_value)
        / NULLIF(
            SUM(SUM(bi.measured_value)) OVER (),
            0
        ) * 100,
        2
    ) AS category_share_percent
FROM business_item bi
JOIN business_category bc
    ON bc.category_id = bi.category_id
WHERE bi.status = 'ACTIVE'
GROUP BY bc.category_name;

BEGIN;

SELECT run_pareto_analysis(1);

COMMIT;

-- Ranked Pareto result.
SELECT *
FROM pareto_analysis_report
WHERE run_id = (
    SELECT MAX(run_id)
    FROM pareto_run
)
ORDER BY rank_position;

-- Vital-few records. The threshold-crossing record remains included.
WITH latest AS (
    SELECT *
    FROM pareto_result
    WHERE run_id = (
        SELECT MAX(run_id)
        FROM pareto_run
    )
),
threshold AS (
    SELECT target_share
    FROM pareto_policy
    WHERE policy_id = (
        SELECT policy_id
        FROM pareto_run
        WHERE run_id = (SELECT MAX(run_id) FROM pareto_run)
    )
)
SELECT
    latest.rank_position,
    bi.item_name,
    latest.value_share,
    latest.cumulative_share,
    latest.priority
FROM latest
CROSS JOIN threshold
JOIN business_item bi
    ON bi.item_id = latest.item_id
WHERE latest.cumulative_share - latest.value_share
      < threshold.target_share
ORDER BY latest.rank_position;

-- Category-level contribution provides a different analytical view
-- from item-level Pareto ranking.
SELECT *
FROM category_contribution
ORDER BY category_value DESC;

-- Capacity-constrained prioritization.
WITH latest AS (
    SELECT
        pr.*,
        pp.maximum_focus_items
    FROM pareto_result pr
    JOIN pareto_run run
        ON run.run_id = pr.run_id
    JOIN pareto_policy pp
        ON pp.policy_id = run.policy_id
    WHERE pr.run_id = (
        SELECT MAX(run_id)
        FROM pareto_run
    )
)
SELECT
    rank_position,
    item_id,
    value_share,
    cumulative_share,
    priority
FROM latest
WHERE rank_position <= (
    SELECT maximum_focus_items
    FROM latest
    LIMIT 1
)
   OR priority = 'THRESHOLD'
ORDER BY rank_position;

-- Integrity check: every active item's contribution should add to one.
SELECT
    run_id,
    ROUND(SUM(value_share), 8) AS total_share
FROM pareto_result
GROUP BY run_id
ORDER BY run_id;

-- Failure case is isolated in a transaction so the production data
-- remains unchanged after the constraint violation.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO business_item (
            category_id,
            item_name,
            measured_value
        )
        SELECT
            category_id,
            'Invalid negative-value item',
            -100.00
        FROM business_category
        WHERE category_name = 'Operations';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected validation failure: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK;
