#!/usr/bin/env python3
"""
Cost Analytics and Cost Optimization Engine

Demonstrates:
- Fixed, variable, semi-variable, direct and indirect costs
- Cost classification and cost allocation
- Contribution margin and break-even analysis
- Cost centre performance
- Budget variance analysis
- Unit economics
- Cost optimization scenarios
- Sensitivity analysis
- JSON reporting and validation
"""

from __future__ import annotations

import json
import logging
import math
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Iterable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("cost_analytics")


class CostType(str, Enum):
    FIXED = "fixed"
    VARIABLE = "variable"
    SEMI_VARIABLE = "semi_variable"


class CostBehavior(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"


class CostCategory(str, Enum):
    LABOR = "labor"
    MATERIALS = "materials"
    TECHNOLOGY = "technology"
    FACILITIES = "facilities"
    LOGISTICS = "logistics"
    ADMINISTRATION = "administration"


class AnalyticsError(Exception):
    """Base exception for cost analytics."""


class ValidationError(AnalyticsError):
    """Raised when financial input is invalid."""


class OptimizationError(AnalyticsError):
    """Raised when an optimization scenario is infeasible."""


@dataclass(frozen=True)
class CostRecord:
    record_id: str
    cost_center: str
    category: CostCategory
    cost_type: CostType
    behavior: CostBehavior
    amount: float
    activity_units: float
    period: str
    description: str

    def __post_init__(self):
        if not self.record_id.strip():
            raise ValidationError("Record ID cannot be empty.")
        if not self.cost_center.strip():
            raise ValidationError("Cost centre cannot be empty.")
        if not math.isfinite(self.amount) or self.amount < 0:
            raise ValidationError("Cost must be finite and non-negative.")
        if not math.isfinite(self.activity_units) or self.activity_units < 0:
            raise ValidationError("Activity units must be non-negative.")
        if not self.period.strip():
            raise ValidationError("Period is required.")


@dataclass(frozen=True)
class Budget:
    cost_center: str
    period: str
    allocated_amount: float

    def __post_init__(self):
        if not math.isfinite(self.allocated_amount) or self.allocated_amount < 0:
            raise ValidationError("Invalid budget amount.")


@dataclass(frozen=True)
class CostOptimization:
    name: str
    category: CostCategory
    reduction_rate: float
    implementation_cost: float
    risk_score: float
    description: str

    def __post_init__(self):
        if not 0 <= self.reduction_rate <= 1:
            raise ValidationError("Reduction rate must be between 0 and 1.")
        if self.implementation_cost < 0:
            raise ValidationError("Implementation cost cannot be negative.")
        if not 0 <= self.risk_score <= 10:
            raise ValidationError("Risk score must be between 0 and 10.")


class CostLedger:
    """Stores validated financial records with unique identifiers."""

    def __init__(self):
        self._records: dict[str, CostRecord] = {}

    def add(self, record: CostRecord) -> None:
        if record.record_id in self._records:
            raise ValidationError(
                f"Duplicate record ID: {record.record_id}"
            )
        self._records[record.record_id] = record

    def records(
        self,
        period: str | None = None,
        cost_center: str | None = None
    ) -> list[CostRecord]:
        return [
            record
            for record in self._records.values()
            if (period is None or record.period == period)
            and (
                cost_center is None
                or record.cost_center == cost_center
            )
        ]

    def total(self, records: Iterable[CostRecord] | None = None) -> float:
        selected = records if records is not None else self._records.values()
        return sum(record.amount for record in selected)

    def export_json(self, path: Path) -> None:
        """Write a complete ledger without exposing sensitive credentials."""
        payload = [
            {
                **asdict(record),
                "category": record.category.value,
                "cost_type": record.cost_type.value,
                "behavior": record.behavior.value,
            }
            for record in self._records.values()
        ]

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")

        try:
            temporary.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8"
            )
            temporary.replace(path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise


class CostAnalyzer:
    def __init__(self, ledger: CostLedger):
        self.ledger = ledger

    def classification(self, period: str) -> dict:
        result = {
            "by_type": defaultdict(float),
            "by_behavior": defaultdict(float),
            "by_category": defaultdict(float),
        }

        for record in self.ledger.records(period=period):
            result["by_type"][record.cost_type.value] += record.amount
            result["by_behavior"][record.behavior.value] += record.amount
            result["by_category"][record.category.value] += record.amount

        return {
            key: dict(values)
            for key, values in result.items()
        }

    def cost_center_report(self, period: str) -> dict:
        report = defaultdict(float)

        for record in self.ledger.records(period=period):
            report[record.cost_center] += record.amount

        return dict(sorted(report.items()))

    def unit_cost(self, period: str) -> float:
        records = self.ledger.records(period=period)
        total_cost = self.ledger.total(records)
        activity = sum(record.activity_units for record in records)

        if activity <= 0:
            raise AnalyticsError(
                "Unit cost cannot be calculated without activity."
            )

        return total_cost / activity

    def break_even(
        self,
        fixed_cost: float,
        selling_price: float,
        variable_cost_per_unit: float
    ) -> dict:
        if fixed_cost < 0:
            raise ValidationError("Fixed cost cannot be negative.")

        if selling_price <= 0:
            raise ValidationError("Selling price must be positive.")

        if variable_cost_per_unit < 0:
            raise ValidationError("Variable cost cannot be negative.")

        contribution = selling_price - variable_cost_per_unit

        if contribution <= 0:
            raise AnalyticsError(
                "Break-even is impossible: contribution is not positive."
            )

        units = math.ceil(fixed_cost / contribution)

        return {
            "contribution_per_unit": contribution,
            "contribution_margin_percent": (
                contribution / selling_price * 100
            ),
            "break_even_units": units,
            "break_even_revenue": units * selling_price,
        }

    def budget_variance(
        self,
        budget: Budget,
        actual_cost: float
    ) -> dict:
        variance = budget.allocated_amount - actual_cost

        return {
            "budget": budget.allocated_amount,
            "actual": actual_cost,
            "variance": variance,
            "variance_percent": (
                variance / budget.allocated_amount * 100
                if budget.allocated_amount else None
            ),
            "status": (
                "UNDER_BUDGET" if variance >= 0 else "OVER_BUDGET"
            ),
        }

    def allocation_report(self, period: str) -> dict:
        """Allocate indirect costs proportionally to direct costs."""
        records = self.ledger.records(period=period)

        direct_by_center = defaultdict(float)
        indirect_total = 0.0

        for record in records:
            if record.behavior == CostBehavior.DIRECT:
                direct_by_center[record.cost_center] += record.amount
            else:
                indirect_total += record.amount

        direct_total = sum(direct_by_center.values())

        if direct_total == 0:
            if indirect_total:
                raise AnalyticsError(
                    "Indirect costs cannot be allocated without a "
                    "direct-cost allocation base."
                )
            return {}

        return {
            center: {
                "direct_cost": direct,
                "allocated_indirect": (
                    indirect_total * direct / direct_total
                ),
                "total_allocated": (
                    direct + indirect_total * direct / direct_total
                ),
            }
            for center, direct in direct_by_center.items()
        }


class OptimizationEngine:
    """Evaluates independent cost-saving proposals."""

    def __init__(self, analyzer: CostAnalyzer):
        self.analyzer = analyzer

    def evaluate(
        self,
        period: str,
        proposals: list[CostOptimization],
        maximum_risk: float = 5.0
    ) -> dict:
        if not 0 <= maximum_risk <= 10:
            raise ValidationError("Invalid maximum risk.")

        records = self.analyzer.ledger.records(period=period)
        category_totals = defaultdict(float)

        for record in records:
            category_totals[record.category] += record.amount

        results = []
        total_savings = 0.0
        total_implementation = 0.0

        for proposal in proposals:
            baseline = category_totals[proposal.category]

            if baseline == 0:
                savings = 0.0
                eligible = False
                reason = "No baseline expenditure in category."
            elif proposal.risk_score > maximum_risk:
                savings = 0.0
                eligible = False
                reason = "Risk exceeds permitted threshold."
            elif proposal.implementation_cost >= (
                baseline * proposal.reduction_rate
            ):
                savings = 0.0
                eligible = False
                reason = "Implementation cost exceeds gross savings."
            else:
                savings = baseline * proposal.reduction_rate
                eligible = True
                reason = "Eligible."

            net_savings = savings - (
                proposal.implementation_cost if eligible else 0
            )

            if eligible:
                total_savings += savings
                total_implementation += proposal.implementation_cost

            results.append({
                "proposal": proposal.name,
                "baseline_cost": baseline,
                "gross_savings": savings,
                "implementation_cost": (
                    proposal.implementation_cost if eligible else 0
                ),
                "net_savings": net_savings,
                "risk_score": proposal.risk_score,
                "eligible": eligible,
                "reason": reason,
            })

        return {
            "period": period,
            "gross_savings": total_savings,
            "implementation_cost": total_implementation,
            "net_savings": total_savings - total_implementation,
            "proposals": results,
        }


def build_sample_ledger() -> CostLedger:
    ledger = CostLedger()

    samples = [
        CostRecord(
            "C001", "PRODUCTION", CostCategory.LABOR,
            CostType.FIXED, CostBehavior.DIRECT,
            120000, 1000, "2026-10", "Production workforce"
        ),
        CostRecord(
            "C002", "PRODUCTION", CostCategory.MATERIALS,
            CostType.VARIABLE, CostBehavior.DIRECT,
            180000, 1000, "2026-10", "Raw materials"
        ),
        CostRecord(
            "C003", "PRODUCTION", CostCategory.FACILITIES,
            CostType.FIXED, CostBehavior.INDIRECT,
            45000, 1000, "2026-10", "Factory rent"
        ),
        CostRecord(
            "C004", "TECHNOLOGY", CostCategory.TECHNOLOGY,
            CostType.SEMI_VARIABLE, CostBehavior.INDIRECT,
            60000, 1000, "2026-10", "Cloud infrastructure"
        ),
        CostRecord(
            "C005", "LOGISTICS", CostCategory.LOGISTICS,
            CostType.VARIABLE, CostBehavior.DIRECT,
            35000, 1000, "2026-10", "Distribution"
        ),
        CostRecord(
            "C006", "ADMINISTRATION", CostCategory.ADMINISTRATION,
            CostType.FIXED, CostBehavior.INDIRECT,
            25000, 1000, "2026-10", "Administrative services"
        ),
    ]

    for record in samples:
        ledger.add(record)

    return ledger


def run_tests() -> None:
    ledger = CostLedger()

    record = CostRecord(
        "T001", "TEST", CostCategory.LABOR,
        CostType.FIXED, CostBehavior.DIRECT,
        100, 10, "2026-10", "Test cost"
    )

    ledger.add(record)

    try:
        ledger.add(record)
        raise AssertionError("Duplicate record was accepted.")
    except ValidationError:
        pass

    analyzer = CostAnalyzer(ledger)
    assert analyzer.unit_cost("2026-10") == 10

    result = analyzer.break_even(1000, 100, 60)
    assert result["break_even_units"] == 25

    assert analyzer.budget_variance(
        Budget("TEST", "2026-10", 150),
        100
    )["status"] == "UNDER_BUDGET"

    try:
        analyzer.break_even(1000, 50, 60)
        raise AssertionError("Invalid contribution was accepted.")
    except AnalyticsError:
        pass

    logger.info("All validation tests passed.")


def main() -> None:
    run_tests()

    ledger = build_sample_ledger()
    analyzer = CostAnalyzer(ledger)
    optimizer = OptimizationEngine(analyzer)

    period = "2026-10"

    print("\nCOST ANALYTICS REPORT")
    print("=" * 55)

    total = ledger.total(ledger.records(period=period))
    print(f"Reporting period: {period}")
    print(f"Total expenditure: Rs. {total:,.2f}")
    print(f"Unit cost: Rs. {analyzer.unit_cost(period):,.2f}")

    print("\nCOST CLASSIFICATION")
    for classification, values in analyzer.classification(period).items():
        print(f"\n{classification.upper()}")
        for name, amount in values.items():
            print(f"  {name}: Rs. {amount:,.2f}")

    print("\nCOST CENTRE PERFORMANCE")
    for center, amount in analyzer.cost_center_report(period).items():
        print(f"  {center}: Rs. {amount:,.2f}")

    budget = Budget("PRODUCTION", period, 350000)
    actual = sum(
        record.amount
        for record in ledger.records(
            period=period,
            cost_center="PRODUCTION"
        )
    )

    print("\nBUDGET VARIANCE")
    print(analyzer.budget_variance(budget, actual))

    print("\nBREAK-EVEN ANALYSIS")
    print(
        analyzer.break_even(
            fixed_cost=150000,
            selling_price=500,
            variable_cost_per_unit=300
        )
    )

    print("\nINDIRECT COST ALLOCATION")
    for center, values in analyzer.allocation_report(period).items():
        print(center, values)

    proposals = [
        CostOptimization(
            "Cloud resource rightsizing",
            CostCategory.TECHNOLOGY,
            0.20,
            3000,
            2,
            "Reduce unused computing capacity."
        ),
        CostOptimization(
            "Material procurement optimization",
            CostCategory.MATERIALS,
            0.08,
            5000,
            3,
            "Consolidate procurement volumes."
        ),
        CostOptimization(
            "Logistics route optimization",
            CostCategory.LOGISTICS,
            0.15,
            2000,
            4,
            "Optimize distribution routes."
        ),
        CostOptimization(
            "High-risk supplier replacement",
            CostCategory.LABOR,
            0.10,
            1000,
            9,
            "Rejected because of risk."
        ),
    ]

    print("\nOPTIMIZATION SCENARIO")
    report = optimizer.evaluate(period, proposals)

    print(json.dumps(report, indent=2))

    # Export to a temporary demonstration file.
    output = Path(tempfile.gettempdir()) / "cost_analytics_report.json"
    ledger.export_json(output)
    print(f"\nLedger exported to: {output}")

    logger.info("Cost analytics execution completed.")


if __name__ == "__main__":
    main()
