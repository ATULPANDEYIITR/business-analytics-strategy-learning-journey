# Power BI Fundamentals: Interface, Datasets, and Reports

## Scope

This project models the core structure of a Power BI analytical workflow through five executable implementations. The central relationship is:

Power BI interface  
→ Dataset  
→ Data validation and refresh  
→ Report pages  
→ Visuals  
→ Measures and dimensions  
→ Filtered analytical views

The implementations use a sales analytics scenario with regions, products, categories, customers, datasets, report pages, visuals, refresh states, and validation rules.

The project focuses on three distinct concepts:

| Area | Technical meaning |
|---|---|
| Power BI interface | The user-facing environment used to work with data, fields, queries, models, visuals, filters, reports, and report pages |
| Dataset | The analytical data structure from which report visuals obtain data |
| Report | A presentation layer containing pages, visuals, filters, and analytical views built over a dataset |

The source files simulate these concepts without depending on the Power BI Desktop application or external libraries.

## Core Domain Model

The implementations use a consistent analytical model:

`Dataset → Sales rows → Dimensions → Measures → Visuals → Report pages → Report`

A sales record contains:

- Sale identifier
- Sale date
- Region
- Product
- Category
- Quantity
- Unit price
- Customer identifier

Revenue is calculated as:

`quantity × unit_price`

This distinction is important because quantity is an additive numeric field while revenue is a derived measure.

## Dataset Fundamentals

A dataset represents the governed analytical data available to a report.

The Python, JavaScript, Java, and PostgreSQL implementations explicitly represent dataset state. A dataset begins in a created state and can move to a refreshed state only after validation succeeds.

The validation rules include:

- Non-empty dataset names
- Unique sale identifiers
- Positive quantities
- Non-negative prices
- Required dimensional values
- Valid dates
- Consistent foreign-key relationships in PostgreSQL

A failed validation prevents the dataset from being treated as ready for report rendering.

This models an important operational distinction:

`Data exists` does not necessarily mean `data is ready for analysis`.

## Dataset Refresh

A refresh represents the operation that makes the latest valid source data available to analytical consumers.

The Python implementation performs synchronous validation and records a refresh date.

The JavaScript implementation models refresh as an asynchronous operation using a Promise. A failed refresh changes the dataset state to `Refresh Failed`.

The Java implementation uses an immutable sales collection and an explicit dataset state transition. Duplicate identifiers are rejected before the dataset becomes refreshed.

The PostgreSQL implementation stores refresh history separately from the dataset itself. This allows the database to retain operational information such as:

- Refresh start time
- Completion time
- Refresh status
- Number of loaded rows
- Error information

This separation supports auditability without mixing operational history into individual sales records.

## Report Structure

A report is modeled as a container over a dataset.

The report structure is:

`Report → Report Page → Visual`

The sample report contains:

| Page | Visual | Purpose |
|---|---|---|
| Executive Overview | Total Revenue | High-level KPI |
| Executive Overview | Revenue by Region | Regional comparison |
| Executive Overview | Quantity by Category | Category-level aggregation |
| North Analysis | North Revenue | Filtered regional KPI |

A report page is not the dataset itself. It is a presentation surface that consumes the dataset.

## Visuals

The implementations model common analytical visual categories:

- Card
- Table
- Bar chart
- Line chart
- Slicer

A card produces a single analytical value.

A table or grouped visual can expose values across a dimension.

A bar chart is represented as grouped measure values suitable for categorical comparison.

A slicer is represented as a filter concept rather than as a separate dataset.

The important relationship is:

`Visual → Measure + optional Dimension + optional Filter`

For example:

`Revenue + Region`

produces regional revenue groups, while:

`Revenue + Filter(North)`

produces the revenue value for North only.

## Measures and Dimensions

The model distinguishes between measures and dimensions.

Dimensions describe categories through which data can be grouped:

- Region
- Category
- Product
- Customer
- Date

Measures represent numeric analytical values:

- Revenue
- Quantity

The implementations calculate revenue from stored quantity and price instead of storing a duplicated revenue column.

This reduces update inconsistency because the derived value is calculated from the underlying transaction attributes.

## Python Implementation

The Python file uses:

- `dataclass` domain models
- `Enum` for dataset and visual states
- Lists for transactional records
- Dictionaries for grouped analytical results
- Sets for duplicate detection
- Exceptions for validation failures
- CSV loading for external data
- JSON export for report definitions
- Assertions through explicit validation logic
- Standard-library file handling

The `Dataset` class validates sales records and performs aggregation.

The `Visual` class evaluates a measure against optional dimensions and filters.

The `ReportPage` class renders multiple visuals against a refreshed dataset.

The `Report` class provides a report definition export.

The CSV loader demonstrates how a report-oriented data model can be populated from a flat source file.

The script also deliberately attempts an invalid zero-quantity transaction to demonstrate failure handling.

## JavaScript Implementation

The JavaScript file models the same analytical domain with JavaScript-specific behavior.

It uses:

- Classes
- Objects
- `Map`
- `Set`
- Promises
- Asynchronous refresh behavior
- Structured JSON output
- Node.js file-system APIs
- Explicit error propagation

Aggregation uses `Map` to group revenue or quantity by a selected dimension.

The asynchronous `refresh()` operation demonstrates why data refresh should be treated as an operational state transition rather than an unconditional assignment.

The report definition is exported as JSON so that the logical report structure can be inspected separately from its rendered representation.

The JavaScript implementation also handles a failed refresh caused by invalid quantity data.

## C++17 Implementation

The C++17 program takes a different perspective and implements a repository governance engine around the analytical artifact.

It models:

- Pull Requests
- Commits
- Reviews
- Status checks
- Protected branches
- Approval requirements
- Conversation resolution
- Merge conflicts
- Merge strategies

The program evaluates whether a Pull Request is eligible for merging.

This is deliberately separate from dataset and report presentation. A dataset can be valid while the repository change containing the report definition is still blocked by governance controls.

The merge engine considers:

- Draft state
- Closed state
- Source and target branches
- Commit availability
- Merge conflicts
- Eligible reviewers
- Current approvals
- Stale approvals
- Required status checks
- Unresolved conversations

The implementation uses `unordered_set` for reviewer and required-check membership and `unordered_map` for status lookup.

The primary merge evaluation is approximately linear in the number of reviews and checks.

## Java 17 Implementation

The Java implementation represents an enterprise-oriented analytical and governance service.

It uses:

- Records for immutable domain values
- Enums for explicit states
- Collections and sets
- Streams for aggregation
- Immutable lists
- Custom validation through constructors
- A dedicated merge-eligibility service
- Explicit policy objects
- Timestamped review decisions

The `Dataset` class performs revenue aggregation through Java Streams.

The `BranchProtectionPolicy` record defines repository-level governance independently from review decisions.

The `MergeEligibilityService` evaluates current approvals, reviewer eligibility, required checks, unresolved conversations, and conflicts.

Stale approvals are deliberately excluded from the approval count.

This reflects an important governance distinction:

`A review decision exists` does not imply `the decision currently satisfies the merge policy`.

## PostgreSQL Implementation

The PostgreSQL implementation represents the analytical environment relationally.

Its schema contains:

- Repositories
- Users
- Datasets
- Regions
- Categories
- Products
- Customers
- Sales
- Refresh history
- Reports
- Report pages
- Visuals
- Branch protection policies
- Pull Requests
- Commits
- Reviews
- Review comments
- Status checks
- Required status checks

Foreign keys preserve relationships between the entities.

Check constraints enforce rules such as:

- Positive quantities
- Non-negative prices
- Positive page ordering
- Non-negative approval requirements
- Non-negative unresolved conversations

Unique constraints prevent duplicate dataset names, product names, commit hashes, report pages, and status-check definitions.

## PostgreSQL Analytical Queries

The `calculate_revenue` function provides a reusable dataset-level measure.

The `dataset_revenue_by_region` view exposes regional revenue and units.

The `report_inventory` view provides a report metadata inventory containing pages and visuals.

The `merge_eligibility` function evaluates repository-level conditions for a Pull Request.

This separates database-level governance from analytical reporting while keeping both models in one executable relational case study.

## Transactional Integrity

The refresh demonstration uses:

`BEGIN → INSERT refresh history → UPDATE dataset → COMMIT`

The transaction ensures that the operational refresh record and dataset state change are committed together.

If the transaction fails before `COMMIT`, PostgreSQL can roll back the complete operation instead of leaving inconsistent refresh metadata.

## Interface, Dataset, and Report Distinctions

These concepts should not be treated as interchangeable.

| Concept | Primary responsibility |
|---|---|
| Interface | Provides controls for interacting with data, models, fields, visuals, filters, and reports |
| Dataset | Supplies structured analytical data and measures |
| Report | Presents analytical results through pages and visuals |
| Visual | Encodes one analytical view of selected measures and dimensions |
| Refresh | Updates dataset availability from its underlying data state |
| Filter | Restricts the data context used by a visual |
| Measure | Defines a numeric analytical calculation |
| Dimension | Provides grouping or slicing context |

A report depends on a dataset, but the dataset does not depend on a particular report page.

Multiple report pages can consume the same dataset.

A dataset can also support multiple reports.

## Filtering and Analytical Context

The sample implementations demonstrate filtering through the North region scenario.

Without a filter:

`Revenue = Sum(all transaction revenue)`

With a North filter:

`Revenue = Sum(revenue where region = North)`

This is conceptually different from permanently modifying the dataset.

The filter changes the analytical context used by the visual while leaving the underlying transaction data unchanged.

## Data Quality and Failure Handling

The implementations deliberately reject invalid states.

Examples include:

- Duplicate sale identifiers
- Zero or negative quantities
- Negative unit prices
- Missing regions
- Missing product information
- Invalid dates
- Unrefreshed datasets
- Missing required status checks
- Failed status checks
- Stale approvals
- Unresolved conversations
- Merge conflicts
- Draft Pull Requests

These failures represent different layers of an analytical system.

`Dataset validation` protects data integrity.

`Report validation` protects rendering assumptions.

`Repository governance` protects the integrity of changes being introduced into the analytical solution.

## Performance Considerations

The sample data is small, but the implementation choices reflect scalable patterns.

Python aggregation uses dictionaries with average O(n) grouping behavior.

JavaScript uses `Map` for efficient grouping.

C++ uses hash-based containers for reviewer and status-check membership.

Java Streams provide declarative aggregation but still require traversal of the source collection.

PostgreSQL indexes are applied to access patterns involving:

- Dataset and date
- Region
- Pull Request reviews
- Pull Request status checks

Indexes are not added indiscriminately because every additional index introduces storage cost and write overhead.

## Security Considerations

The source files model security through validation and governance rather than through application authentication.

Important controls include:

- Strict data validation
- Repository-level branch protection
- Required approvals
- Reviewer eligibility
- Stale approval rejection
- Required automated checks
- Conversation-resolution requirements
- Direct-push restrictions
- Force-push restrictions
- Foreign-key enforcement
- Check constraints
- Transactional integrity

In an operational Power BI environment, access control would also need to address workspace permissions, dataset permissions, report sharing, data-source credentials, and row-level access requirements. Those deployment controls are outside the executable local models in this project.

## Practical Workflow

The implemented workflow can be represented as:

`Source data`
→ `Dataset validation`
→ `Dataset refresh`
→ `Measures and dimensions`
→ `Report pages`
→ `Visual evaluation`
→ `Analytical output`

For governed repository development:

`Report change`
→ `Pull Request`
→ `Code review`
→ `Approval decisions`
→ `Status checks`
→ `Branch protection`
→ `Merge eligibility`

These are related workflows but solve different problems.

The first workflow establishes analytical data and presentation.

The second controls how changes to analytical assets become part of a governed repository.

## Edge Cases

The implementations cover several boundary conditions.

A dataset with duplicate transaction identifiers is rejected.

A zero-quantity transaction is rejected.

A report cannot render a dataset that has not completed refresh.

A stale approval cannot satisfy a current approval requirement.

A failed required status check blocks merge eligibility.

A Pull Request with unresolved conversations is blocked when the policy requires resolution.

A merge conflict blocks the final merge decision even when approvals and status checks are valid.

## Limitations

The implementations are local technical models rather than Power BI Desktop or Power BI Service integrations.

They do not implement:

- Power Query M execution
- DAX engine semantics
- VertiPaq storage
- Power BI workspace APIs
- Gateway configuration
- Row-level security execution
- DirectQuery
- Import-mode storage
- Composite models
- Power BI Service deployment pipelines
- Actual visual rendering

The models instead isolate the fundamental architectural relationships between datasets, analytical calculations, reports, visuals, validation, and governed development.

## File Responsibilities

| File | Main responsibility |
|---|---|
| Python | Dataset lifecycle, validation, aggregation, visual evaluation, report definition export |
| JavaScript | Asynchronous refresh, Map-based aggregation, report modeling, JSON export |
| C++17 | Repository governance and merge-eligibility engine |
| Java 17 | Immutable enterprise domain model and policy-driven governance service |
| PostgreSQL | Relational dataset, report metadata, governance schema, analytical views, functions, constraints, and transactions |
| README.md | Technical description of the complete Power BI fundamentals case study |

## Technical Relationship

The five implementations intentionally use different engineering perspectives while preserving the same core analytical concepts.

Python emphasizes rapid domain modeling and data processing.

JavaScript emphasizes asynchronous state management and structured event-oriented processing.

C++17 emphasizes deterministic governance evaluation and efficient container-based decision logic.

Java 17 emphasizes immutable enterprise domain objects and explicit policy services.

PostgreSQL emphasizes relational integrity, aggregation, reusable database functions, reporting metadata, and transactional state management.

Together they establish a concrete model of:

`Data → Dataset → Measures → Report → Visuals → Analytical Context`

while separating the repository governance workflow:

`Change → Review → Approval → Policy Enforcement → Merge`
