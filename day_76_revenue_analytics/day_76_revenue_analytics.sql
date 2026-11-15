/*
===============================================================================
REVENUE ANALYTICS
Revenue Decomposition and Growth Analysis
PostgreSQL 15+

Relational workflow:
Revenue observations
    -> Monthly aggregation
    -> Revenue growth
    -> Volume, mix and price decomposition
    -> Product and regional contribution
    -> Customer concentration
    -> Forecast inputs
    -> Management reporting

Financial measures:
Revenue = Units * List Price * (1 - Discount Rate)
Gross Profit = Revenue - Variable Cost

Decomposition:
Revenue Change = Volume Effect + Mix Effect + Price Effect

The decomposition uses product-level unit shares and weighted realized prices.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS revenue_analytics;

SET search_path TO revenue_analytics, public;

-- ============================================================================
-- 1. REFERENCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_code VARCHAR(30) NOT NULL UNIQUE,
    product_name VARCHAR(120) NOT NULL UNIQUE,
    category VARCHAR(80) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_code VARCHAR(20) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_code VARCHAR(30) NOT NULL UNIQUE,
    customer_name VARCHAR(150) NOT NULL,
    customer_segment VARCHAR(50) NOT NULL,
    region_id BIGINT REFERENCES regions(region_id),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS reporting_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period_start DATE NOT NULL UNIQUE,
    period_end DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',

    CHECK (period_start = date_trunc('month', period_start)::DATE),
    CHECK (period_end = (period_start + INTERVAL '1 month - 1 day')::DATE),
    CHECK (fiscal_quarter BETWEEN 1 AND 4),
    CHECK (fiscal_year BETWEEN 2000 AND 2200),
    CHECK (status IN ('OPEN', 'CLOSED', 'LOCKED'))
);

-- ============================================================================
-- 2. REVENUE FACT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS revenue_transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    transaction_reference VARCHAR(60) NOT NULL UNIQUE,

    period_id BIGINT NOT NULL
        REFERENCES reporting_periods(period_id),

    product_id BIGINT NOT NULL
        REFERENCES products(product_id),

    region_id BIGINT NOT NULL
        REFERENCES regions(region_id),

    customer_id BIGINT NOT NULL
        REFERENCES customers(customer_id),

    units BIGINT NOT NULL,

    list_price NUMERIC(18, 4) NOT NULL,
    discount_rate NUMERIC(8, 6) NOT NULL DEFAULT 0,

    unit_cost NUMERIC(18, 4) NOT NULL,

    net_unit_price NUMERIC(18, 4)
        GENERATED ALWAYS AS (
            ROUND(list_price * (1 - discount_rate), 4)
        ) STORED,

    revenue NUMERIC(22, 4)
        GENERATED ALWAYS AS (
            ROUND(
                units * list_price * (1 - discount_rate),
                4
            )
        ) STORED,

    variable_cost NUMERIC(22, 4)
        GENERATED ALWAYS AS (
            ROUND(units * unit_cost, 4)
        ) STORED,

    gross_profit NUMERIC(22, 4)
        GENERATED ALWAYS AS (
            ROUND(
                units * (
                    list_price * (1 - discount_rate) - unit_cost
                ),
                4
            )
        ) STORED,

    transaction_date DATE NOT NULL,

    source_system VARCHAR(50) NOT NULL DEFAULT 'INTERNAL',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (units >= 0),
    CHECK (list_price >= 0),
    CHECK (unit_cost >= 0),
    CHECK (discount_rate BETWEEN 0 AND 1),
    CHECK (transaction_date IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_revenue_period
    ON revenue_transactions(period_id);

CREATE INDEX IF NOT EXISTS idx_revenue_product_period
    ON revenue_transactions(product_id, period_id);

CREATE INDEX IF NOT EXISTS idx_revenue_region_period
    ON revenue_transactions(region_id, period_id);

CREATE INDEX IF NOT EXISTS idx_revenue_customer_period
    ON revenue_transactions(customer_id, period_id);

CREATE INDEX IF NOT EXISTS idx_revenue_transaction_date
    ON revenue_transactions(transaction_date);

-- ============================================================================
-- 3. REPORTING ACCESS CONTROL
-- ============================================================================

CREATE TABLE IF NOT EXISTS analytical_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    role_name VARCHAR(30) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (
        role_name IN (
            'ANALYST',
            'MANAGER',
            'FINANCE_ADMIN',
            'AUDITOR'
        )
    )
);

CREATE TABLE IF NOT EXISTS report_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    period_start DATE,
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. INTEGRITY TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_revenue_transaction()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_period_start DATE;
    v_period_end DATE;
    v_period_status VARCHAR(20);
    v_product_active BOOLEAN;
    v_customer_active BOOLEAN;
    v_region_active BOOLEAN;
BEGIN
    SELECT
        period_start,
        period_end,
        status
    INTO
        v_period_start,
        v_period_end,
        v_period_status
    FROM reporting_periods
    WHERE period_id = NEW.period_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reporting period does not exist.';
    END IF;

    IF v_period_status <> 'OPEN' THEN
        RAISE EXCEPTION
            'Transactions cannot be inserted into period status %.',
            v_period_status;
    END IF;

    IF NEW.transaction_date < v_period_start
       OR NEW.transaction_date > v_period_end THEN
        RAISE EXCEPTION
            'Transaction date does not belong to the selected period.';
    END IF;

    SELECT active INTO v_product_active
    FROM products
    WHERE product_id = NEW.product_id;

    SELECT active INTO v_customer_active
    FROM customers
    WHERE customer_id = NEW.customer_id;

    SELECT active INTO v_region_active
    FROM regions
    WHERE region_id = NEW.region_id;

    IF NOT COALESCE(v_product_active, FALSE) THEN
        RAISE EXCEPTION 'Product is inactive or missing.';
    END IF;

    IF NOT COALESCE(v_customer_active, FALSE) THEN
        RAISE EXCEPTION 'Customer is inactive or missing.';
    END IF;

    IF NOT COALESCE(v_region_active, FALSE) THEN
        RAISE EXCEPTION 'Region is inactive or missing.';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_revenue
    ON revenue_transactions;

CREATE TRIGGER trg_validate_revenue
BEFORE INSERT OR UPDATE
ON revenue_transactions
FOR EACH ROW
EXECUTE FUNCTION validate_revenue_transaction();

-- ============================================================================
-- 5. AUDIT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_revenue_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO report_audit (
        username,
        operation,
        details
    )
    VALUES (
        CURRENT_USER,
        TG_OP,
        jsonb_build_object(
            'transaction_id',
            COALESCE(NEW.transaction_id, OLD.transaction_id),
            'transaction_reference',
            COALESCE(
                NEW.transaction_reference,
                OLD.transaction_reference
            )
        )
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_audit_revenue
    ON revenue_transactions;

CREATE TRIGGER trg_audit_revenue
AFTER INSERT OR UPDATE OR DELETE
ON revenue_transactions
FOR EACH ROW
EXECUTE FUNCTION audit_revenue_changes();

-- ============================================================================
-- 6. MONTHLY REVENUE VIEW
-- ============================================================================

CREATE OR REPLACE VIEW monthly_revenue_summary AS
SELECT
    rp.period_start,
    rp.fiscal_year,
    rp.fiscal_quarter,
    p.product_id,
    p.product_name,
    p.category,
    r.region_id,
    r.region_name,

    COUNT(DISTINCT rt.customer_id) AS customer_count,

    SUM(rt.units) AS total_units,
    SUM(rt.revenue) AS total_revenue,
    SUM(rt.variable_cost) AS total_variable_cost,
    SUM(rt.gross_profit) AS gross_profit,

    CASE
        WHEN SUM(rt.units) > 0
        THEN SUM(rt.revenue) / SUM(rt.units)
        ELSE 0
    END AS average_selling_price,

    CASE
        WHEN SUM(rt.revenue) > 0
        THEN SUM(rt.gross_profit) / SUM(rt.revenue)
        ELSE 0
    END AS gross_margin

FROM revenue_transactions rt
JOIN reporting_periods rp
    ON rp.period_id = rt.period_id
JOIN products p
    ON p.product_id = rt.product_id
JOIN regions r
    ON r.region_id = rt.region_id

GROUP BY
    rp.period_start,
    rp.fiscal_year,
    rp.fiscal_quarter,
    p.product_id,
    p.product_name,
    p.category,
    r.region_id,
    r.region_name;

-- ============================================================================
-- 7. OVERALL MONTHLY GROWTH
-- ============================================================================

CREATE OR REPLACE VIEW monthly_growth_analysis AS
WITH monthly AS (
    SELECT
        rp.period_start,
        SUM(rt.revenue) AS revenue,
        SUM(rt.units) AS units,
        SUM(rt.gross_profit) AS gross_profit
    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    GROUP BY rp.period_start
),
comparisons AS (
    SELECT
        period_start,
        revenue,
        units,
        gross_profit,

        LAG(revenue) OVER (
            ORDER BY period_start
        ) AS previous_revenue,

        LAG(units) OVER (
            ORDER BY period_start
        ) AS previous_units,

        LAG(gross_profit) OVER (
            ORDER BY period_start
        ) AS previous_gross_profit

    FROM monthly
)
SELECT
    period_start,
    revenue,
    previous_revenue,

    revenue - previous_revenue AS revenue_change,

    CASE
        WHEN previous_revenue > 0
        THEN (revenue - previous_revenue) / previous_revenue
        ELSE NULL
    END AS revenue_growth_rate,

    units,
    previous_units,
    units - previous_units AS unit_change,

    gross_profit,
    previous_gross_profit,

    CASE
        WHEN revenue > 0
        THEN gross_profit / revenue
        ELSE NULL
    END AS gross_margin

FROM comparisons;

-- ============================================================================
-- 8. PRODUCT PERFORMANCE AND REVENUE CONTRIBUTION
-- ============================================================================

CREATE OR REPLACE VIEW product_revenue_contribution AS
WITH product_totals AS (
    SELECT
        rp.period_start,
        p.product_id,
        p.product_name,

        SUM(rt.units) AS units,
        SUM(rt.revenue) AS revenue,
        SUM(rt.gross_profit) AS gross_profit

    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    JOIN products p
        ON p.product_id = rt.product_id

    GROUP BY
        rp.period_start,
        p.product_id,
        p.product_name
),
period_totals AS (
    SELECT
        period_start,
        SUM(revenue) AS period_revenue
    FROM product_totals
    GROUP BY period_start
)
SELECT
    p.period_start,
    p.product_id,
    p.product_name,
    p.units,
    p.revenue,
    p.gross_profit,

    p.revenue / NULLIF(t.period_revenue, 0)
        AS revenue_share,

    p.gross_profit / NULLIF(p.revenue, 0)
        AS gross_margin

FROM product_totals p
JOIN period_totals t
    ON t.period_start = p.period_start;

-- ============================================================================
-- 9. CUSTOMER CONCENTRATION
-- ============================================================================

CREATE OR REPLACE VIEW customer_concentration AS
WITH customer_revenue AS (
    SELECT
        rp.period_start,
        c.customer_id,
        c.customer_name,
        SUM(rt.revenue) AS revenue

    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    JOIN customers c
        ON c.customer_id = rt.customer_id

    GROUP BY
        rp.period_start,
        c.customer_id,
        c.customer_name
),
shares AS (
    SELECT
        period_start,
        customer_id,
        customer_name,
        revenue,

        revenue / NULLIF(
            SUM(revenue) OVER (
                PARTITION BY period_start
            ),
            0
        ) AS revenue_share

    FROM customer_revenue
)
SELECT
    period_start,

    COUNT(*) AS customer_count,

    MAX(revenue_share) AS largest_customer_share,

    SUM(revenue_share * revenue_share) AS hhi,

    SUM(
        CASE
            WHEN customer_rank <= 5
            THEN revenue_share
            ELSE 0
        END
    ) AS top_five_share

FROM (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY period_start
            ORDER BY revenue DESC
        ) AS customer_rank
    FROM shares
) ranked

GROUP BY period_start;

-- ============================================================================
-- 10. REVENUE DECOMPOSITION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_revenue_decomposition(
    p_previous_period DATE,
    p_current_period DATE
)
RETURNS TABLE (
    previous_revenue NUMERIC,
    current_revenue NUMERIC,
    revenue_change NUMERIC,
    volume_effect NUMERIC,
    mix_effect NUMERIC,
    price_effect NUMERIC,
    reconciliation_difference NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_q0 NUMERIC;
    v_q1 NUMERIC;
    v_old_revenue NUMERIC;
    v_new_revenue NUMERIC;
    v_baseline_price NUMERIC;
    v_volume NUMERIC;
    v_mix NUMERIC;
    v_price NUMERIC;
BEGIN
    IF p_previous_period >= p_current_period THEN
        RAISE EXCEPTION
            'Previous period must precede current period.';
    END IF;

    IF p_previous_period <>
        date_trunc('month', p_previous_period)::DATE
       OR p_current_period <>
        date_trunc('month', p_current_period)::DATE THEN
        RAISE EXCEPTION 'Period parameters must be month starts.';
    END IF;

    SELECT
        COALESCE(SUM(rt.units), 0),
        COALESCE(SUM(rt.revenue), 0)
    INTO
        v_q0,
        v_old_revenue
    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    WHERE rp.period_start = p_previous_period;

    SELECT
        COALESCE(SUM(rt.units), 0),
        COALESCE(SUM(rt.revenue), 0)
    INTO
        v_q1,
        v_new_revenue
    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    WHERE rp.period_start = p_current_period;

    IF v_q0 <= 0 OR v_q1 <= 0 THEN
        RAISE EXCEPTION
            'Both periods require positive units.';
    END IF;

    WITH product_totals AS (
        SELECT
            p.product_id,

            SUM(rt.units) FILTER (
                WHERE rp.period_start = p_previous_period
            ) AS q0,

            SUM(rt.units) FILTER (
                WHERE rp.period_start = p_current_period
            ) AS q1,

            SUM(rt.revenue) FILTER (
                WHERE rp.period_start = p_previous_period
            ) AS r0,

            SUM(rt.revenue) FILTER (
                WHERE rp.period_start = p_current_period
            ) AS r1

        FROM products p
        LEFT JOIN revenue_transactions rt
            ON rt.product_id = p.product_id
        LEFT JOIN reporting_periods rp
            ON rp.period_id = rt.period_id
           AND rp.period_start IN (
               p_previous_period,
               p_current_period
           )

        GROUP BY p.product_id
    ),
    product_shares AS (
        SELECT
            product_id,

            COALESCE(q0, 0) / v_q0 AS s0,
            COALESCE(q1, 0) / v_q1 AS s1,

            CASE
                WHEN COALESCE(q0, 0) > 0
                THEN COALESCE(r0, 0) / q0
                ELSE 0
            END AS p0,

            CASE
                WHEN COALESCE(q1, 0) > 0
                THEN COALESCE(r1, 0) / q1
                ELSE 0
            END AS p1

        FROM product_totals
    )
    SELECT
        SUM(s0 * p0),
        SUM((s1 - s0) * p0),
        SUM(s1 * (p1 - p0))
    INTO
        v_baseline_price,
        v_mix,
        v_price
    FROM product_shares;

    v_volume := (v_q1 - v_q0) * v_baseline_price;

    RETURN QUERY
    SELECT
        v_old_revenue,
        v_new_revenue,
        v_new_revenue - v_old_revenue,
        v_volume,
        v_q1 * v_mix,
        v_q1 * v_price,
        (v_new_revenue - v_old_revenue)
            - (v_volume + v_q1 * v_mix + v_q1 * v_price);
END;
$$;

-- ============================================================================
-- 11. MONTHLY GROWTH FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION get_revenue_growth(
    p_previous DATE,
    p_current DATE
)
RETURNS TABLE (
    previous_revenue NUMERIC,
    current_revenue NUMERIC,
    revenue_change NUMERIC,
    growth_rate NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    IF p_previous >= p_current THEN
        RAISE EXCEPTION
            'Invalid period comparison.';
    END IF;

    RETURN QUERY
    WITH revenue AS (
        SELECT
            rp.period_start,
            SUM(rt.revenue) AS amount
        FROM reporting_periods rp
        JOIN revenue_transactions rt
            ON rt.period_id = rp.period_id
        WHERE rp.period_start IN (p_previous, p_current)
        GROUP BY rp.period_start
    ),
    paired AS (
        SELECT
            MAX(amount) FILTER (
                WHERE period_start = p_previous
            ) AS old_amount,

            MAX(amount) FILTER (
                WHERE period_start = p_current
            ) AS new_amount
        FROM revenue
    )
    SELECT
        old_amount,
        new_amount,
        new_amount - old_amount,

        CASE
            WHEN old_amount > 0
            THEN (new_amount - old_amount) / old_amount
            ELSE NULL
        END

    FROM paired;
END;
$$;

-- ============================================================================
-- 12. REPORTING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE generate_revenue_audit(
    p_username VARCHAR,
    p_period DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_role VARCHAR;
    v_revenue NUMERIC;
BEGIN
    SELECT role_name
    INTO v_role
    FROM analytical_users
    WHERE username = p_username
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'User is inactive or not registered.';
    END IF;

    IF v_role NOT IN ('ANALYST', 'MANAGER', 'FINANCE_ADMIN', 'AUDITOR') THEN
        RAISE EXCEPTION 'User does not have reporting permission.';
    END IF;

    SELECT SUM(rt.revenue)
    INTO v_revenue
    FROM revenue_transactions rt
    JOIN reporting_periods rp
        ON rp.period_id = rt.period_id
    WHERE rp.period_start = p_period;

    IF v_revenue IS NULL THEN
        RAISE EXCEPTION 'No revenue data for requested period.';
    END IF;

    INSERT INTO report_audit (
        username,
        operation,
        period_start,
        details
    )
    VALUES (
        p_username,
        'GENERATE_REVENUE_REPORT',
        p_period,
        jsonb_build_object(
            'revenue',
            v_revenue,
            'currency',
            'INR'
        )
    );
END;
$$;

-- ============================================================================
-- 13. SAMPLE MASTER DATA
-- ============================================================================

INSERT INTO products (
    product_code,
    product_name,
    category
)
VALUES
    ('PRD-CLOUD', 'Cloud', 'Technology'),
    ('PRD-SOFT', 'Software', 'Technology'),
    ('PRD-HARD', 'Hardware', 'Equipment'),
    ('PRD-SERV', 'Services', 'Professional Services')
ON CONFLICT (product_code) DO NOTHING;

INSERT INTO regions (region_code, region_name)
VALUES
    ('NORTH', 'North'),
    ('SOUTH', 'South'),
    ('EAST', 'East'),
    ('WEST', 'West')
ON CONFLICT (region_code) DO NOTHING;

INSERT INTO customers (
    customer_code,
    customer_name,
    customer_segment,
    region_id
)
SELECT
    data.customer_code,
    data.customer_name,
    data.customer_segment,
    r.region_id
FROM (
    VALUES
        ('CUS-A', 'Customer A', 'ENTERPRISE', 'NORTH'),
        ('CUS-B', 'Customer B', 'MID_MARKET', 'SOUTH'),
        ('CUS-C', 'Customer C', 'SMB', 'EAST'),
        ('CUS-D', 'Customer D', 'ENTERPRISE', 'WEST')
) AS data(
    customer_code,
    customer_name,
    customer_segment,
    region_code
)
JOIN regions r
    ON r.region_code = data.region_code
ON CONFLICT (customer_code) DO NOTHING;

INSERT INTO reporting_periods (
    period_start,
    period_end,
    fiscal_year,
    fiscal_quarter
)
SELECT
    month_start::DATE,
    (month_start + INTERVAL '1 month - 1 day')::DATE,
    EXTRACT(YEAR FROM month_start)::INTEGER,
    EXTRACT(QUARTER FROM month_start)::INTEGER
FROM generate_series(
    DATE '2026-01-01',
    DATE '2026-04-01',
    INTERVAL '1 month'
) AS month_start
ON CONFLICT (period_start) DO NOTHING;

INSERT INTO analytical_users (username, role_name)
VALUES
    ('revenue_analyst', 'ANALYST'),
    ('finance_manager', 'MANAGER'),
    ('finance_admin', 'FINANCE_ADMIN'),
    ('internal_auditor', 'AUDITOR')
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- 14. SAMPLE REVENUE TRANSACTIONS
-- ============================================================================

INSERT INTO revenue_transactions (
    transaction_reference,
    period_id,
    product_id,
    region_id,
    customer_id,
    units,
    list_price,
    discount_rate,
    unit_cost,
    transaction_date
)
SELECT
    data.reference,
    rp.period_id,
    p.product_id,
    r.region_id,
    c.customer_id,
    data.units,
    data.list_price,
    data.discount_rate,
    data.unit_cost,
    (rp.period_start + INTERVAL '10 days')::DATE

FROM (
    VALUES
        ('TX-001','2026-01-01','PRD-CLOUD','NORTH','CUS-A',100,1200,.05,600),
        ('TX-002','2026-01-01','PRD-SOFT','SOUTH','CUS-B',180,500,.10,180),
        ('TX-003','2026-01-01','PRD-HARD','EAST','CUS-C',250,300,.08,190),
        ('TX-004','2026-01-01','PRD-SERV','WEST','CUS-D',90,900,.05,400),

        ('TX-005','2026-02-01','PRD-CLOUD','NORTH','CUS-A',115,1250,.04,600),
        ('TX-006','2026-02-01','PRD-SOFT','SOUTH','CUS-B',200,520,.08,180),
        ('TX-007','2026-02-01','PRD-HARD','EAST','CUS-C',230,310,.05,190),
        ('TX-008','2026-02-01','PRD-SERV','WEST','CUS-D',105,920,.04,400),

        ('TX-009','2026-03-01','PRD-CLOUD','NORTH','CUS-A',130,1300,.03,600),
        ('TX-010','2026-03-01','PRD-SOFT','SOUTH','CUS-B',220,540,.07,180),
        ('TX-011','2026-03-01','PRD-HARD','EAST','CUS-C',245,320,.05,190),
        ('TX-012','2026-03-01','PRD-SERV','WEST','CUS-D',115,950,.03,400),

        ('TX-013','2026-04-01','PRD-CLOUD','NORTH','CUS-A',145,1350,.03,600),
        ('TX-014','2026-04-01','PRD-SOFT','SOUTH','CUS-B',240,550,.06,180),
        ('TX-015','2026-04-01','PRD-HARD','EAST','CUS-C',260,330,.06,190),
        ('TX-016','2026-04-01','PRD-SERV','WEST','CUS-D',130,970,.04,400)
) AS data(
    reference,
    period,
    product_code,
    region_code,
    customer_code,
    units,
    list_price,
    discount_rate,
    unit_cost
)

JOIN reporting_periods rp
    ON rp.period_start = data.period::DATE

JOIN products p
    ON p.product_code = data.product_code

JOIN regions r
    ON r.region_code = data.region_code

JOIN customers c
    ON c.customer_code = data.customer_code

ON CONFLICT (transaction_reference) DO NOTHING;

-- ============================================================================
-- 15. REVENUE RETRIEVAL
-- ============================================================================

SELECT
    period_start,
    SUM(total_units) AS units,
    SUM(total_revenue) AS revenue,
    SUM(gross_profit) AS gross_profit
FROM monthly_revenue_summary
GROUP BY period_start
ORDER BY period_start;

-- ============================================================================
-- 16. PERIOD-OVER-PERIOD GROWTH
-- ============================================================================

SELECT *
FROM monthly_growth_analysis
ORDER BY period_start;

-- Explicit March-to-April comparison.
SELECT *
FROM get_revenue_growth(
    DATE '2026-03-01',
    DATE '2026-04-01'
);

-- ============================================================================
-- 17. VOLUME, MIX AND PRICE DECOMPOSITION
-- ============================================================================

SELECT *
FROM calculate_revenue_decomposition(
    DATE '2026-03-01',
    DATE '2026-04-01'
);

-- ============================================================================
-- 18. PRODUCT CONTRIBUTION
-- ============================================================================

SELECT
    period_start,
    product_name,
    revenue,
    revenue_share,
    gross_profit,
    gross_margin
FROM product_revenue_contribution
WHERE period_start = DATE '2026-04-01'
ORDER BY revenue DESC;

-- ============================================================================
-- 19. REGIONAL PERFORMANCE
-- ============================================================================

SELECT
    rp.period_start,
    r.region_name,
    SUM(rt.units) AS units,
    SUM(rt.revenue) AS revenue,
    SUM(rt.gross_profit) AS gross_profit,

    SUM(rt.gross_profit) /
        NULLIF(SUM(rt.revenue), 0) AS gross_margin

FROM revenue_transactions rt
JOIN reporting_periods rp
    ON rp.period_id = rt.period_id
JOIN regions r
    ON r.region_id = rt.region_id

WHERE rp.period_start = DATE '2026-04-01'

GROUP BY rp.period_start, r.region_name
ORDER BY revenue DESC;

-- ============================================================================
-- 20. CUSTOMER CONCENTRATION
-- ============================================================================

SELECT *
FROM customer_concentration
ORDER BY period_start;

-- Individual customer contribution.
SELECT
    c.customer_name,
    SUM(rt.revenue) AS revenue,

    SUM(rt.revenue) /
        NULLIF(
            SUM(SUM(rt.revenue)) OVER (),
            0
        ) AS revenue_share

FROM revenue_transactions rt
JOIN reporting_periods rp
    ON rp.period_id = rt.period_id
JOIN customers c
    ON c.customer_id = rt.customer_id

WHERE rp.period_start = DATE '2026-04-01'

GROUP BY c.customer_name
ORDER BY revenue DESC;

-- ============================================================================
-- 21. VALIDATION: FINANCIAL RECONCILIATION
-- ============================================================================

SELECT
    transaction_reference,
    revenue,
    gross_profit,
    ROUND(
        revenue - variable_cost - gross_profit,
        4
    ) AS reconciliation_difference
FROM revenue_transactions
WHERE ABS(
    revenue - variable_cost - gross_profit
) > 0.0001;

-- Expected result: zero rows.

-- ============================================================================
-- 22. VALIDATION: REVENUE DECOMPOSITION
-- ============================================================================

SELECT
    *,
    CASE
        WHEN ABS(reconciliation_difference) < 0.0001
        THEN 'RECONCILED'
        ELSE 'FAILED'
    END AS validation_status

FROM calculate_revenue_decomposition(
    DATE '2026-03-01',
    DATE '2026-04-01'
);

-- ============================================================================
-- 23. REPORTING WORKFLOW AND AUDIT
-- ============================================================================

CALL generate_revenue_audit(
    'finance_manager',
    DATE '2026-04-01'
);

SELECT
    audit_id,
    username,
    operation,
    period_start,
    details,
    executed_at
FROM report_audit
ORDER BY audit_id DESC;

-- ============================================================================
-- 24. FAILURE CASES
-- ============================================================================
-- These statements are intentionally not executed.
--
-- Negative units:
-- INSERT INTO revenue_transactions (..., units, ...)
-- VALUES (..., -5, ...);
--
-- Discount above 100 percent:
-- INSERT INTO revenue_transactions (..., discount_rate, ...)
-- VALUES (..., 1.5, ...);
--
-- Transaction in a closed period:
-- UPDATE reporting_periods
-- SET status = 'CLOSED'
-- WHERE period_start = DATE '2026-04-01';
--
-- A subsequent transaction insertion into that period is rejected.
--
-- Duplicate transaction reference:
-- Rejected by the UNIQUE constraint.
--
-- Missing product, region or customer:
-- Rejected by foreign-key constraints.
--
-- Reporting with an inactive user:
-- Rejected by the reporting procedure.

-- ============================================================================
-- 25. TRANSACTIONAL PERIOD CLOSURE EXAMPLE
-- ============================================================================
-- This example demonstrates controlled period closure.
-- It is rolled back so the sample reporting periods remain open.

SAVEPOINT before_period_closure;

UPDATE reporting_periods
SET status = 'CLOSED'
WHERE period_start = DATE '2026-01-01'
  AND status = 'OPEN';

ROLLBACK TO SAVEPOINT before_period_closure;

COMMIT;

-- ============================================================================
-- 26. FINAL PERFORMANCE REPORT
-- ============================================================================

SELECT
    period_start,
    revenue,
    revenue_change,
    revenue_growth_rate,
    gross_margin
FROM monthly_growth_analysis
ORDER BY period_start DESC
LIMIT 12;
