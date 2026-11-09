"""
COMPLETE BUSINESS ANALYTICS PROJECT
Domain: Retail Sales, Revenue, Customer Segmentation and Business Performance

Runtime: Python 3.10+
Dependencies: Python standard library only.

Optional input:
    sales.csv

Generated outputs:
    output/business_analysis_report.json
    output/monthly_sales.csv
    output/product_performance.csv
    output/customer_segments.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import random
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("output")
CURRENCY = "INR"


class DataValidationError(ValueError):
    """Raised when source business data is invalid."""


class Segment(Enum):
    HIGH_VALUE = "High Value"
    REGULAR = "Regular"
    OCCASIONAL = "Occasional"
    AT_RISK = "At Risk"


@dataclass(frozen=True)
class Sale:
    transaction_id: str
    transaction_date: date
    customer_id: str
    product_id: str
    category: str
    region: str
    quantity: int
    unit_price: float
    unit_cost: float

    @property
    def revenue(self) -> float:
        return self.quantity * self.unit_price

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost

    @property
    def profit(self) -> float:
        return self.revenue - self.cost


@dataclass
class BusinessMetrics:
    total_transactions: int
    total_revenue: float
    total_cost: float
    gross_profit: float
    gross_margin_percent: float
    average_order_value: float
    total_units_sold: int
    unique_customers: int
    repeat_customers: int
    repeat_customer_rate: float


def validate_sale(sale: Sale) -> None:
    if not sale.transaction_id.strip():
        raise DataValidationError("Transaction ID cannot be empty.")

    if not sale.customer_id.strip() or not sale.product_id.strip():
        raise DataValidationError("Customer and product IDs are required.")

    if sale.quantity <= 0:
        raise DataValidationError("Quantity must be positive.")

    if not math.isfinite(sale.unit_price) or sale.unit_price <= 0:
        raise DataValidationError("Unit price must be finite and positive.")

    if not math.isfinite(sale.unit_cost) or sale.unit_cost < 0:
        raise DataValidationError("Unit cost must be finite and non-negative.")

    if sale.unit_cost > sale.unit_price:
        raise DataValidationError("Unit cost cannot exceed unit selling price.")

    if not sale.category.strip() or not sale.region.strip():
        raise DataValidationError("Category and region are required.")


def generate_sample_data() -> list[Sale]:
    """Generate deterministic sample transactions across business regions."""

    random.seed(42)

    products = {
        "P001": ("Electronics", 25000, 18000),
        "P002": ("Electronics", 12000, 8500),
        "P003": ("Furniture", 18000, 12000),
        "P004": ("Furniture", 8000, 5200),
        "P005": ("Clothing", 2500, 1200),
        "P006": ("Clothing", 1500, 700),
        "P007": ("Groceries", 900, 650),
        "P008": ("Groceries", 500, 350),
    }

    regions = ["North", "South", "East", "West", "Central"]
    transactions = []

    start = date(2025, 1, 1)

    for index in range(1, 501):
        product_id = random.choice(list(products))
        category, price, cost = products[product_id]

        transaction_date = start + timedelta(
            days=random.randint(0, 364)
        )

        quantity = random.randint(1, 5)

        transactions.append(
            Sale(
                transaction_id=f"TXN{index:05d}",
                transaction_date=transaction_date,
                customer_id=f"C{random.randint(1, 120):04d}",
                product_id=product_id,
                category=category,
                region=random.choice(regions),
                quantity=quantity,
                unit_price=round(price * random.uniform(0.90, 1.10), 2),
                unit_cost=round(cost * random.uniform(0.95, 1.05), 2),
            )
        )

    return transactions


def load_sales(filepath: Path) -> list[Sale]:
    """Load and validate transaction records from CSV."""

    required = {
        "transaction_id", "transaction_date", "customer_id",
        "product_id", "category", "region", "quantity",
        "unit_price", "unit_cost"
    }

    sales = []
    seen_ids = set()

    with filepath.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise DataValidationError(
                f"CSV must contain these columns: {sorted(required)}"
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                sale = Sale(
                    transaction_id=row["transaction_id"].strip(),
                    transaction_date=date.fromisoformat(
                        row["transaction_date"].strip()
                    ),
                    customer_id=row["customer_id"].strip(),
                    product_id=row["product_id"].strip(),
                    category=row["category"].strip(),
                    region=row["region"].strip(),
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    unit_cost=float(row["unit_cost"]),
                )

                validate_sale(sale)

                if sale.transaction_id in seen_ids:
                    raise DataValidationError("Duplicate transaction ID.")

                seen_ids.add(sale.transaction_id)
                sales.append(sale)

            except (ValueError, TypeError, KeyError) as exc:
                raise DataValidationError(
                    f"Invalid CSV record at line {line_number}: {exc}"
                ) from exc

    if not sales:
        raise DataValidationError("The input file contains no transactions.")

    return sales


def calculate_metrics(sales: list[Sale]) -> BusinessMetrics:
    revenue = sum(s.revenue for s in sales)
    cost = sum(s.cost for s in sales)
    profit = revenue - cost

    customer_orders = defaultdict(int)

    for sale in sales:
        customer_orders[sale.customer_id] += 1

    unique_customers = len(customer_orders)
    repeat_customers = sum(
        count > 1 for count in customer_orders.values()
    )

    return BusinessMetrics(
        total_transactions=len(sales),
        total_revenue=round(revenue, 2),
        total_cost=round(cost, 2),
        gross_profit=round(profit, 2),
        gross_margin_percent=round(
            profit / revenue * 100 if revenue else 0, 2
        ),
        average_order_value=round(revenue / len(sales), 2),
        total_units_sold=sum(s.quantity for s in sales),
        unique_customers=unique_customers,
        repeat_customers=repeat_customers,
        repeat_customer_rate=round(
            repeat_customers / unique_customers * 100
            if unique_customers else 0, 2
        ),
    )


def aggregate_by_dimension(
    sales: list[Sale],
    dimension: str
) -> dict[str, dict[str, float]]:
    """Aggregate revenue, profit and volume by a selected dimension."""

    if dimension not in {"category", "region", "product_id"}:
        raise ValueError("Unsupported aggregation dimension.")

    groups = defaultdict(lambda: {
        "revenue": 0.0,
        "profit": 0.0,
        "units": 0,
        "transactions": 0,
    })

    for sale in sales:
        key = getattr(sale, dimension)
        groups[key]["revenue"] += sale.revenue
        groups[key]["profit"] += sale.profit
        groups[key]["units"] += sale.quantity
        groups[key]["transactions"] += 1

    return {
        key: {
            "revenue": round(values["revenue"], 2),
            "profit": round(values["profit"], 2),
            "units": values["units"],
            "transactions": values["transactions"],
        }
        for key, values in sorted(
            groups.items(),
            key=lambda item: item[1]["revenue"],
            reverse=True
        )
    }


def monthly_analysis(sales: list[Sale]) -> list[dict[str, Any]]:
    monthly = defaultdict(lambda: {
        "revenue": 0.0,
        "profit": 0.0,
        "transactions": 0,
    })

    for sale in sales:
        month = sale.transaction_date.strftime("%Y-%m")
        monthly[month]["revenue"] += sale.revenue
        monthly[month]["profit"] += sale.profit
        monthly[month]["transactions"] += 1

    results = []

    for month in sorted(monthly):
        values = monthly[month]

        results.append({
            "month": month,
            "revenue": round(values["revenue"], 2),
            "profit": round(values["profit"], 2),
            "transactions": values["transactions"],
        })

    for index, current in enumerate(results):
        previous_revenue = (
            results[index - 1]["revenue"] if index > 0 else None
        )

        current["growth_percent"] = (
            round(
                (current["revenue"] - previous_revenue)
                / previous_revenue * 100,
                2
            )
            if previous_revenue else None
        )

    return results


def linear_trend(values: list[float]) -> dict[str, float]:
    """Calculate a least-squares trend and next-period estimate."""

    if not values:
        return {"slope": 0.0, "next_period_forecast": 0.0}

    if len(values) == 1:
        return {
            "slope": 0.0,
            "next_period_forecast": round(values[0], 2)
        }

    x_values = list(range(len(values)))
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(values)

    denominator = sum((x - x_mean) ** 2 for x in x_values)

    slope = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, values)
    ) / denominator

    intercept = y_mean - slope * x_mean

    forecast = max(0, intercept + slope * len(values))

    return {
        "slope": round(slope, 2),
        "next_period_forecast": round(forecast, 2),
    }


def customer_segmentation(
    sales: list[Sale],
    reference_date: date
) -> dict[str, dict[str, Any]]:
    """
    Segment customers using recency, frequency and monetary value.

    Thresholds are illustrative business rules, not universal standards.
    """

    customer_data = defaultdict(list)

    for sale in sales:
        customer_data[sale.customer_id].append(sale)

    segments = {}

    for customer_id, orders in customer_data.items():
        frequency = len(orders)
        monetary = sum(s.revenue for s in orders)

        last_purchase = max(s.transaction_date for s in orders)
        recency = (reference_date - last_purchase).days

        if frequency >= 5 and monetary >= 50000 and recency <= 90:
            segment = Segment.HIGH_VALUE
        elif frequency >= 3 and recency <= 180:
            segment = Segment.REGULAR
        elif recency > 180:
            segment = Segment.AT_RISK
        else:
            segment = Segment.OCCASIONAL

        segments[customer_id] = {
            "segment": segment.value,
            "frequency": frequency,
            "monetary_value": round(monetary, 2),
            "recency_days": recency,
        }

    return segments


def detect_anomalies(
    monthly: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Flag unusually low monthly revenue using a historical baseline."""

    if len(monthly) < 4:
        return []

    revenues = [item["revenue"] for item in monthly]
    baseline = statistics.mean(revenues)
    deviation = statistics.pstdev(revenues)

    if deviation == 0:
        return []

    return [
        {
            "month": item["month"],
            "revenue": item["revenue"],
            "z_score": round(
                (item["revenue"] - baseline) / deviation, 2
            ),
        }
        for item in monthly
        if (item["revenue"] - baseline) / deviation < -1.5
    ]


def generate_recommendations(
    metrics: BusinessMetrics,
    categories: dict,
    regions: dict,
    segments: dict,
) -> list[str]:

    recommendations = []

    if metrics.gross_margin_percent < 20:
        recommendations.append(
            "Review supplier costs, discount policies and product pricing."
        )

    if metrics.repeat_customer_rate < 30:
        recommendations.append(
            "Introduce customer retention and repeat-purchase campaigns."
        )

    if categories:
        best = next(iter(categories))
        recommendations.append(
            f"Evaluate inventory and marketing investment for "
            f"the leading category: {best}."
        )

    if regions:
        weakest = min(
            regions,
            key=lambda key: regions[key]["revenue"]
        )
        recommendations.append(
            f"Investigate sales performance and distribution in "
            f"the lowest-revenue region: {weakest}."
        )

    high_value = sum(
        value["segment"] == Segment.HIGH_VALUE.value
        for value in segments.values()
    )

    recommendations.append(
        f"Prioritize personalized retention for {high_value} "
        "high-value customers."
    )

    return recommendations


def export_csv(
    filepath: Path,
    records: list[dict[str, Any]]
) -> None:
    if not records:
        return

    with filepath.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def run_analysis(sales: list[Sale]) -> dict[str, Any]:
    for sale in sales:
        validate_sale(sale)

    metrics = calculate_metrics(sales)
    categories = aggregate_by_dimension(sales, "category")
    regions = aggregate_by_dimension(sales, "region")
    products = aggregate_by_dimension(sales, "product_id")
    monthly = monthly_analysis(sales)

    reference_date = max(s.transaction_date for s in sales)
    segments = customer_segmentation(sales, reference_date)

    forecast = linear_trend([
        item["revenue"] for item in monthly
    ])

    anomalies = detect_anomalies(monthly)

    recommendations = generate_recommendations(
        metrics, categories, regions, segments
    )

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "currency": CURRENCY,
        "metrics": asdict(metrics),
        "category_performance": categories,
        "regional_performance": regions,
        "product_performance": products,
        "monthly_analysis": monthly,
        "revenue_forecast": forecast,
        "revenue_anomalies": anomalies,
        "customer_segments": segments,
        "recommendations": recommendations,
    }


def export_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = OUTPUT_DIR / "business_analysis_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    export_csv(
        OUTPUT_DIR / "monthly_sales.csv",
        report["monthly_analysis"]
    )

    export_csv(
        OUTPUT_DIR / "product_performance.csv",
        [
            {"product_id": key, **value}
            for key, value in report["product_performance"].items()
        ]
    )

    export_csv(
        OUTPUT_DIR / "customer_segments.csv",
        [
            {"customer_id": key, **value}
            for key, value in report["customer_segments"].items()
        ]
    )

    print(f"\nReport saved: {report_path.resolve()}")


def run_tests() -> None:
    sample = Sale(
        "TEST001", date(2025, 1, 1), "C001", "P001",
        "Electronics", "North", 2, 1000.0, 600.0
    )

    validate_sale(sample)

    assert sample.revenue == 2000
    assert sample.profit == 800

    metrics = calculate_metrics([sample])

    assert metrics.total_transactions == 1
    assert metrics.gross_profit == 800
    assert metrics.average_order_value == 2000

    assert linear_trend([100, 200, 300])["slope"] == 100
    assert linear_trend([])["next_period_forecast"] == 0

    print("All internal validation tests passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Complete Retail Business Analytics Pipeline"
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Optional path to a sales CSV file."
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run internal validation tests."
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    try:
        if args.test:
            run_tests()

        sales = (
            load_sales(args.input)
            if args.input
            else generate_sample_data()
        )

        report = run_analysis(sales)
        export_report(report)

        metrics = report["metrics"]

        print("\nBUSINESS PERFORMANCE REPORT")
        print("=" * 45)
        print(f"Transactions: {metrics['total_transactions']}")
        print(f"Revenue: {CURRENCY} {metrics['total_revenue']:,.2f}")
        print(f"Gross profit: {CURRENCY} {metrics['gross_profit']:,.2f}")
        print(f"Gross margin: {metrics['gross_margin_percent']}%")
        print(f"Average order value: {CURRENCY} "
              f"{metrics['average_order_value']:,.2f}")
        print(f"Unique customers: {metrics['unique_customers']}")
        print(f"Repeat customer rate: "
              f"{metrics['repeat_customer_rate']}%")

        print("\nBUSINESS RECOMMENDATIONS")

        for recommendation in report["recommendations"]:
            print(f"- {recommendation}")

    except (OSError, DataValidationError, ValueError) as exc:
        logging.error("Analysis failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
