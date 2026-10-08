# Subqueries and Nested Queries: Analytical Logic

## Scope

Subqueries allow one SQL operation to use the result of another SQL operation as an input. The inner query can provide a single scalar value, a set of values, a Boolean existence condition, or an intermediate relation. Nested queries become especially useful when analysis requires several logical stages, such as calculating order totals, aggregating those totals by customer, calculating a benchmark across customers, and then filtering customers against that benchmark.

This repository models those patterns through a common retail analytics domain. Customers place orders, orders contain products, and the analytical questions require multiple levels of relational reasoning.

The central distinction is between the **inner analytical result** and the **outer operation that consumes it**.

A scalar subquery might calculate an average price. An `IN` subquery might produce the customer IDs associated with completed orders. An `EXISTS` subquery might determine whether a customer has at least one furniture purchase. A derived table can turn detailed order-item rows into order-level totals before another query aggregates them.

The implementations deliberately use different techniques in each language rather than treating one implementation as a mechanical translation of another.

## Core terminology

### Scalar subquery

A scalar subquery is expected to produce one value.

The SQL implementation uses:

`WHERE unit_price > (SELECT AVG(unit_price) FROM products)`

The inner query calculates a single average. The outer query compares every product against that value.

A scalar subquery becomes problematic when the inner query unexpectedly returns multiple rows. PostgreSQL raises an error instead of silently selecting an arbitrary value. This makes cardinality an important design property of scalar subqueries.

### Set-returning subquery

A subquery can produce a collection of values that the outer query tests with operators such as `IN`.

The repository uses completed customer IDs as the inner set:

`WHERE customer_id IN (SELECT DISTINCT customer_id FROM orders WHERE status = 'Completed')`

The analytical purpose is membership rather than calculation of a single benchmark.

### Correlated subquery

A correlated subquery references a column from the outer query.

The average-order-value analysis demonstrates this relationship. For each customer row, the inner operation evaluates order totals associated with that particular customer.

Correlation is powerful because the inner condition can depend on the current outer row. It can also be expensive when the database cannot transform the query into a more efficient join or semi-join plan.

### `EXISTS`

`EXISTS` asks whether at least one matching row is present.

The furniture-purchase query does not need the individual order-item rows in its result. It only needs to know whether at least one completed order contains a furniture product.

This is different from a normal join. A join can produce multiple copies of an outer entity when several child records match. `EXISTS` preserves the Boolean nature of the question.

### `NOT EXISTS`

`NOT EXISTS` expresses the absence of a related row.

The category price-leader analysis keeps a product when there is no product in the same category with a higher price. This is a useful pattern for top-per-group analysis.

The customer activity analysis combines `EXISTS` and `NOT EXISTS`: a customer must have completed activity, while no cancellation may exist for that customer.

### Derived table

A derived table is a subquery used in the `FROM` clause.

The regional analysis first calculates one row per completed order:

`order_id`, `region`, and `order_total`.

The outer query then calculates regional averages and maximum order values from that intermediate relation.

This separates the grain of the calculation. Item-level revenue is calculated at the order level before regional statistics are produced.

## Analytical workflow

The dataset has four primary relational levels:

`customers -> orders -> order_items -> products`

An individual order can contain several products, and a customer can have several orders. That means a direct aggregation over all item rows does not automatically produce customer-level or order-level metrics.

A useful analytical sequence is:

`order items -> order totals -> customer revenue -> customer benchmark -> filtered customers`

Each transition changes the grain of the data.

For example, an order total is calculated using:

`SUM(quantity * unit_price)`

Customer revenue then sums those order totals. The average customer revenue is calculated from the customer-level result rather than directly from item rows.

This distinction prevents a common analytical error: calculating a benchmark at the wrong level of aggregation.

## Python implementation

The Python program uses the standard-library `sqlite3` module, so it can execute the SQL examples without installing a database package.

The database is created in memory. Foreign keys are enabled, and the schema includes indexes on customer/order access paths and product access paths.

The program demonstrates:

- Scalar subqueries by comparing product prices with the overall average price.
- `IN` logic by finding customers associated with completed orders.
- Correlated subqueries by calculating customer-specific average order values.
- `EXISTS` by checking whether a customer has purchased furniture.
- Derived tables by first calculating order-level totals and then regional statistics.
- Multi-level nested aggregation by moving from order revenue to customer revenue and then to the average customer benchmark.
- `HAVING` with a nested benchmark for category-level revenue analysis.
- Correlated top-per-group logic for finding the most expensive product in each category.
- Parameterized SQL so analytical filters do not require string concatenation.
- Empty-subquery handling with `COALESCE`.
- `EXPLAIN QUERY PLAN` for examining execution behavior.
- Transactional validation using `INSERT ... SELECT`.

The Python implementation intentionally keeps SQL execution close to the analytical operation. This makes it possible to observe the actual behavior of nested SQL rather than replacing SQL with Python collection processing.

## JavaScript implementation

The JavaScript program implements an in-memory analytical model using arrays, `Set`, `Map`, `filter`, `map`, `reduce`, `some`, and `every-stage` transformations.

It does not require an npm package or database connection.

The JavaScript-specific value comes from modeling the reasoning behind subqueries rather than copying SQL syntax.

For example, the `customersWithCompletedOrders` function first constructs a `Set` of qualifying customer IDs. The outer filter then performs membership testing. This mirrors the logical role of an SQL `IN` subquery while using a data structure appropriate to JavaScript.

The `customersWhoBoughtFurniture` function uses `some`, which closely represents an existence predicate. The function stops looking for additional matching rows after a qualifying purchase is found.

The correlated customer analysis is implemented by calculating order totals inside a customer-specific operation. The inner calculation depends on the current customer, matching the dependency relationship of a correlated SQL subquery.

The derived-table concept appears in `regionalOrderAnalysis`. Completed order totals are materialized as an intermediate array before regional aggregation.

The implementation also demonstrates explicit handling of empty analytical input. The `average` function returns `null` for an empty collection rather than silently treating missing data as zero.

## C++ case study

The C++ program models a retail analytics engine rather than a SQL parser.

Its core domain types are `Customer`, `Product`, `Order`, `OrderItem`, `OrderTotal`, and `CustomerRevenue`. These types represent distinct analytical grains.

`completedOrderTotals()` acts as an intermediate relation. It converts item-level data into order-level facts before higher-level calculations consume those facts.

The customer benchmark analysis then uses those order totals to produce customer revenue. A second aggregation calculates the average revenue across customers, after which the customer collection is filtered against the benchmark.

The category price-leader analysis uses a nested search that asks whether a more expensive product exists within the same category. A candidate is retained only when that search finds no competitor with a greater price. This is the application-level equivalent of a correlated `NOT EXISTS` condition.

The program also separates lookup failures from analytical logic. Missing customer or product identifiers raise exceptions rather than producing silently incorrect financial results.

The data structures use vectors for ordered records, maps for grouped revenue, and standard algorithms such as `find_if`, `copy_if`, `accumulate`, `remove_if`, and `sort`.

The computational cost of the straightforward correlated searches can be higher than an indexed relational implementation. For a production-scale system, grouping and indexing data in memory would reduce repeated scans. The deliberately direct implementation makes the dependency between outer and inner analytical operations visible.

## Java implementation

The Java program uses immutable records for domain entities and standard collections and streams for analytical transformations.

The domain model contains explicit types for customers, products, orders, order items, order totals, and customer revenue. `OrderStatus` represents valid order states instead of relying on unrestricted strings.

The `completedOrderTotals` method establishes a derived analytical relation. Higher-level methods consume that relation rather than repeatedly mixing order-item calculations with customer-level aggregation.

`productsAboveOverallAverage` models a scalar benchmark.

`customersWithCompletedOrders` creates a `Set<Integer>` that represents the result of an `IN`-style analytical subquery.

`customersWhoBoughtFurniture` uses `anyMatch`, providing a direct representation of existence semantics.

`averageOrderValuePerCustomer` demonstrates correlation because each customer's ID controls the inner selection of order totals.

`customersAboveAverageRevenue` performs multi-stage aggregation. The first stage calculates customer revenue. The second calculates the average of those customer-level values. The final stage filters customers against the benchmark.

`categoryPriceLeaders` uses `noneMatch` to represent a `NOT EXISTS` condition.

The Java implementation also uses records to make analytical result objects immutable. This reduces accidental mutation between nested processing stages.

## SQL data model

The PostgreSQL schema contains:

| Table | Analytical role |
| --- | --- |
| `customers` | Customer-level attributes and segmentation |
| `products` | Product prices and categories |
| `orders` | Order-level status, customer relationship, and date |
| `order_items` | Many-to-many order/product detail with quantities |

The relationship is:

`customers 1 -> many orders 1 -> many order_items many -> 1 products`

Primary keys identify entities, foreign keys enforce relationships, and `CHECK` constraints prevent invalid status, tier, quantity, and price values.

The `order_items` primary key prevents the same product from appearing more than once in a single order row.

The indexes target access patterns used by the nested analytical queries:

`idx_orders_customer_status` supports customer-based order existence checks.

`idx_order_items_product` supports product-level analysis.

`idx_products_category_price` supports category-specific price comparisons.

## SQL mechanisms demonstrated

### Scalar analytical benchmark

The product-price query compares every product against:

`SELECT AVG(unit_price) FROM products`

The inner query produces one scalar value.

### `IN`

The completed-customer query uses a subquery that returns a set of customer IDs.

This is suitable when the outer condition is naturally expressed as membership.

### Correlated scalar analysis

The customer average-order-value query references the outer customer's identifier from inside the nested query.

The inner calculation therefore has a different result for each outer customer.

### `EXISTS`

The furniture-purchase query uses `EXISTS` because the analytical question is whether a matching purchase exists, not how many matching rows should be returned.

### Derived tables

The regional analysis calculates order totals inside a subquery in `FROM`.

The outer query receives a relation whose rows already represent completed orders rather than individual order items.

### Multi-level nested aggregation

Customer revenue is produced from completed order items. A second nested query calculates the average customer revenue. The outer query identifies customers above that benchmark.

This is an example where the sequence of aggregation levels matters.

### `HAVING`

The category analysis filters groups after category-level revenue has been calculated. Its benchmark comes from another nested aggregation.

### `NOT EXISTS`

The price-leader query determines whether a higher-priced sibling exists in the same category.

This pattern is more expressive than simply finding the global maximum because the comparison scope changes with the current product.

## `NOT IN` and `NULL`

`NOT IN` requires particular care when the inner query can return `NULL`.

If an inner result contains `NULL`, SQL's three-valued logic can cause a `NOT IN` comparison to become `UNKNOWN`, preventing rows from qualifying.

`NOT EXISTS` generally expresses exclusion more safely when nullable relationships are possible.

The SQL deliverable therefore uses `NOT EXISTS` for absence checks.

## Empty subqueries and `NULL`

Aggregate functions such as `AVG` return `NULL` when there are no input rows.

For example:

`SELECT AVG(unit_price) FROM products WHERE category = 'Nonexistent'`

does not produce zero.

The SQL example uses `COALESCE` when a business rule requires an explicit fallback.

The distinction matters because zero and unknown are not equivalent analytical states. Treating missing data as zero without a business justification can distort benchmarks.

## Nested aggregation and grain

One of the most important issues in analytical SQL is identifying the grain at every stage.

Suppose an order contains three items. The order appears three times at the item level. If customer-level averages are calculated directly from those rows, large orders with more line items can receive unintended weight.

The repository avoids that problem in the customer revenue analysis by first calculating one total per order.

The conceptual transformation is:

`order_items -> order_total`

followed by:

`order_total -> customer_revenue`

followed by:

`customer_revenue -> average_customer_revenue`

followed by:

`customer_revenue > average_customer_revenue`

Each nested layer therefore has a defined meaning.

## Performance considerations

A nested query is not automatically inefficient. PostgreSQL can transform many subqueries into joins, semi-joins, anti-joins, aggregates, or other execution strategies.

The important performance issue is the logical relationship between outer and inner operations.

A correlated subquery can be expensive when the inner operation repeatedly scans a large relation for each outer row.

Indexes can reduce the cost of those lookups, but indexes do not automatically eliminate all repeated work.

Derived tables can also introduce unnecessary work if they materialize large intermediate results, depending on the database version, query structure, and optimizer decisions.

For performance-sensitive analytical workloads, execution plans should be inspected rather than judging a query solely from its surface syntax.

The SQL script includes `EXPLAIN` statements for correlated existence and category price comparisons.

## Query correctness considerations

A nested query should be evaluated at the correct relational grain.

Before writing the query, identify whether the inner result represents:

- one scalar value,
- a set of identifiers,
- a Boolean existence condition,
- one row per order,
- one row per customer,
- one row per category,
- or another explicitly defined relation.

A scalar subquery that accidentally returns multiple rows is a correctness error.

A correlated subquery that references the wrong outer column can produce logically valid SQL with incorrect analytical results.

An aggregation performed before the intended grouping level can produce a mathematically valid but misleading benchmark.

A `JOIN` used where `EXISTS` is intended can duplicate outer rows.

A `NOT IN` condition over nullable values can produce unexpected results through SQL's three-valued logic.

## Common mistakes

### Comparing rows to a multi-row subquery

A condition such as `price = (SELECT price FROM products ...)` requires the inner query to return one row. If multiple rows are possible, an operator such as `IN` may be more appropriate.

### Aggregating at the wrong level

Calculating average customer spending directly from order-item rows can weight customers according to their number of line items. Establishing order totals first avoids that distortion.

### Using a join when only existence matters

If the outer entity should appear once regardless of the number of matching child records, `EXISTS` is often a clearer expression of the requirement.

### Ignoring `NULL`

A missing benchmark, missing foreign value, or nullable subquery result can change a comparison from `TRUE` to `UNKNOWN`.

### Overusing correlated subqueries

Correlation is useful when the inner calculation genuinely depends on the outer row. If the same intermediate result can be computed once and reused, a derived table, common table expression, or grouped relation may be clearer and more efficient.

### Assuming nested syntax determines execution strategy

SQL describes the requested result, while the optimizer determines an execution plan. A syntactically nested query may be transformed internally into a different execution strategy.

## Security considerations

Application code should not construct nested SQL by concatenating untrusted input.

The Python implementation demonstrates parameter binding, and the PostgreSQL script demonstrates `PREPARE` with a parameterized category value.

Parameterization protects values from being interpreted as SQL syntax and also gives the database a stable statement structure.

Security also includes authorization at the database layer. A technically correct analytical query should not expose customer information to a caller who is not authorized to access that information.

## Debugging nested queries

Nested queries are easier to debug when each analytical layer can be inspected independently.

For the customer-revenue analysis, a useful debugging sequence is:

`order totals`

then:

`customer totals`

then:

`average customer total`

then:

`customers above average`

The Python and SQL implementations make these intermediate concepts visible rather than hiding all logic inside one opaque expression.

For performance debugging, `EXPLAIN` and `EXPLAIN ANALYZE` should be used with representative data volumes. The relevant question is not simply whether a query contains a subquery, but how the database executes the nested relationship.

## Practical analytical applications

Subqueries are useful when a metric depends on another computed metric.

Examples represented by this repository include products above average price, customers above average revenue, customers with a particular purchase pattern, category leaders, and customers with positive activity but no cancellation.

The same reasoning applies to operational analytics such as employees above departmental averages, transactions above account-level thresholds, suppliers whose delivery time exceeds category benchmarks, or inventory items whose stock is below a calculated reorder threshold.

The important design principle is that the inner query should represent a meaningful analytical dependency rather than being nested merely for syntactic complexity.

## Implementation relationship

The six deliverables approach the same subject from different technical perspectives.

The Python program demonstrates actual SQL execution through SQLite and focuses on query behavior, validation, transactions, and query plans.

The JavaScript program models subquery semantics through JavaScript collections and makes membership, existence, correlation, and intermediate datasets explicit through native data structures.

The C++ program presents a systems-oriented analytics engine where nested analytical relationships are implemented with vectors, maps, searches, and aggregation algorithms.

The Java program represents the same domain using immutable records, enums, collections, streams, and explicit domain-oriented methods.

The PostgreSQL script provides the authoritative relational implementation, including constraints, indexes, parameterized execution, transactions, nested queries, and execution-plan inspection.

The implementations therefore preserve the distinction between the conceptual meaning of nested analytical logic and the language-specific mechanism used to represent it.
