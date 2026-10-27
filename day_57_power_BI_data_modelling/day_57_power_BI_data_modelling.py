from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from collections import defaultdict
from typing import Iterable


class RelationshipType(str, Enum):
    ONE_TO_MANY = "1:*"
    MANY_TO_ONE = "*:1"


class FilterDirection(str, Enum):
    SINGLE = "single"
    BOTH = "both"


class ModelError(Exception):
    pass


@dataclass(frozen=True)
class DimensionKey:
    value: int


@dataclass
class DateDimension:
    date_key: int
    calendar_date: date
    year: int
    quarter: int
    month: int
    month_name: str
    week: int
    day_of_month: int
    is_weekend: bool


@dataclass
class CustomerDimension:
    customer_key: int
    customer_id: str
    customer_name: str
    segment: str
    region: str


@dataclass
class ProductDimension:
    product_key: int
    product_id: str
    product_name: str
    category: str
    subcategory: str


@dataclass
class SalesFact:
    sales_key: int
    date_key: int
    customer_key: int
    product_key: int
    order_id: str
    quantity: int
    unit_price: Decimal
    discount_rate: Decimal

    @property
    def gross_sales(self) -> Decimal:
        return self.unit_price * self.quantity

    @property
    def discount_amount(self) -> Decimal:
        return self.gross_sales * self.discount_rate

    @property
    def net_sales(self) -> Decimal:
        return self.gross_sales - self.discount_amount


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: RelationshipType
    filter_direction: FilterDirection
    active: bool = True


@dataclass
class StarSchema:
    dates: dict[int, DateDimension] = field(default_factory=dict)
    customers: dict[int, CustomerDimension] = field(default_factory=dict)
    products: dict[int, ProductDimension] = field(default_factory=dict)
    sales: list[SalesFact] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)

    def validate(self) -> None:
        if not self.sales:
            raise ModelError("The fact table cannot be empty.")

        for fact in self.sales:
            if fact.date_key not in self.dates:
                raise ModelError(
                    f"Sales row {fact.sales_key} references missing date {fact.date_key}."
                )
            if fact.customer_key not in self.customers:
                raise ModelError(
                    f"Sales row {fact.sales_key} references missing customer "
                    f"{fact.customer_key}."
                )
            if fact.product_key not in self.products:
                raise ModelError(
                    f"Sales row {fact.sales_key} references missing product "
                    f"{fact.product_key}."
                )
            if fact.quantity <= 0:
                raise ModelError("Fact quantity must be positive.")
            if fact.unit_price < 0:
                raise ModelError("Unit price cannot be negative.")
            if not Decimal("0") <= fact.discount_rate <= Decimal("1"):
                raise ModelError("Discount rate must be between 0 and 1.")

        self._validate_dimension_keys()
        self._validate_relationships()

    def _validate_dimension_keys(self) -> None:
        if len(self.dates) != len(set(self.dates)):
            raise ModelError("Duplicate date keys detected.")
        if len(self.customers) != len(set(self.customers)):
            raise ModelError("Duplicate customer keys detected.")
        if len(self.products) != len(set(self.products)):
            raise ModelError("Duplicate product keys detected.")

    def _validate_relationships(self) -> None:
        expected = {
            ("Sales", "date_key", "DimDate", "date_key"),
            ("Sales", "customer_key", "DimCustomer", "customer_key"),
            ("Sales", "product_key", "DimProduct", "product_key"),
        }

        actual = {
            (r.from_table, r.from_column, r.to_table, r.to_column)
            for r in self.relationships
            if r.active
        }

        missing = expected - actual
        if missing:
            raise ModelError(f"Missing active relationships: {sorted(missing)}")

        for relationship in self.relationships:
            if relationship.filter_direction == FilterDirection.BOTH:
                raise ModelError(
                    "This learning model requires single-direction dimension-to-fact "
                    "filter propagation to avoid ambiguous paths."
                )

    def add_sale(self, fact: SalesFact) -> None:
        if any(existing.sales_key == fact.sales_key for existing in self.sales):
            raise ModelError(f"Duplicate sales key: {fact.sales_key}")
        self.sales.append(fact)

    def filtered_sales(
        self,
        *,
        year: int | None = None,
        region: str | None = None,
        category: str | None = None,
        customer_segment: str | None = None,
    ) -> list[SalesFact]:
        result = []

        for fact in self.sales:
            date_row = self.dates[fact.date_key]
            customer = self.customers[fact.customer_key]
            product = self.products[fact.product_key]

            if year is not None and date_row.year != year:
                continue
            if region is not None and customer.region != region:
                continue
            if category is not None and product.category != category:
                continue
            if customer_segment is not None and customer.segment != customer_segment:
                continue

            result.append(fact)

        return result

    def measure_net_sales(self, facts: Iterable[SalesFact]) -> Decimal:
        return sum((row.net_sales for row in facts), Decimal("0"))

    def measure_quantity(self, facts: Iterable[SalesFact]) -> int:
        return sum(row.quantity for row in facts)

    def sales_by_category(self, facts: Iterable[SalesFact]) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        for fact in facts:
            category = self.products[fact.product_key].category
            totals[category] += fact.net_sales

        return dict(sorted(totals.items()))

    def sales_by_region(self, facts: Iterable[SalesFact]) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        for fact in facts:
            region = self.customers[fact.customer_key].region
            totals[region] += fact.net_sales

        return dict(sorted(totals.items()))

    def sales_by_month(self, facts: Iterable[SalesFact]) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        for fact in facts:
            date_row = self.dates[fact.date_key]
            month = f"{date_row.year}-{date_row.month:02d}"
            totals[month] += fact.net_sales

        return dict(sorted(totals.items()))


def build_date_dimension() -> dict[int, DateDimension]:
    dates = [
        date(2026, 1, 5),
        date(2026, 1, 18),
        date(2026, 2, 7),
        date(2026, 2, 21),
        date(2026, 3, 12),
        date(2026, 3, 28),
        date(2026, 4, 9),
        date(2026, 4, 25),
    ]

    result = {}

    for current in dates:
        key = int(current.strftime("%Y%m%d"))
        result[key] = DateDimension(
            date_key=key,
            calendar_date=current,
            year=current.year,
            quarter=((current.month - 1) // 3) + 1,
            month=current.month,
            month_name=current.strftime("%B"),
            week=current.isocalendar().week,
            day_of_month=current.day,
            is_weekend=current.weekday() >= 5,
        )

    return result


def build_model() -> StarSchema:
    model = StarSchema()

    model.dates = build_date_dimension()

    model.customers = {
        1: CustomerDimension(1, "C001", "Apex Systems", "Enterprise", "North"),
        2: CustomerDimension(2, "C002", "Blue Retail", "SMB", "West"),
        3: CustomerDimension(3, "C003", "Cedar Health", "Enterprise", "South"),
        4: CustomerDimension(4, "C004", "Delta Labs", "Mid-Market", "East"),
    }

    model.products = {
        1: ProductDimension(1, "P001", "Analytics Platform", "Software", "Analytics"),
        2: ProductDimension(2, "P002", "Security Suite", "Software", "Security"),
        3: ProductDimension(3, "P003", "Cloud Appliance", "Hardware", "Infrastructure"),
        4: ProductDimension(4, "P004", "Support Contract", "Services", "Support"),
    }

    model.relationships = [
        Relationship(
            "Sales", "date_key", "DimDate", "date_key",
            RelationshipType.MANY_TO_ONE, FilterDirection.SINGLE
        ),
        Relationship(
            "Sales", "customer_key", "DimCustomer", "customer_key",
            RelationshipType.MANY_TO_ONE, FilterDirection.SINGLE
        ),
        Relationship(
            "Sales", "product_key", "DimProduct", "product_key",
            RelationshipType.MANY_TO_ONE, FilterDirection.SINGLE
        ),
    ]

    rows = [
        (1, 20260105, 1, 1, "SO1001", 3, "1200.00", "0.05"),
        (2, 20260118, 2, 2, "SO1002", 2, "800.00", "0.00"),
        (3, 20260207, 3, 3, "SO1003", 1, "4500.00", "0.10"),
        (4, 20260221, 4, 4, "SO1004", 5, "300.00", "0.05"),
        (5, 20260312, 1, 2, "SO1005", 4, "800.00", "0.10"),
        (6, 20260328, 2, 1, "SO1006", 1, "1200.00", "0.00"),
        (7, 20260409, 3, 4, "SO1007", 8, "300.00", "0.00"),
        (8, 20260425, 4, 3, "SO1008", 2, "4500.00", "0.15"),
    ]

    for row in rows:
        model.add_sale(
            SalesFact(
                sales_key=row[0],
                date_key=row[1],
                customer_key=row[2],
                product_key=row[3],
                order_id=row[4],
                quantity=row[5],
                unit_price=Decimal(row[6]),
                discount_rate=Decimal(row[7]),
            )
        )

    model.validate()
    return model


def run_demo(model: StarSchema) -> None:
    print("POWER BI-STYLE STAR SCHEMA MODEL")
    print("=" * 70)

    print("\nRelationships")
    for relationship in model.relationships:
        print(
            f"{relationship.from_table}.{relationship.from_column} "
            f"{relationship.relationship_type.value} "
            f"{relationship.to_table}.{relationship.to_column} "
            f"[{relationship.filter_direction.value}-direction]"
        )

    all_sales = model.filtered_sales()
    north_sales = model.filtered_sales(region="North")
    software_sales = model.filtered_sales(category="Software")
    enterprise_2026 = model.filtered_sales(
        year=2026,
        customer_segment="Enterprise",
    )

    print("\nMeasures")
    print(f"Total net sales:      ${model.measure_net_sales(all_sales):,.2f}")
    print(f"Total quantity:       {model.measure_quantity(all_sales):,}")
    print(f"North net sales:      ${model.measure_net_sales(north_sales):,.2f}")
    print(f"Software net sales:   ${model.measure_net_sales(software_sales):,.2f}")
    print(
        f"Enterprise 2026:     "
        f"${model.measure_net_sales(enterprise_2026):,.2f}"
    )

    print("\nSales by category")
    for category, amount in model.sales_by_category(all_sales).items():
        print(f"{category:15} ${amount:,.2f}")

    print("\nSales by region")
    for region, amount in model.sales_by_region(all_sales).items():
        print(f"{region:15} ${amount:,.2f}")

    print("\nSales by month")
    for month, amount in model.sales_by_month(all_sales).items():
        print(f"{month:15} ${amount:,.2f}")

    print("\nEdge-case validation")
    try:
        model.add_sale(
            SalesFact(
                sales_key=1,
                date_key=20260105,
                customer_key=1,
                product_key=1,
                order_id="DUPLICATE",
                quantity=1,
                unit_price=Decimal("100"),
                discount_rate=Decimal("0"),
            )
        )
    except ModelError as exc:
        print(f"Duplicate fact rejected: {exc}")

    try:
        invalid = SalesFact(
            sales_key=99,
            date_key=20260105,
            customer_key=999,
            product_key=1,
            order_id="INVALID",
            quantity=1,
            unit_price=Decimal("100"),
            discount_rate=Decimal("0"),
        )
        model.add_sale(invalid)
        model.validate()
    except ModelError as exc:
        model.sales.pop()
        print(f"Invalid foreign key rejected: {exc}")

    print("\nDesign notes")
    print("- Fact rows store measurable business events at a defined grain.")
    print("- Dimensions provide descriptive filtering and grouping attributes.")
    print("- Dimension keys are validated before facts are accepted.")
    print("- Filters propagate from dimensions toward the fact table.")
    print("- Measures aggregate fact values after dimensional filtering.")
    print("- Dictionaries provide approximately O(1) dimension-key lookup.")


if __name__ == "__main__":
    run_demo(build_model())
