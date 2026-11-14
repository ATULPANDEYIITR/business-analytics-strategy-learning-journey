#!/usr/bin/env python3
"""
Pricing Analytics: Pricing Structures, Elasticity and Optimization

Implements:
- Pricing structures and customer segments
- Price elasticity estimation
- Demand forecasting
- Revenue and profit calculations
- Price optimization under business constraints
- Competitor price analysis
- Scenario simulation
- Sensitivity analysis
- CSV reporting and validation
"""

from __future__ import annotations

import csv
import math
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Iterable


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("pricing_analytics")


class PricingStrategy(Enum):
    COST_PLUS = "cost_plus"
    VALUE_BASED = "value_based"
    COMPETITIVE = "competitive"
    PENETRATION = "penetration"
    PREMIUM = "premium"
    DYNAMIC = "dynamic"


class CustomerSegment(Enum):
    RETAIL = "retail"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    unit_cost: float
    reference_price: float
    minimum_price: float
    maximum_price: float
    inventory: int

    def __post_init__(self):
        if not self.product_id.strip():
            raise ValueError("Product ID cannot be empty.")
        if not self.name.strip():
            raise ValueError("Product name cannot be empty.")
        if self.unit_cost < 0:
            raise ValueError("Unit cost cannot be negative.")
        if self.reference_price <= 0:
            raise ValueError("Reference price must be positive.")
        if self.minimum_price <= self.unit_cost:
            raise ValueError("Minimum price must exceed unit cost.")
        if self.maximum_price < self.minimum_price:
            raise ValueError("Invalid price range.")
        if self.inventory < 0:
            raise ValueError("Inventory cannot be negative.")


@dataclass(frozen=True)
class DemandObservation:
    product_id: str
    price: float
    quantity: int
    segment: CustomerSegment

    def __post_init__(self):
        if self.price <= 0 or self.quantity < 0:
            raise ValueError("Invalid demand observation.")


@dataclass(frozen=True)
class Competitor:
    name: str
    price: float

    def __post_init__(self):
        if not self.name.strip() or self.price <= 0:
            raise ValueError("Invalid competitor information.")


@dataclass
class PricingResult:
    product_id: str
    strategy: str
    recommended_price: float
    expected_demand: float
    expected_revenue: float
    expected_profit: float
    margin_percentage: float


class PricingModel:
    """Constant-elasticity demand model."""

    def __init__(
        self,
        base_price: float,
        base_demand: float,
        elasticity: float
    ):
        if base_price <= 0 or base_demand < 0:
            raise ValueError("Invalid demand model parameters.")
        if elasticity >= 0:
            raise ValueError("Own-price elasticity must be negative.")

        self.base_price = base_price
        self.base_demand = base_demand
        self.elasticity = elasticity

    def forecast(self, price: float) -> float:
        if price <= 0:
            raise ValueError("Price must be positive.")

        return self.base_demand * (
            price / self.base_price
        ) ** self.elasticity

    @staticmethod
    def estimate_elasticity(
        observations: Iterable[DemandObservation],
        product_id: str
    ) -> float:
        """
        Estimate elasticity using ordinary least squares:
        ln(quantity) = intercept + elasticity * ln(price).

        Zero-demand observations are excluded because logarithms
        are undefined for zero.
        """
        data = [
            (math.log(item.price), math.log(item.quantity))
            for item in observations
            if item.product_id == product_id
            and item.price > 0
            and item.quantity > 0
        ]

        if len(data) < 3:
            raise ValueError(
                "At least three positive-demand observations are required."
            )

        mean_x = sum(x for x, _ in data) / len(data)
        mean_y = sum(y for _, y in data) / len(data)

        denominator = sum(
            (x - mean_x) ** 2 for x, _ in data
        )

        if denominator == 0:
            raise ValueError("Price variation is insufficient.")

        numerator = sum(
            (x - mean_x) * (y - mean_y)
            for x, y in data
        )

        return numerator / denominator

    @staticmethod
    def elasticity_interpretation(value: float) -> str:
        if abs(value) > 1:
            return "Elastic demand"
        if abs(value) < 1:
            return "Inelastic demand"
        return "Unit elastic demand"


class PricingOptimizer:
    def __init__(self, product: Product, model: PricingModel):
        self.product = product
        self.model = model

    def evaluate(self, price: float) -> PricingResult:
        product = self.product

        if not product.minimum_price <= price <= product.maximum_price:
            raise ValueError("Price is outside permitted boundaries.")

        demand = self.model.forecast(price)

        # Demand cannot exceed available inventory.
        demand = min(demand, float(product.inventory))

        revenue = price * demand
        profit = (price - product.unit_cost) * demand
        margin = (
            (price - product.unit_cost) / price * 100
            if price > 0 else 0
        )

        return PricingResult(
            product_id=product.product_id,
            strategy=PricingStrategy.DYNAMIC.value,
            recommended_price=round(price, 2),
            expected_demand=round(demand, 2),
            expected_revenue=round(revenue, 2),
            expected_profit=round(profit, 2),
            margin_percentage=round(margin, 2)
        )

    def optimize(
        self,
        objective: str = "profit",
        step: float = 0.25,
        minimum_margin: float = 0.0,
        maximum_demand: Optional[float] = None
    ) -> PricingResult:
        """
        Exhaustive bounded price search.

        Complexity: O(R), where R is the number of candidate prices.
        """
        if objective not in {"profit", "revenue"}:
            raise ValueError("Objective must be profit or revenue.")

        if step <= 0:
            raise ValueError("Step must be positive.")

        if not 0 <= minimum_margin < 100:
            raise ValueError("Invalid minimum margin.")

        if maximum_demand is not None and maximum_demand < 0:
            raise ValueError("Maximum demand cannot be negative.")

        candidates = []
        price = self.product.minimum_price

        while price <= self.product.maximum_price + 1e-9:
            result = self.evaluate(round(price, 6))

            if result.margin_percentage + 1e-9 >= minimum_margin:
                if (
                    maximum_demand is None
                    or result.expected_demand <= maximum_demand
                ):
                    candidates.append(result)

            price += step

        if not candidates:
            raise ValueError("No price satisfies the optimization constraints.")

        key = (
            (lambda result: result.expected_profit)
            if objective == "profit"
            else (lambda result: result.expected_revenue)
        )

        return max(
            candidates,
            key=lambda result: (
                key(result),
                result.recommended_price
            )
        )

    def sensitivity_analysis(
        self,
        elasticity_values: list[float],
        objective: str = "profit"
    ) -> list[PricingResult]:
        results = []

        for elasticity in elasticity_values:
            model = PricingModel(
                self.model.base_price,
                self.model.base_demand,
                elasticity
            )

            optimizer = PricingOptimizer(self.product, model)
            result = optimizer.optimize(objective=objective)

            results.append(result)

        return results


class PricingAnalytics:
    def __init__(self):
        self.products: dict[str, Product] = {}
        self.observations: list[DemandObservation] = {}

    def add_product(self, product: Product) -> None:
        if product.product_id in self.products:
            raise ValueError("Duplicate product ID.")

        self.products[product.product_id] = product

    def add_observation(self, observation: DemandObservation) -> None:
        if observation.product_id not in self.products:
            raise ValueError("Unknown product.")

        self.observations.append(observation)

    def analyze(
        self,
        product_id: str,
        base_demand: float
    ) -> tuple[PricingModel, str]:
        product = self.products[product_id]

        elasticity = PricingModel.estimate_elasticity(
            self.observations,
            product_id
        )

        model = PricingModel(
            product.reference_price,
            base_demand,
            elasticity
        )

        return model, PricingModel.elasticity_interpretation(elasticity)

    @staticmethod
    def cost_plus_price(
        unit_cost: float,
        markup_percentage: float
    ) -> float:
        if unit_cost < 0 or markup_percentage < 0:
            raise ValueError("Cost and markup cannot be negative.")

        return unit_cost * (1 + markup_percentage / 100)

    @staticmethod
    def competitive_price(
        competitors: list[Competitor],
        positioning_factor: float = 1.0
    ) -> float:
        if not competitors:
            raise ValueError("Competitor list cannot be empty.")

        if positioning_factor <= 0:
            raise ValueError("Positioning factor must be positive.")

        average = sum(c.price for c in competitors) / len(competitors)
        return round(average * positioning_factor, 2)

    @staticmethod
    def export_results(
        results: list[PricingResult],
        filename: str = "pricing_results.csv"
    ) -> None:
        if not results:
            raise ValueError("No results to export.")

        fields = list(PricingResult.__dataclass_fields__.keys())

        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()

            for result in results:
                writer.writerow(result.__dict__)


def main():
    analytics = PricingAnalytics()

    product = Product(
        product_id="P1001",
        name="Enterprise Analytics Subscription",
        unit_cost=250.0,
        reference_price=500.0,
        minimum_price=300.0,
        maximum_price=900.0,
        inventory=1000
    )

    analytics.add_product(product)

    # Historical observations used to estimate price sensitivity.
    historical = [
        (450, 120),
        (475, 113),
        (500, 105),
        (525, 99),
        (550, 94),
        (575, 89),
        (600, 85),
        (650, 77)
    ]

    for price, quantity in historical:
        analytics.add_observation(
            DemandObservation(
                product_id="P1001",
                price=price,
                quantity=quantity,
                segment=CustomerSegment.BUSINESS
            )
        )

    model, interpretation = analytics.analyze(
        "P1001",
        base_demand=105
    )

    print("\nPRICING ANALYTICS")
    print("=" * 55)
    print(f"Product: {product.name}")
    print(f"Estimated elasticity: {model.elasticity:.4f}")
    print(f"Demand classification: {interpretation}")

    cost_price = analytics.cost_plus_price(
        product.unit_cost,
        markup_percentage=60
    )

    competitor_price = analytics.competitive_price([
        Competitor("Competitor A", 540),
        Competitor("Competitor B", 560),
        Competitor("Competitor C", 520)
    ])

    print(f"Cost-plus price: {cost_price:.2f}")
    print(f"Competitive reference: {competitor_price:.2f}")

    optimizer = PricingOptimizer(product, model)

    profit_result = optimizer.optimize(
        objective="profit",
        step=5,
        minimum_margin=20
    )

    revenue_result = optimizer.optimize(
        objective="revenue",
        step=5
    )

    print("\nPROFIT OPTIMIZATION")
    print(profit_result)

    print("\nREVENUE OPTIMIZATION")
    print(revenue_result)

    sensitivity = optimizer.sensitivity_analysis(
        [-0.8, -1.0, -1.2, -1.5, -2.0]
    )

    print("\nELASTICITY SENSITIVITY")
    for result in sensitivity:
        print(
            f"Price={result.recommended_price:.2f}, "
            f"Revenue={result.expected_revenue:.2f}, "
            f"Profit={result.expected_profit:.2f}"
        )

    # Export both optimization results.
    analytics.export_results([
        profit_result,
        revenue_result,
        *sensitivity
    ])

    # Basic regression and optimization checks.
    assert model.elasticity < 0
    assert profit_result.expected_profit >= 0
    assert product.minimum_price <= profit_result.recommended_price
    assert profit_result.recommended_price <= product.maximum_price

    print("\nValidation completed successfully.")
    print("Results exported to pricing_results.csv")


if __name__ == "__main__":
    main()
