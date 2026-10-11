#!/usr/bin/env python3
"""
Advanced SQL: Advanced joins, window functions, and query optimization.

Run:
    python advanced_sql.py

The script uses only Python's standard library and SQLite. SQLite provides
window functions and query-plan inspection, while the program also explains
PostgreSQL-specific optimization considerations in its documentation output.

The examples use an order-management dataset to investigate customer value,
product performance, fulfillment delays, and query execution plans.
"""

from __future__ import annotations

import random
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')
    ),
    shipping_days INTEGER CHECK (
        shipping_days IS NULL OR shipping_days >= 0
    )
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK (unit_price >= 0)
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    discount_rate REAL NOT NULL DEFAULT 0 CHECK (
        discount_rate >= 0 AND discount_rate <= 1
    ),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    amount REAL NOT NULL CHECK (amount >= 0),
    payment_status TEXT NOT NULL CHECK (
        payment_status IN ('authorized', 'settled', 'refunded', 'failed')
    )
);

CREATE TABLE support_tickets (
    ticket_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_id INTEGER REFERENCES orders(order_id),
    opened_at TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),
    resolved_at TEXT
);
"""


@dataclass(frozen=True)
class QueryResult:
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    """Use an in-memory database so the example is repeatable."""
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)


def seed_data(connection: sqlite3.Connection) -> None:
    customers = [
        (1, "Aarav Sharma", "North", "2025-01-10"),
        (2, "Meera Singh", "South", "2025-02-15"),
        (3, "Kabir Verma", "West", "2025-03-20"),
        (4, "Ananya Rao", "North", "2025-04-05"),
        (5, "Ishaan Gupta", "East", "2025-05-18"),
        (6, "Diya Nair", "South", "2025-06-22"),
    ]
    products = [
        (1, "Laptop", "Electronics", 75000.00),
        (2, "Monitor", "Electronics", 18000.00),
        (3, "Office Chair", "Furniture", 12000.00),
        (4, "Desk Lamp", "Furniture", 2500.00),
        (5, "Keyboard", "Accessories", 3500.00),
    ]
    orders = [
        (101, 1, "2025-01-12", "delivered", 3),
        (102, 1, "2025-02-10", "delivered", 5),
        (103, 2, "2025-02-15", "shipped", 8),
        (104, 2, "2025-03-01", "cancelled", None),
        (105, 3, "2025-03-12", "delivered", 2),
        (106, 3, "2025-04-20", "paid", None),
        (107, 4, "2025-05-02", "delivered", 4),
        (108, 5, "2025-05-19", "pending", None),
        (109, 1, "2025-06-11", "delivered", 2),
        (110, 6, "2025-06-22", "delivered", 6),
        (111, 4, "2025-07-05", "delivered", 3),
    ]
    items = [
        (101, 1, 1, 75000.00, 0.05),
        (101, 5, 2, 3500.00, 0.00),
        (102, 2, 2, 18000.00, 0.10),
        (103, 3, 1, 12000.00, 0.00),
        (103, 4, 2, 2500.00, 0.00),
        (104, 5, 1, 3500.00, 0.00),
        (105, 1, 1, 75000.00, 0.00),
        (106, 3, 2, 12000.00, 0.05),
        (107, 2, 1, 18000.00, 0.00),
        (107, 4, 4, 2500.00, 0.10),
        (108, 5, 3, 3500.00, 0.00),
        (109, 1, 1, 75000.00, 0.10),
        (110, 3, 1, 12000.00, 0.00),
        (110, 5, 1, 3500.00, 0.00),
        (111, 2, 1, 18000.00, 0.00),
    ]
    payments = [
        (1, 101, 81750.00, "settled"),
        (2, 102, 32400.00, "settled"),
        (3, 103, 17000.00, "authorized"),
        (4, 104, 3500.00, "refunded"),
        (5, 105, 75000.00, "settled"),
        (6, 106, 22800.00, "authorized"),
        (7, 107, 27000.00, "settled"),
        (8, 108, 10500.00, "authorized"),
        (9, 109, 67500.00, "settled"),
        (10, 110, 15500.00, "settled"),
        (11, 111, 18000.00, "settled"),
    ]
    tickets = [
        (1, 1, 102, "2025-02-12", "medium", "2025-02-14"),
        (2, 2, 103, "2025-02-20", "high", None),
        (3, 3, 105, "2025-03-15", "low", "2025-03-16"),
        (4, 4, 107, "2025-05-05", "critical", None),
        (5, 1, 109, "2025-06-12", "high", "2025-06-13"),
        (6, 6, 110, "2025-06-23", "medium", None),
    ]

    connection.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?)", customers
    )
    connection.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)", products
    )
    connection.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders
    )
    connection.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", items
    )
    connection.executemany(
        "INSERT INTO payments VALUES (?, ?, ?, ?)", payments
    )
    connection.executemany(
        "INSERT INTO support_tickets VALUES (?, ?, ?, ?, ?, ?)", tickets
    )
    connection.commit()


def execute_query(
    connection: sqlite3.Connection,
    title: str,
    sql: str,
    parameters: tuple[Any, ...] = (),
) -> QueryResult:
    cursor = connection.execute(sql, parameters)
    rows = cursor.fetchall()
    return QueryResult(
        title=title,
        columns=tuple(column[0] for column in cursor.description or ()),
        rows=tuple(tuple(row) for row in rows),
    )


def print_result(result: QueryResult, max_rows: int = 20) -> None:
    print(f"\n--- {result.title} ---")
    if not result.columns:
        print("No result columns.")
        return

    widths = [
        min(
            28,
            max(
                len(column),
                *(len(str(row[index])) for row in result.rows[:max_rows]),
            ),
        )
        for index, column in enumerate(result.columns)
    ]

    def render(row: tuple[Any, ...]) -> str:
        cells = []
        for index, value in enumerate(row):
            rendered = str(value)
            if len(rendered) > widths[index]:
                rendered = rendered[: widths[index] - 3] + "..."
            cells.append(rendered.ljust(widths[index]))
        return " | ".join(cells)

    print(render(result.columns))
    print("-+-".join("-" * width for width in widths))
    for row in result.rows[:max_rows]:
        print(render(row))
    if len(result.rows) > max_rows:
        print(f"... {len(result.rows) - max_rows} additional rows")


def advanced_join_examples(connection: sqlite3.Connection) -> None:
    # Aggregate line items before joining them to payments. Joining two
    # one-to-many relations directly can multiply amounts and inflate totals.
    revenue_by_order = """
        WITH item_totals AS (
            SELECT
                order_id,
                SUM(quantity * unit_price * (1 - discount_rate)) AS net_total
            FROM order_items
            GROUP BY order_id
        ),
        settled_payments AS (
            SELECT order_id, SUM(amount) AS settled_amount
            FROM payments
            WHERE payment_status = 'settled'
            GROUP BY order_id
        )
        SELECT
            o.order_id,
            c.customer_name,
            COALESCE(i.net_total, 0) AS net_total,
            COALESCE(p.settled_amount, 0) AS settled_amount
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        LEFT JOIN item_totals AS i ON i.order_id = o.order_id
        LEFT JOIN settled_payments AS p ON p.order_id = o.order_id
        ORDER BY o.order_id
    """
    print_result(
        execute_query(
            connection, "Pre-aggregated joins avoid fan-out", revenue_by_order
        )
    )

    # The LEFT JOIN preserves customers with no qualifying orders. Moving
    # the status predicate into WHERE would eliminate those customers.
    customers_without_delivered_orders = """
        SELECT c.customer_id, c.customer_name, COUNT(o.order_id) AS delivered_orders
        FROM customers AS c
        LEFT JOIN orders AS o
          ON o.customer_id = c.customer_id
         AND o.status = 'delivered'
        GROUP BY c.customer_id, c.customer_name
        ORDER BY delivered_orders, c.customer_id
    """
    print_result(
        execute_query(
            connection,
            "Outer join with a predicate in ON",
            customers_without_delivered_orders,
        )
    )

    # NOT EXISTS avoids NULL-related surprises associated with NOT IN.
    customers_without_tickets = """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE NOT EXISTS (
            SELECT 1
            FROM support_tickets AS t
            WHERE t.customer_id = c.customer_id
        )
        ORDER BY c.customer_id
    """
    print_result(
        execute_query(
            connection, "Anti-join using NOT EXISTS", customers_without_tickets
        )
    )

    # A correlated subquery selects the latest order independently per
    # customer. A window-function alternative appears in the next section.
    latest_orders = """
        SELECT c.customer_name, o.order_id, o.order_date, o.status
        FROM customers AS c
        JOIN orders AS o ON o.customer_id = c.customer_id
        WHERE o.order_date = (
            SELECT MAX(o2.order_date)
            FROM orders AS o2
            WHERE o2.customer_id = c.customer_id
        )
        ORDER BY c.customer_id
    """
    print_result(
        execute_query(connection, "Latest order per customer", latest_orders)
    )


def window_function_examples(connection: sqlite3.Connection) -> None:
    ranking_query = """
        WITH customer_revenue AS (
            SELECT
                c.customer_id,
                c.customer_name,
                c.region,
                COALESCE(
                    SUM(
                        CASE WHEN o.status <> 'cancelled'
                             THEN oi.quantity * oi.unit_price *
                                  (1 - oi.discount_rate)
                             ELSE 0 END
                    ),
                    0
                ) AS revenue
            FROM customers AS c
            LEFT JOIN orders AS o ON o.customer_id = c.customer_id
            LEFT JOIN order_items AS oi ON oi.order_id = o.order_id
            GROUP BY c.customer_id, c.customer_name, c.region
        )
        SELECT
            customer_name,
            region,
            ROUND(revenue, 2) AS revenue,
            RANK() OVER (
                PARTITION BY region ORDER BY revenue DESC
            ) AS regional_rank,
            DENSE_RANK() OVER (
                ORDER BY revenue DESC
            ) AS overall_dense_rank,
            NTILE(3) OVER (
                ORDER BY revenue DESC
            ) AS revenue_tertile
        FROM customer_revenue
        ORDER BY region, regional_rank, customer_name
    """
    print_result(
        execute_query(
            connection, "Ranking and distribution window functions", ranking_query
        )
    )

    running_total_query = """
        WITH daily_revenue AS (
            SELECT
                o.order_date,
                SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate)) AS revenue
            FROM orders AS o
            JOIN order_items AS oi ON oi.order_id = o.order_id
            WHERE o.status IN ('delivered', 'shipped')
            GROUP BY o.order_date
        )
        SELECT
            order_date,
            ROUND(revenue, 2) AS daily_revenue,
            ROUND(
                SUM(revenue) OVER (
                    ORDER BY order_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ),
                2
            ) AS running_revenue,
            ROUND(
                AVG(revenue) OVER (
                    ORDER BY order_date
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ),
                2
            ) AS trailing_three_observation_average
        FROM daily_revenue
        ORDER BY order_date
    """
    print_result(
        execute_query(
            connection,
            "Running totals and moving averages",
            running_total_query,
        )
    )

    order_sequence_query = """
        SELECT
            customer_id,
            order_id,
            order_date,
            status,
            LAG(order_date) OVER (
                PARTITION BY customer_id ORDER BY order_date, order_id
            ) AS previous_order_date,
            LEAD(order_date) OVER (
                PARTITION BY customer_id ORDER BY order_date, order_id
            ) AS next_order_date,
            ROW_NUMBER() OVER (
                PARTITION BY customer_id ORDER BY order_date DESC, order_id DESC
            ) AS newest_first
        FROM orders
        ORDER BY customer_id, order_date
    """
    print_result(
        execute_query(
            connection, "Order sequences with LAG and LEAD", order_sequence_query
        )
    )

    # ROWS counts physical rows. RANGE and GROUPS have different peer semantics.
    # An explicit frame avoids relying on the default frame for cumulative sums.
    frame_query = """
        WITH sales AS (
            SELECT 'North' AS region, 100 AS amount
            UNION ALL SELECT 'North', 100
            UNION ALL SELECT 'North', 200
            UNION ALL SELECT 'South', 50
        )
        SELECT
            region,
            amount,
            SUM(amount) OVER (
                PARTITION BY region
                ORDER BY amount
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS row_running_total,
            SUM(amount) OVER (
                PARTITION BY region
                ORDER BY amount
                RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS peer_aware_running_total
        FROM sales
        ORDER BY region, amount
    """
    print_result(
        execute_query(
            connection, "ROWS versus RANGE window frames", frame_query
        )
    )


def query_optimization_examples(connection: sqlite3.Connection) -> None:
    selective_query = """
        SELECT order_id, customer_id, order_date, status
        FROM orders
        WHERE customer_id = ? AND order_date >= ?
        ORDER BY order_date DESC
    """

    def explain(sql: str, parameters: tuple[Any, ...] = ()) -> None:
        rows = connection.execute(
            "EXPLAIN QUERY PLAN " + sql, parameters
        ).fetchall()
        for row in rows:
            print(" | ".join(str(value) for value in row))

    print("\n--- Query plan before a composite index ---")
    explain(selective_query, (1, "2025-01-01"))

    # The index begins with customer_id because the query filters on it, then
    # includes order_date for range filtering and ordering.
    connection.execute(
        "CREATE INDEX idx_orders_customer_date "
        "ON orders(customer_id, order_date DESC)"
    )
    connection.execute(
        "CREATE INDEX idx_items_product_order "
        "ON order_items(product_id, order_id)"
    )
    connection.execute(
        "CREATE INDEX idx_tickets_customer_opened "
        "ON support_tickets(customer_id, opened_at DESC)"
    )
    connection.execute("ANALYZE")

    print("\n--- Query plan after a composite index ---")
    explain(selective_query, (1, "2025-01-01"))

    # Avoid applying a function to an indexed date column in a selective
    # predicate. A range can make ordinary B-tree index access possible.
    sargable_query = """
        SELECT order_id, order_date
        FROM orders
        WHERE order_date >= ? AND order_date < ?
        ORDER BY order_date
    """
    print("\n--- Sargable date-range query plan ---")
    explain(sargable_query, ("2025-05-01", "2025-06-01"))

    print_result(
        execute_query(
            connection,
            "Selective date-range result",
            sargable_query,
            ("2025-05-01", "2025-06-01"),
        )
    )

    # EXISTS can stop after finding a qualifying row. It avoids returning
    # duplicate customer rows when several matching orders exist.
    exists_query = """
        SELECT c.customer_id, c.customer_name
        FROM customers AS c
        WHERE EXISTS (
            SELECT 1
            FROM orders AS o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'delivered'
        )
        ORDER BY c.customer_id
    """
    print_result(
        execute_query(
            connection, "Customers with delivered orders", exists_query
        )
    )

    # A repeatable microbenchmark illustrates measurement technique, not a
    # universal claim about which query is faster. Tiny datasets are noisy.
    benchmark_sql = [
        (
            "Customer/date filter",
            "SELECT COUNT(*) FROM orders "
            "WHERE customer_id = 1 AND order_date >= '2025-01-01'",
        ),
        (
            "Full-table aggregate",
            "SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id",
        ),
    ]
    for title, sql in benchmark_sql:
        start = time.perf_counter()
        for _ in range(2000):
            connection.execute(sql).fetchall()
        elapsed = time.perf_counter() - start
        print(f"{title}: 2000 executions in {elapsed:.4f} seconds")


def transaction_and_validation_examples(
    connection: sqlite3.Connection,
) -> None:
    print("\n--- Integrity and transaction behavior ---")

    # SAVEPOINT allows an isolated demonstration without leaving invalid data
    # in the sample database.
    connection.execute("SAVEPOINT validation_demo")
    try:
        connection.execute(
            """
            INSERT INTO order_items
                (order_id, product_id, quantity, unit_price, discount_rate)
            VALUES (?, ?, ?, ?, ?)
            """,
            (101, 2, -1, 18000.0, 0.0),
        )
    except sqlite3.IntegrityError as error:
        print(f"Rejected invalid quantity: {error}")
    finally:
        connection.execute("ROLLBACK TO validation_demo")
        connection.execute("RELEASE validation_demo")

    # A production workflow should use a transaction when multiple writes
    # must succeed together. Here both the payment and order transition are
    # rolled back if any step fails.
    connection.execute("SAVEPOINT payment_demo")
    try:
        connection.execute(
            """
            INSERT INTO payments (payment_id, order_id, amount, payment_status)
            VALUES (?, ?, ?, ?)
            """,
            (99, 106, 22800.0, "settled"),
        )
        connection.execute(
            "UPDATE orders SET status = 'shipped' WHERE order_id = ?",
            (106,),
        )
        connection.execute("RELEASE payment_demo")
        print("Payment and order transition committed within the savepoint.")
    except sqlite3.Error as error:
        connection.execute("ROLLBACK TO payment_demo")
        connection.execute("RELEASE payment_demo")
        print(f"Transaction rolled back: {error}")

    integrity = connection.execute("PRAGMA foreign_key_check").fetchall()
    print(f"Foreign-key violations: {len(integrity)}")


def randomized_invariant_check(connection: sqlite3.Connection) -> None:
    """Check that aggregate totals agree across two independently shaped queries."""
    random.seed(17)

    query_a = """
        SELECT ROUND(SUM(quantity * unit_price * (1 - discount_rate)), 2)
        FROM order_items
        WHERE order_id IN (
            SELECT order_id FROM orders WHERE status = 'delivered'
        )
    """
    query_b = """
        SELECT ROUND(SUM(order_total), 2)
        FROM (
            SELECT
                o.order_id,
                SUM(oi.quantity * oi.unit_price * (1 - oi.discount_rate))
                    AS order_total
            FROM orders AS o
            JOIN order_items AS oi ON oi.order_id = o.order_id
            WHERE o.status = 'delivered'
            GROUP BY o.order_id
        )
    """
    total_a = connection.execute(query_a).fetchone()[0]
    total_b = connection.execute(query_b).fetchone()[0]
    assert total_a == total_b, (total_a, total_b)

    # A generated workload demonstrates that parameter binding keeps data
    # separate from SQL syntax. It is also safe for strings containing quotes.
    customer_name = "O'Brien Analytics"
    connection.execute(
        """
        INSERT INTO customers (customer_id, customer_name, region, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (999, customer_name, "West", "2025-10-01"),
    )
    fetched = connection.execute(
        "SELECT customer_name FROM customers WHERE customer_id = ?",
        (999,),
    ).fetchone()[0]
    assert fetched == customer_name

    print(f"Independent aggregate check passed: {total_a:.2f}")
    print("Parameterized query preserved a name containing an apostrophe.")


def main() -> None:
    with database_connection() as connection:
        create_schema(connection)
        seed_data(connection)

        advanced_join_examples(connection)
        window_function_examples(connection)
        query_optimization_examples(connection)
        transaction_and_validation_examples(connection)
        randomized_invariant_check(connection)

        print("\n--- Operational guidance ---")
        print(
            "Inspect execution plans on representative data, measure real "
            "workloads, and keep indexes aligned with actual predicates."
        )
        print(
            "For PostgreSQL, use EXPLAIN (ANALYZE, BUFFERS) to inspect actual "
            "row counts, timing, and I/O. ANALYZE executes the query."
        )
        print(
            "SQLite and PostgreSQL have different planners and SQL features; "
            "validate plans and syntax against the target database."
        )


if __name__ == "__main__":
    main()
