# Power BI Data Modeling: Relationships, Dimensions and Fact Tables

## Scope

This project models the relational concepts that support a Power BI analytical model, with particular emphasis on **fact tables**, **dimension tables**, **relationships**, **filter propagation**, and **measures**.

The implementations use a realistic sales domain:

`DimDate ─┐`
`DimCustomer ─┼──> FactSales`
`DimProduct ─┘`

The design follows a star-schema pattern. The central fact table records business events at a defined grain, while dimensions provide descriptive attributes used to filter, group, and analyze those events.

The five source files implement the same conceptual model from different engineering perspectives:

| File | Perspective | Main implementation |
|---|---|---|
| Python | Analytical simulation | Validated star-schema model with dimensional filtering and measures |
| JavaScript | Event-driven application model | Maps, immutable rows, event handling, asynchronous report evaluation |
| C++17 | Governance and performance model | Explicit validation, STL structures, efficient key-based lookups |
| Java 17 | Enterprise domain model | Records, immutable domain values, explicit model state and service-style queries |
| PostgreSQL | Relational source model | Dimensions, fact table, constraints, indexes, view, trigger, function, CTEs and transactions |

## Core Data-Model Architecture

The model separates descriptive context from measurable events.

### Fact Table

`FactSales` is the central transaction table. Each row represents one sales event for one order-product combination.

Its grain is:

**One fact row = one product line within one sales order.**

Typical measures include:

- Quantity
- Unit price
- Gross sales
- Discount amount
- Net sales

The fact table uses foreign keys to connect each event to the appropriate dimension row.

### Dimension Tables

The model contains three dimensions.

| Dimension | Purpose | Example attributes |
|---|---|---|
| `DimDate` | Time analysis | Year, quarter, month, calendar date |
| `DimCustomer` | Customer segmentation | Customer, segment, region |
| `DimProduct` | Product analysis | Product, category, subcategory |

Dimensions contain attributes that describe the business event rather than the event's numerical measurements.

## Relationships

The relationships use a many-to-one pattern from the fact table to each dimension.

`FactSales.date_key → DimDate.date_key`

`FactSales.customer_key → DimCustomer.customer_key`

`FactSales.product_key → DimProduct.product_key`

Conceptually, Power BI represents these as:

`DimDate 1 ───── * FactSales`

`DimCustomer 1 ─ * FactSales`

`DimProduct 1 ─── * FactSales`

The dimension side contains unique keys. The fact side can contain many rows referencing the same dimension key.

For example, many sales transactions may belong to the same customer:

`DimCustomer.customer_key = 1`

`FactSales.customer_key = 1` in multiple fact rows.

This cardinality is fundamental to star-schema modeling.

## Filter Propagation

The implementations use single-direction filtering from dimensions toward the fact table.

A filter such as:

`DimCustomer[Region] = "North"`

selects customer dimension rows belonging to the North region. The corresponding customer keys then identify the relevant fact rows.

The conceptual flow is:

`Region filter`
`    ↓`
`DimCustomer`
`    ↓`
`Customer Key`
`    ↓`
`FactSales`
`    ↓`
`Net Sales measure`

This separates filtering attributes from numerical aggregation.

Bidirectional filtering is deliberately not used in the model. It can create ambiguous filter paths when multiple relationships or dimensions provide routes between tables. A controlled star schema generally makes the filter direction explicit and predictable.

## Measures

The source implementations calculate measures from the fact table after dimensional filtering.

The principal measure is:

`Net Sales = Quantity × Unit Price × (1 - Discount Rate)`

The model also calculates total quantity and grouped sales.

Examples include:

- Total net sales
- Total quantity
- Software sales
- Enterprise customer sales
- Sales by region
- Sales by category
- Sales by month

The important modeling distinction is that the measure is calculated from fact values, while dimensions determine which fact rows participate in the calculation.

## Python Implementation

The Python file uses `dataclass` domain structures for dates, customers, products, facts, and relationships.

The `StarSchema` class owns the complete model.

Important mechanisms include:

- Dictionary-based dimension storage
- List-based fact storage
- Enumerations for relationship cardinality and filter direction
- Explicit validation
- Foreign-key checks
- Decimal arithmetic for monetary values
- Filtered fact retrieval
- Category, region, and month aggregation
- Duplicate-key detection
- Failure-case demonstrations

Dimension dictionaries provide approximately constant-time key lookup.

The `validate()` method checks that every fact references an existing date, customer, and product dimension row.

The implementation also rejects bidirectional relationships because the model is intentionally designed around controlled dimension-to-fact filtering.

## JavaScript Implementation

The JavaScript implementation treats the model as an event-driven application.

`DimensionTable` uses `Map` to index dimension rows by key. This gives direct key lookup without scanning the dimension.

`FactSalesTable` validates:

- Fact-key uniqueness
- Positive quantities
- Non-negative prices
- Valid discount rates
- Existing dimension keys

Rows are frozen before storage, reducing accidental mutation.

`StarSchemaModel` extends `EventEmitter`. Adding a fact emits a `saleAdded` event. This demonstrates how an analytical data model can participate in an application workflow rather than being limited to static calculations.

The asynchronous report method uses a Promise boundary to represent report-query or service behavior.

Filtering remains dimension-aware:

`year → DimDate`

`region/segment → DimCustomer`

`category → DimProduct`

followed by aggregation over the selected fact rows.

## C++17 Implementation

The C++ implementation focuses on explicit structures and efficient storage.

The model uses:

- `struct` for dimensions and facts
- `unordered_map` for dimension-key lookup
- `vector` for fact storage
- `set` for fact-key uniqueness
- `map` for deterministic grouped output
- `optional` for optional report filters
- Exceptions for invalid model state

The implementation validates all foreign-key relationships before accepting a fact row.

The query operation first filters the fact records using dimension attributes. Aggregation then operates on the selected records.

This produces a clear separation:

`Dimension lookup → Fact filtering → Measure aggregation`

The primary performance characteristic is efficient dimension lookup. If there are `F` fact rows and the filter requires scanning all facts, the fact filtering step is approximately `O(F)`. Dimension-key lookup is approximately `O(1)` on average with `unordered_map`.

## Java 17 Implementation

The Java implementation uses an enterprise-oriented domain model.

Java records represent immutable:

- Date dimensions
- Customer dimensions
- Product dimensions
- Sales facts
- Relationships

`DataModel` controls the lifecycle of the model through:

`DRAFT → VALIDATED`

Queries are rejected until validation succeeds.

The model uses `BigDecimal` for monetary calculations rather than binary floating-point arithmetic.

Streams are used for grouped reporting operations, while predicates provide reusable filtering behavior.

Validation explicitly checks:

- Required dimensions
- Relationship cardinality
- Filter direction
- Foreign-key references
- Fact-key uniqueness
- Numeric constraints

This makes the model state explicit rather than treating validation as an incidental operation.

## PostgreSQL Implementation

The PostgreSQL file provides the most database-oriented representation.

The schema contains:

- `dim_date`
- `dim_customer`
- `dim_product`
- `fact_sales`

Primary keys identify dimension rows. Foreign keys enforce fact-to-dimension relationships.

The fact table also contains a uniqueness rule on:

`order_id + product_key`

This prevents duplicate product lines for the same order.

### Database Constraints

The model uses database-level constraints for:

- Positive quantities
- Non-negative prices
- Valid discount ranges
- Valid customer segments
- Valid customer regions
- Valid product categories
- Required foreign keys
- Unique business identifiers

These rules protect the data before it reaches a reporting layer.

### Indexes

Indexes are created on fact foreign keys and common dimensional filtering columns.

The fact foreign-key indexes support joins between the central fact table and dimensions.

The customer and product indexes support common report filters such as region, segment, category, and subcategory.

Indexes have a write and storage cost, so the model does not create indexes indiscriminately.

### Analytical View

`vw_sales_model` joins the normalized source tables into an analytical shape.

It exposes:

- Date attributes
- Customer attributes
- Product attributes
- Quantity
- Unit price
- Gross sales
- Discount amount
- Net sales

The view demonstrates the difference between a normalized relational source model and the denormalized analytical representation commonly consumed by reporting logic.

### Function

`calculate_net_sales()` provides a reusable SQL measure.

It accepts optional:

- Year
- Region
- Product category

filters.

This corresponds conceptually to applying dimension filters before evaluating a fact-based measure.

### Trigger

`validate_fact_relationships()` provides an explicit trigger-based relationship validation layer.

PostgreSQL foreign keys already enforce the actual referential integrity. The trigger demonstrates how application-specific relationship validation can be added when required.

### Transaction

The `BEGIN` and `COMMIT` section demonstrates transactional insertion of a fact row after resolving its dimension keys.

The transaction ensures that the operation is treated as one unit of database work.

## Fact Table Grain

Grain is one of the most important decisions in a dimensional model.

This implementation defines:

`One FactSales Row = One Product Line of One Sales Order`

Because the grain is fixed, the numerical fields have predictable meaning.

For example:

`quantity = 3`

means three units for that particular order-product event.

Changing the grain without redesigning the measures can produce incorrect aggregations.

A separate inventory snapshot fact, for example, would have a different grain:

`One Row = One Product at One Location on One Date`

That table should not simply be mixed with transactional sales facts because its measures have different semantics.

## Dimension Keys

The model uses surrogate-style integer keys for customers and products.

For example:

`customer_key = 1`

is an internal warehouse identifier.

`customer_id = "C001"`

is the business identifier.

Separating these values allows the analytical model to maintain stable internal relationships even when operational business identifiers change.

The date dimension uses an integer date key such as:

`20260105`

which represents `2026-01-05`.

## Relationship Validation

The implementations explicitly reject orphan facts.

An orphan fact would contain a foreign key that has no corresponding dimension row.

For example:

`FactSales.customer_key = 999`

is invalid if customer 999 does not exist.

At the database level, PostgreSQL rejects the row through a foreign-key constraint.

At the application level, the Python, JavaScript, C++17, and Java 17 implementations perform equivalent validation.

This produces defense in depth:

`Application validation`
`        ↓`
`Relational constraints`
`        ↓`
`Analytical model`

## Dimensional Filtering Versus Aggregation

The model separates two operations.

### Filtering

Filtering determines which fact rows participate.

Examples:

`Region = North`

`Category = Software`

`Segment = Enterprise`

`Year = 2026`

### Aggregation

Aggregation calculates values over the filtered fact rows.

Examples:

`SUM(Net Sales)`

`SUM(Quantity)`

`Sales by Category`

`Sales by Region`

This separation is central to dimensional analytics.

A dimension should primarily provide context for the fact table rather than duplicating fact measures across descriptive tables.

## Edge Cases

The implementations cover several failure conditions.

| Failure case | Expected behavior |
|---|---|
| Duplicate fact key | Rejected |
| Missing date dimension | Rejected |
| Missing customer dimension | Rejected |
| Missing product dimension | Rejected |
| Zero or negative quantity | Rejected |
| Negative unit price | Rejected |
| Discount below zero | Rejected |
| Discount above one | Rejected |
| Unsupported relationship direction | Rejected |
| Query before model validation | Rejected in Java |
| Empty required model | Rejected during validation |

These checks distinguish a usable data model from a collection of unrelated tables.

## Performance Considerations

The principal fact-table cost is aggregation over the selected rows.

For `F` fact rows, a simple scan-based measure is approximately `O(F)`.

Dimension lookups are optimized with keyed structures:

- Python: dictionaries
- JavaScript: `Map`
- C++17: `unordered_map`
- Java: `LinkedHashMap`
- PostgreSQL: indexed primary and foreign keys

For large analytical datasets, Power BI models also benefit from columnar storage and compression. The relational source schema and the semantic model should therefore be considered separate layers with different optimization objectives.

A normalized transactional database can prioritize update integrity, while an analytical model can prioritize scan efficiency and intuitive dimensional filtering.

## Security and Data Integrity

The model does not embed credentials or external service dependencies.

Security-relevant design decisions include:

- Strong database constraints
- Referential integrity
- Explicit validation
- Controlled relationships
- No dynamic SQL
- No unvalidated external identifiers
- Immutable application-domain records where appropriate
- Separation of descriptive attributes from transactional measurements

At the database layer, access control should be applied separately from the data model itself. The source schema should expose only the tables and views required by the reporting workload.

## Relationship Between the Five Implementations

The files intentionally solve the same modeling problem differently.

`Python`
`  ↓`
`Simulation and validation`

`JavaScript`
`  ↓`
`Event-driven application behavior`

`C++17`
`  ↓`
`Efficient in-memory model and query processing`

`Java 17`
`  ↓`
`Explicit enterprise domain model and state management`

`PostgreSQL`
`  ↓`
`Persistent relational source with enforced integrity`

The conceptual model remains consistent even though the implementation mechanisms differ.

## Practical Modeling Distinctions

The following concepts should not be treated as interchangeable:

| Concept | Role |
|---|---|
| Fact table | Stores measurable business events |
| Dimension table | Stores descriptive analytical context |
| Primary key | Uniquely identifies a table row |
| Foreign key | Connects a fact to a dimension |
| Relationship | Defines how tables are connected and filtered |
| Cardinality | Describes how many rows can relate across the connection |
| Filter direction | Determines how filters propagate |
| Measure | Calculates values from model data |
| Grain | Defines exactly what one fact row represents |
| Star schema | Organizes facts around descriptive dimensions |

## Expected Analytical Workflow

A report query follows the conceptual sequence:

`User selects Region`
`        ↓`
`DimCustomer is filtered`
`        ↓`
`Customer keys identify relevant facts`
`        ↓`
`FactSales is filtered`
`        ↓`
`Net Sales measure is evaluated`
`        ↓`
`Visual receives aggregated result`

For a product analysis:

`Product Category`
`      ↓`
`DimProduct`
`      ↓`
`Product Key`
`      ↓`
`FactSales`
`      ↓`
`SUM(Net Sales)`

For a time analysis:

`Year / Quarter / Month`
`          ↓`
`DimDate`
`          ↓`
`Date Key`
`          ↓`
`FactSales`
`          ↓`
`SUM(Net Sales)`

## Educational Focus

The project emphasizes the modeling decisions that matter when designing a Power BI-ready data structure:

- Define fact-table grain before adding measures.
- Keep descriptive attributes in dimensions.
- Keep measurable events in facts.
- Use stable keys for relationships.
- Prefer clear one-to-many dimensional relationships.
- Keep filter propagation predictable.
- Validate referential integrity.
- Use measures over fact data rather than duplicating calculations.
- Treat transactional and analytical schemas as different design layers.
- Optimize storage and querying according to the workload.

The resulting model provides a concrete foundation for understanding how relationships, dimensions, fact tables, and measures work together in a Power BI data model.
