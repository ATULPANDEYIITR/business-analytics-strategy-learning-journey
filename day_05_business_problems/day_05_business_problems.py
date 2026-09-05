"""
BUSINESS PROBLEMS: IDENTIFYING BUSINESS PROBLEMS AND ANALYTICAL OPPORTUNITIES
=============================================================================

A comprehensive, self-contained study script.

This script teaches how organizations identify business problems, distinguish
symptoms from root causes, frame analytical opportunities, define measurable
questions, select metrics, perform exploratory analysis, prioritize problems,
and translate analytical findings into business decisions.

The examples use only the Python standard library so that the script can run
without external dependencies.

Business analytics commonly follows this chain:

    Business Context
            |
            v
    Observed Symptom
            |
            v
    Business Problem Definition
            |
            v
    Root Cause Investigation
            |
            v
    Analytical Opportunity
            |
            v
    Data and Metric Selection
            |
            v
    Analysis
            |
            v
    Insight
            |
            v
    Decision and Action
            |
            v
    Measurement of Business Impact
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Callable, Dict, List, Optional, Tuple
import math
import random


# =============================================================================
# SECTION 1: FUNDAMENTAL CONCEPTS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 1: FUNDAMENTAL CONCEPTS")
print("=" * 80)


# A business problem is an undesirable gap between the current state and a
# desired business state.

current_revenue = 850_000
target_revenue = 1_000_000

revenue_gap = target_revenue - current_revenue

print(f"Current revenue: {current_revenue:,}")
print(f"Target revenue:  {target_revenue:,}")
print(f"Business gap:    {revenue_gap:,}")


# A business problem is different from a symptom.
#
# Symptom:
#     "Sales are declining."
#
# Possible underlying problems:
#     - Customer acquisition has decreased.
#     - Customer churn has increased.
#     - Conversion rate has decreased.
#     - Average order value has decreased.
#     - Product availability has decreased.
#     - Competitors have reduced prices.
#
# Analytical work should avoid treating the first visible symptom as the
# confirmed root cause.


# =============================================================================
# SECTION 2: BUSINESS PROBLEM STRUCTURE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 2: STRUCTURING A BUSINESS PROBLEM")
print("=" * 80)


@dataclass
class BusinessProblem:
    """
    Represents a structured business problem.

    A well-defined problem normally contains:
        1. Business context
        2. Current situation
        3. Desired situation
        4. Measurable gap
        5. Stakeholders
        6. Business impact
        7. Constraints
    """

    title: str
    context: str
    current_state: str
    desired_state: str
    measurable_gap: str
    stakeholders: List[str]
    business_impact: str
    constraints: List[str] = field(default_factory=list)

    def describe(self) -> None:
        print(f"\nProblem: {self.title}")
        print(f"Context: {self.context}")
        print(f"Current state: {self.current_state}")
        print(f"Desired state: {self.desired_state}")
        print(f"Gap: {self.measurable_gap}")
        print(f"Stakeholders: {', '.join(self.stakeholders)}")
        print(f"Business impact: {self.business_impact}")

        if self.constraints:
            print(f"Constraints: {', '.join(self.constraints)}")


customer_churn_problem = BusinessProblem(
    title="Increasing Customer Churn",
    context="A subscription business has experienced declining recurring revenue.",
    current_state="Monthly customer churn is 8%.",
    desired_state="Monthly customer churn should be below 5%.",
    measurable_gap="Churn exceeds the target by 3 percentage points.",
    stakeholders=["Customers", "Product Team", "Marketing Team", "Finance"],
    business_impact="Higher churn reduces recurring revenue and customer lifetime value.",
    constraints=["Limited retention budget", "Customer data privacy requirements"],
)

customer_churn_problem.describe()


# =============================================================================
# SECTION 3: BUSINESS QUESTIONS VS ANALYTICAL QUESTIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 3: BUSINESS QUESTIONS AND ANALYTICAL QUESTIONS")
print("=" * 80)


# Business questions are decision-oriented.
#
# Example:
#     "Why is customer churn increasing?"
#
# Analytical questions translate the business question into questions that can
# be investigated using data.
#
# Examples:
#     - Which customer segments have the highest churn rate?
#     - Has churn changed after a product release?
#     - Is churn associated with customer support response time?
#     - Do customers with low product usage churn more frequently?
#     - Which reasons are most frequently associated with cancellation?


business_question = "Why is customer churn increasing?"

analytical_questions = [
    "Which customer segment has the highest churn rate?",
    "Is churn higher among recently acquired customers?",
    "Does low product usage correlate with churn?",
    "Is support response time associated with churn?",
]

print(f"Business question:\n{business_question}\n")
print("Analytical questions:")

for question in analytical_questions:
    print(f"- {question}")


# =============================================================================
# SECTION 4: SYMPTOMS, CAUSES, AND ROOT CAUSES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 4: SYMPTOMS, CAUSES, AND ROOT CAUSES")
print("=" * 80)


@dataclass
class CauseNode:
    """
    Represents a node in a cause hierarchy.

    A cause tree helps analysts avoid jumping directly from an observed symptom
    to an unsupported explanation.
    """

    name: str
    children: List["CauseNode"] = field(default_factory=list)

    def display(self, level: int = 0) -> None:
        print("    " * level + f"- {self.name}")

        for child in self.children:
            child.display(level + 1)


churn_cause_tree = CauseNode(
    "Customer churn is increasing",
    children=[
        CauseNode(
            "Product-related factors",
            children=[
                CauseNode("Low product usage"),
                CauseNode("Missing required features"),
                CauseNode("Technical reliability issues"),
            ],
        ),
        CauseNode(
            "Customer experience factors",
            children=[
                CauseNode("Slow support response"),
                CauseNode("Poor onboarding"),
                CauseNode("Difficult cancellation or billing processes"),
            ],
        ),
        CauseNode(
            "Commercial factors",
            children=[
                CauseNode("Price increases"),
                CauseNode("Competitor discounts"),
                CauseNode("Low perceived value"),
            ],
        ),
    ],
)

churn_cause_tree.display()


# =============================================================================
# SECTION 5: THE FIVE WHYS TECHNIQUE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 5: FIVE WHYS ROOT CAUSE ANALYSIS")
print("=" * 80)


five_whys_example = [
    (
        "Problem",
        "Online sales decreased by 20%.",
    ),
    (
        "Why 1",
        "Website conversion rate decreased.",
    ),
    (
        "Why 2",
        "More visitors abandoned the checkout process.",
    ),
    (
        "Why 3",
        "Checkout pages became slower.",
    ),
    (
        "Why 4",
        "A new third-party service increased page load time.",
    ),
    (
        "Why 5",
        "Performance testing was not included in the release process.",
    ),
]

for level, explanation in five_whys_example:
    print(f"{level}: {explanation}")


# The Five Whys is useful for structured reasoning but has limitations.
#
# Important limitations:
#     - A complex problem may have multiple root causes.
#     - The number five is not a strict rule.
#     - The answers must be supported by evidence.
#     - Repeated questioning does not guarantee causal proof.
#
# Analytical validation should follow.


# =============================================================================
# SECTION 6: KPI, METRIC, DIMENSION, AND MEASURE
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 6: BUSINESS METRICS")
print("=" * 80)


# KPI (Key Performance Indicator):
#     A strategically important metric used to evaluate progress toward an
#     important business objective.
#
# Metric:
#     A quantitative measurement.
#
# Measure:
#     A numerical value that can be aggregated or calculated.
#
# Dimension:
#     A descriptive attribute used to segment or group measures.
#
# Example:
#
#     Revenue        -> Measure
#     Region         -> Dimension
#     Monthly Growth -> Metric
#     Annual Revenue -> KPI


monthly_revenue = [100_000, 110_000, 105_000, 125_000]

growth_rates = []

for previous, current in zip(monthly_revenue, monthly_revenue[1:]):
    growth_rate = (current - previous) / previous
    growth_rates.append(growth_rate)

print("Monthly revenue:", monthly_revenue)
print("Month-over-month growth rates:")

for growth_rate in growth_rates:
    print(f"{growth_rate:.2%}")


# =============================================================================
# SECTION 7: COMMON BUSINESS METRICS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 7: COMMON BUSINESS METRICS")
print("=" * 80)


def calculate_conversion_rate(conversions: int, opportunities: int) -> float:
    """
    Conversion rate = conversions / total opportunities.

    Edge case:
        If opportunities are zero, division is undefined.
    """

    if opportunities <= 0:
        return 0.0

    return conversions / opportunities


def calculate_churn_rate(customers_lost: int, customers_at_start: int) -> float:
    """
    Churn rate measures the proportion of customers lost.

    Churn rate = customers lost / customers at the start of the period.
    """

    if customers_at_start <= 0:
        return 0.0

    return customers_lost / customers_at_start


def calculate_average_order_value(revenue: float, orders: int) -> float:
    """
    Average Order Value = total revenue / number of orders.
    """

    if orders <= 0:
        return 0.0

    return revenue / orders


def calculate_customer_acquisition_cost(
    acquisition_spend: float,
    acquired_customers: int,
) -> float:
    """
    Customer Acquisition Cost = acquisition spending / acquired customers.
    """

    if acquired_customers <= 0:
        return 0.0

    return acquisition_spend / acquired_customers


conversion_rate = calculate_conversion_rate(250, 5_000)
churn_rate = calculate_churn_rate(80, 1_000)
average_order_value = calculate_average_order_value(500_000, 4_000)
customer_acquisition_cost = calculate_customer_acquisition_cost(200_000, 1_000)

print(f"Conversion rate: {conversion_rate:.2%}")
print(f"Churn rate: {churn_rate:.2%}")
print(f"Average order value: {average_order_value:.2f}")
print(f"Customer acquisition cost: {customer_acquisition_cost:.2f}")


# =============================================================================
# SECTION 8: LEADING AND LAGGING INDICATORS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 8: LEADING AND LAGGING INDICATORS")
print("=" * 80)


# Lagging indicators measure outcomes that have already occurred.
#
# Examples:
#     - Revenue
#     - Profit
#     - Annual customer churn
#
# Leading indicators may provide early signals about future outcomes.
#
# Examples:
#     - Product usage
#     - Customer support satisfaction
#     - Trial activation rate
#
# Leading indicators are not automatically causal indicators. Their predictive
# usefulness should be tested.


indicators = {
    "Revenue": "Lagging",
    "Profit": "Lagging",
    "Customer Churn": "Lagging",
    "Product Usage": "Potentially Leading",
    "Support Response Time": "Potentially Leading",
    "Customer Satisfaction": "Potentially Leading",
}

for metric_name, indicator_type in indicators.items():
    print(f"{metric_name}: {indicator_type}")


# =============================================================================
# SECTION 9: IDENTIFYING ANALYTICAL OPPORTUNITIES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 9: IDENTIFYING ANALYTICAL OPPORTUNITIES")
print("=" * 80)


# An analytical opportunity exists when data analysis can potentially reduce
# uncertainty and improve a business decision.
#
# A useful framework:
#
#     Decision
#        |
#        v
#     What uncertainty exists?
#        |
#        v
#     Can data reduce that uncertainty?
#        |
#        v
#     Is action possible after obtaining the insight?
#
# Analysis without a decision or possible action may create information without
# meaningful business value.


@dataclass
class AnalyticalOpportunity:
    decision: str
    uncertainty: str
    analytical_question: str
    data_required: List[str]
    possible_action: str

    def display(self) -> None:
        print(f"\nDecision: {self.decision}")
        print(f"Uncertainty: {self.uncertainty}")
        print(f"Analytical question: {self.analytical_question}")
        print(f"Data required: {', '.join(self.data_required)}")
        print(f"Possible action: {self.possible_action}")


retention_opportunity = AnalyticalOpportunity(
    decision="How should the company prioritize customer retention efforts?",
    uncertainty="The company does not know which customers are most likely to churn.",
    analytical_question="Which customer characteristics are associated with higher churn?",
    data_required=[
        "Customer tenure",
        "Product usage",
        "Support interactions",
        "Subscription plan",
        "Churn outcome",
    ],
    possible_action="Target high-risk segments with retention interventions.",
)

retention_opportunity.display()


# =============================================================================
# SECTION 10: PROBLEM PRIORITIZATION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 10: PRIORITIZING BUSINESS PROBLEMS")
print("=" * 80)


@dataclass
class PrioritizedProblem:
    name: str
    business_impact: int
    urgency: int
    feasibility: int
    confidence: int

    def score(self) -> float:
        """
        Simple weighted prioritization score.

        Each dimension uses a score from 1 to 5.

        Weights are business-specific and should not be treated as universal.
        """

        return (
            self.business_impact * 0.40
            + self.urgency * 0.25
            + self.feasibility * 0.20
            + self.confidence * 0.15
        )


problems = [
    PrioritizedProblem(
        "High customer churn",
        business_impact=5,
        urgency=5,
        feasibility=4,
        confidence=4,
    ),
    PrioritizedProblem(
        "Slow internal reporting",
        business_impact=3,
        urgency=2,
        feasibility=5,
        confidence=5,
    ),
    PrioritizedProblem(
        "Low marketing conversion",
        business_impact=5,
        urgency=4,
        feasibility=3,
        confidence=3,
    ),
]

ranked_problems = sorted(
    problems,
    key=lambda problem: problem.score(),
    reverse=True,
)

for problem in ranked_problems:
    print(f"{problem.name}: {problem.score():.2f}")


# =============================================================================
# SECTION 11: GENERATED BUSINESS DATA
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 11: GENERATING SAMPLE BUSINESS DATA")
print("=" * 80)


# Real business analysis normally obtains data from databases, transaction
# systems, CRM platforms, applications, surveys, spreadsheets, or APIs.
#
# This script generates deterministic sample data to remain self-contained.

random.seed(42)

customer_data = []

segments = ["Small Business", "Mid-Market", "Enterprise"]

for customer_id in range(1, 501):
    segment = random.choices(
        segments,
        weights=[0.55, 0.30, 0.15],
    )[0]

    tenure_months = random.randint(1, 60)

    monthly_usage = max(
        0,
        round(random.gauss(55, 25), 2),
    )

    support_tickets = random.randint(0, 8)

    plan_price = {
        "Small Business": 100,
        "Mid-Market": 500,
        "Enterprise": 2_000,
    }[segment]

    # Churn probability is intentionally influenced by business variables.
    # This creates relationships that analysis can attempt to discover.

    churn_probability = 0.05

    if tenure_months <= 3:
        churn_probability += 0.15

    if monthly_usage < 30:
        churn_probability += 0.20

    if support_tickets >= 5:
        churn_probability += 0.15

    if segment == "Small Business":
        churn_probability += 0.05

    churned = random.random() < min(churn_probability, 0.90)

    customer_data.append(
        {
            "customer_id": customer_id,
            "segment": segment,
            "tenure_months": tenure_months,
            "monthly_usage": monthly_usage,
            "support_tickets": support_tickets,
            "monthly_revenue": plan_price,
            "churned": churned,
        }
    )


print(f"Generated customer records: {len(customer_data)}")


# =============================================================================
# SECTION 12: DATA QUALITY CHECKS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 12: DATA QUALITY")
print("=" * 80)


def check_customer_record(record: Dict[str, object]) -> List[str]:
    """
    Performs simple validation checks.

    Data quality problems can produce misleading analytical conclusions.
    """

    errors = []

    customer_id = record.get("customer_id")
    tenure_months = record.get("tenure_months")
    monthly_usage = record.get("monthly_usage")
    support_tickets = record.get("support_tickets")
    monthly_revenue = record.get("monthly_revenue")

    if not isinstance(customer_id, int) or customer_id <= 0:
        errors.append("Invalid customer ID.")

    if not isinstance(tenure_months, int) or tenure_months < 0:
        errors.append("Invalid tenure.")

    if not isinstance(monthly_usage, (int, float)) or monthly_usage < 0:
        errors.append("Invalid usage.")

    if not isinstance(support_tickets, int) or support_tickets < 0:
        errors.append("Invalid support ticket count.")

    if not isinstance(monthly_revenue, (int, float)) or monthly_revenue < 0:
        errors.append("Invalid monthly revenue.")

    if not isinstance(record.get("churned"), bool):
        errors.append("Invalid churn value.")

    return errors


invalid_records = []

for record in customer_data:
    record_errors = check_customer_record(record)

    if record_errors:
        invalid_records.append(
            {
                "record": record,
                "errors": record_errors,
            }
        )

print(f"Invalid records found: {len(invalid_records)}")


# =============================================================================
# SECTION 13: DESCRIPTIVE ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 13: DESCRIPTIVE ANALYSIS")
print("=" * 80)


total_customers = len(customer_data)
total_churned = sum(record["churned"] for record in customer_data)

overall_churn_rate = calculate_churn_rate(
    customers_lost=total_churned,
    customers_at_start=total_customers,
)

average_usage = mean(
    record["monthly_usage"]
    for record in customer_data
)

average_tenure = mean(
    record["tenure_months"]
    for record in customer_data
)

print(f"Total customers: {total_customers}")
print(f"Customers churned: {total_churned}")
print(f"Overall churn rate: {overall_churn_rate:.2%}")
print(f"Average monthly usage: {average_usage:.2f}")
print(f"Average tenure: {average_tenure:.2f} months")


# =============================================================================
# SECTION 14: SEGMENTATION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 14: SEGMENTATION ANALYSIS")
print("=" * 80)


segment_statistics = defaultdict(
    lambda: {
        "customers": 0,
        "churned": 0,
        "revenue": 0.0,
    }
)

for record in customer_data:
    segment = record["segment"]

    segment_statistics[segment]["customers"] += 1
    segment_statistics[segment]["churned"] += int(record["churned"])
    segment_statistics[segment]["revenue"] += record["monthly_revenue"]

print(
    f"{'Segment':<20}"
    f"{'Customers':>12}"
    f"{'Churn Rate':>15}"
    f"{'Monthly Revenue':>20}"
)

for segment, statistics in segment_statistics.items():
    segment_churn_rate = calculate_churn_rate(
        statistics["churned"],
        statistics["customers"],
    )

    print(
        f"{segment:<20}"
        f"{statistics['customers']:>12}"
        f"{segment_churn_rate:>14.2%}"
        f"{statistics['revenue']:>20,.0f}"
    )


# =============================================================================
# SECTION 15: AVERAGES CAN HIDE IMPORTANT INFORMATION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 15: WHY SEGMENTATION MATTERS")
print("=" * 80)


# Suppose two groups have the same overall average performance but very
# different internal distributions.

group_a = [50, 50, 50, 50, 50]
group_b = [0, 0, 50, 100, 100]

print(f"Group A average: {mean(group_a):.2f}")
print(f"Group B average: {mean(group_b):.2f}")

print(f"Group A median: {median(group_a):.2f}")
print(f"Group B median: {median(group_b):.2f}")

# Equal averages do not imply equal distributions.
#
# Analysts should investigate:
#     - Segments
#     - Time periods
#     - Customer cohorts
#     - Product categories
#     - Geographic areas
#     - Extreme values


# =============================================================================
# SECTION 16: COHORT ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 16: COHORT ANALYSIS")
print("=" * 80)


def classify_tenure(tenure_months: int) -> str:
    """Groups customers into tenure cohorts."""

    if tenure_months <= 3:
        return "0-3 months"

    if tenure_months <= 12:
        return "4-12 months"

    if tenure_months <= 24:
        return "13-24 months"

    return "25+ months"


cohort_statistics = defaultdict(
    lambda: {
        "customers": 0,
        "churned": 0,
    }
)

for record in customer_data:
    cohort = classify_tenure(record["tenure_months"])

    cohort_statistics[cohort]["customers"] += 1
    cohort_statistics[cohort]["churned"] += int(record["churned"])

for cohort, statistics in cohort_statistics.items():
    cohort_churn_rate = calculate_churn_rate(
        statistics["churned"],
        statistics["customers"],
    )

    print(
        f"{cohort:<15}"
        f"Customers={statistics['customers']:>4}, "
        f"Churn={cohort_churn_rate:.2%}"
    )


# =============================================================================
# SECTION 17: ASSOCIATION VS CAUSATION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 17: ASSOCIATION AND CAUSATION")
print("=" * 80)


# Analytical data may reveal that two variables change together.
#
# Example:
#     Customers with many support tickets may churn more frequently.
#
# This does not automatically prove:
#
#     Support tickets cause churn.
#
# Alternative explanations may exist:
#
#     - Product problems cause both support tickets and churn.
#     - High-value customers may contact support more frequently.
#     - Churning customers may create more tickets before cancellation.
#
# Observational analysis identifies patterns. Strong causal conclusions often
# require controlled experiments, careful causal design, or domain evidence.


def correlation(values_x: List[float], values_y: List[float]) -> float:
    """
    Calculates Pearson correlation.

    Important limitations:
        - Correlation does not prove causation.
        - Linear correlation may miss nonlinear relationships.
        - Outliers can strongly affect correlation.
    """

    if len(values_x) != len(values_y):
        raise ValueError("Lists must have the same length.")

    if len(values_x) < 2:
        raise ValueError("At least two observations are required.")

    mean_x = mean(values_x)
    mean_y = mean(values_y)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(values_x, values_y)
    )

    denominator_x = math.sqrt(
        sum(
            (x - mean_x) ** 2
            for x in values_x
        )
    )

    denominator_y = math.sqrt(
        sum(
            (y - mean_y) ** 2
            for y in values_y
        )
    )

    if denominator_x == 0 or denominator_y == 0:
        return 0.0

    return numerator / (denominator_x * denominator_y)


usage_values = [
    record["monthly_usage"]
    for record in customer_data
]

churn_values = [
    int(record["churned"])
    for record in customer_data
]

usage_churn_correlation = correlation(
    usage_values,
    churn_values,
)

print(
    "Correlation between usage and churn: "
    f"{usage_churn_correlation:.3f}"
)


# =============================================================================
# SECTION 18: PROBLEM DECOMPOSITION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 18: DECOMPOSING A BUSINESS PROBLEM")
print("=" * 80)


# Revenue can often be decomposed into business drivers.
#
# One simplified relationship is:
#
#     Revenue = Number of Customers
#               * Conversion Rate
#               * Average Order Value
#
# More complex organizations may require additional factors.


visitors = 100_000
conversion_rate_value = 0.03
average_order_value_value = 150

orders = visitors * conversion_rate_value
estimated_revenue = orders * average_order_value_value

print(f"Visitors: {visitors:,}")
print(f"Conversion rate: {conversion_rate_value:.2%}")
print(f"Orders: {orders:,.0f}")
print(f"Average order value: {average_order_value_value:.2f}")
print(f"Estimated revenue: {estimated_revenue:,.2f}")


# Sensitivity analysis asks:
#
#     Which driver has the largest potential impact?


def revenue_model(
    visitors: float,
    conversion_rate_value: float,
    average_order_value_value: float,
) -> float:
    return (
        visitors
        * conversion_rate_value
        * average_order_value_value
    )


baseline_revenue = revenue_model(
    visitors,
    conversion_rate_value,
    average_order_value_value,
)

higher_conversion_revenue = revenue_model(
    visitors,
    conversion_rate_value * 1.10,
    average_order_value_value,
)

higher_order_value_revenue = revenue_model(
    visitors,
    conversion_rate_value,
    average_order_value_value * 1.10,
)

print(f"Baseline revenue: {baseline_revenue:,.2f}")
print(
    "Revenue after 10% conversion improvement: "
    f"{higher_conversion_revenue:,.2f}"
)
print(
    "Revenue after 10% order value improvement: "
    f"{higher_order_value_revenue:,.2f}"
)


# =============================================================================
# SECTION 19: HYPOTHESIS-DRIVEN ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 19: HYPOTHESIS-DRIVEN ANALYSIS")
print("=" * 80)


@dataclass
class AnalyticalHypothesis:
    statement: str
    supporting_metric: str
    comparison_groups: Tuple[str, str]

    def display(self) -> None:
        print(f"\nHypothesis: {self.statement}")
        print(f"Metric: {self.supporting_metric}")
        print(
            "Comparison: "
            f"{self.comparison_groups[0]} "
            f"vs {self.comparison_groups[1]}"
        )


hypothesis = AnalyticalHypothesis(
    statement=(
        "Customers with low monthly product usage have a higher churn rate "
        "than customers with high product usage."
    ),
    supporting_metric="Customer churn rate",
    comparison_groups=("Low usage customers", "High usage customers"),
)

hypothesis.display()


low_usage_customers = [
    record
    for record in customer_data
    if record["monthly_usage"] < 30
]

high_usage_customers = [
    record
    for record in customer_data
    if record["monthly_usage"] >= 60
]

low_usage_churn = calculate_churn_rate(
    sum(record["churned"] for record in low_usage_customers),
    len(low_usage_customers),
)

high_usage_churn = calculate_churn_rate(
    sum(record["churned"] for record in high_usage_customers),
    len(high_usage_customers),
)

print(f"\nLow usage churn rate: {low_usage_churn:.2%}")
print(f"High usage churn rate: {high_usage_churn:.2%}")


# =============================================================================
# SECTION 20: ANALYTICAL OPPORTUNITY SCORING
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 20: SCORING ANALYTICAL OPPORTUNITIES")
print("=" * 80)


@dataclass
class OpportunityScore:
    """
    Scores an analytical opportunity.

    Dimensions:
        business_value:
            Potential economic or strategic impact.

        data_availability:
            Whether required data exists and is accessible.

        actionability:
            Whether the organization can act on the result.

        analytical_feasibility:
            Whether the question can realistically be investigated.

        risk:
            Privacy, financial, operational, or decision risk.
    """

    name: str
    business_value: int
    data_availability: int
    actionability: int
    analytical_feasibility: int
    risk: int

    def calculate(self) -> float:
        positive_score = (
            self.business_value * 0.35
            + self.data_availability * 0.20
            + self.actionability * 0.25
            + self.analytical_feasibility * 0.20
        )

        risk_penalty = self.risk * 0.10

        return positive_score - risk_penalty


opportunities = [
    OpportunityScore(
        name="Identify high-risk churn segments",
        business_value=5,
        data_availability=5,
        actionability=5,
        analytical_feasibility=5,
        risk=2,
    ),
    OpportunityScore(
        name="Optimize warehouse routing",
        business_value=4,
        data_availability=2,
        actionability=4,
        analytical_feasibility=3,
        risk=3,
    ),
    OpportunityScore(
        name="Predict long-term demand",
        business_value=5,
        data_availability=3,
        actionability=4,
        analytical_feasibility=3,
        risk=2,
    ),
]

ranked_opportunities = sorted(
    opportunities,
    key=lambda opportunity: opportunity.calculate(),
    reverse=True,
)

for opportunity in ranked_opportunities:
    print(
        f"{opportunity.name}: "
        f"{opportunity.calculate():.2f}"
    )


# =============================================================================
# SECTION 21: EDGE CASES IN BUSINESS ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 21: IMPORTANT EDGE CASES")
print("=" * 80)


# Edge Case 1: Small sample size.
#
# A segment with 1 customer and 1 churn event has a churn rate of 100%.
# That does not necessarily mean the segment is fundamentally risky.


small_segment_churn = calculate_churn_rate(
    customers_lost=1,
    customers_at_start=1,
)

large_segment_churn = calculate_churn_rate(
    customers_lost=100,
    customers_at_start=1_000,
)

print(f"Small segment churn: {small_segment_churn:.2%}")
print(f"Large segment churn: {large_segment_churn:.2%}")


# Edge Case 2: Percentage changes can be misleading.
#
# Increasing from 1 customer to 2 customers is 100% growth but the absolute
# increase is only one customer.


old_value = 1
new_value = 2

percentage_growth = (
    (new_value - old_value)
    / old_value
)

absolute_growth = new_value - old_value

print(f"Absolute growth: {absolute_growth}")
print(f"Percentage growth: {percentage_growth:.2%}")


# Edge Case 3: Zero denominators.
#
# Division-based metrics require explicit handling.


zero_conversion = calculate_conversion_rate(
    conversions=0,
    opportunities=0,
)

print(f"Conversion rate with zero opportunities: {zero_conversion:.2%}")


# =============================================================================
# SECTION 22: SIMPSON'S PARADOX CONCEPT
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 22: AGGREGATION CAN MISLEAD")
print("=" * 80)


# Aggregated results can hide or reverse patterns visible within subgroups.
#
# Analysts should inspect relevant dimensions before making decisions from
# overall averages or rates.


department_a = {
    "successful": 90,
    "total": 100,
}

department_b = {
    "successful": 1,
    "total": 10,
}

department_a_rate = (
    department_a["successful"]
    / department_a["total"]
)

department_b_rate = (
    department_b["successful"]
    / department_b["total"]
)

combined_rate = (
    department_a["successful"]
    + department_b["successful"]
) / (
    department_a["total"]
    + department_b["total"]
)

print(f"Department A success rate: {department_a_rate:.2%}")
print(f"Department B success rate: {department_b_rate:.2%}")
print(f"Combined success rate: {combined_rate:.2%}")


# =============================================================================
# SECTION 23: COMMON ANALYTICAL MISTAKES
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 23: COMMON MISTAKES")
print("=" * 80)


common_mistakes = [
    "Treating symptoms as confirmed root causes.",
    "Starting analysis before defining the business decision.",
    "Using metrics without defining denominators.",
    "Confusing correlation with causation.",
    "Ignoring missing or inaccurate data.",
    "Using averages without examining segments.",
    "Ignoring sample size.",
    "Optimizing a metric that does not represent business value.",
    "Ignoring operational constraints.",
    "Producing insights without identifying possible actions.",
]

for index, mistake in enumerate(common_mistakes, start=1):
    print(f"{index}. {mistake}")


# =============================================================================
# SECTION 24: METRIC DESIGN AND GOODHART'S LAW
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 24: METRIC DESIGN")
print("=" * 80)


# A metric can influence behavior.
#
# Example:
#
# If a customer support team is measured only by the number of tickets closed,
# employees may close tickets quickly without actually solving customer issues.
#
# A better measurement system may combine:
#
#     - Tickets resolved
#     - Resolution quality
#     - Customer satisfaction
#     - Reopened tickets
#
# This demonstrates a central measurement principle:
#
#     A metric is useful when it encourages behavior aligned with the actual
#     business objective.


support_metrics = {
    "tickets_closed": 1_000,
    "customer_satisfaction": 0.82,
    "reopened_ticket_rate": 0.15,
}

print("Support metrics:")

for metric_name, metric_value in support_metrics.items():
    print(f"{metric_name}: {metric_value}")


# =============================================================================
# SECTION 25: FROM INSIGHT TO ACTION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 25: TRANSLATING INSIGHT INTO ACTION")
print("=" * 80)


@dataclass
class BusinessInsight:
    observation: str
    interpretation: str
    recommended_action: str
    expected_metric: str

    def display(self) -> None:
        print(f"\nObservation: {self.observation}")
        print(f"Interpretation: {self.interpretation}")
        print(f"Action: {self.recommended_action}")
        print(f"Measure impact using: {self.expected_metric}")


insight = BusinessInsight(
    observation=(
        f"Customers with low product usage have a churn rate of "
        f"{low_usage_churn:.2%}, compared with "
        f"{high_usage_churn:.2%} for high-usage customers."
    ),
    interpretation=(
        "Low usage is associated with higher churn and may identify customers "
        "who need additional activation or engagement."
    ),
    recommended_action=(
        "Test an onboarding and engagement intervention for low-usage "
        "customers."
    ),
    expected_metric="Churn rate and product usage after intervention",
)

insight.display()


# =============================================================================
# SECTION 26: EXPERIMENTATION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 26: BUSINESS EXPERIMENTS")
print("=" * 80)


# Observational analysis can identify an opportunity.
#
# An experiment can test whether an intervention produces a measurable change.
#
# Example:
#
#     Control group:
#         Receives the current onboarding process.
#
#     Treatment group:
#         Receives improved onboarding.
#
# Compare relevant outcomes while attempting to keep other important conditions
# comparable.


random.seed(100)

control_outcomes = []
treatment_outcomes = []

for _ in range(200):
    control_outcomes.append(
        random.random() < 0.60
    )

    treatment_outcomes.append(
        random.random() < 0.70
    )

control_activation_rate = mean(control_outcomes)
treatment_activation_rate = mean(treatment_outcomes)

difference = (
    treatment_activation_rate
    - control_activation_rate
)

print(
    "Control activation rate: "
    f"{control_activation_rate:.2%}"
)

print(
    "Treatment activation rate: "
    f"{treatment_activation_rate:.2%}"
)

print(
    "Observed difference: "
    f"{difference:.2%}"
)


# Important experiment considerations:
#
#     - Sample size
#     - Random assignment
#     - Selection bias
#     - Measurement consistency
#     - Statistical uncertainty
#     - Ethical and business constraints
#     - Duration of the experiment
#
# A difference observed in one experiment does not automatically guarantee
# permanent or universal business impact.


# =============================================================================
# SECTION 27: FINANCIAL IMPACT ESTIMATION
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 27: ESTIMATING BUSINESS IMPACT")
print("=" * 80)


def estimate_retention_value(
    customers_targeted: int,
    expected_churn_reduction: float,
    monthly_revenue_per_customer: float,
    retained_months: int,
) -> float:
    """
    Estimates simplified revenue retained from a churn reduction.

    This is not a complete customer lifetime value model because real-world
    models may include:
        - Gross margin
        - Discount rates
        - Future churn probability
        - Retention program cost
        - Customer behavior changes
    """

    if customers_targeted < 0:
        raise ValueError(
            "Customers targeted cannot be negative."
        )

    if not 0 <= expected_churn_reduction <= 1:
        raise ValueError(
            "Expected churn reduction must be between 0 and 1."
        )

    if monthly_revenue_per_customer < 0:
        raise ValueError(
            "Monthly revenue cannot be negative."
        )

    if retained_months < 0:
        raise ValueError(
            "Retained months cannot be negative."
        )

    retained_customers = (
        customers_targeted
        * expected_churn_reduction
    )

    return (
        retained_customers
        * monthly_revenue_per_customer
        * retained_months
    )


estimated_retention_revenue = estimate_retention_value(
    customers_targeted=1_000,
    expected_churn_reduction=0.05,
    monthly_revenue_per_customer=100,
    retained_months=12,
)

print(
    "Estimated retained revenue: "
    f"{estimated_retention_revenue:,.2f}"
)


# =============================================================================
# SECTION 28: COST-BENEFIT ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 28: COST-BENEFIT ANALYSIS")
print("=" * 80)


def calculate_roi(
    benefit: float,
    cost: float,
) -> Optional[float]:
    """
    Return on Investment:

        ROI = (Benefit - Cost) / Cost

    Returns None when cost is zero because percentage ROI becomes undefined.
    """

    if cost == 0:
        return None

    return (
        benefit - cost
    ) / cost


program_cost = 25_000

roi = calculate_roi(
    estimated_retention_revenue,
    program_cost,
)

print(
    f"Estimated benefit: {estimated_retention_revenue:,.2f}"
)
print(f"Program cost: {program_cost:,.2f}")

if roi is None:
    print("ROI: Undefined because cost is zero.")
else:
    print(f"Estimated ROI: {roi:.2%}")


# =============================================================================
# SECTION 29: PRODUCTION CONSIDERATIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 29: PRODUCTION ANALYTICS CONSIDERATIONS")
print("=" * 80)


production_considerations = {
    "Data quality": (
        "Validate completeness, accuracy, consistency, and timeliness."
    ),
    "Data lineage": (
        "Document where important metrics originate."
    ),
    "Metric definitions": (
        "Ensure teams use consistent formulas and denominators."
    ),
    "Privacy": (
        "Limit access to sensitive customer and employee information."
    ),
    "Security": (
        "Protect data using appropriate authentication and access controls."
    ),
    "Monitoring": (
        "Monitor data pipelines and important business metrics."
    ),
    "Reproducibility": (
        "Document assumptions and preserve analytical logic."
    ),
    "Decision ownership": (
        "Identify who can act on analytical findings."
    ),
}

for topic, explanation in production_considerations.items():
    print(f"{topic}: {explanation}")


# =============================================================================
# SECTION 30: DEBUGGING ANALYTICAL RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 30: DEBUGGING ANALYTICAL RESULTS")
print("=" * 80)


def debug_metric(
    numerator: float,
    denominator: float,
    metric_name: str,
) -> float:
    """
    Demonstrates defensive metric calculation.

    Business analytics errors often occur because:
        - The wrong denominator is used.
        - Records are duplicated.
        - Time periods are inconsistent.
        - Filters differ between reports.
        - Missing values are silently removed.
    """

    if denominator < 0:
        raise ValueError(
            f"{metric_name}: denominator cannot be negative."
        )

    if denominator == 0:
        print(
            f"{metric_name}: denominator is zero; "
            "returning 0.0 by convention."
        )
        return 0.0

    return numerator / denominator


print(
    "Debug metric example: "
    f"{debug_metric(25, 100, 'Sample Rate'):.2%}"
)


# =============================================================================
# SECTION 31: BUSINESS PROBLEM IDENTIFICATION WORKFLOW
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 31: COMPLETE PROBLEM IDENTIFICATION WORKFLOW")
print("=" * 80)


workflow = [
    "1. Understand the business context.",
    "2. Identify the observed symptom or performance gap.",
    "3. Define the desired business state.",
    "4. Quantify the size and impact of the gap.",
    "5. Identify stakeholders and decision owners.",
    "6. Decompose the problem into possible drivers.",
    "7. Distinguish symptoms from possible root causes.",
    "8. Formulate analytical questions.",
    "9. Identify required data and evaluate data quality.",
    "10. Define metrics and denominators.",
    "11. Segment the data to identify important patterns.",
    "12. Test hypotheses and investigate alternative explanations.",
    "13. Estimate the potential business value of possible actions.",
    "14. Prioritize analytical opportunities.",
    "15. Translate findings into decisions and actions.",
    "16. Measure business outcomes after implementation.",
]

for step in workflow:
    print(step)


# =============================================================================
# SECTION 32: END-TO-END MINI CASE STUDY
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 32: END-TO-END CASE STUDY")
print("=" * 80)


# Business context:
#
# A subscription company observes declining recurring revenue.
#
# Step 1: Identify the symptom.

symptom = "Recurring revenue growth has slowed."

print(f"Observed symptom: {symptom}")


# Step 2: Define a possible measurable problem.

business_problem_statement = (
    "Monthly customer churn is above the organization's target."
)

print(
    "Business problem: "
    f"{business_problem_statement}"
)


# Step 3: Investigate segments.

segment_churn_rates = {}

for segment, statistics in segment_statistics.items():
    segment_churn_rates[segment] = calculate_churn_rate(
        statistics["churned"],
        statistics["customers"],
    )

highest_risk_segment = max(
    segment_churn_rates,
    key=segment_churn_rates.get,
)

print(
    "Highest observed churn segment: "
    f"{highest_risk_segment}"
)

print(
    "Segment churn rate: "
    f"{segment_churn_rates[highest_risk_segment]:.2%}"
)


# Step 4: Investigate a potential behavioral driver.

print(
    "Low usage churn rate: "
    f"{low_usage_churn:.2%}"
)

print(
    "High usage churn rate: "
    f"{high_usage_churn:.2%}"
)


# Step 5: Frame the analytical opportunity.

case_opportunity = (
    "Determine whether improving product activation for low-usage customers "
    "can reduce churn."
)

print(
    "Analytical opportunity: "
    f"{case_opportunity}"
)


# Step 6: Define an action.

case_action = (
    "Run a controlled onboarding and engagement intervention for "
    "low-usage customers."
)

print(
    "Potential action: "
    f"{case_action}"
)


# Step 7: Define success metrics.

success_metrics = [
    "Product activation rate",
    "Monthly usage",
    "Customer churn rate",
    "Retained revenue",
]

print("Success metrics:")

for metric in success_metrics:
    print(f"- {metric}")


# =============================================================================
# SECTION 33: REUSABLE ANALYTICAL FUNCTIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 33: REUSABLE ANALYTICAL TOOLKIT")
print("=" * 80)


def group_by(
    records: List[Dict[str, object]],
    key: str,
) -> Dict[object, List[Dict[str, object]]]:
    """
    Groups records by a dictionary key.

    Similar grouping operations are central to business analytics.
    """

    groups = defaultdict(list)

    for record in records:
        groups[record.get(key)].append(record)

    return dict(groups)


def calculate_rate_by_group(
    records: List[Dict[str, object]],
    group_key: str,
    outcome_key: str,
) -> Dict[object, float]:
    """
    Calculates a Boolean outcome rate for each group.
    """

    groups = group_by(
        records,
        group_key,
    )

    results = {}

    for group_name, group_records in groups.items():
        outcome_count = sum(
            bool(record.get(outcome_key))
            for record in group_records
        )

        results[group_name] = (
            outcome_count
            / len(group_records)
            if group_records
            else 0.0
        )

    return results


rates_by_segment = calculate_rate_by_group(
    customer_data,
    "segment",
    "churned",
)

print("Reusable group-level churn calculation:")

for segment, rate in rates_by_segment.items():
    print(
        f"{segment}: {rate:.2%}"
    )


# =============================================================================
# SECTION 34: FINAL TECHNICAL DISTINCTIONS
# =============================================================================

print("\n" + "=" * 80)
print("SECTION 34: IMPORTANT DISTINCTIONS")
print("=" * 80)


distinctions = {
    "Symptom vs Root Cause": (
        "A symptom is an observed effect; a root cause is an underlying "
        "condition contributing to the effect."
    ),
    "Business Question vs Analytical Question": (
        "A business question concerns a decision; an analytical question "
        "defines what evidence should be investigated."
    ),
    "Metric vs KPI": (
        "A metric is any measurement; a KPI is strategically important."
    ),
    "Correlation vs Causation": (
        "Correlation measures association; causation requires stronger "
        "evidence about cause and effect."
    ),
    "Insight vs Action": (
        "An insight explains a meaningful pattern; an action changes "
        "business behavior or operations."
    ),
    "Accuracy vs Business Value": (
        "A technically accurate analysis may still have low value if it "
        "does not improve a meaningful decision."
    ),
}

for distinction, explanation in distinctions.items():
    print(f"\n{distinction}")
    print(f"    {explanation}")


# =============================================================================
# SECTION 35: COMPLETION
# =============================================================================

print("\n" + "=" * 80)
print("COMPLETION")
print("=" * 80)

print(
    "Business problem identification is a structured process of moving from "
    "an observed performance gap to a measurable, actionable, and "
    "decision-relevant analytical opportunity."
)
