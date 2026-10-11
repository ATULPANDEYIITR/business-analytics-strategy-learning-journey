# Advanced SQL: Joins, Window Functions, and Query Optimization

## Scope

Advanced SQL combines relational reasoning with analytical calculations and execution-plan analysis. This project examines three connected areas:

- **Advanced joins** determine how related records are matched, retained, excluded, and aggregated.
- **Window functions** calculate rankings, cumulative values, row-relative comparisons, and distributions without collapsing the underlying rows.
- **Query optimization** examines how predicates, indexes, statistics, join strategies, and sorting requirements influence execution cost.

The examples use customer orders, products, payments, and support tickets. The central technical challenge is to produce accurate analytical results while controlling row cardinality and understanding the cost of the query that produces them.

The Python implementation runs on SQLite. The JavaScript and C++ programs model analytical operations in memory. The Java program introduces explicit enterprise domain types. The SQL implementation uses PostgreSQL features, including `LATERAL`, aggregate `FILTER` clauses, partial indexes, materialized views, and execution-plan inspection.

## Relational joins and cardinality

### Inner joins and outer joins

An inner join returns rows satisfying the join condition. If a customer has three orders, joining the customer to the orders produces three rows for that customer.

A left join retains every row from the left relation. When no matching right-side record exists, the right-side columns contain `NULL`.

This distinction matters for customer reporting. Starting with `customers` and left joining qualifying orders preserves customers who have never ordered. Starting with orders and joining customers cannot produce such customers because they have no matching order.

The placement of predicates affects the result:

- A status predicate in the `ON` clause restricts which orders qualify as matches while retaining unmatched customers.
- A status predicate in the `WHERE` clause filters the joined result. A condition such as `WHERE orders.status = 'delivered'` removes rows whose order status is `NULL`, effectively eliminating unmatched customers.

When counting matches after a left join, `COUNT(orders.order_id)` is generally appropriate because it ignores the `NULL` introduced for an unmatched row. `COUNT(*)` counts the preserved customer row and would report one rather than zero.

### Join fan-out and pre-aggregation

An order can have several line items, payments, and support tickets. Joining all three detail tables directly can multiply records.

For example, an order with three line items and two payment records can produce six intermediate rows. Summing line-item amounts after this join counts each line item twice. Summing payments counts each payment three times.

The PostgreSQL script avoids this error by aggregating each detail relation separately:

- `item_totals` produces one row per order.
- `payment_totals` produces one row per order.
- `ticket_totals` produces one row per order.

The resulting relations are joined to orders only after their cardinality has been reduced. This is a correctness technique, not merely a performance optimization.

The same principle appears in the Python implementation's pre-aggregated common table expressions. The C++ and Java implementations avoid the multiplication by accumulating each order directly into a customer-level map.

### Anti-joins and existence tests

An anti-join identifies records with no qualifying match. A typical use case is finding customers without support tickets.

`NOT EXISTS` expresses this requirement directly:

- Evaluate a customer.
- Search for a ticket belonging to that customer.
- Retain the customer only when no matching ticket exists.

`NOT IN` can behave unexpectedly when its subquery returns `NULL`, because SQL uses three-valued logic. `NOT EXISTS` is usually the clearer choice for this type of relationship.

An existence test is also useful when the question is whether a customer has at least one delivered order. A join could return the customer multiple times if several orders qualify. `EXISTS` preserves the customer row without producing those duplicates.

### Correlated queries and `LATERAL`

A correlated subquery can refer to a row from an outer query. In the latest-order example, the inner query restricts orders to the current customer and selects the most recent date and order identifier.

PostgreSQL's `LEFT JOIN LATERAL` provides another way to express a top-one lookup for each customer. The `LEFT` form retains customers without orders. Ordering by both `order_date` and `order_id` provides deterministic behavior when multiple orders share a date.

A composite index beginning with `customer_id` and continuing with descending date and identifier can support this access pattern.

## Window functions

A window function calculates a value across a related set of rows while preserving the individual rows. Unlike ordinary aggregation, it does not automatically collapse a group into a single result.

### Ranking and ties

The implementations distinguish three common ranking operations.

| Function | Behavior |
|---|---|
| `ROW_NUMBER()` | Assigns a unique sequence number to each row. |
| `RANK()` | Gives tied values the same rank and leaves gaps after ties. |
| `DENSE_RANK()` | Gives tied values the same rank without gaps. |

`PARTITION BY region` restarts the ranking independently for each region. Without a partition, the ranking applies to the complete result.

A deterministic `ROW_NUMBER()` should use a stable tie-breaker, such as a primary key. Ordering only by revenue does not specify which tied customer receives the first row number.

`NTILE()` distributes ordered rows among a requested number of buckets. It is useful for broad distribution analysis, but its buckets represent row positions, not necessarily equal ranges of revenue.

The Java implementation explicitly tracks the previous region and revenue to distinguish rank from row number. The C++ implementation uses sorted vectors and the same tie-aware rule. The SQL implementation delegates the calculation to the database window engine.

### Running totals and moving averages

A cumulative revenue calculation uses:

`SUM(revenue) OVER (ORDER BY order_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

The frame begins with the first ordered row and ends with the current row. The result grows as the ordered input progresses.

A trailing three-observation average uses a bounded frame:

`AVG(revenue) OVER (ORDER BY order_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`

The example first groups orders by date. The moving average therefore uses the current date and up to two previous dates represented in the grouped result. It does not automatically generate missing calendar dates. A business report that requires every calendar day needs a date dimension or a generated series and an appropriate treatment of zero-sales days.

### `ROWS`, `RANGE`, and peer behavior

A window frame determines which rows contribute to a window calculation.

- `ROWS` selects a physical number of rows around the current row.
- `RANGE` uses the ordering values and their peer groups.
- `GROUPS` counts peer groups rather than individual rows.

The Python example compares `ROWS` and `RANGE` with repeated values. When two rows share an ordering value, a `RANGE` frame can include both peers at the same point in the calculation, while a `ROWS` frame advances row by row.

Explicit frames make analytical intent easier to review and reduce dependence on default frame behavior. They are particularly important for running aggregates and peer-sensitive calculations.

### `LAG`, `LEAD`, and top-per-group selection

`LAG()` accesses a previous row in the window order. `LEAD()` accesses a subsequent row. They are useful for calculating order intervals, changes in daily revenue, and comparisons with prior observations.

A window expression cannot normally be used directly in the same query level's `WHERE` clause. The PostgreSQL implementation calculates `ROW_NUMBER()` in a common table expression and filters it in the outer query. This produces the latest order for each customer.

A correlated top-one query and a window-ranking query can express similar requirements. The preferable shape depends on the database engine, available indexes, the number of customers, and the number of orders per customer. Execution plans and representative measurements should determine the choice.

## Query optimization and execution plans

### Query plans

A database optimizer chooses an execution strategy based on query structure, available indexes, statistics, estimated row counts, and cost models.

PostgreSQL can use `EXPLAIN` to show an estimated plan. `EXPLAIN (ANALYZE, BUFFERS)` executes the statement and reports actual timing, row counts, and buffer activity.

Actual plans help identify discrepancies between estimated and observed row counts. Large discrepancies can indicate stale statistics, skewed distributions, correlated predicates, or assumptions that do not match the data.

`EXPLAIN ANALYZE` executes the query. It must therefore be used carefully for statements that modify data or consume substantial resources. The script uses it only with a read query.

SQLite's `EXPLAIN QUERY PLAN` provides a different representation of access strategies. SQLite and PostgreSQL plans are not interchangeable, and an index that helps one engine may produce different results under another optimizer.

### Composite indexes

The PostgreSQL script creates a composite index on customer identifier, descending order date, and order identifier.

This order reflects the access pattern:

- Equality filtering on `customer_id` restricts the leading index range.
- A date boundary limits the matching records.
- Descending date and identifier ordering supports deterministic newest-first retrieval.

A B-tree index is not automatically useful for every query. A query returning most of a table may be cheaper with a sequential scan than with index lookups followed by many table accesses.

The script also creates indexes for product-to-order access, payment aggregation by order and status, and unresolved tickets for a customer. The partial ticket index stores only unresolved tickets, which can reduce index size when open tickets are a small subset of all tickets.

Indexes consume storage and add work to inserts, updates, and deletes. They should be selected according to measured workloads rather than added to every column.

### Sargable predicates

A predicate is commonly described as sargable when it can use an index-friendly search condition.

The date-range pattern is:

`WHERE order_date >= DATE '2025-05-01' AND order_date < DATE '2025-06-01'`

This half-open interval includes the first date and excludes the next month. It avoids end-of-day boundary errors and works naturally with timestamp ranges when boundaries use compatible types.

Applying a function to the indexed column, such as extracting the month from every order date, may prevent ordinary index range access. A matching expression index can help when a functional predicate is required, but a range predicate is often simpler.

### Statistics and selectivity

PostgreSQL's `ANALYZE` gathers statistics used by the planner to estimate selectivity and cardinality. After substantial changes to data volume or distribution, current statistics can improve plan selection.

Selectivity describes the fraction of rows expected to match a condition. An index may be especially valuable when a predicate returns a small fraction of the table. A low-selectivity predicate can lead the planner to prefer a sequential scan, depending on table size and physical layout.

Benchmarking should use representative data volumes and distributions. Tiny demonstration datasets often produce plans that differ from those used for production tables.

### Materialized views

The PostgreSQL script creates a materialized view of monthly revenue by region. Unlike an ordinary view, a materialized view stores its result and can avoid recalculating an expensive aggregate for every report.

The trade-off is freshness. The data remains unchanged until a refresh occurs. A unique index supports the concurrent-refresh requirements when those requirements are otherwise satisfied. Refresh frequency, lock behavior, source-table activity, and reporting freshness must be considered together.

## Python implementation

`advanced_sql.py` provides a self-contained SQLite laboratory.

The schema uses primary keys, foreign keys, check constraints, and a composite key on order items. Sample records represent delivered, shipped, paid, pending, and cancelled orders, along with settled, authorized, and refunded payments.

The join examples compare pre-aggregated relations, outer-join filtering, anti-joins, and correlated latest-order selection. The window examples calculate partitioned ranks, cumulative revenue, moving averages, row-relative order dates, and the differences between `ROWS` and `RANGE`.

The optimization section inspects query plans before and after creating indexes. It also demonstrates parameter binding, date-range predicates, a repeatable microbenchmark, integrity checks, and savepoint-based rollback.

The benchmark is illustrative rather than a universal performance claim. Results depend on hardware, cache state, data size, query plans, and database configuration.

## JavaScript implementation

`advanced_sql.js` uses Node.js to model relational and analytical operations through maps, arrays, and event processing.

The `leftJoin()` function preserves unmatched left-side records and expands matching rows according to join cardinality. `calculateCustomerRevenue()` aggregates orders before attaching customer information, including customers without qualifying orders.

`rankWithinGroups()` implements tie-aware ranking within partitions. `calculateRunningRevenue()` aggregates by date before computing a cumulative total. `findLatestOrderPerCustomer()` uses ISO-formatted dates and an identifier tie-breaker to select the latest record deterministically.

The event-processing example updates a latest-order projection as events arrive. It illustrates an application-level aggregate, not a replacement for database transactions or a durable event log. Production systems must address event duplication, ordering, retries, persistence, and concurrent updates.

The program also prints PostgreSQL query patterns so that in-memory operations can be compared with relational expressions. Its JavaScript calculations do not reproduce an SQL optimizer.

## C++ case study

The C++ program models fulfillment analytics for a repository of customers and orders. The architecture separates record validation, storage, aggregation, ranking, and presentation.

`FulfillmentAnalytics` stores customers and orders in hash maps keyed by identifier. This allows expected constant-time lookup and supports efficient accumulation without first constructing a large denormalized join result.

The revenue calculation initializes one metric per customer before processing orders. This preserves customers without orders, corresponding to a left-join result. Cancelled orders are excluded from operational revenue.

The program sorts customer metrics by region, revenue, and identifier. It then computes both a rank that preserves ties and a unique row number. The daily revenue calculation uses an ordered map, so dates are emitted chronologically and cumulative revenue can be calculated in one pass.

Input validation rejects duplicate identifiers, unknown customer references, negative amounts, and unsupported states. Exceptions demonstrate how invalid records can be rejected before they enter the analytical model.

For \(n\) orders and \(c\) customers, accumulation is expected to take \(O(n+c)\) time with hash-based storage, followed by \(O(c\log c)\) sorting for ranked output. These are complexity estimates for the in-memory program, not estimates of PostgreSQL execution cost.

## Java enterprise model

`AdvancedSqlEnterprise.java` represents customers, orders, and analytical results using Java 17 records. `OrderStatus` restricts lifecycle values to a defined enum, while constructors validate identifiers, required fields, dates, and monetary amounts.

`OrderRepository` enforces unique identifiers and rejects orders that reference unknown customers. `AnalyticsService` owns the calculations rather than mixing business logic into console output.

The ranking implementation preserves customers without qualifying orders, uses `BigDecimal` for monetary calculations, and explicitly distinguishes `RANK()` semantics from `ROW_NUMBER()` semantics. `TreeMap` orders daily aggregates by date, allowing a straightforward cumulative calculation.

`QueryPolicy` demonstrates application-level validation of date ranges and expected index configuration for high-volume filters. This is a governance check, not a database optimizer. A production service must still inspect actual execution plans and verify that the database has the intended indexes.

The domain model also illustrates why validation responsibilities differ. Java constructors can reject invalid application objects, while database constraints remain necessary to protect records written through other applications, scripts, or services.

## PostgreSQL data model

The SQL script recreates the `advanced_sql_lab` schema and populates seven related tables.

| Relation | Purpose |
|---|---|
| `customers` | Customer identity and regional reporting attributes. |
| `products` | Product classification and list pricing. |
| `orders` | Customer order lifecycle and dates. |
| `order_items` | Product quantities, prices, and discounts for each order. |
| `payments` | Payment attempts and settlement states. |
| `support_tickets` | Customer support cases and resolution status. |

Foreign keys preserve referential integrity. Check constraints reject invalid quantities, negative prices, invalid discounts, unsupported lifecycle values, and resolution timestamps preceding ticket opening. The composite primary key on order items prevents a product from appearing more than once in a single order.

The analytical queries use common table expressions to establish intermediate aggregation boundaries. Window expressions produce rankings and cumulative measures. `LATERAL` retrieves the newest order for each customer, while `NOT EXISTS` identifies customers without tickets.

The index definitions support specific access patterns. `ANALYZE` refreshes planner statistics, and `EXPLAIN` exposes the estimated plan. `EXPLAIN ANALYZE` provides actual execution data and buffer information by executing the query.

The materialized view caches monthly regional revenue and demonstrates the trade-off between reporting cost and data freshness. The savepoint examples demonstrate constraint enforcement and controlled rollback.

The script is designed for a dedicated learning database because it drops and recreates its schema. Its sample data is small enough for inspection and is not a realistic production benchmark.

## Common analytical failure modes

**Inflated aggregates:** Joining multiple independent one-to-many tables before aggregation can multiply amounts. Aggregate each relation at the intended grain before joining it to other detail relations.

**Missing entities:** An inner join excludes unmatched entities. Use a left join when the reporting requirement includes entities without activity, and place qualifying-match predicates in the join condition when appropriate.

**Unstable ranking:** A non-unique ordering expression can leave row-number assignment nondeterministic. Add a stable tie-breaker when a unique sequence is required.

**Misleading moving averages:** A three-row frame is not necessarily a three-calendar-day frame. Generate or join a calendar when missing dates must count as zero observations.

**Unexpected window frames:** Default frames may group peers differently from a row-by-row cumulative calculation. Specify the intended frame explicitly.

**Unhelpful indexes:** An index can increase write cost without improving the relevant query. Inspect selectivity, actual row counts, sort operations, and buffer activity before changing index design.

**Stale materialized results:** Cached aggregates do not update automatically when their source tables change. The refresh policy must match the reporting freshness requirement.

**Unreliable benchmarks:** Warm caches, small tables, network latency, concurrent activity, and client-side result processing can distort measurements. Compare complete workloads under controlled, representative conditions.

## Production considerations

Analytical SQL must preserve both business meaning and relational correctness. Query tuning cannot compensate for an incorrect aggregation grain, an ambiguous tie-breaking rule, or a misunderstanding of outer-join semantics.

A production review should verify the expected row count at each join boundary, confirm that monetary calculations use suitable decimal types, and test empty groups and tied ordering values. Execution-plan review should compare estimated and actual rows and identify expensive scans, joins, sorts, and repeated operations.

Index design must balance read performance against storage and write amplification. Materialized views require a freshness policy. Queries used by application services should use parameter binding, bounded date ranges, explicit result ordering where required, and appropriate transaction boundaries.

SQLite, PostgreSQL, JavaScript, C++, and Java expose different execution mechanisms. Their implementations are useful for comparing relational semantics and algorithmic trade-offs, but only the target database's execution plan can establish how a particular SQL statement is executed.
