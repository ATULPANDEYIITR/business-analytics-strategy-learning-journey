"""
Business Models: B2B, B2C, D2C, Marketplace and Subscription Models
====================================================================

This script is designed as an academic learning module. It explains the
structure, economics, strategic logic, operational characteristics, metrics,
advantages, risks, and advanced peculiarities of five major business models:

1. B2B - Business to Business
2. B2C - Business to Consumer
3. D2C - Direct to Consumer
4. Marketplace
5. Subscription

The purpose is not merely to define these models, but to understand how they
create value, generate revenue, acquire customers, manage costs, scale, and
compete.

A business model answers several fundamental questions:

- Who is the customer?
- What value is being delivered?
- How is the value delivered?
- How does the business generate revenue?
- What resources and capabilities are required?
- What are the major costs?
- How does the business achieve profitability?
- How does the model scale?
- What risks and constraints exist?

The same company can operate more than one business model simultaneously.
For example, a company may sell directly to consumers while also selling
products to distributors, enterprises, or through a marketplace.

The examples in this script are illustrative and are intended to demonstrate
business-model logic rather than represent financial advice or company data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ============================================================================
# SECTION 1: FUNDAMENTALS OF A BUSINESS MODEL
# ============================================================================

@dataclass
class BusinessModel:
    """
    Represents the fundamental structure of a business model.

    A business model is broader than a revenue model.

    Revenue model:
        Explains how money enters the business.

    Business model:
        Explains the complete system through which an organization creates,
        delivers, captures, and sustains value.
    """

    name: str
    customer: str
    value_proposition: str
    revenue_sources: List[str]
    distribution_channels: List[str]
    major_costs: List[str]
    key_resources: List[str]
    key_metrics: List[str]
    risks: List[str]

    def describe(self):
        print(f"\n{'=' * 80}")
        print(f"BUSINESS MODEL: {self.name.upper()}")
        print(f"{'=' * 80}")

        print(f"\nCustomer:\n{self.customer}")
        print(f"\nValue Proposition:\n{self.value_proposition}")

        print("\nRevenue Sources:")
        for item in self.revenue_sources:
            print(f"  - {item}")

        print("\nDistribution Channels:")
        for item in self.distribution_channels:
            print(f"  - {item}")

        print("\nMajor Costs:")
        for item in self.major_costs:
            print(f"  - {item}")

        print("\nKey Resources:")
        for item in self.key_resources:
            print(f"  - {item}")

        print("\nKey Metrics:")
        for item in self.key_metrics:
            print(f"  - {item}")

        print("\nMajor Risks:")
        for item in self.risks:
            print(f"  - {item}")


# ============================================================================
# SECTION 2: UNIT ECONOMICS
# ============================================================================

def gross_profit(revenue: float, cost_of_goods_sold: float) -> float:
    """
    Gross Profit = Revenue - Cost of Goods Sold
    """
    return revenue - cost_of_goods_sold


def gross_margin(revenue: float, cost_of_goods_sold: float) -> float:
    """
    Gross Margin (%) =
        (Revenue - Cost of Goods Sold) / Revenue * 100
    """
    if revenue == 0:
        return 0

    return ((revenue - cost_of_goods_sold) / revenue) * 100


def contribution_margin(revenue: float, variable_cost: float) -> float:
    """
    Contribution Margin represents the amount remaining after variable costs.

    Contribution Margin =
        Revenue - Variable Costs

    This remaining amount contributes toward fixed costs and profit.
    """
    return revenue - variable_cost


def customer_acquisition_cost(marketing_cost: float,
                              sales_cost: float,
                              customers_acquired: int) -> float:
    """
    Customer Acquisition Cost (CAC)

    CAC =
        Total Sales and Marketing Cost
        --------------------------------
        Number of New Customers Acquired
    """

    if customers_acquired == 0:
        return 0

    return (marketing_cost + sales_cost) / customers_acquired


def customer_lifetime_value(average_revenue_per_period: float,
                            gross_margin_percentage: float,
                            customer_lifetime_periods: float) -> float:
    """
    Simplified Customer Lifetime Value (LTV)

    LTV =
        Average Revenue per Period
        *
        Gross Margin
        *
        Customer Lifetime

    A more advanced calculation may incorporate churn, discount rates,
    retention curves, expansion revenue, cohort behavior, and probability
    of default.
    """

    return (
        average_revenue_per_period
        * (gross_margin_percentage / 100)
        * customer_lifetime_periods
    )


def ltv_cac_ratio(ltv: float, cac: float) -> Optional[float]:
    """
    LTV:CAC Ratio

    This ratio compares the estimated economic value of a customer against
    the cost required to acquire that customer.
    """

    if cac == 0:
        return None

    return ltv / cac


# ============================================================================
# SECTION 3: B2B - BUSINESS TO BUSINESS
# ============================================================================

class B2BModel:
    """
    B2B means Business to Business.

    A B2B organization sells products or services to another organization
    rather than directly to an individual consumer.

    Typical examples include:

    - Enterprise software
    - Cloud infrastructure
    - Consulting
    - Industrial equipment
    - Logistics services
    - Financial technology infrastructure
    - HR technology
    - Cybersecurity products
    - Data services
    - Wholesale suppliers

    The fundamental distinction is that the buyer is usually acting on behalf
    of an organization.

    B2B purchasing decisions often involve multiple stakeholders.
    """

    def __init__(
        self,
        product_name: str,
        annual_contract_value: float,
        sales_cycle_days: int,
        number_of_buyers: int,
        implementation_cost: float
    ):
        self.product_name = product_name
        self.annual_contract_value = annual_contract_value
        self.sales_cycle_days = sales_cycle_days
        self.number_of_buyers = number_of_buyers
        self.implementation_cost = implementation_cost

    def annual_revenue(self) -> float:
        """
        Revenue generated from contracts.

        This is a simplified calculation:

        Annual Revenue =
            Annual Contract Value * Number of Buyers
        """

        return self.annual_contract_value * self.number_of_buyers

    def explain_buying_process(self):
        """
        B2B purchasing is frequently more complex than consumer purchasing.

        A single enterprise purchase may involve:

        - End user
        - Department manager
        - Technical evaluator
        - Procurement team
        - Finance team
        - Legal department
        - Information security team
        - Executive sponsor

        The person using the product may not be the person paying for it.
        The person approving the purchase may not be the person who selected it.

        This creates a multi-stakeholder decision process.
        """

        stakeholders = [
            "End User",
            "Manager",
            "Technical Evaluator",
            "Procurement",
            "Finance",
            "Legal",
            "Security Team",
            "Executive Sponsor"
        ]

        print("\nTypical B2B Buying Stakeholders:")
        for stakeholder in stakeholders:
            print(f"  - {stakeholder}")

    def customer_concentration_risk(
        self,
        largest_customer_revenue: float
    ) -> float:
        """
        Customer concentration risk becomes significant when a small number
        of customers represent a large percentage of total revenue.

        Customer Concentration Percentage =
            Largest Customer Revenue
            -------------------------
            Total Revenue
        """

        total_revenue = self.annual_revenue()

        if total_revenue == 0:
            return 0

        return (largest_customer_revenue / total_revenue) * 100


# ============================================================================
# B2B CHARACTERISTICS
# ============================================================================

B2B_CHARACTERISTICS = {
    "transaction_value":
        "Usually higher than typical consumer transactions.",

    "sales_cycle":
        "Can range from days to months or even years.",

    "decision_making":
        "Often involves multiple stakeholders and formal approval processes.",

    "relationship":
        "Long-term relationships and account management are important.",

    "customization":
        "Products may require configuration, integration, or customization.",

    "contracts":
        "Annual or multi-year contracts are common.",

    "switching_cost":
        "Switching suppliers may involve technical, operational, and financial costs.",

    "procurement":
        "Formal procurement processes may influence purchasing decisions."
}


# ============================================================================
# SECTION 4: B2C - BUSINESS TO CONSUMER
# ============================================================================

class B2CModel:
    """
    B2C means Business to Consumer.

    The organization sells directly to individual consumers.

    Examples include:

    - Retail brands
    - Restaurants
    - Consumer applications
    - Streaming platforms
    - Airlines
    - Consumer electronics companies
    - E-commerce retailers

    B2C purchasing behavior is often characterized by:

    - Large customer populations
    - Lower average transaction values compared with enterprise contracts
    - Faster purchasing decisions
    - Strong influence of brand and convenience
    - Emotional and behavioral factors
    - High dependence on marketing efficiency
    """

    def __init__(
        self,
        product_name: str,
        selling_price: float,
        units_sold: int,
        variable_cost_per_unit: float,
        advertising_cost: float
    ):
        self.product_name = product_name
        self.selling_price = selling_price
        self.units_sold = units_sold
        self.variable_cost_per_unit = variable_cost_per_unit
        self.advertising_cost = advertising_cost

    def revenue(self) -> float:
        return self.selling_price * self.units_sold

    def variable_cost(self) -> float:
        return self.variable_cost_per_unit * self.units_sold

    def contribution_after_advertising(self) -> float:
        """
        Simplified contribution after advertising expenditure.
        """

        return (
            self.revenue()
            - self.variable_cost()
            - self.advertising_cost
        )

    def conversion_rate(
        self,
        visitors: int,
        customers: int
    ) -> float:
        """
        Conversion Rate =
            Customers / Visitors * 100
        """

        if visitors == 0:
            return 0

        return (customers / visitors) * 100


# ============================================================================
# B2C CONSUMER JOURNEY
# ============================================================================

def consumer_journey():
    """
    A simplified B2C customer journey.

    1. Awareness
    2. Consideration
    3. Purchase
    4. Usage
    5. Retention
    6. Advocacy
    """

    stages = {
        "Awareness":
            "The consumer becomes aware of the product or brand.",

        "Consideration":
            "The consumer compares alternatives and evaluates perceived value.",

        "Purchase":
            "The consumer completes a transaction.",

        "Usage":
            "The customer experiences the product or service.",

        "Retention":
            "The business attempts to generate repeat purchases.",

        "Advocacy":
            "Satisfied customers may recommend the product to others."
    }

    print("\nB2C CUSTOMER JOURNEY")

    for stage, description in stages.items():
        print(f"\n{stage}")
        print(description)


# ============================================================================
# SECTION 5: D2C - DIRECT TO CONSUMER
# ============================================================================

class D2CModel:
    """
    D2C means Direct to Consumer.

    In a D2C model, a producer or brand sells directly to the end customer
    rather than relying exclusively on intermediaries such as:

    - Distributors
    - Wholesalers
    - Traditional retailers

    A D2C company may use:

    - Its own website
    - Mobile application
    - Social commerce
    - Direct physical stores

    The defining characteristic is ownership or substantial control over the
    direct customer relationship.
    """

    def __init__(
        self,
        product_price: float,
        manufacturing_cost: float,
        fulfillment_cost: float,
        payment_processing_cost: float,
        marketing_cost_per_customer: float
    ):
        self.product_price = product_price
        self.manufacturing_cost = manufacturing_cost
        self.fulfillment_cost = fulfillment_cost
        self.payment_processing_cost = payment_processing_cost
        self.marketing_cost_per_customer = marketing_cost_per_customer

    def contribution_per_customer(self) -> float:
        """
        D2C Contribution Per Customer

        Revenue
        - Manufacturing Cost
        - Fulfillment Cost
        - Payment Processing Cost
        - Marketing Cost
        """

        return (
            self.product_price
            - self.manufacturing_cost
            - self.fulfillment_cost
            - self.payment_processing_cost
            - self.marketing_cost_per_customer
        )

    def gross_margin_before_customer_acquisition(self) -> float:
        """
        Gross contribution before marketing cost.
        """

        return (
            self.product_price
            - self.manufacturing_cost
            - self.fulfillment_cost
            - self.payment_processing_cost
        )


# ============================================================================
# D2C ECONOMIC PECULIARITY
# ============================================================================

def compare_retail_and_d2c(
    consumer_price: float,
    retailer_margin_percentage: float,
    manufacturer_cost: float,
    d2c_marketing_cost: float,
    fulfillment_cost: float
):
    """
    D2C is often misunderstood as automatically more profitable.

    Removing a retailer can increase the manufacturer's share of revenue,
    but the D2C company may now need to bear costs previously handled by
    intermediaries.

    Traditional retail model:

        Consumer pays retail price
                |
                v
        Retailer retains margin
                |
                v
        Remaining revenue goes through supply chain

    D2C model:

        Consumer pays company directly
                |
                v
        Company receives revenue directly
                |
                v
        Company pays for:
        - Marketing
        - Fulfillment
        - Customer service
        - Returns
        - Payment processing
        - Technology
    """

    retail_revenue_to_brand = (
        consumer_price
        * (1 - retailer_margin_percentage / 100)
    )

    retail_profit_before_other_costs = (
        retail_revenue_to_brand
        - manufacturer_cost
    )

    d2c_profit_before_fixed_costs = (
        consumer_price
        - manufacturer_cost
        - d2c_marketing_cost
        - fulfillment_cost
    )

    print("\nRETAIL VS D2C COMPARISON")

    print(f"\nConsumer Price: {consumer_price:.2f}")

    print(
        f"Revenue to Brand Through Retail: "
        f"{retail_revenue_to_brand:.2f}"
    )

    print(
        f"Retail Model Contribution: "
        f"{retail_profit_before_other_costs:.2f}"
    )

    print(
        f"D2C Model Contribution: "
        f"{d2c_profit_before_fixed_costs:.2f}"
    )

    print(
        "\nInterpretation: D2C provides direct revenue access, but its "
        "profitability depends heavily on customer acquisition and "
        "operational costs."
    )


# ============================================================================
# SECTION 6: MARKETPLACE BUSINESS MODEL
# ============================================================================

class MarketplaceModel:
    """
    A marketplace connects two or more groups.

    Typical examples include:

    - Buyers and sellers
    - Riders and drivers
    - Guests and property owners
    - Freelancers and clients
    - Restaurants and consumers

    A marketplace does not necessarily own the underlying inventory.

    Its primary economic role is to facilitate matching and transactions.
    """

    def __init__(
        self,
        buyers: int,
        sellers: int,
        average_transaction_value: float,
        transactions_per_period: int,
        commission_percentage: float
    ):
        self.buyers = buyers
        self.sellers = sellers
        self.average_transaction_value = average_transaction_value
        self.transactions_per_period = transactions_per_period
        self.commission_percentage = commission_percentage

    def gross_merchandise_value(self) -> float:
        """
        GMV = Total value of transactions occurring on the marketplace.

        GMV is not necessarily marketplace revenue.

        This distinction is critical.

        Example:

        Customer purchases goods worth 1,000.
        Marketplace commission is 10%.

        GMV = 1,000
        Marketplace Revenue = 100
        """

        return (
            self.average_transaction_value
            * self.transactions_per_period
        )

    def marketplace_revenue(self) -> float:
        """
        Marketplace Revenue =
            GMV * Commission Percentage
        """

        return (
            self.gross_merchandise_value()
            * self.commission_percentage
            / 100
        )

    def take_rate(self) -> float:
        """
        Take Rate represents the percentage of transaction value retained by
        the marketplace as revenue.

        Take Rate =
            Marketplace Revenue / GMV * 100
        """

        gmv = self.gross_merchandise_value()

        if gmv == 0:
            return 0

        return (
            self.marketplace_revenue()
            / gmv
            * 100
        )


# ============================================================================
# MARKETPLACE LIQUIDITY
# ============================================================================

def marketplace_liquidity(
    active_buyers: int,
    active_sellers: int,
    successful_matches: int
):
    """
    Marketplace liquidity refers to the efficiency with which demand and
    supply can successfully find one another.

    A marketplace can have many registered users but poor liquidity.

    Example:

    100,000 registered buyers
    10,000 registered sellers

    If buyers cannot find relevant products or sellers receive no orders,
    the marketplace may have low effective liquidity.

    Successful Match Rate is simplified as:

        Successful Matches / Potential Interactions

    Real marketplaces require more sophisticated measurements depending on
    their industry.
    """

    potential_interactions = active_buyers * active_sellers

    if potential_interactions == 0:
        return 0

    return (
        successful_matches
        / potential_interactions
        * 100
    )


# ============================================================================
# NETWORK EFFECTS
# ============================================================================

class NetworkEffects:
    """
    A network effect occurs when the value of a product or platform changes
    as more participants join.

    Marketplace businesses frequently benefit from network effects.

    Direct network effect:

        More users -> More value for users

    Example:
        A communication platform becomes more useful when more contacts use it.

    Indirect network effect:

        More users on one side -> More value for another side

    Example:
        More buyers attract sellers.
        More sellers attract buyers.
    """

    @staticmethod
    def indirect_network_effect(
        buyers: int,
        sellers: int
    ) -> str:

        if buyers == 0 or sellers == 0:
            return "The marketplace lacks sufficient two-sided participation."

        return (
            f"The marketplace has {buyers} buyers and {sellers} sellers. "
            "Growth on one side can increase value for the other side."
        )


# ============================================================================
# MARKETPLACE CHICKEN-AND-EGG PROBLEM
# ============================================================================

def marketplace_chicken_and_egg_problem():
    """
    New marketplaces face a fundamental bootstrapping problem.

    Buyers ask:

        Why should I join if there are no sellers?

    Sellers ask:

        Why should I join if there are no buyers?

    Common strategies include:

    1. Build supply first.
    2. Build demand first.
    3. Subsidize one side.
    4. Focus on a narrow geography.
    5. Focus on a narrow category.
    6. Aggregate fragmented supply.
    7. Provide standalone value before network effects emerge.
    """

    strategies = [
        "Build supply before demand.",
        "Build demand before supply.",
        "Subsidize one side of the marketplace.",
        "Focus on a specific geographic region.",
        "Start with a narrow customer segment.",
        "Start with a narrow product category.",
        "Create standalone utility before the network becomes large."
    ]

    print("\nMARKETPLACE BOOTSTRAPPING STRATEGIES")

    for strategy in strategies:
        print(f"  - {strategy}")


# ============================================================================
# SECTION 7: SUBSCRIPTION BUSINESS MODEL
# ============================================================================

class SubscriptionModel:
    """
    In a subscription model, customers pay repeatedly at regular intervals.

    Common intervals:

    - Weekly
    - Monthly
    - Quarterly
    - Annually

    Subscription models are used for:

    - Software
    - Streaming
    - Education
    - Consumer products
    - Membership communities
    - Professional services
    - Media
    """

    def __init__(
        self,
        subscribers: int,
        monthly_price: float,
        monthly_churn_rate_percentage: float,
        new_subscribers_per_month: int
    ):
        self.subscribers = subscribers
        self.monthly_price = monthly_price
        self.monthly_churn_rate_percentage = monthly_churn_rate_percentage
        self.new_subscribers_per_month = new_subscribers_per_month

    def monthly_recurring_revenue(self) -> float:
        """
        MRR = Active Subscribers * Monthly Subscription Price
        """

        return self.subscribers * self.monthly_price

    def annual_recurring_revenue(self) -> float:
        """
        ARR is commonly approximated as:

        ARR = MRR * 12

        This is most useful for stable recurring revenue structures.
        """

        return self.monthly_recurring_revenue() * 12

    def churned_customers(self) -> float:
        """
        Customer Churn =
            Active Subscribers * Churn Rate
        """

        return (
            self.subscribers
            * self.monthly_churn_rate_percentage
            / 100
        )

    def projected_next_month_subscribers(self) -> float:
        """
        Next Month Subscribers =
            Existing Subscribers
            - Churned Subscribers
            + New Subscribers
        """

        return (
            self.subscribers
            - self.churned_customers()
            + self.new_subscribers_per_month
        )


# ============================================================================
# SUBSCRIPTION CHURN ANALYSIS
# ============================================================================

def calculate_churn_rate(
    customers_at_start: int,
    customers_lost: int
) -> float:
    """
    Churn Rate =
        Customers Lost
        -------------------
        Customers at Start
        *
        100
    """

    if customers_at_start == 0:
        return 0

    return (
        customers_lost
        / customers_at_start
        * 100
    )


def retention_rate(
    customers_at_start: int,
    customers_retained: int
) -> float:
    """
    Retention Rate =
        Customers Retained
        ----------------------
        Customers at Start
        *
        100
    """

    if customers_at_start == 0:
        return 0

    return (
        customers_retained
        / customers_at_start
        * 100
    )


# ============================================================================
# SUBSCRIPTION RETENTION PECULIARITY
# ============================================================================

def subscription_retention_simulation(
    starting_customers: int,
    monthly_churn_percentage: float,
    months: int
):
    """
    Simulates customer retention over time.

    Even apparently small churn rates can have substantial long-term effects.

    Example:

    Monthly Churn = 5%

    After each month, the business retains approximately 95% of the
    customers who were active at the beginning of that month.

    Retention compounds in the same way that financial growth compounds.
    """

    customers = starting_customers

    print("\nSUBSCRIPTION RETENTION SIMULATION")
    print("-" * 50)

    for month in range(1, months + 1):

        churned = (
            customers
            * monthly_churn_percentage
            / 100
        )

        customers -= churned

        print(
            f"Month {month}: "
            f"Estimated Remaining Customers = {customers:.2f}"
        )


# ============================================================================
# SECTION 8: COMPARING THE BUSINESS MODELS
# ============================================================================

BUSINESS_MODEL_COMPARISON = {
    "B2B": {
        "primary_customer": "Organizations",
        "transaction_size": "Usually high",
        "sales_cycle": "Longer",
        "relationship": "Long-term and account-based",
        "key_growth_driver": "Sales capability and customer retention",
        "common_revenue": "Contracts, licensing, services",
        "major_challenge": "Complex decision-making"
    },

    "B2C": {
        "primary_customer": "Individual consumers",
        "transaction_size": "Usually lower per transaction",
        "sales_cycle": "Short",
        "relationship": "Brand and experience-driven",
        "key_growth_driver": "Marketing and distribution",
        "common_revenue": "Product and service purchases",
        "major_challenge": "Customer acquisition competition"
    },

    "D2C": {
        "primary_customer": "Individual consumers",
        "transaction_size": "Consumer-level",
        "sales_cycle": "Short",
        "relationship": "Directly owned by the brand",
        "key_growth_driver": "Customer relationship and repeat purchases",
        "common_revenue": "Direct product sales",
        "major_challenge": "Marketing and fulfillment economics"
    },

    "Marketplace": {
        "primary_customer": "Multiple participant groups",
        "transaction_size": "Depends on category",
        "sales_cycle": "Transaction-driven",
        "relationship": "Platform-mediated",
        "key_growth_driver": "Network effects and liquidity",
        "common_revenue": "Commission and transaction fees",
        "major_challenge": "Balancing supply and demand"
    },

    "Subscription": {
        "primary_customer": "Recurring customers",
        "transaction_size": "Repeated periodic payments",
        "sales_cycle": "Initial conversion followed by retention",
        "relationship": "Ongoing",
        "key_growth_driver": "Retention and recurring revenue",
        "common_revenue": "Recurring fees",
        "major_challenge": "Churn"
    }
}


def display_business_model_comparison():
    """
    Displays a structured comparison of the five business models.
    """

    print("\n" + "=" * 100)
    print("COMPARISON OF BUSINESS MODELS")
    print("=" * 100)

    for model, characteristics in BUSINESS_MODEL_COMPARISON.items():

        print(f"\n{model}")

        for key, value in characteristics.items():

            formatted_key = key.replace("_", " ").title()

            print(
                f"  {formatted_key}: {value}"
            )


# ============================================================================
# SECTION 9: HYBRID BUSINESS MODELS
# ============================================================================

class HybridBusinessModel:
    """
    Modern businesses frequently combine multiple business models.

    Examples of combinations:

    B2B + Subscription
        Enterprise software sold through recurring contracts.

    B2C + Subscription
        Streaming or membership businesses.

    D2C + Subscription
        Consumer products delivered periodically.

    Marketplace + Subscription
        Sellers or users pay membership fees while transactions also generate
        commissions.

    Marketplace + B2B
        Businesses use a platform to transact with other businesses.

    A hybrid model can diversify revenue, but it can also increase
    organizational and operational complexity.
    """

    def __init__(
        self,
        name: str,
        models: List[str],
        revenue_streams: Dict[str, float]
    ):
        self.name = name
        self.models = models
        self.revenue_streams = revenue_streams

    def total_revenue(self) -> float:
        return sum(self.revenue_streams.values())

    def revenue_mix(self) -> Dict[str, float]:

        total = self.total_revenue()

        if total == 0:
            return {}

        return {
            stream: (
                revenue / total * 100
            )
            for stream, revenue
            in self.revenue_streams.items()
        }


# ============================================================================
# SECTION 10: BUSINESS MODEL SCALABILITY
# ============================================================================

def operating_leverage(
    revenue: float,
    variable_cost: float,
    fixed_cost: float
) -> Dict[str, float]:
    """
    Scalability depends partly on how costs behave as revenue grows.

    Variable costs increase with activity.

    Examples:
        - Raw materials
        - Shipping
        - Transaction processing
        - Direct labor in some models

    Fixed costs remain relatively stable within a certain operating range.

    Examples:
        - Core software development
        - Headquarters expenses
        - Certain administrative costs

    Businesses with high fixed costs and relatively low marginal costs may
    demonstrate strong operating leverage after reaching sufficient scale.
    """

    total_cost = variable_cost + fixed_cost

    profit = revenue - total_cost

    return {
        "revenue": revenue,
        "variable_cost": variable_cost,
        "fixed_cost": fixed_cost,
        "total_cost": total_cost,
        "profit": profit
    }


# ============================================================================
# SECTION 11: BREAK-EVEN ANALYSIS
# ============================================================================

def break_even_units(
    fixed_cost: float,
    selling_price_per_unit: float,
    variable_cost_per_unit: float
) -> Optional[float]:
    """
    Break-Even Units

    Fixed Cost
    ---------------------------------
    Selling Price - Variable Cost

    The denominator is the contribution margin per unit.
    """

    contribution_per_unit = (
        selling_price_per_unit
        - variable_cost_per_unit
    )

    if contribution_per_unit <= 0:
        return None

    return (
        fixed_cost
        / contribution_per_unit
    )


# ============================================================================
# SECTION 12: PRICING AND BUSINESS MODELS
# ============================================================================

class PricingStrategy:
    """
    Pricing is closely connected to business model design.

    Common approaches include:

    1. Cost-plus pricing
    2. Value-based pricing
    3. Competitive pricing
    4. Freemium pricing
    5. Tiered pricing
    6. Usage-based pricing
    7. Dynamic pricing
    8. Subscription pricing
    """

    @staticmethod
    def cost_plus_price(
        cost: float,
        markup_percentage: float
    ) -> float:

        return (
            cost
            * (1 + markup_percentage / 100)
        )

    @staticmethod
    def usage_based_revenue(
        units_consumed: int,
        price_per_unit: float
    ) -> float:

        return (
            units_consumed
            * price_per_unit
        )


# ============================================================================
# SECTION 13: B2B SALES FUNNEL
# ============================================================================

def b2b_sales_funnel(
    leads: int,
    qualified_leads: int,
    proposals: int,
    closed_deals: int
):
    """
    B2B sales funnels are useful for measuring progression through the
    enterprise purchasing process.
    """

    def percentage(part, total):

        if total == 0:
            return 0

        return (
            part
            / total
            * 100
        )

    print("\nB2B SALES FUNNEL")

    print(f"Initial Leads: {leads}")

    print(
        f"Qualified Leads: {qualified_leads} "
        f"({percentage(qualified_leads, leads):.2f}%)"
    )

    print(
        f"Proposals: {proposals} "
        f"({percentage(proposals, qualified_leads):.2f}% "
        f"of qualified leads)"
    )

    print(
        f"Closed Deals: {closed_deals} "
        f"({percentage(closed_deals, proposals):.2f}% "
        f"of proposals)"
    )


# ============================================================================
# SECTION 14: CUSTOMER ACQUISITION AND RETENTION
# ============================================================================

def customer_economics_example():

    marketing_cost = 500_000
    sales_cost = 300_000
    customers_acquired = 400

    cac = customer_acquisition_cost(
        marketing_cost,
        sales_cost,
        customers_acquired
    )

    average_revenue = 10_000
    gross_margin_pct = 70
    customer_lifetime_months = 24

    ltv = customer_lifetime_value(
        average_revenue,
        gross_margin_pct,
        customer_lifetime_months
    )

    ratio = ltv_cac_ratio(
        ltv,
        cac
    )

    print("\nCUSTOMER ECONOMICS EXAMPLE")

    print(
        f"Customer Acquisition Cost: {cac:.2f}"
    )

    print(
        f"Estimated Customer Lifetime Value: {ltv:.2f}"
    )

    if ratio is not None:

        print(
            f"LTV:CAC Ratio: {ratio:.2f}"
        )


# ============================================================================
# SECTION 15: STRATEGIC DIFFERENCES BETWEEN MODELS
# ============================================================================

def strategic_questions():

    questions = {
        "B2B": [
            "Who is the economic buyer?",
            "Who is the end user?",
            "What problem has measurable organizational value?",
            "How long is the procurement process?",
            "What integrations are required?",
            "How expensive is implementation?",
            "What creates switching costs?"
        ],

        "B2C": [
            "Why would consumers choose this product?",
            "How strong is brand awareness?",
            "How efficiently can customers be acquired?",
            "What improves conversion?",
            "What drives repeat purchases?",
            "How sensitive are customers to price?"
        ],

        "D2C": [
            "Can the brand profitably acquire customers directly?",
            "How expensive is fulfillment?",
            "What is the repeat purchase rate?",
            "Who owns the customer data?",
            "What happens when advertising costs increase?",
            "Can direct relationships justify the operational complexity?"
        ],

        "Marketplace": [
            "Which side of the market should be built first?",
            "How will supply and demand be balanced?",
            "What creates trust?",
            "What increases marketplace liquidity?",
            "What prevents participants from transacting outside the platform?",
            "How strong are network effects?"
        ],

        "Subscription": [
            "Why should customers continue paying?",
            "What causes churn?",
            "How frequently is value delivered?",
            "What retention mechanisms are sustainable?",
            "What is the relationship between CAC and lifetime value?",
            "How predictable is recurring revenue?"
        ]
    }

    print("\nSTRATEGIC QUESTIONS BY BUSINESS MODEL")

    for model, model_questions in questions.items():

        print(f"\n{model}")

        for question in model_questions:
            print(f"  - {question}")


# ============================================================================
# SECTION 16: ADVANCED BUSINESS MODEL RISKS
# ============================================================================

ADVANCED_RISKS = {

    "B2B": [
        "Revenue concentration",
        "Long procurement cycles",
        "Dependence on large contracts",
        "Complex implementation",
        "High cost of enterprise sales"
    ],

    "B2C": [
        "High advertising dependence",
        "Brand commoditization",
        "Price competition",
        "Rapid changes in consumer behavior",
        "Low switching costs"
    ],

    "D2C": [
        "Increasing customer acquisition costs",
        "Logistics complexity",
        "High product return costs",
        "Dependence on digital advertising",
        "Inventory management"
    ],

    "Marketplace": [
        "Chicken-and-egg problem",
        "Low marketplace liquidity",
        "Disintermediation",
        "Trust and fraud",
        "Supply concentration"
    ],

    "Subscription": [
        "Customer churn",
        "Subscription fatigue",
        "Increasing acquisition cost",
        "Revenue dependence on retention",
        "Price sensitivity"
    ]
}


def display_advanced_risks():

    print("\nADVANCED BUSINESS MODEL RISKS")

    for model, risks in ADVANCED_RISKS.items():

        print(f"\n{model}")

        for risk in risks:
            print(f"  - {risk}")


# ============================================================================
# SECTION 17: PRACTICAL DEMONSTRATION
# ============================================================================

def run_examples():

    print("\n" + "=" * 100)
    print("PRACTICAL BUSINESS MODEL DEMONSTRATION")
    print("=" * 100)

    # ------------------------------------------------------------------------
    # B2B Example
    # ------------------------------------------------------------------------

    b2b = B2BModel(
        product_name="Enterprise Analytics Platform",
        annual_contract_value=500_000,
        sales_cycle_days=120,
        number_of_buyers=50,
        implementation_cost=5_000_000
    )

    print("\nB2B MODEL")

    print(
        f"Annual Revenue: "
        f"{b2b.annual_revenue():,.2f}"
    )

    concentration = b2b.customer_concentration_risk(
        largest_customer_revenue=2_500_000
    )

    print(
        f"Largest Customer Revenue Concentration: "
        f"{concentration:.2f}%"
    )

    b2b.explain_buying_process()

    # ------------------------------------------------------------------------
    # B2C Example
    # ------------------------------------------------------------------------

    b2c = B2CModel(
        product_name="Consumer Product",
        selling_price=2_000,
        units_sold=10_000,
        variable_cost_per_unit=800,
        advertising_cost=3_000_000
    )

    print("\nB2C MODEL")

    print(
        f"Revenue: {b2c.revenue():,.2f}"
    )

    print(
        f"Variable Cost: {b2c.variable_cost():,.2f}"
    )

    print(
        f"Contribution After Advertising: "
        f"{b2c.contribution_after_advertising():,.2f}"
    )

    conversion = b2c.conversion_rate(
        visitors=500_000,
        customers=10_000
    )

    print(
        f"Conversion Rate: {conversion:.2f}%"
    )

    # ------------------------------------------------------------------------
    # D2C Example
    # ------------------------------------------------------------------------

    d2c = D2CModel(
        product_price=3_000,
        manufacturing_cost=900,
        fulfillment_cost=250,
        payment_processing_cost=90,
        marketing_cost_per_customer=600
    )

    print("\nD2C MODEL")

    print(
        f"Contribution Per Customer: "
        f"{d2c.contribution_per_customer():.2f}"
    )

    print(
        f"Contribution Before Marketing: "
        f"{d2c.gross_margin_before_customer_acquisition():.2f}"
    )

    compare_retail_and_d2c(
        consumer_price=3_000,
        retailer_margin_percentage=40,
        manufacturer_cost=900,
        d2c_marketing_cost=600,
        fulfillment_cost=250
    )

    # ------------------------------------------------------------------------
    # Marketplace Example
    # ------------------------------------------------------------------------

    marketplace = MarketplaceModel(
        buyers=100_000,
        sellers=5_000,
        average_transaction_value=1_500,
        transactions_per_period=50_000,
        commission_percentage=12
    )

    print("\nMARKETPLACE MODEL")

    print(
        f"Gross Merchandise Value: "
        f"{marketplace.gross_merchandise_value():,.2f}"
    )

    print(
        f"Marketplace Revenue: "
        f"{marketplace.marketplace_revenue():,.2f}"
    )

    print(
        f"Take Rate: "
        f"{marketplace.take_rate():.2f}%"
    )

    # ------------------------------------------------------------------------
    # Subscription Example
    # ------------------------------------------------------------------------

    subscription = SubscriptionModel(
        subscribers=20_000,
        monthly_price=500,
        monthly_churn_rate_percentage=4,
        new_subscribers_per_month=2_000
    )

    print("\nSUBSCRIPTION MODEL")

    print(
        f"Monthly Recurring Revenue: "
        f"{subscription.monthly_recurring_revenue():,.2f}"
    )

    print(
        f"Annual Recurring Revenue: "
        f"{subscription.annual_recurring_revenue():,.2f}"
    )

    print(
        f"Customers Expected to Churn: "
        f"{subscription.churned_customers():,.2f}"
    )

    print(
        f"Projected Subscribers Next Month: "
        f"{subscription.projected_next_month_subscribers():,.2f}"
    )

    subscription_retention_simulation(
        starting_customers=20_000,
        monthly_churn_percentage=4,
        months=12
    )

    # ------------------------------------------------------------------------
    # Business Model Comparison
    # ------------------------------------------------------------------------

    display_business_model_comparison()

    # ------------------------------------------------------------------------
    # Customer Economics
    # ------------------------------------------------------------------------

    customer_economics_example()

    # ------------------------------------------------------------------------
    # B2B Sales Funnel
    # ------------------------------------------------------------------------

    b2b_sales_funnel(
        leads=1000,
        qualified_leads=400,
        proposals=120,
        closed_deals=30
    )

    # ------------------------------------------------------------------------
    # Break-Even
    # ------------------------------------------------------------------------

    break_even = break_even_units(
        fixed_cost=10_000_000,
        selling_price_per_unit=2_000,
        variable_cost_per_unit=800
    )

    print("\nBREAK-EVEN ANALYSIS")

    if break_even is not None:

        print(
            f"Break-Even Units: "
            f"{break_even:,.2f}"
        )

    # ------------------------------------------------------------------------
    # Strategic Questions
    # ------------------------------------------------------------------------

    strategic_questions()

    # ------------------------------------------------------------------------
    # Risks
    # ------------------------------------------------------------------------

    display_advanced_risks()


# ============================================================================
# SECTION 18: CORE BUSINESS MODEL OBJECTS
# ============================================================================

def demonstrate_business_model_structure():

    models = [

        BusinessModel(
            name="B2B",
            customer="Organizations and institutions.",
            value_proposition=(
                "Solves organizational problems through products, "
                "technology, infrastructure, services, or expertise."
            ),
            revenue_sources=[
                "Enterprise contracts",
                "Licensing",
                "Professional services",
                "Recurring software fees"
            ],
            distribution_channels=[
                "Direct sales",
                "Partners",
                "Resellers",
                "Account-based selling"
            ],
            major_costs=[
                "Sales teams",
                "Product development",
                "Implementation",
                "Customer success"
            ],
            key_resources=[
                "Technology",
                "Sales capability",
                "Domain expertise",
                "Customer relationships"
            ],
            key_metrics=[
                "Annual Contract Value",
                "Customer Retention",
                "Net Revenue Retention",
                "Sales Cycle Length"
            ],
            risks=[
                "Customer concentration",
                "Long sales cycles",
                "Complex procurement"
            ]
        ),

        BusinessModel(
            name="B2C",
            customer="Individual consumers.",
            value_proposition=(
                "Provides a product or service that addresses consumer "
                "needs, preferences, convenience, entertainment, or lifestyle."
            ),
            revenue_sources=[
                "Product sales",
                "Service fees",
                "Advertising",
                "Digital purchases"
            ],
            distribution_channels=[
                "Retail",
                "E-commerce",
                "Mobile applications",
                "Physical stores"
            ],
            major_costs=[
                "Marketing",
                "Inventory",
                "Operations",
                "Customer service"
            ],
            key_resources=[
                "Brand",
                "Distribution",
                "Customer data",
                "Product capability"
            ],
            key_metrics=[
                "Conversion Rate",
                "CAC",
                "Repeat Purchase Rate",
                "Average Order Value"
            ],
            risks=[
                "Marketing cost inflation",
                "Consumer switching",
                "Intense competition"
            ]
        )
    ]

    for model in models:
        model.describe()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":

    demonstrate_business_model_structure()

    consumer_journey()

    marketplace_chicken_and_egg_problem()

    run_examples()
