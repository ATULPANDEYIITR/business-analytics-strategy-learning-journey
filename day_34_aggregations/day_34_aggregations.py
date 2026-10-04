"""
SQL-style Aggregations: COUNT, SUM, AVG, MIN, and MAX
=======================================================

A self-contained Python study of aggregate operations using an order dataset.

The implementation progresses from direct aggregation of Python collections
to grouped aggregation, NULL-like handling, conditional aggregation,
validation, numerical precision, and a reusable aggregation engine.

Run:
    python aggregations.py
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from statistics import fmean
from typing import Callable, Iterable, Optional


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Order:
    order_id: int
    customer: str
    region: str
    category: str
    quantity: int
    unit_price: Decimal
    status: str

    @property
    def revenue(self) -> Decimal:
        """SUM-oriented derived measure: quantity multiplied by unit price."""
        return self.unit_price * self.quantity


def build_orders() -> list[Order]:
    """Create realistic sales records for aggregation examples."""
    return [
        Order(1001, "Aarav", "North", "Laptop", 2, Decimal("850.00"), "completed"),
        Order(1002, "Diya", "North", "Phone", 3, Decimal("500.00"), "completed"),
        Order(1003, "Kabir", "West", "Monitor", 1, Decimal("300.00"), "completed"),
        Order(1004, "Meera", "South", "Laptop", 1, Decimal("920.00"), "cancelled"),
        Order(1005, "Aarav", "North", "Keyboard", 4, Decimal("75.00"), "completed"),
        Order(1006, "Riya", "East", "Phone", 2, Decimal("650.00"), "completed"),
        Order(1007, "Kabir", "West", "Laptop", 1, Decimal("1100.00"), "completed"),
        Order(1008, "Meera", "South", "Monitor", 2, Decimal("280.00"), "completed"),
        Order(1009, "Riya", "East", "Keyboard", 5, Decimal("60.00"), "pending"),
        Order(1010, "Aarav", "North", "Monitor", 2, Decimal("325.00"), "completed"),
    ]


# ---------------------------------------------------------------------------
# Fundamental aggregations
# ---------------------------------------------------------------------------

def count_rows(records: Iterable[object]) -> int:
    """COUNT(*) equivalent: count every input record."""
    return sum(1 for _ in records)


def count_non_null(values: Iterable[Optional[object]]) -> int:
    """
    COUNT(column) equivalent.

    SQL COUNT(column) excludes NULL values. Python uses None here as the
    closest direct representation of a missing scalar value.
    """
    return sum(value is not None for value in values)


def sum_values(values: Iterable[Optional[Decimal]]) -> Decimal:
    """
    SUM equivalent.

    Missing values are ignored, matching SQL's treatment of NULL inputs
    inside SUM. An empty or all-missing input produces Decimal(0).
    """
    total = Decimal("0")
    for value in values:
        if value is not None:
            total += value
    return total


def average_values(values: Iterable[Optional[Decimal]]) -> Optional[Decimal]:
    """
    AVG equivalent.

    AVG is SUM(non-null values) / COUNT(non-null values), not
    SUM(all values) / COUNT(all rows).
    """
    cleaned = [value for value in values if value is not None]
    if not cleaned:
        return None
    return sum(cleaned, Decimal("0")) / Decimal(len(cleaned))


def min_value(values: Iterable[Optional[Decimal]]) -> Optional[Decimal]:
    """MIN equivalent while ignoring missing values."""
    cleaned = [value for value in values if value is not None]
    return min(cleaned) if cleaned else None


def max_value(values: Iterable[Optional[Decimal]]) -> Optional[Decimal]:
    """MAX equivalent while ignoring missing values."""
    cleaned = [value for value in values if value is not None]
    return max(cleaned) if cleaned else None


# ---------------------------------------------------------------------------
# Basic demonstrations
# ---------------------------------------------------------------------------

def demonstrate_scalar_aggregations(orders: list[Order]) -> None:
    print("\n=== Scalar Aggregations ===")

    quantities = [Decimal(order.quantity) for order in orders]
    revenues = [order.revenue for order in orders]
    prices = [order.unit_price for order in orders]

    print(f"COUNT(*)             = {count_rows(orders)}")
    print(f"COUNT(quantity)      = {count_non_null(quantities)}")
    print(f"SUM(quantity)        = {sum_values(quantities)}")
    print(f"SUM(revenue)         = {sum_values(revenues)}")
    print(f"AVG(unit_price)      = {average_values(prices)}")
    print(f"MIN(unit_price)      = {min_value(prices)}")
    print(f"MAX(unit_price)      = {max_value(prices)}")


# ---------------------------------------------------------------------------
# NULL behavior
# ---------------------------------------------------------------------------

def demonstrate_missing_values() -> None:
    print("\n=== Missing-Value Semantics ===")

    scores: list[Optional[Decimal]] = [
        Decimal("80"),
        None,
        Decimal("90"),
        Decimal("70"),
        None,
    ]

    print(f"Input                = {scores}")
    print(f"COUNT(*)             = {count_rows(scores)}")
    print(f"COUNT(score)         = {count_non_null(scores)}")
    print(f"SUM(score)           = {sum_values(scores)}")
    print(f"AVG(score)           = {average_values(scores)}")
    print(f"MIN(score)           = {min_value(scores)}")
    print(f"MAX(score)           = {max_value(scores)}")

    empty: list[Optional[Decimal]] = []
    print(f"AVG(empty)           = {average_values(empty)}")
    print(f"MIN(empty)           = {min_value(empty)}")
    print(f"MAX(empty)           = {max_value(empty)}")


# ---------------------------------------------------------------------------
# Filtering before aggregation
# ---------------------------------------------------------------------------

def completed_orders(orders: Iterable[Order]) -> list[Order]:
    """WHERE-like filtering must occur before a non-window aggregation."""
    return [order for order in orders if order.status == "completed"]


def demonstrate_filtered_aggregations(orders: list[Order]) -> None:
    print("\n=== Filtered Aggregations ===")

    completed = completed_orders(orders)
    revenue = sum_values(order.revenue for order in completed)
    average_order_value = average_values(
        [order.revenue for order in completed]
    )

    print(f"Completed order count = {count_rows(completed)}")
    print(f"Completed revenue     = {revenue:.2f}")
    print(
        "Average completed "
        f"order value        = {average_order_value:.2f}"
        if average_order_value is not None
        else "Average completed order value = NULL"
    )


# ---------------------------------------------------------------------------
# GROUP BY-style aggregation
# ---------------------------------------------------------------------------

def group_by(
    records: Iterable[Order],
    key_function: Callable[[Order], str],
) -> dict[str, list[Order]]:
    """
    Build groups equivalent to the conceptual effect of SQL GROUP BY.

    The key determines which records contribute to the same aggregate row.
    """
    groups: dict[str, list[Order]] = {}

    for record in records:
        key = key_function(record)
        groups.setdefault(key, []).append(record)

    return groups


def aggregate_order_group(records: list[Order]) -> dict[str, object]:
    """Calculate multiple aggregate functions for one group."""
    revenues = [order.revenue for order in records]
    quantities = [Decimal(order.quantity) for order in records]

    return {
        "count": count_rows(records),
        "sum_quantity": sum_values(quantities),
        "avg_revenue": average_values(revenues),
        "min_revenue": min_value(revenues),
        "max_revenue": max_value(revenues),
    }


def demonstrate_grouped_aggregations(orders: list[Order]) -> None:
    print("\n=== GROUP BY Region ===")

    groups = group_by(orders, lambda order: order.region)

    for region in sorted(groups):
        metrics = aggregate_order_group(groups[region])
        print(
            f"{region:>5} | "
            f"COUNT={metrics['count']} | "
            f"SUM(quantity)={metrics['sum_quantity']} | "
            f"AVG(revenue)={metrics['avg_revenue']} | "
            f"MIN(revenue)={metrics['min_revenue']} | "
            f"MAX(revenue)={metrics['max_revenue']}"
        )


def demonstrate_category_aggregation(orders: list[Order]) -> None:
    print("\n=== GROUP BY Category ===")

    groups = group_by(orders, lambda order: order.category)

    for category in sorted(groups):
        records = groups[category]
        revenue = sum_values(order.revenue for order in records)
        quantity = sum_values(Decimal(order.quantity) for order in records)

        print(
            f"{category:>8} | orders={len(records):2d} | "
            f"quantity={quantity:5} | revenue={revenue:8.2f}"
        )


# ---------------------------------------------------------------------------
# Conditional aggregation
# ---------------------------------------------------------------------------

def demonstrate_conditional_aggregation(orders: list[Order]) -> None:
    print("\n=== Conditional Aggregation ===")

    completed = [
        order for order in orders if order.status == "completed"
    ]

    pending_count = count_rows(
        order for order in orders if order.status == "pending"
    )
    cancelled_count = count_rows(
        order for order in orders if order.status == "cancelled"
    )
    completed_revenue = sum_values(
        order.revenue for order in completed
    )

    print(f"Completed revenue    = {completed_revenue:.2f}")
    print(f"Pending orders       = {pending_count}")
    print(f"Cancelled orders     = {cancelled_count}")


# ---------------------------------------------------------------------------
# HAVING-like post-aggregation filtering
# ---------------------------------------------------------------------------

def demonstrate_post_aggregation_filter(orders: list[Order]) -> None:
    print("\n=== Post-Aggregation Filtering ===")

    groups = group_by(orders, lambda order: order.region)

    for region, records in sorted(groups.items()):
        total = sum_values(order.revenue for order in records)

        # This is conceptually different from filtering rows before GROUP BY.
        # The decision uses the aggregate result rather than an individual row.
        if total >= Decimal("2000"):
            print(f"{region}: total revenue {total:.2f}")


# ---------------------------------------------------------------------------
# A reusable aggregation engine
# ---------------------------------------------------------------------------

@dataclass
class AggregateResult:
    count: int
    non_null_count: int
    total: Decimal
    average: Optional[Decimal]
    minimum: Optional[Decimal]
    maximum: Optional[Decimal]


class Aggregator:
    """
    Reusable aggregation object.

    The class keeps the aggregation rules together so callers do not
    accidentally calculate AVG using a different denominator from COUNT.
    """

    def __init__(self) -> None:
        self._count = 0
        self._non_null_count = 0
        self._sum = Decimal("0")
        self._minimum: Optional[Decimal] = None
        self._maximum: Optional[Decimal] = None

    def add(self, value: Optional[Decimal]) -> None:
        self._count += 1

        if value is None:
            return

        self._non_null_count += 1
        self._sum += value

        if self._minimum is None or value < self._minimum:
            self._minimum = value

        if self._maximum is None or value > self._maximum:
            self._maximum = value

    def result(self) -> AggregateResult:
        average = (
            self._sum / Decimal(self._non_null_count)
            if self._non_null_count
            else None
        )

        return AggregateResult(
            count=self._count,
            non_null_count=self._non_null_count,
            total=self._sum,
            average=average,
            minimum=self._minimum,
            maximum=self._maximum,
        )


def demonstrate_streaming_aggregation(orders: list[Order]) -> None:
    print("\n=== Streaming Aggregation ===")

    aggregator = Aggregator()

    for order in orders:
        aggregator.add(order.revenue)

    result = aggregator.result()

    print(f"Rows processed       = {result.count}")
    print(f"Non-null revenues    = {result.non_null_count}")
    print(f"SUM(revenue)         = {result.total:.2f}")
    print(
        f"AVG(revenue)         = "
        f"{result.average:.2f}" if result.average is not None
        else "AVG(revenue)         = NULL"
    )
    print(f"MIN(revenue)         = {result.minimum}")
    print(f"MAX(revenue)         = {result.maximum}")

    # This design requires O(1) aggregation state after each input value.
    # It is useful when the source is a large stream rather than an in-memory list.


# ---------------------------------------------------------------------------
# Validation and data-quality rules
# ---------------------------------------------------------------------------

def validate_orders(orders: Iterable[Order]) -> list[str]:
    """Return data-quality violations relevant to aggregation correctness."""
    errors: list[str] = []

    for order in orders:
        if order.quantity <= 0:
            errors.append(
                f"Order {order.order_id}: quantity must be positive"
            )

        if order.unit_price < 0:
            errors.append(
                f"Order {order.order_id}: unit_price cannot be negative"
            )

        if order.status not in {"completed", "pending", "cancelled"}:
            errors.append(
                f"Order {order.order_id}: unsupported status "
                f"{order.status!r}"
            )

    return errors


def demonstrate_validation(orders: list[Order]) -> None:
    print("\n=== Aggregation Input Validation ===")

    errors = validate_orders(orders)

    if errors:
        print("Invalid records detected:")
        for error in errors:
            print(f"  {error}")
    else:
        print("All records satisfy aggregation input rules.")


# ---------------------------------------------------------------------------
# Precision and type decisions
# ---------------------------------------------------------------------------

def demonstrate_decimal_precision() -> None:
    print("\n=== Decimal Precision ===")

    float_total = sum([0.10, 0.10, 0.10])
    decimal_total = sum(
        [Decimal("0.10"), Decimal("0.10"), Decimal("0.10")],
        Decimal("0"),
    )

    print(f"Binary floating-point SUM = {float_total!r}")
    print(f"Decimal SUM              = {decimal_total}")

    # Financial aggregation should normally use Decimal or an equivalent
    # fixed-precision database type such as DECIMAL/NUMERIC.


# ---------------------------------------------------------------------------
# Comparing AVG with raw arithmetic
# ---------------------------------------------------------------------------

def demonstrate_average_definition() -> None:
    print("\n=== AVG Is SUM / COUNT(non-null) ===")

    values = [
        Decimal("10"),
        Decimal("20"),
        None,
        Decimal("40"),
    ]

    total = sum_values(values)
    count = count_non_null(values)
    average = average_values(values)

    print(f"SUM(non-null values)     = {total}")
    print(f"COUNT(non-null values)   = {count}")
    print(f"SUM / COUNT              = {total / Decimal(count)}")
    print(f"AVG                      = {average}")


# ---------------------------------------------------------------------------
# SQL-equivalent reference queries
# ---------------------------------------------------------------------------

def print_sql_reference() -> None:
    print("\n=== SQL Equivalents ===")

    queries = [
        "SELECT COUNT(*) FROM orders;",
        "SELECT COUNT(unit_price) FROM orders;",
        "SELECT SUM(quantity) FROM orders;",
        "SELECT AVG(unit_price) FROM orders;",
        "SELECT MIN(unit_price) FROM orders;",
        "SELECT MAX(unit_price) FROM orders;",
        (
            "SELECT region, COUNT(*), SUM(quantity), AVG(unit_price), "
            "MIN(unit_price), MAX(unit_price) "
            "FROM orders GROUP BY region;"
        ),
        (
            "SELECT region, SUM(quantity * unit_price) AS revenue "
            "FROM orders "
            "WHERE status = 'completed' "
            "GROUP BY region "
            "HAVING SUM(quantity * unit_price) >= 2000;"
        ),
    ]

    for query in queries:
        print(query)


# ---------------------------------------------------------------------------
# Assertions as executable checks
# ---------------------------------------------------------------------------

def run_checks(orders: list[Order]) -> None:
    """Verify important aggregation invariants."""
    revenues = [order.revenue for order in orders]

    assert count_rows(orders) == 10
    assert count_non_null(revenues) == 10
    assert sum_values(revenues) == Decimal("6905.00")
    assert min_value(revenues) == Decimal("300.00")
    assert max_value(revenues) == Decimal("1700.00")

    values = [Decimal("10"), None, Decimal("30")]
    assert count_rows(values) == 3
    assert count_non_null(values) == 2
    assert sum_values(values) == Decimal("40")
    assert average_values(values) == Decimal("20")
    assert min_value(values) == Decimal("10")
    assert max_value(values) == Decimal("30")

    assert average_values([]) is None
    assert min_value([]) is None
    assert max_value([]) is None

    print("\nAll executable aggregation checks passed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    orders = build_orders()

    demonstrate_scalar_aggregations(orders)
    demonstrate_missing_values()
    demonstrate_filtered_aggregations(orders)
    demonstrate_grouped_aggregations(orders)
    demonstrate_category_aggregation(orders)
    demonstrate_conditional_aggregation(orders)
    demonstrate_post_aggregation_filter(orders)
    demonstrate_streaming_aggregation(orders)
    demonstrate_validation(orders)
    demonstrate_decimal_precision()
    demonstrate_average_definition()
    print_sql_reference()
    run_checks(orders)


if __name__ == "__main__":
    main()
