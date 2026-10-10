#!/usr/bin/env python3
"""Window functions: ranking, running totals, and analytical calculations.

Run with:
    python window_functions.py

Uses only the Python standard library. The program models monthly sales
analytics and implements window-function semantics explicitly, including
partitioning, ordering, ranking, cumulative aggregates, moving averages,
lag/lead, distribution functions, and period-over-period comparisons.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import groupby
from typing import Callable, Iterable, Sequence
import json
import math
import statistics
import unittest


@dataclass(frozen=True)
class Sale:
    sale_id: int
    salesperson: str
    region: str
    month: str
    revenue: Decimal
    units: int

    @classmethod
    def create(
        cls,
        sale_id: int,
        salesperson: str,
        region: str,
        month: str,
        revenue: str | int | float | Decimal,
        units: int,
    ) -> "Sale":
        if isinstance(sale_id, bool) or sale_id <= 0:
            raise ValueError("sale_id must be a positive integer")
        if not salesperson.strip() or not region.strip():
            raise ValueError("Salesperson and region are required")
        if len(month) != 7 or month[4] != "-":
            raise ValueError("month must use YYYY-MM format")
        try:
            year, month_number = map(int, month.split("-"))
            if not 1 <= month_number <= 12 or year < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(f"Invalid calendar month: {month}") from None

        try:
            amount = Decimal(str(revenue))
        except (InvalidOperation, ValueError):
            raise ValueError("Revenue must be numeric") from None

        if not amount.is_finite() or amount < 0:
            raise ValueError("Revenue must be finite and non-negative")
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise ValueError("Units must be a non-negative integer")

        return cls(
            sale_id=sale_id,
            salesperson=salesperson.strip(),
            region=region.strip(),
            month=month,
            revenue=amount,
            units=units,
        )


def sample_sales() -> list[Sale]:
    """Sales data includes tied revenues and multiple analytical partitions."""
    rows = [
        (1, "Asha", "North", "2026-01", "12000.00", 12),
        (2, "Ravi", "North", "2026-01", "12000.00", 10),
        (3, "Meera", "North", "2026-01", "9000.00", 9),
        (4, "Asha", "North", "2026-02", "15000.00", 15),
        (5, "Ravi", "North", "2026-02", "11000.00", 11),
        (6, "Meera", "North", "2026-02", "11000.00", 10),
        (7, "Asha", "North", "2026-03", "14000.00", 14),
        (8, "Ravi", "North", "2026-03", "16000.00", 16),
        (9, "Meera", "North", "2026-03", "10000.00", 10),
        (10, "Kabir", "South", "2026-01", "8000.00", 8),
        (11, "Nila", "South", "2026-01", "10000.00", 10),
        (12, "Kabir", "South", "2026-02", "12000.00", 12),
        (13, "Nila", "South", "2026-02", "10000.00", 9),
        (14, "Kabir", "South", "2026-03", "12000.00", 11),
        (15, "Nila", "South", "2026-03", "14000.00", 14),
    ]
    return [Sale.create(*row) for row in rows]


def validate_dataset(rows: Sequence[Sale]) -> None:
    """A stable unique key is needed to make row ordering deterministic."""
    seen: set[int] = set()
    for row in rows:
        if row.sale_id in seen:
            raise ValueError(f"Duplicate sale_id: {row.sale_id}")
        seen.add(row.sale_id)


def partition_by(
    rows: Iterable[Sale],
    key: Callable[[Sale], str],
) -> dict[str, list[Sale]]:
    partitions: dict[str, list[Sale]] = defaultdict(list)
    for row in rows:
        partitions[key(row)].append(row)
    return dict(partitions)


def rank_rows(
    rows: Sequence[Sale],
    value: Callable[[Sale], object],
    descending: bool = True,
) -> dict[int, dict[str, int]]:
    """Calculate ROW_NUMBER, RANK, and DENSE_RANK for one ordered partition.

    ROW_NUMBER assigns a unique position. RANK leaves gaps after ties.
    DENSE_RANK does not leave gaps. sale_id provides deterministic ordering
    for ROW_NUMBER but does not break ties for the other rank functions.
    """
    ordered = sorted(
        rows,
        key=lambda row: (
            -value(row) if isinstance(value(row), (int, Decimal)) and descending
            else value(row) if not descending
            else value(row),
            row.sale_id,
        ),
    )

    result: dict[int, dict[str, int]] = {}
    previous_value: object = object()
    rank = 0
    dense_rank = 0

    for position, row in enumerate(ordered, start=1):
        current_value = value(row)
        if position == 1 or current_value != previous_value:
            rank = position
            dense_rank += 1
        result[row.sale_id] = {
            "row_number": position,
            "rank": rank,
            "dense_rank": dense_rank,
        }
        previous_value = current_value

    return result


def ordered_partition(
    rows: Sequence[Sale],
    order_key: Callable[[Sale], object],
) -> list[Sale]:
    """Use a unique tie-breaker whenever the ordering value is not unique."""
    return sorted(rows, key=lambda row: (order_key(row), row.sale_id))


def cumulative_sum(
    rows: Sequence[Sale],
    amount: Callable[[Sale], Decimal],
) -> dict[int, Decimal]:
    total = Decimal("0")
    result: dict[int, Decimal] = {}
    for row in rows:
        total += amount(row)
        result[row.sale_id] = total
    return result


def moving_average(
    rows: Sequence[Sale],
    amount: Callable[[Sale], Decimal],
    preceding: int,
    following: int = 0,
) -> dict[int, Decimal]:
    """Compute a row-based frame, including the current row.

    At partition boundaries the frame shrinks rather than inventing rows.
    This is similar to ROWS BETWEEN N PRECEDING AND M FOLLOWING.
    """
    if preceding < 0 or following < 0:
        raise ValueError("Frame offsets cannot be negative")

    values = [amount(row) for row in rows]
    result: dict[int, Decimal] = {}

    for index, row in enumerate(rows):
        start = max(0, index - preceding)
        end = min(len(rows), index + following + 1)
        frame = values[start:end]
        result[row.sale_id] = sum(frame, Decimal("0")) / Decimal(len(frame))

    return result


def lag_lead(
    rows: Sequence[Sale],
    amount: Callable[[Sale], Decimal],
    offset: int = 1,
) -> tuple[dict[int, Decimal | None], dict[int, Decimal | None]]:
    """Return previous and next values within an ordered partition."""
    if offset < 0:
        raise ValueError("Offset cannot be negative")

    values = [amount(row) for row in rows]
    lag_result: dict[int, Decimal | None] = {}
    lead_result: dict[int, Decimal | None] = {}

    for index, row in enumerate(rows):
        lag_index = index - offset
        lead_index = index + offset
        lag_result[row.sale_id] = (
            values[lag_index] if lag_index >= 0 else None
        )
        lead_result[row.sale_id] = (
            values[lead_index] if lead_index < len(rows) else None
        )

    return lag_result, lead_result


def percent_rank(rank: int, count: int) -> float:
    """PERCENT_RANK = (RANK - 1) / (partition row count - 1)."""
    if count <= 0 or not 1 <= rank <= count:
        raise ValueError("Rank and partition size are inconsistent")
    return 0.0 if count == 1 else (rank - 1) / (count - 1)


def cume_dist(
    rows: Sequence[Sale],
    value: Callable[[Sale], object],
) -> dict[int, float]:
    """CUME_DIST is the fraction of rows less than or equal to this value."""
    if not rows:
        return {}

    ordered = sorted(rows, key=lambda row: (value(row), row.sale_id))
    counts: dict[object, int] = defaultdict(int)
    for row in ordered:
        counts[value(row)] += 1

    cumulative = 0
    cumulative_for_value: dict[object, int] = {}
    for row in ordered:
        key = value(row)
        if key not in cumulative_for_value:
            cumulative += counts[key]
            cumulative_for_value[key] = cumulative

    size = len(ordered)
    return {
        row.sale_id: cumulative_for_value[value(row)] / size
        for row in rows
    }


def ntile(
    rows: Sequence[Sale],
    buckets: int,
    order_key: Callable[[Sale], object],
) -> dict[int, int]:
    """Divide ordered rows into nearly equal groups, with earlier groups larger."""
    if buckets <= 0:
        raise ValueError("Bucket count must be positive")

    ordered = sorted(rows, key=lambda row: (order_key(row), row.sale_id))
    count = len(ordered)
    if count == 0:
        return {}

    base_size, remainder = divmod(count, buckets)
    result: dict[int, int] = {}
    position = 0

    for bucket in range(1, buckets + 1):
        size = base_size + (1 if bucket <= remainder else 0)
        for row in ordered[position:position + size]:
            result[row.sale_id] = bucket
        position += size

    return result


def revenue_report(rows: Sequence[Sale]) -> list[dict[str, object]]:
    validate_dataset(rows)

    by_region = partition_by(rows, lambda row: row.region)
    report: list[dict[str, object]] = []

    for region, region_rows in sorted(by_region.items()):
        ordered = ordered_partition(region_rows, lambda row: row.month)
        rankings = rank_rows(ordered, lambda row: row.revenue, descending=True)
        running = cumulative_sum(ordered, lambda row: row.revenue)
        average = moving_average(ordered, lambda row: row.revenue, preceding=1)
        lag_values, lead_values = lag_lead(
            ordered, lambda row: row.revenue
        )
        distributions = cume_dist(ordered, lambda row: row.revenue)

        for row in ordered:
            rank_data = rankings[row.sale_id]
            previous = lag_values[row.sale_id]
            change = (
                None
                if previous is None or previous == 0
                else (row.revenue - previous) / previous * Decimal("100")
            )
            report.append({
                "sale_id": row.sale_id,
                "region": region,
                "salesperson": row.salesperson,
                "month": row.month,
                "revenue": str(row.revenue),
                "row_number": rank_data["row_number"],
                "rank": rank_data["rank"],
                "dense_rank": rank_data["dense_rank"],
                "running_revenue": str(running[row.sale_id]),
                "two_row_moving_average": str(
                    average[row.sale_id].quantize(Decimal("0.01"))
                ),
                "previous_revenue": (
                    str(previous) if previous is not None else None
                ),
                "next_revenue": (
                    str(lead_values[row.sale_id])
                    if lead_values[row.sale_id] is not None else None
                ),
                "change_percent": (
                    str(change.quantize(Decimal("0.01")))
                    if change is not None else None
                ),
                "cume_dist": round(distributions[row.sale_id], 4),
            })

    return report


def show_top_salespeople(rows: Sequence[Sale]) -> None:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        totals[row.salesperson] += row.revenue

    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    print("\nSalespeople ranked by total revenue")
    previous_total: Decimal | None = None
    rank = 0
    dense_rank = 0

    for position, (name, total) in enumerate(ordered, start=1):
        if total != previous_total:
            rank = position
            dense_rank += 1
        print(
            f"{name:8} total={total:>10} "
            f"rank={rank} dense_rank={dense_rank}"
        )
        previous_total = total


def demonstrate_frame_difference() -> None:
    """Contrast a row-based moving frame with a full-partition cumulative frame."""
    values = [Decimal("10"), Decimal("20"), Decimal("30"), Decimal("40")]
    cumulative: list[Decimal] = []
    rolling: list[Decimal] = []
    running = Decimal("0")

    for index, value in enumerate(values):
        running += value
        cumulative.append(running)
        frame = values[max(0, index - 1):index + 1]
        rolling.append(sum(frame, Decimal("0")))

    print("\nROWS frame comparison")
    print("value | cumulative sum | current plus previous row")
    for value, total, average_total in zip(values, cumulative, rolling):
        print(f"{value:>5} | {total:>14} | {average_total:>25}")


class WindowFunctionTests(unittest.TestCase):
    def test_rank_functions_preserve_ties(self) -> None:
        rows = sample_sales()[:3]
        ranks = rank_rows(rows, lambda row: row.revenue)
        self.assertEqual(ranks[1]["rank"], 1)
        self.assertEqual(ranks[2]["rank"], 1)
        self.assertEqual(ranks[3]["rank"], 3)
        self.assertEqual(ranks[3]["dense_rank"], 2)

    def test_running_total_resets_by_partition(self) -> None:
        rows = sample_sales()
        north = ordered_partition(
            [row for row in rows if row.region == "North"],
            lambda row: row.month,
        )
        totals = cumulative_sum(north, lambda row: row.revenue)
        self.assertEqual(totals[north[0].sale_id], Decimal("33000.00"))

    def test_lag_boundary_is_null_like(self) -> None:
        rows = ordered_partition(sample_sales()[:3], lambda row: row.month)
        lag_values, _ = lag_lead(rows, lambda row: row.revenue)
        self.assertIsNone(lag_values[rows[0].sale_id])

    def test_single_row_percent_rank(self) -> None:
        self.assertEqual(percent_rank(1, 1), 0.0)

    def test_empty_ntile(self) -> None:
        self.assertEqual(ntile([], 3, lambda row: row.month), {})

    def test_duplicate_identifiers_rejected(self) -> None:
        row = sample_sales()[0]
        with self.assertRaises(ValueError):
            validate_dataset([row, row])

    def test_negative_revenue_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Sale.create(900, "Test", "North", "2026-01", "-1", 1)

    def test_moving_frame_boundary(self) -> None:
        rows = sample_sales()[:2]
        ordered = ordered_partition(rows, lambda row: row.month)
        result = moving_average(ordered, lambda row: row.revenue, 1)
        self.assertEqual(result[ordered[0].sale_id], ordered[0].revenue)
        self.assertEqual(
            result[ordered[1].sale_id],
            (ordered[0].revenue + ordered[1].revenue) / Decimal("2"),
        )


def main() -> None:
    rows = sample_sales()
    validate_dataset(rows)

    print("Monthly sales window-function report")
    report = revenue_report(rows)
    for item in report:
        print(json.dumps(item, sort_keys=True))

    show_top_salespeople(rows)
    demonstrate_frame_difference()

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WindowFunctionTests)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
