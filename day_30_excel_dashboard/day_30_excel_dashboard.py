"""
Executive Business Dashboard Data Engine

This self-contained Python program creates and analyzes the business data that
would feed an executive Excel dashboard. It demonstrates KPI calculation,
monthly trends, regional performance, product performance, variance analysis,
data validation, dashboard-ready summaries, CSV export, and Excel-compatible
workbook generation using only the Python standard library.

The program does not require third-party packages.
"""

from __future__ import annotations

import csv
import io
import math
import random
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Business data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SalesRecord:
    transaction_date: date
    region: str
    product: str
    channel: str
    units: int
    revenue: float
    cost: float

    @property
    def gross_profit(self) -> float:
        return self.revenue - self.cost

    @property
    def margin(self) -> float:
        return self.gross_profit / self.revenue if self.revenue else 0.0


@dataclass
class DashboardKPI:
    revenue: float
    cost: float
    gross_profit: float
    margin: float
    units: int
    transactions: int
    average_transaction_value: float


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_REGIONS = {"North", "South", "East", "West"}
VALID_CHANNELS = {"Direct", "Online", "Partner"}
VALID_PRODUCTS = {"Cloud Suite", "Analytics Pro", "Security Platform", "Data Hub"}


def validate_record(record: SalesRecord) -> None:
    """Reject records that would corrupt dashboard calculations."""
    if record.region not in VALID_REGIONS:
        raise ValueError(f"Unknown region: {record.region}")

    if record.channel not in VALID_CHANNELS:
        raise ValueError(f"Unknown channel: {record.channel}")

    if record.product not in VALID_PRODUCTS:
        raise ValueError(f"Unknown product: {record.product}")

    if record.units <= 0:
        raise ValueError("Units must be greater than zero.")

    if record.revenue < 0:
        raise ValueError("Revenue cannot be negative.")

    if record.cost < 0:
        raise ValueError("Cost cannot be negative.")

    if record.cost > record.revenue:
        raise ValueError(
            "Cost cannot exceed revenue in this simplified business model."
        )


def validate_dataset(records: Iterable[SalesRecord]) -> list[SalesRecord]:
    """Validate every row and return a concrete list for repeated analysis."""
    validated = list(records)

    if not validated:
        raise ValueError("The dashboard cannot be built from an empty dataset.")

    for record in validated:
        validate_record(record)

    return validated


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

def generate_sales_data(
    start_date: date,
    end_date: date,
    seed: int = 42,
) -> list[SalesRecord]:
    """
    Generate realistic business transactions.

    The data contains seasonal revenue variation, regional differences,
    product-level economics, and channel-level pricing effects so that the
    resulting dashboard has meaningful patterns to analyze.
    """
    if end_date < start_date:
        raise ValueError("end_date must not be earlier than start_date.")

    rng = random.Random(seed)

    region_factor = {
        "North": 1.10,
        "South": 0.94,
        "East": 1.04,
        "West": 1.18,
    }

    product_price = {
        "Cloud Suite": 4200,
        "Analytics Pro": 3600,
        "Security Platform": 5100,
        "Data Hub": 2900,
    }

    product_margin = {
        "Cloud Suite": 0.61,
        "Analytics Pro": 0.56,
        "Security Platform": 0.64,
        "Data Hub": 0.49,
    }

    channel_factor = {
        "Direct": 1.00,
        "Online": 0.91,
        "Partner": 0.96,
    }

    records: list[SalesRecord] = []
    current = start_date

    while current <= end_date:
        # Month-end demand is deliberately stronger to create a useful
        # executive trend chart and variance analysis.
        month_end_boost = 1.18 if current.day >= 24 else 1.0

        for _ in range(rng.randint(2, 5)):
            region = rng.choice(sorted(VALID_REGIONS))
            product = rng.choice(sorted(VALID_PRODUCTS))
            channel = rng.choice(sorted(VALID_CHANNELS))

            units = rng.randint(2, 14)

            base_revenue = (
                product_price[product]
                * units
                * region_factor[region]
                * channel_factor[channel]
                * month_end_boost
            )

            revenue = round(base_revenue * rng.uniform(0.90, 1.12), 2)
            margin = product_margin[product] * rng.uniform(0.94, 1.05)
            cost = round(revenue * (1 - margin), 2)

            records.append(
                SalesRecord(
                    transaction_date=current,
                    region=region,
                    product=product,
                    channel=channel,
                    units=units,
                    revenue=revenue,
                    cost=cost,
                )
            )

        current += timedelta(days=1)

    return validate_dataset(records)


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def calculate_kpis(records: Iterable[SalesRecord]) -> DashboardKPI:
    records = validate_dataset(records)

    revenue = sum(r.revenue for r in records)
    cost = sum(r.cost for r in records)
    gross_profit = revenue - cost
    units = sum(r.units for r in records)
    transactions = len(records)

    return DashboardKPI(
        revenue=revenue,
        cost=cost,
        gross_profit=gross_profit,
        margin=gross_profit / revenue if revenue else 0.0,
        units=units,
        transactions=transactions,
        average_transaction_value=revenue / transactions if transactions else 0.0,
    )


def group_revenue(
    records: Iterable[SalesRecord],
    attribute: str,
) -> dict[str, float]:
    """Aggregate revenue by a dashboard dimension such as region or product."""
    records = validate_dataset(records)

    result: dict[str, float] = {}

    for record in records:
        key = getattr(record, attribute)
        result[key] = result.get(key, 0.0) + record.revenue

    return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


def group_profit_margin(
    records: Iterable[SalesRecord],
    attribute: str,
) -> dict[str, tuple[float, float]]:
    """
    Calculate revenue and weighted margin by a dimension.

    Weighted margin is preferable to averaging row-level percentages because
    larger transactions should contribute proportionally to the result.
    """
    records = validate_dataset(records)

    totals: dict[str, list[float]] = {}

    for record in records:
        key = getattr(record, attribute)

        if key not in totals:
            totals[key] = [0.0, 0.0]

        totals[key][0] += record.revenue
        totals[key][1] += record.gross_profit

    return {
        key: (
            revenue,
            profit / revenue if revenue else 0.0,
        )
        for key, (revenue, profit) in sorted(
            totals.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )
    }


def monthly_summary(
    records: Iterable[SalesRecord],
) -> list[dict[str, float | str]]:
    """Create the dataset behind the dashboard's monthly trend visuals."""
    records = validate_dataset(records)

    grouped: dict[str, dict[str, float]] = {}

    for record in records:
        month = record.transaction_date.strftime("%Y-%m")

        if month not in grouped:
            grouped[month] = {
                "revenue": 0.0,
                "cost": 0.0,
                "units": 0.0,
            }

        grouped[month]["revenue"] += record.revenue
        grouped[month]["cost"] += record.cost
        grouped[month]["units"] += record.units

    rows: list[dict[str, float | str]] = []

    for month, values in sorted(grouped.items()):
        revenue = values["revenue"]
        cost = values["cost"]
        profit = revenue - cost

        rows.append(
            {
                "month": month,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "gross_profit": round(profit, 2),
                "margin": round(profit / revenue, 4) if revenue else 0.0,
                "units": int(values["units"]),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Target and variance analysis
# ---------------------------------------------------------------------------

def create_monthly_targets(
    summaries: list[dict[str, float | str]],
    growth_rate: float = 0.08,
) -> dict[str, float]:
    """
    Create a simple management target model.

    Targets are deliberately independent from actual revenue so that variance
    is meaningful rather than being calculated against the same value.
    """
    targets: dict[str, float] = {}

    previous_target = None

    for index, row in enumerate(summaries):
        actual = float(row["revenue"])

        if previous_target is None:
            target = actual * 0.97
        else:
            target = previous_target * (1 + growth_rate / 12)

        # Introduce a modest management planning adjustment in alternating
        # months rather than making every target identical.
        if index % 3 == 2:
            target *= 1.03

        targets[str(row["month"])] = round(target, 2)
        previous_target = target

    return targets


def variance_report(
    summaries: list[dict[str, float | str]],
    targets: dict[str, float],
) -> list[dict[str, float | str]]:
    """Calculate actual-vs-target variance used by an executive dashboard."""
    report: list[dict[str, float | str]] = []

    for row in summaries:
        month = str(row["month"])
        actual = float(row["revenue"])
        target = targets.get(month, 0.0)
        variance = actual - target
        variance_pct = variance / target if target else 0.0

        report.append(
            {
                "month": month,
                "actual": round(actual, 2),
                "target": round(target, 2),
                "variance": round(variance, 2),
                "variance_pct": round(variance_pct, 4),
                "status": "Above Target" if variance >= 0 else "Below Target",
            }
        )

    return report


# ---------------------------------------------------------------------------
# Dashboard-specific derived metrics
# ---------------------------------------------------------------------------

def top_performer(records: list[SalesRecord], attribute: str) -> tuple[str, float]:
    grouped = group_revenue(records, attribute)

    if not grouped:
        raise ValueError("Cannot determine a performer from an empty dataset.")

    return next(iter(grouped.items()))


def concentration_ratio(records: list[SalesRecord], attribute: str) -> float:
    """
    Measure how much revenue is represented by the largest category.

    This is useful for executive risk analysis because a high concentration
    means overall revenue depends heavily on a small number of categories.
    """
    grouped = group_revenue(records, attribute)
    total = sum(grouped.values())

    if not total:
        return 0.0

    largest = max(grouped.values())
    return largest / total


def correlation(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation used to examine revenue and units relationships."""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Correlation requires paired samples.")

    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys)
    )

    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))

    denominator = denominator_x * denominator_y

    return numerator / denominator if denominator else 0.0


# ---------------------------------------------------------------------------
# Excel-compatible CSV exports
# ---------------------------------------------------------------------------

def records_to_csv(records: list[SalesRecord]) -> str:
    """Produce a clean transaction table that Excel can open directly."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(
        [
            "Transaction Date",
            "Region",
            "Product",
            "Channel",
            "Units",
            "Revenue",
            "Cost",
            "Gross Profit",
            "Margin",
        ]
    )

    for record in records:
        writer.writerow(
            [
                record.transaction_date.isoformat(),
                record.region,
                record.product,
                record.channel,
                record.units,
                f"{record.revenue:.2f}",
                f"{record.cost:.2f}",
                f"{record.gross_profit:.2f}",
                f"{record.margin:.4f}",
            ]
        )

    return buffer.getvalue()


def write_dashboard_exports(
    records: list[SalesRecord],
    output_dir: Path,
) -> None:
    """Write dashboard-ready tables for direct import into Excel."""
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "sales_data.csv").write_text(
        records_to_csv(records),
        encoding="utf-8",
        newline="",
    )

    monthly = monthly_summary(records)
    targets = create_monthly_targets(monthly)
    variance = variance_report(monthly, targets)

    with (output_dir / "monthly_dashboard.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "month",
                "revenue",
                "cost",
                "gross_profit",
                "margin",
                "units",
            ],
        )
        writer.writeheader()
        writer.writerows(monthly)

    with (output_dir / "variance_dashboard.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "month",
                "actual",
                "target",
                "variance",
                "variance_pct",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(variance)


# ---------------------------------------------------------------------------
# Console dashboard
# ---------------------------------------------------------------------------

def print_currency(value: float) -> str:
    return f"${value:,.2f}"


def print_dashboard(records: list[SalesRecord]) -> None:
    kpis = calculate_kpis(records)
    monthly = monthly_summary(records)
    targets = create_monthly_targets(monthly)
    variance = variance_report(monthly, targets)

    best_region, best_region_revenue = top_performer(records, "region")
    best_product, best_product_revenue = top_performer(records, "product")

    print("\nEXECUTIVE BUSINESS DASHBOARD")
    print("=" * 72)

    print(f"Revenue              {print_currency(kpis.revenue)}")
    print(f"Gross Profit         {print_currency(kpis.gross_profit)}")
    print(f"Gross Margin         {kpis.margin:.1%}")
    print(f"Units Sold           {kpis.units:,}")
    print(f"Transactions         {kpis.transactions:,}")
    print(f"Average Transaction  {print_currency(kpis.average_transaction_value)}")

    print("\nPERFORMANCE BY REGION")
    print("-" * 72)

    for region, (revenue, margin) in group_profit_margin(records, "region").items():
        print(
            f"{region:<12}"
            f"Revenue {print_currency(revenue):>15}"
            f"  Margin {margin:>7.1%}"
        )

    print("\nPERFORMANCE BY PRODUCT")
    print("-" * 72)

    for product, (revenue, margin) in group_profit_margin(records, "product").items():
        print(
            f"{product:<22}"
            f"Revenue {print_currency(revenue):>15}"
            f"  Margin {margin:>7.1%}"
        )

    print("\nMONTHLY TARGET VARIANCE")
    print("-" * 72)

    for row in variance:
        print(
            f"{row['month']}  "
            f"Actual {print_currency(float(row['actual'])):>15}  "
            f"Target {print_currency(float(row['target'])):>15}  "
            f"Variance {print_currency(float(row['variance'])):>15}  "
            f"{row['status']}"
        )

    print("\nEXECUTIVE SIGNALS")
    print("-" * 72)

    print(
        f"Top region: {best_region} "
        f"({print_currency(best_region_revenue)} revenue)"
    )
    print(
        f"Top product: {best_product} "
        f"({print_currency(best_product_revenue)} revenue)"
    )
    print(
        f"Revenue concentration in largest region: "
        f"{concentration_ratio(records, 'region'):.1%}"
    )

    revenue_values = [r.revenue for r in records]
    unit_values = [float(r.units) for r in records]

    print(
        f"Revenue/units correlation: "
        f"{correlation(revenue_values, unit_values):.3f}"
    )


# ---------------------------------------------------------------------------
# Demonstration and failure testing
# ---------------------------------------------------------------------------

def demonstrate_validation() -> None:
    """Show how invalid source data should be rejected before aggregation."""
    invalid = SalesRecord(
        transaction_date=date(2026, 1, 1),
        region="Unknown Region",
        product="Cloud Suite",
        channel="Direct",
        units=3,
        revenue=10000,
        cost=4000,
    )

    try:
        validate_record(invalid)
    except ValueError as error:
        print("\nVALIDATION TEST")
        print(f"Rejected invalid dashboard row: {error}")


def main() -> None:
    start = date(2026, 1, 1)
    end = date(2026, 6, 30)

    records = generate_sales_data(start, end)

    print_dashboard(records)
    demonstrate_validation()

    output_directory = Path("excel_dashboard_exports")
    write_dashboard_exports(records, output_directory)

    print("\nEXPORTS")
    print("-" * 72)
    print(f"Dashboard-ready CSV files written to: {output_directory.resolve()}")
    print("sales_data.csv contains the normalized transaction source.")
    print("monthly_dashboard.csv contains trend and KPI calculation inputs.")
    print("variance_dashboard.csv contains actual-versus-target analysis.")


if __name__ == "__main__":
    main()
