DROP SCHEMA IF EXISTS numpy_numerical CASCADE;

CREATE SCHEMA numpy_numerical;

SET search_path TO numpy_numerical, public;

CREATE TYPE measurement_status AS ENUM (
    'NORMAL',
    'WARNING',
    'CRITICAL',
    'INVALID'
);

CREATE TABLE sensor_batches (
    batch_id BIGSERIAL PRIMARY KEY,
    batch_name TEXT NOT NULL UNIQUE,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_system TEXT NOT NULL,
    CONSTRAINT sensor_batches_source_check
        CHECK (length(trim(source_system)) >= 3)
);

CREATE TABLE sensors (
    sensor_id BIGSERIAL PRIMARY KEY,
    sensor_name TEXT NOT NULL UNIQUE,
    unit TEXT NOT NULL,
    minimum_valid DOUBLE PRECISION,
    maximum_valid DOUBLE PRECISION,
    CONSTRAINT sensors_range_check
        CHECK (
            minimum_valid IS NULL
            OR maximum_valid IS NULL
            OR minimum_valid < maximum_valid
        )
);

CREATE TABLE measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL
        REFERENCES sensor_batches(batch_id)
        ON DELETE CASCADE,
    sensor_id BIGINT NOT NULL
        REFERENCES sensors(sensor_id)
        ON DELETE RESTRICT,
    sample_index INTEGER NOT NULL,
    value DOUBLE PRECISION,
    status measurement_status NOT NULL DEFAULT 'NORMAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT measurements_sample_check
        CHECK (sample_index >= 0),
    CONSTRAINT measurements_value_check
        CHECK (
            value IS NULL
            OR value = value
        ),
    CONSTRAINT measurements_unique_sample
        UNIQUE (batch_id, sensor_id, sample_index)
);

CREATE TABLE normalization_profiles (
    profile_id BIGSERIAL PRIMARY KEY,
    sensor_id BIGINT NOT NULL
        REFERENCES sensors(sensor_id)
        ON DELETE CASCADE,
    minimum_value DOUBLE PRECISION NOT NULL,
    maximum_value DOUBLE PRECISION NOT NULL,
    weight DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT normalization_range_check
        CHECK (minimum_value <= maximum_value),
    CONSTRAINT normalization_weight_check
        CHECK (weight >= 0)
);

CREATE TABLE anomaly_evaluations (
    evaluation_id BIGSERIAL PRIMARY KEY,
    batch_id BIGINT NOT NULL
        REFERENCES sensor_batches(batch_id)
        ON DELETE CASCADE,
    sample_index INTEGER NOT NULL,
    z_score_max DOUBLE PRECISION,
    is_anomaly BOOLEAN NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT anomaly_sample_check
        CHECK (sample_index >= 0)
);

CREATE INDEX idx_measurements_batch_sample
    ON measurements(batch_id, sample_index);

CREATE INDEX idx_measurements_sensor
    ON measurements(sensor_id);

CREATE INDEX idx_measurements_status
    ON measurements(status)
    WHERE status IN ('WARNING', 'CRITICAL', 'INVALID');

CREATE INDEX idx_anomaly_batch_sample
    ON anomaly_evaluations(batch_id, sample_index);

INSERT INTO sensors (
    sensor_name,
    unit,
    minimum_valid,
    maximum_valid
)
VALUES
    ('temperature_c', 'C', -40.0, 85.0),
    ('humidity_pct', '%', 0.0, 100.0),
    ('pressure_hpa', 'hPa', 800.0, 1200.0),
    ('vibration', 'g', 0.0, 10.0);

INSERT INTO sensor_batches (
    batch_name,
    source_system
)
VALUES
    ('LAB-2026-11-01-A', 'environment-monitor');

INSERT INTO normalization_profiles (
    sensor_id,
    minimum_value,
    maximum_value,
    weight
)
SELECT
    sensor_id,
    minimum_valid,
    maximum_valid,
    CASE sensor_name
        WHEN 'temperature_c' THEN 0.35
        WHEN 'humidity_pct' THEN 0.20
        WHEN 'pressure_hpa' THEN 0.25
        WHEN 'vibration' THEN 0.20
    END
FROM sensors;

INSERT INTO measurements (
    batch_id,
    sensor_id,
    sample_index,
    value
)
SELECT
    b.batch_id,
    s.sensor_id,
    data.sample_index,
    data.value
FROM sensor_batches b
JOIN sensors s
    ON s.sensor_name = data.sensor_name
CROSS JOIN (
    VALUES
        (0, 'temperature_c', 22.4::DOUBLE PRECISION),
        (0, 'humidity_pct', 45.0::DOUBLE PRECISION),
        (0, 'pressure_hpa', 1012.3::DOUBLE PRECISION),
        (0, 'vibration', 0.12::DOUBLE PRECISION),

        (1, 'temperature_c', 23.1::DOUBLE PRECISION),
        (1, 'humidity_pct', 46.5::DOUBLE PRECISION),
        (1, 'pressure_hpa', 1011.8::DOUBLE PRECISION),
        (1, 'vibration', 0.15::DOUBLE PRECISION),

        (2, 'temperature_c', 24.8::DOUBLE PRECISION),
        (2, 'humidity_pct', 49.2::DOUBLE PRECISION),
        (2, 'pressure_hpa', 1010.4::DOUBLE PRECISION),
        (2, 'vibration', 0.18::DOUBLE PRECISION),

        (3, 'temperature_c', 26.7::DOUBLE PRECISION),
        (3, 'humidity_pct', 54.0::DOUBLE PRECISION),
        (3, 'pressure_hpa', 1008.9::DOUBLE PRECISION),
        (3, 'vibration', 0.31::DOUBLE PRECISION),

        (4, 'temperature_c', 28.4::DOUBLE PRECISION),
        (4, 'humidity_pct', 58.1::DOUBLE PRECISION),
        (4, 'pressure_hpa', 1007.5::DOUBLE PRECISION),
        (4, 'vibration', 0.42::DOUBLE PRECISION),

        (5, 'temperature_c', 29.1::DOUBLE PRECISION),
        (5, 'humidity_pct', 61.0::DOUBLE PRECISION),
        (5, 'pressure_hpa', 1006.2::DOUBLE PRECISION),
        (5, 'vibration', 0.55::DOUBLE PRECISION),

        (6, 'temperature_c', 27.8::DOUBLE PRECISION),
        (6, 'humidity_pct', 57.3::DOUBLE PRECISION),
        (6, 'pressure_hpa', 1007.1::DOUBLE PRECISION),
        (6, 'vibration', 0.38::DOUBLE PRECISION),

        (7, 'temperature_c', 25.6::DOUBLE PRECISION),
        (7, 'humidity_pct', 51.4::DOUBLE PRECISION),
        (7, 'pressure_hpa', 1009.2::DOUBLE PRECISION),
        (7, 'vibration', 0.22::DOUBLE PRECISION)
) AS data(sample_index, sensor_name, value)
WHERE b.batch_name = 'LAB-2026-11-01-A';

CREATE OR REPLACE FUNCTION validate_measurement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    lower_bound DOUBLE PRECISION;
    upper_bound DOUBLE PRECISION;
BEGIN
    SELECT minimum_valid, maximum_valid
    INTO lower_bound, upper_bound
    FROM sensors
    WHERE sensor_id = NEW.sensor_id;

    IF NEW.value IS NULL THEN
        NEW.status := 'INVALID';
        RETURN NEW;
    END IF;

    IF NEW.value < lower_bound OR NEW.value > upper_bound THEN
        NEW.status := 'INVALID';
    ELSE
        NEW.status := 'NORMAL';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT OR UPDATE OF value, sensor_id
ON measurements
FOR EACH ROW
EXECUTE FUNCTION validate_measurement();

CREATE OR REPLACE VIEW measurement_matrix AS
SELECT
    m.batch_id,
    m.sample_index,
    MAX(m.value) FILTER (
        WHERE s.sensor_name = 'temperature_c'
    ) AS temperature_c,
    MAX(m.value) FILTER (
        WHERE s.sensor_name = 'humidity_pct'
    ) AS humidity_pct,
    MAX(m.value) FILTER (
        WHERE s.sensor_name = 'pressure_hpa'
    ) AS pressure_hpa,
    MAX(m.value) FILTER (
        WHERE s.sensor_name = 'vibration'
    ) AS vibration
FROM measurements m
JOIN sensors s
    ON s.sensor_id = m.sensor_id
GROUP BY
    m.batch_id,
    m.sample_index;

CREATE OR REPLACE FUNCTION calculate_column_statistics(
    target_batch BIGINT
)
RETURNS TABLE (
    sensor_name TEXT,
    minimum_value DOUBLE PRECISION,
    maximum_value DOUBLE PRECISION,
    mean_value DOUBLE PRECISION,
    standard_deviation DOUBLE PRECISION,
    measurement_count BIGINT
)
LANGUAGE sql
AS $$
    SELECT
        s.sensor_name,
        MIN(m.value),
        MAX(m.value),
        AVG(m.value),
        STDDEV_POP(m.value),
        COUNT(m.value)
    FROM measurements m
    JOIN sensors s
        ON s.sensor_id = m.sensor_id
    WHERE m.batch_id = target_batch
      AND m.status <> 'INVALID'
    GROUP BY s.sensor_name
    ORDER BY s.sensor_name;
$$;

CREATE OR REPLACE FUNCTION calculate_normalized_scores(
    target_batch BIGINT
)
RETURNS TABLE (
    sample_index INTEGER,
    normalized_score DOUBLE PRECISION
)
LANGUAGE sql
AS $$
    WITH matrix AS (
        SELECT
            m.sample_index,
            s.sensor_name,
            m.value,
            p.minimum_value,
            p.maximum_value,
            p.weight
        FROM measurements m
        JOIN sensors s
            ON s.sensor_id = m.sensor_id
        JOIN normalization_profiles p
            ON p.sensor_id = s.sensor_id
        WHERE m.batch_id = target_batch
          AND m.status <> 'INVALID'
    ),
    normalized AS (
        SELECT
            sample_index,
            sensor_name,
            weight,
            CASE
                WHEN maximum_value = minimum_value THEN 0.0
                ELSE
                    (value - minimum_value)
                    / (maximum_value - minimum_value)
            END AS normalized_value
        FROM matrix
    )
    SELECT
        sample_index,
        SUM(normalized_value * weight) AS normalized_score
    FROM normalized
    GROUP BY sample_index
    ORDER BY sample_index;
$$;

CREATE OR REPLACE FUNCTION calculate_z_scores(
    target_batch BIGINT
)
RETURNS TABLE (
    sample_index INTEGER,
    maximum_absolute_z DOUBLE PRECISION,
    is_anomaly BOOLEAN
)
LANGUAGE sql
AS $$
    WITH source AS (
        SELECT
            m.sample_index,
            s.sensor_name,
            m.value,
            AVG(m.value) OVER (
                PARTITION BY s.sensor_id
            ) AS mean_value,
            STDDEV_POP(m.value) OVER (
                PARTITION BY s.sensor_id
            ) AS standard_deviation
        FROM measurements m
        JOIN sensors s
            ON s.sensor_id = m.sensor_id
        WHERE m.batch_id = target_batch
          AND m.status <> 'INVALID'
          AND m.value IS NOT NULL
    ),
    scores AS (
        SELECT
            sample_index,
            sensor_name,
            ABS(
                CASE
                    WHEN standard_deviation = 0 THEN 0.0
                    ELSE
                        (value - mean_value)
                        / standard_deviation
                END
            ) AS absolute_z
        FROM source
    )
    SELECT
        sample_index,
        MAX(absolute_z) AS maximum_absolute_z,
        MAX(absolute_z) >= 2.0 AS is_anomaly
    FROM scores
    GROUP BY sample_index
    ORDER BY sample_index;
$$;

BEGIN;

UPDATE measurements
SET status = 'WARNING'
WHERE batch_id = (
    SELECT batch_id
    FROM sensor_batches
    WHERE batch_name = 'LAB-2026-11-01-A'
)
AND sensor_id = (
    SELECT sensor_id
    FROM sensors
    WHERE sensor_name = 'temperature_c'
)
AND value >= 28.0
AND status = 'NORMAL';

COMMIT;

SELECT *
FROM measurement_matrix
ORDER BY batch_id, sample_index;

SELECT *
FROM calculate_column_statistics(
    (
        SELECT batch_id
        FROM sensor_batches
        WHERE batch_name = 'LAB-2026-11-01-A'
    )
);

SELECT *
FROM calculate_normalized_scores(
    (
        SELECT batch_id
        FROM sensor_batches
        WHERE batch_name = 'LAB-2026-11-01-A'
    )
);

SELECT *
FROM calculate_z_scores(
    (
        SELECT batch_id
        FROM sensor_batches
        WHERE batch_name = 'LAB-2026-11-01-A'
    )
);

WITH scores AS (
    SELECT *
    FROM calculate_normalized_scores(
        (
            SELECT batch_id
            FROM sensor_batches
            WHERE batch_name = 'LAB-2026-11-01-A'
        )
    )
)
SELECT
    sample_index,
    normalized_score,
    CASE
        WHEN normalized_score >= 0.60 THEN 'ALERT'
        ELSE 'NORMAL'
    END AS decision
FROM scores
ORDER BY sample_index;

INSERT INTO anomaly_evaluations (
    batch_id,
    sample_index,
    z_score_max,
    is_anomaly
)
SELECT
    b.batch_id,
    z.sample_index,
    z.maximum_absolute_z,
    z.is_anomaly
FROM calculate_z_scores(
    (
        SELECT batch_id
        FROM sensor_batches
        WHERE batch_name = 'LAB-2026-11-01-A'
    )
) z
CROSS JOIN sensor_batches b
WHERE b.batch_name = 'LAB-2026-11-01-A';

SELECT
    b.batch_name,
    COUNT(*) AS evaluated_samples,
    COUNT(*) FILTER (WHERE a.is_anomaly) AS anomaly_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE a.is_anomaly)
        / NULLIF(COUNT(*), 0),
        2
    ) AS anomaly_percentage
FROM anomaly_evaluations a
JOIN sensor_batches b
    ON b.batch_id = a.batch_id
GROUP BY b.batch_name;

SELECT
    s.sensor_name,
    COUNT(*) AS records,
    COUNT(*) FILTER (
        WHERE m.status = 'INVALID'
    ) AS invalid_records,
    COUNT(*) FILTER (
        WHERE m.status = 'WARNING'
    ) AS warning_records
FROM measurements m
JOIN sensors s
    ON s.sensor_id = m.sensor_id
GROUP BY s.sensor_name
ORDER BY s.sensor_name;

-- The schema stores each measurement independently while
-- measurement_matrix reconstructs the dense numerical layout
-- required for array-style analysis.
