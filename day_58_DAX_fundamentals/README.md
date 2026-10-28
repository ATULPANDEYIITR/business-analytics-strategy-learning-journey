# DAX Fundamentals: Measures, Calculated Columns and DAX Logic

## Scope

This project models fundamental DAX concepts through a small sales-analysis domain.

The central distinction is between **calculated columns** and **measures**:

- A calculated column evaluates an expression for each row and stores a resulting value as part of the model.
- A measure evaluates when a report query requires it and responds to the current filter context.
- `CALCULATE` changes the evaluation context before a measure is evaluated.
- `DIVIDE`-style logic prevents invalid division when the denominator is zero.
- Dimension filters such as region and category can change the rows available to a measure without changing the definition of that measure.

The five implementations use the same analytical domain while emphasizing different engineering perspectives.

## Domain Model

The model represents sales transactions across regions, products, and categories.

    Region
      |
      +---- Sales Fact ---- Date
               |
               +---- Product ---- Category

A transaction contains:

| Field | Meaning |
|---|---|
| Order ID | Unique transaction identifier |
| Order Date | Transaction date |
| Region | Geographic reporting context |
| Product | Sold product |
| Category | Product classification |
| Quantity | Number of units sold |
| Unit Price | Selling price per unit |
| Unit Cost | Cost per unit |

The analytical relationship is:

    Row data
       |
       +--> Calculated-column expressions
       |
       +--> Filtered context
               |
               +--> Measures
                       |
                       +--> Aggregation
                       |
                       +--> Margin / ratios
                       |
                       +--> Business decisions

## Core DAX Concepts

### Calculated Columns

The source rows support row-level expressions such as:

`Sales Amount = Quantity × Unit Price`

`Cost Amount = Quantity × Unit Cost`

`Profit Amount = Sales Amount - Cost Amount`

`Profit Margin = DIVIDE(Profit Amount, Sales Amount, 0)`

`Sales Band` classifies each transaction according to its calculated sales amount.

These expressions have row context because the calculation operates on one current row at a time.

A calculated column is useful when the resulting value needs to exist for every row and participate in grouping, filtering, or other row-level operations.

## Measures

Measures aggregate model data at query time.

The implemented measures include:

| Measure | Meaning |
|---|---|
| Total Sales | Sum of sales amounts |
| Total Cost | Sum of cost amounts |
| Total Profit | Sum of profit amounts |
| Profit Margin | Total profit divided by total sales |
| Average Order Value | Total sales divided by transaction count |

A measure is not equivalent to a stored row value. Its result depends on the current evaluation context.

For example, `Total Sales` can produce a company-wide value, a regional value, or a category value without requiring separate stored columns for every possible grouping.

## Filter Context

Filter context determines which rows participate in measure evaluation.

The implementations model contexts such as:

- all transactions
- North region
- South region
- Technology category
- North plus Technology
- South plus Technology
- product-specific contexts

The conceptual distinction is:

    Same measure definition
            |
            +---- All rows
            |       -> Total Sales
            |
            +---- North filter
            |       -> North Sales
            |
            +---- South + Technology
                    -> South Technology Sales

The measure remains the same while the evaluation context changes.

## CALCULATE-Style Logic

`CALCULATE` is important because it evaluates an expression after modifying filter context.

The source implementations represent this idea explicitly through a context-building operation followed by measure evaluation.

For example:

`CALCULATE([Total Sales], Region = "North")`

Conceptually means:

    Existing context
          |
          +--> apply Region = North
                    |
                    +--> evaluate Total Sales

This is distinct from merely creating a new calculated column.

The JavaScript, C++, and Java implementations expose context changes as explicit service or model operations. The PostgreSQL implementation uses filtered queries and a reusable `sales_measure` function to express the same analytical pattern relationally.

## Row Context and Filter Context

The two contexts should not be treated as interchangeable.

| Context | Primary purpose | Example |
|---|---|---|
| Row context | Evaluate a current row | `Quantity * Unit Price` |
| Filter context | Determine rows visible to a measure | Region = North |
| Modified filter context | Change evaluation conditions | `CALCULATE([Total Sales], Category = Technology)` |

A calculated column naturally operates over individual rows.

A measure operates over a set of rows established by the current report context.

## Python Implementation

The Python file defines `SalesRow` as an immutable dataclass and `SalesModel` as the analytical model.

Important mechanisms include:

- dataclass-based domain modeling
- explicit validation
- duplicate-order detection
- calculated-column-style methods
- measure-style aggregation methods
- filter-context construction
- `calculate()` for context-changing evaluation
- region and category summarization
- product ranking
- assertions for expected analytical results

The Python implementation also handles empty contexts safely. A zero sales denominator produces a zero margin rather than a runtime division error.

The model validates business conditions before analytical processing. Negative quantities, negative prices, duplicate identifiers, and costs above selling prices are rejected.

## JavaScript Implementation

The JavaScript file uses a Node.js-compatible event-driven model.

It uses:

- classes
- `Map`
- `Set`
- immutable row objects
- `EventEmitter`
- array transformations
- explicit validation
- context filtering
- measure evaluation
- precomputed product totals

The `Map` used for product totals avoids repeatedly scanning every transaction when top products are requested.

The `EventEmitter` introduces an event-driven reporting boundary. A generated report emits a structured event after analytical calculations have completed.

JavaScript-specific asynchronous infrastructure is not required for this in-memory model because the calculations are deterministic and local. Introducing asynchronous operations without an external workload would add complexity without improving the analytical design.

## C++17 Implementation

The C++ program presents the model as a technical analytical engine.

It uses:

- `struct` for domain records
- `class` for model ownership
- STL vectors
- unordered sets for validation
- unordered maps for product aggregation
- ordered maps for deterministic grouped output
- algorithms for ranking
- exceptions for invalid model state
- explicit measure evaluation

The model evaluates a `MeasureResult` containing:

- sales
- cost
- profit
- margin
- order count

This makes aggregate state explicit rather than returning loosely structured values.

The implementation also separates filtering from evaluation. A filtered vector represents a particular context, and the measure engine evaluates that context.

## Java 17 Implementation

The Java program models an enterprise-oriented analytical service.

Java-specific mechanisms include:

- records for immutable domain values
- enums for controlled categories and sales bands
- interfaces for measures
- immutable collections
- service-layer domain behavior
- custom validation exceptions
- streams for aggregation
- explicit context filtering
- policy objects for classification thresholds

The `Measure` interface separates the concept of a measure from the service that supplies the data context.

`SalesService.calculate()` demonstrates the relationship between context construction and measure evaluation.

The `Policy` record centralizes sales-band thresholds so the classification rule is explicit and validated.

## PostgreSQL Implementation

The PostgreSQL script uses a small star-style relational model.

The principal structures are:

| Object | Role |
|---|---|
| `dim_region` | Region dimension |
| `dim_category` | Category dimension |
| `dim_product` | Product dimension |
| `dim_date` | Date dimension |
| `fact_sales` | Transaction fact table |
| `branchless_measure_policy` | Threshold configuration |
| `calculated_sales_columns` | Row-level analytical view |

The fact table contains foreign keys to dimensions and database constraints for quantities and prices.

The database enforces:

- unique order identifiers
- positive quantities
- non-negative monetary values
- unit cost not exceeding unit price
- valid dimension relationships

This prevents invalid business states from entering the analytical model.

## PostgreSQL Calculated-Column Perspective

The `calculated_sales_columns` view exposes row-level expressions.

It calculates:

- sales amount
- cost amount
- profit amount
- profit margin
- sales band

The values are derived from the current fact row.

The view therefore provides a relational representation of calculations that resemble calculated-column logic.

The database does not pretend that these are physically identical to Power BI calculated columns. The purpose is to make the evaluation distinction explicit in a relational environment.

## PostgreSQL Measure Perspective

The SQL aggregation queries calculate measures from the fact table.

For example:

- `SUM(quantity * unit_price)` represents total sales.
- `SUM(quantity * (unit_price - unit_cost))` represents total profit.
- profit divided by sales represents profit margin.

The `sales_measure` function accepts optional region and category filters. This provides a reusable relational equivalent of evaluating the same measure under different contexts.

## Validation and Failure Handling

The implementations intentionally reject invalid business data.

Examples include:

| Failure | Handling |
|---|---|
| Duplicate order ID | Validation failure |
| Zero or negative quantity | Validation failure |
| Negative price | Validation failure |
| Unit cost greater than unit price | Validation failure |
| Empty analytical context | Returns zero aggregates |
| Zero sales denominator | Margin returns zero |
| Invalid top-N limit | Explicit exception |
| Invalid PostgreSQL row | Constraint violation |

The PostgreSQL script also demonstrates a transaction and savepoint for an intentionally invalid insert.

## Performance Considerations

The dataset is intentionally small, but the implementation choices reflect larger analytical systems.

### Python

Filtering is linear in the number of rows. Product totals use a dictionary so aggregation remains a single pass.

### JavaScript

Product totals are indexed in a `Map` during model initialization. Repeated top-product queries therefore avoid reconstructing the product aggregation from raw rows.

### C++17

Hash-based containers provide average constant-time lookup and aggregation. Ordered maps are used where deterministic output is useful.

### Java 17

Streams make grouping and aggregation concise. Immutable records reduce accidental state mutation, while the service performs grouping only when requested.

### PostgreSQL

Indexes are placed on fact-table date, region, and product foreign keys because these columns are natural filtering and join paths. Aggregations remain database-side rather than transferring raw rows to an application.

## Security and Data Integrity

The implementations emphasize integrity rather than authentication because the domain is an analytical model rather than a network service.

Important controls include:

- validation before calculations
- immutable domain objects where practical
- database primary keys
- foreign keys
- check constraints
- controlled enum values
- safe division
- transactional rollback
- explicit failure handling
- avoidance of dynamically constructed SQL

The PostgreSQL model relies on typed parameters and relational constraints rather than concatenating user input into executable SQL.

## Distinguishing the Main Concepts

The four fundamental ideas can be separated as follows:

    Calculated Column
        |
        +--> evaluates row by row
        +--> produces a value associated with each row

    Measure
        |
        +--> evaluates at query time
        +--> aggregates according to current context

    Filter Context
        |
        +--> determines which rows a measure can see
        +--> comes from report filters, groupings, slicers, or context changes

    CALCULATE
        |
        +--> modifies filter context
        +--> evaluates an expression under the modified context

Confusing these concepts leads to incorrect DAX designs.

A calculated column is not simply a measure stored in a table, and a measure is not simply a calculated column evaluated later.

## Example Analytical Workflow

A realistic report workflow represented by the artifacts is:

    Sales transactions
            |
            v
    Validate row data
            |
            v
    Build row-level calculations
            |
            v
    Create report filter context
            |
            +--------------------+
            |                    |
            v                    v
       Total Sales          Total Profit
            |                    |
            +---------+----------+
                      |
                      v
                Profit Margin
                      |
                      v
              Regional / Category
                   reporting

A user can then change the context from all regions to one region or from all products to one category while retaining the same measure definitions.

## Expected Baseline

The supplied records produce these baseline values:

| Metric | Value |
|---|---:|
| Total Sales | 10,555.00 |
| Total Cost | 7,150.00 |
| Total Profit | 3,405.00 |
| Profit Margin | 32.26% |
| Order Count | 8 |

These values are validated directly in the Python, JavaScript, C++17, and Java 17 programs and through SQL validation.

## Edge Cases

The model explicitly considers:

- empty filter contexts
- zero denominators
- duplicate identifiers
- invalid quantities
- invalid monetary values
- invalid cost-to-price relationships
- invalid top-N limits
- combined region and category filters
- repeated product aggregation
- database transaction rollback

The goal is to keep analytical results deterministic and prevent invalid states from being silently converted into plausible-looking business metrics.

## Practical Distinction Between Stored and Dynamic Logic

A useful design decision is to keep logic at the level where it belongs.

Use row-level logic when a value belongs naturally to each transaction, such as:

`Quantity × Unit Price`

Use measures when the result depends on the selected analytical context, such as:

`Total Profit`

Use context-changing logic when a measure must be evaluated under an explicitly altered condition, such as:

`CALCULATE([Total Sales], Region = "North")`

This separation makes models easier to validate, reuse, and reason about.

## File Responsibilities

| File | Primary perspective |
|---|---|
| Python | Validated analytical model and DAX-style calculation semantics |
| JavaScript | Event-driven analytical processing and indexed aggregation |
| C++17 | Explicit analytical engine with STL-based performance structures |
| Java 17 | Enterprise domain model, measure interface, policies, and services |
| PostgreSQL | Relational star schema, constraints, views, functions, transactions, and analytical queries |

Each implementation expresses the same domain without mechanically translating the previous implementation. The differences show how row-level calculations, measures, context, validation, and aggregation can be represented across programming and database environments.
