from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Iterable
import csv
import json
import statistics


class DatasetState(Enum):
    CREATED = "Created"
    REFRESHED = "Refreshed"
    FAILED = "Refresh Failed"


class VisualType(Enum):
    CARD = "Card"
    TABLE = "Table"
    BAR_CHART = "Bar Chart"
    LINE_CHART = "Line Chart"
    SLICER = "Slicer"


@dataclass(frozen=True)
class Sale:
    sale_id: int
    sale_date: date
    region: str
    product: str
    category: str
    quantity: int
    unit_price: float
    customer_id: int

    @property
    def revenue(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Dataset:
    name: str
    rows: list[Sale] = field(default_factory=list)
    state: DatasetState = DatasetState.CREATED
    last_refresh: date | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Dataset name cannot be empty.")

        ids = set()
        for row in self.rows:
            if row.sale_id in ids:
                raise ValueError(f"Duplicate sale_id: {row.sale_id}")
            ids.add(row.sale_id)

            if row.quantity <= 0:
                raise ValueError(f"Invalid quantity for sale {row.sale_id}.")
            if row.unit_price < 0:
                raise ValueError(f"Negative unit price for sale {row.sale_id}.")
            if not row.region.strip() or not row.product.strip():
                raise ValueError(f"Missing dimensional data for sale {row.sale_id}.")

    def refresh(self) -> None:
        self.validate()
        self.state = DatasetState.REFRESHED
        self.last_refresh = date.today()

    def total_revenue(self) -> float:
        return sum(row.revenue for row in self.rows)

    def revenue_by_region(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for row in self.rows:
            result[row.region] = result.get(row.region, 0.0) + row.revenue
        return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))

    def revenue_by_category(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for row in self.rows:
            result[row.category] = result.get(row.category, 0.0) + row.revenue
        return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))


@dataclass
class Visual:
    title: str
    visual_type: VisualType
    measure: str
    dimension: str | None = None
    filter_region: str | None = None

    def render(self, dataset: Dataset) -> dict:
        rows = dataset.rows
        if self.filter_region:
            rows = [r for r in rows if r.region == self.filter_region]

        if self.measure == "Revenue":
            value = sum(r.revenue for r in rows)
        elif self.measure == "Quantity":
            value = sum(r.quantity for r in rows)
        else:
            raise ValueError(f"Unsupported measure: {self.measure}")

        result = {
            "title": self.title,
            "type": self.visual_type.value,
            "measure": self.measure,
            "value": round(value, 2),
        }

        if self.dimension == "Region":
            groups: dict[str, float] = {}
            for row in rows:
                metric = row.revenue if self.measure == "Revenue" else row.quantity
                groups[row.region] = groups.get(row.region, 0) + metric
            result["groups"] = dict(sorted(groups.items()))

        if self.dimension == "Category":
            groups = {}
            for row in rows:
                metric = row.revenue if self.measure == "Revenue" else row.quantity
                groups[row.category] = groups.get(row.category, 0) + metric
            result["groups"] = dict(sorted(groups.items()))

        return result


@dataclass
class ReportPage:
    name: str
    visuals: list[Visual] = field(default_factory=list)

    def render(self, dataset: Dataset) -> list[dict]:
        if dataset.state != DatasetState.REFRESHED:
            raise RuntimeError("Report cannot render an unrefreshed dataset.")
        return [visual.render(dataset) for visual in self.visuals]


@dataclass
class Report:
    name: str
    dataset: Dataset
    pages: list[ReportPage] = field(default_factory=list)

    def add_page(self, page: ReportPage) -> None:
        if not page.name.strip():
            raise ValueError("Report page name cannot be empty.")
        self.pages.append(page)

    def export_definition(self, path: str) -> None:
        payload = {
            "report": self.name,
            "dataset": self.dataset.name,
            "dataset_state": self.dataset.state.value,
            "pages": [
                {
                    "name": page.name,
                    "visuals": [
                        {
                            "title": v.title,
                            "type": v.visual_type.value,
                            "measure": v.measure,
                            "dimension": v.dimension,
                            "filter_region": v.filter_region,
                        }
                        for v in page.visuals
                    ],
                }
                for page in self.pages
            ],
        }

        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_sales_csv(path: str) -> list[Sale]:
    rows: list[Sale] = []

    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required = {
            "sale_id",
            "sale_date",
            "region",
            "product",
            "category",
            "quantity",
            "unit_price",
            "customer_id",
        }

        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV does not contain the required columns.")

        for raw in reader:
            rows.append(
                Sale(
                    sale_id=int(raw["sale_id"]),
                    sale_date=date.fromisoformat(raw["sale_date"]),
                    region=raw["region"].strip(),
                    product=raw["product"].strip(),
                    category=raw["category"].strip(),
                    quantity=int(raw["quantity"]),
                    unit_price=float(raw["unit_price"]),
                    customer_id=int(raw["customer_id"]),
                )
            )

    return rows


def build_sample_dataset() -> Dataset:
    rows = [
        Sale(1, date(2026, 1, 5), "North", "Laptop", "Computers", 2, 85000, 101),
        Sale(2, date(2026, 1, 12), "South", "Monitor", "Accessories", 5, 18000, 102),
        Sale(3, date(2026, 2, 2), "North", "Keyboard", "Accessories", 8, 3500, 103),
        Sale(4, date(2026, 2, 14), "West", "Laptop", "Computers", 1, 92000, 104),
        Sale(5, date(2026, 2, 21), "South", "Laptop", "Computers", 3, 87000, 105),
        Sale(6, date(2026, 3, 3), "East", "Monitor", "Accessories", 7, 17500, 106),
        Sale(7, date(2026, 3, 10), "West", "Keyboard", "Accessories", 10, 3200, 107),
        Sale(8, date(2026, 3, 18), "East", "Laptop", "Computers", 2, 88000, 108),
    ]
    return Dataset("Sales Analytics Dataset", rows)


def demonstrate() -> None:
    dataset = build_sample_dataset()

    try:
        dataset.refresh()
    except ValueError as exc:
        dataset.state = DatasetState.FAILED
        raise RuntimeError(f"Dataset refresh failed: {exc}") from exc

    report = Report("Regional Sales Report", dataset)

    overview = ReportPage(
        "Executive Overview",
        [
            Visual("Total Revenue", VisualType.CARD, "Revenue"),
            Visual("Revenue by Region", VisualType.BAR_CHART, "Revenue", "Region"),
            Visual("Quantity by Category", VisualType.TABLE, "Quantity", "Category"),
        ],
    )

    north_page = ReportPage(
        "North Analysis",
        [
            Visual(
                "North Revenue",
                VisualType.CARD,
                "Revenue",
                filter_region="North",
            )
        ],
    )

    report.add_page(overview)
    report.add_page(north_page)

    print("DATASET")
    print(f"Name: {dataset.name}")
    print(f"Rows: {len(dataset.rows)}")
    print(f"State: {dataset.state.value}")
    print(f"Revenue: {dataset.total_revenue():,.2f}")
    print()

    print("REGION ANALYSIS")
    for region, revenue in dataset.revenue_by_region().items():
        print(f"{region}: {revenue:,.2f}")
    print()

    print("REPORT")
    for page in report.pages:
        print(f"\n[{page.name}]")
        for visual in page.render(dataset):
            print(json.dumps(visual, indent=2))

    output = "power_bi_fundamentals_report_definition.json"
    report.export_definition(output)
    print(f"\nReport definition exported to {output}")

    # A useful data-quality edge case.
    invalid = Dataset(
        "Invalid Dataset",
        [Sale(99, date.today(), "North", "Broken", "Test", 0, 100, 1)],
    )
    try:
        invalid.refresh()
    except ValueError as exc:
        print(f"\nExpected validation failure: {exc}")

    revenue_values = [row.revenue for row in dataset.rows]
    print(f"\nRevenue median: {statistics.median(revenue_values):,.2f}")


if __name__ == "__main__":
    demonstrate()
