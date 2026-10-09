#!/usr/bin/env python3
"""
Common Table Expressions (CTEs) for complex analytical workflows.

This executable module models an e-commerce analytics workload using Python
and SQLite. It mirrors the logical stages commonly expressed as SQL CTEs:
filtering, aggregation, ranking, recursive traversal, cohort analysis,
period-over-period comparisons, and dependency-aware reporting.

Run with Python 3.10 or later. No third-party packages are required.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    signup_date TEXT NOT NULL
        CHECK (date(signup_date) IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    list_price REAL NOT NULL CHECK (list_price >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL CHECK (date(order_date) IS NOT NULL),
    status TEXT NOT NULL CHECK (
        status IN ('completed', 'cancelled', 'refunded', 'pending')
    )
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_date_status
    ON orders(order_date, status);

CREATE INDEX IF NOT EXISTS idx_orders_customer_date
    ON orders(customer_id, order_date);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category_id);
"""


SAMPLE_DATA = """
INSERT OR IGNORE INTO customers
    (customer_id, customer_name, region, signup_date)
VALUES
    (1, 'Asha Sharma', 'North', '2025-01-10'),
    (2, 'Rohan Verma', 'South', '2025-02-14'),
    (3, 'Meera Singh', 'North', '2025-03-02'),
    (4, 'Kabir Rao', 'West', '2025-04-20'),
    (5, 'Ira Das', 'South', '2025-05-01');

INSERT OR IGNORE INTO categories
    (category_id, category_name, parent_category_id)
VALUES
    (1, 'Electronics', NULL),
    (2, 'Computers', 1),
    (3, 'Accessories', 1),
    (4, 'Office Supplies', NULL);

INSERT OR IGNORE INTO products
    (product_id, product_name, category_id, unit_cost, list_price)
VALUES
    (1, 'Laptop', 2, 42000, 60000),
    (2, 'Monitor', 2, 8000, 12000),
    (3, 'Keyboard', 3, 900, 1800),
    (4, 'Notebook', 4, 30, 60);

INSERT OR IGNORE INTO orders
    (order_id, customer_id, order_date, status)
VALUES
    (101, 1, '2025-01-15', 'completed'),
    (102, 1, '2025-02-10', 'completed'),
    (103, 2, '2025-02-18', 'completed'),
    (104, 2, '2025-03-04', 'cancelled'),
    (105, 3, '2025-03-12', 'completed'),
    (106, 3, '2025-04-11', 'completed'),
    (107, 4, '2025-04-25', 'completed'),
    (108, 5, '2025-05-10', 'pending'),
    (109, 1, '2025-05-18', 'refunded'),
    (110, 5, '2025-06-02', 'completed');

INSERT OR IGNORE INTO order_items
    (order_id, product_id, quantity, unit_price)
VALUES
    (101, 1, 1, 60000),
    (101, 3, 2, 1800),
    (102, 2, 1, 12000),
    (103, 3, 3, 1800),
    (104, 1, 1, 60000),
    (105, 1, 1, 58000),
    (105, 4, 10, 60),
    (106, 2, 2, 11500),
    (107, 4, 20, 60),
    (108, 3, 1, 1800),
    (109, 1, 1, 60000),
    (110, 2, 1, 12000);
"""


@dataclass(frozen=True)
class QueryResult:
    """Represent the output of a named analytical stage."""

    name: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]

    def display(self) -> None:
        print(f"\n--- {self.name} ---")
        if not self.rows:
            print("(no rows)")
            return

        widths = [
            max(len(str(self.columns[i])), *(len(str(row[i])) for row in self.rows))
            for i in range(len(self.columns))
        ]
        print(" | ".join(self.columns[i].ljust(widths[i]) for i in range(len(widths))))
        print("-+-".join("-" * width for width in widths))
        for row in self.rows:
            print(" | ".join(str(value).ljust(widths[i]) for i, value in enumerate(row)))


class AnalyticsDatabase:
    """Own the connection and execute reproducible analytical queries."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    @classmethod
    def create_demo(cls) -> "AnalyticsDatabase":
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        connection.executescript(SAMPLE_DATA)
        return cls(connection)

    def query(
        self,
        name: str,
        sql: str,
        parameters: Iterable[Any] = (),
    ) -> QueryResult:
        cursor = self.connection.execute(sql, tuple(parameters))
        rows = cursor.fetchall()
        columns = tuple(item[0] for item in cursor.description or ())
        return QueryResult(
            name=name,
            columns=columns,
            rows=tuple(tuple(row) for row in rows),
        )

    def execute_transaction(self, statements: list[tuple[str, tuple[Any, ...]]]) -> None:
        """Commit every statement together or roll back the complete operation."""
        try:
            with self.connection:
                for sql, parameters in statements:
                    self.connection.execute(sql, parameters)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Analytical data transaction failed: {exc}") from exc

    def close(self) -> None:
        self.connection.close()


def basic_cte(db: AnalyticsDatabase) -> QueryResult:
    """A CTE names an intermediate result used by the outer query."""
    return db.query(
        "Basic CTE: completed order revenue",
        """
        WITH completed_orders AS (
            SELECT order_id, customer_id, order_date
            FROM orders
            WHERE status = 'completed'
        )
        SELECT customer_id,
               COUNT(*) AS completed_order_count,
               MIN(order_date) AS first_completed_order,
               MAX(order_date) AS latest_completed_order
        FROM completed_orders
        GROUP BY customer_id
        ORDER BY completed_order_count DESC, customer_id
        """,
    )


def chained_ctes(db: AnalyticsDatabase) -> QueryResult:
    """Later CTEs can reference earlier CTEs in the same WITH clause."""
    return db.query(
        "Chained CTEs: customer lifetime value",
        """
        WITH
        eligible_orders AS (
            SELECT order_id, customer_id
            FROM orders
            WHERE status = 'completed'
        ),
        order_totals AS (
            SELECT eo.order_id,
                   eo.customer_id,
                   SUM(oi.quantity * oi.unit_price) AS order_value
            FROM eligible_orders AS eo
            JOIN order_items AS oi ON oi.order_id = eo.order_id
            GROUP BY eo.order_id, eo.customer_id
        ),
        customer_value AS (
            SELECT customer_id,
                   COUNT(*) AS order_count,
                   ROUND(SUM(order_value), 2) AS lifetime_revenue,
                   ROUND(AVG(order_value), 2) AS average_order_value
            FROM order_totals
            GROUP BY customer_id
        )
        SELECT c.customer_name,
               COALESCE(cv.order_count, 0) AS order_count,
               COALESCE(cv.lifetime_revenue, 0) AS lifetime_revenue,
               COALESCE(cv.average_order_value, 0) AS average_order_value
        FROM customers AS c
        LEFT JOIN customer_value AS cv USING (customer_id)
        ORDER BY lifetime_revenue DESC, c.customer_id
        """,
    )


def category_profitability(db: AnalyticsDatabase) -> QueryResult:
    """Aggregate item-level margin before ranking product categories."""
    return db.query(
        "Category profitability and ranking",
        """
        WITH
        completed_items AS (
            SELECT oi.product_id,
                   oi.quantity,
                   oi.unit_price,
                   p.unit_cost,
                   p.category_id
            FROM order_items AS oi
            JOIN orders AS o USING (order_id)
            JOIN products AS p USING (product_id)
            WHERE o.status = 'completed'
        ),
        category_metrics AS (
            SELECT c.category_name,
                   SUM(ci.quantity) AS units_sold,
                   ROUND(SUM(ci.quantity * ci.unit_price), 2) AS revenue,
                   ROUND(
                       SUM(ci.quantity * (ci.unit_price - ci.unit_cost)), 2
                   ) AS gross_profit
            FROM completed_items AS ci
            JOIN categories AS c USING (category_id)
            GROUP BY c.category_id, c.category_name
        ),
        ranked_categories AS (
            SELECT *,
                   DENSE_RANK() OVER (
                       ORDER BY gross_profit DESC
                   ) AS profit_rank,
                   ROUND(
                       100.0 * gross_profit / NULLIF(SUM(gross_profit) OVER (), 0),
                       2
                   ) AS profit_share_percent
            FROM category_metrics
        )
        SELECT category_name, units_sold, revenue, gross_profit,
               profit_rank, profit_share_percent
        FROM ranked_categories
        ORDER BY profit_rank, category_name
        """,
    )


def monthly_performance(db: AnalyticsDatabase) -> QueryResult:
    """Compare monthly revenue using a CTE and a window function."""
    return db.query(
        "Monthly revenue and month-over-month change",
        """
        WITH monthly_revenue AS (
            SELECT substr(o.order_date, 1, 7) AS month,
                   SUM(oi.quantity * oi.unit_price) AS revenue
            FROM orders AS o
            JOIN order_items AS oi USING (order_id)
            WHERE o.status = 'completed'
            GROUP BY substr(o.order_date, 1, 7)
        ),
        comparisons AS (
            SELECT month,
                   revenue,
                   LAG(revenue) OVER (ORDER BY month) AS previous_revenue
            FROM monthly_revenue
        )
        SELECT month,
               ROUND(revenue, 2) AS revenue,
               ROUND(previous_revenue, 2) AS previous_revenue,
               ROUND(revenue - previous_revenue, 2) AS revenue_change,
               ROUND(
                   100.0 * (revenue - previous_revenue)
                   / NULLIF(previous_revenue, 0), 2
               ) AS change_percent
        FROM comparisons
        ORDER BY month
        """,
    )


def customer_cohorts(db: AnalyticsDatabase) -> QueryResult:
    """Group customers by first completed purchase and calculate later activity."""
    return db.query(
        "Customer cohort retention",
        """
        WITH
        first_purchase AS (
            SELECT customer_id,
                   MIN(substr(order_date, 1, 7)) AS cohort_month
            FROM orders
            WHERE status = 'completed'
            GROUP BY customer_id
        ),
        active_months AS (
            SELECT DISTINCT customer_id,
                   substr(order_date, 1, 7) AS activity_month
            FROM orders
            WHERE status = 'completed'
        ),
        cohort_activity AS (
            SELECT fp.cohort_month,
                   am.activity_month,
                   (
                       CAST(substr(am.activity_month, 1, 4) AS INTEGER)
                       - CAST(substr(fp.cohort_month, 1, 4) AS INTEGER)
                   ) * 12
                   + CAST(substr(am.activity_month, 6, 2) AS INTEGER)
                   - CAST(substr(fp.cohort_month, 6, 2) AS INTEGER)
                       AS months_after_cohort,
                   COUNT(DISTINCT am.customer_id) AS active_customers
            FROM first_purchase AS fp
            JOIN active_months AS am USING (customer_id)
            GROUP BY fp.cohort_month, am.activity_month
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(*) AS cohort_customers
            FROM first_purchase
            GROUP BY cohort_month
        )
        SELECT ca.cohort_month,
               ca.activity_month,
               ca.months_after_cohort,
               ca.active_customers,
               cs.cohort_customers,
               ROUND(
                   100.0 * ca.active_customers / cs.cohort_customers, 2
               ) AS retention_percent
        FROM cohort_activity AS ca
        JOIN cohort_sizes AS cs USING (cohort_month)
        WHERE ca.months_after_cohort >= 0
        ORDER BY ca.cohort_month, ca.months_after_cohort
        """,
    )


def recursive_category_tree(db: AnalyticsDatabase) -> QueryResult:
    """A recursive CTE traverses a parent-child category hierarchy."""
    return db.query(
        "Recursive CTE: category hierarchy",
        """
        WITH RECURSIVE category_tree(
            category_id, category_name, parent_category_id, depth, path
        ) AS (
            SELECT category_id,
                   category_name,
                   parent_category_id,
                   0,
                   category_name
            FROM categories
            WHERE parent_category_id IS NULL

            UNION ALL

            SELECT child.category_id,
                   child.category_name,
                   child.parent_category_id,
                   parent.depth + 1,
                   parent.path || ' > ' || child.category_name
            FROM categories AS child
            JOIN category_tree AS parent
              ON child.parent_category_id = parent.category_id
            WHERE parent.depth < 20
              AND instr(
                  parent.path,
                  child.category_name
              ) = 0
        )
        SELECT category_id, category_name, parent_category_id, depth, path
        FROM category_tree
        ORDER BY path
        """,
    )


def conditional_metrics(db: AnalyticsDatabase) -> QueryResult:
    """Use separate named stages to calculate order-quality indicators."""
    return db.query(
        "Conditional metrics and status reconciliation",
        """
        WITH
        order_values AS (
            SELECT o.order_id,
                   o.status,
                   SUM(oi.quantity * oi.unit_price) AS order_value
            FROM orders AS o
            JOIN order_items AS oi USING (order_id)
            GROUP BY o.order_id, o.status
        ),
        status_metrics AS (
            SELECT status,
                   COUNT(*) AS order_count,
                   ROUND(SUM(order_value), 2) AS gross_order_value
            FROM order_values
            GROUP BY status
        )
        SELECT status,
               order_count,
               gross_order_value,
               ROUND(
                   100.0 * order_count / SUM(order_count) OVER (), 2
               ) AS order_count_share_percent
        FROM status_metrics
        ORDER BY order_count DESC, status
        """,
    )


def explain_query_plan(db: AnalyticsDatabase) -> QueryResult:
    """Inspect SQLite's plan to see whether indexes can support a query."""
    return db.query(
        "Query plan for date-and-status filtering",
        """
        EXPLAIN QUERY PLAN
        WITH filtered_orders AS (
            SELECT order_id, customer_id
            FROM orders
            WHERE status = 'completed'
              AND order_date >= ?
              AND order_date < ?
        )
        SELECT customer_id, COUNT(*)
        FROM filtered_orders
        GROUP BY customer_id
        """,
        ("2025-01-01", "2025-04-01"),
    )


def validate_sqlite_cte_semantics(db: AnalyticsDatabase) -> None:
    """Verify key results so the demonstration catches analytical regressions."""
    result = db.query(
        "Validation: total completed orders",
        """
        WITH completed AS (
            SELECT order_id
            FROM orders
            WHERE status = 'completed'
        )
        SELECT COUNT(*) AS total FROM completed
        """,
    )
    assert result.rows[0][0] == 8, "Completed-order count changed unexpectedly."

    empty_result = db.query(
        "Validation: empty date range",
        """
        WITH filtered AS (
            SELECT order_id
            FROM orders
            WHERE order_date >= ? AND order_date < ?
        )
        SELECT COUNT(*) FROM filtered
        """,
        ("2030-01-01", "2030-02-01"),
    )
    assert empty_result.rows[0][0] == 0, "Empty date range should return zero rows."

    revenue = db.query(
        "Validation: completed revenue",
        """
        WITH completed_items AS (
            SELECT oi.quantity * oi.unit_price AS line_revenue
            FROM order_items AS oi
            JOIN orders AS o USING (order_id)
            WHERE o.status = 'completed'
        )
        SELECT SUM(line_revenue) FROM completed_items
        """,
    )
    assert revenue.rows[0][0] > 0, "Completed revenue must be positive."

    print("\nValidation passed: CTE row counts, empty ranges, and revenue.")


def demonstrate_invalid_data(db: AnalyticsDatabase) -> None:
    """Show that relational constraints still protect CTE input data."""
    try:
        db.execute_transaction([
            (
                "INSERT INTO order_items(order_id, product_id, quantity, unit_price) "
                "VALUES (?, ?, ?, ?)",
                (99999, 1, 1, 100),
            )
        ])
    except RuntimeError as exc:
        print(f"\nExpected integrity failure: {exc}")


def run_demo() -> None:
    db = AnalyticsDatabase.create_demo()
    try:
        demonstrations = [
            basic_cte(db),
            chained_ctes(db),
            category_profitability(db),
            monthly_performance(db),
            customer_cohorts(db),
            recursive_category_tree(db),
            conditional_metrics(db),
            explain_query_plan(db),
        ]

        for result in demonstrations:
            result.display()

        validate_sqlite_cte_semantics(db)
        demonstrate_invalid_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
