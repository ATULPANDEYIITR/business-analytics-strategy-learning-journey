-- PostgreSQL-compatible Data Quality Model
--
-- The schema separates the four quality dimensions:
-- accuracy      -> trusted reference data
-- completeness  -> required values and NULL prevention
-- consistency   -> relationships between related values and records
-- validity      -> domains, formats, ranges, and state rules
--
-- The database layer deliberately enforces rules that should not depend
-- exclusively on application code.

DROP SCHEMA IF EXISTS data_quality_demo CASCADE;
CREATE SCHEMA data_quality_demo;
SET search_path TO data_quality_demo;

CREATE TYPE customer_status AS ENUM (
    'active',
    'inactive',
    'pending'
);

CREATE TABLE country_currency_reference (
    country_code CHAR(2) PRIMARY KEY,
    currency_code CHAR(3) NOT NULL UNIQUE
);

INSERT INTO country_currency_reference(country_code, currency_code)
VALUES
    ('IN', 'INR'),
    ('US', 'USD'),
    ('GB', 'GBP'),
    ('DE', 'EUR'),
    ('FR', 'EUR'),
    ('JP', 'JPY'),
    ('SG', 'SGD'),
    ('AU', 'AUD');

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(320) NOT NULL,
    country_code CHAR(2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    status customer_status NOT NULL,
    signup_date DATE NOT NULL,
    credit_limit NUMERIC(15,2) NOT NULL DEFAULT 0,

    CONSTRAINT customer_name_not_blank
        CHECK (length(btrim(customer_name)) > 0),

    CONSTRAINT customer_email_not_blank
        CHECK (length(btrim(email)) > 0),

    CONSTRAINT customer_credit_nonnegative
        CHECK (credit_limit >= 0),

    CONSTRAINT customer_email_shape
        CHECK (
            email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
        ),

    CONSTRAINT customer_signup_not_future
        CHECK (signup_date <= CURRENT_DATE),

    CONSTRAINT customer_country_fk
        FOREIGN KEY (country_code)
        REFERENCES country_currency_reference(country_code)
);

-- A separate unique index prevents duplicate customer emails and also
-- gives the database an efficient lookup structure.
CREATE UNIQUE INDEX ux_customers_email
    ON customers (lower(email));

CREATE INDEX ix_customers_country
    ON customers (country_code);

CREATE INDEX ix_customers_status
    ON customers (status);

CREATE TABLE verified_customer_facts (
    customer_id VARCHAR(20) PRIMARY KEY,
    verified_email VARCHAR(320) NOT NULL,
    verified_country CHAR(2) NOT NULL,
    verified_currency CHAR(3) NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT verified_customer_country_fk
        FOREIGN KEY (verified_country)
        REFERENCES country_currency_reference(country_code)
);

-- Reference facts support accuracy testing. A database constraint alone
-- cannot prove that a value represents reality; an independently trusted
-- source is required for that dimension.
INSERT INTO verified_customer_facts(
    customer_id,
    verified_email,
    verified_country,
    verified_currency
)
VALUES
    ('C1001', 'atul@example.com', 'IN', 'INR'),
    ('C1002', 'maria@example.com', 'DE', 'EUR');

INSERT INTO customers(
    customer_id,
    customer_name,
    email,
    country_code,
    currency_code,
    status,
    signup_date,
    credit_limit
)
VALUES
    (
        'C1001',
        'Atul Pandey',
        'atul@example.com',
        'IN',
        'INR',
        'active',
        '2026-01-15',
        500000
    ),
    (
        'C1002',
        'Maria Silva',
        'maria.changed@example.com',
        'DE',
        'EUR',
        'active',
        '2026-02-12',
        75000
    ),
    (
        'C1003',
        'Ravi Kumar',
        'ravi@example.com',
        'IN',
        'INR',
        'pending',
        '2026-03-10',
        25000
    ),
    (
        'C1005',
        'John Smith',
        'john@example.com',
        'US',
        'EUR',
        'inactive',
        '2026-02-01',
        1000
    ),
    (
        'C1006',
        'Duplicate User',
        'duplicate@example.com',
        'IN',
        'INR',
        'active',
        '2026-04-01',
        30000
    );

-- The following insert demonstrates a database-enforced validity failure.
-- It is intentionally commented so that the complete script remains
-- executable from beginning to end.
--
-- INSERT INTO customers(
--     customer_id, customer_name, email, country_code, currency_code,
--     status, signup_date, credit_limit
-- )
-- VALUES (
--     'INVALID-1', 'Bad Customer', 'bad@example.com', 'IN', 'INR',
--     'active', '2027-01-01', -500
-- );

-- -------------------------------------------------------------------------
-- Consistency checks
-- -------------------------------------------------------------------------

CREATE VIEW customer_consistency_issues AS
SELECT
    c.customer_id,
    c.country_code,
    c.currency_code,
    r.currency_code AS expected_currency,
    'Country and currency disagree' AS issue
FROM customers c
JOIN country_currency_reference r
    ON r.country_code = c.country_code
WHERE c.currency_code <> r.currency_code

UNION ALL

SELECT
    c.customer_id,
    c.country_code,
    c.currency_code,
    r.currency_code AS expected_currency,
    'Inactive customer retains positive credit limit' AS issue
FROM customers c
JOIN country_currency_reference r
    ON r.country_code = c.country_code
WHERE c.status = 'inactive'
  AND c.credit_limit > 0;

-- -------------------------------------------------------------------------
-- Accuracy checks
-- -------------------------------------------------------------------------

CREATE VIEW customer_accuracy_issues AS
SELECT
    c.customer_id,
    'email' AS field_name,
    c.email AS actual_value,
    v.verified_email AS expected_value
FROM customers c
JOIN verified_customer_facts v
    ON v.customer_id = c.customer_id
WHERE lower(c.email) <> lower(v.verified_email)

UNION ALL

SELECT
    c.customer_id,
    'country_code',
    c.country_code,
    v.verified_country
FROM customers c
JOIN verified_customer_facts v
    ON v.customer_id = c.customer_id
WHERE c.country_code <> v.verified_country

UNION ALL

SELECT
    c.customer_id,
    'currency_code',
    c.currency_code,
    v.verified_currency
FROM customers c
JOIN verified_customer_facts v
    ON v.customer_id = c.customer_id
WHERE c.currency_code <> v.verified_currency;

-- -------------------------------------------------------------------------
-- Completeness profiling
-- -------------------------------------------------------------------------

CREATE VIEW customer_completeness_profile AS
SELECT
    COUNT(*) AS total_records,
    COUNT(customer_id) AS customer_id_present,
    COUNT(customer_name) AS name_present,
    COUNT(email) AS email_present,
    COUNT(country_code) AS country_present,
    COUNT(currency_code) AS currency_present,
    COUNT(status) AS status_present,
    COUNT(signup_date) AS signup_date_present,
    COUNT(credit_limit) AS credit_limit_present
FROM customers;

-- -------------------------------------------------------------------------
-- Validity profiling
-- -------------------------------------------------------------------------

CREATE VIEW customer_validity_profile AS
SELECT
    customer_id,
    email,
    signup_date,
    credit_limit,
    (
        email ~* '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
    ) AS email_is_valid,
    (
        signup_date <= CURRENT_DATE
    ) AS signup_date_is_valid,
    (
        credit_limit >= 0
    ) AS credit_limit_is_valid
FROM customers;

-- -------------------------------------------------------------------------
-- Unified quality score
--
-- The score counts affected records per dimension. It is intended as an
-- operational metric rather than a universal statistical definition.
-- -------------------------------------------------------------------------

WITH accuracy AS (
    SELECT COUNT(DISTINCT customer_id)::numeric AS affected
    FROM customer_accuracy_issues
),
consistency AS (
    SELECT COUNT(DISTINCT customer_id)::numeric AS affected
    FROM customer_consistency_issues
),
validity AS (
    SELECT COUNT(*)::numeric AS affected
    FROM customer_validity_profile
    WHERE NOT (
        email_is_valid
        AND signup_date_is_valid
        AND credit_limit_is_valid
    )
),
population AS (
    SELECT COUNT(*)::numeric AS total
    FROM customers
)
SELECT
    ROUND(
        100 * (1 - accuracy.affected / NULLIF(population.total, 0)),
        2
    ) AS accuracy_score,
    ROUND(
        100 * (1 - consistency.affected / NULLIF(population.total, 0)),
        2
    ) AS consistency_score,
    ROUND(
        100 * (1 - validity.affected / NULLIF(population.total, 0)),
        2
    ) AS validity_score
FROM accuracy, consistency, validity, population;

-- -------------------------------------------------------------------------
-- Transactional remediation example
--
-- Normalization is safe when it preserves meaning. The transaction permits
-- rollback if the proposed update violates an integrity rule.
-- -------------------------------------------------------------------------

BEGIN;

UPDATE customers
SET
    email = lower(btrim(email)),
    country_code = upper(btrim(country_code)),
    currency_code = upper(btrim(currency_code));

-- Review the affected rows before committing in a production workflow.
SELECT
    customer_id,
    email,
    country_code,
    currency_code
FROM customers
ORDER BY customer_id;

COMMIT;

-- -------------------------------------------------------------------------
-- A consolidated issue report
-- -------------------------------------------------------------------------

SELECT
    customer_id,
    'accuracy' AS dimension,
    field_name,
    actual_value,
    expected_value
FROM customer_accuracy_issues

UNION ALL

SELECT
    customer_id,
    'consistency' AS dimension,
    'currency_or_credit_policy' AS field_name,
    currency_code AS actual_value,
    expected_currency AS expected_value
FROM customer_consistency_issues

ORDER BY customer_id, dimension;

-- -------------------------------------------------------------------------
-- Data quality governance query
-- -------------------------------------------------------------------------

SELECT
    c.customer_id,
    c.customer_name,
    CASE
        WHEN a.customer_id IS NOT NULL THEN 'accuracy_issue'
        WHEN ci.customer_id IS NOT NULL THEN 'consistency_issue'
        WHEN vp.email_is_valid = FALSE
          OR vp.signup_date_is_valid = FALSE
          OR vp.credit_limit_is_valid = FALSE
            THEN 'validity_issue'
        ELSE 'no_detected_issue'
    END AS quality_state
FROM customers c
LEFT JOIN (
    SELECT DISTINCT customer_id
    FROM customer_accuracy_issues
) a
    ON a.customer_id = c.customer_id
LEFT JOIN (
    SELECT DISTINCT customer_id
    FROM customer_consistency_issues
) ci
    ON ci.customer_id = c.customer_id
JOIN customer_validity_profile vp
    ON vp.customer_id = c.customer_id
ORDER BY c.customer_id;
