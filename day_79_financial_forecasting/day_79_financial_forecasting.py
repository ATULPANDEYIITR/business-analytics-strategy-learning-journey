#!/usr/bin/env python3
"""
Financial Forecasting Engine
Revenue, expense, profit, and cash-flow forecasting.

Features:
- Historical financial data management
- Revenue and expense forecasting
- Trend and moving-average calculations
- Growth-rate analysis
- Scenario-based forecasting
- Cash-flow projections
- Budget variance analysis
- Financial risk indicators
- Validation and exception handling
- CSV import and export
- Automated integrity checks

Python 3.10+
Standard library only.
"""

from __future__ import annotations

import csv
import json
import logging
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("financial_forecasting")


class ForecastError(Exception):
    """Base exception for forecasting failures."""


class ValidationError(ForecastError):
    """Invalid financial input."""


class InsufficientDataError(ForecastError):
    """Insufficient historical observations."""


class ScenarioType(Enum):
    BASE = "base"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"


@dataclass(frozen=True)
class FinancialPeriod:
    period: str
    revenue: float
    operating_expenses: float
    investing_expenses: float
    financing_cash_flow: float = 0.0
    opening_cash: float = 0.0

    def __post_init__(self):
        try:
            date.fromisoformat(self.period + "-01")
        except ValueError as exc:
            raise ValidationError(
                f"Invalid period: {self.period}"
            ) from exc

        values = (
            self.revenue,
            self.operating_expenses,
            self.investing_expenses,
            self.financing_cash_flow,
            self.opening_cash
        )

        if not all(math.isfinite(value) for value in values):
            raise ValidationError("Financial values must be finite.")

        if self.revenue < 0:
            raise ValidationError("Revenue cannot be negative.")

        if self.operating_expenses < 0:
            raise ValidationError("Operating expenses cannot be negative.")

        if self.investing_expenses < 0:
            raise ValidationError("Investing expenses cannot be negative.")

        if self.opening_cash < 0:
            raise ValidationError("Opening cash cannot be negative.")

    @property
    def operating_profit(self) -> float:
        return self.revenue - self.operating_expenses

    @property
    def operating_cash_flow(self) -> float:
        return self.operating_profit

    @property
    def net_cash_flow(self) -> float:
        return (
            self.operating_cash_flow
            - self.investing_expenses
            + self.financing_cash_flow
        )

    @property
    def closing_cash(self) -> float:
        return self.opening_cash + self.net_cash_flow


@dataclass(frozen=True)
class ForecastConfig:
    horizon: int = 6
    moving_average_window: int = 3
    optimistic_growth_adjustment: float = 0.05
    pessimistic_growth_adjustment: float = -0.05
    expense_growth_adjustment: float = 0.02

    def __post_init__(self):
        if not 1 <= self.horizon <= 120:
            raise ValidationError("Forecast horizon must be 1 to 120.")

        if self.moving_average_window < 1:
            raise ValidationError("Moving-average window must be positive.")

        adjustments = (
            self.optimistic_growth_adjustment,
            self.pessimistic_growth_adjustment,
            self.expense_growth_adjustment
        )

        if not all(math.isfinite(x) for x in adjustments):
            raise ValidationError("Scenario adjustments must be finite.")


@dataclass(frozen=True)
class ForecastResult:
    period: str
    scenario: str
    revenue: float
    operating_expenses: float
    investing_expenses: float
    operating_profit: float
    net_cash_flow: float
    opening_cash: float
    closing_cash: float
    profit_margin: float
    cash_status: str


class FinancialDataset:
    """Stores chronological financial observations."""

    def __init__(self):
        self._records: dict[str, FinancialPeriod] = {}

    def add(self, record: FinancialPeriod) -> None:
        if record.period in self._records:
            raise ValidationError(
                f"Duplicate financial period: {record.period}"
            )

        self._records[record.period] = record

    def records(self) -> list[FinancialPeriod]:
        return sorted(
            self._records.values(),
            key=lambda record: record.period
        )

    def __len__(self) -> int:
        return len(self._records)

    def validate_cash_sequence(self) -> None:
        records = self.records()

        for previous, current in zip(records, records[1:]):
            if current.opening_cash < 0:
                raise ValidationError("Invalid cash balance.")

            if previous.closing_cash < 0:
                logger.warning(
                    "Negative closing cash in period %s",
                    previous.period
                )


class ForecastEngine:
    def __init__(
        self,
        dataset: FinancialDataset,
        config: ForecastConfig
    ):
        self.dataset = dataset
        self.config = config

        if len(dataset) < config.moving_average_window:
            raise InsufficientDataError(
                "Not enough historical records."
            )

    @staticmethod
    def compound_growth(values: list[float]) -> float:
        """
        Calculate average compound growth.
        Falls back to arithmetic average when the starting value is zero.
        """
        if len(values) < 2:
            return 0.0

        if any(value < 0 for value in values):
            raise ValidationError(
                "Growth calculation requires nonnegative values."
            )

        first = values[0]
        last = values[-1]

        if first > 0:
            periods = len(values) - 1
            return (last / first) ** (1 / periods) - 1

        changes = [
            (current - previous) / max(abs(previous), 1.0)
            for previous, current in zip(values, values[1:])
        ]

        return statistics.mean(changes)

    @staticmethod
    def moving_average(values: list[float], window: int) -> float:
        if not values:
            raise InsufficientDataError("No observations available.")

        selected = values[-window:]
        return statistics.mean(selected)

    def historical_growth(self) -> tuple[float, float]:
        records = self.dataset.records()

        revenue_growth = self.compound_growth(
            [record.revenue for record in records]
        )

        expense_growth = self.compound_growth(
            [record.operating_expenses for record in records]
        )

        return revenue_growth, expense_growth

    @staticmethod
    def next_period(period: str) -> str:
        year, month = map(int, period.split("-"))

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

        return f"{year:04d}-{month:02d}"

    def forecast(
        self,
        scenario: ScenarioType = ScenarioType.BASE
    ) -> list[ForecastResult]:

        records = self.dataset.records()

        revenue_values = [r.revenue for r in records]
        expense_values = [r.operating_expenses for r in records]
        investment_values = [r.investing_expenses for r in records]

        revenue_growth, expense_growth = self.historical_growth()

        revenue_growth += {
            ScenarioType.BASE: 0.0,
            ScenarioType.OPTIMISTIC:
                self.config.optimistic_growth_adjustment,
            ScenarioType.PESSIMISTIC:
                self.config.pessimistic_growth_adjustment
        }[scenario]

        expense_growth += (
            0.0 if scenario == ScenarioType.BASE
            else self.config.expense_growth_adjustment
        )

        revenue_growth = max(-0.95, min(revenue_growth, 1.0))
        expense_growth = max(-0.95, min(expense_growth, 1.0))

        revenue_base = self.moving_average(
            revenue_values,
            self.config.moving_average_window
        )

        expense_base = self.moving_average(
            expense_values,
            self.config.moving_average_window
        )

        investment_base = self.moving_average(
            investment_values,
            self.config.moving_average_window
        )

        cash = records[-1].closing_cash
        period = self.next_period(records[-1].period)

        results = []

        for _ in range(self.config.horizon):
            revenue_base *= 1 + revenue_growth
            expense_base *= 1 + expense_growth

            operating_profit = revenue_base - expense_base

            # Investing expenses are held constant in this model.
            investing_expenses = investment_base

            net_cash_flow = operating_profit - investing_expenses
            opening_cash = cash
            closing_cash = opening_cash + net_cash_flow

            margin = (
                operating_profit / revenue_base
                if revenue_base > 0 else 0.0
            )

            status = (
                "NEGATIVE_CASH"
                if closing_cash < 0
                else "LOW_CASH"
                if closing_cash < expense_base
                else "HEALTHY"
            )

            result = ForecastResult(
                period=period,
                scenario=scenario.value,
                revenue=round(revenue_base, 2),
                operating_expenses=round(expense_base, 2),
                investing_expenses=round(investing_expenses, 2),
                operating_profit=round(operating_profit, 2),
                net_cash_flow=round(net_cash_flow, 2),
                opening_cash=round(opening_cash, 2),
                closing_cash=round(closing_cash, 2),
                profit_margin=round(margin, 4),
                cash_status=status
            )

            results.append(result)

            cash = closing_cash
            period = self.next_period(period)

        return results


class FinancialAnalyzer:
    @staticmethod
    def budget_variance(
        actual: float,
        budget: float
    ) -> dict:
        if not math.isfinite(actual) or not math.isfinite(budget):
            raise ValidationError("Budget values must be finite.")

        variance = actual - budget

        return {
            "actual": round(actual, 2),
            "budget": round(budget, 2),
            "variance": round(variance, 2),
            "variance_percentage": (
                round(variance / abs(budget) * 100, 2)
                if budget != 0 else None
            ),
            "status": (
                "FAVORABLE" if variance >= 0 else "UNFAVORABLE"
            )
        }

    @staticmethod
    def forecast_summary(
        results: list[ForecastResult]
    ) -> dict:
        if not results:
            raise InsufficientDataError("Forecast is empty.")

        total_revenue = sum(r.revenue for r in results)
        total_expenses = sum(r.operating_expenses for r in results)
        total_profit = sum(r.operating_profit for r in results)

        return {
            "periods": len(results),
            "total_revenue": round(total_revenue, 2),
            "total_operating_expenses": round(total_expenses, 2),
            "total_operating_profit": round(total_profit, 2),
            "average_profit_margin": round(
                statistics.mean(r.profit_margin for r in results),
                4
            ),
            "ending_cash": results[-1].closing_cash,
            "negative_cash_periods": sum(
                r.closing_cash < 0 for r in results
            )
        }

    @staticmethod
    def cash_runway(
        cash_balance: float,
        monthly_burn: float
    ) -> Optional[float]:
        if cash_balance < 0 or monthly_burn < 0:
            raise ValidationError("Cash and burn cannot be negative.")

        if monthly_burn == 0:
            return None

        return round(cash_balance / monthly_burn, 2)


def load_csv(path: Path) -> FinancialDataset:
    dataset = FinancialDataset()

    required = {
        "period",
        "revenue",
        "operating_expenses",
        "investing_expenses",
        "financing_cash_flow",
        "opening_cash"
    }

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValidationError("CSV is missing required columns.")

        for row in reader:
            try:
                dataset.add(
                    FinancialPeriod(
                        period=row["period"],
                        revenue=float(row["revenue"]),
                        operating_expenses=float(
                            row["operating_expenses"]
                        ),
                        investing_expenses=float(
                            row["investing_expenses"]
                        ),
                        financing_cash_flow=float(
                            row["financing_cash_flow"]
                        ),
                        opening_cash=float(row["opening_cash"])
                    )
                )
            except (ValueError, TypeError) as exc:
                raise ValidationError(
                    f"Invalid CSV record: {row}"
                ) from exc

    return dataset


def export_forecast(
    results: list[ForecastResult],
    output_path: Path
) -> None:
    if not results:
        raise InsufficientDataError("Cannot export an empty forecast.")

    fields = list(asdict(results[0]).keys())

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))


def create_sample_dataset() -> FinancialDataset:
    dataset = FinancialDataset()

    sample = [
        ("2026-01", 850000, 520000, 65000, 20000, 300000),
        ("2026-02", 875000, 530000, 70000, 0, 595000),
        ("2026-03", 900000, 540000, 60000, -10000, 870000),
        ("2026-04", 925000, 555000, 75000, 15000, 1155000),
        ("2026-05", 960000, 565000, 80000, 0, 1465000),
        ("2026-06", 990000, 580000, 70000, 10000, 1780000)
    ]

    for row in sample:
        dataset.add(FinancialPeriod(*row))

    return dataset


def run_tests() -> None:
    dataset = create_sample_dataset()

    assert len(dataset) == 6

    engine = ForecastEngine(
        dataset,
        ForecastConfig(
            horizon=6,
            moving_average_window=3
        )
    )

    base = engine.forecast(ScenarioType.BASE)
    optimistic = engine.forecast(ScenarioType.OPTIMISTIC)
    pessimistic = engine.forecast(ScenarioType.PESSIMISTIC)

    assert len(base) == 6
    assert optimistic[0].revenue > base[0].revenue
    assert pessimistic[0].revenue < base[0].revenue

    assert abs(
        base[0].closing_cash
        - (
            base[0].opening_cash
            + base[0].net_cash_flow
        )
    ) < 0.01

    try:
        FinancialPeriod(
            "2026-07",
            -100,
            200,
            50
        )
        raise AssertionError("Negative revenue was accepted.")
    except ValidationError:
        pass

    variance = FinancialAnalyzer.budget_variance(950, 1000)
    assert variance["variance"] == -50

    assert FinancialAnalyzer.cash_runway(10000, 2000) == 5

    logger.info("All forecasting tests passed.")


def main() -> None:
    run_tests()

    dataset = create_sample_dataset()
    dataset.validate_cash_sequence()

    config = ForecastConfig(
        horizon=6,
        moving_average_window=3
    )

    engine = ForecastEngine(dataset, config)

    print("\nFINANCIAL FORECASTING ENGINE")
    print("=" * 90)

    all_summaries = {}

    for scenario in ScenarioType:
        results = engine.forecast(scenario)

        print(f"\nSCENARIO: {scenario.value.upper()}")
        print("-" * 90)

        for result in results:
            print(
                f"{result.period} | "
                f"Revenue: {result.revenue:>12,.2f} | "
                f"Expenses: {result.operating_expenses:>12,.2f} | "
                f"Profit: {result.operating_profit:>12,.2f} | "
                f"Cash: {result.closing_cash:>12,.2f} | "
                f"{result.cash_status}"
            )

        all_summaries[scenario.value] = (
            FinancialAnalyzer.forecast_summary(results)
        )

        if scenario == ScenarioType.BASE:
            export_forecast(
                results,
                Path("financial_forecast.csv")
            )

    print("\nSCENARIO COMPARISON")
    print(json.dumps(all_summaries, indent=2))

    latest = dataset.records()[-1]

    print("\nFINANCIAL INDICATORS")
    print(
        "Historical operating profit:",
        f"{latest.operating_profit:,.2f}"
    )
    print(
        "Historical closing cash:",
        f"{latest.closing_cash:,.2f}"
    )

    base_summary = all_summaries["base"]

    print(
        "Forecast ending cash:",
        f"{base_summary['ending_cash']:,.2f}"
    )

    print("\nForecast exported to financial_forecast.csv")


if __name__ == "__main__":
    try:
        main()
    except ForecastError as error:
        logger.error("Forecasting failed: %s", error)
        raise SystemExit(1)
    except OSError as error:
        logger.error("File operation failed: %s", error)
        raise SystemExit(1)
