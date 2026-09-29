"""
Excel What-If Analysis: Scenario Manager, Goal Seek, and Sensitivity Analysis

This standalone study file teaches the core ideas behind Excel What-If Analysis
while implementing equivalent techniques in pure Python:

1. Scenario Manager
2. Goal Seek
3. One-variable sensitivity analysis
4. Two-variable sensitivity analysis
5. Data-table-style analysis
6. Financial modeling
7. Validation, edge cases, numerical stability, and performance
8. Advanced scenario comparison and sensitivity metrics

The examples use a hypothetical investment/project model:

    Revenue = Units Sold * Price per Unit
    Variable Cost = Units Sold * Variable Cost per Unit
    Gross Profit = Revenue - Variable Cost
    Operating Profit = Gross Profit - Fixed Costs
    Tax = max(0, Operating Profit * Tax Rate)
    Net Profit = Operating Profit - Tax
    ROI = Net Profit / Initial Investment

No external packages are required.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Iterable, Optional
import math
import statistics


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL MODEL
# ---------------------------------------------------------------------------

@dataclass
class ModelInputs:
    """Input assumptions that can be changed during What-If Analysis."""
    units_sold: float = 10_000
    price_per_unit: float = 50.0
    variable_cost_per_unit: float = 28.0
    fixed_costs: float = 100_000.0
    tax_rate: float = 0.25
    initial_investment: float = 250_000.0


@dataclass
class ModelOutputs:
    """Calculated outputs from the model."""
    revenue: float
    variable_cost: float
    gross_profit: float
    operating_profit: float
    tax: float
    net_profit: float
    roi: float
    break_even_units: Optional[float]


def validate_inputs(inputs: ModelInputs) -> None:
    """Validate assumptions before calculations are performed."""
    if inputs.units_sold < 0:
        raise ValueError("Units sold cannot be negative.")
    if inputs.price_per_unit < 0:
        raise ValueError("Price per unit cannot be negative.")
    if inputs.variable_cost_per_unit < 0:
        raise ValueError("Variable cost per unit cannot be negative.")
    if inputs.fixed_costs < 0:
        raise ValueError("Fixed costs cannot be negative.")
    if not 0 <= inputs.tax_rate <= 1:
        raise ValueError("Tax rate must be between 0 and 1.")
    if inputs.initial_investment <= 0:
        raise ValueError("Initial investment must be greater than zero.")


def calculate_model(inputs: ModelInputs) -> ModelOutputs:
    """
    Calculate all dependent values.

    This is equivalent to an Excel worksheet whose formulas reference
    assumption cells. What-If Analysis changes the assumptions and observes
    how these formulas respond.
    """
    validate_inputs(inputs)

    revenue = inputs.units_sold * inputs.price_per_unit
    variable_cost = inputs.units_sold * inputs.variable_cost_per_unit
    gross_profit = revenue - variable_cost
    operating_profit = gross_profit - inputs.fixed_costs

    # A simple model assumes tax is not negative when there is a loss.
    tax = max(0.0, operating_profit * inputs.tax_rate)
    net_profit = operating_profit - tax
    roi = net_profit / inputs.initial_investment

    contribution_margin_per_unit = (
        inputs.price_per_unit - inputs.variable_cost_per_unit
    )

    if contribution_margin_per_unit > 0:
        break_even_units = inputs.fixed_costs / contribution_margin_per_unit
    else:
        break_even_units = None

    return ModelOutputs(
        revenue=revenue,
        variable_cost=variable_cost,
        gross_profit=gross_profit,
        operating_profit=operating_profit,
        tax=tax,
        net_profit=net_profit,
        roi=roi,
        break_even_units=break_even_units,
    )


def print_outputs(label: str, outputs: ModelOutputs) -> None:
    """Print a model result in a readable form."""
    print(f"\n--- {label} ---")
    print(f"Revenue:             ${outputs.revenue:,.2f}")
    print(f"Variable Cost:       ${outputs.variable_cost:,.2f}")
    print(f"Gross Profit:        ${outputs.gross_profit:,.2f}")
    print(f"Operating Profit:    ${outputs.operating_profit:,.2f}")
    print(f"Tax:                 ${outputs.tax:,.2f}")
    print(f"Net Profit:          ${outputs.net_profit:,.2f}")
    print(f"ROI:                 {outputs.roi:.2%}")

    if outputs.break_even_units is None:
        print("Break-even Units:    Not achievable")
    else:
        print(f"Break-even Units:    {outputs.break_even_units:,.2f}")


# ---------------------------------------------------------------------------
# 2. BASE CASE
# ---------------------------------------------------------------------------

def base_case_demo() -> None:
    inputs = ModelInputs()
    outputs = calculate_model(inputs)
    print_outputs("BASE CASE", outputs)


# ---------------------------------------------------------------------------
# 3. SCENARIO MANAGER
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    """
    A named collection of input assumptions.

    This corresponds conceptually to an Excel Scenario Manager scenario.
    """
    name: str
    changes: dict[str, float]


class ScenarioManager:
    """Store, validate, execute, and compare named scenarios."""

    def __init__(self, base_inputs: ModelInputs):
        self.base_inputs = base_inputs
        self.scenarios: dict[str, Scenario] = {}

    def add_scenario(self, name: str, **changes: float) -> None:
        if not name.strip():
            raise ValueError("Scenario name cannot be empty.")

        valid_fields = set(asdict(self.base_inputs))
        unknown_fields = set(changes) - valid_fields

        if unknown_fields:
            raise ValueError(
                f"Unknown input fields: {', '.join(sorted(unknown_fields))}"
            )

        self.scenarios[name] = Scenario(name, changes)

    def apply_scenario(self, scenario: Scenario) -> ModelInputs:
        values = asdict(self.base_inputs)
        values.update(scenario.changes)
        return ModelInputs(**values)

    def evaluate(self, name: str) -> ModelOutputs:
        if name not in self.scenarios:
            raise KeyError(f"Scenario not found: {name}")
        inputs = self.apply_scenario(self.scenarios[name])
        return calculate_model(inputs)

    def compare(self) -> dict[str, ModelOutputs]:
        return {
            name: self.evaluate(name)
            for name in self.scenarios
        }


def scenario_manager_demo() -> None:
    manager = ScenarioManager(ModelInputs())

    # These correspond to alternative business assumptions.
    manager.add_scenario(
        "Base",
        units_sold=10_000,
        price_per_unit=50,
        variable_cost_per_unit=28,
    )

    manager.add_scenario(
        "Optimistic",
        units_sold=13_000,
        price_per_unit=55,
        variable_cost_per_unit=26,
    )

    manager.add_scenario(
        "Conservative",
        units_sold=8_000,
        price_per_unit=47,
        variable_cost_per_unit=30,
    )

    print("\n\n================ SCENARIO MANAGER ================")

    for name, outputs in manager.compare().items():
        print_outputs(name, outputs)

    print("\nScenario ROI comparison:")
    for name, outputs in manager.compare().items():
        print(f"{name:15s} {outputs.roi:8.2%}")


# ---------------------------------------------------------------------------
# 4. GOAL SEEK
# ---------------------------------------------------------------------------

def goal_seek(
    model_factory: Callable[[float], float],
    target: float,
    lower: float,
    upper: float,
    tolerance: float = 1e-8,
    max_iterations: int = 200,
) -> float:
    """
    Find x such that model_factory(x) is approximately target.

    This uses bisection, a robust root-finding technique.

    Goal Seek in a spreadsheet normally changes one input until one formula
    reaches a desired result. Bisection is appropriate when the function is
    continuous and the target is bracketed by the lower and upper bounds.
    """
    if lower >= upper:
        raise ValueError("Lower bound must be smaller than upper bound.")

    f_lower = model_factory(lower) - target
    f_upper = model_factory(upper) - target

    if abs(f_lower) <= tolerance:
        return lower
    if abs(f_upper) <= tolerance:
        return upper

    # Bisection requires opposite signs.
    if f_lower * f_upper > 0:
        raise ValueError(
            "Goal cannot be bracketed. Try different lower and upper bounds."
        )

    for _ in range(max_iterations):
        midpoint = (lower + upper) / 2
        f_mid = model_factory(midpoint) - target

        if abs(f_mid) <= tolerance:
            return midpoint

        if f_lower * f_mid <= 0:
            upper = midpoint
            f_upper = f_mid
        else:
            lower = midpoint
            f_lower = f_mid

        if abs(upper - lower) <= tolerance:
            return (lower + upper) / 2

    return (lower + upper) / 2


def goal_seek_demo() -> None:
    print("\n\n================ GOAL SEEK ================")

    base = ModelInputs()

    # Question:
    # How many units must be sold to achieve $100,000 net profit?
    target_profit = 100_000.0

    def profit_from_units(units: float) -> float:
        candidate = ModelInputs(
            units_sold=units,
            price_per_unit=base.price_per_unit,
            variable_cost_per_unit=base.variable_cost_per_unit,
            fixed_costs=base.fixed_costs,
            tax_rate=base.tax_rate,
            initial_investment=base.initial_investment,
        )
        return calculate_model(candidate).net_profit

    units_required = goal_seek(
        profit_from_units,
        target=target_profit,
        lower=0,
        upper=100_000,
    )

    print(f"Target net profit: ${target_profit:,.2f}")
    print(f"Required units:    {units_required:,.2f}")
    print(f"Resulting profit:  ${profit_from_units(units_required):,.2f}")


# ---------------------------------------------------------------------------
# 5. GOAL SEEK WITH A PRICE VARIABLE
# ---------------------------------------------------------------------------

def price_goal_seek_demo() -> None:
    print("\n\n================ PRICE GOAL SEEK ================")

    base = ModelInputs()
    target_roi = 0.40

    def roi_from_price(price: float) -> float:
        candidate = ModelInputs(
            units_sold=base.units_sold,
            price_per_unit=price,
            variable_cost_per_unit=base.variable_cost_per_unit,
            fixed_costs=base.fixed_costs,
            tax_rate=base.tax_rate,
            initial_investment=base.initial_investment,
        )
        return calculate_model(candidate).roi

    required_price = goal_seek(
        roi_from_price,
        target=target_roi,
        lower=base.variable_cost_per_unit + 0.01,
        upper=200,
    )

    print(f"Target ROI:       {target_roi:.2%}")
    print(f"Required price:   ${required_price:,.2f}")
    print(f"Resulting ROI:    {roi_from_price(required_price):.2%}")


# ---------------------------------------------------------------------------
# 6. ONE-VARIABLE SENSITIVITY ANALYSIS
# ---------------------------------------------------------------------------

def one_variable_sensitivity(
    base_inputs: ModelInputs,
    field_name: str,
    values: Iterable[float],
    output_selector: Callable[[ModelOutputs], float],
) -> list[tuple[float, float]]:
    """
    Change one assumption while holding all other assumptions constant.

    This resembles a one-variable Excel data table.
    """
    if field_name not in asdict(base_inputs):
        raise ValueError(f"Unknown model input: {field_name}")

    results = []

    for value in values:
        values_dict = asdict(base_inputs)
        values_dict[field_name] = value

        candidate = ModelInputs(**values_dict)
        output = output_selector(calculate_model(candidate))
        results.append((value, output))

    return results


def one_variable_demo() -> None:
    print("\n\n================ ONE-VARIABLE SENSITIVITY ================")

    base = ModelInputs()
    prices = [40, 45, 50, 55, 60, 65]

    results = one_variable_sensitivity(
        base,
        "price_per_unit",
        prices,
        lambda result: result.net_profit,
    )

    print("Price        Net Profit")
    print("-----------------------")
    for price, profit in results:
        print(f"${price:7.2f}    ${profit:12,.2f}")


# ---------------------------------------------------------------------------
# 7. TWO-VARIABLE SENSITIVITY ANALYSIS
# ---------------------------------------------------------------------------

def two_variable_sensitivity(
    base_inputs: ModelInputs,
    row_field: str,
    row_values: Iterable[float],
    column_field: str,
    column_values: Iterable[float],
    output_selector: Callable[[ModelOutputs], float],
) -> list[list[float]]:
    """
    Evaluate combinations of two assumptions.

    This is conceptually similar to Excel's two-variable data table.
    """
    fields = set(asdict(base_inputs))

    if row_field not in fields or column_field not in fields:
        raise ValueError("One or both sensitivity fields are invalid.")

    if row_field == column_field:
        raise ValueError("Row and column variables must be different.")

    matrix = []

    for row_value in row_values:
        row_results = []

        for column_value in column_values:
            values = asdict(base_inputs)
            values[row_field] = row_value
            values[column_field] = column_value

            candidate = ModelInputs(**values)
            output = output_selector(calculate_model(candidate))
            row_results.append(output)

        matrix.append(row_results)

    return matrix


def two_variable_demo() -> None:
    print("\n\n================ TWO-VARIABLE SENSITIVITY ================")

    base = ModelInputs()

    unit_values = [7_500, 10_000, 12_500, 15_000]
    price_values = [45, 50, 55, 60]

    matrix = two_variable_sensitivity(
        base,
        row_field="units_sold",
        row_values=unit_values,
        column_field="price_per_unit",
        column_values=price_values,
        output_selector=lambda result: result.net_profit,
    )

    print("\nNet profit by units sold and price:")
    print("Units \\ Price", end="")
    for price in price_values:
        print(f"{price:>14.0f}", end="")
    print()

    for units, row in zip(unit_values, matrix):
        print(f"{units:>12,}", end="")
        for value in row:
            print(f"{value:>14,.0f}", end="")
        print()


# ---------------------------------------------------------------------------
# 8. SENSITIVITY METRICS
# ---------------------------------------------------------------------------

def percent_change(old: float, new: float) -> Optional[float]:
    """Calculate percentage change while safely handling zero."""
    if old == 0:
        return None
    return (new - old) / abs(old)


def elasticity(
    base_input: float,
    changed_input: float,
    base_output: float,
    changed_output: float,
) -> Optional[float]:
    """
    Approximate output elasticity:

        % change in output / % change in input

    Values above 1 in absolute magnitude indicate a proportionally larger
    output response than the input change.
    """
    input_change = percent_change(base_input, changed_input)
    output_change = percent_change(base_output, changed_output)

    if input_change is None or input_change == 0 or output_change is None:
        return None

    return output_change / input_change


def sensitivity_metric_demo() -> None:
    print("\n\n================ SENSITIVITY METRICS ================")

    base = ModelInputs()
    base_result = calculate_model(base)

    changed = ModelInputs(
        units_sold=11_000,
        price_per_unit=base.price_per_unit,
        variable_cost_per_unit=base.variable_cost_per_unit,
        fixed_costs=base.fixed_costs,
        tax_rate=base.tax_rate,
        initial_investment=base.initial_investment,
    )

    changed_result = calculate_model(changed)

    e = elasticity(
        base.units_sold,
        changed.units_sold,
        base_result.net_profit,
        changed_result.net_profit,
    )

    print(f"Base net profit:       ${base_result.net_profit:,.2f}")
    print(f"Changed net profit:    ${changed_result.net_profit:,.2f}")
    print(f"Units change:          {percent_change(base.units_sold, changed.units_sold):.2%}")
    print(f"Profit change:         {percent_change(base_result.net_profit, changed_result.net_profit):.2%}")
    print(f"Approx. elasticity:    {e:.4f}" if e is not None else "Elasticity unavailable")


# ---------------------------------------------------------------------------
# 9. BREAK-EVEN ANALYSIS
# ---------------------------------------------------------------------------

def break_even_demo() -> None:
    print("\n\n================ BREAK-EVEN ANALYSIS ================")

    base = ModelInputs()
    result = calculate_model(base)

    print(f"Break-even units: {result.break_even_units:,.2f}")

    if result.break_even_units is not None:
        break_even_revenue = result.break_even_units * base.price_per_unit
        print(f"Break-even revenue: ${break_even_revenue:,.2f}")


# ---------------------------------------------------------------------------
# 10. SCENARIO RANGE AND STATISTICS
# ---------------------------------------------------------------------------

def scenario_statistics_demo() -> None:
    print("\n\n================ SCENARIO STATISTICS ================")

    manager = ScenarioManager(ModelInputs())

    manager.add_scenario("Downside", units_sold=7_000, price_per_unit=45)
    manager.add_scenario("Base", units_sold=10_000, price_per_unit=50)
    manager.add_scenario("Growth", units_sold=13_000, price_per_unit=55)
    manager.add_scenario("Expansion", units_sold=16_000, price_per_unit=58)

    profits = [
        result.net_profit
        for result in manager.compare().values()
    ]

    print(f"Minimum profit: ${min(profits):,.2f}")
    print(f"Maximum profit: ${max(profits):,.2f}")
    print(f"Mean profit:    ${statistics.mean(profits):,.2f}")
    print(f"Median profit:  ${statistics.median(profits):,.2f}")


# ---------------------------------------------------------------------------
# 11. MONTE CARLO-STYLE SENSITIVITY EXAMPLE
# ---------------------------------------------------------------------------

def deterministic_grid_analysis() -> None:
    """
    A dependency-free alternative to random Monte Carlo simulation.

    The grid deliberately explores combinations of key assumptions. In a
    spreadsheet this can be implemented with data tables or scenario grids.
    """
    print("\n\n================ GRID-BASED RISK ANALYSIS ================")

    base = ModelInputs()

    unit_multipliers = [0.80, 0.90, 1.00, 1.10, 1.20]
    price_multipliers = [0.90, 0.95, 1.00, 1.05, 1.10]

    profits = []

    for unit_multiplier in unit_multipliers:
        for price_multiplier in price_multipliers:
            candidate = ModelInputs(
                units_sold=base.units_sold * unit_multiplier,
                price_per_unit=base.price_per_unit * price_multiplier,
                variable_cost_per_unit=base.variable_cost_per_unit,
                fixed_costs=base.fixed_costs,
                tax_rate=base.tax_rate,
                initial_investment=base.initial_investment,
            )

            profits.append(calculate_model(candidate).net_profit)

    print(f"Grid combinations: {len(profits)}")
    print(f"Minimum profit:    ${min(profits):,.2f}")
    print(f"Maximum profit:    ${max(profits):,.2f}")
    print(f"Average profit:    ${statistics.mean(profits):,.2f}")

    profitable_cases = sum(profit > 0 for profit in profits)
    probability_like_ratio = profitable_cases / len(profits)

    print(f"Profitable cases:  {profitable_cases}/{len(profits)}")
    print(f"Grid success rate: {probability_like_ratio:.2%}")

    # Important limitation:
    # A grid ratio is not automatically a true probability. It becomes
    # probabilistic only when the scenarios are assigned appropriate weights
    # or sampled according to a probability distribution.


# ---------------------------------------------------------------------------
# 12. EDGE CASES
# ---------------------------------------------------------------------------

def edge_case_demo() -> None:
    print("\n\n================ EDGE CASES ================")

    # Case 1: Zero units.
    zero_sales = ModelInputs(units_sold=0)
    result = calculate_model(zero_sales)
    print(f"Zero sales net profit: ${result.net_profit:,.2f}")

    # Case 2: Price equals variable cost.
    # Contribution margin is zero, so fixed costs can never be recovered.
    zero_margin = ModelInputs(
        price_per_unit=30,
        variable_cost_per_unit=30,
    )
    result = calculate_model(zero_margin)
    print(
        "Zero contribution margin break-even:",
        result.break_even_units,
    )

    # Case 3: Invalid tax rate.
    try:
        invalid = ModelInputs(tax_rate=1.5)
        calculate_model(invalid)
    except ValueError as error:
        print(f"Validation error correctly caught: {error}")

    # Case 4: Invalid investment.
    try:
        invalid = ModelInputs(initial_investment=0)
        calculate_model(invalid)
    except ValueError as error:
        print(f"Validation error correctly caught: {error}")


# ---------------------------------------------------------------------------
# 13. GOAL SEEK FAILURE CONDITIONS
# ---------------------------------------------------------------------------

def goal_seek_failure_demo() -> None:
    print("\n\n================ GOAL SEEK FAILURE CONDITIONS ================")

    def quadratic(x: float) -> float:
        return x * x

    # Target 10 cannot be bracketed by [1, 2], because both endpoints
    # produce values below 10.
    try:
        goal_seek(quadratic, target=10, lower=1, upper=2)
    except ValueError as error:
        print(f"Expected failure: {error}")

    # A valid bracket.
    solution = goal_seek(quadratic, target=10, lower=0, upper=5)
    print(f"sqrt(10) found approximately as: {solution:.8f}")


# ---------------------------------------------------------------------------
# 14. DISCOUNTED CASH FLOW SENSITIVITY
# ---------------------------------------------------------------------------

def present_value(cash_flow: float, discount_rate: float, period: int) -> float:
    """Present value of a future cash flow."""
    if discount_rate <= -1:
        raise ValueError("Discount rate must be greater than -100%.")
    return cash_flow / ((1 + discount_rate) ** period)


def npv(cash_flows: list[float], discount_rate: float) -> float:
    """Net present value where cash_flows[0] occurs at time zero."""
    return sum(
        present_value(cash_flow, discount_rate, period)
        for period, cash_flow in enumerate(cash_flows)
    )


def dcf_sensitivity_demo() -> None:
    print("\n\n================ DCF SENSITIVITY ================")

    cash_flows = [-250_000, 80_000, 100_000, 120_000, 140_000]

    discount_rates = [0.06, 0.08, 0.10, 0.12, 0.14]

    for rate in discount_rates:
        value = npv(cash_flows, rate)
        print(f"Discount rate {rate:.2%}: NPV ${value:,.2f}")

    # This is an important What-If Analysis pattern:
    # one assumption changes while the other model assumptions remain fixed.


# ---------------------------------------------------------------------------
# 15. LOCAL SENSITIVITY USING FINITE DIFFERENCES
# ---------------------------------------------------------------------------

def numerical_derivative(
    function: Callable[[float], float],
    x: float,
    step: float = 1e-5,
) -> float:
    """
    Central finite difference approximation:

        f'(x) ≈ [f(x+h) - f(x-h)] / 2h
    """
    if step <= 0:
        raise ValueError("Step must be positive.")

    return (function(x + step) - function(x - step)) / (2 * step)


def derivative_demo() -> None:
    print("\n\n================ NUMERICAL SENSITIVITY ================")

    # Profit as a function of price.
    base = ModelInputs()

    def profit_from_price(price: float) -> float:
        candidate = ModelInputs(
            units_sold=base.units_sold,
            price_per_unit=price,
            variable_cost_per_unit=base.variable_cost_per_unit,
            fixed_costs=base.fixed_costs,
            tax_rate=base.tax_rate,
            initial_investment=base.initial_investment,
        )
        return calculate_model(candidate).net_profit

    derivative = numerical_derivative(
        profit_from_price,
        base.price_per_unit,
        step=0.01,
    )

    print(
        "Approximate change in net profit for one additional unit "
        f"of price: ${derivative:,.2f}"
    )


# ---------------------------------------------------------------------------
# 16. COMPARING SCENARIOS AGAINST BASE
# ---------------------------------------------------------------------------

def scenario_delta_demo() -> None:
    print("\n\n================ SCENARIO DELTAS ================")

    base = ModelInputs()
    base_output = calculate_model(base)

    scenarios = {
        "Lower Demand": ModelInputs(units_sold=8_000),
        "Higher Demand": ModelInputs(units_sold=12_000),
        "Higher Price": ModelInputs(price_per_unit=55),
        "Higher Cost": ModelInputs(variable_cost_per_unit=32),
    }

    for name, inputs in scenarios.items():
        result = calculate_model(inputs)
        delta = result.net_profit - base_output.net_profit
        relative = percent_change(base_output.net_profit, result.net_profit)

        print(f"\n{name}")
        print(f"Net profit: ${result.net_profit:,.2f}")
        print(f"Change:     ${delta:,.2f}")

        if relative is None:
            print("Relative change: undefined")
        else:
            print(f"Relative change: {relative:.2%}")


# ---------------------------------------------------------------------------
# 17. PRACTICAL MODELING RULES
# ---------------------------------------------------------------------------

def modeling_rules_demo() -> None:
    print("\n\n================ MODELING RULES ================")

    rules = [
        "Keep assumptions separate from formulas.",
        "Give each scenario a clear name.",
        "Change one variable at a time for isolated sensitivity analysis.",
        "Use two-variable tables when interactions matter.",
        "Validate inputs before running calculations.",
        "Check whether Goal Seek has a valid solution range.",
        "Do not confuse scenario grids with probability distributions.",
        "Document units, percentages, and time periods.",
        "Check formulas against independent calculations.",
        "Use sensitivity analysis to identify assumptions requiring attention.",
    ]

    for number, rule in enumerate(rules, start=1):
        print(f"{number:02d}. {rule}")


# ---------------------------------------------------------------------------
# 18. MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("EXCEL WHAT-IF ANALYSIS STUDY IMPLEMENTATION")
    print("Scenario Manager | Goal Seek | Sensitivity Analysis")
    print("=" * 72)

    base_case_demo()
    scenario_manager_demo()
    goal_seek_demo()
    price_goal_seek_demo()
    one_variable_demo()
    two_variable_demo()
    sensitivity_metric_demo()
    break_even_demo()
    scenario_statistics_demo()
    deterministic_grid_analysis()
    edge_case_demo()
    goal_seek_failure_demo()
    dcf_sensitivity_demo()
    derivative_demo()
    scenario_delta_demo()
    modeling_rules_demo()

    print("\n\nStudy implementation completed successfully.")


if __name__ == "__main__":
    main()
