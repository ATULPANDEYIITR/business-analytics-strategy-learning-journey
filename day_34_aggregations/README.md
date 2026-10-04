# Aggregations: COUNT, SUM, AVG, MIN and MAX

## Topic Scope

Aggregation converts multiple rows or records into descriptive values. The core aggregate functions covered here are `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`.

The central distinction is between **row-level values** and **group-level results**. A row contains an individual order, while an aggregate describes a collection of orders. Filtering determines which rows participate in the calculation, and grouping determines which rows contribute to each aggregate result.

The three implementations use the same business domain, but they approach aggregation differently:

- The Python implementation builds reusable aggregate functions, grouped calculations, validation rules, and a streaming-style accumulator.
- The JavaScript implementation emphasizes `reduce()`, `Map`, event-driven processing, asynchronous iteration, and JavaScript numeric behavior.
- The C++ implementation models a strongly typed sales aggregation engine with exact integer-cent representation for money and mergeable aggregate state.

The examples use orders containing quantity, unit price, region, category, and status. Revenue is derived as `quantity × unitPrice`.

---

## Aggregate Function Semantics

### COUNT

`COUNT(*)` counts rows. It does not care whether a particular column contains a missing value.

`COUNT(column)` counts only rows for which that column is non-null.

This distinction is important when a dataset contains missing measurements. If five rows exist and two values are missing, `COUNT(*)` returns five while `COUNT(column)` returns three.

The Python implementation represents missing values with `None`. The JavaScript implementation treats both `null` and `undefined` as missing at the aggregation boundary. The C++ implementation uses `std::optional` inside its aggregation state to represent a value that may not exist.

### SUM

`SUM` adds all non-null values participating in the aggregate.

For order data, `SUM(quantity)` measures the number of units represented by the rows. `SUM(quantity × unitPrice)` measures revenue when the rows represent completed sales.

The meaning of the result depends strongly on the input expression. Summing unit prices and summing order revenue answer different business questions.

The implementations therefore calculate revenue from each order rather than incorrectly treating `unitPrice` as the order's total value.

### AVG

`AVG` is an arithmetic mean:

`AVG(value) = SUM(non-null value) / COUNT(non-null value)`

The denominator is important. Missing values do not contribute to the count used by the average.

For example, values `10`, `20`, `NULL`, and `40` produce:

- `COUNT(*) = 4`
- `COUNT(value) = 3`
- `SUM(value) = 70`
- `AVG(value) = 70 / 3`

An empty input does not have a meaningful minimum, maximum, or average. The implementations represent those results as `None`, `null`, or `std::nullopt`, depending on the language.

### MIN

`MIN` identifies the smallest non-null value.

For order revenue, it identifies the smallest completed order value in the selected population. It is not the same as the minimum unit price unless unit price is explicitly the aggregated expression.

### MAX

`MAX` identifies the largest non-null value.

For order revenue, it identifies the largest completed order value. It can be useful for identifying unusually large transactions, maximum quantities, highest prices, or peak measurements.

---

## Filtering and Aggregation

Filtering and aggregation operate at different stages.

Consider completed sales. The relevant workflow is conceptually:

`orders → filter status = completed → calculate aggregates`

If cancelled orders are included in the `SUM`, the resulting revenue is no longer a completed-sales metric.

The Python program explicitly constructs completed orders before calculating revenue. The JavaScript program uses `filter()` followed by aggregation. The C++ engine applies the status rule during ingestion so that cancelled and pending orders remain visible to the raw order count but do not enter completed-sales aggregates.

This distinction becomes especially important in production reporting because a mathematically correct aggregate can still represent the wrong business population.

---

## GROUP BY-Style Aggregation

A scalar aggregation produces one result:

`COUNT(*) → 10`

A grouped aggregation produces a result for each group:

`region → COUNT(*)`

For the order dataset, regions such as North, South, East, and West become independent aggregation groups.

Conceptually:

`GROUP BY region`

creates separate populations. `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX` are then calculated independently within each population.

The Python implementation creates a dictionary whose keys are regions. The JavaScript implementation uses `Map`, which makes the grouping operation explicit and preserves the relationship between a group key and its records. The C++ implementation uses `std::map<std::string, AggregateState>` for region and category aggregates.

Grouped aggregation is the basis for reports such as regional revenue, category sales volume, average order value by market, and maximum transaction size by product category.

---

## Aggregate Expressions

Aggregation applies to expressions, not only stored columns.

For an order:

`revenue = quantity × unitPrice`

Therefore:

`SUM(quantity × unitPrice)`

answers a different question from:

`SUM(unitPrice)`

The implementations calculate revenue at the record level before passing it into `SUM`, `AVG`, `MIN`, or `MAX`.

This pattern is useful whenever the reported metric is derived from multiple attributes.

Examples directly related to the order model include:

- `SUM(quantity)` for total units
- `AVG(unitPrice)` for average unit price
- `SUM(quantity × unitPrice)` for revenue
- `MIN(quantity × unitPrice)` for the smallest order
- `MAX(quantity × unitPrice)` for the largest order

---

## Post-Aggregation Filtering

Filtering individual rows is different from filtering aggregate results.

A row-level condition such as completed status decides whether an order participates in the calculation.

A condition such as:

`SUM(revenue) >= 2000`

cannot be evaluated correctly against an individual order because the value depends on the complete group.

This is the role of a `HAVING`-style condition. The implementations calculate grouped revenue first and then select groups whose aggregate reaches the threshold.

The Python and JavaScript programs demonstrate this directly. The C++ program exposes the behavior through `printHighRevenueRegions()`.

---

## Python Implementation

The Python program is structured around reusable functions and a reusable `Aggregator` class.

### Core implementation

`count_rows()` models `COUNT(*)`.

`count_non_null()` models `COUNT(column)` by excluding `None`.

`sum_values()` accumulates non-null `Decimal` values.

`average_values()` explicitly calculates the mean using the number of non-null values.

`min_value()` and `max_value()` return `None` when no non-null value exists.

The use of `Decimal` is deliberate for monetary calculations. Binary floating-point arithmetic can represent some decimal fractions approximately, while `Decimal("0.10")` preserves decimal-oriented arithmetic behavior expected by financial reporting.

### Grouping

`group_by()` constructs groups based on a key function. The same mechanism is used for regional and category analysis.

`aggregate_order_group()` then calculates multiple metrics for each group.

This separates the mechanics of grouping from the mechanics of aggregation, which is useful when the same aggregation policy must be applied to several dimensions.

### Streaming aggregation

The `Aggregator` class maintains:

- total row count
- non-null count
- sum
- minimum
- maximum

It does not need to retain all values merely to calculate these five metrics.

For a stream of `n` values, the accumulator requires one pass through the input and constant aggregation state, excluding the memory used by the input source itself.

This is substantially different from building a list of every value and then performing separate operations over that list.

### Validation

`validate_orders()` rejects invalid quantities, negative prices, and unsupported statuses.

Validation is part of aggregation correctness. If invalid records enter the population, `SUM` or `AVG` may be numerically correct for the supplied values but still produce an invalid business result.

---

## JavaScript Implementation

The JavaScript program emphasizes mechanisms that are natural in the JavaScript runtime.

### Array reduction

`sumValues()` uses `reduce()` to build a total.

This reflects a common JavaScript aggregation pattern where an array is transformed into a scalar result.

The implementation also validates numeric inputs so that values such as `NaN` or infinite values do not silently contaminate the aggregate.

### Map-based grouping

`groupBy()` uses `Map` to associate a region or category with its records.

The approach is more explicit than repeatedly scanning the entire order collection for every possible region. Each record is assigned to a group during one traversal.

### Event-driven aggregation

`OrderAggregator` extends `EventEmitter`.

The `process()` method updates aggregate state and emits an `orderProcessed` event. A consumer can subscribe to that event without changing the aggregation logic.

This models an event-driven application in which records arrive continuously and multiple consumers may react to processed events.

### Asynchronous iteration

`orderStream()` is an asynchronous generator.

`aggregateAsync()` consumes it with `for await...of`.

The example uses an in-memory source, but the important mechanism is the asynchronous interface. The same programming model can represent data arriving from a database cursor, message source, file reader, or network-driven pipeline.

### JavaScript numeric considerations

JavaScript `Number` uses IEEE 754 floating-point representation. Values such as `0.1` cannot always be represented exactly.

The program demonstrates this behavior and distinguishes display rounding from exact decimal arithmetic.

For monetary aggregation, production JavaScript systems should use an appropriate exact representation, such as integer minor units or a dedicated decimal arithmetic implementation, rather than assuming `toFixed()` changes the underlying arithmetic model.

`BigInt` is also demonstrated for exact large integer quantities. It is useful for integer counts beyond the safe range of JavaScript `Number`, but it cannot be freely mixed with `Number`.

---

## C++ Case Study: Sales Aggregation Engine

The C++ program models a regional sales reporting engine.

The system receives orders and produces aggregate metrics for completed sales.

### Architecture

The main components are:

`Order`

Represents a validated sales record.

`Money`

Stores monetary values as integer cents rather than binary floating-point numbers.

`AggregateState`

Stores the state required for `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`.

`SalesAggregationEngine`

Coordinates ingestion, validation, status filtering, overall aggregation, and grouped aggregation.

This produces a coherent pipeline:

`Order → validation → status policy → aggregate state → grouped report`

### Exact monetary representation

The C++ implementation stores `$850.00` as `85000` cents.

This avoids relying on binary floating-point representation for the underlying monetary total.

`Money` provides addition, multiplication by integer quantity, comparison, and display conversion.

The internal aggregate remains integer-based while formatted output is converted to decimal notation.

### Aggregate state

`AggregateState` stores:

- `count`
- `nonNullCount`
- `sum`
- optional minimum
- optional maximum

The average is derived from `sum / nonNullCount`.

Using `std::optional<Money>` allows an empty aggregate to distinguish "no value exists" from a real zero monetary value.

### Status policy

The engine counts every received order through `allOrders_`.

Only completed orders enter the completed-sales aggregate.

This distinction prevents pending and cancelled transactions from contaminating completed-sales revenue while preserving visibility into the raw input population.

### Grouped aggregation

Two grouped dimensions are maintained:

`region → AggregateState`

and:

`category → AggregateState`

The same aggregate state structure therefore supports both geographic and product-oriented reporting.

### Post-aggregation threshold

`printHighRevenueRegions()` evaluates the region's accumulated `SUM(revenue)` against a threshold.

This models a `HAVING`-style decision because the condition is based on an aggregate result rather than an individual row.

### Partition and merge

The C++ program also demonstrates an important property of distributable aggregation.

The dataset is divided into two partitions. Each partition independently calculates an `AggregateState`. `mergeAggregates()` combines those partial states.

This works naturally for `COUNT` and `SUM`. `MIN` and `MAX` can also be merged by selecting the smaller or larger partial result. `AVG` is not merged by simply averaging two averages. The correct merged average requires the combined sum and combined non-null count.

This property is fundamental to large-scale aggregation systems because data can be processed in partitions and the partial results can later be combined.

---

## NULL and Empty-Input Behavior

Missing values require explicit semantics.

For values:

`10, NULL, 30`

the relevant results are:

| Aggregate | Result |
|---|---:|
| `COUNT(*)` | 3 |
| `COUNT(value)` | 2 |
| `SUM(value)` | 40 |
| `AVG(value)` | 20 |
| `MIN(value)` | 10 |
| `MAX(value)` | 30 |

An empty population is different from a population containing zero.

For an empty input:

- `COUNT(*)` is zero.
- `COUNT(value)` is zero.
- `SUM` has no contributing values.
- `AVG` has no denominator.
- `MIN` has no candidate minimum.
- `MAX` has no candidate maximum.

The implementations explicitly represent unavailable `AVG`, `MIN`, and `MAX` results instead of inventing a numeric value.

---

## Common Aggregation Errors

### Counting the wrong population

Calculating the count before applying a business filter can produce a value that does not represent the intended population.

For example, a completed-order metric must not accidentally count pending and cancelled transactions.

### Averaging averages

Suppose one region has two orders with an average of `100`, while another region has eight orders with an average of `200`.

The overall average is not `(100 + 200) / 2`.

The correct calculation requires the underlying counts and sums:

`overall average = combined sum / combined count`

The C++ mergeable aggregate state demonstrates why maintaining `SUM` and `COUNT` is necessary for correct distributed averages.

### Summing the wrong measure

`SUM(unitPrice)` does not calculate revenue when an order contains multiple units.

Revenue requires:

`quantity × unitPrice`

at the row level, followed by aggregation.

### Treating missing values as zero

A missing value does not necessarily mean the measured quantity was zero.

Replacing missing values with zero before calculating `AVG` changes the denominator and therefore changes the meaning of the result.

### Using floating point carelessly for money

A mathematically simple expression such as `0.1 + 0.1 + 0.1` illustrates why binary floating-point representation should not automatically be treated as exact decimal currency arithmetic.

The C++ implementation avoids this issue by storing cents. The Python implementation uses `Decimal`.

---

## Performance Characteristics

For `n` input values, a normal aggregate calculation requires `O(n)` time.

A single-pass implementation of `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX` can maintain the necessary state in `O(1)` additional memory.

Grouped aggregation requires memory proportional to the number of groups and their maintained state. If there are `g` groups, the aggregate state itself can be approximately `O(g)` even when the original records are streamed.

Sorting-based grouping can introduce `O(n log n)` behavior, while hash-based grouping can approach `O(n)` average time. The Python dictionary and JavaScript `Map` approaches provide hash-oriented grouping behavior, while the C++ example uses `std::map`, which keeps keys ordered and therefore has logarithmic insertion and lookup characteristics.

For very large datasets, the most important optimization is often avoiding unnecessary materialization of all records or all intermediate values.

---

## Validation and Data Quality

Aggregation does not repair bad data.

Before calculating business metrics, production systems should define valid ranges and acceptable states for the fields that participate in the metric.

The examples enforce rules such as:

- quantities must be positive
- monetary prices cannot be negative
- order statuses must belong to the supported status set
- identifiers must be valid
- non-finite JavaScript numeric values must not enter numeric aggregation

The appropriate rule depends on the business meaning of the dataset. A negative value might be invalid for a unit price but valid for an accounting adjustment, so validation should be based on domain semantics rather than on generic assumptions.

---

## Production Considerations

Aggregation logic should make the population being measured explicit.

A production report should be able to answer:

- Which rows were included?
- Which rows were excluded?
- Which fields were nullable?
- What unit does `SUM` represent?
- What denominator does `AVG` use?
- Which time or status filters were applied?
- Which grouping dimensions were used?
- What happens when no rows qualify?
- Are monetary values represented exactly enough for the required business precision?

For distributed systems, aggregate state should be designed so that partial results can be merged without changing the mathematical meaning of the result.

For averages, this means retaining sufficient state such as `sum` and `count`, rather than retaining only an average.

For financial data, the numeric representation should be chosen before the aggregation layer is built. Converting inaccurate floating-point results into formatted currency after the calculation does not make the calculation exact.

---

## Relationship Between the Three Implementations

The implementations deliberately use different technical perspectives.

| Area | Python | JavaScript | C++ |
|---|---|---|---|
| Basic aggregation | Reusable functions | Array operations and `reduce()` | Typed aggregate state |
| Missing values | `None` | `null` / `undefined` | `std::optional` |
| Grouping | `dict` | `Map` | `std::map` |
| Streaming | `Aggregator` | Async generator | Partition aggregation |
| Event processing | Not central | `EventEmitter` | Explicit ingestion engine |
| Monetary representation | `Decimal` | `Number` with precision discussion | Integer cents |
| Distributed aggregation | Streaming state | Single-pass state | Mergeable partial states |
| Validation | Dedicated validation function | Runtime validation | Typed exception-based validation |

The common mathematical definitions remain the same, but the implementation choices reflect the strengths and constraints of each language.

---

## Executable Behavior

The Python program can be executed directly with a standard Python installation.

The JavaScript program can be executed with Node.js and uses only built-in runtime functionality.

The C++ program requires C++17 or later and uses only the standard library.

Each implementation contains executable checks for important aggregation invariants. These checks verify counts, totals, minimums, maximums, averages, missing-value behavior, and empty-input behavior.

The resulting programs are therefore both demonstrations of aggregate-function semantics and working examples of how those semantics can be incorporated into application-level data-processing systems.
