# Common Table Expressions for Complex Analysis

## Technical scope

A Common Table Expression (CTE) is a named query result defined with `WITH` and referenced by the main SQL statement or by subsequent CTEs in the same statement. CTEs let analysts separate a complex query into meaningful relational stages without creating permanent tables for every intermediate calculation.

The implementations in this collection examine CTE-style analytical processing through a retail and distribution dataset. The central workflow filters recognized sales, aggregates revenue and profit, ranks business categories, compares monthly results, calculates customer cohorts, and traverses hierarchical categories.

The files use different approaches to the same analytical problem. Python and JavaScript implement executable, application-level analytical pipelines. C++ models a distribution reporting engine with explicit intermediate relations. Java organizes the workflow as a domain-oriented financial reporting service. PostgreSQL expresses the analyses directly through relational queries, window functions, and recursive CTEs.

## Relational foundations

A CTE names the result of a relational expression. Its value is determined by its defining query, and its scope is normally limited to the SQL statement containing its `WITH` clause.

Consider the following conceptual pipeline:

`source orders → eligible orders → order totals → customer metrics → ranked report`

Each stage has a specific responsibility. Filtering establishes which records are eligible. Aggregation converts detailed records into a defined reporting grain. Subsequent stages calculate metrics or apply rankings without repeating the original joins and filters.

This separation is particularly useful when the correctness of later calculations depends on the meaning of earlier results. A report that includes cancelled or refunded orders in recognized revenue can appear internally consistent while still being financially incorrect.

### CTEs and subqueries

A subquery can express the same relational operation as a CTE. The primary advantage of a CTE is that its name communicates the meaning of an intermediate result and makes dependency relationships easier to inspect.

CTEs are particularly useful when:

- Several analytical stages depend on the same eligibility rules.
- The calculation requires multiple levels of aggregation.
- Window functions operate on an already aggregated dataset.
- Cohort membership must be established before retention is measured.
- Recursive traversal is needed to follow a parent-child hierarchy.
- A complex report needs to be reviewed and debugged stage by stage.

A CTE is not automatically faster than a subquery. The optimizer determines the execution plan according to the SQL engine, query structure, indexes, statistics, and materialization rules.

### CTE scope and materialization

An ordinary CTE is not a permanent table. Its name is available within the containing statement, and the result does not automatically persist after the statement finishes.

PostgreSQL may inline eligible CTEs into the surrounding query. `MATERIALIZED` can request a separately materialized result, while `NOT MATERIALIZED` can permit joint optimization where supported. These choices have performance implications: materialization can avoid repeated expensive work, but it can also consume memory or temporary storage and prevent certain optimizations.

SQLite also supports ordinary and recursive CTEs, although optimizer behavior and available syntax differ from PostgreSQL.

## Filtering and aggregation must use the correct grain

The source model contains customers, orders, order items, products, and categories. An order can contain several item rows, so joining orders directly to order items changes the grain from one row per order to one row per item.

This distinction affects counts and sums.

- `COUNT(*)` after joining items counts item rows, not distinct orders.
- `COUNT(DISTINCT order_id)` counts unique orders within the grouping.
- `SUM(quantity * unit_price)` calculates line-level revenue.
- `SUM(quantity * (unit_price - unit_cost))` calculates gross profit using the supplied unit cost.
- `AVG(order_value)` must be calculated after establishing one row per order if the desired measure is average order value.

The SQL file first creates a `completed_lines` relation. Later CTEs reuse the recognized-sales definition and aggregate it at category, customer, or month level.

Cancelled, refunded, and pending orders remain available for status analysis but are excluded from the recognized-sales calculations. This prevents a status count from being confused with a financial-recognition rule.

## Chained CTEs and analytical dependency

A `WITH` clause can define multiple CTEs separated by commas. A later CTE can reference an earlier one.

The category-profitability query follows this structure:

- `completed_lines` filters and enriches eligible line items.
- `category_totals` aggregates units, revenue, and gross profit at category grain.
- `ranked_categories` applies ranking and computes each category's share of total profit.

The ranking stage operates on category totals rather than raw item rows. This is essential because ranking individual order items would answer a different question.

`DENSE_RANK()` assigns the same rank to equal profit values without leaving gaps in subsequent ranks. The profit-share expression uses `NULLIF(total_profit, 0)` to avoid division by zero. A production financial report should also define how negative total profit is interpreted, since percentage shares can become unintuitive when the denominator is negative or when category profits offset one another.

## Window functions over CTE results

Window functions calculate values across related rows without collapsing those rows into a single aggregate.

The monthly comparison uses `LAG(revenue)` to retrieve the previous revenue value in chronological order. The result retains a row for each observed month and provides both the current and previous values.

The percentage change is:

`(current_revenue - previous_revenue) / previous_revenue × 100`

When the previous value is zero, the percentage is undefined. The SQL implementation uses `NULLIF` to return `NULL` instead of raising a division-by-zero error.

There is another important distinction: `LAG()` compares with the previous row in the ordered result, not necessarily the previous calendar month. If a month has no completed orders, it may be absent from the aggregate. A report requiring consecutive calendar-month comparisons should first construct a calendar series, left-join the monthly results to it, and explicitly decide whether missing revenue represents zero, unavailable data, or a reporting gap.

## Customer cohort analysis

Cohort analysis groups customers by a shared starting event and measures subsequent activity.

In the SQL implementation, `first_purchase` establishes each customer's first completed-purchase month. `customer_activity` identifies distinct customer-month combinations. The cohort stages then calculate active customers at each month offset.

Retention is defined as:

`active customers in a cohort at an activity month / original cohort size × 100`

The numerator uses distinct customers rather than order counts. A customer making five purchases in one month remains one active customer for that month.

Cohort retention should not be confused with repeat-purchase rate or revenue retention. Repeat-purchase rate measures a purchasing event under a specified rule. Revenue retention compares revenue associated with a customer population over time. These metrics require different numerators and denominators.

## Recursive CTEs and hierarchical data

A recursive CTE consists of an anchor query and a recursive query joined by `UNION ALL`.

The anchor identifies the root categories. The recursive member joins each discovered category to its children and extends the traversal path. Each recursive result becomes input to the next iteration until no further eligible children are found.

The PostgreSQL script stores visited category IDs in an array and checks whether a child has already appeared in the current path. This prevents a cycle from causing indefinite traversal along that path. A depth limit provides an additional safeguard.

The Python implementation uses a string path and a depth limit for a small demonstration. It is less robust than tracking immutable node identifiers because two distinct categories may share the same name. Production hierarchy traversal should use identifiers for cycle detection and define what to do with disconnected nodes or malformed hierarchies.

A self-referencing foreign key does not prevent every possible multi-node cycle. For example, one category can reference a second category while the second references the first. Strong hierarchy integrity may require controlled write operations, triggers, or explicit validation.

## Python implementation

The Python script creates an in-memory SQLite database using the standard library. Its schema includes foreign keys, uniqueness rules, quantity constraints, status validation, and indexes supporting date, status, customer, and category access.

`AnalyticsDatabase` centralizes connection management and parameterized query execution. `QueryResult` captures the output columns and rows and displays them in a readable table.

The analytical functions demonstrate several different CTE structures:

- `basic_cte` filters completed orders before counting them by customer.
- `chained_ctes` separates eligible orders, order totals, and customer-level lifetime value.
- `category_profitability` calculates revenue, profit, ranking, and profit share at category grain.
- `monthly_performance` combines monthly aggregation with `LAG()` to calculate period-over-period changes.
- `customer_cohorts` calculates first-purchase cohorts and later customer activity.
- `recursive_category_tree` traverses parent-child categories.
- `conditional_metrics` compares order statuses and their values.
- `explain_query_plan` exposes SQLite's query-plan output for a filtered reporting query.

The transaction helper rolls back a batch when a database statement fails. The integrity demonstration attempts to insert an order item referencing a nonexistent order and reports the expected foreign-key error.

The Python version is intended for a compact, repeatable demonstration. Its in-memory database does not represent a production persistence architecture, and its recursive path logic is suitable only for the supplied demonstration data.

## JavaScript implementation

The JavaScript file models a CTE-inspired analytical dependency graph using Node.js and asynchronous functions.

`CTEEngine` stores named stage definitions, their dependencies, cached results, and execution metadata. A stage is evaluated only after its dependencies have been evaluated. Independent stages can be requested concurrently with `Promise.all`, while cached intermediate results prevent repeated calculations during the same evaluation cycle.

The pipeline contains stages for eligible orders, monthly revenue, customer lifetime value, monthly growth, customer-month activity, and cohort retention.

The engine also demonstrates dependency invalidation. When an upstream stage is invalidated, the engine removes cached results for all dependent stages. This is important in application-level analytics because retaining a downstream result after its input has changed can produce a report that no longer corresponds to the underlying data.

Circular dependencies and undefined stage names produce explicit errors. The demonstration also verifies that recomputation produces the same output as the original calculation.

This engine is not a SQL optimizer and does not implement SQL semantics. Its dependency graph is an application-level model inspired by named intermediate query stages. It does not provide database transactions, isolation guarantees, SQL type coercion, or query-plan optimization. A production implementation would need to coordinate cache invalidation with data versions and concurrent updates.

## C++ case study

The C++ program models regional profitability for a distribution business selling industrial sensors and control units.

The `Sale` structure stores the order identifier, region, month, product, quantity, unit price, unit cost, and order status. Input validation rejects non-positive identifiers or quantities, missing dimensions, negative monetary values, non-finite prices, and unsupported statuses.

`eligibleSales()` acts as the initial filtering stage. The reporting methods consume the filtered relation rather than independently reimplementing the status rule.

`monthlyRegionRevenue()` aggregates revenue, gross profit, and units by region and month. A `std::map` provides ordered grouping keys, making the output deterministic.

`regionalPerformance()` aggregates results by region and uses a set of order identifiers to avoid counting repeated product lines as separate orders. The resulting vector is sorted by gross profit and then by region to produce a stable ranking.

`monthlyRevenue()` creates the intermediate monthly totals used by `printMonthOverMonthChange()`. The first month has no previous observation, so its change is displayed as unavailable. A zero previous value also makes percentage change undefined.

The case study illustrates how named analytical stages can be represented through functions and typed collections when a full SQL engine is unavailable. Its trade-off is that the program processes data in application memory. For large datasets, database-side aggregation can reduce data transfer and leverage indexes, parallel execution, and optimizer statistics.

## Java enterprise implementation

The Java program models a financial reporting service using Java 17 records, an enum for order status, immutable collection boundaries, and `BigDecimal` for monetary calculations.

The `Sale` record validates its data at construction time. This prevents malformed records from entering later analytical stages. The `OrderStatus` enum makes recognized, cancelled, refunded, and pending states explicit instead of relying on unrestricted text values.

`eligibleSales()` centralizes the financial-recognition rule. `monthlyMetrics()` calculates monthly revenue, gross profit, and distinct order counts. `accountMetrics()` groups eligible sales by account and validates that the account does not have conflicting regions. `growthMetrics()` compares successive monthly aggregates and represents the first month's unavailable comparison with null values.

The reporting methods consume immutable result lists. Monetary arithmetic uses `BigDecimal` rather than binary floating-point arithmetic, with explicit rounding when values are presented.

The implementation is a domain-oriented application model, not a replacement for a database query planner. It makes business rules and validation visible in the Java type system, but it loads the sample dataset into memory and does not implement persistence, concurrent report snapshots, or distributed caching.

## PostgreSQL relational implementation

The SQL file creates the `cte_lab` schema and defines customers, categories, products, orders, and order items. Primary keys, foreign keys, unique category names, status checks, non-negative monetary checks, and positive quantity checks enforce core data-integrity rules.

Indexes support common access paths: status and date filtering, customer order histories, and product-level analysis. Their value should be verified against actual workloads using `EXPLAIN` and, when appropriate, `EXPLAIN ANALYZE`.

The script contains separate queries for:

- Customer-level recognized revenue and gross profit.
- Category-level revenue, profitability, rank, and profit share.
- Monthly revenue changes using `LAG()`.
- Cohort retention based on first completed purchases.
- Recursive category traversal with visited-ID tracking.
- Order counts and values grouped by status.

The integrity demonstration catches an expected foreign-key violation within a PostgreSQL `DO` block. The surrounding transaction makes the setup and demonstration one executable unit.

The sample inserts use `ON CONFLICT` to avoid duplicating records with existing primary keys. This supports rerunning the script against the same sample schema, although it does not update existing records when their attributes change.

## Important distinctions and failure modes

### Logical correctness versus physical performance

A well-structured CTE query can still be inefficient. The number of stages is not a direct measure of execution cost. A query with several readable CTEs may execute efficiently, while a short query can perform repeated scans or generate large intermediate relations.

Inspect the execution plan to determine whether filters use suitable indexes, whether joins increase row counts unexpectedly, and whether aggregation occurs at the intended grain.

### Filtering before aggregation

Applying eligibility rules consistently is a correctness requirement. If one CTE includes refunded orders and another excludes them, downstream comparisons can become inconsistent. Centralizing the rule in a named stage makes such differences easier to detect.

### NULL and empty-result handling

An aggregate over no rows can produce `NULL` for `SUM`, while `COUNT` returns zero. `COALESCE` is appropriate when a missing amount should be presented as zero, but it should not be used to conceal missing or incomplete source data.

Likewise, a `NULL` percentage may indicate an undefined denominator rather than a missing computation. Reports should preserve that distinction.

### Recursive termination

Recursive queries must define a stopping condition. Cycles, unexpectedly deep hierarchies, and malformed parent relationships can cause incorrect output or excessive work. A visited-node check and depth limit reduce these risks, but data integrity should also be enforced during hierarchy updates.

### Application-side versus database-side computation

The Python, JavaScript, C++, and Java implementations make analytical dependencies explicit in application code. This is useful for understanding intermediate relations, validating business rules, and building specialized reporting services.

The PostgreSQL implementation performs filtering, joining, grouping, ranking, and recursive traversal in the database. For large datasets, this is often preferable because the database can optimize execution and avoid transferring detailed rows into the application.

Application-level materialization can still be useful when an intermediate result is expensive to compute and will be reused. Its correctness depends on an explicit freshness and invalidation policy.

## Performance, precision, and production considerations

CTE design should begin with a clear definition of each intermediate relation's grain and business meaning. Only then should execution performance be evaluated.

- Inspect query plans before adding indexes indiscriminately. Indexes improve selected access patterns but consume storage and increase the cost of inserts and updates.
- Avoid unnecessary `DISTINCT` operations. They can be expensive, and their presence may indicate that an earlier join or grouping has the wrong grain.
- Use `NUMERIC` or `DECIMAL` for financial amounts when exact decimal arithmetic is required. Floating-point values are suitable for many simulations but may introduce rounding differences in financial reporting.
- Define how late-arriving transactions, refunds, missing calendar periods, and corrected historical records affect previously calculated reports.
- Treat cached intermediate results as version-dependent data. An upstream change must invalidate or refresh every dependent result.
- Use transactions when several database modifications must succeed or fail together. CTEs themselves do not automatically make an entire multi-statement workflow atomic.
- Test recursive queries against cycles and large hierarchies. A depth limit is a safety measure, not a substitute for valid source relationships.
- Keep analytical SQL parameterized when application inputs influence filters. Parameter binding prevents user-supplied values from being interpreted as executable SQL.
- Distinguish recognized revenue, gross order value, and refunded value explicitly. These measures may share source tables but represent different business questions.

A reliable analytical pipeline combines readable intermediate stages with correct relational grain, explicit business rules, appropriate constraints, and evidence from the database execution plan.
