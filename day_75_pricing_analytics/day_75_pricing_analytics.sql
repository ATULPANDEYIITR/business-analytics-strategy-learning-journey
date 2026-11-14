/*
===============================================================================
PRICING ANALYTICS
Pricing Structures, Elasticity and Optimization
PostgreSQL 14+

Includes:
- Product catalog and cost structures
- Customer segments
- Pricing strategies
- Historical price and demand observations
- Competitor benchmarking
- Price elasticity estimation
- Pricing experiments
- Optimization scenarios
- Pricing policies and approvals
- Recommendation history
- Merge-ready transactional pricing publication
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS pricing;

SET search_path TO pricing, public;

-- ---------------------------------------------------------------------------
-- 1. ENUMERATIONS
-- ---------------------------------------------------------------------------

CREATE TYPE pricing.pricing_strategy AS ENUM (
    'COST_PLUS',
    'VALUE_BASED',
    'COMPETITIVE',
    'PENETRATION',
    'PREMIUM',
    'DYNAMIC'
);

CREATE TYPE pricing.optimization_objective AS ENUM (
    'REVENUE',
    'PROFIT'
);

CREATE TYPE pricing.approval_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE pricing.experiment_status AS ENUM (
    'DRAFT',
    'RUNNING',
    'COMPLETED',
    'CANCELLED'
);

CREATE TYPE pricing.recommendation_status AS ENUM (
    'PROPOSED',
    'APPROVED',
    'REJECTED',
    'PUBLISHED'
);

-- ---------------------------------------------------------------------------
-- 2. PRODUCT CATALOG
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku VARCHAR(40) NOT NULL UNIQUE,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(80) NOT NULL,
    unit_cost NUMERIC(14,2) NOT NULL CHECK (unit_cost >= 0),
    reference_price NUMERIC(14,2) NOT NULL CHECK (reference_price > 0),
    minimum_price NUMERIC(14,2) NOT NULL,
    maximum_price NUMERIC(14,2) NOT NULL,
    available_inventory INTEGER NOT NULL DEFAULT 0
        CHECK (available_inventory >= 0),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT product_price_boundaries CHECK (
        minimum_price > unit_cost
        AND maximum_price >= minimum_price
    )
);

CREATE INDEX idx_products_category
    ON pricing.products(category);

CREATE INDEX idx_products_active
    ON pricing.products(active)
    WHERE active = TRUE;

-- ---------------------------------------------------------------------------
-- 3. CUSTOMER SEGMENTS
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.customer_segments (
    segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    segment_code VARCHAR(30) NOT NULL UNIQUE,
    segment_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pricing.product_segment_demand (
    demand_model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    segment_id BIGINT NOT NULL
        REFERENCES pricing.customer_segments(segment_id),

    base_price NUMERIC(14,2) NOT NULL CHECK (base_price > 0),
    base_demand NUMERIC(14,2) NOT NULL CHECK (base_demand >= 0),
    price_elasticity NUMERIC(10,5) NOT NULL
        CHECK (price_elasticity < 0),

    valid_from DATE NOT NULL,
    valid_to DATE,

    CONSTRAINT valid_demand_period CHECK (
        valid_to IS NULL OR valid_to >= valid_from
    ),

    UNIQUE(product_id, segment_id, valid_from)
);

CREATE INDEX idx_segment_demand_product
    ON pricing.product_segment_demand(product_id, segment_id);

-- ---------------------------------------------------------------------------
-- 4. HISTORICAL PRICE AND DEMAND
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.demand_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    segment_id BIGINT NOT NULL
        REFERENCES pricing.customer_segments(segment_id),

    observed_at TIMESTAMPTZ NOT NULL,
    selling_price NUMERIC(14,2) NOT NULL CHECK (selling_price > 0),
    quantity_sold INTEGER NOT NULL CHECK (quantity_sold >= 0),
    promotion_discount NUMERIC(5,2) NOT NULL DEFAULT 0
        CHECK (promotion_discount BETWEEN 0 AND 100),
    channel VARCHAR(40) NOT NULL DEFAULT 'DIRECT',

    UNIQUE(product_id, segment_id, observed_at, channel)
);

CREATE INDEX idx_observations_product_date
    ON pricing.demand_observations(product_id, observed_at DESC);

CREATE INDEX idx_observations_segment_date
    ON pricing.demand_observations(segment_id, observed_at DESC);

-- ---------------------------------------------------------------------------
-- 5. COMPETITOR PRICES
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.competitors (
    competitor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    competitor_name VARCHAR(120) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pricing.competitor_prices (
    competitor_price_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    competitor_id BIGINT NOT NULL
        REFERENCES pricing.competitors(competitor_id),
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    observed_at TIMESTAMPTZ NOT NULL,
    market_price NUMERIC(14,2) NOT NULL CHECK (market_price > 0),
    source_description VARCHAR(200),

    UNIQUE(competitor_id, product_id, observed_at)
);

CREATE INDEX idx_competitor_prices_product
    ON pricing.competitor_prices(product_id, observed_at DESC);

-- ---------------------------------------------------------------------------
-- 6. PRICING EXPERIMENTS
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.pricing_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    experiment_name VARCHAR(150) NOT NULL,
    control_price NUMERIC(14,2) NOT NULL CHECK (control_price > 0),
    treatment_price NUMERIC(14,2) NOT NULL CHECK (treatment_price > 0),
    status pricing.experiment_status NOT NULL DEFAULT 'DRAFT',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (control_price <> treatment_price),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE pricing.experiment_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES pricing.pricing_experiments(experiment_id),
    segment_id BIGINT NOT NULL
        REFERENCES pricing.customer_segments(segment_id),
    group_name VARCHAR(20) NOT NULL
        CHECK (group_name IN ('CONTROL', 'TREATMENT')),
    exposure_count INTEGER NOT NULL CHECK (exposure_count >= 0),
    conversion_count INTEGER NOT NULL CHECK (
        conversion_count >= 0
        AND conversion_count <= exposure_count
    ),
    revenue NUMERIC(16,2) NOT NULL CHECK (revenue >= 0),

    UNIQUE(experiment_id, segment_id, group_name)
);

-- ---------------------------------------------------------------------------
-- 7. PRICING GOVERNANCE
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.pricing_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(120) NOT NULL UNIQUE,
    minimum_margin NUMERIC(7,5) NOT NULL
        CHECK (minimum_margin BETWEEN 0 AND 1),
    maximum_discount NUMERIC(7,5) NOT NULL
        CHECK (maximum_discount BETWEEN 0 AND 1),
    required_approvals INTEGER NOT NULL DEFAULT 1
        CHECK (required_approvals >= 0),
    require_competitor_data BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pricing.pricing_recommendations (
    recommendation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    policy_id BIGINT NOT NULL
        REFERENCES pricing.pricing_policies(policy_id),

    strategy pricing.pricing_strategy NOT NULL,
    objective pricing.optimization_objective NOT NULL,

    recommended_price NUMERIC(14,2) NOT NULL CHECK (recommended_price > 0),
    expected_demand NUMERIC(14,2) NOT NULL CHECK (expected_demand >= 0),
    expected_revenue NUMERIC(16,2) NOT NULL CHECK (expected_revenue >= 0),
    expected_cost NUMERIC(16,2) NOT NULL CHECK (expected_cost >= 0),
    expected_profit NUMERIC(16,2) NOT NULL,
    expected_margin NUMERIC(10,5) NOT NULL,

    status pricing.recommendation_status NOT NULL DEFAULT 'PROPOSED',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMPTZ
);

CREATE INDEX idx_recommendations_product
    ON pricing.pricing_recommendations(product_id, generated_at DESC);

CREATE INDEX idx_recommendations_status
    ON pricing.pricing_recommendations(status);

-- ---------------------------------------------------------------------------
-- 8. APPROVAL WORKFLOW
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.pricing_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recommendation_id BIGINT NOT NULL
        REFERENCES pricing.pricing_recommendations(recommendation_id),
    reviewer_name VARCHAR(120) NOT NULL,
    reviewer_role VARCHAR(80) NOT NULL,
    status pricing.approval_status NOT NULL DEFAULT 'PENDING',
    comments TEXT,
    reviewed_at TIMESTAMPTZ,

    UNIQUE(recommendation_id, reviewer_name)
);

CREATE INDEX idx_approvals_recommendation
    ON pricing.pricing_approvals(recommendation_id, status);

-- ---------------------------------------------------------------------------
-- 9. PRICING PUBLICATION HISTORY
-- ---------------------------------------------------------------------------

CREATE TABLE pricing.published_prices (
    publication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id BIGINT NOT NULL
        REFERENCES pricing.products(product_id),
    recommendation_id BIGINT NOT NULL
        REFERENCES pricing.pricing_recommendations(recommendation_id),
    published_price NUMERIC(14,2) NOT NULL CHECK (published_price > 0),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    published_by VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        effective_to IS NULL OR effective_to > effective_from
    )
);

CREATE INDEX idx_published_prices_product
    ON pricing.published_prices(product_id, effective_from DESC);

CREATE UNIQUE INDEX idx_one_current_published_price
    ON pricing.published_prices(product_id)
    WHERE effective_to IS NULL;

-- ---------------------------------------------------------------------------
-- 10. PRICE ELASTICITY ESTIMATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION pricing.estimate_elasticity(
    p_product_id BIGINT,
    p_segment_id BIGINT
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_elasticity NUMERIC;
    v_count BIGINT;
BEGIN
    SELECT
        COUNT(*),
        regr_slope(
            LN(quantity_sold::NUMERIC),
            LN(selling_price)
        )
    INTO v_count, v_elasticity
    FROM pricing.demand_observations
    WHERE product_id = p_product_id
      AND segment_id = p_segment_id
      AND quantity_sold > 0
      AND selling_price > 0;

    IF v_count < 3 THEN
        RAISE EXCEPTION
            'At least three positive-demand observations are required.';
    END IF;

    IF v_elasticity IS NULL THEN
        RAISE EXCEPTION 'Elasticity cannot be estimated.';
    END IF;

    RETURN ROUND(v_elasticity, 5);
END;
$$;

-- ---------------------------------------------------------------------------
-- 11. COMPETITOR BENCHMARK VIEW
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW pricing.competitor_benchmarks AS
SELECT
    product_id,
    COUNT(*) AS competitor_count,
    ROUND(AVG(market_price), 2) AS average_price,
    ROUND(MIN(market_price), 2) AS minimum_price,
    ROUND(MAX(market_price), 2) AS maximum_price,
    ROUND(
        PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY market_price)::NUMERIC,
        2
    ) AS median_price
FROM pricing.competitor_prices
GROUP BY product_id;

-- ---------------------------------------------------------------------------
-- 12. DEMAND FORECAST FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION pricing.forecast_demand(
    p_product_id BIGINT,
    p_price NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_demand NUMERIC;
    v_inventory INTEGER;
BEGIN
    IF p_price <= 0 THEN
        RAISE EXCEPTION 'Price must be positive.';
    END IF;

    SELECT available_inventory
    INTO v_inventory
    FROM pricing.products
    WHERE product_id = p_product_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product does not exist or is inactive.';
    END IF;

    SELECT COALESCE(
        SUM(
            base_demand *
            POWER(p_price / base_price, price_elasticity)
        ),
        0
    )
    INTO v_demand
    FROM pricing.product_segment_demand
    WHERE product_id = p_product_id
      AND valid_from <= CURRENT_DATE
      AND (valid_to IS NULL OR valid_to >= CURRENT_DATE);

    RETURN LEAST(v_demand, v_inventory::NUMERIC);
END;
$$;

-- ---------------------------------------------------------------------------
-- 13. PRICING POLICY EVALUATION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION pricing.evaluate_price(
    p_product_id BIGINT,
    p_policy_id BIGINT,
    p_price NUMERIC,
    p_strategy pricing.pricing_strategy,
    p_competitor_price NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    eligible BOOLEAN,
    expected_demand NUMERIC,
    expected_revenue NUMERIC,
    expected_profit NUMERIC,
    expected_margin NUMERIC,
    violation TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_product pricing.products%ROWTYPE;
    v_policy pricing.pricing_policies%ROWTYPE;
    v_demand NUMERIC;
    v_revenue NUMERIC;
    v_cost NUMERIC;
    v_profit NUMERIC;
    v_margin NUMERIC;
    v_violations TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT *
    INTO v_product
    FROM pricing.products
    WHERE product_id = p_product_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product unavailable.';
    END IF;

    SELECT *
    INTO v_policy
    FROM pricing.pricing_policies
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active pricing policy not found.';
    END IF;

    IF p_price <= 0 THEN
        RAISE EXCEPTION 'Price must be positive.';
    END IF;

    v_demand := pricing.forecast_demand(p_product_id, p_price);

    v_revenue := p_price * v_demand;
    v_cost := v_product.unit_cost * v_demand;
    v_profit := v_revenue - v_cost;

    v_margin := CASE
        WHEN v_revenue > 0 THEN v_profit / v_revenue
        ELSE 0
    END;

    IF p_price < v_product.minimum_price
       OR p_price > v_product.maximum_price THEN
        v_violations := array_append(
            v_violations,
            'Price outside product boundaries'
        );
    END IF;

    IF v_margin < v_policy.minimum_margin THEN
        v_violations := array_append(
            v_violations,
            'Minimum margin not achieved'
        );
    END IF;

    IF p_price <
        v_product.reference_price * (1 - v_policy.maximum_discount) THEN
        v_violations := array_append(
            v_violations,
            'Maximum discount exceeded'
        );
    END IF;

    IF v_policy.require_competitor_data
       AND p_competitor_price IS NULL THEN
        v_violations := array_append(
            v_violations,
            'Competitor data required'
        );
    END IF;

    IF p_competitor_price IS NOT NULL
       AND p_competitor_price <= 0 THEN
        v_violations := array_append(
            v_violations,
            'Invalid competitor price'
        );
    END IF;

    RETURN QUERY SELECT
        cardinality(v_violations) = 0,
        ROUND(v_demand, 2),
        ROUND(v_revenue, 2),
        ROUND(v_profit, 2),
        ROUND(v_margin, 5),
        CASE
            WHEN cardinality(v_violations) = 0 THEN NULL
            ELSE array_to_string(v_violations, '; ')
        END;
END;
$$;

-- ---------------------------------------------------------------------------
-- 14. PRICE OPTIMIZATION FUNCTION
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION pricing.optimize_price(
    p_product_id BIGINT,
    p_policy_id BIGINT,
    p_objective pricing.optimization_objective,
    p_step NUMERIC DEFAULT 5,
    p_competitor_price NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    recommended_price NUMERIC,
    expected_demand NUMERIC,
    expected_revenue NUMERIC,
    expected_profit NUMERIC,
    expected_margin NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_product pricing.products%ROWTYPE;
    v_price NUMERIC;
    v_best_price NUMERIC;
    v_best_demand NUMERIC;
    v_best_revenue NUMERIC;
    v_best_profit NUMERIC;
    v_best_margin NUMERIC;
    v_score NUMERIC;
    v_best_score NUMERIC := NULL;
    v_eligible BOOLEAN;
BEGIN
    IF p_step <= 0 THEN
        RAISE EXCEPTION 'Optimization step must be positive.';
    END IF;

    SELECT *
    INTO v_product
    FROM pricing.products
    WHERE product_id = p_product_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active product not found.';
    END IF;

    v_price := v_product.minimum_price;

    WHILE v_price <= v_product.maximum_price LOOP

        SELECT
            e.eligible,
            e.expected_demand,
            e.expected_revenue,
            e.expected_profit,
            e.expected_margin
        INTO
            v_eligible,
            v_best_demand,
            v_best_revenue,
            v_best_profit,
            v_best_margin
        FROM pricing.evaluate_price(
            p_product_id,
            p_policy_id,
            v_price,
            'DYNAMIC',
            p_competitor_price
        ) e;

        IF v_eligible THEN
            v_score := CASE
                WHEN p_objective = 'PROFIT'
                    THEN v_best_profit
                ELSE v_best_revenue
            END;

            IF v_best_score IS NULL OR
               v_score > v_best_score OR
               (v_score = v_best_score AND
                v_price > v_best_price) THEN

                v_best_score := v_score;
                v_best_price := v_price;
                v_best_demand := v_best_demand;
                v_best_revenue := v_best_revenue;
                v_best_profit := v_best_profit;
                v_best_margin := v_best_margin;
            END IF;
        END IF;

        v_price := v_price + p_step;
    END LOOP;

    IF v_best_score IS NULL THEN
        RAISE EXCEPTION 'No eligible price found.';
    END IF;

    -- Recalculate the final selected candidate.
    SELECT
        e.expected_demand,
        e.expected_revenue,
        e.expected_profit,
        e.expected_margin
    INTO
        v_best_demand,
        v_best_revenue,
        v_best_profit,
        v_best_margin
    FROM pricing.evaluate_price(
        p_product_id,
        p_policy_id,
        v_best_price,
        'DYNAMIC',
        p_competitor_price
    ) e;

    RETURN QUERY SELECT
        v_best_price,
        v_best_demand,
        v_best_revenue,
        v_best_profit,
        v_best_margin;
END;
$$;

-- ---------------------------------------------------------------------------
-- 15. RECOMMENDATION APPROVAL TRIGGER
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION pricing.validate_recommendation_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_required INTEGER;
    v_approved INTEGER;
    v_rejected INTEGER;
BEGIN
    IF NEW.status = 'APPROVED' OR NEW.status = 'PUBLISHED' THEN

        SELECT required_approvals
        INTO v_required
        FROM pricing.pricing_policies
        WHERE policy_id = NEW.policy_id
          AND active = TRUE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Active policy is required.';
        END IF;

        SELECT
            COUNT(*) FILTER (
                WHERE status = 'APPROVED'
            ),
            COUNT(*) FILTER (
                WHERE status = 'REJECTED'
            )
        INTO v_approved, v_rejected
        FROM pricing.pricing_approvals
        WHERE recommendation_id = NEW.recommendation_id;

        IF v_rejected > 0 THEN
            RAISE EXCEPTION
                'Rejected recommendation cannot be approved.';
        END IF;

        IF v_approved < v_required THEN
            RAISE EXCEPTION
                'Required approval threshold not satisfied.';
        END IF;

        IF NEW.status = 'PUBLISHED' THEN
            NEW.published_at := COALESCE(
                NEW.published_at,
                CURRENT_TIMESTAMP
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_recommendation_approval
BEFORE UPDATE OF status
ON pricing.pricing_recommendations
FOR EACH ROW
EXECUTE FUNCTION pricing.validate_recommendation_approval();

-- ---------------------------------------------------------------------------
-- 16. PUBLICATION PROCEDURE
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE pricing.publish_recommendation(
    p_recommendation_id BIGINT,
    p_publisher VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_recommendation pricing.pricing_recommendations%ROWTYPE;
    v_product pricing.products%ROWTYPE;
BEGIN
    IF p_publisher IS NULL OR TRIM(p_publisher) = '' THEN
        RAISE EXCEPTION 'Publisher identity is required.';
    END IF;

    SELECT *
    INTO v_recommendation
    FROM pricing.pricing_recommendations
    WHERE recommendation_id = p_recommendation_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Recommendation not found.';
    END IF;

    IF v_recommendation.status <> 'APPROVED' THEN
        RAISE EXCEPTION
            'Only approved recommendations can be published.';
    END IF;

    SELECT *
    INTO v_product
    FROM pricing.products
    WHERE product_id = v_recommendation.product_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Product not found.';
    END IF;

    IF v_recommendation.recommended_price < v_product.minimum_price
       OR v_recommendation.recommended_price > v_product.maximum_price THEN
        RAISE EXCEPTION 'Published price violates current product limits.';
    END IF;

    UPDATE pricing.published_prices
    SET effective_to = CURRENT_TIMESTAMP
    WHERE product_id = v_recommendation.product_id
      AND effective_to IS NULL;

    INSERT INTO pricing.published_prices (
        product_id,
        recommendation_id,
        published_price,
        effective_from,
        published_by
    )
    VALUES (
        v_recommendation.product_id,
        v_recommendation.recommendation_id,
        v_recommendation.recommended_price,
        CURRENT_TIMESTAMP,
        p_publisher
    );

    UPDATE pricing.pricing_recommendations
    SET status = 'PUBLISHED'
    WHERE recommendation_id = p_recommendation_id;
END;
$$;

-- ---------------------------------------------------------------------------
-- 17. SAMPLE PRODUCT AND CUSTOMER DATA
-- ---------------------------------------------------------------------------

INSERT INTO pricing.products (
    sku,
    product_name,
    category,
    unit_cost,
    reference_price,
    minimum_price,
    maximum_price,
    available_inventory
)
VALUES
(
    'ENT-100',
    'Enterprise Analytics Platform',
    'Software',
    220,
    500,
    300,
    900,
    1000
),
(
    'SMB-200',
    'Small Business Analytics',
    'Software',
    80,
    200,
    110,
    400,
    500
);

INSERT INTO pricing.customer_segments (
    segment_code,
    segment_name,
    description
)
VALUES
('SMB', 'Small Business', 'Small and medium businesses'),
('CORP', 'Corporate', 'Mid-sized corporate customers'),
('ENT', 'Enterprise', 'Large enterprise customers');

INSERT INTO pricing.product_segment_demand (
    product_id,
    segment_id,
    base_price,
    base_demand,
    price_elasticity,
    valid_from
)
SELECT
    p.product_id,
    s.segment_id,
    500,
    CASE s.segment_code
        WHEN 'SMB' THEN 75
        WHEN 'CORP' THEN 45
        WHEN 'ENT' THEN 25
    END,
    CASE s.segment_code
        WHEN 'SMB' THEN -1.50
        WHEN 'CORP' THEN -0.90
        WHEN 'ENT' THEN -0.60
    END,
    CURRENT_DATE
FROM pricing.products p
CROSS JOIN pricing.customer_segments s
WHERE p.sku = 'ENT-100';

INSERT INTO pricing.product_segment_demand (
    product_id,
    segment_id,
    base_price,
    base_demand,
    price_elasticity,
    valid_from
)
SELECT
    p.product_id,
    s.segment_id,
    200,
    CASE s.segment_code
        WHEN 'SMB' THEN 120
        WHEN 'CORP' THEN 20
        WHEN 'ENT' THEN 5
    END,
    CASE s.segment_code
        WHEN 'SMB' THEN -1.60
        WHEN 'CORP' THEN -1.00
        WHEN 'ENT' THEN -0.70
    END,
    CURRENT_DATE
FROM pricing.products p
CROSS JOIN pricing.customer_segments s
WHERE p.sku = 'SMB-200';

-- ---------------------------------------------------------------------------
-- 18. HISTORICAL OBSERVATIONS
-- ---------------------------------------------------------------------------

INSERT INTO pricing.demand_observations (
    product_id,
    segment_id,
    observed_at,
    selling_price,
    quantity_sold,
    promotion_discount,
    channel
)
SELECT
    p.product_id,
    s.segment_id,
    CURRENT_TIMESTAMP - interval_data.days_ago * INTERVAL '1 day',
    interval_data.price,
    interval_data.quantity,
    0,
    'DIRECT'
FROM pricing.products p
JOIN pricing.customer_segments s
    ON s.segment_code = 'SMB'
CROSS JOIN (
    VALUES
        (60, 400::NUMERIC, 150),
        (50, 450::NUMERIC, 133),
        (40, 500::NUMERIC, 115),
        (30, 550::NUMERIC, 105),
        (20, 600::NUMERIC, 94),
        (10, 650::NUMERIC, 86)
) AS interval_data(days_ago, price, quantity)
WHERE p.sku = 'ENT-100';

-- ---------------------------------------------------------------------------
-- 19. COMPETITOR INFORMATION
-- ---------------------------------------------------------------------------

INSERT INTO pricing.competitors(competitor_name)
VALUES
('Market Competitor A'),
('Market Competitor B'),
('Market Competitor C');

INSERT INTO pricing.competitor_prices (
    competitor_id,
    product_id,
    observed_at,
    market_price,
    source_description
)
SELECT
    c.competitor_id,
    p.product_id,
    CURRENT_TIMESTAMP,
    CASE c.competitor_name
        WHEN 'Market Competitor A' THEN 520
        WHEN 'Market Competitor B' THEN 540
        ELSE 560
    END,
    'Illustrative market observation'
FROM pricing.competitors c
CROSS JOIN pricing.products p
WHERE p.sku = 'ENT-100';

-- ---------------------------------------------------------------------------
-- 20. PRICING POLICIES
-- ---------------------------------------------------------------------------

INSERT INTO pricing.pricing_policies (
    policy_name,
    minimum_margin,
    maximum_discount,
    required_approvals,
    require_competitor_data
)
VALUES
(
    'Enterprise Standard Policy',
    0.20,
    0.40,
    2,
    TRUE
),
(
    'Small Business Policy',
    0.15,
    0.45,
    1,
    FALSE
);

-- ---------------------------------------------------------------------------
-- 21. RETRIEVAL AND ELASTICITY ANALYSIS
-- ---------------------------------------------------------------------------

SELECT
    p.sku,
    p.product_name,
    s.segment_name,
    pricing.estimate_elasticity(
        p.product_id,
        s.segment_id
    ) AS estimated_elasticity
FROM pricing.products p
CROSS JOIN pricing.customer_segments s
WHERE p.sku = 'ENT-100'
  AND s.segment_code = 'SMB';

-- Demand observation report.
SELECT
    p.sku,
    s.segment_name,
    COUNT(*) AS observations,
    ROUND(AVG(o.selling_price), 2) AS average_price,
    SUM(o.quantity_sold) AS total_quantity,
    ROUND(AVG(o.quantity_sold), 2) AS average_quantity
FROM pricing.demand_observations o
JOIN pricing.products p USING (product_id)
JOIN pricing.customer_segments s USING (segment_id)
GROUP BY p.sku, s.segment_name;

-- ---------------------------------------------------------------------------
-- 22. COMPETITOR AGGREGATION
-- ---------------------------------------------------------------------------

SELECT
    p.sku,
    p.reference_price,
    b.competitor_count,
    b.minimum_price,
    b.average_price,
    b.median_price,
    b.maximum_price,
    ROUND(
        (p.reference_price - b.average_price)
        / b.average_price * 100,
        2
    ) AS price_position_percentage
FROM pricing.products p
JOIN pricing.competitor_benchmarks b USING (product_id);

-- ---------------------------------------------------------------------------
-- 23. OPTIMIZATION AND POLICY EVALUATION
-- ---------------------------------------------------------------------------

SELECT
    p.sku,
    'PROFIT' AS objective,
    result.*
FROM pricing.products p
CROSS JOIN LATERAL pricing.optimize_price(
    p.product_id,
    policy.policy_id,
    'PROFIT',
    5,
    540
) result
JOIN pricing.pricing_policies policy
    ON policy.policy_name = 'Enterprise Standard Policy'
WHERE p.sku = 'ENT-100';

SELECT
    p.sku,
    result.*
FROM pricing.products p
CROSS JOIN LATERAL pricing.optimize_price(
    p.product_id,
    policy.policy_id,
    'REVENUE',
    5,
    540
) result
JOIN pricing.pricing_policies policy
    ON policy.policy_name = 'Enterprise Standard Policy'
WHERE p.sku = 'ENT-100';

-- Explicitly test a price that violates the minimum margin.
SELECT *
FROM pricing.evaluate_price(
    (
        SELECT product_id
        FROM pricing.products
        WHERE sku = 'ENT-100'
    ),
    (
        SELECT policy_id
        FROM pricing.pricing_policies
        WHERE policy_name = 'Enterprise Standard Policy'
    ),
    310,
    'DYNAMIC',
    540
);

-- ---------------------------------------------------------------------------
-- 24. CREATE A RECOMMENDATION
-- ---------------------------------------------------------------------------

INSERT INTO pricing.pricing_recommendations (
    product_id,
    policy_id,
    strategy,
    objective,
    recommended_price,
    expected_demand,
    expected_revenue,
    expected_cost,
    expected_profit,
    expected_margin
)
SELECT
    p.product_id,
    policy.policy_id,
    'DYNAMIC',
    'PROFIT',
    result.recommended_price,
    result.expected_demand,
    result.expected_revenue,
    result.expected_revenue - result.expected_profit,
    result.expected_profit,
    result.expected_margin
FROM pricing.products p
JOIN pricing.pricing_policies policy
    ON policy.policy_name = 'Enterprise Standard Policy'
CROSS JOIN LATERAL pricing.optimize_price(
    p.product_id,
    policy.policy_id,
    'PROFIT',
    5,
    540
) result
WHERE p.sku = 'ENT-100';

-- ---------------------------------------------------------------------------
-- 25. ASSIGN REVIEWERS AND APPROVALS
-- ---------------------------------------------------------------------------

INSERT INTO pricing.pricing_approvals (
    recommendation_id,
    reviewer_name,
    reviewer_role,
    status,
    comments,
    reviewed_at
)
SELECT
    recommendation_id,
    'Pricing Manager',
    'PRICING_MANAGER',
    'APPROVED',
    'Cost and margin validation completed.',
    CURRENT_TIMESTAMP
FROM pricing.pricing_recommendations
WHERE status = 'PROPOSED';

INSERT INTO pricing.pricing_approvals (
    recommendation_id,
    reviewer_name,
    reviewer_role,
    status,
    comments,
    reviewed_at
)
SELECT
    recommendation_id,
    'Commercial Director',
    'COMMERCIAL_DIRECTOR',
    'APPROVED',
    'Commercial positioning accepted.',
    CURRENT_TIMESTAMP
FROM pricing.pricing_recommendations
WHERE status = 'PROPOSED';

-- ---------------------------------------------------------------------------
-- 26. APPROVAL EVALUATION REPORT
-- ---------------------------------------------------------------------------

WITH approval_summary AS (
    SELECT
        recommendation_id,
        COUNT(*) FILTER (
            WHERE status = 'APPROVED'
        ) AS approved_count,
        COUNT(*) FILTER (
            WHERE status = 'REJECTED'
        ) AS rejected_count
    FROM pricing.pricing_approvals
    GROUP BY recommendation_id
)
SELECT
    r.recommendation_id,
    r.recommended_price,
    r.expected_profit,
    p.policy_name,
    COALESCE(a.approved_count, 0) AS approved_count,
    p.required_approvals,
    COALESCE(a.rejected_count, 0) AS rejected_count,
    (
        COALESCE(a.approved_count, 0) >= p.required_approvals
        AND COALESCE(a.rejected_count, 0) = 0
    ) AS approval_eligible
FROM pricing.pricing_recommendations r
JOIN pricing.pricing_policies p USING (policy_id)
LEFT JOIN approval_summary a USING (recommendation_id);

-- ---------------------------------------------------------------------------
-- 27. APPROVE RECOMMENDATION
-- ---------------------------------------------------------------------------

UPDATE pricing.pricing_recommendations r
SET status = 'APPROVED'
FROM pricing.pricing_policies p
WHERE r.policy_id = p.policy_id
  AND r.status = 'PROPOSED'
  AND p.policy_name = 'Enterprise Standard Policy'
  AND (
      SELECT COUNT(*)
      FROM pricing.pricing_approvals a
      WHERE a.recommendation_id = r.recommendation_id
        AND a.status = 'APPROVED'
  ) >= p.required_approvals
  AND NOT EXISTS (
      SELECT 1
      FROM pricing.pricing_approvals a
      WHERE a.recommendation_id = r.recommendation_id
        AND a.status = 'REJECTED'
  );

-- ---------------------------------------------------------------------------
-- 28. TRANSACTIONAL PUBLICATION
-- ---------------------------------------------------------------------------

DO $$
DECLARE
    v_recommendation_id BIGINT;
BEGIN
    SELECT recommendation_id
    INTO v_recommendation_id
    FROM pricing.pricing_recommendations
    WHERE status = 'APPROVED'
    ORDER BY generated_at DESC
    LIMIT 1;

    IF v_recommendation_id IS NOT NULL THEN
        CALL pricing.publish_recommendation(
            v_recommendation_id,
            'Pricing Operations'
        );
    END IF;
END;
$$;

COMMIT;

-- ---------------------------------------------------------------------------
-- 29. REPORTING
-- ---------------------------------------------------------------------------

-- Current published prices.
SELECT
    p.sku,
    p.product_name,
    pp.published_price,
    pp.effective_from,
    pp.published_by
FROM pricing.published_prices pp
JOIN pricing.products p USING (product_id)
WHERE pp.effective_to IS NULL;

-- Recommendation performance.
SELECT
    p.sku,
    r.objective,
    COUNT(*) AS recommendation_count,
    ROUND(AVG(r.recommended_price), 2) AS average_price,
    ROUND(MAX(r.expected_profit), 2) AS maximum_profit,
    ROUND(AVG(r.expected_margin) * 100, 2) AS average_margin_percentage
FROM pricing.pricing_recommendations r
JOIN pricing.products p USING (product_id)
GROUP BY p.sku, r.objective;

-- Pricing governance status.
SELECT
    r.recommendation_id,
    p.sku,
    r.recommended_price,
    r.status,
    COUNT(a.approval_id) AS review_count,
    COUNT(a.approval_id) FILTER (
        WHERE a.status = 'APPROVED'
    ) AS approval_count,
    COUNT(a.approval_id) FILTER (
        WHERE a.status = 'REJECTED'
    ) AS rejection_count
FROM pricing.pricing_recommendations r
JOIN pricing.products p USING (product_id)
LEFT JOIN pricing.pricing_approvals a USING (recommendation_id)
GROUP BY
    r.recommendation_id,
    p.sku,
    r.recommended_price,
    r.status
ORDER BY r.generated_at DESC;

-- ---------------------------------------------------------------------------
-- 30. DATA QUALITY VALIDATION
-- ---------------------------------------------------------------------------

-- Detect missing segment demand models.
SELECT
    p.sku,
    s.segment_code
FROM pricing.products p
CROSS JOIN pricing.customer_segments s
LEFT JOIN pricing.product_segment_demand d
    ON d.product_id = p.product_id
   AND d.segment_id = s.segment_id
   AND d.valid_from <= CURRENT_DATE
   AND (d.valid_to IS NULL OR d.valid_to >= CURRENT_DATE)
WHERE p.active = TRUE
  AND d.demand_model_id IS NULL;

-- Detect recommendations outside product boundaries.
SELECT
    r.recommendation_id,
    p.sku,
    r.recommended_price,
    p.minimum_price,
    p.maximum_price
FROM pricing.pricing_recommendations r
JOIN pricing.products p USING (product_id)
WHERE r.recommended_price < p.minimum_price
   OR r.recommended_price > p.maximum_price;

-- Detect competitor observations requiring review.
SELECT
    c.competitor_name,
    p.sku,
    cp.market_price,
    p.reference_price
FROM pricing.competitor_prices cp
JOIN pricing.competitors c USING (competitor_id)
JOIN pricing.products p USING (product_id)
WHERE ABS(cp.market_price - p.reference_price)
    / p.reference_price > 0.50;

-- ---------------------------------------------------------------------------
-- END OF PRICING ANALYTICS DATABASE IMPLEMENTATION
-- ---------------------------------------------------------------------------
