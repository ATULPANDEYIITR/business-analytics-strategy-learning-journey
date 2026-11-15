#!/usr/bin/env python3
"""
Revenue Analytics: Revenue Decomposition and Growth Analysis

Features:
- Revenue calculation and validation
- Period-over-period and year-over-year growth
- Revenue decomposition into volume, mix, and price effects
- Product and regional contribution analysis
- Customer and product performance
- Concentration and profitability indicators
- Forecasting using historical growth
- CSV export and reproducible reporting

Python 3.10+
Standard-library only.
"""

from __future__ import annotations

import csv
import json
import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
LOGGER = logging.getLogger("revenue_analytics")


class RevenueAnalyticsError(Exception):
    """Base exception for revenue analytics."""


class DataValidationError(RevenueAnalyticsError):
    """Raised when revenue data violates business rules."""


class PeriodComparisonError(RevenueAnalyticsError):
    """Raised when comparison periods are invalid."""


@dataclass(frozen=True)
class RevenueRecord:
    period: str
    product: str
    region: str
    customer: str
    units: int
    list_price: float
    discount_rate: float
    variable_cost_per_unit: float

    def __post_init__(self):
        try:
            date.fromisoformat(self.period + "-01")
        except ValueError as exc:
            raise DataValidationError(
                f"Invalid period: {self.period}"
            ) from exc

        if not self.product.strip():
            raise DataValidationError("Product cannot be empty.")

        if not self.region.strip():
            raise DataValidationError("Region cannot be empty.")

        if not self.customer.strip():
            raise DataValidationError("Customer cannot be empty.")

        if self.units < 0:
            raise DataValidationError("Units cannot be negative.")

        values = (
            self.list_price,
            self.discount_rate,
            self.variable_cost_per_unit
        )

        if not all(math.isfinite(value) for value in values):
            raise DataValidationError("Financial values must be finite.")

        if self.list_price < 0:
            raise DataValidationError("List price cannot be negative.")

        if not 0 <= self.discount_rate <= 1:
            raise DataValidationError(
                "Discount rate must be between 0 and 1."
            )

        if self.variable_cost_per_unit < 0:
            raise DataValidationError("Variable cost cannot be negative.")

    @property
    def net_price(self) -> float:
        return self.list_price * (1 - self.discount_rate)

    @property
    def revenue(self) -> float:
        return self.units * self.net_price

    @property
    def variable_cost(self) -> float:
        return self.units * self.variable_cost_per_unit

    @property
    def gross_profit(self) -> float:
        return self.revenue - self.variable_cost


@dataclass(frozen=True)
class ProductMetrics:
    product: str
    units: int
    revenue: float
    average_price: float
    gross_profit: float
    margin_rate: float
    revenue_share: float


@dataclass(frozen=True)
class Decomposition:
    previous_revenue: float
    current_revenue: float
    revenue_change: float
    volume_effect: float
    mix_effect: float
    price_effect: float

    @property
    def reconciliation_difference(self) -> float:
        return self.revenue_change - (
            self.volume_effect
            + self.mix_effect
            + self.price_effect
        )


class RevenueAnalytics:
    def __init__(self, records: Iterable[RevenueRecord]):
        self.records = list(records)

        if not self.records:
            raise DataValidationError("Dataset cannot be empty.")

        self._validate_unique_dimensions()

    def _validate_unique_dimensions(self):
        seen = set()

        for record in self.records:
            key = (
                record.period,
                record.product,
                record.region,
                record.customer
            )

            if key in seen:
                raise DataValidationError(
                    f"Duplicate analytical record: {key}"
                )

            seen.add(key)

    def periods(self) -> list[str]:
        return sorted({r.period for r in self.records})

    def available_records(self, period: str) -> list[RevenueRecord]:
        result = [r for r in self.records if r.period == period]

        if not result:
            raise PeriodComparisonError(
                f"No records available for {period}."
            )

        return result

    @staticmethod
    def aggregate(records: Iterable[RevenueRecord]) -> dict:
        records = list(records)

        units = sum(r.units for r in records)
        revenue = sum(r.revenue for r in records)
        cost = sum(r.variable_cost for r in records)
        profit = revenue - cost

        return {
            "units": units,
            "revenue": revenue,
            "variable_cost": cost,
            "gross_profit": profit,
            "average_selling_price": revenue / units if units else 0.0,
            "gross_margin": profit / revenue if revenue else 0.0
        }

    def growth_analysis(self, previous: str, current: str) -> dict:
        if previous >= current:
            raise PeriodComparisonError(
                "Current period must follow previous period."
            )

        old = self.aggregate(self.available_records(previous))
        new = self.aggregate(self.available_records(current))

        revenue_change = new["revenue"] - old["revenue"]
        unit_change = new["units"] - old["units"]

        growth = (
            revenue_change / old["revenue"]
            if old["revenue"] else None
        )

        return {
            "previous_period": previous,
            "current_period": current,
            "previous_revenue": old["revenue"],
            "current_revenue": new["revenue"],
            "revenue_change": revenue_change,
            "revenue_growth_rate": growth,
            "previous_units": old["units"],
            "current_units": new["units"],
            "unit_change": unit_change,
            "previous_average_price": old["average_selling_price"],
            "current_average_price": new["average_selling_price"],
            "previous_gross_margin": old["gross_margin"],
            "current_gross_margin": new["gross_margin"]
        }

    @staticmethod
    def _product_metrics(records: list[RevenueRecord]) -> dict:
        groups = defaultdict(list)

        for record in records:
            groups[record.product].append(record)

        total_revenue = sum(r.revenue for r in records)
        results = {}

        for product, rows in groups.items():
            metrics = RevenueAnalytics.aggregate(rows)
            revenue = metrics["revenue"]

            results[product] = ProductMetrics(
                product=product,
                units=metrics["units"],
                revenue=revenue,
                average_price=metrics["average_selling_price"],
                gross_profit=metrics["gross_profit"],
                margin_rate=metrics["gross_margin"],
                revenue_share=(
                    revenue / total_revenue if total_revenue else 0.0
                )
            )

        return results

    def decompose_revenue(
        self,
        previous: str,
        current: str
    ) -> Decomposition:
        """
        Exact sequential decomposition:

        Volume effect:
            (Q1 - Q0) * sum(s0 * P0)

        Mix effect:
            Q1 * sum((s1 - s0) * P0)

        Price effect:
            Q1 * sum(s1 * (P1 - P0))

        Q = total units.
        s = product unit share.
        P = product weighted average selling price.

        The three effects reconcile exactly to the revenue change.
        """
        old_records = self.available_records(previous)
        new_records = self.available_records(current)

        old = self._product_metrics(old_records)
        new = self._product_metrics(new_records)

        products = set(old) | set(new)

        q0 = sum(r.units for r in old_records)
        q1 = sum(r.units for r in new_records)

        if q0 == 0 or q1 == 0:
            raise PeriodComparisonError(
                "Decomposition requires positive units in both periods."
            )

        old_shares = {
            p: old[p].units / q0 if p in old else 0.0
            for p in products
        }

        new_shares = {
            p: new[p].units / q1 if p in new else 0.0
            for p in products
        }

        old_prices = {
            p: old[p].average_price if p in old else 0.0
            for p in products
        }

        new_prices = {
            p: new[p].average_price if p in new else 0.0
            for p in products
        }

        volume_effect = (q1 - q0) * sum(
            old_shares[p] * old_prices[p]
            for p in products
        )

        mix_effect = q1 * sum(
            (new_shares[p] - old_shares[p]) * old_prices[p]
            for p in products
        )

        price_effect = q1 * sum(
            new_shares[p] * (new_prices[p] - old_prices[p])
            for p in products
        )

        result = Decomposition(
            previous_revenue=self.aggregate(old_records)["revenue"],
            current_revenue=self.aggregate(new_records)["revenue"],
            revenue_change=(
                self.aggregate(new_records)["revenue"]
                - self.aggregate(old_records)["revenue"]
            ),
            volume_effect=volume_effect,
            mix_effect=mix_effect,
            price_effect=price_effect
        )

        if not math.isclose(
            result.reconciliation_difference,
            0.0,
            abs_tol=0.000001
        ):
            raise RevenueAnalyticsError(
                "Revenue decomposition failed reconciliation."
            )

        return result

    def dimension_analysis(
        self,
        period: str,
        dimension: str
    ) -> list[dict]:
        allowed = {
            "product": lambda r: r.product,
            "region": lambda r: r.region,
            "customer": lambda r: r.customer
        }

        if dimension not in allowed:
            raise ValueError(f"Unsupported dimension: {dimension}")

        groups = defaultdict(list)

        for record in self.available_records(period):
            groups[allowed[dimension](record)].append(record)

        total = self.aggregate(self.available_records(period))["revenue"]
        results = []

        for name, rows in groups.items():
            metrics = self.aggregate(rows)

            results.append({
                "dimension": dimension,
                "name": name,
                **metrics,
                "revenue_share": (
                    metrics["revenue"] / total if total else 0.0
                )
            })

        return sorted(
            results,
            key=lambda item: item["revenue"],
            reverse=True
        )

    def customer_concentration(self, period: str) -> dict:
        rows = self.dimension_analysis(period, "customer")
        shares = [row["revenue_share"] for row in rows]

        hhi = sum(share ** 2 for share in shares)

        return {
            "customer_count": len(rows),
            "largest_customer_share": max(shares, default=0.0),
            "top_five_share": sum(shares[:5]),
            "revenue_concentration_hhi": hhi,
            "interpretation": (
                "Higher HHI indicates greater customer concentration."
            )
        }

    def forecast(
        self,
        periods: int,
        method: str = "average_growth"
    ) -> list[dict]:
        if periods <= 0 or periods > 36:
            raise ValueError("Forecast horizon must be between 1 and 36.")

        available = self.periods()

        if len(available) < 2:
            raise PeriodComparisonError(
                "At least two historical periods are required."
            )

        values = [
            self.aggregate(self.available_records(p))["revenue"]
            for p in available
        ]

        if method == "average_growth":
            rates = []

            for previous, current in zip(values, values[1:]):
                if previous <= 0:
                    raise RevenueAnalyticsError(
                        "Growth forecast requires positive base revenue."
                    )
                rates.append(current / previous - 1)

            rate = sum(rates) / len(rates)

        elif method == "linear":
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n

            denominator = sum(
                (i - x_mean) ** 2 for i in range(n)
            )

            slope = sum(
                (i - x_mean) * (value - y_mean)
                for i, value in enumerate(values)
            ) / denominator

            forecast_values = [
                max(0.0, y_mean + slope * (n + i - x_mean))
                for i in range(periods)
            ]

            return [
                {
                    "forecast_step": i + 1,
                    "revenue": value,
                    "method": "linear"
                }
                for i, value in enumerate(forecast_values)
            ]

        else:
            raise ValueError("Unknown forecasting method.")

        result = []
        last_value = values[-1]

        for step in range(1, periods + 1):
            last_value *= 1 + rate

            result.append({
                "forecast_step": step,
                "revenue": max(0.0, last_value),
                "method": method,
                "assumed_growth_rate": rate
            })

        return result

    def export_csv(self, filename: str):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(asdict(self.records[0]).keys())
            )
            writer.writeheader()

            for record in self.records:
                writer.writerow(asdict(record))

        LOGGER.info("Exported %s records to %s", len(self.records), path)

    def export_report(self, filename: str, previous: str, current: str):
        report = {
            "growth_analysis": self.growth_analysis(previous, current),
            "decomposition": asdict(
                self.decompose_revenue(previous, current)
            ),
            "product_analysis": self.dimension_analysis(current, "product"),
            "regional_analysis": self.dimension_analysis(current, "region"),
            "customer_concentration": self.customer_concentration(current),
            "forecast": self.forecast(3)
        }

        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=4)

        LOGGER.info("Report saved to %s", path)


def create_sample_data() -> list[RevenueRecord]:
    """Create a deterministic multi-period commercial dataset."""

    source = [
        ("2026-01", "Cloud", "North", "Customer A", 100, 1200, .05, 600),
        ("2026-01", "Software", "South", "Customer B", 180, 500, .10, 180),
        ("2026-01", "Hardware", "East", "Customer C", 250, 300, .08, 190),
        ("2026-01", "Services", "West", "Customer D", 90, 900, .05, 400),
        ("2026-02", "Cloud", "North", "Customer A", 115, 1250, .04, 600),
        ("2026-02", "Software", "South", "Customer B", 200, 520, .08, 180),
        ("2026-02", "Hardware", "East", "Customer C", 230, 310, .05, 190),
        ("2026-02", "Services", "West", "Customer D", 105, 920, .04, 400),
        ("2026-03", "Cloud", "North", "Customer A", 130, 1300, .03, 600),
        ("2026-03", "Software", "South", "Customer B", 220, 540, .07, 180),
        ("2026-03", "Hardware", "East", "Customer C", 245, 320, .05, 190),
        ("2026-03", "Services", "West", "Customer D", 115, 950, .03, 400),
        ("2026-04", "Cloud", "North", "Customer A", 145, 1350, .03, 600),
        ("2026-04", "Software", "South", "Customer B", 240, 550, .06, 180),
        ("2026-04", "Hardware", "East", "Customer C", 260, 330, .06, 190),
        ("2026-04", "Services", "West", "Customer D", 130, 970, .04, 400)
    ]

    return [
        RevenueRecord(*row)
        for row in source
    ]


def run_tests(analytics: RevenueAnalytics):
    # Revenue must equal units multiplied by net realized price.
    sample = analytics.records[0]
    assert math.isclose(
        sample.revenue,
        sample.units * sample.net_price
    )

    # Every period must reconcile across products.
    for period in analytics.periods():
        records = analytics.available_records(period)
        assert math.isclose(
            sum(r.revenue for r in records),
            analytics.aggregate(records)["revenue"]
        )

    # Decomposition must reconcile to total revenue change.
    result = analytics.decompose_revenue("2026-03", "2026-04")

    assert math.isclose(
        result.volume_effect
        + result.mix_effect
        + result.price_effect,
        result.revenue_change,
        abs_tol=0.000001
    )

    assert analytics.growth_analysis(
        "2026-03", "2026-04"
    )["revenue_change"] > 0

    try:
        RevenueRecord(
            "2026-01", "Invalid", "North", "Customer X",
            -1, 100, .05, 50
        )
    except DataValidationError:
        pass
    else:
        raise AssertionError("Negative units were not rejected.")

    LOGGER.info("All validation tests passed.")


def main():
    analytics = RevenueAnalytics(create_sample_data())

    run_tests(analytics)

    previous = "2026-03"
    current = "2026-04"

    print("\nREVENUE PERFORMANCE")
    print(json.dumps(
        analytics.growth_analysis(previous, current),
        indent=4
    ))

    print("\nREVENUE DECOMPOSITION")
    print(json.dumps(
        asdict(analytics.decompose_revenue(previous, current)),
        indent=4
    ))

    print("\nPRODUCT PERFORMANCE")

    for item in analytics.dimension_analysis(current, "product"):
        print(json.dumps(item, indent=2))

    print("\nREGIONAL PERFORMANCE")

    for item in analytics.dimension_analysis(current, "region"):
        print(json.dumps(item, indent=2))

    print("\nCUSTOMER CONCENTRATION")
    print(json.dumps(
        analytics.customer_concentration(current),
        indent=4
    ))

    print("\nTHREE-PERIOD FORECAST")
    print(json.dumps(analytics.forecast(3), indent=4))

    analytics.export_csv("output/revenue_records.csv")
    analytics.export_report(
        "output/revenue_analytics_report.json",
        previous,
        current
    )


if __name__ == "__main__":
    main()
