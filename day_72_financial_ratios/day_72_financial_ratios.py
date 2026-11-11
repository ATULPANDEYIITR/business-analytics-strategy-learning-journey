#!/usr/bin/env python3
"""
FINANCIAL RATIOS: PROFITABILITY, LIQUIDITY, LEVERAGE AND EFFICIENCY

A self-contained financial ratio analysis system.
Python 3.10+
Uses only the Python standard library.
"""

from __future__ import annotations

import csv
import json
import logging
import argparse
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("financial_ratios")


class RatioCategory(Enum):
    PROFITABILITY = "Profitability"
    LIQUIDITY = "Liquidity"
    LEVERAGE = "Leverage"
    EFFICIENCY = "Efficiency"


class FinancialDataError(ValueError):
    """Raised when financial statement data is invalid."""


@dataclass(frozen=True)
class FinancialStatements:
    company: str
    period: str

    revenue: float
    cost_of_goods_sold: float
    operating_expenses: float
    operating_income: float
    net_income: float

    total_assets: float
    current_assets: float
    inventory: float
    cash: float
    accounts_receivable: float

    total_liabilities: float
    current_liabilities: float
    total_debt: float
    shareholders_equity: float

    interest_expense: float
    inventory_beginning: float
    inventory_ending: float
    receivables_beginning: float
    receivables_ending: float

    def validate(self) -> None:
        if not self.company.strip():
            raise FinancialDataError("Company name cannot be empty.")

        if not self.period.strip():
            raise FinancialDataError("Financial period cannot be empty.")

        for field, value in asdict(self).items():
            if isinstance(value, (int, float)):
                if value < 0:
                    raise FinancialDataError(
                        f"{field} cannot be negative."
                    )

        if self.current_assets > self.total_assets:
            raise FinancialDataError(
                "Current assets cannot exceed total assets."
            )

        if self.cash > self.current_assets:
            raise FinancialDataError(
                "Cash cannot exceed current assets."
            )

        if self.inventory > self.current_assets:
            raise FinancialDataError(
                "Inventory cannot exceed current assets."
            )

        if self.current_liabilities > self.total_liabilities:
            raise FinancialDataError(
                "Current liabilities cannot exceed total liabilities."
            )

        if self.total_debt > self.total_liabilities:
            raise FinancialDataError(
                "Total debt cannot exceed total liabilities."
            )

        if self.shareholders_equity == 0:
            logger.warning(
                "Shareholders' equity is zero; ROE and debt/equity "
                "will be unavailable."
            )


@dataclass(frozen=True)
class RatioResult:
    name: str
    category: RatioCategory
    value: Optional[float]
    unit: str
    interpretation: str
    warning: Optional[str] = None


class FinancialRatioAnalyzer:

    def __init__(self, statements: FinancialStatements):
        statements.validate()
        self.data = statements
        self.results: list[RatioResult] = []

    @staticmethod
    def safe_divide(
        numerator: float,
        denominator: float
    ) -> Optional[float]:
        if denominator == 0:
            return None
        return numerator / denominator

    def calculate(
        self,
        name: str,
        category: RatioCategory,
        numerator: float,
        denominator: float,
        unit: str,
        interpretation: str
    ) -> RatioResult:

        value = self.safe_divide(numerator, denominator)

        result = RatioResult(
            name=name,
            category=category,
            value=value,
            unit=unit,
            interpretation=interpretation,
            warning=(
                "Undefined because the denominator is zero."
                if value is None else None
            )
        )

        self.results.append(result)
        return result

    def profitability_ratios(self) -> list[RatioResult]:
        d = self.data
        start = len(self.results)

        gross_profit = d.revenue - d.cost_of_goods_sold

        self.calculate(
            "Gross Profit Margin",
            RatioCategory.PROFITABILITY,
            gross_profit,
            d.revenue,
            "%",
            "Measures profit remaining after direct production costs."
        )

        self.calculate(
            "Operating Profit Margin",
            RatioCategory.PROFITABILITY,
            d.operating_income,
            d.revenue,
            "%",
            "Measures operating profitability before interest and tax."
        )

        self.calculate(
            "Net Profit Margin",
            RatioCategory.PROFITABILITY,
            d.net_income,
            d.revenue,
            "%",
            "Measures net profit generated by each unit of revenue."
        )

        self.calculate(
            "Return on Assets",
            RatioCategory.PROFITABILITY,
            d.net_income,
            d.total_assets,
            "%",
            "Measures profitability relative to total assets."
        )

        self.calculate(
            "Return on Equity",
            RatioCategory.PROFITABILITY,
            d.net_income,
            d.shareholders_equity,
            "%",
            "Measures returns generated on shareholders' equity."
        )

        return self.results[start:]

    def liquidity_ratios(self) -> list[RatioResult]:
        d = self.data
        start = len(self.results)

        self.calculate(
            "Current Ratio",
            RatioCategory.LIQUIDITY,
            d.current_assets,
            d.current_liabilities,
            "x",
            "Measures short-term asset coverage of current liabilities."
        )

        quick_assets = (
            d.current_assets - d.inventory
        )

        self.calculate(
            "Quick Ratio",
            RatioCategory.LIQUIDITY,
            quick_assets,
            d.current_liabilities,
            "x",
            "Measures short-term coverage excluding inventory."
        )

        self.calculate(
            "Cash Ratio",
            RatioCategory.LIQUIDITY,
            d.cash,
            d.current_liabilities,
            "x",
            "Measures immediate cash coverage of current liabilities."
        )

        return self.results[start:]

    def leverage_ratios(self) -> list[RatioResult]:
        d = self.data
        start = len(self.results)

        self.calculate(
            "Debt-to-Equity Ratio",
            RatioCategory.LEVERAGE,
            d.total_debt,
            d.shareholders_equity,
            "x",
            "Measures debt financing relative to shareholders' equity."
        )

        self.calculate(
            "Debt-to-Assets Ratio",
            RatioCategory.LEVERAGE,
            d.total_debt,
            d.total_assets,
            "%",
            "Measures the proportion of assets financed by debt."
        )

        self.calculate(
            "Debt Ratio",
            RatioCategory.LEVERAGE,
            d.total_liabilities,
            d.total_assets,
            "%",
            "Measures the proportion of assets financed by liabilities."
        )

        self.calculate(
            "Interest Coverage Ratio",
            RatioCategory.LEVERAGE,
            d.operating_income,
            d.interest_expense,
            "x",
            "Measures operating income available to cover interest."
        )

        return self.results[start:]

    def efficiency_ratios(self) -> list[RatioResult]:
        d = self.data
        start = len(self.results)

        average_inventory = (
            d.inventory_beginning + d.inventory_ending
        ) / 2

        average_receivables = (
            d.receivables_beginning + d.receivables_ending
        ) / 2

        self.calculate(
            "Inventory Turnover",
            RatioCategory.EFFICIENCY,
            d.cost_of_goods_sold,
            average_inventory,
            "x",
            "Measures how frequently inventory is sold and replaced."
        )

        self.calculate(
            "Receivables Turnover",
            RatioCategory.EFFICIENCY,
            d.revenue,
            average_receivables,
            "x",
            "Measures the collection efficiency of receivables."
        )

        self.calculate(
            "Total Asset Turnover",
            RatioCategory.EFFICIENCY,
            d.revenue,
            d.total_assets,
            "x",
            "Measures revenue generated per unit of total assets."
        )

        self.calculate(
            "Days Sales Outstanding",
            RatioCategory.EFFICIENCY,
            average_receivables * 365,
            d.revenue,
            "days",
            "Estimates average days required to collect receivables."
        )

        self.calculate(
            "Days Inventory Outstanding",
            RatioCategory.EFFICIENCY,
            average_inventory * 365,
            d.cost_of_goods_sold,
            "days",
            "Estimates average days inventory remains unsold."
        )

        return self.results[start:]

    def analyze(self) -> list[RatioResult]:
        self.results.clear()

        self.profitability_ratios()
        self.liquidity_ratios()
        self.leverage_ratios()
        self.efficiency_ratios()

        return self.results

    def category_summary(self) -> dict:
        summary = {}

        for category in RatioCategory:
            category_results = [
                r for r in self.results
                if r.category == category
            ]

            summary[category.value] = {
                "ratio_count": len(category_results),
                "available": sum(
                    r.value is not None
                    for r in category_results
                ),
                "undefined": sum(
                    r.value is None
                    for r in category_results
                )
            }

        return summary

    def export_json(self, filename: str) -> None:
        output = {
            "company": self.data.company,
            "period": self.data.period,
            "ratios": [
                {
                    "name": r.name,
                    "category": r.category.value,
                    "value": r.value,
                    "unit": r.unit,
                    "interpretation": r.interpretation,
                    "warning": r.warning
                }
                for r in self.results
            ],
            "summary": self.category_summary()
        }

        Path(filename).write_text(
            json.dumps(output, indent=4),
            encoding="utf-8"
        )

    def export_csv(self, filename: str) -> None:
        with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.writer(file)

            writer.writerow([
                "Ratio",
                "Category",
                "Value",
                "Unit",
                "Interpretation",
                "Warning"
            ])

            for r in self.results:
                writer.writerow([
                    r.name,
                    r.category.value,
                    r.value,
                    r.unit,
                    r.interpretation,
                    r.warning
                ])

    def display(self) -> None:
        print("\nFINANCIAL RATIO ANALYSIS")
        print("=" * 100)
        print(f"Company: {self.data.company}")
        print(f"Period:  {self.data.period}")
        print("=" * 100)

        for category in RatioCategory:
            print(f"\n{category.value.upper()}")

            for result in self.results:
                if result.category != category:
                    continue

                value = (
                    "N/A"
                    if result.value is None
                    else f"{result.value:.4f} {result.unit}"
                )

                print(f"{result.name:30} {value:18}")
                print(f"  {result.interpretation}")

                if result.warning:
                    print(f"  Warning: {result.warning}")

        print("\nCATEGORY SUMMARY")
        print(json.dumps(
            self.category_summary(),
            indent=4
        ))


def sample_financial_statements() -> FinancialStatements:
    return FinancialStatements(
        company="Apex Manufacturing Ltd.",
        period="FY2025-26",

        revenue=12_000_000,
        cost_of_goods_sold=7_200_000,
        operating_expenses=2_400_000,
        operating_income=2_400_000,
        net_income=1_500_000,

        total_assets=10_000_000,
        current_assets=4_000_000,
        inventory=1_200_000,
        cash=800_000,
        accounts_receivable=1_000_000,

        total_liabilities=5_000_000,
        current_liabilities=2_000_000,
        total_debt=3_000_000,
        shareholders_equity=5_000_000,

        interest_expense=400_000,
        inventory_beginning=1_000_000,
        inventory_ending=1_200_000,
        receivables_beginning=800_000,
        receivables_ending=1_000_000
    )


def run_tests() -> None:
    sample = sample_financial_statements()
    analyzer = FinancialRatioAnalyzer(sample)
    results = analyzer.analyze()

    assert len(results) == 17

    lookup = {r.name: r.value for r in results}

    assert abs(lookup["Gross Profit Margin"] - 0.4) < 1e-9
    assert abs(lookup["Current Ratio"] - 2.0) < 1e-9
    assert abs(lookup["Quick Ratio"] - 1.4) < 1e-9
    assert abs(lookup["Debt-to-Equity Ratio"] - 0.6) < 1e-9
    assert abs(lookup["Interest Coverage Ratio"] - 6.0) < 1e-9

    # Zero denominator must not crash the analysis.
    zero_revenue = FinancialStatements(
        **{
            **asdict(sample),
            "revenue": 0,
            "operating_income": 0,
            "net_income": 0,
            "cost_of_goods_sold": 0
        }
    )

    zero_analyzer = FinancialRatioAnalyzer(zero_revenue)
    zero_results = zero_analyzer.analyze()

    assert zero_results[0].value is None

    try:
        FinancialStatements(
            **{
                **asdict(sample),
                "cash": -100
            }
        ).validate()
    except FinancialDataError:
        pass
    else:
        raise AssertionError("Negative financial values were accepted.")

    print("\nAll tests passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Financial ratio analysis engine."
    )

    parser.add_argument(
        "--json",
        default="financial_ratios.json",
        help="JSON output filename."
    )

    parser.add_argument(
        "--csv",
        default="financial_ratios.csv",
        help="CSV output filename."
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run validation tests."
    )

    args = parser.parse_args()

    try:
        if args.test:
            run_tests()

        statements = sample_financial_statements()
        analyzer = FinancialRatioAnalyzer(statements)

        analyzer.analyze()
        analyzer.display()

        analyzer.export_json(args.json)
        analyzer.export_csv(args.csv)

        logger.info("JSON report saved to %s", args.json)
        logger.info("CSV report saved to %s", args.csv)

    except (FinancialDataError, OSError, ValueError) as exc:
        logger.error("Analysis failed: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
