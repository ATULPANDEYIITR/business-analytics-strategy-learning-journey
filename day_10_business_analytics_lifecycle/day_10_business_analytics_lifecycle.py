"""
Business Analytics Lifecycle
============================

A comprehensive, self-contained study script covering the Business Analytics
Lifecycle from problem definition through data, analysis, insight,
recommendation, decision-making, implementation, monitoring, and iteration.

The script is designed to be executed directly with Python's standard library.
It uses a realistic business scenario throughout and demonstrates:

1. Business problem definition
2. Stakeholder identification
3. Decision framing
4. Analytical objectives
5. KPI and metric design
6. Data requirements and data quality
7. Data collection and validation
8. Data preparation
9. Descriptive analytics
10. Diagnostic analytics
11. Exploratory data analysis
12. Segmentation
13. Correlation and causality distinctions
14. Predictive analytics
15. Scenario analysis
16. Prescriptive analytics
17. Experimentation and A/B testing
18. Insight generation
19. Recommendation design
20. Decision-making
21. Implementation planning
22. Monitoring and control
23. Model and KPI drift
24. Governance, ethics, privacy, and security
25. Reproducibility and testing
26. Advanced analytics workflow design
27. A complete end-to-end case study
"""

from __future__ import annotations

import csv
import math
import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================================
# 1. FOUNDATIONAL TERMINOLOGY
# ============================================================================

def explain_foundations() -> None:
    """
    Print the foundational vocabulary used throughout business analytics.
    """

    concepts = {
        "Business analytics":
            "The systematic use of data, quantitative methods, and business "
            "reasoning to support decisions and improve outcomes.",

        "Business problem":
            "A business situation requiring a decision, improvement, or "
            "explanation.",

        "Analytical problem":
            "The measurable question that can be investigated using data "
            "to address a business problem.",

        "Insight":
            "A meaningful interpretation of evidence that explains what is "
            "happening and why it matters.",

        "Decision":
            "A selected course of action made using available evidence, "
            "constraints, objectives, and judgment.",

        "KPI":
            "A key performance indicator used to evaluate progress toward "
            "an important business objective.",

        "Metric":
            "A quantitative measure. A KPI is a metric that is strategically "
            "important to a particular objective.",

        "Descriptive analytics":
            "Answers what happened.",

        "Diagnostic analytics":
            "Investigates why something happened.",

        "Predictive analytics":
            "Estimates what is likely to happen.",

        "Prescriptive analytics":
            "Evaluates actions and helps determine what should be done.",

        "Decision intelligence":
            "A broader discipline connecting data, analysis, models, "
            "constraints, human judgment, and organizational decisions.",
    }

    print("\nFOUNDATIONAL TERMINOLOGY")
    print("-" * 80)

    for name, definition in concepts.items():
        print(f"{name}: {definition}")


# ============================================================================
# 2. BUSINESS ANALYTICS LIFECYCLE
# ============================================================================

def explain_lifecycle() -> None:
    """
    Display a practical lifecycle.

    A lifecycle is not necessarily a strictly linear sequence. In real
    organizations, analysts frequently return to earlier stages when new
    evidence changes the problem definition or exposes data limitations.
    """

    stages = [
        "1. Define the business problem",
        "2. Identify stakeholders and decisions",
        "3. Translate the problem into analytical questions",
        "4. Define objectives, KPIs, metrics, and success criteria",
        "5. Identify data requirements",
        "6. Collect and validate data",
        "7. Prepare and transform data",
        "8. Explore and describe the data",
        "9. Diagnose drivers and relationships",
        "10. Build predictive or statistical models when justified",
        "11. Evaluate scenarios and possible actions",
        "12. Generate evidence-based insights",
        "13. Convert insights into recommendations",
        "14. Make and communicate the decision",
        "15. Implement the decision",
        "16. Monitor outcomes and risks",
        "17. Learn, refine, and repeat",
    ]

    print("\nBUSINESS ANALYTICS LIFECYCLE")
    print("-" * 80)

    for stage in stages:
        print(stage)

    print("\nImportant principle:")
    print(
        "The lifecycle is iterative. A poor data definition can require a "
        "return to the data stage. A weak analytical question can require "
        "revisiting the business problem. A failed implementation can require "
        "reframing the recommendation."
    )


# ============================================================================
# 3. PROBLEM DEFINITION
# ============================================================================

@dataclass
class BusinessProblem:
    organization: str
    problem_statement: str
    business_objective: str
    decision_to_make: str
    scope: str
    constraints: List[str]
    stakeholders: List[str]
    target_outcome: str


def define_business_problem() -> BusinessProblem:
    """
    Create a precise problem definition for a fictional retail company.

    Good problem definitions connect:
        business situation -> objective -> decision -> measurable outcome
    """

    problem = BusinessProblem(
        organization="Northstar Retail",
        problem_statement=(
            "Customer retention has declined, and management wants to "
            "understand the main drivers and determine which customers "
            "should receive targeted retention interventions."
        ),
        business_objective=(
            "Increase customer retention while protecting contribution margin."
        ),
        decision_to_make=(
            "Determine which customer segments should receive retention "
            "offers and what offer intensity is economically justified."
        ),
        scope=(
            "Customers who made at least one purchase during the previous "
            "12 months."
        ),
        constraints=[
            "Limited promotional budget",
            "Customer privacy requirements",
            "Retention offers cannot exceed contribution-margin limits",
            "Recommendations must be operationally implementable",
        ],
        stakeholders=[
            "Chief Marketing Officer",
            "Finance team",
            "Customer analytics team",
            "CRM operations",
            "Store and e-commerce leadership",
        ],
        target_outcome=(
            "Increase incremental retained revenue without creating "
            "unprofitable discounting."
        ),
    )

    print("\nBUSINESS PROBLEM DEFINITION")
    print("-" * 80)

    print(f"Organization: {problem.organization}")
    print(f"Problem: {problem.problem_statement}")
    print(f"Objective: {problem.business_objective}")
    print(f"Decision: {problem.decision_to_make}")
    print(f"Scope: {problem.scope}")

    print("\nConstraints:")
    for constraint in problem.constraints:
        print(f"  - {constraint}")

    print("\nStakeholders:")
    for stakeholder in problem.stakeholders:
        print(f"  - {stakeholder}")

    print(f"\nTarget outcome: {problem.target_outcome}")

    return problem


# ============================================================================
# 4. STAKEHOLDERS AND DECISION RIGHTS
# ============================================================================

@dataclass
class Stakeholder:
    name: str
    role: str
    decision_right: str
    information_need: str


def create_stakeholder_map() -> List[Stakeholder]:
    """
    Stakeholder mapping prevents technically correct analysis from becoming
    operationally irrelevant.
    """

    stakeholders = [
        Stakeholder(
            "Chief Marketing Officer",
            "Executive sponsor",
            "Approve retention strategy",
            "Expected business impact and strategic trade-offs",
        ),
        Stakeholder(
            "Finance",
            "Financial control",
            "Approve economic assumptions",
            "Incremental revenue, cost, and margin",
        ),
        Stakeholder(
            "Analytics",
            "Analytical owner",
            "Design and validate analysis",
            "Data quality, methodology, uncertainty",
        ),
        Stakeholder(
            "CRM Operations",
            "Implementation owner",
            "Execute customer campaigns",
            "Target audience and campaign rules",
        ),
        Stakeholder(
            "Business Unit Leaders",
            "Operational stakeholders",
            "Provide operational constraints",
            "Customer and channel implications",
        ),
    ]

    print("\nSTAKEHOLDER MAP")
    print("-" * 80)

    for person in stakeholders:
        print(f"\n{person.name}")
        print(f"  Role: {person.role}")
        print(f"  Decision right: {person.decision_right}")
        print(f"  Information need: {person.information_need}")

    return stakeholders


# ============================================================================
# 5. ANALYTICAL QUESTIONS
# ============================================================================

def create_analytical_questions() -> List[str]:
    """
    Convert a broad business problem into answerable analytical questions.
    """

    questions = [
        "What is the current retention rate?",
        "How has retention changed over time?",
        "Which customer segments have the highest churn risk?",
        "Which behavioral variables are associated with churn?",
        "Are declining purchase frequency and declining monetary value related?",
        "Which customers have high predicted risk and high economic value?",
        "What happens to expected profit under different offer strategies?",
        "What evidence would demonstrate that an intervention caused improvement?",
    ]

    print("\nANALYTICAL QUESTIONS")
    print("-" * 80)

    for number, question in enumerate(questions, start=1):
        print(f"{number}. {question}")

    return questions


# ============================================================================
# 6. KPI AND METRIC DESIGN
# ============================================================================

@dataclass
class MetricDefinition:
    name: str
    formula: str
    purpose: str
    direction: str
    frequency: str


def create_metric_dictionary() -> List[MetricDefinition]:
    """
    A metric dictionary makes calculations consistent across teams.
    """

    metrics = [
        MetricDefinition(
            "Retention Rate",
            "Retained Customers / Eligible Customers",
            "Measure customer retention",
            "Higher is better",
            "Monthly",
        ),
        MetricDefinition(
            "Churn Rate",
            "Churned Customers / Eligible Customers",
            "Measure customer loss",
            "Lower is better",
            "Monthly",
        ),
        MetricDefinition(
            "Average Order Value",
            "Revenue / Number of Orders",
            "Measure average transaction value",
            "Context dependent",
            "Weekly",
        ),
        MetricDefinition(
            "Purchase Frequency",
            "Number of Orders / Customer",
            "Measure engagement",
            "Higher is generally better",
            "Monthly",
        ),
        MetricDefinition(
            "Customer Lifetime Value",
            "Expected future contribution from a customer",
            "Estimate economic customer value",
            "Higher is generally better",
            "Monthly",
        ),
        MetricDefinition(
            "Incremental Revenue",
            "Treatment Revenue - Expected Control Revenue",
            "Measure causal campaign impact",
            "Higher is better",
            "Campaign",
        ),
        MetricDefinition(
            "Incremental Profit",
            "Incremental Revenue - Incremental Cost",
            "Measure economic impact",
            "Higher is better",
            "Campaign",
        ),
    ]

    print("\nMETRIC DICTIONARY")
    print("-" * 80)

    for metric in metrics:
        print(f"\n{metric.name}")
        print(f"  Formula: {metric.formula}")
        print(f"  Purpose: {metric.purpose}")
        print(f"  Direction: {metric.direction}")
        print(f"  Frequency: {metric.frequency}")

    return metrics


# ============================================================================
# 7. SYNTHETIC DATA GENERATION
# ============================================================================

@dataclass
class Customer:
    customer_id: int
    age: int
    region: str
    channel: str
    orders: int
    revenue: float
    discount_rate: float
    support_tickets: int
    days_since_purchase: int
    satisfaction_score: float
    churned: int


def generate_customers(
    number_of_customers: int = 300,
    seed: int = 42,
) -> List[Customer]:
    """
    Generate synthetic customer data.

    Synthetic data is useful for demonstrating an analytics lifecycle without
    depending on external files or confidential customer information.
    """

    random.seed(seed)

    regions = ["North", "South", "East", "West"]
    channels = ["Store", "Online", "Mobile"]

    customers: List[Customer] = []

    for customer_id in range(1, number_of_customers + 1):
        age = random.randint(18, 70)
        region = random.choice(regions)
        channel = random.choice(channels)

        orders = max(1, int(random.gauss(7, 3)))
        average_order_value = max(20, random.gauss(75, 20))
        revenue = round(orders * average_order_value, 2)

        discount_rate = round(random.uniform(0.00, 0.35), 3)
        support_tickets = max(0, int(random.gauss(2, 1.5)))
        days_since_purchase = max(1, int(random.gauss(45, 30)))

        satisfaction_score = max(
            1.0,
            min(
                10.0,
                8.0
                + random.gauss(0, 1.2)
                - support_tickets * 0.25
                - max(days_since_purchase - 60, 0) * 0.01,
            ),
        )

        # The churn mechanism is deliberately probabilistic rather than
        # deterministic. Real business outcomes usually have multiple drivers.
        risk_score = (
            0.015 * days_since_purchase
            - 0.12 * orders
            - 0.45 * satisfaction_score
            + 0.25 * support_tickets
            + random.gauss(0, 1.0)
        )

        churn_probability = 1 / (1 + math.exp(-risk_score))
        churned = int(random.random() < churn_probability)

        customers.append(
            Customer(
                customer_id=customer_id,
                age=age,
                region=region,
                channel=channel,
                orders=orders,
                revenue=revenue,
                discount_rate=discount_rate,
                support_tickets=support_tickets,
                days_since_purchase=days_since_purchase,
                satisfaction_score=round(satisfaction_score, 2),
                churned=churned,
            )
        )

    return customers


# ============================================================================
# 8. DATA DICTIONARY
# ============================================================================

def print_data_dictionary() -> None:
    """
    Explain the meaning and type of each analytical field.
    """

    fields = [
        ("customer_id", "Integer", "Unique customer identifier"),
        ("age", "Integer", "Customer age"),
        ("region", "Categorical", "Geographic business region"),
        ("channel", "Categorical", "Primary customer channel"),
        ("orders", "Integer", "Number of orders"),
        ("revenue", "Numeric", "Observed customer revenue"),
        ("discount_rate", "Numeric", "Average discount rate"),
        ("support_tickets", "Integer", "Number of support tickets"),
        ("days_since_purchase", "Integer", "Recency measure"),
        ("satisfaction_score", "Numeric", "Customer satisfaction score"),
        ("churned", "Binary", "Target outcome: 1 = churned"),
    ]

    print("\nDATA DICTIONARY")
    print("-" * 80)

    for name, data_type, description in fields:
        print(f"{name:25} {data_type:15} {description}")


# ============================================================================
# 9. DATA QUALITY
# ============================================================================

def detect_missing_values(customers: Sequence[Customer]) -> Dict[str, int]:
    """
    Demonstrate missing-value detection.

    Dataclasses do not naturally contain missing fields in this example, so
    the function illustrates the validation pattern using explicit checks.
    """

    missing = Counter()

    for customer in customers:
        values = {
            "age": customer.age,
            "region": customer.region,
            "channel": customer.channel,
            "orders": customer.orders,
            "revenue": customer.revenue,
            "discount_rate": customer.discount_rate,
            "support_tickets": customer.support_tickets,
            "days_since_purchase": customer.days_since_purchase,
            "satisfaction_score": customer.satisfaction_score,
            "churned": customer.churned,
        }

        for field_name, value in values.items():
            if value is None:
                missing[field_name] += 1

    return dict(missing)


def validate_customer_data(customers: Sequence[Customer]) -> List[str]:
    """
    Validate ranges, categorical values, uniqueness, and logical constraints.
    """

    errors: List[str] = []
    customer_ids = set()

    valid_regions = {"North", "South", "East", "West"}
    valid_channels = {"Store", "Online", "Mobile"}

    for customer in customers:
        if customer.customer_id in customer_ids:
            errors.append(
                f"Duplicate customer ID: {customer.customer_id}"
            )
        customer_ids.add(customer.customer_id)

        if not 0 < customer.age <= 120:
            errors.append(
                f"Invalid age for customer {customer.customer_id}"
            )

        if customer.region not in valid_regions:
            errors.append(
                f"Invalid region for customer {customer.customer_id}"
            )

        if customer.channel not in valid_channels:
            errors.append(
                f"Invalid channel for customer {customer.customer_id}"
            )

        if customer.orders < 0:
            errors.append(
                f"Negative order count for customer {customer.customer_id}"
            )

        if customer.revenue < 0:
            errors.append(
                f"Negative revenue for customer {customer.customer_id}"
            )

        if not 0 <= customer.discount_rate <= 1:
            errors.append(
                f"Invalid discount rate for customer {customer.customer_id}"
            )

        if customer.support_tickets < 0:
            errors.append(
                f"Negative support ticket count for customer {customer.customer_id}"
            )

        if customer.days_since_purchase < 0:
            errors.append(
                f"Negative recency for customer {customer.customer_id}"
            )

        if not 1 <= customer.satisfaction_score <= 10:
            errors.append(
                f"Invalid satisfaction score for customer {customer.customer_id}"
            )

        if customer.churned not in {0, 1}:
            errors.append(
                f"Invalid churn value for customer {customer.customer_id}"
            )

    return errors


def demonstrate_data_quality(customers: Sequence[Customer]) -> None:
    print("\nDATA QUALITY ASSESSMENT")
    print("-" * 80)

    missing = detect_missing_values(customers)
    errors = validate_customer_data(customers)

    print(f"Records inspected: {len(customers)}")
    print(f"Missing-value fields: {missing if missing else 'None'}")
    print(f"Validation errors: {len(errors)}")

    if errors:
        for error in errors[:10]:
            print(f"  - {error}")

    print(
        "\nImportant distinction: a dataset can contain no missing values and "
        "still be incorrect. Validity, consistency, uniqueness, timeliness, "
        "completeness, and business-rule correctness are separate concerns."
    )


# ============================================================================
# 10. DATA TRANSFORMATION
# ============================================================================

@dataclass
class CustomerFeature:
    customer_id: int
    revenue: float
    orders: int
    recency: int
    satisfaction: float
    support_tickets: int
    churned: int
    revenue_per_order: float
    engagement_score: float
    risk_score: float


def engineer_features(customers: Sequence[Customer]) -> List[CustomerFeature]:
    """
    Transform raw business data into analytical features.

    Feature engineering should preserve business meaning and avoid leakage.
    """

    features: List[CustomerFeature] = []

    for customer in customers:
        revenue_per_order = (
            customer.revenue / customer.orders
            if customer.orders > 0
            else 0.0
        )

        # Higher engagement is better.
        engagement_score = (
            customer.orders * 0.45
            + customer.satisfaction_score * 0.40
            - customer.days_since_purchase * 0.05
        )

        # Higher risk is worse.
        risk_score = (
            customer.days_since_purchase * 0.05
            - customer.orders * 0.35
            - customer.satisfaction_score * 0.30
            + customer.support_tickets * 0.40
        )

        features.append(
            CustomerFeature(
                customer_id=customer.customer_id,
                revenue=customer.revenue,
                orders=customer.orders,
                recency=customer.days_since_purchase,
                satisfaction=customer.satisfaction_score,
                support_tickets=customer.support_tickets,
                churned=customer.churned,
                revenue_per_order=round(revenue_per_order, 2),
                engagement_score=round(engagement_score, 2),
                risk_score=round(risk_score, 2),
            )
        )

    return features


# ============================================================================
# 11. DESCRIPTIVE ANALYTICS
# ============================================================================

def mean(values: Sequence[float]) -> float:
    return statistics.mean(values) if values else 0.0


def median(values: Sequence[float]) -> float:
    return statistics.median(values) if values else 0.0


def percentile(values: Sequence[float], percentile_value: float) -> float:
    """
    Linear interpolation percentile implementation using only the standard
    library.
    """

    if not values:
        return 0.0

    ordered = sorted(values)

    if percentile_value <= 0:
        return ordered[0]

    if percentile_value >= 100:
        return ordered[-1]

    position = (len(ordered) - 1) * percentile_value / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def describe_numeric_variable(
    values: Sequence[float],
    variable_name: str,
) -> None:
    print(f"\n{variable_name}")
    print(f"  Count: {len(values)}")
    print(f"  Mean: {mean(values):.2f}")
    print(f"  Median: {median(values):.2f}")
    print(f"  Minimum: {min(values):.2f}")
    print(f"  Maximum: {max(values):.2f}")
    print(f"  25th percentile: {percentile(values, 25):.2f}")
    print(f"  75th percentile: {percentile(values, 75):.2f}")


def descriptive_analysis(customers: Sequence[Customer]) -> Dict[str, float]:
    """
    Calculate descriptive statistics and the principal retention KPIs.
    """

    print("\nDESCRIPTIVE ANALYTICS")
    print("-" * 80)

    revenues = [customer.revenue for customer in customers]
    orders = [customer.orders for customer in customers]
    recency = [customer.days_since_purchase for customer in customers]
    satisfaction = [customer.satisfaction_score for customer in customers]

    describe_numeric_variable(revenues, "Revenue")
    describe_numeric_variable(orders, "Orders")
    describe_numeric_variable(recency, "Days since purchase")
    describe_numeric_variable(satisfaction, "Satisfaction")

    total_customers = len(customers)
    churned_customers = sum(customer.churned for customer in customers)

    churn_rate = (
        churned_customers / total_customers
        if total_customers
        else 0.0
    )

    retention_rate = 1 - churn_rate

    total_revenue = sum(revenues)
    average_order_value = (
        total_revenue / sum(orders)
        if sum(orders)
        else 0.0
    )

    metrics = {
        "customers": total_customers,
        "churned": churned_customers,
        "churn_rate": churn_rate,
        "retention_rate": retention_rate,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
    }

    print("\nKEY PERFORMANCE INDICATORS")
    print(f"Customers: {total_customers}")
    print(f"Churned customers: {churned_customers}")
    print(f"Churn rate: {churn_rate:.2%}")
    print(f"Retention rate: {retention_rate:.2%}")
    print(f"Revenue: {total_revenue:,.2f}")
    print(f"Average order value: {average_order_value:,.2f}")

    return metrics


# ============================================================================
# 12. FREQUENCY DISTRIBUTIONS
# ============================================================================

def frequency_distribution(
    customers: Sequence[Customer],
    attribute: str,
) -> Counter:
    """
    Count categorical values.
    """

    values = [getattr(customer, attribute) for customer in customers]
    return Counter(values)


def demonstrate_distributions(customers: Sequence[Customer]) -> None:
    print("\nCATEGORICAL DISTRIBUTIONS")
    print("-" * 80)

    for attribute in ("region", "channel"):
        distribution = frequency_distribution(customers, attribute)
        print(f"\n{attribute.capitalize()}:")

        for category, count in distribution.items():
            share = count / len(customers)
            print(f"  {category}: {count} ({share:.2%})")


# ============================================================================
# 13. SEGMENTATION
# ============================================================================

def segment_customer(customer: Customer) -> str:
    """
    Simple business segmentation based on value and recency.

    Segmentation rules should be documented because changing thresholds can
    materially change business decisions.
    """

    high_value = customer.revenue >= 600
    active = customer.days_since_purchase <= 45
    low_satisfaction = customer.satisfaction_score < 6

    if high_value and active:
        return "High-value active"

    if high_value and not active:
        return "High-value at-risk"

    if low_satisfaction:
        return "Low-satisfaction"

    return "Standard"


def analyze_segments(customers: Sequence[Customer]) -> Dict[str, Dict[str, float]]:
    print("\nCUSTOMER SEGMENTATION")
    print("-" * 80)

    grouped: Dict[str, List[Customer]] = defaultdict(list)

    for customer in customers:
        grouped[segment_customer(customer)].append(customer)

    results: Dict[str, Dict[str, float]] = {}

    for segment, members in sorted(grouped.items()):
        revenue = sum(customer.revenue for customer in members)
        churn_rate = (
            sum(customer.churned for customer in members) / len(members)
            if members
            else 0.0
        )

        results[segment] = {
            "customers": len(members),
            "revenue": revenue,
            "churn_rate": churn_rate,
        }

        print(f"\n{segment}")
        print(f"  Customers: {len(members)}")
        print(f"  Revenue: {revenue:,.2f}")
        print(f"  Churn rate: {churn_rate:.2%}")

    return results


# ============================================================================
# 14. CORRELATION
# ============================================================================

def pearson_correlation(
    x: Sequence[float],
    y: Sequence[float],
) -> float:
    """
    Calculate Pearson correlation without external packages.

    Pearson correlation measures linear association. It does not establish
    causality.
    """

    if len(x) != len(y):
        raise ValueError("Both variables must contain the same number of values.")

    if len(x) < 2:
        raise ValueError("At least two observations are required.")

    mean_x = mean(x)
    mean_y = mean(y)

    numerator = sum(
        (value_x - mean_x) * (value_y - mean_y)
        for value_x, value_y in zip(x, y)
    )

    denominator_x = math.sqrt(
        sum((value_x - mean_x) ** 2 for value_x in x)
    )

    denominator_y = math.sqrt(
        sum((value_y - mean_y) ** 2 for value_y in y)
    )

    denominator = denominator_x * denominator_y

    if denominator == 0:
        return 0.0

    return numerator / denominator


def correlation_analysis(customers: Sequence[Customer]) -> None:
    print("\nCORRELATION ANALYSIS")
    print("-" * 80)

    churn = [customer.churned for customer in customers]

    variables = {
        "orders": [customer.orders for customer in customers],
        "revenue": [customer.revenue for customer in customers],
        "recency": [
            customer.days_since_purchase
            for customer in customers
        ],
        "satisfaction": [
            customer.satisfaction_score
            for customer in customers
        ],
        "support_tickets": [
            customer.support_tickets
            for customer in customers
        ],
    }

    for name, values in variables.items():
        correlation = pearson_correlation(values, churn)
        print(f"Correlation of {name:20} with churn: {correlation:.3f}")

    print(
        "\nInterpretation warning: correlation identifies association. "
        "It does not demonstrate that changing one variable will cause the "
        "business outcome to change."
    )


# ============================================================================
# 15. DIAGNOSTIC ANALYTICS
# ============================================================================

def diagnostic_analysis(customers: Sequence[Customer]) -> None:
    """
    Compare churn behavior across important groups.
    """

    print("\nDIAGNOSTIC ANALYTICS")
    print("-" * 80)

    # Compare churn by channel.
    by_channel: Dict[str, List[Customer]] = defaultdict(list)

    for customer in customers:
        by_channel[customer.channel].append(customer)

    print("\nChurn by channel:")

    for channel, members in by_channel.items():
        churn_rate = mean([customer.churned for customer in members])
        print(f"  {channel}: {churn_rate:.2%}")

    # Compare churn by recency bands.
    bands: Dict[str, List[Customer]] = {
        "0-30 days": [],
        "31-60 days": [],
        "61-90 days": [],
        "91+ days": [],
    }

    for customer in customers:
        if customer.days_since_purchase <= 30:
            bands["0-30 days"].append(customer)
        elif customer.days_since_purchase <= 60:
            bands["31-60 days"].append(customer)
        elif customer.days_since_purchase <= 90:
            bands["61-90 days"].append(customer)
        else:
            bands["91+ days"].append(customer)

    print("\nChurn by recency band:")

    for band, members in bands.items():
        if members:
            churn_rate = mean([customer.churned for customer in members])
            print(f"  {band}: {churn_rate:.2%} ({len(members)} customers)")


# ============================================================================
# 16. SIMPLE PREDICTIVE ANALYTICS
# ============================================================================

def sigmoid(value: float) -> float:
    """
    Numerically stable logistic transformation for ordinary business-scale
    values.
    """

    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)

    z = math.exp(value)
    return z / (1 + z)


@dataclass
class LogisticModel:
    weights: List[float]
    intercept: float
    feature_names: List[str]

    def predict_probability(self, features: Sequence[float]) -> float:
        if len(features) != len(self.weights):
            raise ValueError("Feature count does not match model weights.")

        linear_score = self.intercept + sum(
            weight * feature
            for weight, feature in zip(self.weights, features)
        )

        return sigmoid(linear_score)


def standardize(
    values: Sequence[float],
) -> Tuple[List[float], float, float]:
    """
    Standardization transforms a variable to approximately mean 0 and
    standard deviation 1.

    The training mean and standard deviation must be reused for future data.
    """

    if not values:
        return [], 0.0, 1.0

    average = mean(values)
    standard_deviation = statistics.pstdev(values)

    if standard_deviation == 0:
        standard_deviation = 1.0

    standardized = [
        (value - average) / standard_deviation
        for value in values
    ]

    return standardized, average, standard_deviation


def train_logistic_regression(
    customers: Sequence[Customer],
    epochs: int = 2500,
    learning_rate: float = 0.03,
) -> LogisticModel:
    """
    Train a small binary logistic regression model using gradient descent.

    This implementation is intentionally educational. Production modeling
    requires stronger validation, regularization, calibration, monitoring,
    documentation, and appropriate statistical controls.
    """

    raw_features = [
        [
            customer.orders,
            customer.revenue,
            customer.days_since_purchase,
            customer.satisfaction_score,
            customer.support_tickets,
        ]
        for customer in customers
    ]

    feature_names = [
        "orders",
        "revenue",
        "days_since_purchase",
        "satisfaction_score",
        "support_tickets",
    ]

    columns = list(zip(*raw_features))
    standardized_columns = []

    for column in columns:
        standardized_column, _, _ = standardize(column)
        standardized_columns.append(standardized_column)

    X = [
        [
            standardized_columns[column_index][row_index]
            for column_index in range(len(standardized_columns))
        ]
        for row_index in range(len(customers))
    ]

    y = [customer.churned for customer in customers]

    weights = [0.0] * len(feature_names)
    intercept = 0.0

    for _ in range(epochs):
        probabilities = []

        for row in X:
            score = intercept + sum(
                weight * value
                for weight, value in zip(weights, row)
            )
            probabilities.append(sigmoid(score))

        gradient_weights = [0.0] * len(weights)
        gradient_intercept = 0.0

        for row, actual, predicted in zip(X, y, probabilities):
            error = predicted - actual

            gradient_intercept += error

            for index, value in enumerate(row):
                gradient_weights[index] += error * value

        n = len(X)

        gradient_intercept /= n

        for index in range(len(weights)):
            gradient_weights[index] /= n

            weights[index] -= learning_rate * gradient_weights[index]

        intercept -= learning_rate * gradient_intercept

    return LogisticModel(
        weights=weights,
        intercept=intercept,
        feature_names=feature_names,
    )


# ============================================================================
# 17. MODEL EVALUATION
# ============================================================================

def confusion_matrix(
    actual: Sequence[int],
    predicted: Sequence[int],
) -> Dict[str, int]:
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted values must have equal length.")

    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for actual_value, predicted_value in zip(actual, predicted):
        if actual_value == 1 and predicted_value == 1:
            true_positive += 1
        elif actual_value == 0 and predicted_value == 0:
            true_negative += 1
        elif actual_value == 0 and predicted_value == 1:
            false_positive += 1
        elif actual_value == 1 and predicted_value == 0:
            false_negative += 1

    return {
        "TP": true_positive,
        "TN": true_negative,
        "FP": false_positive,
        "FN": false_negative,
    }


def classification_metrics(
    actual: Sequence[int],
    predicted: Sequence[int],
) -> Dict[str, float]:
    matrix = confusion_matrix(actual, predicted)

    tp = matrix["TP"]
    tn = matrix["TN"]
    fp = matrix["FP"]
    fn = matrix["FN"]

    total = tp + tn + fp + fn

    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    specificity = tn / (tn + fp) if tn + fp else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "specificity": specificity,
    }


def evaluate_model(
    model: LogisticModel,
    customers: Sequence[Customer],
) -> None:
    """
    Evaluate using the same data for educational simplicity.

    A production workflow must use independent validation or test data.
    """

    predictions: List[int] = []
    actual: List[int] = []

    for customer in customers:
        raw_features = [
            customer.orders,
            customer.revenue,
            customer.days_since_purchase,
            customer.satisfaction_score,
            customer.support_tickets,
        ]

        # The educational model was trained using standardized values, but
        # this demonstration recreates standardization across the full dataset.
        # Production systems must persist training transformations.
        predictions.append(
            int(model.predict_probability(
                [
                    raw_features[0],
                    raw_features[1],
                    raw_features[2],
                    raw_features[3],
                    raw_features[4],
                ]
            ) >= 0.5)
        )

        actual.append(customer.churned)

    metrics = classification_metrics(actual, predictions)
    matrix = confusion_matrix(actual, predictions)

    print("\nMODEL EVALUATION")
    print("-" * 80)

    print("Confusion matrix:")
    for key, value in matrix.items():
        print(f"  {key}: {value}")

    print("\nClassification metrics:")

    for name, value in metrics.items():
        print(f"  {name}: {value:.3f}")

    print(
        "\nImportant implementation note: this model evaluation is deliberately "
        "simplified. A real model must separate training and evaluation data, "
        "preserve preprocessing parameters, and evaluate against the actual "
        "decision objective."
    )


# ============================================================================
# 18. RISK SCORING FOR DECISION SUPPORT
# ============================================================================

def calculate_risk_scores(
    customers: Sequence[Customer],
) -> List[Tuple[int, float, float]]:
    """
    Produce a simple operational risk score.

    Returns:
        customer_id, risk_score, revenue
    """

    scored = []

    for customer in customers:
        risk = (
            customer.days_since_purchase * 0.04
            - customer.orders * 0.25
            - customer.satisfaction_score * 0.35
            + customer.support_tickets * 0.35
        )

        scored.append(
            (
                customer.customer_id,
                risk,
                customer.revenue,
            )
        )

    return sorted(scored, key=lambda row: row[1], reverse=True)


def show_high_priority_customers(
    customers: Sequence[Customer],
    limit: int = 10,
) -> None:
    """
    Prioritize high-risk customers while considering economic value.

    Risk alone is not enough. A business decision often needs a combination
    of probability, value, cost, and action effectiveness.
    """

    print("\nHIGH-PRIORITY CUSTOMER ANALYSIS")
    print("-" * 80)

    scored = calculate_risk_scores(customers)

    customer_lookup = {
        customer.customer_id: customer
        for customer in customers
    }

    for customer_id, risk_score, revenue in scored[:limit]:
        customer = customer_lookup[customer_id]

        print(
            f"Customer {customer_id:3d} | "
            f"Risk={risk_score:7.2f} | "
            f"Revenue={revenue:8.2f} | "
            f"Recency={customer.days_since_purchase:3d} | "
            f"Satisfaction={customer.satisfaction_score:4.1f}"
        )


# ============================================================================
# 19. CUSTOMER LIFETIME VALUE
# ============================================================================

def estimate_clv(
    average_order_value: float,
    purchase_frequency_per_year: float,
    gross_margin_rate: float,
    annual_retention_rate: float,
    discount_rate: float = 0.10,
    years: int = 5,
) -> float:
    """
    Estimate CLV using a finite-horizon contribution model.

    CLV is highly assumption-sensitive. It should be treated as an estimate,
    not a directly observed accounting value.
    """

    if not 0 <= gross_margin_rate <= 1:
        raise ValueError("Gross margin rate must be between 0 and 1.")

    if not 0 <= annual_retention_rate <= 1:
        raise ValueError("Retention rate must be between 0 and 1.")

    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")

    value = 0.0

    annual_contribution = (
        average_order_value
        * purchase_frequency_per_year
        * gross_margin_rate
    )

    for year in range(1, years + 1):
        probability_of_survival = annual_retention_rate ** (year - 1)
        discounted_contribution = (
            annual_contribution
            * probability_of_survival
            / ((1 + discount_rate) ** year)
        )

        value += discounted_contribution

    return value


def demonstrate_clv() -> None:
    print("\nCUSTOMER LIFETIME VALUE")
    print("-" * 80)

    clv = estimate_clv(
        average_order_value=80,
        purchase_frequency_per_year=6,
        gross_margin_rate=0.35,
        annual_retention_rate=0.70,
        discount_rate=0.10,
        years=5,
    )

    print(f"Illustrative five-year CLV: {clv:,.2f}")

    print(
        "\nCLV depends on assumptions about future behavior, margin, retention, "
        "discounting, and horizon. Changing these assumptions can materially "
        "change customer prioritization."
    )


# ============================================================================
# 20. SCENARIO ANALYSIS
# ============================================================================

@dataclass
class RetentionScenario:
    name: str
    eligible_customers: int
    expected_incremental_retention: float
    average_customer_value: float
    intervention_cost_per_customer: float

    def expected_incremental_revenue(self) -> float:
        return (
            self.eligible_customers
            * self.expected_incremental_retention
            * self.average_customer_value
        )

    def total_intervention_cost(self) -> float:
        return (
            self.eligible_customers
            * self.intervention_cost_per_customer
        )

    def expected_incremental_profit(
        self,
        contribution_margin_rate: float,
    ) -> float:
        incremental_revenue = self.expected_incremental_revenue()

        contribution = (
            incremental_revenue * contribution_margin_rate
        )

        return contribution - self.total_intervention_cost()


def run_scenario_analysis() -> None:
    print("\nSCENARIO ANALYSIS")
    print("-" * 80)

    scenarios = [
        RetentionScenario(
            "No intervention",
            1000,
            0.00,
            300,
            0,
        ),
        RetentionScenario(
            "Low-cost reminder",
            1000,
            0.025,
            300,
            2,
        ),
        RetentionScenario(
            "Moderate incentive",
            1000,
            0.055,
            300,
            8,
        ),
        RetentionScenario(
            "High incentive",
            1000,
            0.075,
            300,
            18,
        ),
    ]

    contribution_margin_rate = 0.35

    print(
        f"{'Scenario':25} "
        f"{'Incremental Revenue':>20} "
        f"{'Cost':>12} "
        f"{'Profit':>15}"
    )

    for scenario in scenarios:
        revenue = scenario.expected_incremental_revenue()
        cost = scenario.total_intervention_cost()
        profit = scenario.expected_incremental_profit(
            contribution_margin_rate
        )

        print(
            f"{scenario.name:25} "
            f"{revenue:20,.2f} "
            f"{cost:12,.2f} "
            f"{profit:15,.2f}"
        )


# ============================================================================
# 21. PRESCRIPTIVE ANALYTICS
# ============================================================================

def optimize_offer_allocation(
    customers: Sequence[Customer],
    budget: float,
) -> List[Tuple[int, str, float]]:
    """
    A simple greedy prescriptive approach.

    For each customer, estimate expected incremental profit from a retention
    action and choose customers in descending value until the budget is used.

    This is a simplified decision rule rather than a general optimization
    solver.
    """

    candidates = []

    for customer in customers:
        risk_probability = sigmoid(
            -2
            + customer.days_since_purchase * 0.035
            - customer.orders * 0.18
            - customer.satisfaction_score * 0.20
            + customer.support_tickets * 0.25
        )

        expected_lost_value = customer.revenue * risk_probability

        intervention_cost = 5.0

        expected_saved_value = (
            expected_lost_value * 0.20
        )

        expected_profit = expected_saved_value - intervention_cost

        if expected_profit > 0:
            candidates.append(
                (
                    customer.customer_id,
                    "Retention offer",
                    expected_profit,
                    intervention_cost,
                )
            )

    candidates.sort(key=lambda item: item[2], reverse=True)

    selected: List[Tuple[int, str, float]] = []
    spent = 0.0

    for customer_id, action, expected_profit, cost in candidates:
        if spent + cost > budget:
            continue

        selected.append(
            (customer_id, action, expected_profit)
        )

        spent += cost

    print("\nPRESCRIPTIVE ANALYTICS")
    print("-" * 80)
    print(f"Budget: {budget:,.2f}")
    print(f"Selected customers: {len(selected)}")
    print(f"Estimated spend: {len(selected) * 5:,.2f}")
    print(
        f"Estimated expected profit: "
        f"{sum(row[2] for row in selected):,.2f}"
    )

    return selected


# ============================================================================
# 22. A/B TESTING
# ============================================================================

@dataclass
class ExperimentResult:
    control_customers: int
    treatment_customers: int
    control_successes: int
    treatment_successes: int

    @property
    def control_rate(self) -> float:
        return self.control_successes / self.control_customers

    @property
    def treatment_rate(self) -> float:
        return self.treatment_successes / self.treatment_customers

    @property
    def absolute_lift(self) -> float:
        return self.treatment_rate - self.control_rate

    @property
    def relative_lift(self) -> float:
        if self.control_rate == 0:
            return 0.0

        return self.absolute_lift / self.control_rate


def two_proportion_z_test(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
) -> Tuple[float, float]:
    """
    Approximate two-proportion z-test.

    The p-value is calculated using the normal distribution approximation.

    For production experimentation, statistical assumptions, randomization,
    sample size, sequential testing, multiple testing, power, interference,
    and practical significance must be considered.
    """

    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("Group sizes must be positive.")

    p_control = control_successes / control_n
    p_treatment = treatment_successes / treatment_n

    pooled = (
        (control_successes + treatment_successes)
        / (control_n + treatment_n)
    )

    standard_error = math.sqrt(
        pooled * (1 - pooled)
        * (1 / control_n + 1 / treatment_n)
    )

    if standard_error == 0:
        return 0.0, 1.0

    z = (p_treatment - p_control) / standard_error

    # Two-sided normal approximation.
    p_value = math.erfc(abs(z) / math.sqrt(2))

    return z, p_value


def demonstrate_ab_test() -> None:
    print("\nA/B TESTING")
    print("-" * 80)

    experiment = ExperimentResult(
        control_customers=5000,
        treatment_customers=5000,
        control_successes=525,
        treatment_successes=610,
    )

    z_score, p_value = two_proportion_z_test(
        experiment.control_successes,
        experiment.control_customers,
        experiment.treatment_successes,
        experiment.treatment_customers,
    )

    print(f"Control rate: {experiment.control_rate:.2%}")
    print(f"Treatment rate: {experiment.treatment_rate:.2%}")
    print(f"Absolute lift: {experiment.absolute_lift:.2%}")
    print(f"Relative lift: {experiment.relative_lift:.2%}")
    print(f"Z-score: {z_score:.3f}")
    print(f"Approximate p-value: {p_value:.5f}")

    print(
        "\nStatistical significance does not automatically imply business "
        "significance. A small effect can be statistically detectable but "
        "economically irrelevant."
    )


# ============================================================================
# 23. INSIGHT GENERATION
# ============================================================================

@dataclass
class Insight:
    observation: str
    evidence: str
    interpretation: str
    business_implication: str
    confidence: str


def generate_insights(
    customers: Sequence[Customer],
    segments: Dict[str, Dict[str, float]],
) -> List[Insight]:
    """
    Convert analytical observations into decision-relevant statements.

    A useful insight should connect evidence with meaning and business impact.
    """

    churn_rate = mean([customer.churned for customer in customers])

    high_value_at_risk = segments.get(
        "High-value at-risk",
        {
            "customers": 0,
            "revenue": 0,
            "churn_rate": 0,
        },
    )

    insights = [
        Insight(
            observation="Customer churn is measurable at a material rate.",
            evidence=f"Observed churn rate: {churn_rate:.2%}.",
            interpretation=(
                "Customer loss is sufficiently frequent to justify "
                "segmentation and targeted retention analysis."
            ),
            business_implication=(
                "Retention interventions should be evaluated for economic "
                "impact rather than applied uniformly."
            ),
            confidence="Descriptive",
        ),
        Insight(
            observation=(
                "High-value customers who have not purchased recently "
                "represent an important risk group."
            ),
            evidence=(
                f"High-value at-risk customers: "
                f"{int(high_value_at_risk['customers'])}; "
                f"segment churn rate: "
                f"{high_value_at_risk['churn_rate']:.2%}."
            ),
            interpretation=(
                "Customer value and recency together provide a more useful "
                "prioritization framework than either variable alone."
            ),
            business_implication=(
                "Retention resources can be concentrated where potential "
                "economic impact is highest."
            ),
            confidence="Descriptive and diagnostic",
        ),
    ]

    print("\nINSIGHT GENERATION")
    print("-" * 80)

    for index, insight in enumerate(insights, start=1):
        print(f"\nInsight {index}")
        print(f"  Observation: {insight.observation}")
        print(f"  Evidence: {insight.evidence}")
        print(f"  Interpretation: {insight.interpretation}")
        print(f"  Business implication: {insight.business_implication}")
        print(f"  Confidence type: {insight.confidence}")

    return insights


# ============================================================================
# 24. RECOMMENDATIONS
# ============================================================================

@dataclass
class Recommendation:
    action: str
    rationale: str
    expected_benefit: str
    risk: str
    measurement: str


def create_recommendations() -> List[Recommendation]:
    """
    Recommendations should be actionable and measurable.

    An insight says what the evidence means. A recommendation says what should
    be done about it.
    """

    recommendations = [
        Recommendation(
            action=(
                "Prioritize retention interventions for high-value customers "
                "with elevated recency risk."
            ),
            rationale=(
                "These customers combine economic value with observable "
                "behavioral risk."
            ),
            expected_benefit=(
                "Potentially higher incremental value per intervention."
            ),
            risk=(
                "Over-targeting may create unnecessary promotional costs."
            ),
            measurement=(
                "Incremental retention, contribution profit, and ROI versus "
                "a randomized control group."
            ),
        ),
        Recommendation(
            action=(
                "Use lower-cost interventions before high-discount offers."
            ),
            rationale=(
                "Scenario analysis should favor economically positive actions "
                "rather than maximizing retention regardless of cost."
            ),
            expected_benefit=(
                "Improved contribution economics."
            ),
            risk=(
                "Low-intensity interventions may have weaker treatment effects."
            ),
            measurement=(
                "Incremental profit per targeted customer."
            ),
        ),
        Recommendation(
            action=(
                "Validate campaign effectiveness through controlled experiments."
            ),
            rationale=(
                "Observed changes cannot automatically be attributed to the "
                "campaign without an appropriate counterfactual."
            ),
            expected_benefit=(
                "Stronger evidence of causal impact."
            ),
            risk=(
                "Poor randomization or contamination can invalidate results."
            ),
            measurement=(
                "Treatment-control lift with confidence intervals and "
                "business-value analysis."
            ),
        ),
    ]

    print("\nRECOMMENDATIONS")
    print("-" * 80)

    for number, recommendation in enumerate(recommendations, start=1):
        print(f"\nRecommendation {number}")
        print(f"  Action: {recommendation.action}")
        print(f"  Rationale: {recommendation.rationale}")
        print(f"  Expected benefit: {recommendation.expected_benefit}")
        print(f"  Risk: {recommendation.risk}")
        print(f"  Measurement: {recommendation.measurement}")

    return recommendations


# ============================================================================
# 25. DECISION MATRIX
# ============================================================================

def decision_matrix() -> None:
    """
    Demonstrate structured decision-making.

    Analytics informs a decision, but the final decision can also depend on
    legal, operational, strategic, financial, and ethical constraints.
    """

    options = [
        {
            "option": "No intervention",
            "expected_value": 0.45,
            "implementation": 1.00,
            "risk": 0.95,
            "strategic_fit": 0.30,
        },
        {
            "option": "Low-cost retention",
            "expected_value": 0.78,
            "implementation": 0.90,
            "risk": 0.75,
            "strategic_fit": 0.85,
        },
        {
            "option": "High-discount retention",
            "expected_value": 0.65,
            "implementation": 0.80,
            "risk": 0.40,
            "strategic_fit": 0.70,
        },
    ]

    weights = {
        "expected_value": 0.40,
        "implementation": 0.15,
        "risk": 0.15,
        "strategic_fit": 0.30,
    }

    print("\nDECISION MATRIX")
    print("-" * 80)

    scored_options = []

    for option in options:
        score = sum(
            option[criterion] * weight
            for criterion, weight in weights.items()
        )

        scored_options.append(
            (option["option"], score)
        )

        print(
            f"{option['option']:25} "
            f"weighted score={score:.3f}"
        )

    best = max(scored_options, key=lambda item: item[1])

    print(f"\nHighest modeled score: {best[0]}")

    print(
        "\nA decision matrix is not objective merely because it contains "
        "numbers. Weights, scoring rules, assumptions, and constraints all "
        "reflect judgment and should be documented."
    )


# ============================================================================
# 26. IMPLEMENTATION PLAN
# ============================================================================

@dataclass
class ImplementationTask:
    task: str
    owner: str
    dependency: str
    success_measure: str


def create_implementation_plan() -> List[ImplementationTask]:
    tasks = [
        ImplementationTask(
            "Finalize target-selection rules",
            "Analytics + Marketing",
            "Validated analytical definitions",
            "Approved customer-selection logic",
        ),
        ImplementationTask(
            "Create campaign audience",
            "CRM Operations",
            "Target-selection rules",
            "Audience generated without data-quality errors",
        ),
        ImplementationTask(
            "Configure treatment and control groups",
            "CRM Operations + Analytics",
            "Experiment design",
            "Randomized assignment preserved",
        ),
        ImplementationTask(
            "Launch campaign",
            "Marketing",
            "Operational readiness",
            "Campaign delivered successfully",
        ),
        ImplementationTask(
            "Measure incremental outcomes",
            "Analytics + Finance",
            "Experiment data",
            "Validated incremental profit estimate",
        ),
        ImplementationTask(
            "Review and scale decision",
            "Executive sponsor",
            "Experiment and financial results",
            "Scale, modify, or stop decision documented",
        ),
    ]

    print("\nIMPLEMENTATION PLAN")
    print("-" * 80)

    for task in tasks:
        print(f"\nTask: {task.task}")
        print(f"  Owner: {task.owner}")
        print(f"  Dependency: {task.dependency}")
        print(f"  Success measure: {task.success_measure}")

    return tasks


# ============================================================================
# 27. MONITORING
# ============================================================================

@dataclass
class MonitoringMetric:
    name: str
    target: float
    alert_threshold: float
    direction: str


def monitor_kpis(
    observed_metrics: Dict[str, float],
    definitions: Sequence[MonitoringMetric],
) -> None:
    """
    Monitoring compares observed performance with predefined thresholds.

    Monitoring should distinguish ordinary variation from meaningful changes.
    """

    print("\nMONITORING AND CONTROL")
    print("-" * 80)

    for definition in definitions:
        observed = observed_metrics.get(definition.name)

        if observed is None:
            print(f"{definition.name}: NO DATA")
            continue

        if definition.direction == "higher":
            status = (
                "ALERT"
                if observed < definition.alert_threshold
                else "OK"
            )
        else:
            status = (
                "ALERT"
                if observed > definition.alert_threshold
                else "OK"
            )

        print(
            f"{definition.name:25} "
            f"Observed={observed:.3f} "
            f"Target={definition.target:.3f} "
            f"Status={status}"
        )


# ============================================================================
# 28. DATA AND MODEL DRIFT
# ============================================================================

def population_stability_index(
    expected: Sequence[float],
    actual: Sequence[float],
    bins: int = 10,
) -> float:
    """
    Calculate a simplified Population Stability Index.

    PSI is commonly used as a monitoring signal for distribution shifts.
    Thresholds are context dependent and should not be interpreted as universal
    laws.
    """

    if not expected or not actual:
        raise ValueError("Both populations must contain observations.")

    combined = sorted(list(expected) + list(actual))

    boundaries = [
        percentile(combined, i * 100 / bins)
        for i in range(bins + 1)
    ]

    # Ensure boundaries are strictly increasing when the data contain ties.
    unique_boundaries = sorted(set(boundaries))

    if len(unique_boundaries) < 2:
        return 0.0

    def proportions(values: Sequence[float]) -> List[float]:
        counts = [0] * (len(unique_boundaries) - 1)

        for value in values:
            placed = False

            for index in range(len(unique_boundaries) - 1):
                lower = unique_boundaries[index]
                upper = unique_boundaries[index + 1]

                if (
                    lower <= value < upper
                    or (
                        index == len(unique_boundaries) - 2
                        and value == upper
                    )
                ):
                    counts[index] += 1
                    placed = True
                    break

            if not placed:
                if value < unique_boundaries[0]:
                    counts[0] += 1
                else:
                    counts[-1] += 1

        total = len(values)

        return [
            max(count / total, 1e-6)
            for count in counts
        ]

    expected_distribution = proportions(expected)
    actual_distribution = proportions(actual)

    psi = sum(
        (actual_share - expected_share)
        * math.log(actual_share / expected_share)
        for expected_share, actual_share
        in zip(expected_distribution, actual_distribution)
    )

    return psi


def demonstrate_drift_monitoring() -> None:
    print("\nDATA DRIFT MONITORING")
    print("-" * 80)

    baseline = [
        random.gauss(50, 10)
        for _ in range(1000)
    ]

    current = [
        random.gauss(58, 12)
        for _ in range(1000)
    ]

    psi = population_stability_index(baseline, current)

    print(f"Illustrative PSI: {psi:.4f}")

    print(
        "\nDrift can indicate changes in customers, channels, products, "
        "processes, data pipelines, or measurement systems. Drift detection "
        "does not by itself prove that model performance has deteriorated."
    )


# ============================================================================
# 29. DATA LEAKAGE
# ============================================================================

def demonstrate_data_leakage() -> None:
    """
    Explain leakage through an executable example.

    The target variable must not influence a feature that would be unavailable
    at prediction time.
    """

    print("\nDATA LEAKAGE")
    print("-" * 80)

    print(
        "Correct feature examples:"
    )
    print(
        "  - orders before the prediction date"
    )
    print(
        "  - days since last purchase at prediction time"
    )
    print(
        "  - satisfaction survey available before prediction"
    )

    print(
        "\nPotential leakage:"
    )
    print(
        "  - cancellation reason recorded after churn"
    )
    print(
        "  - refund status generated after the outcome"
    )
    print(
        "  - post-churn support interaction"
    )

    print(
        "\nLeakage can produce excellent offline model performance while "
        "making the model unusable in real operations."
    )


# ============================================================================
# 30. CAUSALITY VS CORRELATION
# ============================================================================

def demonstrate_causality_distinction() -> None:
    print("\nCORRELATION VS CAUSATION")
    print("-" * 80)

    examples = [
        (
            "Customers receiving discounts may spend more.",
            "The discount may cause more spending, but high-value customers "
            "may also be more likely to receive discounts."
        ),
        (
            "Customers with more support tickets may churn more.",
            "Poor service could increase churn, but dissatisfied customers "
            "may also generate more support interactions."
        ),
        (
            "Mobile users may have higher retention.",
            "Channel may correlate with retention because mobile users differ "
            "in age, engagement, geography, or customer value."
        ),
    ]

    for observation, explanation in examples:
        print(f"\nObservation: {observation}")
        print(f"Why causality is uncertain: {explanation}")

    print(
        "\nRandomized controlled experiments, natural experiments, causal "
        "inference methods, and carefully designed observational studies can "
        "provide stronger evidence about causality."
    )


# ============================================================================
# 31. DATA SAMPLING
# ============================================================================

def demonstrate_sampling() -> None:
    print("\nSAMPLING")
    print("-" * 80)

    population = list(range(1, 10001))
    random.seed(123)

    simple_random_sample = random.sample(population, 100)

    print(f"Population size: {len(population)}")
    print(f"Simple random sample size: {len(simple_random_sample)}")

    print(
        "\nSampling can reduce data-collection cost, but the sample must "
        "represent the target population for conclusions to generalize."
    )

    print(
        "\nImportant sampling risks:"
    )

    risks = [
        "Selection bias",
        "Non-response bias",
        "Coverage bias",
        "Survivorship bias",
        "Convenience sampling",
        "Time-window bias",
    ]

    for risk in risks:
        print(f"  - {risk}")


# ============================================================================
# 32. BUSINESS RULES AND EDGE CASES
# ============================================================================

def demonstrate_edge_cases() -> None:
    print("\nEDGE CASES")
    print("-" * 80)

    edge_cases = {
        "Zero orders":
            "Revenue per order cannot be calculated by ordinary division. "
            "The implementation must define an explicit behavior.",

        "Zero revenue":
            "A customer may exist without revenue during a defined period.",

        "Duplicate customers":
            "Duplicate identifiers can inflate customer counts and revenue.",

        "Extreme outliers":
            "A few unusually large customers can distort means and model "
            "parameters.",

        "Changing KPI definitions":
            "Historical comparisons become unreliable when metric definitions "
            "change without restatement.",

        "Small samples":
            "Observed rates can be unstable and uncertainty can be large.",

        "Missing data":
            "Missingness can itself contain business information and may not "
            "be random.",

        "Changing business process":
            "A model trained under one process may become invalid after a "
            "major operational change.",
    }

    for case, explanation in edge_cases.items():
        print(f"\n{case}:")
        print(f"  {explanation}")


# ============================================================================
# 33. OUTLIER DETECTION
# ============================================================================

def iqr_outlier_bounds(values: Sequence[float]) -> Tuple[float, float]:
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1

    return (
        q1 - 1.5 * iqr,
        q3 + 1.5 * iqr,
    )


def demonstrate_outliers(customers: Sequence[Customer]) -> None:
    print("\nOUTLIER ANALYSIS")
    print("-" * 80)

    revenue = [customer.revenue for customer in customers]

    lower, upper = iqr_outlier_bounds(revenue)

    outliers = [
        customer
        for customer in customers
        if customer.revenue < lower or customer.revenue > upper
    ]

    print(f"Revenue lower bound: {lower:.2f}")
    print(f"Revenue upper bound: {upper:.2f}")
    print(f"Potential revenue outliers: {len(outliers)}")

    print(
        "\nAn outlier is not automatically an error. A high-value customer "
        "may be a legitimate and strategically important observation."
    )


# ============================================================================
# 34. PERFORMANCE CONSIDERATIONS
# ============================================================================

def demonstrate_performance_principles() -> None:
    print("\nPERFORMANCE CONSIDERATIONS")
    print("-" * 80)

    principles = [
        (
            "Avoid repeated scans",
            "Compute reusable aggregates once instead of repeatedly scanning "
            "the entire dataset."
        ),
        (
            "Prefer appropriate data structures",
            "Sets provide efficient membership testing and dictionaries provide "
            "efficient key-based lookup."
        ),
        (
            "Push computation toward data systems",
            "Large-scale analytical workloads are often more efficient when "
            "filtering and aggregation occur close to the database."
        ),
        (
            "Separate development from production",
            "Exploratory code may prioritize flexibility while production code "
            "must prioritize reliability, observability, and maintainability."
        ),
        (
            "Control model complexity",
            "A more complex model can increase computation, maintenance, and "
            "explainability costs without producing useful business value."
        ),
    ]

    for name, explanation in principles:
        print(f"\n{name}")
        print(f"  {explanation}")


# ============================================================================
# 35. SECURITY, PRIVACY, AND GOVERNANCE
# ============================================================================

def demonstrate_security_and_governance() -> None:
    print("\nSECURITY, PRIVACY, AND GOVERNANCE")
    print("-" * 80)

    principles = [
        "Collect only data necessary for the stated business purpose.",
        "Restrict access according to business need and authorization.",
        "Protect sensitive data during storage and transmission.",
        "Avoid exposing personal identifiers in analytical outputs unnecessarily.",
        "Maintain audit trails for important analytical and decision processes.",
        "Document metric definitions and model assumptions.",
        "Control access to production datasets and credentials.",
        "Validate data sources and prevent unauthorized data manipulation.",
        "Assess fairness and unintended consequences where decisions affect people.",
        "Establish retention and deletion policies appropriate to the data.",
    ]

    for principle in principles:
        print(f"  - {principle}")

    print(
        "\nSecurity is part of the analytics lifecycle rather than a separate "
        "activity performed only after analysis is complete."
    )


# ============================================================================
# 36. ETHICAL ANALYTICS
# ============================================================================

def demonstrate_ethical_analytics() -> None:
    print("\nETHICAL ANALYTICS")
    print("-" * 80)

    dimensions = {
        "Purpose limitation":
            "Use information for a legitimate and clearly defined purpose.",

        "Fairness":
            "Check whether analytical decisions produce unjustified disparities.",

        "Transparency":
            "Make important assumptions and decision rules understandable.",

        "Human oversight":
            "High-impact automated decisions may require review and escalation.",

        "Data quality":
            "Poor data can create harmful decisions even when the algorithm is "
            "mathematically correct.",

        "Proportionality":
            "The analytical intervention should be appropriate to the business "
            "objective and potential impact.",
    }

    for name, explanation in dimensions.items():
        print(f"\n{name}")
        print(f"  {explanation}")


# ============================================================================
# 37. REPRODUCIBILITY
# ============================================================================

def demonstrate_reproducibility() -> None:
    print("\nREPRODUCIBILITY")
    print("-" * 80)

    print(
        "A reproducible analytics workflow records:"
    )

    requirements = [
        "Data source and extraction date",
        "Data transformation logic",
        "Metric definitions",
        "Model version",
        "Feature definitions",
        "Parameter values",
        "Random seeds where randomness is used",
        "Evaluation methodology",
        "Business assumptions",
        "Decision criteria",
    ]

    for requirement in requirements:
        print(f"  - {requirement}")

    print(
        "\nReproducibility allows another analyst to understand how an "
        "analytical result was produced and whether it can be independently "
        "validated."
    )


# ============================================================================
# 38. TESTING ANALYTICAL LOGIC
# ============================================================================

def assert_almost_equal(
    actual: float,
    expected: float,
    tolerance: float = 1e-9,
) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"Expected {expected}, received {actual}"
        )


def test_metric_functions() -> None:
    """
    Lightweight tests for critical analytical calculations.
    """

    print("\nANALYTICAL TESTS")
    print("-" * 80)

    assert_almost_equal(mean([1, 2, 3]), 2.0)
    assert_almost_equal(median([1, 2, 3]), 2.0)
    assert_almost_equal(median([1, 2, 3, 4]), 2.5)

    assert_almost_equal(
        pearson_correlation([1, 2, 3], [1, 2, 3]),
        1.0,
    )

    assert_almost_equal(
        pearson_correlation([1, 2, 3], [3, 2, 1]),
        -1.0,
    )

    scenario = RetentionScenario(
        "Test",
        100,
        0.10,
        200,
        2,
    )

    assert_almost_equal(
        scenario.expected_incremental_revenue(),
        2000.0,
    )

    print("All analytical unit tests passed.")


# ============================================================================
# 39. DATA EXPORT
# ============================================================================

def export_customers_to_csv(
    customers: Sequence[Customer],
    filename: str = "business_analytics_customers.csv",
) -> None:
    """
    Export synthetic data using Python's standard csv library.

    In a production environment, file locations, permissions, encoding,
    retention, and access controls must be managed appropriately.
    """

    fieldnames = [
        "customer_id",
        "age",
        "region",
        "channel",
        "orders",
        "revenue",
        "discount_rate",
        "support_tickets",
        "days_since_purchase",
        "satisfaction_score",
        "churned",
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for customer in customers:
            writer.writerow(
                {
                    "customer_id": customer.customer_id,
                    "age": customer.age,
                    "region": customer.region,
                    "channel": customer.channel,
                    "orders": customer.orders,
                    "revenue": customer.revenue,
                    "discount_rate": customer.discount_rate,
                    "support_tickets": customer.support_tickets,
                    "days_since_purchase": customer.days_since_purchase,
                    "satisfaction_score": customer.satisfaction_score,
                    "churned": customer.churned,
                }
            )

    print(f"\nCSV export created: {filename}")


# ============================================================================
# 40. END-TO-END BUSINESS ANALYTICS PIPELINE
# ============================================================================

def run_end_to_end_case_study() -> None:
    """
    Execute the full lifecycle in business order.

    This function represents how the individual analytical activities connect.
    """

    print("\n" + "=" * 80)
    print("END-TO-END BUSINESS ANALYTICS CASE STUDY")
    print("=" * 80)

    # Stage 1: Define the business problem.
    problem = define_business_problem()

    # Stage 2: Identify stakeholders.
    create_stakeholder_map()

    # Stage 3: Frame analytical questions.
    create_analytical_questions()

    # Stage 4: Define metrics.
    create_metric_dictionary()

    # Stage 5: Acquire data.
    customers = generate_customers(
        number_of_customers=300,
        seed=42,
    )

    print(f"\nSynthetic records acquired: {len(customers)}")

    # Stage 6: Validate data.
    demonstrate_data_quality(customers)

    # Stage 7: Understand data structure.
    print_data_dictionary()

    # Stage 8: Transform data.
    features = engineer_features(customers)

    print(
        f"\nFeature engineering completed for {len(features)} customers."
    )

    # Stage 9: Descriptive analytics.
    descriptive_metrics = descriptive_analysis(customers)

    # Stage 10: Exploratory analysis.
    demonstrate_distributions(customers)
    demonstrate_outliers(customers)

    # Stage 11: Segmentation.
    segments = analyze_segments(customers)

    # Stage 12: Diagnostic analytics.
    diagnostic_analysis(customers)
    correlation_analysis(customers)

    # Stage 13: Predictive analytics.
    model = train_logistic_regression(customers)
    print("\nPredictive model trained.")
    print(
        "Model features:",
        ", ".join(model.feature_names),
    )

    evaluate_model(model, customers)

    # Stage 14: Operational prioritization.
    show_high_priority_customers(customers)

    # Stage 15: Economic analysis.
    demonstrate_clv()
    run_scenario_analysis()

    # Stage 16: Prescriptive decision support.
    optimize_offer_allocation(
        customers,
        budget=500,
    )

    # Stage 17: Experimentation.
    demonstrate_ab_test()

    # Stage 18: Insight generation.
    generate_insights(
        customers,
        segments,
    )

    # Stage 19: Recommendation design.
    create_recommendations()

    # Stage 20: Decision-making.
    decision_matrix()

    # Stage 21: Implementation.
    create_implementation_plan()

    # Stage 22: Monitoring.
    observed_metrics = {
        "retention_rate": descriptive_metrics["retention_rate"],
        "churn_rate": descriptive_metrics["churn_rate"],
    }

    monitoring_definitions = [
        MonitoringMetric(
            "retention_rate",
            target=0.70,
            alert_threshold=0.60,
            direction="higher",
        ),
        MonitoringMetric(
            "churn_rate",
            target=0.30,
            alert_threshold=0.40,
            direction="lower",
        ),
    ]

    monitor_kpis(
        observed_metrics,
        monitoring_definitions,
    )

    # Stage 23: Governance and continuous improvement.
    demonstrate_drift_monitoring()
    demonstrate_data_leakage()
    demonstrate_causality_distinction()
    demonstrate_reproducibility()

    print(
        f"\nLifecycle completed for business problem: "
        f"{problem.problem_statement}"
    )


# ============================================================================
# 41. COMPARISON OF ANALYTICS TYPES
# ============================================================================

def compare_analytics_types() -> None:
    print("\nANALYTICS TYPES COMPARISON")
    print("-" * 80)

    comparison = [
        (
            "Descriptive",
            "What happened?",
            "Reports, dashboards, summaries",
            "Historical/current state",
        ),
        (
            "Diagnostic",
            "Why did it happen?",
            "Drill-downs, segmentation, relationships",
            "Drivers and explanations",
        ),
        (
            "Predictive",
            "What is likely to happen?",
            "Forecasts, classification, probability",
            "Future outcomes",
        ),
        (
            "Prescriptive",
            "What should we do?",
            "Optimization, simulation, decision rules",
            "Actions and trade-offs",
        ),
    ]

    print(
        f"{'Type':15} "
        f"{'Question':28} "
        f"{'Methods':38} "
        f"{'Output'}"
    )

    for row in comparison:
        print(
            f"{row[0]:15} "
            f"{row[1]:28} "
            f"{row[2]:38} "
            f"{row[3]}"
        )


# ============================================================================
# 42. ANALYTICS MATURITY
# ============================================================================

def explain_analytics_maturity() -> None:
    print("\nANALYTICS MATURITY")
    print("-" * 80)

    maturity = [
        (
            "Reporting",
            "Reliable historical information is produced."
        ),
        (
            "Descriptive analytics",
            "Patterns and performance are systematically measured."
        ),
        (
            "Diagnostic analytics",
            "Drivers and relationships are investigated."
        ),
        (
            "Predictive analytics",
            "Future outcomes are estimated."
        ),
        (
            "Prescriptive analytics",
            "Actions are evaluated using constraints and expected outcomes."
        ),
        (
            "Decision intelligence",
            "Analytics becomes integrated into repeatable decision processes."
        ),
    ]

    for stage, description in maturity:
        print(f"\n{stage}")
        print(f"  {description}")


# ============================================================================
# 43. COMMON MISTAKES
# ============================================================================

def demonstrate_common_mistakes() -> None:
    print("\nCOMMON BUSINESS ANALYTICS MISTAKES")
    print("-" * 80)

    mistakes = [
        (
            "Starting with the dataset instead of the decision",
            "This can produce interesting analysis that does not answer an "
            "important business question."
        ),
        (
            "Using vague objectives",
            "Terms such as 'improve performance' need measurable definitions."
        ),
        (
            "Confusing correlation with causation",
            "Association does not prove that an intervention will change an outcome."
        ),
        (
            "Optimizing a proxy instead of the business objective",
            "A model can improve a metric while damaging profit or customer experience."
        ),
        (
            "Ignoring implementation constraints",
            "A theoretically optimal action may be impossible to execute."
        ),
        (
            "Using averages alone",
            "Aggregates can hide important customer, product, regional, or channel differences."
        ),
        (
            "Ignoring uncertainty",
            "Point estimates without uncertainty can encourage overconfident decisions."
        ),
        (
            "Data leakage",
            "Features unavailable at decision time can make models appear much better than they are."
        ),
        (
            "Metric definition drift",
            "Changing calculation rules can make trends misleading."
        ),
        (
            "No post-decision measurement",
            "Without monitoring, organizations cannot determine whether a decision worked."
        ),
    ]

    for mistake, consequence in mistakes:
        print(f"\n{mistake}")
        print(f"  {consequence}")


# ============================================================================
# 44. ADVANCED DECISION CONCEPTS
# ============================================================================

def demonstrate_advanced_decision_concepts() -> None:
    print("\nADVANCED DECISION CONCEPTS")
    print("-" * 80)

    concepts = [
        (
            "Counterfactual",
            "The outcome that would have occurred under an alternative action."
        ),
        (
            "Incrementality",
            "The portion of an outcome caused by an intervention rather than "
            "the portion merely associated with it."
        ),
        (
            "Opportunity cost",
            "The value of the best alternative action that is not selected."
        ),
        (
            "Expected value",
            "A probability-weighted estimate of possible outcomes."
        ),
        (
            "Sensitivity analysis",
            "Testing how conclusions change when assumptions change."
        ),
        (
            "Scenario analysis",
            "Evaluating multiple plausible future situations or strategies."
        ),
        (
            "Optimization",
            "Selecting the best feasible option under defined objectives and constraints."
        ),
        (
            "Robustness",
            "The degree to which a decision remains reasonable under uncertainty "
            "or changing assumptions."
        ),
    ]

    for concept, definition in concepts:
        print(f"\n{concept}")
        print(f"  {definition}")


# ============================================================================
# 45. SENSITIVITY ANALYSIS
# ============================================================================

def sensitivity_analysis() -> None:
    print("\nSENSITIVITY ANALYSIS")
    print("-" * 80)

    retention_rates = [0.02, 0.04, 0.06, 0.08]
    customer_value = 300
    customers = 1000
    margin = 0.35
    intervention_cost = 5

    print(
        f"{'Retention Lift':15} "
        f"{'Revenue':15} "
        f"{'Profit':15}"
    )

    for retention_lift in retention_rates:
        revenue = customers * retention_lift * customer_value
        profit = revenue * margin - customers * intervention_cost

        print(
            f"{retention_lift:15.2%} "
            f"{revenue:15,.2f} "
            f"{profit:15,.2f}"
        )

    print(
        "\nSensitivity analysis identifies assumptions that can change the "
        "decision and therefore deserve stronger validation."
    )


# ============================================================================
# 46. DATA LINEAGE
# ============================================================================

def explain_data_lineage() -> None:
    print("\nDATA LINEAGE")
    print("-" * 80)

    lineage = [
        "Source system",
        "Raw extraction",
        "Validation",
        "Cleaning",
        "Transformation",
        "Analytical dataset",
        "Metric calculation",
        "Model or analysis",
        "Insight",
        "Decision",
        "Operational action",
        "Outcome measurement",
    ]

    print(" -> ".join(lineage))

    print(
        "\nData lineage helps identify where a result originated, what "
        "transformations occurred, and which upstream changes could affect it."
    )


# ============================================================================
# 47. PRODUCTION ANALYTICS CHECKLIST
# ============================================================================

def production_checklist() -> None:
    print("\nPRODUCTION ANALYTICS CHECKLIST")
    print("-" * 80)

    checklist = [
        "Business objective approved",
        "Decision owner identified",
        "Metric definitions documented",
        "Data sources validated",
        "Data quality checks automated",
        "Data lineage documented",
        "Access controls implemented",
        "Privacy requirements reviewed",
        "Feature leakage assessed",
        "Model or analytical methodology validated",
        "Evaluation dataset separated from training data",
        "Business impact measured",
        "Operational constraints confirmed",
        "Monitoring implemented",
        "Alert thresholds defined",
        "Rollback or escalation procedure defined",
        "Results reproducible",
        "Post-implementation review scheduled",
    ]

    for item in checklist:
        print(f"[ ] {item}")


# ============================================================================
# 48. MAIN PROGRAM
# ============================================================================

def main() -> None:
    """
    Run the educational curriculum.

    Each section can also be copied into a separate analytical project after
    the learner understands the complete lifecycle.
    """

    print("=" * 80)
    print("BUSINESS ANALYTICS LIFECYCLE")
    print("Problem Definition to Insight and Decision-Making")
    print("=" * 80)

    explain_foundations()
    explain_lifecycle()
    compare_analytics_types()
    explain_analytics_maturity()

    customers = generate_customers(
        number_of_customers=300,
        seed=42,
    )

    print("\nINITIAL DATASET")
    print("-" * 80)
    print(f"Records: {len(customers)}")

    demonstrate_data_quality(customers)
    print_data_dictionary()

    features = engineer_features(customers)

    print("\nENGINEERED FEATURES")
    print("-" * 80)

    for feature in features[:5]:
        print(
            f"Customer {feature.customer_id}: "
            f"Revenue={feature.revenue:.2f}, "
            f"Orders={feature.orders}, "
            f"Recency={feature.recency}, "
            f"Engagement={feature.engagement_score:.2f}, "
            f"Risk={feature.risk_score:.2f}"
        )

    descriptive_analysis(customers)
    demonstrate_distributions(customers)

    segments = analyze_segments(customers)

    diagnostic_analysis(customers)
    correlation_analysis(customers)

    demonstrate_outliers(customers)
    demonstrate_edge_cases()

    model = train_logistic_regression(customers)

    print("\nLOGISTIC REGRESSION MODEL")
    print("-" * 80)

    print(f"Intercept: {model.intercept:.4f}")

    for name, weight in zip(model.feature_names, model.weights):
        print(f"{name:25}: {weight:.4f}")

    evaluate_model(model, customers)

    show_high_priority_customers(customers)
    demonstrate_clv()
    run_scenario_analysis()
    optimize_offer_allocation(customers, budget=500)

    demonstrate_ab_test()

    generate_insights(
        customers,
        segments,
    )

    create_recommendations()
    decision_matrix()
    create_implementation_plan()

    monitor_kpis(
        {
            "retention_rate": mean(
                [1 - customer.churned for customer in customers]
            ),
            "churn_rate": mean(
                [customer.churned for customer in customers]
            ),
        },
        [
            MonitoringMetric(
                "retention_rate",
                0.70,
                0.60,
                "higher",
            ),
            MonitoringMetric(
                "churn_rate",
                0.30,
                0.40,
                "lower",
            ),
        ],
    )

    demonstrate_drift_monitoring()
    demonstrate_data_leakage()
    demonstrate_causality_distinction()
    demonstrate_sampling()
    demonstrate_performance_principles()
    demonstrate_security_and_governance()
    demonstrate_ethical_analytics()
    demonstrate_reproducibility()
    demonstrate_common_mistakes()
    demonstrate_advanced_decision_concepts()
    sensitivity_analysis()
    explain_data_lineage()
    production_checklist()

    test_metric_functions()

    # Uncomment the following line when a physical CSV export is desired.
    # export_customers_to_csv(customers)

    print("\n" + "=" * 80)
    print("END-TO-END LIFECYCLE DEMONSTRATION")
    print("=" * 80)

    run_end_to_end_case_study()


if __name__ == "__main__":
    main()
