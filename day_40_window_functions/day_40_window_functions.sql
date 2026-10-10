-- PostgreSQL 14+
-- Window functions: ranking, running totals, moving frames, and period comparisons.
-- The transaction keeps the schema and demonstration data together.

BEGIN;

DROP VIEW IF EXISTS monthly_sales_window_report;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS salespeople;
DROP TABLE IF EXISTS regions;

CREATE TABLE regions (
    region_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
        CHECK (length(trim(region_name)) > 0)
);

CREATE TABLE salespeople (
    salesperson_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salesperson_name TEXT NOT NULL
        CHECK (length(trim(salesperson_name)) > 0),
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (salesperson_name, region_id)
);

CREATE TABLE sales (
    sale_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    salesperson_id BIGINT NOT NULL REFERENCES salespeople(salesperson_id),
    sale_month DATE NOT NULL
        CHECK (
            EXTRACT(DAY FROM sale_month) = 1
            AND sale_month = date_trunc('month', sale_month)::date
        ),
    revenue NUMERIC(14, 2) NOT NULL CHECK (revenue >= 0),
    units INTEGER NOT NULL CHECK (units >= 0),
    UNIQUE (salesperson_id, sale_month)
);

INSERT INTO regions (region_name)
VALUES ('North'), ('South');

INSERT INTO salespeople (salesperson_name, region_id)
SELECT source.salesperson_name, region.region_id
FROM (
    VALUES
        ('Asha', 'North'),
        ('Ravi', 'North'),
        ('Meera', 'North'),
        ('Kabir', 'South'),
        ('Nila', 'South')
) AS source(salesperson_name, region_name)
JOIN regions AS region
  ON region.region_name = source.region_name;

INSERT INTO sales (salesperson_id, sale_month, revenue, units)
SELECT salesperson.salesperson_id, source.sale_month::date,
       source.revenue, source.units
FROM (
    VALUES
        ('Asha', '2026-01-01', 12000.00, 12),
        ('Ravi', '2026-01-01', 12000.00, 10),
        ('Meera', '2026-01-01',  9000.00,  9),
        ('Asha', '2026-02-01', 15000.00, 15),
        ('Ravi', '2026-02-01', 11000.00, 11),
        ('Meera', '2026-02-01', 11000.00, 10),
        ('Asha', '2026-03-01', 14000.00, 14),
        ('Ravi', '2026-03-01', 16000.00, 16),
        ('Meera', '2026-03-01', 10000.00, 10),
        ('Kabir', '2026-01-01',  8000.00,  8),
        ('Nila', '2026-01-01', 10000.00, 10),
        ('Kabir', '2026-02-01', 12000.00, 12),
        ('Nila', '2026-02-01', 10000.00,  9),
        ('Kabir', '2026-03-01', 12000.00, 11),
        ('Nila', '2026-03-01', 14000.00, 14)
) AS source(name, sale_month, revenue, units)
JOIN salespeople AS salesperson
  ON salesperson.salesperson_name = source.name;

-- Supports chronological partition scans for regional and salesperson reports.
CREATE INDEX sales_month_person_idx
    ON sales (sale_month, salesperson_id);

CREATE INDEX sales_revenue_idx
    ON sales (revenue DESC, salesperson_id);

CREATE VIEW monthly_sales_window_report AS
WITH base AS (
    SELECT
        s.sale_id,
        r.region_name,
        p.salesperson_name,
        s.sale_month,
        s.revenue,
        s.units
    FROM sales AS s
    JOIN salespeople AS p
      ON p.salesperson_id = s.salesperson_id
    JOIN regions AS r
      ON r.region_id = p.region_id
),
analytics AS (
    SELECT
        base.*,

        -- Ranking order is revenue descending. Tied values share RANK values.
        ROW_NUMBER() OVER (
            PARTITION BY region_name
            ORDER BY revenue DESC, sale_id
        ) AS revenue_row_number,

        RANK() OVER (
            PARTITION BY region_name
            ORDER BY revenue DESC
        ) AS revenue_rank,

        DENSE_RANK() OVER (
            PARTITION BY region_name
            ORDER BY revenue DESC
        ) AS revenue_dense_rank,

        -- Running totals use chronological ordering, a separate analytical order.
        SUM(revenue) OVER (
            PARTITION BY region_name
            ORDER BY sale_month, sale_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_region_revenue,

        SUM(revenue) OVER (
            PARTITION BY salesperson_name
            ORDER BY sale_month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_salesperson_revenue,

        AVG(revenue) OVER (
            PARTITION BY region_name
            ORDER BY sale_month, sale_id
            ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
        ) AS trailing_two_row_average,

        LAG(revenue) OVER (
            PARTITION BY salesperson_name
            ORDER BY sale_month
        ) AS previous_salesperson_revenue,

        LEAD(revenue) OVER (
            PARTITION BY salesperson_name
            ORDER BY sale_month
        ) AS next_salesperson_revenue,

        PERCENT_RANK() OVER (
            PARTITION BY region_name
            ORDER BY revenue
        ) AS revenue_percent_rank,

        CUME_DIST() OVER (
            PARTITION BY region_name
            ORDER BY revenue
        ) AS revenue_cumulative_distribution,

        NTILE(3) OVER (
            PARTITION BY region_name
            ORDER BY revenue DESC, sale_id
        ) AS revenue_tercile
    FROM base
)
SELECT
    analytics.*,
    CASE
        WHEN previous_salesperson_revenue IS NULL
          OR previous_salesperson_revenue = 0
        THEN NULL
        ELSE ROUND(
            (revenue - previous_salesperson_revenue)
            * 100.0 / previous_salesperson_revenue,
            2
        )
    END AS salesperson_monthly_change_pct
FROM analytics;

-- All window expressions retain rows rather than collapsing them like GROUP BY.
SELECT
    region_name,
    salesperson_name,
    sale_month,
    revenue,
    revenue_row_number,
    revenue_rank,
    revenue_dense_rank,
    running_region_revenue,
    running_salesperson_revenue,
    ROUND(trailing_two_row_average, 2) AS trailing_two_row_average,
    previous_salesperson_revenue,
    next_salesperson_revenue,
    salesperson_monthly_change_pct,
    ROUND(revenue_percent_rank::numeric, 4) AS revenue_percent_rank,
    ROUND(revenue_cumulative_distribution::numeric, 4)
        AS revenue_cumulative_distribution,
    revenue_tercile
FROM monthly_sales_window_report
ORDER BY region_name, sale_month, salesperson_name;

-- Top-ranked sales in each region. Filtering the window result requires a
-- subquery or CTE because window functions cannot appear in WHERE directly.
WITH ranked AS (
    SELECT
        region_name,
        salesperson_name,
        sale_month,
        revenue,
        RANK() OVER (
            PARTITION BY region_name
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM monthly_sales_window_report
)
SELECT region_name, salesperson_name, sale_month, revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 2
ORDER BY region_name, revenue_rank, salesperson_name;

-- Compare each salesperson's quarter-to-date contribution with their total.
WITH totals AS (
    SELECT
        salesperson_name,
        sale_month,
        revenue,
        SUM(revenue) OVER (
            PARTITION BY salesperson_name
        ) AS salesperson_total,
        SUM(revenue) OVER (
            PARTITION BY salesperson_name
            ORDER BY sale_month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM monthly_sales_window_report
)
SELECT
    salesperson_name,
    sale_month,
    revenue,
    cumulative_revenue,
    salesperson_total,
    ROUND(
        cumulative_revenue * 100.0
        / NULLIF(salesperson_total, 0),
        2
    ) AS cumulative_share_pct
FROM totals
ORDER BY salesperson_name, sale_month;

-- Duplicate salesperson-month pairs and negative revenue are rejected by
-- database constraints rather than silently producing ambiguous analytics.
-- The following invalid inserts are intentionally omitted so the full script
-- remains executable as one transaction.

COMMIT;
