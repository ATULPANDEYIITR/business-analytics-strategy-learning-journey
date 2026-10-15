-- PostgreSQL-compatible data-cleaning model.
-- The schema separates source observations from cleaned customer transactions.
-- Missing values are represented by NULL rather than multiple textual tokens.
-- Duplicate detection is supported through a deterministic normalized key.
-- Inconsistent categorical representations are constrained in the cleaned layer.

DROP SCHEMA IF EXISTS data_quality_demo CASCADE;
CREATE SCHEMA data_quality_demo;

SET search_path = data_quality_demo;

CREATE TYPE customer_status AS ENUM (
    'active',
    'pending',
    'inactive'
);

CREATE TABLE customer_transaction_raw (
    raw_id              BIGSERIAL PRIMARY KEY,
    customer_id         TEXT,
    name                TEXT,
    email               TEXT,
    phone               TEXT,
    city                TEXT,
    amount_text         TEXT,
    currency_text       TEXT,
    status_text         TEXT,
    signup_date_text    TEXT,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_transaction_clean (
    transaction_id      BIGSERIAL PRIMARY KEY,
    customer_id         TEXT NOT NULL,
    name                TEXT NOT NULL,
    email               TEXT,
    phone               TEXT,
    city                TEXT NOT NULL,
    amount              NUMERIC(14, 2),
    currency            CHAR(3) NOT NULL,
    status              customer_status NOT NULL,
    signup_date         DATE,
    normalized_key      TEXT NOT NULL,
    source_raw_id       BIGINT REFERENCES customer_transaction_raw(raw_id),
    cleaned_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT clean_customer_id_not_blank
        CHECK (btrim(customer_id) <> ''),

    CONSTRAINT clean_name_not_blank
        CHECK (btrim(name) <> ''),

    CONSTRAINT clean_amount_nonnegative
        CHECK (amount IS NULL OR amount >= 0),

    CONSTRAINT clean_currency_supported
        CHECK (currency IN ('INR', 'USD', 'EUR', 'GBP')),

    CONSTRAINT clean_email_format
        CHECK (
            email IS NULL
            OR email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
        ),

    CONSTRAINT clean_phone_format
        CHECK (
            phone IS NULL
            OR phone ~ '^\+91 [0-9]{5} [0-9]{5}$'
        )
);

CREATE TABLE data_quality_audit (
    audit_id            BIGSERIAL PRIMARY KEY,
    raw_id              BIGINT REFERENCES customer_transaction_raw(raw_id),
    field_name          TEXT,
    issue_type          TEXT NOT NULL,
    original_value      TEXT,
    cleaned_value       TEXT,
    action_taken        TEXT NOT NULL,
    reason              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_customer_id
    ON customer_transaction_raw(customer_id);

CREATE INDEX idx_clean_customer_id
    ON customer_transaction_clean(customer_id);

CREATE INDEX idx_clean_city_status
    ON customer_transaction_clean(city, status);

CREATE INDEX idx_clean_email
    ON customer_transaction_clean(email);

CREATE UNIQUE INDEX uq_clean_normalized_key
    ON customer_transaction_clean(normalized_key);

INSERT INTO customer_transaction_raw (
    customer_id,
    name,
    email,
    phone,
    city,
    amount_text,
    currency_text,
    status_text,
    signup_date_text
)
VALUES
(
    'C001',
    'Asha Sharma',
    'ASHA@EXAMPLE.COM',
    '+91 98765 43210',
    'Lucknow',
    '1250',
    'INR',
    'active',
    '2026-01-05'
),
(
    'C002',
    'Rahul Verma',
    'rahul@example.com',
    '9876543211',
    'Lucknow',
    '850',
    'inr',
    'Active',
    '05/01/2026'
),
(
    'C003',
    'Meera Singh',
    '',
    '+91-91234-56789',
    'Kanpur',
    NULL,
    'INR',
    'ACTIVE',
    '2026-01-08'
),
(
    'C004',
    'Arun Kumar',
    'arun@example.com',
    NULL,
    'Kanpur',
    '450',
    'INR',
    'active',
    '2026-01-09'
),
(
    'C005',
    'Neha Gupta',
    'neha@example.com',
    '+91 90000 11111',
    'Lucknow',
    '1250',
    'INR',
    'Active',
    '2026-01-10'
),
(
    'C005',
    'Neha Gupta',
    'neha@example.com',
    '+91 90000 11111',
    'Lucknow',
    '1250',
    'INR',
    'Active',
    '2026-01-10'
),
(
    'C006',
    'Ravi Patel',
    'ravi@example.com',
    '+91-98888-22222',
    'lucknow',
    '850',
    'INR',
    'active',
    '2026-01-11'
),
(
    'C007',
    'Sonia Rao',
    'sonia@example.com',
    '+91 97777 33333',
    'Kanpur',
    'N/A',
    'INR',
    'pending',
    '2026-01-12'
),
(
    'C008',
    'Vikram Das',
    'vIKRAM@EXAMPLE.COM',
    '+91 96666 44444',
    'Kanpur',
    '1,250',
    'INR',
    'active',
    '2026-01-13'
),
(
    'C009',
    'Pooja Nair',
    'pooja@example.com',
    '+91 95555 55555',
    'Lucknow',
    '1250',
    'Rs.',
    'active',
    '2026-01-14'
),
(
    'C010',
    'Dev Shah',
    'dev@example.com',
    '+91 94444 66666',
    'Lucknow',
    '900',
    'INR',
    'ACTIVE',
    NULL
);

-- Standardize missing-value markers before typed conversion.
-- NULLIF handles empty strings, while NULLIF chains handle common textual
-- representations that should not become actual business values.
CREATE VIEW normalized_source AS
SELECT
    raw_id,
    NULLIF(btrim(customer_id), '') AS customer_id,
    NULLIF(initcap(regexp_replace(btrim(name), '\s+', ' ', 'g')), '') AS name,
    NULLIF(lower(btrim(email)), '') AS email,
    NULLIF(btrim(phone), '') AS phone,

    CASE lower(btrim(city))
        WHEN 'lucknow' THEN 'Lucknow'
        WHEN 'lko' THEN 'Lucknow'
        WHEN 'kanpur' THEN 'Kanpur'
        WHEN 'knp' THEN 'Kanpur'
        ELSE initcap(btrim(city))
    END AS city,

    CASE
        WHEN amount_text IS NULL
            OR lower(btrim(amount_text)) IN
                ('', 'na', 'n/a', 'null', 'none', 'unknown', '-', '--')
            THEN NULL
        ELSE regexp_replace(
            regexp_replace(btrim(amount_text), ',', '', 'g'),
            '^(rs\.?|inr)\s*',
            '',
            'i'
        )::NUMERIC(14, 2)
    END AS amount,

    CASE upper(btrim(currency_text))
        WHEN 'RS' THEN 'INR'
        WHEN 'RS.' THEN 'INR'
        WHEN '₹' THEN 'INR'
        WHEN 'RUPEE' THEN 'INR'
        WHEN 'RUPEES' THEN 'INR'
        ELSE upper(btrim(currency_text))
    END AS currency,

    CASE lower(btrim(status_text))
        WHEN 'active' THEN 'active'::customer_status
        WHEN 'act' THEN 'active'::customer_status
        WHEN 'pending' THEN 'pending'::customer_status
        WHEN 'pend' THEN 'pending'::customer_status
        WHEN 'inactive' THEN 'inactive'::customer_status
        WHEN 'in-active' THEN 'inactive'::customer_status
        ELSE NULL
    END AS status,

    CASE
        WHEN signup_date_text IS NULL
            OR btrim(signup_date_text) = ''
            THEN NULL
        WHEN signup_date_text ~ '^\d{4}-\d{2}-\d{2}$'
            THEN signup_date_text::DATE
        WHEN signup_date_text ~ '^\d{2}/\d{2}/\d{4}$'
            THEN to_date(signup_date_text, 'DD/MM/YYYY')
        ELSE NULL
    END AS signup_date
FROM customer_transaction_raw;

-- Audit representations that were explicitly recognized as missing.
INSERT INTO data_quality_audit (
    raw_id,
    field_name,
    issue_type,
    original_value,
    cleaned_value,
    action_taken,
    reason
)
SELECT
    raw_id,
    'email',
    'missing_value',
    email,
    NULL,
    'standardized',
    'Empty email was converted to SQL NULL'
FROM customer_transaction_raw
WHERE email IS NULL OR btrim(email) = '';

INSERT INTO data_quality_audit (
    raw_id,
    field_name,
    issue_type,
    original_value,
    cleaned_value,
    action_taken,
    reason
)
SELECT
    raw_id,
    'amount',
    'missing_value',
    amount_text,
    NULL,
    'standardized',
    'Recognized missing amount token'
FROM customer_transaction_raw
WHERE amount_text IS NULL
   OR lower(btrim(amount_text))
      IN ('', 'na', 'n/a', 'null', 'none', 'unknown', '-', '--');

-- Detect source duplicates after normalization rather than relying on
-- textual equality. This is essential because inconsistent formatting can
-- otherwise hide duplicates.
WITH duplicate_groups AS (
    SELECT
        raw_id,
        customer_id,
        md5(
            concat_ws(
                '|',
                customer_id,
                name,
                email,
                phone,
                city,
                amount,
                currency,
                status,
                signup_date
            )
        ) AS duplicate_key,
        row_number() OVER (
            PARTITION BY
                customer_id,
                name,
                email,
                phone,
                city,
                amount,
                currency,
                status,
                signup_date
            ORDER BY raw_id
        ) AS occurrence_number
    FROM normalized_source
)
INSERT INTO data_quality_audit (
    raw_id,
    field_name,
    issue_type,
    original_value,
    cleaned_value,
    action_taken,
    reason
)
SELECT
    raw_id,
    '__record__',
    'duplicate',
    duplicate_key,
    NULL,
    'removed',
    'Normalized record key occurred more than once'
FROM duplicate_groups
WHERE occurrence_number > 1;

-- Populate the clean table while retaining the first occurrence of each
-- normalized business record.
INSERT INTO customer_transaction_clean (
    customer_id,
    name,
    email,
    phone,
    city,
    amount,
    currency,
    status,
    signup_date,
    normalized_key,
    source_raw_id
)
SELECT
    customer_id,
    name,
    email,

    CASE
        WHEN phone IS NULL THEN NULL
        WHEN regexp_replace(phone, '\D', '', 'g') ~ '^91\d{10}$'
            THEN '+91 '
                 || substring(regexp_replace(phone, '\D', '', 'g') FROM 3 FOR 5)
                 || ' '
                 || substring(regexp_replace(phone, '\D', '', 'g') FROM 8 FOR 5)
        WHEN regexp_replace(phone, '\D', '', 'g') ~ '^\d{10}$'
            THEN '+91 '
                 || substring(regexp_replace(phone, '\D', '', 'g') FROM 1 FOR 5)
                 || ' '
                 || substring(regexp_replace(phone, '\D', '', 'g') FROM 6 FOR 5)
        ELSE NULL
    END AS phone,

    city,

    amount,

    currency,

    status,

    signup_date,

    md5(
        concat_ws(
            '|',
            customer_id,
            name,
            email,
            CASE
                WHEN phone IS NULL THEN NULL
                WHEN regexp_replace(phone, '\D', '', 'g') ~ '^91\d{10}$'
                    THEN '+91 '
                         || substring(regexp_replace(phone, '\D', '', 'g') FROM 3 FOR 5)
                         || ' '
                         || substring(regexp_replace(phone, '\D', '', 'g') FROM 8 FOR 5)
                WHEN regexp_replace(phone, '\D', '', 'g') ~ '^\d{10}$'
                    THEN '+91 '
                         || substring(regexp_replace(phone, '\D', '', 'g') FROM 1 FOR 5)
                         || ' '
                         || substring(regexp_replace(phone, '\D', '', 'g') FROM 6 FOR 5)
                ELSE NULL
            END,
            city,
            amount,
            currency,
            status,
            signup_date
        )
    ) AS normalized_key,

    raw_id
FROM (
    SELECT
        normalized_source.*,
        row_number() OVER (
            PARTITION BY
                customer_id,
                name,
                email,
                phone,
                city,
                amount,
                currency,
                status,
                signup_date
            ORDER BY raw_id
        ) AS occurrence_number
    FROM normalized_source
) AS deduplicated
WHERE occurrence_number = 1;

-- Missing transaction amounts can be imputed only where a documented rule
-- exists. This example uses the median amount within the same city.
WITH city_medians AS (
    SELECT
        city,
        percentile_cont(0.5)
            WITHIN GROUP (ORDER BY amount) AS median_amount
    FROM customer_transaction_clean
    WHERE amount IS NOT NULL
    GROUP BY city
)
UPDATE customer_transaction_clean c
SET amount = m.median_amount
FROM city_medians m
WHERE c.city = m.city
  AND c.amount IS NULL;

INSERT INTO data_quality_audit (
    field_name,
    issue_type,
    original_value,
    cleaned_value,
    action_taken,
    reason
)
SELECT
    'amount',
    'missing_value',
    NULL,
    amount::TEXT,
    'imputed',
    'City-level median applied'
FROM customer_transaction_clean
WHERE amount IS NOT NULL
  AND source_raw_id IN (
      SELECT raw_id
      FROM customer_transaction_raw
      WHERE amount_text IS NULL
         OR lower(btrim(amount_text))
            IN ('', 'na', 'n/a', 'null', 'none', 'unknown', '-', '--')
  );

-- Identify inconsistent source representations that were normalized.
SELECT
    raw_id,
    city AS normalized_city,
    CASE
        WHEN lower(btrim(r.city)) <> lower(btrim(n.city))
            THEN 'city representation changed'
        ELSE NULL
    END AS city_change,
    r.currency_text AS original_currency,
    n.currency AS normalized_currency,
    r.status_text AS original_status,
    n.status AS normalized_status
FROM customer_transaction_raw r
JOIN normalized_source n
    ON n.raw_id = r.raw_id
WHERE lower(btrim(r.city)) <> lower(btrim(n.city))
   OR upper(btrim(r.currency_text)) <> n.currency
   OR lower(btrim(r.status_text)) <> n.status::TEXT;

-- Completeness profile: missingness is measured per business field rather
-- than hiding all missingness behind a single aggregate score.
SELECT
    count(*) AS total_rows,
    count(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_ids,
    count(*) FILTER (WHERE name IS NULL) AS missing_names,
    count(*) FILTER (WHERE email IS NULL) AS missing_emails,
    count(*) FILTER (WHERE phone IS NULL) AS missing_phones,
    count(*) FILTER (WHERE amount IS NULL) AS missing_amounts,
    count(*) FILTER (WHERE signup_date IS NULL) AS missing_signup_dates
FROM customer_transaction_clean;

-- Duplicate check on the final table. The unique index should make this
-- return zero rows.
SELECT
    normalized_key,
    count(*) AS occurrences
FROM customer_transaction_clean
GROUP BY normalized_key
HAVING count(*) > 1;

-- Operational query: compare cleaned transaction behavior by city.
SELECT
    city,
    count(*) AS transactions,
    count(*) FILTER (WHERE amount IS NULL) AS amount_still_missing,
    round(avg(amount), 2) AS average_amount,
    round(sum(amount), 2) AS total_amount
FROM customer_transaction_clean
GROUP BY city
ORDER BY city;

-- Validation query for values that should never survive cleaning.
SELECT *
FROM customer_transaction_clean
WHERE amount < 0
   OR currency NOT IN ('INR', 'USD', 'EUR', 'GBP')
   OR status NOT IN ('active', 'pending', 'inactive'::customer_status);

-- Transactional integrity example. A production pipeline can load a batch
-- inside a transaction so a failed constraint does not leave a partial
-- cleaned dataset.
BEGIN;

INSERT INTO customer_transaction_clean (
    customer_id,
    name,
    email,
    phone,
    city,
    amount,
    currency,
    status,
    signup_date,
    normalized_key
)
VALUES (
    'C011',
    'Test Customer',
    'test@example.com',
    '+91 90000 77777',
    'Lucknow',
    700.00,
    'INR',
    'pending',
    '2026-02-01',
    md5('C011|Test Customer|test@example.com|+91 90000 77777|Lucknow|700|INR|pending|2026-02-01')
)
ON CONFLICT (normalized_key) DO NOTHING;

COMMIT;

-- Final quality report combines completeness, duplicate prevention, and
-- invalid-state checks without treating them as the same quality problem.
SELECT
    (SELECT count(*) FROM customer_transaction_clean) AS cleaned_rows,
    (SELECT count(*) FROM customer_transaction_clean
        WHERE amount IS NULL) AS rows_with_missing_amount,
    (SELECT count(*) FROM data_quality_audit
        WHERE issue_type = 'duplicate') AS duplicate_rows_removed,
    (SELECT count(*) FROM data_quality_audit
        WHERE issue_type = 'missing_value') AS missing_value_events,
    (SELECT count(*) FROM data_quality_audit
        WHERE issue_type = 'inconsistent_representation') AS inconsistency_events;
