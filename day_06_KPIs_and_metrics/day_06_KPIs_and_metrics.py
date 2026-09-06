"""
KPIs & METRICS
Metrics, KPIs, Targets and Performance Measurement

A self-contained educational study script covering KPI and metric concepts from
absolute beginner through advanced performance measurement.

The script is intentionally executable. Run it directly:

    python kpis_metrics.py

It demonstrates:
- Metrics, measures, dimensions, KPIs and targets
- Leading and lagging indicators
- Input, process, output, outcome and impact measures
- SMART targets
- KPI trees and driver-based measurement
- Financial, operational, customer, product, marketing and people metrics
- Rates, ratios, percentages, averages and weighted averages
- Conversion funnels
- Cohort analysis
- Retention and churn
- Customer lifetime value
- Unit economics
- Productivity and efficiency
- Quality and defect metrics
- SLA measurement
- Statistical variation
- Moving averages
- Growth rates and CAGR
- Target achievement and variance analysis
- Benchmarking
- Scorecards and weighted KPI systems
- Composite indices
- Correlation and causality cautions
- Metric gaming and Goodhart's Law
- Data-quality checks
- Measurement bias
- Thresholds and alerting
- Forecasting
- Scenario analysis
- A/B-test style performance comparison
- Statistical significance using a normal approximation
- Control-chart concepts
- KPI governance
- Executive dashboard design
- Production-oriented implementation principles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import erf, sqrt, log
from statistics import mean, median, pstdev
from typing import Any, Callable, Iterable, Optional, Sequence


# =============================================================================
# 1. FOUNDATIONS
# =============================================================================

def print_title(title: str) -> None:
    """Print a consistent section heading."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subtitle(title: str) -> None:
    """Print a smaller subsection heading."""
    print(f"\n--- {title} ---")


def percentage(value: float, decimals: int = 2) -> str:
    """Format a decimal ratio as a percentage."""
    return f"{value * 100:.{decimals}f}%"


def currency(value: float, decimals: int = 2) -> str:
    """Format a number as a currency-like amount."""
    return f"${value:,.{decimals}f}"


def safe_divide(numerator: float, denominator: float) -> float:
    """
    Divide safely.

    A denominator of zero is a meaningful business/data condition, not a
    reason to silently return zero. Returning NaN makes the undefined result
    explicit while allowing the educational program to continue.
    """
    if denominator == 0:
        return float("nan")
    return numerator / denominator


def is_finite_number(value: float) -> bool:
    """Check whether a numeric result is finite."""
    return value == value and abs(value) != float("inf")


print_title("KPIs & METRICS: METRICS, KPIs, TARGETS AND PERFORMANCE MEASUREMENT")

print(
    """
A metric is a quantified observation.
A KPI (Key Performance Indicator) is a strategically important metric used to
judge progress toward an objective.
A target is the desired level or value of performance.
Performance measurement is the systematic process of collecting, interpreting,
comparing and acting on performance information.

A useful mental model is:

Objective -> Drivers -> Metrics/KPIs -> Targets -> Actuals -> Variance -> Action

Example:
Objective: Increase profitable customer growth
Drivers: acquisition, conversion, retention, pricing, cost
KPIs: qualified leads, conversion rate, retention rate, gross margin
Targets: 10,000 leads, 8% conversion, 85% retention, 35% gross margin
Actuals: measured values for the reporting period
Variance: actual versus target
Action: intervention based on diagnosis
"""
)


# =============================================================================
# 2. TERMINOLOGY
# =============================================================================

@dataclass
class MetricDefinition:
    """Metadata describing a measurable business variable."""

    name: str
    definition: str
    formula: str
    unit: str
    frequency: str = "monthly"
    owner: str = "Unassigned"
    source: str = "Unspecified"
    direction: str = "higher_is_better"
    description: str = ""

    def describe(self) -> None:
        print(f"Name: {self.name}")
        print(f"Definition: {self.definition}")
        print(f"Formula: {self.formula}")
        print(f"Unit: {self.unit}")
        print(f"Frequency: {self.frequency}")
        print(f"Owner: {self.owner}")
        print(f"Source: {self.source}")
        print(f"Direction: {self.direction}")


print_subtitle("Metric terminology")

revenue_metric = MetricDefinition(
    name="Revenue",
    definition="Total recognized sales value during a period",
    formula="sum of recognized sales",
    unit="currency",
    frequency="monthly",
    owner="Finance",
    source="General ledger",
    direction="higher_is_better",
)

conversion_metric = MetricDefinition(
    name="Conversion Rate",
    definition="Proportion of eligible visitors who complete the desired action",
    formula="conversions / eligible visitors",
    unit="ratio",
    frequency="weekly",
    owner="Growth",
    source="Analytics platform",
    direction="higher_is_better",
)

revenue_metric.describe()
print()
conversion_metric.describe()

print(
    """
Important distinctions:

Measure:
    A quantified value, such as 4,250 orders.

Metric:
    A defined measurement, such as orders per day.

KPI:
    A metric selected because it is especially important to a strategic or
    operational objective.

Target:
    A desired value, such as 5,000 orders per day.

Threshold:
    A boundary that triggers attention or action.

Benchmark:
    A comparison point, such as an industry median or historical best.

Dimension:
    A category used to segment a metric, such as country, product, channel,
    customer segment or device type.

Grain:
    The level at which observations are recorded, such as transaction,
    customer-day, order-line or monthly business unit.
"""
)


# =============================================================================
# 3. CLASSIFYING MEASURES
# =============================================================================

class MeasureType(Enum):
    INPUT = "Input"
    PROCESS = "Process"
    OUTPUT = "Output"
    OUTCOME = "Outcome"
    IMPACT = "Impact"


@dataclass
class ClassifiedMeasure:
    name: str
    measure_type: MeasureType
    example: str
    purpose: str


measure_chain = [
    ClassifiedMeasure(
        "Training hours",
        MeasureType.INPUT,
        "Employees receive 20 hours of training",
        "Measures resources invested",
    ),
    ClassifiedMeasure(
        "Average handling time",
        MeasureType.PROCESS,
        "Support ticket handling averages 7 minutes",
        "Measures how work is performed",
    ),
    ClassifiedMeasure(
        "Tickets resolved",
        MeasureType.OUTPUT,
        "12,000 tickets resolved",
        "Measures immediate production",
    ),
    ClassifiedMeasure(
        "Customer resolution satisfaction",
        MeasureType.OUTCOME,
        "92% of customers rate resolution positively",
        "Measures the result experienced by customers",
    ),
    ClassifiedMeasure(
        "Customer retention",
        MeasureType.IMPACT,
        "Annual retention reaches 88%",
        "Measures longer-term organizational effect",
    ),
]

for item in measure_chain:
    print(f"{item.measure_type.value:8} | {item.name:30} | {item.example}")


print_subtitle("Leading versus lagging indicators")

print(
    """
Leading indicators tend to change before the outcome of interest and can be
useful for intervention.

Lagging indicators describe results that have already occurred.

Example:
    Sales revenue              -> lagging
    Qualified sales pipeline   -> leading
    Customer retention         -> lagging
    Product activation         -> potentially leading
    Number of sales calls      -> activity metric, not automatically a KPI

A leading indicator is not automatically useful merely because it occurs early.
It should have a credible relationship with the desired outcome and should be
actionable.
"""
)


# =============================================================================
# 4. CORE CALCULATIONS
# =============================================================================

def growth_rate(current: float, previous: float) -> float:
    """Calculate period-over-period growth."""
    return safe_divide(current - previous, previous)


def target_achievement(
    actual: float,
    target: float,
    direction: str = "higher_is_better",
) -> float:
    """
    Calculate target achievement.

    For higher-is-better measures:
        achievement = actual / target

    For lower-is-better measures:
        achievement = target / actual

    The latter rewards lower actual values.
    """
    if direction == "higher_is_better":
        return safe_divide(actual, target)
    if direction == "lower_is_better":
        return safe_divide(target, actual)
    raise ValueError("direction must be higher_is_better or lower_is_better")


def variance(
    actual: float,
    target: float,
    direction: str = "higher_is_better",
) -> float:
    """Return directional performance variance."""
    if direction == "higher_is_better":
        return actual - target
    if direction == "lower_is_better":
        return target - actual
    raise ValueError("Invalid direction")


def percentage_variance(
    actual: float,
    target: float,
    direction: str = "higher_is_better",
) -> float:
    """Return variance relative to target."""
    return safe_divide(variance(actual, target, direction), abs(target))


print_subtitle("Basic KPI calculations")

monthly_revenue = [100_000, 108_000, 115_000, 123_000]
previous = monthly_revenue[-2]
current = monthly_revenue[-1]

print(f"Previous revenue: {currency(previous)}")
print(f"Current revenue:  {currency(current)}")
print(f"Growth:           {percentage(growth_rate(current, previous))}")

sales_target = 130_000
achievement = target_achievement(current, sales_target)
print(f"Target:            {currency(sales_target)}")
print(f"Achievement:       {percentage(achievement)}")
print(f"Variance:           {currency(variance(current, sales_target))}")
print(
    f"Variance %:         "
    f"{percentage(percentage_variance(current, sales_target))}"
)

response_time = 4.5
response_target = 5.0
print("\nLower-is-better example:")
print(f"Actual response time: {response_time:.2f} hours")
print(f"Target response time: {response_target:.2f} hours")
print(
    "Directional achievement:",
    percentage(
        target_achievement(
            response_time,
            response_target,
            "lower_is_better",
        )
    ),
)


# =============================================================================
# 5. RATES, RATIOS, AVERAGES AND WEIGHTED AVERAGES
# =============================================================================

def rate(events: float, population: float) -> float:
    """General rate: events divided by eligible population."""
    return safe_divide(events, population)


def weighted_average(values: Sequence[float], weights: Sequence[float]) -> float:
    """Calculate a weighted average."""
    if len(values) != len(weights):
        raise ValueError("Values and weights must have equal lengths.")
    total_weight = sum(weights)
    if total_weight == 0:
        return float("nan")
    return sum(value * weight for value, weight in zip(values, weights)) / total_weight


print_subtitle("Rates and weighted averages")

orders = 850
visitors = 10_000
conversion_rate = rate(orders, visitors)
print(f"Orders: {orders}")
print(f"Visitors: {visitors}")
print(f"Conversion rate: {percentage(conversion_rate)}")

regions = ["North", "South", "West"]
regional_conversion_rates = [0.04, 0.08, 0.06]
regional_visitors = [5_000, 1_000, 4_000]

simple_average = mean(regional_conversion_rates)
weighted = weighted_average(
    regional_conversion_rates,
    regional_visitors,
)

print(f"Simple average of regional rates:   {percentage(simple_average)}")
print(f"Visitor-weighted conversion rate:   {percentage(weighted)}")

print(
    """
Why does the distinction matter?

A simple average gives each region equal influence.
A weighted average gives larger populations greater influence.

If one region has 100 customers and another has 100,000 customers, averaging
their conversion rates equally may badly misrepresent the organization's
aggregate conversion performance.
"""
)


# =============================================================================
# 6. KPI DESIGN
# =============================================================================

@dataclass
class KPI:
    """A practical KPI definition."""

    name: str
    objective: str
    definition: str
    formula: str
    target: float
    unit: str
    direction: str
    owner: str
    frequency: str
    data_source: str
    leading_or_lagging: str
    action_when_off_target: str
    exclusions: list[str] = field(default_factory=list)

    def evaluate(self, actual: float) -> dict[str, Any]:
        achievement = target_achievement(actual, self.target, self.direction)
        return {
            "name": self.name,
            "actual": actual,
            "target": self.target,
            "achievement": achievement,
            "variance": variance(actual, self.target, self.direction),
            "status": "On target" if achievement >= 1 else "Below target",
        }


conversion_kpi = KPI(
    name="Qualified Lead Conversion Rate",
    objective="Increase profitable customer acquisition",
    definition="Qualified leads that become customers divided by qualified leads",
    formula="new customers / qualified leads",
    target=0.10,
    unit="ratio",
    direction="higher_is_better",
    owner="Sales",
    frequency="weekly",
    data_source="CRM",
    leading_or_lagging="Leading",
    action_when_off_target="Inspect lead quality, sales velocity and conversion stages",
    exclusions=["Test records", "Duplicate leads"],
)

evaluation = conversion_kpi.evaluate(0.085)
print_subtitle("KPI definition and evaluation")
print(evaluation)

print(
    """
A strong KPI specification normally answers:

1. What objective does it support?
2. What exactly is being measured?
3. What is the mathematical formula?
4. What population is eligible?
5. What data source is authoritative?
6. What is the reporting frequency?
7. Who owns it?
8. What direction is desirable?
9. What is the target?
10. What action should follow when performance deviates?
11. What exclusions or business rules apply?

A metric without a clear definition can create multiple competing versions of
the same number.
"""
)


# =============================================================================
# 7. SMART TARGETS
# =============================================================================

@dataclass
class SMARTTarget:
    metric: str
    specific: str
    measurable: str
    achievable: str
    relevant: str
    time_bound: str

    def validate(self) -> bool:
        fields = [
            self.specific,
            self.measurable,
            self.achievable,
            self.relevant,
            self.time_bound,
        ]
        return all(bool(field.strip()) for field in fields)


smart_target = SMARTTarget(
    metric="Customer retention",
    specific="Increase annual customer retention from 82% to 87%",
    measurable="Calculate retained customers divided by eligible beginning customers",
    achievable="Based on historical improvement and planned retention interventions",
    relevant="Retention improves recurring revenue and reduces replacement acquisition cost",
    time_bound="Reach 87% by the end of Q4",
)

print_subtitle("SMART target example")
print("Valid SMART structure:", smart_target.validate())
for attribute in (
    "specific",
    "measurable",
    "achievable",
    "relevant",
    "time_bound",
):
    print(f"{attribute.title():12}: {getattr(smart_target, attribute)}")


# =============================================================================
# 8. KPI TREES
# =============================================================================

@dataclass
class KPIEquation:
    name: str
    formula: str
    drivers: list[str]


revenue_tree = KPIEquation(
    name="Revenue",
    formula="Customers × Average Revenue per Customer",
    drivers=[
        "Traffic",
        "Lead conversion",
        "Customer conversion",
        "Average order value",
        "Purchase frequency",
    ],
)

print_subtitle("KPI tree")
print(f"{revenue_tree.name} = {revenue_tree.formula}")
for index, driver in enumerate(revenue_tree.drivers, start=1):
    print(f"  Driver {index}: {driver}")

print(
    """
A KPI tree decomposes an outcome into measurable drivers.

For example:

Revenue
├── Number of customers
│   ├── Traffic
│   ├── Lead rate
│   └── Conversion rate
└── Revenue per customer
    ├── Average order value
    └── Purchase frequency

The tree helps prevent a common mistake: managing a final outcome without
understanding which controllable drivers are responsible for it.
"""
)


# =============================================================================
# 9. FUNNEL METRICS
# =============================================================================

def funnel_conversion(stages: Sequence[int]) -> list[float]:
    """Return conversion rates from each funnel stage to the next."""
    if len(stages) < 2:
        return []
    return [
        safe_divide(next_stage, current_stage)
        for current_stage, next_stage in zip(stages, stages[1:])
    ]


def overall_funnel_conversion(stages: Sequence[int]) -> float:
    """Return final-stage divided by first-stage population."""
    if not stages:
        return float("nan")
    return safe_divide(stages[-1], stages[0])


print_subtitle("Conversion funnel")

funnel = [
    100_000,  # visitors
    25_000,   # product-page views
    8_000,    # sign-ups
    3_000,    # activated
    1_200,    # trial users
    600,      # paying customers
]

funnel_names = [
    "Visitors",
    "Product-page views",
    "Sign-ups",
    "Activated",
    "Trial users",
    "Paying customers",
]

stage_rates = funnel_conversion(funnel)

for index, (name, count) in enumerate(zip(funnel_names, funnel)):
    print(f"{name:22}: {count:>8,}")
    if index < len(stage_rates):
        print(f"  Conversion to next: {percentage(stage_rates[index])}")

print(f"Overall visitor-to-customer conversion: {percentage(overall_funnel_conversion(funnel))}")

print(
    """
Funnel analysis should examine both:

- Stage conversion: where is the largest proportional loss?
- Volume: where is the largest absolute loss?

A 50% drop from 100,000 to 50,000 represents 50,000 lost units.
A 90% drop from 1,000 to 100 represents only 900 lost units.

Both may matter, but they imply different interventions.
"""


# =============================================================================
# 10. FINANCIAL METRICS AND UNIT ECONOMICS
# =============================================================================

def gross_profit(revenue: float, cost_of_goods_sold: float) -> float:
    return revenue - cost_of_goods_sold


def gross_margin(revenue: float, cost_of_goods_sold: float) -> float:
    return safe_divide(gross_profit(revenue, cost_of_goods_sold), revenue)


def contribution_margin(
    revenue: float,
    variable_costs: float,
) -> float:
    return safe_divide(revenue - variable_costs, revenue)


def customer_acquisition_cost(
    acquisition_spend: float,
    new_customers: int,
) -> float:
    return safe_divide(acquisition_spend, new_customers)


def average_revenue_per_user(
    revenue: float,
    customers: int,
) -> float:
    return safe_divide(revenue, customers)


def simple_clv(
    average_revenue_per_customer: float,
    gross_margin_rate: float,
    annual_churn_rate: float,
) -> float:
    """
    Simplified CLV approximation.

    CLV ≈ annual revenue per customer × gross margin / annual churn.

    This is a model, not an accounting truth. It assumes a simplified stable
    churn process and ignores discounting, expansion, contraction and many
    cohort effects.
    """
    if annual_churn_rate <= 0:
        return float("inf")
    return (
        average_revenue_per_customer
        * gross_margin_rate
        / annual_churn_rate
    )


print_subtitle("Financial and unit-economics metrics")

financial_revenue = 1_000_000
cogs = 600_000
marketing = 120_000
new_customers = 2_000

gp = gross_profit(financial_revenue, cogs)
gm = gross_margin(financial_revenue, cogs)
cac = customer_acquisition_cost(marketing, new_customers)
arpc = average_revenue_per_user(financial_revenue, new_customers)
clv = simple_clv(arpc, gm, 0.20)

print(f"Revenue:                  {currency(financial_revenue)}")
print(f"COGS:                     {currency(cogs)}")
print(f"Gross profit:             {currency(gp)}")
print(f"Gross margin:             {percentage(gm)}")
print(f"Marketing spend:          {currency(marketing)}")
print(f"New customers:            {new_customers:,}")
print(f"CAC:                      {currency(cac)}")
print(f"Revenue per customer:     {currency(arpc)}")
print(f"Simplified CLV estimate:  {currency(clv)}")
print(f"CLV/CAC ratio:            {clv / cac:.2f}")

print(
    """
Important distinctions:

Revenue:
    Top-line sales recognized according to the applicable accounting rules.

Gross profit:
    Revenue minus cost of goods sold.

Gross margin:
    Gross profit divided by revenue.

Contribution margin:
    Revenue minus variable costs, divided by revenue.

CAC:
    Acquisition-related cost divided by acquired customers, with the cost
    definition explicitly specified.

CLV:
    Estimated economic value of a customer over a defined relationship period.

Unit economics become misleading when numerator and denominator use different
populations, periods or accounting definitions.
"""
)


# =============================================================================
# 11. OPERATIONAL PRODUCTIVITY AND EFFICIENCY
# =============================================================================

def productivity(output: float, input_resource: float) -> float:
    """Output per unit of resource."""
    return safe_divide(output, input_resource)


def efficiency(actual_output: float, expected_output: float) -> float:
    """Actual output relative to expected output."""
    return safe_divide(actual_output, expected_output)


def utilization(productive_hours: float, available_hours: float) -> float:
    """Share of available capacity used productively."""
    return safe_divide(productive_hours, available_hours)


print_subtitle("Productivity, efficiency and utilization")

units_produced = 12_000
labor_hours = 2_000
expected_units = 13_000
productive_hours = 1_600
available_hours = 2_000

print(f"Units per labor hour: {productivity(units_produced, labor_hours):.2f}")
print(f"Output efficiency:    {percentage(efficiency(units_produced, expected_units))}")
print(f"Utilization:          {percentage(utilization(productive_hours, available_hours))}")

print(
    """
These measures are related but not identical.

Productivity asks:
    How much output do we produce per input?

Efficiency asks:
    How does actual output compare with a defined expected level?

Utilization asks:
    How much of available capacity is being used?

High utilization is not automatically good. Sustained 100% utilization can
increase queues, reduce resilience and make the system unable to absorb demand
spikes.
"""
)


# =============================================================================
# 12. QUALITY METRICS
# =============================================================================

def defect_rate(defects: int, total_units: int) -> float:
    return safe_divide(defects, total_units)


def first_pass_yield(good_first_pass: int, total_units: int) -> float:
    return safe_divide(good_first_pass, total_units)


def rework_rate(reworked_units: int, total_units: int) -> float:
    return safe_divide(reworked_units, total_units)


print_subtitle("Quality metrics")

total_units = 50_000
defects = 750
first_pass_good = 46_500
reworked = 2_000

print(f"Defect rate:      {percentage(defect_rate(defects, total_units))}")
print(f"First-pass yield: {percentage(first_pass_yield(first_pass_good, total_units))}")
print(f"Rework rate:      {percentage(rework_rate(reworked, total_units))}")

print(
    """
Quality measurement needs a precise unit of analysis.

Defects per unit, defects per transaction, defects per opportunity and defects
per million opportunities are different metrics.

A low defect rate can also coexist with a high severity rate if rare failures
have very large consequences. Therefore volume and severity should often be
tracked separately.
"""
)


# =============================================================================
# 13. CUSTOMER METRICS
# =============================================================================

def retention_rate(
    customers_start: int,
    customers_end: int,
    new_customers: int,
) -> float:
    """
    Customer retention rate excluding newly acquired customers.

    Retained customers = ending customers - new customers.
    """
    retained = customers_end - new_customers
    return safe_divide(retained, customers_start)


def churn_rate(
    customers_start: int,
    customers_lost: int,
) -> float:
    return safe_divide(customers_lost, customers_start)


def net_promoter_score(promoters: int, detractors: int, total_responses: int) -> float:
    """
    NPS = percentage promoters - percentage detractors.

    This returns the score on the conventional -100 to +100 scale.
    """
    if total_responses == 0:
        return float("nan")
    return (
        (promoters / total_responses) * 100
        - (detractors / total_responses) * 100
    )


print_subtitle("Customer metrics")

customers_start = 10_000
customers_end = 10_500
new_customers = 1_200
lost_customers = 700

print(
    "Retention rate:",
    percentage(retention_rate(customers_start, customers_end, new_customers)),
)
print("Churn rate:", percentage(churn_rate(customers_start, lost_customers)))

nps = net_promoter_score(520, 120, 1_000)
print(f"NPS: {nps:.1f}")

print(
    """
Retention and churn require explicit population definitions.

If 10,000 customers start a period and 1,200 new customers are acquired, an
ending population of 10,500 does not imply 105% retention.

The retained population is:
    ending customers - new customers
    = 10,500 - 1,200
    = 9,300

Retention is therefore:
    9,300 / 10,000 = 93%

NPS is also a survey-derived metric, not a direct measure of revenue or
customer lifetime value. It should be interpreted within its survey design,
response bias and business context.
"""
)


# =============================================================================
# 14. SLA METRICS
# =============================================================================

def sla_compliance(
    observations_within_sla: int,
    total_eligible_observations: int,
) -> float:
    return safe_divide(
        observations_within_sla,
        total_eligible_observations,
    )


def percentile(sorted_values: Sequence[float], p: float) -> float:
    """
    Linear-interpolation percentile.

    p must be between 0 and 100.
    """
    if not sorted_values:
        return float("nan")
    if not 0 <= p <= 100:
        raise ValueError("Percentile must be between 0 and 100.")

    values = sorted(sorted_values)
    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * (p / 100)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


print_subtitle("SLA and service-level measurement")

response_times = [1.1, 1.4, 1.5, 1.7, 1.8, 2.0, 2.1, 2.3, 2.5, 6.0]
sla_limit = 3.0

within_sla = sum(value <= sla_limit for value in response_times)

print(f"SLA compliance: {percentage(sla_compliance(within_sla, len(response_times)))}")
print(f"Median response time: {percentile(response_times, 50):.2f} hours")
print(f"P90 response time:    {percentile(response_times, 90):.2f} hours")
print(f"P95 response time:    {percentile(response_times, 95):.2f} hours")

print(
    """
Average latency can hide tail behavior.

For services, p90, p95 and p99 often reveal customer-impacting delays that an
average does not show.

Example:
    [1, 1, 1, 1, 20]

The average is 4.8, while most users experienced 1 unit of latency and one
user experienced 20.

The appropriate percentile depends on the service objective and risk.
"""
)


# =============================================================================
# 15. TIME SERIES AND MOVING AVERAGES
# =============================================================================

def moving_average(values: Sequence[float], window: int) -> list[float]:
    """Return trailing moving averages."""
    if window <= 0:
        raise ValueError("Window must be positive.")
    if window > len(values):
        return []

    return [
        mean(values[index - window + 1 : index + 1])
        for index in range(window - 1, len(values))
    ]


def compound_annual_growth_rate(
    beginning: float,
    ending: float,
    years: float,
) -> float:
    """Calculate CAGR."""
    if beginning <= 0 or ending < 0 or years <= 0:
        raise ValueError("CAGR requires positive beginning value and years.")
    return (ending / beginning) ** (1 / years) - 1


print_subtitle("Time-series analysis")

monthly_orders = [
    1_000,
    1_050,
    1_020,
    1_100,
    1_180,
    1_150,
    1_220,
    1_300,
]

ma3 = moving_average(monthly_orders, 3)

print("Orders:", monthly_orders)
print("Three-period moving averages:", [round(value, 2) for value in ma3])

cagr = compound_annual_growth_rate(1_000_000, 1_610_510, 5)
print(f"Approximate 5-year CAGR: {percentage(cagr)}")

print(
    """
Moving averages smooth short-term noise.

They are useful for:
- trend monitoring,
- operational dashboards,
- capacity planning,
- anomaly review.

They also introduce lag. A rapidly changing metric can look stable because the
moving average incorporates older observations.

CAGR describes the constant annualized growth rate that would connect a
beginning value to an ending value. It does not mean actual yearly growth was
constant.
"""
)


# =============================================================================
# 16. STATISTICAL VARIATION
# =============================================================================

def z_score(value: float, sample_mean: float, population_std: float) -> float:
    """Calculate a standardized score."""
    if population_std == 0:
        return float("nan")
    return (value - sample_mean) / population_std


def coefficient_of_variation(
    values: Sequence[float],
) -> float:
    """Population coefficient of variation."""
    if not values:
        return float("nan")
    average = mean(values)
    if average == 0:
        return float("nan")
    return pstdev(values) / abs(average)


print_subtitle("Variation and consistency")

daily_sales = [100, 102, 98, 101, 99, 103, 97, 150]
sales_mean = mean(daily_sales)
sales_std = pstdev(daily_sales)
last_day_z = z_score(daily_sales[-1], sales_mean, sales_std)

print(f"Mean daily sales: {sales_mean:.2f}")
print(f"Population standard deviation: {sales_std:.2f}")
print(f"Latest-day z-score: {last_day_z:.2f}")
print(f"Coefficient of variation: {percentage(coefficient_of_variation(daily_sales))}")

print(
    """
Performance should be evaluated using both level and variation.

Two teams can have the same average response time:
    Team A: 2, 2, 2, 2, 2
    Team B: 0.5, 1, 2, 3, 3.5

Their customer experience and operational predictability are different.

A KPI dashboard that shows only averages can miss volatility, instability and
tail events.
"""
)


# =============================================================================
# 17. CORRELATION AND CAUSATION
# =============================================================================

def pearson_correlation(
    x_values: Sequence[float],
    y_values: Sequence[float],
) -> float:
    """Calculate Pearson correlation without external packages."""
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise ValueError("Inputs must have equal length and at least two values.")

    x_mean = mean(x_values)
    y_mean = mean(y_values)

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, y_values)
    )

    x_sum = sum((x - x_mean) ** 2 for x in x_values)
    y_sum = sum((y - y_mean) ** 2 for y in y_values)

    denominator = sqrt(x_sum * y_sum)

    if denominator == 0:
        return float("nan")

    return numerator / denominator


print_subtitle("Correlation is not causation")

advertising = [10, 12, 14, 16, 18, 20]
sales = [100, 110, 125, 128, 145, 160]

correlation = pearson_correlation(advertising, sales)
print(f"Advertising/sales correlation: {correlation:.3f}")

print(
    """
A strong correlation means two variables move together statistically. It does
not prove that one causes the other.

Possible confounders include:
- seasonality,
- price changes,
- market growth,
- promotions,
- competitor behavior,
- customer mix,
- simultaneous operational changes.

KPI decisions should therefore distinguish descriptive measurement from causal
inference.
"""
)


# =============================================================================
# 18. COHORT ANALYSIS
# =============================================================================

@dataclass
class Cohort:
    name: str
    starting_customers: int
    retained_by_period: list[int]

    def retention_curve(self) -> list[float]:
        return [
            safe_divide(retained, self.starting_customers)
            for retained in self.retained_by_period
        ]


print_subtitle("Cohort retention")

cohorts = [
    Cohort("January", 1_000, [1_000, 820, 730, 690, 660]),
    Cohort("February", 1_200, [1_200, 1_020, 900, 840, 810]),
    Cohort("March", 900, [900, 810, 740, 700, 675]),
]

for cohort in cohorts:
    curve = cohort.retention_curve()
    print(
        cohort.name,
        "->",
        ", ".join(percentage(value) for value in curve),
    )

print(
    """
Cohort analysis groups customers according to a shared starting condition,
often acquisition month.

It helps distinguish:
- improving customer quality,
- changes in retention,
- changes in acquisition mix,
- seasonality,
- lifecycle behavior.

A single aggregate retention number can hide deteriorating retention in recent
cohorts because older cohorts may have better historical performance.
"""
)


# =============================================================================
# 19. GROWTH, RETENTION AND NET CHANGE
# =============================================================================

@dataclass
class CustomerPeriod:
    period: str
    beginning: int
    acquired: int
    lost: int

    @property
    def ending(self) -> int:
        return self.beginning + self.acquired - self.lost

    @property
    def net_change(self) -> int:
        return self.acquired - self.lost

    @property
    def churn(self) -> float:
        return safe_divide(self.lost, self.beginning)


customer_periods = [
    CustomerPeriod("January", 10_000, 1_000, 700),
    CustomerPeriod("February", 10_300, 1_100, 800),
    CustomerPeriod("March", 10_600, 1_300, 900),
]

print_subtitle("Customer stock-flow model")

for period in customer_periods:
    print(
        f"{period.period}: "
        f"beginning={period.beginning:,}, "
        f"acquired={period.acquired:,}, "
        f"lost={period.lost:,}, "
        f"ending={period.ending:,}, "
        f"net_change={period.net_change:,}, "
        f"churn={percentage(period.churn)}"
    )

print(
    """
Many business metrics represent stock-flow systems.

For customers:

Ending customers
    = Beginning customers
    + Acquired customers
    - Lost customers

For employees:

Ending headcount
    = Beginning headcount
    + Hires
    - Departures

For inventory:

Ending inventory
    = Beginning inventory
    + Purchases
    - Consumption

Understanding the flow prevents incorrect interpretation of stock metrics.
"""
)


# =============================================================================
# 20. TARGET SETTING AND SCENARIO ANALYSIS
# =============================================================================

def required_growth_rate(
    current: float,
    target: float,
    periods: int,
) -> float:
    """Return constant compound growth needed to reach a target."""
    if current <= 0 or target < 0 or periods <= 0:
        raise ValueError("Inputs must represent a valid growth scenario.")
    return (target / current) ** (1 / periods) - 1


def project_compound_growth(
    current: float,
    growth: float,
    periods: int,
) -> list[float]:
    """Project a metric using a constant compound growth assumption."""
    values = []
    value = current
    for _ in range(periods):
        value *= 1 + growth
        values.append(value)
    return values


print_subtitle("Target feasibility and scenario analysis")

current_users = 50_000
target_users = 80_000
periods = 12

required_monthly_growth = required_growth_rate(
    current_users,
    target_users,
    periods,
)

print(
    "Required monthly compounded growth:",
    percentage(required_monthly_growth),
)

projected = project_compound_growth(
    current_users,
    required_monthly_growth,
    periods,
)

print(f"Projected users after {periods} periods: {projected[-1]:,.0f}")

scenarios = {
    "Conservative": 0.01,
    "Base": 0.03,
    "Aggressive": 0.05,
}

for scenario_name, growth in scenarios.items():
    projection = project_compound_growth(current_users, growth, periods)
    print(
        f"{scenario_name:12}: "
        f"{projection[-1]:,.0f} users"
    )

print(
    """
Scenario analysis separates a target from the assumptions required to achieve
it.

A target of 80,000 users is not operationally complete until its drivers are
understood, such as:
- acquisition volume,
- conversion rate,
- retention,
- product capacity,
- marketing spend,
- sales capacity.

A target that requires implausible driver values is a planning signal, not proof
that teams should simply work harder.
"""
)


# =============================================================================
# 21. SCORECARDS
# =============================================================================

@dataclass
class ScorecardItem:
    name: str
    actual: float
    target: float
    weight: float
    direction: str = "higher_is_better"

    def score(self) -> float:
        return target_achievement(
            self.actual,
            self.target,
            self.direction,
        )


def weighted_scorecard(items: Sequence[ScorecardItem]) -> float:
    """Calculate a weighted KPI score."""
    total_weight = sum(item.weight for item in items)
    if total_weight == 0:
        return float("nan")

    return sum(
        item.score() * item.weight
        for item in items
    ) / total_weight


scorecard = [
    ScorecardItem("Revenue growth", 0.12, 0.10, 0.30),
    ScorecardItem("Gross margin", 0.34, 0.35, 0.25),
    ScorecardItem("Retention", 0.88, 0.85, 0.25),
    ScorecardItem(
        "Response time",
        2.8,
        3.0,
        0.20,
        "lower_is_better",
    ),
]

print_subtitle("Weighted KPI scorecard")

for item in scorecard:
    print(
        f"{item.name:20} "
        f"actual={item.actual:.4f} "
        f"target={item.target:.4f} "
        f"achievement={percentage(item.score())} "
        f"weight={percentage(item.weight)}"
    )

score = weighted_scorecard(scorecard)
print(f"Weighted score: {score:.3f} ({percentage(score)})")

print(
    """
Weighted scorecards aggregate multiple dimensions.

They are useful when leadership needs a balanced view, but they have risks:

1. Weights encode managerial judgment.
2. A high score on one KPI can compensate for a serious failure elsewhere.
3. Different KPI units require normalization.
4. Poorly chosen weights can distort incentives.
5. An aggregate score can hide the individual metrics that explain performance.

Critical safety, compliance or reliability measures may need hard gates rather
than allowing strong commercial performance to compensate for them.
"""
)


# =============================================================================
# 22. NORMALIZATION AND COMPOSITE INDICES
# =============================================================================

def min_max_normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Normalize a value to [0, 1]."""
    if maximum == minimum:
        return float("nan")
    return (value - minimum) / (maximum - minimum)


def inverse_min_max_normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Normalize a lower-is-better measure to [0, 1]."""
    return 1 - min_max_normalize(value, minimum, maximum)


print_subtitle("Normalization")

customer_satisfaction = min_max_normalize(4.3, 1.0, 5.0)
complaint_rate = inverse_min_max_normalize(0.02, 0.0, 0.10)

print(f"Normalized satisfaction: {customer_satisfaction:.3f}")
print(f"Normalized complaint performance: {complaint_rate:.3f}")

print(
    """
Composite indices require normalization because KPIs can have incompatible
units.

For example:
- revenue growth is a percentage,
- response time is measured in hours,
- defects are measured per unit,
- satisfaction may be measured on a 1-5 scale.

Min-max normalization maps values to a common interval, but it is sensitive
to the selected minimum and maximum. Production systems should define whether
those boundaries are historical, theoretical, contractual or benchmark-based.
"""
)


# =============================================================================
# 23. TARGET TYPES
# =============================================================================

print_subtitle("Types of targets")

print(
    """
Common target types:

Absolute target:
    Revenue >= $1,000,000

Rate target:
    Conversion >= 8%

Ratio target:
    CLV/CAC >= 3

Time target:
    P95 response time <= 2 seconds

Growth target:
    Revenue growth >= 15%

Reduction target:
    Defect rate <= 1%

Benchmark target:
    Performance reaches or exceeds the industry 75th percentile

Threshold target:
    Metric must remain inside a safe operating range

Stretch target:
    Ambitious performance level above the committed operating target

Targets should distinguish committed expectations from aspirational scenarios.
"""
)


# =============================================================================
# 24. BENCHMARKING
# =============================================================================

@dataclass
class Benchmark:
    metric: str
    organization_value: float
    benchmark_value: float
    direction: str

    def gap(self) -> float:
        if self.direction == "higher_is_better":
            return self.organization_value - self.benchmark_value
        return self.benchmark_value - self.organization_value

    def relative_position(self) -> float:
        return safe_divide(
            self.organization_value,
            self.benchmark_value,
        )


benchmarks = [
    Benchmark("Conversion", 0.075, 0.08, "higher_is_better"),
    Benchmark("Defect rate", 0.018, 0.012, "lower_is_better"),
    Benchmark("Response time", 2.5, 2.0, "lower_is_better"),
]

print_subtitle("Benchmarking")

for benchmark in benchmarks:
    print(
        f"{benchmark.metric:15} "
        f"value={benchmark.organization_value:.4f} "
        f"benchmark={benchmark.benchmark_value:.4f} "
        f"directional gap={benchmark.gap():.4f}"
    )

print(
    """
Benchmarking can be:

Internal:
    Compare teams, products, regions or periods.

Historical:
    Compare against the organization's own past performance.

Competitive:
    Compare against identified competitors.

External:
    Compare against an industry benchmark.

Functional:
    Compare against organizations performing a similar process even if they
    operate in different industries.

Benchmarks must be comparable. Different definitions, customer populations,
geographies, accounting policies or measurement periods can invalidate an
apparently precise comparison.
"""
)


# =============================================================================
# 25. DATA QUALITY
# =============================================================================

@dataclass
class DataQualityReport:
    total_rows: int
    missing_values: int
    invalid_values: int
    duplicate_rows: int

    @property
    def completeness(self) -> float:
        return safe_divide(
            self.total_rows - self.missing_values,
            self.total_rows,
        )

    @property
    def validity(self) -> float:
        return safe_divide(
            self.total_rows - self.invalid_values,
            self.total_rows,
        )

    @property
    def uniqueness(self) -> float:
        return safe_divide(
            self.total_rows - self.duplicate_rows,
            self.total_rows,
        )


def validate_percentage_values(values: Iterable[float]) -> list[float]:
    """
    Validate ratios that should fall between 0 and 1.

    Invalid values are returned separately by raising an exception here. A
    production pipeline might instead route invalid records to a quarantine
    table.
    """
    validated = []
    for value in values:
        if not 0 <= value <= 1:
            raise ValueError(f"Invalid percentage ratio: {value}")
        validated.append(value)
    return validated


print_subtitle("Data-quality checks")

quality_report = DataQualityReport(
    total_rows=100_000,
    missing_values=250,
    invalid_values=75,
    duplicate_rows=100,
)

print(f"Completeness: {percentage(quality_report.completeness)}")
print(f"Validity:     {percentage(quality_report.validity)}")
print(f"Uniqueness:   {percentage(quality_report.uniqueness)}")

valid_conversion_values = validate_percentage_values([0.01, 0.05, 0.12])
print("Validated conversion ratios:", valid_conversion_values)

print(
    """
A KPI can be mathematically correct while still being operationally wrong if
the underlying data is incomplete or incorrectly defined.

Important data-quality dimensions include:
- accuracy,
- completeness,
- consistency,
- timeliness,
- validity,
- uniqueness,
- lineage.

Data-quality KPIs should themselves be monitored when the business depends on
automated measurement.
"""
)


# =============================================================================
# 26. EDGE CASES
# =============================================================================

print_subtitle("Important mathematical edge cases")

print("10 / 0 ->", safe_divide(10, 0))
print("0 / 10 ->", safe_divide(0, 10))
print("0 / 0 ->", safe_divide(0, 0))

try:
    validate_percentage_values([0.20, 1.20])
except ValueError as error:
    print("Invalid percentage correctly rejected:", error)

try:
    weighted_average([1, 2], [1])
except ValueError as error:
    print("Mismatched weights correctly rejected:", error)

print(
    """
Common edge cases include:

Zero denominator:
    A rate is undefined, not automatically zero.

No eligible population:
    A conversion rate should normally be reported as unavailable rather than
    falsely reporting 0%.

100% conversion:
    Possible, but investigate sample size and measurement logic.

Negative growth:
    Valid when the metric decreases, but interpretation depends on whether
    higher or lower values are desirable.

Lower-is-better metrics:
    Response time, defect rate and cost often require reversed target logic.

Changing definitions:
    A historical trend becomes unreliable when the KPI definition changes
    without a documented methodology break.

Small samples:
    Large percentage changes may be statistically unstable.
"""
)


# =============================================================================
# 27. STATISTICAL CONFIDENCE FOR PROPORTIONS
# =============================================================================

def proportion_standard_error(
    proportion_value: float,
    sample_size: int,
) -> float:
    """Approximate standard error of a binomial proportion."""
    if sample_size <= 0:
        return float("nan")
    return sqrt(
        proportion_value
        * (1 - proportion_value)
        / sample_size
    )


def normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1 + erf(z / sqrt(2)))


def two_proportion_z_test(
    successes_a: int,
    observations_a: int,
    successes_b: int,
    observations_b: int,
) -> dict[str, float]:
    """
    Approximate two-proportion z-test.

    This implementation is educational. Real experimentation systems should
    also consider repeated testing, power, sequential analysis, clustering,
    novelty effects and experiment design.
    """
    if observations_a <= 0 or observations_b <= 0:
        raise ValueError("Observation counts must be positive.")

    p_a = successes_a / observations_a
    p_b = successes_b / observations_b

    pooled = (
        successes_a + successes_b
    ) / (
        observations_a + observations_b
    )

    standard_error = sqrt(
        pooled * (1 - pooled)
        * (
            1 / observations_a
            + 1 / observations_b
        )
    )

    if standard_error == 0:
        return {
            "rate_a": p_a,
            "rate_b": p_b,
            "difference": p_b - p_a,
            "z": float("nan"),
            "p_value": float("nan"),
        }

    z = (p_b - p_a) / standard_error
    two_sided_p = 2 * (1 - normal_cdf(abs(z)))

    return {
        "rate_a": p_a,
        "rate_b": p_b,
        "difference": p_b - p_a,
        "z": z,
        "p_value": two_sided_p,
    }


print_subtitle("Statistical comparison of conversion rates")

experiment = two_proportion_z_test(
    successes_a=480,
    observations_a=10_000,
    successes_b=540,
    observations_b=10_000,
)

for key, value in experiment.items():
    if "rate" in key or key == "difference":
        print(f"{key:12}: {percentage(value)}")
    else:
        print(f"{key:12}: {value:.6f}")

print(
    """
A KPI difference can be caused by random sampling variation.

For proportions, an approximate standard error is:

SE(p) = sqrt[p(1-p)/n]

A statistical test asks whether the observed difference is difficult to explain
under a specified null hypothesis.

Statistical significance is not the same as business significance.

A 0.1 percentage-point improvement can be statistically significant at very
large sample sizes but economically irrelevant.

Conversely, a valuable improvement may fail to reach conventional significance
when the sample is too small.
"""
)


# =============================================================================
# 28. CONTROL LIMITS AND PROCESS STABILITY
# =============================================================================

def control_limits(
    values: Sequence[float],
    sigma_multiplier: float = 3.0,
) -> tuple[float, float, float]:
    """
    Basic Shewhart-style control limits using the mean and population standard
    deviation.

    This simplified calculation assumes independent observations and a
    continuous metric. Real statistical process control may require
    distribution-specific methods, subgrouping and appropriate control charts.
    """
    if len(values) < 2:
        raise ValueError("At least two observations are required.")

    center = mean(values)
    std = pstdev(values)
    upper = center + sigma_multiplier * std
    lower = center - sigma_multiplier * std

    return lower, center, upper


stable_process = [100, 101, 99, 100, 102, 98, 101, 100, 99, 101]
lower, center, upper = control_limits(stable_process)

print_subtitle("Process stability")

print(f"Center line: {center:.2f}")
print(f"Lower limit: {lower:.2f}")
print(f"Upper limit: {upper:.2f}")

new_observation = 115
print(
    f"New observation {new_observation} is outside limits:",
    new_observation < lower or new_observation > upper,
)

print(
    """
A target answers:
    "Where do we want performance to be?"

A control limit answers:
    "What range is consistent with the current process variation?"

They are not interchangeable.

A stable process can consistently miss the business target.
An unstable process can temporarily exceed the target.

Management action differs:
- unstable process -> investigate special causes,
- stable but underperforming process -> redesign or improve the process.
"""
)


# =============================================================================
# 29. FORECASTING
# =============================================================================

def simple_linear_forecast(
    values: Sequence[float],
    periods_ahead: int,
) -> list[float]:
    """
    Forecast using ordinary least squares for y = a + bx.

    This is intentionally simple and dependency-free. It is not a substitute
    for a production forecasting model where seasonality, autocorrelation,
    holidays, promotions and structural breaks matter.
    """
    if len(values) < 2:
        raise ValueError("At least two historical observations are required.")
    if periods_ahead < 0:
        raise ValueError("Forecast horizon cannot be negative.")

    x_values = list(range(len(values)))
    x_mean = mean(x_values)
    y_mean = mean(values)

    numerator = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in zip(x_values, values)
    )
    denominator = sum(
        (x - x_mean) ** 2
        for x in x_values
    )

    slope = safe_divide(numerator, denominator)
    intercept = y_mean - slope * x_mean

    return [
        intercept + slope * (len(values) + offset)
        for offset in range(1, periods_ahead + 1)
    ]


print_subtitle("Basic forecasting")

historical_revenue = [
    100_000,
    103_000,
    108_000,
    111_000,
    116_000,
    121_000,
]

forecast = simple_linear_forecast(historical_revenue, 3)

print("Historical revenue:", [currency(value) for value in historical_revenue])
print("Forecast:", [currency(value) for value in forecast])

print(
    """
Forecasts should be treated as estimates conditional on assumptions.

A straight-line forecast is weak when the metric has:
- seasonality,
- saturation,
- sudden regime changes,
- promotional spikes,
- changing customer mix,
- capacity constraints.

A forecast should therefore include its methodology, horizon, data cutoff,
assumptions and uncertainty rather than presenting one number as certainty.
"""
)


# =============================================================================
# 30. ANOMALY DETECTION
# =============================================================================

def detect_zscore_anomalies(
    values: Sequence[float],
    threshold: float = 3.0,
) -> list[tuple[int, float, float]]:
    """Return index, value and z-score for observations above threshold."""
    if len(values) < 2:
        return []

    average = mean(values)
    std = pstdev(values)

    if std == 0:
        return []

    anomalies = []
    for index, value in enumerate(values):
        score = z_score(value, average, std)
        if abs(score) >= threshold:
            anomalies.append((index, value, score))

    return anomalies


print_subtitle("Anomaly detection")

kpi_series = [
    101, 100, 102, 99, 101, 100, 98,
    103, 102, 100, 101, 160,
]

anomalies = detect_zscore_anomalies(kpi_series, threshold=2.5)

for index, value, score in anomalies:
    print(
        f"Potential anomaly: index={index}, "
        f"value={value}, z-score={score:.2f}"
    )

print(
    """
Anomaly detection should trigger investigation, not automatically trigger
business action.

Possible causes include:
- real business events,
- instrumentation changes,
- duplicate data,
- missing data,
- batch processing,
- seasonal effects,
- fraud,
- system failures.

A detection threshold should reflect the cost of false positives and false
negatives.
"""
)


# =============================================================================
# 31. KPI GOVERNANCE
# =============================================================================

@dataclass
class KPIGovernanceRecord:
    name: str
    owner: str
    executive_sponsor: str
    definition_version: str
    source_of_truth: str
    refresh_schedule: str
    access_level: str
    last_validation_date: str
    known_limitations: list[str]

    def governance_check(self) -> dict[str, bool]:
        return {
            "owner_defined": bool(self.owner),
            "sponsor_defined": bool(self.executive_sponsor),
            "definition_versioned": bool(self.definition_version),
            "source_defined": bool(self.source_of_truth),
            "refresh_defined": bool(self.refresh_schedule),
            "access_defined": bool(self.access_level),
            "validation_recorded": bool(self.last_validation_date),
            "limitations_documented": bool(self.known_limitations),
        }


governance = KPIGovernanceRecord(
    name="Customer Retention",
    owner="Customer Success",
    executive_sponsor="Chief Revenue Officer",
    definition_version="v2.1",
    source_of_truth="Customer data warehouse",
    refresh_schedule="Daily",
    access_level="Internal",
    last_validation_date="2026-08-31",
    known_limitations=[
        "Excludes customers below contractual minimum term",
        "Requires reliable cancellation timestamps",
    ],
)

print_subtitle("KPI governance")
for check, passed in governance.governance_check().items():
    print(f"{check:24}: {'PASS' if passed else 'FAIL'}")

print(
    """
Production KPI governance should establish:

Definition:
    Exact business and mathematical meaning.

Ownership:
    Someone is accountable for the metric's quality and interpretation.

Data lineage:
    Where the metric originates and which transformations occur.

Versioning:
    Definition changes should be documented.

Refresh policy:
    How frequently the KPI is updated.

Access:
    Who can view or modify the underlying data and logic.

Quality controls:
    Automated and manual validation.

Known limitations:
    Conditions under which the KPI should not be interpreted normally.

Auditability:
    Ability to reconstruct how a reported number was produced.
"""
)


# =============================================================================
# 32. KPI CASCADE
# =============================================================================

@dataclass
class KPILevel:
    organizational_level: str
    example_kpis: list[str]


kpi_cascade = [
    KPILevel(
        "Enterprise",
        ["Revenue growth", "Economic profit", "Customer retention"],
    ),
    KPILevel(
        "Business unit",
        ["Market share", "Contribution margin", "New customer growth"],
    ),
    KPILevel(
        "Department",
        ["Qualified pipeline", "Cycle time", "Defect rate"],
    ),
    KPILevel(
        "Team",
        ["Tickets resolved", "First response time", "First-pass yield"],
    ),
    KPILevel(
        "Individual",
        ["Role-specific quality", "Timeliness", "Goal completion"],
    ),
]

print_subtitle("KPI cascade")

for level in kpi_cascade:
    print(
        f"{level.organizational_level:15}: "
        + ", ".join(level.example_kpis)
    )

print(
    """
A KPI cascade links organizational objectives to lower-level drivers.

The cascade should preserve causal relevance without forcing every employee to
own a financial outcome they cannot directly influence.

A team responsible for technical reliability may own:
    uptime, error rate, recovery time.

The enterprise may own:
    revenue, customer retention, economic profit.

The team contributes to the enterprise outcomes, but the measurements should
match the team's actual sphere of control.
"""
)


# =============================================================================
# 33. BALANCED PERFORMANCE MEASUREMENT
# =============================================================================

@dataclass
class PerformanceDimension:
    name: str
    purpose: str
    example_kpis: list[str]


balanced_dimensions = [
    PerformanceDimension(
        "Financial",
        "Economic performance and sustainability",
        ["Revenue growth", "Gross margin", "Cash conversion"],
    ),
    PerformanceDimension(
        "Customer",
        "Value and experience delivered to customers",
        ["Retention", "Conversion", "Customer satisfaction"],
    ),
    PerformanceDimension(
        "Process",
        "Operational quality and speed",
        ["Cycle time", "Defect rate", "SLA compliance"],
    ),
    PerformanceDimension(
        "People",
        "Organizational capability and workforce health",
        ["Capability attainment", "Voluntary attrition", "Productivity"],
    ),
]

print_subtitle("Balanced measurement")

for dimension in balanced_dimensions:
    print(f"{dimension.name}: {dimension.purpose}")
    print("  KPIs:", ", ".join(dimension.example_kpis))

print(
    """
A balanced system avoids optimizing one dimension at the expense of others.

For example:

If a support organization measures only tickets closed:
    agents may close tickets prematurely.

If it measures only satisfaction:
    throughput may collapse.

A balanced design might combine:
    resolution quality,
    customer satisfaction,
    resolution time,
    reopened-ticket rate,
    backlog,
    cost per resolution.

The purpose is not to maximize every KPI independently. It is to optimize the
system under its real constraints.
"""
)


# =============================================================================
# 34. GOODHART'S LAW AND METRIC GAMING
# =============================================================================

@dataclass
class IncentiveRisk:
    metric: str
    possible_behavior: str
    countermeasure: str


gaming_risks = [
    IncentiveRisk(
        "Tickets closed",
        "Close simple tickets while avoiding difficult cases",
        "Track resolution quality, reopen rate and customer outcome",
    ),
    IncentiveRisk(
        "Sales volume",
        "Sell low-quality customers who quickly churn",
        "Track retention, margin and customer quality",
    ),
    IncentiveRisk(
        "Average handling time",
        "Rush conversations and reduce service quality",
        "Track satisfaction, first-contact resolution and repeat contacts",
    ),
    IncentiveRisk(
        "Ad clicks",
        "Optimize for low-value clicks",
        "Track qualified conversion and downstream revenue",
    ),
]

print_subtitle("Metric gaming and Goodhart's Law")

for risk in gaming_risks:
    print(f"Metric: {risk.metric}")
    print(f"  Risk: {risk.possible_behavior}")
    print(f"  Countermeasure: {risk.countermeasure}")

print(
    """
Goodhart's Law is commonly expressed as:

"When a measure becomes a target, it ceases to be a good measure."

The practical lesson is not that targets are useless. It is that a metric used
as an incentive can change the behavior that generated the metric.

Controls include:
- paired quality metrics,
- guardrail metrics,
- outcome metrics,
- audit sampling,
- anomaly detection,
- balanced incentives,
- qualitative review,
- explicit exception handling.

Metric gaming is often a system-design problem rather than simply an employee
ethics problem.
"""
)


# =============================================================================
# 35. GUARDRAIL METRICS
# =============================================================================

@dataclass
class Guardrail:
    name: str
    actual: float
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def passes(self) -> bool:
        if self.minimum is not None and self.actual < self.minimum:
            return False
        if self.maximum is not None and self.actual > self.maximum:
            return False
        return True


guardrails = [
    Guardrail("Customer satisfaction", 0.90, minimum=0.85),
    Guardrail("Defect rate", 0.018, maximum=0.020),
    Guardrail("Critical incident rate", 0.001, maximum=0.002),
]

print_subtitle("Guardrails")

for guardrail in guardrails:
    print(
        f"{guardrail.name:25}: "
        f"actual={guardrail.actual:.4f} "
        f"status={'PASS' if guardrail.passes() else 'FAIL'}"
    )

print(
    """
A guardrail prevents optimization from damaging a critical dimension.

Example:
    Increase conversion rate while keeping fraud rate below a defined ceiling.

The primary KPI can improve while a guardrail fails. The correct response may
be to reject the optimization rather than celebrate the primary KPI.
"""
)


# =============================================================================
# 36. ALERTING LOGIC
# =============================================================================

class AlertLevel(Enum):
    NORMAL = "Normal"
    WARNING = "Warning"
    CRITICAL = "Critical"


def evaluate_alert(
    actual: float,
    target: float,
    warning_gap: float,
    critical_gap: float,
    direction: str = "higher_is_better",
) -> AlertLevel:
    """
    Evaluate a metric against directional target gaps.

    warning_gap and critical_gap are expressed as decimal proportions of target.
    """
    if target == 0:
        raise ValueError("Alert evaluation requires a non-zero target.")

    achievement = target_achievement(actual, target, direction)
    shortfall = 1 - achievement

    if shortfall >= critical_gap:
        return AlertLevel.CRITICAL
    if shortfall >= warning_gap:
        return AlertLevel.WARNING
    return AlertLevel.NORMAL


print_subtitle("Threshold-based alerting")

for actual_value in [0.098, 0.091, 0.075]:
    alert = evaluate_alert(
        actual_value,
        target=0.10,
        warning_gap=0.05,
        critical_gap=0.15,
    )
    print(
        f"Actual={percentage(actual_value):>7} -> "
        f"{alert.value}"
    )

print(
    """
Alerts should be designed around actionability.

A dashboard with hundreds of alerts that do not require action produces alert
fatigue.

A useful alert should define:
- trigger condition,
- severity,
- recipient,
- expected response time,
- owner,
- escalation path,
- suppression logic,
- recovery condition.

The metric itself should be monitored for data failures so a missing data feed
is not mistaken for zero performance.
"""
)


# =============================================================================
# 37. PERFORMANCE REVIEW FUNCTION
# =============================================================================

def performance_review(
    kpi: KPI,
    actual: float,
) -> str:
    """Generate a concise performance interpretation."""
    result = kpi.evaluate(actual)
    achievement = result["achievement"]

    if achievement >= 1.10:
        performance = "materially above target"
    elif achievement >= 1.00:
        performance = "at or above target"
    elif achievement >= 0.90:
        performance = "slightly below target"
    else:
        performance = "materially below target"

    return (
        f"{kpi.name}: actual={actual:.4f}, "
        f"target={kpi.target:.4f}, "
        f"achievement={percentage(achievement)}, "
        f"assessment={performance}. "
        f"Recommended focus: {kpi.action_when_off_target}."
    )


print_subtitle("Automated KPI interpretation")

print(performance_review(conversion_kpi, 0.115))
print(performance_review(conversion_kpi, 0.095))
print(performance_review(conversion_kpi, 0.070))


# =============================================================================
# 38. EXECUTIVE DASHBOARD DESIGN
# =============================================================================

@dataclass
class DashboardCard:
    name: str
    actual: str
    target: str
    trend: str
    status: str
    driver: str


dashboard = [
    DashboardCard(
        "Revenue",
        "$1.23M",
        "$1.30M",
        "+6.9%",
        "Below target",
        "Pipeline conversion",
    ),
    DashboardCard(
        "Retention",
        "88%",
        "85%",
        "+2 pp",
        "Above target",
        "Customer success",
    ),
    DashboardCard(
        "Gross Margin",
        "34%",
        "35%",
        "-1 pp",
        "Below target",
        "Unit costs",
    ),
    DashboardCard(
        "P95 Response Time",
        "2.1h",
        "3.0h",
        "-0.3h",
        "Above target",
        "Staffing and routing",
    ),
]

print_subtitle("Executive dashboard example")

for card in dashboard:
    print(
        f"{card.name:20} | "
        f"Actual {card.actual:>8} | "
        f"Target {card.target:>8} | "
        f"Trend {card.trend:>8} | "
        f"{card.status:15} | "
        f"Driver: {card.driver}"
    )

print(
    """
An executive dashboard should prioritize decision support over decoration.

A useful card usually communicates:
- KPI name,
- current value,
- target,
- trend,
- variance,
- status,
- relevant driver,
- action or owner when appropriate.

Avoid presenting dozens of equally prominent KPIs. Hierarchy matters.

Executives usually need the answer to:
    What happened?
    Why did it happen?
    Does it matter?
    What should be done?
"""
)


# =============================================================================
# 39. COMMON KPI MISTAKES
# =============================================================================

print_subtitle("Common KPI mistakes")

mistakes = [
    (
        "Vanity metrics",
        "A large number looks impressive but does not represent meaningful value.",
    ),
    (
        "Too many KPIs",
        "Excess measurement dilutes attention and accountability.",
    ),
    (
        "Ambiguous definitions",
        "Different teams calculate the same KPI differently.",
    ),
    (
        "No denominator",
        "Counts can be misleading without exposure or population context.",
    ),
    (
        "Wrong aggregation",
        "Averaging rates without appropriate weights produces distorted results.",
    ),
    (
        "Target-only management",
        "Teams chase thresholds without understanding causal drivers.",
    ),
    (
        "Ignoring variation",
        "Averages hide instability and tail behavior.",
    ),
    (
        "Ignoring data quality",
        "Bad inputs create precise-looking but unreliable KPIs.",
    ),
    (
        "No owner",
        "Nobody is accountable for investigating poor performance.",
    ),
    (
        "Metric gaming",
        "Incentives cause behavior that improves the metric but harms the objective.",
    ),
    (
        "Correlation as causation",
        "A relationship is interpreted as proof of causal impact.",
    ),
    (
        "Static targets",
        "Targets remain unchanged despite structural changes in the business.",
    ),
]

for name, explanation in mistakes:
    print(f"{name:28}: {explanation}")


# =============================================================================
# 40. COMPARISON: METRIC VS KPI VS TARGET VS BENCHMARK
# =============================================================================

print_subtitle("Metric versus KPI versus target versus benchmark")

comparison = [
    (
        "Metric",
        "What is measured?",
        "Conversion rate = customers / leads",
    ),
    (
        "KPI",
        "What strategically important measure are we watching?",
        "Qualified lead conversion rate",
    ),
    (
        "Target",
        "What performance level do we want?",
        "10% conversion",
    ),
    (
        "Benchmark",
        "What reference point are we comparing against?",
        "Industry median = 8%",
    ),
    (
        "Threshold",
        "When should action be triggered?",
        "Escalate if conversion < 7%",
    ),
]

for concept, question, example in comparison:
    print(f"{concept:10} | {question:45} | {example}")


# =============================================================================
# 41. ADVANCED PERFORMANCE MODEL
# =============================================================================

@dataclass
class PerformanceModel:
    """
    A compact model connecting outcomes, drivers, targets and guardrails.
    """

    outcome_name: str
    outcome_actual: float
    outcome_target: float
    drivers: dict[str, float]
    guardrails: list[Guardrail]

    def outcome_achievement(self) -> float:
        return target_achievement(
            self.outcome_actual,
            self.outcome_target,
        )

    def all_guardrails_pass(self) -> bool:
        return all(guardrail.passes() for guardrail in self.guardrails)

    def evaluate(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome_name,
            "achievement": self.outcome_achievement(),
            "drivers": self.drivers,
            "guardrails_pass": self.all_guardrails_pass(),
        }


advanced_model = PerformanceModel(
    outcome_name="Monthly recurring revenue",
    outcome_actual=1_180_000,
    outcome_target=1_200_000,
    drivers={
        "new_logo_revenue": 300_000,
        "expansion_revenue": 80_000,
        "contraction_revenue": -40_000,
        "churned_revenue": -60_000,
    },
    guardrails=[
        Guardrail("Gross margin", 0.34, minimum=0.30),
        Guardrail("Critical incident rate", 0.001, maximum=0.003),
    ],
)

print_subtitle("Integrated performance model")

print(advanced_model.evaluate())

print(
    """
Advanced measurement connects three layers:

Outcome layer:
    Did the business objective improve?

Driver layer:
    Which controllable factors explain the movement?

Guardrail layer:
    Did the improvement violate an important constraint?

This structure is more useful than treating every metric as an independent
score.
"""
)


# =============================================================================
# 42. IMPLEMENTATION PATTERN
# =============================================================================

class KPIRegistry:
    """
    Small in-memory registry illustrating how KPI metadata can be centralized.

    A production registry might store this information in a database or
    governed semantic layer and connect it to a warehouse and BI platform.
    """

    def __init__(self) -> None:
        self._kpis: dict[str, KPI] = {}

    def register(self, kpi: KPI) -> None:
        if kpi.name in self._kpis:
            raise ValueError(f"KPI already registered: {kpi.name}")
        self._kpis[kpi.name] = kpi

    def get(self, name: str) -> KPI:
        try:
            return self._kpis[name]
        except KeyError as error:
            raise KeyError(f"Unknown KPI: {name}") from error

    def list_names(self) -> list[str]:
        return sorted(self._kpis)

    def evaluate(self, name: str, actual: float) -> dict[str, Any]:
        return self.get(name).evaluate(actual)


registry = KPIRegistry()
registry.register(conversion_kpi)

print_subtitle("KPI registry")
print("Registered KPIs:", registry.list_names())
print("Evaluation:", registry.evaluate("Qualified Lead Conversion Rate", 0.11))

print(
    """
A governed KPI registry prevents duplicated definitions.

In a production architecture, a registry can contain:
- KPI ID,
- name,
- business definition,
- SQL or semantic expression,
- owner,
- source tables,
- refresh frequency,
- dimensionality,
- target,
- thresholds,
- access classification,
- version,
- effective date,
- deprecation date,
- validation rules.

The registry should be treated as a controlled definition layer, not merely a
list of dashboard labels.
"""
)


# =============================================================================
# 43. PERFORMANCE AND COMPUTATIONAL CONSIDERATIONS
# =============================================================================

print_subtitle("Performance considerations")

print(
    """
For small educational calculations, ordinary Python data structures are
sufficient.

For production-scale KPI systems:

1. Push aggregation toward the analytical database.
2. Avoid repeatedly scanning billions of raw events.
3. Partition data by appropriate time dimensions.
4. Materialize frequently used aggregates where justified.
5. Use incremental pipelines when full recomputation is unnecessary.
6. Cache stable dashboard queries.
7. Monitor query latency and pipeline freshness.
8. Separate raw event storage from governed analytical models.
9. Test metric logic against representative data volumes.
10. Preserve reproducibility when late-arriving data changes historical values.

Performance optimization must not silently change metric semantics.
"""
)


# =============================================================================
# 44. SECURITY AND ACCESS CONTROL
# =============================================================================

print_subtitle("Security considerations")

print(
    """
KPI systems may expose sensitive business or personal information.

Important controls include:

- role-based access control,
- least-privilege permissions,
- row-level security where appropriate,
- column-level protection for sensitive attributes,
- encryption in transit and at rest,
- audit logging,
- credential rotation,
- controlled exports,
- data retention policies,
- environment separation,
- secure secrets management.

A dashboard can be statistically correct and still be insecure if it exposes
customer-level records to users who should only see aggregated metrics.

Performance data can also reveal commercially sensitive information such as
pricing, margins, customer concentration and operational capacity.
"""
)


# =============================================================================
# 45. TESTS
# =============================================================================

def approximately_equal(
    actual: float,
    expected: float,
    tolerance: float = 1e-9,
) -> bool:
    return abs(actual - expected) <= tolerance


def run_tests() -> None:
    """Run core correctness tests."""
    assert approximately_equal(rate(10, 100), 0.10)
    assert approximately_equal(growth_rate(110, 100), 0.10)
    assert approximately_equal(
        gross_margin(100, 60),
        0.40,
    )
    assert approximately_equal(
        retention_rate(100, 105, 15),
        0.90,
    )
    assert approximately_equal(
        first_pass_yield(90, 100),
        0.90,
    )
    assert approximately_equal(
        min_max_normalize(5, 0, 10),
        0.50,
    )
    assert approximately_equal(
        inverse_min_max_normalize(2, 0, 10),
        0.80,
    )

    moving = moving_average([1, 2, 3, 4], 2)
    assert moving == [1.5, 2.5, 3.5]

    assert target_achievement(
        110,
        100,
        "higher_is_better",
    ) == 1.1

    assert target_achievement(
        90,
        100,
        "lower_is_better",
    ) == 100 / 90

    assert (
        weighted_average(
            [10, 20],
            [1, 3],
        )
        == 17.5
    )

    assert (
        overall_funnel_conversion([100, 50, 10])
        == 0.10
    )


print_subtitle("Automated correctness tests")
run_tests()
print("All core tests passed.")


# =============================================================================
# 46. CAPSTONE EXAMPLE
# =============================================================================

@dataclass
class BusinessPerformance:
    """Integrated business-performance example."""

    revenue: float
    revenue_target: float
    gross_margin_rate: float
    gross_margin_target: float
    retention_rate_value: float
    retention_target: float
    conversion_rate_value: float
    conversion_target: float
    response_time: float
    response_time_target: float

    def evaluate(self) -> dict[str, dict[str, Any]]:
        return {
            "Revenue": {
                "actual": self.revenue,
                "target": self.revenue_target,
                "achievement": target_achievement(
                    self.revenue,
                    self.revenue_target,
                ),
            },
            "Gross margin": {
                "actual": self.gross_margin_rate,
                "target": self.gross_margin_target,
                "achievement": target_achievement(
                    self.gross_margin_rate,
                    self.gross_margin_target,
                ),
            },
            "Retention": {
                "actual": self.retention_rate_value,
                "target": self.retention_target,
                "achievement": target_achievement(
                    self.retention_rate_value,
                    self.retention_target,
                ),
            },
            "Conversion": {
                "actual": self.conversion_rate_value,
                "target": self.conversion_target,
                "achievement": target_achievement(
                    self.conversion_rate_value,
                    self.conversion_target,
                ),
            },
            "Response time": {
                "actual": self.response_time,
                "target": self.response_time_target,
                "achievement": target_achievement(
                    self.response_time,
                    self.response_time_target,
                    "lower_is_better",
                ),
            },
        }


business = BusinessPerformance(
    revenue=1_180_000,
    revenue_target=1_200_000,
    gross_margin_rate=0.34,
    gross_margin_target=0.35,
    retention_rate_value=0.88,
    retention_target=0.85,
    conversion_rate_value=0.075,
    conversion_target=0.08,
    response_time=2.1,
    response_time_target=3.0,
)

print_subtitle("Capstone: integrated KPI review")

business_results = business.evaluate()

for metric_name, result in business_results.items():
    print(
        f"{metric_name:20} "
        f"actual={result['actual']:.4f} "
        f"target={result['target']:.4f} "
        f"achievement={percentage(result['achievement'])}"
    )

print(
    """
Interpretation:

Revenue is below target.
Gross margin is below target.
Retention is above target.
Conversion is below target.
Response time is better than target because lower is better.

A disciplined performance review should not conclude merely that "performance
is bad" or "performance is good." It should identify the specific dimensions
that require investigation and connect them to drivers.

A sensible sequence is:

1. Validate the data.
2. Confirm KPI definitions and population.
3. Compare actuals with targets.
4. Examine trend and variation.
5. Segment by relevant dimensions.
6. Identify likely drivers.
7. Check guardrails.
8. Distinguish correlation from causal evidence.
9. Decide on intervention.
10. Assign an owner and expected outcome.
11. Monitor the result.
12. Record methodology changes.

This is the operating discipline behind useful performance measurement.
"""
)


# =============================================================================
# 47. FINAL STUDY CHECKLIST
# =============================================================================

print_subtitle("KPI study checklist")

checklist = [
    "Can you distinguish a metric from a KPI?",
    "Can you define a KPI mathematically and operationally?",
    "Can you identify the correct denominator?",
    "Can you distinguish leading and lagging indicators?",
    "Can you distinguish input, process, output, outcome and impact measures?",
    "Can you calculate growth and target variance?",
    "Can you handle lower-is-better metrics?",
    "Can you explain weighted versus unweighted averages?",
    "Can you analyze a conversion funnel?",
    "Can you calculate retention, churn, CAC and gross margin?",
    "Can you explain why averages can hide tail behavior?",
    "Can you perform cohort analysis?",
    "Can you explain correlation versus causation?",
    "Can you recognize metric gaming?",
    "Can you design guardrails?",
    "Can you explain target versus control limit?",
    "Can you identify data-quality problems?",
    "Can you explain statistical versus business significance?",
    "Can you design a governed KPI definition?",
    "Can you connect an outcome KPI to its drivers?",
]

for index, question in enumerate(checklist, start=1):
    print(f"{index:2}. {question}")


# =============================================================================
# 48. REUSABLE KPI TEMPLATE
# =============================================================================

print_subtitle("Reusable KPI specification template")

template = {
    "KPI name": "",
    "business objective": "",
    "business question": "",
    "definition": "",
    "formula": "",
    "numerator": "",
    "denominator": "",
    "eligible population": "",
    "unit": "",
    "direction": "higher_is_better / lower_is_better",
    "target": "",
    "warning threshold": "",
    "critical threshold": "",
    "owner": "",
    "data source": "",
    "dimensions": "",
    "reporting frequency": "",
    "leading_or_lagging": "",
    "guardrails": "",
    "known limitations": "",
    "definition version": "",
}

for field_name in template:
    print(f"{field_name:24}: {template[field_name]}")


# =============================================================================
# 49. END-TO-END PRINCIPLES
# =============================================================================

print_title("END-TO-END PERFORMANCE MEASUREMENT PRINCIPLES")

print(
    """
1. Start with the objective, not the available data.

2. Measure what matters to the objective, not everything that can be measured.

3. Define the numerator, denominator, population, period and exclusions.

4. Separate descriptive metrics from KPIs.

5. Pair outcome measures with actionable driver measures.

6. Use leading indicators when intervention before the outcome is valuable.

7. Use lagging indicators to verify whether the desired result actually occurred.

8. Treat targets as management commitments or planning assumptions, not
   universal truths.

9. Use directional logic for lower-is-better metrics.

10. Segment metrics when aggregate values hide important differences.

11. Use weighted averages when the business question requires population-level
    performance.

12. Monitor distributions and percentiles when averages hide customer impact.

13. Track variation and process stability, not just level.

14. Validate data quality before interpreting KPI movement.

15. Treat statistical significance and business significance as different
    questions.

16. Do not infer causality from correlation alone.

17. Use guardrails to prevent local optimization from damaging system outcomes.

18. Expect incentives to influence behavior.

19. Version KPI definitions and preserve data lineage.

20. Assign clear ownership and define the action associated with a threshold.

21. Design dashboards for decisions rather than information volume.

22. Keep critical KPIs understandable enough that their meaning can be explained
    without relying on undocumented institutional knowledge.

23. Reassess KPI relevance when strategy, products, customers, processes or data
    definitions change.

24. Optimize the measurement system for decision quality, not for producing
    impressive numbers.

A mature KPI system connects strategy, measurement, analysis, accountability and
action into one coherent management process.
"""
)

print("\nStudy script execution completed successfully.")
