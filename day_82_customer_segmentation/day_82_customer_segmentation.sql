-- ============================================================
-- CUSTOMER SEGMENTATION AND ANALYTICS
-- PostgreSQL relational implementation
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS customer_analytics;

SET search_path TO customer_analytics, public;

-- Reset the demonstration schema for repeatable execution.
DROP VIEW IF EXISTS campaign_eligibility_report CASCADE;
DROP VIEW IF EXISTS customer_segmentation_report CASCADE;
DROP VIEW IF EXISTS segment_distribution CASCADE;

DROP TABLE IF EXISTS campaign_assignments CASCADE;
DROP TABLE IF EXISTS segmentation_results CASCADE;
DROP TABLE IF EXISTS segmentation_runs CASCADE;
DROP TABLE IF EXISTS segmentation_policies CASCADE;
DROP TABLE IF EXISTS behavioral_events CASCADE;
DROP TABLE IF EXISTS purchases CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

DROP TYPE IF EXISTS customer_status CASCADE;
DROP TYPE IF EXISTS campaign_status CASCADE;

CREATE TYPE customer_status AS ENUM (
    'active',
    'inactive',
    'suspended'
);

CREATE TYPE campaign_status AS ENUM (
    'eligible',
    'ineligible',
    'assigned',
    'completed'
);

-- ============================================================
-- 1. CUSTOMER MASTER
-- ============================================================

CREATE TABLE customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    external_customer_code VARCHAR(50) NOT NULL UNIQUE,

    full_name VARCHAR(150) NOT NULL,

    date_of_birth DATE NOT NULL,

    gender VARCHAR(30),

    region VARCHAR(100) NOT NULL,

    city VARCHAR(100),

    occupation VARCHAR(100),

    annual_income NUMERIC(14,2) NOT NULL DEFAULT 0,

    account_status customer_status NOT NULL DEFAULT 'active',

    marketing_consent BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_customer_name
        CHECK (length(trim(full_name)) > 0),

    CONSTRAINT valid_income
        CHECK (annual_income >= 0),

    CONSTRAINT valid_birth_date
        CHECK (
            date_of_birth <= CURRENT_DATE
            AND date_of_birth >= DATE '1900-01-01'
        ),

    CONSTRAINT valid_gender
        CHECK (
            gender IS NULL
            OR gender IN (
                'female',
                'male',
                'non_binary',
                'undisclosed'
            )
        )
);

CREATE INDEX idx_customers_region
    ON customers(region);

CREATE INDEX idx_customers_income
    ON customers(annual_income DESC);

CREATE INDEX idx_customers_status
    ON customers(account_status);

CREATE INDEX idx_customers_active_region
    ON customers(region, customer_id)
    WHERE account_status = 'active';

-- ============================================================
-- 2. PURCHASE TRANSACTIONS
-- ============================================================

CREATE TABLE purchases (
    purchase_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    transaction_reference VARCHAR(100) NOT NULL UNIQUE,

    purchase_date TIMESTAMPTZ NOT NULL,

    product_category VARCHAR(100) NOT NULL,

    quantity INTEGER NOT NULL,

    unit_price NUMERIC(14,2) NOT NULL,

    discount_amount NUMERIC(14,2) NOT NULL DEFAULT 0,

    net_amount NUMERIC(14,2)
        GENERATED ALWAYS AS (
            quantity * unit_price - discount_amount
        ) STORED,

    payment_status VARCHAR(20) NOT NULL DEFAULT 'completed',

    CONSTRAINT valid_quantity
        CHECK (quantity > 0),

    CONSTRAINT valid_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT valid_discount
        CHECK (
            discount_amount >= 0
            AND discount_amount <= quantity * unit_price
        ),

    CONSTRAINT valid_payment_status
        CHECK (
            payment_status IN (
                'completed',
                'refunded',
                'pending'
            )
        )
);

CREATE INDEX idx_purchases_customer_date
    ON purchases(customer_id, purchase_date DESC);

CREATE INDEX idx_purchases_completed
    ON purchases(customer_id, purchase_date)
    WHERE payment_status = 'completed';

CREATE INDEX idx_purchases_category
    ON purchases(product_category);

-- ============================================================
-- 3. BEHAVIORAL EVENTS
-- ============================================================

CREATE TABLE behavioral_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    event_type VARCHAR(40) NOT NULL,

    event_timestamp TIMESTAMPTZ NOT NULL,

    product_category VARCHAR(100),

    session_reference VARCHAR(100),

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT valid_event_type
        CHECK (
            event_type IN (
                'website_visit',
                'product_view',
                'cart_addition',
                'cart_abandonment',
                'email_open',
                'email_click',
                'search',
                'support_interaction'
            )
        ),

    CONSTRAINT valid_event_metadata
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX idx_behavior_customer_timestamp
    ON behavioral_events(customer_id, event_timestamp DESC);

CREATE INDEX idx_behavior_event_type
    ON behavioral_events(event_type, event_timestamp DESC);

CREATE INDEX idx_behavior_metadata
    ON behavioral_events USING GIN(metadata);

-- ============================================================
-- 4. SEGMENTATION POLICIES
-- ============================================================

CREATE TABLE segmentation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(100) NOT NULL,

    version INTEGER NOT NULL,

    high_value_threshold NUMERIC(14,2) NOT NULL,

    medium_value_threshold NUMERIC(14,2) NOT NULL,

    high_income_threshold NUMERIC(14,2) NOT NULL,

    recent_purchase_days INTEGER NOT NULL,

    dormant_purchase_days INTEGER NOT NULL,

    frequent_purchase_threshold INTEGER NOT NULL,

    engaged_session_threshold INTEGER NOT NULL,

    engaged_email_threshold INTEGER NOT NULL,

    effective_from TIMESTAMPTZ NOT NULL,

    effective_until TIMESTAMPTZ,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_policy_version
        UNIQUE(policy_name, version),

    CONSTRAINT valid_value_thresholds
        CHECK (
            high_value_threshold > medium_value_threshold
            AND medium_value_threshold >= 0
        ),

    CONSTRAINT valid_income_threshold
        CHECK (high_income_threshold > 0),

    CONSTRAINT valid_recency_thresholds
        CHECK (
            recent_purchase_days > 0
            AND dormant_purchase_days > recent_purchase_days
        ),

    CONSTRAINT valid_frequency_threshold
        CHECK (frequent_purchase_threshold > 0),

    CONSTRAINT valid_engagement_thresholds
        CHECK (
            engaged_session_threshold > 0
            AND engaged_email_threshold > 0
        ),

    CONSTRAINT valid_policy_period
        CHECK (
            effective_until IS NULL
            OR effective_until > effective_from
        )
);

CREATE UNIQUE INDEX idx_one_active_policy
    ON segmentation_policies(policy_name)
    WHERE is_active = TRUE;

-- ============================================================
-- 5. SEGMENTATION RUNS
-- ============================================================

CREATE TABLE segmentation_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_id BIGINT NOT NULL
        REFERENCES segmentation_policies(policy_id),

    observation_date DATE NOT NULL,

    run_status VARCHAR(20) NOT NULL DEFAULT 'completed',

    customers_processed INTEGER NOT NULL DEFAULT 0,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_run_status
        CHECK (
            run_status IN (
                'running',
                'completed',
                'failed'
            )
        ),

    CONSTRAINT valid_processed_count
        CHECK (customers_processed >= 0)
);

CREATE INDEX idx_segmentation_runs_policy
    ON segmentation_runs(policy_id, observation_date DESC);

-- ============================================================
-- 6. SEGMENTATION RESULTS
-- ============================================================

CREATE TABLE segmentation_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES segmentation_runs(run_id),

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    demographic_segment VARCHAR(100) NOT NULL,

    behavioral_segment VARCHAR(50) NOT NULL,

    value_segment VARCHAR(30) NOT NULL,

    recency_days INTEGER NOT NULL,

    purchase_frequency INTEGER NOT NULL,

    monetary_value NUMERIC(14,2) NOT NULL,

    average_order_value NUMERIC(14,2) NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT one_result_per_customer_per_run
        UNIQUE(run_id, customer_id),

    CONSTRAINT valid_recency
        CHECK (recency_days >= 0),

    CONSTRAINT valid_purchase_frequency
        CHECK (purchase_frequency >= 0),

    CONSTRAINT valid_monetary_value
        CHECK (monetary_value >= 0),

    CONSTRAINT valid_average_order_value
        CHECK (average_order_value >= 0),

    CONSTRAINT valid_behavioral_segment
        CHECK (
            behavioral_segment IN (
                'loyal_active',
                'recent_customer',
                'digitally_engaged',
                'repeat_customer',
                'occasional_customer',
                'dormant'
            )
        ),

    CONSTRAINT valid_value_segment
        CHECK (
            value_segment IN (
                'high_value',
                'medium_value',
                'low_value'
            )
        )
);

CREATE INDEX idx_results_value
    ON segmentation_results(run_id, value_segment);

CREATE INDEX idx_results_behavior
    ON segmentation_results(run_id, behavioral_segment);

CREATE INDEX idx_results_demographic
    ON segmentation_results(run_id, demographic_segment);

CREATE INDEX idx_results_customer
    ON segmentation_results(customer_id, evaluated_at DESC);

-- ============================================================
-- 7. CAMPAIGN ASSIGNMENTS
-- ============================================================

CREATE TABLE campaign_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    result_id BIGINT NOT NULL
        REFERENCES segmentation_results(result_id),

    campaign_name VARCHAR(100) NOT NULL,

    eligibility_status campaign_status NOT NULL,

    eligibility_reason TEXT NOT NULL,

    assigned_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_campaign_dates
        CHECK (
            completed_at IS NULL
            OR assigned_at IS NOT NULL
            AND completed_at >= assigned_at
        ),

    CONSTRAINT valid_assignment_state
        CHECK (
            eligibility_status <> 'assigned'
            OR assigned_at IS NOT NULL
        )
);

CREATE INDEX idx_campaign_status
    ON campaign_assignments(eligibility_status);

CREATE INDEX idx_campaign_name
    ON campaign_assignments(campaign_name);

-- ============================================================
-- 8. UPDATE TIMESTAMP TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_customer_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_customer_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_customer_timestamp();

-- ============================================================
-- 9. PURCHASE VALIDATION TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION validate_purchase_customer()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    customer_state customer_status;
BEGIN
    SELECT account_status
    INTO customer_state
    FROM customers
    WHERE customer_id = NEW.customer_id
    FOR KEY SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Customer % does not exist', NEW.customer_id;
    END IF;

    IF customer_state = 'suspended' THEN
        RAISE EXCEPTION
            'Purchases are not accepted for suspended customers';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_purchase
BEFORE INSERT OR UPDATE ON purchases
FOR EACH ROW
EXECUTE FUNCTION validate_purchase_customer();

-- ============================================================
-- 10. DEMOGRAPHIC CLASSIFICATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION demographic_segment(
    p_birth_date DATE,
    p_income NUMERIC,
    p_high_income_threshold NUMERIC
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    customer_age INTEGER;
    age_group TEXT;
    income_group TEXT;
BEGIN
    IF p_birth_date IS NULL
       OR p_birth_date > CURRENT_DATE
       OR p_income < 0
       OR p_high_income_threshold <= 0
    THEN
        RAISE EXCEPTION 'Invalid demographic input';
    END IF;

    customer_age :=
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, p_birth_date))::INTEGER;

    age_group := CASE
        WHEN customer_age < 30 THEN 'young_adult'
        WHEN customer_age < 45 THEN 'adult'
        WHEN customer_age < 60 THEN 'middle_aged'
        ELSE 'senior'
    END;

    income_group := CASE
        WHEN p_income >= p_high_income_threshold
            THEN 'high_income'
        WHEN p_income >= p_high_income_threshold / 3
            THEN 'middle_income'
        ELSE 'lower_income'
    END;

    RETURN age_group || '_' || income_group;
END;
$$;

-- ============================================================
-- 11. SEGMENTATION PROCESSING PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE process_customer_segmentation(
    p_policy_id BIGINT,
    p_observation_date DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    policy_row segmentation_policies%ROWTYPE;
    new_run_id BIGINT;
    processed_count INTEGER;
BEGIN
    IF p_observation_date IS NULL
       OR p_observation_date > CURRENT_DATE
    THEN
        RAISE EXCEPTION 'Invalid observation date';
    END IF;

    SELECT *
    INTO STRICT policy_row
    FROM segmentation_policies
    WHERE policy_id = p_policy_id
      AND is_active = TRUE
      AND effective_from <=
          (p_observation_date::TIMESTAMP AT TIME ZONE 'UTC')
      AND (
          effective_until IS NULL
          OR effective_until >
              (p_observation_date::TIMESTAMP AT TIME ZONE 'UTC')
      );

    INSERT INTO segmentation_runs (
        policy_id,
        observation_date,
        run_status
    )
    VALUES (
        p_policy_id,
        p_observation_date,
        'running'
    )
    RETURNING run_id INTO new_run_id;

    WITH purchase_metrics AS (
        SELECT
            c.customer_id,

            COUNT(p.purchase_id) FILTER (
                WHERE p.payment_status = 'completed'
            )::INTEGER AS frequency,

            COALESCE(
                SUM(p.net_amount) FILTER (
                    WHERE p.payment_status = 'completed'
                ),
                0
            )::NUMERIC(14,2) AS monetary,

            MAX(p.purchase_date) FILTER (
                WHERE p.payment_status = 'completed'
            )::DATE AS last_purchase

        FROM customers c

        LEFT JOIN purchases p
            ON p.customer_id = c.customer_id
           AND p.purchase_date <
               (p_observation_date + 1)::TIMESTAMP

        WHERE c.account_status <> 'suspended'

        GROUP BY c.customer_id
    ),

    behavioral_metrics AS (
        SELECT
            customer_id,

            COUNT(*) FILTER (
                WHERE event_type = 'website_visit'
            )::INTEGER AS sessions,

            COUNT(*) FILTER (
                WHERE event_type = 'email_click'
            )::INTEGER AS email_clicks,

            COUNT(*) FILTER (
                WHERE event_type = 'cart_abandonment'
            )::INTEGER AS cart_abandonments

        FROM behavioral_events

        WHERE event_timestamp >=
            (p_observation_date - INTERVAL '365 days')

          AND event_timestamp <
            (p_observation_date + 1)::TIMESTAMP

        GROUP BY customer_id
    ),

    customer_metrics AS (
        SELECT
            c.customer_id,

            demographic_segment(
                c.date_of_birth,
                c.annual_income,
                policy_row.high_income_threshold
            ) AS demographic,

            COALESCE(
                (p_observation_date - pm.last_purchase),
                policy_row.dormant_purchase_days + 1
            )::INTEGER AS recency,

            pm.frequency,

            pm.monetary,

            COALESCE(bm.sessions, 0) AS sessions,

            COALESCE(bm.email_clicks, 0) AS email_clicks

        FROM customers c

        JOIN purchase_metrics pm
            ON pm.customer_id = c.customer_id

        LEFT JOIN behavioral_metrics bm
            ON bm.customer_id = c.customer_id

        WHERE c.account_status <> 'suspended'
    ),

    classified AS (
        SELECT
            customer_id,
            demographic,
            recency,
            frequency,
            monetary,

            CASE
                WHEN recency > policy_row.dormant_purchase_days
                    THEN 'dormant'

                WHEN recency <= policy_row.recent_purchase_days
                 AND frequency >=
                    policy_row.frequent_purchase_threshold
                    THEN 'loyal_active'

                WHEN recency <= policy_row.recent_purchase_days
                    THEN 'recent_customer'

                WHEN sessions >=
                    policy_row.engaged_session_threshold
                  OR email_clicks >=
                    policy_row.engaged_email_threshold
                    THEN 'digitally_engaged'

                WHEN frequency >=
                    policy_row.frequent_purchase_threshold
                    THEN 'repeat_customer'

                ELSE 'occasional_customer'
            END AS behavioral,

            CASE
                WHEN monetary >= policy_row.high_value_threshold
                    THEN 'high_value'

                WHEN monetary >= policy_row.medium_value_threshold
                    THEN 'medium_value'

                ELSE 'low_value'
            END AS value_segment

        FROM customer_metrics
    )

    INSERT INTO segmentation_results (
        run_id,
        customer_id,
        demographic_segment,
        behavioral_segment,
        value_segment,
        recency_days,
        purchase_frequency,
        monetary_value,
        average_order_value
    )
    SELECT
        new_run_id,
        customer_id,
        demographic,
        behavioral,
        value_segment,
        recency,
        frequency,
        monetary,

        CASE
            WHEN frequency > 0
                THEN monetary / frequency
            ELSE 0
        END

    FROM classified;

    GET DIAGNOSTICS processed_count = ROW_COUNT;

    UPDATE segmentation_runs
    SET
        run_status = 'completed',
        customers_processed = processed_count,
        completed_at = CURRENT_TIMESTAMP
    WHERE run_id = new_run_id;

    RAISE NOTICE
        'Segmentation run % completed for % customers',
        new_run_id,
        processed_count;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION
            'Segmentation processing failed: %',
            SQLERRM;
END;
$$;

-- ============================================================
-- 12. CAMPAIGN ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION campaign_eligibility(
    p_result_id BIGINT
)
RETURNS TABLE (
    customer_id BIGINT,
    eligible BOOLEAN,
    campaign_name TEXT,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    result_row segmentation_results%ROWTYPE;
    account_state customer_status;
    consent BOOLEAN;
BEGIN
    SELECT sr.*, c.account_status, c.marketing_consent
    INTO result_row, account_state, consent
    FROM segmentation_results sr
    JOIN customers c
      ON c.customer_id = sr.customer_id
    WHERE sr.result_id = p_result_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Segmentation result % does not exist',
            p_result_id;
    END IF;

    customer_id := result_row.customer_id;

    IF account_state <> 'active' THEN
        eligible := FALSE;
        campaign_name := NULL;
        reason := 'Customer account is not active';

    ELSIF NOT consent THEN
        eligible := FALSE;
        campaign_name := NULL;
        reason := 'Marketing consent has not been granted';

    ELSIF result_row.behavioral_segment = 'dormant' THEN
        eligible := FALSE;
        campaign_name := 'reactivation_review';
        reason := 'Requires separate reactivation eligibility review';

    ELSIF result_row.value_segment = 'high_value' THEN
        eligible := TRUE;
        campaign_name := 'premium_retention';
        reason := 'High monetary customer value';

    ELSIF result_row.behavioral_segment = 'digitally_engaged' THEN
        eligible := TRUE;
        campaign_name := 'digital_engagement';
        reason := 'High digital engagement';

    ELSE
        eligible := TRUE;
        campaign_name := 'standard_engagement';
        reason := 'Standard campaign eligibility';
    END IF;

    RETURN NEXT;
END;
$$;

-- ============================================================
-- 13. REPORTING VIEWS
-- ============================================================

CREATE OR REPLACE VIEW customer_segmentation_report AS
SELECT
    sr.result_id,
    sr.run_id,
    sr.customer_id,
    c.full_name,
    c.region,
    c.city,
    c.annual_income,
    c.account_status,
    c.marketing_consent,

    sr.demographic_segment,
    sr.behavioral_segment,
    sr.value_segment,

    sr.recency_days,
    sr.purchase_frequency,
    sr.monetary_value,
    sr.average_order_value,

    sr.evaluated_at

FROM segmentation_results sr

JOIN customers c
    ON c.customer_id = sr.customer_id;

CREATE OR REPLACE VIEW segment_distribution AS
SELECT
    run_id,
    demographic_segment,
    behavioral_segment,
    value_segment,
    COUNT(*) AS customer_count,
    SUM(monetary_value) AS segment_revenue,
    AVG(monetary_value) AS average_customer_value

FROM segmentation_results

GROUP BY
    run_id,
    demographic_segment,
    behavioral_segment,
    value_segment;

CREATE OR REPLACE VIEW campaign_eligibility_report AS
SELECT
    sr.result_id,
    sr.run_id,
    sr.customer_id,
    c.full_name,
    c.account_status,
    c.marketing_consent,
    sr.value_segment,
    sr.behavioral_segment,
    ce.eligible,
    ce.campaign_name,
    ce.reason

FROM segmentation_results sr

JOIN customers c
    ON c.customer_id = sr.customer_id

CROSS JOIN LATERAL campaign_eligibility(sr.result_id) ce;

-- ============================================================
-- 14. SAMPLE POLICY
-- ============================================================

INSERT INTO segmentation_policies (
    policy_name,
    version,
    high_value_threshold,
    medium_value_threshold,
    high_income_threshold,
    recent_purchase_days,
    dormant_purchase_days,
    frequent_purchase_threshold,
    engaged_session_threshold,
    engaged_email_threshold,
    effective_from,
    is_active
)
VALUES (
    'standard_customer_segmentation',
    1,
    100000,
    30000,
    1200000,
    30,
    180,
    10,
    20,
    10,
    '2026-01-01 00:00:00+00',
    TRUE
);

-- ============================================================
-- 15. SAMPLE CUSTOMERS
-- ============================================================

INSERT INTO customers (
    external_customer_code,
    full_name,
    date_of_birth,
    gender,
    region,
    city,
    occupation,
    annual_income,
    account_status,
    marketing_consent
)
VALUES
(
    'CUST-5001',
    'Customer A',
    CURRENT_DATE - INTERVAL '27 years',
    'undisclosed',
    'North',
    'Delhi',
    'Engineer',
    1800000,
    'active',
    TRUE
),
(
    'CUST-5002',
    'Customer B',
    CURRENT_DATE - INTERVAL '39 years',
    'undisclosed',
    'West',
    'Mumbai',
    'Manager',
    850000,
    'active',
    TRUE
),
(
    'CUST-5003',
    'Customer C',
    CURRENT_DATE - INTERVAL '55 years',
    'undisclosed',
    'North',
    'Lucknow',
    'Teacher',
    450000,
    'active',
    TRUE
),
(
    'CUST-5004',
    'Customer D',
    CURRENT_DATE - INTERVAL '65 years',
    'undisclosed',
    'West',
    'Pune',
    'Consultant',
    2200000,
    'active',
    TRUE
),
(
    'CUST-5005',
    'Customer E',
    CURRENT_DATE - INTERVAL '32 years',
    'undisclosed',
    'North',
    'Jaipur',
    'Analyst',
    700000,
    'inactive',
    FALSE
),
(
    'CUST-5006',
    'Customer F',
    CURRENT_DATE - INTERVAL '44 years',
    'undisclosed',
    'South',
    'Bengaluru',
    'Designer',
    1100000,
    'active',
    TRUE
),
(
    'CUST-5007',
    'Customer G',
    CURRENT_DATE - INTERVAL '35 years',
    'undisclosed',
    'North',
    'Lucknow',
    'Developer',
    950000,
    'active',
    FALSE
);

-- ============================================================
-- 16. SAMPLE PURCHASES
-- ============================================================

INSERT INTO purchases (
    customer_id,
    transaction_reference,
    purchase_date,
    product_category,
    quantity,
    unit_price,
    discount_amount,
    payment_status
)
SELECT
    c.customer_id,
    x.reference,
    CURRENT_DATE - x.days_ago,
    x.category,
    x.quantity,
    x.price,
    x.discount,
    'completed'
FROM customers c
JOIN (
    VALUES
    ('CUST-5001', 'TX-5001-A', 5, 'Electronics', 1, 85000, 0),
    ('CUST-5001', 'TX-5001-B', 20, 'Electronics', 1, 80000, 0),
    ('CUST-5002', 'TX-5002-A', 25, 'Fashion', 1, 35000, 0),
    ('CUST-5002', 'TX-5002-B', 80, 'Fashion', 1, 30000, 0),
    ('CUST-5003', 'TX-5003-A', 95, 'Books', 1, 18000, 0),
    ('CUST-5004', 'TX-5004-A', 12, 'Travel', 1, 145000, 0),
    ('CUST-5004', 'TX-5004-B', 50, 'Travel', 1, 100000, 0),
    ('CUST-5005', 'TX-5005-A', 250, 'Home', 1, 2500, 0),
    ('CUST-5006', 'TX-5006-A', 15, 'Electronics', 1, 92000, 0),
    ('CUST-5007', 'TX-5007-A', 210, 'Books', 1, 12000, 0)
) AS x(
    code,
    reference,
    days_ago,
    category,
    quantity,
    price,
    discount
)
    ON c.external_customer_code = x.code;

-- ============================================================
-- 17. SAMPLE BEHAVIORAL EVENTS
-- ============================================================

INSERT INTO behavioral_events (
    customer_id,
    event_type,
    event_timestamp,
    product_category,
    session_reference,
    metadata
)
SELECT
    c.customer_id,
    e.event_type,
    CURRENT_TIMESTAMP - e.days_ago * INTERVAL '1 day',
    e.category,
    e.session_reference,
    e.metadata::JSONB

FROM customers c

JOIN (
    VALUES
    ('CUST-5001', 'website_visit', 2, 'Electronics', 'S1',
        '{"source":"organic"}'),
    ('CUST-5001', 'email_click', 3, 'Electronics', 'S1',
        '{"campaign":"retention"}'),
    ('CUST-5002', 'website_visit', 10, 'Fashion', 'S2',
        '{"source":"paid"}'),
    ('CUST-5002', 'email_click', 15, 'Fashion', 'S2',
        '{"campaign":"promotion"}'),
    ('CUST-5003', 'website_visit', 80, 'Books', 'S3',
        '{"source":"direct"}'),
    ('CUST-5004', 'website_visit', 5, 'Travel', 'S4',
        '{"source":"organic"}'),
    ('CUST-5004', 'email_click', 7, 'Travel', 'S4',
        '{"campaign":"premium"}'),
    ('CUST-5006', 'website_visit', 10, 'Electronics', 'S5',
        '{"source":"direct"}'),
    ('CUST-5007', 'website_visit', 100, 'Books', 'S6',
        '{"source":"organic"}'),
    ('CUST-5007', 'cart_abandonment', 105, 'Books', 'S6',
        '{"cart_value":12000}')
) AS e(
    code,
    event_type,
    days_ago,
    category,
    session_reference,
    metadata
)
    ON c.external_customer_code = e.code;

-- ============================================================
-- 18. INVALID CASE VALIDATION
-- ============================================================

DO $$
DECLARE
    test_customer_id BIGINT;
BEGIN
    SELECT customer_id
    INTO test_customer_id
    FROM customers
    WHERE external_customer_code = 'CUST-5001';

    -- A negative purchase quantity must be rejected.
    BEGIN
        INSERT INTO purchases (
            customer_id,
            transaction_reference,
            purchase_date,
            product_category,
            quantity,
            unit_price
        )
        VALUES (
            test_customer_id,
            'INVALID-NEGATIVE-QUANTITY',
            CURRENT_TIMESTAMP,
            'Electronics',
            -1,
            500
        );

        RAISE EXCEPTION
            'Invalid negative purchase quantity was accepted';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Correctly rejected negative purchase quantity';
    END;

    -- A duplicate external customer code must be rejected.
    BEGIN
        INSERT INTO customers (
            external_customer_code,
            full_name,
            date_of_birth,
            region,
            annual_income
        )
        VALUES (
            'CUST-5001',
            'Duplicate Customer',
            DATE '1990-01-01',
            'North',
            500000
        );

        RAISE EXCEPTION
            'Duplicate customer was accepted';

    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'Correctly rejected duplicate customer';
    END;
END;
$$;

-- ============================================================
-- 19. EXECUTE SEGMENTATION
-- ============================================================

CALL process_customer_segmentation(
    (
        SELECT policy_id
        FROM segmentation_policies
        WHERE policy_name = 'standard_customer_segmentation'
          AND is_active = TRUE
    ),
    CURRENT_DATE
);

-- ============================================================
-- 20. CAMPAIGN ASSIGNMENT PROCESSING
-- ============================================================

INSERT INTO campaign_assignments (
    result_id,
    campaign_name,
    eligibility_status,
    eligibility_reason,
    assigned_at
)
SELECT
    report.result_id,
    report.campaign_name,

    CASE
        WHEN report.eligible THEN 'assigned'::campaign_status
        ELSE 'ineligible'::campaign_status
    END,

    report.reason,

    CASE
        WHEN report.eligible THEN CURRENT_TIMESTAMP
        ELSE NULL
    END

FROM campaign_eligibility_report report

WHERE report.run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
);

-- ============================================================
-- 21. RETRIEVAL QUERIES
-- ============================================================

-- Detailed segmentation results.
SELECT
    customer_id,
    full_name,
    region,
    demographic_segment,
    behavioral_segment,
    value_segment,
    recency_days,
    purchase_frequency,
    monetary_value
FROM customer_segmentation_report
ORDER BY monetary_value DESC;

-- ============================================================
-- 22. VALIDATION QUERIES
-- ============================================================

-- Check for missing or inconsistent segmentation results.
SELECT
    c.customer_id,
    c.full_name,
    sr.result_id
FROM customers c
LEFT JOIN segmentation_results sr
    ON sr.customer_id = c.customer_id
   AND sr.run_id = (
       SELECT MAX(run_id)
       FROM segmentation_runs
   )
WHERE c.account_status <> 'suspended'
  AND sr.result_id IS NULL;

-- Verify that spending and frequency agree.
SELECT
    result_id,
    customer_id,
    purchase_frequency,
    monetary_value
FROM segmentation_results
WHERE (purchase_frequency = 0 AND monetary_value > 0)
   OR monetary_value < 0;

-- ============================================================
-- 23. AGGREGATION QUERIES
-- ============================================================

SELECT
    value_segment,
    COUNT(*) AS customer_count,
    ROUND(SUM(monetary_value), 2) AS total_revenue,
    ROUND(AVG(monetary_value), 2) AS average_value,
    ROUND(
        COUNT(*) * 100.0 /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS customer_percentage
FROM segmentation_results
WHERE run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
)
GROUP BY value_segment
ORDER BY total_revenue DESC;

-- ============================================================
-- 24. BEHAVIORAL-VALUE CROSS TABULATION
-- ============================================================

SELECT
    behavioral_segment,

    COUNT(*) FILTER (
        WHERE value_segment = 'high_value'
    ) AS high_value_customers,

    COUNT(*) FILTER (
        WHERE value_segment = 'medium_value'
    ) AS medium_value_customers,

    COUNT(*) FILTER (
        WHERE value_segment = 'low_value'
    ) AS low_value_customers,

    COUNT(*) AS total_customers

FROM segmentation_results

WHERE run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
)

GROUP BY behavioral_segment
ORDER BY total_customers DESC;

-- ============================================================
-- 25. GEOGRAPHICAL ANALYSIS
-- ============================================================

SELECT
    c.region,
    c.city,
    COUNT(*) AS customer_count,
    ROUND(AVG(c.annual_income), 2) AS average_income,
    ROUND(SUM(sr.monetary_value), 2) AS revenue,
    COUNT(*) FILTER (
        WHERE sr.value_segment = 'high_value'
    ) AS high_value_customers

FROM segmentation_results sr

JOIN customers c
    ON c.customer_id = sr.customer_id

WHERE sr.run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
)

GROUP BY c.region, c.city

ORDER BY revenue DESC;

-- ============================================================
-- 26. CAMPAIGN ELIGIBILITY REPORT
-- ============================================================

SELECT
    customer_id,
    full_name,
    behavioral_segment,
    value_segment,
    eligible,
    campaign_name,
    reason
FROM campaign_eligibility_report
WHERE run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
)
ORDER BY eligible DESC, value_segment;

-- ============================================================
-- 27. PURCHASE FREQUENCY AND RECENCY ANALYSIS
-- ============================================================

SELECT
    behavioral_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(recency_days), 2) AS average_recency,
    ROUND(AVG(purchase_frequency), 2) AS average_frequency,
    ROUND(AVG(monetary_value), 2) AS average_monetary_value,
    ROUND(AVG(average_order_value), 2) AS average_order_value

FROM segmentation_results

WHERE run_id = (
    SELECT MAX(run_id)
    FROM segmentation_runs
)

GROUP BY behavioral_segment;

-- ============================================================
-- 28. POLICY AND RUN AUDIT
-- ============================================================

SELECT
    sr.run_id,
    sp.policy_name,
    sp.version,
    sr.observation_date,
    sr.run_status,
    sr.customers_processed,
    sr.started_at,
    sr.completed_at
FROM segmentation_runs sr
JOIN segmentation_policies sp
    ON sp.policy_id = sr.policy_id
ORDER BY sr.run_id DESC;

-- ============================================================
-- 29. TRANSACTION EXAMPLE
-- ============================================================

-- A campaign can be marked completed atomically.
-- The example completes only an existing assigned campaign.

DO $$
DECLARE
    selected_assignment BIGINT;
BEGIN
    SELECT assignment_id
    INTO selected_assignment
    FROM campaign_assignments
    WHERE eligibility_status = 'assigned'
    ORDER BY assignment_id
    LIMIT 1;

    IF selected_assignment IS NOT NULL THEN
        UPDATE campaign_assignments
        SET
            eligibility_status = 'completed',
            completed_at = CURRENT_TIMESTAMP
        WHERE assignment_id = selected_assignment;
    END IF;
END;
$$;

COMMIT;
