#!/usr/bin/env python3
"""
GROUP BY: Segmenting and Aggregating Business Data

A self-contained business analytics study of SQL-style GROUP BY concepts
implemented with Python data structures and standard-library tools.

The examples use sales transactions and demonstrate:
- Grouping by one or more business dimensions
- SUM, COUNT, AVG, MIN, MAX
- Conditional aggregation
- Multi-level segmentation
- HAVING-style post-aggregation filtering
- NULL/missing-value handling
- Time-period aggregation
- Revenue and margin calculations
- Top-segment analysis
- Validation and data-quality failures
- A reusable aggregation engine
- Exporting analytical results to CSV
- Performance considerations
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable, Iterable, Sequence
import csv
import json
import math
import tempfile


# ---------------------------------------------------------------------------
# Business transaction model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sale:
    sale_id: int
    sale_date: date
    region: str
    channel: str
    category: str
    product: str
    customer_segment: str
    units: int
    revenue: Decimal
    cost: Decimal
    discount: Decimal

    @property
    def gross_profit(self) -> Decimal:
        return self.revenue - self.cost

    @property
    def margin_rate(self) -> Decimal:
        if self.revenue == 0:
            return Decimal("0")
        return self.gross_profit / self.revenue


def money(value: str | int | float | Decimal) -> Decimal:
    """Convert monetary input to Decimal to avoid binary floating-point errors."""
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc


def percentage(value: Decimal) -> str:
    return f"{value * Decimal('100'):.2f}%"


SALES: list[Sale] = [
    Sale(1001, date(2026, 1, 5), "North", "Online", "Electronics", "Laptop",
         "Enterprise", 4, money("4800"), money("3600"), money("0.05")),
    Sale(1002, date(2026, 1, 8), "North", "Retail", "Office", "Monitor",
         "SMB", 10, money("3000"), money("2100"), money("0.00")),
    Sale(1003, date(2026, 1, 12), "South", "Online", "Electronics", "Phone",
         "Consumer", 15, money("9000"), money("6300"), money("0.10")),
    Sale(1004, date(2026, 1, 15), "West", "Partner", "Software", "Analytics",
         "Enterprise", 3, money("7500"), money("2250"), money("0.15")),
    Sale(1005, date(2026, 1, 20), "East", "Retail", "Office", "Chair",
         "SMB", 20, money("4000"), money("2600"), money("0.05")),
    Sale(1006, date(2026, 2, 2), "North", "Online", "Software", "CRM",
         "Enterprise", 5, money("10000"), money("3000"), money("0.08")),
    Sale(1007, date(2026, 2, 5), "South", "Retail", "Electronics", "Laptop",
         "Consumer", 3, money("3600"), money("2700"), money("0.03")),
    Sale(1008, date(2026, 2, 11), "West", "Online", "Office", "Desk",
         "SMB", 12, money("4800"), money("3000"), money("0.00")),
    Sale(1009, date(2026, 2, 17), "East", "Partner", "Software", "Analytics",
         "Enterprise", 4, money("10000"), money("3000"), money("0.12")),
    Sale(1010, date(2026, 2, 22), "North", "Retail", "Electronics", "Phone",
         "Consumer", 8, money("4800"), money("3360"), money("0.07")),
    Sale(1011, date(2026, 3, 3), "South", "Online", "Software", "CRM",
         "SMB", 7, money("8400"), money("2800"), money("0.05")),
    Sale(1012, date(2026, 3, 7), "West", "Partner", "Electronics", "Laptop",
         "Enterprise", 6, money("7200"), money("5400"), money("0.10")),
    Sale(1013, date(2026, 3, 10), "East", "Retail", "Office", "Monitor",
         "Consumer", 14, money("4200"), money("2940"), money("0.04")),
    Sale(1014, date(2026, 3, 18), "North", "Online", "Software", "Analytics",
         "Enterprise", 2, money("5000"), money("1500"), money("0.20")),
    Sale(1015, date(2026, 3, 24), "South", "Partner", "Office", "Chair",
         "SMB", 25, money("5000"), money("3250"), money("0.06")),
]


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------

def validate_sales(records: Sequence[Sale]) -> None:
    """Validate invariants that should hold before business aggregation."""
    seen_ids: set[int] = set()

    for sale in records:
        if sale.sale_id in seen_ids:
            raise ValueError(f"Duplicate sale_id: {sale.sale_id}")
        seen_ids.add(sale.sale_id)

        if sale.units <= 0:
            raise ValueError(f"Sale {sale.sale_id}: units must be positive")

        if sale.revenue < 0 or sale.cost < 0:
            raise ValueError(f"Sale {sale.sale_id}: monetary values cannot be negative")

        if sale.cost > sale.revenue:
            raise ValueError(
                f"Sale {sale.sale_id}: cost cannot exceed revenue in this model"
            )

        if not Decimal("0") <= sale.discount <= Decimal("1"):
            raise ValueError(f"Sale {sale.sale_id}: discount must be between 0 and 1")

        if not sale.region.strip():
            raise ValueError(f"Sale {sale.sale_id}: region is required")

        if not sale.category.strip():
            raise ValueError(f"Sale {sale.sale_id}: category is required")


# ---------------------------------------------------------------------------
# Fundamental GROUP BY behavior
# ---------------------------------------------------------------------------

def group_by(
    records: Iterable[Sale],
    key_function: Callable[[Sale], Any],
) -> dict[Any, list[Sale]]:
    """
    Equivalent in spirit to:

        GROUP BY <key>

    Every input record is assigned to a bucket identified by key_function.
    """
    groups: dict[Any, list[Sale]] = defaultdict(list)

    for record in records:
        groups[key_function(record)].append(record)

    return dict(groups)


def aggregate_group(records: Sequence[Sale]) -> dict[str, Any]:
    """Calculate common business aggregates for one group."""
    revenues = [sale.revenue for sale in records]
    profits = [sale.gross_profit for sale in records]
    units = [sale.units for sale in records]

    total_revenue = sum(revenues, Decimal("0"))
    total_profit = sum(profits, Decimal("0"))

    return {
        "transaction_count": len(records),
        "units": sum(units),
        "revenue": total_revenue,
        "average_order_value": (
            total_revenue / len(records) if records else Decimal("0")
        ),
        "minimum_revenue": min(revenues) if revenues else Decimal("0"),
        "maximum_revenue": max(revenues) if revenues else Decimal("0"),
        "profit": total_profit,
        "margin_rate": (
            total_profit / total_revenue if total_revenue else Decimal("0")
        ),
    }


def print_table(rows: Sequence[dict[str, Any]], title: str) -> None:
    """Print compact analytical output without external dependencies."""
    print(f"\n=== {title} ===")

    if not rows:
        print("(no rows)")
        return

    columns = list(rows[0].keys())
    widths = {
        column: max(
            len(str(column)),
            *(len(str(row.get(column, ""))) for row in rows),
        )
        for column in columns
    }

    header = " | ".join(str(column).ljust(widths[column]) for column in columns)
    divider = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(divider)

    for row in rows:
        print(
            " | ".join(
                str(row.get(column, "")).ljust(widths[column])
                for column in columns
            )
        )


def money_text(value: Decimal) -> str:
    return f"{value:,.2f}"


def group_sales_by_region(records: Sequence[Sale]) -> list[dict[str, Any]]:
    """Equivalent to GROUP BY region with SUM/COUNT/AVG-style aggregates."""
    groups = group_by(records, lambda sale: sale.region)
    rows = []

    for region, sales in sorted(groups.items()):
        aggregate = aggregate_group(sales)
        rows.append(
            {
                "region": region,
                "transactions": aggregate["transaction_count"],
                "units": aggregate["units"],
                "revenue": money_text(aggregate["revenue"]),
                "avg_order": money_text(aggregate["average_order_value"]),
                "profit": money_text(aggregate["profit"]),
                "margin": percentage(aggregate["margin_rate"]),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Multi-column grouping
# ---------------------------------------------------------------------------

def group_sales_by_region_channel(
    records: Sequence[Sale],
) -> list[dict[str, Any]]:
    """
    Equivalent to:

        GROUP BY region, channel

    A tuple is used because a business segment can be defined by multiple
    dimensions simultaneously.
    """
    groups = group_by(records, lambda sale: (sale.region, sale.channel))
    rows = []

    for (region, channel), sales in sorted(groups.items()):
        aggregate = aggregate_group(sales)
        rows.append(
            {
                "region": region,
                "channel": channel,
                "transactions": aggregate["transaction_count"],
                "revenue": money_text(aggregate["revenue"]),
                "profit": money_text(aggregate["profit"]),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Conditional aggregation
# ---------------------------------------------------------------------------

def conditional_region_metrics(records: Sequence[Sale]) -> list[dict[str, Any]]:
    """
    Demonstrates SQL-style conditional aggregation.

    Conceptually:

        SUM(CASE WHEN channel = 'Online' THEN revenue ELSE 0 END)
        COUNT(CASE WHEN category = 'Software' THEN 1 END)

    The conditions are evaluated inside each region's aggregate bucket.
    """
    groups = group_by(records, lambda sale: sale.region)
    rows = []

    for region, sales in sorted(groups.items()):
        online_revenue = sum(
            (sale.revenue for sale in sales if sale.channel == "Online"),
            Decimal("0"),
        )
        software_revenue = sum(
            (sale.revenue for sale in sales if sale.category == "Software"),
            Decimal("0"),
        )
        enterprise_transactions = sum(
            1 for sale in sales if sale.customer_segment == "Enterprise"
        )

        rows.append(
            {
                "region": region,
                "total_revenue": money_text(
                    sum((s.revenue for s in sales), Decimal("0"))
                ),
                "online_revenue": money_text(online_revenue),
                "software_revenue": money_text(software_revenue),
                "enterprise_txns": enterprise_transactions,
            }
        )

    return rows


# ---------------------------------------------------------------------------
# HAVING-style filtering
# ---------------------------------------------------------------------------

def high_value_regions(
    records: Sequence[Sale],
    minimum_revenue: Decimal,
) -> list[dict[str, Any]]:
    """
    WHERE filters individual rows before grouping.
    HAVING filters groups after aggregation.

    This function intentionally aggregates first and then applies the
    group-level threshold.
    """
    groups = group_by(records, lambda sale: sale.region)
    rows = []

    for region, sales in sorted(groups.items()):
        total_revenue = sum((s.revenue for s in sales), Decimal("0"))

        if total_revenue >= minimum_revenue:
            rows.append(
                {
                    "region": region,
                    "revenue": money_text(total_revenue),
                    "transactions": len(sales),
                }
            )

    return rows


# ---------------------------------------------------------------------------
# Time-based business segmentation
# ---------------------------------------------------------------------------

def quarter_for(month: int) -> str:
    quarter = ((month - 1) // 3) + 1
    return f"Q{quarter}"


def monthly_region_summary(records: Sequence[Sale]) -> list[dict[str, Any]]:
    """Segment revenue by calendar month and region."""
    groups = group_by(
        records,
        lambda sale: (sale.sale_date.year, sale.sale_date.month, sale.region),
    )

    rows = []

    for (year, month, region), sales in sorted(groups.items()):
        revenue = sum((s.revenue for s in sales), Decimal("0"))
        profit = sum((s.gross_profit for s in sales), Decimal("0"))

        rows.append(
            {
                "period": f"{year}-{month:02d}",
                "region": region,
                "transactions": len(sales),
                "revenue": money_text(revenue),
                "profit": money_text(profit),
            }
        )

    return rows


def quarterly_category_summary(records: Sequence[Sale]) -> list[dict[str, Any]]:
    """Segment category performance by financial quarter."""
    groups = group_by(
        records,
        lambda sale: (sale.sale_date.year, quarter_for(sale.sale_date.month), sale.category),
    )

    rows = []

    for (year, quarter, category), sales in sorted(groups.items()):
        revenue = sum((s.revenue for s in sales), Decimal("0"))
        profit = sum((s.gross_profit for s in sales), Decimal("0"))

        rows.append(
            {
                "period": f"{year} {quarter}",
                "category": category,
                "transactions": len(sales),
                "revenue": money_text(revenue),
                "profit": money_text(profit),
                "margin": percentage(
                    profit / revenue if revenue else Decimal("0")
                ),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Top-N analysis
# ---------------------------------------------------------------------------

def top_categories_by_profit(
    records: Sequence[Sale],
    limit: int = 3,
) -> list[dict[str, Any]]:
    groups = group_by(records, lambda sale: sale.category)

    rows = []
    for category, sales in groups.items():
        profit = sum((s.gross_profit for s in sales), Decimal("0"))
        revenue = sum((s.revenue for s in sales), Decimal("0"))

        rows.append(
            {
                "category": category,
                "revenue": money_text(revenue),
                "profit": money_text(profit),
                "margin": percentage(
                    profit / revenue if revenue else Decimal("0")
                ),
            }
        )

    return sorted(
        rows,
        key=lambda row: Decimal(row["profit"].replace(",", "")),
        reverse=True,
    )[:limit]


# ---------------------------------------------------------------------------
# Distinct counts and customer segmentation
# ---------------------------------------------------------------------------

def customer_segment_analysis(
    records: Sequence[Sale],
) -> list[dict[str, Any]]:
    """
    Segment by customer type and derive revenue share.

    A separate set is maintained for each group when a distinct count is
    needed. In this simplified dataset product names stand in for distinct
    products purchased by the segment.
    """
    groups = group_by(records, lambda sale: sale.customer_segment)
    total_revenue = sum((s.revenue for s in records), Decimal("0"))
    rows = []

    for segment, sales in sorted(groups.items()):
        revenue = sum((s.revenue for s in sales), Decimal("0"))
        products = {s.product for s in sales}

        rows.append(
            {
                "customer_segment": segment,
                "transactions": len(sales),
                "distinct_products": len(products),
                "revenue": money_text(revenue),
                "revenue_share": percentage(
                    revenue / total_revenue if total_revenue else Decimal("0")
                ),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Reusable aggregation engine
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AggregateSpec:
    name: str
    function: Callable[[Sequence[Sale]], Any]


def sum_revenue(rows: Sequence[Sale]) -> Decimal:
    return sum((row.revenue for row in rows), Decimal("0"))


def sum_profit(rows: Sequence[Sale]) -> Decimal:
    return sum((row.gross_profit for row in rows), Decimal("0"))


def average_discount(rows: Sequence[Sale]) -> Decimal:
    if not rows:
        return Decimal("0")
    return sum((row.discount for row in rows), Decimal("0")) / len(rows)


def count_enterprise(rows: Sequence[Sale]) -> int:
    return sum(1 for row in rows if row.customer_segment == "Enterprise")


def run_grouped_aggregation(
    records: Sequence[Sale],
    dimensions: Sequence[Callable[[Sale], Any]],
    dimension_names: Sequence[str],
    specifications: Sequence[AggregateSpec],
) -> list[dict[str, Any]]:
    """
    Generic grouping engine.

    The grouping key is a tuple, making the implementation naturally support
    one-dimensional and multi-dimensional business segmentation.
    """
    if len(dimensions) != len(dimension_names):
        raise ValueError("Dimension functions and names must have equal lengths")

    grouped: dict[tuple[Any, ...], list[Sale]] = defaultdict(list)

    for record in records:
        key = tuple(function(record) for function in dimensions)
        grouped[key].append(record)

    result = []

    for key, rows in sorted(grouped.items(), key=lambda item: item[0]):
        output = dict(zip(dimension_names, key))

        for specification in specifications:
            output[specification.name] = specification.function(rows)

        result.append(output)

    return result


def format_generic_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Decimal values for readable terminal output."""
    formatted = []

    for row in rows:
        converted = {}
        for key, value in row.items():
            converted[key] = (
                money_text(value) if isinstance(value, Decimal) else value
            )
        formatted.append(converted)

    return formatted


# ---------------------------------------------------------------------------
# Missing-value grouping
# ---------------------------------------------------------------------------

def normalize_dimension(value: str | None) -> str:
    """
    SQL NULL is not the same as an empty string.

    This example explicitly maps missing region data to a business label so
    that incomplete records remain visible in an analytical report instead of
    silently disappearing.
    """
    if value is None or not value.strip():
        return "Unknown"
    return value.strip()


@dataclass(frozen=True)
class OptionalSale:
    sale_id: int
    region: str | None
    revenue: Decimal


def group_optional_regions(records: Sequence[OptionalSale]) -> list[dict[str, Any]]:
    groups: dict[str, list[OptionalSale]] = defaultdict(list)

    for record in records:
        groups[normalize_dimension(record.region)].append(record)

    return [
        {
            "region": region,
            "transactions": len(rows),
            "revenue": money_text(sum((r.revenue for r in rows), Decimal("0"))),
        }
        for region, rows in sorted(groups.items())
    ]


# ---------------------------------------------------------------------------
# Outlier and statistical analysis
# ---------------------------------------------------------------------------

def region_revenue_statistics(
    records: Sequence[Sale],
) -> list[dict[str, Any]]:
    """Use transaction-level revenue statistics within each region."""
    groups = group_by(records, lambda sale: sale.region)
    rows = []

    for region, sales in sorted(groups.items()):
        revenues = [float(s.revenue) for s in sales]

        rows.append(
            {
                "region": region,
                "mean_order": f"{mean(revenues):,.2f}",
                "median_order": f"{median(revenues):,.2f}",
                "min_order": f"{min(revenues):,.2f}",
                "max_order": f"{max(revenues):,.2f}",
            }
        )

    return rows


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_region_report(
    records: Sequence[Sale],
    output_path: Path,
) -> None:
    """Persist an aggregate report for downstream business analysis."""
    rows = group_sales_by_region(records)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# JSON serialization of source data
# ---------------------------------------------------------------------------

def export_source_snapshot(
    records: Sequence[Sale],
    output_path: Path,
) -> None:
    payload = []

    for record in records:
        item = asdict(record)
        item["sale_date"] = record.sale_date.isoformat()
        item["revenue"] = str(record.revenue)
        item["cost"] = str(record.cost)
        item["discount"] = str(record.discount)
        payload.append(item)

    output_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Demonstration and test-like checks
# ---------------------------------------------------------------------------

def demonstrate_validation() -> None:
    invalid = Sale(
        9999,
        date(2026, 4, 1),
        "North",
        "Online",
        "Software",
        "CRM",
        "Enterprise",
        1,
        money("100"),
        money("125"),
        money("0.05"),
    )

    try:
        validate_sales([invalid])
    except ValueError as exc:
        print("\n=== Validation Failure ===")
        print(exc)


def demonstrate_empty_group_behavior() -> None:
    print("\n=== Empty Input Behavior ===")
    print(group_sales_by_region([]))


def demonstrate_generic_engine(records: Sequence[Sale]) -> None:
    specifications = [
        AggregateSpec("revenue", sum_revenue),
        AggregateSpec("profit", sum_profit),
        AggregateSpec("avg_discount", average_discount),
        AggregateSpec("enterprise_transactions", count_enterprise),
    ]

    rows = run_grouped_aggregation(
        records,
        dimensions=[
            lambda sale: sale.region,
            lambda sale: sale.category,
        ],
        dimension_names=["region", "category"],
        specifications=specifications,
    )

    print_table(format_generic_rows(rows), "Generic Region + Category Aggregation")


def demonstrate_performance_characteristics(records: Sequence[Sale]) -> None:
    """
    A hash-based grouping pass is approximately O(n) expected time for n
    records, excluding the cost of sorting the resulting groups.

    Sorting g groups adds approximately O(g log g). Memory is O(n) in the
    worst case because records are retained inside their buckets.
    """
    groups = group_by(records, lambda sale: sale.region)

    print("\n=== Performance Characteristics ===")
    print(f"Input records: {len(records)}")
    print(f"Groups created: {len(groups)}")
    print("Hash grouping: approximately O(n) expected time")
    print("Group sorting when requested: O(g log g)")
    print("Bucket storage: O(n) additional memory in this implementation")


def demonstrate_business_rules(records: Sequence[Sale]) -> None:
    """
    A margin percentage must be calculated from aggregated revenue and
    aggregated profit when reporting group-level profitability.

    Averaging transaction-level margin percentages can produce a misleading
    result because transactions may have very different revenue values.
    """
    groups = group_by(records, lambda sale: sale.category)
    rows = []

    for category, sales in sorted(groups.items()):
        total_revenue = sum((s.revenue for s in sales), Decimal("0"))
        total_profit = sum((s.gross_profit for s in sales), Decimal("0"))

        weighted_margin = (
            total_profit / total_revenue
            if total_revenue
            else Decimal("0")
        )

        unweighted_average_margin = (
            sum((s.margin_rate for s in sales), Decimal("0")) / len(sales)
            if sales
            else Decimal("0")
        )

        rows.append(
            {
                "category": category,
                "weighted_margin": percentage(weighted_margin),
                "avg_transaction_margin": percentage(unweighted_average_margin),
            }
        )

    print_table(rows, "Weighted vs Unweighted Margin")


def main() -> None:
    validate_sales(SALES)

    print("GROUP BY: Segmenting and Aggregating Business Data")
    print(f"Validated {len(SALES)} sales transactions.")

    print_table(
        group_sales_by_region(SALES),
        "Revenue by Region",
    )

    print_table(
        group_sales_by_region_channel(SALES),
        "Revenue by Region and Channel",
    )

    print_table(
        conditional_region_metrics(SALES),
        "Conditional Aggregation by Region",
    )

    print_table(
        high_value_regions(SALES, money("15000")),
        "Regions Passing the HAVING Revenue Threshold",
    )

    print_table(
        monthly_region_summary(SALES),
        "Monthly Revenue by Region",
    )

    print_table(
        quarterly_category_summary(SALES),
        "Quarterly Category Performance",
    )

    print_table(
        top_categories_by_profit(SALES),
        "Top Categories by Profit",
    )

    print_table(
        customer_segment_analysis(SALES),
        "Customer Segment Analysis",
    )

    print_table(
        region_revenue_statistics(SALES),
        "Regional Order Statistics",
    )

    demonstrate_generic_engine(SALES)
    demonstrate_business_rules(SALES)
    demonstrate_validation()
    demonstrate_empty_group_behavior()

    optional_records = [
        OptionalSale(2001, "North", money("500")),
        OptionalSale(2002, None, money("300")),
        OptionalSale(2003, "", money("200")),
        OptionalSale(2004, "South", money("700")),
    ]

    print_table(
        group_optional_regions(optional_records),
        "Explicit Handling of Missing Regions",
    )

    with tempfile.TemporaryDirectory() as directory:
        directory_path = Path(directory)
        csv_path = directory_path / "region_report.csv"
        json_path = directory_path / "sales_snapshot.json"

        export_region_report(SALES, csv_path)
        export_source_snapshot(SALES, json_path)

        print("\n=== File Export ===")
        print(f"CSV report created: {csv_path.name}")
        print(f"JSON source snapshot created: {json_path.name}")

    demonstrate_performance_characteristics(SALES)

    print("\n=== Completed ===")


if __name__ == "__main__":
    main()
