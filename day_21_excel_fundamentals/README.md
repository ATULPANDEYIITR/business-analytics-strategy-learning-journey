# Excel Fundamentals: Worksheets, Formulas, References and Formatting

## Topic overview

Excel is a spreadsheet system built around a grid of cells arranged into worksheets. A workbook can contain multiple worksheets, and each worksheet can contain data, calculations, formatting, and presentation structures.

The central concepts covered in this project are:

- Workbooks
- Worksheets
- Rows and columns
- Cells
- Ranges
- Values and labels
- Formulas
- Functions
- Relative references
- Absolute references
- Mixed references
- Formula copying
- Number formats
- Alignment
- Fonts and emphasis
- Conditional formatting
- Validation
- Formula dependencies
- Formula errors
- Circular references
- Calculation performance
- Spreadsheet security
- Practical spreadsheet design

The three implementations approach the subject from different technical perspectives:

- Python implements a relatively broad educational spreadsheet engine.
- JavaScript models spreadsheet behavior with an application-oriented object model and asynchronous execution example.
- C++ develops an industry-style financial sales case study with explicit classes, validation, formula evaluation, dependency analysis, formatting metadata, and error handling.

The implementations are educational models of spreadsheet behavior. They do not attempt to reproduce the complete Excel file format or the complete Excel formula language.

## Fundamental spreadsheet concepts

### Workbook

A workbook is the document-level container for worksheets.

A workbook may contain worksheets such as:

- `Sales`
- `Expenses`
- `Employees`
- `Inventory`
- `Financial Model`
- `Dashboard`
- `Assumptions`

The Python implementation represents a workbook with the `Workbook` class. Its `worksheets` dictionary maps worksheet names to `Worksheet` objects.

The JavaScript implementation uses a `Map` inside the `Workbook` class.

The C++ implementation uses a `std::map<string, Worksheet>`.

This separation is important because a worksheet is not the same thing as the workbook. A workbook can contain several independent or related worksheets.

### Worksheet

A worksheet is the two-dimensional grid in which spreadsheet data is organized.

Columns are identified by letters:

- A
- B
- C
- Z
- AA
- AB

Rows are identified by numbers:

- 1
- 2
- 3
- 100
- 1000

A worksheet therefore creates addresses such as:

- A1
- B2
- C10
- AA25

The implementations include functions that convert between numeric column positions and Excel-style column letters.

For example:

`1 -> A`

`26 -> Z`

`27 -> AA`

`28 -> AB`

This conversion is not ordinary base-10 numbering. Excel-style columns behave similarly to a positional numbering system with letters rather than decimal digits, with the important difference that there is no zero column.

### Cell

A cell is the intersection of a column and a row.

For example:

`B4`

means:

- column B
- row 4

A cell can contain:

- Text
- Numbers
- Boolean values
- Dates
- Errors
- Formulas
- Other spreadsheet-supported data types

A cell can also have formatting independent of the value stored in it.

The implementations model a cell as an object or class containing both its content and formatting metadata.

### Range

A range represents multiple cells.

For example:

`A1:C3`

contains:

- A1
- B1
- C1
- A2
- B2
- C2
- A3
- B3
- C3

The Python, JavaScript, and C++ implementations contain range expansion logic.

Ranges are especially important for functions such as `SUM`, `AVERAGE`, `MIN`, and `MAX`.

## Values, labels, and formulas

Spreadsheet cells can have different semantic roles.

### Label

A label is descriptive text.

Examples:

- `Product`
- `Revenue`
- `Operating Cost`
- `Employee`
- `Total`

Labels make a worksheet understandable to a human reader.

### Numeric value

A numeric cell may contain:

`125`

`3500.50`

`0.15`

The underlying number can subsequently be used in formulas.

### Boolean value

A logical value represents a true or false condition.

Examples include:

`TRUE`

`FALSE`

Boolean results commonly occur when formulas perform comparisons.

### Formula

A formula is an expression that calculates a result.

Excel formulas begin with `=`.

Examples include:

`=A1+B1`

`=B2*C2`

`=SUM(B2:B10)`

`=AVERAGE(C2:C20)`

`=IF(D2>=100,"High","Normal")`

The Python and JavaScript implementations evaluate a useful subset of these expressions. The C++ implementation concentrates on the numerical formula mechanisms needed by its financial case study.

## Formula operators

### Addition

`=A1+B1`

Adds two values.

### Subtraction

`=A1-B1`

Subtracts the second value from the first.

### Multiplication

`=A1*B1`

Multiplies two values.

### Division

`=A1/B1`

Divides one value by another.

Division requires special attention because division by zero is invalid.

### Exponentiation

Excel uses `^` for exponentiation.

Example:

`=2^3`

produces 8.

The Python evaluator translates this operation into Python's exponentiation representation internally.

### Comparisons

Common comparison operators include:

- `=`
- `<>`
- `>`
- `<`
- `>=`
- `<=`

Examples:

`=A1>100`

`=B2<=50`

`=C3<>0`

A comparison produces a logical result that can be used in functions such as `IF`.

## Functions

A function packages a commonly required operation.

### SUM

`=SUM(A1:A10)`

Adds numeric values in a range.

The implementations ignore non-numeric values in their simplified `SUM` behavior.

### AVERAGE

`=AVERAGE(B2:B10)`

Calculates the arithmetic mean.

The basic mathematical operation is:

average = sum of values / number of values

An empty numeric set creates a divide-by-zero type of error condition.

### MIN

`=MIN(C2:C10)`

Returns the smallest numeric value.

### MAX

`=MAX(C2:C10)`

Returns the largest numeric value.

### ROUND

`=ROUND(A1,2)`

Rounds a number to two decimal places.

This is important because formatting a number to two decimal places and actually rounding the stored calculation are different operations.

For example, a value may internally contain more precision while being displayed with two decimal places.

### IF

A typical `IF` structure is:

`=IF(A1>=50,"Pass","Fail")`

The logical condition is evaluated first. One result is returned when it is true and another when it is false.

The Python and JavaScript implementations support text results for this type of example. The C++ case study focuses primarily on numeric calculations.

### COUNT

`=COUNT(A1:A10)`

Counts numeric values.

### COUNTA

`=COUNTA(A1:A10)`

Counts non-empty values.

The exact behavior of spreadsheet functions can contain many detailed rules, so the implementations intentionally provide a clearly defined educational subset rather than claiming full Excel compatibility.

## Cell references

A reference identifies a cell used by a formula.

For example:

`=A1+B1`

references both A1 and B1.

References are fundamental because formulas normally operate on relationships between cells rather than requiring every input to be manually typed into each formula.

## Relative references

A normal reference such as:

`A1`

is relative.

If a formula containing `A1` is copied one row downward, the reference normally becomes:

`A2`

If it is copied one column to the right, it becomes:

`B1`

This behavior makes it practical to create a formula once and copy it through a table.

The Python, JavaScript, and C++ implementations include formula-copying demonstrations.

For example:

`=B2*C2`

copied down one row becomes:

`=B3*C3`

The relationship between the cells is preserved.

## Absolute references

An absolute reference uses `$` to prevent movement.

For example:

`$A$1`

fixes both the column and row.

When copied, `$A$1` remains `$A$1`.

This is useful for fixed assumptions such as:

- Tax rate
- Exchange rate
- Discount rate
- Target value
- Commission percentage

For example, if a tax rate is stored in H1, a formula might use:

`=D2*$H$1`

When the formula is copied downward, the sales value changes from D2 to D3, D4, and so on, while `$H$1` remains fixed.

## Mixed references

A mixed reference fixes only one dimension.

### Fixed row

`A$1`

The row remains fixed while the column can change.

### Fixed column

`$A1`

The column remains fixed while the row can change.

Mixed references are particularly useful when formulas are copied across two-dimensional tables.

The Python reference model explicitly stores:

- `column_absolute`
- `row_absolute`

The JavaScript and C++ implementations model the same distinction.

## Formula copying

Formula copying is one of the most useful spreadsheet mechanisms.

Suppose:

`D2 = B2*C2`

The formula can be copied down so that:

`D3 = B3*C3`

`D4 = B4*C4`

`D5 = B5*C5`

This avoids manually rewriting each formula.

The implementations provide `copyFormula` functions that shift relative references while leaving absolute references unchanged.

The essential rule is:

- Relative reference: moves.
- Absolute reference: does not move.
- Mixed reference: only its relative dimension moves.

## Formatting

Formatting controls how spreadsheet information is presented.

Formatting can include:

- Number format
- Font
- Font size
- Bold
- Italic
- Alignment
- Fill
- Border
- Text wrapping
- Font color

Formatting is presentation metadata. It does not automatically change the underlying numerical value.

### Number formatting

A value such as:

`1250`

can be displayed as:

`$1,250.00`

when an appropriate currency format is applied.

The underlying value remains numerical.

Similarly:

`0.125`

can be displayed as:

`12.50%`

with a percentage format.

### Currency

The implementations use a simplified currency format:

`$#,##0.00`

This demonstrates the distinction between the stored numeric value and its presentation.

### Percentage

A stored value such as:

`0.15`

can represent 15 percent when the appropriate percentage format is applied.

The formatting layer multiplies the displayed representation by 100 and appends `%`.

### Alignment

Common alignment choices include:

- General
- Left
- Center
- Right

Text is often presented differently from numeric values, while headings frequently use centered or emphasized formatting.

### Bold and emphasis

Headers can use bold formatting to distinguish them from data.

The examples apply bold formatting to header cells.

### Borders

Borders can visually separate headings, totals, and sections.

The implementations model borders as formatting metadata rather than attempting to render a full graphical spreadsheet.

## Conditional formatting

Conditional formatting applies presentation rules based on cell values.

For example:

- Values below 500 may be highlighted.
- Values above a target may receive a particular format.
- Negative values may be emphasized.
- High percentages may be visually distinguished.

The Python, JavaScript, and C++ implementations model a rule containing:

- An operator
- A threshold
- A display format

For example:

`< 500`

means that a numeric value is considered to satisfy the rule when it is less than 500.

Conditional formatting should communicate information rather than conceal errors.

## Python implementation

The Python program is the broadest educational implementation.

### Workbook and worksheet model

The `Workbook` class stores worksheets by name.

The `Worksheet` class stores cells and formatting rules.

A worksheet can receive:

- Literal values through `set_value`
- Formulas through `set_formula`
- Formatting through `format_cell`
- Conditional rules through `add_conditional_rule`

### Cell model

The Python `Cell` class stores:

- `value`
- `formula`
- `format`

This provides a simple separation between content and presentation.

### Reference model

The `CellReference` class represents:

- Column number
- Row number
- Absolute column state
- Absolute row state

Its `shifted` method demonstrates how copying formulas affects relative and absolute coordinates.

### Formula evaluator

The `SpreadsheetEvaluator` class implements a restricted formula language.

It supports:

- Arithmetic
- Comparisons
- Cell references
- Ranges
- `SUM`
- `AVERAGE`
- `MIN`
- `MAX`
- `ROUND`
- `IF`
- `COUNT`
- `COUNTA`

The evaluator first translates supported spreadsheet syntax into a controlled expression representation.

It then uses Python's `ast` module rather than unrestricted `eval`.

This is an important security design choice. An arbitrary expression evaluator could execute operations unrelated to spreadsheet calculation.

The implementation explicitly permits only selected AST node types and operations.

### Dependency evaluation

When a formula references another formula cell, the evaluator recursively calculates the dependency.

For example:

`D2 = B2*C2`

and:

`E2 = D2*10`

requires D2 to be evaluated before E2 can be evaluated.

The evaluator maintains an `evaluation_stack`.

If a reference appears again while it is already being evaluated, the implementation identifies a circular dependency.

### Circular references

A circular reference occurs when formulas depend on one another in a cycle.

For example:

`A1 = B1+1`

and:

`B1 = A1+1`

creates:

`A1 -> B1 -> A1`

The Python implementation raises `CircularReferenceError`.

Real spreadsheet systems can support intentional iterative calculation in some circumstances, but circular calculations require explicit configuration and careful modeling.

### Formula auditing

The Python program includes a lightweight formula auditor.

It checks for conditions such as:

- Missing `=`
- Unbalanced parentheses
- Formulas ending unexpectedly with an operator

A full spreadsheet auditing system would require a much more complete formula grammar.

### Financial model

The Python implementation constructs a financial worksheet containing:

- Quarter
- Revenue
- Operating Cost
- Operating Profit
- Margin

For each quarter:

`Operating Profit = Revenue - Operating Cost`

and:

`Margin = Operating Profit / Revenue`

The worksheet also calculates totals and overall margin.

This demonstrates how simple formulas can be combined to create a business model.

## JavaScript implementation

The JavaScript implementation uses an object-oriented structure similar to a small application-level spreadsheet system.

### Workbook and worksheet classes

The JavaScript `Workbook` class uses a `Map` to store worksheets.

The `Worksheet` class uses another `Map` to store cells.

This is appropriate for a sparse spreadsheet representation because empty cells do not need to be stored.

### Cell formatting

The `CellFormat` class models:

- Number format
- Bold
- Italic
- Alignment
- Fill
- Font
- Border
- Text wrapping

The implementation uses JavaScript object properties to represent formatting state.

### Formula evaluator

The `FormulaEvaluator` class parses a restricted set of formula expressions.

It supports:

- Arithmetic
- Comparisons
- Cell references
- Ranges
- Spreadsheet functions
- Recursive calculation
- Circular reference detection

The evaluator deliberately avoids JavaScript's unrestricted `eval()`.

This distinction is important when formula content might originate from an external workbook or user input.

### Asynchronous behavior

JavaScript is particularly useful for demonstrating application-level asynchronous behavior.

The `calculateAsync` function returns a Promise.

The `asynchronousExample` function uses:

`Promise.all`

to process multiple calculations concurrently from the application's perspective.

This does not make arithmetic itself inherently parallel. It demonstrates the programming model used when spreadsheet data or calculations interact with asynchronous sources such as:

- APIs
- Network services
- Browser storage
- Remote data
- User interfaces

### Browser and application relevance

JavaScript is closely associated with web applications, so the same spreadsheet concepts can be incorporated into:

- Browser-based calculators
- Financial dashboards
- Interactive reporting systems
- Web spreadsheet interfaces
- Data-entry applications
- Client-side validation
- Dynamic tables

The implementation remains a command-line JavaScript program so that it does not depend on a browser or external package.

## C++ case study

The C++ implementation models an industry-style sales workbook.

The scenario contains products, units, unit prices, revenue, targets, and a fixed target assumption.

### Problem being modeled

The system calculates sales revenue for several products.

For each product:

`Revenue = Units × Unit Price`

It then calculates:

- Total revenue
- Average revenue
- Maximum revenue
- Minimum revenue
- Revenue relative to a fixed target

The resulting worksheet behaves like a simplified business reporting workbook.

### Major components

The architecture consists of:

- `Workbook`
- `Worksheet`
- `Cell`
- `CellReference`
- `CellFormat`
- `ConditionalFormatRule`
- `FormulaEvaluator`

This separation mirrors the logical responsibilities found in larger software systems.

### Workbook

The `Workbook` owns worksheets.

This gives the system a document-level container.

### Worksheet

The `Worksheet` owns cells and conditional formatting rules.

It provides operations to:

- Set values
- Set formulas
- Retrieve cells
- Format cells
- Add conditional rules
- Print the worksheet

### Cell

The `Cell` class supports several content types:

- Numeric value
- Text
- Boolean
- Formula

It also stores `CellFormat`.

This demonstrates an important design principle: the cell's content and presentation can be represented as separate properties.

### Cell references

`CellReference` stores:

- Column
- Row
- Absolute-column state
- Absolute-row state

Its `shifted` method implements spreadsheet-style formula copying.

### Formula evaluator

The C++ evaluator supports a deliberately restricted formula language.

It includes:

- Arithmetic
- Comparisons
- Cell references
- Ranges
- `SUM`
- `AVERAGE`
- `MIN`
- `MAX`
- `ROUND`
- `IF`

The evaluator recursively resolves referenced cells.

### Dependency chains

Suppose:

`D2 = B2*C2`

and:

`D7 = SUM(D2:D6)`

The total depends on all product revenue calculations.

The dependency relationship can be represented as:

`D7 -> D2, D3, D4, D5, D6`

A production spreadsheet application can use such dependency information to determine which formulas must be recalculated after an input changes.

### Circular-reference detection

The C++ evaluator maintains an evaluation stack.

If a cell being evaluated is encountered again, the system throws `CircularReferenceError`.

This prevents uncontrolled recursion.

### Validation

The C++ case study validates numeric inputs with `validatePositive`.

This prevents invalid negative units or prices from entering the model.

Real systems require more extensive validation, including:

- Range validation
- Required fields
- Data types
- Date constraints
- Business rules
- Duplicate detection
- Imported-data validation

## Important distinctions

### Value versus displayed value

A cell can contain:

`1250.456`

while displaying:

`$1,250.46`

The display does not necessarily mean the stored value has become exactly 1250.46.

If a business rule requires the calculation to be rounded, an explicit formula such as:

`=ROUND(A1,2)`

is different from merely applying a two-decimal display format.

### Formula versus value

A formula is an instruction for calculating a result.

A value is the result or literal data stored in the cell.

A spreadsheet application generally maintains both the formula and its calculated result.

### Relative versus absolute reference

| Reference | Column | Row | Copy behavior |
|---|---|---|---|
| `A1` | Relative | Relative | Both can move |
| `$A$1` | Absolute | Absolute | Neither moves |
| `A$1` | Relative | Absolute | Column can move |
| `$A1` | Absolute | Relative | Row can move |

Understanding this distinction is essential when constructing formulas that will be copied across a worksheet.

### Formatting versus calculation

Formatting communicates information visually.

Calculation changes the logical result.

Changing a number format from `General` to currency does not constitute a financial calculation.

Similarly, coloring a negative number red does not change its numerical value.

## Edge cases and exceptions

### Division by zero

A formula such as:

`=A1/B1`

is invalid when B1 is zero.

The implementations raise or represent a `#DIV/0!`-style error.

### Empty ranges

Functions such as `AVERAGE` require appropriate numeric inputs.

An empty numeric set cannot produce a meaningful arithmetic mean.

### Invalid references

Examples include malformed addresses such as:

`A`

`1A`

`A0`

`$`

The reference parsers reject invalid formats.

### Invalid ranges

A range must have valid endpoints.

Examples of valid ranges include:

`A1:B5`

`C2:F20`

### Circular references

A cycle such as:

`A1 -> B1 -> A1`

requires special treatment.

The implementations detect cycles instead of allowing infinite recursion.

### Numeric precision

Binary floating-point arithmetic can produce small representation differences.

For example, in many programming languages:

`0.1 + 0.2`

does not represent the decimal value 0.3 with perfect binary floating-point representation.

The Python implementation demonstrates `Decimal` for decimal arithmetic.

Financial spreadsheet models should establish clear rules for:

- Precision
- Rounding
- Currency conversion
- Display precision
- Calculation precision

### Text that looks like a number

A cell containing text such as:

`"100"`

is not necessarily equivalent to a numeric cell containing:

`100`

The distinction matters for:

- Arithmetic
- Sorting
- Filtering
- Aggregation
- Validation

Data imported from external systems should be checked carefully.

## Common mistakes

### Hard-coded assumptions

A formula such as:

`=A1*0.18`

may be difficult to maintain if 0.18 represents a tax rate that can change.

A more maintainable design places the assumption in a dedicated cell and references it.

For example:

`=A1*$H$1`

This makes the assumption visible and reusable.

### Forgetting absolute references

Suppose H1 contains a fixed rate.

Using:

`=D2*H1`

and copying the formula downward can change the reference to H2, H3, and so forth.

Using:

`=D2*$H$1`

keeps the assumption fixed.

### Confusing display with rounding

Applying a two-decimal number format does not necessarily alter the underlying value.

If the calculation itself needs to be rounded, use a rounding formula.

### Incorrect data types

Numeric data stored as text can cause formulas or functions to behave differently from expectations.

Imported data should be validated before it is used in calculations.

### Excessive formatting

Formatting every cell differently can make a workbook harder to maintain and can increase workbook complexity.

Formatting should communicate structure and meaning.

### Hidden information

Hiding a row, column, or worksheet is not a reliable security mechanism.

Hidden content can often be revealed.

Sensitive information should not be stored in a workbook merely because a worksheet is hidden.

## Best practices

### Separate inputs from calculations

A structured model often contains:

- Inputs
- Assumptions
- Calculations
- Outputs

This makes the workbook easier to understand and audit.

### Use clear labels

Labels such as `Revenue`, `Operating Cost`, and `Operating Profit` are easier to interpret than unexplained abbreviations.

### Use consistent formatting

A consistent visual convention can distinguish:

- Headers
- Inputs
- Calculations
- Totals
- Percentages
- Currency
- Warnings

### Keep formulas auditable

A formula should be understandable enough that another person can trace its inputs.

### Use fixed references for fixed assumptions

Absolute references are particularly useful for shared assumptions.

### Validate data

Imported or user-entered data should be checked for:

- Type
- Range
- Missing values
- Invalid values
- Business constraints

### Avoid unnecessary hard coding

Repeated business assumptions should normally be stored in identifiable cells rather than embedded throughout many formulas.

### Treat formatting as communication

Formatting should help a reader understand the model rather than disguise errors.

## Formula dependencies and recalculation

A spreadsheet is effectively a dependency system.

Consider:

`B2 = 100`

`C2 = 20`

`D2 = B2*C2`

`E2 = D2*0.10`

The dependency chain is:

`B2 -> D2`

`C2 -> D2`

`D2 -> E2`

If B2 changes, D2 must be recalculated. Because E2 depends on D2, E2 must also be recalculated.

A sophisticated spreadsheet engine maintains a dependency graph and uses it to determine what must be recalculated.

The project implementations include simple dependency extraction to demonstrate this concept.

## Performance considerations

Spreadsheet performance depends on both the number of cells and the complexity of the dependency graph.

### Number of formulas

A large workbook containing many formulas requires more calculation work.

### Large ranges

A formula operating over a very large range may need to inspect many cells.

### Long dependency chains

A long sequence of dependent formulas can increase recalculation work.

### Repeated calculations

If the same expensive calculation is repeated many times, a better model may calculate it once and reference the result.

### Volatile calculations

Some spreadsheet functions recalculate frequently. Excessive use can increase calculation cost.

### Formatting complexity

A workbook with many distinct formatting combinations can become more complex than one using a small, consistent formatting system.

### External data

External workbook references, network data, and other external sources can introduce:

- Latency
- Availability problems
- Authentication requirements
- Version inconsistencies

## Data structures and performance in the C++ implementation

The C++ case study uses `std::map` for sparse worksheet storage.

A map provides approximately:

`O(log n)`

lookup complexity.

For a large sparse spreadsheet, a hash-based structure such as `std::unordered_map` could provide average constant-time lookup, although memory behavior and ordering characteristics differ.

Range expansion for an r-by-c rectangular region requires:

`O(r × c)`

cell visits.

A production spreadsheet engine may use additional structures for dependency tracking and recalculation scheduling.

## Security considerations

Spreadsheets can contain sensitive business information and executable functionality.

### Macros and executable content

A workbook containing macros or other executable content should not automatically be trusted.

### External links

External links can retrieve data or connect a workbook to external resources.

### Secrets

Passwords, API keys, access tokens, and other credentials should not be stored in ordinary spreadsheet cells.

### Hidden worksheets

Hidden worksheets are not a substitute for access control.

### Formula evaluation

A custom spreadsheet engine must not execute arbitrary programming-language expressions as formulas.

The Python implementation uses a restricted AST evaluator rather than unrestricted `eval`.

The JavaScript implementation similarly avoids `eval`.

The C++ implementation parses only a limited set of explicitly supported operations.

### Imported data

Data imported from external sources should be treated as untrusted until validated.

## Implementation considerations

A complete spreadsheet system would require significantly more functionality than the educational implementations provide.

Important production features would include:

- Dates and times
- Rich error values
- Text functions
- Lookup functions
- Logical functions
- Statistical functions
- Financial functions
- Named ranges
- Cross-sheet references
- Cross-workbook references
- Array formulas
- Dynamic arrays
- Structured table references
- Data validation
- Charts
- Pivot tables
- Conditional formatting with many rule types
- Workbook persistence
- Excel file-format compatibility
- Formula dependency graphs
- Efficient recalculation
- Undo and redo
- Cell comments
- Protection
- Permissions
- Import and export
- Localization
- Formula compatibility rules

The project intentionally focuses on the fundamentals needed to understand how spreadsheet concepts fit together.

## Practical applications

The concepts demonstrated here apply to many common spreadsheet tasks.

### Sales analysis

A sales table can calculate:

`Revenue = Units × Price`

and then aggregate revenue by product, region, or period.

### Budgeting

A budget can contain:

- Planned revenue
- Planned expenses
- Actual revenue
- Actual expenses
- Variance

### Payroll

A payroll worksheet can calculate:

`Gross Pay = Hours × Rate`

and:

`Net Pay = Gross Pay - Deductions`

### Financial modeling

A financial model can contain:

- Revenue
- Operating expenses
- Operating profit
- Margins
- Growth assumptions
- Discount rates
- Cash flows

### Inventory

Inventory calculations can track:

`Ending Inventory = Beginning Inventory + Purchases - Sales`

### Project management

A spreadsheet can track:

- Tasks
- Owners
- Dates
- Estimated hours
- Actual hours
- Costs
- Completion status

## Comparison of the three implementations

| Area | Python | JavaScript | C++ |
|---|---|---|---|
| Workbook model | Yes | Yes | Yes |
| Worksheet model | Yes | Yes | Yes |
| Cell references | Detailed | Detailed | Detailed |
| Relative references | Yes | Yes | Yes |
| Absolute references | Yes | Yes | Yes |
| Mixed references | Yes | Yes | Yes |
| Formula evaluation | Broad educational subset | Application-oriented subset | Restricted case-study subset |
| Formatting | Detailed metadata | Object-based metadata | Explicit structures |
| Conditional formatting | Yes | Yes | Yes |
| Dependency analysis | Yes | Yes | Yes |
| Circular reference detection | Yes | Yes | Yes |
| Validation | Yes | Yes | Yes |
| Testing | Yes | Yes | Yes |
| Asynchronous example | No | Yes | No |
| Financial case study | Yes | Yes | Yes |
| Low-level memory control | Limited | Runtime-managed | Stronger control |

The languages demonstrate different aspects of spreadsheet engineering.

Python makes it convenient to construct an educational calculation engine and work with dynamic data structures.

JavaScript is well suited to interactive application environments, particularly browser and web applications. Its Promise-based model also demonstrates how spreadsheet interfaces can interact with asynchronous data sources.

C++ exposes more explicit control over types, object lifetime, data structures, and performance characteristics, making it useful for modeling a more systems-oriented spreadsheet engine.

## Python implementation structure

The major Python components are:

- `column_number_to_letter`
- `column_letter_to_number`
- `CellReference`
- `CellFormat`
- `ConditionalFormatRule`
- `Cell`
- `Worksheet`
- `Workbook`
- Spreadsheet functions
- `expand_range`
- `SpreadsheetEvaluator`
- `copy_formula`
- Dependency extraction
- Formula auditing
- CSV-style export
- Financial examples
- Tests

The Python implementation is particularly focused on explaining how the underlying mechanisms can be represented programmatically.

## JavaScript implementation structure

The major JavaScript components are:

- Column conversion functions
- Reference parsing
- Range expansion
- `CellFormat`
- `ConditionalFormatRule`
- `Cell`
- `Worksheet`
- `Workbook`
- Spreadsheet functions
- `FormulaEvaluator`
- Formula copying
- Dependency extraction
- Validation
- Sales workbook
- Conditional formatting
- Error handling
- Circular-reference detection
- Asynchronous processing
- Tests

The JavaScript implementation demonstrates how these mechanisms can be represented in an application-oriented environment.

## C++ implementation structure

The major C++ components are:

- Column conversion
- `CellReference`
- Range expansion
- `FormulaError`
- `CircularReferenceError`
- `CellFormat`
- `ConditionalFormatRule`
- `Cell`
- `Worksheet`
- `Workbook`
- `FormulaEvaluator`
- Formula copying
- Dependency graph
- Validation
- Sales-model population
- Formula evaluation
- Formatting
- Conditional formatting
- Error tests
- Circular-reference tests
- Performance notes

The C++ program is organized as a progressively developed technical case study rather than as a collection of isolated syntax examples.

## Case-study calculation flow

The central C++ sales model follows this structure:

`Product data`

↓

`Units and unit price`

↓

`Revenue formulas`

↓

`Aggregate calculations`

↓

`Target comparison`

↓

`Formatting and conditional rules`

↓

`Business report`

For an individual product:

`Revenue = Units × Unit Price`

For the entire product set:

`Total Revenue = SUM(Product Revenues)`

The model also calculates:

`Average Revenue`

`Maximum Revenue`

`Minimum Revenue`

A fixed target is represented separately so that the revenue formulas can use an absolute reference.

## Formula auditing

Formula auditing is important because spreadsheet errors are not always syntax errors.

A formula may be perfectly valid syntactically while referring to the wrong cells.

Examples include:

- Referencing the previous row instead of the current row
- Using a relative reference where an absolute reference was required
- Including an incorrect range
- Omitting an input
- Using an incorrect assumption

Dependency graphs help identify relationships between calculations, while human review remains important for determining whether the relationships represent the intended business logic.

## Formatting and model readability

A spreadsheet is both a computational system and a human-readable document.

Good formatting should make distinctions visible.

For example:

- Headers can be bold.
- Currency values can use currency formatting.
- Percentages can use percentage formatting.
- Totals can use borders or emphasis.
- Warnings can use conditional formatting.

Formatting should not be used to conceal errors or create a false impression of accuracy.

## Testing

The three programs contain deterministic tests for important mechanisms.

The tests cover concepts such as:

- Column conversion
- Cell-reference parsing
- Range expansion
- Relative reference movement
- Absolute reference preservation
- Formula evaluation
- `SUM`
- `IF`
- Formula copying

Testing is particularly important for spreadsheet calculations because small reference mistakes can propagate into many outputs.

A spreadsheet implementation should test both ordinary cases and boundary conditions.

## Relationship between formulas and formatting

Formula calculation and formatting are separate layers.

For example:

`D2 = B2*C2`

calculates revenue.

Applying currency formatting to D2 changes its presentation.

Applying conditional formatting to D2 can add a visual rule based on the result.

These operations have different responsibilities:

- Formula: calculation
- Number format: representation
- Conditional formatting: value-dependent presentation

Keeping these responsibilities separate makes spreadsheet systems easier to reason about and maintain.

## Limitations of the educational implementations

The programs deliberately implement a subset of spreadsheet functionality.

They do not reproduce the full Excel formula grammar.

They also do not implement the Excel workbook file format.

They do not provide complete support for:

- Dates
- Rich text
- Cross-sheet references
- External workbook references
- Charts
- Pivot tables
- Macros
- Dynamic arrays
- Structured table references
- Full error semantics
- Full locale-specific behavior
- Full Excel-compatible calculation rules

The purpose is to expose the underlying concepts rather than reproduce the complete Excel application.

## Real-world relevance

Worksheets, formulas, references, and formatting are foundational concepts for spreadsheet-based analysis.

The same principles appear when designing larger data systems:

- Cells resemble individual data fields.
- Ranges resemble collections of related records.
- Formulas resemble transformations.
- Dependencies resemble data-processing graphs.
- Formatting resembles presentation logic.
- Validation resembles data-quality rules.
- Conditional formatting resembles rule-driven presentation.
- Recalculation resembles dependency-aware computation.

Understanding these fundamentals is therefore useful beyond manual spreadsheet usage. They provide a foundation for understanding financial models, reporting systems, business analytics, data-processing applications, and spreadsheet automation.
