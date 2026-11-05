from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("business_visualization")

OUTPUT_DIR = Path("business_reports")
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class MonthlyPerformance:
    month: str
    revenue: float
    expenses: float
    orders: int
    customers: int
    target: float

    @property
    def profit(self) -> float:
        return self.revenue - self.expenses

    @property
    def profit_margin(self) -> float:
        return self.profit / self.revenue * 100 if self.revenue else 0.0

    @property
    def target_achievement(self) -> float:
        return self.revenue / self.target * 100 if self.target else 0.0


class DataValidationError(ValueError):
    pass


def validate_records(records: Iterable[MonthlyPerformance]) -> list[MonthlyPerformance]:
    records = list(records)

    if not records:
        raise DataValidationError("At least one performance record is required.")

    months = set()

    for record in records:
        if record.month in months:
            raise DataValidationError(f"Duplicate month: {record.month}")

        months.add(record.month)

        if not record.month.strip():
            raise DataValidationError("Month cannot be empty.")

        if record.revenue < 0 or record.expenses < 0:
            raise DataValidationError("Revenue and expenses cannot be negative.")

        if record.orders < 0 or record.customers < 0:
            raise DataValidationError("Orders and customers cannot be negative.")

        if record.target <= 0:
            raise DataValidationError("Revenue target must be positive.")

        if record.customers > record.orders and record.orders > 0:
            raise DataValidationError(
                "Customer count cannot exceed order count in this dataset."
            )

    return records


def currency(value: float) -> str:
    return f"₹{value:,.0f}"


def save_csv(records: list[MonthlyPerformance]) -> Path:
    path = OUTPUT_DIR / "monthly_performance.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "month",
                "revenue",
                "expenses",
                "profit",
                "orders",
                "customers",
                "profit_margin",
                "target",
                "target_achievement"
            ]
        )
        writer.writeheader()

        for item in records:
            writer.writerow({
                "month": item.month,
                "revenue": item.revenue,
                "expenses": item.expenses,
                "profit": item.profit,
                "orders": item.orders,
                "customers": item.customers,
                "profit_margin": round(item.profit_margin, 2),
                "target": item.target,
                "target_achievement": round(item.target_achievement, 2)
            })

    return path


def create_revenue_chart(records: list[MonthlyPerformance]) -> None:
    months = [r.month for r in records]
    revenue = [r.revenue for r in records]
    target = [r.target for r in records]

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(months))
    width = 0.36

    bars = ax.bar(
        x - width / 2,
        revenue,
        width,
        label="Actual Revenue"
    )

    ax.bar(
        x + width / 2,
        target,
        width,
        label="Revenue Target",
        alpha=0.65
    )

    ax.bar_label(
        bars,
        labels=[currency(value) for value in revenue],
        padding=3,
        fontsize=8
    )

    ax.set_title("Monthly Revenue Performance", fontsize=15, weight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (INR)")
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"₹{value / 1000:.0f}K")
    )
    ax.legend()
    ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "revenue_performance.png", dpi=160)
    plt.close(fig)


def create_profitability_chart(records: list[MonthlyPerformance]) -> None:
    months = [r.month for r in records]
    profit = [r.profit for r in records]
    margins = [r.profit_margin for r in records]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.bar(months, profit, alpha=0.75, label="Profit")
    ax1.set_ylabel("Profit (INR)")
    ax1.set_title("Profitability and Profit Margin")
    ax1.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"₹{value / 1000:.0f}K")
    )
    ax1.axhline(0, linewidth=0.8)

    ax2 = ax1.twinx()
    ax2.plot(
        months,
        margins,
        marker="o",
        linewidth=2,
        label="Profit Margin"
    )
    ax2.set_ylabel("Profit Margin (%)")

    ax1.grid(axis="y", alpha=0.2)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "profitability_analysis.png", dpi=160)
    plt.close(fig)


def create_expense_chart(records: list[MonthlyPerformance]) -> None:
    months = [r.month for r in records]
    revenue = np.array([r.revenue for r in records])
    expenses = np.array([r.expenses for r in records])

    expense_ratio = np.divide(
        expenses,
        revenue,
        out=np.zeros_like(expenses),
        where=revenue != 0
    ) * 100

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        months,
        expense_ratio,
        marker="s",
        linewidth=2,
        label="Expense-to-Revenue Ratio"
    )

    ax.axhline(
        70,
        linestyle="--",
        alpha=0.7,
        label="70% Reference Level"
    )

    ax.set_title("Operating Expense Efficiency")
    ax.set_xlabel("Month")
    ax.set_ylabel("Expenses / Revenue (%)")
    ax.legend()
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "expense_efficiency.png", dpi=160)
    plt.close(fig)


def create_orders_chart(records: list[MonthlyPerformance]) -> None:
    months = [r.month for r in records]
    orders = [r.orders for r in records]
    customers = [r.customers for r in records]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(months, orders, marker="o", label="Orders")
    ax.plot(months, customers, marker="s", label="Customers")

    ax.set_title("Customer and Order Trends")
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "customer_order_trends.png", dpi=160)
    plt.close(fig)


def create_correlation_heatmap(records: list[MonthlyPerformance]) -> None:
    metrics = np.array([
        [r.revenue for r in records],
        [r.expenses for r in records],
        [r.profit for r in records],
        [r.orders for r in records],
        [r.customers for r in records],
        [r.profit_margin for r in records]
    ], dtype=float)

    labels = [
        "Revenue",
        "Expenses",
        "Profit",
        "Orders",
        "Customers",
        "Margin"
    ]

    correlation = np.corrcoef(metrics)

    # Correlation is undefined for constant columns.
    correlation = np.nan_to_num(correlation, nan=0.0)

    fig, ax = plt.subplots(figsize=(9, 7))

    image = ax.imshow(
        correlation,
        cmap="coolwarm",
        vmin=-1,
        vmax=1
    )

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticklabels(labels)

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j,
                i,
                f"{correlation[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=9
            )

    ax.set_title("Business Metric Correlation")
    fig.colorbar(image, ax=ax, label="Correlation")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "correlation_heatmap.png", dpi=160)
    plt.close(fig)


def create_executive_dashboard(records: list[MonthlyPerformance]) -> None:
    total_revenue = sum(r.revenue for r in records)
    total_expenses = sum(r.expenses for r in records)
    total_profit = total_revenue - total_expenses
    total_orders = sum(r.orders for r in records)
    total_customers = sum(r.customers for r in records)
    average_margin = (
        total_profit / total_revenue * 100
        if total_revenue else 0
    )

    months = [r.month for r in records]
    revenue = [r.revenue for r in records]
    expenses = [r.expenses for r in records]
    targets = [r.target for r in records]

    fig = plt.figure(figsize=(15, 10))
    grid = fig.add_gridspec(3, 2)

    fig.suptitle(
        "Executive Business Performance Dashboard",
        fontsize=18,
        weight="bold"
    )

    ax1 = fig.add_subplot(grid[0, :])
    ax1.plot(months, revenue, marker="o", label="Revenue")
    ax1.plot(months, targets, linestyle="--", label="Target")
    ax1.plot(months, expenses, marker="s", label="Expenses")
    ax1.set_title("Revenue, Target and Expenses")
    ax1.legend()
    ax1.grid(alpha=0.2)

    ax2 = fig.add_subplot(grid[1, 0])
    ax2.bar(months, [r.profit for r in records])
    ax2.set_title("Monthly Profit")
    ax2.axhline(0, color="black", linewidth=0.8)

    ax3 = fig.add_subplot(grid[1, 1])
    ax3.bar(
        months,
        [r.target_achievement for r in records]
    )
    ax3.axhline(100, linestyle="--")
    ax3.set_title("Target Achievement (%)")
    ax3.set_ylabel("%")

    ax4 = fig.add_subplot(grid[2, :])
    ax4.axis("off")

    kpis = [
        ("Total Revenue", currency(total_revenue)),
        ("Total Expenses", currency(total_expenses)),
        ("Net Profit", currency(total_profit)),
        ("Profit Margin", f"{average_margin:.2f}%"),
        ("Orders", f"{total_orders:,}"),
        ("Customers", f"{total_customers:,}")
    ]

    for index, (label, value) in enumerate(kpis):
        column = index % 3
        row = index // 3

        ax4.text(
            0.08 + column * 0.32,
            0.75 - row * 0.45,
            f"{label}\n{value}",
            transform=ax4.transAxes,
            ha="center",
            va="center",
            fontsize=13,
            bbox={
                "boxstyle": "round,pad=0.7",
                "facecolor": "white",
                "edgecolor": "gray"
            }
        )

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUTPUT_DIR / "executive_dashboard.png", dpi=160)
    plt.close(fig)


def print_business_report(records: list[MonthlyPerformance]) -> None:
    revenue = sum(r.revenue for r in records)
    expenses = sum(r.expenses for r in records)
    profit = revenue - expenses

    print("\nBUSINESS PERFORMANCE REPORT")
    print("=" * 55)
    print(f"Reporting periods : {len(records)}")
    print(f"Total revenue     : {currency(revenue)}")
    print(f"Total expenses    : {currency(expenses)}")
    print(f"Net profit        : {currency(profit)}")
    print(
        f"Profit margin     : "
        f"{profit / revenue * 100 if revenue else 0:.2f}%"
    )

    best = max(records, key=lambda r: r.profit)
    worst = min(records, key=lambda r: r.profit)

    print(f"Best profit month : {best.month}")
    print(f"Lowest profit     : {worst.month}")

    print("\nTARGET PERFORMANCE")
    for record in records:
        status = (
            "ACHIEVED"
            if record.revenue >= record.target
            else "BELOW TARGET"
        )
        print(
            f"{record.month:12} "
            f"{record.target_achievement:7.2f}% "
            f"{status}"
        )


def run_assertions(records: list[MonthlyPerformance]) -> None:
    for record in records:
        assert abs(
            record.profit - (record.revenue - record.expenses)
        ) < 0.001

        assert record.profit_margin >= 0 or record.profit < 0

    assert sum(r.revenue for r in records) > 0


def main() -> None:
    records = [
        MonthlyPerformance("January", 450000, 310000, 420, 350, 430000),
        MonthlyPerformance("February", 480000, 325000, 450, 370, 450000),
        MonthlyPerformance("March", 520000, 340000, 490, 395, 500000),
        MonthlyPerformance("April", 495000, 350000, 465, 380, 510000),
        MonthlyPerformance("May", 560000, 365000, 530, 425, 530000),
        MonthlyPerformance("June", 590000, 375000, 560, 445, 550000),
        MonthlyPerformance("July", 610000, 390000, 580, 460, 580000),
        MonthlyPerformance("August", 575000, 385000, 550, 440, 590000),
        MonthlyPerformance("September", 650000, 405000, 610, 490, 620000),
        MonthlyPerformance("October", 680000, 420000, 640, 510, 650000),
        MonthlyPerformance("November", 710000, 440000, 670, 535, 680000),
        MonthlyPerformance("December", 780000, 465000, 740, 590, 720000)
    ]

    try:
        records = validate_records(records)
        run_assertions(records)

        csv_path = save_csv(records)

        create_revenue_chart(records)
        create_profitability_chart(records)
        create_expense_chart(records)
        create_orders_chart(records)
        create_correlation_heatmap(records)
        create_executive_dashboard(records)

        print_business_report(records)

        print(f"\nCSV saved: {csv_path}")
        print(f"Charts saved in: {OUTPUT_DIR.resolve()}")

    except (DataValidationError, OSError, ValueError) as error:
        logger.exception("Business visualization failed: %s", error)
        raise


if __name__ == "__main__":
    main()
