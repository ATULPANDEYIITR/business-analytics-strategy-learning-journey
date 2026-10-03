# Filtering & Sorting Business Data

## Purpose

Filtering and sorting are fundamental operations in business-data analysis.

A business application rarely needs every stored record at the same time. A sales dashboard may need only active customers in a particular region. An operations queue may need pending orders above a particular value. A finance report may require non-cancelled transactions ordered from the largest value to the smallest.

The central distinction is:

- **Filtering** determines which rows qualify.
- **Sorting** determines the order in which qualifying rows are presented.
- **Pagination** selects a window from an already filtered and ordered result.
- **Aggregation** calculates business metrics from a selected dataset.

The implementations in this repository model these operations with realistic customer and order data.

The Python program emphasizes reusable predicate functions and an in-memory query abstraction. The JavaScript program emphasizes composable functions, object-based query construction, asynchronous execution, and event-driven reporting. The C++ program presents a repository-style business reporting engine with typed domain models, predicate composition, configurable sort rules, deterministic pagination, validation, and regional reporting.

---

## Business Meaning of Filtering

A filter is a business rule that excludes records that do not satisfy a condition.

For example, a sales application might need:

`region = 'West'`

This is not an ordering rule. It is a membership condition that determines which records remain in the result.

A more restrictive rule could be:

`region = 'West' AND order_value >= 200000`

The second condition reduces the eligible dataset further.

A different requirement might use alternatives:

`status = 'Pending' OR status = 'Processing'`

This produces an operational queue containing orders that still require action.

Negation is also useful:

`status != 'Cancelled'`

The implementations represent these relationships with predicate functions rather than hard-coding one particular report.

---

## Filtering Conditions

### Equality

Equality checks whether a business field has an exact value.

Examples include:

`region = 'North'`

`status = 'Shipped'`

`segment = 'Enterprise'`

In Python, this is represented through `equals()`. JavaScript uses a corresponding predicate factory, while the C++ implementation uses typed functions such as `hasRegion()` and `hasStatus()`.

Typed predicates in C++ reduce accidental comparisons between incompatible domain values because order status is represented by `OrderStatus` rather than an arbitrary string.

### Numeric comparisons

Business thresholds frequently use comparisons such as:

`order_value > 200000`

or:

`order_value >= 100000`

The difference between strict and inclusive comparisons matters at the boundary. An order worth exactly 100,000 is excluded by `> 100000` but included by `>= 100000`.

The sample programs deliberately use both forms.

### Membership filtering

A business rule may permit several values:

`status IN ('Pending', 'Processing')`

The Python implementation uses `in_values()`, the JavaScript implementation uses a `Set`, and the C++ implementation combines typed status predicates.

This is particularly useful for operational queues where several states represent unfinished work.

### Text filtering

Customer search often requires a partial text match rather than exact equality.

The Python and JavaScript implementations demonstrate case-insensitive name filtering. This is application-level substring matching rather than a database-specific text-search implementation.

Production systems should distinguish ordinary substring searches from full-text search. Large datasets may require database indexes or specialized search mechanisms rather than scanning every record.

---

## Combining Conditions

Real business rules normally contain several conditions.

The programs provide explicit predicate composition:

- `allOf()` represents logical AND.
- `anyOf()` represents logical OR.
- `negate()` represents logical NOT.

For example, an operational rule can be expressed as:

`(status = Pending OR status = Processing) AND priority != Low`

This is materially different from applying each condition independently without considering the intended boolean grouping.

Parentheses matter when translating business requirements into filtering logic.

A rule such as:

`region = 'West' AND (category = 'Cloud' OR category = 'Security')`

should not accidentally become:

`(region = 'West' AND category = 'Cloud') OR category = 'Security'`

The latter admits Security orders from every region.

---

## Missing Business Data

Missing values require explicit treatment.

The sample customer data contains missing annual revenue and credit-limit values. Python represents these values with `None`, JavaScript uses `null`, and C++ uses `std::optional<double>`.

A missing value is not automatically equivalent to zero.

For example, a customer with:

`annual_revenue = NULL`

does not necessarily have zero revenue. The value is unknown or unavailable.

This distinction is important for financial and operational reporting.

The implementations therefore provide explicit predicates for known and unknown values.

The C++ case study uses `std::optional<double>` so the type system distinguishes a missing credit limit from a numeric credit limit.

---

## Filtering Before Sorting

A typical business-data pipeline is conceptually:

`source data -> filtering -> sorting -> pagination -> presentation`

Suppose a system contains one million orders but only 4,000 orders satisfy a regional and value filter.

Sorting the 4,000 qualifying rows is usually preferable to sorting all one million rows when the query engine can apply the filter first.

The in-memory programs model this ordering of operations explicitly.

This should not be confused with the physical execution strategy of a database. A database optimizer may reorder operations internally when it can prove that the result remains equivalent and the alternative is cheaper.

The important application-level distinction remains clear:

- filtering controls membership;
- sorting controls presentation order.

---

## ORDER BY Semantics

Sorting is represented by one or more sort keys.

A single ordering rule might be:

`ORDER BY order_value DESC`

This puts the largest orders first.

A business report may need:

`ORDER BY region ASC, order_value DESC`

This means:

- group rows by region alphabetically;
- within each region, place the highest-value order first.

The direction belongs to each sort key.

It is therefore possible to combine:

`region ASC`

with:

`order_value DESC`

rather than applying one global direction to every field.

The Python `multi_sort()`, JavaScript `orderBy()`, and C++ `SortRule` abstractions all model independent sort directions.

---

## Deterministic Tie-Breaking

Sorting by one field may not produce a sufficiently deterministic business report.

Consider two orders with the same value:

`order_value = 250000`

If the report sorts only by value, both records are equivalent under that ordering rule.

For stable pagination and reproducible reports, a final unique field can be used:

`ORDER BY order_value DESC, order_id ASC`

The order ID acts as a deterministic tie-breaker.

This matters when a user moves between pages. Without deterministic ordering, records with equal sort values can appear in different positions if the underlying data or execution plan changes.

The sample implementations deliberately use order IDs as final tie-breakers in several reporting workflows.

---

## NULL and Sorting

Missing values introduce another ordering decision.

A database system can have explicit rules for whether NULL values appear before or after non-NULL values, and behavior can vary by database engine and ordering expression.

The Python and JavaScript implementations explicitly support `nullsLast`.

This is preferable to relying on accidental language-level comparison behavior.

The C++ credit-risk scenario avoids comparing missing credit limits numerically by requiring `creditLimitKnown()` before applying a credit threshold.

That is an important business rule as well as a type-safety rule.

---

## Filtering and Sorting Are Not Aggregation

Filtering and sorting operate on individual records.

Aggregation changes the shape of the result into business metrics.

For example:

`WHERE status != 'Cancelled'`

still produces individual orders.

A later calculation can compute:

`SUM(order_value)`

or:

`AVG(order_value)`

The Python implementation calculates total and average qualifying order values and groups sales by region.

The JavaScript implementation uses `reduce()` and `Map`.

The C++ implementation uses a `map<string, double>` to calculate regional totals.

The separation is useful because a business report can first define which records are eligible and then calculate metrics over precisely that eligible population.

---

## Python Implementation

The Python program models business data with `dataclass` records for customers, orders, and employees.

The filtering layer provides reusable predicate factories including:

- `equals()`
- `greater_than()`
- `greater_or_equal()`
- `less_than()`
- `contains()`
- `in_values()`
- `is_null()`
- `is_not_null()`

The boolean-composition functions allow a report to express AND, OR, and NOT without embedding business logic into one large function.

The `Query` class combines filters and order specifications. Its `execute()` method applies predicates, performs multi-column ordering, and then applies offset and limit pagination.

The Python implementation also demonstrates validation, regional aggregation, deterministic ordering, operational queues, and customer-level analysis based on shipped orders.

A useful design characteristic is that the query object stores intent separately from execution. A caller can construct a reusable query specification and execute it later against the in-memory dataset.

---

## JavaScript Implementation

The JavaScript implementation uses objects for business records and first-class functions for query predicates.

This is particularly natural in JavaScript because functions can be created dynamically and passed into `Array.prototype.filter()`.

The `BusinessQuery` class provides a chainable interface:

`new BusinessQuery(orders).where(...).where(...).orderBy(...).execute()`

The implementation supports independent sorting directions and explicit NULL handling.

It also demonstrates JavaScript-specific asynchronous and event-driven behavior through `BusinessDataService`.

The service emits `queryStarted` and `queryCompleted` events around an asynchronous query operation. This models an application architecture in which a real business-data service could later replace the in-memory operation with database or network access while retaining lifecycle events for logging, metrics, or monitoring.

The implementation deliberately avoids an external npm dependency.

---

## C++ Case Study

The C++ program represents a typed business reporting engine for a regional sales organization.

An `Order` contains typed fields for:

- order identity;
- customer identity;
- sales representative;
- region;
- category;
- monetary value;
- status;
- order date;
- priority;
- discount rate;
- optional customer credit limit.

Order status and priority are modeled with enumerations instead of arbitrary strings.

### Query architecture

`QueryEngine` owns a source dataset and accepts predicates and sort rules.

A query can therefore be constructed as:

`engine.where(...).where(...).orderBy(...).orderBy(...).execute()`

Filtering is performed before sorting.

Pagination is applied by `executePage()` after the complete filtering and ordering pipeline has established the result order.

### Predicate architecture

C++ `std::function` is used to represent a reusable order predicate.

Typed predicates include:

`hasStatus()`

`hasRegion()`

`hasCategory()`

`valueAbove()`

`valueAtLeast()`

`priorityAtLeast()`

`creditLimitKnown()`

`creditLimitAbove()`

The `allOf()`, `anyOf()`, and `negate()` functions compose these predicates into larger business rules.

### Sorting architecture

The case study uses `SortRule` objects containing comparison functions.

Separate rules exist for region, order value, date, priority, and order ID.

A query can combine these rules to express a business ordering such as:

`priority DESC, order_date ASC, order_id ASC`

The final order ID rule provides deterministic tie-breaking.

### Business scenarios

The program contains several distinct reporting workflows.

The high-value West-region report filters for West-region orders, excludes cancelled orders, requires a minimum order value, and sorts by value.

The operational queue selects pending or processing orders with at least medium priority and places higher-priority work first.

The credit-risk report requires a known credit limit, applies a credit threshold, excludes cancelled orders, and then orders qualifying transactions by value.

The regional report filters the eligible sales population before calculating regional totals.

The pagination example demonstrates why a stable final ordering field is important when presenting records in pages.

---

## Filtering Versus Sorting

| Operation | Business question | Example |
| --- | --- | --- |
| Filtering | Which records qualify? | Orders above 200K |
| Multiple filtering conditions | Which records satisfy a compound rule? | West AND above 200K |
| Sorting | In what order should qualifying records appear? | Highest value first |
| Multi-column sorting | How should ties and groups be ordered? | Region ascending, value descending |
| Pagination | Which portion of the ordered result should be shown? | Rows 11 through 20 |
| Aggregation | What metric describes the qualifying population? | Total sales by region |

Confusing these operations produces incorrect reports.

Sorting a dataset does not remove records. Filtering does not inherently establish a presentation order.

---

## Query Pipeline

A practical application can think about a business query as a pipeline:

`source -> validation -> filter -> sort -> paginate -> aggregate/present`

Not every system executes these operations in exactly this physical order.

For example, a database optimizer may use an index to locate matching records and may perform sorting through an index rather than an explicit in-memory sort.

The logical responsibilities remain separate even when the physical execution plan is optimized.

The sample programs keep the logical pipeline explicit so that the relationship between each operation can be inspected.

---

## Pagination and Stable Ordering

Pagination becomes unreliable when the ordering criteria do not uniquely identify a position.

Suppose a report sorts only by:

`order_value DESC`

and several orders have exactly the same value.

A page boundary can fall inside that group of equal-valued records.

Adding:

`order_id ASC`

as a final tie-breaker produces a deterministic sequence.

For large production datasets, offset pagination can also become expensive at high offsets. Cursor or keyset pagination can be more appropriate when the application needs to navigate deeply through an ordered result.

A cursor must be based on the same ordering fields that define the result sequence. For a sort such as:

`order_value DESC, order_id ASC`

a cursor needs enough information to identify the last returned position in that ordering.

---

## Validation

Filtering should not be used as a substitute for data validation.

The sample programs validate business constraints such as:

- order values cannot be negative;
- discount rates must remain between zero and one;
- known status values must belong to the permitted domain;
- priority values must belong to the permitted domain;
- numeric comparisons must not silently treat missing values as zero.

Validation protects the meaning of subsequent filtering and sorting.

For example, sorting a dataset containing invalid negative order values may technically work but produce a business report that is logically incorrect.

---

## Common Filtering Errors

### Treating missing values as zero

A missing revenue value is not necessarily zero revenue.

The correct approach is to explicitly define whether the business rule means:

- value is known and above a threshold;
- value is unknown;
- value is zero;
- or either known or missing values should qualify.

### Mixing AND and OR incorrectly

A filter containing both AND and OR needs explicit grouping.

`A AND B OR C`

can have a very different meaning from:

`A AND (B OR C)`

The business requirement should determine the grouping before implementation.

### Filtering after pagination

Applying pagination before filtering can produce pages containing fewer records than expected and can exclude qualifying records that should have appeared earlier in the filtered dataset.

The intended logical pipeline is normally:

`filter -> order -> page`

### Sorting before selective filtering

Sorting the entire dataset before applying a highly selective filter can perform unnecessary work in an in-memory implementation.

Database engines can optimize this differently, but application code should still represent the intended query semantics correctly.

---

## Common Sorting Errors

### Assuming one direction applies to every field

A report may require:

`region ASC, order_value DESC`

rather than both fields ascending or both descending.

Each sort key should have an explicit direction when the business requirement depends on it.

### Ignoring ties

If two records share the same primary sort value, the report needs a deterministic secondary rule when reproducible pagination matters.

### Comparing missing values without a policy

Direct comparison of missing values can cause errors or produce language-specific behavior that does not match the business requirement.

A NULL ordering policy should be deliberate.

---

## Performance Considerations

For an in-memory collection containing `n` records, a straightforward filter performs approximately `O(n)` predicate evaluations.

If `m` records remain after filtering, a comparison-based sort generally requires approximately `O(m log m)` comparisons.

This creates an important practical relationship:

`selectivity of filtering -> amount of data requiring sorting`

A selective filter can reduce the amount of work performed by a later sort.

For large production datasets, databases provide additional mechanisms:

- indexes can accelerate selective predicates;
- composite indexes can support combinations of filtering and ordering;
- query planners can choose execution strategies;
- statistics can help estimate predicate selectivity;
- database engines can sort data outside application memory;
- covering indexes can sometimes satisfy both filtering and ordering requirements.

An application should not assume that the in-memory implementation has the same performance characteristics as a database query.

---

## Security and Data Integrity

Filtering and sorting become security-sensitive when users control the query criteria.

A reporting application should validate requested fields and allowed sort directions rather than blindly accepting arbitrary field names or constructing executable query expressions.

For database-backed systems, parameterized values should be used for filter parameters.

For example, a value supplied by a user should be bound as a query parameter rather than concatenated into SQL text.

Column names and sort directions generally require allowlisting because they are structural query elements rather than ordinary values.

Authorization must also be applied independently of ordinary business filters.

A user being able to request:

`region = 'West'`

does not imply that the user is authorized to access all West-region records.

Access-control predicates should therefore be part of the server-side data-access policy rather than being supplied only by the user interface.

---

## Production Considerations

A production filtering and sorting system should establish clear rules for:

- permitted filter fields;
- permitted operators;
- data types for each field;
- missing-value behavior;
- permitted sort fields;
- default ordering;
- maximum page size;
- pagination strategy;
- authorization boundaries;
- validation rules;
- query timeout behavior;
- indexing strategy;
- audit logging for sensitive reports.

The default sort order should be deterministic when the output feeds pagination, exports, downstream processing, or reconciliation.

Business rules should also be kept separate from presentation code. A dashboard table should not be the only place where an important eligibility rule exists.

---

## Relationship Between the Three Implementations

The three implementations solve the same business-data problem from different engineering perspectives.

The Python program emphasizes flexible data processing and reusable predicates. Its dynamic object model makes it convenient to construct filtering expressions and reporting pipelines.

The JavaScript program emphasizes function composition, chainable query construction, asynchronous service behavior, and event-driven lifecycle reporting. This is useful for application-layer systems that eventually connect the query pipeline to APIs or user interfaces.

The C++ program emphasizes static typing, explicit domain models, typed business states, reusable comparison rules, and a coherent query engine. `std::optional` makes missing credit-limit values explicit, while enumerations constrain status and priority values.

The business meaning remains consistent across all three implementations:

`filter` decides eligibility, `sort` establishes sequence, `paginate` selects a window, and `aggregate` calculates metrics.

The implementation techniques differ because each language provides different mechanisms for expressing those responsibilities.

---

## Practical Data Flow

A realistic sales report can be understood as:

`orders`
→ validate business fields
→ select non-cancelled orders
→ apply region and value conditions
→ sort by business priority
→ apply deterministic tie-breakers
→ select a page
→ calculate or display metrics

The important property is that each stage has a distinct responsibility.

A change to the ordering requirement should not silently change which records qualify.

A change to the eligibility rule should not silently alter the meaning of the sort keys.

A change to pagination should not change the underlying filtered dataset.

Keeping these responsibilities separate makes business reporting easier to test, reason about, and maintain.
