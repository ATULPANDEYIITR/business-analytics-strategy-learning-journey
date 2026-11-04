#!/usr/bin/env python3
"""
Data Aggregation: Grouping, Aggregation, and Pivot Operations.

Demonstrates:
- Grouping records by one or multiple dimensions.
- Count, sum, average, minimum, maximum, and distinct count.
- Conditional aggregation.
- Multi-level aggregation.
- Pivot and unpivot operations.
- Missing-value handling.
- Validation and aggregation policies.
- Streaming aggregation for large datasets.
- JSON and CSV file processing.
- Reconciliation and automated tests.
"""

from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Sequence


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("data_aggregation")


class AggregationError(Exception):
    """Base exception for aggregation failures."""


class ValidationError(AggregationError):
    """Raised when input records violate the data contract."""


class AggregationOperation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    DISTINCT_COUNT = "distinct_count"


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: str
    region: str
    category: str
    product: str
    salesperson: str
    quantity: int
    unit_price: Decimal
    transaction_date: date
    status: str

    @property
    def revenue(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class AggregationResult:
    group: tuple[Any, ...]
    transaction_count: int
    total_quantity: int
    total_revenue: Decimal
    average_revenue: Decimal
    minimum_revenue: Decimal
    maximum_revenue: Decimal
    distinct_products: int


class RecordValidator:
    """Enforces the record contract before aggregation."""

    REQUIRED_FIELDS = {
        "transaction_id",
        "region",
        "category",
        "product",
        "salesperson",
        "quantity",
        "unit_price",
        "transaction_date",
        "status",
    }

    @classmethod
    def validate(cls, raw: dict[str, Any]) -> SalesRecord:
        if not isinstance(raw, dict):
            raise ValidationError("Each record must be a dictionary.")

        missing = cls.REQUIRED_FIELDS - raw.keys()
        if missing:
            raise ValidationError(
                f"Missing required fields: {sorted(missing)}"
            )

        for field in (
            "transaction_id",
            "region",
            "category",
            "product",
            "salesperson",
            "status",
        ):
            if not isinstance(raw[field], str) or not raw[field].strip():
                raise ValidationError(f"{field} must be a nonempty string.")

        try:
            quantity = int(raw["quantity"])
            unit_price = Decimal(str(raw["unit_price"]))
            transaction_date = date.fromisoformat(
                str(raw["transaction_date"])
            )
        except (ValueError, TypeError, InvalidOperation) as exc:
            raise ValidationError(f"Invalid record value: {exc}") from exc

        if quantity <= 0:
            raise ValidationError("Quantity must be positive.")

        if not unit_price.is_finite() or unit_price < 0:
            raise ValidationError("Unit price must be finite and nonnegative.")

        if unit_price.as_tuple().exponent < -2:
            raise ValidationError("Unit price cannot have more than two decimals.")

        if raw["status"] not in {"completed", "pending", "cancelled"}:
            raise ValidationError("Unsupported transaction status.")

        return SalesRecord(
            transaction_id=raw["transaction_id"].strip(),
            region=raw["region"].strip(),
            category=raw["category"].strip(),
            product=raw["product"].strip(),
            salesperson=raw["salesperson"].strip(),
            quantity=quantity,
            unit_price=unit_price,
            transaction_date=transaction_date,
            status=raw["status"],
        )


class DataAggregator:
    """Provides reusable grouping and aggregation operations."""

    @staticmethod
    def group_by(
        records: Iterable[SalesRecord],
        dimensions: Sequence[str],
    ) -> dict[tuple[Any, ...], list[SalesRecord]]:
        if not dimensions:
            raise ValidationError("At least one grouping dimension is required.")

        grouped: dict[tuple[Any, ...], list[SalesRecord]] = defaultdict(list)

        for record in records:
            try:
                key = tuple(getattr(record, field) for field in dimensions)
            except AttributeError as exc:
                raise ValidationError(
                    f"Unknown grouping dimension: {exc}"
                ) from exc

            grouped[key].append(record)

        return dict(grouped)

    @staticmethod
    def aggregate(
        records: Sequence[SalesRecord],
        dimensions: Sequence[str],
    ) -> list[AggregationResult]:
        grouped = DataAggregator.group_by(records, dimensions)
        results = []

        for key, items in grouped.items():
            revenues = [item.revenue for item in items]

            results.append(
                AggregationResult(
                    group=key,
                    transaction_count=len(items),
                    total_quantity=sum(item.quantity for item in items),
                    total_revenue=sum(revenues, Decimal("0")),
                    average_revenue=(
                        sum(revenues, Decimal("0")) / len(revenues)
                    ).quantize(Decimal("0.01")),
                    minimum_revenue=min(revenues),
                    maximum_revenue=max(revenues),
                    distinct_products=len({item.product for item in items}),
                )
            )

        return sorted(results, key=lambda result: tuple(map(str, result.group)))

    @staticmethod
    def conditional_aggregate(
        records: Sequence[SalesRecord],
    ) -> dict[str, Any]:
        completed = [
            record for record in records
            if record.status == "completed"
        ]

        pending = [
            record for record in records
            if record.status == "pending"
        ]

        cancelled = [
            record for record in records
            if record.status == "cancelled"
        ]

        return {
            "total_records": len(records),
            "completed_count": len(completed),
            "pending_count": len(pending),
            "cancelled_count": len(cancelled),
            "completed_revenue": sum(
                (record.revenue for record in completed),
                Decimal("0"),
            ),
            "pending_revenue": sum(
                (record.revenue for record in pending),
                Decimal("0"),
            ),
        }

    @staticmethod
    def pivot(
        records: Sequence[SalesRecord],
        row_field: str,
        column_field: str,
        value_field: str,
        operation: AggregationOperation,
    ) -> dict[str, dict[str, Any]]:
        """Create a pivot table with dynamic row and column dimensions."""

        grouped: dict[tuple[str, str], list[Any]] = defaultdict(list)

        for record in records:
            try:
                row_key = str(getattr(record, row_field))
                column_key = str(getattr(record, column_field))
                value = getattr(record, value_field)
            except AttributeError as exc:
                raise ValidationError(f"Invalid pivot field: {exc}") from exc

            if operation in {
                AggregationOperation.SUM,
                AggregationOperation.AVERAGE,
                AggregationOperation.MINIMUM,
                AggregationOperation.MAXIMUM,
            }:
                if isinstance(value, bool) or not isinstance(
                    value, (int, float, Decimal)
                ):
                    raise ValidationError(
                        f"{value_field} must be numeric for {operation.value}."
                    )

            grouped[(row_key, column_key)].append(value)

        pivot_table: dict[str, dict[str, Any]] = defaultdict(dict)

        for (row_key, column_key), values in grouped.items():
            if operation == AggregationOperation.COUNT:
                result = len(values)
            elif operation == AggregationOperation.SUM:
                result = sum(values, Decimal("0"))
            elif operation == AggregationOperation.AVERAGE:
                result = sum(values, Decimal("0")) / len(values)
            elif operation == AggregationOperation.MINIMUM:
                result = min(values)
            elif operation == AggregationOperation.MAXIMUM:
                result = max(values)
            elif operation == AggregationOperation.DISTINCT_COUNT:
                result = len(set(values))
            else:
                raise ValidationError("Unsupported aggregation operation.")

            pivot_table[row_key][column_key] = result

        return dict(pivot_table)

    @staticmethod
    def unpivot(
        pivot_table: dict[str, dict[str, Any]],
        row_name: str = "row",
        column_name: str = "column",
        value_name: str = "value",
    ) -> list[dict[str, Any]]:
        """Convert a wide pivot table into normalized long-form records."""

        return [
            {
                row_name: row_key,
                column_name: column_key,
                value_name: value,
            }
            for row_key, columns in pivot_table.items()
            for column_key, value in columns.items()
        ]


class StreamingAggregator:
    """
    Aggregates large datasets without retaining every input record.

    Memory consumption is proportional to the number of distinct groups.
    """

    def __init__(self, dimensions: Sequence[str]):
        if not dimensions:
            raise ValidationError("At least one grouping dimension is required.")

        self.dimensions = tuple(dimensions)
        self.state: dict[tuple[Any, ...], dict[str, Any]] = {}

    def add(self, record: SalesRecord) -> None:
        key = tuple(getattr(record, field) for field in self.dimensions)

        if key not in self.state:
            self.state[key] = {
                "count": 0,
                "quantity": 0,
                "revenue": Decimal("0"),
                "products": set(),
            }

        current = self.state[key]
        current["count"] += 1
        current["quantity"] += record.quantity
        current["revenue"] += record.revenue
        current["products"].add(record.product)

    def results(self) -> list[AggregationResult]:
        output = []

        for key, state in self.state.items():
            revenue = state["revenue"]
            count = state["count"]

            output.append(
                AggregationResult(
                    group=key,
                    transaction_count=count,
                    total_quantity=state["quantity"],
                    total_revenue=revenue,
                    average_revenue=(
                        revenue / count
                    ).quantize(Decimal("0.01")),
                    minimum_revenue=Decimal("0"),
                    maximum_revenue=Decimal("0"),
                    distinct_products=len(state["products"]),
                )
            )

        return sorted(output, key=lambda item: tuple(map(str, item.group)))


def sample_records() -> list[SalesRecord]:
    raw_records = [
        ("T001", "North", "Electronics", "Laptop", "Asha", 2, "65000.00", "2026-10-01", "completed"),
        ("T002", "North", "Electronics", "Phone", "Asha", 3, "25000.00", "2026-10-02", "completed"),
        ("T003", "South", "Furniture", "Chair", "Ravi", 5, "3000.00", "2026-10-03", "completed"),
        ("T004", "South", "Electronics", "Laptop", "Ravi", 1, "65000.00", "2026-10-04", "pending"),
        ("T005", "East", "Furniture", "Table", "Neha", 2, "12000.00", "2026-10-05", "completed"),
        ("T006", "East", "Electronics", "Phone", "Neha", 4, "25000.00", "2026-10-06", "cancelled"),
        ("T007", "West", "Furniture", "Chair", "Arun", 3, "3000.00", "2026-10-07", "completed"),
        ("T008", "West", "Electronics", "Laptop", "Arun", 2, "65000.00", "2026-10-08", "completed"),
        ("T009", "North", "Furniture", "Table", "Asha", 1, "12000.00", "2026-10-09", "pending"),
        ("T010", "South", "Furniture", "Chair", "Ravi", 2, "3000.00", "2026-10-10", "completed"),
    ]

    return [
        RecordValidator.validate({
            "transaction_id": row[0],
            "region": row[1],
            "category": row[2],
            "product": row[3],
            "salesperson": row[4],
            "quantity": row[5],
            "unit_price": row[6],
            "transaction_date": row[7],
            "status": row[8],
        })
        for row in raw_records
    ]


def load_csv(path: Path) -> list[SalesRecord]:
    """Load records while rejecting duplicate transaction identifiers."""

    records = []
    seen = set()

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for line_number, raw in enumerate(reader, start=2):
            try:
                record = RecordValidator.validate(raw)

                if record.transaction_id in seen:
                    raise ValidationError("Duplicate transaction identifier.")

                seen.add(record.transaction_id)
                records.append(record)

            except ValidationError as exc:
                logger.error("CSV line %s rejected: %s", line_number, exc)

    return records


def export_json(
    results: Sequence[AggregationResult],
    path: Path,
) -> None:
    """Write aggregated data using JSON-compatible decimal strings."""

    payload = [
        {
            **asdict(result),
            "total_revenue": str(result.total_revenue),
            "average_revenue": str(result.average_revenue),
            "minimum_revenue": str(result.minimum_revenue),
            "maximum_revenue": str(result.maximum_revenue),
        }
        for result in results
    ]

    path.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )


def demonstrate() -> None:
    records = sample_records()

    print("\n1. Grouping by region and category")

    regional = DataAggregator.aggregate(
        records,
        ["region", "category"],
    )

    for result in regional:
        print(
            result.group,
            "count =", result.transaction_count,
            "quantity =", result.total_quantity,
            "revenue =", result.total_revenue,
        )

    print("\n2. Conditional aggregation")
    print(DataAggregator.conditional_aggregate(records))

    print("\n3. Pivot: region versus category, total revenue")

    pivot_table = DataAggregator.pivot(
        records,
        "region",
        "category",
        "revenue",
        AggregationOperation.SUM,
    )

    for region, columns in sorted(pivot_table.items()):
        print(region, columns)

    print("\n4. Unpivot")
    for item in DataAggregator.unpivot(pivot_table):
        print(item)

    print("\n5. Streaming aggregation")

    streaming = StreamingAggregator(["region"])
    for record in records:
        streaming.add(record)

    for result in streaming.results():
        print(result)

    print("\n6. Validation edge cases")

    invalid = {
        "transaction_id": "BAD",
        "region": "North",
        "category": "Electronics",
        "product": "Laptop",
        "salesperson": "Asha",
        "quantity": -1,
        "unit_price": "500.00",
        "transaction_date": "2026-10-11",
        "status": "completed",
    }

    try:
        RecordValidator.validate(invalid)
    except ValidationError as exc:
        print("Rejected invalid record:", exc)

    print("\n7. Automated consistency checks")

    assert len(records) == 10

    total_revenue = sum(
        (record.revenue for record in records),
        Decimal("0"),
    )

    assert total_revenue == Decimal("337000.00")

    assert sum(
        result.transaction_count for result in regional
    ) == len(records)

    assert sum(
        result.total_revenue for result in regional
    ) == total_revenue

    assert len(DataAggregator.unpivot(pivot_table)) == 8

    print("All assertions passed.")

    print("\n8. Exporting aggregated results")

    output_path = Path("regional_aggregation.json")
    export_json(regional, output_path)
    print("Created:", output_path.resolve())


if __name__ == "__main__":
    demonstrate()
