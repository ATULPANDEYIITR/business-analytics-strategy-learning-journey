# Excel What-If Analysis: Scenario Manager, Goal Seek, and Sensitivity Analysis

## 1. Topic Introduction

Excel What-If Analysis is a collection of techniques for studying how changes in assumptions affect calculated results.

The central idea is simple:

- Inputs represent assumptions.
- Formulas transform those inputs into outputs.
- What-If Analysis changes selected inputs.
- The resulting outputs are compared to the original or to a target.

Three major Excel techniques are:

1. **Scenario Manager**: compares named sets of assumptions.
2. **Goal Seek**: changes one input until a formula reaches a specified target.
3. **Sensitivity analysis**: measures how an output responds to changes in one or more assumptions.

These techniques are especially useful in financial modeling, budgeting, pricing, investment analysis, business planning, project evaluation, operations, and decision support.

The implementations in this study use a common financial model:

- Units sold
- Price per unit
- Variable cost per unit
- Fixed costs
- Tax rate
- Initial investment

The resulting calculations include:

- Revenue
- Variable cost
- Gross profit
- Operating profit
- Tax
- Net profit
- ROI
- Break-even units

The Python and JavaScript implementations emphasize reusable modeling techniques. The C++ implementation turns the same concepts into a structured technical case study.

---

## 2. Fundamental Concepts

### 2.1 Input

An input is an assumption that can be changed.

Examples include:

- Units sold = 10,000
- Price per unit = $50
- Variable cost per unit = $28
- Fixed costs = $100,000
- Tax rate = 25%
- Initial investment = $250,000

In Excel, these would normally be stored in dedicated assumption cells.

### 2.2 Formula

A formula transforms inputs into outputs.

The model uses:

`Revenue = Units Sold × Price per Unit`

`Variable Cost = Units Sold × Variable Cost per Unit`

`Gross Profit = Revenue − Variable Cost`

`Operating Profit = Gross Profit − Fixed Costs`

`Tax = max(0, Operating Profit × Tax Rate)`

`Net Profit = Operating Profit − Tax`

`ROI = Net Profit / Initial Investment`

### 2.3 What-If Analysis

What-If Analysis does not necessarily change the underlying business logic. Instead, it changes assumptions and observes the consequences.

For example, a model can answer:

- What happens if demand falls by 20%?
- What happens if the selling price rises?
- What price is required to achieve a 40% ROI?
- How does profit change when both demand and price change?
- At what sales volume does the project break even?

---

## 3. Scenario Manager

### 3.1 Definition

Scenario Manager organizes different combinations of input assumptions into named scenarios.

A scenario might contain:

- Units sold
- Price
- Variable cost
- Fixed costs
- Tax rate

For example:

| Scenario | Units | Price | Variable Cost |
|---|---:|---:|---:|
| Conservative | 8,000 | $47 | $30 |
| Base | 10,000 | $50 | $28 |
| Optimistic | 13,000 | $55 | $26 |

The purpose is not to identify a universally correct scenario. It is to make alternative assumptions explicit and comparable.

### 3.2 Scenario Manager in the Python Implementation

The Python implementation defines:

- `Scenario`
- `ScenarioManager`
- `ModelInputs`
- `ModelOutputs`

`ScenarioManager` stores named scenarios and applies their changed assumptions to a base model.

The important conceptual separation is:

`ModelInputs -> Calculation -> ModelOutputs`

A scenario changes the input layer rather than duplicating the calculation logic.

This reduces the risk of having slightly different formulas for different scenarios.

### 3.3 Scenario Manager in JavaScript

The JavaScript implementation uses:

- `ModelInputs`
- `cloneWith()`
- `ScenarioManager`
- `Map`

The `Map` stores scenario names and their associated assumption changes.

JavaScript's object-spread behavior is useful for maintaining immutable-style scenario definitions while creating modified model inputs.

### 3.4 Scenario Manager in C++

The C++ implementation introduces:

- `ModelInputs`
- `ModelOutputs`
- `Scenario`
- `ScenarioManager`

The manager stores scenarios in a `std::vector`.

Each scenario contains a complete `ModelInputs` object.

This makes the C++ version slightly different from the Python and JavaScript implementations: instead of storing only a dictionary/object of changed fields, the case study stores a validated complete input state for each scenario.

That design is appropriate when strong structure and predictable data ownership are important.

---

## 4. Goal Seek

### 4.1 Definition

Goal Seek works backward from a desired result.

Normal model flow:

`Input -> Formula -> Output`

Goal Seek asks:

`Desired Output -> Find Input`

For example:

> What number of units must be sold to produce $100,000 of net profit?

The target is the net profit.

The variable being changed is units sold.

### 4.2 Goal Seek Is Not the Same as Scenario Analysis

Scenario analysis asks:

> What happens under these predefined assumptions?

Goal Seek asks:

> What assumption is required to achieve this predefined result?

This distinction is important.

### 4.3 Bisection Method

The implementations use the bisection method.

Suppose a function is:

`f(x)`

and the desired result is:

`target`

Goal Seek searches for:

`f(x) = target`

Define:

`g(x) = f(x) - target`

A solution occurs where:

`g(x) = 0`

If two bounds produce values with opposite signs, a root lies between them under the continuity assumptions required by bisection.

The algorithm repeatedly:

1. Calculates the midpoint.
2. Evaluates the midpoint.
3. Determines which half contains the solution.
4. Repeats until the desired tolerance is reached.

### 4.4 Why Bracketing Matters

A Goal Seek implementation cannot blindly assume that a solution exists.

For example, the C++, Python, and JavaScript implementations deliberately reject an interval when both endpoints are on the same side of the target.

This is demonstrated with the equation:

`x² = 10`

The interval `[1, 2]` is insufficient because:

- `1² = 1`
- `2² = 4`

Neither endpoint reaches 10.

The interval `[0, 5]` brackets the solution because:

- `0² - 10 < 0`
- `5² - 10 > 0`

### 4.5 Goal Seek Limitations

Goal Seek can become difficult when:

- no solution exists;
- multiple solutions exist;
- the function is discontinuous;
- the function is not monotonic;
- the search range is inappropriate;
- the model contains invalid input regions;
- rounding prevents a precise target from being reached.

A production implementation should therefore define:

- valid input bounds;
- maximum iterations;
- numerical tolerance;
- failure behavior.

---

## 5. One-Variable Sensitivity Analysis

One-variable sensitivity changes one assumption while keeping other assumptions constant.

For example:

| Price | Net Profit |
|---:|---:|
| $40 | Calculated |
| $45 | Calculated |
| $50 | Calculated |
| $55 | Calculated |
| $60 | Calculated |
| $65 | Calculated |

This answers:

> How sensitive is net profit to the selling price?

The Python implementation provides `one_variable_sensitivity()`.

The JavaScript implementation provides a corresponding generic function.

The C++ implementation uses a function object that modifies one selected input.

This abstraction allows the same sensitivity engine to work with different assumptions.

---

## 6. Two-Variable Sensitivity Analysis

Two-variable sensitivity evaluates combinations of two changing assumptions.

The case study uses:

- Units sold
- Price per unit

The output is net profit.

Conceptually:

| Units / Price | $45 | $50 | $55 | $60 |
|---|---:|---:|---:|---:|
| 7,500 | Result | Result | Result | Result |
| 10,000 | Result | Result | Result | Result |
| 12,500 | Result | Result | Result | Result |
| 15,000 | Result | Result | Result | Result |

This is conceptually equivalent to an Excel two-variable Data Table.

### Why Two Variables Matter

Inputs can interact.

For example:

- Increasing price may increase profit.
- Increasing volume may increase profit.
- Increasing both can create a larger combined effect.

A one-variable analysis can hide these interactions.

---

## 7. Sensitivity Versus Scenario Analysis

These concepts are related but distinct.

| Technique | Main Question |
|---|---|
| Scenario Manager | What happens under each named assumption set? |
| One-variable sensitivity | What happens when one assumption changes? |
| Two-variable sensitivity | What happens when two assumptions change together? |
| Goal Seek | What input is required to reach a target? |

Scenario Manager is usually categorical.

Sensitivity analysis is usually systematic.

Goal Seek is target-oriented.

---

## 8. Break-Even Analysis

Break-even analysis determines the point where operating profit becomes zero.

Contribution margin per unit is:

`Contribution Margin = Price − Variable Cost`

Break-even units are:

`Break-even Units = Fixed Costs / Contribution Margin`

For the base model:

- Price = $50
- Variable cost = $28
- Contribution margin = $22
- Fixed costs = $100,000

Therefore:

`Break-even Units = 100,000 / 22`

The implementations calculate this dynamically rather than hard-coding the result.

### Zero Contribution Margin

If:

`Price = Variable Cost`

then:

`Contribution Margin = 0`

Fixed costs cannot be recovered through unit contribution.

The implementations therefore return no finite break-even quantity.

### Negative Contribution Margin

If:

`Price < Variable Cost`

each additional unit increases the loss.

A standard positive break-even volume does not exist under these assumptions.

---

## 9. Percentage Change

Percentage change is calculated as:

`(New − Old) / |Old|`

The implementations protect against a zero base because percentage change relative to zero is undefined.

This matters when analyzing outputs such as:

- Profit
- Revenue
- ROI
- Units
- Costs

A model should not silently return misleading values when the denominator is zero.

---

## 10. Elasticity

Elasticity measures the proportional response of one quantity to another.

The implementation uses:

`Elasticity = % Change in Output / % Change in Input`

For example:

- Input changes by 10%.
- Output changes by 20%.

Then:

`Elasticity = 20% / 10% = 2`

An absolute elasticity greater than 1 means the output changes proportionally more than the input within the tested range.

Elasticity is especially useful for:

- demand analysis;
- pricing;
- revenue models;
- operating leverage;
- financial assumptions.

The value is local to the tested changes. It should not automatically be treated as a constant relationship across the entire model.

---

## 11. Numerical Derivatives

The Python, JavaScript, and C++ implementations demonstrate numerical sensitivity using a central finite difference:

`f'(x) ≈ [f(x+h) − f(x−h)] / (2h)`

This estimates how much the output changes when the input changes by a small amount.

For the business model, the derivative of profit with respect to price gives an approximate change in profit per unit of price change.

### Step Size

A very large step can produce a poor local approximation.

A very small step can be affected by floating-point precision.

Therefore, numerical differentiation involves a trade-off between:

- approximation error;
- rounding error;
- computational cost.

---

## 12. Discounted Cash Flow Sensitivity

What-If Analysis is particularly important in investment models.

The case study includes:

`PV = Cash Flow / (1 + r)^t`

where:

- `PV` is present value;
- `r` is the discount rate;
- `t` is the period.

Net present value is:

`NPV = Sum of discounted cash flows`

The implementations calculate NPV at several discount rates.

This creates a sensitivity analysis around the discount-rate assumption.

For example:

- 6%
- 8%
- 10%
- 12%
- 14%

The resulting NPV can change substantially even when the underlying cash flows remain unchanged.

---

## 13. Python Implementation

The Python script is organized around reusable functions and data classes.

### Major Components

`ModelInputs`

Stores assumptions.

`ModelOutputs`

Stores calculated results.

`calculate_model()`

Centralizes the financial formulas.

`validate_inputs()`

Protects the model against invalid assumptions.

`Scenario`

Represents a named scenario.

`ScenarioManager`

Stores and evaluates scenarios.

`goal_seek()`

Implements bisection-based target seeking.

`one_variable_sensitivity()`

Evaluates one assumption over multiple values.

`two_variable_sensitivity()`

Evaluates combinations of two assumptions.

`elasticity()`

Measures proportional sensitivity.

`numerical_derivative()`

Approximates local sensitivity.

### Why Python Is Useful

Python provides concise data structures and functions, making it suitable for:

- financial modeling;
- analytical prototypes;
- scenario engines;
- numerical experiments;
- automated testing;
- data processing.

The implementation intentionally avoids external packages so that the concepts remain visible in the source code.

---

## 14. JavaScript Implementation

The JavaScript implementation uses object-oriented structures and native language features.

### Major Components

`ModelInputs`

Represents the model assumptions.

`cloneWith()`

Creates a modified input state without changing the original model.

`ScenarioManager`

Uses a `Map` to store named scenarios.

`goalSeek()`

Implements the bisection search.

`oneVariableSensitivity()`

Runs systematic input variations.

`twoVariableSensitivity()`

Builds a two-dimensional sensitivity matrix.

`npv()`

Calculates discounted cash flow value.

### JavaScript-Specific Relevance

JavaScript is useful when What-If Analysis becomes part of an interactive application.

For example, a browser interface could connect sliders or form fields to the same model:

`User Input -> JavaScript Model -> Updated Output`

This makes JavaScript particularly relevant to:

- financial dashboards;
- browser calculators;
- interactive business tools;
- web-based scenario planning;
- client-side sensitivity tables.

The current file remains runtime-independent and does not require a browser-specific framework.

---

## 15. C++ Case Study

### Problem

The C++ program models a product launch and evaluates whether the project remains financially viable under changing assumptions.

The system needs to answer:

1. What is the base-case profit?
2. What happens under conservative and optimistic assumptions?
3. How many units are required to achieve a target profit?
4. What price is required to achieve a target ROI?
5. How sensitive is profit to price?
6. How sensitive is profit to both price and volume?
7. What is the break-even volume?
8. How does NPV change with the discount rate?
9. What happens across a grid of demand and price assumptions?

### Architecture

The system separates:

`ModelInputs`

from:

`calculateModel()`

which produces:

`ModelOutputs`

The Scenario Manager operates around complete input states.

This separation provides a clear dependency structure:

`Assumptions -> Financial Model -> Results`

### Data Structures

The program uses:

- `struct` for model state;
- `std::vector` for collections;
- `std::function` for configurable calculation and setter behavior;
- `std::string` for scenario names;
- `std::map`-like conceptual organization through the Scenario Manager;
- standard algorithms such as `std::min_element`, `std::max_element`, `std::count_if`, and `std::accumulate`.

### Goal Seek

The C++ implementation uses the same bisection principle as Python and JavaScript.

Function behavior is supplied using `std::function<double(double)>`.

This separates the numerical search algorithm from the financial model.

The same Goal Seek implementation can therefore solve different target problems.

### Sensitivity Engine

The one-variable engine accepts:

- a base input;
- possible values;
- a setter function;
- an output selector.

This makes it reusable.

The two-variable engine follows the same design but evaluates a Cartesian product of two input ranges.

### Complexity

For a one-variable sensitivity analysis with `n` values:

`O(n)`

model evaluations are required.

For a two-variable analysis with `r` row values and `c` column values:

`O(r × c)`

model evaluations are required.

For a scenario grid with `n` possible values for one assumption and `m` for another:

`O(n × m)`

This becomes important when the underlying financial model is computationally expensive.

---

## 16. Scenario Grid Analysis

The case study creates a grid using:

- demand multipliers from 80% to 120%;
- price multipliers from 90% to 110%.

Every combination is evaluated.

This is useful for exploring a range of possible operating conditions.

It is important to distinguish a deterministic scenario grid from probability analysis.

If 20 of 25 grid cells are profitable, that does not automatically mean there is an 80% probability of profitability.

The grid cells may not have equal probability.

A true probability model requires assumptions about the probability distribution of the underlying variables.

---

## 17. Edge Cases

Important edge cases include:

### Zero Sales

If units sold are zero:

- revenue is zero;
- variable cost is zero;
- fixed costs still exist;
- the business produces an operating loss under the model.

### Zero Contribution Margin

If price equals variable cost:

`Contribution Margin = 0`

There is no finite positive sales volume that recovers fixed costs.

### Negative Contribution Margin

If variable cost exceeds price:

Each additional unit creates additional operating loss.

### Invalid Tax Rate

A tax rate below 0% or above 100% is rejected by the simplified model.

### Invalid Investment

An initial investment of zero would make ROI undefined.

The implementation rejects it instead of silently returning infinity or an invalid result.

### Goal Seek With No Bracket

The bisection algorithm rejects a range when the target is not bracketed.

---

## 18. Common Modeling Mistakes

### Changing Multiple Inputs Accidentally

If the purpose is one-variable sensitivity analysis, only one input should change.

### Mixing Units

Examples of dangerous inconsistencies include:

- annual revenue with monthly costs;
- percentages represented as 25 instead of 0.25;
- thousands of units mixed with individual units.

### Hard-Coding Formula Results

A model should calculate dependent values from assumptions rather than storing manually calculated outputs.

### Ignoring Invalid Inputs

A spreadsheet or program should validate assumptions before calculating results.

### Treating Scenarios as Probabilities

A named scenario is not automatically a probability-weighted outcome.

### Assuming Goal Seek Always Has One Solution

Some functions have:

- no solution;
- one solution;
- multiple solutions.

The algorithm and input range must account for this.

### Excessive Precision

Displaying many decimal places does not imply that the underlying business assumptions are accurate to the same precision.

### Hidden Assumptions

A model should make important assumptions visible and documented.

---

## 19. Important Distinctions

### Scenario Manager vs Sensitivity Analysis

Scenario Manager usually uses meaningful named states such as:

- Conservative
- Base
- Optimistic

Sensitivity analysis typically evaluates a systematic range.

### Goal Seek vs Optimization

Goal Seek normally changes one variable to hit one target.

Optimization can involve:

- multiple decision variables;
- multiple constraints;
- objective functions;
- maximization or minimization.

Therefore Goal Seek is narrower than a general optimization problem.

### Sensitivity vs Uncertainty Analysis

Sensitivity analysis asks:

> What happens if an assumption changes?

Uncertainty analysis asks:

> What range of outcomes is plausible given uncertainty in assumptions?

The second question requires probability or distribution assumptions when expressed probabilistically.

---

## 20. Performance Considerations

A simple spreadsheet model may calculate almost instantly.

Large models can become expensive when:

- many scenarios are evaluated;
- two-variable tables contain thousands of combinations;
- formulas include expensive operations;
- external data is retrieved;
- simulations are nested;
- repeated calculations are not cached.

Useful performance techniques include:

- avoiding duplicate calculations;
- separating input and output layers;
- caching invariant calculations;
- reducing unnecessary recalculation;
- using efficient data structures;
- vectorizing calculations when appropriate;
- limiting sensitivity ranges to meaningful values.

The C++ implementation demonstrates how the calculation engine can be separated from the analysis engine, which makes optimization easier.

---

## 21. Numerical Considerations

Financial models frequently involve floating-point numbers.

Floating-point arithmetic can introduce small representation errors.

Therefore, numerical comparisons should usually use a tolerance rather than exact equality.

For example, Goal Seek stops when the target error is within a specified tolerance.

The tolerance represents the required numerical precision, not necessarily business accuracy.

A model with highly uncertain business assumptions does not become more reliable merely because the numerical solver uses a very small tolerance.

---

## 22. Security Considerations

Basic What-If Analysis does not normally require advanced cybersecurity mechanisms, but production implementations should consider data integrity.

Relevant concerns include:

- validating user inputs;
- preventing malformed numeric data;
- controlling access to sensitive financial models;
- protecting confidential assumptions;
- avoiding unsafe formula construction;
- auditing changes to important assumptions;
- distinguishing trusted model logic from user-provided content.

For web applications, user-supplied values should be validated on the server as well as in the browser.

Client-side JavaScript validation alone should not be treated as a security boundary.

---

## 23. Production Implementation Considerations

A production What-If Analysis system would normally need more structure than the educational implementations.

Useful production components include:

- explicit model versioning;
- input metadata;
- units and currencies;
- scenario identifiers;
- scenario ownership;
- audit history;
- validation rules;
- calculation logs;
- test suites;
- numerical tolerances;
- error reporting;
- reproducible calculation results.

For financial applications, assumptions should also include clear time periods.

For example:

`10,000 units per month`

is fundamentally different from:

`10,000 units per year`.

The model should not leave such distinctions implicit.

---

## 24. Testing Considerations

The implementations demonstrate validation and failure conditions, but a production model should have dedicated automated tests.

Important test categories include:

### Formula Tests

Verify known inputs against independently calculated expected outputs.

### Boundary Tests

Test:

- zero units;
- zero contribution margin;
- very small positive margins;
- maximum permitted tax rates;
- minimum permitted investment.

### Goal Seek Tests

Verify:

- exact targets;
- approximate targets;
- invalid brackets;
- unreachable targets;
- convergence behavior.

### Sensitivity Tests

Verify:

- one-variable results;
- matrix dimensions;
- combinations of assumptions;
- unchanged assumptions.

### Regression Tests

When a financial formula changes, previous known scenarios can be recalculated to detect unintended behavior changes.

---

## 25. Practical Applications

What-If Analysis can be applied to:

- product pricing;
- sales forecasting;
- capital budgeting;
- investment analysis;
- project planning;
- operating budgets;
- procurement decisions;
- staffing models;
- capacity planning;
- break-even analysis;
- financial planning;
- business-case evaluation;
- cost-volume-profit analysis.

The same conceptual structure appears in many domains:

`Assumptions -> Model -> Outputs -> Alternative Inputs -> Comparison`

---

## 26. Key Implementation Principles

A reliable What-If Analysis model should:

1. Separate assumptions from calculations.
2. Validate assumptions.
3. Centralize formulas.
4. Give scenarios explicit names.
5. Keep sensitivity variables identifiable.
6. Define valid ranges for Goal Seek.
7. Handle impossible targets explicitly.
8. Treat numerical precision carefully.
9. Distinguish scenarios from probabilities.
10. Document units and time periods.
11. Test boundary conditions.
12. Keep the analysis engine independent from the underlying business model.

The three implementations demonstrate these principles through different programming styles while preserving the same underlying financial logic.
