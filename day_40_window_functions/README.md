# Window Functions: Ranking, Running Totals, and Analytical Calculations

## Technical scope

Window functions calculate a value from a set of rows associated with the current row while retaining the individual rows in the result. They are particularly useful for sales performance analysis, financial reporting, operational monitoring, and time-series comparisons.

The six deliverables use monthly sales data to distinguish three important analytical tasks:

- **Ranking** determines a row's relative position within a group, including how ties affect rank values.
- **Running totals and moving calculations** summarize values across an ordered frame without removing individual records.
- **Analytical calculations** compare adjacent rows, measure relative position in a distribution, and derive changes over time.

Python, JavaScript, C++, and Java implement the mechanics explicitly to expose ordering and state management. PostgreSQL provides native window functions and demonstrates how the same class of calculations can be executed close to the data.

## Window-function model

A window calculation is defined by the relationship between the current row and a set of related rows. Three clauses or decisions determine its meaning.

| Mechanism | Meaning | Example |
|---|---|---|
| Partition | Separates rows into independent groups | Rank sales separately for North and South |
| Ordering | Defines row sequence or value order inside a partition | Chronological order for running totals |
| Frame | Restricts the rows used by a frame-sensitive calculation | Current month and previous row for a moving average |

A partition does not aggregate its rows into one record. Each input row remains available, with additional analytical values attached.

The ordering used for ranking need not be the ordering used for a running total. Revenue may be ranked from highest to lowest, while cumulative revenue must be calculated in chronological order. Reusing one ordering for both operations changes the meaning of the result.

### Ranking semantics

Consider revenue values ordered from highest to lowest:

| Revenue | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---:|---:|---:|---:|
| 12000 | 1 | 1 | 1 |
| 12000 | 2 | 1 | 1 |
| 9000 | 3 | 3 | 2 |

`ROW_NUMBER()` assigns a unique position to every row. A deterministic tie-breaker, such as a unique identifier, is important when reproducible results are required.

`RANK()` assigns equal values the same rank and leaves gaps after ties. The two rows ranked first cause the next distinct value to receive rank three.

`DENSE_RANK()` also preserves ties, but the next distinct value receives rank two. It counts distinct ranking groups rather than positions.

The ordering expression used by `RANK()` and `DENSE_RANK()` should not include a unique identifier if equal revenue values are supposed to remain tied. Adding a unique identifier to the ranking expression makes every row's ordering key distinct.

### Running totals and frame boundaries

A cumulative sum commonly uses the equivalent of:

`SUM(revenue) OVER (PARTITION BY region ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

The first row contributes its own revenue. Each subsequent row adds its revenue to the values from earlier rows in the same partition. A new partition starts a new cumulative series.

A moving average uses a narrower frame. The PostgreSQL report uses `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW`, which includes the current row and up to one preceding row. At the beginning of a partition, the frame contains fewer rows. The average is calculated from the rows that actually exist.

`ROWS` defines a physical row-based frame. `RANGE` instead considers ordering values and peer groups. With duplicate ordering values, `RANGE` may include several peers at once. Explicit frames prevent unintended differences between database defaults and the intended calculation.

### Adjacent-row and distribution calculations

`LAG()` retrieves a value from an earlier row, while `LEAD()` retrieves a value from a later row. These functions support month-over-month comparisons without joining a table to itself.

The percentage change is:

`(current_value - previous_value) / previous_value * 100`

A missing previous row produces no comparison. A zero previous value also requires an explicit policy because division by zero is undefined. The implementations return a missing result rather than fabricating a percentage.

`PERCENT_RANK()` describes relative rank position using `(rank - 1) / (partition_size - 1)`. A single-row partition has a percent rank of zero. `CUME_DIST()` measures the proportion of rows whose ordered values are less than or equal to the current row's value. `NTILE()` distributes ordered rows across a requested number of buckets; bucket sizes can differ by one row.

These functions answer different questions. Ranking identifies relative position, percent rank normalizes rank position, cumulative distribution measures the proportion of observations at or below a value, and `NTILE()` creates approximate quantile groups.

## Python implementation

The Python program provides a standard-library implementation of the underlying mechanics.

### Validated records and numeric precision

The immutable `Sale` dataclass validates identifiers, calendar months, non-negative revenue, and unit counts. Revenue is represented using `Decimal` rather than binary floating-point values so financial calculations avoid common representation errors.

`validate_dataset()` rejects duplicate identifiers. This matters because analytical results need a stable identity for each input record, particularly when tied values occur.

### Partitioning and ordering

`partition_by()` groups records using a caller-provided key. `ordered_partition()` establishes chronological ordering and adds the sale identifier as a deterministic tie-breaker.

`rank_rows()` returns all three ranking forms in one pass over the sorted partition. The ranking value determines ties, while the secondary identifier makes row-number assignment reproducible.

The implementation deliberately separates ordering from partitioning. North and South have independent analytical state, while rows inside each region are ordered chronologically for running totals and adjacent-row comparisons.

### Frames, offsets, and distributions

`cumulative_sum()` accumulates revenue over the ordered rows. `moving_average()` accepts preceding and following offsets, making its frame boundaries explicit. The implementation clips the frame to the available partition instead of manufacturing missing records.

`lag_lead()` returns optional previous and next values. `percent_rank()` handles a single-row partition, and `cume_dist()` computes a value-based cumulative distribution while preserving ties. `ntile()` distributes rows into nearly equal groups.

The report combines these functions into a regional analysis containing rankings, running revenue, moving averages, prior and subsequent values, percentage changes, and cumulative distributions.

The unit tests check tied ranks, partition-local totals, missing lag values, single-row percent rank, empty input, invalid revenue, duplicate identifiers, and moving-frame boundaries.

The program is a teaching implementation rather than a replacement for an optimized analytical database. Several operations sort or repeatedly traverse collections, and the implementation stores intermediate mappings to connect values back to their record identifiers. For large datasets, native database execution or carefully designed streaming algorithms may use less memory and provide better performance.

## JavaScript implementation

The JavaScript program uses Node.js and models analytical processing as composable transformations.

### Immutable processing pipeline

`loadSales()` provides an asynchronous ingestion boundary, while `validateRows()` rejects malformed records before analysis begins. The ingestion function copies and freezes each record so downstream calculations do not accidentally mutate the original data.

`partitionRows()` uses a `Map` to maintain independent regional groups. `orderRows()` sorts a copy rather than changing the caller's array. This is important when the same input is used by several analytical reports.

The ranking pipeline creates new objects with `rowNumber`, `rank`, and `denseRank` properties. Running totals, moving averages, and lag/lead calculations are separate transformations, allowing their outputs to be combined without confusing their distinct orderings.

### Asynchronous failure handling

`main()` awaits the ingestion operation and catches errors at the program boundary. A production implementation could replace the in-memory source with a database query or HTTP endpoint while retaining the validation and transformation boundaries.

The script explicitly rejects negative offsets and invalid frame sizes. It also distinguishes a missing prior value from a numeric zero when calculating percentage changes.

JavaScript `Number` uses binary floating-point arithmetic. It is adequate for demonstrating analytical mechanics, but exact financial systems should use integer minor units or a decimal arithmetic implementation when monetary precision is material. The sample uses whole-number revenues to keep its displayed calculations predictable.

## C++ case study: Branch revenue analytics

The C++ program models an operational reporting service that processes monthly revenue transactions for several business branches.

### Domain model and validation

`Transaction` represents a branch, month, service category, unique identifier, and revenue in integer cents. Integer minor units prevent ordinary floating-point representation errors in cumulative monetary totals.

`RevenueGovernanceEngine` owns the dataset and validates identifiers, required fields, month formatting, and non-negative revenue at construction. Invalid data is rejected before any report is produced.

The engine separates two analytical orders:

- Chronological ordering drives the cumulative total, moving average, and month-over-month comparison.
- Descending revenue ordering drives row number, rank, and dense rank.

This separation avoids a common analytical error: calculating a running total over a revenue-ranked sequence rather than over time.

### Data structures and algorithms

The implementation uses vectors for ordered records, maps to associate ranking results with transaction identifiers, and sets to enumerate branches without duplicates.

Sorting dominates the ranking work. For a partition of size \(n\), the ranking order costs \(O(n \log n)\). The implementation then traverses chronological records to compute cumulative values. The moving-frame implementation scans a small bounded frame for each record; its cost is \(O(nw)\), where \(w\) is the frame width. For the fixed two-row frame, this is linear in the partition size.

The program prints separate reports for each branch and handles duplicate identifiers through an exception. It demonstrates how an analytics engine can validate input, retain domain-specific records, and return reproducible output.

The example is intentionally in-memory. A production service would also need defined handling for late-arriving transactions, corrected historical revenue, missing months, currency changes, and concurrent updates to the source dataset.

## Java implementation: Typed analytics service

The Java program presents a service-oriented model using Java 17 language features and immutable domain data.

### Domain types and policy boundaries

`MonthlySales` is a record that validates its own required fields, non-negative monetary values, and unit counts. `YearMonth` represents calendar months directly, avoiding ambiguity from arbitrary dates within a month.

`Metric` selects the value to analyze. The same service can rank and aggregate either revenue or units without duplicating the entire analytical pipeline.

`SalesAnalyticsService` copies its input with `List.copyOf()` and rejects duplicate record identifiers. This provides a clear boundary between validated domain data and analytical operations.

### State and calculation rules

`analyzePartition()` establishes chronological order for period-based calculations and constructs a separate revenue- or unit-ranked sequence for ranking. `calculateRanks()` preserves ties by comparing analytical values rather than the secondary identifier used for deterministic ordering.

`WindowResult` represents the values calculated for each record, including its running total, moving average, adjacent values, and percentage change. A missing adjacent row is represented by `null`, and the percentage-change calculation excludes zero denominators.

`BigDecimal` is used for monetary values. Explicit scale and rounding rules make the moving average and percentage-change output predictable. The service is reusable and does not expose mutable collections to its callers.

The implementation demonstrates an application-level analytical service, while the PostgreSQL implementation delegates window calculations to the database. In an enterprise system, the choice depends on dataset size, where the data resides, consistency requirements, and whether results must be computed as part of a database query or in application memory.

## PostgreSQL implementation

The SQL script provides the most direct demonstration of native window functions.

### Relational data model

The schema contains three related entities:

- `regions` provides unique region names.
- `salespeople` associates each salesperson with a region and prevents duplicate names within that region.
- `sales` stores monthly revenue and unit counts for a salesperson.

Primary keys identify rows, foreign keys maintain relationships, and check constraints reject negative measures and invalid month dates. The unique salesperson-month constraint prevents two monthly records from being silently treated as separate observations for the same person.

The indexes support common access paths for chronological sales reporting and revenue-oriented analysis. Their usefulness depends on table size, query predicates, and the database query planner. Indexes increase write costs and storage use, so they should be evaluated against actual query workloads.

### Analytical view

`monthly_sales_window_report` joins the relational entities and calculates multiple windows without grouping away individual sales records.

`ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` rank revenue within each region. Their ordering expression deliberately excludes the unique sale identifier so equal revenues remain tied.

The running regional total uses chronological order and an explicit row frame. The salesperson total uses a separate partition, allowing the report to compare regional accumulation with an individual's cumulative revenue.

The trailing average uses the current row and one preceding row. `LAG()` and `LEAD()` expose adjacent monthly revenue values for each salesperson. `PERCENT_RANK()`, `CUME_DIST()`, and `NTILE(3)` provide distribution-oriented views of revenue performance.

The final view derives percentage change using a `CASE` expression. The condition prevents division by zero and leaves the first observation without a prior value.

### Filtering analytical results

Window functions are evaluated after the ordinary `WHERE` filtering stage of a query. Consequently, a query cannot directly filter on a window expression in its own `WHERE` clause. The top-sales query uses a common table expression to calculate rank first, then filters the calculated rank in the outer query.

This distinction matters when interpreting results. Filtering records before a window calculation changes the population included in its partition. Filtering after calculation selects from already calculated results.

### Transaction and integrity behavior

The script wraps schema creation and sample-data insertion in a transaction. Relational constraints reject invalid values independently of the analytical queries, and the view exposes the resulting records through a reusable reporting interface.

The demonstration keeps intentionally invalid inserts out of the transaction so that the complete script executes successfully. In an operational environment, invalid writes should be tested in isolated transactions or automated database tests to verify constraint failures without aborting the reporting setup.

## Comparing application and database calculations

| Implementation | Primary technical emphasis | Important consideration |
|---|---|---|
| Python | Explicit algorithms, validation, and testable helper functions | Intermediate mappings and repeated sorts consume memory |
| JavaScript | Immutable transformations and asynchronous ingestion boundaries | Numeric precision and mutable array behavior require attention |
| C++ | A branch-level analytics engine with integer monetary storage | Data ownership, deterministic ordering, and bounded-frame cost |
| Java | Typed domain records and a reusable analytics service | Null semantics, immutable collections, and explicit decimal rounding |
| PostgreSQL | Native window expressions over relational data | Partition order, frame definitions, query plans, and integrity constraints |

The implementations share the same analytical principles but do not need identical internal structures. Application code is useful when calculations belong to a domain service or must be reused outside SQL. Database window functions are especially useful when large datasets should be processed near their source and returned as an enriched result set.

## Edge cases and production considerations

### Deterministic ordering

Ordering by a non-unique value can produce different row-number assignments when the underlying execution order changes. Use a stable secondary key for deterministic row ordering. Do not include that key in a ranking expression when tied analytical values are intended to share a rank.

### Missing periods

`LAG()` compares adjacent rows, not necessarily adjacent calendar months. If a salesperson has records for January and March but no February record, the previous-row value for March is January's value. A report requiring strict month-over-month comparison must generate or join against a complete calendar series and define how missing months should be represented.

### Nulls and zero values

A missing observation, a zero revenue value, and an unavailable percentage change are different states. A robust reporting contract must distinguish them rather than converting all three to zero. SQL also has its own null ordering and aggregate behavior, which should be specified explicitly when null-valued measures are permitted.

### Ranking and frame defaults

Database defaults can make frame-sensitive aggregates behave differently from a full-partition calculation, particularly when ordering values have ties. Specify a `ROWS` frame for row-based running totals and moving windows when that is the intended behavior.

Ranking functions use ordering and peer-group semantics, whereas aggregate windows use a frame to determine which rows contribute to a result. These are related mechanisms but should not be treated as interchangeable.

### Performance and scale

Sorting each partition generally costs \(O(n \log n)\), while a simple cumulative scan is \(O(n)\) after ordering. Multiple calculations with compatible partition and ordering specifications may be able to reuse work in a database execution plan, although this depends on the optimizer.

Indexes can reduce the cost of some access patterns but do not guarantee that a query avoids sorting. Inspect actual query plans before making performance claims.

For large reports, avoid transferring an entire table to an application merely to compute values that a database can calculate efficiently. Conversely, application-level processing may be appropriate for specialized algorithms, small datasets, or workflows that combine analytical results with domain logic.

### Data consistency and interpretation

A running total depends on the records included in its partition and on their ordering. Late-arriving data or corrections can change historical cumulative values. A production reporting process should define the reporting cutoff, correction policy, and treatment of backdated records.

Moving averages also require an explicit interpretation. A two-row moving average is not necessarily a two-month moving average unless the input contains exactly one row per month. The unit of the frame must match the business question.

### Monetary precision and rounding

Rounding should generally occur at the presentation boundary unless business rules require rounding each intermediate operation. Rounding every step can produce a different total from rounding only the final result. PostgreSQL `NUMERIC`, Java `BigDecimal`, and Python `Decimal` provide decimal arithmetic, while the C++ example uses integer cents for stored monetary amounts.

### Testing analytical correctness

Tests should include ties, singleton partitions, empty partitions, zero prior values, missing periods, duplicate identifiers, invalid measures, and frame boundaries. Validation tests verify that malformed inputs are rejected, while analytical tests verify that correct inputs produce the intended rank, cumulative, and comparison semantics.
