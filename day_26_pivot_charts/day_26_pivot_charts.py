"""
Pivot Charts | Visualizing Business Performance

A self-contained study script for learning how pivot-style data aggregation
and charting can be used to visualize business performance.

The script starts with raw business transactions, builds reusable aggregation
logic, calculates business KPIs, creates pivot-style summaries, produces
terminal-friendly chart data, exports CSV/JSON reports, and demonstrates
advanced analytical techniques such as time grouping, Pareto analysis,
contribution analysis, ranking, growth rates, rolling averages, and
performance diagnostics.

No external packages are required. Charts are represented using textual
bar charts so that the program remains executable in a standard Python
installation without requiring a plotting library.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import csv
import io
import json
import math
import statistics
from typing import Any, Callable, Iterable, Sequence


# ============================================================================
# 1. FUNDAMENTAL CONCEPTS
# ============================================================================

print("=" * 78)
print("PIVOT CHARTS | VISUALIZING BUSINESS PERFORMANCE")
print("=" * 78)


@dataclass(frozen=True)
class Transaction:
    """
    One row of business transaction data.

    A pivot analysis normally starts with records containing dimensions
    (Region, Product, Segment, Channel, etc.) and measures (Sales, Profit,
    Quantity, Cost, etc.).
    """

    transaction_id: str
    transaction_date: date
    region: str
    segment: str
    category: str
    product: str
    channel: str
    salesperson: str
    quantity: int
    sales: Decimal
    cost: Decimal

    @property
    def profit(self) -> Decimal:
        """Profit is revenue minus cost."""
        return self.sales - self.cost

    @property
    def margin(self) -> Decimal:
        """Profit margin expressed as a decimal fraction."""
        if self.sales == 0:
            return Decimal("0")
        return self.profit / self.sales


# ============================================================================
# 2. SAMPLE BUSINESS DATA
# ============================================================================

def build_sample_data() -> list[Transaction]:
    """
    Build a realistic multi-dimensional business dataset.

    The records intentionally cover:
    - multiple months
    - regions
    - customer segments
    - product categories
    - products
    - sales channels
    - salespeople
    - different quantities
    - different profitability levels
    - a zero-profit and zero-sales edge case
    """
    raw_rows = [
        ("T001", "2026-01-05", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 4, "4800", "3400"),
        ("T002", "2026-01-08", "South", "Consumer", "Technology", "Phone", "Retail", "Ravi", 8, "6400", "5000"),
        ("T003", "2026-01-12", "West", "SMB", "Office", "Chair", "Partner", "Neha", 12, "3600", "2280"),
        ("T004", "2026-01-19", "East", "Enterprise", "Software", "Analytics", "Online", "Arjun", 3, "7500", "3300"),
        ("T005", "2026-02-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 10, "8000", "6200"),
        ("T006", "2026-02-10", "South", "SMB", "Office", "Desk", "Partner", "Ravi", 7, "3500", "2380"),
        ("T007", "2026-02-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 4, "10000", "4400"),
        ("T008", "2026-02-21", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 3, "3600", "2550"),
        ("T009", "2026-03-04", "North", "SMB", "Office", "Chair", "Partner", "Asha", 15, "4500", "2850"),
        ("T010", "2026-03-09", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 5, "6000", "4250"),
        ("T011", "2026-03-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 14, "11200", "8680"),
        ("T012", "2026-03-22", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 2, "5000", "2200"),
        ("T013", "2026-04-02", "North", "Enterprise", "Software", "Analytics", "Online", "Asha", 5, "12500", "5500"),
        ("T014", "2026-04-11", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 9, "4500", "3060"),
        ("T015", "2026-04-17", "West", "SMB", "Technology", "Laptop", "Partner", "Neha", 6, "7200", "5100"),
        ("T016", "2026-04-26", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 7, "5600", "4340"),
        ("T017", "2026-05-03", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 18, "14400", "11160"),
        ("T018", "2026-05-08", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 20, "6000", "3800"),
        ("T019", "2026-05-15", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 6, "15000", "6600"),
        ("T020", "2026-05-23", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 5, "6000", "4250"),
        ("T021", "2026-06-04", "North", "SMB", "Office", "Desk", "Partner", "Asha", 11, "5500", "3740"),
        ("T022", "2026-06-10", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 8, "9600", "6800"),
        ("T023", "2026-06-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 20, "16000", "12400"),
        ("T024", "2026-06-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 4, "10000", "4400"),
        ("T025", "2026-07-03", "North", "Enterprise", "Technology", "Laptop", "Online", "Asha", 9, "10800", "7650"),
        ("T026", "2026-07-09", "South", "Consumer", "Office", "Desk", "Retail", "Ravi", 13, "6500", "4420"),
        ("T027", "2026-07-15", "West", "SMB", "Software", "Analytics", "Partner", "Neha", 5, "12500", "5500"),
        ("T028", "2026-07-23", "East", "Enterprise", "Technology", "Phone", "Online", "Arjun", 10, "8000", "6200"),
        ("T029", "2026-08-04", "North", "Consumer", "Technology", "Phone", "Retail", "Asha", 22, "17600", "13640"),
        ("T030", "2026-08-12", "South", "SMB", "Office", "Chair", "Partner", "Ravi", 18, "5400", "3420"),
        ("T031", "2026-08-18", "West", "Enterprise", "Software", "Analytics", "Online", "Neha", 8, "20000", "8800"),
        ("T032", "2026-08-25", "East", "Consumer", "Technology", "Laptop", "Retail", "Arjun", 7, "8400", "5950"),
        ("T033", "2026-09-02", "North", "SMB", "Office", "Desk", "Partner", "Asha", 14, "7000", "4760"),
        ("T034", "2026-09-08", "South", "Enterprise", "Technology", "Laptop", "Online", "Ravi", 10, "12000", "8500"),
        ("T035", "2026-09-16", "West", "Consumer", "Technology", "Phone", "Retail", "Neha", 25, "20000", "15500"),
        ("T036", "2026-09-24", "East", "SMB", "Software", "Analytics", "Partner", "Arjun", 6, "15000", "6600"),
        ("T037", "2026-09-27", "North", "Consumer", "Office", "Chair", "Retail", "Asha", 0, "0", "0"),
    ]

    transactions: list[Transaction] = []

    for row in raw_rows:
        (
            transaction_id,
            transaction_date,
            region,
            segment,
            category,
            product,
            channel,
            salesperson,
            quantity,
            sales,
            cost,
        ) = row

        transactions.append(
            Transaction(
                transaction_id=transaction_id,
                transaction_date=datetime.strptime(transaction_date, "%Y-%m-%d").date(),
                region=region,
                segment=segment,
                category=category,
                product=product,
                channel=channel,
                salesperson=salesperson,
                quantity=quantity,
                sales=Decimal(sales),
                cost=Decimal(cost),
            )
        )

    return transactions


transactions = build_sample_data()

print(f"Loaded {len(transactions)} transactions.")
print()


# ============================================================================
# 3. BASIC BUSINESS METRICS
# ============================================================================

def total_sales(rows: Iterable[Transaction]) -> Decimal:
    return sum((row.sales for row in rows), Decimal("0"))


def total_cost(rows: Iterable[Transaction]) -> Decimal:
    return sum((row.cost for row in rows), Decimal("0"))


def total_profit(rows: Iterable[Transaction]) -> Decimal:
    return total_sales(rows) - total_cost(rows)


def total_quantity(rows: Iterable[Transaction]) -> int:
    return sum(row.quantity for row in rows)


def profit_margin(rows: Iterable[Transaction]) -> Decimal:
    sales = total_sales(rows)
    profit = total_profit(rows)
    return Decimal("0") if sales == 0 else profit / sales


def format_currency(value: Decimal) -> str:
    value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${value:,.2f}"


def format_percent(value: Decimal | float) -> str:
    return f"{float(value) * 100:.2f}%"


print("BASIC BUSINESS KPIs")
print("-" * 78)
print(f"Revenue:       {format_currency(total_sales(transactions))}")
print(f"Cost:          {format_currency(total_cost(transactions))}")
print(f"Profit:        {format_currency(total_profit(transactions))}")
print(f"Units sold:    {total_quantity(transactions):,}")
print(f"Profit margin: {format_percent(profit_margin(transactions))}")
print()


# ============================================================================
# 4. WHAT A PIVOT TABLE DOES
# ============================================================================

def pivot_sum(
    rows: Sequence[Transaction],
    row_field: str,
    value_field: str,
    column_field: str | None = None,
) -> dict[Any, Any]:
    """
    Generic pivot-style sum.

    Without column_field:
        {row_value: total}

    With column_field:
        {row_value: {column_value: total}}
    """
    if column_field is None:
        result: dict[Any, Decimal] = defaultdict(lambda: Decimal("0"))
        for row in rows:
            row_key = getattr(row, row_field)
            value = getattr(row, value_field)
            result[row_key] += Decimal(str(value))
        return dict(result)

    result_2d: dict[Any, dict[Any, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: Decimal("0"))
    )

    for row in rows:
        row_key = getattr(row, row_field)
        column_key = getattr(row, column_field)
        value = getattr(row, value_field)
        result_2d[row_key][column_key] += Decimal(str(value))

    return {key: dict(value) for key, value in result_2d.items()}


def print_simple_pivot(title: str, data: dict[Any, Decimal]) -> None:
    print(title)
    print("-" * 78)

    for key, value in sorted(data.items(), key=lambda item: item[1], reverse=True):
        print(f"{str(key):<25} {format_currency(value):>18}")

    print()


sales_by_region = pivot_sum(
    transactions,
    row_field="region",
    value_field="sales",
)

print_simple_pivot("SALES BY REGION", sales_by_region)


# ============================================================================
# 5. TWO-DIMENSIONAL PIVOT
# ============================================================================

def print_matrix_pivot(
    title: str,
    matrix: dict[Any, dict[Any, Decimal]],
) -> None:
    row_keys = sorted(matrix)
    column_keys = sorted(
        {
            column
            for row_data in matrix.values()
            for column in row_data
        }
    )

    print(title)
    print("-" * 78)

    header = f"{'Row':<18}" + "".join(f"{str(column):>16}" for column in column_keys)
    print(header)
    print("-" * len(header))

    for row_key in row_keys:
        line = f"{str(row_key):<18}"
        for column_key in column_keys:
            value = matrix.get(row_key, {}).get(column_key, Decimal("0"))
            line += f"{format_currency(value):>16}"
        print(line)

    print()


sales_by_region_and_segment = pivot_sum(
    transactions,
    row_field="region",
    value_field="sales",
    column_field="segment",
)

print_matrix_pivot(
    "SALES BY REGION AND CUSTOMER SEGMENT",
    sales_by_region_and_segment,
)


# ============================================================================
# 6. MULTI-MEASURE PIVOT
# ============================================================================

def multi_measure_pivot(
    rows: Sequence[Transaction],
    dimension: str,
) -> dict[str, dict[str, Decimal]]:
    """
    Produces a pivot table containing several measures.

    A business dashboard often needs more than one metric for the same
    dimension. Sales alone can hide low-margin products.
    """
    output: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "sales": Decimal("0"),
            "cost": Decimal("0"),
            "profit": Decimal("0"),
            "quantity": Decimal("0"),
        }
    )

    for row in rows:
        key = str(getattr(row, dimension))
        output[key]["sales"] += row.sales
        output[key]["cost"] += row.cost
        output[key]["profit"] += row.profit
        output[key]["quantity"] += Decimal(row.quantity)

    return dict(output)


region_metrics = multi_measure_pivot(transactions, "region")

print("MULTI-MEASURE PIVOT: REGION")
print("-" * 78)
for region, metrics in sorted(region_metrics.items()):
    margin = (
        Decimal("0")
        if metrics["sales"] == 0
        else metrics["profit"] / metrics["sales"]
    )
    print(
        f"{region:<10} "
        f"Sales={format_currency(metrics['sales']):>12} "
        f"Profit={format_currency(metrics['profit']):>12} "
        f"Margin={format_percent(margin):>8} "
        f"Units={int(metrics['quantity']):>5}"
    )
print()


# ============================================================================
# 7. PIVOT CHART DATA
# ============================================================================

def scale_bar(value: Decimal, maximum: Decimal, width: int = 42) -> str:
    """
    Convert a numeric measure into a proportional text bar.

    This is a chart representation that works in a terminal without external
    visualization packages.
    """
    if maximum <= 0:
        return ""

    units = int((value / maximum) * width)
    return "#" * max(0, units)


def print_bar_chart(
    title: str,
    data: dict[str, Decimal],
    width: int = 42,
) -> None:
    print(title)
    print("-" * 78)

    if not data:
        print("No data.")
        print()
        return

    maximum = max(data.values())

    for label, value in sorted(data.items(), key=lambda item: item[1], reverse=True):
        bar = scale_bar(value, maximum, width)
        print(f"{label:<15} | {bar:<{width}} {format_currency(value)}")

    print()


print_bar_chart("PIVOT CHART: SALES BY REGION", sales_by_region)


# ============================================================================
# 8. GROUPING BY MONTH
# ============================================================================

def month_key(transaction: Transaction) -> str:
    return transaction.transaction_date.strftime("%Y-%m")


sales_by_month = pivot_sum(
    transactions,
    row_field="transaction_date",
    value_field="sales",
)

monthly_sales: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

for transaction in transactions:
    monthly_sales[month_key(transaction)] += transaction.sales

monthly_sales = dict(sorted(monthly_sales.items()))

print_bar_chart("PIVOT CHART: MONTHLY SALES", monthly_sales)


# ============================================================================
# 9. MONTHLY BUSINESS PERFORMANCE
# ============================================================================

def monthly_metrics(
    rows: Sequence[Transaction],
) -> dict[str, dict[str, Decimal]]:
    result: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "sales": Decimal("0"),
            "cost": Decimal("0"),
            "profit": Decimal("0"),
            "quantity": Decimal("0"),
        }
    )

    for row in rows:
        key = month_key(row)
        result[key]["sales"] += row.sales
        result[key]["cost"] += row.cost
        result[key]["profit"] += row.profit
        result[key]["quantity"] += Decimal(row.quantity)

    return dict(sorted(result.items()))


month_metrics = monthly_metrics(transactions)

print("MONTHLY PERFORMANCE")
print("-" * 78)

for month, metrics in month_metrics.items():
    margin = (
        Decimal("0")
        if metrics["sales"] == 0
        else metrics["profit"] / metrics["sales"]
    )
    print(
        f"{month}  "
        f"Sales={format_currency(metrics['sales']):>12}  "
        f"Profit={format_currency(metrics['profit']):>12}  "
        f"Margin={format_percent(margin):>8}"
    )

print()


# ============================================================================
# 10. GROWTH ANALYSIS
# ============================================================================

def growth_rate(current: Decimal, previous: Decimal) -> Decimal | None:
    """
    Calculate percentage growth.

    None is returned when the previous value is zero because percentage
    growth from zero is undefined.
    """
    if previous == 0:
        return None

    return (current - previous) / previous


def monthly_growth(
    monthly_values: dict[str, Decimal],
) -> dict[str, Decimal | None]:
    months = list(monthly_values.keys())
    result: dict[str, Decimal | None] = {}

    for index, month in enumerate(months):
        if index == 0:
            result[month] = None
            continue

        result[month] = growth_rate(
            monthly_values[month],
            monthly_values[months[index - 1]],
        )

    return result


sales_growth = monthly_growth(monthly_sales)

print("MONTH-OVER-MONTH SALES GROWTH")
print("-" * 78)

for month, growth in sales_growth.items():
    value = "N/A" if growth is None else format_percent(growth)
    print(f"{month}: {value}")

print()


# ============================================================================
# 11. PRODUCT PERFORMANCE
# ============================================================================

product_metrics = multi_measure_pivot(transactions, "product")

print("PRODUCT PERFORMANCE")
print("-" * 78)

for product, metrics in sorted(
    product_metrics.items(),
    key=lambda item: item[1]["sales"],
    reverse=True,
):
    margin = (
        Decimal("0")
        if metrics["sales"] == 0
        else metrics["profit"] / metrics["sales"]
    )
    print(
        f"{product:<12} "
        f"Sales={format_currency(metrics['sales']):>12} "
        f"Profit={format_currency(metrics['profit']):>12} "
        f"Margin={format_percent(margin):>8}"
    )

print()


# ============================================================================
# 12. TOP-N ANALYSIS
# ============================================================================

def top_n(
    data: dict[str, Decimal],
    n: int,
) -> list[tuple[str, Decimal]]:
    return sorted(
        data.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:n]


top_products = top_n(
    {key: value["sales"] for key, value in product_metrics.items()},
    3,
)

print("TOP 3 PRODUCTS BY SALES")
print("-" * 78)

for rank, (product, sales) in enumerate(top_products, start=1):
    print(f"{rank}. {product}: {format_currency(sales)}")

print()


# ============================================================================
# 13. PARETO ANALYSIS
# ============================================================================

def pareto_analysis(
    data: dict[str, Decimal],
) -> list[dict[str, Any]]:
    ordered = sorted(data.items(), key=lambda item: item[1], reverse=True)
    total = sum(data.values(), Decimal("0"))
    cumulative = Decimal("0")

    result = []

    for key, value in ordered:
        cumulative += value
        share = Decimal("0") if total == 0 else value / total
        cumulative_share = (
            Decimal("0") if total == 0 else cumulative / total
        )

        result.append(
            {
                "key": key,
                "value": value,
                "share": share,
                "cumulative_share": cumulative_share,
            }
        )

    return result


product_sales = {
    product: metrics["sales"]
    for product, metrics in product_metrics.items()
}

pareto = pareto_analysis(product_sales)

print("PRODUCT PARETO ANALYSIS")
print("-" * 78)

for row in pareto:
    print(
        f"{row['key']:<12} "
        f"Share={format_percent(row['share']):>8} "
        f"Cumulative={format_percent(row['cumulative_share']):>10}"
    )

print()


# ============================================================================
# 14. CONTRIBUTION ANALYSIS
# ============================================================================

def contribution_percentages(
    data: dict[str, Decimal],
) -> dict[str, Decimal]:
    total = sum(data.values(), Decimal("0"))

    if total == 0:
        return {key: Decimal("0") for key in data}

    return {
        key: value / total
        for key, value in data.items()
    }


region_contribution = contribution_percentages(sales_by_region)

print("REGIONAL SALES CONTRIBUTION")
print("-" * 78)

for region, contribution in sorted(
    region_contribution.items(),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{region:<12} {format_percent(contribution):>10}")

print()


# ============================================================================
# 15. CROSS-FILTERING
# ============================================================================

def filter_transactions(
    rows: Sequence[Transaction],
    predicate: Callable[[Transaction], bool],
) -> list[Transaction]:
    return [row for row in rows if predicate(row)]


enterprise_transactions = filter_transactions(
    transactions,
    lambda row: row.segment == "Enterprise",
)

enterprise_sales_by_region = pivot_sum(
    enterprise_transactions,
    "region",
    "sales",
)

print_bar_chart(
    "ENTERPRISE SALES BY REGION",
    enterprise_sales_by_region,
)


# ============================================================================
# 16. FILTER + PIVOT + CHART
# ============================================================================

west_transactions = filter_transactions(
    transactions,
    lambda row: row.region == "West",
)

west_product_sales = pivot_sum(
    west_transactions,
    "product",
    "sales",
)

print_bar_chart(
    "WEST REGION: SALES BY PRODUCT",
    west_product_sales,
)


# ============================================================================
# 17. HANDLING MISSING, ZERO, AND INVALID VALUES
# ============================================================================

def safe_divide(
    numerator: Decimal,
    denominator: Decimal,
) -> Decimal | None:
    """
    Safe division prevents a dashboard from producing misleading infinite
    values or crashing when the denominator is zero.
    """
    if denominator == 0:
        return None
    return numerator / denominator


print("EDGE CASE HANDLING")
print("-" * 78)

zero_sales_transaction = transactions[-1]

print(
    "Zero-sales margin:",
    safe_divide(
        zero_sales_transaction.profit,
        zero_sales_transaction.sales,
    ),
)

print()


# ============================================================================
# 18. DATA VALIDATION
# ============================================================================

def validate_transactions(rows: Sequence[Transaction]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()

    for row in rows:
        if row.transaction_id in seen_ids:
            errors.append(f"Duplicate transaction ID: {row.transaction_id}")
        seen_ids.add(row.transaction_id)

        if row.quantity < 0:
            errors.append(f"Negative quantity: {row.transaction_id}")

        if row.sales < 0:
            errors.append(f"Negative sales: {row.transaction_id}")

        if row.cost < 0:
            errors.append(f"Negative cost: {row.transaction_id}")

        if not row.region.strip():
            errors.append(f"Missing region: {row.transaction_id}")

        if not row.product.strip():
            errors.append(f"Missing product: {row.transaction_id}")

    return errors


validation_errors = validate_transactions(transactions)

print("DATA VALIDATION")
print("-" * 78)

if validation_errors:
    for error in validation_errors:
        print("ERROR:", error)
else:
    print("All sample records passed validation.")

print()


# ============================================================================
# 19. RANKING WITH TIES
# ============================================================================

def dense_rank(data: dict[str, Decimal]) -> dict[str, int]:
    ordered = sorted(
        data.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    ranks: dict[str, int] = {}
    current_rank = 0
    previous_value: Decimal | None = None

    for key, value in ordered:
        if previous_value is None or value != previous_value:
            current_rank += 1

        ranks[key] = current_rank
        previous_value = value

    return ranks


salesperson_sales = pivot_sum(
    transactions,
    "salesperson",
    "sales",
)

salesperson_ranks = dense_rank(salesperson_sales)

print("SALESPERSON RANKING")
print("-" * 78)

for salesperson, sales in sorted(
    salesperson_sales.items(),
    key=lambda item: item[1],
    reverse=True,
):
    print(
        f"Rank {salesperson_ranks[salesperson]}  "
        f"{salesperson:<10} "
        f"{format_currency(sales):>12}"
    )

print()


# ============================================================================
# 20. ROLLING AVERAGE
# ============================================================================

def rolling_average(
    values: Sequence[Decimal],
    window: int,
) -> list[Decimal]:
    if window <= 0:
        raise ValueError("Window must be positive.")

    result: list[Decimal] = []

    for index in range(len(values)):
        start = max(0, index - window + 1)
        segment = values[start : index + 1]

        result.append(
            sum(segment, Decimal("0")) / Decimal(len(segment))
        )

    return result


monthly_sales_values = list(monthly_sales.values())
monthly_sales_rolling_3 = rolling_average(
    monthly_sales_values,
    window=3,
)

print("3-MONTH ROLLING SALES AVERAGE")
print("-" * 78)

for month, average in zip(monthly_sales.keys(), monthly_sales_rolling_3):
    print(f"{month}: {format_currency(average)}")

print()


# ============================================================================
# 21. BUSINESS KPI CARD MODEL
# ============================================================================

def kpi_cards(rows: Sequence[Transaction]) -> list[dict[str, str]]:
    sales = total_sales(rows)
    cost = total_cost(rows)
    profit = sales - cost
    units = total_quantity(rows)
    margin = safe_divide(profit, sales)

    return [
        {"name": "Revenue", "value": format_currency(sales)},
        {"name": "Cost", "value": format_currency(cost)},
        {"name": "Profit", "value": format_currency(profit)},
        {"name": "Units", "value": f"{units:,}"},
        {
            "name": "Margin",
            "value": "N/A" if margin is None else format_percent(margin),
        },
    ]


print("DASHBOARD KPI CARDS")
print("-" * 78)

for card in kpi_cards(transactions):
    print(f"{card['name']:<15}: {card['value']}")

print()


# ============================================================================
# 22. EXECUTIVE DASHBOARD DATA MODEL
# ============================================================================

def build_dashboard_model(rows: Sequence[Transaction]) -> dict[str, Any]:
    sales = total_sales(rows)
    cost = total_cost(rows)
    profit = total_profit(rows)

    region_sales = pivot_sum(rows, "region", "sales")
    product_sales = pivot_sum(rows, "product", "sales")
    channel_sales = pivot_sum(rows, "channel", "sales")

    month_data = monthly_metrics(rows)

    return {
        "kpis": {
            "revenue": str(sales),
            "cost": str(cost),
            "profit": str(profit),
            "profit_margin": (
                str(Decimal("0"))
                if sales == 0
                else str(profit / sales)
            ),
            "units": total_quantity(rows),
        },
        "charts": {
            "sales_by_region": {
                key: str(value)
                for key, value in region_sales.items()
            },
            "sales_by_product": {
                key: str(value)
                for key, value in product_sales.items()
            },
            "sales_by_channel": {
                key: str(value)
                for key, value in channel_sales.items()
            },
            "monthly": {
                month: {
                    metric: str(value)
                    for metric, value in metrics.items()
                }
                for month, metrics in month_data.items()
            },
        },
    }


dashboard_model = build_dashboard_model(transactions)

print("DASHBOARD MODEL CREATED")
print("-" * 78)
print(json.dumps(dashboard_model, indent=2))
print()


# ============================================================================
# 23. CSV EXPORT
# ============================================================================

def transactions_to_csv(rows: Sequence[Transaction]) -> str:
    buffer = io.StringIO()

    fieldnames = [
        "transaction_id",
        "transaction_date",
        "region",
        "segment",
        "category",
        "product",
        "channel",
        "salesperson",
        "quantity",
        "sales",
        "cost",
        "profit",
        "margin",
    ]

    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow(
            {
                "transaction_id": row.transaction_id,
                "transaction_date": row.transaction_date.isoformat(),
                "region": row.region,
                "segment": row.segment,
                "category": row.category,
                "product": row.product,
                "channel": row.channel,
                "salesperson": row.salesperson,
                "quantity": row.quantity,
                "sales": str(row.sales),
                "cost": str(row.cost),
                "profit": str(row.profit),
                "margin": str(row.margin),
            }
        )

    return buffer.getvalue()


csv_preview = transactions_to_csv(transactions)

print("CSV EXPORT PREVIEW")
print("-" * 78)
print("\n".join(csv_preview.splitlines()[:5]))
print()


# ============================================================================
# 24. JSON EXPORT
# ============================================================================

json_export = json.dumps(dashboard_model, indent=2)

print("JSON EXPORT PREVIEW")
print("-" * 78)
print("\n".join(json_export.splitlines()[:12]))
print()


# ============================================================================
# 25. ADVANCED ANALYSIS: MARGIN RANKING
# ============================================================================

def margin_by_dimension(
    rows: Sequence[Transaction],
    dimension: str,
) -> dict[str, Decimal]:
    grouped_sales: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    grouped_profit: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for row in rows:
        key = str(getattr(row, dimension))
        grouped_sales[key] += row.sales
        grouped_profit[key] += row.profit

    result: dict[str, Decimal] = {}

    for key in grouped_sales:
        result[key] = safe_divide(
            grouped_profit[key],
            grouped_sales[key],
        ) or Decimal("0")

    return result


product_margins = margin_by_dimension(transactions, "product")

print("PRODUCT MARGIN RANKING")
print("-" * 78)

for product, margin in sorted(
    product_margins.items(),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{product:<12} {format_percent(margin):>10}")

print()


# ============================================================================
# 26. SALES VERSUS PROFIT COMPARISON
# ============================================================================

def print_comparison_chart(
    sales_data: dict[str, Decimal],
    profit_data: dict[str, Decimal],
) -> None:
    labels = sorted(set(sales_data) | set(profit_data))
    maximum = max(
        [sales_data.get(label, Decimal("0")) for label in labels]
        + [profit_data.get(label, Decimal("0")) for label in labels]
    )

    print("SALES VS PROFIT")
    print("-" * 78)

    for label in labels:
        sales_bar = scale_bar(sales_data.get(label, Decimal("0")), maximum, 25)
        profit_bar = scale_bar(profit_data.get(label, Decimal("0")), maximum, 25)

        print(
            f"{label:<12} "
            f"S:{sales_bar:<25} "
            f"P:{profit_bar:<25}"
        )

    print()


region_profit = {
    region: metrics["profit"]
    for region, metrics in region_metrics.items()
}

print_comparison_chart(
    sales_by_region,
    region_profit,
)


# ============================================================================
# 27. SIMPLE STATISTICAL ANALYSIS
# ============================================================================

def mean(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def median(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")

    numeric_values = [float(value) for value in values]
    return Decimal(str(statistics.median(numeric_values)))


monthly_profit_values = [
    metrics["profit"]
    for metrics in month_metrics.values()
]

print("MONTHLY PROFIT STATISTICS")
print("-" * 78)
print(f"Mean:   {format_currency(mean(monthly_profit_values))}")
print(f"Median: {format_currency(median(monthly_profit_values))}")
print()


# ============================================================================
# 28. BUSINESS ANOMALY DETECTION
# ============================================================================

def detect_low_margin_products(
    rows: Sequence[Transaction],
    threshold: Decimal,
) -> list[tuple[str, Decimal]]:
    margins = margin_by_dimension(rows, "product")

    return [
        (product, margin)
        for product, margin in margins.items()
        if margin < threshold
    ]


low_margin_products = detect_low_margin_products(
    transactions,
    Decimal("0.25"),
)

print("LOW-MARGIN PRODUCT CHECK")
print("-" * 78)

if low_margin_products:
    for product, margin in low_margin_products:
        print(f"{product:<12} {format_percent(margin)}")
else:
    print("No products are below the selected margin threshold.")

print()


# ============================================================================
# 29. PERFORMANCE CONSIDERATIONS
# ============================================================================

def benchmark_style_operation(rows: Sequence[Transaction]) -> dict[str, int]:
    """
    Illustrates operation counts rather than pretending to be a precise
    wall-clock benchmark.

    A real production benchmark should use time.perf_counter(), realistic
    datasets, repeated trials, and controlled environments.
    """
    operation_count = 0

    for row in rows:
        _ = row.region
        _ = row.sales
        operation_count += 2

    return {
        "records_processed": len(rows),
        "illustrative_operations": operation_count,
    }


performance = benchmark_style_operation(transactions)

print("PERFORMANCE MODEL")
print("-" * 78)
print(f"Records processed: {performance['records_processed']}")
print(f"Illustrative operations: {performance['illustrative_operations']}")
print(
    "Most single-pass grouping operations are approximately O(n), "
    "while sorting a grouped result is typically O(k log k), where "
    "n is the number of transactions and k is the number of groups."
)
print()


# ============================================================================
# 30. TESTABLE BUSINESS RULES
# ============================================================================

def run_assertion_tests(rows: Sequence[Transaction]) -> None:
    assert len(rows) > 0
    assert total_sales(rows) >= Decimal("0")
    assert total_cost(rows) >= Decimal("0")
    assert total_profit(rows) == total_sales(rows) - total_cost(rows)

    regions = pivot_sum(rows, "region", "sales")
    assert sum(regions.values(), Decimal("0")) == total_sales(rows)

    product_data = multi_measure_pivot(rows, "product")
    assert sum(
        item["sales"] for item in product_data.values()
    ) == total_sales(rows)


run_assertion_tests(transactions)

print("TESTS")
print("-" * 78)
print("All internal assertions passed.")
print()


# ============================================================================
# 31. DATA-QUALITY FAILURE EXAMPLE
# ============================================================================

def parse_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def demonstrate_validation_failure() -> None:
    test_values = ["100.50", "0", "-20", "not-a-number"]

    print("DECIMAL VALIDATION EXAMPLE")
    print("-" * 78)

    for value in test_values:
        try:
            parsed = parse_decimal(value)
            print(f"{value!r} -> {parsed}")
        except ValueError as error:
            print(f"{value!r} -> rejected: {error}")

    print()


demonstrate_validation_failure()


# ============================================================================
# 32. EXECUTIVE INSIGHT GENERATION
# ============================================================================

def generate_business_insights(
    rows: Sequence[Transaction],
) -> list[str]:
    insights: list[str] = []

    region_data = pivot_sum(rows, "region", "sales")
    product_data = pivot_sum(rows, "product", "sales")
    margins = margin_by_dimension(rows, "product")

    if region_data:
        best_region, best_region_sales = max(
            region_data.items(),
            key=lambda item: item[1],
        )
        insights.append(
            f"{best_region} has the highest regional sales at "
            f"{format_currency(best_region_sales)}."
        )

    if product_data:
        best_product, best_product_sales = max(
            product_data.items(),
            key=lambda item: item[1],
        )
        insights.append(
            f"{best_product} generates the highest product sales at "
            f"{format_currency(best_product_sales)}."
        )

    if margins:
        best_margin_product, best_margin = max(
            margins.items(),
            key=lambda item: item[1],
        )
        insights.append(
            f"{best_margin_product} has the highest product margin at "
            f"{format_percent(best_margin)}."
        )

    return insights


print("DATA-DRIVEN BUSINESS INSIGHTS")
print("-" * 78)

for insight in generate_business_insights(transactions):
    print("-", insight)

print()


# ============================================================================
# 33. PRACTICAL PIVOT-CHART DESIGN PRINCIPLES
# ============================================================================

design_principles = [
    "Choose a dimension that answers a real business question.",
    "Choose a measure that represents the business outcome.",
    "Use aggregation functions appropriate to the measure.",
    "Use filters to isolate relevant populations.",
    "Use time grouping for trend analysis.",
    "Use bar charts for categorical comparisons.",
    "Use line charts for trends across ordered time.",
    "Use stacked charts only when composition matters.",
    "Avoid decorative 3D effects that obscure values.",
    "Show units, currency, and time periods clearly.",
    "Compare sales with profit when revenue alone can mislead.",
    "Validate source data before trusting dashboard results.",
    "Document definitions for every KPI.",
]

print("PIVOT-CHART DESIGN PRINCIPLES")
print("-" * 78)

for index, principle in enumerate(design_principles, start=1):
    print(f"{index:02d}. {principle}")

print()


# ============================================================================
# 34. ADVANCED TOPIC: STAR-SCHEMA THINKING
# ============================================================================

print("STAR-SCHEMA CONCEPT")
print("-" * 78)
print(
    "A production business analytics system often separates a fact table "
    "from dimensions. The transaction records in this example behave like "
    "a simplified fact table, while region, product, customer segment, "
    "channel, salesperson, and date behave like dimensions."
)
print(
    "This separation makes pivot-style analysis scalable and easier to "
    "govern when the dataset grows."
)
print()


# ============================================================================
# 35. ADVANCED TOPIC: SECURITY AND GOVERNANCE
# ============================================================================

security_principles = [
    "Do not expose confidential customer or financial records in public dashboards.",
    "Apply access control to sensitive business metrics.",
    "Validate uploaded CSV and spreadsheet values before aggregation.",
    "Avoid executing formulas or scripts originating from untrusted data.",
    "Log data refreshes and report generation events in production systems.",
    "Protect credentials and database connection information.",
    "Use least-privilege access for analytics services.",
    "Document metric definitions to prevent unauthorized reinterpretation.",
]

print("SECURITY AND GOVERNANCE")
print("-" * 78)

for principle in security_principles:
    print("-", principle)

print()


# ============================================================================
# 36. FINAL DASHBOARD REPORT
# ============================================================================

def print_executive_report(rows: Sequence[Transaction]) -> None:
    sales = total_sales(rows)
    profit = total_profit(rows)
    margin = safe_divide(profit, sales)

    region_sales = pivot_sum(rows, "region", "sales")
    product_sales = pivot_sum(rows, "product", "sales")

    best_region = max(region_sales.items(), key=lambda item: item[1])
    best_product = max(product_sales.items(), key=lambda item: item[1])

    print("=" * 78)
    print("EXECUTIVE BUSINESS PERFORMANCE REPORT")
    print("=" * 78)
    print(f"Revenue:              {format_currency(sales)}")
    print(f"Profit:               {format_currency(profit)}")
    print(
        f"Profit margin:        "
        f"{'N/A' if margin is None else format_percent(margin)}"
    )
    print(f"Units sold:           {total_quantity(rows):,}")
    print(
        f"Highest-sales region: {best_region[0]} "
        f"({format_currency(best_region[1])})"
    )
    print(
        f"Highest-sales product:{best_product[0]} "
        f"({format_currency(best_product[1])})"
    )
    print()
    print("The report is generated from the same grouped data structures used")
    print("for the pivot-style analysis and chart representations.")
    print("=" * 78)


print_executive_report(transactions)
