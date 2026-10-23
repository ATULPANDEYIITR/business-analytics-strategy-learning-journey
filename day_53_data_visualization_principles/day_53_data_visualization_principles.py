from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
import csv
import json
import statistics
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DataPoint:
    category: str
    value: float
    secondary: float | None = None


@dataclass(frozen=True)
class ChartRecommendation:
    chart: str
    score: float
    purpose: str
    reason: str
    warnings: tuple[str, ...]


class VisualizationError(ValueError):
    """Raised when data cannot support a meaningful visualization."""


class DataValidator:
    """Validates analytical data before chart selection."""

    @staticmethod
    def numeric(values: Sequence[float], name: str = "values") -> list[float]:
        if not values:
            raise VisualizationError(f"{name} cannot be empty.")

        cleaned: list[float] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VisualizationError(f"{name} contains a non-numeric value.")
            if value != value:
                raise VisualizationError(f"{name} contains NaN.")
            if value in (float("inf"), float("-inf")):
                raise VisualizationError(f"{name} contains an infinite value.")
            cleaned.append(float(value))
        return cleaned

    @staticmethod
    def paired(
        categories: Sequence[str], values: Sequence[float]
    ) -> tuple[list[str], list[float]]:
        if len(categories) != len(values):
            raise VisualizationError("Categories and values must have equal lengths.")
        if not categories:
            raise VisualizationError("At least one observation is required.")

        normalized = [str(category).strip() for category in categories]
        if any(not category for category in normalized):
            raise VisualizationError("Categories cannot be empty.")

        return normalized, DataValidator.numeric(values)

    @staticmethod
    def matrix(matrix: Sequence[Sequence[float]]) -> list[list[float]]:
        if not matrix or any(not row for row in matrix):
            raise VisualizationError("Matrix must contain non-empty rows.")

        width = len(matrix[0])
        if any(len(row) != width for row in matrix):
            raise VisualizationError("All matrix rows must have equal length.")

        return [DataValidator.numeric(row, "matrix row") for row in matrix]


def summarize(values: Sequence[float]) -> dict[str, float]:
    values = DataValidator.numeric(values)
    ordered = sorted(values)
    return {
        "count": float(len(values)),
        "minimum": min(values),
        "maximum": max(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "standard_deviation": statistics.pstdev(values),
        "range": max(values) - min(values),
        "coefficient_of_variation": (
            statistics.pstdev(values) / statistics.fmean(values)
            if statistics.fmean(values) != 0
            else 0.0
        ),
        "first_quartile": statistics.quantiles(
            ordered, n=4, method="inclusive"
        )[0]
        if len(values) >= 2
        else ordered[0],
        "third_quartile": statistics.quantiles(
            ordered, n=4, method="inclusive"
        )[2]
        if len(values) >= 2
        else ordered[0],
    }


def choose_chart(
    *,
    purpose: str,
    categories: Sequence[str] | None = None,
    values: Sequence[float] | None = None,
    x: Sequence[float] | None = None,
    y: Sequence[float] | None = None,
    time_ordered: bool = False,
    parts_of_whole: bool = False,
    distribution: bool = False,
    matrix_data: Sequence[Sequence[float]] | None = None,
) -> list[ChartRecommendation]:
    """
    Selects charts by matching analytical intent to data structure.

    The scoring rules deliberately favor charts that expose the intended
    comparison or relationship with the least visual interpretation cost.
    """
    purpose = purpose.lower().strip()
    recommendations: list[ChartRecommendation] = []

    if categories is not None and values is not None:
        categories, values = DataValidator.paired(categories, values)
        unique_categories = len(set(categories))

        if purpose in {"comparison", "ranking"}:
            score = 0.95
            if unique_categories > 20:
                score -= 0.15
            recommendations.append(
                ChartRecommendation(
                    "horizontal bar chart",
                    score,
                    "compare categories",
                    "Position and length make category differences easy to compare.",
                    (
                        "Sort categories when ranking is important.",
                        "Avoid excessive categories because labels become difficult to read.",
                    ),
                )
            )
            recommendations.append(
                ChartRecommendation(
                    "dot plot",
                    0.90,
                    "compare precise values",
                    "Dots reduce visual ink while preserving a common position scale.",
                    ("Use direct labels when the number of categories is small.",),
                )
            )
            if unique_categories <= 8:
                recommendations.append(
                    ChartRecommendation(
                        "column chart",
                        0.78,
                        "compare a small number of categories",
                        "Vertical bars work when category labels are short and the category count is limited.",
                        ("Avoid 3D columns and decorative effects.",),
                    )
                )

        if parts_of_whole:
            warnings: list[str] = []
            if any(value < 0 for value in values):
                warnings.append("Negative values cannot represent parts of a whole.")
            if sum(values) <= 0:
                warnings.append("The total must be positive.")
            recommendations.append(
                ChartRecommendation(
                    "100% stacked bar chart",
                    0.94 if not warnings else 0.30,
                    "show composition",
                    "A common baseline makes component proportions easier to compare.",
                    tuple(warnings)
                    or ("Use a limited number of components.",),
                )
            )
            recommendations.append(
                ChartRecommendation(
                    "pie chart",
                    0.58 if unique_categories <= 5 and not warnings else 0.25,
                    "show simple composition",
                    "Angles and areas communicate broad part-to-whole differences.",
                    (
                        "Keep the number of slices small.",
                        "Do not use a pie chart when precise comparison matters.",
                    )
                    + tuple(warnings),
                )
            )

        if distribution:
            recommendations.append(
                ChartRecommendation(
                    "histogram",
                    0.96,
                    "show the distribution of a numeric variable",
                    "Binning reveals concentration, spread, skewness, and possible outliers.",
                    (
                        "Bin width affects the visible pattern.",
                        "Do not interpret bins as categorical groups.",
                    ),
                )
            )
            recommendations.append(
                ChartRecommendation(
                    "box plot",
                    0.92,
                    "compare distributions",
                    "Quartiles and extreme observations remain visible without requiring many bins.",
                    (
                        "A box plot hides some distribution shape.",
                        "Use multiple boxes when comparing groups.",
                    ),
                )
            )

    if x is not None and y is not None:
        x = DataValidator.numeric(x, "x")
        y = DataValidator.numeric(y, "y")
        if len(x) != len(y):
            raise VisualizationError("x and y must contain the same number of values.")

        correlation = _correlation(x, y)
        recommendations.append(
            ChartRecommendation(
                "scatter plot",
                0.98,
                "show a relationship between two numeric variables",
                f"Each observation remains visible and supports relationship and outlier analysis; correlation is {correlation:.3f}.",
                (
                    "Correlation does not establish causation.",
                    "Use transparency or aggregation for very dense datasets.",
                ),
            )
        )

        if time_ordered:
            recommendations.append(
                ChartRecommendation(
                    "line chart",
                    0.93,
                    "show change over ordered observations",
                    "Connected positions emphasize sequence and trend.",
                    (
                        "Only connect observations when the ordering has meaningful continuity.",
                    ),
                )
            )

    if time_ordered and values is not None:
        values = DataValidator.numeric(values)
        recommendations.append(
            ChartRecommendation(
                "line chart",
                0.97,
                "show temporal change",
                "The continuous path makes direction, turning points, and rate of change visible.",
                (
                    "Keep the time axis chronologically ordered.",
                    "Do not connect unrelated categorical observations.",
                ),
            )
        )
        if len(values) >= 4:
            recommendations.append(
                ChartRecommendation(
                    "area chart",
                    0.70,
                    "emphasize magnitude across time",
                    "Filled area can emphasize accumulated visual mass.",
                    (
                        "Avoid overlapping areas when series are numerous.",
                        "A line chart is usually better for precise comparisons.",
                    ),
                )
            )

    if matrix_data is not None:
        matrix_data = DataValidator.matrix(matrix_data)
        if len(matrix_data) > 1 and len(matrix_data[0]) > 1:
            recommendations.append(
                ChartRecommendation(
                    "heatmap",
                    0.97,
                    "show patterns across two categorical dimensions",
                    "Color intensity provides a compact representation of a rectangular matrix.",
                    (
                        "Use a perceptually ordered color scale.",
                        "Annotate cells when exact values matter.",
                    ),
                )
            )

    if not recommendations:
        raise VisualizationError(
            "Insufficient information to choose a chart. Specify an analytical "
            "purpose and provide compatible data."
        )

    return sorted(recommendations, key=lambda item: item.score, reverse=True)


def _correlation(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) < 2:
        return 0.0

    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denominator_x = sqrt(sum((a - mean_x) ** 2 for a in x))
    denominator_y = sqrt(sum((b - mean_y) ** 2 for b in y))

    if denominator_x == 0 or denominator_y == 0:
        return 0.0

    return numerator / (denominator_x * denominator_y)


def ascii_bar_chart(categories: Sequence[str], values: Sequence[float]) -> str:
    """
    A dependency-free rendering used to inspect the selected structure.

    It intentionally uses bars rather than pretending that terminal output
    is a substitute for a production visualization library.
    """
    categories, values = DataValidator.paired(categories, values)
    maximum = max(values)
    minimum = min(values)
    span = maximum - minimum

    lines = ["Category comparison"]
    for category, value in zip(categories, values):
        normalized = 0 if span == 0 else (value - minimum) / span
        width = max(1, round(normalized * 40))
        lines.append(f"{category:<18} {value:>8.2f} | {'#' * width}")
    return "\n".join(lines)


def export_recommendations(
    recommendations: Iterable[ChartRecommendation], path: str
) -> None:
    """Writes machine-readable recommendations without executing arbitrary code."""
    output = [
        {
            "chart": item.chart,
            "score": item.score,
            "purpose": item.purpose,
            "reason": item.reason,
            "warnings": list(item.warnings),
        }
        for item in recommendations
    ]

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )


def load_sales_csv(path: str) -> tuple[list[str], list[float]]:
    """
    Loads only the two expected columns from a trusted analytical CSV.

    No formula evaluation or dynamic code execution is performed, which keeps
    imported data inert.
    """
    categories: list[str] = []
    values: list[float] = []

    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"category", "value"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise VisualizationError(
                "CSV must contain category and value columns."
            )

        for row in reader:
            categories.append(row["category"])
            try:
                values.append(float(row["value"]))
            except (TypeError, ValueError) as exc:
                raise VisualizationError(
                    f"Invalid numeric value for category {row['category']!r}."
                ) from exc

    return DataValidator.paired(categories, values)


def demonstrate() -> None:
    # Scenario: an operations team needs to compare quarterly service demand.
    categories = ["Cloud", "Security", "Data", "Networking", "Applications"]
    values = [1840, 1320, 1610, 940, 2110]

    print("DATA SUMMARY")
    summary = summarize(values)
    for key, value in summary.items():
        print(f"{key:>24}: {value:.3f}")

    print("\nRECOMMENDED STRUCTURES")
    recommendations = choose_chart(
        purpose="ranking",
        categories=categories,
        values=values,
    )
    for recommendation in recommendations:
        print(
            f"{recommendation.chart:<24} "
            f"score={recommendation.score:.2f} | "
            f"{recommendation.reason}"
        )

    print("\nTERMINAL PREVIEW")
    print(ascii_bar_chart(categories, values))

    print("\nRELATIONSHIP EXAMPLE")
    hours = [12, 18, 21, 27, 30, 35, 41, 48]
    defects = [17, 15, 14, 12, 11, 9, 8, 6]
    relationship = choose_chart(x=hours, y=defects)
    print(
        f"{relationship[0].chart}: "
        f"{relationship[0].reason}"
    )

    print("\nCOMPOSITION CHECK")
    composition = choose_chart(
        purpose="composition",
        categories=["Product", "Support", "Operations", "Other"],
        values=[52, 21, 17, 10],
        parts_of_whole=True,
    )
    for recommendation in composition[:2]:
        print(
            f"{recommendation.chart}: "
            f"{'valid' if not recommendation.warnings else recommendation.warnings}"
        )

    print("\nMATRIX EXAMPLE")
    heatmap = choose_chart(
        purpose="pattern",
        matrix_data=[
            [92, 84, 76],
            [71, 88, 94],
            [63, 79, 91],
            [55, 68, 83],
        ],
    )
    print(f"{heatmap[0].chart}: {heatmap[0].reason}")

    # Uncomment when a writable destination is appropriate:
    # export_recommendations(recommendations, "chart_recommendations.json")


if __name__ == "__main__":
    demonstrate()
