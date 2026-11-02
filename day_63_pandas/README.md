# Pandas DataFrames, Series and Data Manipulation

## Technical Scope

This learning artifact models a sales-analysis workflow centered on the concepts represented by Pandas `Series` and `DataFrame` objects.

The common dataset contains sales orders with:

- Order identifiers and dates
- Regions and products
- Product categories
- Units and unit prices
- Discounts
- Customers
- Derived gross sales, discount amounts and net sales

The implementations deliberately use different programming models. Python provides the direct DataFrame-oriented implementation. JavaScript builds a lightweight tabular abstraction using arrays, objects, `Map`, `Set`, asynchronous execution and event emission. C++17 treats the data as strongly typed records and uses STL algorithms and associative containers. Java 17 models the same analytical operations through immutable records, services, streams, predicates and explicit workflow states. PostgreSQL represents the tabular operations through relational tables, views, joins, aggregates, window functions, functions, triggers and transactional operations.

## Data Model

The core order structure is:

| Field | Meaning | Validation |
|---|---|---|
| `order_id` | Unique order identifier | Must be unique |
| `order_date` | Order date | Valid calendar date |
| `region` | Sales region | Required |
| `product` | Product name | Required |
| `category` | Product category | Controlled category |
| `units` | Quantity sold | Positive integer |
| `unit_price` | Price per unit | Positive numeric value |
| `discount` | Fractional discount | `0 <= discount < 1` |
| `customer` | Customer name | Required |

The derived sales measure is:

`gross_sales = units × unit_price`

`discount_amount = gross_sales × discount`

`net_sales = gross_sales - discount_amount`

A record is classified as `high_value` when `net_sales >= 100000`.

## Series and DataFrame Concepts

A Pandas `Series` is a one-dimensional labeled data structure. In the Python implementation, expressions such as `sales["net_sales"]`, `sales["region"].value_counts()`, `sales["net_sales"].mean()`, and `sales["order_date"].dt.quarter` operate on individual Series.

A Pandas `DataFrame` is a two-dimensional labeled table. The Python implementation uses it for filtering, column creation, grouping, joining, pivoting, sorting, missing-value handling, serialization and rolling calculations.

The principal operations are:

| Operation | Python implementation |
|---|---|
| Construction | `pd.DataFrame` |
| Date conversion | `pd.to_datetime` |
| Numeric conversion | `pd.to_numeric` |
| Boolean filtering | `DataFrame.loc` |
| Derived columns | Direct column assignment |
| Sorting | `sort_values` |
| Grouping | `groupby` |
| Aggregation | `agg` |
| Joining | `merge` |
| Pivoting | `pivot_table` |
| Missing values | `isna`, `fillna` |
| Concatenation | `pd.concat` |
| Rolling analysis | `rolling` |
| CSV persistence | `to_csv`, `read_csv` |
| JSON conversion | `to_json` |

## Transformation Workflow

The implementations follow the same logical analytical progression:

`Raw records`
→ `Validation`
→ `Typed tabular data`
→ `Derived measures`
→ `Filtering`
→ `Grouping`
→ `Joining`
→ `Pivoting`
→ `Time-based analysis`
→ `Validation`
→ `Persistence`

The stages have different purposes.

Validation prevents malformed records from entering analytical calculations. Enrichment derives measures that can be reused by later operations. Filtering narrows the working set. Grouping changes the analytical grain. Joining adds attributes from another dimension. Pivoting changes the representation from long-form records to a cross-tabular view.

## Python Implementation

The Python file is the most direct implementation of DataFrame and Series concepts.

`SalesRecord` is a frozen dataclass used to define the source domain. `records_to_dataframe()` converts those records into a DataFrame and establishes appropriate numeric and datetime types.

`enrich_dataframe()` demonstrates vectorized column calculations. Instead of iterating over every record manually, expressions operate over complete Series.

The filtering implementation uses boolean masks with `loc`. The condition combines category and monetary constraints without modifying the original frame.

The aggregation implementation groups by both `region` and `category`. It calculates distinct order counts, total units, gross sales, net sales and average order value.

The customer merge uses `validate="many_to_one"`. This is an important data-integrity control because each sales record may refer to a customer, while the customer dimension should contain only one profile per customer.

The missing-data example distinguishes between detecting missing values and choosing a controlled replacement strategy. The sample replaces an unknown region with `Unknown` and a missing numeric value with the median.

The pivot table converts monthly sales into a region-by-month analytical layout.

The rolling calculation orders records chronologically and calculates a three-order moving average.

The CSV round trip demonstrates serialization and restoration of a DataFrame. JSON conversion demonstrates transformation into application-friendly record structures.

Assertions and explicit exceptions provide failure detection rather than silently accepting malformed input.

## JavaScript Implementation

The JavaScript implementation does not attempt to reproduce Pandas syntax. It creates a small `DataFrame` abstraction around arrays of objects.

The `DataFrame` class provides:

- Column discovery
- Shape information
- Column selection
- Predicate filtering
- Record transformation
- Sorting
- Grouping
- Numeric descriptive statistics
- JSON serialization

`Map` is used for grouping and customer dimension lookup. `Set` is used for duplicate detection and distinct order identifiers.

The `DataPipeline` extends `EventEmitter`. It emits `started`, `enriched`, and `filtered` events so that processing stages can be observed independently.

The asynchronous `execute()` method demonstrates how tabular processing can participate in an event-driven Node.js workflow.

The JSON persistence operation uses a temporary directory and the filesystem module. The file is opened with the exclusive `wx` mode so that an existing file cannot be silently overwritten.

The implementation also handles null-like values explicitly with nullish coalescing and validates dates, identifiers, quantities, prices and discounts before transformation.

## C++17 Implementation

The C++ implementation uses a strongly typed model rather than a dynamically typed table.

`SalesRecord` contains the source fields. `EnrichedRecord` contains derived measures. `Category` is represented as an enum class, preventing arbitrary category values from being silently introduced.

The program uses:

- `std::vector` for ordered records
- `std::set` for duplicate detection
- `std::map` for grouped aggregates
- `std::copy_if` for filtering
- `std::sort` for ordering
- `std::all_of` for validation assertions
- `std::map` for chronological monthly totals

The aggregation key is a pair consisting of region and category. This makes the grouping operation explicit and strongly typed.

The rolling calculation uses a running sum instead of recalculating every window from scratch. For `n` records and a fixed window, this reduces the rolling calculation to approximately `O(n)` time.

Exception handling surrounds the complete application workflow. Invalid input and invalid analytical parameters become controlled failures rather than undefined behavior.

## Java 17 Implementation

The Java implementation uses domain-oriented services.

`SalesRecord`, `EnrichedRecord`, `CustomerProfile`, `GroupKey`, and `Aggregate` are Java records. This makes immutable domain values concise and explicit.

The `SalesValidator` implements a generic `DataTransformer` interface. Validation checks duplicate identifiers, quantities, prices, discounts and date format.

`EnrichmentService` transforms source records into enriched records using Java streams.

`AggregationService` uses `Collectors.groupingBy()` to create grouped analytical results and `Collectors.summingDouble()` for monthly totals.

`QueryService` accepts a `Predicate<EnrichedRecord>`, allowing analytical conditions to be expressed independently from the service implementation.

`CustomerMergeService` performs dimension-style lookup against an immutable customer profile map.

`DataWorkflow` explicitly tracks processing state:

`RAW → VALIDATED → ENRICHED`

This makes the workflow state visible rather than allowing every operation to run against arbitrary input.

Custom `DataValidationException` handling distinguishes data-quality failures from ordinary application termination.

## PostgreSQL Implementation

The PostgreSQL implementation treats the dataset as a relational analytical model.

The `sales_orders` table stores the fact-like order records. `customer_dimension` provides customer attributes.

Database constraints enforce:

- Primary-key uniqueness
- Positive quantities
- Positive unit prices
- Valid discount ranges
- Required values

The `enriched_sales` view provides calculated columns without duplicating the derived values in the base table.

`calculate_net_sales()` centralizes the net-sales formula.

The `sales_with_customers` view performs the customer dimension join.

The `audit_sales_order()` trigger records successful validation events and rejects invalid business values before the row becomes available to analytical queries.

The aggregation function `region_category_report()` exposes grouped results as a relational function.

The quality-check function records transformation runs and compares source row counts with valid analytical rows.

Window functions are used for regional rankings and rolling monthly averages. These operations provide relational equivalents for common analytical DataFrame workflows.

The database also contains indexes on order dates, region/category combinations, customers and audit lookups. These indexes correspond to recurring access patterns rather than indexing every column.

## Filtering and Selection

The high-value electronics query illustrates a two-condition selection:

`category = Electronics`

and

`net_sales >= 50000`

The same logical operation appears in each implementation using the idioms appropriate to its language.

Filtering should occur before expensive downstream transformations when the business operation does not require the complete dataset. This can reduce memory consumption and computation for large datasets.

## Grouping and Aggregation

Grouping changes the analytical grain.

The source data has one row per order. Grouping by region and category produces one row per region/category combination.

The resulting measures include:

- Number of orders
- Units sold
- Total net sales
- Average order value

The distinction between row-level calculations and group-level calculations is important. `net_sales` is calculated at order level, while total regional sales are calculated after grouping.

## Joining and Dimension Data

Customer information is stored separately from order facts.

The relationship is:

`Sales Order → Customer → Customer Profile`

The Python implementation uses `merge()` with a many-to-one validation rule.

The JavaScript implementation uses a `Map`.

The Java implementation uses an immutable customer profile map.

The PostgreSQL implementation uses a foreign-key-like dimensional relationship through the customer value and a relational join.

The implementations preserve the distinction between fact data and descriptive dimension data.

## Missing Values

Missing values require explicit policy decisions.

The Python implementation demonstrates:

- Detection with `isna()`
- Replacement with `fillna()`
- Median-based numeric replacement
- Explicit `Unknown` categorical values

The other implementations represent the same concern using their native data structures. JavaScript uses nullish fallback behavior, Java uses explicit profile lookup handling, C++ uses validation before processing, and PostgreSQL uses `NOT NULL` constraints where absence is not acceptable.

Missingness should not automatically be replaced with zero. Zero represents a measured quantity, while a missing value represents unavailable information.

## Time-Based Analysis

The dataset spans January and February 2026.

The implementations derive a monthly key and calculate monthly totals.

The Python implementation uses datetime-aware Series operations. PostgreSQL uses `to_char()` and date extraction. C++ and Java use controlled date-string representations for the fixed sample data. JavaScript derives the month from the ISO date representation.

Rolling analysis is demonstrated through a three-order rolling mean in Python, JavaScript and C++. PostgreSQL uses a window frame over monthly aggregates.

The ordering dimension is essential. A rolling calculation without deterministic ordering does not have a meaningful temporal interpretation.

## Validation and Failure Handling

The implementations reject:

- Empty datasets
- Duplicate order identifiers
- Non-positive quantities
- Non-positive unit prices
- Invalid discount values
- Invalid dates
- Missing mandatory dimensions

Validation is performed before analytical calculations so invalid rows do not contaminate aggregate results.

The examples also deliberately exercise failure paths. Duplicate records and invalid discounts are expected to be rejected.

Database constraints provide a second validation layer. This is important because application-level validation alone cannot guarantee correctness when multiple clients can write to the same database.

## Performance Considerations

For a DataFrame workflow, vectorized column operations are generally preferable to Python-level row iteration for numerical transformations.

Grouping and joining can become expensive as datasets grow. Useful keys and controlled cardinality reduce unnecessary work.

The Python customer merge uses many-to-one validation to detect accidental dimension duplication.

The JavaScript implementation uses `Map` and `Set` for average constant-time lookup and membership behavior rather than repeatedly scanning arrays.

The C++ implementation uses associative containers for explicit grouping and uses a running sum for rolling windows.

The Java implementation uses stream-based grouping and immutable results. The trade-off is that streams can introduce allocation and abstraction overhead compared with tightly optimized loops.

The PostgreSQL implementation places filtering, grouping and aggregation close to the stored data. Appropriate indexes support selective queries, while unnecessary indexes are avoided because indexes add storage and write-maintenance costs.

## Security and Data Integrity

The examples use static local sample data and do not embed credentials.

Database-level constraints protect critical invariants independently of application code.

The PostgreSQL trigger records validation outcomes and rejects invalid rows.

The Python file export uses a temporary directory and controlled filenames rather than constructing a path from untrusted user input.

The JavaScript persistence example uses exclusive file creation and removes the temporary directory after processing.

The implementations avoid evaluating executable expressions supplied as data. Values remain data values rather than dynamically executed code.

## Conceptual Mapping

| Analytical concept | Pandas | JavaScript | C++17 | Java 17 | PostgreSQL |
|---|---|---|---|---|---|
| Table | `DataFrame` | `DataFrame` class | `vector<Record>` | `List<Record>` | Table/view |
| Column | `Series` | Object property | Struct field | Record component | Column |
| Filter | Boolean mask | Predicate | `copy_if` | Stream `filter` | `WHERE` |
| Grouping | `groupby` | `Map` | `map` | `groupingBy` | `GROUP BY` |
| Join | `merge` | `Map` lookup | Explicit lookup | Profile map | `JOIN` |
| Pivot | `pivot_table` | Map-derived rows | Grouped maps | Grouped collections | Conditional/grouped queries |
| Rolling | `rolling` | Window loop | Running sum | Ordered stream processing | Window functions |
| Missing values | `isna`, `fillna` | Nullish handling | Validation | Explicit lookup handling | `NULL`, constraints |
| Serialization | CSV/JSON | JSON/filesystem | I/O structures | Records/collections | Relational persistence |
| Validation | Assertions/exceptions | Exceptions | Exceptions/assertions | Custom exception | Constraints/triggers |

## Practical DataFrame Pattern

A typical analytical transformation represented by the Python implementation is:

`raw DataFrame`
→ `type normalization`
→ `quality validation`
→ `derived columns`
→ `boolean selection`
→ `groupby/aggregation`
→ `merge`
→ `pivot`
→ `rolling analysis`
→ `export`

Each stage should preserve a clearly defined data shape and meaning.

The central distinction is between manipulating individual values, manipulating columns as Series, and manipulating complete DataFrames. Reliable analytical workflows make those levels explicit and validate the transition between them.
