# Business Valuation: DCF, Multiples and Valuation Fundamentals

## 1. Domain Overview

Business valuation estimates the economic value of an enterprise or its equity using financial information, operating forecasts, capital costs, market evidence and assumptions about future performance.

The implementation covers two principal valuation approaches:

- **Income approach:** Determines value from expected future cash flows. Discounted Cash Flow (DCF) is the primary method.
- **Market approach:** Estimates value using valuation multiples observed in comparable publicly traded companies.

The two approaches answer related but different questions. DCF estimates value from the company's expected financial performance. Comparable company analysis estimates value relative to market pricing of similar businesses.

All five implementations use a hypothetical software company. Monetary values are expressed in INR millions unless explicitly stated otherwise.

## 2. Fundamental Valuation Concepts

### 2.1 Enterprise Value and Equity Value

Enterprise Value (EV) represents the value of the operating business available to all capital providers, including debt and equity investors.

Equity Value represents the residual value attributable to shareholders after accounting for financial obligations and non-operating cash.

The simplified reconciliation is:

**Equity Value = Enterprise Value + Cash - Debt**

For the example company:

| Financial item | Amount |
|---|---:|
| Cash | 100 |
| Debt | 300 |
| Net debt | 200 |
| Shares outstanding | 50 million |

If enterprise value is INR 2,000 million:

- Equity value = 2,000 + 100 - 300
- Equity value = INR 1,800 million
- Value per share = 1,800 / 50
- Value per share = INR 36

This distinction is essential because enterprise valuation and share valuation are not interchangeable.

A complete equity bridge may require adjustments for minority interests, preferred securities, leases, pension obligations, investments, restricted cash and other non-operating items. The implementations use a simplified cash-and-debt bridge.

### 2.2 Revenue, EBIT and EBITDA

| Metric | Meaning | Application |
|---|---|---|
| Revenue | Income generated from business operations | Growth forecasting and EV/Revenue |
| EBIT | Earnings before interest and tax | Operating profitability |
| EBITDA | EBIT plus depreciation and amortization | EV/EBITDA comparison |
| NOPAT | Net Operating Profit After Tax | DCF operating cash flow |
| FCFF | Free Cash Flow to Firm | Enterprise valuation |
| Net Income | Earnings attributable to shareholders | P/E valuation |

EBITDA excludes depreciation and amortization, while EBIT includes their effect.

EBITDA is not equivalent to cash flow because it excludes capital expenditure, working capital investment and taxes.

### 2.3 Free Cash Flow to Firm

Free Cash Flow to Firm measures operating cash available to both debt and equity capital providers after operating taxes and reinvestment requirements.

The implementation uses:

**NOPAT = EBIT × (1 - Tax Rate)**

**FCFF = NOPAT + Depreciation - Capital Expenditure - Change in Working Capital**

The calculation excludes interest expense because FCFF is discounted using WACC, which incorporates the costs of both debt and equity financing.

Working capital increases consume cash. Working capital decreases release cash.

A company can report increasing revenue and positive EBITDA while producing negative FCFF if capital expenditure and working capital requirements are substantial.

### 2.4 Discount Rate

The Weighted Average Cost of Capital represents the blended required return of debt and equity capital providers.

The formula is:

**WACC = (E/V × Ke) + (D/V × Kd × (1 - T))**

Where:

| Variable | Meaning |
|---|---|
| E | Market value of equity |
| D | Market value of debt |
| V | Total market value of capital |
| Ke | Cost of equity |
| Kd | Pre-tax cost of debt |
| T | Corporate tax rate |

The cost of equity represents the return required by shareholders.

The cost of debt represents the borrowing cost before the tax adjustment.

The debt tax adjustment reflects the tax deductibility of interest under the simplified model.

The example assumes:

| Input | Assumption |
|---|---:|
| Cost of equity | 14% |
| Cost of debt | 9% |
| Equity weight | 70% |
| Debt weight | 30% |
| Tax rate | 25% |

The resulting WACC is:

- Equity contribution = 70% × 14% = 9.80%
- After-tax debt contribution = 30% × 9% × 75% = 2.025%
- WACC = 11.825%

The capital weights must sum to 100%.

For a practical valuation, capital structure weights should generally reflect market values and an appropriate target financing structure rather than automatically relying on historical book values.

## 3. Discounted Cash Flow Valuation

### 3.1 DCF Mechanism

DCF converts expected future FCFF into present value using the required return on capital.

The calculation involves:

1. Establishing historical financial performance.
2. Forecasting future revenue.
3. Estimating operating margins.
4. Calculating NOPAT.
5. Estimating depreciation and reinvestment.
6. Calculating FCFF.
7. Determining WACC.
8. Discounting forecast cash flows.
9. Calculating terminal value.
10. Reconciling enterprise value to equity value.

The mathematical representation is:

\[
EV = \sum_{t=1}^{n}\frac{FCFF_t}{(1+WACC)^t}
+\frac{TV_n}{(1+WACC)^n}
\]

### 3.2 Explicit Forecast Period

The implementations use five forecast years.

Revenue is projected using:

\[
Revenue_t = Revenue_{t-1}(1+g_t)
\]

EBIT is calculated using forecast operating margins:

\[
EBIT_t = Revenue_t \times EBIT\ Margin_t
\]

Depreciation and capital expenditure are modeled as percentages of revenue.

Working capital is also estimated as a percentage of revenue. The annual working capital investment is the difference between current and previous forecast working capital.

These assumptions are simplified but make the relationship between operating growth, profitability and reinvestment explicit.

A detailed financial model would generally forecast individual working capital components, depreciation schedules, capital expenditure categories and tax adjustments.

### 3.3 Terminal Value

The explicit forecast period cannot reasonably extend indefinitely. Terminal value represents the estimated value of cash flows after the explicit forecast period.

The implementations use the Gordon Growth Model:

\[
TV_n = \frac{FCFF_{n+1}}{WACC-g}
\]

Where:

- \(FCFF_{n+1}\) is the cash flow in the first terminal year.
- \(g\) is the perpetual growth rate.
- WACC is the discount rate.

The terminal growth rate must be lower than WACC.

The terminal cash flow is calculated as:

\[
FCFF_{n+1}=FCFF_n(1+g)
\]

Terminal value is calculated at the end of the final explicit forecast year and then discounted to present value.

An important analytical consideration is the terminal value contribution:

\[
Terminal\ Contribution =
\frac{PV(TV)}{EV}
\]

A high terminal contribution indicates that the valuation depends heavily on long-term assumptions rather than near-term projected cash flows.

This is not automatically an error, but it warrants greater scrutiny.

### 3.4 Enterprise-to-Equity Reconciliation

After calculating enterprise value:

\[
Equity\ Value = EV + Cash - Debt
\]

The per-share valuation is:

\[
Intrinsic\ Value\ Per\ Share =
\frac{Equity\ Value}{Shares\ Outstanding}
\]

The scripts explicitly separate enterprise valuation from shareholder valuation.

## 4. Scenario Analysis

The model implements three operating scenarios.

| Assumption | Bear | Base | Bull |
|---|---:|---:|---:|
| Year 1 revenue growth | 4% | 10% | 16% |
| Year 2 revenue growth | 3.5% | 9% | 14% |
| Year 3 revenue growth | 3% | 8% | 12% |
| Year 4 revenue growth | 2.5% | 7% | 10% |
| Year 5 revenue growth | 2% | 6% | 8% |
| Terminal growth | 2% | 3% | 3.5% |

The scenarios also use different operating margins, depreciation rates, capital expenditure assumptions and working capital requirements.

### Bear Scenario

Represents weaker growth and relatively lower operating profitability.

Possible business conditions include:

- Reduced customer demand.
- Pricing pressure.
- Higher operating costs.
- Slower market expansion.
- Greater reinvestment requirements.

### Base Scenario

Represents the central operating forecast based on the selected assumptions.

It is not necessarily the most probable outcome without supporting evidence.

### Bull Scenario

Represents stronger growth and operating performance.

Possible business conditions include:

- Increased customer acquisition.
- Improved operating efficiency.
- Stronger pricing.
- Better utilization of existing infrastructure.
- Higher operating margins.

Scenario analysis is distinct from sensitivity analysis. Scenario analysis changes a collection of related business assumptions, while sensitivity analysis isolates selected valuation variables.

## 5. Sensitivity Analysis

DCF valuation can change significantly when WACC or terminal growth changes.

The implementations evaluate a grid of alternative assumptions:

| WACC adjustment | Terminal growth adjustment |
|---|---|
| -1 percentage point | -1 percentage point |
| No adjustment | No adjustment |
| +1 percentage point | +1 percentage point |

This produces multiple enterprise value estimates.

The general relationship is:

- Higher WACC reduces present value.
- Lower WACC increases present value.
- Higher terminal growth increases terminal value.
- Lower terminal growth reduces terminal value.

Combinations where terminal growth equals or exceeds WACC are rejected because the Gordon Growth calculation becomes invalid or economically inconsistent.

Sensitivity results are not forecasts. They demonstrate how valuation responds to changes in assumptions.

## 6. Comparable Company Valuation

Comparable company analysis estimates business value using financial multiples observed in companies with similar economic characteristics.

The selection of peers should consider:

- Industry and business model.
- Revenue composition.
- Operating margins.
- Geographic exposure.
- Growth prospects.
- Capital intensity.
- Financial leverage.
- Company size.
- Risk profile.

A company should not be selected as a comparable merely because it operates in the same broad industry.

### 6.1 Enterprise Value to Revenue

\[
EV/Revenue = \frac{Enterprise\ Value}{Revenue}
\]

This multiple is useful when companies have different profitability levels or when earnings are temporarily depressed.

Its limitation is that it does not directly account for differences in operating margins.

### 6.2 Enterprise Value to EBITDA

\[
EV/EBITDA = \frac{Enterprise\ Value}{EBITDA}
\]

This multiple compares enterprise value with operating earnings before depreciation, amortization, interest and taxes.

It is commonly used in transaction analysis and trading comparables.

Its limitations include differences in capital expenditure, depreciation policies, leverage-related financing requirements and working capital.

### 6.3 Price to Earnings

\[
P/E = \frac{Equity\ Value}{Net\ Income}
\]

P/E directly relates shareholder valuation to earnings attributable to shareholders.

Unlike EV/EBITDA and EV/Revenue, it is an equity valuation multiple.

Consequently, its application does not require the enterprise-to-equity bridge used for enterprise value multiples.

Negative or zero earnings make conventional P/E interpretation unsuitable.

### 6.4 Median Multiple

The implementations calculate the median comparable-company multiple rather than relying exclusively on the arithmetic mean.

The median reduces the influence of unusually high or low observations.

For an even number of observations, it is the average of the two central sorted values.

### 6.5 Applying Multiples to the Target

For EV/EBITDA:

\[
Target\ EV = Target\ EBITDA \times Median\ EV/EBITDA
\]

For EV/Revenue:

\[
Target\ EV = Target\ Revenue \times Median\ EV/Revenue
\]

The resulting enterprise value is converted to equity value using cash and debt adjustments.

For P/E:

\[
Target\ Equity\ Value = Target\ Net\ Income \times Median\ P/E
\]

The implementation calculates three independent estimates to demonstrate why different valuation methods can produce different results.

## 7. Python Implementation

The Python implementation uses a structured financial-model architecture.

| Component | Responsibility |
|---|---|
| `FinancialStatements` | Validates historical financial inputs |
| `CapitalStructure` | Represents financing assumptions |
| `ForecastAssumptions` | Stores operating forecast parameters |
| `ForecastYear` | Stores annual projected financial metrics |
| `DCFResult` | Stores DCF valuation outputs |
| `BusinessValuator` | Calculates WACC, FCFF and DCF |
| `ComparableCompany` | Represents peer financial information |
| `ComparableValuation` | Calculates market multiples |
| `Scenario` | Defines operating scenarios |

The script uses dataclasses to make financial inputs explicit and provides immutable input records for the principal assumptions.

The `BusinessValuator` class calculates FCFF and generates forecast records. Its sensitivity method recalculates enterprise value under different discount rates and terminal growth assumptions.

The comparable valuation component uses the standard library's median calculation to estimate representative peer multiples.

The implementation also uses assertions to verify enterprise-to-equity reconciliation.

### Important Python design decisions

- Financial input validation is performed before calculations.
- Invalid capital weights are rejected.
- Terminal growth must remain below WACC.
- Negative forecast revenue growth is permitted if it exceeds -100%.
- The model does not recognize tax benefits from operating losses.
- The calculation does not require third-party packages.

## 8. JavaScript Implementation

The JavaScript implementation uses an event-driven valuation architecture.

Its principal components are:

| Component | Responsibility |
|---|---|
| `FinancialModel` | Normalizes financial statement inputs |
| `CapitalCost` | Calculates WACC |
| `ForecastPlan` | Holds forecast assumptions |
| `DCFEngine` | Performs cash flow projections |
| `ComparableCompany` | Represents peer information |
| `ComparableEngine` | Calculates trading multiples |
| `ValuationPolicy` | Evaluates valuation quality conditions |
| `ValuationEventBus` | Publishes valuation completion events |

### Event-driven execution

The `ValuationEventBus` extends Node.js `EventEmitter`.

After a valuation is completed, the system publishes a `valuation:completed` event.

Listeners receive the calculated valuation and can produce reports or evaluate policies without coupling those operations directly to the DCF calculation.

This separation supports larger applications in which valuation calculations, reporting and approval workflows operate independently.

### State and data integrity

The implementation uses:

- `Map` for storing scenario results.
- `Object.freeze()` for immutable financial records and outputs.
- `EventEmitter` for event-driven reporting.
- `assert` for integrity verification.
- Standard JavaScript exceptions for invalid financial assumptions.

The implementation is synchronous because the calculations are local and computationally small. An asynchronous architecture would be more appropriate if market data, financial statements or peer information were retrieved from external services.

## 9. C++17 Implementation

The C++ implementation emphasizes explicit financial domain structures and computational control.

| Component | Responsibility |
|---|---|
| `FinancialStatements` | Stores company financial data |
| `CapitalStructure` | Stores capital financing assumptions |
| `ForecastAssumptions` | Stores forecast parameters |
| `ForecastYear` | Stores projected cash flow data |
| `DCFResult` | Stores valuation results |
| `ValuationEngine` | Executes DCF calculations |
| `ComparableCompany` | Models a comparable business |
| `ComparableValuator` | Calculates market valuation estimates |

### Computational approach

The implementation uses STL containers for forecasts and peer datasets.

`std::vector` stores forecast periods and comparable companies.

`std::map` stores named valuation metrics.

`std::sort` and `std::accumulate`-compatible numerical operations support data processing, while median calculation explicitly sorts observations.

The program uses exceptions to reject invalid financial assumptions and `assert` to verify important valuation relationships.

### Performance characteristics

For \(n\) forecast periods:

- Forecast generation: \(O(n)\).
- DCF calculation: \(O(n)\).
- Sensitivity analysis: \(O(nwg)\), where \(w\) and \(g\) are the number of WACC and growth assumptions.
- Comparable median calculation: \(O(m\log m)\) for \(m\) peer companies.

For larger financial datasets, peer filtering and aggregation should be performed before valuation calculations.

## 10. Java 17 Implementation

The Java implementation adopts an enterprise-oriented service architecture.

Its principal domain records represent:

- Financial statements.
- Capital structure.
- Forecast assumptions.
- Annual forecast periods.
- DCF results.
- Comparable company financial information.

Records provide concise immutable data structures and reduce the risk of accidental modification of financial assumptions during calculation.

### Service separation

`CapitalCostService` calculates WACC.

`DCFService` generates forecast cash flows, calculates enterprise value and performs sensitivity analysis.

`ComparableValuationService` calculates peer multiples and estimates target company valuation.

`ValuationPolicy` evaluates whether the calculated valuation meets configured thresholds.

This design separates calculation logic from financial policy.

### Policy evaluation

The valuation policy checks:

- Whether terminal value contribution exceeds the configured maximum.
- Whether WACC is below the permitted minimum.
- Whether WACC exceeds the permitted maximum.
- Whether equity value is positive.

A policy failure does not automatically invalidate the mathematical calculation. It indicates that the result requires further review.

This distinction is important in enterprise financial systems: a valid calculation and an acceptable valuation are different outcomes.

The implementation requires Java 17 and uses no external dependencies.

## 11. PostgreSQL Database Architecture

The PostgreSQL implementation models valuation as a relational financial workflow.

### 11.1 Database Relationship

The main relationship is:

    Companies
       |
       +---- Financial Statements
       |
       +---- Capital Structures
       |
       +---- Valuation Assumptions
       |          |
       |          +---- Forecast Periods
       |
       +---- Valuations
       |          |
       |          +---- Projected Cash Flows
       |          |
       |          +---- Sensitivity Results
       |
       +---- Valuation Policies
       |
       +---- Comparable Companies
                  |
                  +---- Comparable Multiples

The design separates historical information, financing assumptions, forecast inputs, valuation outputs and peer-market observations.

### 11.2 Principal Tables

| Table | Purpose |
|---|---|
| `companies` | Company master data |
| `financial_statements` | Historical financial information |
| `capital_structures` | Cost of capital and financing weights |
| `valuation_assumptions` | Bear, base and bull operating assumptions |
| `forecast_periods` | Annual growth and operating margins |
| `valuations` | DCF execution results and valuation status |
| `projected_cash_flows` | Annual projected FCFF and present values |
| `comparable_companies` | Target-to-peer financial observations |
| `comparable_multiples` | EV/Revenue, EV/EBITDA and P/E |
| `valuation_policies` | Valuation quality thresholds |
| `valuation_sensitivity` | Alternative valuation assumptions |
| `valuation_audit` | Status transition history |

### 11.3 Integrity Constraints

The schema uses primary keys and foreign keys to preserve entity relationships.

Important financial constraints include:

- Revenue must be positive.
- Shares outstanding must be positive.
- Cash and debt cannot be negative.
- Tax rates must remain below 100%.
- Capital weights must sum to 100%.
- Forecast revenue growth must exceed -100%.
- EBIT margins must remain within the permitted range.
- Terminal growth must remain below the discount rate in sensitivity records.

Unique constraints prevent duplicate company-year statements, duplicate scenario assumptions and duplicate forecast periods.

### 11.4 Database Functions

`calculate_wacc()` implements the weighted average cost of capital calculation.

`calculate_fcff()` calculates free cash flow to firm from operating earnings and reinvestment.

Both functions validate their inputs before returning results.

### 11.5 DCF Stored Procedure

`run_dcf()` performs the DCF workflow within the database.

Its responsibilities include:

1. Locking the valuation record.
2. Loading financial statements.
3. Loading capital structure.
4. Loading scenario assumptions.
5. Checking company and scenario consistency.
6. Calculating WACC.
7. Validating forecast periods.
8. Generating projected revenue.
9. Calculating EBIT and NOPAT.
10. Calculating FCFF.
11. Calculating annual discount factors.
12. Storing projected cash flows.
13. Calculating terminal value.
14. Reconciling enterprise and equity values.
15. Updating the valuation status.

The procedure runs within the calling transaction. A failure causes the transaction to be rolled back, preventing partially completed valuation records from being committed.

### 11.6 Triggers

Two triggers provide additional database functionality.

**Comparable multiple trigger**

The trigger automatically calculates EV/Revenue, EV/EBITDA and P/E whenever a comparable company's financial observation is inserted or updated.

**Valuation audit trigger**

The trigger records changes in valuation status, including the previous status, new status, timestamp and database user.

This provides a basic record of workflow transitions.

### 11.7 Views and Reporting

The database provides:

- `comparable_valuation_report`
- `dcf_forecast_report`
- `valuation_summary`

These views simplify access to normalized valuation information.

The reporting queries demonstrate scenario comparisons, financial reconciliation, comparable multiples, cash flow aggregation, input validation and policy evaluation.

### 11.8 Transaction Management

Sample data insertion and DCF execution use explicit transactions.

The execution procedure locks individual valuation records using `FOR UPDATE`.

This helps prevent concurrent processes from recalculating the same draft valuation simultaneously.

The database should also use appropriate application permissions. Production access should not allow ordinary reporting users to modify financial statements or valuation outputs.

## 12. Valuation Quality and Practical Limitations

### 12.1 Forecast Reliability

DCF depends on estimates of future revenue, operating margins and reinvestment.

Historical growth does not guarantee future growth.

Forecasts should be tested against market conditions, industry economics, company strategy and operating capacity.

### 12.2 WACC Estimation

WACC is sensitive to financing structure and capital market assumptions.

Cost of equity commonly requires a separate estimation process using risk-free rates, equity risk premiums and company-specific systematic risk.

The examples use supplied cost-of-equity and cost-of-debt assumptions rather than estimating them from market data.

### 12.3 Terminal Value Risk

Terminal value can account for a substantial proportion of enterprise value.

Perpetual growth assumptions must reflect sustainable long-term economic conditions.

A high terminal growth assumption can produce an inflated valuation, especially when WACC is only slightly higher.

### 12.4 Comparable Company Selection

Peer multiples are meaningful only when the underlying businesses have sufficiently comparable operating and financial characteristics.

Differences in leverage, profitability, growth, accounting treatment and market conditions can make direct comparisons misleading.

### 12.5 Accounting Consistency

The implementations use a simplified model in which depreciation, capital expenditure and working capital are forecast as percentages of revenue.

A production-grade financial model should consider:

- Deferred taxation.
- Net operating loss carryforwards.
- Capital expenditure schedules.
- Depreciation and amortization schedules.
- Lease obligations.
- Minority interests.
- Preferred securities.
- Non-operating assets.
- Pension liabilities.
- Foreign exchange effects.
- Different fiscal periods.
- Acquisitions and divestitures.

The models also assume that cash and debt inputs are suitable for the enterprise-to-equity bridge and that forecast FCFF is consistent with the selected discount rate.

### 12.6 Currency and Units

All example monetary values are expressed in INR millions.

The valuation outputs per share are expressed in INR because the share count is represented in millions.

Real financial systems should explicitly store currency, reporting period, unit scale and exchange-rate assumptions to prevent inconsistencies.

### 12.7 Data Governance

Financial valuation systems should preserve:

- Original financial statement inputs.
- Forecast assumption versions.
- Valuation execution timestamps.
- Calculation outputs.
- Source and observation dates.
- Approval and review records.
- Changes to model assumptions.

The database provides basic audit logging and scenario separation. A production deployment would require more comprehensive versioning, user authorization, model approval workflows and immutable historical valuation snapshots.

## 13. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary focus | Financial modeling | Event-driven valuation | Computational engine | Enterprise services | Relational workflow |
| DCF | Yes | Yes | Yes | Yes | Yes |
| WACC | Yes | Yes | Yes | Yes | Yes |
| FCFF | Yes | Yes | Yes | Yes | Yes |
| Terminal value | Yes | Yes | Yes | Yes | Yes |
| Comparables | Yes | Yes | Yes | Yes | Yes |
| Sensitivity | Yes | Yes | Yes | Yes | Yes |
| Scenario analysis | Yes | Yes | Yes | Yes | Yes |
| Input validation | Exceptions | Exceptions | Exceptions | Domain validation | Constraints and functions |
| Reporting | Console | Event-driven console | Console | Service output | Views and queries |
| Audit functionality | No persistent audit | Event notifications | No persistent audit | Policy evaluation | Status audit table |

## 14. Execution Requirements

| Deliverable | Runtime | Dependencies |
|---|---|---|
| Python | Python 3.10+ | Standard library |
| JavaScript | Node.js 18+ | Node.js standard library |
| C++17 | C++17 compiler | Standard Template Library |
| Java | JDK 17+ | Java standard library |
| PostgreSQL | PostgreSQL 14+ | PostgreSQL server |

### Python

The script executes the bear, base and bull DCF valuations, comparable company analysis and sensitivity calculations.

### JavaScript

The application executes the same principal valuation categories using event-driven reporting and policy evaluation.

### C++17

The program compiles as a standalone C++17 executable and performs the calculations using standard library containers and algorithms.

### Java 17

The program uses records, immutable collections, service classes and domain validation.

### PostgreSQL

Execute the SQL script against a PostgreSQL database with permission to create schemas, tables, functions, procedures and triggers.

The script creates the valuation schema, inserts sample companies and financial records, executes the DCF procedures and runs reporting and integrity queries.

## 15. Key Financial Distinctions

| Concept | What it represents | What it does not represent |
|---|---|---|
| Enterprise Value | Value of the operating business to capital providers | Shareholder value alone |
| Equity Value | Value attributable to equity holders | Total operating enterprise value |
| EBIT | Operating profit before interest and taxes | Cash available to investors |
| EBITDA | Earnings before interest, taxes, depreciation and amortization | Free cash flow |
| NOPAT | After-tax operating profit | Net income |
| FCFF | Cash available to debt and equity investors | Cash flow available exclusively to shareholders |
| WACC | Blended required return of capital providers | Historical accounting interest expense |
| Terminal Value | Value of post-forecast cash flows | A separately generated operating cash flow |
| EV/EBITDA | Enterprise value relative to EBITDA | Direct equity valuation multiple |
| EV/Revenue | Enterprise value relative to revenue | Profitability measure |
| P/E | Equity value relative to net income | Enterprise value multiple |
| Sensitivity Analysis | Effect of changing selected assumptions | A probability-weighted forecast |
| Scenario Analysis | Alternative sets of business assumptions | A market trading multiple |

The implementations keep the distinction between operating performance, reinvestment, financing structure, enterprise valuation and equity valuation explicit throughout the calculation process.
