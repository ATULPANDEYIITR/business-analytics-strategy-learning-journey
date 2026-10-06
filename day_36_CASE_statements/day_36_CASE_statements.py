"""
CASE Statements: Creating Business Logic Using SQL

This executable Python script teaches SQL CASE expressions by modeling a
subscription-commerce business. Python is used to generate realistic data,
run equivalent business rules locally, and produce PostgreSQL SQL that can
be executed against the same conceptual model.

The SQL itself is the controlling implementation. Python deliberately focuses
on how conditional business rules can be represented, tested, compared, and
validated before being placed into SQL queries.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Iterable


@dataclass(frozen=True)
class Customer:
    customer_id: int
    name: str
    country: str
    lifetime_value: Decimal
    account_status: str


@dataclass(frozen=True)
class Order:
    order_id: int
    customer_id: int
    subtotal: Decimal
    shipping: Decimal
    payment_status: str
    order_status: str


def classify_customer(customer: Customer) -> str:
    """Equivalent to a searched SQL CASE expression."""
    if customer.account_status == "suspended":
        return "RESTRICTED"
    if customer.lifetime_value >= Decimal("100000"):
        return "PLATINUM"
    if customer.lifetime_value >= Decimal("50000"):
        return "GOLD"
    if customer.lifetime_value >= Decimal("10000"):
        return "SILVER"
    return "STANDARD"


def customer_risk(customer: Customer) -> str:
    """
    Demonstrates condition precedence.

    A restricted account is classified before monetary thresholds, just as
    the first matching WHEN branch wins in SQL CASE.
    """
    if customer.account_status == "suspended":
        return "HIGH"
    if customer.lifetime_value >= Decimal("75000"):
        return "LOW"
    if customer.lifetime_value >= Decimal("25000"):
        return "MEDIUM"
    return "NORMAL"


def order_payment_label(order: Order) -> str:
    """Equivalent to CASE payment_status WHEN ... END."""
    labels = {
        "paid": "SETTLED",
        "pending": "AWAITING PAYMENT",
        "failed": "PAYMENT FAILED",
        "refunded": "REFUNDED",
    }
    return labels.get(order.payment_status, "UNKNOWN PAYMENT STATE")


def shipping_priority(order: Order) -> str:
    """
    Demonstrates a multi-condition business rule.

    The rule deliberately separates payment validity from monetary value:
    an expensive unpaid order must not become a priority shipment.
    """
    if order.order_status == "cancelled":
        return "DO NOT SHIP"
    if order.payment_status != "paid":
        return "HOLD"
    total = order.subtotal + order.shipping
    if total >= Decimal("10000"):
        return "URGENT"
    if total >= Decimal("5000"):
        return "HIGH"
    return "NORMAL"


def discount_rate(customer: Customer, order: Order) -> Decimal:
    """Business rule with explicit precedence and a capped discount."""
    if order.payment_status != "paid":
        return Decimal("0.00")
    if customer.account_status == "suspended":
        return Decimal("0.00")

    total = order.subtotal + order.shipping

    if customer.lifetime_value >= Decimal("100000") and total >= Decimal("5000"):
        return Decimal("0.15")
    if customer.lifetime_value >= Decimal("50000"):
        return Decimal("0.10")
    if total >= Decimal("10000"):
        return Decimal("0.08")
    if total >= Decimal("5000"):
        return Decimal("0.05")
    return Decimal("0.00")


def normalize_region(country: str) -> str:
    """
    Demonstrates a simple CASE-style lookup.

    Unknown countries intentionally map to OTHER rather than producing an
    invalid category.
    """
    mapping = {
        "IN": "APAC",
        "JP": "APAC",
        "SG": "APAC",
        "DE": "EUROPE",
        "FR": "EUROPE",
        "GB": "EUROPE",
        "US": "NORTH_AMERICA",
        "CA": "NORTH_AMERICA",
    }
    return mapping.get(country.upper(), "OTHER")


def sql_case_examples() -> dict[str, str]:
    """
    Return representative PostgreSQL expressions.

    Simple CASE compares one expression against multiple values.
    Searched CASE evaluates independent Boolean conditions.
    """
    return {
        "simple_case": """
CASE payment_status
    WHEN 'paid' THEN 'SETTLED'
    WHEN 'pending' THEN 'AWAITING PAYMENT'
    WHEN 'failed' THEN 'PAYMENT FAILED'
    WHEN 'refunded' THEN 'REFUNDED'
    ELSE 'UNKNOWN PAYMENT STATE'
END
""".strip(),
        "searched_case": """
CASE
    WHEN account_status = 'suspended' THEN 'RESTRICTED'
    WHEN lifetime_value >= 100000 THEN 'PLATINUM'
    WHEN lifetime_value >= 50000 THEN 'GOLD'
    WHEN lifetime_value >= 10000 THEN 'SILVER'
    ELSE 'STANDARD'
END
""".strip(),
        "conditional_aggregation": """
SUM(
    CASE
        WHEN payment_status = 'paid' THEN subtotal + shipping
        ELSE 0
    END
)
""".strip(),
        "conditional_count": """
COUNT(
    CASE
        WHEN payment_status = 'failed' THEN 1
    END
)
""".strip(),
    }


def validate_case_rule(
    name: str,
    evaluator: Callable[[Customer], str],
    cases: Iterable[tuple[Customer, str]],
) -> None:
    """Test business-rule outcomes without requiring a database."""
    failures: list[str] = []

    for customer, expected in cases:
        actual = evaluator(customer)
        if actual != expected:
            failures.append(
                f"{name}: customer {customer.customer_id}: "
                f"expected {expected}, received {actual}"
            )

    if failures:
        raise AssertionError("\n".join(failures))


def demonstrate_null_behavior() -> None:
    """
    SQL NULL is not equivalent to an ordinary Python value.

    A CASE condition such as lifetime_value >= 50000 evaluates to UNKNOWN
    when lifetime_value is NULL. If no WHEN condition is true, ELSE is used.
    """
    print("\nNULL behavior:")
    print(
        "SQL CASE WHEN lifetime_value >= 50000 "
        "THEN 'GOLD' ELSE 'STANDARD' END "
        "classifies NULL as STANDARD unless a separate NULL branch exists."
    )


def print_customer_report(customers: list[Customer]) -> None:
    print("\nCustomer classification")
    print("-" * 78)

    for customer in customers:
        print(
            f"{customer.customer_id:>3} | "
            f"{customer.name:<14} | "
            f"{customer.country:<2} | "
            f"{normalize_region(customer.country):<16} | "
            f"{classify_customer(customer):<9} | "
            f"{customer_risk(customer):<6}"
        )


def print_order_report(
    customers: dict[int, Customer],
    orders: list[Order],
) -> None:
    print("\nOrder business-rule evaluation")
    print("-" * 105)

    for order in orders:
        customer = customers[order.customer_id]
        rate = discount_rate(customer, order)
        gross = order.subtotal + order.shipping
        discount = (gross * rate).quantize(Decimal("0.01"))
        net = gross - discount

        print(
            f"Order {order.order_id}: "
            f"customer={customer.name}, "
            f"gross={gross:.2f}, "
            f"payment={order_payment_label(order)}, "
            f"priority={shipping_priority(order)}, "
            f"discount={rate:.0%}, "
            f"net={net:.2f}"
        )


def main() -> None:
    customers = [
        Customer(1, "Aarav Labs", "IN", Decimal("125000"), "active"),
        Customer(2, "Northwind", "US", Decimal("62000"), "active"),
        Customer(3, "BerlinWorks", "DE", Decimal("18000"), "active"),
        Customer(4, "SmallMart", "IN", Decimal("2400"), "active"),
        Customer(5, "RiskAccount", "US", Decimal("200000"), "suspended"),
        Customer(6, "Tokyo Systems", "JP", Decimal("75000"), "active"),
    ]

    orders = [
        Order(101, 1, Decimal("12000"), Decimal("250"), "paid", "confirmed"),
        Order(102, 2, Decimal("7000"), Decimal("200"), "paid", "confirmed"),
        Order(103, 3, Decimal("3000"), Decimal("150"), "pending", "confirmed"),
        Order(104, 4, Decimal("850"), Decimal("80"), "failed", "cancelled"),
        Order(105, 5, Decimal("15000"), Decimal("250"), "paid", "confirmed"),
        Order(106, 6, Decimal("5000"), Decimal("150"), "paid", "confirmed"),
    ]

    customer_map = {customer.customer_id: customer for customer in customers}

    validate_case_rule(
        "customer classification",
        classify_customer,
        [
            (customers[0], "PLATINUM"),
            (customers[1], "GOLD"),
            (customers[2], "SILVER"),
            (customers[3], "STANDARD"),
            (customers[4], "RESTRICTED"),
        ],
    )

    print("CASE statement business-logic demonstration")
    print_customer_report(customers)
    print_order_report(customer_map, orders)

    print("\nCASE expression patterns")
    print("-" * 78)
    for name, expression in sql_case_examples().items():
        print(f"\n{name}:\n{expression}")

    demonstrate_null_behavior()

    print("\nImportant design observation:")
    print(
        "CASE should express deterministic classification or transformation "
        "rules. Referential integrity, uniqueness, and multi-row invariants "
        "belong in constraints, indexes, triggers, or application workflows."
    )


if __name__ == "__main__":
    main()
