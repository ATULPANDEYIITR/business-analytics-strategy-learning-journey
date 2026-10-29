from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from collections import defaultdict
from typing import Iterable, Sequence


# Advanced Power BI analytical calculations modelled with explicit filter context.
# The implementation mirrors important DAX concepts:
#   - filter context
#   - CALCULATE-like context replacement
#   - time intelligence
#   - iterators
#   - distinct counts
#   - rolling calculations
#   - ranking
#   - percent-of-total
#   - variance analysis
#   - semi-additive inventory measures


class Channel(Enum):
    ONLINE = "Online"
    RETAIL = "Retail"
    PARTNER = "Partner"


@dataclass(frozen=True)
class Sale:
    sale_id: int
    sale_date: date
    region: str
    product: str
    channel: Channel
    customer_id: int
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal

    @property
    def revenue(self) -> Decimal:
        return self.unit_price * self.quantity

    @property
    def cost(self) -> Decimal:
        return self.unit_cost * self.quantity

    @property
    def margin(self) -> Decimal:
        return self.revenue - self.cost


@dataclass(frozen=True)
class InventorySnapshot:
    snapshot_date: date
    region: str
    product: str
    units: int


@dataclass(frozen=True)
class FilterContext:
    dates: frozenset[date] | None = None
    regions: frozenset[str] | None = None
    products: frozenset[str] | None = None
    channels: frozenset[Channel] | None = None
    customers: frozenset[int] | None = None

    def with_dates(self, dates: Iterable[date]) -> "FilterContext":
        return FilterContext(
            dates=frozenset(dates),
            regions=self.regions,
            products=self.products,
            channels=self.channels,
            customers=self.customers,
        )


class AnalyticsModel:
    def __init__(
        self,
        sales: Sequence[Sale],
        inventory: Sequence[InventorySnapshot],
    ) -> None:
        self.sales = tuple(sales)
        self.inventory = tuple(inventory)

    def _filtered_sales(self, context: FilterContext) -> list[Sale]:
        result = []
        for sale in self.sales:
            if context.dates is not None and sale.sale_date not in context.dates:
                continue
            if context.regions is not None and sale.region not in context.regions:
                continue
            if context.products is not None and sale.product not in context.products:
                continue
            if context.channels is not None and sale.channel not in context.channels:
                continue
            if context.customers is not None and sale.customer_id not in context.customers:
                continue
            result.append(sale)
        return result

    def _filtered_inventory(
        self, context: FilterContext
    ) -> list[InventorySnapshot]:
        result = []
        for row in self.inventory:
            if context.dates is not None and row.snapshot_date not in context.dates:
                continue
            if context.regions is not None and row.region not in context.regions:
                continue
            if context.products is not None and row.product not in context.products:
                continue
            result.append(row)
        return result

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def revenue(self, context: FilterContext) -> Decimal:
        return self._money(sum((s.revenue for s in self._filtered_sales(context)), Decimal()))

    def cost(self, context: FilterContext) -> Decimal:
        return self._money(sum((s.cost for s in self._filtered_sales(context)), Decimal()))

    def margin(self, context: FilterContext) -> Decimal:
        return self._money(self.revenue(context) - self.cost(context))

    def margin_pct(self, context: FilterContext) -> Decimal:
        revenue = self.revenue(context)
        if revenue == 0:
            return Decimal("0.00")
        return self._money(self.margin(context) * 100 / revenue)

    def distinct_customers(self, context: FilterContext) -> int:
        return len({s.customer_id for s in self._filtered_sales(context)})

    def average_order_value(self, context: FilterContext) -> Decimal:
        sales = self._filtered_sales(context)
        if not sales:
            return Decimal("0.00")

        orders = defaultdict(Decimal)
        for sale in sales:
            # sale_id represents an order in this deliberately compact model.
            orders[sale.sale_id] += sale.revenue

        return self._money(sum(orders.values(), Decimal()) / len(orders))

    def quantity(self, context: FilterContext) -> int:
        return sum(s.quantity for s in self._filtered_sales(context))

    def date_range(self, context: FilterContext) -> tuple[date, date] | None:
        if context.dates:
            return min(context.dates), max(context.dates)

        if not self.sales:
            return None

        return min(s.sale_date for s in self.sales), max(
            s.sale_date for s in self.sales
        )

    @staticmethod
    def month_start(value: date) -> date:
        return date(value.year, value.month, 1)

    @staticmethod
    def shift_month(value: date, offset: int) -> date:
        month_index = value.year * 12 + value.month - 1 + offset
        year, month_zero_based = divmod(month_index, 12)
        return date(year, month_zero_based + 1, 1)

    @classmethod
    def month_dates(cls, year: int, month: int) -> frozenset[date]:
        start = date(year, month, 1)
        next_month = cls.shift_month(start, 1)
        days = (next_month - start).days
        return frozenset(start.fromordinal(start.toordinal() + i) for i in range(days))

    @classmethod
    def previous_month_dates(cls, context: FilterContext) -> frozenset[date]:
        if not context.dates:
            return frozenset()

        start = cls.month_start(min(context.dates))
        previous = cls.shift_month(start, -1)
        return cls.month_dates(previous.year, previous.month)

    @classmethod
    def year_to_date_dates(cls, current_date: date) -> frozenset[date]:
        start = date(current_date.year, 1, 1)
        return frozenset(
            start.fromordinal(start.toordinal() + i)
            for i in range((current_date - start).days + 1)
        )

    def ytd_revenue(self, current_date: date, context: FilterContext) -> Decimal:
        dates = self.year_to_date_dates(current_date)
        return self.revenue(context.with_dates(dates))

    def previous_month_revenue(self, context: FilterContext) -> Decimal:
        dates = self.previous_month_dates(context)
        if not dates:
            return Decimal("0.00")
        return self.revenue(context.with_dates(dates))

    def month_over_month_pct(self, context: FilterContext) -> Decimal:
        current = self.revenue(context)
        previous = self.previous_month_revenue(context)

        if previous == 0:
            return Decimal("0.00")

        return self._money((current - previous) * 100 / previous)

    def rolling_revenue(
        self,
        anchor_date: date,
        days: int,
        context: FilterContext,
    ) -> Decimal:
        if days <= 0:
            raise ValueError("Rolling window must contain at least one day.")

        start = anchor_date.fromordinal(anchor_date.toordinal() - days + 1)
        dates = frozenset(
            start.fromordinal(start.toordinal() + i)
            for i in range(days)
        )
        return self.revenue(context.with_dates(dates))

    def percent_of_total(
        self,
        context: FilterContext,
        remove_dimensions: set[str],
    ) -> Decimal:
        numerator = self.revenue(context)

        # This simulates the intent of REMOVEFILTERS for selected dimensions.
        total_context = FilterContext(
            dates=context.dates if "date" not in remove_dimensions else None,
            regions=context.regions if "region" not in remove_dimensions else None,
            products=context.products if "product" not in remove_dimensions else None,
            channels=context.channels if "channel" not in remove_dimensions else None,
            customers=context.customers if "customer" not in remove_dimensions else None,
        )

        denominator = self.revenue(total_context)
        if denominator == 0:
            return Decimal("0.00")

        return self._money(numerator * 100 / denominator)

    def product_rank(self, context: FilterContext) -> list[tuple[str, int, Decimal]]:
        products = sorted({s.product for s in self._filtered_sales(
            FilterContext(
                dates=context.dates,
                regions=context.regions,
                products=None,
                channels=context.channels,
                customers=context.customers,
            )
        )})

        scores = []
        for product in products:
            product_context = FilterContext(
                dates=context.dates,
                regions=context.regions,
                products=frozenset({product}),
                channels=context.channels,
                customers=context.customers,
            )
            scores.append((product, self.revenue(product_context)))

        scores.sort(key=lambda item: (-item[1], item[0]))

        result = []
        previous_revenue: Decimal | None = None
        rank = 0

        for position, (product, revenue) in enumerate(scores, start=1):
            if previous_revenue != revenue:
                rank = position
            result.append((product, rank, revenue))
            previous_revenue = revenue

        return result

    def latest_inventory(
        self,
        context: FilterContext,
    ) -> int:
        rows = self._filtered_inventory(context)
        if not rows:
            return 0

        latest_date = max(row.snapshot_date for row in rows)

        # Inventory is semi-additive: sum across products/regions for the
        # latest snapshot, rather than summing every historical snapshot.
        return sum(
            row.units for row in rows if row.snapshot_date == latest_date
        )

    def sales_by_channel(
        self, context: FilterContext
    ) -> dict[Channel, Decimal]:
        result: dict[Channel, Decimal] = {}
        for channel in Channel:
            channel_context = FilterContext(
                dates=context.dates,
                regions=context.regions,
                products=context.products,
                channels=frozenset({channel}),
                customers=context.customers,
            )
            result[channel] = self.revenue(channel_context)
        return result

    def evaluate(self, context: FilterContext, anchor_date: date) -> dict:
        revenue = self.revenue(context)
        previous = self.previous_month_revenue(context)

        return {
            "revenue": revenue,
            "cost": self.cost(context),
            "margin": self.margin(context),
            "margin_pct": self.margin_pct(context),
            "distinct_customers": self.distinct_customers(context),
            "average_order_value": self.average_order_value(context),
            "quantity": self.quantity(context),
            "previous_month_revenue": previous,
            "month_over_month_pct": self.month_over_month_pct(context),
            "ytd_revenue": self.ytd_revenue(anchor_date, context),
            "rolling_7_day_revenue": self.rolling_revenue(
                anchor_date, 7, context
            ),
            "percent_of_all_revenue": self.percent_of_total(
                context, {"region", "product", "channel", "customer"}
            ),
            "latest_inventory": self.latest_inventory(context),
            "product_rank": self.product_rank(context),
            "channel_revenue": self.sales_by_channel(context),
        }


def build_sample_model() -> AnalyticsModel:
    rows = [
        Sale(1001, date(2026, 1, 2), "North", "Laptop", Channel.ONLINE, 501, 2, Decimal("1200"), Decimal("800")),
        Sale(1002, date(2026, 1, 4), "North", "Monitor", Channel.RETAIL, 502, 4, Decimal("300"), Decimal("180")),
        Sale(1003, date(2026, 1, 8), "South", "Laptop", Channel.PARTNER, 503, 1, Decimal("1250"), Decimal("800")),
        Sale(1004, date(2026, 1, 12), "North", "Keyboard", Channel.ONLINE, 501, 5, Decimal("80"), Decimal("35")),
        Sale(1005, date(2026, 1, 18), "South", "Monitor", Channel.RETAIL, 504, 3, Decimal("310"), Decimal("180")),
        Sale(1006, date(2026, 1, 23), "West", "Laptop", Channel.ONLINE, 505, 1, Decimal("1190"), Decimal("800")),
        Sale(1007, date(2026, 1, 28), "North", "Laptop", Channel.ONLINE, 506, 1, Decimal("1210"), Decimal("800")),
        Sale(1008, date(2026, 2, 2), "North", "Monitor", Channel.RETAIL, 507, 5, Decimal("305"), Decimal("180")),
        Sale(1009, date(2026, 2, 7), "South", "Laptop", Channel.ONLINE, 503, 2, Decimal("1240"), Decimal("800")),
        Sale(1010, date(2026, 2, 11), "West", "Keyboard", Channel.PARTNER, 508, 8, Decimal("82"), Decimal("35")),
        Sale(1011, date(2026, 2, 16), "North", "Laptop", Channel.ONLINE, 509, 1, Decimal("1230"), Decimal("800")),
        Sale(1012, date(2026, 2, 20), "South", "Monitor", Channel.RETAIL, 510, 4, Decimal("315"), Decimal("180")),
        Sale(1013, date(2026, 2, 24), "West", "Laptop", Channel.PARTNER, 511, 2, Decimal("1180"), Decimal("800")),
        Sale(1014, date(2026, 2, 27), "North", "Keyboard", Channel.ONLINE, 512, 10, Decimal("78"), Decimal("35")),
        Sale(1015, date(2026, 3, 2), "South", "Laptop", Channel.ONLINE, 513, 2, Decimal("1260"), Decimal("800")),
        Sale(1016, date(2026, 3, 5), "North", "Monitor", Channel.RETAIL, 514, 6, Decimal("310"), Decimal("180")),
        Sale(1017, date(2026, 3, 10), "West", "Keyboard", Channel.PARTNER, 515, 7, Decimal("85"), Decimal("35")),
        Sale(1018, date(2026, 3, 14), "South", "Laptop", Channel.ONLINE, 516, 1, Decimal("1270"), Decimal("800")),
    ]

    inventory = [
        InventorySnapshot(date(2026, 1, 31), "North", "Laptop", 42),
        InventorySnapshot(date(2026, 1, 31), "North", "Monitor", 70),
        InventorySnapshot(date(2026, 1, 31), "South", "Laptop", 31),
        InventorySnapshot(date(2026, 2, 28), "North", "Laptop", 37),
        InventorySnapshot(date(2026, 2, 28), "North", "Monitor", 64),
        InventorySnapshot(date(2026, 2, 28), "South", "Laptop", 26),
        InventorySnapshot(date(2026, 2, 28), "West", "Keyboard", 90),
        InventorySnapshot(date(2026, 3, 15), "North", "Laptop", 34),
        InventorySnapshot(date(2026, 3, 15), "North", "Monitor", 58),
        InventorySnapshot(date(2026, 3, 15), "South", "Laptop", 24),
        InventorySnapshot(date(2026, 3, 15), "West", "Keyboard", 82),
    ]

    return AnalyticsModel(rows, inventory)


def run_assertions(model: AnalyticsModel) -> None:
    january = FilterContext(
        dates=model.month_dates(2026, 1),
    )

    assert model.revenue(january) > Decimal("0")
    assert model.margin(january) < model.revenue(january)
    assert model.distinct_customers(january) == 6
    assert model.previous_month_revenue(january) == Decimal("0.00")

    february = FilterContext(
        dates=model.month_dates(2026, 2),
    )

    assert model.previous_month_revenue(february) == model.revenue(january)
    assert model.rolling_revenue(date(2026, 2, 24), 7, FilterContext()) > 0
    assert model.latest_inventory(FilterContext()) == 198

    ranked = model.product_rank(FilterContext())
    assert ranked
    assert ranked[0][1] == 1

    empty = FilterContext(products=frozenset({"DoesNotExist"}))
    assert model.revenue(empty) == Decimal("0.00")
    assert model.margin_pct(empty) == Decimal("0.00")


def main() -> None:
    model = build_sample_model()
    run_assertions(model)

    context = FilterContext(
        dates=model.month_dates(2026, 2),
        regions=frozenset({"North", "South"}),
    )

    metrics = model.evaluate(context, date(2026, 2, 28))

    print("Advanced Power BI Analytical Measures Model")
    print("=" * 52)

    for key, value in metrics.items():
        if key == "product_rank":
            print(f"{key}:")
            for product, rank, revenue in value:
                print(f"  rank={rank:<2} product={product:<10} revenue={revenue}")
        elif key == "channel_revenue":
            print(f"{key}:")
            for channel, revenue in value.items():
                print(f"  {channel.value:<8} {revenue}")
        else:
            print(f"{key}: {value}")

    print("\nValidation: all assertions passed.")
    print("Security: analytical input is represented by typed in-memory records;")
    print("external credentials and executable expressions are intentionally absent.")
    print("Performance: filtering is O(n) per measure; production models should")
    print("prefer a star schema and VertiPaq-friendly low-cardinality dimensions.")


if __name__ == "__main__":
    main()
