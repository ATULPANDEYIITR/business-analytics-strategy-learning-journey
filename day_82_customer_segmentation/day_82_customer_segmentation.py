from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("customer_segmentation")


class SegmentType(str, Enum):
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    VALUE_BASED = "value_based"


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ValueSegment(str, Enum):
    HIGH_VALUE = "high_value"
    MEDIUM_VALUE = "medium_value"
    LOW_VALUE = "low_value"


@dataclass
class Customer:
    customer_id: int
    name: str
    age: int
    location: str
    occupation: str
    income: float
    visits: int
    purchases: int
    total_spend: float
    last_purchase: date
    website_sessions: int
    email_interactions: int
    product_category: str
    status: CustomerStatus = CustomerStatus.ACTIVE

    def validate(self) -> None:
        if self.customer_id <= 0:
            raise ValueError("Customer ID must be positive.")

        if not self.name.strip():
            raise ValueError("Customer name cannot be empty.")

        if not 18 <= self.age <= 120:
            raise ValueError("Age must be between 18 and 120.")

        if self.income < 0 or self.total_spend < 0:
            raise ValueError("Income and spending cannot be negative.")

        if min(
            self.visits,
            self.purchases,
            self.website_sessions,
            self.email_interactions
        ) < 0:
            raise ValueError("Behavioral metrics cannot be negative.")

        if self.purchases > self.visits:
            raise ValueError("Purchases cannot exceed recorded visits.")

        if self.purchases == 0 and self.total_spend > 0:
            raise ValueError("Spending requires at least one purchase.")

        if self.last_purchase > date.today():
            raise ValueError("Last purchase cannot be in the future.")


@dataclass
class SegmentationResult:
    customer_id: int
    demographic_segment: str
    behavioral_segment: str
    value_segment: str
    recency_days: int
    frequency: int
    monetary_value: float
    average_order_value: float
    lifetime_value_estimate: float
    assigned_at: str
    explanations: list[str] = field(default_factory=list)


@dataclass
class SegmentationConfig:
    high_value_threshold: float = 100000.0
    medium_value_threshold: float = 30000.0
    high_income_threshold: float = 1200000.0
    recent_purchase_days: int = 30
    inactive_purchase_days: int = 180
    frequent_purchase_threshold: int = 10
    engaged_session_threshold: int = 20
    engaged_email_threshold: int = 10
    observation_days: int = 365

    def validate(self) -> None:
        if not (
            self.high_value_threshold > self.medium_value_threshold >= 0
        ):
            raise ValueError("Invalid value segmentation thresholds.")

        if min(
            self.recent_purchase_days,
            self.inactive_purchase_days,
            self.frequent_purchase_threshold,
            self.engaged_session_threshold,
            self.engaged_email_threshold,
            self.observation_days
        ) <= 0:
            raise ValueError("Segmentation thresholds must be positive.")


class CustomerRepository:
    """In-memory repository with duplicate prevention and validation."""

    def __init__(self):
        self._customers: dict[int, Customer] = {}

    def add(self, customer: Customer) -> None:
        customer.validate()

        if customer.customer_id in self._customers:
            raise ValueError(
                f"Duplicate customer ID: {customer.customer_id}"
            )

        self._customers[customer.customer_id] = customer

    def get(self, customer_id: int) -> Customer:
        try:
            return self._customers[customer_id]
        except KeyError:
            raise KeyError(f"Customer {customer_id} does not exist.")

    def all(self) -> list[Customer]:
        return list(self._customers.values())


class CustomerSegmenter:
    """
    Segmentation engine combining three independent dimensions:

    1. Demographic: age, income and geographic characteristics.
    2. Behavioral: purchase recency, frequency and digital engagement.
    3. Value-based: observed monetary spending.
    """

    def __init__(
        self,
        config: SegmentationConfig | None = None
    ):
        self.config = config or SegmentationConfig()
        self.config.validate()

    def demographic_segment(self, customer: Customer) -> str:
        if customer.age < 30:
            age_group = "young_adult"
        elif customer.age < 45:
            age_group = "adult"
        elif customer.age < 60:
            age_group = "middle_aged"
        else:
            age_group = "senior"

        if customer.income >= self.config.high_income_threshold:
            income_group = "high_income"
        elif customer.income >= self.config.high_income_threshold / 3:
            income_group = "middle_income"
        else:
            income_group = "lower_income"

        return f"{age_group}_{income_group}"

    def behavioral_segment(
        self,
        customer: Customer,
        reference_date: date
    ) -> tuple[str, int]:
        recency = (reference_date - customer.last_purchase).days

        if recency < 0:
            raise ValueError("Purchase date is later than reference date.")

        if recency > self.config.inactive_purchase_days:
            return "dormant", recency

        if (
            recency <= self.config.recent_purchase_days
            and customer.purchases >= self.config.frequent_purchase_threshold
        ):
            return "loyal_active", recency

        if recency <= self.config.recent_purchase_days:
            return "recent_customer", recency

        if (
            customer.website_sessions >= self.config.engaged_session_threshold
            or customer.email_interactions >= self.config.engaged_email_threshold
        ):
            return "digitally_engaged", recency

        if customer.purchases >= self.config.frequent_purchase_threshold:
            return "repeat_customer", recency

        return "occasional_customer", recency

    def value_segment(self, customer: Customer) -> ValueSegment:
        if customer.total_spend >= self.config.high_value_threshold:
            return ValueSegment.HIGH_VALUE

        if customer.total_spend >= self.config.medium_value_threshold:
            return ValueSegment.MEDIUM_VALUE

        return ValueSegment.LOW_VALUE

    def segment(
        self,
        customer: Customer,
        reference_date: date | None = None
    ) -> SegmentationResult:
        customer.validate()

        reference_date = reference_date or date.today()

        demographic = self.demographic_segment(customer)

        behavioral, recency = self.behavioral_segment(
            customer,
            reference_date
        )

        value = self.value_segment(customer)

        average_order_value = (
            customer.total_spend / customer.purchases
            if customer.purchases
            else 0.0
        )

        lifetime_value = (
            customer.total_spend
            * min(
                1.0,
                self.config.observation_days / max(recency + 1, 1)
            )
        )

        explanations = [
            f"Demographic classification: {demographic}",
            f"Behavioral classification: {behavioral}",
            f"Value classification: {value.value}",
            f"Purchase recency: {recency} days"
        ]

        if customer.status != CustomerStatus.ACTIVE:
            explanations.append(
                f"Customer account status: {customer.status.value}"
            )

        return SegmentationResult(
            customer_id=customer.customer_id,
            demographic_segment=demographic,
            behavioral_segment=behavioral,
            value_segment=value.value,
            recency_days=recency,
            frequency=customer.purchases,
            monetary_value=customer.total_spend,
            average_order_value=round(average_order_value, 2),
            lifetime_value_estimate=round(lifetime_clv(lifetime_value), 2),
            assigned_at=datetime.now(timezone.utc).isoformat(),
            explanations=explanations
        )

    def segment_many(
        self,
        customers: Iterable[Customer],
        reference_date: date | None = None
    ) -> list[SegmentationResult]:
        results = []

        for customer in customers:
            try:
                results.append(self.segment(customer, reference_date))
            except (ValueError, TypeError) as error:
                logger.warning(
                    "Customer %s rejected: %s",
                    customer.customer_id,
                    error
                )

        return results


def lifetime_clv(value: float) -> float:
    """Keep financial estimates finite and non-negative."""
    if not math.isfinite(value) or value < 0:
        raise ValueError("Invalid lifetime value estimate.")

    return value


class SegmentationAnalytics:
    def summarize(
        self,
        results: list[SegmentationResult]
    ) -> dict[str, Any]:
        if not results:
            return {
                "customer_count": 0,
                "segments": {},
                "average_spend": 0.0
            }

        dimensions = {
            "demographic": {},
            "behavioral": {},
            "value": {}
        }

        for result in results:
            dimensions["demographic"].setdefault(
                result.demographic_segment, 0
            )
            dimensions["demographic"][
                result.demographic_segment
            ] += 1

            dimensions["behavioral"].setdefault(
                result.behavioral_segment, 0
            )
            dimensions["behavioral"][
                result.behavioral_segment
            ] += 1

            dimensions["value"].setdefault(
                result.value_segment, 0
            )
            dimensions["value"][result.value_segment] += 1

        spends = [r.monetary_value for r in results]

        return {
            "customer_count": len(results),
            "segments": dimensions,
            "average_spend": round(statistics.mean(spends), 2),
            "median_spend": round(statistics.median(spends), 2),
            "total_revenue": round(sum(spends), 2),
            "high_value_percentage": round(
                dimensions["value"].get("high_value", 0)
                / len(results) * 100,
                2
            )
        }

    def cross_tabulate(
        self,
        results: list[SegmentationResult]
    ) -> dict[str, dict[str, int]]:
        matrix: dict[str, dict[str, int]] = {}

        for result in results:
            row = matrix.setdefault(
                result.behavioral_segment, {}
            )
            row[result.value_segment] = (
                row.get(result.value_segment, 0) + 1
            )

        return matrix


class CampaignPolicy:
    """Example of deterministic segment-based campaign eligibility."""

    def eligible(
        self,
        customer: Customer,
        result: SegmentationResult
    ) -> tuple[bool, str]:
        if customer.status != CustomerStatus.ACTIVE:
            return False, "Account is not active."

        if result.behavioral_segment == "dormant":
            return False, "Customer requires a separate reactivation policy."

        if result.value_segment == ValueSegment.HIGH_VALUE.value:
            return True, "Eligible for premium retention campaign."

        if result.behavioral_segment == "recent_customer":
            return True, "Eligible for new customer engagement campaign."

        if result.behavioral_segment == "digitally_engaged":
            return True, "Eligible for digital engagement campaign."

        return True, "Eligible for standard campaign."


class SegmentationExporter:
    def export_json(
        self,
        results: list[SegmentationResult],
        output_path: str
    ) -> None:
        path = Path(output_path)

        if path.suffix.lower() != ".json":
            raise ValueError("Export destination must use .json extension.")

        path.parent.mkdir(parents=True, exist_ok=True)

        data = [asdict(result) for result in results]

        # Write atomically to avoid leaving partially written reports.
        temporary = path.with_suffix(".json.tmp")

        try:
            temporary.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise


def build_sample_repository() -> CustomerRepository:
    repository = CustomerRepository()

    samples = [
        Customer(
            1001, "Customer A", 27, "Delhi", "Engineer",
            1800000, 24, 18, 165000,
            date.today() - timedelta(days=5),
            55, 20, "Electronics"
        ),
        Customer(
            1002, "Customer B", 38, "Mumbai", "Manager",
            900000, 14, 8, 65000,
            date.today() - timedelta(days=25),
            30, 12, "Fashion"
        ),
        Customer(
            1003, "Customer C", 52, "Lucknow", "Teacher",
            450000, 5, 3, 18000,
            date.today() - timedelta(days=95),
            8, 2, "Books"
        ),
        Customer(
            1004, "Customer D", 64, "Pune", "Consultant",
            2200000, 30, 22, 245000,
            date.today() - timedelta(days=12),
            75, 35, "Travel"
        ),
        Customer(
            1005, "Customer E", 31, "Jaipur", "Analyst",
            700000, 2, 1, 2500,
            date.today() - timedelta(days=250),
            3, 0, "Home"
        ),
        Customer(
            1006, "Customer F", 44, "Bengaluru", "Designer",
            1100000, 16, 11, 92000,
            date.today() - timedelta(days=15),
            42, 18, "Electronics"
        )
    ]

    for customer in samples:
        repository.add(customer)

    return repository


def run_tests() -> None:
    segmenter = CustomerSegmenter()

    customer = Customer(
        9999, "Test Customer", 29, "Delhi", "Engineer",
        1500000, 15, 12, 125000,
        date.today() - timedelta(days=10),
        40, 15, "Electronics"
    )

    result = segmenter.segment(customer)

    assert result.value_segment == "high_value"
    assert result.behavioral_segment == "loyal_active"
    assert result.recency_days == 10

    invalid = Customer(
        9998, "Invalid", 15, "Delhi", "Student",
        10000, 1, 0, 0,
        date.today(), 0, 0, "Books"
    )

    try:
        invalid.validate()
        raise AssertionError("Invalid age was accepted.")
    except ValueError:
        pass

    zero_purchase = Customer(
        9997, "Zero Purchase", 30, "Delhi", "Analyst",
        500000, 0, 0, 0,
        date.today() - timedelta(days=10),
        5, 1, "Books"
    )

    assert segmenter.segment(zero_purchase).average_order_value == 0

    print("All segmentation tests passed.")


def main() -> None:
    run_tests()

    repository = build_sample_repository()
    segmenter = CustomerSegmenter()
    analytics = SegmentationAnalytics()
    campaign_policy = CampaignPolicy()

    reference_date = date.today()

    results = segmenter.segment_many(
        repository.all(),
        reference_date
    )

    print("\nCUSTOMER SEGMENTATION REPORT")

    for result in results:
        customer = repository.get(result.customer_id)

        print(
            f"\nCustomer: {customer.customer_id} | {customer.name}"
        )
        print(f"Demographic: {result.demographic_segment}")
        print(f"Behavioral: {result.behavioral_segment}")
        print(f"Value: {result.value_segment}")
        print(f"Recency: {result.recency_days} days")
        print(f"Monetary: Rs. {result.monetary_value:,.2f}")
        print(
            "Campaign:",
            campaign_policy.eligible(customer, result)
        )

    print("\nSEGMENT ANALYTICS")

    print(
        json.dumps(
            analytics.summarize(results),
            indent=2
        )
    )

    print("\nBEHAVIORAL VS VALUE CROSS-TABULATION")

    print(
        json.dumps(
            analytics.cross_tabulate(results),
            indent=2
        )
    )

    SegmentationExporter().export_json(
        results,
        "customer_segmentation_report.json"
    )

    print("\nReport exported to customer_segmentation_report.json")


if __name__ == "__main__":
    main()
