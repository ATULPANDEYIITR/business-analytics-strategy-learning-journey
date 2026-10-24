from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from pathlib import Path
from statistics import mean, median
from typing import Iterable
import csv
import json


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"


@dataclass(frozen=True)
class SalesRecord:
    month: str
    region: str
    revenue: float
    orders: int
    marketing_spend: float
    delivery_days: float


@dataclass(frozen=True)
class HistogramBin:
    lower: float
    upper: float
    count: int


@dataclass(frozen=True)
class BoxStatistics:
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    outliers: tuple[float, ...]


class ChartValidationError(ValueError):
    """Raised when chart input violates business-chart requirements."""


def validate_records(records: Iterable[SalesRecord]) -> list[SalesRecord]:
    data = list(records)

    if not data:
        raise ChartValidationError("At least one record is required.")

    for record in data:
        if record.revenue < 0:
            raise ChartValidationError(
                f"Revenue cannot be negative: {record.revenue}"
            )
        if record.orders < 0:
            raise ChartValidationError(
                f"Orders cannot be negative: {record.orders}"
            )
        if record.marketing_spend < 0:
            raise ChartValidationError(
                f"Marketing spend cannot be negative: {record.marketing_spend}"
            )
        if record.delivery_days < 0:
            raise ChartValidationError(
                f"Delivery days cannot be negative: {record.delivery_days}"
            )

    return data


def aggregate_revenue_by_region(
    records: Iterable[SalesRecord],
) -> dict[str, float]:
    totals: dict[str, float] = {}

    for record in validate_records(records):
        totals[record.region] = totals.get(record.region, 0.0) + record.revenue

    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def aggregate_monthly_revenue(
    records: Iterable[SalesRecord],
) -> dict[str, float]:
    totals: dict[str, float] = {}

    for record in validate_records(records):
        totals[record.month] = totals.get(record.month, 0.0) + record.revenue

    return dict(sorted(totals.items()))


def pearson_correlation(
    x_values: list[float],
    y_values: list[float],
) -> float:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise ChartValidationError(
            "Correlation requires equally sized sequences with at least two values."
        )

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )
    denominator = sqrt(
        sum((x - x_mean) ** 2 for x in x_values)
        * sum((y - y_mean) ** 2 for y in y_values)
    )

    if denominator == 0:
        raise ChartValidationError(
            "Correlation is undefined when either variable has zero variance."
        )

    return numerator / denominator


def build_histogram(
    values: Iterable[float],
    bin_width: float,
) -> list[HistogramBin]:
    numbers = list(values)

    if not numbers:
        raise ChartValidationError("Histogram requires at least one value.")
    if bin_width <= 0:
        raise ChartValidationError("Histogram bin width must be positive.")

    minimum = min(numbers)
    maximum = max(numbers)

    if minimum == maximum:
        return [HistogramBin(minimum, minimum + bin_width, len(numbers))]

    bin_count = int((maximum - minimum) / bin_width) + 1
    bins = [0] * bin_count

    for value in numbers:
        index = int((value - minimum) / bin_width)
        if index >= bin_count:
            index = bin_count - 1
        bins[index] += 1

    return [
        HistogramBin(
            lower=minimum + index * bin_width,
            upper=minimum + (index + 1) * bin_width,
            count=count,
        )
        for index, count in enumerate(bins)
    ]


def percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        raise ChartValidationError("Percentile requires data.")
    if not 0 <= fraction <= 1:
        raise ChartValidationError("Percentile fraction must be between 0 and 1.")

    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower

    return (
        sorted_values[lower] * (1 - weight)
        + sorted_values[upper] * weight
    )


def box_statistics(values: Iterable[float]) -> BoxStatistics:
    numbers = sorted(values)

    if not numbers:
        raise ChartValidationError("Box plot requires at least one value.")

    q1 = percentile(numbers, 0.25)
    q2 = percentile(numbers, 0.50)
    q3 = percentile(numbers, 0.75)

    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    outliers = tuple(
        value
        for value in numbers
        if value < lower_fence or value > upper_fence
    )

    non_outliers = [
        value
        for value in numbers
        if lower_fence <= value <= upper_fence
    ]

    return BoxStatistics(
        minimum=min(non_outliers),
        q1=q1,
        median=q2,
        q3=q3,
        maximum=max(non_outliers),
        outliers=outliers,
    )


def render_ascii_bar(data: dict[str, float], width: int = 50) -> str:
    if not data:
        raise ChartValidationError("Bar chart requires data.")

    maximum = max(data.values())
    if maximum <= 0:
        raise ChartValidationError("Bar chart requires at least one positive value.")

    lines = ["BAR CHART - REVENUE BY REGION"]
    for label, value in data.items():
        bar_length = round(value / maximum * width)
        lines.append(f"{label:10} {'#' * bar_length} {value:,.0f}")

    return "\n".join(lines)


def render_ascii_line(data: dict[str, float], width: int = 60) -> str:
    if len(data) < 2:
        raise ChartValidationError("Line chart requires at least two observations.")

    values = list(data.values())
    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return (
            "LINE CHART - MONTHLY REVENUE\n"
            + " -> ".join(f"{label}: {value:,.0f}" for label, value in data.items())
        )

    points = []
    for index, (label, value) in enumerate(data.items()):
        x = index / (len(values) - 1) * width
        y = (value - minimum) / (maximum - minimum)
        points.append((x, y, label, value))

    lines = ["LINE CHART - MONTHLY REVENUE"]
    for x, y, label, value in points:
        lines.append(
            f"{label:10} position={x:5.1f} "
            f"normalized={y:0.3f} value={value:,.0f}"
        )

    return "\n".join(lines)


def render_histogram(histogram: list[HistogramBin]) -> str:
    if not histogram:
        raise ChartValidationError("Histogram requires bins.")

    lines = ["HISTOGRAM - ORDER COUNTS"]
    maximum = max(item.count for item in histogram)

    for item in histogram:
        bar_length = round(item.count / maximum * 45) if maximum else 0
        lines.append(
            f"{item.lower:6.1f}-{item.upper:6.1f} | "
            f"{'*' * bar_length} {item.count}"
        )

    return "\n".join(lines)


def render_box(statistics: BoxStatistics) -> str:
    return (
        "BOX PLOT - DELIVERY DAYS\n"
        f"Minimum : {statistics.minimum:.2f}\n"
        f"Q1      : {statistics.q1:.2f}\n"
        f"Median  : {statistics.median:.2f}\n"
        f"Q3      : {statistics.q3:.2f}\n"
        f"Maximum : {statistics.maximum:.2f}\n"
        f"Outliers: {list(statistics.outliers)}"
    )


def write_csv(records: list[SalesRecord], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "month",
                "region",
                "revenue",
                "orders",
                "marketing_spend",
                "delivery_days",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    record.month,
                    record.region,
                    f"{record.revenue:.2f}",
                    record.orders,
                    f"{record.marketing_spend:.2f}",
                    f"{record.delivery_days:.2f}",
                ]
            )


def write_chart_metrics(records: list[SalesRecord], path: Path) -> None:
    monthly = aggregate_monthly_revenue(records)
    regional = aggregate_revenue_by_region(records)
    deliveries = [record.delivery_days for record in records]
    marketing = [record.marketing_spend for record in records]
    revenue = [record.revenue for record in records]

    payload = {
        "bar": regional,
        "line": monthly,
        "scatter": {
            "x": marketing,
            "y": revenue,
            "pearson_correlation": pearson_correlation(marketing, revenue),
        },
        "histogram": [
            {
                "lower": item.lower,
                "upper": item.upper,
                "count": item.count,
            }
            for item in build_histogram(revenue, 10000)
        ],
        "box": box_statistics(deliveries).__dict__,
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    records = [
        SalesRecord("2026-01", "North", 72000, 410, 11000, 3.2),
        SalesRecord("2026-01", "South", 64000, 390, 9500, 4.1),
        SalesRecord("2026-01", "West", 81000, 450, 12500, 2.8),
        SalesRecord("2026-02", "North", 76000, 425, 11500, 3.4),
        SalesRecord("2026-02", "South", 68000, 402, 10200, 4.0),
        SalesRecord("2026-02", "West", 87000, 478, 13100, 2.6),
        SalesRecord("2026-03", "North", 83000, 440, 12000, 3.6),
        SalesRecord("2026-03", "South", 70000, 410, 10500, 4.4),
        SalesRecord("2026-03", "West", 92000, 495, 13800, 2.9),
        SalesRecord("2026-04", "North", 88000, 462, 12700, 3.5),
        SalesRecord("2026-04", "South", 73000, 421, 10800, 4.2),
        SalesRecord("2026-04", "West", 97000, 510, 14500, 2.7),
        SalesRecord("2026-05", "North", 91000, 475, 13000, 3.8),
        SalesRecord("2026-05", "South", 76000, 430, 11100, 4.5),
        SalesRecord("2026-05", "West", 103000, 535, 15100, 2.5),
        SalesRecord("2026-06", "North", 96000, 490, 13600, 3.7),
        SalesRecord("2026-06", "South", 79000, 442, 11400, 4.3),
        SalesRecord("2026-06", "West", 108000, 552, 15700, 2.8),
        SalesRecord("2026-06", "West", 155000, 600, 22000, 9.5),
    ]

    records = validate_records(records)

    regional = aggregate_revenue_by_region(records)
    monthly = aggregate_monthly_revenue(records)
    histogram = build_histogram([record.revenue for record in records], 20000)
    delivery_box = box_statistics(
        [record.delivery_days for record in records]
    )

    print(render_ascii_bar(regional))
    print()
    print(render_ascii_line(monthly))
    print()
    print(
        "SCATTER ANALYSIS - MARKETING SPEND VS REVENUE\n"
        f"Pearson correlation: "
        f"{pearson_correlation("
        f"[r.marketing_spend for r in records], "
        f"[r.revenue for r in records]):.3f}"
    )
    print()
    print(render_histogram(histogram))
    print()
    print(render_box(delivery_box))

    output_directory = Path("business_chart_output")
    output_directory.mkdir(exist_ok=True)

    write_csv(records, output_directory / "sales_data.csv")
    write_chart_metrics(records, output_directory / "chart_metrics.json")

    assert sum(regional.values()) == sum(record.revenue for record in records)
    assert all(item.count >= 0 for item in histogram)

    print()
    print(f"Data exported to: {output_directory.resolve()}")


if __name__ == "__main__":
    main()
