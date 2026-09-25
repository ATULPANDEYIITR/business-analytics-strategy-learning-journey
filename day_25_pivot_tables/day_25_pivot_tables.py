"""
Pivot Tables: Aggregating and Analyzing Business Data

A self-contained study program covering pivot-table concepts from beginner
through advanced level using only the Python standard library.

The program demonstrates:
- Dimensions, measures, categories, aggregation
- SUM, COUNT, AVERAGE, MIN, MAX, DISTINCT COUNT
- Grouping and multi-dimensional aggregation
- Row and column dimensions
- Filtering
- Sorting
- Percentages and calculated metrics
- Missing values and invalid records
- Hierarchical dimensions
- Time-based grouping
- Drill-down
- Margins and grand totals
- Conditional aggregation
- Ranking
- Pareto-style analysis
- Cohort-style analysis
- Pivoting and unpivoting concepts
- Performance considerations
- Validation and testing
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any, Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# 1. SAMPLE BUSINESS DATA
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sale:
    order_id: str
    order_date: date
    region: str
    country: str
    category: str
    product: str
    salesperson: str
    channel: str
    units: int
    unit_price: float
    discount: float
    cost_per_unit: float

    @property
    def gross_sales(self) -> float:
        return self.units * self.unit_price

    @property
    def discount_amount(self) -> float:
        return self.gross_sales * self.discount

    @property
    def net_sales(self) -> float:
        return self.gross_sales - self.discount_amount

    @property
    def total_cost(self) -> float:
        return self.units * self.cost_per_unit

    @property
    def profit(self) -> float:
        return self.net_sales - self.total_cost

    @property
    def margin_percent(self) -> float:
        if self.net_sales == 0:
            return 0.0
        return self.profit / self.net_sales * 100


DATA = [
    Sale("O1001", date(2026, 1, 5), "North", "India", "Electronics", "Laptop", "Asha", "Online", 5, 900, 0.05, 650),
    Sale("O1002", date(2026, 1, 8), "North", "India", "Electronics", "Monitor", "Ravi", "Retail", 8, 300, 0.02, 210),
    Sale("O1003", date(2026, 1, 15), "South", "India", "Furniture", "Desk", "Meera", "Online", 4, 450, 0.10, 300),
    Sale("O1004", date(2026, 1, 21), "West", "India", "Office", "Chair", "Arjun", "Retail", 12, 180, 0.05, 110),
    Sale("O1005", date(2026, 2, 2), "East", "India", "Electronics", "Laptop", "Asha", "Online", 3, 950, 0.00, 680),
    Sale("O1006", date(2026, 2, 6), "North", "India", "Furniture", "Desk", "Ravi", "Online", 7, 425, 0.08, 295),
    Sale("O1007", date(2026, 2, 13), "South", "India", "Office", "Chair", "Meera", "Retail", 15, 175, 0.03, 108),
    Sale("O1008", date(2026, 2, 20), "West", "India", "Electronics", "Monitor", "Arjun", "Online", 10, 290, 0.04, 205),
    Sale("O1009", date(2026, 3, 3), "East", "India", "Furniture", "Desk", "Asha", "Retail", 6, 470, 0.06, 310),
    Sale("O1010", date(2026, 3, 9), "North", "India", "Office", "Chair", "Ravi", "Online", 20, 165, 0.02, 105),
    Sale("O1011", date(2026, 3, 18), "South", "India", "Electronics", "Laptop", "Meera", "Retail", 4, 920, 0.07, 655),
    Sale("O1012", date(2026, 3, 25), "West", "India", "Furniture", "Desk", "Arjun", "Online", 5, 460, 0.05, 305),
]


# ---------------------------------------------------------------------------
# 2. BASIC AGGREGATION
# ---------------------------------------------------------------------------

def money(value: float) -> str:
    return f"{value:,.2f}"


def sum_values(records: Iterable[Sale], value_getter: Callable[[Sale], float]) -> float:
    return sum(value_getter(record) for record in records)


def count_records(records: Iterable[Sale]) -> int:
    return sum(1 for _ in records)


def average_values(records: Iterable[Sale], value_getter: Callable[[Sale], float]) -> float:
    values = [value_getter(record) for record in records]
    return sum(values) / len(values) if values else 0.0


def minimum_value(records: Iterable[Sale], value_getter: Callable[[Sale], float]) -> float:
    values = [value_getter(record) for record in records]
    return min(values) if values else 0.0


def maximum_value(records: Iterable[Sale], value_getter: Callable[[Sale], float]) -> float:
    values = [value_getter(record) for record in records]
    return max(values) if values else 0.0


def distinct_count(records: Iterable[Sale], value_getter: Callable[[Sale], Any]) -> int:
    return len({value_getter(record) for record in records})


def demonstrate_basic_aggregation(records: Sequence[Sale]) -> None:
    print("\n=== BASIC AGGREGATION ===")
    print("Total orders:", count_records(records))
    print("Total units:", sum_values(records, lambda r: r.units))
    print("Net sales:", money(sum_values(records, lambda r: r.net_sales)))
    print("Average order value:", money(average_values(records, lambda r: r.net_sales)))
    print("Highest order:", money(maximum_value(records, lambda r: r.net_sales)))
    print("Lowest order:", money(minimum_value(records, lambda r: r.net_sales)))
    print("Distinct products:", distinct_count(records, lambda r: r.product))
    print("Distinct salespeople:", distinct_count(records, lambda r: r.salesperson))


# ---------------------------------------------------------------------------
# 3. GENERIC PIVOT ENGINE
# ---------------------------------------------------------------------------

def normalize_key(value: Any) -> str:
    return "(Blank)" if value is None or value == "" else str(value)


def pivot(
    records: Iterable[Sale],
    row_field: Callable[[Sale], Any],
    value_field: Callable[[Sale], float],
    aggregator: Callable[[list[float]], float],
) -> dict[str, float]:
    """
    A simple one-dimensional pivot.

    Conceptually:
        ROW DIMENSION -> groups records
        VALUE         -> numeric field
        AGGREGATOR    -> SUM, AVG, MIN, MAX, etc.
    """
    groups: dict[str, list[float]] = defaultdict(list)

    for record in records:
        groups[normalize_key(row_field(record))].append(value_field(record))

    return {
        key: aggregator(values)
        for key, values in sorted(groups.items())
    }


def pivot_sum(records, row_field, value_field):
    return pivot(records, row_field, value_field, sum)


def pivot_average(records, row_field, value_field):
    return pivot(records, row_field, value_field, lambda values: sum(values) / len(values))


def pivot_count(records, row_field):
    return pivot(records, row_field, lambda _: 1.0, sum)


def pivot_min(records, row_field, value_field):
    return pivot(records, row_field, value_field, min)


def pivot_max(records, row_field, value_field):
    return pivot(records, row_field, value_field, max)


def demonstrate_single_dimension_pivots(records: Sequence[Sale]) -> None:
    print("\n=== SINGLE-DIMENSION PIVOTS ===")

    regional_sales = pivot_sum(records, lambda r: r.region, lambda r: r.net_sales)
    print("\nSales by region:")
    for region, value in regional_sales.items():
        print(f"  {region:8} {money(value)}")

    category_profit = pivot_sum(records, lambda r: r.category, lambda r: r.profit)
    print("\nProfit by category:")
    for category, value in category_profit.items():
        print(f"  {category:12} {money(value)}")

    order_count = pivot_count(records, lambda r: r.salesperson)
    print("\nOrders by salesperson:")
    for person, value in order_count.items():
        print(f"  {person:8} {int(value)}")

    average_order = pivot_average(records, lambda r: r.channel, lambda r: r.net_sales)
    print("\nAverage order value by channel:")
    for channel, value in average_order.items():
        print(f"  {channel:8} {money(value)}")


# ---------------------------------------------------------------------------
# 4. TWO-DIMENSIONAL PIVOT
# ---------------------------------------------------------------------------

def pivot_2d(
    records: Iterable[Sale],
    row_field: Callable[[Sale], Any],
    column_field: Callable[[Sale], Any],
    value_field: Callable[[Sale], float],
    aggregator: Callable[[list[float]], float] = sum,
) -> tuple[list[str], list[str], dict[tuple[str, str], float]]:
    rows: set[str] = set()
    columns: set[str] = set()
    cells: dict[tuple[str, str], list[float]] = defaultdict(list)

    for record in records:
        row = normalize_key(row_field(record))
        column = normalize_key(column_field(record))
        rows.add(row)
        columns.add(column)
        cells[(row, column)].append(value_field(record))

    final_cells = {
        key: aggregator(values)
        for key, values in cells.items()
    }

    return sorted(rows), sorted(columns), final_cells


def print_pivot_table(
    rows: list[str],
    columns: list[str],
    cells: dict[tuple[str, str], float],
    title: str,
    integer_values: bool = False,
) -> None:
    print(f"\n{title}")

    widths = {column: max(12, len(column) + 2) for column in columns}
    row_width = max(12, max((len(row) for row in rows), default=4) + 2)

    header = " " * row_width + "".join(
        f"{column:>{widths[column]}}" for column in columns
    )
    print(header)

    for row in rows:
        values = []
        for column in columns:
            value = cells.get((row, column), 0.0)
            formatted = f"{value:.0f}" if integer_values else f"{value:,.2f}"
            values.append(f"{formatted:>{widths[column]}}")
        print(f"{row:<{row_width}}" + "".join(values))


def demonstrate_two_dimensional_pivot(records: Sequence[Sale]) -> None:
    rows, columns, cells = pivot_2d(
        records,
        lambda r: r.region,
        lambda r: r.category,
        lambda r: r.net_sales,
    )
    print_pivot_table(rows, columns, cells, "Net sales: Region x Category")


# ---------------------------------------------------------------------------
# 5. THREE-DIMENSIONAL / HIERARCHICAL GROUPING
# ---------------------------------------------------------------------------

def group_by_dimensions(
    records: Iterable[Sale],
    dimensions: Sequence[Callable[[Sale], Any]],
    value_field: Callable[[Sale], float],
) -> dict[tuple[str, ...], float]:
    result: dict[tuple[str, ...], float] = defaultdict(float)

    for record in records:
        key = tuple(normalize_key(dimension(record)) for dimension in dimensions)
        result[key] += value_field(record)

    return dict(sorted(result.items()))


def demonstrate_hierarchical_pivot(records: Sequence[Sale]) -> None:
    print("\n=== HIERARCHICAL PIVOT ===")

    grouped = group_by_dimensions(
        records,
        [
            lambda r: r.region,
            lambda r: r.category,
            lambda r: r.product,
        ],
        lambda r: r.net_sales,
    )

    for (region, category, product), sales in grouped.items():
        print(f"{region:8} | {category:12} | {product:10} | {money(sales)}")


# ---------------------------------------------------------------------------
# 6. FILTERING
# ---------------------------------------------------------------------------

def filter_records(
    records: Iterable[Sale],
    predicate: Callable[[Sale], bool],
) -> list[Sale]:
    return [record for record in records if predicate(record)]


def demonstrate_filtering(records: Sequence[Sale]) -> None:
    print("\n=== FILTERED PIVOTS ===")

    north = filter_records(records, lambda r: r.region == "North")
    north_sales = pivot_sum(north, lambda r: r.category, lambda r: r.net_sales)

    print("North region sales by category:")
    for category, value in north_sales.items():
        print(f"  {category:12} {money(value)}")

    online = filter_records(records, lambda r: r.channel == "Online")
    online_profit = sum_values(online, lambda r: r.profit)
    print("Online-channel profit:", money(online_profit))


# ---------------------------------------------------------------------------
# 7. PERCENTAGE OF TOTAL
# ---------------------------------------------------------------------------

def percentage_of_total(pivot_values: dict[str, float]) -> dict[str, float]:
    total = sum(pivot_values.values())
    if total == 0:
        return {key: 0.0 for key in pivot_values}

    return {
        key: value / total * 100
        for key, value in pivot_values.items()
    }


def demonstrate_percentages(records: Sequence[Sale]) -> None:
    print("\n=== PERCENTAGE OF TOTAL ===")

    sales = pivot_sum(records, lambda r: r.category, lambda r: r.net_sales)
    percentages = percentage_of_total(sales)

    for category in sales:
        print(
            f"{category:12} "
            f"sales={money(sales[category]):>12} "
            f"share={percentages[category]:6.2f}%"
        )


# ---------------------------------------------------------------------------
# 8. GRAND TOTALS AND MARGINS
# ---------------------------------------------------------------------------

def add_grand_total(
    values: dict[str, float],
    label: str = "Grand Total",
) -> dict[str, float]:
    result = dict(values)
    result[label] = sum(values.values())
    return result


def demonstrate_totals(records: Sequence[Sale]) -> None:
    print("\n=== GRAND TOTAL ===")

    values = pivot_sum(records, lambda r: r.region, lambda r: r.net_sales)
    values = add_grand_total(values)

    for region, sales in values.items():
        print(f"{region:12} {money(sales)}")


# ---------------------------------------------------------------------------
# 9. CALCULATED FIELDS
# ---------------------------------------------------------------------------

def calculate_sales_metrics(records: Sequence[Sale]) -> list[dict[str, Any]]:
    result = []

    for record in records:
        result.append(
            {
                "order_id": record.order_id,
                "region": record.region,
                "category": record.category,
                "net_sales": record.net_sales,
                "profit": record.profit,
                "margin_percent": record.margin_percent,
                "units": record.units,
                "revenue_per_unit": record.net_sales / record.units if record.units else 0,
            }
        )

    return result


def demonstrate_calculated_fields(records: Sequence[Sale]) -> None:
    print("\n=== CALCULATED FIELDS ===")

    metrics = calculate_sales_metrics(records)

    for row in metrics[:5]:
        print(
            f"{row['order_id']} "
            f"sales={money(row['net_sales'])} "
            f"profit={money(row['profit'])} "
            f"margin={row['margin_percent']:.2f}%"
        )


# ---------------------------------------------------------------------------
# 10. TIME-BASED PIVOTS
# ---------------------------------------------------------------------------

def month_key(record: Sale) -> str:
    return record.order_date.strftime("%Y-%m")


def quarter_key(record: Sale) -> str:
    quarter = (record.order_date.month - 1) // 3 + 1
    return f"{record.order_date.year}-Q{quarter}"


def demonstrate_time_pivots(records: Sequence[Sale]) -> None:
    print("\n=== TIME-BASED PIVOTS ===")

    monthly = pivot_sum(records, month_key, lambda r: r.net_sales)
    quarterly = pivot_sum(records, quarter_key, lambda r: r.net_sales)

    print("Monthly sales:")
    for month, sales in monthly.items():
        print(f"  {month}: {money(sales)}")

    print("Quarterly sales:")
    for quarter, sales in quarterly.items():
        print(f"  {quarter}: {money(sales)}")


# ---------------------------------------------------------------------------
# 11. RANKING
# ---------------------------------------------------------------------------

def rank_pivot(values: dict[str, float], descending: bool = True) -> list[tuple[int, str, float]]:
    ordered = sorted(
        values.items(),
        key=lambda item: item[1],
        reverse=descending,
    )

    return [
        (rank, key, value)
        for rank, (key, value) in enumerate(ordered, start=1)
    ]


def demonstrate_ranking(records: Sequence[Sale]) -> None:
    print("\n=== RANKING ===")

    product_sales = pivot_sum(records, lambda r: r.product, lambda r: r.net_sales)

    for rank, product, sales in rank_pivot(product_sales):
        print(f"{rank}. {product:10} {money(sales)}")


# ---------------------------------------------------------------------------
# 12. CONDITIONAL AGGREGATION
# ---------------------------------------------------------------------------

def conditional_sum(
    records: Iterable[Sale],
    condition: Callable[[Sale], bool],
    value_field: Callable[[Sale], float],
) -> float:
    return sum(
        value_field(record)
        for record in records
        if condition(record)
    )


def demonstrate_conditional_aggregation(records: Sequence[Sale]) -> None:
    print("\n=== CONDITIONAL AGGREGATION ===")

    high_value_online = conditional_sum(
        records,
        lambda r: r.channel == "Online" and r.net_sales >= 1000,
        lambda r: r.net_sales,
    )

    profitable_orders = conditional_sum(
        records,
        lambda r: r.profit > 500,
        lambda r: r.profit,
    )

    print("High-value online sales:", money(high_value_online))
    print("Profit from orders above $500 profit:", money(profitable_orders))


# ---------------------------------------------------------------------------
# 13. PARETO ANALYSIS
# ---------------------------------------------------------------------------

def pareto_analysis(records: Sequence[Sale]) -> list[dict[str, Any]]:
    product_sales = pivot_sum(
        records,
        lambda r: r.product,
        lambda r: r.net_sales,
    )

    ordered = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
    total = sum(value for _, value in ordered)

    cumulative = 0.0
    result = []

    for product, sales in ordered:
        cumulative += sales
        result.append(
            {
                "product": product,
                "sales": sales,
                "share_percent": sales / total * 100 if total else 0,
                "cumulative_percent": cumulative / total * 100 if total else 0,
            }
        )

    return result


def demonstrate_pareto(records: Sequence[Sale]) -> None:
    print("\n=== PARETO-STYLE ANALYSIS ===")

    for row in pareto_analysis(records):
        print(
            f"{row['product']:10} "
            f"share={row['share_percent']:6.2f}% "
            f"cumulative={row['cumulative_percent']:6.2f}%"
        )


# ---------------------------------------------------------------------------
# 14. DRILL-DOWN
# ---------------------------------------------------------------------------

def drill_down(
    records: Sequence[Sale],
    dimension: Callable[[Sale], Any],
    selected_value: Any,
) -> list[Sale]:
    return [
        record
        for record in records
        if dimension(record) == selected_value
    ]


def demonstrate_drill_down(records: Sequence[Sale]) -> None:
    print("\n=== DRILL-DOWN ===")

    region_records = drill_down(records, lambda r: r.region, "North")

    for record in region_records:
        print(
            f"{record.order_id}: "
            f"{record.product}, "
            f"{record.units} units, "
            f"{money(record.net_sales)}"
        )


# ---------------------------------------------------------------------------
# 15. DATA VALIDATION
# ---------------------------------------------------------------------------

def validate_record(record: Sale) -> list[str]:
    errors = []

    if not record.order_id:
        errors.append("Missing order ID.")

    if record.units <= 0:
        errors.append("Units must be positive.")

    if not isfinite(record.unit_price) or record.unit_price < 0:
        errors.append("Unit price must be a finite non-negative number.")

    if not 0 <= record.discount <= 1:
        errors.append("Discount must be between 0 and 1.")

    if not isfinite(record.cost_per_unit) or record.cost_per_unit < 0:
        errors.append("Cost per unit must be non-negative.")

    return errors


def validate_dataset(records: Sequence[Sale]) -> dict[str, list[str]]:
    errors = {}

    for record in records:
        record_errors = validate_record(record)
        if record_errors:
            errors[record.order_id] = record_errors

    order_ids = [record.order_id for record in records]

    if len(order_ids) != len(set(order_ids)):
        errors["DATASET"] = ["Duplicate order IDs detected."]

    return errors


def demonstrate_validation(records: Sequence[Sale]) -> None:
    print("\n=== VALIDATION ===")

    errors = validate_dataset(records)

    if not errors:
        print("Dataset validation passed.")
    else:
        for key, messages in errors.items():
            print(key, messages)


# ---------------------------------------------------------------------------
# 16. UNPIVOT CONCEPT
# ---------------------------------------------------------------------------

def unpivot_region_category(records: Sequence[Sale]) -> list[dict[str, Any]]:
    """
    A pivot converts rows into grouped columns.
    Unpivoting reverses a wide representation into a long representation.

    This function produces a normalized long-form result from the original
    transactional records, making the relationship explicit.
    """
    result = []

    for record in records:
        result.append(
            {
                "region": record.region,
                "category": record.category,
                "metric": "net_sales",
                "value": record.net_sales,
            }
        )
        result.append(
            {
                "region": record.region,
                "category": record.category,
                "metric": "profit",
                "value": record.profit,
            }
        )

    return result


def demonstrate_unpivot(records: Sequence[Sale]) -> None:
    print("\n=== LONG-FORM / UNPIVOT REPRESENTATION ===")

    rows = unpivot_region_category(records)

    for row in rows[:6]:
        print(
            f"{row['region']:8} "
            f"{row['category']:12} "
            f"{row['metric']:10} "
            f"{money(row['value'])}"
        )


# ---------------------------------------------------------------------------
# 17. ADVANCED MULTI-METRIC PIVOT
# ---------------------------------------------------------------------------

def multi_metric_pivot(records: Sequence[Sale]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}

    for category in sorted({record.category for record in records}):
        subset = [r for r in records if r.category == category]

        result[category] = {
            "orders": float(len(subset)),
            "units": sum(r.units for r in subset),
            "sales": sum(r.net_sales for r in subset),
            "profit": sum(r.profit for r in subset),
            "average_order": (
                sum(r.net_sales for r in subset) / len(subset)
                if subset else 0.0
            ),
            "average_margin": (
                sum(r.margin_percent for r in subset) / len(subset)
                if subset else 0.0
            ),
        }

    return result


def demonstrate_multi_metric_pivot(records: Sequence[Sale]) -> None:
    print("\n=== MULTI-METRIC PIVOT ===")

    result = multi_metric_pivot(records)

    for category, metrics in result.items():
        print(
            f"{category:12} "
            f"orders={metrics['orders']:.0f}, "
            f"units={metrics['units']:.0f}, "
            f"sales={money(metrics['sales'])}, "
            f"profit={money(metrics['profit'])}, "
            f"avg_order={money(metrics['average_order'])}, "
            f"avg_margin={metrics['average_margin']:.2f}%"
        )


# ---------------------------------------------------------------------------
# 18. ADVANCED GROUPING WITH CUSTOM AGGREGATORS
# ---------------------------------------------------------------------------

def median(values: list[float]) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)
    middle = len(ordered) // 2

    if len(ordered) % 2:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2


def custom_pivot(
    records: Sequence[Sale],
    group_field: Callable[[Sale], Any],
    metric_field: Callable[[Sale], float],
    aggregator: Callable[[list[float]], float],
) -> dict[str, float]:
    groups: dict[str, list[float]] = defaultdict(list)

    for record in records:
        groups[normalize_key(group_field(record))].append(
            metric_field(record)
        )

    return {
        key: aggregator(values)
        for key, values in sorted(groups.items())
    }


def demonstrate_custom_aggregation(records: Sequence[Sale]) -> None:
    print("\n=== CUSTOM AGGREGATION ===")

    median_order = custom_pivot(
        records,
        lambda r: r.region,
        lambda r: r.net_sales,
        median,
    )

    for region, value in median_order.items():
        print(f"Median order value in {region}: {money(value)}")


# ---------------------------------------------------------------------------
# 19. PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def benchmark_style_single_pass(records: Sequence[Sale]) -> dict[str, dict[str, float]]:
    """
    A single-pass aggregation avoids repeatedly filtering the complete dataset.
    For N records and K groups, this is approximately O(N) time.
    """

    aggregates: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "orders": 0.0,
            "units": 0.0,
            "sales": 0.0,
            "profit": 0.0,
        }
    )

    for record in records:
        bucket = aggregates[record.region]
        bucket["orders"] += 1
        bucket["units"] += record.units
        bucket["sales"] += record.net_sales
        bucket["profit"] += record.profit

    return dict(aggregates)


def demonstrate_performance_design(records: Sequence[Sale]) -> None:
    print("\n=== SINGLE-PASS PERFORMANCE DESIGN ===")

    result = benchmark_style_single_pass(records)

    for region, metrics in result.items():
        print(
            f"{region:8} "
            f"orders={metrics['orders']:.0f}, "
            f"units={metrics['units']:.0f}, "
            f"sales={money(metrics['sales'])}, "
            f"profit={money(metrics['profit'])}"
        )


# ---------------------------------------------------------------------------
# 20. TESTS
# ---------------------------------------------------------------------------

def run_tests() -> None:
    print("\n=== TESTS ===")

    assert count_records(DATA) == 12

    total_sales = sum_values(DATA, lambda r: r.net_sales)
    assert total_sales > 0

    region_sales = pivot_sum(DATA, lambda r: r.region, lambda r: r.net_sales)
    assert set(region_sales) == {"North", "South", "East", "West"}

    percentages = percentage_of_total(region_sales)
    assert abs(sum(percentages.values()) - 100.0) < 1e-9

    rows, columns, cells = pivot_2d(
        DATA,
        lambda r: r.region,
        lambda r: r.category,
        lambda r: r.net_sales,
    )
    assert rows
    assert columns
    assert cells

    assert not validate_dataset(DATA)

    assert median([10, 20, 30]) == 20
    assert median([10, 20, 30, 40]) == 25

    filtered = filter_records(DATA, lambda r: r.region == "North")
    assert all(r.region == "North" for r in filtered)

    print("All tests passed.")


# ---------------------------------------------------------------------------
# 21. MAIN STUDY RUNNER
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("PIVOT TABLES: AGGREGATING AND ANALYZING BUSINESS DATA")
    print("=" * 72)

    demonstrate_basic_aggregation(DATA)
    demonstrate_single_dimension_pivots(DATA)
    demonstrate_two_dimensional_pivot(DATA)
    demonstrate_hierarchical_pivot(DATA)
    demonstrate_filtering(DATA)
    demonstrate_percentages(DATA)
    demonstrate_totals(DATA)
    demonstrate_calculated_fields(DATA)
    demonstrate_time_pivots(DATA)
    demonstrate_ranking(DATA)
    demonstrate_conditional_aggregation(DATA)
    demonstrate_pareto(DATA)
    demonstrate_drill_down(DATA)
    demonstrate_validation(DATA)
    demonstrate_unpivot(DATA)
    demonstrate_multi_metric_pivot(DATA)
    demonstrate_custom_aggregation(DATA)
    demonstrate_performance_design(DATA)
    run_tests()

    print("\n=== KEY PIVOT DESIGN PRINCIPLES ===")
    print("1. Dimensions describe how records are grouped.")
    print("2. Measures are values that can be aggregated.")
    print("3. The aggregation function determines the meaning of a result.")
    print("4. Filtering changes the population before aggregation.")
    print("5. Calculated fields derive new measures from existing fields.")
    print("6. A pivot table is an analytical view, not a replacement for source data.")
    print("7. Validate source data before trusting aggregated results.")
    print("8. For large datasets, prefer efficient grouping and single-pass aggregation.")
    print("9. Distinguish weighted metrics from simple averages.")
    print("10. Always preserve the ability to drill from an aggregate back to detail.")


if __name__ == "__main__":
    main()
