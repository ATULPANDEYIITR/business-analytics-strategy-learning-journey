"""
====================================================================
BUSINESS FUNCTIONS
====================================================================

Topic:
    Finance, Marketing, Sales, Operations, HR and Supply Chain

Purpose:
    This program provides a comprehensive, beginner-to-advanced
    explanation of the major business functions and demonstrates
    how Python can be used by a Data Analyst to understand, analyze,
    measure and connect these functions.

The six major business functions covered are:

    1. Finance
    2. Marketing
    3. Sales
    4. Operations
    5. Human Resources (HR)
    6. Supply Chain

The program progresses from:
    Business basics
        ->
    Functional understanding
        ->
    KPIs and metrics
        ->
    Business calculations
        ->
    Data analysis
        ->
    Cross-functional analysis
        ->
    Advanced business analytics
        ->
    Strategic decision-making

Requirements:
    Python 3.x

Optional libraries:
    pandas
    numpy

The core examples below use Python's standard library so that the
program can be understood without installing external packages.
====================================================================
"""


# ==================================================================
# SECTION 1: WHAT IS A BUSINESS FUNCTION?
# ==================================================================

"""
A business function is a major area of organizational activity that
performs a specific set of responsibilities.

A company does not operate as one single activity.

Different teams perform different functions.

For example:

    Finance
        -> manages money

    Marketing
        -> creates awareness and demand

    Sales
        -> converts demand into revenue

    Operations
        -> delivers products or services efficiently

    HR
        -> manages people and organizational capability

    Supply Chain
        -> manages movement of materials, products and information

Although these functions have different responsibilities, they are
highly interconnected.

Example:

Marketing launches a campaign
        ->
More customers become interested
        ->
Sales receives more leads
        ->
Sales converts leads into orders
        ->
Operations must fulfill those orders
        ->
Supply Chain must provide required materials
        ->
HR may need additional employees
        ->
Finance records revenue, costs and profit


This means a Data Analyst should not analyze departments in complete
isolation.

A good analyst understands both:

    Functional analysis
        = understanding one business function

and

    Cross-functional analysis
        = understanding how multiple functions affect each other.
"""


# ==================================================================
# SECTION 2: BUSINESS FUNCTION VS DEPARTMENT
# ==================================================================

"""
A business function describes WHAT type of work is performed.

A department describes WHERE organizational responsibility for that
work is assigned.

For example:

    Function:
        Finance

    Department:
        Finance Department

The organizational structure can vary.

A startup might have:

    Founder
        |
        +-- Finance
        +-- Marketing
        +-- Sales
        +-- Operations

A large enterprise might have:

    CFO
        |
        +-- Financial Planning
        +-- Accounting
        +-- Treasury
        +-- Tax
        +-- Audit


Therefore, business functions are conceptual areas of business
activity rather than rigid organizational structures.
"""


# ==================================================================
# SECTION 3: THE SIX MAJOR BUSINESS FUNCTIONS
# ==================================================================

business_functions = {
    "Finance": "Manages money, financial resources, profitability, risk and financial reporting.",
    "Marketing": "Creates awareness, generates demand, understands customers and builds the brand.",
    "Sales": "Converts prospects into customers and generates revenue.",
    "Operations": "Transforms resources into products or services and manages execution.",
    "HR": "Manages employees, talent, workforce planning, performance and organizational capability.",
    "Supply Chain": "Manages sourcing, procurement, inventory, logistics and movement of goods."
}

for function, responsibility in business_functions.items():
    print(function, ":", responsibility)


# ==================================================================
# SECTION 4: FINANCE
# ==================================================================

"""
Finance is concerned with the management of money and financial
resources.

At the basic level, Finance answers questions such as:

    How much money did the company make?
    How much did the company spend?
    How profitable is the company?
    How much cash does the company have?
    What assets does the company own?
    What liabilities does it owe?
    Can the company afford an investment?
    What financial risks exist?

Major areas within Finance include:

    Accounting
    Financial Planning and Analysis (FP&A)
    Treasury
    Tax
    Audit
    Corporate Finance
    Risk Management
"""


# ------------------------------------------------------------------
# Finance: Basic financial concepts
# ------------------------------------------------------------------

revenue = 1_000_000
cost_of_goods_sold = 600_000
operating_expenses = 250_000
interest_expense = 20_000
tax = 30_000

gross_profit = revenue - cost_of_goods_sold
operating_profit = gross_profit - operating_expenses
profit_before_tax = operating_profit - interest_expense
net_profit = profit_before_tax - tax

print("\nFINANCE")
print("Revenue:", revenue)
print("Gross Profit:", gross_profit)
print("Operating Profit:", operating_profit)
print("Net Profit:", net_profit)


# ------------------------------------------------------------------
# Finance KPIs
# ------------------------------------------------------------------

gross_margin = gross_profit / revenue
operating_margin = operating_profit / revenue
net_profit_margin = net_profit / revenue

print("Gross Margin:", gross_margin)
print("Operating Margin:", operating_margin)
print("Net Profit Margin:", net_profit_margin)


"""
Important Finance KPIs:

Revenue
    Total money generated from business activities.

Gross Profit
    Revenue - Cost of Goods Sold

Gross Margin
    Gross Profit / Revenue

Operating Profit
    Gross Profit - Operating Expenses

Operating Margin
    Operating Profit / Revenue

Net Profit
    Revenue - all applicable expenses

Net Profit Margin
    Net Profit / Revenue

EBITDA
    Earnings Before Interest, Taxes, Depreciation and Amortization

Cash Flow
    Movement of cash into and out of the business.

Accounts Receivable
    Money customers owe the company.

Accounts Payable
    Money the company owes suppliers.
"""


# ------------------------------------------------------------------
# Finance: Break-even analysis
# ------------------------------------------------------------------

"""
Break-even analysis identifies the sales volume at which:

    Total Revenue = Total Cost

Formula:

    Break-even units =
        Fixed Costs / (Selling Price per Unit - Variable Cost per Unit)
"""

fixed_cost = 500_000
selling_price = 2_000
variable_cost = 1_200

break_even_units = fixed_cost / (selling_price - variable_cost)

print("\nBreak-even Units:", break_even_units)


# ------------------------------------------------------------------
# Finance: ROI
# ------------------------------------------------------------------

"""
ROI = Return on Investment

Formula:

    ROI = (Gain from Investment - Cost of Investment)
          / Cost of Investment
"""

investment = 100_000
gain = 130_000

roi = (gain - investment) / investment

print("ROI:", roi)


# ------------------------------------------------------------------
# Finance: NPV
# ------------------------------------------------------------------

"""
Net Present Value (NPV) accounts for the time value of money.

A rupee received today is generally more valuable than a rupee
received several years later because today's money can be invested.

Simplified formula:

    NPV =
        Initial Investment
        + Σ [Future Cash Flow / (1 + Discount Rate)^t]

A positive NPV can indicate that an investment creates economic value.
"""

cash_flows = [-100000, 30000, 40000, 50000, 60000]
discount_rate = 0.10

npv = 0

for year, cash_flow in enumerate(cash_flows):
    npv += cash_flow / ((1 + discount_rate) ** year)

print("NPV:", npv)


# ==================================================================
# SECTION 5: MARKETING
# ==================================================================

"""
Marketing focuses on understanding customers and creating, communicating
and delivering value.

Marketing answers questions such as:

    Who are our customers?
    What do customers need?
    How do customers discover our product?
    Which campaigns work?
    Which channels generate customers?
    How much does it cost to acquire a customer?
    What is the lifetime value of a customer?

Major marketing areas include:

    Market Research
    Brand Management
    Digital Marketing
    Content Marketing
    Performance Marketing
    Product Marketing
    Social Media Marketing
    Email Marketing
    Customer Relationship Management
"""


# ------------------------------------------------------------------
# Marketing funnel
# ------------------------------------------------------------------

"""
A typical marketing funnel:

    Awareness
        ->
    Interest
        ->
    Consideration
        ->
    Conversion
        ->
    Retention
        ->
    Advocacy

A Data Analyst can measure conversion between each stage.
"""

marketing_funnel = {
    "Website Visitors": 100_000,
    "Leads": 10_000,
    "Qualified Leads": 4_000,
    "Opportunities": 1_500,
    "Customers": 500
}

print("\nMARKETING FUNNEL")

previous_value = None

for stage, value in marketing_funnel.items():
    print(stage, ":", value)

    if previous_value is not None:
        conversion_rate = value / previous_value
        print("  Conversion from previous stage:", conversion_rate)

    previous_value = value


# ------------------------------------------------------------------
# Marketing KPIs
# ------------------------------------------------------------------

"""
Important Marketing KPIs:

Impressions
    Number of times an advertisement/content is displayed.

Reach
    Number of unique people exposed to content.

CTR
    Click-Through Rate

    CTR = Clicks / Impressions

Conversion Rate
    Conversions / Visitors or Leads

CPC
    Cost Per Click

CPM
    Cost Per Thousand Impressions

CPL
    Cost Per Lead

CAC
    Customer Acquisition Cost

ROAS
    Return on Advertising Spend

Customer Lifetime Value
    Estimated economic value generated by a customer throughout
    the customer relationship.
"""

impressions = 1_000_000
clicks = 30_000
marketing_cost = 600_000
customers_acquired = 1_200
revenue_from_campaign = 2_400_000

ctr = clicks / impressions
cpc = marketing_cost / clicks
cac = marketing_cost / customers_acquired
roas = revenue_from_campaign / marketing_cost

print("\nMarketing Metrics")
print("CTR:", ctr)
print("CPC:", cpc)
print("CAC:", cac)
print("ROAS:", roas)


# ------------------------------------------------------------------
# Customer Lifetime Value
# ------------------------------------------------------------------

average_purchase_value = 5_000
purchases_per_year = 4
customer_lifetime_years = 5
gross_margin = 0.40

customer_lifetime_value = (
    average_purchase_value
    * purchases_per_year
    * customer_lifetime_years
    * gross_margin
)

print("Estimated Customer Lifetime Value:", customer_lifetime_value)


# ==================================================================
# SECTION 6: SALES
# ==================================================================

"""
Sales converts potential customer demand into actual revenue.

Sales answers:

    How many leads do we have?
    How many leads are qualified?
    How many opportunities exist?
    How many deals are likely to close?
    How much revenue will be generated?
    How long does the sales process take?
    Which salesperson or territory performs best?

Common sales processes:

    Lead
      ->
    Qualification
      ->
    Opportunity
      ->
    Proposal
      ->
    Negotiation
      ->
    Closed Won / Closed Lost
"""


# ------------------------------------------------------------------
# Sales pipeline
# ------------------------------------------------------------------

sales_pipeline = [
    {"stage": "Lead", "count": 1000},
    {"stage": "Qualified", "count": 500},
    {"stage": "Opportunity", "count": 250},
    {"stage": "Proposal", "count": 120},
    {"stage": "Closed Won", "count": 60}
]

print("\nSALES PIPELINE")

for item in sales_pipeline:
    print(item["stage"], ":", item["count"])


# ------------------------------------------------------------------
# Sales conversion rate
# ------------------------------------------------------------------

leads = 1000
closed_won = 60

sales_conversion_rate = closed_won / leads

print("Overall Sales Conversion Rate:", sales_conversion_rate)


# ------------------------------------------------------------------
# Sales revenue
# ------------------------------------------------------------------

deals = [
    {"customer": "Customer A", "value": 100000},
    {"customer": "Customer B", "value": 150000},
    {"customer": "Customer C", "value": 75000},
    {"customer": "Customer D", "value": 200000},
]

total_sales = sum(deal["value"] for deal in deals)

print("Total Sales:", total_sales)


# ------------------------------------------------------------------
# Average Deal Size
# ------------------------------------------------------------------

average_deal_size = total_sales / len(deals)

print("Average Deal Size:", average_deal_size)


# ------------------------------------------------------------------
# Sales forecasting
# ------------------------------------------------------------------

"""
Weighted pipeline forecasting assigns a probability to each opportunity.

Example:

    Opportunity value = ₹1,000,000
    Probability = 60%

Expected revenue:

    ₹1,000,000 × 60%
    = ₹600,000
"""

opportunities = [
    {"value": 1_000_000, "probability": 0.60},
    {"value": 500_000, "probability": 0.80},
    {"value": 750_000, "probability": 0.30},
    {"value": 300_000, "probability": 0.20},
]

expected_sales = sum(
    opportunity["value"] * opportunity["probability"]
    for opportunity in opportunities
)

print("Expected Sales Forecast:", expected_sales)


"""
Advanced Sales Analytics:

    Pipeline velocity
    Win rate
    Sales cycle length
    Quota attainment
    Territory performance
    Rep productivity
    Forecast accuracy
    Deal slippage
    Churn
    Expansion revenue
    Cross-sell
    Upsell
"""


# ==================================================================
# SECTION 7: OPERATIONS
# ==================================================================

"""
Operations is concerned with converting inputs into outputs.

Inputs can include:

    People
    Machines
    Materials
    Capital
    Information
    Technology
    Time

Outputs can include:

    Products
    Services
    Completed transactions
    Customer experiences

Operations focuses heavily on:

    Efficiency
    Productivity
    Quality
    Capacity
    Cost
    Speed
    Reliability
"""


# ------------------------------------------------------------------
# Productivity
# ------------------------------------------------------------------

units_produced = 10_000
labor_hours = 2_000

labor_productivity = units_produced / labor_hours

print("\nOPERATIONS")
print("Labor Productivity:", labor_productivity)


# ------------------------------------------------------------------
# Capacity utilization
# ------------------------------------------------------------------

actual_output = 80_000
maximum_capacity = 100_000

capacity_utilization = actual_output / maximum_capacity

print("Capacity Utilization:", capacity_utilization)


# ------------------------------------------------------------------
# Defect rate
# ------------------------------------------------------------------

total_units = 50_000
defective_units = 500

defect_rate = defective_units / total_units

print("Defect Rate:", defect_rate)


# ------------------------------------------------------------------
# Throughput
# ------------------------------------------------------------------

"""
Throughput represents the rate at which a process produces output.

Example:

    10,000 units / 500 hours
    = 20 units/hour
"""

throughput = units_produced / labor_hours

print("Throughput:", throughput)


# ------------------------------------------------------------------
# Cycle time
# ------------------------------------------------------------------

"""
Cycle Time:

    Time required to complete one unit or process.

Lower cycle time generally means faster process execution,
provided quality and sustainability are maintained.
"""

total_processing_time = 5_000
units_completed = 1_000

cycle_time = total_processing_time / units_completed

print("Average Cycle Time:", cycle_time)


# ------------------------------------------------------------------
# Operations KPIs
# ------------------------------------------------------------------

"""
Important Operations KPIs:

    Capacity Utilization
    Throughput
    Cycle Time
    Lead Time
    Productivity
    Defect Rate
    First Pass Yield
    Downtime
    OEE
    Cost per Unit
    On-Time Delivery
    Service Level
"""


# ==================================================================
# SECTION 8: HUMAN RESOURCES
# ==================================================================

"""
Human Resources manages the people side of the organization.

HR deals with:

    Recruitment
    Hiring
    Onboarding
    Training
    Compensation
    Benefits
    Performance Management
    Employee Engagement
    Retention
    Workforce Planning
    Succession Planning
    Organizational Development
"""


# ------------------------------------------------------------------
# Headcount
# ------------------------------------------------------------------

employees = 500
new_hires = 60
departures = 40

ending_headcount = employees + new_hires - departures

print("\nHUMAN RESOURCES")
print("Ending Headcount:", ending_headcount)


# ------------------------------------------------------------------
# Employee turnover
# ------------------------------------------------------------------

average_headcount = (employees + ending_headcount) / 2

turnover_rate = departures / average_headcount

print("Employee Turnover Rate:", turnover_rate)


# ------------------------------------------------------------------
# Employee retention
# ------------------------------------------------------------------

retained_employees = employees - departures

retention_rate = retained_employees / employees

print("Retention Rate:", retention_rate)


# ------------------------------------------------------------------
# Cost per hire
# ------------------------------------------------------------------

recruitment_cost = 1_200_000
number_of_hires = 60

cost_per_hire = recruitment_cost / number_of_hires

print("Cost per Hire:", cost_per_hire)


# ------------------------------------------------------------------
# Absenteeism
# ------------------------------------------------------------------

available_work_days = 100_000
absence_days = 2_000

absenteeism_rate = absence_days / available_work_days

print("Absenteeism Rate:", absenteeism_rate)


"""
Important HR KPIs:

    Headcount
    Turnover Rate
    Retention Rate
    Cost per Hire
    Time to Hire
    Time to Fill
    Absenteeism Rate
    Employee Engagement
    Training Hours
    Training Cost
    Revenue per Employee
    Profit per Employee
    Internal Promotion Rate

Advanced HR analytics can investigate:

    Why employees leave
    Which departments have high turnover
    Whether compensation affects retention
    Whether managers influence employee engagement
    Whether training improves performance
    Workforce demand forecasting
"""


# ==================================================================
# SECTION 9: SUPPLY CHAIN
# ==================================================================

"""
Supply Chain manages the flow of:

    Raw materials
    Components
    Finished goods
    Information
    Money

from suppliers through the organization to customers.

A simplified supply chain:

Supplier
    ->
Procurement
    ->
Warehouse
    ->
Manufacturing
    ->
Distribution
    ->
Retail / Customer
"""


# ------------------------------------------------------------------
# Inventory
# ------------------------------------------------------------------

beginning_inventory = 10_000
purchases = 30_000
sales_units = 25_000

ending_inventory = beginning_inventory + purchases - sales_units

print("\nSUPPLY CHAIN")
print("Ending Inventory:", ending_inventory)


# ------------------------------------------------------------------
# Inventory turnover
# ------------------------------------------------------------------

average_inventory = (beginning_inventory + ending_inventory) / 2

inventory_turnover = sales_units / average_inventory

print("Inventory Turnover:", inventory_turnover)


# ------------------------------------------------------------------
# Days inventory outstanding
# ------------------------------------------------------------------

days_in_year = 365

days_inventory = days_in_year / inventory_turnover

print("Days of Inventory:", days_inventory)


# ------------------------------------------------------------------
# Stockout rate
# ------------------------------------------------------------------

total_orders = 10_000
stockout_orders = 300

stockout_rate = stockout_orders / total_orders

print("Stockout Rate:", stockout_rate)


# ------------------------------------------------------------------
# Supplier performance
# ------------------------------------------------------------------

orders_received = 1_000
orders_on_time = 920

supplier_on_time_rate = orders_on_time / orders_received

print("Supplier On-Time Rate:", supplier_on_time_rate)


"""
Important Supply Chain KPIs:

    Inventory Turnover
    Days Inventory
    Stockout Rate
    Fill Rate
    Order Cycle Time
    Supplier Lead Time
    Supplier On-Time Delivery
    Forecast Accuracy
    Perfect Order Rate
    Logistics Cost
    Warehousing Cost
    Transportation Cost
"""


# ==================================================================
# SECTION 10: HOW THE SIX FUNCTIONS CONNECT
# ==================================================================

"""
Business functions should not be viewed as independent boxes.

Consider this example:

Marketing increases advertising.

        ↓

Website traffic increases.

        ↓

Leads increase.

        ↓

Sales opportunities increase.

        ↓

Sales increase.

        ↓

Operations receives more orders.

        ↓

Inventory requirements increase.

        ↓

Supply Chain increases procurement.

        ↓

Warehouse workload increases.

        ↓

HR may need additional employees.

        ↓

Costs increase.

        ↓

Finance evaluates whether the additional revenue
creates additional profit.

This is a classic cross-functional business problem.
"""


# ==================================================================
# SECTION 11: CROSS-FUNCTIONAL BUSINESS DATA
# ==================================================================

business_data = [
    {
        "month": "January",
        "marketing_spend": 100000,
        "leads": 1000,
        "sales": 500000,
        "operating_cost": 350000,
        "employees": 100,
        "inventory": 5000
    },
    {
        "month": "February",
        "marketing_spend": 120000,
        "leads": 1300,
        "sales": 620000,
        "operating_cost": 400000,
        "employees": 105,
        "inventory": 5500
    },
    {
        "month": "March",
        "marketing_spend": 150000,
        "leads": 1600,
        "sales": 750000,
        "operating_cost": 480000,
        "employees": 110,
        "inventory": 7000
    }
]

print("\nCROSS-FUNCTIONAL BUSINESS DATA")

for month in business_data:
    print(month)


# ==================================================================
# SECTION 12: DERIVED BUSINESS METRICS
# ==================================================================

for month in business_data:

    month["profit"] = month["sales"] - month["operating_cost"]

    month["marketing_cost_per_lead"] = (
        month["marketing_spend"] / month["leads"]
    )

    month["revenue_per_employee"] = (
        month["sales"] / month["employees"]
    )

    month["profit_margin"] = (
        month["profit"] / month["sales"]
    )


print("\nDERIVED METRICS")

for month in business_data:
    print(
        month["month"],
        "Profit =", month["profit"],
        "CPL =", month["marketing_cost_per_lead"],
        "Revenue/Employee =", month["revenue_per_employee"],
        "Profit Margin =", month["profit_margin"]
    )


# ==================================================================
# SECTION 13: BUSINESS QUESTIONS VS DATA QUESTIONS
# ==================================================================

"""
A Data Analyst should distinguish between a business question and
a data question.

Business question:

    "Why did profit decline?"

Data questions:

    Did revenue decline?
    Did average selling price decline?
    Did sales volume decline?
    Did marketing costs increase?
    Did employee costs increase?
    Did material costs increase?
    Did logistics costs increase?
    Did customer churn increase?

Business analytics converts:

    Business problem
            ->
    Analytical questions
            ->
    Data requirements
            ->
    Analysis
            ->
    Insight
            ->
    Decision
            ->
    Business action
"""


# ==================================================================
# SECTION 14: BUSINESS KPI HIERARCHY
# ==================================================================

"""
A useful hierarchy is:

LEVEL 1: OUTCOME METRICS

    Revenue
    Profit
    Cash Flow
    Market Share
    Customer Lifetime Value

LEVEL 2: DRIVER METRICS

    Customers
    Average Order Value
    Conversion Rate
    Customer Retention
    Cost per Customer

LEVEL 3: PROCESS METRICS

    Lead Response Time
    Cycle Time
    Defect Rate
    Inventory Turnover
    Employee Productivity

LEVEL 4: ACTIVITY METRICS

    Calls Made
    Emails Sent
    Ads Published
    Units Produced
    Interviews Conducted

The deeper the analyst goes, the closer they get to identifying
the actual cause of a business outcome.
"""


# ==================================================================
# SECTION 15: LEADING VS LAGGING INDICATORS
# ==================================================================

"""
Lagging indicators measure outcomes.

Examples:

    Revenue
    Profit
    Churn
    Annual turnover
    Market share

Leading indicators may provide early signals of future outcomes.

Examples:

    Website traffic
    Qualified leads
    Customer complaints
    Employee engagement
    Sales pipeline
    Inventory levels

Example:

    Declining customer satisfaction
            ->
    increasing complaints
            ->
    customer churn
            ->
    revenue decline

Customer satisfaction may therefore act as an earlier warning
than revenue decline.
"""


# ==================================================================
# SECTION 16: CAUSAL THINKING
# ==================================================================

"""
Correlation does not automatically mean causation.

Suppose:

    Marketing Spend increases
    Sales increase

This does not prove:

    Marketing Spend caused all of the Sales increase.

Other factors may include:

    Seasonality
    Pricing
    Competitor behavior
    Product launch
    Economic conditions
    Distribution expansion
    Sales team changes

An analyst should ask:

    What changed?
    When did it change?
    What else changed?
    What would have happened without the change?
    Can we establish a counterfactual?
"""


# ==================================================================
# SECTION 17: SEGMENTATION
# ==================================================================

"""
Business performance should rarely be evaluated only at an aggregate
level.

Instead, analysts segment data.

Common segmentation dimensions:

    Customer
    Geography
    Product
    Channel
    Industry
    Salesperson
    Department
    Employee level
    Supplier
    Time
"""


customers = [
    {"customer": "A", "region": "North", "sales": 100000},
    {"customer": "B", "region": "North", "sales": 150000},
    {"customer": "C", "region": "South", "sales": 200000},
    {"customer": "D", "region": "South", "sales": 120000},
    {"customer": "E", "region": "West", "sales": 80000},
]

regional_sales = {}

for customer in customers:
    region = customer["region"]

    if region not in regional_sales:
        regional_sales[region] = 0

    regional_sales[region] += customer["sales"]

print("\nREGIONAL SALES")

for region, sales in regional_sales.items():
    print(region, sales)


# ==================================================================
# SECTION 18: BUSINESS PERFORMANCE COMPARISON
# ==================================================================

"""
A business analyst frequently compares:

    Actual vs Budget
    Actual vs Forecast
    Current vs Previous Period
    Current Year vs Previous Year
    Product A vs Product B
    Region A vs Region B
    Customer Segment A vs Segment B

Example:
"""

actual_revenue = 1_200_000
budget_revenue = 1_000_000

variance = actual_revenue - budget_revenue
variance_percentage = variance / budget_revenue

print("\nRevenue Variance:", variance)
print("Revenue Variance %:", variance_percentage)


# ==================================================================
# SECTION 19: YEAR-OVER-YEAR GROWTH
# ==================================================================

previous_year_revenue = 10_000_000
current_year_revenue = 12_500_000

yoy_growth = (
    (current_year_revenue - previous_year_revenue)
    / previous_year_revenue
)

print("\nYear-over-Year Growth:", yoy_growth)


# ==================================================================
# SECTION 20: MONTH-OVER-MONTH GROWTH
# ==================================================================

previous_month_sales = 900_000
current_month_sales = 950_000

mom_growth = (
    (current_month_sales - previous_month_sales)
    / previous_month_sales
)

print("Month-over-Month Growth:", mom_growth)


# ==================================================================
# SECTION 21: UNIT ECONOMICS
# ==================================================================

"""
Unit economics evaluates the economics of one unit of business.

For a subscription business:

    Revenue per customer
        -
    Variable cost per customer
        =
    Contribution margin

Important concepts:

    CAC
        Customer Acquisition Cost

    LTV
        Customer Lifetime Value

    Contribution Margin

    Payback Period

A common strategic question:

    Is the customer worth more than it costs to acquire?
"""

cac = 2_000
monthly_revenue_per_customer = 1_000
monthly_variable_cost = 300

monthly_contribution = (
    monthly_revenue_per_customer
    - monthly_variable_cost
)

payback_period = cac / monthly_contribution

print("\nUnit Economics")
print("Monthly Contribution:", monthly_contribution)
print("CAC Payback Period:", payback_period, "months")


# ==================================================================
# SECTION 22: PROCESS ANALYSIS
# ==================================================================

"""
A business process can be represented as:

Input
    ->
Activity
    ->
Output
    ->
Outcome

Example:

Marketing Budget
    ->
Advertising
    ->
Leads
    ->
Customers
    ->
Revenue

Another example:

Raw Materials
    ->
Manufacturing
    ->
Finished Goods
    ->
Shipment
    ->
Customer Delivery
"""


# ==================================================================
# SECTION 23: BOTTLENECK ANALYSIS
# ==================================================================

"""
A bottleneck is the stage that limits the overall capacity of a system.

Example:

Stage A = 100 units/hour
Stage B = 40 units/hour
Stage C = 80 units/hour

The overall process cannot sustainably produce more than
approximately 40 units/hour because Stage B is the bottleneck.
"""

process_capacity = {
    "Stage A": 100,
    "Stage B": 40,
    "Stage C": 80
}

bottleneck = min(
    process_capacity,
    key=process_capacity.get
)

print("\nBottleneck:", bottleneck)
print("Bottleneck Capacity:", process_capacity[bottleneck])


# ==================================================================
# SECTION 24: FORECASTING
# ==================================================================

"""
Business functions depend heavily on forecasts.

Finance forecasts:

    Revenue
    Expenses
    Cash Flow

Marketing forecasts:

    Leads
    Campaign performance
    Customer acquisition

Sales forecasts:

    Pipeline
    Deals
    Revenue

Operations forecasts:

    Capacity
    Demand
    Workforce requirements

HR forecasts:

    Headcount
    Hiring requirements
    Attrition

Supply Chain forecasts:

    Demand
    Inventory
    Procurement
    Logistics

A simple moving average is one basic forecasting technique.
"""

sales_history = [100, 120, 130, 140, 160, 170]

window = 3

moving_average = sum(sales_history[-window:]) / window

print("\nSimple Moving Average Forecast:", moving_average)


# ==================================================================
# SECTION 25: SCENARIO ANALYSIS
# ==================================================================

"""
Scenario analysis evaluates possible future situations.

Example scenarios:

    Base Case
    Best Case
    Worst Case

This helps management understand uncertainty.
"""

scenarios = {
    "Worst Case": {
        "revenue": 8_000_000,
        "cost": 7_000_000
    },
    "Base Case": {
        "revenue": 10_000_000,
        "cost": 7_500_000
    },
    "Best Case": {
        "revenue": 13_000_000,
        "cost": 8_000_000
    }
}

print("\nSCENARIO ANALYSIS")

for scenario, values in scenarios.items():

    profit = values["revenue"] - values["cost"]

    print(
        scenario,
        "Revenue =", values["revenue"],
        "Profit =", profit
    )


# ==================================================================
# SECTION 26: SENSITIVITY ANALYSIS
# ==================================================================

"""
Sensitivity analysis asks:

    "What happens to the outcome if one input changes?"

For example:

    What happens to profit if price changes?
    What happens to profit if costs rise?
    What happens to revenue if conversion falls?
"""

base_price = 1000
units = 10_000
variable_cost_per_unit = 600
fixed_cost = 2_000_000

for price_change in [-0.10, 0, 0.10]:

    price = base_price * (1 + price_change)

    revenue = price * units

    total_cost = (
        variable_cost_per_unit * units
        + fixed_cost
    )

    profit = revenue - total_cost

    print(
        "Price Change:",
        price_change,
        "Profit:",
        profit
    )


# ==================================================================
# SECTION 27: DATA QUALITY IN BUSINESS ANALYTICS
# ==================================================================

"""
Business decisions depend on data quality.

Common data quality problems:

    Missing values
    Duplicate records
    Incorrect dates
    Incorrect units
    Invalid categories
    Incorrect joins
    Inconsistent naming
    Outliers
    Delayed data
    Manual entry errors

Example:

    "UP"
    "U.P."
    "Uttar Pradesh"
    "uttar pradesh"

These may represent the same category but appear as different
values in a dataset.

A Data Analyst must understand that:

    Bad Data
        ->
    Bad Analysis
        ->
    Bad Insight
        ->
    Bad Decision
"""


# ==================================================================
# SECTION 28: BUSINESS ANALYTICS MATURITY
# ==================================================================

"""
Business analytics can be understood through four levels.

LEVEL 1: DESCRIPTIVE ANALYTICS

Question:

    What happened?

Examples:

    Revenue was ₹10 crore.
    Sales declined by 5%.

LEVEL 2: DIAGNOSTIC ANALYTICS

Question:

    Why did it happen?

Examples:

    Sales declined because conversion rate decreased.

LEVEL 3: PREDICTIVE ANALYTICS

Question:

    What is likely to happen?

Examples:

    Next month's sales are forecast at ₹12 crore.

LEVEL 4: PRESCRIPTIVE ANALYTICS

Question:

    What should we do?

Examples:

    Increase inventory by 10% for high-demand products.
"""


# ==================================================================
# SECTION 29: BUSINESS INTELLIGENCE
# ==================================================================

"""
Business Intelligence (BI) converts business data into information
that supports decision-making.

A typical BI pipeline:

Data Sources
    ->
Data Collection
    ->
Data Storage
    ->
Data Transformation
    ->
Data Modeling
    ->
Analytics
    ->
Dashboard
    ->
Decision

Possible data sources:

    CRM
    ERP
    HRIS
    Marketing platforms
    Accounting systems
    E-commerce systems
    Supply chain systems
    Databases
    APIs
    Excel files
"""


# ==================================================================
# SECTION 30: DATA ANALYST'S ROLE ACROSS BUSINESS FUNCTIONS
# ==================================================================

"""
A Data Analyst may work with every business function.

FINANCE ANALYST QUESTIONS:

    Why did expenses increase?
    Which business unit is most profitable?
    Are we above or below budget?

MARKETING ANALYST QUESTIONS:

    Which campaign has the best ROAS?
    Which channel has the lowest CAC?
    Which customer segment converts best?

SALES ANALYST QUESTIONS:

    Which sales representatives exceed quota?
    Where is the pipeline leaking?
    What is the expected revenue?

OPERATIONS ANALYST QUESTIONS:

    Which process is the bottleneck?
    Why is productivity declining?
    What causes defects?

HR ANALYST QUESTIONS:

    Why is employee turnover increasing?
    Which departments have the highest attrition?
    What is the cost of hiring?

SUPPLY CHAIN ANALYST QUESTIONS:

    Which products are frequently out of stock?
    Which supplier performs best?
    How much inventory should we maintain?
"""


# ==================================================================
# SECTION 31: CROSS-FUNCTIONAL ROOT CAUSE ANALYSIS
# ==================================================================

"""
Suppose company profit declined.

A weak analysis:

    "Profit declined by 10%."

A stronger analysis:

    Revenue declined.
    Marketing conversion declined.
    Sales win rate declined.
    Inventory shortages increased.
    Customer complaints increased.

An advanced analysis asks:

    Did inventory shortages cause lost sales?

    Did supplier delays cause inventory shortages?

    Did demand forecasting fail?

    Did marketing generate demand for products that were
    unavailable?

    Did sales incentives encourage orders that operations could
    not fulfill?

This is cross-functional root-cause analysis.
"""


# ==================================================================
# SECTION 32: BALANCED BUSINESS VIEW
# ==================================================================

"""
A strong analyst avoids optimizing one function at the expense
of the whole organization.

Example:

Marketing wants:

    Maximum leads.

Sales wants:

    Maximum qualified opportunities.

Operations wants:

    Stable demand.

Finance wants:

    Maximum profitable growth.

Supply Chain wants:

    Predictable demand and manageable inventory.

HR wants:

    Sustainable workforce requirements.

These objectives can conflict.

Example:

Marketing may generate 100,000 leads.

That sounds positive.

But if:

    Sales cannot handle the leads
    Operations cannot fulfill demand
    Customer service becomes overloaded
    Inventory becomes unavailable
    Costs increase

then the business may not benefit.

Therefore:

    Local optimization
        !=
    Global optimization
"""


# ==================================================================
# SECTION 33: STRATEGIC KPI TREE
# ==================================================================

"""
A KPI tree decomposes a high-level outcome into its drivers.

Example:

                    PROFIT
                       |
            ---------------------
            |                   |
         Revenue              Cost
            |                   |
       -----------        -------------
       |         |        |     |     |
     Price     Volume   Labor Materials Logistics

Another example:

                 REVENUE
                    |
          --------------------
          |                  |
      Customers         Revenue/Customer
          |
     --------------
     |            |
 Acquisition   Retention
"""


# ==================================================================
# SECTION 34: DATA ANALYST THINKING FRAMEWORK
# ==================================================================

"""
A practical framework:

STEP 1
Understand the business objective.

STEP 2
Define the problem.

STEP 3
Identify stakeholders.

STEP 4
Identify the relevant business function.

STEP 5
Define the KPI.

STEP 6
Identify KPI drivers.

STEP 7
Identify required data.

STEP 8
Validate data quality.

STEP 9
Analyze trends.

STEP 10
Segment the results.

STEP 11
Investigate root causes.

STEP 12
Quantify business impact.

STEP 13
Develop recommendations.

STEP 14
Communicate findings.

STEP 15
Track results after implementation.
"""


# ==================================================================
# SECTION 35: STAKEHOLDER THINKING
# ==================================================================

"""
The same data can answer different questions for different
stakeholders.

CEO:

    Is the business growing profitably?

CFO:

    What is driving margin?

CMO:

    Which channels generate profitable customers?

Sales Director:

    Where is the pipeline weakening?

COO:

    Can operations handle expected demand?

HR Director:

    Do we have enough people to support growth?

Supply Chain Director:

    Do we have enough inventory and supplier capacity?

A Data Analyst should therefore understand:

    WHO is asking?
    WHY are they asking?
    WHAT decision will they make?
    WHEN do they need the answer?
"""


# ==================================================================
# SECTION 36: ADVANCED BUSINESS METRICS
# ==================================================================

"""
Advanced analytics may include:

    Customer Lifetime Value
    Customer Acquisition Cost
    Contribution Margin
    Cohort Retention
    Churn Rate
    Net Revenue Retention
    Gross Revenue Retention
    LTV/CAC
    Payback Period
    Working Capital
    Cash Conversion Cycle
    Economic Value Added
    Return on Invested Capital
    Total Cost of Ownership
    Forecast Accuracy
    Service Level
    Capacity Utilization
    Employee Productivity
"""


# ==================================================================
# SECTION 37: CASH CONVERSION CYCLE
# ==================================================================

"""
Cash Conversion Cycle (CCC) measures how long cash is tied up
in the operating cycle.

Simplified:

    CCC =
        Days Inventory Outstanding
        +
        Days Sales Outstanding
        -
        Days Payable Outstanding
"""

days_inventory_outstanding = 60
days_sales_outstanding = 45
days_payable_outstanding = 30

cash_conversion_cycle = (
    days_inventory_outstanding
    + days_sales_outstanding
    - days_payable_outstanding
)

print("\nCash Conversion Cycle:", cash_conversion_cycle, "days")


# ==================================================================
# SECTION 38: LTV TO CAC
# ==================================================================

ltv = 40_000
cac = 10_000

ltv_cac_ratio = ltv / cac

print("LTV/CAC Ratio:", ltv_cac_ratio)


# ==================================================================
# SECTION 39: COHORT THINKING
# ==================================================================

"""
A cohort is a group of customers sharing a common characteristic.

Examples:

    Customers acquired in January
    Customers acquired in Q1
    Customers who purchased Product A
    Customers from a specific region

Cohort analysis is useful for:

    Retention
    Churn
    Revenue
    Customer behavior
    Product performance
"""


cohorts = {
    "January": [100, 80, 65, 55],
    "February": [120, 90, 70, 60],
    "March": [150, 115, 90, 70]
}

print("\nCOHORT RETENTION")

for cohort, values in cohorts.items():

    initial_customers = values[0]

    retention = [
        value / initial_customers
        for value in values
    ]

    print(cohort, retention)


# ==================================================================
# SECTION 40: BUSINESS TRADE-OFFS
# ==================================================================

"""
Business decisions frequently involve trade-offs.

Examples:

    Higher inventory
        ->
    Better product availability
        ->
    Higher inventory carrying cost

Lower inventory
        ->
    Lower carrying cost
        ->
    Higher stockout risk

More employees
        ->
    Higher capacity
        ->
    Higher labor cost

Fewer employees
        ->
    Lower cost
        ->
    Potential productivity/service problems

More marketing
        ->
    More demand
        ->
    Higher acquisition cost

Therefore the analyst must evaluate the entire economic impact.
"""


# ==================================================================
# SECTION 41: DECISION ANALYTICS
# ==================================================================

"""
The ultimate objective of business analytics is not to produce
numbers.

The objective is to improve decisions.

A useful chain is:

    Data
      ->
    Information
      ->
    Insight
      ->
    Decision
      ->
    Action
      ->
    Outcome
      ->
    Measurement
      ->
    Learning

Example:

Data:
    Conversion rate declined from 5% to 3%.

Information:
    Fewer visitors are becoming customers.

Insight:
    Mobile users experienced a significant checkout failure.

Decision:
    Fix the mobile checkout process.

Action:
    Engineering deploys the fix.

Outcome:
    Conversion increases to 4.8%.

Measurement:
    Monitor conversion and revenue.

Learning:
    Technical reliability materially affects customer conversion.
"""


# ==================================================================
# SECTION 42: ADVANCED BUSINESS ANALYST MINDSET
# ==================================================================

"""
At an advanced level, a Data Analyst should think in terms of:

    Business model
    Value creation
    Value capture
    Revenue drivers
    Cost drivers
    Customer behavior
    Process efficiency
    Organizational capability
    Risk
    Constraints
    Trade-offs
    Opportunity cost
    Causality
    Uncertainty
    Decision impact

The analyst should move from:

    "What does the data say?"

to:

    "What does the data mean for the business?"

and ultimately:

    "What decision should the business make based on the evidence?"
"""


# ==================================================================
# SECTION 43: FINAL INTEGRATED BUSINESS EXAMPLE
# ==================================================================

"""
Suppose a company wants to increase profit.

The analyst should not immediately create a revenue dashboard.

Instead:

1. Define the objective.

       Increase sustainable profit.

2. Understand the profit equation.

       Profit = Revenue - Cost

3. Decompose revenue.

       Revenue =
           Customers × Average Revenue per Customer

4. Decompose customers.

       Customers =
           Acquisition × Conversion × Retention

5. Analyze costs.

       Labor
       Marketing
       Materials
       Logistics
       Technology
       Overheads

6. Connect functions.

       Marketing
           ->
       Sales
           ->
       Operations
           ->
       Supply Chain
           ->
       HR
           ->
       Finance

7. Identify constraints.

8. Identify root causes.

9. Estimate potential impact.

10. Recommend actions.

11. Measure post-action results.

This is the difference between simply reporting data and performing
business analysis.
"""


# ==================================================================
# SECTION 44: FINAL SUMMARY
# ==================================================================

print("\n" + "=" * 70)
print("BUSINESS FUNCTIONS - LEARNING COMPLETE")
print("=" * 70)

summary = {
    "Finance": [
        "Revenue",
        "Profit",
        "Margins",
        "ROI",
        "NPV",
        "Budgeting",
        "Cash Flow"
    ],
    "Marketing": [
        "Funnels",
        "CTR",
        "CPC",
        "CAC",
        "ROAS",
        "LTV",
        "Customer Segmentation"
    ],
    "Sales": [
        "Pipeline",
        "Conversion",
        "Win Rate",
        "Average Deal Size",
        "Forecasting",
        "Quota"
    ],
    "Operations": [
        "Productivity",
        "Capacity",
        "Throughput",
        "Cycle Time",
        "Quality",
        "Bottlenecks"
    ],
    "HR": [
        "Headcount",
        "Turnover",
        "Retention",
        "Cost per Hire",
        "Absenteeism",
        "Workforce Planning"
    ],
    "Supply Chain": [
        "Inventory",
        "Stockouts",
        "Supplier Performance",
        "Logistics",
        "Demand Forecasting",
        "Inventory Turnover"
    ]
}

for function, topics in summary.items():
    print(f"\n{function}:")
    for topic in topics:
        print("  -", topic)

print("\nCore analytical principle:")
print("Understand the business before analyzing the data.")

print("\nFinal business analytics flow:")
print(
    "Business Problem -> KPI -> Drivers -> Data -> Analysis -> "
    "Insight -> Decision -> Action -> Outcome"
)
