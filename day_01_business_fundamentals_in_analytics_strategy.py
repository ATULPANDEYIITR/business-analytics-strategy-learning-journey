# ============================================================
# DAY 00: BUSINESS FUNDAMENTALS IN ANALYTICS AND STRATEGY
# ============================================================

print("DAY 01 - BUSINESS FUNDAMENTALS IN ANALYTICS AND STRATEGY")


# ============================================================
# 1. WHAT IS A BUSINESS?
# ============================================================

print("\n1. WHAT IS A BUSINESS?")

business_name = "EdTech Company"
business_goal = "Create value for customers and generate sustainable revenue"

print("Business:", business_name)
print("Goal:", business_goal)


# ============================================================
# 2. BUSINESS OBJECTIVES
# ============================================================

print("\n2. BUSINESS OBJECTIVES")

objectives = [
    "Generate Revenue",
    "Serve Customers",
    "Control Costs",
    "Grow the Business",
    "Improve Profitability",
    "Create Long-Term Value"
]

for objective in objectives:
    print("-", objective)


# ============================================================
# 3. REVENUE, COST AND PROFIT
# ============================================================

print("\n3. REVENUE, COST AND PROFIT")

revenue = 100000
cost = 70000

profit = revenue - cost

print("Revenue: ₹", revenue)
print("Cost: ₹", cost)
print("Profit: ₹", profit)


# ============================================================
# 4. BUSINESS METRICS
# ============================================================

print("\n4. BUSINESS METRICS")

customers = 500
orders = 750
revenue = 150000

average_order_value = revenue / orders

print("Customers:", customers)
print("Orders:", orders)
print("Revenue: ₹", revenue)
print("Average Order Value: ₹", average_order_value)


# ============================================================
# 5. DATA AND BUSINESS ANALYTICS
# ============================================================

print("\n5. DATA AND BUSINESS ANALYTICS")

sales = [100, 150, 120, 180, 200]

total_sales = sum(sales)
average_sales = total_sales / len(sales)

print("Sales:", sales)
print("Total Sales:", total_sales)
print("Average Sales:", average_sales)

print("\nBusiness Analytics uses data to understand")
print("performance, identify patterns, and support decisions.")


# ============================================================
# 6. BUSINESS DECISION MAKING
# ============================================================

print("\n6. BUSINESS DECISION MAKING")

current_sales = 120000
target_sales = 150000

if current_sales >= target_sales:
    print("Sales target achieved.")
else:
    gap = target_sales - current_sales
    print("Sales target not achieved.")
    print("Sales gap: ₹", gap)


# ============================================================
# 7. STRATEGY
# ============================================================

print("\n7. BUSINESS STRATEGY")

strategy = {
    "Target Market": "Students and Professionals",
    "Value Proposition": "Affordable skill-based learning",
    "Growth Strategy": "Digital customer acquisition",
    "Competitive Focus": "Quality and accessibility"
}

for key, value in strategy.items():
    print(key + ":", value)


# ============================================================
# 8. SWOT ANALYSIS
# ============================================================

print("\n8. SWOT ANALYSIS")

swot = {
    "Strengths": ["Strong content", "Skilled team"],
    "Weaknesses": ["Limited brand awareness"],
    "Opportunities": ["Growing online learning market"],
    "Threats": ["High competition"]
}

for category, points in swot.items():
    print("\n" + category + ":")
    
    for point in points:
        print("-", point)


# ============================================================
# 9. KEY PERFORMANCE INDICATORS
# ============================================================

print("\n9. KEY PERFORMANCE INDICATORS")

kpis = {
    "Revenue": 150000,
    "Customers": 500,
    "Orders": 750,
    "Customer Retention": 80
}

for kpi, value in kpis.items():
    print(kpi + ":", value)


# ============================================================
# 10. BASIC BUSINESS ANALYSIS
# ============================================================

print("\n10. BASIC BUSINESS ANALYSIS")

previous_revenue = 100000
current_revenue = 125000

growth = ((current_revenue - previous_revenue)
          / previous_revenue) * 100

print("Previous Revenue: ₹", previous_revenue)
print("Current Revenue: ₹", current_revenue)
print("Revenue Growth:", growth, "%")


# ============================================================
# 11. ANALYTICS TO STRATEGY
# ============================================================

print("\n11. ANALYTICS TO STRATEGY")

print("""
Business Data
      ↓
Analysis
      ↓
Insights
      ↓
Business Decision
      ↓
Strategy
      ↓
Action
      ↓
Business Results
""")


# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. What a business is
2. Business objectives
3. Revenue, cost and profit
4. Business metrics
5. Data and business analytics
6. Business decision making
7. Business strategy
8. SWOT analysis
9. KPIs
10. Basic business analysis
11. Relationship between analytics and strategy
""")
