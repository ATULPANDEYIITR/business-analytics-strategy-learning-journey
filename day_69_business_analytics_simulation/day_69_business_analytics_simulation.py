#!/usr/bin/env python3
"""
Business Analytics Automation
Automated sales analysis, KPI computation, anomaly detection,
periodic reporting, data validation, and CSV/JSON report generation.

Python 3.10+
Standard-library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "sales_data.csv"
OUTPUT_DIR = BASE_DIR / "analytics_output"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("business_analytics")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: str
    transaction_date: date
    region: str
    product: str
    category: str
    quantity: int
    unit_price: float
    cost_per_unit: float

    @property
    def revenue(self) -> float:
        return self.quantity * self.unit_price

    @property
    def cost(self) -> float:
        return self.quantity * self.cost_per_unit

    @property
    def profit(self) -> float:
        return self.revenue - self.cost

    @property
    def margin(self) -> float:
        return self.profit / self.revenue if self.revenue else 0.0


@dataclass
class AnalyticsReport:
    generated_at: str
    total_transactions: int
    total_units: int
    total_revenue: float
    total_cost: float
    total_profit: float
    profit_margin_percent: float
    average_transaction_value: float
    regional_performance: dict[str, dict[str, float]]
    product_performance: dict[str, dict[str, float]]
    monthly_performance: dict[str, dict[str, float]]
    anomalies: list[dict[str, Any]]
    data_quality: dict[str, int]


class DataValidationError(Exception):
    """Raised when source records contain invalid business data."""


class AnalyticsPipeline:
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        anomaly_threshold: float = 2.0
    ):
        if anomaly_threshold <= 0:
            raise ValueError("Anomaly threshold must be positive.")

        self.input_file = input_file
        self.output_dir = output_dir
        self.anomaly_threshold = anomaly_threshold
        self.status = JobStatus.PENDING
        self.records: list[SalesRecord] = []
        self.quality = {
            "accepted": 0,
            "rejected": 0,
            "duplicates": 0
        }

    def create_sample_data(self) -> None:
        """Create reproducible sample data if the source does not exist."""
        if self.input_file.exists():
            return

        self.input_file.parent.mkdir(parents=True, exist_ok=True)

        rows = [
            ["T001", "2026-01-05", "North", "Laptop", "Electronics", 3, 75000, 60000],
            ["T002", "2026-01-08", "South", "Phone", "Electronics", 8, 25000, 18000],
            ["T003", "2026-01-12", "East", "Desk", "Furniture", 5, 12000, 8000],
            ["T004", "2026-02-03", "West", "Laptop", "Electronics", 4, 75000, 60000],
            ["T005", "2026-02-09", "North", "Chair", "Furniture", 10, 5000, 3000],
            ["T006", "2026-02-15", "South", "Phone", "Electronics", 12, 25000, 18000],
            ["T007", "2026-03-02", "East", "Desk", "Furniture", 7, 12000, 8000],
            ["T008", "2026-03-10", "West", "Laptop", "Electronics", 2, 75000, 60000],
            ["T009", "2026-03-18", "North", "Phone", "Electronics", 15, 25000, 18000],
            ["T010", "2026-03-22", "South", "Chair", "Furniture", 9, 5000, 3000],
            ["T011", "2026-04-04", "East", "Laptop", "Electronics", 30, 75000, 60000],
            ["T012", "2026-04-12", "West", "Desk", "Furniture", 6, 12000, 8000],
        ]

        with self.input_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "transaction_id", "transaction_date", "region",
                "product", "category", "quantity",
                "unit_price", "cost_per_unit"
            ])
            writer.writerows(rows)

        logger.info("Created sample sales dataset.")

    @staticmethod
    def parse_record(row: dict[str, str]) -> SalesRecord:
        required = [
            "transaction_id", "transaction_date", "region",
            "product", "category", "quantity",
            "unit_price", "cost_per_unit"
        ]

        if any(not row.get(field) for field in required):
            raise DataValidationError("Missing required field.")

        record = SalesRecord(
            transaction_id=row["transaction_id"].strip(),
            transaction_date=date.fromisoformat(row["transaction_date"]),
            region=row["region"].strip(),
            product=row["product"].strip(),
            category=row["category"].strip(),
            quantity=int(row["quantity"]),
            unit_price=float(row["unit_price"]),
            cost_per_unit=float(row["cost_per_unit"])
        )

        if not record.transaction_id:
            raise DataValidationError("Empty transaction ID.")

        if min(record.quantity, record.unit_price, record.cost_per_unit) < 0:
            raise DataValidationError("Negative sales values are invalid.")

        if not all([record.region, record.product, record.category]):
            raise DataValidationError("Empty business dimension.")

        if record.unit_price == 0 and record.quantity > 0:
            raise DataValidationError("Positive quantity requires a price.")

        return record

    def load_data(self) -> None:
        seen_ids: set[str] = set()

        if not self.input_file.exists():
            raise FileNotFoundError(self.input_file)

        with self.input_file.open(
            "r", newline="", encoding="utf-8-sig"
        ) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise DataValidationError("CSV has no header.")

            for line_number, row in enumerate(reader, start=2):
                try:
                    record = self.parse_record(row)

                    if record.transaction_id in seen_ids:
                        self.quality["duplicates"] += 1
                        self.quality["rejected"] += 1
                        logger.warning(
                            "Duplicate transaction at line %d.",
                            line_number
                        )
                        continue

                    seen_ids.add(record.transaction_id)
                    self.records.append(record)
                    self.quality["accepted"] += 1

                except (ValueError, TypeError, DataValidationError) as exc:
                    self.quality["rejected"] += 1
                    logger.warning(
                        "Rejected line %d: %s", line_number, exc
                    )

        if not self.records:
            raise DataValidationError("No valid transactions found.")

        logger.info("Loaded %d valid transactions.", len(self.records))

    @staticmethod
    def summarize(records: list[SalesRecord]) -> dict[str, float]:
        revenue = sum(r.revenue for r in records)
        cost = sum(r.cost for r in records)
        profit = revenue - cost
        quantity = sum(r.quantity for r in records)

        return {
            "transactions": len(records),
            "units": quantity,
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "profit": round(profit, 2),
            "margin_percent": round(
                profit / revenue * 100 if revenue else 0, 2
            )
        }

    def group_performance(
        self,
        key_function
    ) -> dict[str, dict[str, float]]:
        groups = defaultdict(list)

        for record in self.records:
            groups[key_function(record)].append(record)

        return {
            key: self.summarize(items)
            for key, items in sorted(groups.items())
        }

    def detect_anomalies(self) -> list[dict[str, Any]]:
        """
        Detect unusual transaction revenues using population
        standard deviation. This is a screening method, not
        a statistical proof of fraud or business error.
        """
        revenues = [r.revenue for r in self.records]

        if len(revenues) < 3:
            return []

        mean = statistics.mean(revenues)
        deviation = statistics.pstdev(revenues)

        if deviation == 0:
            return []

        anomalies = []

        for record in self.records:
            score = (record.revenue - mean) / deviation

            if abs(score) >= self.anomaly_threshold:
                anomalies.append({
                    "transaction_id": record.transaction_id,
                    "region": record.region,
                    "revenue": round(record.revenue, 2),
                    "z_score": round(score, 3),
                    "reason": "Unusual transaction revenue"
                })

        return anomalies

    def build_report(self) -> AnalyticsReport:
        summary = self.summarize(self.records)

        return AnalyticsReport(
            generated_at=datetime.now().astimezone().isoformat(),
            total_transactions=len(self.records),
            total_units=int(summary["units"]),
            total_revenue=summary["revenue"],
            total_cost=summary["cost"],
            total_profit=summary["profit"],
            profit_margin_percent=summary["margin_percent"],
            average_transaction_value=round(
                summary["revenue"] / len(self.records), 2
            ),
            regional_performance=self.group_performance(
                lambda r: r.region
            ),
            product_performance=self.group_performance(
                lambda r: r.product
            ),
            monthly_performance=self.group_performance(
                lambda r: r.transaction_date.strftime("%Y-%m")
            ),
            anomalies=self.detect_anomalies(),
            data_quality=self.quality.copy()
        )

    def save_report(self, report: AnalyticsReport) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        data = asdict(report)

        json_path = self.output_dir / "business_report.json"
        csv_path = self.output_dir / "regional_report.csv"
        text_path = self.output_dir / "business_report.txt"

        with json_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        with csv_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow([
                "region", "transactions", "units",
                "revenue", "cost", "profit", "margin_percent"
            ])

            for region, metrics in report.regional_performance.items():
                writer.writerow([
                    region,
                    metrics["transactions"],
                    metrics["units"],
                    metrics["revenue"],
                    metrics["cost"],
                    metrics["profit"],
                    metrics["margin_percent"]
                ])

        lines = [
            "BUSINESS ANALYTICS REPORT",
            "=" * 45,
            f"Generated: {report.generated_at}",
            f"Transactions: {report.total_transactions}",
            f"Units sold: {report.total_units}",
            f"Revenue: {report.total_revenue:,.2f}",
            f"Cost: {report.total_cost:,.2f}",
            f"Profit: {report.total_profit:,.2f}",
            f"Profit margin: {report.profit_margin_percent:.2f}%",
            f"Average transaction: {report.average_transaction_value:,.2f}",
            "",
            "REGIONAL PERFORMANCE",
            "-" * 45
        ]

        for region, metrics in report.regional_performance.items():
            lines.append(
                f"{region}: Revenue={metrics['revenue']:,.2f}, "
                f"Profit={metrics['profit']:,.2f}"
            )

        lines.extend([
            "",
            "ANOMALIES",
            "-" * 45
        ])

        if report.anomalies:
            for anomaly in report.anomalies:
                lines.append(str(anomaly))
        else:
            lines.append("No anomalies detected.")

        with text_path.open("w", encoding="utf-8") as file:
            file.write("\n".join(lines))

        logger.info("Reports saved to %s", self.output_dir)

    def run(self) -> AnalyticsReport:
        if self.status != JobStatus.PENDING:
            raise RuntimeError("Pipeline can only run once.")

        self.status = JobStatus.RUNNING

        try:
            self.create_sample_data()
            self.load_data()
            report = self.build_report()
            self.save_report(report)

            self.status = JobStatus.COMPLETED
            logger.info("Analytics pipeline completed.")
            return report

        except Exception:
            self.status = JobStatus.FAILED
            logger.exception("Analytics pipeline failed.")
            raise


def run_self_tests() -> None:
    sample = SalesRecord(
        "TEST", date(2026, 1, 1), "North",
        "Laptop", "Electronics", 2, 1000, 700
    )

    assert sample.revenue == 2000
    assert sample.cost == 1400
    assert sample.profit == 600
    assert round(sample.margin, 2) == 0.30

    assert AnalyticsPipeline.summarize([sample])["profit"] == 600

    try:
        AnalyticsPipeline.parse_record({
            "transaction_id": "BAD",
            "transaction_date": "2026-01-01",
            "region": "North",
            "product": "Laptop",
            "category": "Electronics",
            "quantity": "-2",
            "unit_price": "100",
            "cost_per_unit": "70"
        })
    except DataValidationError:
        pass
    else:
        raise AssertionError("Negative quantity should be rejected.")

    logger.info("All self-tests passed.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated business analytics pipeline."
    )
    parser.add_argument("--input", type=Path, default=INPUT_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_self_tests()
        return 0

    try:
        pipeline = AnalyticsPipeline(
            args.input, args.output, args.threshold
        )
        report = pipeline.run()

        print("\nBUSINESS ANALYTICS RESULTS")
        print("=" * 45)
        print(f"Revenue: {report.total_revenue:,.2f}")
        print(f"Profit: {report.total_profit:,.2f}")
        print(f"Margin: {report.profit_margin_percent:.2f}%")
        print(f"Transactions: {report.total_transactions}")
        print(f"Anomalies: {len(report.anomalies)}")
        print(f"Pipeline status: {pipeline.status.value}")

        return 0

    except (OSError, ValueError, RuntimeError, DataValidationError) as exc:
        logger.error("Execution error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
