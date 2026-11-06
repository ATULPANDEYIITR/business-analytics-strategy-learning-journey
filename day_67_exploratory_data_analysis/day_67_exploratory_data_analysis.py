#!/usr/bin/env python3
"""
Exploratory Data Analysis (EDA)
Analyze datasets programmatically using Python's standard library.

Features:
- Dataset loading and validation
- Data profiling and type inference
- Missing-value and duplicate analysis
- Descriptive statistics
- Distribution and outlier detection
- Categorical frequency analysis
- Correlation analysis
- Grouped analysis
- Data-quality assessment
- CSV report generation
- Reproducible execution
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class EDAError(Exception):
    """Base exception for EDA operations."""


class DatasetValidationError(EDAError):
    """Raised when dataset structure or content is invalid."""


class DatasetLoadError(EDAError):
    """Raised when a dataset cannot be loaded."""


@dataclass
class ColumnProfile:
    name: str
    inferred_type: str
    total: int
    missing: int
    unique: int
    statistics: dict[str, Any] = field(default_factory=dict)
    frequencies: dict[str, int] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    rows: int
    columns: int
    duplicate_rows: int
    column_profiles: list[ColumnProfile]
    correlations: dict[str, float]
    quality_issues: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": datetime.now().isoformat(),
            "dataset": {
                "rows": self.rows,
                "columns": self.columns,
                "duplicate_rows": self.duplicate_rows,
            },
            "columns": [
                {
                    "name": p.name,
                    "type": p.inferred_type,
                    "total": p.total,
                    "missing": p.missing,
                    "unique": p.unique,
                    "statistics": p.statistics,
                    "frequencies": p.frequencies,
                }
                for p in self.column_profiles
            ],
            "correlations": self.correlations,
            "quality_issues": self.quality_issues,
        }


class Dataset:
    """Stores and validates tabular records."""

    def __init__(self, headers: list[str], rows: list[dict[str, Any]]):
        if not headers:
            raise DatasetValidationError("Dataset has no columns.")

        if len(headers) != len(set(headers)):
            raise DatasetValidationError("Column names must be unique.")

        if any(not h.strip() for h in headers):
            raise DatasetValidationError("Column names cannot be empty.")

        self.headers = headers
        self.rows = rows

        for index, row in enumerate(rows):
            if set(row.keys()) != set(headers):
                raise DatasetValidationError(
                    f"Inconsistent columns in row {index + 1}."
                )

    @classmethod
    def from_csv(cls, path: Path) -> "Dataset":
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise DatasetLoadError("CSV has no header.")

                headers = [h.strip() for h in reader.fieldnames]

                if len(headers) != len(set(headers)):
                    raise DatasetValidationError(
                        "Duplicate column names detected."
                    )

                rows = []
                for row in reader:
                    normalized = {
                        key.strip(): value.strip() if value is not None else None
                        for key, value in row.items()
                        if key is not None
                    }
                    if set(normalized) != set(headers):
                        raise DatasetValidationError(
                            "CSV row contains an inconsistent number of fields."
                        )
                    rows.append(normalized)

                return cls(headers, rows)

        except OSError as exc:
            raise DatasetLoadError(f"Cannot read CSV: {exc}") from exc
        except csv.Error as exc:
            raise DatasetLoadError(f"Invalid CSV: {exc}") from exc

    @classmethod
    def sample(cls) -> "Dataset":
        headers = ["employee_id", "department", "salary", "experience", "rating"]

        rows = [
            {"employee_id": "E001", "department": "Engineering",
             "salary": "85000", "experience": "5", "rating": "4.5"},
            {"employee_id": "E002", "department": "Analytics",
             "salary": "72000", "experience": "3", "rating": "4.2"},
            {"employee_id": "E003", "department": "Engineering",
             "salary": "95000", "experience": "8", "rating": "4.8"},
            {"employee_id": "E004", "department": "Operations",
             "salary": "61000", "experience": "2", "rating": "3.9"},
            {"employee_id": "E005", "department": "Analytics",
             "salary": "78000", "experience": "4", "rating": "4.4"},
            {"employee_id": "E006", "department": "Engineering",
             "salary": "110000", "experience": "12", "rating": "4.9"},
            {"employee_id": "E007", "department": "Operations",
             "salary": "", "experience": "3", "rating": "3.7"},
            {"employee_id": "E008", "department": "Analytics",
             "salary": "75000", "experience": "4", "rating": ""},
            {"employee_id": "E009", "department": "Engineering",
             "salary": "85000", "experience": "5", "rating": "4.5"},
            {"employee_id": "E010", "department": "Operations",
             "salary": "58000", "experience": "1", "rating": "3.5"},
            {"employee_id": "E010", "department": "Operations",
             "salary": "58000", "experience": "1", "rating": "3.5"},
        ]

        return cls(headers, rows)


class ExploratoryDataAnalyzer:
    """Performs statistical and structural analysis."""

    MISSING_VALUES = {"", "na", "n/a", "null", "none", "nan", "missing"}

    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        self.numeric_data: dict[str, list[float]] = {}

    @classmethod
    def is_missing(cls, value: Any) -> bool:
        return value is None or (
            isinstance(value, str)
            and value.strip().lower() in cls.MISSING_VALUES
        )

    @staticmethod
    def to_number(value: Any) -> Optional[float]:
        try:
            if isinstance(value, bool):
                return None
            number = float(value)
            return number if math.isfinite(number) else None
        except (ValueError, TypeError):
            return None

    def infer_type(self, values: list[Any]) -> str:
        valid = [v for v in values if not self.is_missing(v)]

        if not valid:
            return "empty"

        numeric_count = sum(
            self.to_number(value) is not None for value in valid
        )

        if numeric_count == len(valid):
            return "numeric"

        if all(
            isinstance(value, str)
            and value.lower() in {"true", "false"}
            for value in valid
        ):
            return "boolean"

        date_formats = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S")
        if all(
            any(
                self._valid_date(value, fmt)
                for fmt in date_formats
            )
            for value in valid
        ):
            return "datetime"

        return "categorical"

    @staticmethod
    def _valid_date(value: Any, fmt: str) -> bool:
        try:
            datetime.strptime(str(value), fmt)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def quartile(values: list[float], fraction: float) -> float:
        """Linear interpolation using the (n - 1) position convention."""
        ordered = sorted(values)
        position = (len(ordered) - 1) * fraction
        lower = math.floor(position)
        upper = math.ceil(position)

        if lower == upper:
            return ordered[lower]

        return (
            ordered[lower] * (upper - position)
            + ordered[upper] * (position - lower)
        )

    def numeric_statistics(self, values: list[float]) -> dict[str, Any]:
        if not values:
            return {}

        q1 = self.quartile(values, 0.25)
        median = statistics.median(values)
        q3 = self.quartile(values, 0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": median,
            "mode": statistics.multimode(values),
            "minimum": min(values),
            "maximum": max(values),
            "range": max(values) - min(values),
            "standard_deviation": (
                statistics.stdev(values) if len(values) > 1 else 0.0
            ),
            "variance": (
                statistics.variance(values) if len(values) > 1 else 0.0
            ),
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "outliers": [
                value for value in values
                if value < lower_bound or value > upper_bound
            ],
        }

    def profile_column(self, column: str) -> ColumnProfile:
        values = [row[column] for row in self.dataset.rows]
        missing = sum(self.is_missing(v) for v in values)
        valid = [v for v in values if not self.is_missing(v)]

        inferred_type = self.infer_type(values)
        stats: dict[str, Any] = {}
        frequencies: dict[str, int] = {}

        if inferred_type == "numeric":
            numeric_values = [
                self.to_number(v) for v in valid
            ]
            numeric = [v for v in numeric_values if v is not None]
            self.numeric_data[column] = numeric
            stats = self.numeric_statistics(numeric)

        elif inferred_type == "categorical":
            frequencies = dict(
                Counter(str(v) for v in valid).most_common(10)
            )

            if valid:
                stats = {
                    "mode": statistics.multimode(
                        [str(v) for v in valid]
                    ),
                    "most_frequent": max(
                        Counter(str(v) for v in valid).values()
                    ),
                }

        elif inferred_type == "datetime":
            dates = [str(v) for v in valid]
            stats = {
                "earliest": min(dates),
                "latest": max(dates),
            }

        return ColumnProfile(
            name=column,
            inferred_type=inferred_type,
            total=len(values),
            missing=missing,
            unique=len(set(str(v) for v in valid)),
            statistics=stats,
            frequencies=frequencies,
        )

    def duplicate_count(self) -> int:
        """Count repeated records beyond their first occurrence."""
        seen = set()
        duplicates = 0

        for row in self.dataset.rows:
            key = tuple(row[column] for column in self.dataset.headers)
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)

        return duplicates

    @staticmethod
    def pearson_correlation(
        first: list[float],
        second: list[float]
    ) -> Optional[float]:
        if len(first) != len(second) or len(first) < 2:
            return None

        mean_x = statistics.mean(first)
        mean_y = statistics.mean(second)

        deviations_x = [x - mean_x for x in first]
        deviations_y = [y - mean_y for y in second]

        sum_x = sum(x * x for x in deviations_x)
        sum_y = sum(y * y for y in deviations_y)

        denominator = math.sqrt(sum_x * sum_y)

        if denominator == 0:
            return None

        return (
            sum(x * y for x, y in zip(deviations_x, deviations_y))
            / denominator
        )

    def correlation_matrix(self) -> dict[str, float]:
        result = {}
        columns = list(self.numeric_data)

        for i, first in enumerate(columns):
            for second in columns[i + 1:]:
                # Pairwise deletion keeps observations aligned.
                pairs = []

                for row in self.dataset.rows:
                    x = self.to_number(row[first])
                    y = self.to_number(row[second])

                    if x is not None and y is not None:
                        pairs.append((x, y))

                if len(pairs) < 2:
                    continue

                correlation = self.pearson_correlation(
                    [p[0] for p in pairs],
                    [p[1] for p in pairs],
                )

                if correlation is not None:
                    result[f"{first}__{second}"] = correlation

        return result

    def grouped_analysis(
        self,
        category: str,
        numeric_column: str
    ) -> dict[str, dict[str, float]]:
        if category not in self.dataset.headers:
            raise DatasetValidationError(
                f"Unknown grouping column: {category}"
            )

        if numeric_column not in self.dataset.headers:
            raise DatasetValidationError(
                f"Unknown numeric column: {numeric_column}"
            )

        groups: dict[str, list[float]] = defaultdict(list)

        for row in self.dataset.rows:
            group = row[category]
            value = self.to_number(row[numeric_column])

            if self.is_missing(group) or value is None:
                continue

            groups[str(group)].append(value)

        return {
            name: {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "minimum": min(values),
                "maximum": max(values),
            }
            for name, values in sorted(groups.items())
        }

    def quality_checks(
        self,
        profiles: list[ColumnProfile]
    ) -> list[str]:
        issues = []

        if not self.dataset.rows:
            issues.append("Dataset contains no records.")

        if self.duplicate_count():
            issues.append(
                f"Found {self.duplicate_count()} duplicate rows."
            )

        for profile in profiles:
            if profile.missing:
                percentage = (
                    profile.missing / profile.total * 100
                    if profile.total else 0
                )
                issues.append(
                    f"{profile.name}: {profile.missing} missing "
                    f"values ({percentage:.2f}%)."
                )

            if profile.unique <= 1 and profile.total > 0:
                issues.append(
                    f"{profile.name}: constant or single-valued column."
                )

        return issues

    def analyze(self) -> AnalysisReport:
        profiles = [
            self.profile_column(column)
            for column in self.dataset.headers
        ]

        return AnalysisReport(
            rows=len(self.dataset.rows),
            columns=len(self.dataset.headers),
            duplicate_rows=self.duplicate_count(),
            column_profiles=profiles,
            correlations=self.correlation_matrix(),
            quality_issues=self.quality_checks(profiles),
        )

    @staticmethod
    def save_report(report: AnalysisReport, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8") as file:
                json.dump(
                    report.to_dict(),
                    file,
                    indent=2,
                    allow_nan=False,
                )

        except OSError as exc:
            raise EDAError(f"Cannot save report: {exc}") from exc


def display_report(report: AnalysisReport) -> None:
    print("\nEXPLORATORY DATA ANALYSIS")
    print("=" * 65)
    print(f"Rows: {report.rows}")
    print(f"Columns: {report.columns}")
    print(f"Duplicate rows: {report.duplicate_rows}")

    print("\nCOLUMN PROFILES")
    print("-" * 65)

    for profile in report.column_profiles:
        missing_percentage = (
            profile.missing / profile.total * 100
            if profile.total else 0
        )

        print(f"\nColumn: {profile.name}")
        print(f"Type: {profile.inferred_type}")
        print(f"Missing: {profile.missing} ({missing_percentage:.2f}%)")
        print(f"Unique: {profile.unique}")

        if profile.statistics:
            for key, value in profile.statistics.items():
                print(f"  {key}: {value}")

        if profile.frequencies:
            print(f"  Frequencies: {profile.frequencies}")

    print("\nNUMERIC CORRELATIONS")
    print("-" * 65)

    if report.correlations:
        for pair, value in report.correlations.items():
            print(f"{pair}: {value:.4f}")
    else:
        print("No valid numeric column pairs.")

    print("\nDATA QUALITY")
    print("-" * 65)

    if report.quality_issues:
        for issue in report.quality_issues:
            print(f"- {issue}")
    else:
        print("No basic quality issues detected.")


def run_tests() -> None:
    """Basic correctness tests for statistical calculations."""
    analyzer = ExploratoryDataAnalyzer(Dataset.sample())

    assert analyzer.quartile([1, 2, 3, 4, 5], 0.5) == 3
    assert analyzer.pearson_correlation(
        [1, 2, 3], [2, 4, 6]
    ) == 1.0

    assert analyzer.pearson_correlation(
        [1, 1, 1], [2, 3, 4]
    ) is None

    assert analyzer.duplicate_count() == 1

    assert analyzer.is_missing("")
    assert analyzer.is_missing("NaN")
    assert not analyzer.is_missing("0")

    print("All tests passed.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Programmatic Exploratory Data Analysis"
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Input CSV file. Uses sample data if omitted.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eda_report.json"),
        help="JSON report destination.",
    )

    parser.add_argument(
        "--group",
        help="Categorical column for grouped analysis.",
    )

    parser.add_argument(
        "--measure",
        default="salary",
        help="Numeric column for grouped analysis.",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run built-in correctness tests.",
    )

    args = parser.parse_args()

    try:
        if args.test:
            run_tests()
            return 0

        dataset = (
            Dataset.from_csv(args.input)
            if args.input
            else Dataset.sample()
        )

        analyzer = ExploratoryDataAnalyzer(dataset)
        report = analyzer.analyze()

        display_report(report)

        if args.group:
            print("\nGROUPED ANALYSIS")
            print("-" * 65)

            grouped = analyzer.grouped_analysis(
                args.group,
                args.measure,
            )

            print(json.dumps(grouped, indent=2))

        analyzer.save_report(report, args.output)

        print(f"\nReport saved to: {args.output.resolve()}")
        return 0

    except (EDAError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
