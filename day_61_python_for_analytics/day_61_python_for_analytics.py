from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from statistics import mean, median
from typing import Iterable
import csv
import json
import math
import tempfile


class ValidationError(ValueError):
    """Raised when business data violates an analytical rule."""


class CustomerSegment(Enum):
    HIGH_VALUE = "High Value"
    GROWTH = "Growth"
    AT_RISK = "At Risk"
    STANDARD = "Standard"


@dataclass(frozen=True)
class SalesRecord:
    order_id: str
    order_date: date
    region: str
    salesperson: str
    customer: str
    product: str
    units: int
    unit_price: float
    discount_rate: float
    cost_per_unit: float

    @property
    def gross_sales(self) -> float:
        return self.units * self.unit_price

    @property
    def discount_amount(self) -> float:
        return self.gross_sales * self.discount_rate

    @property
    def net_sales(self) -> float:
        return self.gross_sales - self.discount_amount

    @property
    def cost(self) -> float:
        return self.units * self.cost_per_unit

    @property
    def profit(self) -> float:
        return self.net_sales - self.cost

    @property
    def margin(self) -> float:
        return self.profit / self.net_sales if self.net_sales else 0.0


def validate_record(record: SalesRecord) -> None:
    if not record.order_id.strip():
        raise ValidationError("Order ID cannot be empty.")
    if record.units <= 0:
        raise ValidationError(f"{record.order_id}: units must be positive.")
    if record.unit_price < 0 or record.cost_per_unit < 0:
        raise ValidationError(f"{record.order_id}: prices cannot be negative.")
    if not 0 <= record.discount_rate <= 1:
        raise ValidationError(f"{record.order_id}: discount rate must be 0..1.")
    if record.cost_per_unit > record.unit_price:
        raise ValidationError(
            f"{record.order_id}: cost per unit exceeds list price."
        )


def load_records() -> list[SalesRecord]:
    raw = [
        ("O1001", "2026-01-05", "North", "Asha", "Acme", "Analytics", 12, 850, .05, 510),
        ("O1002", "2026-01-09", "South", "Ravi", "Beta", "Automation", 8, 1200, .10, 720),
        ("O1003", "2026-01-15", "North", "Asha", "Delta", "Analytics", 5, 850, .00, 510),
        ("O1004", "2026-02-03", "West", "Neha", "Acme", "Security", 15, 700, .08, 420),
        ("O1005", "2026-02-11", "South", "Ravi", "Gamma", "Analytics", 20, 850, .12, 510),
        ("O1006", "2026-02-19", "West", "Neha", "Delta", "Automation", 7, 1200, .05, 720),
        ("O1007", "2026-03-02", "North", "Asha", "Beta", "Security", 10, 700, .03, 420),
        ("O1008", "2026-03-12", "South", "Ravi", "Acme", "Analytics", 16, 850, .07, 510),
        ("O1009", "2026-03-20", "West", "Neha", "Gamma", "Security", 6, 700, .15, 420),
        ("O1010", "2026-03-25", "North", "Asha", "Delta", "Automation", 11, 1200, .06, 720),
    ]

    records = []
    for row in raw:
        record = SalesRecord(
            order_id=row[0],
            order_date=date.fromisoformat(row[1]),
            region=row[2],
            salesperson=row[3],
            customer=row[4],
            product=row[5],
            units=row[6],
            unit_price=row[7],
            discount_rate=row[8],
            cost_per_unit=row[9],
        )
        validate_record(record)
        records.append(record)

    return records


def group_sum(records: Iterable[SalesRecord], key_function, value_function):
    result: dict[str, float] = {}
    for record in records:
        key = key_function(record)
        result[key] = result.get(key, 0.0) + value_function(record)
    return result


def group_count(records: Iterable[SalesRecord], key_function):
    result: dict[str, int] = {}
    for record in records:
        key = key_function(record)
        result[key] = result.get(key, 0) + 1
    return result


def classify_customer(records: list[SalesRecord]) -> dict[str, CustomerSegment]:
    sales = group_sum(records, lambda r: r.customer, lambda r: r.net_sales)
    margins = {}

    for customer in sales:
        customer_records = [r for r in records if r.customer == customer]
        margins[customer] = (
            sum(r.profit for r in customer_records) / sales[customer]
            if sales[customer]
            else 0
        )

    segments = {}
    for customer, revenue in sales.items():
        if revenue >= 15000 and margins[customer] >= 0.30:
            segments[customer] = CustomerSegment.HIGH_VALUE
        elif revenue >= 10000:
            segments[customer] = CustomerSegment.GROWTH
        elif margins[customer] < 0.25:
            segments[customer] = CustomerSegment.AT_RISK
        else:
            segments[customer] = CustomerSegment.STANDARD

    return segments


def monthly_sales(records: list[SalesRecord]) -> dict[str, float]:
    return group_sum(
        records,
        lambda r: r.order_date.strftime("%Y-%m"),
        lambda r: r.net_sales,
    )


def correlation(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Correlation requires equal-sized arrays with at least two values.")

    x_mean = mean(x)
    y_mean = mean(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    x_variance = sum((a - x_mean) ** 2 for a in x)
    y_variance = sum((b - y_mean) ** 2 for b in y)

    denominator = math.sqrt(x_variance * y_variance)
    return numerator / denominator if denominator else 0.0


def save_csv(records: list[SalesRecord], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "order_id", "order_date", "region", "salesperson", "customer",
                "product", "units", "unit_price", "discount_rate",
                "cost_per_unit", "net_sales", "profit", "margin"
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.order_id,
                    r.order_date.isoformat(),
                    r.region,
                    r.salesperson,
                    r.customer,
                    r.product,
                    r.units,
                    r.unit_price,
                    r.discount_rate,
                    r.cost_per_unit,
                    round(r.net_sales, 2),
                    round(r.profit, 2),
                    round(r.margin, 4),
                ]
            )


def build_report(records: list[SalesRecord]) -> dict:
    total_sales = sum(r.net_sales for r in records)
    total_profit = sum(r.profit for r in records)
    total_units = sum(r.units for r in records)

    report = {
        "records": len(records),
        "total_sales": round(total_sales, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": round(total_profit / total_sales, 4),
        "total_units": total_units,
        "average_order_value": round(total_sales / len(records), 2),
        "median_order_value": round(median(r.net_sales for r in records), 2),
        "sales_by_region": {
            k: round(v, 2)
            for k, v in group_sum(
                records, lambda r: r.region, lambda r: r.net_sales
            ).items()
        },
        "profit_by_product": {
            k: round(v, 2)
            for k, v in group_sum(
                records, lambda r: r.product, lambda r: r.profit
            ).items()
        },
        "sales_by_month": {
            k: round(v, 2) for k, v in monthly_sales(records).items()
        },
        "customer_segments": {
            k: v.value for k, v in classify_customer(records).items()
        },
    }

    return report


def run_quality_checks(records: list[SalesRecord]) -> None:
    assert records
    assert all(r.net_sales >= 0 for r in records)
    assert all(r.margin <= 1 for r in records)

    duplicate_ids = len({r.order_id for r in records}) != len(records)
    assert not duplicate_ids, "Duplicate order IDs detected."

    monthly = monthly_sales(records)
    assert len(monthly) == 3

    units = [r.units for r in records]
    sales = [r.net_sales for r in records]
    assert correlation(units, sales) > 0


def main() -> None:
    records = load_records()
    run_quality_checks(records)

    report = build_report(records)

    print("BUSINESS ANALYTICS REPORT")
    print("=" * 70)
    print(f"Orders:             {report['records']}")
    print(f"Units:              {report['total_units']:,}")
    print(f"Net sales:          ${report['total_sales']:,.2f}")
    print(f"Profit:             ${report['total_profit']:,.2f}")
    print(f"Profit margin:      {report['profit_margin']:.2%}")
    print(f"Average order:      ${report['average_order_value']:,.2f}")
    print(f"Median order:       ${report['median_order_value']:,.2f}")

    print("\nSales by region")
    for region, value in sorted(report["sales_by_region"].items()):
        print(f"  {region:<10} ${value:,.2f}")

    print("\nProfit by product")
    for product, value in sorted(report["profit_by_product"].items()):
        print(f"  {product:<12} ${value:,.2f}")

    print("\nCustomer segmentation")
    for customer, segment in sorted(report["customer_segments"].items()):
        print(f"  {customer:<10} {segment}")

    print("\nMonthly sales")
    for month, value in sorted(report["sales_by_month"].items()):
        print(f"  {month:<10} ${value:,.2f}")

    with tempfile.TemporaryDirectory() as directory:
        output_path = Path(directory) / "sales_analysis.csv"
        save_csv(records, output_path)

        json_path = Path(directory) / "analytics_report.json"
        json_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        assert output_path.exists()
        assert json_path.exists()
        print(f"\nValidated CSV export: {output_path.name}")
        print(f"Validated JSON export: {json_path.name}")


if __name__ == "__main__":
    main()
