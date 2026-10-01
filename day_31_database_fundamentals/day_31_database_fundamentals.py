"""
Database Fundamentals: Databases, Tables, Rows, Columns, and Relationships

A self-contained SQLite case study that progresses from relational database
fundamentals to practical schema design, constraints, relationships, joins,
transactions, indexing, validation, and diagnostic queries.

The program uses only Python's standard library.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


DATABASE_FILE = Path("database_fundamentals_demo.sqlite3")


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    email: str


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    category: str
    price: float


class DatabaseError(Exception):
    """Base exception for application-level database errors."""


class ValidationError(DatabaseError):
    """Raised when application input violates business rules."""


class Database:
    """
    Small database access layer.

    SQLite is used because it is available in Python's standard library and
    exposes relational database concepts without requiring a server.
    """

    def __init__(self, path: str = ":memory:") -> None:
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, parameters)

    def executemany(self, sql: str, parameters: list[tuple]) -> sqlite3.Cursor:
        return self.connection.executemany(sql, parameters)

    def commit(self) -> None:
        self.connection.commit()

    def rollback(self) -> None:
        self.connection.rollback()

    def script(self, sql: str) -> None:
        self.connection.executescript(sql)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """
        A transaction groups multiple changes into one atomic operation.

        If any operation raises an exception, all changes made inside the
        transaction are rolled back.
        """
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise


def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_rows(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("(no rows)")
        return

    columns = rows[0].keys()
    widths = {
        column: max(
            len(column),
            *(len(str(row[column])) for row in rows),
        )
        for column in columns
    }

    print(" | ".join(column.ljust(widths[column]) for column in columns))
    print("-+-".join("-" * widths[column] for column in columns))

    for row in rows:
        print(" | ".join(str(row[column]).ljust(widths[column]) for column in columns))


def create_schema(db: Database) -> None:
    """
    The schema separates entities into tables.

    customers stores customer attributes.
    categories stores product categories.
    products stores product attributes and references categories.
    orders stores order-level information.
    order_items resolves the many-to-many relationship between orders and
    products while also storing quantity and the price at purchase time.
    """
    db.script(
        """
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (length(trim(name)) >= 2),
            CHECK (instr(email, '@') > 1)
        );

        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            CHECK (price >= 0),
            CHECK (stock_quantity >= 0),
            FOREIGN KEY (category_id)
                REFERENCES categories(category_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'PENDING',
            CHECK (status IN ('PENDING', 'PAID', 'SHIPPED', 'CANCELLED')),
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );

        CREATE TABLE order_items (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            PRIMARY KEY (order_id, product_id),
            CHECK (quantity > 0),
            CHECK (unit_price >= 0),
            FOREIGN KEY (order_id)
                REFERENCES orders(order_id)
                ON DELETE CASCADE,
            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
                ON DELETE RESTRICT
        );

        CREATE INDEX idx_products_category
            ON products(category_id);

        CREATE INDEX idx_orders_customer
            ON orders(customer_id);

        CREATE INDEX idx_order_items_product
            ON order_items(product_id);

        CREATE INDEX idx_orders_status
            ON orders(status);
        """
    )


def seed_reference_data(db: Database) -> None:
    db.executemany(
        "INSERT INTO categories(category_id, name) VALUES (?, ?)",
        [
            (1, "Laptops"),
            (2, "Monitors"),
            (3, "Accessories"),
        ],
    )

    db.executemany(
        """
        INSERT INTO products(product_id, name, category_id, price, stock_quantity)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (101, "ThinkPad E16", 1, 89999.00, 12),
            (102, "Framework Laptop", 1, 104999.00, 8),
            (201, "27-inch 4K Monitor", 2, 32999.00, 15),
            (202, "24-inch IPS Monitor", 2, 16999.00, 20),
            (301, "Mechanical Keyboard", 3, 6999.00, 30),
            (302, "USB-C Dock", 3, 8999.00, 18),
        ],
    )

    db.executemany(
        "INSERT INTO customers(customer_id, name, email) VALUES (?, ?, ?)",
        [
            (1, "Atul Pandey", "atul@example.com"),
            (2, "Priya Sharma", "priya@example.com"),
            (3, "Rahul Verma", "rahul@example.com"),
        ],
    )
    db.commit()


def demonstrate_relational_structure(db: Database) -> None:
    print_title("DATABASE STRUCTURE")

    tables = db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print("Tables:")
    for table in tables:
        print(f"  {table['name']}")

    print("\nColumns in products:")
    columns = db.execute("PRAGMA table_info(products)").fetchall()
    print_rows(columns)

    print("\nForeign keys in order_items:")
    foreign_keys = db.execute("PRAGMA foreign_key_list(order_items)").fetchall()
    print_rows(foreign_keys)


def demonstrate_rows_and_columns(db: Database) -> None:
    print_title("ROWS AND COLUMNS")

    rows = db.execute(
        """
        SELECT product_id, name, price, stock_quantity
        FROM products
        ORDER BY product_id
        """
    ).fetchall()

    print_rows(rows)

    print("\nA column can be selected without retrieving every other column:")
    prices = db.execute(
        "SELECT name, price FROM products ORDER BY price DESC"
    ).fetchall()
    print_rows(prices)


def demonstrate_relationships(db: Database) -> None:
    print_title("RELATIONSHIPS AND JOINS")

    print("Many-to-one: products belong to categories.")
    rows = db.execute(
        """
        SELECT
            p.product_id,
            p.name AS product,
            c.name AS category
        FROM products AS p
        INNER JOIN categories AS c
            ON p.category_id = c.category_id
        ORDER BY c.name, p.name
        """
    ).fetchall()
    print_rows(rows)

    print("\nCustomer-to-order relationship:")
    rows = db.execute(
        """
        SELECT
            c.name AS customer,
            o.order_id,
            o.status,
            o.order_date
        FROM customers AS c
        LEFT JOIN orders AS o
            ON o.customer_id = c.customer_id
        ORDER BY c.customer_id, o.order_id
        """
    ).fetchall()
    print_rows(rows)

    print(
        "\nOrder-to-product is many-to-many through order_items, "
        "which acts as a junction table."
    )


def create_order(
    db: Database,
    customer_id: int,
    requested_items: list[tuple[int, int]],
) -> int:
    """
    Create an order atomically.

    requested_items contains (product_id, quantity). The function validates
    references and stock before changing either the order or inventory.
    """
    if not requested_items:
        raise ValidationError("An order must contain at least one product.")

    if customer_id <= 0:
        raise ValidationError("customer_id must be positive.")

    with db.transaction() as connection:
        customer = connection.execute(
            "SELECT customer_id FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()

        if customer is None:
            raise ValidationError("Customer does not exist.")

        normalized_items: dict[int, int] = {}

        for product_id, quantity in requested_items:
            if product_id <= 0:
                raise ValidationError("Product IDs must be positive.")
            if quantity <= 0:
                raise ValidationError("Order quantities must be positive.")

            # Combining duplicate product entries prevents two lines for the
            # same product from bypassing the intended stock check.
            normalized_items[product_id] = (
                normalized_items.get(product_id, 0) + quantity
            )

        order_cursor = connection.execute(
            """
            INSERT INTO orders(customer_id, status)
            VALUES (?, 'PENDING')
            """,
            (customer_id,),
        )
        order_id = order_cursor.lastrowid

        for product_id, quantity in normalized_items.items():
            product = connection.execute(
                """
                SELECT product_id, price, stock_quantity
                FROM products
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchone()

            if product is None:
                raise ValidationError(f"Product {product_id} does not exist.")

            if product["stock_quantity"] < quantity:
                raise ValidationError(
                    f"Insufficient stock for product {product_id}."
                )

            connection.execute(
                """
                INSERT INTO order_items(order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    product_id,
                    quantity,
                    product["price"],
                ),
            )

            connection.execute(
                """
                UPDATE products
                SET stock_quantity = stock_quantity - ?
                WHERE product_id = ?
                """,
                (quantity, product_id),
            )

        return int(order_id)


def demonstrate_order_workflow(db: Database) -> None:
    print_title("TRANSACTIONAL RELATIONSHIP WORKFLOW")

    order_id = create_order(
        db,
        customer_id=1,
        requested_items=[
            (101, 1),
            (301, 2),
        ],
    )

    print(f"Created order {order_id}.")

    rows = db.execute(
        """
        SELECT
            o.order_id,
            c.name AS customer,
            p.name AS product,
            oi.quantity,
            oi.unit_price,
            oi.quantity * oi.unit_price AS line_total
        FROM orders AS o
        JOIN customers AS c
            ON c.customer_id = o.customer_id
        JOIN order_items AS oi
            ON oi.order_id = o.order_id
        JOIN products AS p
            ON p.product_id = oi.product_id
        WHERE o.order_id = ?
        """,
        (order_id,),
    ).fetchall()

    print_rows(rows)

    total = db.execute(
        """
        SELECT SUM(quantity * unit_price) AS total
        FROM order_items
        WHERE order_id = ?
        """,
        (order_id,),
    ).fetchone()["total"]

    print(f"\nOrder total: ₹{total:,.2f}")


def demonstrate_aggregation(db: Database) -> None:
    print_title("GROUPING AND AGGREGATION")

    rows = db.execute(
        """
        SELECT
            c.name AS category,
            COUNT(p.product_id) AS product_count,
            ROUND(AVG(p.price), 2) AS average_price,
            SUM(p.stock_quantity) AS total_stock
        FROM categories AS c
        LEFT JOIN products AS p
            ON p.category_id = c.category_id
        GROUP BY c.category_id, c.name
        ORDER BY average_price DESC
        """
    ).fetchall()

    print_rows(rows)

    print("\nCustomers and their order counts:")
    rows = db.execute(
        """
        SELECT
            c.name,
            COUNT(o.order_id) AS order_count
        FROM customers AS c
        LEFT JOIN orders AS o
            ON o.customer_id = c.customer_id
        GROUP BY c.customer_id, c.name
        ORDER BY order_count DESC, c.name
        """
    ).fetchall()
    print_rows(rows)


def demonstrate_null_and_outer_join(db: Database) -> None:
    print_title("OPTIONAL RELATIONSHIPS AND NULL")

    rows = db.execute(
        """
        SELECT
            c.name,
            o.order_id,
            o.status
        FROM customers AS c
        LEFT JOIN orders AS o
            ON o.customer_id = c.customer_id
        ORDER BY c.customer_id
        """
    ).fetchall()

    print_rows(rows)
    print(
        "\nA LEFT JOIN retains the customer even when no matching order exists; "
        "missing order columns become NULL."
    )


def demonstrate_constraints(db: Database) -> None:
    print_title("CONSTRAINTS AND FAILURE CONDITIONS")

    tests = [
        (
            "duplicate customer email",
            """
            INSERT INTO customers(name, email)
            VALUES ('Duplicate Email', 'atul@example.com')
            """,
        ),
        (
            "negative product price",
            """
            INSERT INTO products(name, category_id, price, stock_quantity)
            VALUES ('Invalid Product', 1, -10, 1)
            """,
        ),
        (
            "invalid category reference",
            """
            INSERT INTO products(name, category_id, price, stock_quantity)
            VALUES ('Unknown Category Product', 999, 100, 1)
            """,
        ),
    ]

    for label, sql in tests:
        try:
            db.execute(sql)
            db.commit()
        except sqlite3.IntegrityError as exc:
            db.rollback()
            print(f"{label}: rejected -> {exc}")


def demonstrate_transaction_rollback(db: Database) -> None:
    print_title("TRANSACTION ROLLBACK")

    before = db.execute(
        "SELECT stock_quantity FROM products WHERE product_id = 102"
    ).fetchone()["stock_quantity"]

    try:
        create_order(
            db,
            customer_id=2,
            requested_items=[
                (102, 1),
                (999, 1),
            ],
        )
    except ValidationError as exc:
        print(f"Order rejected: {exc}")

    after = db.execute(
        "SELECT stock_quantity FROM products WHERE product_id = 102"
    ).fetchone()["stock_quantity"]

    print(f"Stock before failed transaction: {before}")
    print(f"Stock after failed transaction:  {after}")
    print("Because the operation was atomic, the valid item was not partially deducted.")


def demonstrate_safe_parameterization(db: Database) -> None:
    print_title("SAFE QUERY PARAMETERS")

    customer_input = "Atul' OR 1=1 --"

    rows = db.execute(
        """
        SELECT customer_id, name, email
        FROM customers
        WHERE name = ?
        """,
        (customer_input,),
    ).fetchall()

    print("User input is treated as data rather than executable SQL.")
    print_rows(rows)

    print(
        "\nBuilding SQL by concatenating untrusted input can turn input into "
        "SQL syntax and create injection vulnerabilities."
    )


def demonstrate_index_inspection(db: Database) -> None:
    print_title("INDEXES AND QUERY PLANNING")

    indexes = db.execute(
        """
        SELECT name, tbl_name, sql
        FROM sqlite_master
        WHERE type = 'index'
          AND sql IS NOT NULL
        ORDER BY name
        """
    ).fetchall()

    print_rows(indexes)

    plan = db.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT order_id, status
        FROM orders
        WHERE customer_id = ?
        """,
        (1,),
    ).fetchall()

    print("\nQuery plan for customer_id lookup:")
    print_rows(plan)

    print(
        "\nIndexes can reduce lookup work, but they consume storage and make "
        "writes more expensive because index entries must also be maintained."
    )


def demonstrate_update_and_delete_rules(db: Database) -> None:
    print_title("RELATIONSHIP INTEGRITY DURING UPDATE AND DELETE")

    print("Attempting to delete a category that still owns products:")

    try:
        db.execute("DELETE FROM categories WHERE category_id = 1")
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        print(f"Rejected: {exc}")

    print(
        "\nThe schema uses ON DELETE RESTRICT for categories and products so "
        "referenced entities cannot disappear accidentally."
    )

    order_id = db.execute(
        "SELECT order_id FROM orders ORDER BY order_id LIMIT 1"
    ).fetchone()["order_id"]

    item_count_before = db.execute(
        "SELECT COUNT(*) AS count FROM order_items WHERE order_id = ?",
        (order_id,),
    ).fetchone()["count"]

    db.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    db.commit()

    item_count_after = db.execute(
        "SELECT COUNT(*) AS count FROM order_items WHERE order_id = ?",
        (order_id,),
    ).fetchone()["count"]

    print(
        f"\nOrder {order_id}: {item_count_before} order-item rows before deletion, "
        f"{item_count_after} afterward."
    )
    print(
        "order_items uses ON DELETE CASCADE because an item has no meaningful "
        "existence in this model without its parent order."
    )


def demonstrate_schema_relationships(db: Database) -> None:
    print_title("RELATIONSHIP MODEL")

    print(
        """
customers
    |
    | one customer can have many orders
    v
orders
    |
    | one order can contain many order_items
    v
order_items
    ^
    | many order_items can reference one product
    |
products
    |
    | many products belong to one category
    v
categories

The order/product relationship is therefore many-to-many:
one order can contain many products, and one product can appear in many
orders. The order_items junction table converts that many-to-many relationship
into two one-to-many relationships.
""".strip()
    )


def demonstrate_database_metadata(db: Database) -> None:
    print_title("DATABASE METADATA")

    for table_name in ("customers", "categories", "products", "orders", "order_items"):
        print(f"\nSchema for {table_name}:")
        columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()
        for column in columns:
            print(
                f"  {column['name']}: type={column['type']}, "
                f"not_null={column['notnull']}, primary_key={column['pk']}"
            )


def main() -> None:
    print_title("RELATIONAL DATABASE FUNDAMENTALS")

    db = Database()

    try:
        create_schema(db)
        seed_reference_data(db)

        demonstrate_relational_structure(db)
        demonstrate_rows_and_columns(db)
        demonstrate_relationships(db)
        demonstrate_schema_relationships(db)
        demonstrate_order_workflow(db)
        demonstrate_aggregation(db)
        demonstrate_null_and_outer_join(db)
        demonstrate_constraints(db)
        demonstrate_transaction_rollback(db)
        demonstrate_safe_parameterization(db)
        demonstrate_index_inspection(db)
        demonstrate_update_and_delete_rules(db)
        demonstrate_database_metadata(db)

        print_title("DATABASE FILE")
        print(f"SQLite database location: {Path(db.path).resolve()}")
        print(
            "The file can be inspected with any SQLite-compatible database "
            "viewer or with the sqlite3 command-line client."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
