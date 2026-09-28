"""
Advanced Excel: INDEX, MATCH, Dynamic Arrays, and Advanced Formulas
====================================================================

This study script models advanced spreadsheet techniques in Python.

The Python standard library does not implement Excel's calculation engine, so
the examples below reproduce the underlying logic of important Excel formulas:

    INDEX
    MATCH
    XLOOKUP-style lookups
    two-dimensional lookups
    INDEX + MATCH
    dynamic-array concepts
    FILTER
    SORT / SORTBY
    UNIQUE
    SEQUENCE
    TAKE / DROP
    CHOOSECOLS / CHOOSEROWS
    HSTACK / VSTACK
    LET-style formula decomposition
    conditional aggregation
    SUMIFS / COUNTIFS / AVERAGEIFS concepts
    lookup error handling
    wildcard matching
    approximate matching
    ranking
    running calculations
    weighted calculations
    advanced analytical formulas
    formula performance considerations

The demonstrations are deliberately implemented without external packages so
the file can be executed directly with Python 3.9+.

Run:
    python advanced_excel_formulas.py
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from itertools import accumulate
from math import isclose
from statistics import mean, median
from typing import Any, Callable, Iterable, Sequence


# ============================================================================
# 1. FUNDAMENTAL DATA MODEL
# ============================================================================

@dataclass(frozen=True)
class SalesRecord:
    """Represents one row in a spreadsheet-like sales table."""

    order_id: str
    region: str
    salesperson: str
    product: str
    category: str
    month: str
    units: int
    revenue: float
    cost: float

    @property
    def profit(self) -> float:
        return self.revenue - self.cost

    @property
    def margin(self) -> float:
        if self.revenue == 0:
            return 0.0
        return self.profit / self.revenue


DATA = [
    SalesRecord("O1001", "North", "Asha", "Laptop Pro", "Computers", "Jan", 8, 96000, 72000),
    SalesRecord("O1002", "South", "Ravi", "Laptop Pro", "Computers", "Jan", 6, 72000, 54000),
    SalesRecord("O1003", "West", "Neha", "Tablet X", "Tablets", "Jan", 12, 60000, 42000),
    SalesRecord("O1004", "East", "Vikram", "Phone Z", "Phones", "Jan", 20, 100000, 70000),
    SalesRecord("O1005", "North", "Asha", "Tablet X", "Tablets", "Feb", 15, 75000, 52500),
    SalesRecord("O1006", "South", "Ravi", "Phone Z", "Phones", "Feb", 17, 85000, 59500),
    SalesRecord("O1007", "West", "Neha", "Laptop Pro", "Computers", "Feb", 10, 120000, 90000),
    SalesRecord("O1008", "East", "Vikram", "Tablet X", "Tablets", "Feb", 9, 45000, 31500),
    SalesRecord("O1009", "North", "Asha", "Phone Z", "Phones", "Mar", 25, 125000, 87500),
    SalesRecord("O1010", "South", "Ravi", "Tablet X", "Tablets", "Mar", 14, 70000, 49000),
    SalesRecord("O1011", "West", "Neha", "Phone Z", "Phones", "Mar", 22, 110000, 77000),
    SalesRecord("O1012", "East", "Vikram", "Laptop Pro", "Computers", "Mar", 7, 84000, 63000),
]


def print_section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_table(rows: Iterable[Sequence[Any]], headers: Sequence[str]) -> None:
    rows = [list(row) for row in rows]
    widths = [
        max(len(str(headers[i])), *(len(str(row[i])) for row in rows))
        if rows
        else len(str(headers[i]))
        for i in range(len(headers))
    ]

    header = " | ".join(str(headers[i]).ljust(widths[i]) for i in range(len(headers)))
    print(header)
    print("-+-".join("-" * width for width in widths))

    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


# ============================================================================
# 2. EXCEL-LIKE INDEX
# ============================================================================

def excel_index(
    array: Sequence[Sequence[Any]] | Sequence[Any],
    row_num: int,
    column_num: int | None = None,
) -> Any:
    """
    Reproduce the core behavior of Excel INDEX.

    Excel:
        =INDEX(A2:A10, 3)
        =INDEX(A2:D10, 3, 2)

    Excel positions are one-based, while Python indexes are zero-based.
    """

    if row_num < 1:
        raise ValueError("Excel INDEX row_num must be at least 1.")

    if column_num is None:
        if row_num > len(array):
            raise IndexError("INDEX row is outside the supplied range.")
        return array[row_num - 1]

    if column_num < 1:
        raise ValueError("Excel INDEX column_num must be at least 1.")

    if row_num > len(array):
        raise IndexError("INDEX row is outside the supplied range.")

    row = array[row_num - 1]

    if column_num > len(row):
        raise IndexError("INDEX column is outside the supplied range.")

    return row[column_num - 1]


# ============================================================================
# 3. EXCEL-LIKE MATCH
# ============================================================================

def excel_match(
    lookup_value: Any,
    lookup_array: Sequence[Any],
    match_type: int = 0,
) -> int:
    """
    Reproduce Excel MATCH's three principal modes.

    match_type = 0:
        Exact match.

    match_type = 1:
        Largest value <= lookup_value.
        lookup_array must be ascending.

    match_type = -1:
        Smallest value >= lookup_value.
        lookup_array must be descending.

    Returns a one-based position, matching Excel's MATCH behavior.
    """

    if not lookup_array:
        raise ValueError("MATCH cannot search an empty range.")

    if match_type == 0:
        for position, value in enumerate(lookup_array, start=1):
            if value == lookup_value:
                return position
        raise LookupError(f"MATCH could not find {lookup_value!r}.")

    if match_type == 1:
        candidate = None
        for position, value in enumerate(lookup_array, start=1):
            if value <= lookup_value:
                candidate = position
            else:
                break

        if candidate is None:
            raise LookupError("No value satisfies MATCH approximate criteria.")

        return candidate

    if match_type == -1:
        candidate = None
        for position, value in enumerate(lookup_array, start=1):
            if value >= lookup_value:
                candidate = position
            else:
                break

        if candidate is None:
            raise LookupError("No value satisfies MATCH reverse approximate criteria.")

        return candidate

    raise ValueError("match_type must be -1, 0, or 1.")


# ============================================================================
# 4. INDEX + MATCH
# ============================================================================

def index_match(
    return_values: Sequence[Any],
    lookup_values: Sequence[Any],
    lookup_value: Any,
) -> Any:
    """
    Equivalent conceptually to:

        =INDEX(return_range, MATCH(lookup_value, lookup_range, 0))

    This separates the location-finding operation from the value-returning
    operation.
    """

    position = excel_match(lookup_value, lookup_values, 0)
    return excel_index(return_values, position)


# ============================================================================
# 5. TWO-DIMENSIONAL INDEX + MATCH
# ============================================================================

def two_way_lookup(
    table: Sequence[Sequence[Any]],
    row_labels: Sequence[Any],
    column_labels: Sequence[Any],
    row_key: Any,
    column_key: Any,
) -> Any:
    """
    Equivalent conceptually to:

        =INDEX(data,
               MATCH(row_key, row_labels, 0),
               MATCH(column_key, column_labels, 0))

    This is a powerful replacement for nested lookup formulas.
    """

    row_position = excel_match(row_key, row_labels, 0)
    column_position = excel_match(column_key, column_labels, 0)

    return excel_index(table, row_position, column_position)


# ============================================================================
# 6. EXACT MATCH WITH MULTIPLE CONDITIONS
# ============================================================================

def multi_criteria_index_match(
    records: Sequence[SalesRecord],
    region: str,
    product: str,
    month: str,
) -> SalesRecord:
    """
    Models a formula such as:

        =INDEX(order_id_range,
               MATCH(1,
                     (region_range=region)*
                     (product_range=product)*
                     (month_range=month),
                     0))

    Multiplication turns TRUE/FALSE conditions into 1/0 values.
    """

    for record in records:
        if (
            record.region == region
            and record.product == product
            and record.month == month
        ):
            return record

    raise LookupError("No record satisfies all criteria.")


# ============================================================================
# 7. FILTER: DYNAMIC ARRAYS
# ============================================================================

def excel_filter(
    values: Sequence[Any],
    include: Sequence[bool],
    if_empty: Any = None,
) -> list[Any]:
    """
    Model Excel FILTER:

        =FILTER(A2:A20, B2:B20="North", "No results")

    The result can contain zero, one, or many records. This is the central
    behavioral idea behind dynamic-array formulas.
    """

    if len(values) != len(include):
        raise ValueError("FILTER values and include arrays must have equal length.")

    result = [value for value, flag in zip(values, include) if flag]
    return result if result else ([] if if_empty is None else [if_empty])


def filter_records(
    records: Sequence[SalesRecord],
    predicate: Callable[[SalesRecord], bool],
) -> list[SalesRecord]:
    return [record for record in records if predicate(record)]


# ============================================================================
# 8. UNIQUE
# ============================================================================

def excel_unique(values: Iterable[Any]) -> list[Any]:
    """
    Model:

        =UNIQUE(A2:A100)

    Dictionary membership preserves first-seen order, which is useful for
    explaining the practical behavior of a spill result.
    """

    seen = set()
    result = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


# ============================================================================
# 9. SORT AND SORTBY
# ============================================================================

def excel_sort(
    values: Sequence[Any],
    descending: bool = False,
) -> list[Any]:
    """Model SORT for a one-dimensional range."""

    return sorted(values, reverse=descending)


def excel_sortby(
    records: Sequence[SalesRecord],
    key_function: Callable[[SalesRecord], Any],
    descending: bool = False,
) -> list[SalesRecord]:
    """Model SORTBY using an independently supplied sort key."""

    return sorted(records, key=key_function, reverse=descending)


# ============================================================================
# 10. SEQUENCE
# ============================================================================

def excel_sequence(
    rows: int,
    columns: int = 1,
    start: int = 1,
    step: int = 1,
) -> list[list[int]]:
    """
    Model:

        =SEQUENCE(5)
        =SEQUENCE(3, 4, 10, 10)
    """

    if rows < 1 or columns < 1:
        raise ValueError("SEQUENCE dimensions must be positive.")

    values = [
        start + index * step
        for index in range(rows * columns)
    ]

    return [
        values[row * columns:(row + 1) * columns]
        for row in range(rows)
    ]


# ============================================================================
# 11. TAKE AND DROP
# ============================================================================

def excel_take(
    matrix: Sequence[Sequence[Any]],
    rows: int | None = None,
    columns: int | None = None,
) -> list[list[Any]]:
    """Model positive and negative TAKE behavior."""

    result = [list(row) for row in matrix]

    if rows is not None:
        if rows >= 0:
            result = result[:rows]
        else:
            result = result[rows:]

    if columns is not None:
        if columns >= 0:
            result = [row[:columns] for row in result]
        else:
            result = [row[columns:] for row in result]

    return result


def excel_drop(
    matrix: Sequence[Sequence[Any]],
    rows: int = 0,
    columns: int = 0,
) -> list[list[Any]]:
    """Model positive and negative DROP behavior."""

    result = [list(row) for row in matrix]

    if rows > 0:
        result = result[rows:]
    elif rows < 0:
        result = result[:rows]

    if columns > 0:
        result = [row[columns:] for row in result]
    elif columns < 0:
        result = [row[:columns] for row in result]

    return result


# ============================================================================
# 12. CHOOSECOLS AND CHOOSEROWS
# ============================================================================

def excel_choosecols(
    matrix: Sequence[Sequence[Any]],
    *column_numbers: int,
) -> list[list[Any]]:
    """Model CHOOSECOLS using one-based Excel-style column numbers."""

    result = []

    for row in matrix:
        selected = []
        for column_number in column_numbers:
            index = column_number - 1 if column_number > 0 else len(row) + column_number
            if index < 0 or index >= len(row):
                raise IndexError("CHOOSECOLS column is outside the range.")
            selected.append(row[index])
        result.append(selected)

    return result


def excel_chooserows(
    matrix: Sequence[Sequence[Any]],
    *row_numbers: int,
) -> list[list[Any]]:
    """Model CHOOSEROWS using one-based Excel-style row numbers."""

    result = []

    for row_number in row_numbers:
        index = row_number - 1 if row_number > 0 else len(matrix) + row_number
        if index < 0 or index >= len(matrix):
            raise IndexError("CHOOSEROWS row is outside the range.")
        result.append(list(matrix[index]))

    return result


# ============================================================================
# 13. HSTACK AND VSTACK
# ============================================================================

def excel_hstack(*arrays: Sequence[Sequence[Any]]) -> list[list[Any]]:
    """Model HSTACK for rectangular arrays."""

    if not arrays:
        return []

    row_count = max(len(array) for array in arrays)
    result = [[] for _ in range(row_count)]

    for array in arrays:
        width = len(array[0]) if array else 0

        for row_index in range(row_count):
            if row_index < len(array):
                result[row_index].extend(array[row_index])
            else:
                result[row_index].extend(["#N/A"] * width)

    return result


def excel_vstack(*arrays: Sequence[Sequence[Any]]) -> list[list[Any]]:
    """Model VSTACK for arrays with potentially different widths."""

    if not arrays:
        return []

    width = max(len(row) for array in arrays for row in array)

    result = []

    for array in arrays:
        for row in array:
            padded = list(row) + ["#N/A"] * (width - len(row))
            result.append(padded)

    return result


# ============================================================================
# 14. IFERROR AND IFNA CONCEPTS
# ============================================================================

def excel_iferror(
    operation: Callable[[], Any],
    fallback: Any,
) -> Any:
    """Model IFERROR(expression, fallback)."""

    try:
        return operation()
    except Exception:
        return fallback


def excel_ifna(
    operation: Callable[[], Any],
    fallback: Any,
) -> Any:
    """Model IFNA(expression, fallback), limited to lookup failures."""

    try:
        return operation()
    except LookupError:
        return fallback


# ============================================================================
# 15. CONDITIONAL AGGREGATION
# ============================================================================

def sum_if(
    records: Sequence[SalesRecord],
    condition: Callable[[SalesRecord], bool],
    value: Callable[[SalesRecord], float],
) -> float:
    """Model SUMIF/SUMIFS."""

    return sum(value(record) for record in records if condition(record))


def count_if(
    records: Sequence[SalesRecord],
    condition: Callable[[SalesRecord], bool],
) -> int:
    """Model COUNTIF/COUNTIFS."""

    return sum(1 for record in records if condition(record))


def average_if(
    records: Sequence[SalesRecord],
    condition: Callable[[SalesRecord], bool],
    value: Callable[[SalesRecord], float],
) -> float:
    """Model AVERAGEIF/AVERAGEIFS."""

    selected = [value(record) for record in records if condition(record)]

    if not selected:
        raise ZeroDivisionError("AVERAGEIF has no qualifying values.")

    return mean(selected)


# ============================================================================
# 16. SUMPRODUCT
# ============================================================================

def sumproduct(
    first: Sequence[float],
    second: Sequence[float],
) -> float:
    """
    Model Excel SUMPRODUCT.

    Example:
        =SUMPRODUCT(units_range, price_range)

    It multiplies corresponding elements and then sums the products.
    """

    if len(first) != len(second):
        raise ValueError("SUMPRODUCT arrays must have the same length.")

    return sum(a * b for a, b in zip(first, second))


def weighted_average(
    values: Sequence[float],
    weights: Sequence[float],
) -> float:
    """Classic SUMPRODUCT / SUM pattern."""

    if len(values) != len(weights):
        raise ValueError("Values and weights must have equal length.")

    total_weight = sum(weights)

    if total_weight == 0:
        raise ZeroDivisionError("Weighted average requires non-zero total weight.")

    return sumproduct(values, weights) / total_weight


# ============================================================================
# 17. LET CONCEPT
# ============================================================================

def excel_let_demo(
    records: Sequence[SalesRecord],
    region: str,
) -> dict[str, float]:
    """
    Model the reasoning behind LET.

    Excel can bind reusable intermediate values:

        =LET(
            regionalSales,
            FILTER(Revenue, Region=SelectedRegion),
            total,
            SUM(regionalSales),
            average,
            AVERAGE(regionalSales),
            total/average
        )

    Naming repeated calculations improves readability and can reduce
    recalculation of expensive expressions.
    """

    regional_sales = [
        record.revenue
        for record in records
        if record.region == region
    ]

    total = sum(regional_sales)
    average_value = mean(regional_sales) if regional_sales else 0.0

    ratio = total / average_value if average_value else 0.0

    return {
        "total": total,
        "average": average_value,
        "total_to_average_ratio": ratio,
    }


# ============================================================================
# 18. LAMBDA-STYLE REUSABLE CALCULATIONS
# ============================================================================

def make_margin_calculator() -> Callable[[float, float], float]:
    """
    Model the conceptual purpose of Excel LAMBDA.

    Excel:

        =LAMBDA(revenue,cost,(revenue-cost)/revenue)

    The returned Python function is reusable without repeating the formula.
    """

    def margin(revenue: float, cost: float) -> float:
        if revenue == 0:
            return 0.0
        return (revenue - cost) / revenue

    return margin


# ============================================================================
# 19. WILDCARD MATCHING
# ============================================================================

def wildcard_to_regex(pattern: str) -> str:
    """
    Convert Excel-like wildcards to regular expressions.

    * = any number of characters
    ? = exactly one character
    ~ = escape the next wildcard character
    """

    import re

    output = []
    index = 0

    while index < len(pattern):
        character = pattern[index]

        if character == "~" and index + 1 < len(pattern):
            output.append(re.escape(pattern[index + 1]))
            index += 2
            continue

        if character == "*":
            output.append(".*")
        elif character == "?":
            output.append(".")
        else:
            output.append(re.escape(character))

        index += 1

    return "^" + "".join(output) + "$"


def excel_wildcard_match(
    pattern: str,
    value: str,
) -> bool:
    import re

    return re.match(wildcard_to_regex(pattern), value) is not None


# ============================================================================
# 20. APPROXIMATE LOOKUP
# ============================================================================

def approximate_lookup_ascending(
    lookup_value: float,
    thresholds: Sequence[float],
    results: Sequence[Any],
) -> Any:
    """
    Model approximate MATCH + INDEX.

    Example threshold table:

        0       Bronze
        10000   Silver
        50000   Gold
        100000  Platinum

    A value of 75000 belongs to Gold.
    """

    if len(thresholds) != len(results):
        raise ValueError("Thresholds and results must have equal lengths.")

    if not thresholds:
        raise ValueError("Threshold table cannot be empty.")

    if list(thresholds) != sorted(thresholds):
        raise ValueError("Thresholds must be ascending.")

    position = bisect_right(thresholds, lookup_value) - 1

    if position < 0:
        raise LookupError("Lookup value is below the first threshold.")

    return results[position]


# ============================================================================
# 21. RANKING
# ============================================================================

def excel_rank_descending(
    value: float,
    values: Sequence[float],
) -> int:
    """
    Model RANK.EQ in descending order.

    Equal values receive the same rank.
    """

    return 1 + sum(other > value for other in values)


def rank_with_ties(
    values: Sequence[float],
) -> list[int]:
    return [excel_rank_descending(value, values) for value in values]


# ============================================================================
# 22. RUNNING TOTAL
# ============================================================================

def running_total(values: Sequence[float]) -> list[float]:
    """
    Model a dynamic running calculation.

    A modern Excel equivalent can be constructed using SCAN or an expanding
    range depending on the Excel version and desired design.
    """

    return list(accumulate(values))


# ============================================================================
# 23. RUNNING AVERAGE
# ============================================================================

def running_average(values: Sequence[float]) -> list[float]:
    result = []
    total = 0.0

    for index, value in enumerate(values, start=1):
        total += value
        result.append(total / index)

    return result


# ============================================================================
# 24. DISTINCT COUNT
# ============================================================================

def distinct_count(values: Sequence[Any]) -> int:
    """
    Dynamic-array conceptual equivalent:

        =COUNTA(UNIQUE(A2:A100))
    """

    return len(excel_unique(values))


# ============================================================================
# 25. ADVANCED SALES ANALYSIS
# ============================================================================

def regional_summary(
    records: Sequence[SalesRecord],
) -> list[dict[str, Any]]:
    regions = excel_unique(record.region for record in records)

    summary = []

    for region in regions:
        selected = [record for record in records if record.region == region]

        revenue = sum(record.revenue for record in selected)
        profit = sum(record.profit for record in selected)
        units = sum(record.units for record in selected)

        summary.append(
            {
                "region": region,
                "orders": len(selected),
                "units": units,
                "revenue": revenue,
                "profit": profit,
                "margin": profit / revenue if revenue else 0.0,
            }
        )

    return summary


def product_summary(
    records: Sequence[SalesRecord],
) -> list[dict[str, Any]]:
    products = excel_unique(record.product for record in records)
    result = []

    for product in products:
        selected = [record for record in records if record.product == product]
        revenue = sum(record.revenue for record in selected)
        profit = sum(record.profit for record in selected)

        result.append(
            {
                "product": product,
                "orders": len(selected),
                "units": sum(record.units for record in selected),
                "revenue": revenue,
                "profit": profit,
                "margin": profit / revenue if revenue else 0.0,
            }
        )

    return result


# ============================================================================
# 26. MATRIX REPRESENTATION
# ============================================================================

def records_to_matrix(records: Sequence[SalesRecord]) -> list[list[Any]]:
    return [
        [
            record.order_id,
            record.region,
            record.salesperson,
            record.product,
            record.category,
            record.month,
            record.units,
            record.revenue,
            record.cost,
            record.profit,
            record.margin,
        ]
        for record in records
    ]


# ============================================================================
# 27. ERROR AND EDGE-CASE DEMONSTRATIONS
# ============================================================================

def demonstrate_errors() -> None:
    print_section("LOOKUP ERROR HANDLING")

    try:
        excel_match("DoesNotExist", ["A", "B", "C"], 0)
    except LookupError as error:
        print("Raw lookup error:", error)

    safe_result = excel_ifna(
        lambda: excel_match("DoesNotExist", ["A", "B", "C"], 0),
        "Not Found",
    )
    print("IFNA-style result:", safe_result)

    safe_error_result = excel_iferror(
        lambda: 10 / 0,
        "Calculation Error",
    )
    print("IFERROR-style result:", safe_error_result)

    try:
        excel_index([[1, 2], [3, 4]], 5, 1)
    except IndexError as error:
        print("INDEX edge case:", error)


# ============================================================================
# 28. PERFORMANCE COMPARISON
# ============================================================================

def naive_lookup(
    records: Sequence[SalesRecord],
    order_id: str,
) -> SalesRecord | None:
    """O(n) lookup, equivalent to scanning a range."""

    for record in records:
        if record.order_id == order_id:
            return record

    return None


def indexed_lookup_factory(
    records: Sequence[SalesRecord],
) -> Callable[[str], SalesRecord | None]:
    """
    Build an index once.

    Construction: O(n)
    Each lookup afterward: average O(1)
    """

    index = {record.order_id: record for record in records}

    def lookup(order_id: str) -> SalesRecord | None:
        return index.get(order_id)

    return lookup


def demonstrate_performance_concepts() -> None:
    print_section("PERFORMANCE CONCEPTS")

    large_dataset = [
        SalesRecord(
            order_id=f"O{i:06d}",
            region="North" if i % 2 == 0 else "South",
            salesperson="Asha" if i % 3 == 0 else "Ravi",
            product="Laptop Pro",
            category="Computers",
            month="Jan",
            units=1 + i % 10,
            revenue=1000 + i,
            cost=700 + i,
        )
        for i in range(1, 10001)
    ]

    target = "O009999"

    linear_result = naive_lookup(large_dataset, target)
    indexed_lookup = indexed_lookup_factory(large_dataset)
    indexed_result = indexed_lookup(target)

    print("Linear lookup found:", linear_result.order_id if linear_result else None)
    print("Indexed lookup found:", indexed_result.order_id if indexed_result else None)
    print("Linear lookup complexity: O(n)")
    print("Indexed lookup after index construction: average O(1)")
    print("Index construction complexity: O(n)")


# ============================================================================
# 29. PRACTICAL FORMULA REFERENCE
# ============================================================================

def print_formula_reference() -> None:
    print_section("EXCEL FORMULA REFERENCE")

    formulas = [
        ("INDEX", "=INDEX(return_range, row_num, [column_num])"),
        ("MATCH", "=MATCH(lookup_value, lookup_array, 0)"),
        ("INDEX + MATCH", "=INDEX(return_range, MATCH(key, lookup_range, 0))"),
        (
            "Two-way lookup",
            "=INDEX(data, MATCH(row_key, rows, 0), MATCH(column_key, columns, 0))",
        ),
        ("FILTER", '=FILTER(array, include, "No results")'),
        ("UNIQUE", "=UNIQUE(range)"),
        ("SORT", "=SORT(array, 1, -1)"),
        ("SORTBY", "=SORTBY(array, sort_range, -1)"),
        ("SEQUENCE", "=SEQUENCE(rows, columns, start, step)"),
        ("TAKE", "=TAKE(array, rows, [columns])"),
        ("DROP", "=DROP(array, rows, [columns])"),
        ("CHOOSECOLS", "=CHOOSECOLS(array, 1, 3, 5)"),
        ("CHOOSEROWS", "=CHOOSEROWS(array, 2, 5, -1)"),
        ("HSTACK", "=HSTACK(array1, array2)"),
        ("VSTACK", "=VSTACK(array1, array2)"),
        ("IFERROR", '=IFERROR(expression, "Fallback")'),
        ("SUMIFS", "=SUMIFS(sum_range, criteria_range1, criteria1, ...)"),
        ("COUNTIFS", "=COUNTIFS(criteria_range1, criteria1, ...)"),
        ("AVERAGEIFS", "=AVERAGEIFS(avg_range, criteria_range1, criteria1, ...)"),
        ("SUMPRODUCT", "=SUMPRODUCT(array1, array2)"),
        ("LET", "=LET(name1, value1, name2, value2, calculation)"),
        ("LAMBDA", "=LAMBDA(parameter1, parameter2, calculation)"),
        ("Running total", "=SCAN(0, values, LAMBDA(a,b,a+b))"),
        ("Distinct count", "=COUNTA(UNIQUE(range))"),
    ]

    print_table(formulas, ["Function", "Representative Formula"])


# ============================================================================
# 30. MAIN EDUCATIONAL DEMONSTRATION
# ============================================================================

def main() -> None:
    print_section("ADVANCED EXCEL FORMULAS: PYTHON STUDY IMPLEMENTATION")

    print(
        """
This program reproduces the logic behind advanced Excel formulas.
The key distinction is:

INDEX finds a value by position.
MATCH finds a position.
INDEX + MATCH combines both operations.
Dynamic-array functions return collections that can spill into neighboring
cells instead of requiring one formula per output cell.
LET and LAMBDA improve formula structure and reuse.
"""
    )

    # ------------------------------------------------------------------------
    # Basic INDEX
    # ------------------------------------------------------------------------
    print_section("1. INDEX")

    matrix = [
        ["North", 120000, 0.25],
        ["South", 90000, 0.20],
        ["West", 150000, 0.30],
        ["East", 110000, 0.22],
    ]

    print("INDEX row 3:", excel_index(matrix, 3))
    print("INDEX row 2, column 2:", excel_index(matrix, 2, 2))

    # ------------------------------------------------------------------------
    # MATCH
    # ------------------------------------------------------------------------
    print_section("2. MATCH")

    products = ["Laptop Pro", "Tablet X", "Phone Z"]

    print("Exact MATCH for Tablet X:", excel_match("Tablet X", products, 0))

    thresholds = [0, 10000, 50000, 100000]
    print(
        "Approximate MATCH position for 75000:",
        excel_match(75000, thresholds, 1),
    )

    # ------------------------------------------------------------------------
    # INDEX + MATCH
    # ------------------------------------------------------------------------
    print_section("3. INDEX + MATCH")

    product_prices = [12000, 5000, 3000]

    tablet_price = index_match(
        product_prices,
        products,
        "Tablet X",
    )

    print("Tablet X price:", tablet_price)

    # ------------------------------------------------------------------------
    # Two-way lookup
    # ------------------------------------------------------------------------
    print_section("4. TWO-WAY INDEX + MATCH")

    regions = ["North", "South", "West", "East"]
    months = ["Jan", "Feb", "Mar"]

    revenue_table = [
        [96000, 75000, 125000],
        [72000, 85000, 70000],
        [60000, 120000, 110000],
        [100000, 45000, 84000],
    ]

    result = two_way_lookup(
        revenue_table,
        regions,
        months,
        "West",
        "Feb",
    )

    print("West / Feb revenue:", result)

    # ------------------------------------------------------------------------
    # Multi-criteria lookup
    # ------------------------------------------------------------------------
    print_section("5. MULTI-CRITERIA LOOKUP")

    record = multi_criteria_index_match(
        DATA,
        region="North",
        product="Tablet X",
        month="Feb",
    )

    print("Matching order:", record.order_id)
    print("Revenue:", record.revenue)

    # ------------------------------------------------------------------------
    # Dynamic FILTER
    # ------------------------------------------------------------------------
    print_section("6. FILTER AND SPILL CONCEPT")

    north_records = filter_records(
        DATA,
        lambda record: record.region == "North",
    )

    print_table(
        [
            (r.order_id, r.product, r.month, r.revenue)
            for r in north_records
        ],
        ["Order", "Product", "Month", "Revenue"],
    )

    high_profit_records = filter_records(
        DATA,
        lambda record: record.profit >= 30000,
    )

    print("\nOrders with profit >= 30000:")
    print([record.order_id for record in high_profit_records])

    # Multiple criteria:
    north_laptops = filter_records(
        DATA,
        lambda record: record.region == "North"
        and record.product == "Laptop Pro",
    )

    print("North Laptop Pro orders:")
    print([record.order_id for record in north_laptops])

    # ------------------------------------------------------------------------
    # UNIQUE
    # ------------------------------------------------------------------------
    print_section("7. UNIQUE")

    all_regions = [record.region for record in DATA]
    all_products = [record.product for record in DATA]

    print("Unique regions:", excel_unique(all_regions))
    print("Unique products:", excel_unique(all_products))

    # ------------------------------------------------------------------------
    # SORT / SORTBY
    # ------------------------------------------------------------------------
    print_section("8. SORT AND SORTBY")

    revenues = [record.revenue for record in DATA]

    print("Revenue ascending:")
    print(excel_sort(revenues))

    top_orders = excel_sortby(
        DATA,
        key_function=lambda record: record.profit,
        descending=True,
    )[:5]

    print("\nTop five orders by profit:")
    print_table(
        [
            (r.order_id, r.product, r.region, round(r.profit, 2))
            for r in top_orders
        ],
        ["Order", "Product", "Region", "Profit"],
    )

    # ------------------------------------------------------------------------
    # SEQUENCE
    # ------------------------------------------------------------------------
    print_section("9. SEQUENCE")

    print("SEQUENCE(5):")
    print(excel_sequence(5))

    print("\nSEQUENCE(3, 4, 10, 10):")
    print(excel_sequence(3, 4, 10, 10))

    # ------------------------------------------------------------------------
    # TAKE / DROP / CHOOSECOLS / CHOOSEROWS
    # ------------------------------------------------------------------------
    print_section("10. DYNAMIC-ARRAY SHAPING")

    matrix_with_header = [
        ["Order", "Region", "Product", "Revenue", "Profit"],
        ["O1001", "North", "Laptop Pro", 96000, 24000],
        ["O1002", "South", "Laptop Pro", 72000, 18000],
        ["O1003", "West", "Tablet X", 60000, 18000],
        ["O1004", "East", "Phone Z", 100000, 30000],
    ]

    print("TAKE first 3 rows:")
    for row in excel_take(matrix_with_header, rows=3):
        print(row)

    print("\nDROP first row:")
    for row in excel_drop(matrix_with_header, rows=1):
        print(row)

    print("\nCHOOSECOLS: Order, Product, Profit:")
    for row in excel_choosecols(matrix_with_header, 1, 3, 5):
        print(row)

    print("\nCHOOSEROWS: header and final data row:")
    for row in excel_chooserows(matrix_with_header, 1, -1):
        print(row)

    # ------------------------------------------------------------------------
    # HSTACK / VSTACK
    # ------------------------------------------------------------------------
    print_section("11. HSTACK AND VSTACK")

    left = [["A", 10], ["B", 20]]
    right = [["X"], ["Y"]]

    print("HSTACK:")
    for row in excel_hstack(left, right):
        print(row)

    print("\nVSTACK:")
    for row in excel_vstack(left, right):
        print(row)

    # ------------------------------------------------------------------------
    # Conditional aggregation
    # ------------------------------------------------------------------------
    print_section("12. SUMIFS, COUNTIFS, AVERAGEIFS")

    north_revenue = sum_if(
        DATA,
        lambda record: record.region == "North",
        lambda record: record.revenue,
    )

    north_order_count = count_if(
        DATA,
        lambda record: record.region == "North",
    )

    north_average_revenue = average_if(
        DATA,
        lambda record: record.region == "North",
        lambda record: record.revenue,
    )

    print("North revenue:", north_revenue)
    print("North orders:", north_order_count)
    print("North average order revenue:", north_average_revenue)

    # Multiple criteria:
    north_phone_revenue = sum_if(
        DATA,
        lambda record: record.region == "North"
        and record.product == "Phone Z",
        lambda record: record.revenue,
    )

    print("North Phone Z revenue:", north_phone_revenue)

    # ------------------------------------------------------------------------
    # SUMPRODUCT
    # ------------------------------------------------------------------------
    print_section("13. SUMPRODUCT")

    units = [record.units for record in DATA]
    average_order_revenue = mean(revenues)

    print("Total units:", sum(units))
    print("Revenue total:", sumproduct([1] * len(revenues), revenues))
    print("Average order revenue:", average_order_revenue)

    category_values = [100, 200, 300]
    category_weights = [2, 3, 5]

    print(
        "Weighted average:",
        weighted_average(category_values, category_weights),
    )

    # ------------------------------------------------------------------------
    # LET
    # ------------------------------------------------------------------------
    print_section("14. LET-STYLE FORMULA STRUCTURE")

    print("North LET calculation:")
    print(excel_let_demo(DATA, "North"))

    # ------------------------------------------------------------------------
    # LAMBDA
    # ------------------------------------------------------------------------
    print_section("15. LAMBDA-STYLE REUSABLE CALCULATION")

    margin_calculator = make_margin_calculator()

    for revenue, cost in [(1000, 700), (5000, 3000), (0, 0)]:
        print(
            f"Revenue={revenue}, Cost={cost}, "
            f"Margin={margin_calculator(revenue, cost):.2%}"
        )

    # ------------------------------------------------------------------------
    # Wildcards
    # ------------------------------------------------------------------------
    print_section("16. WILDCARD MATCHING")

    for pattern in ["Laptop*", "?hone Z", "Tablet ?"]:
        matching_products = [
            product
            for product in products
            if excel_wildcard_match(pattern, product)
        ]

        print(f"{pattern!r} -> {matching_products}")

    # ------------------------------------------------------------------------
    # Approximate lookup
    # ------------------------------------------------------------------------
    print_section("17. APPROXIMATE LOOKUP")

    customer_levels = ["Bronze", "Silver", "Gold", "Platinum"]

    for revenue in [5000, 10000, 25000, 50000, 75000, 100000, 150000]:
        level = approximate_lookup_ascending(
            revenue,
            thresholds,
            customer_levels,
        )
        print(f"{revenue:>7} -> {level}")

    # ------------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------------
    print_section("18. RANKING")

    profits = [record.profit for record in DATA]
    ranks = rank_with_ties(profits)

    print_table(
        [
            (record.order_id, record.profit, rank)
            for record, rank in zip(DATA, ranks)
        ],
        ["Order", "Profit", "Rank"],
    )

    # ------------------------------------------------------------------------
    # Running calculations
    # ------------------------------------------------------------------------
    print_section("19. RUNNING TOTAL AND RUNNING AVERAGE")

    monthly_revenue = [
        sum(record.revenue for record in DATA if record.month == month)
        for month in ["Jan", "Feb", "Mar"]
    ]

    print("Monthly revenue:", monthly_revenue)
    print("Running total:", running_total(monthly_revenue))
    print("Running average:", running_average(monthly_revenue))

    # ------------------------------------------------------------------------
    # Distinct counts
    # ------------------------------------------------------------------------
    print_section("20. DISTINCT COUNT")

    salespeople = [record.salesperson for record in DATA]
    print("Distinct salespeople:", distinct_count(salespeople))

    # ------------------------------------------------------------------------
    # Regional analysis
    # ------------------------------------------------------------------------
    print_section("21. REGIONAL ANALYSIS")

    summary = regional_summary(DATA)

    print_table(
        [
            (
                item["region"],
                item["orders"],
                item["units"],
                f"{item['revenue']:,.0f}",
                f"{item['profit']:,.0f}",
                f"{item['margin']:.2%}",
            )
            for item in summary
        ],
        ["Region", "Orders", "Units", "Revenue", "Profit", "Margin"],
    )

    # ------------------------------------------------------------------------
    # Product analysis
    # ------------------------------------------------------------------------
    print_section("22. PRODUCT ANALYSIS")

    product_data = product_summary(DATA)

    print_table(
        [
            (
                item["product"],
                item["orders"],
                item["units"],
                f"{item['revenue']:,.0f}",
                f"{item['profit']:,.0f}",
                f"{item['margin']:.2%}",
            )
            for item in product_data
        ],
        ["Product", "Orders", "Units", "Revenue", "Profit", "Margin"],
    )

    # ------------------------------------------------------------------------
    # Matrix extraction
    # ------------------------------------------------------------------------
    print_section("23. SPREADSHEET-LIKE TABLE")

    table = records_to_matrix(DATA[:5])

    print_table(
        table,
        [
            "Order",
            "Region",
            "Salesperson",
            "Product",
            "Category",
            "Month",
            "Units",
            "Revenue",
            "Cost",
            "Profit",
            "Margin",
        ],
    )

    # ------------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------------
    demonstrate_errors()

    # ------------------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------------------
    demonstrate_performance_concepts()

    # ------------------------------------------------------------------------
    # Formula reference
    # ------------------------------------------------------------------------
    print_formula_reference()

    # ------------------------------------------------------------------------
    # Conceptual comparison
    # ------------------------------------------------------------------------
    print_section("IMPORTANT DISTINCTIONS")

    distinctions = [
        (
            "INDEX",
            "Returns a value from a specified position.",
        ),
        (
            "MATCH",
            "Returns the position of a matching value.",
        ),
        (
            "INDEX + MATCH",
            "Separates lookup-location logic from returned-value logic.",
        ),
        (
            "FILTER",
            "Returns every row or value satisfying a Boolean condition.",
        ),
        (
            "UNIQUE",
            "Returns distinct values as a dynamic array.",
        ),
        (
            "SORT / SORTBY",
            "Reorders a dynamic array by values or independent sort keys.",
        ),
        (
            "LET",
            "Names intermediate expressions inside one formula.",
        ),
        (
            "LAMBDA",
            "Defines reusable custom calculations without VBA.",
        ),
        (
            "SUMIFS",
            "Aggregates a numeric range using one or more criteria.",
        ),
        (
            "SUMPRODUCT",
            "Multiplies corresponding arrays and sums their products.",
        ),
    ]

    print_table(distinctions, ["Technique", "Purpose"])

    print_section("END OF STUDY SCRIPT")

    print(
        """
Key formula-design principles demonstrated:

1. Find positions separately from returned values when lookup logic benefits
   from INDEX + MATCH.
2. Use exact matching when identifiers must match precisely.
3. Use approximate matching only with correctly ordered lookup tables.
4. Use dynamic arrays when the output naturally contains multiple values.
5. Treat spill ranges as a single logical result rather than manually copying
   formulas into every output cell.
6. Use IFNA for lookup-specific failures when other calculation errors should
   remain visible.
7. Use IFERROR when a broader fallback is genuinely appropriate.
8. Use LET to name expensive or repeated intermediate expressions.
9. Use LAMBDA for reusable business logic.
10. Consider calculation cost, range size, volatile functions, and repeated
    computations when designing large workbooks.
"""
    )


if __name__ == "__main__":
    main()
