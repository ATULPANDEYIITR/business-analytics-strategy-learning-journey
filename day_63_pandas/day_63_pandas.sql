DROP SCHEMA IF EXISTS pandas_learning CASCADE;
CREATE SCHEMA pandas_learning;

SET search_path TO pandas_learning;

CREATE TYPE data_quality_status AS ENUM (
    'VALID',
    'INVALID'
);

CREATE TABLE sales_orders (
    order_id       integer PRIMARY KEY,
    order_date     date NOT NULL,
    region         text NOT NULL,
    product        text NOT NULL,
    category       text NOT NULL,
    units          integer NOT NULL CHECK (units > 0),
    unit_price     numeric(14,2) NOT NULL CHECK (unit_price > 0),
    discount       numeric(5,4) NOT NULL CHECK (discount >= 0 AND discount < 1),
    customer       text NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE customer_dimension (
    customer       text PRIMARY KEY,
    segment        text NOT NULL CHECK (segment IN ('Enterprise', 'Mid-Market', 'SMB')),
    account_manager text NOT NULL
);

CREATE TABLE data_quality_audit (
    audit_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id       integer NOT NULL,
    status         data_quality_status NOT NULL,
    reason         text,
    checked_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE transformation_runs (
    run_id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_started_at timestamptz NOT NULL DEFAULT now(),
    source_rows    integer NOT NULL CHECK (source_rows >= 0),
    valid_rows     integer NOT NULL CHECK (valid_rows >= 0),
    status         data_quality_status NOT NULL
);

CREATE INDEX idx_sales_orders_date
    ON sales_orders (order_date);

CREATE INDEX idx_sales_orders_region_category
    ON sales_orders (region, category);

CREATE INDEX idx_sales_orders_customer
    ON sales_orders (customer);

CREATE INDEX idx_quality_audit_order
    ON data_quality_audit (order_id, checked_at DESC);

INSERT INTO customer_dimension (
    customer,
    segment,
    account_manager
)
VALUES
    ('Apex Ltd', 'Enterprise', 'Neha'),
    ('Beta Corp', 'Enterprise', 'Ravi'),
    ('Gamma Pvt', 'Mid-Market', 'Meera'),
    ('Delta Inc', 'Enterprise', 'Arjun');

INSERT INTO sales_orders (
    order_id,
    order_date,
    region,
    product,
    category,
    units,
    unit_price,
    discount,
    customer
)
VALUES
    (1001, '2026-01-03', 'North', 'Laptop', 'Electronics', 2, 75000, 0.05, 'Apex Ltd'),
    (1002, '2026-01-05', 'South', 'Monitor', 'Electronics', 4, 18000, 0.10, 'Beta Corp'),
    (1003, '2026-01-08', 'West', 'Desk', 'Furniture', 3, 12000, 0.00, 'Gamma Pvt'),
    (1004, '2026-01-11', 'North', 'Chair', 'Furniture', 10, 6500, 0.08, 'Apex Ltd'),
    (1005, '2026-01-13', 'East', 'Laptop', 'Electronics', 1, 82000, 0.05, 'Delta Inc'),
    (1006, '2026-01-18', 'South', 'Desk', 'Furniture', 2, 13500, 0.03, 'Beta Corp'),
    (1007, '2026-01-20', 'West', 'Keyboard', 'Accessories', 15, 2200, 0.00, 'Gamma Pvt'),
    (1008, '2026-01-23', 'East', 'Monitor', 'Electronics', 5, 19500, 0.12, 'Delta Inc'),
    (1009, '2026-02-02', 'North', 'Laptop', 'Electronics', 3, 76000, 0.04, 'Apex Ltd'),
    (1010, '2026-02-04', 'South', 'Chair', 'Furniture', 8, 6200, 0.06, 'Beta Corp'),
    (1011, '2026-02-09', 'West', 'Monitor', 'Electronics', 2, 18500, 0.02, 'Gamma Pvt'),
    (1012, '2026-02-15', 'East', 'Keyboard', 'Accessories', 20, 2100, 0.05, 'Delta Inc');

CREATE OR REPLACE FUNCTION calculate_net_sales(
    p_units integer,
    p_unit_price numeric,
    p_discount numeric
)
RETURNS numeric
LANGUAGE sql
IMMUTABLE
STRICT
AS $$
    SELECT round(
        p_units * p_unit_price * (1 - p_discount),
        2
    );
$$;

CREATE OR REPLACE FUNCTION audit_sales_order()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.units <= 0 THEN
        INSERT INTO data_quality_audit (
            order_id,
            status,
            reason
        )
        VALUES (
            NEW.order_id,
            'INVALID',
            'Units must be positive'
        );
        RAISE EXCEPTION 'Invalid units for order %', NEW.order_id;
    END IF;

    IF NEW.discount < 0 OR NEW.discount >= 1 THEN
        INSERT INTO data_quality_audit (
            order_id,
            status,
            reason
        )
        VALUES (
            NEW.order_id,
            'INVALID',
            'Discount must be in [0, 1)'
        );
        RAISE EXCEPTION 'Invalid discount for order %', NEW.order_id;
    END IF;

    INSERT INTO data_quality_audit (
        order_id,
        status,
        reason
    )
    VALUES (
        NEW.order_id,
        'VALID',
        'Row passed database validation'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_sales_order
BEFORE INSERT OR UPDATE ON sales_orders
FOR EACH ROW
EXECUTE FUNCTION audit_sales_order();

CREATE VIEW enriched_sales AS
SELECT
    s.order_id,
    s.order_date,
    s.region,
    s.product,
    s.category,
    s.units,
    s.unit_price,
    s.discount,
    s.customer,
    s.units * s.unit_price AS gross_sales,
    round(
        s.units * s.unit_price * s.discount,
        2
    ) AS discount_amount,
    calculate_net_sales(
        s.units,
        s.unit_price,
        s.discount
    ) AS net_sales,
    to_char(s.order_date, 'YYYY-MM') AS month,
    extract(quarter FROM s.order_date)::integer AS quarter,
    (
        calculate_net_sales(
            s.units,
            s.unit_price,
            s.discount
        ) >= 100000
    ) AS high_value
FROM sales_orders s;

CREATE VIEW sales_with_customers AS
SELECT
    e.*,
    c.segment,
    c.account_manager
FROM enriched_sales e
LEFT JOIN customer_dimension c
    ON c.customer = e.customer;

CREATE OR REPLACE FUNCTION run_quality_check()
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
    v_source_rows integer;
    v_valid_rows integer;
    v_run_id bigint;
BEGIN
    SELECT count(*)::integer
    INTO v_source_rows
    FROM sales_orders;

    SELECT count(*)::integer
    INTO v_valid_rows
    FROM enriched_sales
    WHERE net_sales >= 0;

    INSERT INTO transformation_runs (
        source_rows,
        valid_rows,
        status
    )
    VALUES (
        v_source_rows,
        v_valid_rows,
        CASE
            WHEN v_source_rows = v_valid_rows THEN 'VALID'
            ELSE 'INVALID'
        END
    )
    RETURNING run_id INTO v_run_id;

    RETURN v_run_id;
END;
$$;

CREATE OR REPLACE FUNCTION region_category_report()
RETURNS TABLE (
    region text,
    category text,
    orders bigint,
    units bigint,
    net_sales numeric,
    average_order_value numeric
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        e.region,
        e.category,
        count(DISTINCT e.order_id),
        sum(e.units)::bigint,
        round(sum(e.net_sales), 2),
        round(avg(e.net_sales), 2)
    FROM enriched_sales e
    GROUP BY e.region, e.category
    ORDER BY e.region, sum(e.net_sales) DESC;
$$;

BEGIN;

SELECT run_quality_check();

COMMIT;

SELECT
    order_id,
    region,
    category,
    net_sales
FROM enriched_sales
WHERE category = 'Electronics'
  AND net_sales >= 50000
ORDER BY net_sales DESC, order_id;

SELECT
    region,
    category,
    count(*) AS orders,
    sum(units) AS units,
    round(sum(net_sales), 2) AS net_sales
FROM enriched_sales
GROUP BY region, category
ORDER BY region, net_sales DESC;

SELECT
    month,
    round(sum(net_sales), 2) AS monthly_net_sales,
    count(*) AS order_count
FROM enriched_sales
GROUP BY month
ORDER BY month;

SELECT
    region,
    round(sum(net_sales), 2) AS net_sales
FROM enriched_sales
GROUP BY region
ORDER BY net_sales DESC;

WITH ranked_orders AS (
    SELECT
        e.*,
        dense_rank() OVER (
            PARTITION BY e.region
            ORDER BY e.net_sales DESC
        ) AS regional_rank
    FROM enriched_sales e
)
SELECT
    region,
    order_id,
    product,
    net_sales,
    regional_rank
FROM ranked_orders
WHERE regional_rank <= 2
ORDER BY region, regional_rank, order_id;

SELECT
    order_id,
    customer,
    segment,
    account_manager,
    net_sales
FROM sales_with_customers
ORDER BY net_sales DESC;

WITH monthly AS (
    SELECT
        month,
        sum(net_sales) AS monthly_sales
    FROM enriched_sales
    GROUP BY month
)
SELECT
    month,
    round(monthly_sales, 2) AS monthly_sales,
    round(
        avg(monthly_sales) OVER (
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS rolling_three_month_average
FROM monthly
ORDER BY month;

SELECT
    order_id,
    status,
    reason,
    checked_at
FROM data_quality_audit
ORDER BY checked_at DESC, audit_id DESC;

SELECT *
FROM region_category_report();

SELECT
    run_id,
    source_rows,
    valid_rows,
    status,
    run_started_at
FROM transformation_runs
ORDER BY run_id DESC;

DO $$
BEGIN
    BEGIN
        INSERT INTO sales_orders (
            order_id,
            order_date,
            region,
            product,
            category,
            units,
            unit_price,
            discount,
            customer
        )
        VALUES (
            9999,
            '2026-02-20',
            'North',
            'Invalid Product',
            'Electronics',
            1,
            1000,
            1.0,
            'Apex Ltd'
        );
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid discount rejected by database constraint';
        WHEN OTHERS THEN
            RAISE NOTICE 'Invalid test row rejected: %', SQLERRM;
    END;
END;
$$;
