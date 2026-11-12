#!/usr/bin/env python3
"""
UNIT ECONOMICS ANALYTICS ENGINE

Implements:
- Customer Acquisition Cost (CAC)
- Customer Lifetime Value (LTV)
- Contribution Margin
- CAC Payback Period
- Cohort analysis
- Channel profitability
- Sensitivity analysis
- Financial validation
- JSON reporting

Runtime: Python 3.10+
Dependencies: Python standard library only
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s"
)

logger = logging.getLogger("unit_economics")


class UnitEconomicsError(Exception):
    """Base exception for unit economics operations."""


class ValidationError(UnitEconomicsError):
    """Raised when financial inputs are invalid."""


class InsufficientDataError(UnitEconomicsError):
    """Raised when a metric cannot be calculated."""


class Channel(str, Enum):
    ORGANIC = "organic"
    PAID_SEARCH = "paid_search"
    SOCIAL = "social"
    REFERRAL = "referral"
    PARTNERSHIP = "partnership"


@dataclass(frozen=True)
class Acquisition:
    channel: Channel
    advertising_cost: float
    sales_cost: float
    marketing_cost: float
    new_customers: int
    period: str

    def __post_init__(self):
        costs = (
            self.advertising_cost,
            self.sales_cost,
            self.marketing_cost
        )
        if any(not math.isfinite(x) or x < 0 for x in costs):
            raise ValidationError("Acquisition costs must be finite and non-negative.")
        if self.new_customers <= 0:
            raise ValidationError("New customer count must be positive.")


@dataclass(frozen=True)
class CustomerEconomics:
    customer_id: str
    cohort: str
    acquisition_channel: Channel
    monthly_revenue: float
    monthly_variable_cost: float
    expected_lifetime_months: float
    monthly_churn_rate: float

    def __post_init__(self):
        if not self.customer_id.strip():
            raise ValidationError("Customer ID cannot be empty.")
        if not self.cohort.strip():
            raise ValidationError("Cohort cannot be empty.")
        if not math.isfinite(self.monthly_revenue) or self.monthly_revenue < 0:
            raise ValidationError("Revenue must be finite and non-negative.")
        if not math.isfinite(self.monthly_variable_cost) or self.monthly_variable_cost < 0:
            raise ValidationError("Variable cost must be finite and non-negative.")
        if not math.isfinite(self.expected_lifetime_months) or self.expected_lifetime_months <= 0:
            raise ValidationError("Lifetime must be positive.")
        if not 0 <= self.monthly_churn_rate < 1:
            raise ValidationError("Monthly churn must be between 0 and 1.")


@dataclass(frozen=True)
class UnitEconomicsResult:
    cac: float
    monthly_contribution: float
    contribution_margin_pct: float
    gross_ltv: float
    contribution_ltv: float
    ltv_cac_ratio: float
    payback_months: Optional[float]
    profitability: str


@dataclass
class Cohort:
    name: str
    customers: list[CustomerEconomics]


class UnitEconomicsEngine:
    """Calculates customer-level and acquisition-level economics."""

    def calculate_cac(self, acquisition: Acquisition) -> float:
        total_cost = (
            acquisition.advertising_cost
            + acquisition.sales_cost
            + acquisition.marketing_cost
        )
        return total_cost / acquisition.new_customers

    def calculate_contribution_margin(
        self,
        revenue: float,
        variable_cost: float
    ) -> tuple[float, float]:
        if not math.isfinite(revenue) or not math.isfinite(variable_cost):
            raise ValidationError("Financial values must be finite.")
        if revenue < 0 or variable_cost < 0:
            raise ValidationError("Financial values cannot be negative.")
        if revenue == 0:
            if variable_cost > 0:
                raise ValidationError("Positive variable cost with zero revenue is invalid.")
            return 0.0, 0.0

        contribution = revenue - variable_cost
        margin = contribution / revenue * 100
        return contribution, margin

    def calculate_ltv(
        self,
        monthly_revenue: float,
        monthly_variable_cost: float,
        lifetime_months: float
    ) -> tuple[float, float]:
        contribution, _ = self.calculate_contribution_margin(
            monthly_revenue,
            monthly_variable_cost
        )

        if lifetime_months <= 0 or not math.isfinite(lifetime_months):
            raise ValidationError("Lifetime must be finite and positive.")

        gross_ltv = monthly_revenue * lifetime_months
        contribution_ltv = contribution * lifetime_months

        return gross_ltv, contribution_ltv

    def calculate_payback(
        self,
        cac: float,
        monthly_contribution: float
    ) -> Optional[float]:
        if cac < 0 or monthly_contribution < 0:
            raise ValidationError("CAC and contribution cannot be negative.")

        if monthly_contribution == 0:
            return None

        return cac / monthly_contribution

    def evaluate(
        self,
        acquisition: Acquisition,
        customer: CustomerEconomics
    ) -> UnitEconomicsResult:

        if acquisition.channel != customer.acquisition_channel:
            raise ValidationError("Acquisition and customer channels do not match.")

        cac = self.calculate_cac(acquisition)

        contribution, margin = self.calculate_contribution_margin(
            customer.monthly_revenue,
            customer.monthly_variable_cost
        )

        gross_ltv, contribution_ltv = self.calculate_ltv(
            customer.monthly_revenue,
            customer.monthly_variable_cost,
            customer.expected_lifetime_months
        )

        ratio = contribution_ltv / cac if cac > 0 else (
            math.inf if contribution_ltv > 0 else 0.0
        )

        payback = self.calculate_payback(cac, contribution)

        if contribution_ltv <= cac:
            profitability = "UNPROFITABLE"
        elif payback is None:
            profitability = "NO_PAYBACK"
        elif payback <= customer.expected_lifetime_months:
            profitability = "LIFETIME_POSITIVE"
        else:
            profitability = "PAYBACK_EXCEEDS_LIFETIME"

        return UnitEconomicsResult(
            cac=round(cac, 2),
            monthly_contribution=round(contribution, 2),
            contribution_margin_pct=round(margin, 2),
            gross_ltv=round(gross_ltv, 2),
            contribution_ltv=round(contribution_ltv, 2),
            ltv_cac_ratio=round(ratio, 2),
            payback_months=round(payback, 2) if payback is not None else None,
            profitability=profitability
        )


class CohortAnalyzer:
    """Aggregates customer economics by acquisition cohort."""

    @staticmethod
    def analyze(cohorts: list[Cohort]) -> list[dict]:
        results = []

        for cohort in cohorts:
            if not cohort.customers:
                continue

            revenue = sum(c.monthly_revenue for c in cohort.customers)
            variable_cost = sum(c.monthly_variable_cost for c in cohort.customers)
            contribution = revenue - variable_cost

            results.append({
                "cohort": cohort.name,
                "customers": len(cohort.customers),
                "monthly_revenue": round(revenue, 2),
                "monthly_variable_cost": round(variable_cost, 2),
                "monthly_contribution": round(contribution, 2),
                "contribution_margin_pct": round(
                    contribution / revenue * 100, 2
                ) if revenue else 0.0
            })

        return results


class ChannelAnalyzer:
    """Compares acquisition channels using weighted acquisition costs."""

    @staticmethod
    def analyze(acquisitions: list[Acquisition]) -> list[dict]:
        grouped: dict[Channel, dict] = {}

        for item in acquisitions:
            data = grouped.setdefault(
                item.channel,
                {"cost": 0.0, "customers": 0}
            )

            data["cost"] += (
                item.advertising_cost
                + item.sales_cost
                + item.marketing_cost
            )
            data["customers"] += item.new_customers

        return [
            {
                "channel": channel.value,
                "total_cost": round(data["cost"], 2),
                "customers": data["customers"],
                "cac": round(data["cost"] / data["customers"], 2)
            }
            for channel, data in sorted(
                grouped.items(),
                key=lambda item: item[1]["cost"] / item[1]["customers"]
            )
        ]


class SensitivityAnalyzer:
    """Tests the effect of changes in revenue, churn and acquisition cost."""

    @staticmethod
    def calculate(
        monthly_revenue: float,
        monthly_variable_cost: float,
        lifetime_months: float,
        cac: float,
        revenue_changes: list[float]
    ) -> list[dict]:

        results = []

        for change in revenue_changes:
            if change <= -1:
                raise ValidationError("Revenue reduction cannot be 100% or greater.")

            adjusted_revenue = monthly_revenue * (1 + change)

            contribution = adjusted_revenue - monthly_variable_cost
            ltv = contribution * lifetime_months

            results.append({
                "revenue_change_pct": round(change * 100, 2),
                "adjusted_revenue": round(adjusted_revenue, 2),
                "monthly_contribution": round(contribution, 2),
                "contribution_ltv": round(ltv, 2),
                "ltv_cac_ratio": round(ltv / cac, 2) if cac else None
            })

        return results


def create_demo_data():
    acquisitions = [
        Acquisition(
            Channel.PAID_SEARCH, 30000, 10000, 10000, 100, "2026-01"
        ),
        Acquisition(
            Channel.SOCIAL, 18000, 6000, 6000, 120, "2026-01"
        ),
        Acquisition(
            Channel.REFERRAL, 5000, 2000, 3000, 100, "2026-01"
        ),
        Acquisition(
            Channel.ORGANIC, 0, 4000, 6000, 100, "2026-01"
        )
    ]

    customers = [
        CustomerEconomics(
            "C001", "2026-Q1", Channel.PAID_SEARCH,
            1000, 300, 18, 0.04
        ),
        CustomerEconomics(
            "C002", "2026-Q1", Channel.SOCIAL,
            800, 280, 15, 0.05
        ),
        CustomerEconomics(
            "C003", "2026-Q1", Channel.REFERRAL,
            1200, 350, 24, 0.025
        ),
        CustomerEconomics(
            "C004", "2026-Q1", Channel.ORGANIC,
            900, 270, 20, 0.035
        )
    ]

    return acquisitions, customers


def export_report(report: dict, filename: str = "unit_economics_report.json"):
    path = Path(filename).resolve()

    # Restrict report filenames to the current working directory.
    if path.parent != Path.cwd().resolve():
        raise ValidationError("Report must be saved in the current directory.")

    temporary = path.with_suffix(path.suffix + ".tmp")

    try:
        temporary.write_text(
            json.dumps(report, indent=4, allow_nan=False),
            encoding="utf-8"
        )
        temporary.replace(path)
        logger.info("Report exported to %s", path)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def run_tests(engine: UnitEconomicsEngine):
    assert engine.calculate_cac(
        Acquisition(Channel.ORGANIC, 0, 100, 100, 10, "test")
    ) == 20

    contribution, margin = engine.calculate_contribution_margin(1000, 300)
    assert contribution == 700
    assert margin == 70

    assert engine.calculate_payback(700, 100) == 7
    assert engine.calculate_payback(700, 0) is None

    try:
        engine.calculate_contribution_margin(100, 120)
    except AssertionError:
        raise
    except ValidationError:
        pass

    logger.info("Core calculation tests passed.")


def main():
    engine = UnitEconomicsEngine()
    run_tests(engine)

    acquisitions, customers = create_demo_data()

    customer_results = []

    for acquisition, customer in zip(acquisitions, customers):
        result = engine.evaluate(acquisition, customer)

        customer_results.append({
            "customer_id": customer.customer_id,
            "channel": customer.acquisition_channel.value,
            "metrics": asdict(result)
        })

    cohorts = [
        Cohort("2026-Q1", customers)
    ]

    report = {
        "generated_at": datetime.now().isoformat(),
        "currency": "INR",
        "metric_definitions": {
            "cac": "Total acquisition expenditure / new customers",
            "contribution_margin": "Revenue minus variable costs",
            "contribution_ltv": "Monthly contribution multiplied by expected lifetime",
            "ltv_cac_ratio": "Contribution LTV / CAC",
            "payback": "CAC / monthly contribution"
        },
        "customer_analysis": customer_results,
        "channel_analysis": ChannelAnalyzer.analyze(acquisitions),
        "cohort_analysis": CohortAnalyzer.analyze(cohorts),
        "sensitivity_analysis": SensitivityAnalyzer.calculate(
            1000, 300, 18, 500,
            [-0.20, -0.10, 0, 0.10, 0.20]
        )
    }

    print(json.dumps(report, indent=4, allow_nan=False))
    export_report(report)


if __name__ == "__main__":
    main()
