"""
Profitability Metrics: Gross Profit, EBITDA, Operating Profit, and Net Profit

This self-contained script explains and demonstrates the major profitability
measures used in financial analysis:

1. Revenue
2. Cost of Goods Sold (COGS)
3. Gross Profit
4. EBITDA
5. Operating Profit (EBIT)
6. Net Profit

The script progresses from basic calculations to margin analysis, statement
construction, scenario analysis, validation, edge cases, comparisons, and
practical business analysis.

All examples use Python's Decimal class for financial calculations because
binary floating-point values can introduce rounding inaccuracies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Dict, List, Optional


# =============================================================================
# SECTION 1: FINANCIAL NUMBER BASICS
# =============================================================================

# Decimal is preferred for financial calculations where predictable decimal
# arithmetic and explicit rounding are important.
MONEY_QUANTUM = Decimal("0.01")
PERCENT_QUANTUM = Decimal("0.01")


def to_decimal(value: object) -> Decimal:
    """
    Convert a numeric value safely into Decimal.

    Strings are generally preferred over floats because Decimal(float) may
    preserve floating-point approximation artifacts.

    Examples:
        to_decimal("100.25")
        to_decimal(100)
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"Cannot convert {value!r} to a financial number.") from error


def money(value: Decimal) -> Decimal:
    """Round a monetary value to two decimal places."""
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def percentage(value: Decimal) -> Decimal:
    """Round a percentage to two decimal places."""
    return value.quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    """Format a Decimal value as a monetary amount."""
    return f"{money(value):,.2f}"


def format_percent(value: Optional[Decimal]) -> str:
    """Format a Decimal percentage, handling unavailable values."""
    if value is None:
        return "N/A"
    return f"{percentage(value):,.2f}%"


def calculate_margin(profit: Decimal, revenue: Decimal) -> Optional[Decimal]:
    """
    Calculate profit margin as:

        Profit Margin = (Profit / Revenue) × 100

    Revenue equal to zero produces an undefined percentage, so None is returned.
    """
    if revenue == 0:
        return None
    return (profit / revenue) * Decimal("100")


# =============================================================================
# SECTION 2: FUNDAMENTAL PROFITABILITY CONCEPTS
# =============================================================================

"""
A simplified income statement can be represented as:

Revenue
- Cost of Goods Sold
= Gross Profit

Gross Profit
- Operating Expenses
= Operating Profit / EBIT

Operating Profit
+ Other Operating Adjustments where applicable
+ Depreciation and Amortization for EBITDA reconstruction
= EBITDA

Operating Profit
- Interest Expense
+ Interest Income
+/- Non-operating Income or Expense
= Profit Before Tax

Profit Before Tax
- Income Tax
= Net Profit

The exact presentation can differ depending on accounting standards, industry,
and company reporting policies.
"""


def gross_profit(revenue: Decimal, cost_of_goods_sold: Decimal) -> Decimal:
    """
    Calculate gross profit.

        Gross Profit = Revenue - COGS
    """
    return revenue - cost_of_goods_sold


def gross_profit_margin(
    revenue: Decimal,
    cost_of_goods_sold: Decimal,
) -> Optional[Decimal]:
    """Calculate gross profit as a percentage of revenue."""
    return calculate_margin(gross_profit(revenue, cost_of_goods_sold), revenue)


def operating_profit(
    gross_profit_value: Decimal,
    operating_expenses: Decimal,
) -> Decimal:
    """
    Calculate operating profit.

        Operating Profit = Gross Profit - Operating Expenses

    Operating expenses may include selling, general, administrative, research,
    marketing, salaries, rent, utilities, and other expenses related to normal
    operations, depending on accounting classification.
    """
    return gross_profit_value - operating_expenses


def operating_profit_margin(
    revenue: Decimal,
    gross_profit_value: Decimal,
    operating_expenses: Decimal,
) -> Optional[Decimal]:
    """Calculate operating profit margin."""
    return calculate_margin(
        operating_profit(gross_profit_value, operating_expenses),
        revenue,
    )


def calculate_ebitda(
    operating_profit_value: Decimal,
    depreciation: Decimal,
    amortization: Decimal,
) -> Decimal:
    """
    Calculate EBITDA using operating profit.

        EBITDA = Operating Profit + Depreciation + Amortization

    EBITDA is a non-GAAP or non-IFRS measure in many jurisdictions. Companies
    may use different definitions, especially when presenting adjusted EBITDA.
    """
    return operating_profit_value + depreciation + amortization


def ebitda_margin(
    revenue: Decimal,
    operating_profit_value: Decimal,
    depreciation: Decimal,
    amortization: Decimal,
) -> Optional[Decimal]:
    """Calculate EBITDA margin."""
    return calculate_margin(
        calculate_ebitda(
            operating_profit_value,
            depreciation,
            amortization,
        ),
        revenue,
    )


def net_profit(
    operating_profit_value: Decimal,
    interest_income: Decimal,
    interest_expense: Decimal,
    other_income: Decimal,
    other_expenses: Decimal,
    income_tax: Decimal,
) -> Decimal:
    """
    Calculate simplified net profit.

        Net Profit
        = Operating Profit
        + Interest Income
        - Interest Expense
        + Other Income
        - Other Expenses
        - Income Tax

    Real-world financial statements may include additional items such as:
    discontinued operations, minority interests, exceptional items, and
    accounting adjustments.
    """
    return (
        operating_profit_value
        + interest_income
        - interest_expense
        + other_income
        - other_expenses
        - income_tax
    )


# =============================================================================
# SECTION 3: SIMPLE CALCULATION EXAMPLE
# =============================================================================


def demonstrate_basic_profitability() -> None:
    """Demonstrate the basic relationship between major profitability measures."""

    print("\n" + "=" * 80)
    print("BASIC PROFITABILITY EXAMPLE")
    print("=" * 80)

    revenue = to_decimal("1000000")
    cogs = to_decimal("400000")

    # Operating expenses exclude depreciation and amortization here so that
    # EBITDA and operating profit can be demonstrated distinctly.
    cash_operating_expenses = to_decimal("250000")
    depreciation = to_decimal("30000")
    amortization = to_decimal("20000")

    gross = gross_profit(revenue, cogs)

    total_operating_expenses = (
        cash_operating_expenses + depreciation + amortization
    )

    operating = operating_profit(gross, total_operating_expenses)

    ebitda = calculate_ebitda(
        operating,
        depreciation,
        amortization,
    )

    interest_income = to_decimal("5000")
    interest_expense = to_decimal("25000")
    other_income = to_decimal("10000")
    other_expenses = to_decimal("5000")
    tax = to_decimal("60000")

    final_net_profit = net_profit(
        operating,
        interest_income,
        interest_expense,
        other_income,
        other_expenses,
        tax,
    )

    print(f"Revenue:                 {format_money(revenue)}")
    print(f"COGS:                    {format_money(cogs)}")
    print(f"Gross Profit:            {format_money(gross)}")
    print(f"Gross Profit Margin:     {format_percent(calculate_margin(gross, revenue))}")
    print()

    print(f"Cash Operating Expenses: {format_money(cash_operating_expenses)}")
    print(f"Depreciation:            {format_money(depreciation)}")
    print(f"Amortization:            {format_money(amortization)}")
    print(f"Operating Profit:        {format_money(operating)}")
    print(
        f"Operating Profit Margin: "
        f"{format_percent(calculate_margin(operating, revenue))}"
    )
    print()

    print(f"EBITDA:                  {format_money(ebitda)}")
    print(f"EBITDA Margin:           {format_percent(calculate_margin(ebitda, revenue))}")
    print()

    print(f"Interest Income:         {format_money(interest_income)}")
    print(f"Interest Expense:        {format_money(interest_expense)}")
    print(f"Other Income:            {format_money(other_income)}")
    print(f"Other Expenses:          {format_money(other_expenses)}")
    print(f"Income Tax:              {format_money(tax)}")
    print(f"Net Profit:              {format_money(final_net_profit)}")
    print(
        f"Net Profit Margin:       "
        f"{format_percent(calculate_margin(final_net_profit, revenue))}"
    )


# =============================================================================
# SECTION 4: STRUCTURED INCOME STATEMENT MODEL
# =============================================================================


@dataclass
class IncomeStatement:
    """
    A simplified income statement model.

    Amounts are stored as positive values representing the magnitude of each
    revenue or expense category. Calculation methods apply the appropriate
    accounting direction.

    Important distinction:
        Revenue is normally recognized under accounting rules and does not
        necessarily equal cash collected during the period.

        Expenses are recognized according to accounting principles and may not
        equal cash paid during the period.
    """

    revenue: Decimal
    cost_of_goods_sold: Decimal

    selling_expense: Decimal = Decimal("0")
    general_administrative_expense: Decimal = Decimal("0")
    research_and_development_expense: Decimal = Decimal("0")
    other_cash_operating_expenses: Decimal = Decimal("0")

    depreciation: Decimal = Decimal("0")
    amortization: Decimal = Decimal("0")

    interest_income: Decimal = Decimal("0")
    interest_expense: Decimal = Decimal("0")

    other_income: Decimal = Decimal("0")
    other_expenses: Decimal = Decimal("0")

    income_tax_expense: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate that financial inputs are not negative magnitudes."""
        for field_name, field_value in self.__dict__.items():
            if field_value < 0:
                raise ValueError(
                    f"{field_name} cannot be negative. "
                    "Use positive expense magnitudes and allow calculations "
                    "to apply subtraction."
                )

    @property
    def gross_profit(self) -> Decimal:
        """Revenue minus cost of goods sold."""
        return self.revenue - self.cost_of_goods_sold

    @property
    def cash_operating_expenses(self) -> Decimal:
        """
        Operating expenses excluding depreciation and amortization.

        This separation helps reconstruct EBITDA.
        """
        return (
            self.selling_expense
            + self.general_administrative_expense
            + self.research_and_development_expense
            + self.other_cash_operating_expenses
        )

    @property
    def total_operating_expenses(self) -> Decimal:
        """All operating expenses including depreciation and amortization."""
        return (
            self.cash_operating_expenses
            + self.depreciation
            + self.amortization
        )

    @property
    def operating_profit(self) -> Decimal:
        """
        Operating Profit, commonly related to EBIT in many analytical contexts.

        Terminology can differ across companies. Analysts should always inspect
        the specific financial statement definitions and line items.
        """
        return self.gross_profit - self.total_operating_expenses

    @property
    def ebitda(self) -> Decimal:
        """
        Earnings before interest, taxes, depreciation, and amortization.

        Calculated here as:
            Operating Profit + Depreciation + Amortization
        """
        return (
            self.operating_profit
            + self.depreciation
            + self.amortization
        )

    @property
    def profit_before_tax(self) -> Decimal:
        """Profit before income tax."""
        return (
            self.operating_profit
            + self.interest_income
            - self.interest_expense
            + self.other_income
            - self.other_expenses
        )

    @property
    def net_profit(self) -> Decimal:
        """Profit after income tax expense."""
        return self.profit_before_tax - self.income_tax_expense

    @property
    def gross_margin(self) -> Optional[Decimal]:
        return calculate_margin(self.gross_profit, self.revenue)

    @property
    def ebitda_margin(self) -> Optional[Decimal]:
        return calculate_margin(self.ebitda, self.revenue)

    @property
    def operating_margin(self) -> Optional[Decimal]:
        return calculate_margin(self.operating_profit, self.revenue)

    @property
    def net_margin(self) -> Optional[Decimal]:
        return calculate_margin(self.net_profit, self.revenue)

    def as_dict(self) -> Dict[str, Decimal]:
        """Return important income statement measures as a dictionary."""
        return {
            "Revenue": self.revenue,
            "Cost of Goods Sold": self.cost_of_goods_sold,
            "Gross Profit": self.gross_profit,
            "Cash Operating Expenses": self.cash_operating_expenses,
            "Depreciation": self.depreciation,
            "Amortization": self.amortization,
            "Operating Profit": self.operating_profit,
            "EBITDA": self.ebitda,
            "Interest Income": self.interest_income,
            "Interest Expense": self.interest_expense,
            "Other Income": self.other_income,
            "Other Expenses": self.other_expenses,
            "Profit Before Tax": self.profit_before_tax,
            "Income Tax Expense": self.income_tax_expense,
            "Net Profit": self.net_profit,
        }

    def print_statement(self) -> None:
        """Print a readable simplified income statement."""
        print("\n" + "=" * 80)
        print("SIMPLIFIED INCOME STATEMENT")
        print("=" * 80)

        print(f"Revenue                         {format_money(self.revenue)}")
        print(
            f"Less: Cost of Goods Sold        "
            f"({format_money(self.cost_of_goods_sold)})"
        )
        print(f"Gross Profit                    {format_money(self.gross_profit)}")
        print(f"Gross Margin                    {format_percent(self.gross_margin)}")
        print()

        print(
            f"Less: Cash Operating Expenses   "
            f"({format_money(self.cash_operating_expenses)})"
        )
        print(
            f"Less: Depreciation              "
            f"({format_money(self.depreciation)})"
        )
        print(
            f"Less: Amortization              "
            f"({format_money(self.amortization)})"
        )
        print(
            f"Operating Profit                "
            f"{format_money(self.operating_profit)}"
        )
        print(
            f"Operating Margin                "
            f"{format_percent(self.operating_margin)}"
        )
        print()

        print(f"EBITDA                          {format_money(self.ebitda)}")
        print(f"EBITDA Margin                   {format_percent(self.ebitda_margin)}")
        print()

        print(
            f"Add: Interest Income            "
            f"{format_money(self.interest_income)}"
        )
        print(
            f"Less: Interest Expense          "
            f"({format_money(self.interest_expense)})"
        )
        print(f"Add: Other Income               {format_money(self.other_income)}")
        print(
            f"Less: Other Expenses            "
            f"({format_money(self.other_expenses)})"
        )
        print(
            f"Profit Before Tax               "
            f"{format_money(self.profit_before_tax)}"
        )
        print(
            f"Less: Income Tax Expense        "
            f"({format_money(self.income_tax_expense)})"
        )
        print(f"Net Profit                      {format_money(self.net_profit)}")
        print(f"Net Profit Margin               {format_percent(self.net_margin)}")


# =============================================================================
# SECTION 5: GROSS PROFIT IN DETAIL
# =============================================================================


def demonstrate_gross_profit_concepts() -> None:
    """
    Demonstrate gross profit and the importance of cost classification.
    """

    print("\n" + "=" * 80)
    print("GROSS PROFIT: COST STRUCTURE EXAMPLE")
    print("=" * 80)

    revenue = to_decimal("500000")
    material_cost = to_decimal("120000")
    direct_labor = to_decimal("80000")
    manufacturing_overhead = to_decimal("50000")

    cogs = material_cost + direct_labor + manufacturing_overhead
    gross = revenue - cogs

    print(f"Revenue:                  {format_money(revenue)}")
    print(f"Direct Materials:         {format_money(material_cost)}")
    print(f"Direct Labor:             {format_money(direct_labor)}")
    print(f"Manufacturing Overhead:   {format_money(manufacturing_overhead)}")
    print(f"Total COGS:               {format_money(cogs)}")
    print(f"Gross Profit:             {format_money(gross)}")
    print(f"Gross Margin:             {format_percent(calculate_margin(gross, revenue))}")

    print("\nInterpretation:")
    print(
        "Gross profit measures the amount remaining after direct or production-"
        "related costs are deducted from revenue."
    )
    print(
        "A company can have a high gross profit but still have a net loss if "
        "operating expenses, interest costs, taxes, or other expenses are large."
    )


# =============================================================================
# SECTION 6: EBITDA AND OPERATING PROFIT
# =============================================================================


def demonstrate_ebitda_vs_operating_profit() -> None:
    """
    Demonstrate the relationship between EBITDA and operating profit.
    """

    print("\n" + "=" * 80)
    print("EBITDA VS OPERATING PROFIT")
    print("=" * 80)

    revenue = to_decimal("2000000")
    gross = to_decimal("1200000")
    cash_operating_expenses = to_decimal("600000")
    depreciation = to_decimal("100000")
    amortization = to_decimal("50000")

    ebitda = gross - cash_operating_expenses

    operating = (
        ebitda
        - depreciation
        - amortization
    )

    reconstructed_ebitda = (
        operating
        + depreciation
        + amortization
    )

    print(f"Revenue:                     {format_money(revenue)}")
    print(f"Gross Profit:                {format_money(gross)}")
    print(f"Cash Operating Expenses:     {format_money(cash_operating_expenses)}")
    print(f"EBITDA:                      {format_money(ebitda)}")
    print()

    print(f"Depreciation:                {format_money(depreciation)}")
    print(f"Amortization:                {format_money(amortization)}")
    print(f"Operating Profit:            {format_money(operating)}")
    print()

    print(
        f"EBITDA reconstructed from "
        f"Operating Profit:            {format_money(reconstructed_ebitda)}"
    )

    print("\nKey distinction:")
    print(
        "Depreciation and amortization are expenses that reduce operating profit "
        "but are added back when calculating EBITDA."
    )
    print(
        "EBITDA is not the same as cash flow. A business can report positive "
        "EBITDA while facing negative operating cash flow because of working "
        "capital changes, taxes, interest payments, and capital expenditures."
    )


# =============================================================================
# SECTION 7: NET PROFIT AND CAPITAL STRUCTURE
# =============================================================================


def demonstrate_interest_impact() -> None:
    """
    Demonstrate how two businesses with identical operations can have different
    net profits because of different financing structures.
    """

    print("\n" + "=" * 80)
    print("OPERATING PERFORMANCE VS FINANCING STRUCTURE")
    print("=" * 80)

    operating_profit_value = to_decimal("500000")
    tax_rate = Decimal("0.25")

    low_debt_interest = to_decimal("50000")
    high_debt_interest = to_decimal("250000")

    low_debt_profit_before_tax = (
        operating_profit_value - low_debt_interest
    )
    high_debt_profit_before_tax = (
        operating_profit_value - high_debt_interest
    )

    low_debt_tax = low_debt_profit_before_tax * tax_rate
    high_debt_tax = high_debt_profit_before_tax * tax_rate

    low_debt_net_profit = (
        low_debt_profit_before_tax - low_debt_tax
    )

    high_debt_net_profit = (
        high_debt_profit_before_tax - high_debt_tax
    )

    print(
        f"Identical Operating Profit:      "
        f"{format_money(operating_profit_value)}"
    )
    print()

    print("LOWER-DEBT BUSINESS")
    print(f"Interest Expense:                {format_money(low_debt_interest)}")
    print(
        f"Profit Before Tax:               "
        f"{format_money(low_debt_profit_before_tax)}"
    )
    print(f"Tax:                             {format_money(low_debt_tax)}")
    print(f"Net Profit:                      {format_money(low_debt_net_profit)}")
    print()

    print("HIGHER-DEBT BUSINESS")
    print(f"Interest Expense:                {format_money(high_debt_interest)}")
    print(
        f"Profit Before Tax:               "
        f"{format_money(high_debt_profit_before_tax)}"
    )
    print(f"Tax:                             {format_money(high_debt_tax)}")
    print(f"Net Profit:                      {format_money(high_debt_net_profit)}")

    print("\nObservation:")
    print(
        "Operating profit isolates core operating performance more effectively "
        "than net profit when comparing companies with substantially different "
        "interest burdens."
    )


# =============================================================================
# SECTION 8: COMPLETE BUSINESS EXAMPLE
# =============================================================================


def create_sample_income_statement() -> IncomeStatement:
    """Create a realistic example for repeated analysis."""

    return IncomeStatement(
        revenue=to_decimal("10000000"),
        cost_of_goods_sold=to_decimal("4200000"),
        selling_expense=to_decimal("850000"),
        general_administrative_expense=to_decimal("900000"),
        research_and_development_expense=to_decimal("300000"),
        other_cash_operating_expenses=to_decimal("250000"),
        depreciation=to_decimal("400000"),
        amortization=to_decimal("100000"),
        interest_income=to_decimal("50000"),
        interest_expense=to_decimal("300000"),
        other_income=to_decimal("75000"),
        other_expenses=to_decimal("25000"),
        income_tax_expense=to_decimal("925000"),
    )


# =============================================================================
# SECTION 9: PROFITABILITY MARGINS
# =============================================================================


def demonstrate_profitability_margins(statement: IncomeStatement) -> None:
    """
    Demonstrate why absolute profit and profit margins answer different
    analytical questions.
    """

    print("\n" + "=" * 80)
    print("PROFITABILITY MARGINS")
    print("=" * 80)

    metrics = [
        ("Gross Profit", statement.gross_profit, statement.gross_margin),
        ("EBITDA", statement.ebitda, statement.ebitda_margin),
        (
            "Operating Profit",
            statement.operating_profit,
            statement.operating_margin,
        ),
        ("Net Profit", statement.net_profit, statement.net_margin),
    ]

    for name, value, margin in metrics:
        print(
            f"{name:<20} "
            f"Amount: {format_money(value):>15}   "
            f"Margin: {format_percent(margin):>10}"
        )

    print("\nMargin interpretation:")
    print(
        "A margin standardizes profit relative to revenue. This makes it easier "
        "to compare businesses of different sizes."
    )


# =============================================================================
# SECTION 10: VERTICAL ANALYSIS
# =============================================================================


def vertical_analysis(statement: IncomeStatement) -> Dict[str, Optional[Decimal]]:
    """
    Express each income statement item as a percentage of revenue.

    This is commonly called common-size or vertical analysis.
    """
    results: Dict[str, Optional[Decimal]] = {}

    for name, value in statement.as_dict().items():
        results[name] = calculate_margin(value, statement.revenue)

    return results


def demonstrate_vertical_analysis(statement: IncomeStatement) -> None:
    """Print a common-size income statement."""

    print("\n" + "=" * 80)
    print("VERTICAL ANALYSIS: EACH ITEM AS A PERCENTAGE OF REVENUE")
    print("=" * 80)

    analysis = vertical_analysis(statement)

    for name, margin in analysis.items():
        print(f"{name:<30} {format_percent(margin)}")


# =============================================================================
# SECTION 11: PERIOD-TO-PERIOD GROWTH
# =============================================================================


def percentage_change(
    previous: Decimal,
    current: Decimal,
) -> Optional[Decimal]:
    """
    Calculate percentage change.

        ((Current - Previous) / Previous) × 100

    Percentage change is undefined when the previous value is zero.
    """
    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * Decimal("100")


@dataclass
class ProfitabilityPeriod:
    """A named period containing an income statement."""

    name: str
    statement: IncomeStatement


def compare_periods(
    previous: ProfitabilityPeriod,
    current: ProfitabilityPeriod,
) -> None:
    """
    Compare important profitability metrics between two periods.
    """

    print("\n" + "=" * 80)
    print(f"PERIOD COMPARISON: {previous.name} VS {current.name}")
    print("=" * 80)

    comparison_metrics = [
        ("Revenue", previous.statement.revenue, current.statement.revenue),
        (
            "Gross Profit",
            previous.statement.gross_profit,
            current.statement.gross_profit,
        ),
        (
            "EBITDA",
            previous.statement.ebitda,
            current.statement.ebitda,
        ),
        (
            "Operating Profit",
            previous.statement.operating_profit,
            current.statement.operating_profit,
        ),
        (
            "Net Profit",
            previous.statement.net_profit,
            current.statement.net_profit,
        ),
    ]

    print(
        f"{'Metric':<20}"
        f"{previous.name:>15}"
        f"{current.name:>15}"
        f"{'Change':>15}"
        f"{'% Change':>15}"
    )
    print("-" * 80)

    for name, previous_value, current_value in comparison_metrics:
        absolute_change = current_value - previous_value
        change_percent = percentage_change(
            previous_value,
            current_value,
        )

        print(
            f"{name:<20}"
            f"{format_money(previous_value):>15}"
            f"{format_money(current_value):>15}"
            f"{format_money(absolute_change):>15}"
            f"{format_percent(change_percent):>15}"
        )


# =============================================================================
# SECTION 12: SCENARIO ANALYSIS
# =============================================================================


def create_statement_from_percentage_changes(
    base: IncomeStatement,
    revenue_change_percent: Decimal,
    cogs_change_percent: Decimal,
    operating_expense_change_percent: Decimal,
) -> IncomeStatement:
    """
    Create a new scenario from percentage changes.

    This simplified model changes revenue, COGS, and selected operating expenses
    while keeping financing and tax line items unchanged.

    Example:
        10 means increase by 10%.
        -5 means decrease by 5%.
    """

    revenue_multiplier = (
        Decimal("1") + revenue_change_percent / Decimal("100")
    )

    cogs_multiplier = (
        Decimal("1") + cogs_change_percent / Decimal("100")
    )

    operating_multiplier = (
        Decimal("1") + operating_expense_change_percent / Decimal("100")
    )

    return IncomeStatement(
        revenue=base.revenue * revenue_multiplier,
        cost_of_goods_sold=base.cost_of_goods_sold * cogs_multiplier,
        selling_expense=base.selling_expense * operating_multiplier,
        general_administrative_expense=(
            base.general_administrative_expense * operating_multiplier
        ),
        research_and_development_expense=(
            base.research_and_development_expense * operating_multiplier
        ),
        other_cash_operating_expenses=(
            base.other_cash_operating_expenses * operating_multiplier
        ),
        depreciation=base.depreciation,
        amortization=base.amortization,
        interest_income=base.interest_income,
        interest_expense=base.interest_expense,
        other_income=base.other_income,
        other_expenses=base.other_expenses,
        income_tax_expense=base.income_tax_expense,
    )


def demonstrate_scenarios(base: IncomeStatement) -> None:
    """Demonstrate how profitability changes under different assumptions."""

    print("\n" + "=" * 80)
    print("PROFITABILITY SCENARIO ANALYSIS")
    print("=" * 80)

    scenarios = {
        "Base Case": (
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
        ),
        "Revenue Growth": (
            Decimal("10"),
            Decimal("0"),
            Decimal("0"),
        ),
        "Higher Input Costs": (
            Decimal("0"),
            Decimal("10"),
            Decimal("0"),
        ),
        "Cost Efficiency": (
            Decimal("0"),
            Decimal("-5"),
            Decimal("-10"),
        ),
        "Stress Case": (
            Decimal("-10"),
            Decimal("8"),
            Decimal("5"),
        ),
    }

    print(
        f"{'Scenario':<22}"
        f"{'Revenue':>14}"
        f"{'Gross Profit':>16}"
        f"{'EBITDA':>14}"
        f"{'Operating':>14}"
        f"{'Net Profit':>14}"
    )
    print("-" * 94)

    for name, (
        revenue_change,
        cogs_change,
        operating_change,
    ) in scenarios.items():

        scenario = create_statement_from_percentage_changes(
            base,
            revenue_change,
            cogs_change,
            operating_change,
        )

        print(
            f"{name:<22}"
            f"{format_money(scenario.revenue):>14}"
            f"{format_money(scenario.gross_profit):>16}"
            f"{format_money(scenario.ebitda):>14}"
            f"{format_money(scenario.operating_profit):>14}"
            f"{format_money(scenario.net_profit):>14}"
        )


# =============================================================================
# SECTION 13: OPERATING LEVERAGE
# =============================================================================


def demonstrate_operating_leverage() -> None:
    """
    Demonstrate the effect of fixed costs.

    A business with significant fixed operating costs can experience a large
    increase in operating profit when revenue rises after fixed costs are covered.
    The reverse can also occur when revenue falls.
    """

    print("\n" + "=" * 80)
    print("OPERATING LEVERAGE EXAMPLE")
    print("=" * 80)

    revenue_levels = [
        Decimal("500000"),
        Decimal("750000"),
        Decimal("1000000"),
        Decimal("1250000"),
    ]

    variable_cost_ratio = Decimal("0.45")
    fixed_operating_cost = Decimal("300000")

    print(
        f"{'Revenue':>15}"
        f"{'Variable Cost':>18}"
        f"{'Gross Contribution':>22}"
        f"{'Operating Profit':>20}"
    )
    print("-" * 75)

    for revenue in revenue_levels:
        variable_cost = revenue * variable_cost_ratio
        contribution = revenue - variable_cost
        operating = contribution - fixed_operating_cost

        print(
            f"{format_money(revenue):>15}"
            f"{format_money(variable_cost):>18}"
            f"{format_money(contribution):>22}"
            f"{format_money(operating):>20}"
        )

    print(
        "\nFixed costs create operating leverage. Revenue growth can increase "
        "operating profit faster than revenue when variable costs remain stable."
    )


# =============================================================================
# SECTION 14: BREAK-EVEN ANALYSIS
# =============================================================================


def break_even_revenue(
    fixed_costs: Decimal,
    contribution_margin_ratio: Decimal,
) -> Optional[Decimal]:
    """
    Calculate break-even revenue.

        Break-Even Revenue
        = Fixed Costs / Contribution Margin Ratio

    A contribution margin ratio must be greater than zero.
    """
    if contribution_margin_ratio <= 0:
        return None

    return fixed_costs / contribution_margin_ratio


def demonstrate_break_even() -> None:
    """Demonstrate the relationship between margins and break-even revenue."""

    print("\n" + "=" * 80)
    print("BREAK-EVEN ANALYSIS")
    print("=" * 80)

    selling_price_per_unit = Decimal("100")
    variable_cost_per_unit = Decimal("60")
    fixed_costs = Decimal("200000")

    contribution_per_unit = (
        selling_price_per_unit - variable_cost_per_unit
    )

    contribution_margin_ratio = (
        contribution_per_unit / selling_price_per_unit
    )

    units_required = fixed_costs / contribution_per_unit

    revenue_required = break_even_revenue(
        fixed_costs,
        contribution_margin_ratio,
    )

    print(f"Selling Price Per Unit:       {format_money(selling_price_per_unit)}")
    print(f"Variable Cost Per Unit:       {format_money(variable_cost_per_unit)}")
    print(f"Contribution Per Unit:        {format_money(contribution_per_unit)}")
    print(
        f"Contribution Margin Ratio:    "
        f"{format_percent(contribution_margin_ratio * Decimal('100'))}"
    )
    print(f"Fixed Costs:                  {format_money(fixed_costs)}")
    print(f"Break-Even Units:             {format_money(units_required)}")
    print(f"Break-Even Revenue:           {format_money(revenue_required)}")


# =============================================================================
# SECTION 15: PROFITABILITY COMPARISON BETWEEN BUSINESSES
# =============================================================================


def compare_businesses() -> None:
    """
    Compare businesses with different scales and cost structures.
    """

    print("\n" + "=" * 80)
    print("COMPARING BUSINESSES USING PROFITABILITY METRICS")
    print("=" * 80)

    business_a = IncomeStatement(
        revenue=Decimal("1000000"),
        cost_of_goods_sold=Decimal("300000"),
        selling_expense=Decimal("150000"),
        general_administrative_expense=Decimal("100000"),
        depreciation=Decimal("50000"),
        amortization=Decimal("0"),
        interest_expense=Decimal("30000"),
        income_tax_expense=Decimal("70000"),
    )

    business_b = IncomeStatement(
        revenue=Decimal("5000000"),
        cost_of_goods_sold=Decimal("2500000"),
        selling_expense=Decimal("600000"),
        general_administrative_expense=Decimal("500000"),
        depreciation=Decimal("150000"),
        amortization=Decimal("50000"),
        interest_expense=Decimal("200000"),
        income_tax_expense=Decimal("250000"),
    )

    print(
        f"{'Metric':<24}"
        f"{'Business A':>18}"
        f"{'Business B':>18}"
    )
    print("-" * 60)

    metrics = [
        (
            "Revenue",
            business_a.revenue,
            business_b.revenue,
        ),
        (
            "Gross Margin",
            business_a.gross_margin,
            business_b.gross_margin,
        ),
        (
            "EBITDA Margin",
            business_a.ebitda_margin,
            business_b.ebitda_margin,
        ),
        (
            "Operating Margin",
            business_a.operating_margin,
            business_b.operating_margin,
        ),
        (
            "Net Margin",
            business_a.net_margin,
            business_b.net_margin,
        ),
    ]

    for name, value_a, value_b in metrics:
        if "Margin" in name:
            display_a = format_percent(value_a)
            display_b = format_percent(value_b)
        else:
            display_a = format_money(value_a)
            display_b = format_money(value_b)

        print(
            f"{name:<24}"
            f"{display_a:>18}"
            f"{display_b:>18}"
        )

    print(
        "\nAbsolute profit measures business scale, while margins provide a "
        "relative view of profitability efficiency."
    )


# =============================================================================
# SECTION 16: EDGE CASES AND LOSSES
# =============================================================================


def demonstrate_edge_cases() -> None:
    """Demonstrate unusual but important profitability situations."""

    print("\n" + "=" * 80)
    print("EDGE CASES AND IMPORTANT EXCEPTIONS")
    print("=" * 80)

    # Case 1: Zero revenue.
    zero_revenue = IncomeStatement(
        revenue=Decimal("0"),
        cost_of_goods_sold=Decimal("0"),
        general_administrative_expense=Decimal("50000"),
    )

    print("\nCASE 1: ZERO REVENUE")
    print(f"Gross Profit:       {format_money(zero_revenue.gross_profit)}")
    print(f"Gross Margin:       {format_percent(zero_revenue.gross_margin)}")
    print(
        "A margin is undefined when revenue is zero because division by zero "
        "cannot produce a meaningful profitability percentage."
    )

    # Case 2: Negative gross profit.
    negative_gross = IncomeStatement(
        revenue=Decimal("100000"),
        cost_of_goods_sold=Decimal("120000"),
        general_administrative_expense=Decimal("10000"),
    )

    print("\nCASE 2: NEGATIVE GROSS PROFIT")
    print(f"Revenue:            {format_money(negative_gross.revenue)}")
    print(f"COGS:               {format_money(negative_gross.cost_of_goods_sold)}")
    print(f"Gross Profit:       {format_money(negative_gross.gross_profit)}")
    print(f"Gross Margin:       {format_percent(negative_gross.gross_margin)}")

    # Case 3: Positive EBITDA but negative net profit.
    positive_ebitda_negative_net = IncomeStatement(
        revenue=Decimal("1000000"),
        cost_of_goods_sold=Decimal("400000"),
        general_administrative_expense=Decimal("300000"),
        depreciation=Decimal("50000"),
        interest_expense=Decimal("300000"),
        income_tax_expense=Decimal("0"),
    )

    print("\nCASE 3: POSITIVE EBITDA BUT NEGATIVE NET PROFIT")
    print(f"EBITDA:             {format_money(positive_ebitda_negative_net.ebitda)}")
    print(
        f"Operating Profit:   "
        f"{format_money(positive_ebitda_negative_net.operating_profit)}"
    )
    print(
        f"Net Profit:         "
        f"{format_money(positive_ebitda_negative_net.net_profit)}"
    )

    print(
        "This demonstrates why EBITDA should not be interpreted as equivalent "
        "to final shareholder earnings."
    )


# =============================================================================
# SECTION 17: EBITDA LIMITATIONS
# =============================================================================


def demonstrate_ebitda_limitations() -> None:
    """Explain important analytical limitations through numerical examples."""

    print("\n" + "=" * 80)
    print("EBITDA LIMITATIONS")
    print("=" * 80)

    revenue = Decimal("5000000")
    ebitda = Decimal("1000000")

    annual_capital_expenditure = Decimal("900000")
    annual_interest = Decimal("300000")
    annual_tax = Decimal("150000")

    simplified_remaining_cash = (
        ebitda
        - annual_capital_expenditure
        - annual_interest
        - annual_tax
    )

    print(f"Revenue:                       {format_money(revenue)}")
    print(f"EBITDA:                        {format_money(ebitda)}")
    print(f"Capital Expenditure:           {format_money(annual_capital_expenditure)}")
    print(f"Interest Payments:             {format_money(annual_interest)}")
    print(f"Taxes:                         {format_money(annual_tax)}")
    print(
        f"Simplified Remaining Amount:   "
        f"{format_money(simplified_remaining_cash)}"
    )

    print(
        "\nEBITDA ignores depreciation and amortization in the metric itself, "
        "but asset-intensive businesses may need significant recurring capital "
        "investment to maintain productive capacity."
    )
    print(
        "EBITDA also excludes financing costs and taxes, so it should be "
        "interpreted together with cash flow, capital expenditure requirements, "
        "debt obligations, and the complete financial statements."
    )


# =============================================================================
# SECTION 18: TAX RATE ANALYSIS
# =============================================================================


def effective_tax_rate(
    profit_before_tax: Decimal,
    income_tax_expense: Decimal,
) -> Optional[Decimal]:
    """
    Calculate effective tax rate.

        Effective Tax Rate = Tax Expense / Profit Before Tax × 100

    The result may be difficult to interpret when profit before tax is zero
    or negative.
    """
    if profit_before_tax <= 0:
        return None

    return (
        income_tax_expense
        / profit_before_tax
        * Decimal("100")
    )


def demonstrate_tax_analysis(statement: IncomeStatement) -> None:
    """Demonstrate effective tax rate analysis."""

    print("\n" + "=" * 80)
    print("TAX AND NET PROFIT ANALYSIS")
    print("=" * 80)

    rate = effective_tax_rate(
        statement.profit_before_tax,
        statement.income_tax_expense,
    )

    print(
        f"Profit Before Tax:      "
        f"{format_money(statement.profit_before_tax)}"
    )
    print(
        f"Income Tax Expense:     "
        f"{format_money(statement.income_tax_expense)}"
    )
    print(
        f"Effective Tax Rate:     "
        f"{format_percent(rate)}"
    )
    print(
        f"Net Profit:             "
        f"{format_money(statement.net_profit)}"
    )


# =============================================================================
# SECTION 19: DATA VALIDATION AND COMMON MISTAKES
# =============================================================================


def demonstrate_validation() -> None:
    """Demonstrate validation errors and safe handling."""

    print("\n" + "=" * 80)
    print("VALIDATION AND COMMON DATA ERRORS")
    print("=" * 80)

    try:
        IncomeStatement(
            revenue=Decimal("100000"),
            cost_of_goods_sold=Decimal("-10000"),
        )
    except ValueError as error:
        print(f"Invalid expense input detected: {error}")

    try:
        to_decimal("not-a-number")
    except ValueError as error:
        print(f"Invalid numeric input detected: {error}")

    print(
        "\nCommon mistakes include:"
    )
    print(
        "1. Treating EBITDA as equivalent to cash flow."
    )
    print(
        "2. Comparing gross margins across businesses with different accounting "
        "classifications without checking the definition of COGS."
    )
    print(
        "3. Assuming operating profit and EBIT are always presented identically."
    )
    print(
        "4. Ignoring one-time income or expenses when evaluating recurring profit."
    )
    print(
        "5. Comparing net margins without considering differences in debt and tax."
    )
    print(
        "6. Using percentages without checking whether the denominator is zero."
    )


# =============================================================================
# SECTION 20: ADVANCED METRIC INTERPRETATION
# =============================================================================


def analyze_profitability_quality(statement: IncomeStatement) -> List[str]:
    """
    Produce simple rule-based observations.

    This is educational logic, not an investment recommendation or accounting
    opinion. Real analysis requires industry context and audited disclosures.
    """

    observations: List[str] = []

    if statement.gross_margin is not None:
        if statement.gross_margin < Decimal("20"):
            observations.append(
                "Low gross margin indicates a relatively high direct cost burden."
            )
        elif statement.gross_margin > Decimal("60"):
            observations.append(
                "High gross margin indicates substantial revenue remaining after COGS."
            )

    if (
        statement.ebitda_margin is not None
        and statement.operating_margin is not None
    ):
        margin_gap = (
            statement.ebitda_margin
            - statement.operating_margin
        )

        if margin_gap > Decimal("10"):
            observations.append(
                "A large EBITDA-to-operating-margin gap suggests depreciation "
                "and amortization are materially affecting operating profit."
            )

    if (
        statement.operating_profit > 0
        and statement.net_profit < 0
    ):
        observations.append(
            "Positive operating performance is being offset by non-operating "
            "costs, taxes, or other expenses."
        )

    if (
        statement.gross_margin is not None
        and statement.net_margin is not None
        and statement.gross_margin - statement.net_margin > Decimal("30")
    ):
        observations.append(
            "A large difference between gross and net margins indicates that "
            "operating, financing, tax, or other costs materially reduce final profit."
        )

    if not observations:
        observations.append(
            "No simple rule-based warning was triggered by the selected thresholds."
        )

    return observations


def demonstrate_profitability_quality_analysis(
    statement: IncomeStatement,
) -> None:
    """Display analytical observations."""

    print("\n" + "=" * 80)
    print("PROFITABILITY QUALITY OBSERVATIONS")
    print("=" * 80)

    for observation in analyze_profitability_quality(statement):
        print(f"- {observation}")


# =============================================================================
# SECTION 21: SIMPLE TESTS
# =============================================================================


def run_tests() -> None:
    """
    Run lightweight tests.

    Financial software in production should normally use a comprehensive testing
    framework and should validate accounting rules, source data, permissions,
    audit trails, and reporting requirements.
    """

    print("\n" + "=" * 80)
    print("BASIC CALCULATION TESTS")
    print("=" * 80)

    assert gross_profit(
        Decimal("1000"),
        Decimal("400"),
    ) == Decimal("600")

    assert calculate_ebitda(
        Decimal("500"),
        Decimal("100"),
        Decimal("50"),
    ) == Decimal("650")

    test_statement = IncomeStatement(
        revenue=Decimal("1000"),
        cost_of_goods_sold=Decimal("400"),
        general_administrative_expense=Decimal("200"),
        depreciation=Decimal("50"),
        amortization=Decimal("25"),
        interest_expense=Decimal("25"),
        income_tax_expense=Decimal("50"),
    )

    assert test_statement.gross_profit == Decimal("600")
    assert test_statement.ebitda == Decimal("400")
    assert test_statement.operating_profit == Decimal("325")
    assert test_statement.net_profit == Decimal("250")

    assert calculate_margin(
        Decimal("250"),
        Decimal("1000"),
    ) == Decimal("25")

    assert calculate_margin(
        Decimal("250"),
        Decimal("0"),
    ) is None

    print("All basic tests passed.")


# =============================================================================
# SECTION 22: PRODUCTION CONSIDERATIONS
# =============================================================================


def demonstrate_production_considerations() -> None:
    """
    Present practical considerations for implementing profitability calculations
    in real software systems.
    """

    print("\n" + "=" * 80)
    print("PRODUCTION AND IMPLEMENTATION CONSIDERATIONS")
    print("=" * 80)

    considerations = [
        (
            "Precision",
            "Use Decimal or integer minor currency units instead of binary "
            "floating-point values for monetary calculations.",
        ),
        (
            "Accounting Definitions",
            "Do not assume that EBITDA, operating profit, COGS, or adjusted "
            "metrics have identical definitions across organizations.",
        ),
        (
            "Data Quality",
            "Validate missing values, duplicate transactions, incorrect signs, "
            "period mismatches, and inconsistent currencies.",
        ),
        (
            "Currency",
            "Separate local currency reporting from exchange-rate conversion and "
            "document the exchange rate and conversion date.",
        ),
        (
            "Auditability",
            "Retain source references, calculation inputs, timestamps, and "
            "transformation history for financial reporting systems.",
        ),
        (
            "Security",
            "Restrict access to sensitive financial data and avoid exposing "
            "financial records through logs or error messages.",
        ),
        (
            "Performance",
            "For large financial datasets, avoid repeatedly recalculating "
            "aggregates and use database aggregation or efficient data pipelines.",
        ),
        (
            "Reconciliation",
            "Reconcile calculated metrics against approved financial statements "
            "and investigate differences caused by classification or timing.",
        ),
        (
            "Testing",
            "Test positive values, losses, zero revenue, unusual adjustments, "
            "rounding boundaries, and invalid source data.",
        ),
    ]

    for title, description in considerations:
        print(f"{title}: {description}")


# =============================================================================
# SECTION 23: MAIN PROGRAM
# =============================================================================


def main() -> None:
    """Run the complete profitability tutorial."""

    print("=" * 80)
    print("PROFITABILITY METRICS")
    print("Gross Profit | EBITDA | Operating Profit | Net Profit")
    print("=" * 80)

    demonstrate_basic_profitability()
    demonstrate_gross_profit_concepts()
    demonstrate_ebitda_vs_operating_profit()
    demonstrate_interest_impact()

    sample_statement = create_sample_income_statement()

    sample_statement.print_statement()
    demonstrate_profitability_margins(sample_statement)
    demonstrate_vertical_analysis(sample_statement)

    previous_period = ProfitabilityPeriod(
        name="Year 1",
        statement=IncomeStatement(
            revenue=Decimal("8500000"),
            cost_of_goods_sold=Decimal("3900000"),
            selling_expense=Decimal("800000"),
            general_administrative_expense=Decimal("850000"),
            research_and_development_expense=Decimal("250000"),
            other_cash_operating_expenses=Decimal("220000"),
            depreciation=Decimal("350000"),
            amortization=Decimal("90000"),
            interest_income=Decimal("40000"),
            interest_expense=Decimal("280000"),
            other_income=Decimal("50000"),
            other_expenses=Decimal("20000"),
            income_tax_expense=Decimal("600000"),
        ),
    )

    current_period = ProfitabilityPeriod(
        name="Year 2",
        statement=sample_statement,
    )

    compare_periods(
        previous_period,
        current_period,
    )

    demonstrate_scenarios(sample_statement)
    demonstrate_operating_leverage()
    demonstrate_break_even()
    compare_businesses()
    demonstrate_edge_cases()
    demonstrate_ebitda_limitations()
    demonstrate_tax_analysis(sample_statement)
    demonstrate_validation()
    demonstrate_profitability_quality_analysis(sample_statement)
    run_tests()
    demonstrate_production_considerations()


if __name__ == "__main__":
    main()
