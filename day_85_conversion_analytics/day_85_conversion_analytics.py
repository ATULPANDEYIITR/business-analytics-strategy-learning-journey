#!/usr/bin/env python3
"""
Conversion Analytics and Funnel Optimization
Python 3.10+

Implements:
- Conversion rate measurement
- Multi-stage funnel analysis
- Step-by-step drop-off analysis
- Cohort conversion analysis
- Channel and campaign attribution
- A/B experiment evaluation
- Funnel optimization recommendations
- Event validation and deduplication
- CSV reporting
- Unit-style assertions
"""

from __future__ import annotations

import csv
import json
import logging
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("conversion_analytics")


# ---------------------------------------------------------
# 1. DOMAIN TYPES
# ---------------------------------------------------------

class EventType(str, Enum):
    VISIT = "visit"
    PRODUCT_VIEW = "product_view"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT = "checkout"
    PURCHASE = "purchase"


FUNNEL_STAGES = [
    EventType.VISIT,
    EventType.PRODUCT_VIEW,
    EventType.ADD_TO_CART,
    EventType.CHECKOUT,
    EventType.PURCHASE,
]


@dataclass(frozen=True)
class AnalyticsEvent:
    event_id: str
    user_id: str
    event_type: EventType
    timestamp: datetime
    channel: str
    campaign: str
    experiment: str = "control"
    revenue: float = 0.0

    def __post_init__(self):
        if not self.event_id.strip():
            raise ValueError("Event ID cannot be empty")

        if not self.user_id.strip():
            raise ValueError("User ID cannot be empty")

        if self.timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")

        if not self.channel.strip():
            raise ValueError("Channel cannot be empty")

        if not math.isfinite(self.revenue) or self.revenue < 0:
            raise ValueError("Revenue must be finite and non-negative")

        if self.event_type != EventType.PURCHASE and self.revenue != 0:
            raise ValueError("Revenue is only allowed on purchase events")


@dataclass
class FunnelStepResult:
    stage: str
    users: int
    previous_users: int
    conversion_rate: float
    drop_off_rate: float


@dataclass
class FunnelReport:
    total_users: int
    converted_users: int
    conversion_rate: float
    steps: list[FunnelStepResult] = field(default_factory=list)


# ---------------------------------------------------------
# 2. EVENT COLLECTION AND VALIDATION
# ---------------------------------------------------------

class EventStore:
    def __init__(self):
        self.events: list[AnalyticsEvent] = []
        self.event_ids: set[str] = set()

    def add(self, event: AnalyticsEvent) -> bool:
        """Return False when an event has already been ingested."""

        if event.event_id in self.event_ids:
            logger.warning("Duplicate event ignored: %s", event.event_id)
            return False

        self.event_ids.add(event.event_id)
        self.events.append(event)
        return True

    def add_many(self, events: list[AnalyticsEvent]) -> int:
        accepted = 0

        for event in events:
            if self.add(event):
                accepted += 1

        return accepted

    def between(
        self,
        start: datetime,
        end: datetime
    ) -> list[AnalyticsEvent]:

        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Date filters must be timezone-aware")

        if start >= end:
            raise ValueError("Start must be earlier than end")

        return [
            event for event in self.events
            if start <= event.timestamp < end
        ]


# ---------------------------------------------------------
# 3. CONVERSION METRICS
# ---------------------------------------------------------

def conversion_rate(
    converted: int,
    eligible: int
) -> float:

    if eligible < 0 or converted < 0:
        raise ValueError("Counts cannot be negative")

    if converted > eligible:
        raise ValueError("Conversions cannot exceed eligible users")

    if eligible == 0:
        return 0.0

    return converted / eligible * 100


def revenue_per_user(revenue: float, users: int) -> float:
    if not math.isfinite(revenue) or revenue < 0 or users < 0:
        raise ValueError("Invalid revenue or user count")

    return revenue / users if users else 0.0


def average_order_value(revenue: float, orders: int) -> float:
    if not math.isfinite(revenue) or revenue < 0 or orders < 0:
        raise ValueError("Invalid revenue or order count")

    return revenue / orders if orders else 0.0


# ---------------------------------------------------------
# 4. FUNNEL ANALYSIS
# ---------------------------------------------------------

class FunnelAnalyzer:
    def __init__(self, stages: list[EventType]):
        if not stages or len(set(stages)) != len(stages):
            raise ValueError("Funnel stages must be non-empty and unique")

        self.stages = stages

    def analyze(
        self,
        events: list[AnalyticsEvent]
    ) -> FunnelReport:

        user_stages: dict[str, set[EventType]] = defaultdict(set)

        for event in events:
            if event.event_type in self.stages:
                user_stages[event.user_id].add(event.event_type)

        # Each stage counts users who reached every preceding stage.
        # Event timestamps are also checked to prevent invalid sequences.
        user_timestamps: dict[str, dict[EventType, datetime]] = defaultdict(dict)

        for event in events:
            if event.event_type not in self.stages:
                continue

            current = user_timestamps[event.user_id].get(event.event_type)

            if current is None or event.timestamp < current:
                user_timestamps[event.user_id][event.event_type] = (
                    event.timestamp
                )

        stage_counts = []

        for user_id, timestamps in user_timestamps.items():
            reached = True
            previous_time: Optional[datetime] = None
            reached_count = 0

            for stage in self.stages:
                timestamp = timestamps.get(stage)

                if timestamp is None:
                    reached = False
                    break

                if previous_time is not None and timestamp < previous_time:
                    reached = False
                    break

                previous_time = timestamp
                reached_count += 1

            stage_counts.append(reached_count)

        total_users = sum(
            EventType.VISIT in stages
            for stages in user_stages.values()
        )

        counts = []

        for index in range(len(self.stages)):
            count = sum(
                reached_count > index
                for reached_count in stage_counts
            )
            counts.append(count)

        if total_users == 0:
            return FunnelReport(0, 0, 0.0, [])

        results = []
        previous_users = total_users

        for index, stage in enumerate(self.stages):
            current_users = counts[index]

            rate = (
                current_users / previous_users * 100
                if previous_users else 0.0
            )

            drop_off = 100 - rate if previous_users else 0.0

            results.append(
                FunnelStepResult(
                    stage=stage.value,
                    users=current_users,
                    previous_users=previous_users,
                    conversion_rate=round(rate, 2),
                    drop_off_rate=round(drop_off, 2)
                )
            )

            previous_users = current_users

        converted = counts[-1]

        return FunnelReport(
            total_users=total_users,
            converted_users=converted,
            conversion_rate=round(
                conversion_rate(converted, total_users), 2
            ),
            steps=results
        )


# ---------------------------------------------------------
# 5. CHANNEL AND CAMPAIGN ANALYSIS
# ---------------------------------------------------------

def channel_analysis(
    events: list[AnalyticsEvent]
) -> dict[str, dict]:

    visits = defaultdict(set)
    purchases = defaultdict(set)
    revenue = defaultdict(float)

    for event in events:
        if event.event_type == EventType.VISIT:
            visits[event.channel].add(event.user_id)

        elif event.event_type == EventType.PURCHASE:
            purchases[event.channel].add(event.user_id)
            revenue[event.channel] += event.revenue

    results = {}

    for channel, users in visits.items():
        converted = len(purchases[channel] & users)

        results[channel] = {
            "visitors": len(users),
            "conversions": converted,
            "conversion_rate": round(
                conversion_rate(converted, len(users)), 2
            ),
            "revenue": round(revenue[channel], 2),
            "revenue_per_visitor": round(
                revenue_per_user(revenue[channel], len(users)), 2
            )
        }

    return results


def campaign_analysis(
    events: list[AnalyticsEvent]
) -> dict[str, dict]:

    campaigns = defaultdict(lambda: {
        "visitors": set(),
        "buyers": set(),
        "revenue": 0.0
    })

    for event in events:
        campaign = campaigns[event.campaign]

        if event.event_type == EventType.VISIT:
            campaign["visitors"].add(event.user_id)

        elif event.event_type == EventType.PURCHASE:
            campaign["buyers"].add(event.user_id)
            campaign["revenue"] += event.revenue

    results = {}

    for name, data in campaigns.items():
        visitors = data["visitors"]
        buyers = data["buyers"] & visitors

        results[name] = {
            "visitors": len(visitors),
            "buyers": len(buyers),
            "conversion_rate": round(
                conversion_rate(len(buyers), len(visitors)), 2
            ),
            "revenue": round(data["revenue"], 2)
        }

    return results


# ---------------------------------------------------------
# 6. COHORT ANALYSIS
# ---------------------------------------------------------

def cohort_analysis(
    events: list[AnalyticsEvent]
) -> dict[str, dict]:

    first_visit = {}
    purchased = set()

    for event in events:
        if event.event_type == EventType.VISIT:
            existing = first_visit.get(event.user_id)

            if existing is None or event.timestamp < existing:
                first_visit[event.user_id] = event.timestamp

        elif event.event_type == EventType.PURCHASE:
            purchased.add(event.user_id)

    cohorts = defaultdict(set)

    for user_id, timestamp in first_visit.items():
        month = timestamp.strftime("%Y-%m")
        cohorts[month].add(user_id)

    results = {}

    for month, users in sorted(cohorts.items()):
        buyers = users & purchased

        results[month] = {
            "users": len(users),
            "buyers": len(buyers),
            "conversion_rate": round(
                conversion_rate(len(buyers), len(users)), 2
            )
        }

    return results


# ---------------------------------------------------------
# 7. A/B TESTING
# ---------------------------------------------------------

def normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def ab_test(
    control_conversions: int,
    control_users: int,
    treatment_conversions: int,
    treatment_users: int
) -> dict:

    for converted, users in [
        (control_conversions, control_users),
        (treatment_conversions, treatment_users)
    ]:
        if users <= 0 or converted < 0 or converted > users:
            raise ValueError("Invalid experiment counts")

    p1 = control_conversions / control_users
    p2 = treatment_conversions / treatment_users

    pooled = (
        control_conversions + treatment_conversions
    ) / (control_users + treatment_users)

    standard_error = math.sqrt(
        pooled * (1 - pooled) *
        (1 / control_users + 1 / treatment_users)
    )

    z_score = (
        (p2 - p1) / standard_error
        if standard_error else 0.0
    )

    p_value = 2 * (1 - normal_cdf(abs(z_score)))

    relative_lift = (
        (p2 - p1) / p1 * 100
        if p1 else None
    )

    return {
        "control_rate": round(p1 * 100, 2),
        "treatment_rate": round(p2 * 100, 2),
        "absolute_lift_percentage_points": round(
            (p2 - p1) * 100, 2
        ),
        "relative_lift_percent": (
            round(relative_lift, 2)
            if relative_lift is not None else None
        ),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 6),
        "significant_at_5_percent": p_value < 0.05
    }


# ---------------------------------------------------------
# 8. OPTIMIZATION RECOMMENDATIONS
# ---------------------------------------------------------

def optimization_recommendations(
    report: FunnelReport
) -> list[str]:

    if not report.steps:
        return ["Collect sufficient funnel data before optimization."]

    weakest = max(
        report.steps,
        key=lambda step: step.drop_off_rate
    )

    recommendations = []

    if weakest.drop_off_rate >= 50:
        recommendations.append(
            f"Investigate the {weakest.stage} stage: "
            f"{weakest.drop_off_rate}% drop-off."
        )

    if report.conversion_rate < 2:
        recommendations.append(
            "Inspect acquisition quality, page relevance, "
            "and purchase friction."
        )

    if not recommendations:
        recommendations.append(
            "Monitor the funnel and test one measurable improvement."
        )

    recommendations.append(
        "Validate changes through controlled experiments."
    )

    return recommendations


# ---------------------------------------------------------
# 9. CSV REPORTING
# ---------------------------------------------------------

def export_funnel_csv(
    report: FunnelReport,
    filename: str = "funnel_report.csv"
) -> None:

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Stage",
            "Users",
            "Previous Users",
            "Conversion Rate (%)",
            "Drop Off Rate (%)"
        ])

        for step in report.steps:
            writer.writerow([
                step.stage,
                step.users,
                step.previous_users,
                step.conversion_rate,
                step.drop_off_rate
            ])


# ---------------------------------------------------------
# 10. REALISTIC DATASET
# ---------------------------------------------------------

def create_sample_events() -> list[AnalyticsEvent]:

    base = datetime(2026, 11, 1, 10, tzinfo=timezone.utc)

    records = [
        ("u1", ["visit", "product_view", "add_to_cart", "checkout", "purchase"], "organic", "seo", 2500),
        ("u2", ["visit", "product_view", "add_to_cart", "checkout"], "paid", "search_ads", 0),
        ("u3", ["visit", "product_view", "add_to_cart", "purchase"], "organic", "seo", 1800),
        ("u4", ["visit", "product_view"], "social", "social_ads", 0),
        ("u5", ["visit", "product_view", "add_to_cart", "checkout", "purchase"], "paid", "search_ads", 3200),
        ("u6", ["visit", "product_view"], "social", "social_ads", 0),
        ("u7", ["visit", "product_view", "add_to_cart", "checkout", "purchase"], "organic", "seo", 1500),
        ("u8", ["visit", "product_view", "add_to_cart"], "paid", "search_ads", 0),
        ("u9", ["visit"], "referral", "partner", 0),
        ("u10", ["visit", "product_view", "add_to_cart", "checkout", "purchase"], "organic", "seo", 4100),
    ]

    events = []

    for user_index, record in enumerate(records):
        user_id, stages, channel, campaign, revenue = record

        for index, stage_name in enumerate(stages):
            events.append(
                AnalyticsEvent(
                    event_id=f"evt-{user_id}-{index}",
                    user_id=user_id,
                    event_type=EventType(stage_name),
                    timestamp=base + timedelta(
                        minutes=user_index * 20 + index * 5
                    ),
                    channel=channel,
                    campaign=campaign,
                    revenue=(
                        revenue if stage_name == "purchase" else 0
                    )
                )
            )

    return events


# ---------------------------------------------------------
# 11. MAIN EXECUTION
# ---------------------------------------------------------

def main():

    store = EventStore()
    events = create_sample_events()

    accepted = store.add_many(events)

    logger.info("Accepted events: %d", accepted)

    report = FunnelAnalyzer(FUNNEL_STAGES).analyze(store.events)

    print("\nCONVERSION FUNNEL")
    print("=" * 65)
    print(f"Visitors: {report.total_users}")
    print(f"Purchasers: {report.converted_users}")
    print(f"Overall conversion: {report.conversion_rate}%")

    for step in report.steps:
        print(
            f"{step.stage:15} | "
            f"{step.users:3} users | "
            f"{step.conversion_rate:6.2f}% step conversion | "
            f"{step.drop_off_rate:6.2f}% drop-off"
        )

    print("\nCHANNEL PERFORMANCE")
    print(json.dumps(channel_analysis(store.events), indent=2))

    print("\nCAMPAIGN PERFORMANCE")
    print(json.dumps(campaign_analysis(store.events), indent=2))

    print("\nCOHORT PERFORMANCE")
    print(json.dumps(cohort_analysis(store.events), indent=2))

    print("\nA/B EXPERIMENT")
    experiment = ab_test(120, 2000, 150, 2000)
    print(json.dumps(experiment, indent=2))

    print("\nOPTIMIZATION RECOMMENDATIONS")
    for recommendation in optimization_recommendations(report):
        print("-", recommendation)

    export_funnel_csv(report)

    # Fundamental metric checks.
    assert conversion_rate(25, 100) == 25.0
    assert conversion_rate(0, 0) == 0.0
    assert average_order_value(5000, 5) == 1000
    assert report.total_users == 10
    assert report.converted_users == 4
    assert report.steps[-1].users == 4

    # Duplicate ingestion must not increase the event count.
    assert store.add(events[0]) is False

    print("\nAll validation checks passed.")
    print("Report saved to funnel_report.csv")


if __name__ == "__main__":
    main()
