from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable
import csv
import json
import math
import statistics


# Funnel Analysis
# This script models customer journeys through ordered conversion stages,
# calculates stage conversion and drop-off, compares segments, identifies
# time-to-convert behavior, and exports an analysis suitable for reporting.


@dataclass(frozen=True)
class FunnelStage:
    name: str
    order: int


@dataclass
class CustomerJourney:
    customer_id: str
    segment: str
    events: dict[str, datetime]
    revenue: float = 0.0

    def reached(self, stage: FunnelStage) -> bool:
        return stage.name in self.events

    def timestamp(self, stage: FunnelStage) -> datetime | None:
        return self.events.get(stage.name)


@dataclass
class FunnelMetrics:
    stage_name: str
    reached_users: int
    previous_stage_users: int | None
    conversion_from_previous: float | None
    conversion_from_entry: float
    drop_off_from_previous: float | None
    median_seconds_from_previous: float | None = None


@dataclass
class SegmentReport:
    segment: str
    users: int
    converters: int
    conversion_rate: float
    revenue: float


class FunnelAnalyzer:
    def __init__(self, stages: Iterable[FunnelStage], journeys: Iterable[CustomerJourney]):
        self.stages = sorted(stages, key=lambda stage: stage.order)
        self.journeys = list(journeys)
        self._validate_configuration()
        self._validate_journeys()

    def _validate_configuration(self) -> None:
        if not self.stages:
            raise ValueError("A funnel requires at least one stage.")

        names = [stage.name for stage in self.stages]
        if len(names) != len(set(names)):
            raise ValueError("Funnel stage names must be unique.")

        orders = [stage.order for stage in self.stages]
        if len(orders) != len(set(orders)):
            raise ValueError("Funnel stage orders must be unique.")

    def _validate_journeys(self) -> None:
        known_stages = {stage.name for stage in self.stages}
        customer_ids: set[str] = set()

        for journey in self.journeys:
            if journey.customer_id in customer_ids:
                raise ValueError(f"Duplicate customer ID: {journey.customer_id}")

            customer_ids.add(journey.customer_id)

            if journey.revenue < 0:
                raise ValueError(
                    f"Revenue cannot be negative for {journey.customer_id}."
                )

            unknown = set(journey.events) - known_stages
            if unknown:
                raise ValueError(
                    f"Customer {journey.customer_id} has unknown funnel stages: {unknown}"
                )

            timestamps = [
                journey.events[stage.name]
                for stage in self.stages
                if stage.name in journey.events
            ]

            if timestamps != sorted(timestamps):
                raise ValueError(
                    f"Customer {journey.customer_id} has events occurring out of order."
                )

    def reached_users(self, stage: FunnelStage) -> list[CustomerJourney]:
        return [journey for journey in self.journeys if journey.reached(stage)]

    @staticmethod
    def _percentage(numerator: int, denominator: int) -> float:
        return 0.0 if denominator == 0 else numerator / denominator

    def stage_metrics(self) -> list[FunnelMetrics]:
        results: list[FunnelMetrics] = []
        entry_count = len(self.journeys)

        previous_users: list[CustomerJourney] | None = None

        for stage in self.stages:
            current_users = self.reached_users(stage)
            current_count = len(current_users)

            if previous_users is None:
                previous_count = None
                conversion_from_previous = None
                drop_off = None
                durations: list[float] = []
            else:
                previous_count = len(previous_users)
                conversion_from_previous = self._percentage(
                    current_count, previous_count
                )
                drop_off = 1.0 - conversion_from_previous

                durations = []
                for journey in current_users:
                    current_time = journey.timestamp(stage)
                    previous_stage = self.stages[stage.order - 2]
                    previous_time = journey.timestamp(previous_stage)

                    if current_time and previous_time:
                        durations.append(
                            (current_time - previous_time).total_seconds()
                        )

            median_duration = (
                statistics.median(durations) if durations else None
            )

            results.append(
                FunnelMetrics(
                    stage_name=stage.name,
                    reached_users=current_count,
                    previous_stage_users=previous_count,
                    conversion_from_previous=conversion_from_previous,
                    conversion_from_entry=self._percentage(
                        current_count, entry_count
                    ),
                    drop_off_from_previous=drop_off,
                    median_seconds_from_previous=median_duration,
                )
            )

            previous_users = current_users

        return results

    def overall_conversion(self) -> float:
        if not self.journeys:
            return 0.0

        final_stage = self.stages[-1]
        converters = len(self.reached_users(final_stage))
        return converters / len(self.journeys)

    def segment_analysis(self) -> list[SegmentReport]:
        grouped: dict[str, list[CustomerJourney]] = defaultdict(list)

        for journey in self.journeys:
            grouped[journey.segment].append(journey)

        final_stage = self.stages[-1]
        reports = []

        for segment, journeys in sorted(grouped.items()):
            converters = sum(
                journey.reached(final_stage) for journey in journeys
            )

            reports.append(
                SegmentReport(
                    segment=segment,
                    users=len(journeys),
                    converters=converters,
                    conversion_rate=self._percentage(converters, len(journeys)),
                    revenue=sum(journey.revenue for journey in journeys),
                )
            )

        return reports

    def stage_dropoff_by_segment(self, stage_name: str) -> dict[str, float]:
        if stage_name not in {stage.name for stage in self.stages}:
            raise ValueError(f"Unknown stage: {stage_name}")

        stage_index = next(
            index for index, stage in enumerate(self.stages)
            if stage.name == stage_name
        )

        if stage_index == 0:
            raise ValueError("The entry stage has no previous stage.")

        previous_stage = self.stages[stage_index - 1]
        target_stage = self.stages[stage_index]

        grouped: dict[str, list[CustomerJourney]] = defaultdict(list)

        for journey in self.journeys:
            grouped[journey.segment].append(journey)

        result = {}

        for segment, journeys in grouped.items():
            previous_count = sum(
                journey.reached(previous_stage) for journey in journeys
            )
            target_count = sum(
                journey.reached(target_stage) for journey in journeys
            )

            conversion = self._percentage(target_count, previous_count)
            result[segment] = 1.0 - conversion

        return result

    def time_to_conversion(self) -> dict[str, float | None]:
        entry_stage = self.stages[0]
        final_stage = self.stages[-1]

        durations = []

        for journey in self.journeys:
            start = journey.timestamp(entry_stage)
            end = journey.timestamp(final_stage)

            if start and end:
                durations.append((end - start).total_seconds())

        if not durations:
            return {
                "count": 0,
                "mean_seconds": None,
                "median_seconds": None,
                "minimum_seconds": None,
                "maximum_seconds": None,
            }

        return {
            "count": len(durations),
            "mean_seconds": statistics.mean(durations),
            "median_seconds": statistics.median(durations),
            "minimum_seconds": min(durations),
            "maximum_seconds": max(durations),
        }

    def revenue_metrics(self) -> dict[str, float]:
        converters = [
            journey
            for journey in self.journeys
            if journey.reached(self.stages[-1])
        ]

        revenue = sum(journey.revenue for journey in converters)

        return {
            "converters": len(converters),
            "total_revenue": revenue,
            "average_revenue_per_converter": (
                revenue / len(converters) if converters else 0.0
            ),
        }

    def identify_largest_dropoff(self) -> FunnelMetrics | None:
        metrics = self.stage_metrics()

        eligible = [
            metric
            for metric in metrics
            if metric.drop_off_from_previous is not None
        ]

        if not eligible:
            return None

        return max(
            eligible,
            key=lambda metric: metric.drop_off_from_previous or 0.0,
        )

    def customer_paths(self) -> Counter[str]:
        paths = Counter()

        for journey in self.journeys:
            path = " → ".join(
                stage.name
                for stage in self.stages
                if journey.reached(stage)
            )
            paths[path] += 1

        return paths

    def export_json(self, path: str | Path) -> None:
        metrics = self.stage_metrics()

        payload = {
            "overall_conversion": self.overall_conversion(),
            "stages": [
                {
                    "stage": metric.stage_name,
                    "reached_users": metric.reached_users,
                    "previous_stage_users": metric.previous_stage_users,
                    "conversion_from_previous": metric.conversion_from_previous,
                    "conversion_from_entry": metric.conversion_from_entry,
                    "drop_off_from_previous": metric.drop_off_from_previous,
                    "median_seconds_from_previous": metric.median_seconds_from_previous,
                }
                for metric in metrics
            ],
            "segments": [
                {
                    "segment": report.segment,
                    "users": report.users,
                    "converters": report.converters,
                    "conversion_rate": report.conversion_rate,
                    "revenue": report.revenue,
                }
                for report in self.segment_analysis()
            ],
            "time_to_conversion": self.time_to_conversion(),
            "revenue": self.revenue_metrics(),
            "customer_paths": dict(self.customer_paths()),
        }

        Path(path).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def export_stage_csv(self, path: str | Path) -> None:
        metrics = self.stage_metrics()

        with Path(path).open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "stage",
                    "reached_users",
                    "previous_stage_users",
                    "conversion_from_previous",
                    "conversion_from_entry",
                    "drop_off_from_previous",
                    "median_seconds_from_previous",
                ],
            )
            writer.writeheader()

            for metric in metrics:
                writer.writerow(
                    {
                        "stage": metric.stage_name,
                        "reached_users": metric.reached_users,
                        "previous_stage_users": metric.previous_stage_users,
                        "conversion_from_previous": metric.conversion_from_previous,
                        "conversion_from_entry": metric.conversion_from_entry,
                        "drop_off_from_previous": metric.drop_off_from_previous,
                        "median_seconds_from_previous": metric.median_seconds_from_previous,
                    }
                )


def parse_event(timestamp: str) -> datetime:
    value = datetime.fromisoformat(timestamp)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value


def build_demo_data() -> list[CustomerJourney]:
    base = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)

    def event(minutes: int) -> datetime:
        return base + timedelta(minutes=minutes)

    return [
        CustomerJourney(
            "C001",
            "mobile",
            {
                "Visited Landing Page": event(0),
                "Viewed Product": event(4),
                "Added to Cart": event(9),
                "Started Checkout": event(15),
                "Purchased": event(23),
            },
            129.00,
        ),
        CustomerJourney(
            "C002",
            "mobile",
            {
                "Visited Landing Page": event(1),
                "Viewed Product": event(6),
                "Added to Cart": event(12),
                "Started Checkout": event(21),
            },
        ),
        CustomerJourney(
            "C003",
            "desktop",
            {
                "Visited Landing Page": event(2),
                "Viewed Product": event(5),
                "Added to Cart": event(14),
                "Started Checkout": event(20),
                "Purchased": event(32),
            },
            249.00,
        ),
        CustomerJourney(
            "C004",
            "desktop",
            {
                "Visited Landing Page": event(3),
                "Viewed Product": event(8),
            },
        ),
        CustomerJourney(
            "C005",
            "mobile",
            {
                "Visited Landing Page": event(10),
                "Viewed Product": event(14),
                "Added to Cart": event(19),
            },
        ),
        CustomerJourney(
            "C006",
            "desktop",
            {
                "Visited Landing Page": event(11),
                "Viewed Product": event(16),
                "Added to Cart": event(22),
                "Started Checkout": event(30),
                "Purchased": event(41),
            },
            89.00,
        ),
        CustomerJourney(
            "C007",
            "tablet",
            {
                "Visited Landing Page": event(13),
                "Viewed Product": event(18),
                "Added to Cart": event(26),
                "Started Checkout": event(40),
            },
        ),
        CustomerJourney(
            "C008",
            "tablet",
            {
                "Visited Landing Page": event(15),
                "Viewed Product": event(21),
            },
        ),
        CustomerJourney(
            "C009",
            "mobile",
            {
                "Visited Landing Page": event(18),
                "Viewed Product": event(23),
                "Added to Cart": event(31),
                "Started Checkout": event(37),
                "Purchased": event(48),
            },
            159.00,
        ),
        CustomerJourney(
            "C010",
            "desktop",
            {
                "Visited Landing Page": event(20),
                "Viewed Product": event(24),
                "Added to Cart": event(30),
            },
        ),
    ]


def print_report(analyzer: FunnelAnalyzer) -> None:
    print("\nFUNNEL ANALYSIS")
    print("=" * 72)

    for metric in analyzer.stage_metrics():
        previous_conversion = (
            "n/a"
            if metric.conversion_from_previous is None
            else f"{metric.conversion_from_previous:.1%}"
        )

        dropoff = (
            "n/a"
            if metric.drop_off_from_previous is None
            else f"{metric.drop_off_from_previous:.1%}"
        )

        entry_conversion = f"{metric.conversion_from_entry:.1%}"

        print(
            f"{metric.stage_name:<24}"
            f" users={metric.reached_users:<3} "
            f"previous_conversion={previous_conversion:<7} "
            f"entry_conversion={entry_conversion:<7} "
            f"dropoff={dropoff}"
        )

    largest = analyzer.identify_largest_dropoff()

    if largest:
        print(
            f"\nLargest stage drop-off: {largest.stage_name} "
            f"({largest.drop_off_from_previous:.1%})"
        )

    print("\nSEGMENT PERFORMANCE")
    print("-" * 72)

    for report in analyzer.segment_analysis():
        print(
            f"{report.segment:<10}"
            f" users={report.users:<3}"
            f" converters={report.converters:<3}"
            f" conversion={report.conversion_rate:.1%}"
            f" revenue=${report.revenue:,.2f}"
        )

    print("\nTIME TO CONVERSION")
    print("-" * 72)

    timing = analyzer.time_to_conversion()

    if timing["count"]:
        print(f"Converted journeys: {int(timing['count'])}")
        print(f"Mean: {timing['mean_seconds'] / 60:.1f} minutes")
        print(f"Median: {timing['median_seconds'] / 60:.1f} minutes")
        print(f"Minimum: {timing['minimum_seconds'] / 60:.1f} minutes")
        print(f"Maximum: {timing['maximum_seconds'] / 60:.1f} minutes")

    revenue = analyzer.revenue_metrics()

    print("\nREVENUE")
    print("-" * 72)
    print(f"Total revenue from converters: ${revenue['total_revenue']:,.2f}")
    print(
        f"Average revenue per converter: "
        f"${revenue['average_revenue_per_converter']:,.2f}"
    )

    print("\nOBSERVED CUSTOMER PATHS")
    print("-" * 72)

    for path, count in analyzer.customer_paths().most_common():
        print(f"{count:>3}  {path}")

    print("\nSEGMENT DROP-OFF AT CHECKOUT")
    print("-" * 72)

    for segment, dropoff in analyzer.stage_dropoff_by_segment(
        "Started Checkout"
    ).items():
        print(f"{segment:<10} {dropoff:.1%}")


def demonstrate_validation() -> None:
    print("\nVALIDATION EXAMPLE")
    print("=" * 72)

    stages = [
        FunnelStage("Visited Landing Page", 1),
        FunnelStage("Viewed Product", 2),
        FunnelStage("Added to Cart", 3),
        FunnelStage("Started Checkout", 4),
        FunnelStage("Purchased", 5),
    ]

    invalid_journey = CustomerJourney(
        "INVALID",
        "mobile",
        {
            "Visited Landing Page": parse_event("2026-10-01T10:00:00+00:00"),
            "Viewed Product": parse_event("2026-10-01T09:50:00+00:00"),
        },
    )

    try:
        FunnelAnalyzer(stages, [invalid_journey])
    except ValueError as error:
        print(f"Rejected invalid journey: {error}")


def main() -> None:
    stages = [
        FunnelStage("Visited Landing Page", 1),
        FunnelStage("Viewed Product", 2),
        FunnelStage("Added to Cart", 3),
        FunnelStage("Started Checkout", 4),
        FunnelStage("Purchased", 5),
    ]

    analyzer = FunnelAnalyzer(stages, build_demo_data())
    print_report(analyzer)
    demonstrate_validation()

    output_directory = Path("funnel_output")
    output_directory.mkdir(exist_ok=True)

    analyzer.export_json(output_directory / "funnel_report.json")
    analyzer.export_stage_csv(output_directory / "funnel_stage_metrics.csv")

    print("\nREPORT FILES")
    print("=" * 72)
    print(f"JSON: {output_directory / 'funnel_report.json'}")
    print(f"CSV : {output_directory / 'funnel_stage_metrics.csv'}")


if __name__ == "__main__":
    main()
