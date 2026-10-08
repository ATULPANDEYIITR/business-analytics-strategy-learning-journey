"""
Subqueries and Nested Queries: analytical logic with Python + SQLite

This executable example uses Python's standard-library sqlite3 module to
demonstrate how SQL subqueries support filtering, comparison, aggregation,
correlation, existence checks, derived tables, and multi-stage analytical
queries.

The data represents an e-commerce business so that every query has a concrete
analytical purpose.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable


SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region TEXT NOT NULL,
    customer_tier TEXT NOT NULL CHECK (customer_tier IN ('Standard', 'Silver', 'Gold')),
    signup_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Completed', 'Cancelled', 'Pending')),
    shipping_region TEXT NOT NULL
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price > 0),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_orders_customer_date
    ON orders(customer_id, order_date);

CREATE INDEX idx_order_items_product
    ON order_items(product_id);
"""

CUSTOMERS = [
    (1, "Aarav Mehta", "North", "Gold", "2024-01-12"),
    (2, "Diya Sharma", "North", "Silver", "2024-02-10"),
    (3, "Kabir Singh", "West", "Gold", "2024-03-08"),
    (4, "Meera Iyer", "South", "Standard", "2024-04-15"),
    (5, "Rohan Gupta", "West", "Silver", "2024-05-21"),
    (6, "Ananya Rao", "South", "Gold", "2024-06-18"),
    (7, "Vikram Joshi", "East", "Standard", "2024-07-01"),
    (8, "Sara Khan", "East", "Silver", "2024-08-11"),
]

PRODUCTS = [
    (1, "Laptop Pro", "Electronics", 1200.00),
    (2, "Mechanical Keyboard", "Electronics", 140.00),
    (3, "Office Chair", "Furniture", 350.00),
    (4, "Monitor 27", "Electronics", 420.00),
    (5, "Standing Desk", "Furniture", 650.00),
    (6, "USB-C Hub", "Accessories", 80.00),
    (7, "Webcam", "Accessories", 110.00),
]

ORDERS = [
    (101, 1, "2025-01-05", "Completed", "North"),
    (102, 1, "2025-02-11", "Completed", "North"),
    (103, 2, "2025-01-20", "Completed", "North"),
    (104, 2, "2025-03-14", "Completed", "North"),
    (105, 3, "2025-01-22", "Completed", "West"),
    (106, 3, "2025-02-25", "Completed", "West"),
    (107, 3, "2025-03-02", "Completed", "West"),
    (108, 4, "2025-02-02", "Completed", "South"),
    (109, 4, "2025-03-19", "Cancelled", "South"),
    (110, 5, "2025-01-18", "Completed", "West"),
    (111, 5, "2025-03-21", "Completed", "West"),
    (112, 6, "2025-01-27", "Completed", "South"),
    (113, 6, "2025-02-28", "Completed", "South"),
    (114, 7, "2025-02-08", "Completed", "East"),
    (115, 8, "2025-03-04", "Pending", "East"),
]

ORDER_ITEMS = [
    (101, 1, 1, 1200), (101, 2, 1, 140),
    (102, 4, 1, 420), (102, 6, 2, 80),
    (103, 3, 1, 350), (103, 7, 1, 110),
    (104, 2, 2, 140), (104, 6, 1, 80),
    (105, 1, 1, 1200), (105, 6, 1, 80),
    (106, 5, 1, 650), (106, 4, 1, 420),
    (107, 1, 1, 1200), (107, 7, 2, 110),
    (108, 3, 1, 350), (108, 6, 2, 80),
    (109, 4, 1, 420),
    (110, 5, 1, 650), (110, 2, 1, 140),
    (111, 3, 2, 350), (111, 7, 1, 110),
    (112, 1, 1, 1200), (112, 4, 1, 420),
    (113, 5, 1, 650), (113, 6, 2, 80),
    (114, 2, 1, 140), (114, 7, 1, 110),
    (115, 4, 1, 420),
]


@dataclass(frozen=True)
class QueryResult:
    title: str
    columns: tuple[str, ...]
    rows: list[tuple[Any, ...]]


def create_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    with connection:
        connection.executescript(SCHEMA)
        connection.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
            CUSTOMERS,
        )
        connection.executemany(
            "INSERT INTO products VALUES (?, ?, ?, ?)",
            PRODUCTS,
        )
        connection.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
            ORDERS,
        )
        connection.executemany(
            "INSERT INTO order_items VALUES (?, ?, ?, ?)",
            ORDER_ITEMS,
        )

    return connection


def execute_query(
    connection: sqlite3.Connection,
    title: str,
    sql: str,
    parameters: Iterable[Any] = (),
) -> QueryResult:
    try:
        cursor = connection.execute(sql, tuple(parameters))
        rows = cursor.fetchall()
        columns = tuple(column[0] for column in cursor.description or [])
        return QueryResult(title, columns, [tuple(row) for row in rows])
    except sqlite3.Error as exc:
        raise RuntimeError(f"Query failed: {title}: {exc}") from exc


def print_result(result: QueryResult) -> None:
    print(f"\n--- {result.title} ---")

    if not result.columns:
        print("(no result columns)")
        return

    widths = []
    for index, column in enumerate(result.columns):
        values = [str(row[index]) for row in result.rows]
        widths.append(max(len(column), *(len(value) for value in values)) if values else len(column))

    header = " | ".join(
        column.ljust(widths[index])
        for index, column in enumerate(result.columns)
    )
    print(header)
    print("-+-".join("-" * width for width in widths))

    for row in result.rows:
        print(
            " | ".join(
                str(value).ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


def demonstrate_scalar_subquery(connection: sqlite3.Connection) -> None:
    # A scalar subquery returns one value. Each qualifying product is compared
    # against the average price calculated by the inner SELECT.
    sql = """
        SELECT
            product_name,
            category,
            unit_price
        FROM products
        WHERE unit_price > (
            SELECT AVG(unit_price)
            FROM products
        )
        ORDER BY unit_price DESC
    """
    print_result(execute_query(connection, "Products above overall average price", sql))


def demonstrate_subquery_with_in(connection: sqlite3.Connection) -> None:
    # The inner query identifies customers with completed orders. The outer
    # query then retrieves customer attributes for that set.
    sql = """
        SELECT customer_id, customer_name, region
        FROM customers
        WHERE customer_id IN (
            SELECT DISTINCT customer_id
            FROM orders
            WHERE status = 'Completed'
        )
        ORDER BY customer_id
    """
    print_result(execute_query(connection, "Customers with completed orders", sql))


def demonstrate_not_in_with_null_warning(connection: sqlite3.Connection) -> None:
    # NOT IN has special NULL semantics in SQL. This example deliberately
    # avoids NULL data, but the comment highlights why NOT EXISTS is usually
    # safer when the subquery can contain nullable values.
    sql = """
        SELECT customer_id, customer_name
        FROM customers
        WHERE customer_id NOT IN (
            SELECT DISTINCT customer_id
            FROM orders
            WHERE status = 'Completed'
        )
    """
    print_result(
        execute_query(
            connection,
            "Customers without completed orders",
            sql,
        )
    )


def demonstrate_correlated_subquery(connection: sqlite3.Connection) -> None:
    # Unlike an independent subquery, this inner query refers to the current
    # row of the outer query. It is therefore evaluated conceptually per
    # customer and calculates that customer's average completed-order value.
    sql = """
        SELECT
            c.customer_name,
            ROUND(
                (
                    SELECT AVG(order_total)
                    FROM (
                        SELECT
                            o.order_id,
                            o.customer_id,
                            SUM(oi.quantity * oi.unit_price) AS order_total
                        FROM orders o
                        JOIN order_items oi ON oi.order_id = o.order_id
                        WHERE o.status = 'Completed'
                        GROUP BY o.order_id, o.customer_id
                    ) customer_orders
                    WHERE customer_orders.customer_id = c.customer_id
                ),
                2
            ) AS average_order_value
        FROM customers c
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Completed'
        )
        ORDER BY average_order_value DESC
    """
    print_result(
        execute_query(
            connection,
            "Correlated average order value by customer",
            sql,
        )
    )


def demonstrate_exists(connection: sqlite3.Connection) -> None:
    # EXISTS answers a Boolean question: does at least one matching row exist?
    # The selected value inside EXISTS is irrelevant, so SELECT 1 is idiomatic.
    sql = """
        SELECT
            c.customer_name,
            c.customer_tier
        FROM customers c
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            JOIN products p ON p.product_id = oi.product_id
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Completed'
              AND p.category = 'Furniture'
        )
        ORDER BY c.customer_name
    """
    print_result(
        execute_query(
            connection,
            "Customers who purchased furniture",
            sql,
        )
    )


def demonstrate_derived_table(connection: sqlite3.Connection) -> None:
    # A subquery in FROM creates a derived table. The outer query can then
    # aggregate or filter the already-computed order-level totals.
    sql = """
        SELECT
            region,
            ROUND(AVG(order_total), 2) AS average_order_value,
            ROUND(MAX(order_total), 2) AS largest_order
        FROM (
            SELECT
                o.order_id,
                c.region,
                SUM(oi.quantity * oi.unit_price) AS order_total
            FROM orders o
            JOIN customers c ON c.customer_id = o.customer_id
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'Completed'
            GROUP BY o.order_id, c.region
        ) order_summary
        GROUP BY region
        ORDER BY average_order_value DESC
    """
    print_result(
        execute_query(
            connection,
            "Regional analysis using a derived table",
            sql,
        )
    )


def demonstrate_multi_level_nesting(connection: sqlite3.Connection) -> None:
    # Three analytical layers are used here:
    # order totals -> customer totals -> customers above the customer average.
    sql = """
        SELECT
            customer_name,
            customer_revenue
        FROM (
            SELECT
                c.customer_name,
                SUM(order_total) AS customer_revenue
            FROM customers c
            JOIN (
                SELECT
                    o.order_id,
                    o.customer_id,
                    SUM(oi.quantity * oi.unit_price) AS order_total
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                WHERE o.status = 'Completed'
                GROUP BY o.order_id, o.customer_id
            ) order_totals
                ON order_totals.customer_id = c.customer_id
            GROUP BY c.customer_id, c.customer_name
        ) customer_totals
        WHERE customer_revenue > (
            SELECT AVG(customer_revenue)
            FROM (
                SELECT
                    c2.customer_id,
                    SUM(oi.quantity * oi.unit_price) AS customer_revenue
                FROM customers c2
                JOIN orders o2
                    ON o2.customer_id = c2.customer_id
                   AND o2.status = 'Completed'
                JOIN order_items oi
                    ON oi.order_id = o2.order_id
                GROUP BY c2.customer_id
            ) all_customer_totals
        )
        ORDER BY customer_revenue DESC
    """
    print_result(
        execute_query(
            connection,
            "Customers above the average customer revenue",
            sql,
        )
    )


def demonstrate_subquery_in_having(connection: sqlite3.Connection) -> None:
    # HAVING filters groups after aggregation. The scalar subquery supplies
    # the benchmark used to identify unusually productive categories.
    sql = """
        SELECT
            p.category,
            SUM(oi.quantity * oi.unit_price) AS category_revenue
        FROM products p
        JOIN order_items oi ON oi.product_id = p.product_id
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'Completed'
        GROUP BY p.category
        HAVING SUM(oi.quantity * oi.unit_price) > (
            SELECT AVG(category_revenue)
            FROM (
                SELECT
                    p2.category,
                    SUM(oi2.quantity * oi2.unit_price) AS category_revenue
                FROM products p2
                JOIN order_items oi2
                    ON oi2.product_id = p2.product_id
                JOIN orders o2
                    ON o2.order_id = oi2.order_id
                WHERE o2.status = 'Completed'
                GROUP BY p2.category
            ) category_totals
        )
        ORDER BY category_revenue DESC
    """
    print_result(
        execute_query(
            connection,
            "Categories above average category revenue",
            sql,
        )
    )


def demonstrate_top_per_group(connection: sqlite3.Connection) -> None:
    # A correlated subquery can count how many products in the same category
    # have a greater price. A rank of zero means the product is the most
    # expensive product in its category.
    sql = """
        SELECT
            p.product_name,
            p.category,
            p.unit_price
        FROM products p
        WHERE (
            SELECT COUNT(*)
            FROM products p2
            WHERE p2.category = p.category
              AND p2.unit_price > p.unit_price
        ) = 0
        ORDER BY p.category, p.product_name
    """
    print_result(
        execute_query(
            connection,
            "Most expensive product in each category",
            sql,
        )
    )


def demonstrate_exists_vs_join(connection: sqlite3.Connection) -> None:
    # EXISTS is useful when the requirement is membership rather than data
    # retrieval. Unlike a normal join, it does not duplicate an outer row when
    # multiple matching child records exist.
    sql = """
        SELECT
            c.customer_name
        FROM customers c
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Completed'
        )
        AND NOT EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Cancelled'
        )
        ORDER BY c.customer_name
    """
    print_result(
        execute_query(
            connection,
            "Customers with completed orders but no cancellations",
            sql,
        )
    )


def demonstrate_parameterized_subquery(connection: sqlite3.Connection) -> None:
    # Parameters should be bound instead of concatenated into SQL. The scalar
    # subquery then uses the supplied category as its analytical scope.
    sql = """
        SELECT product_name, unit_price
        FROM products
        WHERE category = ?
          AND unit_price > (
              SELECT AVG(unit_price)
              FROM products
              WHERE category = ?
          )
        ORDER BY unit_price DESC
    """
    category = "Electronics"
    print_result(
        execute_query(
            connection,
            "Products above their category average",
            sql,
            (category, category),
        )
    )


def demonstrate_edge_case_empty_subquery(connection: sqlite3.Connection) -> None:
    # AVG over no rows returns NULL. A comparison such as > NULL is UNKNOWN,
    # not TRUE, so no rows qualify. COALESCE can provide an explicit fallback.
    sql = """
        SELECT product_name, unit_price
        FROM products
        WHERE unit_price > COALESCE(
            (
                SELECT AVG(unit_price)
                FROM products
                WHERE category = 'Nonexistent'
            ),
            0
        )
        ORDER BY unit_price DESC
        LIMIT 5
    """
    print_result(
        execute_query(
            connection,
            "Handling an empty scalar subquery with COALESCE",
            sql,
        )
    )


def demonstrate_query_plan(connection: sqlite3.Connection) -> None:
    # EXPLAIN QUERY PLAN is a practical debugging tool. It reveals whether
    # indexes and table scans are being used for a nested analytical query.
    sql = """
        EXPLAIN QUERY PLAN
        SELECT c.customer_name
        FROM customers c
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.customer_id = c.customer_id
              AND o.status = 'Completed'
        )
    """
    print_result(
        execute_query(
            connection,
            "Query plan for a correlated EXISTS condition",
            sql,
        )
    )


def demonstrate_safe_transaction(connection: sqlite3.Connection) -> None:
    # Transactional behavior is independent of subquery syntax, but analytical
    # validation often precedes a state change. Here a subquery verifies that
    # the customer exists before inserting a new pending order.
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO orders (
                    order_id,
                    customer_id,
                    order_date,
                    status,
                    shipping_region
                )
                SELECT
                    ?,
                    customer_id,
                    ?,
                    'Pending',
                    region
                FROM customers
                WHERE customer_id = ?
                """,
                (999, "2025-03-25", 1),
            )

        result = execute_query(
            connection,
            "Order created only for an existing customer",
            """
                SELECT order_id, customer_id, status
                FROM orders
                WHERE order_id = 999
            """,
        )
        print_result(result)
    except sqlite3.IntegrityError as exc:
        print(f"Transaction rejected: {exc}")


def main() -> None:
    connection = create_database()

    try:
        demonstrate_scalar_subquery(connection)
        demonstrate_subquery_with_in(connection)
        demonstrate_not_in_with_null_warning(connection)
        demonstrate_correlated_subquery(connection)
        demonstrate_exists(connection)
        demonstrate_derived_table(connection)
        demonstrate_multi_level_nesting(connection)
        demonstrate_subquery_in_having(connection)
        demonstrate_top_per_group(connection)
        demonstrate_exists_vs_join(connection)
        demonstrate_parameterized_subquery(connection)
        demonstrate_edge_case_empty_subquery(connection)
        demonstrate_query_plan(connection)
        demonstrate_safe_transaction(connection)

        print("\nAnalytical validation:")
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT customer_id
                    FROM orders
                    WHERE status = 'Completed'
                    GROUP BY customer_id
                ) active_customers
                """
            )
            active_customer_count = cursor.fetchone()[0]

        print(
            f"Completed-order customer groups discovered through a derived table: "
            f"{active_customer_count}"
        )

        # Decimal is used here only to make the Python-side presentation of a
        # floating-point SQL result explicit and stable.
        revenue = connection.execute(
            """
            SELECT COALESCE(SUM(quantity * unit_price), 0)
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            WHERE o.status = 'Completed'
            """
        ).fetchone()[0]

        print(f"Completed revenue: {Decimal(str(revenue)):.2f}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
