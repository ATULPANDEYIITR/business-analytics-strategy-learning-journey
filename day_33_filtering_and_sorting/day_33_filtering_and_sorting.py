"""
Filtering & Sorting Business Data
=================================

A self-contained demonstration of business-data filtering and sorting.

The program progresses from:
- basic WHERE-style predicates
- combining filters with AND/OR/NOT
- NULL-like values and validation
- ORDER BY with multiple sort keys
- ascending and descending ordering
- stable sorting and deterministic tie-breaking
- pagination after filtering and sorting
- reusable query specifications
- aggregation after filtering
- a small query-engine style implementation
- realistic business reporting examples

No third-party packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from functools import cmp_to_key
from typing import Any, Callable, Iterable, Optional


# ---------------------------------------------------------------------------
# Business data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    region: str
    segment: str
    annual_revenue: Optional[float]
    credit_limit: Optional[float]
    active: bool
    signup_date: date


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    sales_rep: str
    region: str
    product_category: str
    order_value: float
    status: str
    order_date: date
    priority: str
    discount_rate: float = 0.0


@dataclass(frozen=True)
class Employee:
    employee_id: int
    name: str
    department: str
    region: str
    salary: float
    performance_score: Optional[float]
    active: bool
    hire_date: date


CUSTOMERS = [
    Customer(101, "Apex Retail", "North", "Enterprise", 18_500_000, 2_000_000, True, date(2021, 4, 12)),
    Customer(102, "Blue Horizon", "West", "Mid-Market", 7_250_000, 750_000, True, date(2022, 8, 19)),
    Customer(103, "Cedar Foods", "South", "SMB", 1_850_000, 200_000, True, date(2023, 2, 5)),
    Customer(104, "Delta Manufacturing", "East", "Enterprise", 12_400_000, 1_500_000, False, date(2020, 11, 23)),
    Customer(105, "Evergreen Health", "North", "Mid-Market", None, 600_000, True, date(2024, 1, 14)),
    Customer(106, "Frontier Logistics", "West", "Enterprise", 21_300_000, 2_500_000, True, date(2019, 6, 30)),
    Customer(107, "Granite Systems", "East", "SMB", 950_000, None, True, date(2024, 5, 2)),
    Customer(108, "Harbor Hotels", "South", "Mid-Market", 5_900_000, 500_000, False, date(2022, 3, 17)),
]

ORDERS = [
    Order(5001, 101, "Anita", "North", "Cloud", 245000, "Shipped", date(2026, 9, 3), "High", 0.05),
    Order(5002, 102, "Rahul", "West", "Security", 185000, "Pending", date(2026, 9, 4), "Medium", 0.02),
    Order(5003, 103, "Meera", "South", "Analytics", 72000, "Shipped", date(2026, 9, 5), "Low", 0.00),
    Order(5004, 104, "Vikram", "East", "Cloud", 310000, "Cancelled", date(2026, 9, 6), "High", 0.10),
    Order(5005, 105, "Anita", "North", "Security", 126000, "Processing", date(2026, 9, 8), "High", 0.03),
    Order(5006, 106, "Rahul", "West", "Cloud", 455000, "Shipped", date(2026, 9, 9), "High", 0.07),
    Order(5007, 107, "Vikram", "East", "Analytics", 64000, "Pending", date(2026, 9, 10), "Low", 0.00),
    Order(5008, 108, "Meera", "South", "Security", 198000, "Shipped", date(2026, 9, 11), "Medium", 0.04),
    Order(5009, 101, "Anita", "North", "Analytics", 175000, "Processing", date(2026, 9, 12), "Medium", 0.02),
    Order(5010, 102, "Rahul", "West", "Cloud", 225000, "Shipped", date(2026, 9, 13), "High", 0.05),
    Order(5011, 103, "Meera", "South", "Security", 91000, "Pending", date(2026, 9, 15), "Low", 0.01),
    Order(5012, 106, "Rahul", "West", "Security", 275000, "Processing", date(2026, 9, 16), "High", 0.06),
]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_title(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_table(rows: Iterable[Any], fields: list[str]) -> None:
    rows = list(rows)
    if not rows:
        print("(no rows)")
        return

    values = []
    for row in rows:
        current = []
        for field_name in fields:
            value = getattr(row, field_name)
            current.append("" if value is None else str(value))
        values.append(current)

    widths = [
        max(len(field_name), *(len(row[index]) for row in values))
        for index, field_name in enumerate(fields)
    ]

    header = " | ".join(
        field_name.ljust(widths[index])
        for index, field_name in enumerate(fields)
    )
    separator = "-+-".join("-" * width for width in widths)

    print(header)
    print(separator)

    for row in values:
        print(
            " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
        )


# ---------------------------------------------------------------------------
# Basic WHERE-style filtering
# ---------------------------------------------------------------------------

def where(
    rows: Iterable[Any],
    predicate: Callable[[Any], bool],
) -> list[Any]:
    """
    Return rows for which the predicate evaluates to True.

    This is analogous to the conceptual role of SQL WHERE:
    filtering happens before later ordering and pagination.
    """
    return [row for row in rows if predicate(row)]


def equals(field_name: str, expected: Any) -> Callable[[Any], bool]:
    return lambda row: getattr(row, field_name) == expected


def greater_than(field_name: str, threshold: Any) -> Callable[[Any], bool]:
    def predicate(row: Any) -> bool:
        value = getattr(row, field_name)
        return value is not None and value > threshold

    return predicate


def greater_or_equal(field_name: str, threshold: Any) -> Callable[[Any], bool]:
    def predicate(row: Any) -> bool:
        value = getattr(row, field_name)
        return value is not None and value >= threshold

    return predicate


def less_than(field_name: str, threshold: Any) -> Callable[[Any], bool]:
    def predicate(row: Any) -> bool:
        value = getattr(row, field_name)
        return value is not None and value < threshold

    return predicate


def contains(field_name: str, fragment: str) -> Callable[[Any], bool]:
    fragment = fragment.casefold()

    def predicate(row: Any) -> bool:
        value = getattr(row, field_name)
        return value is not None and fragment in str(value).casefold()

    return predicate


def in_values(field_name: str, allowed: set[Any]) -> Callable[[Any], bool]:
    return lambda row: getattr(row, field_name) in allowed


def is_null(field_name: str) -> Callable[[Any], bool]:
    return lambda row: getattr(row, field_name) is None


def is_not_null(field_name: str) -> Callable[[Any], bool]:
    return lambda row: getattr(row, field_name) is not None


# ---------------------------------------------------------------------------
# Boolean predicate composition
# ---------------------------------------------------------------------------

def all_of(*predicates: Callable[[Any], bool]) -> Callable[[Any], bool]:
    return lambda row: all(predicate(row) for predicate in predicates)


def any_of(*predicates: Callable[[Any], bool]) -> Callable[[Any], bool]:
    return lambda row: any(predicate(row) for predicate in predicates)


def negate(predicate: Callable[[Any], bool]) -> Callable[[Any], bool]:
    return lambda row: not predicate(row)


# ---------------------------------------------------------------------------
# ORDER BY-style sorting
# ---------------------------------------------------------------------------

def sort_by(
    rows: Iterable[Any],
    field_name: str,
    descending: bool = False,
    nulls_last: bool = True,
) -> list[Any]:
    """
    Sort by one business field.

    Python's sorted() is stable. The explicit NULL handling prevents
    comparisons such as None > 100 from raising TypeError.
    """
    rows = list(rows)

    def key(row: Any) -> tuple[int, Any]:
        value = getattr(row, field_name)

        if value is None:
            return (1 if nulls_last else 0, None)

        return (0 if nulls_last else 1, value)

    return sorted(rows, key=key, reverse=descending)


def multi_sort(
    rows: Iterable[Any],
    specifications: list[tuple[str, bool]],
) -> list[Any]:
    """
    Multi-column ORDER BY.

    Each specification is (field_name, descending).
    A comparator is used so each field can have its own direction.
    """
    rows = list(rows)

    def compare(left: Any, right: Any) -> int:
        for field_name, descending in specifications:
            left_value = getattr(left, field_name)
            right_value = getattr(right, field_name)

            if left_value is None and right_value is None:
                continue

            if left_value is None:
                result = 1
            elif right_value is None:
                result = -1
            elif left_value < right_value:
                result = -1
            elif left_value > right_value:
                result = 1
            else:
                result = 0

            if result:
                return -result if descending else result

        return 0

    return sorted(rows, key=cmp_to_key(compare))


# ---------------------------------------------------------------------------
# Query object: reusable filtering + ordering + pagination
# ---------------------------------------------------------------------------

@dataclass
class Query:
    rows: list[Any]
    predicates: list[Callable[[Any], bool]] = field(default_factory=list)
    orderings: list[tuple[str, bool]] = field(default_factory=list)

    def where(self, predicate: Callable[[Any], bool]) -> "Query":
        self.predicates.append(predicate)
        return self

    def order_by(
        self,
        field_name: str,
        descending: bool = False,
    ) -> "Query":
        self.orderings.append((field_name, descending))
        return self

    def execute(
        self,
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> list[Any]:
        if offset < 0:
            raise ValueError("offset cannot be negative")

        if limit is not None and limit < 0:
            raise ValueError("limit cannot be negative")

        result = self.rows

        for predicate in self.predicates:
            result = where(result, predicate)

        if self.orderings:
            result = multi_sort(result, self.orderings)

        result = result[offset:]

        if limit is not None:
            result = result[:limit]

        return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_ORDER_STATUSES = {"Pending", "Processing", "Shipped", "Cancelled"}
VALID_PRIORITIES = {"Low", "Medium", "High"}


def validate_orders(orders: Iterable[Order]) -> list[str]:
    errors: list[str] = []

    for order in orders:
        if order.order_value < 0:
            errors.append(f"Order {order.order_id}: negative order value")

        if order.discount_rate < 0 or order.discount_rate > 1:
            errors.append(f"Order {order.order_id}: invalid discount rate")

        if order.status not in VALID_ORDER_STATUSES:
            errors.append(f"Order {order.order_id}: invalid status")

        if order.priority not in VALID_PRIORITIES:
            errors.append(f"Order {order.order_id}: invalid priority")

    return errors


# ---------------------------------------------------------------------------
# Business calculations after filtering
# ---------------------------------------------------------------------------

def total_value(orders: Iterable[Order]) -> float:
    return sum(order.order_value for order in orders)


def average_value(orders: Iterable[Order]) -> float:
    values = [order.order_value for order in orders]
    return sum(values) / len(values) if values else 0.0


def group_total_by(
    orders: Iterable[Order],
    field_name: str,
) -> dict[Any, float]:
    totals: dict[Any, float] = {}

    for order in orders:
        key = getattr(order, field_name)
        totals[key] = totals.get(key, 0.0) + order.order_value

    return totals


def group_count_by(
    rows: Iterable[Any],
    field_name: str,
) -> dict[Any, int]:
    counts: dict[Any, int] = {}

    for row in rows:
        key = getattr(row, field_name)
        counts[key] = counts.get(key, 0) + 1

    return counts


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def demonstrate_basic_where() -> None:
    print_title("Basic WHERE-style filtering")

    north_customers = where(CUSTOMERS, equals("region", "North"))
    print("\nCustomers in the North region:")
    print_table(
        north_customers,
        ["customer_id", "name", "region", "segment"],
    )

    large_orders = where(ORDERS, greater_than("order_value", 200000))
    print("\nOrders above 200,000:")
    print_table(
        large_orders,
        ["order_id", "region", "order_value", "status"],
    )


def demonstrate_boolean_filtering() -> None:
    print_title("Combined business filters")

    enterprise_or_large = where(
        CUSTOMERS,
        any_of(
            equals("segment", "Enterprise"),
            greater_than("annual_revenue", 10_000_000),
        ),
    )

    print("\nEnterprise customers OR customers with revenue above 10M:")
    print_table(
        enterprise_or_large,
        ["customer_id", "name", "segment", "annual_revenue"],
    )

    active_north_high_value = where(
        CUSTOMERS,
        all_of(
            equals("region", "North"),
            equals("active", True),
            greater_than("credit_limit", 500_000),
        ),
    )

    print("\nActive North customers with credit limit above 500K:")
    print_table(
        active_north_high_value,
        ["customer_id", "name", "region", "credit_limit"],
    )

    non_cancelled = where(
        ORDERS,
        negate(equals("status", "Cancelled")),
    )

    print("\nOrders that are not cancelled:")
    print_table(
        non_cancelled,
        ["order_id", "status", "order_value"],
    )


def demonstrate_null_handling() -> None:
    print_title("NULL-style business-data handling")

    customers_without_revenue = where(
        CUSTOMERS,
        is_null("annual_revenue"),
    )

    print("\nCustomers whose annual revenue is unknown:")
    print_table(
        customers_without_revenue,
        ["customer_id", "name", "annual_revenue"],
    )

    customers_with_credit_limit = where(
        CUSTOMERS,
        is_not_null("credit_limit"),
    )

    print("\nCustomers with a known credit limit:")
    print_table(
        customers_with_credit_limit,
        ["customer_id", "name", "credit_limit"],
    )

    # A common mistake is attempting direct comparison with None.
    # The predicate below explicitly checks for None before comparison.
    known_large_revenue = where(
        CUSTOMERS,
        greater_or_equal("annual_revenue", 10_000_000),
    )

    print("\nCustomers with known revenue >= 10M:")
    print_table(
        known_large_revenue,
        ["customer_id", "name", "annual_revenue"],
    )


def demonstrate_order_by() -> None:
    print_title("ORDER BY-style sorting")

    highest_value_first = sort_by(
        ORDERS,
        "order_value",
        descending=True,
    )

    print("\nOrders sorted by value descending:")
    print_table(
        highest_value_first,
        ["order_id", "order_value", "region", "status"],
    )

    newest_first = sort_by(
        ORDERS,
        "order_date",
        descending=True,
    )

    print("\nOrders sorted by date descending:")
    print_table(
        newest_first,
        ["order_id", "order_date", "order_value"],
    )

    multi_column = multi_sort(
        ORDERS,
        [
            ("region", False),
            ("order_value", True),
        ],
    )

    print("\nOrders sorted by region ascending, then value descending:")
    print_table(
        multi_column,
        ["order_id", "region", "order_value"],
    )


def demonstrate_query_pipeline() -> None:
    print_title("Filtering, ordering, and pagination as a query pipeline")

    result = (
        Query(ORDERS)
        .where(equals("status", "Shipped"))
        .where(greater_or_equal("order_value", 150_000))
        .order_by("order_value", descending=True)
        .execute(offset=0, limit=3)
    )

    print("\nTop three shipped orders worth at least 150K:")
    print_table(
        result,
        ["order_id", "order_value", "status", "order_date"],
    )

    page_two = (
        Query(ORDERS)
        .where(negate(equals("status", "Cancelled")))
        .order_by("order_date", descending=True)
        .execute(offset=3, limit=3)
    )

    print("\nSecond page of non-cancelled orders, newest first:")
    print_table(
        page_two,
        ["order_id", "order_date", "status", "order_value"],
    )


def demonstrate_business_reporting() -> None:
    print_title("Business reporting after filtering")

    sales_orders = where(
        ORDERS,
        all_of(
            negate(equals("status", "Cancelled")),
            greater_or_equal("order_value", 100_000),
        ),
    )

    print("\nQualified sales orders:")
    print_table(
        sales_orders,
        ["order_id", "sales_rep", "region", "order_value", "status"],
    )

    print(f"\nQualified order count: {len(sales_orders)}")
    print(f"Qualified order value: {total_value(sales_orders):,.2f}")
    print(f"Average qualified order: {average_value(sales_orders):,.2f}")

    totals_by_region = group_total_by(sales_orders, "region")

    print("\nFiltered sales value by region:")
    for region, value in sorted(
        totals_by_region.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"{region:10} {value:,.2f}")


def demonstrate_status_priority_workflow() -> None:
    print_title("Operational queue: filtering before prioritised sorting")

    operational_queue = (
        Query(ORDERS)
        .where(
            all_of(
                in_values("status", {"Pending", "Processing"}),
                negate(equals("priority", "Low")),
            )
        )
        .order_by("priority", descending=True)
        .order_by("order_date", descending=False)
        .execute()
    )

    print("\nPending/processing orders excluding low priority:")
    print_table(
        operational_queue,
        [
            "order_id",
            "priority",
            "status",
            "order_date",
            "order_value",
        ],
    )


def demonstrate_search_filter() -> None:
    print_title("Text filtering for customer operations")

    matching_customers = where(
        CUSTOMERS,
        contains("name", "health"),
    )

    print("\nCustomers whose names contain 'health':")
    print_table(
        matching_customers,
        ["customer_id", "name", "region", "segment"],
    )


def demonstrate_validation() -> None:
    print_title("Validation before business filtering")

    errors = validate_orders(ORDERS)

    if errors:
        print("Validation failures:")
        for error in errors:
            print(f"- {error}")
    else:
        print("All sample orders passed business-data validation.")

    try:
        Query(ORDERS).execute(offset=-1)
    except ValueError as exc:
        print(f"\nInvalid pagination rejected: {exc}")


def demonstrate_filter_order_relationship() -> None:
    print_title("Why filtering and sorting are separate operations")

    # Filtering first reduces the number of rows that need ordering.
    # In a database engine, indexes and query planning can make this
    # distinction especially important for large business tables.
    filtered = where(
        ORDERS,
        all_of(
            equals("region", "West"),
            greater_than("order_value", 200_000),
        ),
    )

    sorted_result = multi_sort(
        filtered,
        [
            ("order_value", True),
            ("order_id", False),
        ],
    )

    print("\nWest-region orders above 200K, ordered by value:")
    print_table(
        sorted_result,
        ["order_id", "region", "order_value", "status"],
    )


# ---------------------------------------------------------------------------
# A compact SQL-style query specification
# ---------------------------------------------------------------------------

@dataclass
class QuerySpec:
    """
    Represents the intent of a business-data query without executing SQL.

    This demonstrates the separation between:
    - selecting records
    - filtering records
    - ordering records
    - limiting the result set
    """

    conditions: list[Callable[[Any], bool]]
    order_by: list[tuple[str, bool]]
    offset: int = 0
    limit: Optional[int] = None


def execute_query_spec(
    rows: Iterable[Any],
    specification: QuerySpec,
) -> list[Any]:
    query = Query(list(rows))

    for condition in specification.conditions:
        query.where(condition)

    for field_name, descending in specification.order_by:
        query.order_by(field_name, descending)

    return query.execute(
        offset=specification.offset,
        limit=specification.limit,
    )


def demonstrate_query_specification() -> None:
    print_title("Reusable query specification")

    specification = QuerySpec(
        conditions=[
            equals("region", "North"),
            greater_or_equal("order_value", 100_000),
            negate(equals("status", "Cancelled")),
        ],
        order_by=[
            ("order_value", True),
            ("order_id", False),
        ],
        limit=5,
    )

    result = execute_query_spec(ORDERS, specification)

    print("\nNorth-region orders >= 100K, excluding cancelled orders:")
    print_table(
        result,
        ["order_id", "region", "order_value", "status"],
    )


# ---------------------------------------------------------------------------
# Advanced business analysis
# ---------------------------------------------------------------------------

def demonstrate_customer_order_analysis() -> None:
    print_title("Customer-level filtering using related order data")

    customer_lookup = {customer.customer_id: customer for customer in CUSTOMERS}

    shipped_orders = where(
        ORDERS,
        equals("status", "Shipped"),
    )

    revenue_by_customer: dict[int, float] = {}

    for order in shipped_orders:
        revenue_by_customer[order.customer_id] = (
            revenue_by_customer.get(order.customer_id, 0.0)
            + order.order_value
        )

    qualified_customers = [
        customer
        for customer in CUSTOMERS
        if revenue_by_customer.get(customer.customer_id, 0.0) >= 300_000
    ]

    qualified_customers.sort(
        key=lambda customer: revenue_by_customer.get(customer.customer_id, 0.0),
        reverse=True,
    )

    print("\nCustomers with at least 300K in shipped-order value:")
    for customer in qualified_customers:
        shipped_value = revenue_by_customer[customer.customer_id]
        print(
            f"{customer.name:22} "
            f"region={customer.region:6} "
            f"shipped_value={shipped_value:,.2f}"
        )

    # The lookup is intentionally retained to demonstrate how an application
    # can resolve foreign-key relationships without repeatedly scanning
    # the entire customer collection.
    missing_customer_orders = [
        order
        for order in shipped_orders
        if order.customer_id not in customer_lookup
    ]

    if missing_customer_orders:
        print("\nOrders with unknown customer references:")
        for order in missing_customer_orders:
            print(order.order_id)
    else:
        print("\nAll shipped orders reference known customers.")


def demonstrate_deterministic_sorting() -> None:
    print_title("Deterministic ordering for reproducible reports")

    # If two rows have identical order values, order_id provides a stable
    # secondary key. This prevents pagination from appearing to reshuffle
    # records between repeated executions.
    deterministic = multi_sort(
        ORDERS,
        [
            ("order_value", True),
            ("order_date", False),
            ("order_id", False),
        ],
    )

    print("\nOrders with explicit tie-breakers:")
    print_table(
        deterministic,
        ["order_id", "order_value", "order_date"],
    )


def demonstrate_performance_considerations() -> None:
    print_title("Performance characteristics")

    print(
        "A Python in-memory filter generally scans O(n) rows for each predicate."
    )
    print(
        "Sorting n retained rows generally costs O(n log n) comparisons."
    )
    print(
        "Applying selective filtering before sorting can reduce the number of "
        "rows that must be sorted."
    )
    print(
        "Production database engines can use indexes, statistics, query "
        "planners, and external sorting rather than loading all rows into Python."
    )

    filtered = where(
        ORDERS,
        greater_than("order_value", 200_000),
    )

    sorted_filtered = sort_by(
        filtered,
        "order_value",
        descending=True,
    )

    print(
        f"\nSample pipeline retained {len(filtered)} of {len(ORDERS)} "
        f"orders before sorting."
    )
    print_table(
        sorted_filtered,
        ["order_id", "order_value"],
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    demonstrate_basic_where()
    demonstrate_boolean_filtering()
    demonstrate_null_handling()
    demonstrate_order_by()
    demonstrate_query_pipeline()
    demonstrate_business_reporting()
    demonstrate_status_priority_workflow()
    demonstrate_search_filter()
    demonstrate_validation()
    demonstrate_filter_order_relationship()
    demonstrate_query_specification()
    demonstrate_customer_order_analysis()
    demonstrate_deterministic_sorting()
    demonstrate_performance_considerations()

    print_title("Filtering and sorting demonstration complete")


if __name__ == "__main__":
    main()
