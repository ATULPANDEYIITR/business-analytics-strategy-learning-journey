#!/usr/bin/env python3
"""
BUSINESS VALUATION: DCF, MULTIPLES AND VALUATION FUNDAMENTALS

Implements:
- Discounted Cash Flow (DCF) valuation
- Free Cash Flow to Firm (FCFF)
- Weighted Average Cost of Capital (WACC)
- Terminal value using the Gordon Growth Model
- Enterprise value to equity value reconciliation
- Comparable company valuation
- EV/EBITDA, EV/Revenue and P/E multiples
- Sensitivity analysis
- Scenario analysis
- Valuation validation and reporting

Python 3.10+
Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import median
from typing import Iterable


class ValuationError(Exception):
    """Raised when valuation inputs or calculations are invalid."""


class Scenario(Enum):
    BEAR = "Bear"
    BASE = "Base"
    BULL = "Bull"


@dataclass(frozen=True)
class FinancialStatements:
    revenue: float
    ebit: float
    depreciation: float
    capital_expenditure: float
    working_capital_increase: float
    tax_rate: float
    cash: float
    debt: float
    shares_outstanding: float

    def validate(self) -> None:
        non_negative = {
            "revenue": self.revenue,
            "depreciation": self.depreciation,
            "capital expenditure": self.capital_expenditure,
            "cash": self.cash,
            "debt": self.debt,
            "shares outstanding": self.shares_outstanding,
        }

        for name, value in non_negative.items():
            if value < 0:
                raise ValuationError(f"{name} cannot be negative.")

        if self.revenue <= 0 or self.shares_outstanding <= 0:
            raise ValuationError("Revenue and shares must be positive.")

        if not 0 <= self.tax_rate < 1:
            raise ValuationError("Tax rate must be between 0 and 1.")

        if self.ebit < 0 and self.tax_rate > 0:
            raise ValuationError(
                "This simplified model does not recognize tax benefits "
                "from operating losses."
            )


@dataclass(frozen=True)
class CapitalStructure:
    cost_of_equity: float
    cost_of_debt: float
    equity_weight: float
    debt_weight: float

    def validate(self) -> None:
        if not 0 <= self.cost_of_equity <= 1:
            raise ValuationError("Invalid cost of equity.")

        if not 0 <= self.cost_of_debt <= 1:
            raise ValuationError("Invalid cost of debt.")

        if abs(self.equity_weight + self.debt_weight - 1.0) > 1e-9:
            raise ValuationError("Capital weights must sum to 1.")

        if self.equity_weight < 0 or self.debt_weight < 0:
            raise ValuationError("Capital weights cannot be negative.")


@dataclass(frozen=True)
class ForecastAssumptions:
    growth_rates: tuple[float, ...]
    ebit_margins: tuple[float, ...]
    tax_rate: float
    depreciation_rate: float
    capex_rate: float
    working_capital_rate: float
    terminal_growth: float

    def validate(self) -> None:
        periods = len(self.growth_rates)

        if periods == 0:
            raise ValuationError("At least one forecast period is required.")

        if len(self.ebit_margins) != periods:
            raise ValuationError("Forecast arrays must have equal lengths.")

        if any(rate <= -1 for rate in self.growth_rates):
            raise ValuationError("Growth rates must exceed -100%.")

        for rate in (
            self.tax_rate,
            self.depreciation_rate,
            self.capex_rate,
            self.working_capital_rate,
        ):
            if not 0 <= rate <= 1:
                raise ValuationError("Invalid forecast assumption.")

        if not 0 <= self.terminal_growth < 1:
            raise ValuationError("Invalid terminal growth rate.")


@dataclass
class ForecastYear:
    year: int
    revenue: float
    ebit: float
    nopat: float
    depreciation: float
    capex: float
    change_in_working_capital: float
    fcff: float
    discount_factor: float
    present_value: float


@dataclass(frozen=True)
class ComparableCompany:
    name: str
    enterprise_value: float
    revenue: float
    ebitda: float
    net_income: float

    def validate(self) -> None:
        if not self.name.strip():
            raise ValuationError("Company name cannot be empty.")

        if self.enterprise_value <= 0 or self.revenue <= 0:
            raise ValuationError("Enterprise value and revenue must be positive.")

        if self.ebitda <= 0:
            raise ValuationError(
                f"{self.name}: EBITDA must be positive for EV/EBITDA."
            )

        if self.net_income <= 0:
            raise ValuationError(
                f"{self.name}: net income must be positive for P/E."
            )

    @property
    def ev_revenue(self) -> float:
        return self.enterprise_value / self.revenue

    @property
    def ev_ebitda(self) -> float:
        return self.enterprise_value / self.ebitda


@dataclass
class DCFResult:
    enterprise_value: float
    terminal_value: float
    terminal_value_present: float
    explicit_period_value: float
    equity_value: float
    intrinsic_value_per_share: float
    forecast: list[ForecastYear]


class BusinessValuator:
    def __init__(
        self,
        statements: FinancialStatements,
        capital: CapitalStructure,
        assumptions: ForecastAssumptions,
    ):
        statements.validate()
        capital.validate()
        assumptions.validate()

        self.statements = statements
        self.capital = capital
        self.assumptions = assumptions

        self.wacc = (
            capital.equity_weight * capital.cost_of_equity
            + capital.debt_weight
            * capital.cost_of_debt
            * (1 - statements.tax_rate)
        )

        if self.wacc <= 0:
            raise ValuationError("WACC must be positive.")

        if assumptions.terminal_growth >= self.wacc:
            raise ValuationError(
                "Terminal growth must be lower than WACC."
            )

    def calculate_fcff(
        self,
        ebit: float,
        depreciation: float,
        capex: float,
        change_in_working_capital: float,
    ) -> tuple[float, float]:
        # FCFF is calculated before interest payments.
        nopat = ebit * (1 - self.assumptions.tax_rate)

        fcff = (
            nopat
            + depreciation
            - capex
            - change_in_working_capital
        )

        return nopat, fcff

    def run_dcf(self) -> DCFResult:
        forecast: list[ForecastYear] = []
        revenue = self.statements.revenue
        previous_working_capital = (
            revenue * self.assumptions.working_capital_rate
        )

        for index, (growth, margin) in enumerate(
            zip(
                self.assumptions.growth_rates,
                self.assumptions.ebit_margins,
            ),
            start=1,
        ):
            revenue *= 1 + growth

            ebit = revenue * margin
            depreciation = revenue * self.assumptions.depreciation_rate
            capex = revenue * self.assumptions.capex_rate

            current_working_capital = (
                revenue * self.assumptions.working_capital_rate
            )

            change_in_working_capital = (
                current_working_capital - previous_working_capital
            )

            nopat, fcff = self.calculate_fcff(
                ebit,
                depreciation,
                capex,
                change_in_working_capital,
            )

            discount_factor = 1 / ((1 + self.wacc) ** index)
            present_value = fcff * discount_factor

            forecast.append(
                ForecastYear(
                    year=index,
                    revenue=revenue,
                    ebit=ebit,
                    nopat=nopat,
                    depreciation=depreciation,
                    capex=capex,
                    change_in_working_capital=change_in_working_capital,
                    fcff=fcff,
                    discount_factor=discount_factor,
                    present_value=present_value,
                )
            )

            previous_working_capital = current_working_capital

        final_fcff = forecast[-1].fcff

        terminal_fcff = final_fcff * (
            1 + self.assumptions.terminal_growth
        )

        terminal_value = terminal_fcff / (
            self.wacc - self.assumptions.terminal_growth
        )

        terminal_present = (
            terminal_value / ((1 + self.wacc) ** len(forecast))
        )

        explicit_value = sum(item.present_value for item in forecast)

        enterprise_value = explicit_value + terminal_present

        equity_value = (
            enterprise_value
            + self.statements.cash
            - self.statements.debt
        )

        intrinsic_value = (
            equity_value / self.statements.shares_outstanding
        )

        return DCFResult(
            enterprise_value=enterprise_value,
            terminal_value=terminal_value,
            terminal_value_present=terminal_present,
            explicit_period_value=explicit_value,
            equity_value=equity_value,
            intrinsic_value_per_share=intrinsic_value,
            forecast=forecast,
        )

    def sensitivity_analysis(
        self,
        wacc_adjustments: Iterable[float],
        growth_adjustments: Iterable[float],
    ) -> dict[tuple[float, float], float]:
        """
        Recalculate enterprise value under alternative WACC and
        terminal-growth assumptions.
        """
        result = {}

        for wacc_adjustment in wacc_adjustments:
            adjusted_wacc = self.wacc + wacc_adjustment

            for growth_adjustment in growth_adjustments:
                adjusted_growth = (
                    self.assumptions.terminal_growth + growth_adjustment
                )

                if adjusted_wacc <= adjusted_growth or adjusted_wacc <= 0:
                    continue

                explicit_value = sum(
                    year.fcff / ((1 + adjusted_wacc) ** year.year)
                    for year in self.run_dcf().forecast
                )

                final_fcff = self.run_dcf().forecast[-1].fcff

                terminal_value = (
                    final_fcff * (1 + adjusted_growth)
                    / (adjusted_wacc - adjusted_growth)
                )

                terminal_pv = terminal_value / (
                    (1 + adjusted_wacc)
                    ** len(self.assumptions.growth_rates)
                )

                result[(adjusted_wacc, adjusted_growth)] = (
                    explicit_value + terminal_pv
                )

        return result


class ComparableValuation:
    def __init__(self, companies: list[ComparableCompany]):
        if not companies:
            raise ValuationError("At least one comparable is required.")

        for company in companies:
            company.validate()

        self.companies = companies

    def calculate_multiples(self) -> dict[str, float]:
        ev_ebitda = median(
            company.ev_ebitda for company in self.companies
        )

        ev_revenue = median(
            company.ev_revenue for company in self.companies
        )

        return {
            "median_ev_ebitda": ev_ebitda,
            "median_ev_revenue": ev_revenue,
        }

    def estimate_target(
        self,
        target_revenue: float,
        target_ebitda: float,
        cash: float,
        debt: float,
        shares: float,
    ) -> dict[str, float]:
        if min(target_revenue, target_ebitda, shares) <= 0:
            raise ValuationError("Target financial metrics must be positive.")

        multiples = self.calculate_multiples()

        ev_ebitda = target_ebitda * multiples["median_ev_ebitda"]
        ev_revenue = target_revenue * multiples["median_ev_revenue"]

        equity_ebitda = ev_ebitda + cash - debt
        equity_revenue = ev_revenue + cash - debt

        return {
            "ev_ebitda": ev_ebitda,
            "ev_revenue": ev_revenue,
            "equity_value_ebitda": equity_ebitda,
            "equity_value_revenue": equity_revenue,
            "price_per_share_ebitda": equity_ebitda / shares,
            "price_per_share_revenue": equity_revenue / shares,
        }


def scenario_assumptions(
    scenario: Scenario,
) -> ForecastAssumptions:
    scenarios = {
        Scenario.BEAR: ForecastAssumptions(
            growth_rates=(0.04, 0.035, 0.03, 0.025, 0.02),
            ebit_margins=(0.15, 0.15, 0.155, 0.16, 0.16),
            tax_rate=0.25,
            depreciation_rate=0.035,
            capex_rate=0.06,
            working_capital_rate=0.12,
            terminal_growth=0.02,
        ),
        Scenario.BASE: ForecastAssumptions(
            growth_rates=(0.10, 0.09, 0.08, 0.07, 0.06),
            ebit_margins=(0.18, 0.19, 0.20, 0.205, 0.21),
            tax_rate=0.25,
            depreciation_rate=0.04,
            capex_rate=0.055,
            working_capital_rate=0.10,
            terminal_growth=0.03,
        ),
        Scenario.BULL: ForecastAssumptions(
            growth_rates=(0.16, 0.14, 0.12, 0.10, 0.08),
            ebit_margins=(0.20, 0.21, 0.22, 0.23, 0.23),
            tax_rate=0.25,
            depreciation_rate=0.045,
            capex_rate=0.05,
            working_capital_rate=0.09,
            terminal_growth=0.035,
        ),
    }

    return scenarios[scenario]


def print_dcf_report(
    scenario: Scenario,
    valuator: BusinessValuator,
    result: DCFResult,
) -> None:
    print(f"\n{'=' * 68}")
    print(f"{scenario.value.upper()} CASE DCF VALUATION")
    print(f"{'=' * 68}")

    print(f"WACC:                         {valuator.wacc:.2%}")
    print(
        f"Terminal growth:              "
        f"{valuator.assumptions.terminal_growth:.2%}"
    )

    print("\nForecast")

    print(
        f"{'Year':<8}{'Revenue':>14}{'EBIT':>14}"
        f"{'FCFF':>14}{'Present Value':>18}"
    )

    for year in result.forecast:
        print(
            f"{year.year:<8}"
            f"{year.revenue:>14,.2f}"
            f"{year.ebit:>14,.2f}"
            f"{year.fcff:>14,.2f}"
            f"{year.present_value:>18,.2f}"
        )

    print("\nValuation")

    print(f"Explicit cash flow value:     {result.explicit_period_value:,.2f}")
    print(f"Terminal value:               {result.terminal_value:,.2f}")
    print(f"Present value of terminal:    {result.terminal_value_present:,.2f}")
    print(f"Enterprise value:             {result.enterprise_value:,.2f}")
    print(f"Equity value:                  {result.equity_value:,.2f}")
    print(f"Intrinsic value per share:    {result.intrinsic_value_per_share:,.2f}")

    terminal_percentage = (
        result.terminal_value_present / result.enterprise_value
        if result.enterprise_value > 0 else 0
    )

    print(f"Terminal value contribution:  {terminal_percentage:.2%}")


def main() -> None:
    # All monetary figures are in INR millions, except per-share values.
    statements = FinancialStatements(
        revenue=1000.0,
        ebit=180.0,
        depreciation=40.0,
        capital_expenditure=55.0,
        working_capital_increase=10.0,
        tax_rate=0.25,
        cash=100.0,
        debt=300.0,
        shares_outstanding=50.0,
    )

    capital = CapitalStructure(
        cost_of_equity=0.14,
        cost_of_debt=0.09,
        equity_weight=0.70,
        debt_weight=0.30,
    )

    print("BUSINESS VALUATION ANALYSIS")
    print("Currency: INR millions unless stated otherwise")

    scenario_results = {}

    for scenario in Scenario:
        assumptions = scenario_assumptions(scenario)

        valuator = BusinessValuator(
            statements,
            capital,
            assumptions,
        )

        result = valuator.run_dcf()
        scenario_results[scenario] = result

        print_dcf_report(scenario, valuator, result)

    print("\n" + "=" * 68)
    print("DCF SCENARIO COMPARISON")
    print("=" * 68)

    for scenario, result in scenario_results.items():
        print(
            f"{scenario.value:<10}"
            f"Enterprise Value: {result.enterprise_value:>14,.2f}"
            f" | Share Value: {result.intrinsic_value_per_share:>10,.2f}"
        )

    comparables = [
        ComparableCompany("Alpha Technologies", 1800, 1200, 240, 140),
        ComparableCompany("Beta Systems", 2100, 1500, 300, 175),
        ComparableCompany("Gamma Digital", 1650, 1100, 220, 125),
        ComparableCompany("Delta Software", 2400, 1600, 320, 190),
    ]

    comparable_valuation = ComparableValuation(comparables)

    multiples = comparable_valuation.calculate_multiples()

    target_valuation = comparable_valuation.estimate_target(
        target_revenue=1000,
        target_ebitda=220,
        cash=100,
        debt=300,
        shares=50,
    )

    print("\n" + "=" * 68)
    print("COMPARABLE COMPANY ANALYSIS")
    print("=" * 68)

    for company in comparables:
        print(
            f"{company.name:<24}"
            f"EV/Revenue: {company.ev_revenue:>7.2f}"
            f" | EV/EBITDA: {company.ev_ebitda:>7.2f}"
        )

    print(f"\nMedian EV/Revenue: {multiples['median_ev_revenue']:.2f}x")
    print(f"Median EV/EBITDA:  {multiples['median_ev_ebitda']:.2f}x")

    print("\nTarget valuation")

    for metric, value in target_valuation.items():
        print(f"{metric:<30}{value:>14,.2f}")

    base_valuator = BusinessValuator(
        statements,
        capital,
        scenario_assumptions(Scenario.BASE),
    )

    sensitivity = base_valuator.sensitivity_analysis(
        wacc_adjustments=(-0.01, 0.0, 0.01),
        growth_adjustments=(-0.01, 0.0, 0.01),
    )

    print("\n" + "=" * 68)
    print("DCF SENSITIVITY ANALYSIS: ENTERPRISE VALUE")
    print("=" * 68)

    for (wacc, growth), value in sorted(sensitivity.items()):
        print(
            f"WACC: {wacc:.2%} | Growth: {growth:.2%}"
            f" | EV: {value:,.2f}"
        )

    # Basic integrity assertions.
    base_result = scenario_results[Scenario.BASE]

    assert base_result.enterprise_value > 0
    assert len(base_result.forecast) == 5
    assert base_result.equity_value == (
        base_result.enterprise_value + statements.cash - statements.debt
    )

    print("\nValuation calculations and integrity checks completed.")


if __name__ == "__main__":
    try:
        main()
    except (ValuationError, ArithmeticError, ValueError) as exc:
        print(f"Valuation failed: {exc}")
        raise SystemExit(1)
