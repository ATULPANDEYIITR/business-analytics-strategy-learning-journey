# Advanced Power BI: Measures and Analytical Calculations

## Scope

This project models advanced Power BI analytical calculations through five complementary implementations. The central subject is the design of measures whose results change correctly when the analytical filter context changes.

The four major analytical concerns are treated as distinct mechanisms:

| Area | Meaning in the model |
|---|---|
| Base measures | Reusable numerical definitions such as revenue, cost, margin, and quantity |
| Context-sensitive measures | Calculations whose result changes according to selected dates, regions, products, channels, or customers |
| Time intelligence | Period comparisons, year-to-date values, previous-period values, and rolling windows |
| Advanced analytical measures | Ranking, contribution percentages, distinct counts, average order value, and semi-additive inventory |

The implementations use a common business scenario containing sales transactions, customers, products, regions, channels, and inventory snapshots.

The relationship between the major concepts is:

`Fact Sales → Filter Context → Base Measures → Derived Measures → Analytical Decisions`

A measure is not simply a stored column. It is an expression evaluated against the current analytical context.

## Analytical Domain Model

The model represents a simplified sales organization.

```text
Date
 │
 ├── Region
 ├── Product
 ├── Channel
 └── Customer
        │
        ▼
    Fact Sales
        │
        ├── Revenue
        ├── Cost
        ├── Margin
        ├── Distinct Customers
        └── Order Value
                │
                ▼
        Derived Measures
                │
        ├── Margin %
        ├── Previous Month
        ├── MoM %
        ├── YTD
        ├── Rolling 7 Days
        ├── % of Total
        └── Product Rank

Inventory Snapshots
        │
        ▼
Latest Available Inventory
```

The sales fact is additive for revenue, cost, margin, and quantity. Inventory is treated as semi-additive because historical snapshots should not normally be summed across time.

## Measure Design

The fundamental revenue calculation is:

`Revenue = Quantity × Unit Price`

Cost is:

`Cost = Quantity × Unit Cost`

Margin is:

`Margin = Revenue − Cost`

Margin percentage is:

`Margin % = Margin / Revenue`

The implementations protect division operations against zero denominators. This is important because an analytical measure should return a controlled result when a selected context contains no transactions.

The model also distinguishes calculated columns from measures conceptually. Revenue can be calculated at transaction level, while percentage-of-total, ranking, rolling values, and period comparisons require evaluation across a selected collection of rows.

## Filter Context

Filter context determines which fact rows participate in a measure.

Examples include:

- February 2026
- North region
- Laptop product
- Online channel
- Enterprise customers
- combinations of these selections

A filter context can be represented as:

`Date + Region + Product + Channel + Customer`

The Python implementation uses the `FilterContext` dataclass. The JavaScript implementation uses a `FilterContext` class backed by `Set` objects. The C++ implementation represents context with ordered sets. Java uses immutable sets inside a record.

This makes context changes explicit rather than hiding them inside global state.

For example, product ranking requires evaluating revenue separately for every product while retaining the surrounding date, region, channel, and customer filters.

## Context Modification

A central advanced-measure pattern is evaluating a numerator under one context while evaluating a denominator under a deliberately modified context.

The percentage-of-total calculation is:

`Selected Revenue / Revenue With Selected Dimensions Removed`

The implementations remove product, region, channel, and customer filters while retaining the selected date context.

This is conceptually similar to the DAX pattern using `CALCULATE` with filter-removal functions such as `REMOVEFILTERS`.

The distinction matters because a percentage is meaningful only when the numerator and denominator have deliberately defined contexts.

## Time Intelligence

The model contains a calendar dimension covering January through March 2026.

The Python, JavaScript, and Java implementations explicitly generate date sets. PostgreSQL uses `dim_date` and date arithmetic. C++ represents selected dates as a set.

### Previous Month

Previous-month revenue shifts the current month context to the preceding calendar month.

The measure protects against the absence of a previous period:

`Previous Month Revenue = 0`

when no earlier period exists.

### Month-over-Month Change

The calculation is:

`MoM % = (Current Revenue − Previous Revenue) / Previous Revenue`

A zero previous-period value is handled without division by zero.

### Year-to-Date

YTD revenue begins on January 1 of the anchor year and ends on the selected anchor date.

This is different from simply summing all rows visible in a report. The measure explicitly defines the period represented by the calculation.

### Rolling Seven-Day Revenue

The rolling measure uses the current date as an anchor and includes the anchor plus six preceding dates.

The calendar table is important because dates without transactions still belong to the analytical window.

The SQL implementation therefore starts from `dim_date` and left joins sales instead of generating the window solely from transaction dates.

## Distinct Counts

Distinct customers cannot safely be calculated by summing daily customer counts.

A customer appearing on several days should still contribute one customer to a period-level distinct count.

The implementations therefore use:

- Python `set`
- JavaScript `Set`
- C++ `unordered_set`
- Java Stream `distinct`
- PostgreSQL `COUNT(DISTINCT customer_id)`

This is an example of a measure whose aggregation behavior differs from ordinary additive measures.

## Average Order Value

Average order value is calculated from order-level totals rather than averaging individual transaction prices.

The model treats each `sale_id` as an order identifier:

`AOV = Total Revenue / Number of Orders`

This avoids a common analytical error in which transaction-level averages are used when the business metric is defined at order level.

## Product Ranking

Product ranking evaluates the revenue measure separately for each visible product.

The ranking workflow is:

```text
Selected Context
      │
      ▼
Visible Products
      │
      ▼
Revenue per Product
      │
      ▼
Sort Descending
      │
      ▼
Assign Rank
```

Ties receive the same rank. The following rank is skipped according to competition-ranking semantics.

For example:

`100, 90, 90, 70`

produces ranks:

`1, 2, 2, 4`

The Python, JavaScript, C++, and Java implementations explicitly preserve this behavior.

## Semi-Additive Inventory

Inventory is fundamentally different from sales.

Sales from January and February can be summed to obtain a two-month sales total. Inventory snapshots from January and February cannot normally be summed because they represent point-in-time balances.

The model therefore calculates:

`Latest Inventory = Sum of Units at Latest Available Snapshot`

The SQL implementation first determines the maximum snapshot date and then sums inventory only at that date.

This distinction is essential when designing Power BI measures for balances, headcount, account balances, inventory, and other snapshot-style facts.

## Python Implementation

The Python implementation is an in-memory analytical model designed around explicit domain objects.

Important mechanisms include:

| Mechanism | Implementation |
|---|---|
| Domain data | `dataclass` records |
| Categories | `Enum` |
| Filter context | `FilterContext` |
| Fact filtering | `_filtered_sales` |
| Revenue | `revenue()` |
| Margin | `margin()` |
| Distinct customers | Set comprehension |
| Time intelligence | Date-set generation |
| Rolling calculation | `rolling_revenue()` |
| Filter removal | `percent_of_total()` |
| Ranking | `product_rank()` |
| Semi-additive inventory | `latest_inventory()` |
| Validation | Assertions and typed checks |

The Python model intentionally uses standard-library features only.

Its `evaluate()` method provides a consolidated analytical result while individual methods remain independently testable.

The assertions cover positive revenue, distinct-customer behavior, previous-period behavior, rolling calculations, inventory snapshots, ranking, and empty filter contexts.

## JavaScript Implementation

The JavaScript implementation emphasizes event-driven evaluation and JavaScript collection semantics.

`Map` and `Set` are used for grouped calculations and filter membership.

The `MeasureEventBus` introduces an event-driven boundary around analytical results. Independent listeners can subscribe to the `measureEvaluated` event, and handlers are dispatched with `Promise.all`.

The implementation therefore provides a different engineering perspective from the Python version rather than translating Python syntax directly.

Validation occurs in constructors, while analytical failures are propagated through rejected promises and the process exit code.

## C++17 Implementation

The C++ implementation treats the analytical engine as a strongly typed technical case study.

Important structures include:

- `Sale`
- `InventorySnapshot`
- `FilterContext`
- `GovernanceAnalytics`

`FilterContext::matches()` centralizes filtering rules.

The implementation uses STL containers for dimension selections and customer distinctness. Product ranking uses sorting and explicit competition-rank handling.

Currency values use `double` for compact demonstration purposes. A production financial implementation should use a fixed-point representation or an integer minor-unit representation when exact monetary arithmetic is required.

The C++ program reports complexity explicitly:

- Fact filtering: O(n)
- Distinct customer collection: O(n) expected with hashing
- Product ranking: O(p log p)
- Inventory latest-date scan: O(i)

where `n` is the number of fact rows, `p` is the number of visible products, and `i` is the number of inventory rows.

## Java 17 Implementation

The Java implementation uses explicit domain modeling and immutable records.

The principal domain records are:

- `Sale`
- `InventorySnapshot`
- `FilterContext`
- `RankedProduct`
- `MeasureResult`

The `MeasurePolicy` interface provides a policy boundary for validating analytical contexts.

`StandardMeasurePolicy` demonstrates how enterprise applications can separate policy validation from measure calculation.

Java's `BigDecimal` is used for monetary calculations, avoiding binary floating-point representation issues.

The service layer is represented by `AnalyticsService`, which owns the measure operations while the records remain focused on domain state.

The result of the analytical evaluation is represented by an immutable `MeasureResult`.

## PostgreSQL Implementation

The SQL implementation uses a relational star-schema structure.

The primary tables are:

| Table | Role |
|---|---|
| `dim_date` | Calendar and time-intelligence attributes |
| `dim_region` | Geographic dimension |
| `dim_product` | Product and category dimension |
| `dim_channel` | Sales-channel dimension |
| `dim_customer` | Customer dimension |
| `fact_sales` | Transaction-level additive facts |
| `fact_inventory_snapshot` | Point-in-time inventory facts |

The database contains primary keys, foreign keys, unique constraints, check constraints, and indexes.

The sales fact references all relevant dimensions, producing a structure suitable for analytical grouping.

## Database-Level Validation

`fn_validate_sale()` is implemented as a trigger function.

It rejects a sale when unit cost exceeds unit price.

This illustrates an important distinction between analytical validation and transactional validation:

- Analytical validation checks whether a measure can be evaluated correctly.
- Database validation prevents invalid state from being persisted.

The database also protects quantity, price, inventory, and dimensional relationships through constraints.

## SQL Analytical Queries

The SQL script demonstrates several analytical patterns.

### Monthly Measures

A common table expression groups revenue, cost, margin, distinct customers, and orders by month.

`LAG()` provides previous-month revenue without requiring a self-join.

### Ranking

`RANK()` ranks products by revenue.

The query also calculates each product's percentage contribution to the selected total using a window aggregate.

### Region Contribution

The region query calculates revenue per region and divides it by the selected monthly total.

This corresponds to the conceptual distinction between a filtered numerator and a denominator with a selected dimension removed.

### Rolling Windows

The rolling seven-day calculation uses:

`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`

The date dimension ensures that the window remains calendar-based even when a day has no transactions.

### Latest Inventory

The latest snapshot is identified with `MAX(snapshot_date)` and only that snapshot is aggregated.

This prevents the incorrect addition of historical inventory balances.

## Performance Considerations

Advanced measures should be designed with the data model in mind.

Important considerations include:

- Keep a clear star schema.
- Prefer numeric surrogate keys for large dimensions.
- Keep dimensions relatively narrow.
- Use a proper calendar table for time intelligence.
- Avoid unnecessary high-cardinality calculated columns.
- Prefer reusable base measures over repeated expressions.
- Filter dimensions rather than scanning unnecessarily large fact subsets.
- Use database indexes according to actual query patterns.
- Avoid excessive iterator-style calculations when a simple aggregation is sufficient.
- Measure performance using representative data volumes.

The PostgreSQL implementation indexes transaction dates and common product, region, and customer access paths.

The in-memory implementations deliberately expose scan complexity so the cost of repeated filtering remains visible.

## Calculation Correctness

Several common analytical errors are explicitly avoided.

| Error | Correct treatment |
|---|---|
| Dividing by zero | Return a controlled zero result |
| Summing historical inventory | Use latest available snapshot |
| Summing daily distinct customers | Count distinct customers over the selected period |
| Averaging transaction prices for AOV | Aggregate order revenue first |
| Ranking against unrelated context | Preserve surrounding filters |
| Calculating rolling periods only from transaction dates | Use a continuous calendar |
| Mixing numerator and denominator contexts | Define filter removal explicitly |
| Treating all measures as additive | Classify measures by aggregation behavior |

## Edge Cases

The implementations cover several failure conditions:

- Empty filter contexts
- Unknown products
- No previous month
- Zero previous-period revenue
- Zero revenue
- Empty inventory selection
- Invalid quantities
- Negative prices
- Negative inventory
- Duplicate identifiers
- Invalid dates
- Invalid categorical values
- Missing transactional data on calendar dates

A production Power BI model should make equivalent decisions explicitly rather than allowing undefined behavior to propagate into visuals.

## Security Considerations

The implementations intentionally avoid dynamic expression execution and external credential handling.

The database version uses:

- Typed columns
- Foreign keys
- Check constraints
- Trigger validation
- Parameterized function arguments

The application versions validate input before calculations.

For a production Power BI environment, security design must also consider row-level security, workspace permissions, semantic-model permissions, data-source credentials, gateway configuration, and least-privilege access. These controls are separate from the mathematical correctness of a measure.

## Relationship Between the Implementations

The five implementations represent the same analytical domain from different engineering perspectives.

```text
                 Analytical Domain
                        │
        ┌───────────────┼────────────────┐
        │               │                │
     Python        JavaScript         C++17
     model         event model       typed engine
        │               │                │
        └───────────────┼────────────────┘
                        │
                   Java 17
                enterprise model
                        │
                        ▼
                  PostgreSQL
                 relational model
```

They deliberately differ in implementation style while retaining comparable analytical concepts.

Python emphasizes explicit simulation and assertions.

JavaScript emphasizes collection operations, asynchronous event handling, and policy-oriented evaluation.

C++ emphasizes explicit data structures, algorithms, validation, and computational complexity.

Java emphasizes immutable domain records, service boundaries, interfaces, policy validation, and exact monetary arithmetic.

PostgreSQL emphasizes relational integrity, database-level validation, CTEs, window functions, reusable SQL functions, indexing, and transactional behavior.

## Practical Interpretation in Power BI

The source implementations correspond to a Power BI semantic-model design in which reusable measures form the foundation of analytical calculations.

A conceptual measure hierarchy is:

```text
[Revenue]
    │
    ├── [Margin]
    │       └── [Margin %]
    │
    ├── [Previous Month Revenue]
    │       └── [MoM %]
    │
    ├── [YTD Revenue]
    │
    ├── [Rolling 7 Day Revenue]
    │
    ├── [Percent of Total]
    │
    ├── [Average Order Value]
    │
    └── [Product Revenue Rank]

[Inventory Units]
    └── [Latest Inventory]
```

This structure reduces duplicated business logic because derived calculations depend on clearly defined base measures.

The critical design principle is that a measure's meaning includes its evaluation context. A mathematically correct expression can still produce an incorrect business result if the date, dimension, or filter context is not deliberately controlled.

## Limitations

The implementations simulate analytical semantics and do not attempt to reproduce the internal Power BI Formula Engine or VertiPaq storage engine.

The in-memory programs use linear scans and therefore do not represent the compression, dictionary encoding, storage engine scans, caching, or query optimization performed by Power BI.

The SQL implementation represents relational analytical equivalents rather than executing DAX.

The C++ demonstration uses floating-point values for compactness, while the Java implementation uses `BigDecimal` for monetary precision.

The sample dataset is intentionally small enough to make each calculation inspectable. Production performance conclusions require representative data volumes and actual workload measurements.
