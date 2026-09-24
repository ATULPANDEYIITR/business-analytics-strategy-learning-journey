# Excel Tables: Structured Data and Dynamic Calculations

## Topic introduction

An Excel Table is a structured collection of related data organized into named columns and records. Unlike an ordinary cell range, a Table provides a formal structure for data entry, filtering, sorting, calculated columns, totals, and formula references.

The central idea is to treat spreadsheet data as a small data model rather than as an arbitrary collection of cells.

For example, a sales table can contain columns such as `Order ID`, `Customer`, `Region`, `Product`, `Quantity`, `Unit Price`, `Discount Rate`, and `Net Amount`.

A calculated column can then derive `Net Amount` from other columns:

`Net Amount = Quantity × Unit Price × (1 − Discount Rate)`

When a new row is added to an Excel Table, calculated-column formulas can automatically propagate into the new record. This dynamic behavior is one of the principal advantages of structured tables.

The three implementations in this study model the same underlying concepts using Python, JavaScript, and C++.

---

## Fundamental concepts

### Structured data

Structured data follows a predictable schema.

A sales record might contain:

- Order ID
- Customer
- Region
- Product
- Category
- Quantity
- Unit Price
- Discount Rate
- Order Date

Each row represents one logical record, while each column represents one attribute of that record.

A well-designed table normally follows the principle of one fact per field and one logical record per row.

### Excel Table

An Excel Table is a named structured range containing:

- headers,
- data rows,
- optional totals,
- filtering controls,
- sorting capabilities,
- formatting,
- calculated columns,
- structured references.

If a range is converted into an Excel Table, formulas and references can use column names rather than relying exclusively on cell coordinates.

### Ordinary range versus Table

An ordinary range might refer to data as:

`A2:H100`

An Excel Table can refer to a column conceptually as:

`SalesTable[Net Amount]`

A current-row reference can conceptually be expressed as:

`[@[Net Amount]]`

The structured form is more descriptive because it identifies the logical column instead of depending on a particular column letter.

### Record

A record is one complete row representing one logical entity or transaction.

For example:

`Order ID = 1001`

identifies one sales transaction.

### Field

A field is an individual attribute of a record.

Examples include:

`Customer`

`Region`

`Quantity`

`Unit Price`

### Column

A column contains the same type of attribute across many records.

A `Quantity` column should normally contain quantities rather than a mixture of quantities, notes, subtotals, and unrelated text.

### Calculated column

A calculated column derives values from other fields.

For example:

`Gross Amount = Quantity × Unit Price`

`Discount Amount = Gross Amount × Discount Rate`

`Net Amount = Gross Amount − Discount Amount`

The Python, JavaScript, and C++ implementations all demonstrate this dependency chain.

---

## Core principles of structured tables

A reliable structured-data design generally follows these principles:

1. Keep one logical record per row.
2. Give every column a meaningful name.
3. Keep data types consistent.
4. Avoid unnecessary blank rows inside the data set.
5. Avoid merged cells inside the structured data.
6. Separate source inputs from calculated outputs.
7. Validate important input fields.
8. Keep calculations deterministic.
9. Use explicit handling for missing values.
10. Avoid duplicating the same business rule across many unrelated formulas.
11. Use lookup structures efficiently when repeated searches are required.
12. Keep confidential information appropriately protected.

These principles apply beyond Excel. They are also fundamental to databases, programming data structures, APIs, reporting systems, and analytical pipelines.

---

## Structured references

Structured references are one of the defining features of Excel Tables.

A reference such as:

`SalesTable[Net Amount]`

represents the `Net Amount` column.

A reference such as:

`SalesTable[@[Net Amount]]`

represents the value from the current row.

Special table references can also identify table headers, data rows, and totals.

The exact syntax depends on the Excel formula context, but the conceptual distinction is important:

- a column reference represents many records,
- a current-row reference represents one record,
- a table reference represents the structured data set.

The Python implementation models a column reference with a list comprehension over the named column:

`[row["Net Amount"] for row in table]`

The JavaScript implementation uses:

`table.rows.map(row => row.netAmount)`

The C++ implementation stores each field as a member of `SalesRecord`.

---

## Calculated columns

A calculated column applies the same logical rule to every row.

Consider the following calculation chain:

`Gross Amount = Quantity × Unit Price`

`Discount Amount = Gross Amount × Discount Rate`

`Net Amount = Gross Amount − Discount Amount`

The first calculation depends only on input columns.

The second depends on the first calculated value.

The third depends on both previous calculations.

This creates a dependency graph:

`Quantity + Unit Price → Gross Amount`

`Gross Amount + Discount Rate → Discount Amount`

`Gross Amount + Discount Amount → Net Amount`

A well-designed calculation system must respect these dependencies.

### Python implementation

The Python `StructuredTable` class contains the `calculated_column()` method.

The following logical operation is represented by:

`table.calculated_column("Gross Amount", lambda row: ...)`

The function receives the current record and calculates its derived value.

The next calculated columns use the results of earlier calculations.

Python's dictionary-based records make named-field access explicit:

`row["Quantity"]`

`row["Unit Price"]`

`row["Gross Amount"]`

This closely communicates the relationship between structured columns.

### JavaScript implementation

JavaScript uses objects to represent records.

A calculated column is implemented by:

`table.addCalculatedColumn("grossAmount", row => ...)`

Properties are accessed using expressions such as:

`row.quantity`

The implementation also demonstrates how `Array.prototype.map()`, `filter()`, and `sort()` naturally operate on structured records.

### C++ implementation

The C++ case study represents each record with the `SalesRecord` structure.

The `SalesCalculationEngine` class centralizes calculation logic.

This separation makes the architecture more explicit:

`SalesRecord` represents data.

`SalesCalculationEngine` represents calculation rules.

`SalesTable` manages the collection and lookup operations.

---

## Dynamic table expansion

One of the important behaviors of an Excel Table is its ability to expand when new records are added.

Suppose the original table contains five sales records. A sixth record is inserted beneath the table.

The Table can automatically incorporate the new record, extend formatting, and propagate calculated-column formulas.

The Python example demonstrates this by calling `add_row()` and then recalculating the derived fields.

The JavaScript example uses `addRow()` followed by recalculation.

The C++ example calculates derived values during insertion itself.

This illustrates an important architectural distinction.

A static range is primarily a location.

A structured table is primarily a collection of records with a schema.

---

## Dynamic calculations

A dynamic calculation is one whose result changes when the underlying records change.

For example:

`Net Amount = Quantity × Unit Price × (1 − Discount Rate)`

If `Quantity` changes from `2` to `3`, the calculated result should change.

This is the same dependency principle used in spreadsheet formulas, databases, business intelligence systems, and software applications.

The C++ case study explicitly demonstrates recalculation after changing an input quantity.

---

## Relative and absolute references

Spreadsheet formulas distinguish between references that should change when copied and references that should remain fixed.

A conceptual example is:

`=[@Amount]*(1+$B$1)`

The current row's amount changes for every record, while `$B$1` represents a shared parameter.

The Python implementation models this distinction with:

- a row-specific amount,
- a shared tax rate.

The same conceptual pattern occurs in software systems.

A record-specific variable is analogous to a relative reference.

A shared configuration value is analogous to an absolute reference.

---

## Filtering

Filtering selects records that satisfy a condition.

Examples include:

`Region = North`

`Net Amount >= 50000`

`Region = North AND Net Amount >= 50000`

The Python implementation uses the `filter()` method with a predicate.

The JavaScript implementation uses array filtering.

The C++ implementation accepts a predicate function and creates a new collection containing matching records.

Filtering is important because it separates the full data set from the current analytical view.

A filter should not normally be treated as deleting data.

It changes which records are being viewed or processed.

---

## Sorting

Sorting changes the order in which records are presented.

The examples sort sales records by `Net Amount`.

Sorting by a numeric measure in descending order makes high-value transactions appear first.

The underlying data structure and the sorted presentation should conceptually remain separate.

The Python implementation creates a sorted `StructuredTable`.

The JavaScript implementation creates a sorted table using `sort()`.

The C++ implementation copies the records and uses `std::sort`.

For `n` records, comparison-based sorting generally requires approximately `O(n log n)` comparisons.

---

## Aggregation

Structured tables are frequently used for aggregation.

Common aggregations include:

- sum,
- average,
- count,
- minimum,
- maximum,
- grouped totals.

The sales implementation calculates:

`Total Sales`

`Average Order Value`

`Total Profit`

`Sales by Region`

`Units by Category`

These operations correspond conceptually to spreadsheet functions such as `SUM`, `AVERAGE`, and `COUNT`, as well as grouped analytical operations.

---

## Totals rows

An Excel Table can contain a Totals Row.

The Totals Row can display aggregate information without mixing summary records into the main data set.

This distinction is important.

A data row represents a transaction.

A totals row represents an aggregate calculation.

The Python implementation uses `calculate_totals_row()`.

The JavaScript implementation uses `calculateTotalsRow()`.

The C++ implementation provides aggregation methods directly on `SalesTable`.

Keeping aggregate calculations separate from transactional records prevents the table from becoming structurally ambiguous.

---

## Data validation

Structured data is only useful when its inputs are reliable.

The implementations validate conditions such as:

- positive order IDs,
- non-empty customers,
- valid regions,
- positive quantities,
- non-negative prices,
- discount rates between zero and one.

Excel can enforce many similar constraints using Data Validation.

Programming languages provide an additional advantage because validation can be made explicit, reusable, testable, and enforceable before data enters the calculation system.

### Invalid values

Examples include:

`Quantity = 0`

`Unit Price = -100`

`Discount Rate = 1.5`

`Region = Unknown`

Such values should be rejected or explicitly handled rather than silently producing misleading results.

---

## Missing values

A blank cell is not necessarily equivalent to zero.

For example:

- missing quantity may indicate incomplete data,
- zero quantity may represent a legitimate zero,
- missing price may indicate an import problem,
- zero price may represent a free item.

The Python example returns `None` when required inputs are missing.

The JavaScript example uses `null`.

The distinction is important because replacing all missing values with zero can hide data-quality problems.

---

## Error handling

The Python implementation uses exceptions such as `ValueError`.

The JavaScript implementation uses `Error`.

The C++ case study defines a dedicated `ValidationError` derived from `std::runtime_error`.

Error handling is particularly important when structured data is imported from external sources.

A robust system should distinguish between:

- invalid data,
- missing data,
- duplicate keys,
- unsupported values,
- empty data sets,
- calculation errors.

---

## Lookup operations

A spreadsheet frequently needs to retrieve a value associated with a key.

For example:

`Order ID → Customer`

`Order ID → Net Amount`

`Product ID → Product Name`

This is the conceptual role of lookup functions such as `XLOOKUP`.

The Python implementation first demonstrates a linear search and then creates a dictionary index.

The JavaScript implementation uses `find()` for linear lookup and `Map` for indexed lookup.

The C++ implementation uses `unordered_map<int, size_t>`.

### Linear lookup

A linear lookup can require scanning many rows.

Its approximate time complexity is:

`O(n)`

### Indexed lookup

An appropriate hash-based index provides approximately constant average-time lookup:

`O(1)` average case

The trade-off is additional memory and the cost of maintaining the index.

---

## Dynamic results

Modern spreadsheet systems can return arrays of results from a single formula.

The Python and JavaScript implementations model this idea by producing dynamic collections of unique values.

Examples include:

- unique regions,
- unique products,
- products sold in the North region.

The important concept is that the result is generated from the current data rather than manually maintained as a static list.

---

## Dependency chains

The financial calculation example uses:

`Gross Revenue`

then:

`Discount`

then:

`Net Revenue`

then:

`Cost`

then:

`Profit`

then:

`Margin`

The dependency chain is:

`Gross Revenue → Discount → Net Revenue → Cost → Profit → Margin`

If an upstream value changes, dependent values must be recalculated.

This is a simplified model of spreadsheet calculation engines.

In a sophisticated spreadsheet system, formulas form a dependency graph and the calculation engine determines which dependent cells require recalculation.

---

## Financial calculation considerations

Financial values require careful numerical handling.

The Python implementation uses `Decimal` for currency-related calculations.

This avoids some of the binary floating-point representation issues associated with ordinary floating-point arithmetic.

The JavaScript and C++ implementations use `number` and `double` respectively for simplicity and demonstration.

In production financial software, monetary representation should be chosen deliberately. Depending on the system, integer minor units such as paise or cents, decimal arithmetic, or a dedicated monetary type may be preferable.

For example, storing:

`₹1250.50`

as:

`125050` paise

can avoid many floating-point problems when the business domain permits that representation.

---

## Python implementation

The Python implementation provides the most flexible educational representation of structured table behavior.

### Main components

`SalesRecord`

A dataclass representing one sales record.

`StructuredTable`

A reusable table abstraction containing:

- named columns,
- rows,
- calculated columns,
- filtering,
- sorting,
- aggregation,
- grouping,
- CSV export.

`validate_sales_row()`

Validates input records.

`lookup_by_key()`

Provides a simple linear lookup.

`build_index()`

Builds a dictionary-based index for repeated lookups.

`calculate_financial_columns()`

Demonstrates a dependency chain of calculated values.

### Why Python is useful here

Python dictionaries naturally represent named columns.

Python functions can be passed as calculations and predicates.

Python's standard library also makes it straightforward to demonstrate data transformation, validation, testing, and exporting.

The script therefore emphasizes the conceptual data-processing model behind a spreadsheet table.

---

## JavaScript implementation

The JavaScript implementation emphasizes application-level data processing.

### Main components

`StructuredTable`

Provides:

- row insertion,
- calculated columns,
- filtering,
- sorting,
- aggregation,
- unique values,
- grouping.

`addSalesCalculations()`

Adds calculated columns to the table.

`buildIndex()`

Uses JavaScript `Map` as an indexed lookup structure.

`demonstrateAsyncPipeline()`

Demonstrates how table-like data can enter an application asynchronously.

### Why JavaScript is useful here

JavaScript is particularly relevant when structured table data becomes part of:

- browser applications,
- dashboards,
- web forms,
- APIs,
- client-side calculations,
- asynchronous data pipelines.

The implementation also demonstrates `map()`, `filter()`, `find()`, `sort()`, `Set`, `Map`, Promises, and `async`/`await`.

---

## C++ case study

The C++ implementation models an industry-style sales operations system.

### Problem being solved

A business maintains a collection of sales records and needs to:

- validate incoming records,
- calculate revenue,
- calculate discounts,
- calculate profit,
- calculate margins,
- classify order size,
- filter transactions,
- sort transactions,
- aggregate sales,
- perform repeated lookups,
- handle invalid input,
- measure performance.

### Architecture

The system contains three principal components.

#### `SalesRecord`

Represents one logical row.

It contains raw fields such as:

`orderId`

`customer`

`region`

`product`

`category`

`quantity`

`unitPrice`

`discountRate`

It also stores derived values such as:

`grossAmount`

`discountAmount`

`netAmount`

`cost`

`profit`

`margin`

`orderSize`

#### `SalesCalculationEngine`

Centralizes calculated-column logic.

This prevents business formulas from being duplicated throughout the program.

#### `SalesTable`

Manages the complete collection.

It provides:

- insertion,
- validation,
- recalculation,
- lookup,
- filtering,
- sorting,
- aggregation,
- grouped reporting.

An `unordered_map` provides an index on `orderId`.

---

## C++ data structures

The case study uses:

`vector<SalesRecord>`

for ordered table storage.

`unordered_map<int, size_t>`

for indexed order lookup.

`map<string, double>`

for grouped aggregation.

`optional`

for representing a lookup that may not produce a result.

These structures demonstrate an important distinction between the logical table and the implementation used to store and process it.

---

## C++ algorithms

The C++ case study uses standard-library algorithms and containers.

Filtering uses a predicate.

Sorting uses `std::sort`.

Lookup uses a hash index.

Aggregation uses iteration over records.

This resembles how a larger data-processing system might separate data storage, transformation, and reporting.

---

## C++ validation and failure conditions

The C++ case study explicitly handles:

- duplicate order IDs,
- missing customer names,
- invalid regions,
- zero or negative quantities,
- invalid prices,
- discount rates outside the permitted range,
- missing lookup keys.

The program catches `ValidationError` exceptions at appropriate boundaries.

This is preferable to allowing invalid records to silently enter the calculation pipeline.

---

## Edge cases

Important edge cases demonstrated across the implementations include:

### Empty table

An average cannot be calculated when there are no records.

The Python and C++ implementations explicitly reject this operation.

### Missing values

Missing quantity or price should not automatically become zero.

The implementations return explicit missing-value indicators.

### Zero revenue

A zero revenue value can cause a division-by-zero problem when calculating margins.

The implementations explicitly check the denominator.

### Duplicate keys

An order ID used as a unique identifier must not occur twice.

The Python dictionary index and C++ `unordered_map` index detect duplicates.

### Invalid discount

A discount rate below zero or above one is rejected.

### New records

A new record must receive the same calculated-column treatment as existing records.

---

## Important distinctions

### Excel Table versus ordinary cell range

A Table provides a formal structure and named references.

A range is primarily a collection of cells identified by coordinates.

### Input column versus calculated column

An input column stores supplied information.

A calculated column derives information from other fields.

### Data row versus totals row

A data row represents an individual record.

A totals row represents an aggregate.

### Filtering versus deleting

Filtering changes the visible or processed subset.

Deleting removes records.

### Sorting versus changing values

Sorting changes order.

It does not change the underlying values.

### Missing versus zero

Missing means information is unavailable or absent.

Zero is a legitimate numerical value.

### Linear lookup versus indexed lookup

Linear lookup scans records.

Indexed lookup uses an additional structure to find records efficiently.

---

## Performance considerations

For `n` records:

| Operation | Typical approach | Approximate complexity |
|---|---|---:|
| Add row to vector-backed table | Append | O(1) amortized |
| Linear lookup | Scan | O(n) |
| Hash-indexed lookup | Hash table | O(1) average |
| Filtering | Scan | O(n) |
| Aggregation | Scan | O(n) |
| Sorting | Comparison sort | O(n log n) |
| Building an index | Scan and insert | O(n) average |

The actual performance depends on implementation details, data distribution, memory usage, hashing behavior, spreadsheet calculation strategy, and workload.

For a small spreadsheet, a linear scan may be entirely sufficient.

For repeated lookups over a large data set, an index can significantly reduce repeated work.

---

## Dynamic calculations and recalculation

A spreadsheet formula is not merely a text expression. It participates in a calculation system.

When one input changes, dependent formulas may need to be recalculated.

The financial model demonstrates:

`Gross Revenue`

`Discount`

`Net Revenue`

`Cost`

`Profit`

`Margin`

The correct dependency order is essential.

If `Net Revenue` has not been updated, a subsequent `Profit` calculation may use stale data.

A production calculation engine therefore needs a reliable strategy for dependency tracking and recalculation.

---

## Common mistakes

### Mixing data and presentation

Headers, subtotals, comments, and decorative content should not be randomly inserted into the data region.

### Inconsistent column types

A quantity column should not contain numbers in some rows and textual descriptions in others.

### Hard-coded ranges

A formula based on `A2:A100` can become incorrect when records are added beyond row 100.

Structured references are designed to reduce this problem.

### Manual calculated values

Typing derived values manually creates a risk of inconsistent results.

Calculated columns should generally derive values from their source fields.

### Ignoring validation

Invalid records can propagate incorrect calculations throughout a report.

### Treating blanks as zero

This can hide incomplete information.

### Duplicate keys

A lookup based on a supposed unique identifier becomes ambiguous when duplicates exist.

### Excessive formulas

A workbook containing unnecessary repeated formulas can become difficult to audit and maintain.

### Hidden business rules

A discount or cost assumption should be explicit and documented rather than silently embedded in unrelated formulas.

---

## Limitations

Excel Tables are highly useful for structured spreadsheet data, but they are not a replacement for every database or application architecture.

Large datasets may be better handled by databases or dedicated analytical systems.

Complex relational relationships can become difficult to represent cleanly in a single spreadsheet table.

Multi-user concurrency can introduce challenges.

Large calculation graphs can become expensive to recalculate.

Spreadsheet files can also contain sensitive business information and therefore require appropriate access control.

The Python, JavaScript, and C++ implementations model the conceptual behavior of Excel Tables. They do not implement the Excel file format or the complete Excel calculation engine.

---

## Security considerations

Structured spreadsheet data can contain confidential information such as:

- customer information,
- employee information,
- financial records,
- transaction details,
- internal pricing.

Important security practices include:

- validate imported data,
- restrict access to confidential files,
- avoid unnecessary exposure of personal information,
- do not execute untrusted formulas or expressions,
- validate external data before calculations,
- protect important workbooks,
- maintain version history for important business logic.

When spreadsheet data is moved into an application, external input should be treated as untrusted until validated.

When spreadsheet data is moved into a database, parameterized queries should be used rather than constructing SQL statements through string concatenation.

---

## Implementation considerations

A structured-data system should define its schema explicitly.

For the sales example, the schema includes:

| Column | Purpose |
|---|---|
| Order ID | Unique transaction identifier |
| Customer | Customer name |
| Region | Sales region |
| Product | Product name |
| Category | Product classification |
| Quantity | Number of units |
| Unit Price | Price per unit |
| Discount Rate | Discount represented as a fraction |
| Gross Amount | Quantity multiplied by unit price |
| Discount Amount | Gross amount multiplied by discount rate |
| Net Amount | Gross amount after discount |
| Cost | Modeled cost |
| Profit | Net revenue minus cost |
| Margin | Profit divided by net revenue |
| Order Size | Conditional classification |

The input columns should be distinguishable from derived columns.

---

## Real-world applications

Excel Tables and the concepts modeled in these implementations are applicable to:

### Sales management

- order tracking,
- revenue analysis,
- customer analysis,
- regional performance,
- product performance.

### Inventory management

- SKU tracking,
- stock levels,
- reorder thresholds,
- inventory valuation.

### Finance

- transaction records,
- budgeting,
- expense tracking,
- financial ratios,
- cash-flow analysis.

### Human resources

- employee records,
- compensation analysis,
- department reporting,
- attendance data.

### Project management

- budgets,
- tasks,
- project costs,
- resource allocation,
- milestone tracking.

### Operations

- procurement,
- supplier records,
- service tickets,
- production data,
- quality metrics.

---

## Testing strategy

The implementations include tests for core calculations.

For the first sales record:

`Quantity = 2`

`Unit Price = 75000`

`Discount Rate = 0.05`

Therefore:

`Gross Amount = 150000`

`Discount Amount = 7500`

`Net Amount = 142500`

If the modeled cost is 70% of net revenue:

`Cost = 99750`

`Profit = 42750`

`Margin = 30%`

Testing these known values verifies the dependency chain.

Additional tests cover:

- row counts,
- missing lookup results,
- invalid records,
- empty-table averages,
- duplicate identifiers,
- zero-revenue margins.

---

## Production design principles

A production implementation should treat structured data as a formal data model.

Important principles include:

- define a clear schema,
- validate records at the boundary,
- maintain unique identifiers,
- separate raw data from derived data,
- centralize important business rules,
- test calculations,
- explicitly handle missing values,
- use appropriate numeric representations,
- use efficient lookup structures for repeated queries,
- monitor schema changes,
- protect sensitive information,
- keep calculation logic auditable.

These principles make a spreadsheet-based workflow easier to migrate into software, databases, APIs, and analytical systems.

---

## Relationship between Excel Tables and software systems

An Excel Table provides a useful bridge between spreadsheet work and programming concepts.

The correspondence can be viewed as:

| Excel concept | Python | JavaScript | C++ |
|---|---|---|---|
| Table | `StructuredTable` | `StructuredTable` | `SalesTable` |
| Row | dictionary/dataclass | object | `SalesRecord` |
| Column | dictionary key | object property | struct member |
| Calculated column | function | callback | calculation engine |
| Filter | predicate | `filter()` | predicate |
| Sort | `sorted()` | `sort()` | `std::sort` |
| Lookup | dictionary/index | `Map` | `unordered_map` |
| Aggregate | table methods | reduction methods | class methods |
| Validation | exception/value checks | errors | `ValidationError` |
| Missing value | `None` | `null` | `optional` where appropriate |

The underlying principles remain similar even though the implementation mechanisms differ.

---

## Practical interpretation

The key conceptual shift is from thinking about spreadsheet cells individually to thinking about structured records and relationships.

Instead of asking:

`What is in cell H17?`

a structured-data approach asks:

`What is the Net Amount for this sales record?`

Instead of:

`Sum H2:H100`

the structured approach asks:

`What is the total Net Amount for the sales table?`

This shift makes calculations more understandable because they are expressed in terms of business meaning rather than physical cell coordinates.

---

## Files and execution

The Python implementation is a standalone script and uses only the Python standard library.

The JavaScript implementation is a standalone Node.js program and does not require external npm packages.

The C++ implementation is designed for C++17 or later and uses the C++ standard library.

Typical execution commands are:

`python excel_tables.py`

`node excel_tables.js`

`g++ -std=c++17 -O2 excel_tables.cpp -o excel_tables`

`./excel_tables`

The examples are intentionally self-contained so that the underlying structured-data and dynamic-calculation concepts can be studied without external dependencies.
