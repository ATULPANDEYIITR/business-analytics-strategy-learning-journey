from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import csv
import json
import math
import statistics


@dataclass(frozen=True)
class BusinessItem:
    name: str
    category: str
    value: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Item name cannot be empty.")
        if not self.category.strip():
            raise ValueError("Category cannot be empty.")
        if not math.isfinite(self.value) or self.value < 0:
            raise ValueError("Value must be a finite non-negative number.")


@dataclass(frozen=True)
class ParetoResult:
    item: BusinessItem
    rank: int
    percentage: float
    cumulative_percentage: float
    cumulative_share: float
    priority: str


def validate_items(items: Iterable[BusinessItem]) -> list[BusinessItem]:
    validated = list(items)
    if not validated:
        raise ValueError("At least one business item is required.")

    names = set()
    for item in validated:
        key = item.name.casefold()
        if key in names:
            raise ValueError(f"Duplicate item: {item.name}")
        names.add(key)

    if sum(item.value for item in validated) <= 0:
        raise ValueError("Total business value must be greater than zero.")

    return validated


def pareto_analysis(
    items: Iterable[BusinessItem],
    threshold: float = 0.80,
) -> list[ParetoResult]:
    if not 0 < threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1.")

    validated = validate_items(items)
    ordered = sorted(validated, key=lambda item: item.value, reverse=True)
    total = sum(item.value for item in ordered)

    results: list[ParetoResult] = []
    cumulative = 0.0

    for rank, item in enumerate(ordered, start=1):
        percentage = item.value / total
        cumulative += percentage

        # The item crossing the threshold is included because excluding it
        # could leave the selected portfolio below the required contribution.
        priority = "CORE" if cumulative - percentage < threshold else (
            "THRESHOLD" if cumulative - percentage < threshold <= cumulative else "REMAINDER"
        )

        results.append(
            ParetoResult(
                item=item,
                rank=rank,
                percentage=percentage,
                cumulative_percentage=cumulative,
                cumulative_share=cumulative,
                priority=priority,
            )
        )

    return results


def identify_vital_few(
    results: list[ParetoResult],
    threshold: float = 0.80,
) -> list[ParetoResult]:
    selected: list[ParetoResult] = []
    cumulative = 0.0

    for result in results:
        selected.append(result)
        cumulative += result.percentage
        if cumulative >= threshold:
            break

    return selected


def category_analysis(items: Iterable[BusinessItem]) -> dict[str, float]:
    totals: dict[str, float] = {}

    for item in items:
        totals[item.category] = totals.get(item.category, 0.0) + item.value

    return dict(sorted(totals.items(), key=lambda pair: pair[1], reverse=True))


def concentration_metrics(results: list[ParetoResult]) -> dict[str, float]:
    total_items = len(results)
    top_20_count = max(1, math.ceil(total_items * 0.20))
    top_20_share = sum(
        result.percentage for result in results[:top_20_count]
    )

    values = [result.item.value for result in results]

    return {
        "item_count": total_items,
        "top_20_count": top_20_count,
        "top_20_share": top_20_share,
        "mean_value": statistics.mean(values),
        "median_value": statistics.median(values),
        "max_value": max(values),
        "min_value": min(values),
    }


def print_report(
    results: list[ParetoResult],
    threshold: float = 0.80,
) -> None:
    vital_few = identify_vital_few(results, threshold)
    metrics = concentration_metrics(results)

    print("\nPARETO BUSINESS PRIORITIZATION")
    print("=" * 78)
    print(
        f"{'Rank':<6}{'Item':<28}{'Value':>12}"
        f"{'Share':>10}{'Cumulative':>13}{'Priority':>11}"
    )
    print("-" * 78)

    for result in results:
        print(
            f"{result.rank:<6}"
            f"{result.item.name[:27]:<28}"
            f"{result.item.value:>12,.2f}"
            f"{result.percentage:>9.1%}"
            f"{result.cumulative_percentage:>12.1%}"
            f"{result.priority:>11}"
        )

    print("-" * 78)
    print(f"Vital-few items: {len(vital_few)} of {len(results)}")
    print(f"Value captured: {sum(x.percentage for x in vital_few):.1%}")
    print(f"Top 20% item share: {metrics['top_20_share']:.1%}")
    print(f"Mean value: {metrics['mean_value']:,.2f}")
    print(f"Median value: {metrics['median_value']:,.2f}")

    print("\nCATEGORY CONTRIBUTION")
    print("-" * 42)
    for category, value in category_analysis(
        [result.item for result in results]
    ).items():
        total = sum(result.item.value for result in results)
        print(f"{category:<28}{value:>10,.2f} ({value / total:.1%})")


def export_json(results: list[ParetoResult], path: Path) -> None:
    payload = [
        {
            "rank": result.rank,
            "item": result.item.name,
            "category": result.item.category,
            "value": result.item.value,
            "percentage": round(result.percentage, 6),
            "cumulative_percentage": round(
                result.cumulative_percentage, 6
            ),
            "priority": result.priority,
        }
        for result in results
    ]

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )


def export_csv(results: list[ParetoResult], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "rank",
                "item",
                "category",
                "value",
                "percentage",
                "cumulative_percentage",
                "priority",
            ]
        )

        for result in results:
            writer.writerow(
                [
                    result.rank,
                    result.item.name,
                    result.item.category,
                    f"{result.item.value:.2f}",
                    f"{result.percentage:.6f}",
                    f"{result.cumulative_percentage:.6f}",
                    result.priority,
                ]
            )


def load_csv(path: Path) -> list[BusinessItem]:
    if not path.exists():
        raise FileNotFoundError(path)

    items: list[BusinessItem] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required = {"name", "category", "value"}

        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV must contain name, category, and value columns.")

        for row_number, row in enumerate(reader, start=2):
            try:
                items.append(
                    BusinessItem(
                        name=row["name"],
                        category=row["category"],
                        value=float(row["value"]),
                    )
                )
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Invalid CSV row {row_number}: {exc}"
                ) from exc

    return validate_items(items)


def run_self_tests() -> None:
    sample = [
        BusinessItem("Enterprise accounts", "Customers", 420000),
        BusinessItem("SMB accounts", "Customers", 160000),
        BusinessItem("Support tickets", "Operations", 90000),
        BusinessItem("Cloud infrastructure", "Technology", 75000),
        BusinessItem("Marketing campaigns", "Marketing", 60000),
        BusinessItem("Training programs", "People", 40000),
        BusinessItem("Internal tooling", "Technology", 25000),
        BusinessItem("Legacy reporting", "Operations", 15000),
        BusinessItem("Office services", "Operations", 10000),
        BusinessItem("Other requests", "Operations", 5000),
    ]

    results = pareto_analysis(sample)

    assert len(results) == len(sample)
    assert results[0].item.name == "Enterprise accounts"
    assert math.isclose(
        sum(result.percentage for result in results),
        1.0,
        rel_tol=1e-9,
    )

    vital = identify_vital_few(results)
    assert sum(result.percentage for result in vital) >= 0.80

    try:
        pareto_analysis(
            [BusinessItem("Invalid", "Test", 0)],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Zero-total input should fail.")

    print("Self-tests passed.")


def main() -> None:
    data = [
        BusinessItem("Enterprise accounts", "Customers", 420000),
        BusinessItem("SMB accounts", "Customers", 160000),
        BusinessItem("Support tickets", "Operations", 90000),
        BusinessItem("Cloud infrastructure", "Technology", 75000),
        BusinessItem("Marketing campaigns", "Marketing", 60000),
        BusinessItem("Training programs", "People", 40000),
        BusinessItem("Internal tooling", "Technology", 25000),
        BusinessItem("Legacy reporting", "Operations", 15000),
        BusinessItem("Office services", "Operations", 10000),
        BusinessItem("Other requests", "Operations", 5000),
    ]

    results = pareto_analysis(data, threshold=0.80)
    print_report(results)
    run_self_tests()

    output_dir = Path("pareto_output")
    output_dir.mkdir(exist_ok=True)

    export_json(results, output_dir / "pareto_analysis.json")
    export_csv(results, output_dir / "pareto_analysis.csv")

    print(f"\nReports written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
