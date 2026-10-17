from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from collections import Counter, defaultdict
from math import sqrt
from statistics import mean
from typing import Iterable, Sequence


class SegmentDimension(str, Enum):
    CUSTOMER = "customer"
    PRODUCT = "product"
    GEOGRAPHIC = "geographic"
    BEHAVIORAL = "behavioral"


@dataclass(frozen=True)
class Customer:
    customer_id: str
    age: int
    annual_income: float
    region: str
    city: str
    preferred_category: str
    loyalty_tier: str
    acquisition_channel: str


@dataclass(frozen=True)
class Product:
    product_id: str
    category: str
    price: float
    margin: float
    product_family: str


@dataclass(frozen=True)
class Purchase:
    customer_id: str
    product_id: str
    quantity: int
    unit_price: float
    timestamp: str
    channel: str

    @property
    def value(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Segment:
    name: str
    dimension: SegmentDimension
    members: set[str] = field(default_factory=set)
    description: str = ""


class SegmentationEngine:
    """
    A practical segmentation engine covering four distinct dimensions.

    Customer segmentation describes who customers are.
    Product segmentation describes what products represent.
    Geographic segmentation describes where demand originates.
    Behavioral segmentation describes what customers actually do.
    """

    def __init__(
        self,
        customers: Sequence[Customer],
        products: Sequence[Product],
        purchases: Sequence[Purchase],
    ) -> None:
        self.customers = {c.customer_id: c for c in customers}
        self.products = {p.product_id: p for p in products}
        self.purchases = list(purchases)
        self._validate_data()

    def _validate_data(self) -> None:
        if not self.customers:
            raise ValueError("At least one customer is required.")
        if not self.products:
            raise ValueError("At least one product is required.")

        for customer in self.customers.values():
            if customer.age < 18:
                raise ValueError(f"Customer {customer.customer_id} has an invalid age.")
            if customer.annual_income < 0:
                raise ValueError(
                    f"Customer {customer.customer_id} has negative income."
                )

        for product in self.products.values():
            if product.price < 0 or product.margin < 0:
                raise ValueError(f"Product {product.product_id} has invalid pricing.")

        for purchase in self.purchases:
            if purchase.customer_id not in self.customers:
                raise ValueError(f"Unknown customer: {purchase.customer_id}")
            if purchase.product_id not in self.products:
                raise ValueError(f"Unknown product: {purchase.product_id}")
            if purchase.quantity <= 0:
                raise ValueError("Purchase quantity must be positive.")
            if purchase.unit_price < 0:
                raise ValueError("Purchase price cannot be negative.")

    def customer_segments(self) -> list[Segment]:
        """
        Customer segmentation uses demographic and economic attributes.
        The rules are intentionally different from behavioral segmentation.
        """
        segments = [
            Segment(
                "young_professionals",
                SegmentDimension.CUSTOMER,
                description="Adults aged 18-34 with income above the dataset median.",
            ),
            Segment(
                "established_high_income",
                SegmentDimension.CUSTOMER,
                description="Customers aged 35+ with high annual income.",
            ),
            Segment(
                "value_conscious",
                SegmentDimension.CUSTOMER,
                description="Customers below the median annual income.",
            ),
        ]

        median_income = self._median(
            customer.annual_income for customer in self.customers.values()
        )

        for customer in self.customers.values():
            if customer.age <= 34 and customer.annual_income >= median_income:
                segments[0].members.add(customer.customer_id)

            if customer.age >= 35 and customer.annual_income > median_income:
                segments[1].members.add(customer.customer_id)

            if customer.annual_income < median_income:
                segments[2].members.add(customer.customer_id)

        return segments

    def product_segments(self) -> list[Segment]:
        """
        Product segmentation uses product economics and product hierarchy.
        It does not infer customer behavior.
        """
        segments = [
            Segment(
                "premium_products",
                SegmentDimension.PRODUCT,
                description="Products priced above the portfolio median.",
            ),
            Segment(
                "high_margin_products",
                SegmentDimension.PRODUCT,
                description="Products with a margin of at least 30%.",
            ),
            Segment(
                "essential_products",
                SegmentDimension.PRODUCT,
                description="Products belonging to essential-use families.",
            ),
        ]

        median_price = self._median(p.price for p in self.products.values())

        for product in self.products.values():
            if product.price > median_price:
                segments[0].members.add(product.product_id)

            if product.margin >= 0.30:
                segments[1].members.add(product.product_id)

            if product.product_family.lower() in {
                "essential",
                "household",
                "daily_needs",
            }:
                segments[2].members.add(product.product_id)

        return segments

    def geographic_segments(self) -> list[Segment]:
        """
        Geographic segmentation groups customers by physical market.
        City and region are treated as geographic attributes rather than
        proxies for customer income or behavior.
        """
        region_members: dict[str, set[str]] = defaultdict(set)

        for customer in self.customers.values():
            region_members[customer.region].add(customer.customer_id)

        return [
            Segment(
                f"region_{region.lower().replace(' ', '_')}",
                SegmentDimension.GEOGRAPHIC,
                members=members,
                description=f"Customers located in {region}.",
            )
            for region, members in sorted(region_members.items())
        ]

    def behavioral_segments(self) -> list[Segment]:
        """
        Behavioral segmentation is derived from observed transactions.

        RFM-style measures:
        - Recency: days since the latest purchase in the supplied period.
        - Frequency: number of transactions.
        - Monetary: total purchase value.

        The sample data uses a fixed reference date so the program is
        deterministic and reproducible.
        """
        reference_date = "2026-10-17"
        metrics = self._behavioral_metrics(reference_date)

        monetary_values = [m["monetary"] for m in metrics.values()]
        frequency_values = [m["frequency"] for m in metrics.values()]

        median_monetary = self._median(monetary_values)
        median_frequency = self._median(frequency_values)

        segments = {
            "loyal_high_value": Segment(
                "loyal_high_value",
                SegmentDimension.BEHAVIORAL,
                description="Frequent customers with above-median monetary value.",
            ),
            "recent_low_frequency": Segment(
                "recent_low_frequency",
                SegmentDimension.BEHAVIORAL,
                description="Recently active customers with below-median frequency.",
            ),
            "at_risk": Segment(
                "at_risk",
                SegmentDimension.BEHAVIORAL,
                description="Customers whose most recent transaction is relatively old.",
            ),
        }

        for customer_id, metric in metrics.items():
            if (
                metric["frequency"] >= median_frequency
                and metric["monetary"] >= median_monetary
            ):
                segments["loyal_high_value"].members.add(customer_id)

            if (
                metric["recency"] <= 30
                and metric["frequency"] < median_frequency
            ):
                segments["recent_low_frequency"].members.add(customer_id)

            if metric["recency"] > 60:
                segments["at_risk"].members.add(customer_id)

        return list(segments.values())

    def _behavioral_metrics(self, reference_date: str) -> dict[str, dict[str, float]]:
        from datetime import date

        reference = date.fromisoformat(reference_date)
        grouped: dict[str, list[Purchase]] = defaultdict(list)

        for purchase in self.purchases:
            grouped[purchase.customer_id].append(purchase)

        result: dict[str, dict[str, float]] = {}

        for customer_id in self.customers:
            transactions = grouped.get(customer_id, [])

            if not transactions:
                result[customer_id] = {
                    "recency": float("inf"),
                    "frequency": 0,
                    "monetary": 0.0,
                }
                continue

            dates = [date.fromisoformat(p.timestamp) for p in transactions]
            latest = max(dates)

            result[customer_id] = {
                "recency": float((reference - latest).days),
                "frequency": float(len(transactions)),
                "monetary": sum(p.value for p in transactions),
            }

        return result

    def cross_dimension_profile(self, customer_id: str) -> dict[str, object]:
        """
        Combines independent segment assignments without confusing
        segmentation dimensions with one another.
        """
        if customer_id not in self.customers:
            raise KeyError(f"Unknown customer: {customer_id}")

        customer = self.customers[customer_id]

        def matching_names(segments: Iterable[Segment]) -> list[str]:
            return [s.name for s in segments if customer_id in s.members]

        product_categories = [
            self.products[p.product_id].category
            for p in self.purchases
            if p.customer_id == customer_id
        ]

        return {
            "customer_id": customer_id,
            "customer_segments": matching_names(self.customer_segments()),
            "geographic_segments": matching_names(self.geographic_segments()),
            "behavioral_segments": matching_names(self.behavioral_segments()),
            "preferred_category": customer.preferred_category,
            "purchased_categories": sorted(set(product_categories)),
        }

    def product_performance_by_segment(self) -> dict[str, float]:
        """
        Measures revenue by product category. This is useful for connecting
        product segmentation with observed commercial performance.
        """
        revenue_by_category: defaultdict[str, float] = defaultdict(float)

        for purchase in self.purchases:
            product = self.products[purchase.product_id]
            revenue_by_category[product.category] += purchase.value

        return dict(sorted(revenue_by_category.items()))

    @staticmethod
    def _median(values: Iterable[float]) -> float:
        ordered = sorted(values)
        if not ordered:
            raise ValueError("Median requires at least one value.")

        middle = len(ordered) // 2

        if len(ordered) % 2:
            return float(ordered[middle])

        return (ordered[middle - 1] + ordered[middle]) / 2

    def segment_summary(self) -> dict[str, dict[str, int]]:
        all_segments = (
            self.customer_segments()
            + self.product_segments()
            + self.geographic_segments()
            + self.behavioral_segments()
        )

        result: dict[str, dict[str, int]] = defaultdict(dict)

        for segment in all_segments:
            result[segment.dimension.value][segment.name] = len(segment.members)

        return dict(result)


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """
    A small numerical example for behavioral segmentation.

    Vectors can represent normalized behavior such as purchase frequency,
    average order value, category diversity, and digital-channel usage.
    """
    if len(left) != len(right):
        raise ValueError("Vectors must have equal dimensions.")

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (left_norm * right_norm)


def print_segments(title: str, segments: Sequence[Segment]) -> None:
    print(f"\n{title}")
    for segment in segments:
        members = ", ".join(sorted(segment.members)) or "none"
        print(f"  {segment.name}: {members}")
        print(f"    {segment.description}")


def build_sample_data() -> tuple[list[Customer], list[Product], list[Purchase]]:
    customers = [
        Customer(
            "C001", 27, 90000, "North", "Delhi",
            "Electronics", "Gold", "Digital",
        ),
        Customer(
            "C002", 42, 145000, "West", "Mumbai",
            "Home", "Platinum", "Referral",
        ),
        Customer(
            "C003", 31, 42000, "East", "Kolkata",
            "Household", "Silver", "Search",
        ),
        Customer(
            "C004", 55, 70000, "South", "Bengaluru",
            "Electronics", "Gold", "Retail",
        ),
        Customer(
            "C005", 23, 52000, "North", "Lucknow",
            "Fashion", "Silver", "Social",
        ),
        Customer(
            "C006", 38, 160000, "West", "Pune",
            "Electronics", "Platinum", "Referral",
        ),
    ]

    products = [
        Product("P001", "Electronics", 120000, 0.22, "Premium"),
        Product("P002", "Home", 18000, 0.35, "Household"),
        Product("P003", "Household", 3500, 0.42, "Essential"),
        Product("P004", "Fashion", 6500, 0.48, "Lifestyle"),
        Product("P005", "Electronics", 42000, 0.31, "Premium"),
        Product("P006", "Home", 9000, 0.28, "Daily_Needs"),
    ]

    purchases = [
        Purchase("C001", "P005", 1, 42000, "2026-10-05", "online"),
        Purchase("C001", "P003", 3, 3500, "2026-09-20", "online"),
        Purchase("C001", "P002", 2, 18000, "2026-08-12", "mobile"),
        Purchase("C002", "P001", 1, 120000, "2026-10-10", "online"),
        Purchase("C002", "P002", 3, 18000, "2026-09-11", "store"),
        Purchase("C002", "P005", 1, 42000, "2026-07-01", "online"),
        Purchase("C003", "P003", 4, 3500, "2026-10-01", "online"),
        Purchase("C004", "P006", 2, 9000, "2026-07-05", "store"),
        Purchase("C005", "P004", 1, 6500, "2026-10-03", "mobile"),
        Purchase("C006", "P001", 1, 120000, "2026-09-30", "online"),
        Purchase("C006", "P005", 2, 42000, "2026-08-29", "online"),
        Purchase("C006", "P002", 1, 18000, "2026-08-15", "mobile"),
    ]

    return customers, products, purchases


def run_validation_examples() -> None:
    print("\nValidation behavior")

    try:
        SegmentationEngine(
            [
                Customer(
                    "INVALID", 16, 10000, "North", "Delhi",
                    "Home", "Silver", "Search",
                )
            ],
            [Product("P", "Home", 100, 0.2, "Essential")],
            [],
        )
    except ValueError as error:
        print(f"  Invalid customer rejected: {error}")

    try:
        cosine_similarity([1.0, 2.0], [1.0])
    except ValueError as error:
        print(f"  Invalid vector rejected: {error}")


def main() -> None:
    customers, products, purchases = build_sample_data()
    engine = SegmentationEngine(customers, products, purchases)

    print("Customer, Product, Geographic, and Behavioral Segmentation")

    print_segments("Customer segmentation", engine.customer_segments())
    print_segments("Product segmentation", engine.product_segments())
    print_segments("Geographic segmentation", engine.geographic_segments())
    print_segments("Behavioral segmentation", engine.behavioral_segments())

    print("\nCross-dimension customer profile")
    for customer_id in ("C001", "C002", "C006"):
        print(f"  {engine.cross_dimension_profile(customer_id)}")

    print("\nRevenue by product category")
    for category, revenue in engine.product_performance_by_segment().items():
        print(f"  {category}: ₹{revenue:,.2f}")

    print("\nSegmentation summary")
    for dimension, segments in engine.segment_summary().items():
        print(f"  {dimension}: {segments}")

    print("\nBehavioral similarity")
    print(
        "  C001 vs C006:",
        f"{cosine_similarity([0.8, 0.7, 0.6], [0.9, 0.8, 0.7]):.3f}",
    )

    run_validation_examples()


if __name__ == "__main__":
    main()
