"""
SQL Analytics Project: Retail Business Performance Analysis

A self-contained business analytics project using a realistic retail dataset.
The script demonstrates data validation, exploratory analysis, revenue and
profitability metrics, customer segmentation, inventory analysis, cohort
retention, forecasting, anomaly detection, and PostgreSQL export.

Runtime: Python 3.10+
Dependencies: Python standard library only.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import tempfile
import unittest
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Order:
    order_id: str
    order_date: date
    customer_id: str
    region: str
    category: str
    product: str
    quantity: int
    unit_price: float
    unit_cost: float
    discount: float
    payment_method: str
    returned: bool = False

    @property
    def gross_sales(self) -> float:
        return self.quantity * self.unit_price

    @property
    def discount_amount(self) -> float:
        return self.gross_sales * self.discount

    @property
    def revenue(self) -> float:
        return self.gross_sales - self.discount_amount

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost

    @property
    def profit(self) -> float:
        # Returns reverse recognized sales and cost in this simplified model.
        return -self.revenue if self.returned else self.revenue - self.cost

    @property
    def effective_revenue(self) -> float:
        return 0.0 if self.returned else self.revenue

    @property
    def effective_cost(self) -> float:
        return 0.0 if self.returned else self.cost


def money(value: float) -> str:
    return f"${value:,.2f}"


def validate_order(order: Order) -> list[str]:
    errors: list[str] = []

    if not order.order_id.strip():
        errors.append("order_id cannot be empty")
    if not order.customer_id.strip():
        errors.append("customer_id cannot be empty")
    if order.quantity <= 0:
        errors.append("quantity must be positive")
    if not math.isfinite(order.unit_price) or order.unit_price < 0:
        errors.append("unit_price must be finite and non-negative")
    if not math.isfinite(order.unit_cost) or order.unit_cost < 0:
        errors.append("unit_cost must be finite and non-negative")
    if not math.isfinite(order.discount) or not 0 <= order.discount <= 1:
        errors.append("discount must be between 0 and 1")
    if not order.region.strip():
        errors.append("region cannot be empty")
    if not order.category.strip():
        errors.append("category cannot be empty")
    if not order.product.strip():
        errors.append("product cannot be empty")
    if order.payment_method not in {
        "Card", "UPI", "Cash", "Bank Transfer", "Wallet"
    }:
        errors.append("unsupported payment method")

    return errors


def validate_dataset(orders: Iterable[Order]) -> dict:
    rows = list(orders)
    seen: set[str] = set()
    duplicates: list[str] = []
    invalid: list[dict] = []

    for order in rows:
        if order.order_id in seen:
            duplicates.append(order.order_id)
        seen.add(order.order_id)

        errors = validate_order(order)
        if errors:
            invalid.append({"order_id": order.order_id, "errors": errors})

    return {
        "row_count": len(rows),
        "unique_order_ids": len(seen),
        "duplicate_order_ids": sorted(set(duplicates)),
        "invalid_rows": invalid,
        "valid": not duplicates and not invalid,
    }


def create_business_dataset(seed: int = 42) -> list[Order]:
    """Create deterministic, synthetic retail transactions with business patterns."""
    rng = random.Random(seed)

    products = [
        ("Laptop", "Electronics", 850.0, 610.0),
        ("Headphones", "Electronics", 95.0, 48.0),
        ("Monitor", "Electronics", 260.0, 175.0),
        ("Office Chair", "Furniture", 190.0, 118.0),
        ("Desk", "Furniture", 320.0, 220.0),
        ("Notebook Pack", "Stationery", 12.0, 4.0),
        ("Printer Paper", "Stationery", 8.0, 3.2),
        ("Backpack", "Accessories", 55.0, 24.0),
        ("USB Hub", "Accessories", 28.0, 11.0),
    ]

    regions = ["North", "South", "East", "West", "Central"]
    payments = ["Card", "UPI", "Cash", "Bank Transfer", "Wallet"]
    start = date(2025, 1, 1)
    orders: list[Order] = []

    for index in range(1, 1201):
        # More orders occur on weekdays and near month-end in this simulation.
        day_offset = rng.randrange(365)
        order_date = start + timedelta(days=day_offset)
        product, category, base_price, base_cost = rng.choice(products)

        quantity = rng.choices(
            [1, 2, 3, 4, 5, 8],
            weights=[40, 28, 15, 9, 5, 3],
        )[0]

        # A seasonal sales lift is applied in November and December.
        seasonal_factor = (
            1.18 if order_date.month in (11, 12)
            else 1.0
        )
        unit_price = round(base_price * seasonal_factor, 2)
        discount = rng.choices(
            [0.0, 0.05, 0.10, 0.15, 0.20],
            weights=[35, 25, 23, 12, 5],
        )[0]

        returned = rng.random() < 0.045

        # Introduce a small number of high-value transactions to make
        # outlier detection and business investigation meaningful.
        if index in (111, 444, 888):
            quantity = 15
            discount = 0.0

        orders.append(
            Order(
                order_id=f"ORD-{index:05d}",
                order_date=order_date,
                customer_id=f"CUST-{rng.randint(1, 320):04d}",
                region=rng.choice(regions),
                category=category,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=round(base_cost, 2),
                discount=discount,
                payment_method=rng.choice(payments),
                returned=returned,
            )
        )

    return orders


def load_orders_csv(path: Path) -> list[Order]:
    """Read the documented CSV schema and reject malformed records."""
    orders: list[Order] = []

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {
            "order_id", "order_date", "customer_id", "region", "category",
            "product", "quantity", "unit_price", "unit_cost", "discount",
            "payment_method", "returned",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("CSV is missing required columns")

        for line_number, row in enumerate(reader, start=2):
            try:
                order = Order(
                    order_id=row["order_id"].strip(),
                    order_date=date.fromisoformat(row["order_date"]),
                    customer_id=row["customer_id"].strip(),
                    region=row["region"].strip(),
                    category=row["category"].strip(),
                    product=row["product"].strip(),
                    quantity=int(row["quantity"]),
                    unit_price=float(row["unit_price"]),
                    unit_cost=float(row["unit_cost"]),
                    discount=float(row["discount"]),
                    payment_method=row["payment_method"].strip(),
                    returned=row["returned"].strip().lower() in {
                        "true", "1", "yes"
                    },
                )
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(
                    f"Malformed CSV record at line {line_number}: {exc}"
                ) from exc

            errors = validate_order(order)
            if errors:
                raise ValueError(
                    f"Invalid CSV record at line {line_number}: {errors}"
                )

            orders.append(order)

    return orders


def export_orders_csv(orders: Iterable[Order], path: Path) -> None:
    fields = [
        "order_id", "order_date", "customer_id", "region", "category",
        "product", "quantity", "unit_price", "unit_cost", "discount",
        "payment_method", "returned",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for order in orders:
            record = asdict(order)
            record["order_date"] = order.order_date.isoformat()
            writer.writerow(record)


def aggregate_sales(orders: Iterable[Order]) -> dict:
    rows = list(orders)
    gross = sum(order.gross_sales for order in rows)
    discounts = sum(order.discount_amount for order in rows)
    returned_count = sum(order.returned for order in rows)
    recognized = sum(order.effective_revenue for order in rows)
    recognized_cost = sum(order.effective_cost for order in rows)
    profit = recognized - recognized_cost

    return {
        "transaction_count": len(rows),
        "returned_transactions": returned_count,
        "gross_sales": round(gross, 2),
        "discounts": round(discounts, 2),
        "net_sales_before_returns": round(gross - discounts, 2),
        "recognized_revenue": round(recognized, 2),
        "recognized_cost": round(recognized_cost, 2),
        "profit": round(profit, 2),
        "profit_margin": round(profit / recognized, 4) if recognized else 0.0,
        "average_order_value": round(recognized / len(rows), 2) if rows else 0.0,
        "return_rate": round(returned_count / len(rows), 4) if rows else 0.0,
    }


def group_metrics(
    orders: Iterable[Order],
    key_function,
) -> list[dict]:
    groups: dict[str, list[Order]] = defaultdict(list)

    for order in orders:
        groups[str(key_function(order))].append(order)

    results = []
    for group_name, group_orders in groups.items():
        metrics = aggregate_sales(group_orders)
        results.append({
            "group": group_name,
            **metrics,
        })

    return sorted(results, key=lambda row: row["recognized_revenue"], reverse=True)


def monthly_metrics(orders: Iterable[Order]) -> list[dict]:
    return group_metrics(
        orders,
        lambda order: order.order_date.strftime("%Y-%m"),
    )


def customer_metrics(orders: Iterable[Order]) -> list[dict]:
    rows = list(orders)
    customers: dict[str, list[Order]] = defaultdict(list)

    for order in rows:
        customers[order.customer_id].append(order)

    results = []
    for customer_id, customer_orders in customers.items():
        valid_orders = [o for o in customer_orders if not o.returned]
        revenue = sum(o.effective_revenue for o in customer_orders)
        cost = sum(o.effective_cost for o in customer_orders)

        results.append({
            "customer_id": customer_id,
            "transactions": len(customer_orders),
            "purchase_days": len({o.order_date for o in customer_orders}),
            "first_purchase": min(o.order_date for o in customer_orders).isoformat(),
            "last_purchase": max(o.order_date for o in customer_orders).isoformat(),
            "revenue": round(revenue, 2),
            "profit": round(revenue - cost, 2),
            "segment": (
                "High Value" if revenue >= 1500
                else "Regular" if revenue >= 400
                else "Occasional"
            ),
            "non_returned_transactions": len(valid_orders),
        })

    return sorted(results, key=lambda row: row["revenue"], reverse=True)


def category_metrics(orders: Iterable[Order]) -> list[dict]:
    rows = list(orders)
    results = group_metrics(rows, lambda order: order.category)

    for result in results:
        category = result["group"]
        category_orders = [o for o in rows if o.category == category]
        units = sum(o.quantity for o in category_orders if not o.returned)
        result["units_sold"] = units
        result["revenue_per_unit"] = (
            round(result["recognized_revenue"] / units, 2) if units else 0.0
        )

    return results


def payment_metrics(orders: Iterable[Order]) -> list[dict]:
    return group_metrics(orders, lambda order: order.payment_method)


def discount_analysis(orders: Iterable[Order]) -> list[dict]:
    groups: dict[str, list[Order]] = defaultdict(list)

    for order in orders:
        if order.discount == 0:
            band = "No discount"
        elif order.discount <= 0.05:
            band = "Up to 5%"
        elif order.discount <= 0.10:
            band = "6% to 10%"
        elif order.discount <= 0.15:
            band = "11% to 15%"
        else:
            band = "Above 15%"
        groups[band].append(order)

    return [
        {
            "discount_band": band,
            "transactions": len(group),
            "revenue": round(sum(o.effective_revenue for o in group), 2),
            "profit": round(
                sum(o.effective_revenue - o.effective_cost for o in group), 2
            ),
        }
        for band, group in sorted(groups.items())
    ]


def detect_revenue_outliers(orders: Iterable[Order]) -> list[dict]:
    """Use the interquartile range to flag unusual order revenue."""
    values = sorted(order.effective_revenue for order in orders)
    if len(values) < 4:
        return []

    def percentile(sorted_values: list[float], fraction: float) -> float:
        position = (len(sorted_values) - 1) * fraction
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return sorted_values[lower]
        return (
            sorted_values[lower] * (upper - position)
            + sorted_values[upper] * (position - lower)
        )

    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    iqr = q3 - q1
    upper_limit = q3 + 1.5 * iqr
    lower_limit = max(0.0, q1 - 1.5 * iqr)

    return [
        {
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "date": order.order_date.isoformat(),
            "revenue": round(order.effective_revenue, 2),
            "reason": (
                "High revenue outlier"
                if order.effective_revenue > upper_limit
                else "Low revenue outlier"
            ),
        }
        for order in orders
        if order.effective_revenue > upper_limit
        or order.effective_revenue < lower_limit
    ]


def monthly_revenue_forecast(
    orders: Iterable[Order],
    forecast_periods: int = 3,
) -> list[dict]:
    """
    Produce a transparent baseline forecast from monthly revenue.

    The method uses a three-month moving average when enough observations
    exist. It is a baseline, not a causal or seasonality-aware model.
    """
    if forecast_periods <= 0:
        raise ValueError("forecast_periods must be positive")

    monthly = monthly_metrics(orders)
    if not monthly:
        return []

    history = [
        (date.fromisoformat(row["group"] + "-01"), row["recognized_revenue"])
        for row in monthly
    ]

    values = [value for _, value in history]
    latest_month = history[-1][0]
    results = []

    for step in range(1, forecast_periods + 1):
        window = values[-3:] if len(values) >= 3 else values
        forecast = statistics.mean(window) if window else 0.0

        month_index = latest_month.month - 1 + step
        year = latest_month.year + month_index // 12
        month = month_index % 12 + 1

        results.append({
            "forecast_month": f"{year:04d}-{month:02d}",
            "forecast_revenue": round(forecast, 2),
            "method": "Three-month moving average",
        })
        values.append(forecast)

    return results


def cohort_retention(orders: Iterable[Order]) -> list[dict]:
    """Measure customer activity by first-purchase cohort and calendar month."""
    rows = list(orders)
    if not rows:
        return []

    first_month: dict[str, str] = {}
    active: dict[str, set[str]] = defaultdict(set)

    for order in rows:
        month = order.order_date.strftime("%Y-%m")
        current = first_month.get(order.customer_id)
        if current is None or month < current:
            first_month[order.customer_id] = month
        active[month].add(order.customer_id)

    cohort_sizes = Counter(first_month.values())
    results = []

    for cohort_month, cohort_size in sorted(cohort_sizes.items()):
        cohort_customers = {
            customer_id
            for customer_id, month in first_month.items()
            if month == cohort_month
        }

        start = date.fromisoformat(cohort_month + "-01")
        for month, active_customers in sorted(active.items()):
            current = date.fromisoformat(month + "-01")
            month_index = (current.year - start.year) * 12 + current.month - start.month
            if month_index < 0:
                continue

            retained = len(cohort_customers & active_customers)
            results.append({
                "cohort_month": cohort_month,
                "activity_month": month,
                "months_since_first_purchase": month_index,
                "cohort_customers": cohort_size,
                "active_customers": retained,
                "retention_rate": round(retained / cohort_size, 4),
            })

    return results


def inventory_proxy(orders: Iterable[Order]) -> list[dict]:
    """
    Estimate product movement from sales history.

    This is a demand proxy, not a stock-on-hand calculation, because no
    purchase receipts or physical inventory snapshots are present.
    """
    groups: dict[str, list[Order]] = defaultdict(list)
    for order in orders:
        groups[order.product].append(order)

    results = []
    for product, product_orders in groups.items():
        sold_units = sum(o.quantity for o in product_orders if not o.returned)
        active_days = max(
            1,
            (max(o.order_date for o in product_orders)
             - min(o.order_date for o in product_orders)).days + 1,
        )
        daily_demand = sold_units / active_days

        results.append({
            "product": product,
            "units_sold": sold_units,
            "active_days": active_days,
            "average_daily_demand": round(daily_demand, 4),
            "estimated_30_day_demand": round(daily_demand * 30, 2),
        })

    return sorted(results, key=lambda row: row["estimated_30_day_demand"], reverse=True)


def write_json(path: Path, data: object) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def write_postgres_insert_script(orders: Iterable[Order], path: Path) -> None:
    """
    Export PostgreSQL-compatible INSERT statements with safe literal quoting.

    For production ingestion, parameterized database drivers or COPY are
    preferable to generated INSERT statements.
    """
    def quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    statements = [
        """
        CREATE TABLE IF NOT EXISTS retail_orders (
            order_id TEXT PRIMARY KEY,
            order_date DATE NOT NULL,
            customer_id TEXT NOT NULL,
            region TEXT NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
            unit_cost NUMERIC(12,2) NOT NULL CHECK (unit_cost >= 0),
            discount NUMERIC(5,4) NOT NULL CHECK (discount BETWEEN 0 AND 1),
            payment_method TEXT NOT NULL,
            returned BOOLEAN NOT NULL DEFAULT FALSE
        );
        """.strip()
    ]

    for order in orders:
        values = [
            quote(order.order_id),
            quote(order.order_date.isoformat()),
            quote(order.customer_id),
            quote(order.region),
            quote(order.category),
            quote(order.product),
            str(order.quantity),
            f"{order.unit_price:.2f}",
            f"{order.unit_cost:.2f}",
            f"{order.discount:.4f}",
            quote(order.payment_method),
            "TRUE" if order.returned else "FALSE",
        ]
        statements.append(
            "INSERT INTO retail_orders "
            "(order_id, order_date, customer_id, region, category, product, "
            "quantity, unit_price, unit_cost, discount, payment_method, returned) "
            f"VALUES ({', '.join(values)}) ON CONFLICT (order_id) DO NOTHING;"
        )

    path.write_text("\n\n".join(statements) + "\n", encoding="utf-8")


def build_analytics_report(orders: list[Order]) -> dict:
    validation = validate_dataset(orders)
    if not validation["valid"]:
        raise ValueError(f"Dataset validation failed: {validation}")

    return {
        "dataset_validation": validation,
        "overall": aggregate_sales(orders),
        "regional_performance": group_metrics(orders, lambda o: o.region),
        "category_performance": category_metrics(orders),
        "monthly_performance": monthly_metrics(orders),
        "payment_method_performance": payment_metrics(orders),
        "discount_analysis": discount_analysis(orders),
        "top_customers": customer_metrics(orders)[:15],
        "revenue_outliers": detect_revenue_outliers(orders),
        "revenue_forecast": monthly_revenue_forecast(orders),
        "customer_cohorts": cohort_retention(orders),
        "inventory_demand_proxy": inventory_proxy(orders),
    }


def print_business_report(report: dict) -> None:
    overall = report["overall"]

    print("\nRETAIL BUSINESS PERFORMANCE")
    print("=" * 72)
    print(f"Transactions:          {overall['transaction_count']:,}")
    print(f"Returned transactions: {overall['returned_transactions']:,}")
    print(f"Recognized revenue:    {money(overall['recognized_revenue'])}")
    print(f"Recognized cost:       {money(overall['recognized_cost'])}")
    print(f"Profit:                {money(overall['profit'])}")
    print(f"Profit margin:         {overall['profit_margin']:.2%}")
    print(f"Average revenue/order: {money(overall['average_order_value'])}")
    print(f"Return rate:           {overall['return_rate']:.2%}")

    for title, key in [
        ("Regional performance", "regional_performance"),
        ("Product category performance", "category_performance"),
        ("Monthly performance", "monthly_performance"),
    ]:
        print(f"\n{title}")
        print("-" * 72)
        for row in report[key]:
            print(
                f"{row['group']:<18} "
                f"Revenue {money(row['recognized_revenue']):>13} "
                f"Profit {money(row['profit']):>13} "
                f"Margin {row['profit_margin']:>7.2%}"
            )

    print("\nHighest-value customers")
    print("-" * 72)
    for customer in report["top_customers"][:8]:
        print(
            f"{customer['customer_id']:<12} "
            f"{customer['segment']:<12} "
            f"Revenue {money(customer['revenue']):>12} "
            f"Profit {money(customer['profit']):>12}"
        )

    print("\nRevenue forecast")
    print("-" * 72)
    for row in report["revenue_forecast"]:
        print(f"{row['forecast_month']}: {money(row['forecast_revenue'])}")

    print(f"\nPotential revenue outliers: {len(report['revenue_outliers'])}")
    print("Outlier flags require business investigation, not automatic rejection.")


class AnalyticsTests(unittest.TestCase):
    def test_revenue_calculation(self):
        order = Order(
            "A", date(2025, 1, 1), "C1", "North", "Electronics", "Monitor",
            2, 100, 60, 0.10, "Card",
        )
        self.assertAlmostEqual(order.revenue, 180)
        self.assertAlmostEqual(order.profit, 60)

    def test_returned_order_excluded_from_recognized_sales(self):
        order = Order(
            "A", date(2025, 1, 1), "C1", "North", "Electronics", "Monitor",
            1, 100, 60, 0, "Card", True,
        )
        metrics = aggregate_sales([order])
        self.assertEqual(metrics["recognized_revenue"], 0)
        self.assertEqual(metrics["recognized_cost"], 0)

    def test_invalid_discount_rejected(self):
        order = Order(
            "A", date(2025, 1, 1), "C1", "North", "Electronics", "Monitor",
            1, 100, 60, 1.2, "Card",
        )
        self.assertTrue(validate_order(order))

    def test_duplicate_identifier_detected(self):
        order = Order(
            "A", date(2025, 1, 1), "C1", "North", "Electronics", "Monitor",
            1, 100, 60, 0, "Card",
        )
        result = validate_dataset([order, order])
        self.assertEqual(result["duplicate_order_ids"], ["A"])

    def test_forecast_requires_positive_horizon(self):
        with self.assertRaises(ValueError):
            monthly_revenue_forecast([], 0)

    def test_csv_round_trip(self):
        order = Order(
            "A", date(2025, 1, 1), "C1", "North", "Electronics", "Monitor",
            1, 100, 60, 0.05, "Card",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orders.csv"
            export_orders_csv([order], path)
            loaded = load_orders_csv(path)
            self.assertEqual(loaded, [order])


def run_tests() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AnalyticsTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Retail SQL analytics with a reproducible sample dataset."
    )
    parser.add_argument("--input", type=Path, help="Load transactions from CSV.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("retail_analytics_output"),
        help="Directory for generated reports and exports.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test", action="store_true", help="Run unit tests.")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    orders = (
        load_orders_csv(args.input)
        if args.input
        else create_business_dataset(args.seed)
    )

    report = build_analytics_report(orders)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    export_orders_csv(orders, args.output_dir / "retail_orders.csv")
    write_json(args.output_dir / "analytics_report.json", report)
    write_json(
        args.output_dir / "customer_metrics.json",
        customer_metrics(orders),
    )
    write_json(
        args.output_dir / "cohort_retention.json",
        cohort_retention(orders),
    )
    write_postgres_insert_script(
        orders,
        args.output_dir / "retail_orders_postgres.sql",
    )

    print_business_report(report)
    print(f"\nExports written to: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
