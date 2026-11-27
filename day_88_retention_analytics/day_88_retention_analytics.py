#!/usr/bin/env python3
"""
RETENTION ANALYTICS
Churn Prediction, Customer Retention, and Customer Loyalty

A self-contained customer retention analytics system featuring:
- Customer lifecycle management
- Transaction and engagement tracking
- Churn identification
- Recency, Frequency, Monetary (RFM) analysis
- Cohort retention analysis
- Customer segmentation
- Loyalty tier management
- Retention campaign evaluation
- Customer lifetime value estimation
- Retention performance reporting

Runtime: Python 3.10+
Dependencies: Python standard library only
"""

from __future__ import annotations

import csv
import json
import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("retention_analytics")


# ============================================================
# 1. DOMAIN ENUMERATIONS
# ============================================================

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    REACTIVATED = "reactivated"


class EventType(str, Enum):
    PURCHASE = "purchase"
    LOGIN = "login"
    SUPPORT = "support"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    SUBSCRIPTION = "subscription"
    REFUND = "refund"


class LoyaltyTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class CampaignType(str, Enum):
    DISCOUNT = "discount"
    LOYALTY_REWARD = "loyalty_reward"
    REACTIVATION = "reactivation"
    PERSONALIZED_OFFER = "personalized_offer"


# ============================================================
# 2. DOMAIN EXCEPTIONS
# ============================================================

class RetentionError(Exception):
    """Base exception for retention analytics."""


class ValidationError(RetentionError):
    """Invalid customer or event information."""


class DuplicateEventError(RetentionError):
    """An event identifier already exists."""


class CustomerNotFoundError(RetentionError):
    """Requested customer does not exist."""


class CampaignError(RetentionError):
    """Invalid campaign operation."""


# ============================================================
# 3. DATA MODELS
# ============================================================

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    acquisition_date: date
    region: str
    monthly_subscription: float = 0.0
    status: CustomerStatus = CustomerStatus.ACTIVE
    loyalty_tier: LoyaltyTier = LoyaltyTier.BRONZE

    def __post_init__(self):
        if not self.customer_id.strip():
            raise ValidationError("Customer ID cannot be empty.")

        if "@" not in self.email:
            raise ValidationError("Invalid email address.")

        if self.monthly_subscription < 0:
            raise ValidationError("Subscription cannot be negative.")


@dataclass
class CustomerEvent:
    event_id: str
    customer_id: str
    event_type: EventType
    timestamp: datetime
    amount: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id or not self.customer_id:
            raise ValidationError("Event and customer IDs are required.")

        if self.amount < 0:
            raise ValidationError("Event amount cannot be negative.")

        if self.timestamp.tzinfo is None:
            raise ValidationError("Event timestamps must be timezone-aware.")

        if self.event_type != EventType.PURCHASE and self.amount > 0:
            if self.event_type not in (EventType.SUBSCRIPTION,):
                raise ValidationError(
                    "Monetary amounts are not permitted for this event type."
                )


@dataclass
class RFMScore:
    recency_days: int
    frequency: int
    monetary_value: float
    score: float
    segment: str


@dataclass
class ChurnAssessment:
    customer_id: str
    probability: float
    risk_level: str
    contributing_factors: list[str]
    assessed_at: datetime


@dataclass
class Campaign:
    campaign_id: str
    name: str
    campaign_type: CampaignType
    budget: float
    cost_per_contact: float
    target_status: CustomerStatus
    assigned_customers: set[str] = field(default_factory=set)
    conversions: set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.budget < 0 or self.cost_per_contact < 0:
            raise ValidationError("Campaign costs cannot be negative.")


# ============================================================
# 4. CUSTOMER DATA MANAGEMENT
# ============================================================

class CustomerRepository:

    def __init__(self):
        self.customers: dict[str, Customer] = {}
        self.email_index: dict[str, str] = {}

    def add(self, customer: Customer) -> None:
        if customer.customer_id in self.customers:
            raise ValidationError("Customer ID already exists.")

        normalized_email = customer.email.lower()

        if normalized_email in self.email_index:
            raise ValidationError("Customer email already exists.")

        self.customers[customer.customer_id] = customer
        self.email_index[normalized_email] = customer.customer_id

    def get(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id]
        except KeyError as exc:
            raise CustomerNotFoundError(customer_id) from exc

    def all(self) -> list[Customer]:
        return list(self.customers.values())


# ============================================================
# 5. EVENT TRACKING
# ============================================================

class EventRepository:

    def __init__(self):
        self.events: dict[str, CustomerEvent] = {}
        self.customer_events: dict[str, list[CustomerEvent]] = defaultdict(list)

    def record(
        self,
        event: CustomerEvent,
        customer_repository: CustomerRepository
    ) -> None:

        if event.event_id in self.events:
            raise DuplicateEventError(event.event_id)

        customer_repository.get(event.customer_id)

        self.events[event.event_id] = event
        self.customer_events[event.customer_id].append(event)

    def get_customer_events(
        self,
        customer_id: str
    ) -> list[CustomerEvent]:

        return sorted(
            self.customer_events.get(customer_id, []),
            key=lambda event: event.timestamp
        )


# ============================================================
# 6. CUSTOMER ACTIVITY AND RFM ANALYTICS
# ============================================================

class RFMAnalyzer:

    @staticmethod
    def calculate(
        customer: Customer,
        events: list[CustomerEvent],
        reference_date: date
    ) -> RFMScore:

        purchases = [
            event for event in events
            if event.event_type == EventType.PURCHASE
            and event.timestamp.date() <= reference_date
        ]

        if purchases:
            last_purchase = max(
                event.timestamp.date() for event in purchases
            )
            recency = (reference_date - last_purchase).days
        else:
            recency = max(
                0, (reference_date - customer.acquisition_date).days
            )

        frequency = len(purchases)
        monetary = sum(event.amount for event in purchases)

        # A bounded score combines purchase frequency, monetary value,
        # and recency without allowing one metric to dominate indefinitely.
        recency_component = max(0.0, 1.0 - min(recency, 180) / 180)
        frequency_component = min(frequency / 12, 1.0)
        monetary_component = min(monetary / 12000, 1.0)

        score = (
            recency_component * 0.40
            + frequency_component * 0.30
            + monetary_component * 0.30
        ) * 100

        if frequency == 0:
            segment = "new_or_non_purchasing"
        elif recency <= 30 and score >= 65:
            segment = "champions"
        elif recency <= 60:
            segment = "loyal_customers"
        elif recency <= 90:
            segment = "potential_at_risk"
        else:
            segment = "hibernating"

        return RFMScore(
            recency_days=recency,
            frequency=frequency,
            monetary_value=round(monetary, 2),
            score=round(score, 2),
            segment=segment
        )


# ============================================================
# 7. CHURN RISK MODEL
# ============================================================

class ChurnPredictor:
    """
    Transparent heuristic risk model.

    This is a rule-based operational score, not a statistically
    trained or calibrated probability model.
    """

    def __init__(self, churn_threshold: float = 0.60):
        if not 0 < churn_threshold < 1:
            raise ValidationError("Threshold must be between 0 and 1.")

        self.churn_threshold = churn_threshold

    def assess(
        self,
        customer: Customer,
        events: list[CustomerEvent],
        reference_date: date
    ) -> ChurnAssessment:

        purchases = [
            event for event in events
            if event.event_type == EventType.PURCHASE
            and event.timestamp.date() <= reference_date
        ]

        activities = [
            event for event in events
            if event.timestamp.date() <= reference_date
        ]

        last_activity = max(
            (event.timestamp.date() for event in activities),
            default=customer.acquisition_date
        )

        inactivity = max(0, (reference_date - last_activity).days)

        last_purchase = max(
            (event.timestamp.date() for event in purchases),
            default=customer.acquisition_date
        )

        purchase_inactivity = max(
            0, (reference_date - last_purchase).days
        )

        factors = []
        risk = 0.05

        if purchase_inactivity > 30:
            risk += 0.20
            factors.append("No purchase for more than 30 days")

        if purchase_inactivity > 60:
            risk += 0.20
            factors.append("No purchase for more than 60 days")

        if purchase_inactivity > 90:
            risk += 0.20
            factors.append("No purchase for more than 90 days")

        if inactivity > 45:
            risk += 0.15
            factors.append("Low overall engagement")

        if len(purchases) == 0:
            risk += 0.15
            factors.append("No recorded purchases")

        recent_support = [
            event for event in activities
            if event.event_type == EventType.SUPPORT
            and (reference_date - event.timestamp.date()).days <= 30
        ]

        if len(recent_support) >= 3:
            risk += 0.10
            factors.append("Repeated recent support interactions")

        risk = min(risk, 0.99)

        if risk >= self.churn_threshold:
            level = "high"
        elif risk >= 0.35:
            level = "medium"
        else:
            level = "low"

        return ChurnAssessment(
            customer_id=customer.customer_id,
            probability=round(risk, 3),
            risk_level=level,
            contributing_factors=factors,
            assessed_at=datetime.now(timezone.utc)
        )


# ============================================================
# 8. COHORT RETENTION ANALYSIS
# ============================================================

class CohortAnalyzer:

    @staticmethod
    def month_difference(start: date, end: date) -> int:
        return (
            (end.year - start.year) * 12
            + end.month - start.month
        )

    def calculate(
        self,
        customers: list[Customer],
        events: list[CustomerEvent]
    ) -> dict:

        cohorts = defaultdict(set)
        active = defaultdict(set)

        for customer in customers:
            cohort = customer.acquisition_date.strftime("%Y-%m")
            cohorts[cohort].add(customer.customer_id)

        for event in events:
            if event.event_type not in (
                EventType.PURCHASE,
                EventType.LOGIN
            ):
                continue

            customer = next(
                (c for c in customers
                 if c.customer_id == event.customer_id),
                None
            )

            if customer is None:
                continue

            cohort = customer.acquisition_date.strftime("%Y-%m")
            period = self.month_difference(
                customer.acquisition_date,
                event.timestamp.date()
            )

            if period >= 0:
                active[(cohort, period)].add(customer.customer_id)

        result = {}

        for cohort, members in sorted(cohorts.items()):
            size = len(members)
            periods = sorted(
                period for current_cohort, period in active
                if current_cohort == cohort
            )

            result[cohort] = {
                "cohort_size": size,
                "retention": {
                    period: round(
                        len(active[(cohort, period)]) / size * 100, 2
                    )
                    for period in periods
                }
            }

        return result


# ============================================================
# 9. LOYALTY MANAGEMENT
# ============================================================

class LoyaltyManager:

    @staticmethod
    def determine_tier(lifetime_spend: float) -> LoyaltyTier:

        if lifetime_spend >= 10000:
            return LoyaltyTier.PLATINUM

        if lifetime_spend >= 5000:
            return LoyaltyTier.GOLD

        if lifetime_spend >= 2000:
            return LoyaltyTier.SILVER

        return LoyaltyTier.BRONZE

    @staticmethod
    def reward_multiplier(tier: LoyaltyTier) -> float:

        return {
            LoyaltyTier.BRONZE: 1.0,
            LoyaltyTier.SILVER: 1.25,
            LoyaltyTier.GOLD: 1.50,
            LoyaltyTier.PLATINUM: 2.0
        }[tier]

    def update(
        self,
        customer: Customer,
        events: list[CustomerEvent]
    ) -> LoyaltyTier:

        lifetime_spend = sum(
            event.amount for event in events
            if event.event_type == EventType.PURCHASE
        )

        customer.loyalty_tier = self.determine_tier(lifetime_spend)
        return customer.loyalty_tier


# ============================================================
# 10. CAMPAIGN MANAGEMENT
# ============================================================

class CampaignManager:

    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}

    def create(self, campaign: Campaign):

        if campaign.campaign_id in self.campaigns:
            raise CampaignError("Campaign already exists.")

        self.campaigns[campaign.campaign_id] = campaign

    def assign(
        self,
        campaign_id: str,
        customer: Customer
    ) -> None:

        campaign = self.campaigns[campaign_id]

        if customer.status != campaign.target_status:
            raise CampaignError(
                "Customer does not satisfy campaign targeting rules."
            )

        if customer.customer_id in campaign.assigned_customers:
            raise CampaignError("Customer already assigned.")

        if (
            len(campaign.assigned_customers) + 1
        ) * campaign.cost_per_contact > campaign.budget:
            raise CampaignError("Campaign budget exceeded.")

        campaign.assigned_customers.add(customer.customer_id)

    def record_conversion(
        self,
        campaign_id: str,
        customer_id: str
    ) -> None:

        campaign = self.campaigns[campaign_id]

        if customer_id not in campaign.assigned_customers:
            raise CampaignError("Customer was not assigned to campaign.")

        campaign.conversions.add(customer_id)

    def report(
        self,
        campaign_id: str,
        revenue_per_conversion: float
    ) -> dict:

        if revenue_per_conversion < 0:
            raise ValidationError("Revenue cannot be negative.")

        campaign = self.campaigns[campaign_id]

        contacted = len(campaign.assigned_customers)
        converted = len(campaign.conversions)

        conversion_rate = (
            converted / contacted * 100 if contacted else 0
        )

        cost = contacted * campaign.cost_per_contact
        revenue = converted * revenue_per_conversion

        roi = (
            (revenue - cost) / cost * 100 if cost else 0
        )

        return {
            "campaign_id": campaign_id,
            "contacted": contacted,
            "converted": converted,
            "conversion_rate": round(conversion_rate, 2),
            "campaign_cost": round(cost, 2),
            "attributed_revenue": round(revenue, 2),
            "roi_percent": round(roi, 2)
        }


# ============================================================
# 11. CUSTOMER LIFETIME VALUE
# ============================================================

class CLVAnalyzer:

    @staticmethod
    def calculate(
        average_monthly_revenue: float,
        gross_margin: float,
        monthly_churn_rate: float
    ) -> float:

        if average_monthly_revenue < 0:
            raise ValidationError("Revenue cannot be negative.")

        if not 0 <= gross_margin <= 1:
            raise ValidationError("Margin must be between 0 and 1.")

        if not 0 < monthly_churn_rate <= 1:
            raise ValidationError("Churn rate must be greater than 0.")

        return round(
            average_monthly_revenue
            * gross_margin
            / monthly_churn_rate,
            2
        )


# ============================================================
# 12. RETENTION SERVICE
# ============================================================

class RetentionService:

    def __init__(self):

        self.customers = CustomerRepository()
        self.events = EventRepository()

        self.rfm = RFMAnalyzer()
        self.churn = ChurnPredictor()
        self.cohorts = CohortAnalyzer()
        self.loyalty = LoyaltyManager()
        self.campaigns = CampaignManager()

    def add_customer(self, customer: Customer):
        self.customers.add(customer)

    def record_event(self, event: CustomerEvent):
        self.events.record(event, self.customers)

    def analyze_customer(
        self,
        customer_id: str,
        reference_date: date
    ) -> dict:

        customer = self.customers.get(customer_id)
        events = self.events.get_customer_events(customer_id)

        rfm = self.rfm.calculate(
            customer, events, reference_date
        )

        churn = self.churn.assess(
            customer, events, reference_date
        )

        tier = self.loyalty.update(customer, events)

        if churn.risk_level == "high":
            customer.status = CustomerStatus.AT_RISK
        elif customer.status == CustomerStatus.AT_RISK:
            customer.status = CustomerStatus.ACTIVE

        return {
            "customer_id": customer_id,
            "status": customer.status.value,
            "loyalty_tier": tier.value,
            "rfm": asdict(rfm),
            "churn": {
                **asdict(churn),
                "assessed_at": churn.assessed_at.isoformat()
            }
        }

    def retention_report(self, reference_date: date) -> dict:

        assessments = [
            self.analyze_customer(c.customer_id, reference_date)
            for c in self.customers.all()
        ]

        total = len(assessments)

        risk_counts = defaultdict(int)

        for assessment in assessments:
            risk_counts[
                assessment["churn"]["risk_level"]
            ] += 1

        return {
            "report_date": reference_date.isoformat(),
            "total_customers": total,
            "risk_distribution": dict(risk_counts),
            "high_risk_percentage": round(
                risk_counts["high"] / total * 100, 2
            ) if total else 0,
            "average_rfm_score": round(
                mean([
                    item["rfm"]["score"] for item in assessments
                ]), 2
            ) if total else 0,
            "customer_assessments": assessments
        }


# ============================================================
# 13. EXPORT AND REPORTING
# ============================================================

def export_json(data: dict, output_path: str) -> None:

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # UTF-8 JSON export preserves structured analytical results.
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def export_cohorts(cohorts: dict, output_path: str) -> None:

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "cohort",
            "cohort_size",
            "period",
            "retention_percentage"
        ])

        for cohort, information in cohorts.items():
            for period, retention in information["retention"].items():
                writer.writerow([
                    cohort,
                    information["cohort_size"],
                    period,
                    retention
                ])


# ============================================================
# 14. REALISTIC SAMPLE WORKFLOW
# ============================================================

def build_demo_service() -> RetentionService:

    service = RetentionService()

    reference_date = date(2026, 11, 27)

    customers = [
        Customer(
            "C001", "Aarav Sharma", "aarav@example.com",
            date(2026, 1, 10), "North", 999
        ),
        Customer(
            "C002", "Priya Verma", "priya@example.com",
            date(2026, 2, 15), "South", 1499
        ),
        Customer(
            "C003", "Rahul Singh", "rahul@example.com",
            date(2026, 3, 20), "West", 799
        ),
        Customer(
            "C004", "Ananya Gupta", "ananya@example.com",
            date(2026, 4, 5), "East", 1999
        ),
        Customer(
            "C005", "Vikram Rao", "vikram@example.com",
            date(2026, 5, 12), "North", 499
        )
    ]

    for customer in customers:
        service.add_customer(customer)

    def timestamp(days_ago: int) -> datetime:
        return datetime.combine(
            reference_date - timedelta(days=days_ago),
            datetime.min.time(),
            tzinfo=timezone.utc
        )

    sample_events = [
        CustomerEvent("E001", "C001", EventType.PURCHASE,
                      timestamp(5), 3000),
        CustomerEvent("E002", "C001", EventType.PURCHASE,
                      timestamp(35), 2500),
        CustomerEvent("E003", "C001", EventType.LOGIN,
                      timestamp(1)),
        CustomerEvent("E004", "C002", EventType.PURCHASE,
                      timestamp(15), 1500),
        CustomerEvent("E005", "C002", EventType.LOGIN,
                      timestamp(2)),
        CustomerEvent("E006", "C003", EventType.PURCHASE,
                      timestamp(110), 700),
        CustomerEvent("E007", "C004", EventType.PURCHASE,
                      timestamp(80), 8000),
        CustomerEvent("E008", "C004", EventType.SUPPORT,
                      timestamp(10)),
        CustomerEvent("E009", "C004", EventType.SUPPORT,
                      timestamp(8)),
        CustomerEvent("E010", "C004", EventType.SUPPORT,
                      timestamp(5)),
        CustomerEvent("E011", "C005", EventType.PURCHASE,
                      timestamp(3), 600),
        CustomerEvent("E012", "C005", EventType.LOGIN,
                      timestamp(1))
    ]

    for event in sample_events:
        service.record_event(event)

    return service


# ============================================================
# 15. VALIDATION AND SELF-TESTS
# ============================================================

def run_tests():

    assert CLVAnalyzer.calculate(1000, 0.70, 0.05) == 14000

    assert (
        LoyaltyManager.determine_tier(12000)
        == LoyaltyTier.PLATINUM
    )

    assert (
        LoyaltyManager.determine_tier(3000)
        == LoyaltyTier.SILVER
    )

    assert CohortAnalyzer.month_difference(
        date(2026, 1, 15),
        date(2026, 4, 1)
    ) == 3

    try:
        Customer(
            "", "Invalid", "invalid@example.com",
            date.today(), "Unknown"
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Customer validation failed.")

    try:
        CustomerEvent(
            "BAD", "C001", EventType.LOGIN,
            datetime.now(), 0
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Timezone validation failed.")

    logger.info("All validation tests passed.")


# ============================================================
# 16. APPLICATION ENTRY POINT
# ============================================================

def main():

    run_tests()

    service = build_demo_service()
    reference_date = date(2026, 11, 27)

    report = service.retention_report(reference_date)

    cohorts = service.cohorts.calculate(
        service.customers.all(),
        list(service.events.events.values())
    )

    campaign = Campaign(
        campaign_id="CMP001",
        name="November Customer Reactivation",
        campaign_type=CampaignType.REACTIVATION,
        budget=1000,
        cost_per_contact=50,
        target_status=CustomerStatus.AT_RISK
    )

    service.campaigns.create(campaign)

    for customer in service.customers.all():
        assessment = service.analyze_customer(
            customer.customer_id, reference_date
        )

        if customer.status == CustomerStatus.AT_RISK:
            service.campaigns.assign(
                campaign.campaign_id, customer
            )

            logger.info(
                "Retention campaign assigned to %s",
                customer.customer_id
            )

    if campaign.assigned_customers:
        first_customer = sorted(
            campaign.assigned_customers
        )[0]

        service.campaigns.record_conversion(
            campaign.campaign_id,
            first_customer
        )

    campaign_report = service.campaigns.report(
        campaign.campaign_id,
        revenue_per_conversion=1500
    )

    export_json(report, "output/retention_report.json")
    export_json(cohorts, "output/cohort_analysis.json")
    export_json(campaign_report, "output/campaign_report.json")
    export_cohorts(cohorts, "output/cohort_retention.csv")

    print("\nCUSTOMER RETENTION ANALYTICS")
    print("=" * 55)
    print(json.dumps(report, indent=2))
    print("\nCOHORT ANALYSIS")
    print(json.dumps(cohorts, indent=2))
    print("\nCAMPAIGN PERFORMANCE")
    print(json.dumps(campaign_report, indent=2))

    print("\nCLV EXAMPLE")
    print(
        "Estimated CLV:",
        CLVAnalyzer.calculate(1500, 0.65, 0.04)
    )

    print("\nReports saved in the output directory.")


if __name__ == "__main__":
    main()
