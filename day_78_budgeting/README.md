# Budget Preparation and Variance Analysis

## 1. Financial Planning and Budget Management

Budget preparation and variance analysis are two connected financial management activities.

**Budget preparation** establishes the financial resources an organization expects to receive and spend during a defined period.

**Variance analysis** compares actual financial performance with the approved budget to identify differences, measure financial performance, and investigate the reasons behind those differences.

The two activities create a continuous financial management process:

Planning → Budget Preparation → Review → Approval → Execution → Actual Recording → Variance Analysis → Forecast Revision

The implementations use an annual operating budget for a fictional organization with three departments:

- Finance (FIN)
- Operations (OPS)
- Information Technology (IT)

The reporting currency is INR.

## 2. Budgeting Fundamentals

### 2.1 Meaning of a Budget

A budget is a quantified financial plan for a future period.

It defines expected revenue, planned expenditure, resource allocations, and financial targets.

A budget normally contains:

| Component | Purpose |
|---|---|
| Budget period | Defines the financial planning period |
| Revenue estimates | Forecasts expected income |
| Expense estimates | Defines planned expenditure |
| Department allocations | Distributes financial resources |
| Cost assumptions | Describes fixed and variable spending |
| Activity assumptions | Estimates operational volume |
| Approval information | Records authorization |
| Performance measures | Supports financial monitoring |

The annual budget is not the same as an actual financial statement. It represents an approved plan, whereas actual transactions represent financial activity that has occurred.

### 2.2 Budget Preparation Process

A practical budget preparation workflow consists of the following stages.

1. Establish the fiscal year and financial objectives.
2. Identify departments and their responsibilities.
3. Estimate revenue and operational activity.
4. Identify fixed, variable, and mixed expenses.
5. Calculate departmental financial requirements.
6. Compare proposed allocations with spending limits.
7. Submit the proposed budget for review.
8. Obtain the required approval.
9. Record the approved budget as the financial baseline.
10. Monitor actual performance throughout the year.

The implementations represent these activities through budget objects, financial policies, department allocations, and approval states.

### 2.3 Budget Types

| Budget type | Meaning | Practical application |
|---|---|---|
| Static budget | Prepared for one planned activity level | Annual departmental allocation |
| Flexible budget | Adjusted for actual activity | Production and operational expenditure |
| Rolling budget | Continuously updated as new information becomes available | Forecasting and changing business conditions |
| Incremental budget | Uses an existing budget as the starting point | Routine departmental planning |
| Zero-based budget | Requires expenditure to be justified from the beginning | Major cost restructuring |
| Capital budget | Plans long-term asset investment | Infrastructure and equipment |
| Operating budget | Plans routine business operations | Salaries, utilities, and supplies |
| Cash budget | Estimates cash receipts and payments | Liquidity management |

The five implementations directly calculate static and flexible budgets. The SQL implementation also stores rolling forecast records.

Incremental and zero-based budgeting are distinct preparation methods and are not represented as separate calculation engines in these programs.

## 3. Revenue and Expense Planning

### 3.1 Revenue Budget

A revenue budget estimates income expected during a financial period.

Common revenue sources include:

- Product sales
- Service revenue
- Subscription income
- Contract revenue
- Licensing income
- Other operating income

The example organization has planned annual service revenue of INR 30,00,000.

The revenue estimate is recorded separately from operating expenses.

Revenue performance is favorable when actual revenue exceeds planned revenue, assuming the comparison uses the same period and accounting basis.

### 3.2 Expense Budget

An expense budget establishes the resources required to operate the organization.

Examples include:

- Employee salaries
- Production materials
- Infrastructure
- Electricity
- Maintenance
- Transportation
- Office supplies
- Software subscriptions

Expenses are allocated to departments and classified according to their cost behavior.

### 3.3 Fixed Costs

Fixed costs remain unchanged within a relevant operating range and period.

Examples:

- Fixed employee salaries
- Office rent
- Annual software subscriptions
- Fixed maintenance contracts

If monthly rent is INR 40,000, a change in production activity does not automatically change the rent.

### 3.4 Variable Costs

Variable costs change with operational activity.

Examples:

- Production materials
- Packaging
- Transaction processing charges
- Per-unit delivery expenses

The calculation is:

Variable Cost = Variable Rate × Activity Level

For example:

- Material cost per unit: INR 120
- Planned production: 5,000 units

Planned material expenditure:

INR 120 × 5,000 = INR 6,00,000

### 3.5 Mixed Costs

Mixed costs contain fixed and variable components.

The calculation is:

Mixed Cost = Fixed Component + (Variable Rate × Activity Level)

For example:

- Fixed infrastructure expenditure: INR 1,80,000
- Variable infrastructure cost per activity unit: INR 20
- Planned activity: 5,000 units

Planned infrastructure expenditure:

INR 1,80,000 + (INR 20 × 5,000)

= INR 2,80,000

The Python, JavaScript, C++17, Java 17, and PostgreSQL implementations support these cost classifications.

## 4. Departmental Budget Allocation

Departmental budgeting distributes financial resources across organizational units.

The example uses the following annual spending limits:

| Department | Annual spending limit |
|---|---:|
| Finance | INR 5,00,000 |
| Operations | INR 9,00,000 |
| Information Technology | INR 6,00,000 |

The budget contains the following planned allocations:

| Account | Department | Account type | Planned amount |
|---|---|---|---:|
| REV001 | Finance | Revenue | INR 30,00,000 |
| EXP001 | Finance | Fixed expense | INR 3,60,000 |
| EXP002 | Operations | Variable expense | INR 6,00,000 |
| EXP003 | IT | Mixed expense | INR 2,80,000 |

The planned annual figures are:

| Financial measure | Amount |
|---|---:|
| Total revenue | INR 30,00,000 |
| Total expenses | INR 12,40,000 |
| Planned operating surplus | INR 17,60,000 |

The departmental limits apply to planned expenses rather than revenue.

Departmental limits provide a control against excessive resource allocation.

A department exceeding its spending limit cannot submit its budget for approval in the implemented workflow.

## 5. Budget Approval and Financial Controls

Budget preparation and budget approval are separate activities.

A department manager may prepare and submit a proposed budget, while an authorized financial controller or CFO may approve it.

The budget lifecycle uses these states:

| State | Meaning |
|---|---|
| DRAFT | Budget is being prepared |
| SUBMITTED | Budget is awaiting approval |
| APPROVED | Budget is authorized for execution |
| REJECTED | Budget has been rejected |
| CLOSED | Budget execution period has been formally closed |

The permitted principal transitions are:

DRAFT → SUBMITTED → APPROVED → CLOSED

A submitted budget may also move to REJECTED.

Approval is necessary before actual transactions can be associated with the budget.

This prevents unapproved financial plans from being treated as authorized spending baselines.

The Java implementation provides explicit role authorization through:

- DEPARTMENT_MANAGER
- FINANCE_MANAGER
- FINANCE_CONTROLLER
- CFO
- AUDITOR

The JavaScript implementation uses an independent policy evaluation mechanism. The Python and C++17 implementations provide controlled state transitions and financial validation.

The PostgreSQL implementation stores approval records and enforces the approval workflow through stored procedures.

## 6. Budget Execution and Actual Transactions

After approval, the organization begins recording financial transactions.

Each actual transaction contains:

| Field | Description |
|---|---|
| Transaction ID | Unique transaction identifier |
| Budget ID | Associated approved budget |
| Account code | Financial account |
| Department ID | Responsible department |
| Period | Accounting period |
| Transaction date | Date of financial activity |
| Amount | Actual financial value |
| Activity units | Associated operational volume |
| Description | Transaction explanation |
| Entered by | Employee responsible for recording |

An actual transaction must correspond to an existing budget line.

The implementations reject:

- Duplicate transaction identifiers
- Negative financial amounts
- Invalid accounting periods
- Unknown departments
- Unknown accounts
- Transactions against unapproved budgets
- Transactions that reference an unrelated budget

The SQL database also validates that transaction dates belong to the selected fiscal period.

These controls maintain consistency between the approved financial plan and recorded expenditure.

## 7. Variance Analysis

### 7.1 Meaning of Variance

A variance is the difference between an actual financial result and its corresponding budgeted amount.

The general formula is:

Variance = Actual Amount − Budgeted Amount

Interpretation depends on whether the account represents revenue or expenditure.

### 7.2 Revenue Variance

Revenue variance measures the difference between actual and planned revenue.

Example:

| Measure | Amount |
|---|---:|
| Planned monthly revenue | INR 2,50,000 |
| Actual monthly revenue | INR 2,80,000 |
| Variance | INR 30,000 |

The positive INR 30,000 variance is favorable because actual revenue exceeds planned revenue.

### 7.3 Expense Variance

Expense variance measures the difference between actual expenditure and planned expenditure.

Example:

| Measure | Amount |
|---|---:|
| Planned monthly expense | INR 30,000 |
| Actual monthly expense | INR 35,000 |
| Variance | INR 5,000 |

The positive INR 5,000 variance is unfavorable because actual expenditure exceeds the budget.

### 7.4 Favorable, Unfavorable, and On-Target Results

| Classification | Revenue | Expenses |
|---|---|---|
| Favorable | Actual exceeds budget | Actual is below budget |
| Unfavorable | Actual is below budget | Actual exceeds budget |
| On target | Actual equals budget | Actual equals budget |

A favorable variance does not automatically indicate good operational performance.

For example, lower maintenance expenditure could result from delayed maintenance rather than improved efficiency.

Similarly, favorable revenue variance could result from increased sales volume, higher prices, or a one-time event.

Financial interpretation therefore requires investigation of the underlying business activity.

### 7.5 Variance Percentage

Variance percentage expresses the financial difference relative to the budgeted amount.

Formula:

Variance Percentage = (Variance / Budgeted Amount) × 100

Example:

- Budget: INR 1,00,000
- Actual: INR 1,10,000
- Variance: INR 10,000

Variance percentage:

(INR 10,000 / INR 1,00,000) × 100 = 10%

When the budgeted amount is zero, the percentage is undefined. The implementations return zero or a null value depending on the reporting context rather than performing division by zero.

## 8. Static and Flexible Budget Analysis

### 8.1 Static Budget

A static budget uses the original planned activity level.

It remains unchanged when actual operational volume differs from the original assumption.

Suppose production was planned at 5,000 units with a variable cost of INR 120 per unit.

The original budget is:

5,000 × INR 120 = INR 6,00,000

If actual production is 450 units during a particular month, the static monthly comparison uses one-twelfth of the annual budget.

### 8.2 Flexible Budget

A flexible budget adjusts expected expenditure to actual operational activity.

Formula:

Flexible Budget = Fixed Cost + (Variable Rate × Actual Activity)

Suppose:

- Fixed monthly cost: INR 0
- Variable rate: INR 120
- Actual production: 450 units

Flexible expenditure:

INR 0 + (INR 120 × 450)

= INR 54,000

If actual expenditure is INR 55,000:

Spending Variance = INR 55,000 − INR 54,000

= INR 1,000 unfavorable

This comparison provides a more useful assessment of expenditure control because it accounts for the actual activity level.

### 8.3 Why the Two Methods Differ

| Feature | Static budget | Flexible budget |
|---|---|---|
| Activity assumption | Original planned activity | Actual activity |
| Budget revision | No activity adjustment | Adjusted for activity |
| Primary purpose | Compare against original plan | Evaluate spending control |
| Variable costs | Based on planned volume | Based on actual volume |
| Fixed costs | Original fixed amount | Normally unchanged within the relevant range |

A flexible budget does not automatically change the approved financial allocation. It provides an adjusted performance benchmark.

## 9. Forecasting and Budget Utilization

### 9.1 Annualized Run-Rate Forecast

A run-rate forecast projects annual expenditure using actual financial activity recorded so far.

Formula:

Forecast = Year-to-Date Actual × 12 / Elapsed Months

Example:

- Actual expenditure after one month: INR 55,000
- Elapsed months: 1

Forecast:

INR 55,000 × 12 = INR 6,60,000

This is a simple projection, not a guaranteed future result.

It assumes that the observed monthly expenditure rate continues throughout the year.

It may be unsuitable when spending is seasonal, irregular, or concentrated in particular periods.

### 9.2 Budget Utilization

Budget utilization measures how much of an approved allocation has been consumed.

Formula:

Budget Utilization = (Actual Expenditure / Approved Budget) × 100

Example:

- Approved allocation: INR 6,00,000
- Actual expenditure: INR 55,000

Utilization:

(INR 55,000 / INR 6,00,000) × 100

= 9.17%

Utilization helps identify:

- Departments approaching their spending limits
- Accounts exceeding their allocations
- Unused budget allocations
- Unexpected expenditure
- Potential financial control problems

A utilization percentage should always be interpreted with reference to the reporting period.

## 10. Python Implementation

The Python file implements a complete object-oriented budgeting simulation.

### Main components

| Component | Responsibility |
|---|---|
| `Department` | Stores departmental limits |
| `BudgetLine` | Represents an individual revenue or expense allocation |
| `Budget` | Maintains budget data and lifecycle state |
| `BudgetPreparationService` | Validates and approves budgets |
| `ActualTransaction` | Represents recorded financial activity |
| `ActualLedger` | Maintains and aggregates transactions |
| `VarianceAnalyzer` | Calculates static and flexible variances |
| `BudgetReporter` | Produces financial reports |
| `save_budget()` | Persists budget data |
| `load_budget()` | Restores budget data |

### Important implementation decisions

Financial amounts use Python's `Decimal` rather than binary floating-point arithmetic.

This reduces precision problems in monetary calculations.

Dataclasses provide structured domain records, while enumerations restrict account types, cost behavior, and budget states.

The ledger uses transaction identifiers to prevent duplicate entries.

The persistence mechanism writes JSON to a temporary file before replacing the destination file.

This reduces the risk of leaving a partially written budget file after an interrupted write.

The reporting module exports variance results into CSV format.

The included assertions validate monetary rounding, variance classification, and persistence consistency.

### Execution

The program runs using the Python standard library.

It produces:

- Budget preparation information
- Annual variance report
- Monthly variance report
- Flexible budget analysis
- Department summaries
- Forecasting results
- Utilization calculations
- JSON budget persistence
- CSV variance report

## 11. JavaScript Implementation

The JavaScript file uses an event-driven approach to budgeting.

It is designed around Node.js and its standard library.

### Main components

| Component | Responsibility |
|---|---|
| `Department` | Departmental allocation data |
| `BudgetItem` | Budget account and cost calculations |
| `Budget` | Budget aggregate and event emitter |
| `BudgetPolicy` | Financial policy evaluation |
| `BudgetWorkflow` | Submission and approval |
| `ActualLedger` | Actual transaction processing |
| `VarianceEngine` | Variance calculations |
| `ReportingService` | Aggregation and forecasting |

### Event-driven design

The implementation uses Node.js `EventEmitter`.

Events are generated when:

- A budget line is registered.
- A budget changes state.
- A budget receives approval.
- An actual transaction is recorded.

This separates business operations from monitoring and reporting activities.

For example, recording a financial transaction emits a `transactionRecorded` event.

Other components can subscribe to this event to implement logging, notifications, or additional reporting.

### Policy evaluation

The `BudgetPolicy` class evaluates department spending limits and revision restrictions.

The workflow service uses the resulting validation report before allowing submission.

This separates financial rules from the lifecycle operations that apply them.

### Asynchronous persistence

The reporting service uses Node.js filesystem promises.

It writes a report to a temporary file and then renames the file into its final location.

The application also handles asynchronous failures through a top-level error handler.

The monetary calculations use JavaScript numbers with two-decimal rounding. This is suitable for the demonstration but is not a substitute for decimal arithmetic or integer minor-unit accounting in a production financial ledger.

## 12. C++17 Implementation

The C++17 implementation focuses on financial domain modeling and controlled transaction processing.

### Main components

| Component | Responsibility |
|---|---|
| `Department` | Stores spending limits |
| `BudgetLine` | Stores account planning information |
| `Budget` | Maintains the budget aggregate |
| `BudgetPreparation` | Validates and approves budget proposals |
| `ActualLedger` | Maintains actual transactions |
| `VarianceEngine` | Evaluates financial differences |
| `VarianceResult` | Stores calculated variance information |

### Financial representation

The implementation stores monetary amounts as integer minor units.

For INR, one major unit is represented by 100 minor units.

For example:

INR 1,250.50 = 125050 minor units.

This avoids many floating-point precision problems associated with repeated financial calculations.

### STL usage

The implementation uses:

- `std::vector` for budget lines and report results.
- `std::map` for departments and transaction records.
- `std::set` for duplicate budget-line detection.
- `std::find_if` for account matching.
- `std::optional` for optional accounting periods.
- `std::exception` for structured failure handling.

The transaction ledger performs identifier-based lookup through an ordered map.

This gives logarithmic lookup and insertion complexity.

The flexible budget engine evaluates actual activity against fixed, variable, and mixed expense definitions.

The application rejects invalid state transitions and duplicate transactions.

## 13. Java 17 Implementation

The Java implementation represents a more structured enterprise financial management system.

### Main components

| Component | Responsibility |
|---|---|
| `Budget` | Maintains financial planning state |
| `BudgetLine` | Immutable budget line record |
| `ActualTransaction` | Immutable financial transaction record |
| `BudgetPolicy` | Evaluates financial constraints |
| `AuthorizationService` | Controls user permissions |
| `BudgetWorkflow` | Manages budget submission and approval |
| `ActualLedger` | Stores actual transactions |
| `VarianceService` | Performs financial comparisons |
| `ReportingService` | Produces financial reports |
| `AuditEvent` | Records important workflow actions |

### Enterprise domain modeling

Java records provide immutable representations for departments, budget lines, transactions, variance results, and audit events.

The `Budget` class maintains its own lifecycle state and audit history.

The policy service validates department spending limits before submission.

The authorization service distinguishes between employees permitted to submit budgets and those permitted to approve them.

Custom exceptions identify different failure conditions:

- `BudgetValidationException`
- `BudgetStateException`
- `AuthorizationException`

This makes financial validation and workflow failures easier to distinguish.

### Auditability

Important state changes generate audit events containing:

- Event identifier
- Budget identifier
- Action
- Actor
- Timestamp
- Event details

The audit trail supports financial accountability and subsequent investigation.

The implementation also uses immutable collection copies to prevent callers from directly modifying internal budget records.

## 14. PostgreSQL Implementation

The PostgreSQL implementation models the budgeting process as a relational financial management database.

It is designed to demonstrate how financial planning and performance records can be stored and evaluated using database-level controls.

### 14.1 Database Structure

The database uses a dedicated `budgeting` schema.

| Table | Purpose |
|---|---|
| `departments` | Department master data |
| `employees` | Employee roles and authorization information |
| `accounts` | Revenue and expense classifications |
| `fiscal_periods` | Monthly financial periods |
| `budgets` | Budget master records |
| `budget_lines` | Department and account allocations |
| `budget_approvals` | Approval and rejection decisions |
| `actual_transactions` | Actual financial entries |
| `budget_audit_log` | Budget lifecycle audit records |
| `budget_forecasts` | Forecast values |

### 14.2 Relational Structure

The principal relationships are:

Departments
→ Budget Lines
→ Accounts

Budgets
→ Budget Lines
→ Actual Transactions

Budgets
→ Approval Records
→ Employees

Budgets
→ Audit Records

Budgets
→ Forecast Records
→ Fiscal Periods

These relationships are maintained through primary keys and foreign keys.

### 14.3 Data Integrity

The database applies several levels of validation.

**Primary key constraints**

Ensure that each record has a unique identifier.

**Foreign key constraints**

Prevent records from referencing nonexistent departments, employees, accounts, budgets, or fiscal periods.

**Unique constraints**

Prevent duplicate budget codes, duplicate account allocations within a department, and duplicate transaction references.

**Check constraints**

Prevent negative financial amounts, invalid fiscal periods, and invalid revision numbers.

**Triggers**

Enforce draft-only budget-line modifications and validate actual transaction relationships.

### 14.4 Stored Functions

The database includes the following financial calculation functions.

| Function | Purpose |
|---|---|
| `calculate_budget_amount()` | Calculates a budget line's planned value |
| `calculate_flexible_budget()` | Calculates activity-adjusted expenditure |
| `classify_variance()` | Determines favorable, unfavorable, or on-target status |
| `monthly_variance_report()` | Produces monthly comparisons |
| `flexible_variance_report()` | Compares actual expenditure with flexible budget values |

### 14.5 Stored Procedures

| Procedure | Purpose |
|---|---|
| `submit_budget()` | Validates and submits a draft budget |
| `approve_budget()` | Records approval and updates budget status |
| `reject_budget()` | Records rejection and its reason |
| `create_run_rate_forecast()` | Generates annualized financial forecasts |

Stored procedures centralize important financial operations.

The application can invoke these operations without duplicating every validation rule in its own code.

### 14.6 Reporting Views

| View | Purpose |
|---|---|
| `v_budget_line_details` | Combines budget, account, and department information |
| `v_actual_summary` | Aggregates actual transactions |
| `v_annual_variance` | Calculates annual budget differences |
| `v_department_budget_summary` | Produces departmental financial summaries |
| `v_budget_utilization` | Measures expenditure against allocations |

The indexes support common reporting filters and joins.

For larger databases, query plans should be evaluated using `EXPLAIN ANALYZE` against representative transaction volumes.

## 15. Financial Reporting and Management Interpretation

Budget reports should communicate more than numerical differences.

A useful financial performance report includes:

- Original approved budget
- Actual expenditure
- Actual revenue
- Financial variance
- Variance percentage
- Department responsible
- Account classification
- Budget utilization
- Operational activity
- Forecast expenditure
- Explanations for significant deviations

A practical management interpretation process follows:

1. Identify significant variances.
2. Identify the department and financial account responsible.
3. Determine whether the variance is favorable or unfavorable.
4. Compare actual activity with planned activity.
5. Separate changes in activity from changes in spending rates.
6. Investigate one-time and recurring financial events.
7. Estimate the effect on the full-year forecast.
8. Decide whether corrective action is necessary.
9. Record the explanation and responsible authority.

### Important distinctions

| Financial measure | What it explains |
|---|---|
| Budget variance | Difference between budget and actual |
| Activity variance | Difference caused by actual activity differing from planned activity |
| Spending variance | Difference between actual expenditure and an activity-adjusted budget |
| Revenue variance | Difference between actual and planned revenue |
| Utilization | Proportion of an allocation consumed |
| Forecast variance | Difference between projected and approved financial expectations |

A variance report identifies differences. It does not independently establish their causes.

## 16. Edge Cases and Financial Control Considerations

The implementations include controls for several important situations.

| Situation | Expected behavior |
|---|---|
| Negative budget allocation | Rejected |
| Negative actual transaction | Rejected |
| Duplicate transaction identifier | Rejected |
| Unknown department | Rejected |
| Missing budget line | Rejected |
| Invalid accounting period | Rejected |
| Approval before submission | Rejected |
| Actual transaction against draft budget | Rejected |
| Department spending limit exceeded | Submission rejected |
| Zero budget denominator | Division by zero avoided |
| Zero variance | Classified as on target |
| Revenue below budget | Unfavorable |
| Expense below budget | Favorable |
| Invalid flexible activity | Rejected |
| Unauthorized approval | Rejected in the Java and PostgreSQL workflows |

### Financial precision

Financial systems should avoid uncontrolled floating-point arithmetic.

The Python and Java implementations use decimal arithmetic.

The C++ implementation stores integer minor units.

The SQL implementation uses `NUMERIC`.

The JavaScript implementation uses rounded JavaScript numbers for demonstration purposes. A production financial system should use integer minor units or a dedicated decimal arithmetic implementation.

### Concurrency

Multiple users may update the same budget simultaneously.

A production implementation should use database transactions, appropriate row-level locking, and isolation controls.

The PostgreSQL approval and transaction procedures use row locks when validating budget state.

Unique constraints protect transaction identifiers against duplicate insertion.

### Security

Financial information requires strict access controls.

Important production controls include:

- Role-based permissions
- Separation of budget preparation and approval responsibilities
- Restricted access to salary and departmental spending information
- Database authentication and authorization
- Encrypted network connections
- Protected audit records
- Input validation
- Backup and recovery procedures
- Controlled changes to approved budgets
- Monitoring of unauthorized transaction attempts

The sample database demonstrates application-level role validation inside stored procedures. Production deployments should also implement database roles, grants, and row-level security where appropriate.

## 17. Implementation Comparison

| Dimension | Python | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Primary focus | Budget simulation | Event-driven processing | Financial calculation engine | Enterprise workflow | Relational financial system |
| Domain modeling | Dataclasses | Classes and objects | Structs and classes | Records and classes | Relational tables |
| State management | Enums | Private state and transitions | Enum-based state | Explicit lifecycle | Database status |
| Validation | Exceptions | Policy engine | Exceptions | Custom exceptions | Constraints and triggers |
| Actual transactions | Dictionary | Map | Ordered map | HashMap | Relational ledger |
| Variance analysis | Dedicated analyzer | Variance engine | Variance engine | Variance service | Functions and views |
| Forecasting | Annualized run rate | Reporting service | Forecast function | Reporting service | Stored procedure |
| Persistence | JSON and CSV | JSON | Runtime memory | Runtime memory | PostgreSQL |

## 18. Execution and Expected Outputs

### Python

Run the Python file with Python 3.10 or newer.

Expected generated files:

- `budget_2027.json`
- `budget_variance_report.csv`

### JavaScript

Run the JavaScript file with Node.js 18 or newer.

Expected generated file:

- `budget_variance_report.json`

### C++17

Compile with a C++17-compatible compiler.

The application prints annual and monthly variance reports, flexible budget comparisons, forecasts, and validation results.

### Java 17

Compile and execute `BudgetManagement.java` using Java 17.

The application produces approval events, audit records, variance reports, and financial summaries.

### PostgreSQL

Execute the SQL script using PostgreSQL 14 or newer.

The script creates the schema, master records, budget, approval records, actual transactions, functions, procedures, triggers, indexes, and reporting views.

The script assumes a clean or previously unused `budgeting` schema and suitable privileges to create database objects.

## 19. Limitations of the Demonstration

The implementations demonstrate core budgeting and variance analysis mechanisms. They are not complete enterprise accounting or ERP systems.

The following capabilities are outside the implemented scope:

- Double-entry bookkeeping
- General ledger reconciliation
- Tax calculations
- Accounts payable and receivable
- Payroll processing
- Multi-currency conversion
- Exchange-rate adjustments
- Depreciation schedules
- Capital asset accounting
- Cash flow statement preparation
- Consolidated financial statements
- Complex seasonal forecasting
- Statistical demand forecasting
- Inflation-adjusted budget scenarios
- Multi-level approval thresholds
- Full enterprise identity management

The monthly static budget comparison distributes annual budget amounts evenly across twelve months. This is a simplified assumption and may not reflect seasonal expenditure patterns.

The flexible budget examples use departmental activity as an input. A production system should maintain activity measures separately for each cost driver and budget line.

The rolling forecast procedure demonstrates annualized run-rate forecasting. It does not model seasonality, contractual commitments, inflation, or planned future operational changes.

The sample datasets are illustrative. Actual business use requires validated financial data, approved accounting policies, and appropriate authorization controls.
