"""
INTRODUCTION TO BUSINESS ANALYTICS
==================================

Topic:
Business analytics concepts, objectives, applications

Purpose:
This beginner-friendly Python program explains business analytics through
a combination of theory, examples, calculations, simulated business data,
and practical analysis.

The script is intentionally detailed so that a learner can run it section by
section and understand not only WHAT business analytics is, but also WHY it
is used and HOW it supports business decisions.

Requirements:
    Python 3.x

Optional libraries:
    pandas
    numpy
    matplotlib

Install optional libraries with:
    pip install pandas numpy matplotlib

The core concepts are demonstrated using Python's standard library where
possible. Optional libraries are used for realistic business-analysis
examples and visualizations.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import List, Dict, Any
import math


# =============================================================================
# 1. INTRODUCTION
# =============================================================================

def introduction():
    print("=" * 80)
    print("INTRODUCTION TO BUSINESS ANALYTICS")
    print("=" * 80)

    print("""
Business Analytics (BA) is the systematic use of data, statistics,
quantitative methods, technology, and business knowledge to understand
business performance and support better decisions.

In simple language:

    BUSINESS ANALYTICS = DATA + ANALYSIS + BUSINESS CONTEXT + DECISION

A business generates data every day:

    - Sales transactions
    - Customer purchases
    - Website visits
    - Advertising campaigns
    - Employee information
    - Inventory movements
    - Financial transactions
    - Customer complaints
    - Product reviews
    - Supply-chain events

Business analytics converts this raw information into useful insights.

Example:

Raw data:
    January sales = ₹10 lakh
    February sales = ₹12 lakh
    March sales = ₹9 lakh

Basic observation:
    Sales increased in February but declined in March.

Business question:
    Why did March sales decline?

Analytics may investigate:
    - Region
    - Product
    - Customer segment
    - Price
    - Discounts
    - Marketing campaigns
    - Competitors
    - Seasonality
    - Stock availability

Decision:
    Increase inventory for high-demand products, modify promotions,
    improve regional marketing, or change pricing.

The important idea is that analytics is NOT simply making charts.
Analytics exists to improve business decisions.
""")


# =============================================================================
# 2. WHAT IS DATA?
# =============================================================================

def explain_data():
    print("\n" + "=" * 80)
    print("2. UNDERSTANDING DATA")
    print("=" * 80)

    print("""
Data is a collection of observations, measurements, records, or facts.

Examples:

    Customer age          -> 29
    Product category      -> Electronics
    Order value           -> ₹5,499
    Customer rating       -> 4.5
    Purchase date         -> 2026-09-01
    Region                -> North India

Business data can be broadly classified as:

1. STRUCTURED DATA
   Data organized in rows and columns.

   Example:
       Customer_ID | Age | City | Revenue

2. SEMI-STRUCTURED DATA
   Data with some organizational structure but not a rigid table.

   Examples:
       JSON
       XML
       API responses

3. UNSTRUCTURED DATA
   Data without a conventional tabular structure.

   Examples:
       Images
       Videos
       Audio
       Emails
       Documents
       Social-media text

Analytics can be performed on all these forms of data, although the
techniques and tools may differ.
""")


# =============================================================================
# 3. DATA -> INFORMATION -> INSIGHT -> DECISION
# =============================================================================

def data_to_decision():
    print("\n" + "=" * 80)
    print("3. DATA -> INFORMATION -> INSIGHT -> DECISION")
    print("=" * 80)

    print("""
A useful way to understand business analytics is through this chain:

    DATA
      ↓
    INFORMATION
      ↓
    INSIGHT
      ↓
    DECISION
      ↓
    BUSINESS ACTION
      ↓
    BUSINESS OUTCOME

Example:

DATA:
    1,000 transactions

INFORMATION:
    Product A generated ₹8 lakh revenue.

INSIGHT:
    Product A contributes 42% of total revenue but has declining
    repeat purchases.

DECISION:
    Investigate customer retention and improve the product experience.

ACTION:
    Launch a retention campaign and analyze customer feedback.

OUTCOME:
    Measure whether repeat purchases increase.

This is why business analytics is more than data collection.
It connects evidence to action.
""")


# =============================================================================
# 4. CORE BUSINESS ANALYTICS CONCEPTS
# =============================================================================

def core_concepts():
    print("\n" + "=" * 80)
    print("4. CORE BUSINESS ANALYTICS CONCEPTS")
    print("=" * 80)

    concepts = {
        "Metric": "A measurable value used to evaluate performance.",
        "KPI": "A key metric directly connected to an important business objective.",
        "Dimension": "A category used to analyze a metric, such as region or product.",
        "Trend": "The general direction of a metric over time.",
        "Segmentation": "Dividing customers/data into meaningful groups.",
        "Benchmark": "A reference point used to compare performance.",
        "Correlation": "A statistical relationship between variables.",
        "Forecast": "An estimate of future outcomes based on available information.",
        "Optimization": "Finding a better decision under defined constraints.",
        "Insight": "A meaningful interpretation that can influence a decision.",
    }

    for name, meaning in concepts.items():
        print(f"\n{name.upper()}")
        print(f"  {meaning}")


# =============================================================================
# 5. TYPES OF BUSINESS ANALYTICS
# =============================================================================

def types_of_analytics():
    print("\n" + "=" * 80)
    print("5. FOUR MAJOR TYPES OF BUSINESS ANALYTICS")
    print("=" * 80)

    types = [
        (
            "Descriptive Analytics",
            "What happened?",
            "Sales dashboard showing monthly revenue."
        ),
        (
            "Diagnostic Analytics",
            "Why did it happen?",
            "Finding that revenue dropped because inventory was unavailable."
        ),
        (
            "Predictive Analytics",
            "What is likely to happen?",
            "Forecasting next month's sales."
        ),
        (
            "Prescriptive Analytics",
            "What should we do?",
            "Recommending the best discount or inventory allocation."
        ),
    ]

    for category, question, example in types:
        print(f"\n{category}")
        print(f"  Key question: {question}")
        print(f"  Example:      {example}")

    print("""
Think of them as a progression:

    Descriptive  -> Past
    Diagnostic   -> Explanation
    Predictive   -> Future
    Prescriptive -> Action

A mature analytics organization often uses all four.
""")


# =============================================================================
# 6. BUSINESS ANALYTICS OBJECTIVES
# =============================================================================

def objectives():
    print("\n" + "=" * 80)
    print("6. OBJECTIVES OF BUSINESS ANALYTICS")
    print("=" * 80)

    objectives_list = [
        "Improve decision-making",
        "Increase revenue",
        "Reduce costs",
        "Understand customers",
        "Improve operational efficiency",
        "Manage risk",
        "Optimize pricing",
        "Improve marketing effectiveness",
        "Forecast demand",
        "Improve employee productivity",
        "Optimize supply chains",
        "Identify new business opportunities",
    ]

    for number, objective in enumerate(objectives_list, start=1):
        print(f"{number:02d}. {objective}")

    print("""
The ultimate objective is not 'more data'.

The objective is:

    BETTER INFORMATION
          +
    BETTER DECISIONS
          =
    BETTER BUSINESS OUTCOMES
""")


# =============================================================================
# 7. BUSINESS QUESTIONS
# =============================================================================

def business_questions():
    print("\n" + "=" * 80)
    print("7. BUSINESS QUESTIONS ANALYTICS CAN ANSWER")
    print("=" * 80)

    questions = {
        "Sales": [
            "Which products generate the most revenue?",
            "Which regions are growing fastest?",
            "Why did sales decline?",
        ],
        "Marketing": [
            "Which campaign generates the highest ROI?",
            "Which customer segment responds best?",
            "What is the cost of acquiring a customer?",
        ],
        "Finance": [
            "What is the profit margin?",
            "Which costs are increasing?",
            "What is the expected cash flow?",
        ],
        "Operations": [
            "Where are process bottlenecks?",
            "How much inventory is required?",
            "Which suppliers perform best?",
        ],
        "Human Resources": [
            "What is employee turnover?",
            "Which departments have high attrition?",
            "What factors are associated with employee performance?",
        ],
    }

    for function, qs in questions.items():
        print(f"\n{function.upper()}")
        for q in qs:
            print(f"  - {q}")


# =============================================================================
# 8. SIMULATED BUSINESS DATA
# =============================================================================

@dataclass
class SalesRecord:
    month: str
    region: str
    product: str
    units: int
    revenue: float
    cost: float
    customers: int


def create_sales_data() -> List[SalesRecord]:
    return [
        SalesRecord("Jan", "North", "Laptop", 40, 240000, 190000, 35),
        SalesRecord("Jan", "South", "Laptop", 35, 210000, 168000, 31),
        SalesRecord("Jan", "North", "Phone", 90, 270000, 216000, 78),
        SalesRecord("Jan", "South", "Phone", 80, 240000, 192000, 71),
        SalesRecord("Feb", "North", "Laptop", 48, 288000, 226000, 41),
        SalesRecord("Feb", "South", "Laptop", 42, 252000, 197000, 38),
        SalesRecord("Feb", "North", "Phone", 105, 315000, 249000, 90),
        SalesRecord("Feb", "South", "Phone", 95, 285000, 225000, 84),
        SalesRecord("Mar", "North", "Laptop", 44, 264000, 208000, 39),
        SalesRecord("Mar", "South", "Laptop", 39, 234000, 184000, 35),
        SalesRecord("Mar", "North", "Phone", 115, 345000, 272000, 98),
        SalesRecord("Mar", "South", "Phone", 100, 300000, 237000, 88),
    ]


# =============================================================================
# 9. BASIC DESCRIPTIVE ANALYTICS
# =============================================================================

def descriptive_analysis(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("9. DESCRIPTIVE ANALYTICS: WHAT HAPPENED?")
    print("=" * 80)

    total_revenue = sum(row.revenue for row in data)
    total_cost = sum(row.cost for row in data)
    total_units = sum(row.units for row in data)
    total_customers = sum(row.customers for row in data)
    profit = total_revenue - total_cost
    margin = profit / total_revenue * 100

    print(f"Total units sold:       {total_units:,}")
    print(f"Total revenue:          ₹{total_revenue:,.2f}")
    print(f"Total cost:             ₹{total_cost:,.2f}")
    print(f"Gross profit:           ₹{profit:,.2f}")
    print(f"Profit margin:          {margin:.2f}%")
    print(f"Customer records:       {total_customers:,}")

    monthly = {}

    for row in data:
        monthly.setdefault(row.month, 0)
        monthly[row.month] += row.revenue

    print("\nMonthly revenue:")
    for month, revenue in monthly.items():
        print(f"  {month}: ₹{revenue:,.2f}")


# =============================================================================
# 10. KPI CALCULATIONS
# =============================================================================

def calculate_kpis(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("10. KEY PERFORMANCE INDICATORS (KPIs)")
    print("=" * 80)

    revenue = sum(r.revenue for r in data)
    units = sum(r.units for r in data)
    customers = sum(r.customers for r in data)
    cost = sum(r.cost for r in data)
    profit = revenue - cost

    average_order_value = revenue / customers if customers else 0
    revenue_per_unit = revenue / units if units else 0
    profit_margin = profit / revenue * 100 if revenue else 0

    kpis = {
        "Revenue": f"₹{revenue:,.2f}",
        "Units Sold": f"{units:,}",
        "Gross Profit": f"₹{profit:,.2f}",
        "Profit Margin": f"{profit_margin:.2f}%",
        "Revenue per Customer Record": f"₹{average_order_value:,.2f}",
        "Revenue per Unit": f"₹{revenue_per_unit:,.2f}",
    }

    for name, value in kpis.items():
        print(f"{name:35} {value}")


# =============================================================================
# 11. SEGMENTATION
# =============================================================================

def segmentation_analysis(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("11. SEGMENTATION ANALYSIS")
    print("=" * 80)

    region_revenue: Dict[str, float] = {}
    product_revenue: Dict[str, float] = {}

    for row in data:
        region_revenue[row.region] = region_revenue.get(row.region, 0) + row.revenue
        product_revenue[row.product] = product_revenue.get(row.product, 0) + row.revenue

    print("\nRevenue by region:")
    for region, revenue in sorted(region_revenue.items(), key=lambda x: x[1], reverse=True):
        print(f"  {region:10} ₹{revenue:,.2f}")

    print("\nRevenue by product:")
    for product, revenue in sorted(product_revenue.items(), key=lambda x: x[1], reverse=True):
        print(f"  {product:10} ₹{revenue:,.2f}")

    print("""
Segmentation helps answer:

    WHO?
    WHERE?
    WHAT?
    WHEN?

For example:
    WHO    -> customer segment
    WHERE  -> geography
    WHAT   -> product
    WHEN   -> month/quarter

This makes analysis more actionable than looking only at total revenue.
""")


# =============================================================================
# 12. GROWTH ANALYSIS
# =============================================================================

def growth_analysis(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("12. GROWTH ANALYSIS")
    print("=" * 80)

    monthly = {}

    for row in data:
        monthly[row.month] = monthly.get(row.month, 0) + row.revenue

    months = list(monthly.keys())

    print("Month-over-month growth:")

    for i in range(1, len(months)):
        previous = monthly[months[i - 1]]
        current = monthly[months[i]]

        growth = ((current - previous) / previous) * 100 if previous else 0

        print(
            f"  {months[i - 1]} -> {months[i]}: "
            f"{growth:.2f}%"
        )


# =============================================================================
# 13. PROFITABILITY ANALYSIS
# =============================================================================

def profitability_analysis(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("13. PROFITABILITY ANALYSIS")
    print("=" * 80)

    product_stats: Dict[str, Dict[str, float]] = {}

    for row in data:
        if row.product not in product_stats:
            product_stats[row.product] = {"revenue": 0, "cost": 0}

        product_stats[row.product]["revenue"] += row.revenue
        product_stats[row.product]["cost"] += row.cost

    for product, values in product_stats.items():
        revenue = values["revenue"]
        cost = values["cost"]
        profit = revenue - cost
        margin = profit / revenue * 100

        print(f"\nProduct: {product}")
        print(f"  Revenue:       ₹{revenue:,.2f}")
        print(f"  Cost:          ₹{cost:,.2f}")
        print(f"  Profit:        ₹{profit:,.2f}")
        print(f"  Profit margin: {margin:.2f}%")

    print("""
Important lesson:

A product with high revenue is not automatically the most attractive
product.

Management should consider:

    Revenue
    Profit
    Margin
    Growth
    Customer retention
    Strategic importance
    Operational complexity
""")


# =============================================================================
# 14. DIAGNOSTIC ANALYTICS
# =============================================================================

def diagnostic_example():
    print("\n" + "=" * 80)
    print("14. DIAGNOSTIC ANALYTICS: WHY DID IT HAPPEN?")
    print("=" * 80)

    print("""
Suppose a company observes:

    Revenue ↓ 10%

A descriptive dashboard identifies the problem.

Diagnostic analytics investigates possible causes.

Possible dimensions:

    1. Product
    2. Geography
    3. Customer segment
    4. Price
    5. Discount
    6. Marketing
    7. Inventory
    8. Competitor activity
    9. Seasonality
    10. Operational disruption

Example reasoning:

    Total revenue fell
          ↓
    North region was stable
          ↓
    South region declined
          ↓
    Phone sales declined
          ↓
    Phone inventory was unavailable
          ↓
    Lost sales caused the revenue decline

This is a diagnostic analytics workflow.
""")


# =============================================================================
# 15. PREDICTIVE ANALYTICS
# =============================================================================

def predictive_example(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("15. PREDICTIVE ANALYTICS: WHAT MAY HAPPEN?")
    print("=" * 80)

    monthly = {}

    for row in data:
        monthly[row.month] = monthly.get(row.month, 0) + row.revenue

    values = list(monthly.values())

    print("Historical monthly revenue:")
    for month, revenue in monthly.items():
        print(f"  {month}: ₹{revenue:,.2f}")

    simple_average = mean(values)

    print(f"\nSimple average monthly revenue: ₹{simple_average:,.2f}")

    print("""
A simple average is NOT a sophisticated forecasting model.

Real predictive analytics may use:

    - Time-series forecasting
    - Regression
    - Decision trees
    - Random forests
    - Gradient boosting
    - Neural networks
    - Machine learning
    - External variables

Examples:

    Predict next month's sales.
    Predict customer churn.
    Predict loan default.
    Predict demand.
    Predict equipment failure.
    Predict employee attrition.

Prediction always contains uncertainty.
A responsible analyst communicates confidence, assumptions, and limitations.
""")


# =============================================================================
# 16. PRESCRIPTIVE ANALYTICS
# =============================================================================

def prescriptive_example():
    print("\n" + "=" * 80)
    print("16. PRESCRIPTIVE ANALYTICS: WHAT SHOULD WE DO?")
    print("=" * 80)

    print("""
Prescriptive analytics goes beyond prediction.

Example:

Prediction:
    Product demand next month = 10,000 units.

Prescriptive question:
    How many units should we order?

The answer may depend on:

    Expected demand
    Storage capacity
    Supplier lead time
    Purchase cost
    Stockout cost
    Holding cost
    Cash availability

The objective is to identify an action that produces the best expected
business result while respecting constraints.
""")


# =============================================================================
# 17. BUSINESS ANALYTICS APPLICATIONS
# =============================================================================

def applications():
    print("\n" + "=" * 80)
    print("17. APPLICATIONS OF BUSINESS ANALYTICS")
    print("=" * 80)

    applications_data = {
        "Marketing": [
            "Campaign ROI",
            "Customer segmentation",
            "Attribution",
            "Lead scoring",
            "Customer acquisition cost",
        ],
        "Sales": [
            "Sales forecasting",
            "Territory analysis",
            "Pipeline analysis",
            "Cross-selling",
            "Upselling",
        ],
        "Finance": [
            "Budget analysis",
            "Profitability analysis",
            "Fraud detection",
            "Cash-flow forecasting",
            "Financial risk analysis",
        ],
        "Operations": [
            "Process optimization",
            "Capacity planning",
            "Quality monitoring",
            "Inventory optimization",
            "Performance measurement",
        ],
        "Supply Chain": [
            "Demand forecasting",
            "Supplier performance",
            "Route optimization",
            "Inventory planning",
            "Logistics analytics",
        ],
        "Human Resources": [
            "Attrition analysis",
            "Workforce planning",
            "Recruitment analytics",
            "Performance analytics",
            "Compensation analysis",
        ],
        "Customer Service": [
            "Complaint analysis",
            "Response-time analysis",
            "Customer satisfaction",
            "Churn prediction",
            "Service quality monitoring",
        ],
    }

    for function, uses in applications_data.items():
        print(f"\n{function.upper()}")
        for use in uses:
            print(f"  - {use}")


# =============================================================================
# 18. BUSINESS ANALYTICS VS DATA ANALYTICS
# =============================================================================

def analytics_comparison():
    print("\n" + "=" * 80)
    print("18. BUSINESS ANALYTICS VS DATA ANALYTICS")
    print("=" * 80)

    print("""
DATA ANALYTICS
    Focus:
        Finding patterns, trends, relationships, and insights in data.

BUSINESS ANALYTICS
    Focus:
        Applying analytical insights specifically to business problems
        and decisions.

Example:

Data analytics:
    "Customers aged 25-34 have the highest average purchase frequency."

Business analytics:
    "The company should increase targeted offers for the 25-34 segment
     because this group has high purchase frequency and strong potential
     for repeat revenue."

Business analytics therefore requires both analytical capability and
business understanding.
""")


# =============================================================================
# 19. BUSINESS ANALYTICS VS BUSINESS INTELLIGENCE
# =============================================================================

def bi_comparison():
    print("\n" + "=" * 80)
    print("19. BUSINESS ANALYTICS VS BUSINESS INTELLIGENCE")
    print("=" * 80)

    print("""
Business Intelligence (BI) commonly focuses on:

    - Reporting
    - Dashboards
    - Monitoring KPIs
    - Historical analysis
    - Data visualization

Business Analytics commonly extends toward:

    - Statistical analysis
    - Root-cause analysis
    - Forecasting
    - Predictive modeling
    - Optimization
    - Decision support

In practice, the boundaries can overlap.

A modern analytics professional may work with both BI and advanced
analytics.
""")


# =============================================================================
# 20. ANALYTICS WORKFLOW
# =============================================================================

def analytics_workflow():
    print("\n" + "=" * 80)
    print("20. END-TO-END BUSINESS ANALYTICS WORKFLOW")
    print("=" * 80)

    workflow = [
        "1. Define the business problem",
        "2. Define the decision that must be made",
        "3. Identify required data",
        "4. Collect the data",
        "5. Clean and validate the data",
        "6. Explore the data",
        "7. Analyze patterns and relationships",
        "8. Build models when appropriate",
        "9. Interpret results in business context",
        "10. Communicate insights",
        "11. Recommend actions",
        "12. Implement the decision",
        "13. Measure the outcome",
        "14. Improve the process continuously",
    ]

    for step in workflow:
        print(step)

    print("""
The most important step is often Step 1.

If the business question is poorly defined, even perfect analysis may
produce an irrelevant answer.

GOOD ANALYTICS begins with a GOOD BUSINESS QUESTION.
""")


# =============================================================================
# 21. COMMON BUSINESS METRICS
# =============================================================================

def common_metrics():
    print("\n" + "=" * 80)
    print("21. COMMON BUSINESS METRICS")
    print("=" * 80)

    metrics = {
        "Revenue": "Money generated from sales.",
        "Gross Profit": "Revenue minus direct costs.",
        "Profit Margin": "Profit divided by revenue.",
        "Average Order Value (AOV)": "Revenue divided by number of orders.",
        "Customer Acquisition Cost (CAC)": "Marketing/sales acquisition cost per new customer.",
        "Customer Lifetime Value (CLV/LTV)": "Estimated value generated by a customer over the relationship.",
        "Conversion Rate": "Percentage of users/leads completing a desired action.",
        "Retention Rate": "Percentage of customers retained over a period.",
        "Churn Rate": "Percentage of customers lost over a period.",
        "ROI": "Return generated relative to investment.",
    }

    for metric, definition in metrics.items():
        print(f"\n{metric}")
        print(f"  {definition}")


# =============================================================================
# 22. SIMPLE ROI CALCULATION
# =============================================================================

def roi_example():
    print("\n" + "=" * 80)
    print("22. ROI CALCULATION")
    print("=" * 80)

    investment = 100000
    return_generated = 150000

    profit = return_generated - investment
    roi = (profit / investment) * 100

    print(f"Investment:       ₹{investment:,.2f}")
    print(f"Return generated: ₹{return_generated:,.2f}")
    print(f"Profit:           ₹{profit:,.2f}")
    print(f"ROI:              {roi:.2f}%")

    print("""
Formula:

    ROI = (Gain - Investment) / Investment × 100

ROI allows managers to compare the economic attractiveness of different
initiatives, although ROI should not be the only decision criterion.
""")


# =============================================================================
# 23. CORRELATION CONCEPT
# =============================================================================

def correlation_example():
    print("\n" + "=" * 80)
    print("23. CORRELATION")
    print("=" * 80)

    print("""
Correlation measures the degree to which two variables move together.

Example:

    Advertising Spend ↑
    Sales ↑

A positive correlation may exist.

However:

    CORRELATION DOES NOT AUTOMATICALLY MEAN CAUSATION.

Sales may have increased because of:

    - Advertising
    - Seasonal demand
    - Price changes
    - Competitor problems
    - Product launch
    - Economic conditions

An analyst must therefore investigate context and, where possible,
use experimental or causal methods.
""")


# =============================================================================
# 24. DATA QUALITY
# =============================================================================

def data_quality():
    print("\n" + "=" * 80)
    print("24. DATA QUALITY")
    print("=" * 80)

    dimensions = [
        ("Accuracy", "Is the data correct?"),
        ("Completeness", "Are important values missing?"),
        ("Consistency", "Are values represented consistently?"),
        ("Timeliness", "Is the data current enough?"),
        ("Validity", "Does the data follow required rules?"),
        ("Uniqueness", "Are duplicate records present?"),
    ]

    for dimension, question in dimensions:
        print(f"{dimension:15} -> {question}")

    print("""
Poor-quality data can produce poor decisions.

A useful principle:

    GARBAGE IN -> GARBAGE OUT

Therefore, data cleaning and validation are essential parts of business
analytics.
""")


# =============================================================================
# 25. ETHICS AND RESPONSIBLE ANALYTICS
# =============================================================================

def ethics():
    print("\n" + "=" * 80)
    print("25. ETHICS AND RESPONSIBLE BUSINESS ANALYTICS")
    print("=" * 80)

    principles = [
        "Protect personal and confidential information.",
        "Use data only for legitimate and appropriate purposes.",
        "Check models for unfair bias.",
        "Explain important analytical decisions when possible.",
        "Do not deliberately manipulate metrics.",
        "Distinguish facts from assumptions.",
        "Communicate uncertainty honestly.",
        "Respect applicable laws, policies, and data-governance requirements.",
    ]

    for p in principles:
        print(f"- {p}")

    print("""
Analytics can influence:

    Hiring
    Lending
    Pricing
    Insurance
    Healthcare
    Marketing
    Public services

Because analytical decisions can affect people, responsible analytics is
an important professional responsibility.
""")


# =============================================================================
# 26. BUSINESS ANALYTICS TOOLS
# =============================================================================

def tools():
    print("\n" + "=" * 80)
    print("26. COMMON BUSINESS ANALYTICS TOOLS")
    print("=" * 80)

    tools_list = {
        "Excel": "Spreadsheet analysis, formulas, pivot tables, modeling.",
        "SQL": "Querying and transforming data stored in databases.",
        "Python": "Data analysis, automation, statistics, machine learning.",
        "R": "Statistics, visualization, and analytical research.",
        "Power BI": "Business intelligence dashboards and reporting.",
        "Tableau": "Interactive data visualization and BI.",
        "Cloud Platforms": "Scalable storage, processing, analytics, and ML.",
        "Statistical Software": "Advanced statistical modeling and analysis.",
    }

    for tool, purpose in tools_list.items():
        print(f"{tool:20} -> {purpose}")


# =============================================================================
# 27. MINI CASE STUDY
# =============================================================================

def mini_case_study():
    print("\n" + "=" * 80)
    print("27. MINI BUSINESS ANALYTICS CASE STUDY")
    print("=" * 80)

    print("""
SCENARIO
--------
An online retailer reports that revenue increased by 8%, but management
is concerned because profit increased by only 1%.

BUSINESS QUESTION
-----------------
Why is profit growing much more slowly than revenue?

ANALYTICAL APPROACH
-------------------
1. Compare revenue growth.
2. Compare cost growth.
3. Analyze product-level margins.
4. Analyze discount levels.
5. Analyze customer acquisition costs.
6. Analyze shipping and fulfillment costs.
7. Segment by region and customer type.

POSSIBLE FINDING
----------------
Revenue increased because sales volume increased, but aggressive discounts
and higher logistics costs reduced profitability.

BUSINESS DECISION
-----------------
Management could:

    - Review discount strategy.
    - Improve product mix.
    - Renegotiate logistics contracts.
    - Increase prices selectively.
    - Target higher-margin customers.

MEASUREMENT
-----------
After implementation, management should monitor:

    Revenue
    Gross profit
    Margin
    Average order value
    Discount rate
    Logistics cost
    Customer retention

This final measurement closes the analytics loop.
""")


# =============================================================================
# 28. BUSINESS ANALYTICS MINDSET
# =============================================================================

def analytics_mindset():
    print("\n" + "=" * 80)
    print("28. BUSINESS ANALYTICS MINDSET")
    print("=" * 80)

    questions = [
        "What decision are we trying to improve?",
        "What evidence do we have?",
        "What data is missing?",
        "Is the data reliable?",
        "What does the data actually say?",
        "What does it NOT say?",
        "What assumptions are we making?",
        "What alternative explanations exist?",
        "What action should management take?",
        "How will we measure whether the action worked?",
    ]

    for q in questions:
        print(f"- {q}")


# =============================================================================
# 29. QUICK KNOWLEDGE CHECK
# =============================================================================

def knowledge_check():
    print("\n" + "=" * 80)
    print("29. KNOWLEDGE CHECK")
    print("=" * 80)

    questions = [
        ("What happened?", "Descriptive analytics"),
        ("Why did it happen?", "Diagnostic analytics"),
        ("What may happen?", "Predictive analytics"),
        ("What should we do?", "Prescriptive analytics"),
    ]

    print("\nMatch the business question to the analytics type:\n")

    for question, answer in questions:
        print(f"{question:25} -> {answer}")


# =============================================================================
# 30. FINAL SUMMARY
# =============================================================================

def final_summary():
    print("\n" + "=" * 80)
    print("30. FINAL SUMMARY")
    print("=" * 80)

    print("""
Business Analytics is the disciplined use of data and analytical methods
to improve business decisions.

The foundation can be remembered as:

    BUSINESS PROBLEM
          ↓
        DATA
          ↓
      ANALYSIS
          ↓
       INSIGHT
          ↓
       DECISION
          ↓
        ACTION
          ↓
       OUTCOME
          ↓
      MEASUREMENT

The four major forms of analytics are:

    1. Descriptive  -> What happened?
    2. Diagnostic   -> Why did it happen?
    3. Predictive   -> What may happen?
    4. Prescriptive -> What should we do?

Business analytics can be applied to:

    Marketing
    Sales
    Finance
    Operations
    Supply Chain
    Human Resources
    Customer Service
    Risk
    Strategy
    Product Management

A strong business analyst combines:

    Business understanding
    Data literacy
    Statistics
    Analytical thinking
    Technology
    Communication
    Problem solving
    Ethical judgment

The ultimate goal is not to create complicated models.

The ultimate goal is to make better decisions using reliable evidence.
""")


# =============================================================================
# 31. OPTIONAL PANDAS DEMONSTRATION
# =============================================================================

def optional_pandas_demo(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("31. OPTIONAL PANDAS DEMONSTRATION")
    print("=" * 80)

    try:
        import pandas as pd
    except ImportError:
        print("""
Pandas is not installed.

Install it with:

    pip install pandas

Then run this program again.
""")
        return

    df = pd.DataFrame([vars(record) for record in data])

    print("\nDataFrame:")
    print(df)

    print("\nRevenue by product:")
    print(
        df.groupby("product")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nRevenue by region:")
    print(
        df.groupby("region")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nAverage revenue:")
    print(df["revenue"].mean())


# =============================================================================
# 32. OPTIONAL VISUALIZATION
# =============================================================================

def optional_visualization(data: List[SalesRecord]):
    print("\n" + "=" * 80)
    print("32. OPTIONAL BUSINESS VISUALIZATION")
    print("=" * 80)

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("""
Matplotlib is not installed.

Install it with:

    pip install matplotlib
""")
        return

    monthly = {}

    for row in data:
        monthly[row.month] = monthly.get(row.month, 0) + row.revenue

    plt.figure(figsize=(9, 5))
    plt.plot(list(monthly.keys()), list(monthly.values()), marker="o")
    plt.title("Monthly Revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


# =============================================================================
# MAIN PROGRAM
# =============================================================================

def main():
    introduction()
    explain_data()
    data_to_decision()
    core_concepts()
    types_of_analytics()
    objectives()
    business_questions()

    data = create_sales_data()

    descriptive_analysis(data)
    calculate_kpis(data)
    segmentation_analysis(data)
    growth_analysis(data)
    profitability_analysis(data)

    diagnostic_example()
    predictive_example(data)
    prescriptive_example()
    applications()

    analytics_comparison()
    bi_comparison()
    analytics_workflow()
    common_metrics()
    roi_example()
    correlation_example()
    data_quality()
    ethics()
    tools()
    mini_case_study()
    analytics_mindset()
    knowledge_check()
    final_summary()

    # Optional practical demonstrations
    optional_pandas_demo(data)

    # Uncomment the next line if you want a chart.
    # optional_visualization(data)


if __name__ == "__main__":
    main()

