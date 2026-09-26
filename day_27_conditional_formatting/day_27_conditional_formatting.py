"""
Conditional Formatting: Identifying Trends, Anomalies, and Exceptions

A comprehensive standalone study program covering the ideas behind
conditional formatting and demonstrating them with executable Python.

The program models spreadsheet-style conditional formatting without
requiring an external spreadsheet package. It covers:

1. Fundamental concepts
2. Rule types and precedence
3. Comparisons and threshold rules
4. Formula-style rules
5. Color scales
6. Data bars
7. Duplicate and unique values
8. Blank and error detection
9. Trend detection
10. Statistical anomaly detection
11. Outlier detection using IQR
12. Moving averages
13. Exception detection
14. Rule precedence and conflicts
15. Practical sales-monitoring examples
16. Validation and edge cases
17. Performance considerations
18. A small test suite
19. Exporting formatted results as HTML

The code intentionally separates:
- data
- conditions
- formatting decisions
- analysis
- presentation

That separation mirrors how conditional formatting is implemented
conceptually in spreadsheet and reporting systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from html import escape
from math import isfinite, sqrt
from statistics import mean, median, pstdev
from typing import Any, Callable, Iterable, Optional
import json
import re
import unittest


# ============================================================================
# 1. FUNDAMENTAL DATA TYPES
# ============================================================================

class Severity(Enum):
    """Priority assigned to a conditional-formatting result."""
    NORMAL = 0
    INFORMATION = 1
    WARNING = 2
    CRITICAL = 3


@dataclass(frozen=True)
class FormatStyle:
    """
    Describes visual formatting.

    A real spreadsheet engine may support many more properties:
    font, fill, borders, number formats, icons, alignment, and so on.
    This educational engine concentrates on the most useful properties.
    """
    background: str = ""
    foreground: str = ""
    bold: bool = False
    italic: bool = False
    marker: str = ""


@dataclass
class Cell:
    """Represents one logical spreadsheet cell."""
    value: Any
    row: int
    column: str
    style: FormatStyle = field(default_factory=FormatStyle)
    reasons: list[str] = field(default_factory=list)

    @property
    def address(self) -> str:
        return f"{self.column}{self.row}"


@dataclass
class ConditionalRule:
    """
    A conditional-formatting rule.

    condition:
        Function receiving a Cell and the complete dataset.

    style:
        Style to apply if condition returns True.

    priority:
        Lower number means higher priority.

    stop_if_true:
        If True, lower-priority rules do not override this rule.
    """
    name: str
    condition: Callable[[Cell, list[Cell]], bool]
    style: FormatStyle
    priority: int
    severity: Severity = Severity.INFORMATION
    stop_if_true: bool = False


# ============================================================================
# 2. DATASET CREATION
# ============================================================================

def create_sales_dataset() -> list[dict[str, Any]]:
    """
    Create a realistic monthly sales dataset.

    The dataset deliberately contains:
    - normal values
    - a very high sales value
    - a very low sales value
    - a negative growth value
    - a missing value
    - a duplicate value
    - a target exception

    These make the conditional-formatting examples observable.
    """
    return [
        {"month": "Jan", "sales": 82000, "target": 80000, "growth": 0.04, "returns": 1200},
        {"month": "Feb", "sales": 84500, "target": 81000, "growth": 0.03, "returns": 1300},
        {"month": "Mar", "sales": 87000, "target": 83000, "growth": 0.03, "returns": 1400},
        {"month": "Apr", "sales": 61000, "target": 84000, "growth": -0.30, "returns": 3100},
        {"month": "May", "sales": 89000, "target": 85000, "growth": 0.46, "returns": 1500},
        {"month": "Jun", "sales": 91000, "target": 87000, "growth": 0.02, "returns": 1600},
        {"month": "Jul", "sales": 91000, "target": 88000, "growth": 0.00, "returns": 1700},
        {"month": "Aug", "sales": None, "target": 90000, "growth": None, "returns": 1800},
        {"month": "Sep", "sales": 93000, "target": 92000, "growth": 0.02, "returns": 1900},
        {"month": "Oct", "sales": 210000, "target": 94000, "growth": 1.26, "returns": 2200},
        {"month": "Nov", "sales": 95000, "target": 96000, "growth": -0.55, "returns": 7000},
        {"month": "Dec", "sales": 99000, "target": 98000, "growth": 0.04, "returns": 2000},
    ]


def flatten_dataset(rows: list[dict[str, Any]]) -> list[Cell]:
    """
    Convert selected numeric fields into Cell objects.

    Conditional formatting normally operates cell-by-cell, while
    analytical rules often need the surrounding range.
    """
    cells: list[Cell] = []

    for row_number, row in enumerate(rows, start=2):
        for column, key in (
            ("B", "sales"),
            ("C", "target"),
            ("D", "growth"),
            ("E", "returns"),
        ):
            cells.append(Cell(row[key], row_number, column))

    return cells


# ============================================================================
# 3. BASIC VALUE VALIDATION
# ============================================================================

def is_number(value: Any) -> bool:
    """
    Return True for finite numeric values.

    bool is deliberately excluded because bool is a subclass of int in Python.
    """
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(float(value))
    )


def numeric_values(cells: Iterable[Cell]) -> list[float]:
    """Extract valid numeric values from cells."""
    return [float(cell.value) for cell in cells if is_number(cell.value)]


def safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    """
    Calculate a ratio while explicitly handling division by zero.
    """
    if denominator == 0:
        return None
    return numerator / denominator


# ============================================================================
# 4. BASIC CONDITIONAL-FORMATTING RULES
# ============================================================================

def greater_than(threshold: float) -> Callable[[Cell, list[Cell]], bool]:
    """Create a reusable greater-than rule."""
    def condition(cell: Cell, _: list[Cell]) -> bool:
        return is_number(cell.value) and float(cell.value) > threshold

    return condition


def less_than(threshold: float) -> Callable[[Cell, list[Cell]], bool]:
    """Create a reusable less-than rule."""
    def condition(cell: Cell, _: list[Cell]) -> bool:
        return is_number(cell.value) and float(cell.value) < threshold

    return condition


def between(low: float, high: float) -> Callable[[Cell, list[Cell]], bool]:
    """Create an inclusive range rule."""
    def condition(cell: Cell, _: list[Cell]) -> bool:
        return is_number(cell.value) and low <= float(cell.value) <= high

    return condition


def is_blank(cell: Cell, _: list[Cell]) -> bool:
    """Identify missing or empty values."""
    return cell.value is None or cell.value == ""


# ============================================================================
# 5. DUPLICATE AND UNIQUE VALUE DETECTION
# ============================================================================

def duplicate_condition(cell: Cell, cells: list[Cell]) -> bool:
    """
    Identify duplicated values.

    Missing values are excluded because two blank cells generally represent
    missing information rather than a meaningful duplicate business value.
    """
    if not is_number(cell.value):
        return False

    occurrences = sum(
        1 for other in cells
        if other.column == cell.column and other.value == cell.value
    )
    return occurrences > 1


def unique_condition(cell: Cell, cells: list[Cell]) -> bool:
    """Identify numeric values occurring exactly once."""
    if not is_number(cell.value):
        return False

    occurrences = sum(
        1 for other in cells
        if other.column == cell.column and other.value == cell.value
    )
    return occurrences == 1


# ============================================================================
# 6. STATISTICAL ANOMALY DETECTION
# ============================================================================

def z_score(value: float, values: list[float]) -> Optional[float]:
    """
    Calculate a population z-score.

    z = (x - mean) / standard deviation

    A z-score indicates how many standard deviations a value is away
    from the population mean.

    If every value is identical, standard deviation is zero and a
    z-score cannot be meaningfully calculated.
    """
    if not values:
        return None

    deviation = pstdev(values)

    if deviation == 0:
        return None

    return (value - mean(values)) / deviation


def z_score_condition(
    cells: list[Cell],
    threshold: float = 2.0
) -> Callable[[Cell, list[Cell]], bool]:
    """
    Build a z-score anomaly rule for one column.

    The supplied cells define the reference population.
    """
    values = numeric_values(cells)

    def condition(cell: Cell, _: list[Cell]) -> bool:
        if not is_number(cell.value):
            return False

        score = z_score(float(cell.value), values)
        return score is not None and abs(score) >= threshold

    return condition


# ============================================================================
# 7. IQR OUTLIER DETECTION
# ============================================================================

def quartile(values: list[float], q: float) -> Optional[float]:
    """
    Calculate a percentile using linear interpolation.

    q must be between 0 and 1.
    """
    if not values:
        return None

    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def iqr_bounds(values: list[float]) -> tuple[Optional[float], Optional[float]]:
    """Return Tukey-style lower and upper outlier boundaries."""
    if len(values) < 4:
        return None, None

    q1 = quartile(values, 0.25)
    q3 = quartile(values, 0.75)

    if q1 is None or q3 is None:
        return None, None

    iqr = q3 - q1

    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def iqr_condition(cells: list[Cell]) -> Callable[[Cell, list[Cell]], bool]:
    """Build an IQR-based outlier condition."""
    values = numeric_values(cells)
    lower, upper = iqr_bounds(values)

    def condition(cell: Cell, _: list[Cell]) -> bool:
        if not is_number(cell.value):
            return False

        if lower is None or upper is None:
            return False

        return float(cell.value) < lower or float(cell.value) > upper

    return condition


# ============================================================================
# 8. COLOR SCALES
# ============================================================================

def interpolate_rgb(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    ratio: float
) -> tuple[int, int, int]:
    """
    Interpolate between two RGB colors.

    ratio is clamped to [0, 1].
    """
    ratio = max(0.0, min(1.0, ratio))

    return tuple(
        round(start[index] + (end[index] - start[index]) * ratio)
        for index in range(3)
    )


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple into a CSS hexadecimal color."""
    return "#" + "".join(f"{component:02X}" for component in rgb)


def color_scale(
    value: float,
    minimum: float,
    maximum: float,
    low_color: tuple[int, int, int] = (255, 220, 220),
    high_color: tuple[int, int, int] = (190, 255, 200),
) -> str:
    """
    Generate a continuous color-scale value.

    This is useful for showing magnitude rather than a simple pass/fail state.
    """
    if maximum == minimum:
        return rgb_hex(low_color)

    ratio = (value - minimum) / (maximum - minimum)

    return rgb_hex(interpolate_rgb(low_color, high_color, ratio))


# ============================================================================
# 9. DATA BARS
# ============================================================================

def data_bar_length(value: float, minimum: float, maximum: float, width: int = 20) -> int:
    """
    Convert a numeric value into a proportional bar length.

    A data bar communicates relative magnitude.
    """
    if width <= 0:
        raise ValueError("width must be positive")

    if maximum == minimum:
        return width

    ratio = (value - minimum) / (maximum - minimum)
    ratio = max(0.0, min(1.0, ratio))

    return round(ratio * width)


def render_data_bar(
    value: float,
    minimum: float,
    maximum: float,
    width: int = 20,
    symbol: str = "█",
) -> str:
    """Render a terminal-friendly data bar."""
    filled = data_bar_length(value, minimum, maximum, width)
    return symbol * filled + " " * (width - filled)


# ============================================================================
# 10. TREND DETECTION
# ============================================================================

def moving_average(values: list[Optional[float]], window: int) -> list[Optional[float]]:
    """
    Calculate a trailing moving average.

    None values are skipped. A result is produced only when the window
    contains enough valid observations.

    Example:
        values = [10, 20, 30]
        window = 2
        result = [None, 15, 25]
    """
    if window <= 0:
        raise ValueError("window must be greater than zero")

    result: list[Optional[float]] = []

    for index in range(len(values)):
        start = max(0, index - window + 1)
        window_values = [
            value for value in values[start:index + 1]
            if is_number(value)
        ]

        if len(window_values) < window:
            result.append(None)
        else:
            result.append(mean(window_values))

    return result


def linear_slope(values: list[Optional[float]]) -> Optional[float]:
    """
    Calculate the least-squares slope of a sequence.

    Missing values are ignored, but their original positions are retained.
    """
    points = [
        (index, float(value))
        for index, value in enumerate(values)
        if is_number(value)
    ]

    if len(points) < 2:
        return None

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    denominator = sum((x - x_mean) ** 2 for x in x_values)

    if denominator == 0:
        return None

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in points
    )

    return numerator / denominator


def trend_direction(values: list[Optional[float]]) -> str:
    """
    Classify the overall trend based on regression slope.

    The threshold is intentionally relative to the mean so that the rule
    is less sensitive to absolute scale.
    """
    slope = linear_slope(values)

    valid = [float(value) for value in values if is_number(value)]

    if slope is None or not valid:
        return "insufficient-data"

    average = mean(valid)

    if average == 0:
        return "flat" if abs(slope) < 1e-12 else ("up" if slope > 0 else "down")

    relative_slope = slope / abs(average)

    if relative_slope > 0.01:
        return "up"
    if relative_slope < -0.01:
        return "down"

    return "flat"


# ============================================================================
# 11. EXCEPTION DETECTION
# ============================================================================

def target_exception(row: dict[str, Any]) -> Optional[str]:
    """
    Identify business exceptions.

    The function demonstrates a common conditional-formatting pattern:
    calculate a business condition first, then map it to visual formatting.
    """
    sales = row.get("sales")
    target = row.get("target")

    if sales is None:
        return "Missing sales value"

    if not is_number(sales) or not is_number(target):
        return "Invalid numeric data"

    ratio = safe_ratio(float(sales), float(target))

    if ratio is None:
        return "Target is zero"

    if ratio < 0.80:
        return "Severely below target"

    if ratio < 1.00:
        return "Below target"

    if ratio > 1.50:
        return "Unusually high sales"

    return None


def return_rate_exception(row: dict[str, Any]) -> Optional[str]:
    """Flag unusually high returns relative to sales."""
    sales = row.get("sales")
    returns = row.get("returns")

    if not is_number(sales) or not is_number(returns) or sales == 0:
        return None

    rate = float(returns) / float(sales)

    if rate >= 0.05:
        return f"High return rate: {rate:.1%}"

    return None


# ============================================================================
# 12. RULE ENGINE
# ============================================================================

class ConditionalFormattingEngine:
    """
    Apply conditional-formatting rules using priority order.

    The engine separates:
    - rule definition
    - rule evaluation
    - style selection

    This makes rules easier to test and modify.
    """

    def __init__(self, rules: Iterable[ConditionalRule]):
        self.rules = sorted(rules, key=lambda rule: rule.priority)

    def apply(self, cells: list[Cell]) -> None:
        """
        Apply rules to cells.

        Every matching rule contributes a reason.
        The first applicable style becomes the visual style unless
        a higher-priority rule has already stopped evaluation.
        """
        for cell in cells:
            style_selected = False

            for rule in self.rules:
                try:
                    matched = rule.condition(cell, cells)
                except (TypeError, ValueError, ZeroDivisionError):
                    matched = False

                if not matched:
                    continue

                cell.reasons.append(rule.name)

                if not style_selected:
                    cell.style = rule.style
                    style_selected = True

                if rule.stop_if_true:
                    break


# ============================================================================
# 13. RULE FACTORIES
# ============================================================================

CRITICAL = FormatStyle(
    background="#8B0000",
    foreground="#FFFFFF",
    bold=True,
    marker="CRITICAL",
)

WARNING = FormatStyle(
    background="#FFD966",
    foreground="#000000",
    bold=True,
    marker="WARNING",
)

INFO = FormatStyle(
    background="#D9EAF7",
    foreground="#000000",
    marker="INFO",
)

SUCCESS = FormatStyle(
    background="#D9EAD3",
    foreground="#000000",
    marker="GOOD",
)

NEUTRAL = FormatStyle(
    background="#FFFFFF",
    foreground="#000000",
    marker="NORMAL",
)


# ============================================================================
# 14. COLUMN-SPECIFIC RULES
# ============================================================================

def build_sales_rules(rows: list[dict[str, Any]]) -> list[ConditionalRule]:
    """Build a rule set for the sales column."""
    sales_cells = [
        cell for cell in flatten_dataset(rows)
        if cell.column == "B"
    ]

    return [
        ConditionalRule(
            name="Missing sales",
            condition=is_blank,
            style=CRITICAL,
            priority=1,
            severity=Severity.CRITICAL,
            stop_if_true=True,
        ),
        ConditionalRule(
            name="Sales statistical anomaly",
            condition=z_score_condition(sales_cells, threshold=2.0),
            style=WARNING,
            priority=2,
            severity=Severity.WARNING,
        ),
        ConditionalRule(
            name="Sales IQR outlier",
            condition=iqr_condition(sales_cells),
            style=WARNING,
            priority=3,
            severity=Severity.WARNING,
        ),
        ConditionalRule(
            name="Sales below minimum",
            condition=less_than(70000),
            style=WARNING,
            priority=4,
            severity=Severity.WARNING,
        ),
        ConditionalRule(
            name="Sales above target range",
            condition=greater_than(100000),
            style=INFO,
            priority=5,
            severity=Severity.INFORMATION,
        ),
    ]


# ============================================================================
# 15. REPORTING UTILITIES
# ============================================================================

def format_value(value: Any) -> str:
    """Format values consistently for terminal output."""
    if value is None:
        return "MISSING"

    if isinstance(value, float):
        if abs(value) < 1:
            return f"{value:.1%}"
        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def print_rule_report(cells: list[Cell]) -> None:
    """Print a detailed conditional-formatting report."""
    print("\n" + "=" * 92)
    print("CONDITIONAL FORMATTING RULE REPORT")
    print("=" * 92)

    print(
        f"{'Cell':<7}"
        f"{'Value':>14}"
        f"{'Style':<12}"
        f"{'Rules Triggered':<50}"
    )
    print("-" * 92)

    for cell in cells:
        reasons = ", ".join(cell.reasons) if cell.reasons else "None"
        marker = cell.style.marker or "NORMAL"

        print(
            f"{cell.address:<7}"
            f"{format_value(cell.value):>14}"
            f"{marker:<12}"
            f"{reasons:<50}"
        )


def print_data_bars(rows: list[dict[str, Any]]) -> None:
    """Display sales magnitude using text data bars."""
    sales = [
        float(row["sales"])
        for row in rows
        if is_number(row["sales"])
    ]

    minimum = min(sales)
    maximum = max(sales)

    print("\n" + "=" * 92)
    print("DATA BARS: RELATIVE SALES MAGNITUDE")
    print("=" * 92)

    for row in rows:
        value = row["sales"]

        if not is_number(value):
            print(f"{row['month']:>3} | MISSING")
            continue

        bar = render_data_bar(float(value), minimum, maximum, 30)

        print(
            f"{row['month']:>3} | "
            f"{bar} "
            f"{float(value):>10,.0f}"
        )


def print_color_scale(rows: list[dict[str, Any]]) -> None:
    """Display the numeric color-scale classification."""
    values = [
        float(row["sales"])
        for row in rows
        if is_number(row["sales"])
    ]

    minimum = min(values)
    maximum = max(values)

    print("\n" + "=" * 92)
    print("COLOR SCALE")
    print("=" * 92)

    for row in rows:
        value = row["sales"]

        if not is_number(value):
            print(f"{row['month']:>3} | MISSING")
            continue

        color = color_scale(float(value), minimum, maximum)

        print(
            f"{row['month']:>3} | "
            f"{float(value):>10,.0f} | "
            f"{color}"
        )


# ============================================================================
# 16. HTML CONDITIONAL-FORMATTING EXPORT
# ============================================================================

def html_style(style: FormatStyle) -> str:
    """Convert FormatStyle into inline CSS."""
    properties = []

    if style.background:
        properties.append(f"background:{style.background}")

    if style.foreground:
        properties.append(f"color:{style.foreground}")

    if style.bold:
        properties.append("font-weight:bold")

    if style.italic:
        properties.append("font-style:italic")

    return ";".join(properties)


def generate_html_report(
    rows: list[dict[str, Any]],
    output_file: str = "conditional_formatting_report.html",
) -> None:
    """
    Generate a browser-readable report.

    HTML is used here because it allows the conditional-formatting concepts
    to be visually demonstrated without depending on spreadsheet software.
    """
    sales_values = [
        float(row["sales"])
        for row in rows
        if is_number(row["sales"])
    ]

    minimum = min(sales_values)
    maximum = max(sales_values)

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Conditional Formatting Report</title>",
        "<style>",
        "body{font-family:Arial,sans-serif;background:#111;color:#eee;padding:24px}",
        "table{border-collapse:collapse;width:100%;max-width:1100px}",
        "th,td{border:1px solid #444;padding:10px;text-align:right}",
        "th{background:#222}",
        "td:first-child,th:first-child{text-align:left}",
        ".bar{height:12px;background:#4caf50}",
        ".bar-container{background:#333;width:180px}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Conditional Formatting Report</h1>",
        "<table>",
        "<tr><th>Month</th><th>Sales</th><th>Target</th><th>Growth</th>"
        "<th>Returns</th><th>Exception</th><th>Magnitude</th></tr>",
    ]

    for row in rows:
        exception = target_exception(row)
        exception_text = exception or "None"

        sales = row["sales"]

        if is_number(sales):
            ratio = (
                (float(sales) - minimum) / (maximum - minimum)
                if maximum != minimum
                else 1
            )
            width = max(0, min(100, ratio * 100))
            bar_html = (
                "<div class='bar-container'>"
                f"<div class='bar' style='width:{width:.1f}%'></div>"
                "</div>"
            )
            color = color_scale(float(sales), minimum, maximum)
            sales_style = f"background:{color}"
            sales_display = f"{float(sales):,.0f}"
        else:
            bar_html = "MISSING"
            sales_style = "background:#8B0000;color:white;font-weight:bold"
            sales_display = "MISSING"

        html_parts.append(
            "<tr>"
            f"<td>{escape(str(row['month']))}</td>"
            f"<td style='{sales_style}'>{escape(sales_display)}</td>"
            f"<td>{float(row['target']):,.0f}</td>"
            f"<td>{escape(format_value(row['growth']))}</td>"
            f"<td>{float(row['returns']):,.0f}</td>"
            f"<td>{escape(exception_text)}</td>"
            f"<td>{bar_html}</td>"
            "</tr>"
        )

    html_parts.extend([
        "</table>",
        "</body>",
        "</html>",
    ])

    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(html_parts))

    print(f"\nHTML report written to: {output_file}")


# ============================================================================
# 17. TREND ANALYSIS REPORT
# ============================================================================

def print_trend_report(rows: list[dict[str, Any]]) -> None:
    """Show moving averages, slopes, and trend classifications."""
    sales = [row["sales"] for row in rows]

    average_3 = moving_average(sales, 3)
    direction = trend_direction(sales)
    slope = linear_slope(sales)

    print("\n" + "=" * 92)
    print("TREND ANALYSIS")
    print("=" * 92)
    print(f"Overall trend: {direction}")
    print(f"Regression slope: {slope:.2f}" if slope is not None else "Regression slope: unavailable")
    print("\n3-period moving average:")

    for row, average_value in zip(rows, average_3):
        display_average = (
            f"{average_value:,.2f}"
            if average_value is not None
            else "insufficient data"
        )

        print(
            f"{row['month']:>3} | "
            f"sales={format_value(row['sales']):>10} | "
            f"MA3={display_average}"
        )


# ============================================================================
# 18. EXCEPTION REPORT
# ============================================================================

def print_exception_report(rows: list[dict[str, Any]]) -> None:
    """Print business-level exceptions."""
    print("\n" + "=" * 92)
    print("BUSINESS EXCEPTION REPORT")
    print("=" * 92)

    found_exception = False

    for row in rows:
        exceptions = []

        target_problem = target_exception(row)
        return_problem = return_rate_exception(row)

        if target_problem:
            exceptions.append(target_problem)

        if return_problem:
            exceptions.append(return_problem)

        if exceptions:
            found_exception = True
            print(
                f"{row['month']:>3}: "
                + " | ".join(exceptions)
            )

    if not found_exception:
        print("No exceptions detected.")


# ============================================================================
# 19. ADVANCED: RULE PRECEDENCE DEMONSTRATION
# ============================================================================

def demonstrate_precedence() -> None:
    """
    Demonstrate why rule order matters.

    A missing value should normally be more important than a generic
    formatting rule. The critical rule therefore has priority 1 and
    stop_if_true=True.
    """
    cells = [
        Cell(None, 2, "B"),
        Cell(50000, 3, "B"),
        Cell(150000, 4, "B"),
    ]

    rules = [
        ConditionalRule(
            name="Missing",
            condition=is_blank,
            style=CRITICAL,
            priority=1,
            severity=Severity.CRITICAL,
            stop_if_true=True,
        ),
        ConditionalRule(
            name="Low",
            condition=less_than(70000),
            style=WARNING,
            priority=2,
            severity=Severity.WARNING,
        ),
        ConditionalRule(
            name="High",
            condition=greater_than(100000),
            style=INFO,
            priority=3,
            severity=Severity.INFORMATION,
        ),
    ]

    ConditionalFormattingEngine(rules).apply(cells)

    print("\n" + "=" * 92)
    print("RULE PRECEDENCE DEMONSTRATION")
    print("=" * 92)

    for cell in cells:
        print(
            f"{cell.address}: value={format_value(cell.value):>10} | "
            f"style={cell.style.marker:<8} | "
            f"rules={cell.reasons}"
        )


# ============================================================================
# 20. ADVANCED: PERCENTILE-BASED FLAGGING
# ============================================================================

def percentile_flag(
    values: list[float],
    value: float,
    lower_percentile: float = 0.10,
    upper_percentile: float = 0.90,
) -> str:
    """
    Classify a value relative to empirical percentile boundaries.

    This can be useful when fixed business thresholds are not appropriate.
    """
    if not values:
        return "insufficient-data"

    if not 0 <= lower_percentile <= 1:
        raise ValueError("lower_percentile must be between 0 and 1")

    if not 0 <= upper_percentile <= 1:
        raise ValueError("upper_percentile must be between 0 and 1")

    if lower_percentile > upper_percentile:
        raise ValueError("lower percentile cannot exceed upper percentile")

    lower = quartile(values, lower_percentile)
    upper = quartile(values, upper_percentile)

    if lower is None or upper is None:
        return "insufficient-data"

    if value < lower:
        return "low"

    if value > upper:
        return "high"

    return "normal"


# ============================================================================
# 21. JSON EXPORT
# ============================================================================

def export_analysis_json(rows: list[dict[str, Any]]) -> str:
    """
    Produce machine-readable analysis results.

    This illustrates how conditional-formatting decisions can become
    part of a larger reporting pipeline rather than remaining visual only.
    """
    sales = [
        float(row["sales"])
        for row in rows
        if is_number(row["sales"])
    ]

    lower, upper = iqr_bounds(sales)

    result = []

    for row in rows:
        sales_value = row["sales"]

        if is_number(sales_value):
            z = z_score(float(sales_value), sales)
            percentile_class = percentile_flag(sales, float(sales_value))

            if lower is not None and upper is not None:
                iqr_outlier = (
                    float(sales_value) < lower
                    or float(sales_value) > upper
                )
            else:
                iqr_outlier = False
        else:
            z = None
            percentile_class = "missing"
            iqr_outlier = False

        result.append({
            "month": row["month"],
            "sales": sales_value,
            "target": row["target"],
            "growth": row["growth"],
            "target_exception": target_exception(row),
            "return_exception": return_rate_exception(row),
            "z_score": z,
            "iqr_outlier": iqr_outlier,
            "percentile_class": percentile_class,
        })

    return json.dumps(result, indent=2)


# ============================================================================
# 22. TESTS
# ============================================================================

class ConditionalFormattingTests(unittest.TestCase):
    """Focused tests for important analytical behaviors."""

    def test_safe_ratio_zero_denominator(self) -> None:
        self.assertIsNone(safe_ratio(10, 0))

    def test_moving_average(self) -> None:
        values = [10, 20, 30, 40]
        self.assertEqual(
            moving_average(values, 2),
            [None, 15, 25, 35],
        )

    def test_missing_value(self) -> None:
        cell = Cell(None, 2, "B")
        self.assertTrue(is_blank(cell, []))

    def test_duplicate_detection(self) -> None:
        cells = [
            Cell(100, 2, "B"),
            Cell(100, 3, "B"),
            Cell(200, 4, "B"),
        ]

        self.assertTrue(duplicate_condition(cells[0], cells))
        self.assertFalse(duplicate_condition(cells[2], cells))

    def test_color_scale_clamps(self) -> None:
        self.assertEqual(
            color_scale(100, 0, 100),
            "#BEFFC8",
        )

    def test_invalid_percentile_order(self) -> None:
        with self.assertRaises(ValueError):
            percentile_flag([1, 2, 3], 2, 0.9, 0.1)

    def test_target_exception(self) -> None:
        row = {
            "sales": 50000,
            "target": 100000,
        }

        self.assertEqual(
            target_exception(row),
            "Severely below target",
        )


def run_tests() -> None:
    """Run the internal test suite."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ConditionalFormattingTests
    )

    result = unittest.TextTestRunner(verbosity=1).run(suite)

    if not result.wasSuccessful():
        raise SystemExit("One or more tests failed.")


# ============================================================================
# 23. MAIN STUDY PROGRAM
# ============================================================================

def main() -> None:
    rows = create_sales_dataset()

    print("=" * 92)
    print("CONDITIONAL FORMATTING STUDY PROGRAM")
    print("Identifying Trends, Anomalies, and Exceptions")
    print("=" * 92)

    # ------------------------------------------------------------------------
    # Basic data display
    # ------------------------------------------------------------------------
    print("\nRAW DATA")
    print("-" * 92)

    for row in rows:
        print(
            f"{row['month']:>3} | "
            f"sales={format_value(row['sales']):>10} | "
            f"target={format_value(row['target']):>10} | "
            f"growth={format_value(row['growth']):>8} | "
            f"returns={format_value(row['returns']):>8}"
        )

    # ------------------------------------------------------------------------
    # Apply conditional formatting to sales cells
    # ------------------------------------------------------------------------
    sales_cells = [
        cell for cell in flatten_dataset(rows)
        if cell.column == "B"
    ]

    sales_rules = build_sales_rules(rows)
    ConditionalFormattingEngine(sales_rules).apply(sales_cells)

    print_rule_report(sales_cells)

    # ------------------------------------------------------------------------
    # Data bars
    # ------------------------------------------------------------------------
    print_data_bars(rows)

    # ------------------------------------------------------------------------
    # Color scales
    # ------------------------------------------------------------------------
    print_color_scale(rows)

    # ------------------------------------------------------------------------
    # Trend analysis
    # ------------------------------------------------------------------------
    print_trend_report(rows)

    # ------------------------------------------------------------------------
    # Business exceptions
    # ------------------------------------------------------------------------
    print_exception_report(rows)

    # ------------------------------------------------------------------------
    # Rule precedence
    # ------------------------------------------------------------------------
    demonstrate_precedence()

    # ------------------------------------------------------------------------
    # JSON output
    # ------------------------------------------------------------------------
    print("\n" + "=" * 92)
    print("MACHINE-READABLE ANALYSIS")
    print("=" * 92)

    analysis_json = export_analysis_json(rows)

    # Print only the first part to keep terminal output manageable.
    print(analysis_json[:2500])

    if len(analysis_json) > 2500:
        print("...")

    # ------------------------------------------------------------------------
    # Generate browser-readable report
    # ------------------------------------------------------------------------
    generate_html_report(rows)

    # ------------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------------
    print("\n" + "=" * 92)
    print("RUNNING TESTS")
    print("=" * 92)

    run_tests()

    print("\nAll demonstrations and tests completed successfully.")


if __name__ == "__main__":
    main()
