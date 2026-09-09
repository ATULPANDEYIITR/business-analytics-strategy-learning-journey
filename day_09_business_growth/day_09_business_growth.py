"""
BUSINESS GROWTH: REVENUE GROWTH, CUSTOMER GROWTH AND MARKET EXPANSION
=====================================================================

A self-contained study and demonstration program covering business growth from
absolute beginner concepts through advanced strategy, quantitative analysis,
forecasting, experimentation, segmentation, unit economics, pricing, retention,
market expansion, growth loops, and practical decision-making.

The program uses only Python's standard library.

Run:
    python business_growth.py

The script is intentionally executable. Each section prints concepts and then
demonstrates them with calculations, simulations, validations, and examples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil, log
from statistics import mean, median, pstdev
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import random


# ============================================================================
# 1. FOUNDATIONS
# ============================================================================

def section(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def money(value: float) -> str:
    """Format an amount as currency without assuming a particular currency."""
    return f"₹{value:,.2f}"


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def safe_divide(numerator: float, denominator: float) -> float:
    """Avoid accidental division by zero in analytical calculations."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compound_growth(start: float, growth_rate: float, periods: int) -> float:
    """
    Calculate compound growth.

    Example:
        ₹100 growing 10% for three periods becomes ₹133.10.
    """
    if periods < 0:
        raise ValueError("periods cannot be negative")
    return start * (1 + growth_rate) ** periods


def annualized_growth_rate(start: float, end: float, years: float) -> float:
    """Calculate CAGR."""
    if start <= 0 or end < 0 or years <= 0:
        raise ValueError("start must be > 0 and years must be > 0")
    return (end / start) ** (1 / years) - 1


def explain_foundations() -> None:
    section("1. BUSINESS GROWTH FOUNDATIONS")

    print("""
Business growth is the sustained increase in the economic value created by a
business. It can appear through:

1. Revenue growth
   More money generated from customers.

2. Customer growth
   More customers acquired, activated, retained, or reactivated.

3. Market expansion
   Selling to new geographic markets, segments, industries, channels, or
   use cases.

Growth is not synonymous with simply becoming larger. A company can increase
revenue while destroying cash, acquiring unprofitable customers, or creating
operational problems. High-quality growth therefore considers both scale and
economics.

A useful decomposition is:

    Revenue = Customers × Revenue per Customer

For recurring businesses:

    Revenue = Customers × Average Revenue per Customer per Period

Customer count itself is dynamic:

    Ending Customers =
        Beginning Customers
        + New Customers
        + Reactivated Customers
        - Churned Customers

A practical growth system therefore connects acquisition, conversion,
monetization, retention, and expansion.
""")

    customers = 1000
    average_revenue_per_customer = 2500
    revenue = customers * average_revenue_per_customer

    print("Example:")
    print(f"Customers: {customers:,}")
    print(f"Revenue/customer: {money(average_revenue_per_customer)}")
    print(f"Revenue: {money(revenue)}")

    print("\nGrowth arithmetic:")
    print(f"10% customer growth -> {customers * 1.10:,.0f} customers")
    print(
        f"15% revenue/customer growth -> "
        f"{money(average_revenue_per_customer * 1.15)}"
    )
    print(
        f"Combined revenue after both changes -> "
        f"{money(customers * 1.10 * average_revenue_per_customer * 1.15)}"
    )


# ============================================================================
# 2. CORE BUSINESS GROWTH METRICS
# ============================================================================

@dataclass
class GrowthMetrics:
    revenue: float
    customers: int
    new_customers: int
    churned_customers: int
    marketing_spend: float
    gross_profit: float
    orders: int
    average_order_value: float

    @property
    def revenue_per_customer(self) -> float:
        return safe_divide(self.revenue, self.customers)

    @property
    def customer_growth_rate(self) -> float:
        denominator = self.customers - self.new_customers + self.churned_customers
        return safe_divide(
            self.new_customers - self.churned_customers,
            denominator,
        )

    @property
    def gross_margin(self) -> float:
        return safe_divide(self.gross_profit, self.revenue)

    @property
    def marketing_roi(self) -> float:
        return safe_divide(
            self.gross_profit - self.marketing_spend,
            self.marketing_spend,
        )


def explain_core_metrics() -> None:
    section("2. CORE BUSINESS GROWTH METRICS")

    print("""
Important metrics:

Revenue
    Total money generated from customers during a period.

Revenue Growth Rate
    (Current Revenue - Previous Revenue) / Previous Revenue

Customer Growth Rate
    (Current Customers - Previous Customers) / Previous Customers

Average Order Value (AOV)
    Revenue / Number of Orders

Average Revenue Per Customer (ARPC)
    Revenue / Number of Customers

Gross Margin
    Gross Profit / Revenue

Gross profit
    Revenue minus directly attributable cost of goods/services.

A business should distinguish:
    revenue growth
    gross-profit growth
    operating-profit growth
    cash-flow growth

These can move in different directions.
""")

    metrics = GrowthMetrics(
        revenue=5_000_000,
        customers=2000,
        new_customers=400,
        churned_customers=100,
        marketing_spend=800_000,
        gross_profit=3_000_000,
        orders=5000,
        average_order_value=1000,
    )

    print(f"Revenue/customer: {money(metrics.revenue_per_customer)}")
    print(f"Customer growth: {percent(metrics.customer_growth_rate)}")
    print(f"Gross margin: {percent(metrics.gross_margin)}")
    print(f"Marketing ROI on gross profit: {percent(metrics.marketing_roi)}")


# ============================================================================
# 3. REVENUE GROWTH DECOMPOSITION
# ============================================================================

@dataclass
class RevenueBridge:
    starting_revenue: float
    new_customer_revenue: float
    expansion_revenue: float
    price_increase_revenue: float
    churned_revenue: float
    contraction_revenue: float

    @property
    def ending_revenue(self) -> float:
        return (
            self.starting_revenue
            + self.new_customer_revenue
            + self.expansion_revenue
            + self.price_increase_revenue
            - self.churned_revenue
            - self.contraction_revenue
        )

    @property
    def growth_rate(self) -> float:
        return safe_divide(
            self.ending_revenue - self.starting_revenue,
            self.starting_revenue,
        )


def explain_revenue_bridge() -> None:
    section("3. REVENUE GROWTH DECOMPOSITION")

    print("""
Revenue growth should be diagnosed rather than treated as one number.

A useful revenue bridge is:

Ending Revenue =
    Starting Revenue
    + New Customer Revenue
    + Expansion Revenue
    + Price Revenue
    - Churn Revenue
    - Contraction Revenue

This distinguishes growth caused by:
    acquisition
    upselling
    cross-selling
    price changes

from revenue losses caused by:
    customer churn
    downgrades
    lower usage
    cancellations
""")

    bridge = RevenueBridge(
        starting_revenue=10_000_000,
        new_customer_revenue=2_500_000,
        expansion_revenue=1_000_000,
        price_increase_revenue=500_000,
        churned_revenue=800_000,
        contraction_revenue=300_000,
    )

    print(f"Starting revenue: {money(bridge.starting_revenue)}")
    print(f"Ending revenue:   {money(bridge.ending_revenue)}")
    print(f"Growth rate:      {percent(bridge.growth_rate)}")


# ============================================================================
# 4. CUSTOMER FUNNEL
# ============================================================================

@dataclass
class FunnelStage:
    name: str
    volume: int


@dataclass
class Funnel:
    stages: List[FunnelStage]

    def conversion_rates(self) -> List[Tuple[str, str, float]]:
        results = []
        for first, second in zip(self.stages, self.stages[1:]):
            results.append(
                (first.name, second.name, safe_divide(second.volume, first.volume))
            )
        return results

    def overall_conversion(self) -> float:
        if not self.stages:
            return 0.0
        return safe_divide(self.stages[-1].volume, self.stages[0].volume)


def explain_customer_growth() -> None:
    section("4. CUSTOMER GROWTH AND THE FUNNEL")

    print("""
Customer growth usually involves a sequence such as:

Awareness
    ↓
Visitors / Leads
    ↓
Qualified Prospects
    ↓
Trials / Demonstrations
    ↓
Paying Customers
    ↓
Retained Customers
    ↓
Expanded Customers / Advocates

The exact stages differ by business.

A low customer-growth rate can be caused by:
    insufficient traffic
    weak lead quality
    poor conversion
    high acquisition cost
    onboarding friction
    weak retention
    poor product-market fit

Optimizing the wrong stage creates local improvements without necessarily
improving total business performance.
""")

    funnel = Funnel(
        [
            FunnelStage("Website Visitors", 100_000),
            FunnelStage("Leads", 10_000),
            FunnelStage("Qualified Leads", 3_000),
            FunnelStage("Trials", 1_500),
            FunnelStage("Paying Customers", 600),
        ]
    )

    for first, second, rate in funnel.conversion_rates():
        print(f"{first} -> {second}: {percent(rate)}")

    print(f"Overall visitor-to-customer conversion: {percent(funnel.overall_conversion())}")

    print("\nFunnel optimization example:")
    improved_trial_to_paid = 0.50
    trials = 1500
    current_paid = 600
    improved_paid = trials * improved_trial_to_paid

    print(f"Current paid customers: {current_paid:,}")
    print(f"Improved paid customers: {improved_paid:,.0f}")
    print(f"Incremental customers: {improved_paid - current_paid:,.0f}")


# ============================================================================
# 5. CUSTOMER ACQUISITION COST AND UNIT ECONOMICS
# ============================================================================

@dataclass
class UnitEconomics:
    acquisition_spend: float
    new_customers: int
    average_revenue_per_customer: float
    gross_margin: float
    monthly_churn_rate: float
    monthly_discount_rate: float = 0.0

    @property
    def cac(self) -> float:
        return safe_divide(self.acquisition_spend, self.new_customers)

    @property
    def gross_profit_per_month(self) -> float:
        return self.average_revenue_per_customer * self.gross_margin

    @property
    def simple_lifetime_months(self) -> float:
        if self.monthly_churn_rate <= 0:
            return float("inf")
        return 1 / self.monthly_churn_rate

    @property
    def simple_ltv(self) -> float:
        return self.gross_profit_per_month * self.simple_lifetime_months

    @property
    def ltv_to_cac(self) -> float:
        return safe_divide(self.simple_ltv, self.cac)

    @property
    def cac_payback_months(self) -> float:
        return safe_divide(self.cac, self.gross_profit_per_month)


def discounted_customer_ltv(
    monthly_gross_profit: float,
    monthly_churn: float,
    monthly_discount_rate: float,
    horizon: int = 120,
) -> float:
    """
    Calculate a finite-horizon discounted LTV.

    Survival probability after month m is approximated by:
        (1 - churn)^m

    The model is intentionally simplified. Real businesses may need cohort
    retention curves, expansion, contraction, refunds, support costs, and
    variable margins.
    """
    total = 0.0

    for month in range(1, horizon + 1):
        survival = (1 - monthly_churn) ** (month - 1)
        discounted_profit = (
            monthly_gross_profit
            * survival
            / ((1 + monthly_discount_rate) ** month)
        )
        total += discounted_profit

    return total


def explain_unit_economics() -> None:
    section("5. UNIT ECONOMICS: CAC, LTV AND PAYBACK")

    print("""
Customer Acquisition Cost (CAC):

    CAC = Acquisition Spend / New Customers

Lifetime Value (simple recurring model):

    LTV ≈ Monthly Gross Profit per Customer / Monthly Churn Rate

LTV is not the same as lifetime revenue. A useful LTV model should normally
use contribution or gross profit rather than raw revenue.

CAC Payback:

    CAC Payback = CAC / Monthly Gross Profit per Customer

The faster CAC is recovered, the less capital is required to finance growth.

LTV:CAC is useful as a diagnostic, not as a universal law. Its interpretation
depends on gross-margin structure, retention quality, acquisition channel,
growth stage, and cash requirements.
""")

    economics = UnitEconomics(
        acquisition_spend=1_200_000,
        new_customers=1000,
        average_revenue_per_customer=2000,
        gross_margin=0.70,
        monthly_churn_rate=0.04,
        monthly_discount_rate=0.01,
    )

    print(f"CAC: {money(economics.cac)}")
    print(f"Monthly gross profit/customer: {money(economics.gross_profit_per_month)}")
    print(f"Simple lifetime: {economics.simple_lifetime_months:.1f} months")
    print(f"Simple LTV: {money(economics.simple_ltv)}")
    print(f"LTV:CAC: {economics.ltv_to_cac:.2f}x")
    print(f"CAC payback: {economics.cac_payback_months:.1f} months")

    discounted_ltv = discounted_customer_ltv(
        economics.gross_profit_per_month,
        economics.monthly_churn_rate,
        economics.monthly_discount_rate,
    )

    print(f"Discounted finite-horizon LTV: {money(discounted_ltv)}")


# ============================================================================
# 6. RETENTION, CHURN AND NET REVENUE RETENTION
# ============================================================================

@dataclass
class SubscriptionCohort:
    starting_customers: int
    retention_by_month: List[float]

    def retained_customers(self, month_index: int) -> float:
        if month_index < 0 or month_index >= len(self.retention_by_month):
            raise IndexError("month index outside cohort data")
        return self.starting_customers * self.retention_by_month[month_index]


def net_revenue_retention(
    starting_revenue: float,
    expansion: float,
    contraction: float,
    churn: float,
) -> float:
    """
    NRR excludes new customer revenue.

    NRR = (Starting Revenue + Expansion - Contraction - Churn)
          / Starting Revenue
    """
    return safe_divide(
        starting_revenue + expansion - contraction - churn,
        starting_revenue,
    )


def explain_retention() -> None:
    section("6. RETENTION, CHURN AND NET REVENUE RETENTION")

    print("""
Customer retention asks:
    How many customers remain?

Revenue retention asks:
    How much revenue from the existing customer base remains?

Customer churn:
    Churned Customers / Customers at Start

Revenue churn:
    Churned Revenue / Revenue at Start

Net Revenue Retention (NRR):

    NRR =
        (Starting Revenue
         + Expansion
         - Contraction
         - Churn)
        / Starting Revenue

NRR above 100% means the existing customer base generated more recurring
revenue than it had at the start, even before counting new customers.

Retention is strategically important because acquisition is expensive. A
business with weak retention can repeatedly replace lost customers instead of
building a durable customer base.
""")

    cohort = SubscriptionCohort(
        starting_customers=1000,
        retention_by_month=[1.00, 0.92, 0.86, 0.81, 0.77, 0.74, 0.72],
    )

    for month, retention in enumerate(cohort.retention_by_month):
        print(
            f"Month {month}: retention={percent(retention)}, "
            f"customers={cohort.retained_customers(month):.0f}"
        )

    nrr = net_revenue_retention(
        starting_revenue=5_000_000,
        expansion=750_000,
        contraction=250_000,
        churn=400_000,
    )
    print(f"\nExample NRR: {percent(nrr)}")


# ============================================================================
# 7. PRICING AND MONETIZATION
# ============================================================================

class PricingModel(Enum):
    ONE_TIME = "one-time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage-based"
    TRANSACTIONAL = "transactional"
    FREEMIUM = "freemium"
    MARKETPLACE_COMMISSION = "marketplace commission"


@dataclass
class PricingScenario:
    customers: int
    monthly_price: float
    conversion_rate: float
    churn_rate: float

    def monthly_revenue(self) -> float:
        return self.customers * self.conversion_rate * self.monthly_price


def price_sensitivity(
    base_customers: int,
    base_price: float,
    elasticity: float,
    price_changes: Sequence[float],
) -> List[Tuple[float, float, float]]:
    """
    Simplified constant-elasticity demand model.

    Demand multiplier:
        (1 + price_change)^(-elasticity)

    This is an analytical teaching model, not a substitute for experiments.
    """
    results = []

    for change in price_changes:
        if change <= -1:
            raise ValueError("price change cannot reduce price by 100% or more")

        multiplier = (1 + change) ** (-elasticity)
        customers = base_customers * multiplier
        price = base_price * (1 + change)
        revenue = customers * price

        results.append((change, customers, revenue))

    return results


def explain_pricing() -> None:
    section("7. PRICING AND MONETIZATION")

    print("""
Monetization is the mechanism through which customer value becomes business
revenue.

Common models:

One-time
    Customer pays once.

Subscription
    Customer pays repeatedly over a defined period.

Usage-based
    Customer pays according to consumption.

Transactional
    Revenue occurs per transaction.

Freemium
    A free tier creates adoption while premium features monetize a subset.

Marketplace commission
    Platform takes a percentage of transaction value.

Pricing decisions should consider:
    willingness to pay
    customer value
    competitive alternatives
    variable cost
    gross margin
    price sensitivity
    segmentation
    positioning
    sales friction
    retention impact

Price increases can increase revenue while reducing customer volume. The
important question is the resulting contribution and customer lifetime value,
not simply the percentage price change.
""")

    scenarios = price_sensitivity(
        base_customers=10_000,
        base_price=1000,
        elasticity=1.2,
        price_changes=[-0.20, -0.10, 0.0, 0.10, 0.20, 0.50],
    )

    print("Illustrative price sensitivity:")
    for change, customers, revenue in scenarios:
        print(
            f"Price change={percent(change):>8} | "
            f"customers={customers:>9.0f} | "
            f"revenue={money(revenue)}"
        )


# ============================================================================
# 8. MARKET SEGMENTATION
# ============================================================================

@dataclass
class CustomerSegment:
    name: str
    customers: int
    annual_revenue_per_customer: float
    annual_retention: float
    acquisition_cost: float

    @property
    def annual_revenue(self) -> float:
        return self.customers * self.annual_revenue_per_customer

    @property
    def approximate_lifetime_years(self) -> float:
        churn = 1 - self.annual_retention
        if churn <= 0:
            return float("inf")
        return 1 / churn

    @property
    def approximate_ltv(self) -> float:
        return self.annual_revenue_per_customer * self.approximate_lifetime_years


def rank_segments(segments: Iterable[CustomerSegment]) -> List[CustomerSegment]:
    return sorted(
        segments,
        key=lambda segment: segment.annual_revenue,
        reverse=True,
    )


def explain_segmentation() -> None:
    section("8. CUSTOMER SEGMENTATION")

    print("""
Segmentation divides a broad market into groups with meaningfully different
needs, economics, behaviors, or buying processes.

Useful dimensions include:

Firmographic
    industry, company size, geography, revenue

Demographic
    age, role, income, household characteristics

Behavioral
    usage, purchase frequency, feature adoption, engagement

Needs-based
    problem, job-to-be-done, desired outcome

Economic
    willingness to pay, profitability, service cost

A segment is strategically attractive when it combines:
    meaningful demand
    strong product fit
    reachable customers
    favorable economics
    acceptable competition
    scalable service requirements
""")

    segments = [
        CustomerSegment("SMB", 5000, 20_000, 0.75, 5_000),
        CustomerSegment("Mid-Market", 1200, 100_000, 0.88, 25_000),
        CustomerSegment("Enterprise", 250, 800_000, 0.95, 150_000),
        CustomerSegment("Low-value", 20_000, 2_000, 0.55, 1_500),
    ]

    for segment in rank_segments(segments):
        print(
            f"{segment.name:15} | "
            f"customers={segment.customers:>6,} | "
            f"revenue={money(segment.annual_revenue):>15} | "
            f"retention={percent(segment.annual_retention):>8}"
        )


# ============================================================================
# 9. MARKET SIZE: TAM, SAM, SOM
# ============================================================================

@dataclass
class MarketSizing:
    total_potential_customers: int
    annual_spend_per_customer: float
    serviceable_percentage: float
    achievable_share: float

    @property
    def tam(self) -> float:
        return self.total_potential_customers * self.annual_spend_per_customer

    @property
    def sam(self) -> float:
        return self.tam * self.serviceable_percentage

    @property
    def som(self) -> float:
        return self.sam * self.achievable_share


def explain_market_sizing() -> None:
    section("9. TAM, SAM AND SOM")

    print("""
TAM: Total Addressable Market
    The theoretical revenue opportunity if the business served the entire
    relevant market.

SAM: Serviceable Available Market
    The part of TAM the product can realistically serve based on geography,
    capabilities, customer type, distribution, and constraints.

SOM: Serviceable Obtainable Market
    The portion of SAM the business could reasonably capture.

Market sizing should avoid circular reasoning. A company cannot justify a
large SOM simply by assuming it will acquire a large percentage of customers.
Operational capacity, sales productivity, competition, retention, pricing,
and time horizon should support the estimate.
""")

    market = MarketSizing(
        total_potential_customers=2_000_000,
        annual_spend_per_customer=15_000,
        serviceable_percentage=0.25,
        achievable_share=0.05,
    )

    print(f"TAM: {money(market.tam)}")
    print(f"SAM: {money(market.sam)}")
    print(f"SOM: {money(market.som)}")


# ============================================================================
# 10. MARKET EXPANSION
# ============================================================================

class ExpansionDimension(Enum):
    GEOGRAPHY = "new geography"
    CUSTOMER_SEGMENT = "new customer segment"
    PRODUCT = "new product"
    CHANNEL = "new distribution channel"
    USE_CASE = "new use case"
    VERTICAL = "new industry vertical"


@dataclass
class ExpansionOption:
    name: str
    dimension: ExpansionDimension
    market_size: float
    expected_share: float
    probability: float
    investment: float
    strategic_fit: float

    @property
    def expected_revenue(self) -> float:
        return self.market_size * self.expected_share * self.probability

    @property
    def expected_net_value(self) -> float:
        return self.expected_revenue - self.investment

    @property
    def score(self) -> float:
        return self.expected_net_value * self.strategic_fit


def explain_market_expansion() -> None:
    section("10. MARKET EXPANSION")

    print("""
Market expansion can occur along several dimensions:

1. Geography
   Enter a new city, state, country, or region.

2. Customer segment
   Move from one customer size or demographic group to another.

3. Product expansion
   Add products that solve adjacent customer problems.

4. Distribution channel
   Introduce partners, marketplaces, direct sales, affiliates, retail,
   resellers, or self-service channels.

5. Use-case expansion
   Apply an existing capability to a different problem.

6. Vertical expansion
   Adapt the offering to a new industry.

Expansion should be evaluated against:
    market size
    customer need
    product fit
    regulatory complexity
    localization
    competitive intensity
    acquisition cost
    operational complexity
    expected margin
    required investment
    strategic fit
""")

    options = [
        ExpansionOption(
            "South India",
            ExpansionDimension.GEOGRAPHY,
            800_000_000,
            0.03,
            0.75,
            5_000_000,
            0.85,
        ),
        ExpansionOption(
            "Enterprise",
            ExpansionDimension.CUSTOMER_SEGMENT,
            1_500_000_000,
            0.02,
            0.60,
            12_000_000,
            0.90,
        ),
        ExpansionOption(
            "Partner Channel",
            ExpansionDimension.CHANNEL,
            500_000_000,
            0.05,
            0.80,
            3_000_000,
            0.95,
        ),
    ]

    for option in sorted(options, key=lambda x: x.score, reverse=True):
        print(
            f"{option.name:20} | "
            f"dimension={option.dimension.value:20} | "
            f"expected value={money(option.expected_net_value):>15} | "
            f"score={option.score:,.0f}"
        )


# ============================================================================
# 11. GROWTH STRATEGY MATRIX
# ============================================================================

@dataclass
class GrowthInitiative:
    name: str
    revenue_impact: float
    customer_impact: float
    cost: float
    confidence: float
    strategic_alignment: float

    @property
    def expected_value(self) -> float:
        return (
            (self.revenue_impact + self.customer_impact * 100)
            * self.confidence
            * self.strategic_alignment
            - self.cost
        )


def explain_growth_strategies() -> None:
    section("11. GROWTH STRATEGY OPTIONS")

    print("""
A practical growth strategy can be organized into several levers:

Acquire more customers
    Increase qualified demand and improve acquisition.

Convert more prospects
    Improve landing pages, sales processes, trials, demos, or onboarding.

Retain more customers
    Reduce preventable churn and increase product value.

Expand existing accounts
    Upsell, cross-sell, increase usage, or move customers into higher tiers.

Increase price
    Capture more value where willingness to pay supports it.

Enter new markets
    Expand geographically, vertically, or by segment.

Add products
    Solve adjacent problems for existing or new customers.

Improve distribution
    Add scalable channels and partnerships.

The strongest strategy often combines multiple levers while protecting unit
economics and operational capacity.
""")

    initiatives = [
        GrowthInitiative("Improve activation", 2_000_000, 800, 300_000, 0.85, 0.95),
        GrowthInitiative("Reduce churn", 3_500_000, 0, 600_000, 0.75, 0.98),
        GrowthInitiative("Enterprise sales", 8_000_000, 120, 2_500_000, 0.55, 0.90),
        GrowthInitiative("Partner channel", 5_000_000, 500, 1_000_000, 0.70, 0.85),
    ]

    for initiative in sorted(
        initiatives,
        key=lambda item: item.expected_value,
        reverse=True,
    ):
        print(
            f"{initiative.name:22} | "
            f"expected score/value={initiative.expected_value:,.0f}"
        )


# ============================================================================
# 12. GROWTH ACCOUNTING
# ============================================================================

@dataclass
class CustomerMovement:
    starting_customers: int
    new_customers: int
    reactivated_customers: int
    churned_customers: int

    @property
    def ending_customers(self) -> int:
        return (
            self.starting_customers
            + self.new_customers
            + self.reactivated_customers
            - self.churned_customers
        )

    @property
    def gross_customer_retention(self) -> float:
        return safe_divide(
            self.starting_customers - self.churned_customers,
            self.starting_customers,
        )

    @property
    def net_customer_growth(self) -> float:
        return safe_divide(
            self.ending_customers - self.starting_customers,
            self.starting_customers,
        )


def explain_growth_accounting() -> None:
    section("12. CUSTOMER GROWTH ACCOUNTING")

    print("""
Customer growth is not just acquisition.

A customer base changes through:

    Beginning customers
    + New customers
    + Reactivated customers
    - Churned customers
    = Ending customers

This prevents an important analytical mistake: assuming all customer growth
came from new acquisition.

Reactivation may reveal dormant demand. Churn may indicate poor product fit,
bad onboarding, competitive pressure, pricing issues, or changes in customer
needs.
""")

    movement = CustomerMovement(
        starting_customers=10_000,
        new_customers=2_000,
        reactivated_customers=300,
        churned_customers=1_200,
    )

    print(f"Ending customers: {movement.ending_customers:,}")
    print(f"Gross customer retention: {percent(movement.gross_customer_retention)}")
    print(f"Net customer growth: {percent(movement.net_customer_growth)}")


# ============================================================================
# 13. COHORT ANALYSIS
# ============================================================================

@dataclass
class Cohort:
    name: str
    customers: int
    revenue_by_month: List[float]

    def cumulative_revenue(self) -> float:
        return sum(self.revenue_by_month)

    def revenue_per_original_customer(self) -> float:
        return safe_divide(self.cumulative_revenue(), self.customers)


def cohort_retention_matrix(
    cohorts: Dict[str, Sequence[float]],
) -> Dict[str, List[float]]:
    """Return retention curves without mutating input data."""
    result: Dict[str, List[float]] = {}

    for name, retention in cohorts.items():
        if not retention:
            result[name] = []
            continue

        baseline = retention[0]
        if baseline == 0:
            result[name] = [0.0 for _ in retention]
        else:
            result[name] = [value / baseline for value in retention]

    return result


def explain_cohort_analysis() -> None:
    section("13. COHORT ANALYSIS")

    print("""
Cohort analysis groups customers according to a shared starting event, such
as acquisition month.

Instead of asking:
    "What is our average retention?"

ask:
    "How does each acquisition cohort retain over time?"

Cohorts can reveal:
    improving or deteriorating acquisition quality
    seasonal effects
    onboarding changes
    product changes
    pricing effects
    channel-specific retention

A rising aggregate retention number can be misleading if the customer mix is
changing. Cohorts separate time effects from composition effects.
""")

    cohorts = {
        "Jan": [100, 80, 70, 65, 62],
        "Feb": [100, 83, 74, 69, 66],
        "Mar": [100, 87, 79, 74, 71],
    }

    normalized = cohort_retention_matrix(cohorts)

    for name, values in normalized.items():
        print(
            f"{name}: "
            + ", ".join(percent(value) for value in values)
        )


# ============================================================================
# 14. GROWTH LOOPS
# ============================================================================

def referral_loop(
    initial_users: int,
    invites_per_user: float,
    invite_to_user_rate: float,
    cycles: int,
) -> List[int]:
    """
    Simulate a referral growth loop.

    Each cycle's users create invitations, some of which become new users.
    This is a simplified model and intentionally ignores saturation.
    """
    users = initial_users
    history = [users]

    for _ in range(cycles):
        new_users = int(users * invites_per_user * invite_to_user_rate)
        users += new_users
        history.append(users)

    return history


def explain_growth_loops() -> None:
    section("14. GROWTH LOOPS")

    print("""
A funnel describes a sequence.

A growth loop describes a repeating mechanism where one group of users or
activities produces inputs that create more users or activity.

Example referral loop:

    Users
      ↓
    Invitations
      ↓
    New users
      ↓
    More users who can invite others

Other loops include:
    content -> traffic -> users -> content
    transactions -> supply/data -> better discovery -> more transactions
    usage -> collaboration -> invitations -> more usage

Loops can compound, but the model must account for saturation, declining
conversion, duplicate users, incentives, fraud, and market size.
""")

    history = referral_loop(
        initial_users=1000,
        invites_per_user=2,
        invite_to_user_rate=0.15,
        cycles=8,
    )

    for cycle, users in enumerate(history):
        print(f"Cycle {cycle}: {users:,} users")


# ============================================================================
# 15. VIRALITY
# ============================================================================

def viral_coefficient(
    invitations_per_user: float,
    invitation_conversion_rate: float,
) -> float:
    return invitations_per_user * invitation_conversion_rate


def explain_virality() -> None:
    section("15. VIRALITY AND K-FACTOR")

    print("""
A simplified viral coefficient is:

    K = Invitations per User × Invitation Conversion Rate

If K is above 1 in an idealized model, each generation can create more users
than the previous generation. Real businesses rarely experience unlimited
exponential growth because:

    market size is finite
    invitations overlap
    conversion declines
    users become saturated
    channels have different audiences
    churn removes users
    incentives create artificial behavior

Therefore K should be treated as a diagnostic measurement rather than a
guarantee of viral growth.
""")

    k = viral_coefficient(3, 0.20)
    print(f"Illustrative K-factor: {k:.2f}")


# ============================================================================
# 16. EXPERIMENTATION AND A/B TESTING
# ============================================================================

@dataclass
class ExperimentResult:
    control_successes: int
    control_trials: int
    treatment_successes: int
    treatment_trials: int

    @property
    def control_rate(self) -> float:
        return safe_divide(self.control_successes, self.control_trials)

    @property
    def treatment_rate(self) -> float:
        return safe_divide(self.treatment_successes, self.treatment_trials)

    @property
    def relative_lift(self) -> float:
        return safe_divide(
            self.treatment_rate - self.control_rate,
            self.control_rate,
        )

    @property
    def absolute_lift(self) -> float:
        return self.treatment_rate - self.control_rate


def approximate_two_proportion_z_score(result: ExperimentResult) -> float:
    """
    Approximate z-score for difference between two proportions.

    This is useful for teaching the mechanics. Production experimentation
    should define the statistical design, power, stopping rules, randomization,
    and appropriate inference method before running the experiment.
    """
    p1 = result.control_rate
    p2 = result.treatment_rate

    pooled = safe_divide(
        result.control_successes + result.treatment_successes,
        result.control_trials + result.treatment_trials,
    )

    standard_error = (
        pooled * (1 - pooled)
        * (1 / result.control_trials + 1 / result.treatment_trials)
    ) ** 0.5

    return safe_divide(p2 - p1, standard_error)


def explain_experimentation() -> None:
    section("16. GROWTH EXPERIMENTATION")

    print("""
Growth teams often use controlled experiments to evaluate changes.

A/B testing compares:
    Control = existing experience
    Treatment = changed experience

Important metrics:
    conversion rate
    absolute lift
    relative lift
    revenue per visitor
    retention
    contribution margin

Example:

    Control conversion = 10%
    Treatment conversion = 11%

Absolute lift:
    11% - 10% = 1 percentage point

Relative lift:
    (11% - 10%) / 10% = 10%

These are not the same measurement.

Experiments require:
    randomization
    appropriate sample size
    predefined primary metric
    clear unit of randomization
    guardrail metrics
    avoidance of repeated peeking
    protection against sample-ratio mismatch
    attention to novelty and seasonality
""")

    result = ExperimentResult(
        control_successes=1000,
        control_trials=10_000,
        treatment_successes=1150,
        treatment_trials=10_000,
    )

    z = approximate_two_proportion_z_score(result)

    print(f"Control rate: {percent(result.control_rate)}")
    print(f"Treatment rate: {percent(result.treatment_rate)}")
    print(f"Absolute lift: {percent(result.absolute_lift)}")
    print(f"Relative lift: {percent(result.relative_lift)}")
    print(f"Approximate z-score: {z:.2f}")


# ============================================================================
# 17. FORECASTING
# ============================================================================

def forecast_revenue(
    starting_revenue: float,
    monthly_growth: Sequence[float],
) -> List[float]:
    values = [starting_revenue]
    current = starting_revenue

    for growth in monthly_growth:
        current *= 1 + growth
        values.append(current)

    return values


def forecast_customer_base(
    starting_customers: int,
    monthly_new_customers: Sequence[int],
    monthly_churn_rates: Sequence[float],
) -> List[float]:
    if len(monthly_new_customers) != len(monthly_churn_rates):
        raise ValueError("new-customer and churn-rate series must have equal length")

    customers = float(starting_customers)
    history = [customers]

    for new_customers, churn_rate in zip(
        monthly_new_customers,
        monthly_churn_rates,
    ):
        if not 0 <= churn_rate <= 1:
            raise ValueError("churn rate must be between 0 and 1")

        churned = customers * churn_rate
        customers = customers + new_customers - churned
        history.append(customers)

    return history


def explain_forecasting() -> None:
    section("17. BUSINESS GROWTH FORECASTING")

    print("""
A forecast estimates future business outcomes based on assumptions.

A good forecast separates:

    inputs
        acquisition volume
        conversion
        pricing
        churn
        expansion
        capacity

    from

    outputs
        customers
        revenue
        gross profit
        cash requirements

Do not confuse:
    forecast = expected outcome based on assumptions
    target = desired outcome
    scenario = possible outcome under a defined set of assumptions

Growth forecasts should be scenario-based when uncertainty is high.
""")

    monthly_growth = [0.05, 0.04, 0.06, 0.03, 0.05, 0.04]
    revenue_history = forecast_revenue(10_000_000, monthly_growth)

    for month, value in enumerate(revenue_history):
        print(f"Month {month}: {money(value)}")

    customers = forecast_customer_base(
        starting_customers=10_000,
        monthly_new_customers=[800, 850, 900, 950, 1000, 1050],
        monthly_churn_rates=[0.03, 0.03, 0.029, 0.028, 0.028, 0.027],
    )

    print("\nCustomer forecast:")
    for month, value in enumerate(customers):
        print(f"Month {month}: {value:,.0f}")


# ============================================================================
# 18. SCENARIO PLANNING
# ============================================================================

@dataclass
class Scenario:
    name: str
    acquisition_growth: float
    retention_rate: float
    revenue_per_customer_growth: float
    probability: float

    def projected_revenue_multiplier(self, periods: int) -> float:
        """
        Approximate combined growth in customers and revenue/customer.

        Retention is represented as a simplified multiplier here. Real models
        should explicitly model customer inflow and churn by period.
        """
        customer_multiplier = (1 + self.acquisition_growth) ** periods
        retention_multiplier = self.retention_rate ** max(periods - 1, 0)
        arpc_multiplier = (1 + self.revenue_per_customer_growth) ** periods

        return customer_multiplier * retention_multiplier * arpc_multiplier


def explain_scenarios() -> None:
    section("18. SCENARIO PLANNING")

    print("""
A robust planning model should not depend on one forecast.

Typical scenarios:

Base
    Most reasonable assumptions.

Upside
    Better acquisition, retention, pricing, or expansion.

Downside
    Lower demand, higher churn, pricing pressure, or slower expansion.

Scenario analysis exposes which assumptions drive the largest differences.
Sensitivity analysis then identifies the variables that deserve the most
management attention.
""")

    scenarios = [
        Scenario("Downside", 0.05, 0.94, 0.01, 0.25),
        Scenario("Base", 0.10, 0.96, 0.03, 0.55),
        Scenario("Upside", 0.16, 0.98, 0.05, 0.20),
    ]

    starting_revenue = 50_000_000

    for scenario in scenarios:
        multiplier = scenario.projected_revenue_multiplier(4)
        projected = starting_revenue * multiplier
        print(
            f"{scenario.name:10} | "
            f"multiplier={multiplier:.2f}x | "
            f"projected={money(projected)}"
        )


# ============================================================================
# 19. SENSITIVITY ANALYSIS
# ============================================================================

def sensitivity_table(
    base_customers: int,
    base_arpc: float,
    customer_growth_rates: Sequence[float],
    arpc_growth_rates: Sequence[float],
) -> List[Tuple[float, float, float]]:
    results = []

    for customer_growth in customer_growth_rates:
        for arpc_growth in arpc_growth_rates:
            revenue = (
                base_customers
                * (1 + customer_growth)
                * base_arpc
                * (1 + arpc_growth)
            )
            results.append((customer_growth, arpc_growth, revenue))

    return results


def explain_sensitivity() -> None:
    section("19. SENSITIVITY ANALYSIS")

    print("""
Sensitivity analysis asks:

    "What happens if an important assumption changes?"

For revenue:

    Revenue = Customers × Revenue per Customer

If both drivers change:

    New Revenue =
        Old Customers × (1 + Customer Growth)
        × Old ARPC × (1 + ARPC Growth)

This reveals whether management should prioritize:
    customer acquisition
    retention
    pricing
    upselling
    cross-selling
    product mix
""")

    table = sensitivity_table(
        100_000,
        5000,
        [0.05, 0.10, 0.20],
        [0.00, 0.05, 0.10],
    )

    for customer_growth, arpc_growth, revenue in table:
        print(
            f"Customer growth={percent(customer_growth):>7} | "
            f"ARPC growth={percent(arpc_growth):>7} | "
            f"Revenue={money(revenue)}"
        )


# ============================================================================
# 20. PROFITABLE GROWTH
# ============================================================================

@dataclass
class ProfitabilityModel:
    revenue: float
    variable_cost: float
    sales_marketing: float
    research_development: float
    general_admin: float

    @property
    def contribution_profit(self) -> float:
        return self.revenue - self.variable_cost

    @property
    def operating_profit(self) -> float:
        return (
            self.revenue
            - self.variable_cost
            - self.sales_marketing
            - self.research_development
            - self.general_admin
        )

    @property
    def operating_margin(self) -> float:
        return safe_divide(self.operating_profit, self.revenue)


def explain_profitable_growth() -> None:
    section("20. PROFITABLE GROWTH")

    print("""
Growth quality matters.

A business can increase revenue while:
    gross margin falls
    CAC rises
    churn increases
    support costs increase
    cash burn accelerates
    working capital requirements increase

Contribution margin is useful for evaluating incremental economics.

Operating profit then accounts for broader fixed and semi-fixed expenses.

The correct growth decision depends on the business model. Some businesses
rationally accept lower near-term profitability to build durable distribution,
technology, or market position. The trade-off should be explicit.
""")

    model = ProfitabilityModel(
        revenue=100_000_000,
        variable_cost=40_000_000,
        sales_marketing=25_000_000,
        research_development=15_000_000,
        general_admin=10_000_000,
    )

    print(f"Contribution profit: {money(model.contribution_profit)}")
    print(f"Operating profit: {money(model.operating_profit)}")
    print(f"Operating margin: {percent(model.operating_margin)}")


# ============================================================================
# 21. BREAK-EVEN ANALYSIS
# ============================================================================

def break_even_customers(
    fixed_costs: float,
    price_per_customer: float,
    variable_cost_per_customer: float,
) -> float:
    contribution = price_per_customer - variable_cost_per_customer

    if contribution <= 0:
        raise ValueError("unit contribution must be positive")

    return fixed_costs / contribution


def explain_break_even() -> None:
    section("21. BREAK-EVEN ANALYSIS")

    print("""
Break-even occurs when contribution covers fixed costs.

Break-even customers:

    Fixed Costs
    -------------------------------
    Price per Customer - Variable Cost

This is particularly useful when evaluating:
    new markets
    sales teams
    stores
    manufacturing capacity
    products
    distribution channels

A market may be large but unattractive if contribution margins are too low or
the required scale is operationally unrealistic.
""")

    customers = break_even_customers(
        fixed_costs=20_000_000,
        price_per_customer=50_000,
        variable_cost_per_customer=20_000,
    )

    print(f"Break-even customers: {customers:,.0f}")


# ============================================================================
# 22. SALES CAPACITY
# ============================================================================

@dataclass
class SalesRep:
    annual_capacity: int
    average_deal_value: float
    win_rate: float

    @property
    def annual_revenue_capacity(self) -> float:
        return (
            self.annual_capacity
            * self.win_rate
            * self.average_deal_value
        )


def required_sales_reps(
    target_revenue: float,
    sales_rep_capacity: float,
) -> int:
    if sales_rep_capacity <= 0:
        raise ValueError("sales rep capacity must be positive")
    return ceil(target_revenue / sales_rep_capacity)


def explain_sales_capacity() -> None:
    section("22. SALES CAPACITY AND GROWTH")

    print("""
Growth plans must respect capacity.

For sales-led businesses, revenue depends on:

    qualified opportunities
    sales productivity
    win rate
    average deal size
    sales cycle
    number of productive representatives

A target such as "double revenue" is incomplete unless the business knows
how much additional selling capacity is required.
""")

    rep = SalesRep(
        annual_capacity=120,
        average_deal_value=250_000,
        win_rate=0.25,
    )

    print(f"Revenue capacity/rep: {money(rep.annual_revenue_capacity)}")

    reps = required_sales_reps(
        target_revenue=500_000_000,
        sales_rep_capacity=rep.annual_revenue_capacity,
    )

    print(f"Reps required for target: {reps}")


# ============================================================================
# 23. DISTRIBUTION CHANNEL ECONOMICS
# ============================================================================

@dataclass
class Channel:
    name: str
    customers: int
    cac: float
    average_revenue: float
    gross_margin: float

    @property
    def revenue(self) -> float:
        return self.customers * self.average_revenue

    @property
    def gross_profit(self) -> float:
        return self.revenue * self.gross_margin

    @property
    def acquisition_spend(self) -> float:
        return self.customers * self.cac

    @property
    def gross_profit_after_acquisition(self) -> float:
        return self.gross_profit - self.acquisition_spend


def explain_channels() -> None:
    section("23. DISTRIBUTION CHANNELS")

    print("""
Common acquisition and distribution channels include:

    direct sales
    digital advertising
    organic search
    content
    referrals
    partnerships
    affiliates
    marketplaces
    retail
    resellers
    communities
    outbound sales

A channel should be evaluated on more than volume.

Important dimensions:
    CAC
    customer quality
    conversion
    retention
    gross margin
    sales cycle
    scalability
    operational complexity
    attribution reliability

The cheapest acquisition channel is not automatically the best channel if
its customers churn quickly or generate low contribution.
""")

    channels = [
        Channel("Organic", 3000, 200, 20_000, 0.70),
        Channel("Paid", 5000, 2500, 25_000, 0.68),
        Channel("Partners", 2500, 1200, 30_000, 0.72),
        Channel("Enterprise Sales", 400, 100_000, 900_000, 0.75),
    ]

    for channel in sorted(
        channels,
        key=lambda item: item.gross_profit_after_acquisition,
        reverse=True,
    ):
        print(
            f"{channel.name:20} | "
            f"revenue={money(channel.revenue):>15} | "
            f"GP after CAC={money(channel.gross_profit_after_acquisition):>15}"
        )


# ============================================================================
# 24. PRODUCT-LED GROWTH
# ============================================================================

def product_led_growth_model(
    visitors: int,
    signup_rate: float,
    activation_rate: float,
    paid_conversion_rate: float,
    average_revenue: float,
) -> Dict[str, float]:
    signups = visitors * signup_rate
    activated = signups * activation_rate
    paid = activated * paid_conversion_rate
    revenue = paid * average_revenue

    return {
        "visitors": visitors,
        "signups": signups,
        "activated": activated,
        "paid_customers": paid,
        "revenue": revenue,
    }


def explain_product_led_growth() -> None:
    section("24. PRODUCT-LED GROWTH")

    print("""
Product-led growth uses the product itself as a major acquisition,
activation, conversion, retention, or expansion mechanism.

Typical mechanics:

    visitor
      ↓
    signup
      ↓
    activation
      ↓
    recurring value
      ↓
    conversion
      ↓
    expansion
      ↓
    referral

The key metric is not merely signup volume. Activation and retained usage
determine whether users actually experience value.
""")

    result = product_led_growth_model(
        visitors=100_000,
        signup_rate=0.08,
        activation_rate=0.60,
        paid_conversion_rate=0.25,
        average_revenue=10_000,
    )

    for key, value in result.items():
        if key == "revenue":
            print(f"{key}: {money(value)}")
        else:
            print(f"{key}: {value:,.0f}")


# ============================================================================
# 25. CUSTOMER EXPANSION
# ============================================================================

@dataclass
class AccountExpansion:
    accounts: int
    base_arpa: float
    expansion_rate: float
    expansion_arpa: float

    @property
    def expansion_revenue(self) -> float:
        return (
            self.accounts
            * self.expansion_rate
            * self.expansion_arpa
        )


def explain_expansion() -> None:
    section("25. UPSELL, CROSS-SELL AND ACCOUNT EXPANSION")

    print("""
Existing customers can generate more revenue through:

Upsell
    Moving to a more expensive tier.

Cross-sell
    Buying additional products.

Usage expansion
    Increasing consumption.

Seat expansion
    Adding more users.

Geographic expansion
    Deploying to additional locations.

Contract expansion
    Increasing scope or duration.

Expansion can be economically attractive because customer acquisition has
already occurred. It can also improve retention if the product becomes more
embedded in the customer's operations.
""")

    expansion = AccountExpansion(
        accounts=2000,
        base_arpa=50_000,
        expansion_rate=0.30,
        expansion_arpa=20_000,
    )

    print(f"Potential expansion revenue: {money(expansion.expansion_revenue)}")


# ============================================================================
# 26. CUSTOMER LIFECYCLE
# ============================================================================

class LifecycleStage(Enum):
    ACQUIRED = "acquired"
    ACTIVATED = "activated"
    RETAINED = "retained"
    EXPANDED = "expanded"
    AT_RISK = "at-risk"
    CHURNED = "churned"
    REACTIVATED = "reactivated"


@dataclass
class Customer:
    customer_id: int
    stage: LifecycleStage
    revenue: float
    usage_score: float
    months_active: int


def classify_customer(customer: Customer) -> LifecycleStage:
    """
    Illustrative rule-based classification.

    Real customer-health systems typically use historical behavior, product
    usage, support signals, payment behavior, contract events, and predictive
    models.
    """
    if customer.stage == LifecycleStage.CHURNED:
        return LifecycleStage.CHURNED

    if customer.usage_score < 0.20:
        return LifecycleStage.AT_RISK

    if customer.months_active <= 1:
        return LifecycleStage.ACQUIRED

    if customer.usage_score >= 0.85 and customer.revenue > 100_000:
        return LifecycleStage.EXPANDED

    return LifecycleStage.RETAINED


def explain_lifecycle() -> None:
    section("26. CUSTOMER LIFECYCLE MANAGEMENT")

    print("""
Growth management should treat customers differently based on lifecycle
state.

Acquired
    Recently obtained.

Activated
    Experienced the intended core value.

Retained
    Continues to receive value.

Expanded
    Increased economic relationship.

At-risk
    Signals indicate possible churn.

Churned
    Relationship ended.

Reactivated
    Previously inactive customer returned.

Lifecycle segmentation allows different interventions instead of sending one
generic message to every customer.
""")

    customers = [
        Customer(1, LifecycleStage.ACQUIRED, 10_000, 0.70, 1),
        Customer(2, LifecycleStage.RETAINED, 40_000, 0.80, 12),
        Customer(3, LifecycleStage.RETAINED, 200_000, 0.95, 24),
        Customer(4, LifecycleStage.RETAINED, 20_000, 0.10, 8),
        Customer(5, LifecycleStage.CHURNED, 50_000, 0.00, 10),
    ]

    for customer in customers:
        print(
            f"Customer {customer.customer_id}: "
            f"{classify_customer(customer).value}"
        )


# ============================================================================
# 27. UNIT ECONOMICS BY SEGMENT
# ============================================================================

def segment_unit_economics(
    segments: Sequence[CustomerSegment],
) -> List[Tuple[str, float, float]]:
    results = []

    for segment in segments:
        ltv = segment.approximate_ltv
        ltv_cac = safe_divide(ltv, segment.acquisition_cost)
        results.append((segment.name, ltv, ltv_cac))

    return results


def explain_segment_economics() -> None:
    section("27. SEGMENT-LEVEL ECONOMICS")

    print("""
Averages can hide economically different customer groups.

One segment may have:
    high CAC
    high retention
    high ARPA
    strong expansion

Another may have:
    low CAC
    low retention
    low ARPA
    high support cost

Business growth should therefore evaluate unit economics by:
    customer segment
    channel
    geography
    product
    cohort
    acquisition campaign
""")

    segments = [
        CustomerSegment("SMB", 5000, 20_000, 0.75, 5_000),
        CustomerSegment("Mid-Market", 1200, 100_000, 0.88, 25_000),
        CustomerSegment("Enterprise", 250, 800_000, 0.95, 150_000),
    ]

    for name, ltv, ratio in segment_unit_economics(segments):
        print(f"{name:15} | LTV={money(ltv):>15} | LTV:CAC={ratio:.2f}x")


# ============================================================================
# 28. RETENTION ECONOMICS AND THE COMPOUND EFFECT
# ============================================================================

def retained_fraction(
    initial_customers: int,
    monthly_retention: float,
    months: int,
) -> float:
    return initial_customers * monthly_retention ** months


def explain_compounding_retention() -> None:
    section("28. THE COMPOUND EFFECT OF RETENTION")

    print("""
Small retention differences compound.

If monthly retention is 95%:

    Month 1: 95.00% remain
    Month 12: 95%^12 remain

If retention is 97%, the long-run retained population is materially different.

This is why retention improvements can create substantial downstream effects
on LTV and revenue without requiring proportional increases in acquisition.
""")

    for retention in [0.90, 0.95, 0.97, 0.99]:
        retained = retained_fraction(100_000, retention, 12)
        print(
            f"Monthly retention={percent(retention)} -> "
            f"{retained:,.0f} customers after 12 months"
        )


# ============================================================================
# 29. GO-TO-MARKET STRATEGY
# ============================================================================

@dataclass
class GTMPlan:
    target_segment: str
    value_proposition: str
    acquisition_channels: List[str]
    sales_motion: str
    monetization: PricingModel
    expansion_strategy: str


def explain_gtm() -> None:
    section("29. GO-TO-MARKET STRATEGY")

    print("""
Go-to-market strategy connects:

    target customer
        ↓
    problem/value proposition
        ↓
    positioning
        ↓
    acquisition channel
        ↓
    sales motion
        ↓
    onboarding
        ↓
    retention
        ↓
    expansion

Common sales motions:

Self-service
    Customer discovers and purchases independently.

Inside sales
    Remote sales representatives manage opportunities.

Field sales
    High-touch sales for larger or complex accounts.

Channel sales
    Partners or resellers acquire and serve customers.

Hybrid
    Different segments use different motions.

The correct motion depends on deal complexity, customer value, buying
committee size, implementation requirements, and acquisition economics.
""")

    plan = GTMPlan(
        target_segment="Mid-market technology companies",
        value_proposition="Reduce operational reporting time",
        acquisition_channels=["Content", "Partnerships", "Outbound"],
        sales_motion="Inside sales",
        monetization=PricingModel.SUBSCRIPTION,
        expansion_strategy="Additional teams and modules",
    )

    print(f"Target segment: {plan.target_segment}")
    print(f"Value proposition: {plan.value_proposition}")
    print(f"Channels: {', '.join(plan.acquisition_channels)}")
    print(f"Sales motion: {plan.sales_motion}")
    print(f"Monetization: {plan.monetization.value}")
    print(f"Expansion: {plan.expansion_strategy}")


# ============================================================================
# 30. COMPETITIVE STRATEGY
# ============================================================================

def competitive_positioning_score(
    differentiation: float,
    customer_value: float,
    defensibility: float,
    execution_capability: float,
) -> float:
    values = [
        differentiation,
        customer_value,
        defensibility,
        execution_capability,
    ]

    if any(not 0 <= value <= 10 for value in values):
        raise ValueError("scores must be between 0 and 10")

    return mean(values)


def explain_competitive_strategy() -> None:
    section("30. COMPETITIVE POSITIONING AND DEFENSIBILITY")

    print("""
Growth attracts competition.

A company can defend growth through:
    brand
    product quality
    switching costs
    network effects
    proprietary distribution
    operational excellence
    scale economies
    data advantages
    ecosystem relationships
    customer trust
    regulatory capability
    intellectual property where applicable

Growth without differentiation can lead to price competition and rising CAC.

A useful strategic test is:

    Can competitors copy the growth mechanism quickly?

If yes, the business may need stronger differentiation or a more defensible
distribution advantage.
""")

    score = competitive_positioning_score(8, 9, 7, 8)
    print(f"Illustrative strategic score: {score:.2f}/10")


# ============================================================================
# 31. OPERATIONAL SCALING
# ============================================================================

@dataclass
class CapacityModel:
    current_capacity: int
    demand: int
    capacity_growth: float

    @property
    def future_capacity(self) -> float:
        return self.current_capacity * (1 + self.capacity_growth)

    @property
    def utilization(self) -> float:
        return safe_divide(self.demand, self.current_capacity)


def explain_operational_scaling() -> None:
    section("31. OPERATIONAL SCALING")

    print("""
Growth can expose bottlenecks in:

    hiring
    infrastructure
    customer support
    fulfillment
    inventory
    payment systems
    compliance
    quality control
    onboarding
    account management

A growth strategy is incomplete if operational capacity cannot serve the
customers acquired.

High utilization is not automatically good. Near-100% utilization can reduce
resilience, create delays, and make demand spikes difficult to absorb.
""")

    model = CapacityModel(
        current_capacity=100_000,
        demand=85_000,
        capacity_growth=0.30,
    )

    print(f"Current utilization: {percent(model.utilization)}")
    print(f"Future capacity: {model.future_capacity:,.0f}")


# ============================================================================
# 32. CASH AND WORKING CAPITAL
# ============================================================================

@dataclass
class CashGrowthModel:
    starting_cash: float
    monthly_operating_cash_flow: List[float]

    def ending_cash(self) -> float:
        return self.starting_cash + sum(self.monthly_operating_cash_flow)

    def minimum_cash(self) -> float:
        cash = self.starting_cash
        minimum = cash

        for flow in self.monthly_operating_cash_flow:
            cash += flow
            minimum = min(minimum, cash)

        return minimum


def explain_cash() -> None:
    section("32. CASH REQUIREMENTS FOR GROWTH")

    print("""
Accounting revenue does not equal cash collected.

Fast growth can increase working-capital requirements because the business
may need to finance:

    inventory
    production
    receivables
    sales hiring
    marketing
    implementation
    infrastructure

A company can therefore be profitable on paper while experiencing cash
pressure.

Growth planning should model:
    cash collection
    payment terms
    inventory turns
    accounts receivable
    accounts payable
    capital expenditure
    operating expenses
""")

    cash_model = CashGrowthModel(
        starting_cash=20_000_000,
        monthly_operating_cash_flow=[
            -2_000_000,
            -3_000_000,
            -1_000_000,
            500_000,
            1_500_000,
            2_500_000,
        ],
    )

    print(f"Ending cash: {money(cash_model.ending_cash())}")
    print(f"Minimum cash: {money(cash_model.minimum_cash())}")


# ============================================================================
# 33. MARKET ENTRY DECISION MODEL
# ============================================================================

@dataclass
class MarketEntry:
    market: str
    market_attractiveness: float
    product_fit: float
    competitive_intensity: float
    regulatory_complexity: float
    distribution_access: float
    investment_required: float

    def score(self) -> float:
        """
        Simple weighted score.

        Higher competition and regulatory complexity reduce attractiveness.
        """
        positive = (
            0.30 * self.market_attractiveness
            + 0.30 * self.product_fit
            + 0.20 * self.distribution_access
        )

        negative = (
            0.10 * self.competitive_intensity
            + 0.10 * self.regulatory_complexity
        )

        return positive - negative


def explain_market_entry() -> None:
    section("33. MARKET ENTRY DECISION")

    print("""
A new market should not be evaluated solely by TAM.

Important factors include:

    market attractiveness
    product-market fit
    competitive intensity
    regulatory requirements
    localization
    distribution access
    required investment
    operational complexity
    customer acquisition cost
    expected retention
    strategic adjacency

A weighted score can structure a decision, but the weights should reflect the
company's actual strategy.
""")

    entries = [
        MarketEntry("Market A", 9, 8, 7, 4, 9, 10_000_000),
        MarketEntry("Market B", 8, 6, 5, 2, 6, 7_000_000),
        MarketEntry("Market C", 7, 9, 4, 7, 5, 15_000_000),
    ]

    for entry in sorted(entries, key=lambda item: item.score(), reverse=True):
        print(f"{entry.market}: score={entry.score():.2f}")


# ============================================================================
# 34. RISK-ADJUSTED GROWTH
# ============================================================================

@dataclass
class Risk:
    name: str
    probability: float
    financial_impact: float

    @property
    def expected_loss(self) -> float:
        return self.probability * self.financial_impact


def explain_risk_adjustment() -> None:
    section("34. RISK-ADJUSTED GROWTH")

    print("""
Growth initiatives carry risks.

Examples:
    regulatory changes
    competitor response
    channel dependence
    pricing pressure
    technology failures
    supply constraints
    customer concentration
    fraud
    geopolitical disruption
    execution failure

Expected loss is a simple risk measure:

    Expected Loss = Probability × Financial Impact

It does not capture all strategic risks, but it helps compare initiatives
whose headline revenue opportunities look similar.
""")

    risks = [
        Risk("Competitor response", 0.30, 5_000_000),
        Risk("Regulatory delay", 0.15, 8_000_000),
        Risk("Channel failure", 0.25, 3_000_000),
    ]

    for risk in risks:
        print(
            f"{risk.name:25} | "
            f"expected loss={money(risk.expected_loss)}"
        )


# ============================================================================
# 35. ADVANCED GROWTH METRICS
# ============================================================================

def magic_number(
    current_period_revenue: float,
    prior_period_revenue: float,
    prior_period_sales_marketing_spend: float,
) -> float:
    """
    Simplified SaaS-style magic number.

    Approximation:
        Revenue change × annualization factor / prior S&M spend

    This implementation uses 4 quarters and is illustrative.
    """
    revenue_change = current_period_revenue - prior_period_revenue
    annualized_change = revenue_change * 4
    return safe_divide(annualized_change, prior_period_sales_marketing_spend)


def rule_of_40(
    revenue_growth: float,
    free_cash_flow_margin: float,
) -> float:
    return revenue_growth + free_cash_flow_margin


def explain_advanced_metrics() -> None:
    section("35. ADVANCED GROWTH METRICS")

    print("""
Useful advanced metrics vary by business model.

Rule of 40
    A common SaaS heuristic combines revenue growth and profitability:

        Revenue Growth % + Free Cash Flow Margin %

It is a heuristic, not a law of business performance.

Magic Number
    A sales-and-marketing efficiency diagnostic often used in SaaS contexts.

Gross Revenue Retention (GRR)
    Measures retained recurring revenue excluding expansion.

Net Revenue Retention (NRR)
    Includes expansion and therefore measures the economic evolution of the
    existing customer base.

Payback period
    Time required to recover customer acquisition investment.

Contribution margin
    Revenue minus variable costs associated with serving the business.

Metrics should be interpreted together rather than optimized independently.
""")

    magic = magic_number(
        current_period_revenue=30_000_000,
        prior_period_revenue=25_000_000,
        prior_period_sales_marketing_spend=12_000_000,
    )

    r40 = rule_of_40(0.30, 0.12)

    print(f"Illustrative Magic Number: {magic:.2f}")
    print(f"Illustrative Rule of 40 score: {percent(r40)}")


# ============================================================================
# 36. DATA QUALITY AND GROWTH ANALYTICS
# ============================================================================

def validate_growth_dataset(records: Sequence[Dict[str, float]]) -> List[str]:
    errors: List[str] = []

    required_fields = {
        "revenue",
        "customers",
        "new_customers",
        "churned_customers",
    }

    for index, record in enumerate(records):
        missing = required_fields - record.keys()

        if missing:
            errors.append(
                f"Row {index}: missing fields {sorted(missing)}"
            )
            continue

        for field_name in required_fields:
            value = record[field_name]

            if value < 0:
                errors.append(
                    f"Row {index}: {field_name} cannot be negative"
                )

        if record["churned_customers"] > record["customers"]:
            errors.append(
                f"Row {index}: churned customers exceed ending customers"
            )

    return errors


def explain_data_quality() -> None:
    section("36. GROWTH ANALYTICS AND DATA QUALITY")

    print("""
Growth decisions depend on measurement quality.

Common analytical problems:

    duplicate customers
    inconsistent customer IDs
    missing revenue
    incorrect churn definitions
    mixing bookings and revenue
    mixing gross and net revenue
    inconsistent time zones
    attribution errors
    survivorship bias
    cohort leakage
    changing metric definitions
    counting free users as paying customers
    mixing recognized revenue with cash collections

Metric definitions should be documented.

For example:
    "Churned customer" must have a precise operational definition.
""")

    records = [
        {
            "revenue": 1_000_000,
            "customers": 500,
            "new_customers": 100,
            "churned_customers": 50,
        },
        {
            "revenue": -20,
            "customers": 100,
            "new_customers": 10,
            "churned_customers": 5,
        },
        {
            "revenue": 500_000,
            "customers": 50,
            "new_customers": 10,
            "churned_customers": 100,
        },
    ]

    errors = validate_growth_dataset(records)

    for error in errors:
        print("DATA ERROR:", error)


# ============================================================================
# 37. SECURITY AND FRAUD CONSIDERATIONS
# ============================================================================

def calculate_anomaly_score(
    normal_transactions: Sequence[float],
    transaction: float,
) -> float:
    """
    Basic standardized distance from historical transaction values.

    It is not a production fraud detector.
    """
    if len(normal_transactions) < 2:
        return 0.0

    average = mean(normal_transactions)
    deviation = pstdev(normal_transactions)

    if deviation == 0:
        return 0.0

    return abs(transaction - average) / deviation


def explain_security() -> None:
    section("37. SECURITY, FRAUD AND GROWTH")

    print("""
Growth systems can create security and fraud risks.

Examples:
    fake accounts
    referral abuse
    coupon abuse
    payment fraud
    bot traffic
    account takeover
    synthetic leads
    fraudulent reviews
    marketplace manipulation
    data leakage

Security should not be treated as an afterthought because growth channels
often expose public acquisition and referral surfaces.

Controls can include:
    rate limiting
    identity and account verification where appropriate
    anomaly detection
    abuse monitoring
    fraud rules
    payment controls
    access control
    audit logs
    privacy controls
    separation of production and analytical permissions

A growth metric can be artificially improved by fraudulent activity. Therefore
growth dashboards should distinguish legitimate business activity from abuse.
""")

    history = [100, 110, 95, 105, 108, 102, 107]
    transaction = 300

    score = calculate_anomaly_score(history, transaction)

    print(f"Illustrative transaction anomaly score: {score:.2f} standard deviations")


# ============================================================================
# 38. ETHICAL GROWTH AND CUSTOMER VALUE
# ============================================================================

def customer_value_index(
    retention: float,
    satisfaction: float,
    complaint_rate: float,
    refund_rate: float,
) -> float:
    """
    Simple normalized index for educational purposes.
    """
    return (
        0.40 * retention
        + 0.30 * satisfaction
        + 0.15 * (1 - complaint_rate)
        + 0.15 * (1 - refund_rate)
    )


def explain_responsible_growth() -> None:
    section("38. RESPONSIBLE GROWTH")

    print("""
A growth strategy should create durable customer value.

Warning signs include:
    misleading acquisition
    hidden fees
    intentionally difficult cancellation
    deceptive pricing
    manipulative interfaces
    exploiting vulnerable customers
    excessive notification pressure
    artificial scarcity
    collecting unnecessary personal data

Short-term conversion improvements can create long-term damage if customers
lose trust.

Useful guardrails include:
    refund rates
    complaint rates
    support burden
    cancellation friction
    customer satisfaction
    retention quality
    product outcomes
""")

    index = customer_value_index(
        retention=0.90,
        satisfaction=0.85,
        complaint_rate=0.03,
        refund_rate=0.02,
    )

    print(f"Illustrative customer-value index: {index:.3f}")


# ============================================================================
# 39. STRATEGIC TRADE-OFFS
# ============================================================================

def compare_tradeoffs() -> None:
    section("39. IMPORTANT GROWTH TRADE-OFFS")

    print("""
Revenue growth vs profitability
    Faster acquisition can require greater spending.

Customer growth vs customer quality
    More customers are not necessarily better if retention and contribution
    are poor.

Price vs volume
    Higher prices can reduce volume but increase revenue per customer.

Geographic expansion vs focus
    Expansion increases opportunity while increasing complexity.

Product breadth vs product focus
    More products can create cross-sell opportunities but increase
    engineering, sales, support, and operational complexity.

Growth vs cash
    Faster growth can require more working capital.

Automation vs human service
    Automation improves scalability but can reduce flexibility for complex
    customer needs.

Centralization vs localization
    Centralized processes can create efficiency while local teams may better
    understand regional customers.

Short-term conversion vs long-term trust
    Aggressive tactics can increase immediate conversion while damaging
    retention and reputation.

The right choice depends on strategy, economics, constraints, and time horizon.
""")


# ============================================================================
# 40. COMMON MISTAKES
# ============================================================================

def explain_common_mistakes() -> None:
    section("40. COMMON BUSINESS GROWTH MISTAKES")

    mistakes = [
        (
            "Optimizing revenue alone",
            "Revenue without margin, retention, or cash analysis can produce "
            "low-quality growth.",
        ),
        (
            "Ignoring churn",
            "Acquiring customers while losing existing customers creates a "
            "leaky growth system.",
        ),
        (
            "Using averages only",
            "Segment, cohort, geography, and channel differences can disappear "
            "inside averages.",
        ),
        (
            "Confusing correlation with causation",
            "A metric moving after a change does not prove that the change "
            "caused it.",
        ),
        (
            "Changing too many variables",
            "When multiple interventions happen simultaneously, causal "
            "interpretation becomes difficult.",
        ),
        (
            "Scaling before product-market fit",
            "Increasing acquisition can amplify dissatisfaction and churn.",
        ),
        (
            "Ignoring operational capacity",
            "Demand growth can overwhelm fulfillment, support, or infrastructure.",
        ),
        (
            "Using unrealistic market-share assumptions",
            "A large TAM does not imply an attainable SOM.",
        ),
        (
            "Ignoring customer concentration",
            "Large accounts can create revenue risk if a small number of "
            "customers represent a large percentage of sales.",
        ),
        (
            "Treating forecasts as facts",
            "Forecasts depend on assumptions and should be tested against actuals.",
        ),
    ]

    for mistake, explanation in mistakes:
        print(f"\n{mistake}")
        print(f"  {explanation}")


# ============================================================================
# 41. ADVANCED CUSTOMER CONCENTRATION
# ============================================================================

def customer_concentration(
    revenues: Sequence[float],
    top_n: int,
) -> float:
    if not revenues or top_n <= 0:
        return 0.0

    total = sum(revenues)
    if total <= 0:
        return 0.0

    return sum(sorted(revenues, reverse=True)[:top_n]) / total


def explain_concentration() -> None:
    section("41. CUSTOMER CONCENTRATION")

    print("""
Customer growth can conceal concentration risk.

For example, a business may have thousands of customers but depend heavily
on three enterprise accounts.

Concentration metrics can measure:
    top-1 revenue share
    top-5 revenue share
    top-10 revenue share

High concentration is not automatically bad. Enterprise businesses often
have large customers. The issue is whether the business understands the
associated renewal, pricing, credit, and relationship risk.
""")

    revenues = [
        50_000_000,
        30_000_000,
        20_000_000,
        10_000_000,
        8_000_000,
        7_000_000,
        5_000_000,
    ]

    print(f"Top-1 concentration: {percent(customer_concentration(revenues, 1))}")
    print(f"Top-3 concentration: {percent(customer_concentration(revenues, 3))}")
    print(f"Top-5 concentration: {percent(customer_concentration(revenues, 5))}")


# ============================================================================
# 42. MARKET EXPANSION WITH LOCALIZATION
# ============================================================================

@dataclass
class LocalizationRequirement:
    market: str
    language: bool
    payment_methods: bool
    regulatory_changes: bool
    support_hours: bool
    pricing_adaptation: bool

    def complexity_score(self) -> int:
        return sum(
            [
                self.language,
                self.payment_methods,
                self.regulatory_changes,
                self.support_hours,
                self.pricing_adaptation,
            ]
        )


def explain_localization() -> None:
    section("42. MARKET EXPANSION AND LOCALIZATION")

    print("""
Entering a new geography is rarely a simple copy-paste operation.

Potential localization requirements:
    language
    currency
    taxes
    payment methods
    legal agreements
    data requirements
    customer support hours
    cultural adaptation
    pricing
    sales practices
    product workflows
    regulatory compliance

A market can have strong demand but poor expansion economics if localization
costs are high relative to achievable revenue.
""")

    requirements = LocalizationRequirement(
        market="New Country",
        language=True,
        payment_methods=True,
        regulatory_changes=True,
        support_hours=True,
        pricing_adaptation=True,
    )

    print(f"Localization complexity score: {requirements.complexity_score()}/5")


# ============================================================================
# 43. GROWTH OPERATING SYSTEM
# ============================================================================

@dataclass
class GrowthDashboard:
    revenue: float
    revenue_growth: float
    customers: int
    customer_growth: float
    cac: float
    ltv: float
    churn: float
    nrr: float
    gross_margin: float

    def health_flags(self) -> List[str]:
        flags = []

        if self.revenue_growth < 0:
            flags.append("Revenue is contracting.")

        if self.customer_growth < 0:
            flags.append("Customer base is shrinking.")

        if self.ltv > 0 and self.cac > self.ltv:
            flags.append("CAC exceeds modeled LTV.")

        if self.churn > 0.05:
            flags.append("Churn requires investigation.")

        if self.nrr < 1:
            flags.append("Existing recurring revenue is shrinking.")

        if self.gross_margin < 0.30:
            flags.append("Gross margin may constrain scalable growth.")

        return flags


def explain_growth_operating_system() -> None:
    section("43. THE GROWTH OPERATING SYSTEM")

    print("""
A practical growth operating system connects:

    Strategy
       ↓
    Growth objectives
       ↓
    Metrics
       ↓
    Diagnosis
       ↓
    Initiatives
       ↓
    Experiments
       ↓
    Results
       ↓
    Learning
       ↓
    Resource allocation

A leadership dashboard should contain a limited number of decision-relevant
metrics rather than hundreds of disconnected numbers.

Example categories:

North-star business outcome
    Revenue, gross profit, contribution, or another value-creation metric.

Customer health
    Acquisition, activation, retention, expansion.

Economics
    CAC, LTV, payback, gross margin.

Market
    Segment penetration, geographic performance, market share.

Operational
    Capacity, service levels, fulfillment.

Risk
    Concentration, fraud, regulatory exposure, cash.
""")

    dashboard = GrowthDashboard(
        revenue=100_000_000,
        revenue_growth=0.22,
        customers=20_000,
        customer_growth=0.18,
        cac=10_000,
        ltv=60_000,
        churn=0.025,
        nrr=1.08,
        gross_margin=0.72,
    )

    print("Health flags:")
    flags = dashboard.health_flags()

    if not flags:
        print("  No configured warning thresholds triggered.")
    else:
        for flag in flags:
            print(" ", flag)


# ============================================================================
# 44. MINI CASE STUDY
# ============================================================================

@dataclass
class BusinessCase:
    name: str
    starting_customers: int
    starting_arpc: float
    acquisition_rate: float
    monthly_churn: float
    arpc_growth: float
    gross_margin: float

    def project(self, months: int) -> Dict[str, float]:
        customers = float(self.starting_customers)
        arpc = self.starting_arpc

        for _ in range(months):
            new_customers = customers * self.acquisition_rate
            churned = customers * self.monthly_churn

            customers = customers + new_customers - churned
            arpc *= 1 + self.arpc_growth

        revenue = customers * arpc
        gross_profit = revenue * self.gross_margin

        return {
            "customers": customers,
            "arpc": arpc,
            "revenue": revenue,
            "gross_profit": gross_profit,
        }


def explain_case_study() -> None:
    section("44. INTEGRATED BUSINESS GROWTH CASE STUDY")

    print("""
Consider a subscription business with:

    10,000 starting customers
    ₹5,000 starting monthly ARPC
    4% monthly acquisition growth
    2.5% monthly churn
    1% monthly ARPC growth
    70% gross margin

The model combines customer acquisition, churn, monetization, and margin.
""")

    case = BusinessCase(
        name="Subscription Business",
        starting_customers=10_000,
        starting_arpc=5_000,
        acquisition_rate=0.04,
        monthly_churn=0.025,
        arpc_growth=0.01,
        gross_margin=0.70,
    )

    projection = case.project(12)

    print(f"Customers after 12 months: {projection['customers']:,.0f}")
    print(f"ARPC after 12 months: {money(projection['arpc'])}")
    print(f"Monthly revenue after 12 months: {money(projection['revenue'])}")
    print(f"Monthly gross profit: {money(projection['gross_profit'])}")


# ============================================================================
# 45. INTEGRATED STRATEGIC DECISION
# ============================================================================

@dataclass
class StrategicDecision:
    initiative: str
    expected_incremental_revenue: float
    expected_incremental_gross_profit: float
    implementation_cost: float
    risk_adjustment: float
    strategic_fit: float

    @property
    def risk_adjusted_value(self) -> float:
        return (
            self.expected_incremental_gross_profit
            * self.risk_adjustment
            * self.strategic_fit
            - self.implementation_cost
        )


def choose_growth_initiative(
    initiatives: Sequence[StrategicDecision],
) -> StrategicDecision:
    if not initiatives:
        raise ValueError("at least one initiative is required")

    return max(
        initiatives,
        key=lambda initiative: initiative.risk_adjusted_value,
    )


def explain_integrated_decision() -> None:
    section("45. INTEGRATED GROWTH DECISION MODEL")

    print("""
A leadership team can compare growth initiatives using a combination of:

    incremental revenue
    incremental gross profit
    implementation cost
    probability of success
    strategic fit

The model below deliberately uses gross profit rather than revenue as the
primary economic driver. Revenue without contribution can produce misleading
rankings.
""")

    initiatives = [
        StrategicDecision(
            "Improve retention",
            expected_incremental_revenue=12_000_000,
            expected_incremental_gross_profit=8_000_000,
            implementation_cost=1_500_000,
            risk_adjustment=0.85,
            strategic_fit=0.95,
        ),
        StrategicDecision(
            "New geography",
            expected_incremental_revenue=25_000_000,
            expected_incremental_gross_profit=12_000_000,
            implementation_cost=8_000_000,
            risk_adjustment=0.55,
            strategic_fit=0.80,
        ),
        StrategicDecision(
            "Price optimization",
            expected_incremental_revenue=10_000_000,
            expected_incremental_gross_profit=7_000_000,
            implementation_cost=500_000,
            risk_adjustment=0.75,
            strategic_fit=0.90,
        ),
    ]

    for initiative in initiatives:
        print(
            f"{initiative.initiative:22} | "
            f"risk-adjusted value={money(initiative.risk_adjusted_value)}"
        )

    best = choose_growth_initiative(initiatives)
    print(f"\nIllustrative highest-scoring initiative: {best.initiative}")


# ============================================================================
# 46. TESTS
# ============================================================================

def run_tests() -> None:
    section("46. BUILT-IN VALIDATION TESTS")

    assert compound_growth(100, 0.10, 3) == 133.1
    assert round(annualized_growth_rate(100, 121, 2), 10) == 0.1

    metrics = GrowthMetrics(
        revenue=1_000,
        customers=10,
        new_customers=2,
        churned_customers=1,
        marketing_spend=100,
        gross_profit=600,
        orders=20,
        average_order_value=50,
    )

    assert metrics.revenue_per_customer == 100
    assert round(metrics.gross_margin, 2) == 0.60

    economics = UnitEconomics(
        acquisition_spend=1_000,
        new_customers=10,
        average_revenue_per_customer=100,
        gross_margin=0.50,
        monthly_churn_rate=0.10,
    )

    assert economics.cac == 100
    assert economics.simple_ltv == 500
    assert economics.ltv_to_cac == 5

    movement = CustomerMovement(100, 20, 5, 10)
    assert movement.ending_customers == 115

    assert viral_coefficient(2, 0.25) == 0.5

    records = [
        {
            "revenue": 100,
            "customers": 10,
            "new_customers": 2,
            "churned_customers": 1,
        }
    ]

    assert validate_growth_dataset(records) == []

    try:
        break_even_customers(100, 10, 20)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected break-even validation error")

    print("All built-in tests passed.")


# ============================================================================
# 47. PRACTICAL GROWTH DIAGNOSTIC
# ============================================================================

def growth_diagnostic(
    previous_revenue: float,
    current_revenue: float,
    previous_customers: int,
    current_customers: int,
    cac: float,
    ltv: float,
    churn: float,
    gross_margin: float,
) -> Dict[str, str]:
    """
    Provide a simple diagnostic classification.

    This is intentionally rule-based rather than predictive.
    """
    revenue_growth = safe_divide(
        current_revenue - previous_revenue,
        previous_revenue,
    )

    customer_growth = safe_divide(
        current_customers - previous_customers,
        previous_customers,
    )

    diagnosis: Dict[str, str] = {}

    diagnosis["revenue"] = (
        "growing" if revenue_growth > 0 else "contracting"
    )

    diagnosis["customers"] = (
        "growing" if customer_growth > 0 else "contracting"
    )

    diagnosis["unit_economics"] = (
        "favorable" if ltv > cac else "needs attention"
    )

    diagnosis["retention"] = (
        "strong" if churn < 0.03
        else "moderate" if churn < 0.06
        else "weak"
    )

    diagnosis["margin"] = (
        "healthy" if gross_margin >= 0.60
        else "moderate" if gross_margin >= 0.30
        else "low"
    )

    if revenue_growth > 0 and customer_growth <= 0:
        diagnosis["growth_driver"] = "monetization or mix is likely important"

    elif revenue_growth <= 0 and customer_growth > 0:
        diagnosis["growth_driver"] = "monetization, pricing, or retention needs investigation"

    elif revenue_growth > 0 and customer_growth > 0:
        diagnosis["growth_driver"] = "both customer and revenue growth are positive"

    else:
        diagnosis["growth_driver"] = "business is contracting on both dimensions"

    return diagnosis


def explain_diagnostic() -> None:
    section("47. PRACTICAL GROWTH DIAGNOSTIC")

    print("""
A basic management diagnostic can classify the business across:

    revenue direction
    customer direction
    unit economics
    retention
    gross margin
    likely growth driver

This should trigger investigation, not replace management judgment.
""")

    diagnosis = growth_diagnostic(
        previous_revenue=80_000_000,
        current_revenue=100_000_000,
        previous_customers=15_000,
        current_customers=18_000,
        cac=12_000,
        ltv=75_000,
        churn=0.025,
        gross_margin=0.72,
    )

    for key, value in diagnosis.items():
        print(f"{key:18}: {value}")


# ============================================================================
# 48. EXECUTIVE CHECKLIST
# ============================================================================

def print_executive_checklist() -> None:
    section("48. EXECUTIVE BUSINESS GROWTH CHECKLIST")

    checklist = [
        "Is revenue growing at the required rate?",
        "Is gross profit growing at least as fast as revenue?",
        "Is customer acquisition producing economically attractive customers?",
        "Are retention and churn improving?",
        "Is existing-customer expansion increasing?",
        "Which segments have the strongest economics?",
        "Which channels produce the best retained contribution?",
        "Which customer cohorts are improving or deteriorating?",
        "Is pricing aligned with customer value and willingness to pay?",
        "Is the addressable market sufficiently large?",
        "Can the organization realistically enter the chosen market?",
        "Does operational capacity support the growth target?",
        "Will growth create additional working-capital requirements?",
        "Are the largest growth assumptions supported by evidence?",
        "Which risks could invalidate the plan?",
        "Are fraud, security, privacy, and regulatory risks controlled?",
        "Are experiments measuring causal impact rather than correlation?",
        "Are growth incentives aligned with long-term customer value?",
    ]

    for number, item in enumerate(checklist, 1):
        print(f"{number:2}. {item}")


# ============================================================================
# 49. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the complete educational program.

    Each function is independent enough to be reused in another Python
    application or notebook.
    """
    explain_foundations()
    explain_core_metrics()
    explain_revenue_bridge()
    explain_customer_growth()
    explain_unit_economics()
    explain_retention()
    explain_pricing()
    explain_segmentation()
    explain_market_sizing()
    explain_market_expansion()
    explain_growth_strategies()
    explain_growth_accounting()
    explain_cohort_analysis()
    explain_growth_loops()
    explain_virality()
    explain_experimentation()
    explain_forecasting()
    explain_scenarios()
    explain_sensitivity()
    explain_profitable_growth()
    explain_break_even()
    explain_sales_capacity()
    explain_channels()
    explain_product_led_growth()
    explain_expansion()
    explain_lifecycle()
    explain_segment_economics()
    explain_compounding_retention()
    explain_gtm()
    explain_competitive_strategy()
    explain_operational_scaling()
    explain_cash()
    explain_market_entry()
    explain_risk_adjustment()
    explain_advanced_metrics()
    explain_data_quality()
    explain_security()
    explain_responsible_growth()
    compare_tradeoffs()
    explain_common_mistakes()
    explain_concentration()
    explain_localization()
    explain_growth_operating_system()
    explain_case_study()
    explain_integrated_decision()
    run_tests()
    explain_diagnostic()
    print_executive_checklist()

    print("\n" + "=" * 78)
    print("END OF BUSINESS GROWTH STUDY PROGRAM")
    print("=" * 78)


if __name__ == "__main__":
    main()
