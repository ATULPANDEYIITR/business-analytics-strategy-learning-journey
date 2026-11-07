#!/usr/bin/env python3
"""
Statistical Analysis: Statistical Calculations Using Python

Features:
- Data validation and cleaning
- Descriptive statistics
- Mean, median, mode, range
- Variance and standard deviation
- Quartiles and percentiles
- Frequency distributions
- Covariance and Pearson correlation
- Simple linear regression
- Confidence intervals
- Outlier detection using IQR
- CSV import and export
- Statistical assertions and error handling

Python standard library only.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


class StatisticalError(Exception):
    """Base exception for statistical operations."""


class InsufficientDataError(StatisticalError):
    """Raised when a calculation requires more observations."""


class InvalidDataError(StatisticalError):
    """Raised when input data is invalid."""


class StatisticalMeasure:
    """Validated statistical calculation service."""

    @staticmethod
    def validate(data: Iterable[float], minimum: int = 1) -> list[float]:
        values = list(data)

        if len(values) < minimum:
            raise InsufficientDataError(
                f"At least {minimum} observations are required."
            )

        for value in values:
            if isinstance(value, bool):
                raise InvalidDataError("Boolean values are not valid observations.")

            if not isinstance(value, (int, float)):
                raise InvalidDataError("All observations must be numeric.")

            if not math.isfinite(value):
                raise InvalidDataError("NaN and infinite values are not permitted.")

        return [float(value) for value in values]

    @staticmethod
    def mean(data: Iterable[float]) -> float:
        values = StatisticalMeasure.validate(data)
        return statistics.fmean(values)

    @staticmethod
    def median(data: Iterable[float]) -> float:
        values = StatisticalMeasure.validate(data)
        return statistics.median(values)

    @staticmethod
    def mode(data: Iterable[float]) -> list[float]:
        values = StatisticalMeasure.validate(data)
        counts = Counter(values)
        highest = max(counts.values())
        return sorted(
            value for value, count in counts.items()
            if count == highest
        )

    @staticmethod
    def variance(data: Iterable[float], sample: bool = True) -> float:
        values = StatisticalMeasure.validate(
            data, minimum=2 if sample else 1
        )
        return statistics.variance(values) if sample else statistics.pvariance(values)

    @staticmethod
    def standard_deviation(
        data: Iterable[float], sample: bool = True
    ) -> float:
        values = StatisticalMeasure.validate(
            data, minimum=2 if sample else 1
        )
        return (
            statistics.stdev(values)
            if sample
            else statistics.pstdev(values)
        )

    @staticmethod
    def percentile(data: Iterable[float], percentage: float) -> float:
        values = StatisticalMeasure.validate(data)

        if not 0 <= percentage <= 100:
            raise ValueError("Percentile must be between 0 and 100.")

        return statistics.quantiles(
            values, n=100, method="inclusive"
        )[int(percentage) - 1] if percentage == 100 else (
            sorted(values)[0] if percentage == 0 else
            statistics.quantiles(
                values, n=100, method="inclusive"
            )[int(percentage) - 1]
            if percentage.is_integer()
            else _interpolated_percentile(values, percentage)
        )

    @staticmethod
    def quartiles(data: Iterable[float]) -> dict[str, float]:
        values = StatisticalMeasure.validate(data)

        q1, q2, q3 = statistics.quantiles(
            values, n=4, method="inclusive"
        )

        return {"Q1": q1, "Q2": q2, "Q3": q3}

    @staticmethod
    def frequency(data: Iterable[float]) -> dict[float, int]:
        values = StatisticalMeasure.validate(data)
        return dict(sorted(Counter(values).items()))

    @staticmethod
    def covariance(x: Iterable[float], y: Iterable[float]) -> float:
        x_values = StatisticalMeasure.validate(x, 2)
        y_values = StatisticalMeasure.validate(y, 2)

        if len(x_values) != len(y_values):
            raise InvalidDataError("Both datasets must have equal lengths.")

        return statistics.covariance(x_values, y_values)

    @staticmethod
    def correlation(x: Iterable[float], y: Iterable[float]) -> float:
        x_values = StatisticalMeasure.validate(x, 2)
        y_values = StatisticalMeasure.validate(y, 2)

        if len(x_values) != len(y_values):
            raise InvalidDataError("Both datasets must have equal lengths.")

        if len(set(x_values)) == 1 or len(set(y_values)) == 1:
            raise InvalidDataError(
                "Correlation is undefined for constant datasets."
            )

        return statistics.correlation(x_values, y_values)

    @staticmethod
    def regression(
        x: Iterable[float], y: Iterable[float]
    ) -> dict[str, float]:
        x_values = StatisticalMeasure.validate(x, 2)
        y_values = StatisticalMeasure.validate(y, 2)

        if len(x_values) != len(y_values):
            raise InvalidDataError("Both datasets must have equal lengths.")

        if len(set(x_values)) == 1:
            raise InvalidDataError(
                "Regression requires variation in independent variable."
            )

        slope, intercept = statistics.linear_regression(
            x_values, y_values
        )

        predictions = [
            slope * value + intercept for value in x_values
        ]

        y_mean = statistics.fmean(y_values)
        total = sum((value - y_mean) ** 2 for value in y_values)
        residual = sum(
            (actual - predicted) ** 2
            for actual, predicted in zip(y_values, predictions)
        )

        r_squared = 1 - residual / total if total else float("nan")

        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
        }

    @staticmethod
    def outliers(data: Iterable[float]) -> list[float]:
        values = StatisticalMeasure.validate(data, 2)
        q1, _, q3 = statistics.quantiles(
            values, n=4, method="inclusive"
        )

        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        return [
            value for value in values
            if value < lower or value > upper
        ]

    @staticmethod
    def mean_confidence_interval(
        data: Iterable[float], z_score: float = 1.96
    ) -> dict[str, float]:
        values = StatisticalMeasure.validate(data, 2)

        if not math.isfinite(z_score) or z_score <= 0:
            raise ValueError("Z-score must be a positive finite number.")

        average = statistics.fmean(values)
        standard_error = statistics.stdev(values) / math.sqrt(len(values))
        margin = z_score * standard_error

        return {
            "mean": average,
            "lower": average - margin,
            "upper": average + margin,
            "standard_error": standard_error,
            "confidence_level": 0.95 if z_score == 1.96 else float("nan"),
        }


def _interpolated_percentile(
    data: Iterable[float], percentage: float
) -> float:
    values = sorted(data)
    position = (len(values) - 1) * percentage / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    fraction = position - lower
    return values[lower] + fraction * (
        values[upper] - values[lower]
    )


@dataclass
class AnalysisReport:
    observations: int
    mean: float
    median: float
    modes: list[float]
    minimum: float
    maximum: float
    range: float
    population_variance: float
    sample_variance: float
    population_std: float
    sample_std: float
    quartiles: dict[str, float]
    frequency: dict[float, int]
    outliers: list[float]
    confidence_interval: dict[str, float]


class StatisticalAnalyzer:
    """Produces a complete descriptive statistical report."""

    def analyze(self, data: Iterable[float]) -> AnalysisReport:
        values = StatisticalMeasure.validate(data, 2)

        return AnalysisReport(
            observations=len(values),
            mean=statistics.fmean(values),
            median=statistics.median(values),
            modes=StatisticalMeasure.mode(values),
            minimum=min(values),
            maximum=max(values),
            range=max(values) - min(values),
            population_variance=statistics.pvariance(values),
            sample_variance=statistics.variance(values),
            population_std=statistics.pstdev(values),
            sample_std=statistics.stdev(values),
            quartiles=StatisticalMeasure.quartiles(values),
            frequency=StatisticalMeasure.frequency(values),
            outliers=StatisticalMeasure.outliers(values),
            confidence_interval=(
                StatisticalMeasure.mean_confidence_interval(values)
            ),
        )


class CSVHandler:
    """Reads and writes numerical datasets."""

    @staticmethod
    def read_column(
        filename: str,
        column: str,
        delimiter: str = ","
    ) -> list[float]:
        path = Path(filename)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        values = []

        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=delimiter)

            if not reader.fieldnames or column not in reader.fieldnames:
                raise InvalidDataError(
                    f"Column '{column}' does not exist."
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    value = float(row[column])

                    if not math.isfinite(value):
                        raise ValueError("Non-finite value")

                    values.append(value)

                except (ValueError, TypeError, KeyError) as error:
                    raise InvalidDataError(
                        f"Invalid value at row {row_number}."
                    ) from error

        return StatisticalMeasure.validate(values, 2)

    @staticmethod
    def export_report(
        report: AnalysisReport,
        filename: str
    ) -> None:
        path = Path(filename)

        with path.open("w", encoding="utf-8") as file:
            json.dump(asdict(report), file, indent=4)


def bootstrap_mean(
    data: Iterable[float],
    iterations: int = 2000,
    seed: int = 42
) -> dict[str, float]:
    """Estimates a percentile bootstrap interval for the mean."""

    values = StatisticalMeasure.validate(data, 2)

    if not isinstance(iterations, int) or isinstance(iterations, bool):
        raise ValueError("Iterations must be an integer.")

    if not 100 <= iterations <= 1_000_000:
        raise ValueError("Iterations must be between 100 and 1,000,000.")

    rng = random.Random(seed)
    estimates = []

    for _ in range(iterations):
        sample = rng.choices(values, k=len(values))
        estimates.append(statistics.fmean(sample))

    estimates.sort()

    return {
        "bootstrap_mean": statistics.fmean(estimates),
        "lower_95": _interpolated_percentile(estimates, 2.5),
        "upper_95": _interpolated_percentile(estimates, 97.5),
        "iterations": iterations,
    }


def run_tests() -> None:
    """Checks core calculations and invalid input handling."""

    values = [10, 20, 20, 30, 40]

    assert StatisticalMeasure.mean(values) == 24
    assert StatisticalMeasure.median(values) == 20
    assert StatisticalMeasure.mode(values) == [20]
    assert StatisticalMeasure.frequency(values)[20.0] == 2

    try:
        StatisticalMeasure.mean([float("nan")])
        raise AssertionError("NaN should be rejected.")
    except InvalidDataError:
        pass

    try:
        StatisticalMeasure.correlation([1, 1], [2, 3])
        raise AssertionError("Constant datasets should be rejected.")
    except InvalidDataError:
        pass

    print("All statistical tests passed.")


def main() -> None:
    print("=" * 65)
    print("STATISTICAL ANALYSIS ENGINE")
    print("=" * 65)

    # Simulated examination scores.
    scores = [
        45, 52, 56, 60, 62, 65, 67, 68,
        70, 72, 72, 75, 78, 80, 82, 85,
        88, 90, 92, 95, 98, 100, 105, 150
    ]

    analyzer = StatisticalAnalyzer()
    report = analyzer.analyze(scores)

    print("\n1. DESCRIPTIVE STATISTICS")
    print(json.dumps(asdict(report), indent=4))

    print("\n2. CORRELATION AND REGRESSION")

    study_hours = [
        1, 2, 2, 3, 3, 4, 4, 5,
        5, 6, 6, 7, 7, 8, 8, 9
    ]

    performance = [
        35, 42, 45, 48, 52, 55, 58, 62,
        65, 68, 70, 74, 77, 81, 85, 90
    ]

    print(
        "Covariance:",
        StatisticalMeasure.covariance(study_hours, performance)
    )

    print(
        "Pearson correlation:",
        StatisticalMeasure.correlation(study_hours, performance)
    )

    regression = StatisticalMeasure.regression(
        study_hours, performance
    )

    print("Regression:", json.dumps(regression, indent=4))

    print("\n3. BOOTSTRAP CONFIDENCE INTERVAL")
    print(json.dumps(bootstrap_mean(scores), indent=4))

    print("\n4. EXPORTING RESULTS")

    output = Path("statistical_report.json")
    CSVHandler.export_report(report, str(output))
    print(f"Report exported to {output.resolve()}")

    print("\n5. VALIDATION")
    run_tests()

    print("\nAnalysis completed successfully.")


if __name__ == "__main__":
    main()
