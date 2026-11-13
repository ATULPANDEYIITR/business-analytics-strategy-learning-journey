#!/usr/bin/env python3
"""
BREAK-EVEN ANALYSIS ENGINE

Implements:
- Fixed and variable cost classification
- Contribution margin and contribution margin ratio
- Break-even units and revenue
- Target-profit analysis
- Multi-product weighted-average contribution margin
- Margin of safety
- Operating leverage
- Sensitivity analysis
- Cost-volume-profit scenarios
- Input validation and automated tests

Python 3.10+
Standard library only.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import json
import math


class CostType(Enum):
    FIXED = "fixed"
    VARIABLE = "variable"


class AnalysisError(Exception):
    """Base exception for financial analysis errors."""


class ValidationError(AnalysisError):
    """Raised when financial inputs are invalid."""


class CalculationError(AnalysisError):
    """Raised when a calculation cannot be performed."""


@dataclass(frozen=True)
class CostItem:
    name: str
    amount: float
    cost_type: CostType

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("Cost name cannot be empty.")
        if not math.isfinite(self.amount) or self.amount < 0:
            raise ValidationError("Cost must be finite and non-negative.")


@dataclass(frozen=True)
class Product:
    name: str
    selling_price: float
    variable_cost: float
    sales_mix: float

    def __post_init__(self):
        if not self.name.strip():
            raise ValidationError("Product name cannot be empty.")

        values = (
            self.selling_price,
            self.variable_cost,
            self.sales_mix
        )

        if not all(math.isfinite(value) for value in values):
            raise ValidationError("Product values must be finite.")

        if self.selling_price <= 0:
            raise ValidationError("Selling price must be positive.")

        if self.variable_cost < 0:
            raise ValidationError("Variable cost cannot be negative.")

        if self.variable_cost >= self.selling_price:
            raise ValidationError(
                "Variable cost must be lower than selling price."
            )

        if self.sales_mix <= 0:
            raise ValidationError("Sales mix must be positive.")


@dataclass
class BreakEvenResult:
    fixed_costs: float
    variable_cost_per_unit: float
    selling_price_per_unit: float
    contribution_per_unit: float
    contribution_margin_ratio: float
    break_even_units: float
    practical_break_even_units: int
    break_even_revenue: float
    target_profit_units: Optional[int] = None
    margin_of_safety_units: Optional[float] = None
    margin_of_safety_ratio: Optional[float] = None
    operating_profit: Optional[float] = None


@dataclass
class BreakEvenModel:
    selling_price: float
    variable_cost: float
    fixed_costs: float
    currency: str = "INR"

    def __post_init__(self):
        values = (
            self.selling_price,
            self.variable_cost,
            self.fixed_costs
        )

        if not all(math.isfinite(value) for value in values):
            raise ValidationError("All financial inputs must be finite.")

        if self.selling_price <= 0:
            raise ValidationError("Selling price must be positive.")

        if self.variable_cost < 0:
            raise ValidationError("Variable cost cannot be negative.")

        if self.fixed_costs < 0:
            raise ValidationError("Fixed costs cannot be negative.")

        if self.variable_cost >= self.selling_price:
            raise CalculationError(
                "Contribution margin must be positive."
            )

    @property
    def contribution_per_unit(self) -> float:
        return self.selling_price - self.variable_cost

    @property
    def contribution_margin_ratio(self) -> float:
        return self.contribution_per_unit / self.selling_price

    def break_even_units(self) -> float:
        return self.fixed_costs / self.contribution_per_unit

    def break_even_revenue(self) -> float:
        return self.fixed_costs / self.contribution_margin_ratio

    def calculate(
        self,
        expected_units: Optional[int] = None,
        target_profit: float = 0
    ) -> BreakEvenResult:

        if not math.isfinite(target_profit):
            raise ValidationError("Target profit must be finite.")

        if target_profit < 0:
            raise ValidationError("Target profit cannot be negative.")

        bep = self.break_even_units()

        target_units = math.ceil(
            (self.fixed_costs + target_profit)
            / self.contribution_per_unit
        )

        result = BreakEvenResult(
            fixed_costs=self.fixed_costs,
            variable_cost_per_unit=self.variable_cost,
            selling_price_per_unit=self.selling_price,
            contribution_per_unit=self.contribution_per_unit,
            contribution_margin_ratio=self.contribution_margin_ratio,
            break_even_units=bep,
            practical_break_even_units=math.ceil(bep),
            break_even_revenue=self.break_even_revenue(),
            target_profit_units=target_units
        )

        if expected_units is not None:
            if isinstance(expected_units, bool) or not isinstance(
                expected_units, int
            ):
                raise ValidationError(
                    "Expected units must be an integer."
                )

            if expected_units < 0:
                raise ValidationError(
                    "Expected units cannot be negative."
                )

            revenue = expected_units * self.selling_price
            total_variable = expected_units * self.variable_cost
            profit = revenue - total_variable - self.fixed_costs

            result.operating_profit = profit
            result.margin_of_safety_units = expected_units - bep
            result.margin_of_safety_ratio = (
                (expected_units - bep) / expected_units
                if expected_units > 0 else None
            )

        return result

    def operating_leverage(self, units: int) -> Optional[float]:
        result = self.calculate(expected_units=units)

        if result.operating_profit is None:
            return None

        contribution = units * self.contribution_per_unit

        if result.operating_profit <= 0:
            return None

        return contribution / result.operating_profit


@dataclass
class MultiProductAnalysis:
    fixed_costs: float
    products: List[Product]
    normalized_mix: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not math.isfinite(self.fixed_costs) or self.fixed_costs < 0:
            raise ValidationError("Fixed costs must be non-negative.")

        if not self.products:
            raise ValidationError("At least one product is required.")

        names = [product.name for product in self.products]

        if len(names) != len(set(names)):
            raise ValidationError("Product names must be unique.")

        total_mix = sum(product.sales_mix for product in self.products)

        self.normalized_mix = {
            product.name: product.sales_mix / total_mix
            for product in self.products
        }

    def weighted_contribution_margin(self) -> float:
        return sum(
            self.normalized_mix[p.name]
            * (p.selling_price - p.variable_cost)
            for p in self.products
        )

    def weighted_break_even_units(self) -> float:
        margin = self.weighted_contribution_margin()

        if margin <= 0:
            raise CalculationError("Weighted contribution must be positive.")

        return self.fixed_costs / margin

    def sales_mix_breakdown(self) -> List[dict]:
        weighted_margin = self.weighted_contribution_margin()

        return [
            {
                "product": p.name,
                "sales_mix": self.normalized_mix[p.name],
                "contribution_per_unit": (
                    p.selling_price - p.variable_cost
                ),
                "weighted_contribution": (
                    self.normalized_mix[p.name]
                    * (p.selling_price - p.variable_cost)
                ),
                "break_even_mix_units": (
                    self.fixed_costs
                    * self.normalized_mix[p.name]
                    / weighted_margin
                )
            }
            for p in self.products
        ]


def classify_costs(items: List[CostItem]) -> Dict[str, float]:
    totals = {
        CostType.FIXED.value: 0.0,
        CostType.VARIABLE.value: 0.0
    }

    for item in items:
        totals[item.cost_type.value] += item.amount

    return totals


def sensitivity_analysis(
    model: BreakEvenModel,
    price_changes: List[float],
    cost_changes: List[float]
) -> List[dict]:

    scenarios = []

    for price_change in price_changes:
        for cost_change in cost_changes:
            new_price = model.selling_price * (1 + price_change)
            new_cost = model.variable_cost * (1 + cost_change)

            try:
                scenario = BreakEvenModel(
                    selling_price=new_price,
                    variable_cost=new_cost,
                    fixed_costs=model.fixed_costs,
                    currency=model.currency
                )

                scenarios.append({
                    "price_change": price_change,
                    "variable_cost_change": cost_change,
                    "break_even_units": scenario.break_even_units(),
                    "break_even_revenue": scenario.break_even_revenue()
                })

            except AnalysisError as error:
                scenarios.append({
                    "price_change": price_change,
                    "variable_cost_change": cost_change,
                    "error": str(error)
                })

    return scenarios


def run_example():
    print("=" * 65)
    print("BREAK-EVEN ANALYSIS AND COST-VOLUME-PROFIT ENGINE")
    print("=" * 65)

    costs = [
        CostItem("Factory Rent", 80000, CostType.FIXED),
        CostItem("Salaries", 120000, CostType.FIXED),
        CostItem("Insurance", 20000, CostType.FIXED),
        CostItem("Raw Materials", 250, CostType.VARIABLE),
        CostItem("Packaging", 50, CostType.VARIABLE),
        CostItem("Direct Labour", 100, CostType.VARIABLE)
    ]

    totals = classify_costs(costs)

    print("\n1. COST CLASSIFICATION")
    for category, amount in totals.items():
        print(f"{category.title():15}: {amount:,.2f}")

    model = BreakEvenModel(
        selling_price=1000,
        variable_cost=400,
        fixed_costs=totals["fixed"],
        currency="INR"
    )

    result = model.calculate(
        expected_units=600,
        target_profit=200000
    )

    print("\n2. UNIT ECONOMICS")
    print(f"Selling price:          {model.selling_price:,.2f}")
    print(f"Variable cost:          {model.variable_cost:,.2f}")
    print(f"Contribution/unit:      {result.contribution_per_unit:,.2f}")
    print(f"Contribution margin:    {result.contribution_margin_ratio:.2%}")

    print("\n3. BREAK-EVEN ANALYSIS")
    print(f"Exact break-even units:  {result.break_even_units:.2f}")
    print(f"Whole break-even units:  {result.practical_break_even_units}")
    print(f"Break-even revenue:      {result.break_even_revenue:,.2f}")

    print("\n4. TARGET PROFIT")
    print(f"Target profit:           200,000.00")
    print(f"Required units:          {result.target_profit_units:,}")

    print("\n5. SALES AND PROFIT ANALYSIS")
    print(f"Expected units:          600")
    print(f"Operating profit:        {result.operating_profit:,.2f}")
    print(f"Margin of safety units:  {result.margin_of_safety_units:.2f}")
    print(f"Margin of safety ratio:  {result.margin_of_safety_ratio:.2%}")

    leverage = model.operating_leverage(600)
    print(f"Operating leverage:      {leverage:.2f}x")

    print("\n6. MULTI-PRODUCT ANALYSIS")

    products = [
        Product("Standard", 1000, 400, 0.60),
        Product("Premium", 1500, 650, 0.40)
    ]

    multi = MultiProductAnalysis(
        fixed_costs=220000,
        products=products
    )

    print(
        f"Weighted contribution: "
        f"{multi.weighted_contribution_margin():,.2f}"
    )

    print(
        f"Weighted break-even units: "
        f"{multi.weighted_break_even_units():.2f}"
    )

    for item in multi.sales_mix_breakdown():
        print(
            f"{item['product']:12} | "
            f"Mix: {item['sales_mix']:.0%} | "
            f"Contribution: {item['contribution_per_unit']:,.2f} | "
            f"BE allocation: {item['break_even_mix_units']:.2f}"
        )

    print("\n7. SENSITIVITY ANALYSIS")

    scenarios = sensitivity_analysis(
        model,
        price_changes=[-0.10, 0.0, 0.10],
        cost_changes=[-0.10, 0.0, 0.10]
    )

    for scenario in scenarios:
        if "error" in scenario:
            print(f"Invalid scenario: {scenario['error']}")
        else:
            print(
                f"Price {scenario['price_change']:+.0%}, "
                f"Variable cost {scenario['variable_cost_change']:+.0%}: "
                f"{scenario['break_even_units']:.2f} units"
            )

    print("\n8. EDGE-CASE VALIDATION")

    try:
        BreakEvenModel(100, 100, 500)
    except AnalysisError as error:
        print(f"Correctly rejected zero contribution: {error}")

    try:
        model.calculate(expected_units=-10)
    except AnalysisError as error:
        print(f"Correctly rejected negative sales: {error}")

    print("\n9. AUTOMATED ASSERTIONS")

    assert model.contribution_per_unit == 600
    assert math.isclose(model.break_even_units(), 220000 / 600)
    assert model.calculate().practical_break_even_units == 367
    assert model.calculate(expected_units=0).operating_profit == -220000

    assert math.ceil(
        (220000 + 200000) / 600
    ) == 700

    print("All validation assertions passed.")

    print("\n10. JSON REPORT")

    report = {
        "currency": model.currency,
        "fixed_costs": result.fixed_costs,
        "selling_price": result.selling_price_per_unit,
        "variable_cost": result.variable_cost_per_unit,
        "contribution": result.contribution_per_unit,
        "contribution_margin_ratio": result.contribution_margin_ratio,
        "break_even_units": result.break_even_units,
        "break_even_revenue": result.break_even_revenue,
        "target_profit_units": result.target_profit_units,
        "expected_sales_units": 600,
        "operating_profit": result.operating_profit
    }

    print(json.dumps(report, indent=4))


if __name__ == "__main__":
    run_example()
