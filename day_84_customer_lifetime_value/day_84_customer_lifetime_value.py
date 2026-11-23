"""
CUSTOMER LIFETIME VALUE (CLV)
LTV calculation, customer segmentation, profitability analysis,
retention forecasting, acquisition economics, and strategic decisions.

Python 3.10+
Standard-library implementation.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger("customer_ltv")


class CLVError(Exception):
    """Base exception for CLV operations."""


class ValidationError(CLVError):
    """Raised when business data is invalid."""


class CustomerStatus(Enum):
    ACTIVE = "active"
    AT_RISK = "at_risk"
    CHURNED = "churned"


class CustomerSegment(Enum):
    HIGH_VALUE = "high_value"
    GROWING = "growing"
    STANDARD = "standard"
    LOW_VALUE = "low_value"
    UNPROFITABLE = "unprofitable"


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    customer_id: str
    transaction_date: date
    revenue: float
    variable_cost: float = 0.0
    acquisition_cost: float = 0.0

    def __post_init__(self):
        if not self.transaction_id or not self.customer_id:
            raise ValidationError("Transaction identifiers are required.")

        for name, value in (
            ("revenue", self.revenue),
            ("variable_cost", self.variable_cost),
            ("acquisition_cost", self.acquisition_cost),
        ):
            if not math.isfinite(value) or value < 0:
                raise ValidationError(f"Invalid {name}.")

        if self.variable_cost > self.revenue:
            logger.warning(
                "Transaction %s has negative contribution margin.",
                self.transaction_id
            )

    @property
    def contribution(self) -> float:
        return self.revenue - self.variable_cost


@dataclass
class Customer:
    customer_id: str
    acquisition_date: date
    acquisition_channel: str
    transactions: list[Transaction] = field(default_factory=list)
    status: CustomerStatus = CustomerStatus.ACTIVE

    def add_transaction(self, transaction: Transaction) -> None:
        if transaction.customer_id != self.customer_id:
            raise ValidationError("Transaction belongs to another customer.")

        if transaction.transaction_date < self.acquisition_date:
            raise ValidationError("Transaction predates acquisition.")

        if any(
            item.transaction_id == transaction.transaction_id
            for item in self.transactions
        ):
            raise ValidationError("Duplicate transaction identifier.")

        self.transactions.append(transaction)
        self.transactions.sort(key=lambda item: item.transaction_date)

    @property
    def revenue(self) -> float:
        return sum(t.revenue for t in self.transactions)

    @property
    def contribution(self) -> float:
        return sum(t.contribution for t in self.transactions)

    @property
    def acquisition_cost(self) -> float:
        return sum(t.acquisition_cost for t in self.transactions)

    @property
    def order_count(self) -> int:
        return len(self.transactions)

    @property
    def average_order_value(self) -> float:
        if not self.transactions:
            return 0.0
        return self.revenue / self.order_count

    @property
    def purchase_frequency(self) -> float:
        if len(self.transactions) < 2:
            return 0.0

        days = (
            self.transactions[-1].transaction_date
            - self.transactions[0].transaction_date
        ).days

        if days == 0:
            return float(self.order_count)

        return self.order_count / (days / 365.25)


@dataclass(frozen=True)
class CLVResult:
    customer_id: str
    historical_revenue: float
    historical_contribution: float
    acquisition_cost: float
    gross_margin_rate: float
    projected_clv: float
    net_clv: float
    expected_lifetime_years: float
    segment: str
    confidence: str


class CLVCalculator:
    """
    Calculates historical, predictive, and discounted CLV.

    Predictive model:
        Annual contribution = Annual revenue * Gross margin rate

        Expected lifetime =
            min(max_lifetime, 1 / annual churn probability)

        Predictive CLV =
            Annual contribution *
            [1 - (1 + discount_rate)^(-lifetime)] / discount_rate

        Net CLV = Predictive CLV - Acquisition cost

    This is a simplified constant-cash-flow model.
    """

    def __init__(
        self,
        annual_churn_rate: float = 0.20,
        annual_discount_rate: float = 0.10,
        gross_margin_rate: float = 0.60,
        max_lifetime_years: float = 10.0,
    ):
        if not 0 < annual_churn_rate <= 1:
            raise ValidationError("Churn rate must be in (0, 1].")

        if not 0 <= annual_discount_rate < 1:
            raise ValidationError("Discount rate must be in [0, 1).")

        if not 0 <= gross_margin_rate <= 1:
            raise ValidationError("Gross margin must be in [0, 1].")

        if max_lifetime_years <= 0:
            raise ValidationError("Maximum lifetime must be positive.")

        self.churn_rate = annual_churn_rate
        self.discount_rate = annual_discount_rate
        self.margin_rate = gross_margin_rate
        self.max_lifetime = max_lifetime_years

    def segment(self, net_clv: float) -> CustomerSegment:
        if net_clv < 0:
            return CustomerSegment.UNPROFITABLE
        if net_clv >= 10000:
            return CustomerSegment.HIGH_VALUE
        if net_clv >= 5000:
            return CustomerSegment.GROWING
        if net_clv >= 1000:
            return CustomerSegment.STANDARD
        return CustomerSegment.LOW_VALUE

    def calculate(self, customer: Customer) -> CLVResult:
        historical_revenue = customer.revenue
        historical_contribution = customer.contribution

        acquisition_cost = customer.acquisition_cost

        margin = (
            historical_contribution / historical_revenue
            if historical_revenue > 0
            else self.margin_rate
        )

        annual_revenue = (
            customer.purchase_frequency * customer.average_order_value
            if customer.purchase_frequency > 0
            else 0.0
        )

        annual_contribution = annual_revenue * margin
        lifetime = min(
            self.max_lifetime,
            1.0 / self.churn_rate
        )

        if self.discount_rate == 0:
            projected = annual_contribution * lifetime
        else:
            projected = (
                annual_contribution
                * (
                    1 - (1 + self.discount_rate) ** (-lifetime)
                )
                / self.discount_rate
            )

        net_clv = projected - acquisition_cost

        confidence = (
            "high" if customer.order_count >= 5
            else "medium" if customer.order_count >= 2
            else "low"
        )

        return CLVResult(
            customer_id=customer.customer_id,
            historical_revenue=round(historical_revenue, 2),
            historical_contribution=round(historical_contribution, 2),
            acquisition_cost=round(acquisition_cost, 2),
            gross_margin_rate=round(margin, 4),
            projected_clv=round(projected, 2),
            net_clv=round(net_clv, 2),
            expected_lifetime_years=round(lifetime, 2),
            segment=self.segment(net_clv).value,
            confidence=confidence,
        )


@dataclass
class AcquisitionMetrics:
    total_marketing_spend: float
    acquired_customers: int
    average_clv: float
    average_order_value: float

    @property
    def cac(self) -> float:
        if self.acquired_customers <= 0:
            raise ValidationError("Acquired customer count must be positive.")
        return self.total_marketing_spend / self.acquired_customers

    @property
    def clv_cac_ratio(self) -> float:
        if self.cac == 0:
            return math.inf
        return self.average_clv / self.cac

    @property
    def acquisition_payback_orders(self) -> float:
        if self.average_order_value <= 0:
            return math.inf
        return self.cac / self.average_order_value


class StrategicEngine:
    """Converts CLV and customer behavior into business actions."""

    @staticmethod
    def recommend(result: CLVResult, churn_risk: float) -> list[str]:
        if not 0 <= churn_risk <= 1:
            raise ValidationError("Churn risk must be between 0 and 1.")

        actions = []

        if result.net_clv < 0:
            actions.append("Reduce acquisition expenditure and reassess pricing.")

        elif result.segment == CustomerSegment.HIGH_VALUE.value:
            actions.append("Prioritize loyalty benefits and personalized service.")

        elif result.segment == CustomerSegment.GROWING.value:
            actions.append("Offer relevant cross-selling and premium products.")

        elif result.segment == CustomerSegment.STANDARD.value:
            actions.append("Improve repeat purchase frequency.")

        else:
            actions.append("Use low-cost retention and automated engagement.")

        if churn_risk >= 0.70:
            actions.append("Trigger an immediate churn-prevention intervention.")
        elif churn_risk >= 0.40:
            actions.append("Monitor engagement and initiate targeted retention.")

        if result.confidence == "low":
            actions.append("Collect additional behavioral data before major investment.")

        return actions


class CustomerRepository:
    """In-memory repository with customer and transaction integrity."""

    def __init__(self):
        self.customers: dict[str, Customer] = {}

    def add_customer(self, customer: Customer) -> None:
        if customer.customer_id in self.customers:
            raise ValidationError("Customer already exists.")
        self.customers[customer.customer_id] = customer

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self.customers[customer_id]
        except KeyError as exc:
            raise ValidationError("Customer not found.") from exc

    def portfolio_value(
        self,
        calculator: CLVCalculator
    ) -> list[CLVResult]:
        return [
            calculator.calculate(customer)
            for customer in self.customers.values()
        ]

    def channel_analysis(
        self,
        calculator: CLVCalculator
    ) -> dict[str, dict[str, float]]:
        grouped: dict[str, list[float]] = {}

        for customer in self.customers.values():
            result = calculator.calculate(customer)
            grouped.setdefault(customer.acquisition_channel, []).append(
                result.net_clv
            )

        return {
            channel: {
                "customers": len(values),
                "average_net_clv": round(statistics.mean(values), 2),
                "total_net_clv": round(sum(values), 2),
            }
            for channel, values in grouped.items()
        }


def calculate_retention_cohort(
    customer_acquisition_dates: list[date],
    activity_dates: dict[date, set[str]],
    period: date,
) -> dict[str, float]:
    """Calculate cohort retention from explicit active-customer sets."""

    cohort = {
        customer_id
        for customer_id, acquired in customer_acquisition_dates
    } if False else set()

    # The function below uses a mapping of customer IDs to acquisition dates.
    raise NotImplementedError("Use calculate_cohort_retention instead.")


def calculate_cohort_retention(
    acquisition_dates: dict[str, date],
    activity_by_period: dict[date, set[str]],
    cohort_month: date,
) -> dict[str, float]:
    cohort = {
        customer_id
        for customer_id, acquired in acquisition_dates.items()
        if acquired.year == cohort_month.year
        and acquired.month == cohort_month.month
    }

    if not cohort:
        return {}

    report = {}

    for period, active_customers in sorted(activity_by_period.items()):
        if period < cohort_month:
            continue

        retained = len(cohort.intersection(active_customers))

        report[period.isoformat()] = round(
            retained / len(cohort) * 100,
            2
        )

    return report


def save_report(
    results: list[CLVResult],
    output_file: str = "customer_ltv_report.json"
) -> None:
    path = Path(output_file)

    # Avoid accepting paths containing parent traversal components.
    if ".." in path.parts:
        raise ValidationError("Unsafe output path.")

    payload = [asdict(result) for result in results]

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8"
    )

    logger.info("Report saved to %s", path.resolve())


def build_demo_repository() -> CustomerRepository:
    repository = CustomerRepository()

    customers = [
        Customer("C001", date(2024, 1, 10), "organic"),
        Customer("C002", date(2024, 3, 15), "paid_search"),
        Customer("C003", date(2024, 5, 20), "referral"),
        Customer("C004", date(2025, 1, 5), "paid_social"),
    ]

    transactions = [
        Transaction("T001", "C001", date(2024, 2, 1), 5000, 1800, 500),
        Transaction("T002", "C001", date(2024, 5, 1), 6500, 2200),
        Transaction("T003", "C001", date(2024, 9, 1), 7000, 2500),
        Transaction("T004", "C001", date(2025, 2, 1), 8000, 2800),

        Transaction("T005", "C002", date(2024, 4, 1), 1500, 900, 2000),
        Transaction("T006", "C002", date(2024, 7, 1), 1800, 1000),
        Transaction("T007", "C002", date(2024, 10, 1), 2000, 1100),

        Transaction("T008", "C003", date(2024, 6, 1), 3000, 1200, 300),
        Transaction("T009", "C003", date(2024, 10, 1), 4000, 1500),
        Transaction("T010", "C003", date(2025, 3, 1), 5000, 1800),

        Transaction("T011", "C004", date(2025, 2, 1), 700, 500, 2500),
        Transaction("T012", "C004", date(2025, 4, 1), 800, 600),
    ]

    for customer in customers:
        repository.add_customer(customer)

    for transaction in transactions:
        repository.get_customer(transaction.customer_id).add_transaction(
            transaction
        )

    return repository


def run_tests() -> None:
    calculator = CLVCalculator()

    customer = Customer("TEST", date(2025, 1, 1), "test")

    customer.add_transaction(
        Transaction("A", "TEST", date(2025, 2, 1), 1000, 400, 200)
    )

    customer.add_transaction(
        Transaction("B", "TEST", date(2025, 8, 1), 2000, 800)
    )

    result = calculator.calculate(customer)

    assert result.historical_revenue == 3000
    assert result.historical_contribution == 1800
    assert result.acquisition_cost == 200
    assert result.net_clv > 0

    try:
        customer.add_transaction(
            Transaction("A", "TEST", date(2025, 9, 1), 100, 20)
        )
        raise AssertionError("Duplicate transaction was accepted.")
    except ValidationError:
        pass

    assert calculator.segment(-100) == CustomerSegment.UNPROFITABLE

    try:
        CLVCalculator(annual_churn_rate=0)
        raise AssertionError("Invalid churn rate was accepted.")
    except ValidationError:
        pass

    print("All tests passed.")


def main() -> None:
    repository = build_demo_repository()
    calculator = CLVCalculator(
        annual_churn_rate=0.20,
        annual_discount_rate=0.10,
        gross_margin_rate=0.60,
    )

    results = repository.portfolio_value(calculator)

    print("\nCUSTOMER LIFETIME VALUE REPORT")
    print("=" * 90)

    for result in results:
        print(
            f"{result.customer_id:8} "
            f"Revenue: {result.historical_revenue:10.2f} "
            f"Contribution: {result.historical_contribution:10.2f} "
            f"Net CLV: {result.net_clv:10.2f} "
            f"Segment: {result.segment}"
        )

        for action in StrategicEngine.recommend(result, 0.45):
            print(f"    - {action}")

    print("\nACQUISITION CHANNEL ANALYSIS")
    for channel, metrics in repository.channel_analysis(calculator).items():
        print(channel, metrics)

    acquisition = AcquisitionMetrics(
        total_marketing_spend=50000,
        acquired_customers=100,
        average_clv=6000,
        average_order_value=1500,
    )

    print("\nACQUISITION ECONOMICS")
    print(f"CAC: {acquisition.cac:.2f}")
    print(f"CLV/CAC: {acquisition.clv_cac_ratio:.2f}")
    print(
        f"Revenue-based payback orders: "
        f"{acquisition.acquisition_payback_orders:.2f}"
    )

    save_report(results)
    run_tests()


if __name__ == "__main__":
    main()
