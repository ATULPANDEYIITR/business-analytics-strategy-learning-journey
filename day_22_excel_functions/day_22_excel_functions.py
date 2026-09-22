"""
Excel Functions: IF, SUMIF, COUNTIF, XLOOKUP and Related Functions

A self-contained study and practice program covering:
- IF, IFS, AND, OR, NOT
- SUM, AVERAGE, MIN, MAX, ROUND
- SUMIF, SUMIFS
- COUNT, COUNTA, COUNTIF, COUNTIFS
- XLOOKUP-style exact and approximate lookup
- INDEX/MATCH-style lookup concepts
- IFERROR and validation
- Text and date-related helper logic
- Nested conditions
- Data cleaning
- Formula dependency concepts
- Business reporting
- Edge cases, errors, and performance considerations

The program uses ordinary Python data structures to model spreadsheet-style
records and implements reusable functions that behave similarly to important
Excel functions. No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Iterable, Optional


# ---------------------------------------------------------------------------
# SECTION 1: BASIC SPREADSHEET-LIKE FUNCTIONS
# ---------------------------------------------------------------------------

def excel_sum(values: Iterable[Any]) -> float:
    """Approximate Excel SUM behavior for numeric values."""
    total = 0.0

    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            total += value

    return total


def excel_average(values: Iterable[Any]) -> float:
    """Calculate the arithmetic mean of numeric values."""
    numbers = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numbers:
        raise ValueError("AVERAGE requires at least one numeric value.")

    return sum(numbers) / len(numbers)


def excel_min(values: Iterable[Any]) -> float:
    """Return the minimum numeric value."""
    numbers = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numbers:
        raise ValueError("MIN requires at least one numeric value.")

    return min(numbers)


def excel_max(values: Iterable[Any]) -> float:
    """Return the maximum numeric value."""
    numbers = [
        value
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]

    if not numbers:
        raise ValueError("MAX requires at least one numeric value.")

    return max(numbers)


def excel_round(number: float, digits: int = 0) -> float:
    """
    Spreadsheet-style decimal rounding using ROUND_HALF_UP.

    Python's built-in round() uses bankers rounding for some values, so
    Decimal is used here when deterministic financial-style rounding matters.
    """
    quantizer = Decimal("1") if digits == 0 else Decimal("1." + "0" * digits)

    rounded = Decimal(str(number)).quantize(
        quantizer,
        rounding=ROUND_HALF_UP,
    )

    return float(rounded)


# ---------------------------------------------------------------------------
# SECTION 2: LOGICAL FUNCTIONS
# ---------------------------------------------------------------------------

def excel_if(
    condition: bool,
    value_if_true: Any,
    value_if_false: Any,
) -> Any:
    """
    Excel-style IF.

    Concept:
        IF(condition, value_if_true, value_if_false)
    """
    return value_if_true if condition else value_if_false


def excel_ifs(*conditions_and_values: Any) -> Any:
    """
    Simplified Excel IFS.

    Arguments are supplied as:
        condition1, value1, condition2, value2, ...

    The first true condition determines the result.
    """
    if len(conditions_and_values) % 2 != 0:
        raise ValueError("IFS requires condition/value pairs.")

    for index in range(0, len(conditions_and_values), 2):
        condition = conditions_and_values[index]
        result = conditions_and_values[index + 1]

        if condition:
            return result

    raise ValueError("IFS found no TRUE condition.")


def excel_and(*conditions: bool) -> bool:
    """Return TRUE only when every condition is TRUE."""
    return all(conditions)


def excel_or(*conditions: bool) -> bool:
    """Return TRUE when at least one condition is TRUE."""
    return any(conditions)


def excel_not(condition: bool) -> bool:
    """Reverse a logical condition."""
    return not condition


def excel_iferror(
    calculation: Callable[[], Any],
    fallback: Any,
) -> Any:
    """
    Excel-style IFERROR.

    The calculation is delayed through a callable so exceptions can be caught.
    """
    try:
        return calculation()
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# SECTION 3: CONDITIONAL AGGREGATION
# ---------------------------------------------------------------------------

def matches_criterion(value: Any, criterion: Any) -> bool:
    """
    Implement common SUMIF/COUNTIF-style criteria.

    Supported examples:
        100
        "North"
        ">100"
        ">=500"
        "<50"
        "<=20"
        "<>Cancelled"
    """
    if not isinstance(criterion, str):
        return value == criterion

    operators = [">=", "<=", "<>", ">", "<", "="]

    operator = "="
    target = criterion

    for candidate in operators:
        if criterion.startswith(candidate):
            operator = candidate
            target = criterion[len(candidate):]
            break

    target = target.strip()

    # Attempt numeric comparison when both sides can be numeric.
    try:
        numeric_value = float(value)
        numeric_target = float(target)

        if operator == "=":
            return numeric_value == numeric_target
        if operator == ">":
            return numeric_value > numeric_target
        if operator == "<":
            return numeric_value < numeric_target
        if operator == ">=":
            return numeric_value >= numeric_target
        if operator == "<=":
            return numeric_value <= numeric_target
        if operator == "<>":
            return numeric_value != numeric_target

    except (ValueError, TypeError):
        pass

    text_value = str(value).lower()
    text_target = target.lower()

    if operator == "=":
        return text_value == text_target

    if operator == "<>":
        return text_value != text_target

    if operator == ">":
        return text_value > text_target

    if operator == "<":
        return text_value < text_target

    if operator == ">=":
        return text_value >= text_target

    if operator == "<=":
        return text_value <= text_target

    return False


def excel_sumif(
    criteria_range: Iterable[Any],
    criterion: Any,
    sum_range: Iterable[Any],
) -> float:
    """
    SUMIF implementation.

    Concept:
        SUMIF(criteria_range, criterion, sum_range)
    """
    criteria_values = list(criteria_range)
    sum_values = list(sum_range)

    if len(criteria_values) != len(sum_values):
        raise ValueError("criteria_range and sum_range must have equal length.")

    total = 0.0

    for criterion_value, sum_value in zip(criteria_values, sum_values):
        if matches_criterion(criterion_value, criterion):
            if isinstance(sum_value, (int, float)) and not isinstance(sum_value, bool):
                total += sum_value

    return total


def excel_sumifs(
    sum_range: Iterable[Any],
    *criteria_pairs: Any,
) -> float:
    """
    SUMIFS implementation.

    Arguments after sum_range are supplied as:
        criteria_range1, criterion1, criteria_range2, criterion2, ...
    """
    sum_values = list(sum_range)

    if len(criteria_pairs) % 2 != 0:
        raise ValueError("SUMIFS requires range/criterion pairs.")

    pairs = []

    for index in range(0, len(criteria_pairs), 2):
        current_range = list(criteria_pairs[index])
        criterion = criteria_pairs[index + 1]

        if len(current_range) != len(sum_values):
            raise ValueError("All ranges must have equal length.")

        pairs.append((current_range, criterion))

    total = 0.0

    for row_index, sum_value in enumerate(sum_values):
        if not isinstance(sum_value, (int, float)) or isinstance(sum_value, bool):
            continue

        all_conditions_match = all(
            matches_criterion(current_range[row_index], criterion)
            for current_range, criterion in pairs
        )

        if all_conditions_match:
            total += sum_value

    return total


def excel_countif(
    criteria_range: Iterable[Any],
    criterion: Any,
) -> int:
    """COUNTIF implementation."""
    return sum(
        1
        for value in criteria_range
        if matches_criterion(value, criterion)
    )


def excel_countifs(*criteria_pairs: Any) -> int:
    """COUNTIFS implementation."""
    if len(criteria_pairs) == 0 or len(criteria_pairs) % 2 != 0:
        raise ValueError("COUNTIFS requires range/criterion pairs.")

    pairs = []

    expected_length: Optional[int] = None

    for index in range(0, len(criteria_pairs), 2):
        current_range = list(criteria_pairs[index])
        criterion = criteria_pairs[index + 1]

        if expected_length is None:
            expected_length = len(current_range)

        if len(current_range) != expected_length:
            raise ValueError("All criteria ranges must have equal length.")

        pairs.append((current_range, criterion))

    return sum(
        all(
            matches_criterion(current_range[row_index], criterion)
            for current_range, criterion in pairs
        )
        for row_index in range(expected_length or 0)
    )


# ---------------------------------------------------------------------------
# SECTION 4: LOOKUP FUNCTIONS
# ---------------------------------------------------------------------------

def excel_xlookup(
    lookup_value: Any,
    lookup_array: Iterable[Any],
    return_array: Iterable[Any],
    if_not_found: Any = None,
    match_mode: int = 0,
) -> Any:
    """
    XLOOKUP-style implementation.

    match_mode:
        0  -> exact match
        -1 -> exact match or next smaller item
        1  -> exact match or next larger item
    """
    lookup_values = list(lookup_array)
    return_values = list(return_array)

    if len(lookup_values) != len(return_values):
        raise ValueError("Lookup and return arrays must have equal length.")

    # Exact lookup.
    if match_mode == 0:
        for current_value, return_value in zip(lookup_values, return_values):
            if current_value == lookup_value:
                return return_value

        return if_not_found

    # Approximate lookup requires comparable values.
    if match_mode == -1:
        candidates = [
            (current_value, return_value)
            for current_value, return_value in zip(
                lookup_values,
                return_values,
            )
            if current_value <= lookup_value
        ]

        if not candidates:
            return if_not_found

        return max(candidates, key=lambda item: item[0])[1]

    if match_mode == 1:
        candidates = [
            (current_value, return_value)
            for current_value, return_value in zip(
                lookup_values,
                return_values,
            )
            if current_value >= lookup_value
        ]

        if not candidates:
            return if_not_found

        return min(candidates, key=lambda item: item[0])[1]

    raise ValueError("Unsupported match_mode.")


def index_match(
    lookup_value: Any,
    lookup_array: Iterable[Any],
    return_array: Iterable[Any],
    if_not_found: Any = None,
) -> Any:
    """
    INDEX/MATCH-style lookup.

    This illustrates the conceptual relationship:
        MATCH finds the position.
        INDEX returns the value at that position.
    """
    lookup_values = list(lookup_array)
    return_values = list(return_array)

    if len(lookup_values) != len(return_values):
        raise ValueError("Arrays must have equal length.")

    try:
        position = lookup_values.index(lookup_value)
    except ValueError:
        return if_not_found

    return return_values[position]


# ---------------------------------------------------------------------------
# SECTION 5: TEXT AND VALIDATION HELPERS
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    """Simulate common spreadsheet data-cleaning behavior."""
    return " ".join(str(value).strip().split()).lower()


def excel_exact(first: Any, second: Any) -> bool:
    """
    Similar to Excel EXACT.

    EXACT is case-sensitive, unlike a normal case-insensitive comparison.
    """
    return str(first) == str(second)


def is_blank(value: Any) -> bool:
    """Represent the practical meaning of an empty spreadsheet cell."""
    return value is None or value == ""


def validate_required_fields(record: dict[str, Any], fields: list[str]) -> list[str]:
    """Return missing required fields."""
    return [
        field
        for field in fields
        if field not in record or is_blank(record[field])
    ]


# ---------------------------------------------------------------------------
# SECTION 6: BUSINESS DATA MODEL
# ---------------------------------------------------------------------------

@dataclass
class SalesRecord:
    order_id: str
    region: str
    salesperson: str
    product: str
    category: str
    quantity: int
    unit_price: float
    discount: float
    status: str
    order_date: date

    @property
    def gross_sales(self) -> float:
        return self.quantity * self.unit_price

    @property
    def net_sales(self) -> float:
        return self.gross_sales * (1 - self.discount)


SALES_DATA = [
    SalesRecord(
        "ORD-001", "North", "Asha", "Laptop", "Electronics",
        3, 65000, 0.05, "Completed", date(2026, 1, 10)
    ),
    SalesRecord(
        "ORD-002", "South", "Ravi", "Monitor", "Electronics",
        8, 18000, 0.02, "Completed", date(2026, 1, 11)
    ),
    SalesRecord(
        "ORD-003", "North", "Meera", "Desk", "Furniture",
        5, 12000, 0.10, "Completed", date(2026, 1, 12)
    ),
    SalesRecord(
        "ORD-004", "West", "Kabir", "Chair", "Furniture",
        10, 7500, 0.08, "Cancelled", date(2026, 1, 14)
    ),
    SalesRecord(
        "ORD-005", "East", "Asha", "Laptop", "Electronics",
        2, 70000, 0.03, "Completed", date(2026, 2, 2)
    ),
    SalesRecord(
        "ORD-006", "South", "Ravi", "Keyboard", "Electronics",
        20, 2500, 0.00, "Completed", date(2026, 2, 5)
    ),
    SalesRecord(
        "ORD-007", "West", "Kabir", "Desk", "Furniture",
        4, 13500, 0.05, "Completed", date(2026, 2, 8)
    ),
    SalesRecord(
        "ORD-008", "North", "Meera", "Chair", "Furniture",
        15, 7200, 0.07, "Completed", date(2026, 2, 12)
    ),
    SalesRecord(
        "ORD-009", "East", "Asha", "Monitor", "Electronics",
        6, 19500, 0.04, "Pending", date(2026, 2, 15)
    ),
    SalesRecord(
        "ORD-010", "South", "Ravi", "Laptop", "Electronics",
        1, 68000, 0.01, "Completed", date(2026, 3, 1)
    ),
]


# ---------------------------------------------------------------------------
# SECTION 7: BEGINNER EXAMPLES
# ---------------------------------------------------------------------------

def beginner_examples() -> None:
    print("\n" + "=" * 80)
    print("BEGINNER: IF AND BASIC FUNCTIONS")
    print("=" * 80)

    score = 82

    result = excel_if(
        score >= 40,
        "Pass",
        "Fail",
    )

    print(f"Score: {score}")
    print(f"IF(score >= 40, 'Pass', 'Fail') -> {result}")

    marks = [72, 81, 65, 93, 58]

    print(f"SUM -> {excel_sum(marks)}")
    print(f"AVERAGE -> {excel_average(marks):.2f}")
    print(f"MIN -> {excel_min(marks)}")
    print(f"MAX -> {excel_max(marks)}")
    print(f"ROUND(AVERAGE, 1) -> {excel_round(excel_average(marks), 1)}")

    attendance = 91

    eligibility = excel_if(
        excel_and(score >= 40, attendance >= 75),
        "Eligible",
        "Not eligible",
    )

    print(f"Eligibility using IF + AND -> {eligibility}")

    special_case = excel_if(
        excel_or(score >= 90, attendance == 100),
        "Special recognition",
        "Standard status",
    )

    print(f"IF + OR -> {special_case}")


# ---------------------------------------------------------------------------
# SECTION 8: NESTED IF AND IFS
# ---------------------------------------------------------------------------

def grading_examples() -> None:
    print("\n" + "=" * 80)
    print("INTERMEDIATE: NESTED IF AND IFS")
    print("=" * 80)

    scores = [95, 87, 74, 61, 49, 31]

    for score in scores:
        grade = excel_ifs(
            score >= 90, "A",
            score >= 80, "B",
            score >= 70, "C",
            score >= 60, "D",
            score >= 40, "E",
            True, "F",
        )

        print(f"Score {score:>3} -> Grade {grade}")

    # Nested IF is valid but becomes harder to maintain as complexity grows.
    score = 83

    nested_result = excel_if(
        score >= 90,
        "A",
        excel_if(
            score >= 80,
            "B",
            excel_if(
                score >= 70,
                "C",
                "Below C",
            ),
        ),
    )

    print(f"Nested IF result for {score}: {nested_result}")


# ---------------------------------------------------------------------------
# SECTION 9: SUMIF, SUMIFS, COUNTIF, COUNTIFS
# ---------------------------------------------------------------------------

def conditional_aggregation_examples() -> None:
    print("\n" + "=" * 80)
    print("INTERMEDIATE: SUMIF, SUMIFS, COUNTIF, COUNTIFS")
    print("=" * 80)

    regions = [record.region for record in SALES_DATA]
    sales = [record.net_sales for record in SALES_DATA]
    statuses = [record.status for record in SALES_DATA]
    categories = [record.category for record in SALES_DATA]
    quantities = [record.quantity for record in SALES_DATA]

    north_sales = excel_sumif(
        regions,
        "North",
        sales,
    )

    completed_sales = excel_sumif(
        statuses,
        "Completed",
        sales,
    )

    print(f"North sales -> {north_sales:,.2f}")
    print(f"Completed sales -> {completed_sales:,.2f}")

    north_completed_sales = excel_sumifs(
        sales,
        regions,
        "North",
        statuses,
        "Completed",
    )

    print(f"North + Completed sales -> {north_completed_sales:,.2f}")

    electronics_completed_sales = excel_sumifs(
        sales,
        categories,
        "Electronics",
        statuses,
        "Completed",
    )

    print(
        "Electronics + Completed sales -> "
        f"{electronics_completed_sales:,.2f}"
    )

    completed_count = excel_countif(
        statuses,
        "Completed",
    )

    print(f"Completed orders -> {completed_count}")

    high_quantity_orders = excel_countif(
        quantities,
        ">10",
    )

    print(f"Orders with quantity > 10 -> {high_quantity_orders}")

    north_completed_count = excel_countifs(
        regions,
        "North",
        statuses,
        "Completed",
    )

    print(
        "North + Completed order count -> "
        f"{north_completed_count}"
    )


# ---------------------------------------------------------------------------
# SECTION 10: XLOOKUP
# ---------------------------------------------------------------------------

def lookup_examples() -> None:
    print("\n" + "=" * 80)
    print("INTERMEDIATE: XLOOKUP")
    print("=" * 80)

    order_ids = [record.order_id for record in SALES_DATA]
    salespeople = [record.salesperson for record in SALES_DATA]
    products = [record.product for record in SALES_DATA]
    net_sales = [record.net_sales for record in SALES_DATA]

    target_order = "ORD-005"

    salesperson = excel_xlookup(
        target_order,
        order_ids,
        salespeople,
        if_not_found="Order not found",
    )

    product = excel_xlookup(
        target_order,
        order_ids,
        products,
        if_not_found="Product not found",
    )

    amount = excel_xlookup(
        target_order,
        order_ids,
        net_sales,
        if_not_found=0,
    )

    print(f"XLOOKUP salesperson -> {salesperson}")
    print(f"XLOOKUP product -> {product}")
    print(f"XLOOKUP net sales -> {amount:,.2f}")

    missing_order = excel_xlookup(
        "ORD-999",
        order_ids,
        products,
        if_not_found="No matching order",
    )

    print(f"Missing lookup -> {missing_order}")

    # INDEX/MATCH is shown as a conceptual alternative.
    index_match_result = index_match(
        target_order,
        order_ids,
        products,
        if_not_found="Not found",
    )

    print(f"INDEX/MATCH-style result -> {index_match_result}")


# ---------------------------------------------------------------------------
# SECTION 11: APPROXIMATE LOOKUP
# ---------------------------------------------------------------------------

def approximate_lookup_examples() -> None:
    print("\n" + "=" * 80)
    print("ADVANCED: APPROXIMATE XLOOKUP")
    print("=" * 80)

    thresholds = [0, 50_000, 100_000, 250_000, 500_000]
    tiers = [
        "Bronze",
        "Silver",
        "Gold",
        "Platinum",
        "Enterprise",
    ]

    for revenue in [20_000, 75_000, 125_000, 300_000, 750_000]:
        tier = excel_xlookup(
            revenue,
            thresholds,
            tiers,
            if_not_found="No tier",
            match_mode=-1,
        )

        print(f"Revenue {revenue:>8,.0f} -> {tier}")


# ---------------------------------------------------------------------------
# SECTION 12: BUSINESS RULES
# ---------------------------------------------------------------------------

def calculate_commission(record: SalesRecord) -> float:
    """
    Demonstrate combining IF, AND and numerical calculations.

    Completed orders receive commission.
    The rate depends on net sales.
    """
    if record.status != "Completed":
        return 0.0

    if record.net_sales >= 100_000:
        rate = 0.05
    elif record.net_sales >= 50_000:
        rate = 0.03
    else:
        rate = 0.02

    return record.net_sales * rate


def business_rule_examples() -> None:
    print("\n" + "=" * 80)
    print("ADVANCED: BUSINESS RULES")
    print("=" * 80)

    for record in SALES_DATA:
        commission = calculate_commission(record)

        performance = excel_ifs(
            record.net_sales >= 100_000, "High",
            record.net_sales >= 50_000, "Medium",
            True, "Standard",
        )

        print(
            f"{record.order_id} | "
            f"{record.salesperson:<6} | "
            f"Net Sales {record.net_sales:>10,.2f} | "
            f"Performance {performance:<8} | "
            f"Commission {commission:>8,.2f}"
        )


# ---------------------------------------------------------------------------
# SECTION 13: ERROR HANDLING
# ---------------------------------------------------------------------------

def error_handling_examples() -> None:
    print("\n" + "=" * 80)
    print("ADVANCED: IFERROR AND DATA VALIDATION")
    print("=" * 80)

    order_ids = [record.order_id for record in SALES_DATA]
    products = [record.product for record in SALES_DATA]

    safe_lookup = excel_iferror(
        lambda: order_ids.index("ORD-999"),
        "Not found",
    )

    print(f"Safe lookup result -> {safe_lookup}")

    invalid_average = excel_iferror(
        lambda: excel_average([]),
        0,
    )

    print(f"Safe AVERAGE result -> {invalid_average}")

    incomplete_record = {
        "order_id": "ORD-011",
        "region": "",
        "product": "Tablet",
    }

    missing_fields = validate_required_fields(
        incomplete_record,
        ["order_id", "region", "product", "status"],
    )

    print(f"Missing required fields -> {missing_fields}")

    print(
        "EXACT('Excel', 'excel') -> "
        f"{excel_exact('Excel', 'excel')}"
    )

    print(
        "EXACT('Excel', 'Excel') -> "
        f"{excel_exact('Excel', 'Excel')}"
    )

    cleaned = normalize_text("   North    Region   ")

    print(f"Normalized text -> {cleaned}")

    # Avoid unused-variable warnings in environments that inspect locals.
    _ = products


# ---------------------------------------------------------------------------
# SECTION 14: EDGE CASES
# ---------------------------------------------------------------------------

def edge_case_examples() -> None:
    print("\n" + "=" * 80)
    print("EDGE CASES")
    print("=" * 80)

    values = [10, None, "20", 30, "", True, 40]

    print(f"SUM mixed values -> {excel_sum(values)}")

    print(
        "COUNTIF numeric > 20 -> "
        f"{excel_countif([10, 20, 30, 40, 50], '>20')}"
    )

    print(
        "COUNTIF not equal to Completed -> "
        f"{excel_countif(['Completed', 'Pending', 'Cancelled'], '<>Completed')}"
    )

    empty_lookup = excel_xlookup(
        "",
        ["A", "B", ""],
        [100, 200, 300],
        if_not_found="Not found",
    )

    print(f"Lookup blank key -> {empty_lookup}")

    mismatched_result = excel_iferror(
        lambda: excel_sumif(
            ["A", "B"],
            "A",
            [100],
        ),
        "Range size error handled",
    )

    print(f"Mismatched range -> {mismatched_result}")


# ---------------------------------------------------------------------------
# SECTION 15: REPORTING ENGINE
# ---------------------------------------------------------------------------

def generate_sales_report(records: list[SalesRecord]) -> None:
    print("\n" + "=" * 80)
    print("INDUSTRY-STYLE SALES REPORT")
    print("=" * 80)

    total_sales = excel_sum(record.net_sales for record in records)

    completed_records = [
        record
        for record in records
        if record.status == "Completed"
    ]

    completed_sales = excel_sum(
        record.net_sales
        for record in completed_records
    )

    cancelled_count = excel_countif(
        [record.status for record in records],
        "Cancelled",
    )

    average_completed_order = excel_average(
        record.net_sales
        for record in completed_records
    )

    print(f"Total orders: {len(records)}")
    print(f"Completed orders: {len(completed_records)}")
    print(f"Cancelled orders: {cancelled_count}")
    print(f"Total net sales: {total_sales:,.2f}")
    print(f"Completed sales: {completed_sales:,.2f}")
    print(f"Average completed order: {average_completed_order:,.2f}")

    print("\nRegional report:")

    regions = sorted({record.region for record in records})

    for region in regions:
        region_records = [
            record
            for record in records
            if record.region == region
        ]

        region_sales = excel_sum(
            record.net_sales
            for record in region_records
        )

        region_completed_sales = excel_sumifs(
            [record.net_sales for record in records],
            [record.region for record in records],
            region,
            [record.status for record in records],
            "Completed",
        )

        print(
            f"{region:<8} | "
            f"Orders {len(region_records):>2} | "
            f"Sales {region_sales:>12,.2f} | "
            f"Completed Sales {region_completed_sales:>12,.2f}"
        )


# ---------------------------------------------------------------------------
# SECTION 16: PERFORMANCE CONSIDERATIONS
# ---------------------------------------------------------------------------

def performance_demonstration() -> None:
    print("\n" + "=" * 80)
    print("PERFORMANCE CONCEPTS")
    print("=" * 80)

    # A simple linear XLOOKUP scans the lookup array.
    # Average lookup cost is O(n).
    lookup_values = list(range(1, 10_001))
    return_values = [value * 10 for value in lookup_values]

    result = excel_xlookup(
        9_999,
        lookup_values,
        return_values,
        if_not_found=None,
    )

    print(f"Linear XLOOKUP-style search result -> {result}")
    print("Simple linear lookup complexity: O(n)")
    print("Conditional aggregation over n rows: O(n) per criterion set")

    # Dictionary indexing represents a common optimization when many
    # repeated lookups are required.
    indexed_sales = {
        record.order_id: record
        for record in SALES_DATA
    }

    fast_result = indexed_sales.get("ORD-005")

    print(
        "Dictionary-indexed lookup -> "
        f"{fast_result.product if fast_result else 'Not found'}"
    )
    print("Hash-map-style lookup is approximately O(1) average-case.")


# ---------------------------------------------------------------------------
# SECTION 17: FORMULA TRANSLATION TABLE
# ---------------------------------------------------------------------------

def formula_reference() -> None:
    print("\n" + "=" * 80)
    print("EXCEL FORMULA REFERENCE")
    print("=" * 80)

    formulas = {
        "IF": '=IF(A2>=40,"Pass","Fail")',
        "IFS": '=IFS(A2>=90,"A",A2>=80,"B",A2>=70,"C",TRUE,"F")',
        "AND": "=AND(A2>=40,B2>=75)",
        "OR": '=OR(A2="North",A2="South")',
        "NOT": "=NOT(A2=\"Cancelled\")",
        "SUM": "=SUM(B2:B20)",
        "AVERAGE": "=AVERAGE(B2:B20)",
        "SUMIF": '=SUMIF(A2:A20,"North",B2:B20)',
        "SUMIFS": '=SUMIFS(C2:C20,A2:A20,"North",B2:B20,"Completed")',
        "COUNTIF": '=COUNTIF(A2:A20,"Completed")',
        "COUNTIFS": '=COUNTIFS(A2:A20,"North",B2:B20,"Completed")',
        "XLOOKUP": '=XLOOKUP(E2,A2:A20,C2:C20,"Not found")',
        "IFERROR": '=IFERROR(XLOOKUP(E2,A2:A20,C2:C20),"Not found")',
    }

    for function_name, formula in formulas.items():
        print(f"{function_name:<10} {formula}")


# ---------------------------------------------------------------------------
# SECTION 18: MINI TEST SUITE
# ---------------------------------------------------------------------------

def run_tests() -> None:
    print("\n" + "=" * 80)
    print("SELF-TESTS")
    print("=" * 80)

    assert excel_sum([1, 2, 3]) == 6
    assert excel_average([10, 20, 30]) == 20
    assert excel_if(True, "yes", "no") == "yes"
    assert excel_if(False, "yes", "no") == "no"

    assert excel_sumif(
        ["A", "B", "A"],
        "A",
        [10, 20, 30],
    ) == 40

    assert excel_countif(
        ["Completed", "Pending", "Completed"],
        "Completed",
    ) == 2

    assert excel_countif(
        [10, 20, 30, 40],
        ">20",
    ) == 2

    assert excel_xlookup(
        "B",
        ["A", "B", "C"],
        [100, 200, 300],
    ) == 200

    assert excel_xlookup(
        "Z",
        ["A", "B", "C"],
        [100, 200, 300],
        if_not_found="Missing",
    ) == "Missing"

    assert excel_ifs(
        False, "A",
        True, "B",
        True, "C",
    ) == "B"

    print("All tests passed.")


# ---------------------------------------------------------------------------
# SECTION 19: MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 80)
    print("EXCEL FUNCTIONS STUDY PROGRAM")
    print("IF | SUMIF | COUNTIF | XLOOKUP | RELATED FUNCTIONS")
    print("=" * 80)

    beginner_examples()
    grading_examples()
    conditional_aggregation_examples()
    lookup_examples()
    approximate_lookup_examples()
    business_rule_examples()
    error_handling_examples()
    edge_case_examples()
    generate_sales_report(SALES_DATA)
    performance_demonstration()
    formula_reference()
    run_tests()

    print("\n" + "=" * 80)
    print("PROGRAM COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
