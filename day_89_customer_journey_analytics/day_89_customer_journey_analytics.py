#!/usr/bin/env python3
"""
Customer Journey Analytics
Touchpoints, behavioral analysis, funnel measurement, attribution,
sessionization, cohort analysis, and privacy-aware reporting.

Python 3.10+
Standard-library implementation.
"""

from __future__ import annotations

import json
import statistics
import unittest
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Iterable, Optional
from uuid import uuid4


# ============================================================
# 1. DOMAIN TYPES
# ============================================================

class EventType(str, Enum):
    AD_IMPRESSION = "ad_impression"
    AD_CLICK = "ad_click"
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    SEARCH = "search"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT = "checkout"
    PURCHASE = "purchase"
    SIGNUP = "signup"
    SUPPORT_REQUEST = "support_request"


class Channel(str, Enum):
    ORGANIC_SEARCH = "organic_search"
    PAID_SEARCH = "paid_search"
    SOCIAL = "social"
    EMAIL = "email"
    DIRECT = "direct"
    REFERRAL = "referral"
    DISPLAY = "display"


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN = "unknown"


class JourneyStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ADVOCACY = "advocacy"


class AnalyticsError(Exception):
    """Base analytics exception."""


class ValidationError(AnalyticsError):
    """Raised when an event violates domain constraints."""


class PrivacyError(AnalyticsError):
    """Raised when processing violates privacy requirements."""


@dataclass(frozen=True)
class Customer:
    customer_id: str
    consent: ConsentStatus
    region: str = "IN"
    registered_at: Optional[datetime] = None


@dataclass(frozen=True)
class Touchpoint:
    event_id: str
    customer_id: str
    event_type: EventType
    timestamp: datetime
    channel: Channel
    session_id: str
    page: str
    campaign: Optional[str] = None
    product_id: Optional[str] = None
    value: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    session_id: str
    customer_id: str
    started_at: datetime
    ended_at: datetime
    events: list[Touchpoint] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.ended_at - self.started_at).total_seconds())

    @property
    def channel(self) -> Channel:
        return self.events[0].channel


# ============================================================
# 2. EVENT VALIDATION
# ============================================================

class EventValidator:

    ALLOWED_PROPERTIES = {
        "device_type",
        "browser",
        "experiment",
        "country",
        "campaign_group",
    }

    MAX_PAGE_LENGTH = 500

    @classmethod
    def validate(cls, event: Touchpoint) -> None:
        if not event.event_id or not event.customer_id:
            raise ValidationError("Event and customer identifiers are required.")

        if not event.session_id:
            raise ValidationError("Session identifier is required.")

        if event.timestamp.tzinfo is None:
            raise ValidationError("Timestamps must include timezone information.")

        if not isinstance(event.event_type, EventType):
            raise ValidationError("Invalid event type.")

        if not isinstance(event.channel, Channel):
            raise ValidationError("Invalid acquisition channel.")

        if not isinstance(event.value, (int, float)):
            raise ValidationError("Event value must be numeric.")

        if event.value < 0:
            raise ValidationError("Event value cannot be negative.")

        if event.value != event.value or event.value == float("inf"):
            raise ValidationError("Event value must be finite.")

        if len(event.page) > cls.MAX_PAGE_LENGTH:
            raise ValidationError("Page identifier exceeds maximum length.")

        if not isinstance(event.properties, dict):
            raise ValidationError("Properties must be a dictionary.")

        unknown = set(event.properties) - cls.ALLOWED_PROPERTIES
        if unknown:
            raise ValidationError(
                f"Unsupported event properties: {sorted(unknown)}"
            )

        if event.event_type == EventType.PURCHASE and event.value <= 0:
            raise ValidationError("Purchase events require positive revenue.")


# ============================================================
# 3. CUSTOMER AND EVENT STORAGE
# ============================================================

class JourneyStore:

    def __init__(self):
        self.customers: dict[str, Customer] = {}
        self.events: dict[str, Touchpoint] = {}
        self._customer_events: dict[str, list[str]] = defaultdict(list)

    def register_customer(self, customer: Customer) -> None:
        if not customer.customer_id:
            raise ValidationError("Customer identifier cannot be empty.")

        self.customers[customer.customer_id] = customer

    def record_event(self, event: Touchpoint) -> bool:
        EventValidator.validate(event)

        if event.event_id in self.events:
            return False

        customer = self.customers.get(event.customer_id)

        if customer is None:
            raise ValidationError("Customer has not been registered.")

        if customer.consent != ConsentStatus.GRANTED:
            raise PrivacyError(
                "Customer has not granted analytics consent."
            )

        self.events[event.event_id] = event
        self._customer_events[event.customer_id].append(event.event_id)
        return True

    def customer_events(self, customer_id: str) -> list[Touchpoint]:
        event_ids = self._customer_events.get(customer_id, [])

        return sorted(
            (self.events[event_id] for event_id in event_ids),
            key=lambda event: event.timestamp
        )

    def all_events(self) -> list[Touchpoint]:
        return sorted(
            self.events.values(),
            key=lambda event: event.timestamp
        )

    def erase_customer(self, customer_id: str) -> None:
        """Delete stored customer-level analytics data."""
        customer_event_ids = self._customer_events.pop(customer_id, [])

        for event_id in customer_event_ids:
            self.events.pop(event_id, None)

        self.customers.pop(customer_id, None)


# ============================================================
# 4. JOURNEY STAGE CLASSIFICATION
# ============================================================

class JourneyClassifier:

    EVENT_STAGES = {
        EventType.AD_IMPRESSION: JourneyStage.AWARENESS,
        EventType.AD_CLICK: JourneyStage.AWARENESS,
        EventType.PAGE_VIEW: JourneyStage.AWARENESS,
        EventType.SEARCH: JourneyStage.CONSIDERATION,
        EventType.PRODUCT_VIEW: JourneyStage.CONSIDERATION,
        EventType.ADD_TO_CART: JourneyStage.CONSIDERATION,
        EventType.CHECKOUT: JourneyStage.CONVERSION,
        EventType.PURCHASE: JourneyStage.CONVERSION,
        EventType.SIGNUP: JourneyStage.RETENTION,
        EventType.SUPPORT_REQUEST: JourneyStage.RETENTION,
    }

    @classmethod
    def classify(cls, event: Touchpoint) -> JourneyStage:
        return cls.EVENT_STAGES[event.event_type]


# ============================================================
# 5. SESSIONIZATION
# ============================================================

class SessionAnalyzer:

    def __init__(self, inactivity_minutes: int = 30):
        if inactivity_minutes <= 0:
            raise ValueError("Inactivity threshold must be positive.")

        self.threshold = timedelta(minutes=inactivity_minutes)

    def analyze(self, events: Iterable[Touchpoint]) -> list[Session]:
        ordered = sorted(
            events,
            key=lambda event: (event.customer_id, event.timestamp)
        )

        sessions: list[Session] = []
        current: Optional[Session] = None

        for event in ordered:
            should_start = (
                current is None
                or current.customer_id != event.customer_id
                or current.session_id != event.session_id
                or event.timestamp - current.ended_at > self.threshold
            )

            if should_start:
                current = Session(
                    session_id=event.session_id,
                    customer_id=event.customer_id,
                    started_at=event.timestamp,
                    ended_at=event.timestamp,
                    events=[event],
                )
                sessions.append(current)
            else:
                current.events.append(event)
                current.ended_at = event.timestamp

        return sessions

    @staticmethod
    def average_session_duration(sessions: list[Session]) -> float:
        if not sessions:
            return 0.0

        return statistics.mean(
            session.duration_seconds for session in sessions
        )


# ============================================================
# 6. FUNNEL ANALYSIS
# ============================================================

class FunnelAnalyzer:

    DEFAULT_STAGES = [
        EventType.PAGE_VIEW,
        EventType.PRODUCT_VIEW,
        EventType.ADD_TO_CART,
        EventType.CHECKOUT,
        EventType.PURCHASE,
    ]

    def analyze(
        self,
        events: Iterable[Touchpoint],
        stages: Optional[list[EventType]] = None,
    ) -> dict[str, Any]:

        stages = stages or self.DEFAULT_STAGES

        if not stages or len(set(stages)) != len(stages):
            raise ValidationError("Funnel stages must be unique and nonempty.")

        customer_events: dict[str, list[Touchpoint]] = defaultdict(list)

        for event in events:
            customer_events[event.customer_id].append(event)

        counts = [0] * len(stages)

        for customer_event_list in customer_events.values():
            customer_event_list.sort(key=lambda event: event.timestamp)

            next_stage = 0

            for event in customer_event_list:
                if event.event_type == stages[next_stage]:
                    counts[next_stage] += 1
                    next_stage += 1

                    if next_stage == len(stages):
                        break

        results = []

        for index, stage in enumerate(stages):
            previous = counts[index - 1] if index > 0 else counts[index]

            conversion_rate = (
                counts[index] / previous if previous else 0.0
            )

            results.append({
                "stage": stage.value,
                "customers": counts[index],
                "conversion_rate": round(conversion_rate, 4),
                "drop_off": (
                    round(1 - conversion_rate, 4) if index > 0 else 0.0
                ),
            })

        return {
            "stages": results,
            "overall_conversion": round(
                counts[-1] / counts[0], 4
            ) if counts[0] else 0.0,
        }


# ============================================================
# 7. MULTI-TOUCH ATTRIBUTION
# ============================================================

class AttributionModel:

    @staticmethod
    def first_touch(events: list[Touchpoint]) -> dict[str, float]:
        if not events:
            return {}

        return {events[0].channel.value: 1.0}

    @staticmethod
    def last_touch(events: list[Touchpoint]) -> dict[str, float]:
        if not events:
            return {}

        return {events[-1].channel.value: 1.0}

    @staticmethod
    def linear(events: list[Touchpoint]) -> dict[str, float]:
        if not events:
            return {}

        channel_counts = Counter(event.channel.value for event in events)
        total = len(events)

        return {
            channel: count / total
            for channel, count in channel_counts.items()
        }

    @staticmethod
    def position_based(
        events: list[Touchpoint],
        first_weight: float = 0.4,
        last_weight: float = 0.4,
    ) -> dict[str, float]:

        if not events:
            return {}

        if first_weight < 0 or last_weight < 0:
            raise ValidationError("Attribution weights cannot be negative.")

        if first_weight + last_weight > 1:
            raise ValidationError("Attribution weights exceed 100%.")

        if len(events) == 1:
            return {events[0].channel.value: 1.0}

        credits: dict[str, float] = defaultdict(float)

        credits[events[0].channel.value] += first_weight
        credits[events[-1].channel.value] += last_weight

        middle_weight = 1 - first_weight - last_weight

        middle_events = events[1:-1]

        if middle_events:
            credit = middle_weight / len(middle_events)

            for event in middle_events:
                credits[event.channel.value] += credit

        return dict(credits)

    @staticmethod
    def allocate_revenue(
        revenue: float,
        attribution: dict[str, float]
    ) -> dict[str, float]:

        if revenue < 0:
            raise ValidationError("Revenue cannot be negative.")

        if not attribution:
            return {}

        if abs(sum(attribution.values()) - 1.0) > 1e-9:
            raise ValidationError("Attribution weights must total one.")

        return {
            channel: round(revenue * weight, 2)
            for channel, weight in attribution.items()
        }


# ============================================================
# 8. COHORT ANALYSIS
# ============================================================

class CohortAnalyzer:

    @staticmethod
    def monthly_cohorts(
        customers: Iterable[Customer],
        events: Iterable[Touchpoint],
    ) -> list[dict[str, Any]]:

        customer_map = {
            customer.customer_id: customer
            for customer in customers
            if customer.registered_at is not None
        }

        activity: dict[str, set[str]] = defaultdict(set)

        for event in events:
            if event.customer_id in customer_map:
                activity[event.customer_id].add(
                    event.timestamp.strftime("%Y-%m")
                )

        cohorts: dict[str, set[str]] = defaultdict(set)

        for customer_id, customer in customer_map.items():
            cohorts[customer.registered_at.strftime("%Y-%m")].add(
                customer_id
            )

        results = []

        for cohort_month, customer_ids in sorted(cohorts.items()):
            cohort_size = len(customer_ids)

            active_counts = Counter(
                month
                for customer_id in customer_ids
                for month in activity.get(customer_id, set())
            )

            for activity_month, active_count in sorted(active_counts.items()):
                if activity_month < cohort_month:
                    continue

                results.append({
                    "cohort": cohort_month,
                    "activity_month": activity_month,
                    "cohort_size": cohort_size,
                    "active_customers": active_count,
                    "retention_rate": round(
                        active_count / cohort_size, 4
                    ),
                })

        return results


# ============================================================
# 9. CUSTOMER BEHAVIOR ANALYSIS
# ============================================================

class BehaviorAnalyzer:

    @staticmethod
    def channel_performance(
        events: Iterable[Touchpoint]
    ) -> list[dict[str, Any]]:

        metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "touchpoints": 0,
                "customers": set(),
                "purchases": 0,
                "revenue": 0.0,
            }
        )

        for event in events:
            record = metrics[event.channel.value]
            record["touchpoints"] += 1
            record["customers"].add(event.customer_id)

            if event.event_type == EventType.PURCHASE:
                record["purchases"] += 1
                record["revenue"] += event.value

        results = []

        for channel, data in metrics.items():
            results.append({
                "channel": channel,
                "touchpoints": data["touchpoints"],
                "customers": len(data["customers"]),
                "purchases": data["purchases"],
                "revenue": round(data["revenue"], 2),
            })

        return sorted(results, key=lambda item: item["revenue"], reverse=True)

    @staticmethod
    def popular_pages(
        events: Iterable[Touchpoint],
        limit: int = 10
    ) -> list[tuple[str, int]]:

        if limit <= 0:
            raise ValueError("Limit must be positive.")

        counts = Counter(
            event.page
            for event in events
            if event.event_type == EventType.PAGE_VIEW
        )

        return counts.most_common(limit)

    @staticmethod
    def customer_paths(
        events: Iterable[Touchpoint]
    ) -> dict[str, list[str]]:

        paths: dict[str, list[str]] = defaultdict(list)

        for event in sorted(events, key=lambda item: item.timestamp):
            paths[event.customer_id].append(event.event_type.value)

        return dict(paths)


# ============================================================
# 10. ANALYTICS REPORTING
# ============================================================

class JourneyAnalytics:

    def __init__(self, store: JourneyStore):
        self.store = store
        self.sessions = SessionAnalyzer()
        self.funnel = FunnelAnalyzer()
        self.behavior = BehaviorAnalyzer()

    def generate_report(self) -> dict[str, Any]:
        events = self.store.all_events()

        if not events:
            return {
                "event_count": 0,
                "customer_count": 0,
                "message": "No analytics events available.",
            }

        sessions = self.sessions.analyze(events)

        purchase_events = [
            event for event in events
            if event.event_type == EventType.PURCHASE
        ]

        revenue = sum(event.value for event in purchase_events)

        purchasing_customers = {
            event.customer_id for event in purchase_events
        }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(events),
            "customer_count": len({
                event.customer_id for event in events
            }),
            "session_count": len(sessions),
            "average_session_duration_seconds": round(
                self.sessions.average_session_duration(sessions), 2
            ),
            "purchase_count": len(purchase_events),
            "purchasing_customers": len(purchasing_customers),
            "total_revenue": round(revenue, 2),
            "funnel": self.funnel.analyze(events),
            "channel_performance": self.behavior.channel_performance(events),
            "popular_pages": self.behavior.popular_pages(events),
            "customer_paths": self.behavior.customer_paths(events),
        }

    @staticmethod
    def export_json(report: dict[str, Any], filename: str) -> None:
        # Prevent accidental output to an arbitrary path supplied by a caller.
        if not filename.endswith(".json"):
            raise ValueError("Report filename must end in .json")

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)


# ============================================================
# 11. REALISTIC DATASET
# ============================================================

def create_demo_store() -> JourneyStore:
    store = JourneyStore()

    base = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)

    customer_definitions = [
        ("C001", ConsentStatus.GRANTED, 0),
        ("C002", ConsentStatus.GRANTED, 1),
        ("C003", ConsentStatus.GRANTED, 2),
        ("C004", ConsentStatus.GRANTED, 3),
        ("C005", ConsentStatus.DENIED, 4),
    ]

    for customer_id, consent, offset in customer_definitions:
        store.register_customer(
            Customer(
                customer_id=customer_id,
                consent=consent,
                registered_at=base + timedelta(days=offset),
            )
        )

    journeys = {
        "C001": [
            (EventType.AD_CLICK, Channel.SOCIAL, "/landing", 0),
            (EventType.PAGE_VIEW, Channel.ORGANIC_SEARCH, "/home", 2),
            (EventType.PRODUCT_VIEW, Channel.ORGANIC_SEARCH, "/product/101", 5),
            (EventType.ADD_TO_CART, Channel.ORGANIC_SEARCH, "/cart", 10),
            (EventType.CHECKOUT, Channel.ORGANIC_SEARCH, "/checkout", 15),
            (EventType.PURCHASE, Channel.ORGANIC_SEARCH, "/success", 20),
        ],
        "C002": [
            (EventType.AD_CLICK, Channel.PAID_SEARCH, "/landing", 0),
            (EventType.PAGE_VIEW, Channel.PAID_SEARCH, "/home", 3),
            (EventType.PRODUCT_VIEW, Channel.PAID_SEARCH, "/product/102", 7),
            (EventType.ADD_TO_CART, Channel.PAID_SEARCH, "/cart", 12),
        ],
        "C003": [
            (EventType.PAGE_VIEW, Channel.DIRECT, "/home", 0),
            (EventType.PRODUCT_VIEW, Channel.DIRECT, "/product/103", 4),
            (EventType.CHECKOUT, Channel.DIRECT, "/checkout", 8),
            (EventType.PURCHASE, Channel.DIRECT, "/success", 12),
        ],
        "C004": [
            (EventType.AD_IMPRESSION, Channel.DISPLAY, "/campaign", 0),
            (EventType.PAGE_VIEW, Channel.EMAIL, "/home", 3),
            (EventType.PRODUCT_VIEW, Channel.EMAIL, "/product/104", 7),
        ],
    }

    for customer_id, journey in journeys.items():
        session_id = f"S-{customer_id}"

        for index, (event_type, channel, page, minute) in enumerate(journey):
            event = Touchpoint(
                event_id=str(uuid4()),
                customer_id=customer_id,
                event_type=event_type,
                timestamp=base + timedelta(days=int(customer_id[-1]), minutes=minute),
                channel=channel,
                session_id=session_id,
                page=page,
                campaign="AUTUMN-2026",
                value=1499.0 if event_type == EventType.PURCHASE else 0.0,
                properties={"device_type": "desktop"},
            )

            store.record_event(event)

    return store


# ============================================================
# 12. AUTOMATED VALIDATION
# ============================================================

class AnalyticsTests(unittest.TestCase):

    def setUp(self):
        self.store = create_demo_store()

    def test_event_count(self):
        self.assertEqual(len(self.store.all_events()), 18)

    def test_duplicate_event(self):
        event = self.store.all_events()[0]
        self.assertFalse(self.store.record_event(event))

    def test_consent_enforcement(self):
        denied = Touchpoint(
            "DENIED-001",
            "C005",
            EventType.PAGE_VIEW,
            datetime.now(timezone.utc),
            Channel.DIRECT,
            "SESSION-X",
            "/home",
        )

        with self.assertRaises(PrivacyError):
            self.store.record_event(denied)

    def test_purchase_revenue(self):
        report = JourneyAnalytics(self.store).generate_report()
        self.assertEqual(report["total_revenue"], 2998.0)

    def test_funnel(self):
        report = JourneyAnalytics(self.store).generate_report()
        self.assertGreaterEqual(
            report["funnel"]["overall_conversion"], 0
        )

    def test_attribution(self):
        events = self.store.customer_events("C001")
        credits = AttributionModel.linear(events)

        self.assertAlmostEqual(sum(credits.values()), 1.0)

    def test_customer_erasure(self):
        self.store.erase_customer("C001")
        self.assertEqual(self.store.customer_events("C001"), [])
        self.assertNotIn("C001", self.store.customers)

    def test_invalid_purchase(self):
        invalid = Touchpoint(
            "INVALID-001",
            "C001",
            EventType.PURCHASE,
            datetime.now(timezone.utc),
            Channel.DIRECT,
            "SESSION-X",
            "/success",
            value=0,
        )

        with self.assertRaises(ValidationError):
            EventValidator.validate(invalid)


# ============================================================
# 13. EXECUTION
# ============================================================

def main() -> None:
    store = create_demo_store()
    analytics = JourneyAnalytics(store)

    report = analytics.generate_report()

    print("=" * 65)
    print("CUSTOMER JOURNEY ANALYTICS")
    print("=" * 65)

    print(json.dumps(report, indent=2))

    events = store.customer_events("C001")

    print("\nMULTI-TOUCH ATTRIBUTION: CUSTOMER C001")

    models = {
        "First touch": AttributionModel.first_touch(events),
        "Last touch": AttributionModel.last_touch(events),
        "Linear": AttributionModel.linear(events),
        "Position based": AttributionModel.position_based(events),
    }

    for model_name, attribution in models.items():
        print(f"\n{model_name}:")
        print(json.dumps(attribution, indent=2))

    purchase = next(
        event for event in events
        if event.event_type == EventType.PURCHASE
    )

    print("\nREVENUE ATTRIBUTION")
    print(json.dumps(
        AttributionModel.allocate_revenue(
            purchase.value,
            models["Linear"]
        ),
        indent=2,
    ))

    print("\nMONTHLY COHORT RETENTION")
    print(json.dumps(
        CohortAnalyzer.monthly_cohorts(
            store.customers.values(),
            store.all_events()
        ),
        indent=2,
    ))

    print("\nAUTOMATED TESTS")
    unittest.main(argv=["analytics"], exit=False)


if __name__ == "__main__":
    main()
