from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from collections import defaultdict
from datetime import date


class DataType(Enum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"


@dataclass(frozen=True)
class SalesRow:
    order_id: int
    order_date: date
    region: str
    product: str
    category: str
    quantity: int
    unit_price: float
    unit_cost: float


class ValidationError(ValueError):
    pass


class SalesModel:
    """
    Small tabular model used to illustrate DAX concepts.

    The Python calculations intentionally mirror common DAX semantics:
    - calculated-column logic evaluates one row at a time
    - measures aggregate according to the current filter context
    - CALCULATE-like behavior changes the filter context
    - DIVIDE-like behavior handles zero denominators safely
    """

    def __init__(self, rows: Iterable[SalesRow]) -> None:
        self.rows = list(rows)
        self._validate()

    def _validate(self) -> None:
        if not self.rows:
            raise ValidationError("The model requires at least one sales row.")

        order_ids = set()

        for row in self.rows:
            if row.order_id in order_ids:
                raise ValidationError(f"Duplicate order_id: {row.order_id}")
            order_ids.add(row.order_id)

            if row.quantity <= 0:
                raise ValidationError(f"Quantity must be positive: {row.order_id}")

            if row.unit_price < 0 or row.unit_cost < 0:
                raise ValidationError(f"Prices cannot be negative: {row.order_id}")

            if row.unit_cost > row.unit_price:
                raise ValidationError(
                    f"Unit cost exceeds unit price for order {row.order_id}"
                )

    # Calculated-column style expressions.
    @staticmethod
    def sales_amount(row: SalesRow) -> float:
        return row.quantity * row.unit_price

    @staticmethod
    def cost_amount(row: SalesRow) -> float:
        return row.quantity * row.unit_cost

    @staticmethod
    def profit_amount(row: SalesRow) -> float:
        return SalesModel.sales_amount(row) - SalesModel.cost_amount(row)

    @staticmethod
    def profit_margin(row: SalesRow) -> float:
        sales = SalesModel.sales_amount(row)
        return SalesModel.profit_amount(row) / sales if sales else 0.0

    @staticmethod
    def sales_band(row: SalesRow) -> str:
        amount = SalesModel.sales_amount(row)
        if amount >= 5000:
            return "High"
        if amount >= 2000:
            return "Medium"
        return "Low"

    # Measure-like calculations.
    def total_sales(self, rows: Iterable[SalesRow] | None = None) -> float:
        source = self.rows if rows is None else rows
        return sum(self.sales_amount(row) for row in source)

    def total_cost(self, rows: Iterable[SalesRow] | None = None) -> float:
        source = self.rows if rows is None else rows
        return sum(self.cost_amount(row) for row in source)

    def total_profit(self, rows: Iterable[SalesRow] | None = None) -> float:
        source = self.rows if rows is None else rows
        return sum(self.profit_amount(row) for row in source)

    def profit_margin_measure(
        self, rows: Iterable[SalesRow] | None = None
    ) -> float:
        sales = self.total_sales(rows)
        return self.total_profit(rows) / sales if sales else 0.0

    def average_order_value(
        self, rows: Iterable[SalesRow] | None = None
    ) -> float:
        source = list(self.rows if rows is None else rows)
        return self.total_sales(source) / len(source) if source else 0.0

    def filter_context(
        self,
        region: str | None = None,
        category: str | None = None,
        product: str | None = None,
        minimum_sales: float | None = None,
    ) -> list[SalesRow]:
        """
        Represents a simplified filter context.

        In a Power BI model, slicers and visual groupings establish filter
        context. A measure then evaluates against the resulting context.
        """
        result = self.rows

        if region is not None:
            result = [r for r in result if r.region == region]

        if category is not None:
            result = [r for r in result if r.category == category]

        if product is not None:
            result = [r for r in result if r.product == product]

        if minimum_sales is not None:
            result = [
                r for r in result
                if self.sales_amount(r) >= minimum_sales
            ]

        return result

    def calculate(
        self,
        measure,
        *,
        region: str | None = None,
        category: str | None = None,
        product: str | None = None,
    ) -> float:
        """
        Simplified CALCULATE behavior:
        modify filter context, then evaluate a measure.
        """
        context = self.filter_context(
            region=region,
            category=category,
            product=product,
        )
        return measure(context)

    def summarize_by_region(self) -> list[dict[str, object]]:
        groups: dict[str, list[SalesRow]] = defaultdict(list)

        for row in self.rows:
            groups[row.region].append(row)

        result = []

        for region, rows in sorted(groups.items()):
            result.append(
                {
                    "region": region,
                    "sales": self.total_sales(rows),
                    "cost": self.total_cost(rows),
                    "profit": self.total_profit(rows),
                    "margin": self.profit_margin_measure(rows),
                    "orders": len(rows),
                }
            )

        return result

    def summarize_by_category(self) -> list[dict[str, object]]:
        groups: dict[str, list[SalesRow]] = defaultdict(list)

        for row in self.rows:
            groups[row.category].append(row)

        result = []

        for category, rows in sorted(groups.items()):
            result.append(
                {
                    "category": category,
                    "sales": self.total_sales(rows),
                    "profit": self.total_profit(rows),
                    "margin": self.profit_margin_measure(rows),
                }
            )

        return result

    def top_products(self, limit: int = 3) -> list[tuple[str, float]]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        totals: dict[str, float] = defaultdict(float)

        for row in self.rows:
            totals[row.product] += self.sales_amount(row)

        return sorted(
            totals.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]

    def calculated_column_snapshot(self) -> list[dict[str, object]]:
        return [
            {
                "order_id": row.order_id,
                "sales_amount": self.sales_amount(row),
                "cost_amount": self.cost_amount(row),
                "profit_amount": self.profit_amount(row),
                "profit_margin": self.profit_margin(row),
                "sales_band": self.sales_band(row),
            }
            for row in self.rows
        ]


def print_currency(value: float) -> str:
    return f"${value:,.2f}"


def main() -> None:
    rows = [
        SalesRow(1001, date(2026, 1, 5), "North", "Laptop", "Technology", 2, 1200, 850),
        SalesRow(1002, date(2026, 1, 7), "South", "Monitor", "Technology", 4, 350, 220),
        SalesRow(1003, date(2026, 1, 9), "North", "Desk", "Furniture", 3, 500, 310),
        SalesRow(1004, date(2026, 1, 12), "West", "Laptop", "Technology", 1, 1500, 980),
        SalesRow(1005, date(2026, 1, 15), "South", "Chair", "Furniture", 8, 180, 110),
        SalesRow(1006, date(2026, 1, 19), "West", "Desk", "Furniture", 2, 550, 320),
        SalesRow(1007, date(2026, 1, 23), "North", "Monitor", "Technology", 5, 325, 200),
        SalesRow(1008, date(2026, 1, 27), "South", "Laptop", "Technology", 3, 1100, 790),
    ]

    model = SalesModel(rows)

    print("=== DAX FUNDAMENTALS MODEL ===")
    print(f"Rows: {len(model.rows)}")
    print(f"Total Sales: {print_currency(model.total_sales())}")
    print(f"Total Cost: {print_currency(model.total_cost())}")
    print(f"Total Profit: {print_currency(model.total_profit())}")
    print(f"Profit Margin: {model.profit_margin_measure():.2%}")
    print(f"Average Order Value: {print_currency(model.average_order_value())}")

    print("\n=== CALCULATED-COLUMN STYLE RESULTS ===")
    for item in model.calculated_column_snapshot():
        print(
            f"Order {item['order_id']}: "
            f"sales={print_currency(item['sales_amount'])}, "
            f"profit={print_currency(item['profit_amount'])}, "
            f"margin={item['profit_margin']:.2%}, "
            f"band={item['sales_band']}"
        )

    print("\n=== FILTER CONTEXT ===")
    north = model.filter_context(region="North")
    print(f"North Sales: {print_currency(model.total_sales(north))}")
    print(f"North Profit: {print_currency(model.total_profit(north))}")

    technology_north = model.filter_context(
        region="North",
        category="Technology",
    )
    print(
        "North Technology Sales: "
        f"{print_currency(model.total_sales(technology_north))}"
    )

    print("\n=== CALCULATE-LIKE EVALUATION ===")
    south_sales = model.calculate(
        model.total_sales,
        region="South",
    )
    south_technology_profit = model.calculate(
        model.total_profit,
        region="South",
        category="Technology",
    )
    print(f"South Sales: {print_currency(south_sales)}")
    print(
        "South Technology Profit: "
        f"{print_currency(south_technology_profit)}"
    )

    print("\n=== REGION MEASURES ===")
    for item in model.summarize_by_region():
        print(
            f"{item['region']}: "
            f"sales={print_currency(item['sales'])}, "
            f"profit={print_currency(item['profit'])}, "
            f"margin={item['margin']:.2%}, "
            f"orders={item['orders']}"
        )

    print("\n=== CATEGORY MEASURES ===")
    for item in model.summarize_by_category():
        print(
            f"{item['category']}: "
            f"sales={print_currency(item['sales'])}, "
            f"profit={print_currency(item['profit'])}, "
            f"margin={item['margin']:.2%}"
        )

    print("\n=== TOP PRODUCTS ===")
    for product, sales in model.top_products(3):
        print(f"{product}: {print_currency(sales)}")

    # Assertions provide executable checks for important model behavior.
    assert round(model.total_sales(), 2) == 10555.00
    assert round(model.total_profit(), 2) == 3405.00
    assert len(model.filter_context(region="North")) == 3
    assert model.total_sales([]) == 0.0
    assert model.profit_margin_measure([]) == 0.0

    print("\nValidation checks: PASSED")


if __name__ == "__main__":
    main()
