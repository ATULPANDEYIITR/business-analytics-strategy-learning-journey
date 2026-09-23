# Data Cleaning in Excel

## Introduction

Data cleaning is the process of identifying, correcting, standardizing, validating, and documenting problems in a dataset before the data is used for analysis, reporting, decision-making, automation, or downstream systems.

Excel is frequently used for data cleaning because it combines tabular storage, formulas, filtering, sorting, conditional formatting, data validation, lookup functions, PivotTables, Power Query, and interactive inspection in one environment.

A dataset can be technically stored in a spreadsheet and still contain serious quality problems. Examples include:

- Extra spaces around values
- Inconsistent capitalization
- Different spellings for the same category
- Multiple representations of the same state
- Numbers stored as text
- Currency symbols mixed with numeric values
- Dates stored in different formats
- Impossible dates
- Invalid email addresses
- Incorrect phone-number formats
- Missing values
- Duplicate records
- Invalid ages
- Negative values where negative values are not permitted
- Inconsistent relationships between columns
- Statistical outliers
- Hidden or non-printing characters

The three implementations in this project demonstrate the same general data-quality principles from different technical perspectives.

The Python program focuses on detailed transformation, validation, profiling, testing, audit trails, data-quality metrics, and CSV handling.

The JavaScript program emphasizes array processing, functional transformations, JSON-oriented data, application-side processing, asynchronous execution, and CSV generation.

The C++ program develops an industry-style customer transaction data-quality engine with explicit domain structures, validation functions, controlled vocabularies, duplicate detection, audit records, aggregation, CSV output, and complexity considerations.

---

## The data-cleaning lifecycle

A reliable cleaning workflow normally follows a sequence similar to:

1. Preserve the raw data.
2. Inspect the structure.
3. Profile the data.
4. Identify quality problems.
5. Define cleaning rules.
6. Standardize representations.
7. Validate individual fields.
8. Validate relationships between fields.
9. Detect duplicates.
10. Investigate anomalies.
11. Generate an audit trail.
12. Recalculate quality metrics.
13. Export the cleaned dataset.
14. Document the rules and assumptions.

The sequence matters because cleaning should not be treated as arbitrary editing.

For example, replacing every occurrence of `UP` with `Uttar Pradesh` may appear harmless, but a replacement rule becomes dangerous if the same text has a different meaning in another column. Data transformations should therefore be based on the meaning of each field.

---

## Raw data versus cleaned data

The raw dataset is the original source received from a user, system, export, database, API, or spreadsheet.

The cleaned dataset is the result after defined transformations and validation.

The original data should normally be preserved.

A safer architecture is:

`Raw data -> Cleaning rules -> Cleaned data -> Validation -> Output`

rather than:

`Raw data -> overwrite raw data`

Preserving the original provides traceability and makes it possible to compare the original values with the transformed values.

The Python and C++ implementations demonstrate this separation explicitly.

---

## Data quality dimensions

Data quality is not one single property. Several dimensions are useful.

### Completeness

Completeness concerns whether required information is present.

For example, if every customer record requires a customer ID, name, city, and phone number, blank values reduce completeness.

The Python implementation calculates completeness as the proportion of populated required cells.

The JavaScript implementation provides the same type of calculation through `completenessScore()`.

### Validity

Validity concerns whether a value follows the rules defined for that field.

Examples:

- Age must be an integer between 0 and 120.
- Customer ID must follow the pattern `C001`.
- Amount must not be negative.
- Category must belong to a controlled vocabulary.
- A date must represent a real calendar date.

A value can be present and still be invalid.

For example, `150` is not missing, but it is invalid under the age rule used in the implementations.

### Consistency

Consistency concerns whether related values agree with each other.

For example:

- Lucknow should be associated with Uttar Pradesh.
- Kanpur should be associated with Uttar Pradesh.
- A transaction amount should not be negative if the business rule defines sales as non-negative.
- A state code should correspond to the selected state.

Cross-field validation is therefore different from validating each field independently.

### Uniqueness

Uniqueness concerns whether a field that is supposed to identify a record contains duplicates.

The example data contains `C005` twice.

A duplicate is not automatically an error. The meaning depends on the business context.

For a customer master table, two records with the same customer ID may indicate duplication.

For a transaction table, the same customer ID can legitimately appear thousands of times because one customer can place many orders.

The definition of a duplicate must therefore come from the structure and business meaning of the dataset.

### Accuracy

Accuracy concerns whether a value correctly represents the real-world entity it claims to represent.

Syntax validation cannot establish complete accuracy.

For example:

`person@example.com`

may have valid email syntax while the mailbox does not exist.

Similarly, a ten-digit phone number may have a correct format without proving that the number belongs to the intended customer.

---

## Missing values

A missing value can appear in many forms:

- Empty cell
- Empty string
- Spaces
- `NULL`
- `N/A`
- `Unknown`
- `Not available`
- Placeholder values such as `-999`
- Invalid values that effectively represent missing information

The first step is to define which representations count as missing.

The Python function `is_missing()` treats `None`, empty strings, and whitespace-only strings as missing.

The JavaScript function `isMissing()` handles `null`, `undefined`, and blank strings.

Excel users should distinguish between a genuinely empty cell and text such as `N/A`. The latter is still a value from Excel's perspective and may need explicit treatment.

---

## Handling missing values

There is no universal rule for missing values.

Possible approaches include:

- Leave the value blank
- Remove the record
- Replace it with a documented default
- Use a category such as `Unknown`
- Impute a value
- Obtain the missing value from the source system
- Flag the record for manual review

The correct approach depends on the field and its purpose.

For example, replacing a missing customer email with `unknown@example.com` creates a value that looks like a real email address and can create downstream errors.

A missing email should usually remain missing unless a reliable source can provide it.

---

## Whitespace cleaning

Whitespace problems are common in spreadsheets.

Examples:

`" Rahul Sharma "`

`"Rahul    Sharma"`

`"  Delhi"`

These values can appear visually similar while behaving differently in comparisons.

Excel functions commonly used for text cleanup include `TRIM()` and `CLEAN()`.

The Python implementation provides `clean_whitespace()`.

The JavaScript implementation provides `cleanWhitespace()`.

The C++ implementation uses `trim()` and `collapseWhitespace()`.

Whitespace normalization is especially important before:

- Duplicate detection
- Lookup operations
- Comparisons
- Grouping
- Validation
- Joining datasets

---

## Case standardization

The same value may appear in several cases:

- `ELECTRONICS`
- `Electronics`
- `electronics`
- ` Electronics `

If the values represent the same category, a controlled standard should be selected.

Excel functions include:

- `UPPER()`
- `LOWER()`
- `PROPER()`

The implementations use lower-case comparison keys and controlled output values.

For example:

`electronics`

becomes:

`Electronics`

Case normalization should be applied according to the semantic requirements of the field. Email addresses are normally normalized to lowercase in the examples, while names and cities use title-style formatting.

---

## Controlled vocabularies

A controlled vocabulary is a predefined set of accepted values.

The example category vocabulary is:

- Electronics
- Home Appliances
- Furniture

The raw dataset contains variations such as:

- `electronics`
- `electronic`
- `home appliance`
- `Home Appliances`

A mapping table converts these representations into standardized values.

In Excel, this can be implemented using:

- XLOOKUP
- VLOOKUP
- lookup tables
- Power Query merges
- Data Validation lists

A mapping table is generally safer than a sequence of uncontrolled Find & Replace operations because the replacement rule can be explicitly documented.

---

## State standardization

The example dataset contains:

- `UP`
- `U.P.`
- `Uttar Pradesh`
- `DL`
- `Delhi`

The cleaning rules standardize these to:

- `Uttar Pradesh`
- `Delhi`

This demonstrates an important distinction between source representation and canonical representation.

A source may use short codes for operational purposes while a reporting dataset may require full names.

A standardized dataset should not necessarily discard the original code. In production systems, both the original source value and standardized value can be retained when traceability is important.

---

## Phone-number cleaning

Phone numbers frequently contain formatting differences:

- `9876543210`
- `98765 43210`
- `98765-43210`
- `+91-9876543210`
- `09876543210`

The implementations remove formatting characters and normalize common Indian `+91` and leading-zero representations.

The result is a ten-digit number when the input satisfies the expected format.

This does not prove that the number exists.

It only establishes that the value conforms to the formatting rule implemented by the program.

A production system may require:

- Country code handling
- Country-specific rules
- Number portability considerations
- Verification through a trusted system
- Preservation of the original phone value

---

## Email validation

The example validation checks whether an email resembles a standard address structure.

For example:

`person@example.com`

passes the basic syntax rule.

The following does not:

`person@example`

Syntax validation should not be confused with verification.

A syntactically valid email address may still:

- Not exist
- Be inactive
- Belong to another person
- Reject messages

The implementations intentionally perform a practical syntax check rather than attempting to implement the complete email specification.

---

## Numeric cleaning

Spreadsheet data often contains numbers represented as text.

Examples include:

- `12,500`
- `₹ 12,500`
- `8,750.50`
- `15000`

Before numerical analysis, the formatting characters need to be removed and the value converted to a numeric representation.

The Python implementation uses `Decimal` for monetary values.

This is useful because binary floating-point arithmetic can introduce representation issues.

The JavaScript and C++ demonstrations use ordinary numeric types for simplicity. Production financial applications may use decimal arithmetic libraries or store monetary values as integer minor units such as paise or cents.

---

## Invalid numeric data

The example includes:

`1O,500`

The final character is the letter `O`, not the number `0`.

A dangerous cleaning rule might automatically replace every `O` with `0`.

That could silently corrupt legitimate text.

The implementations therefore reject the value instead of guessing.

This demonstrates an important cleaning principle:

> When the intended correction cannot be established reliably, flag the value instead of inventing a correction.

---

## Date standardization

Dates may appear as:

- `15/09/2026`
- `16-09-2026`
- `2026-09-16`

These can represent the same logical type while having different textual formats.

The implementations convert accepted dates into ISO-style representation:

`YYYY-MM-DD`

For example:

`15/09/2026`

becomes:

`2026-09-15`

---

## Invalid dates

The dataset contains:

`31/09/2026`

September has only 30 days.

A date parser should therefore reject it.

The Python implementation returns `None`.

The JavaScript implementation checks the components after constructing a UTC date because JavaScript's `Date` object can normalize invalid dates automatically.

The C++ implementation explicitly checks the number of days in the month.

This is a useful example of why data validation cannot always be reduced to formatting.

A value can look like a date while still representing an impossible calendar date.

---

## Numbers versus text

Excel can display a value such as `10000` while the underlying cell is text.

This can cause problems with:

- Sorting
- Arithmetic
- PivotTables
- Conditional formatting
- Lookups
- Charts
- Comparisons

A cleaning process should therefore distinguish between:

`"10000"`

and:

`10000`

The first is text.

The second is numeric.

The Python program includes type inference and explicit conversion functions.

---

## Duplicate detection

Duplicate detection has at least two different meanings.

### Exact duplicate

Every relevant field has the same value.

### Key duplicate

Two or more records share a field or combination of fields that is expected to identify one entity.

For example:

`Customer ID = C005`

appears twice.

That is a key duplicate.

The two rows may or may not be exact duplicates.

The correct duplicate definition must therefore be documented.

---

## Composite keys

A single field may not uniquely identify a record.

A transaction dataset might require:

`Customer ID + Order Date + Product ID + Order Number`

as a composite key.

The Python implementation demonstrates multi-column duplicate detection through `find_duplicates()`.

Composite keys are useful when:

- No single natural key exists
- Multiple systems generate partial identifiers
- Records represent events rather than master entities

---

## Identity matching

The Python implementation also demonstrates the creation of a normalized identity key using:

- Name
- Email
- Phone

This can help find potentially related records.

It should not be treated as proof that two records represent the same person.

Two people can share:

- A name
- A household phone
- A similar email
- Similar addresses

Identity resolution is therefore a separate problem from simple duplicate detection.

---

## Standardization versus validation

These concepts should be separated.

Standardization changes representation.

Validation checks whether the representation satisfies a rule.

For example:

`USER@EXAMPLE.COM`

can be standardized to:

`user@example.com`

Validation then determines whether it has an acceptable email structure.

A transformation can produce a standardized value that remains invalid.

A valid value can also be represented in a non-standard format.

This distinction is important when designing Excel formulas and Power Query transformations.

---

## Excel functions relevant to data cleaning

Several Excel functions are particularly useful for cleaning.

### TRIM

`=TRIM(A2)`

Removes unnecessary spaces from ordinary text.

### CLEAN

`=CLEAN(A2)`

Removes many non-printing characters.

### UPPER

`=UPPER(A2)`

Converts text to uppercase.

### LOWER

`=LOWER(A2)`

Converts text to lowercase.

### PROPER

`=PROPER(A2)`

Converts words to title-style capitalization.

### LEFT

`=LEFT(A2,4)`

Extracts characters from the left.

### RIGHT

`=RIGHT(A2,4)`

Extracts characters from the right.

### MID

`=MID(A2,2,4)`

Extracts a specified number of characters beginning at a specified position.

Excel uses one-based character positions.

Python and many programming languages use zero-based indexes, which is an important implementation difference.

### SUBSTITUTE

`=SUBSTITUTE(A2,"U.P.","UP")`

Replaces matching text.

### LEN

`=LEN(A2)`

Counts characters.

### FIND

`=FIND("@",A2)`

Locates text using case-sensitive matching.

### SEARCH

`=SEARCH("@",A2)`

Locates text without requiring case-sensitive matching.

### VALUE

`=VALUE(A2)`

Converts suitable text representing numbers into numeric values.

### IF

`=IF(B2="","Missing","Present")`

Applies conditional logic.

### IFERROR

`=IFERROR(formula,"Invalid")`

Provides an alternative result when a formula generates an error.

### XLOOKUP

`=XLOOKUP(A2,Mapping[Source],Mapping[Standard])`

Retrieves a standardized value from a mapping table.

### COUNTIF

`=COUNTIF(A:A,A2)`

Counts occurrences matching a criterion.

This can help identify duplicate values.

### COUNTIFS

`=COUNTIFS(A:A,A2,B:B,B2)`

Counts records satisfying multiple conditions.

### SUMIF

`=SUMIF(A:A,A2,B:B)`

Adds values associated with a criterion.

### SUMIFS

`=SUMIFS(C:C,A:A,A2,B:B,B2)`

Adds values satisfying multiple criteria.

### UNIQUE

`=UNIQUE(A2:A1000)`

Returns unique values.

### FILTER

`=FILTER(A2:D1000,D2:D1000="Electronics")`

Returns rows satisfying a condition.

### SORT

`=SORT(A2:D1000,4,-1)`

Sorts an array according to a selected column and direction.

---

## Find and Replace

Find and Replace is useful for simple deterministic corrections.

Examples include replacing:

`U.P.`

with:

`UP`

or removing a known unwanted character.

It becomes risky when:

- The same text has different meanings
- Replacements are performed across unrelated columns
- Original values are not preserved
- The replacement rule is undocumented

For repeatable workflows, Power Query or explicit formulas can provide better traceability.

---

## Data Validation

Excel Data Validation can restrict user input.

Examples include:

- Whole number between 0 and 120
- Decimal greater than or equal to zero
- Date within a range
- List of allowed categories
- Custom formula

For the example category field, a validation list can contain:

`Electronics`

`Home Appliances`

`Furniture`

This prevents many inconsistent values from being introduced in the first place.

Data cleaning is therefore not only about fixing historical data. Good validation can prevent future quality problems.

---

## Conditional formatting

Conditional formatting is useful for visual quality inspection.

Examples include highlighting:

- Duplicate customer IDs
- Blank required cells
- Negative amounts
- Invalid ages
- Out-of-range values
- Missing dates
- Unapproved categories

A common duplicate rule is conceptually equivalent to:

`COUNTIF($A:$A,A2)>1`

The exact formula depends on the worksheet structure.

Conditional formatting is particularly useful when a human needs to inspect exceptions rather than automatically correcting them.

---

## Power Query

Power Query provides a repeatable transformation environment within the Microsoft data ecosystem.

Typical operations include:

- Removing columns
- Renaming columns
- Changing data types
- Removing duplicates
- Replacing values
- Splitting columns
- Merging queries
- Appending datasets
- Filtering records
- Grouping data
- Filling values
- Transforming text
- Creating repeatable transformation steps

Power Query is particularly useful when the same cleaning process must be applied repeatedly to refreshed source data.

The Python pipeline in this project demonstrates the same conceptual idea: transformations are represented as explicit repeatable steps instead of manual edits.

---

## Python implementation

The Python implementation is designed as a detailed educational data-cleaning laboratory.

### Dataset representation

Records are represented as dictionaries inside a list.

Conceptually:

`list[dict[str, Any]]`

This is convenient for demonstrating spreadsheet-like rows and columns.

Each dictionary represents one row.

Each dictionary key represents a column.

### Profiling

`profile_dataset()` calculates:

- Number of rows
- Number of columns
- Missing values
- Unique values

Profiling should happen before transformation because cleaning decisions depend on what the dataset actually contains.

### Whitespace normalization

`clean_whitespace()`:

- Replaces non-breaking spaces
- Removes control characters
- Collapses repeated whitespace
- Removes leading and trailing whitespace

### Standardization

The Python program contains separate functions for:

- Names
- Email addresses
- Cities
- Categories
- States
- Phone numbers

Separating these operations makes the cleaning rules easier to test and modify.

### Numeric conversion

`parse_currency()` handles common currency representations and returns `Decimal`.

Invalid values return `None`.

The implementation deliberately rejects ambiguous values such as `1O,500`.

### Date conversion

`parse_date()` accepts several explicitly defined formats.

Invalid dates return `None`.

### Validation

`validate_row()` combines field-level validation.

The implementation checks:

- Required values
- Customer ID format
- Email syntax
- Amount validity
- Date validity
- Age validity

`cross_field_validation()` then checks relationships between fields.

### Duplicate detection

`find_duplicates()` groups records according to one or more key columns.

This allows duplicate definitions to be explicit.

### Audit trail

`create_audit_trail()` compares the raw and cleaned versions.

Each detected change records:

- Row
- Column
- Original value
- New value

An audit trail is useful because automatic transformation should remain explainable.

### Quality scoring

The Python implementation calculates:

- Completeness
- Uniqueness
- Validity

These measurements provide a quantitative view of data quality.

They should not be interpreted as a universal single quality score because different datasets have different business requirements.

### Testing

The script uses assertions to test important edge cases.

Examples include:

- Whitespace normalization
- Email normalization
- Phone normalization
- Currency parsing
- Invalid numeric text
- Valid dates
- Invalid dates
- Valid ages
- Invalid ages

Testing is important because a cleaning rule can itself introduce errors.

---

## JavaScript implementation

The JavaScript implementation approaches the same subject through application-style data processing.

### Objects and arrays

JavaScript objects represent spreadsheet-like rows.

An array represents the dataset.

This structure maps naturally to JSON-based web applications and APIs.

### Array transformations

The implementation uses:

- `map()`
- `filter()`
- `reduce()`
- `sort()`

These are important JavaScript mechanisms for transforming collections.

For example:

`rows.map(cleanCustomer)`

creates a new array without modifying the original array.

This supports an immutable transformation style.

### Maps

`Map` is used for controlled vocabularies and grouped values.

For example:

`categoryMap`

maps multiple source representations to one canonical category.

### Regular expressions

Regular expressions are used for:

- Email validation
- Customer ID validation
- Date structure detection
- Numeric structure validation

Regular expressions are useful for syntax-level checks, but they do not prove semantic correctness.

### Date handling

The JavaScript implementation demonstrates an important subtlety.

JavaScript `Date` can normalize impossible dates instead of simply rejecting them.

The implementation therefore creates the date and compares the resulting year, month, and day against the input components.

This prevents values such as `31/09/2026` from silently becoming a different date.

### Functional pipeline

The JavaScript pipeline contains transformation steps with names and functions.

This resembles a repeatable data-processing workflow.

A pipeline approach provides a clear order of operations and makes transformations easier to test.

### Asynchronous processing

The asynchronous example demonstrates a Promise-based cleaning boundary.

Real applications may receive data from:

- File uploads
- APIs
- Databases
- Browser events
- Cloud services

The example keeps the cleaning logic synchronous while demonstrating how it can participate in an asynchronous application.

### CSV generation

The JavaScript implementation creates CSV output and escapes fields containing:

- Commas
- Quotes
- Newlines

CSV escaping is necessary because a comma inside a field should not automatically be interpreted as a column separator.

---

## C++ case study

The C++ program models a customer transaction data-quality engine.

The purpose is to demonstrate how spreadsheet-oriented cleaning concepts can be implemented as a structured application.

### Problem being solved

An organization receives customer transaction records containing inconsistent values.

The system must:

- Normalize values
- Reject invalid values
- Detect duplicates
- Validate relationships
- Record transformations
- Measure data quality
- Aggregate transactions
- Produce cleaned CSV output

The input resembles a spreadsheet export.

The output represents a cleaned dataset suitable for further processing.

---

## C++ domain model

The program defines:

`CustomerRecord`

for raw input.

`CleanCustomerRecord`

for transformed data.

`ValidationResult`

for validation status and error messages.

Separating raw and cleaned structures reduces the risk of accidentally replacing source information.

It also makes the architecture clearer.

---

## C++ optional values

C++17 `std::optional` is used for values that may not exist after cleaning.

Examples include:

- Email
- Phone
- Amount
- Order date
- Age

An invalid amount is not converted to zero.

Instead, the program represents the absence of a valid value.

This is an important design distinction because zero and missing are not necessarily equivalent.

---

## C++ date validation

The case study implements its own calendar validation.

It checks:

- Month range
- Day range
- Leap years
- Month-specific day counts

Leap years follow the Gregorian rules:

- Divisible by 4
- Except years divisible by 100
- Unless also divisible by 400

This allows the program to reject impossible dates without relying on external libraries.

---

## C++ validation architecture

The C++ program separates:

1. Parsing
2. Standardization
3. Field validation
4. Cross-field validation

This separation prevents different concerns from becoming one large function.

For example:

`parseAmount()`

determines whether text can be interpreted as a number.

`validateRecord()`

determines whether the resulting record satisfies required business rules.

`validateRelationships()`

checks relationships between fields.

---

## C++ duplicate detection

Customer IDs are grouped using a map.

The algorithm conceptually performs:

`Customer ID -> list of spreadsheet rows`

If the list contains more than one row, the identifier is duplicated.

This provides a direct way to report the original spreadsheet row numbers.

The program also generates complete record signatures for exact duplicate detection.

---

## C++ audit trail

The audit trail records:

- Spreadsheet row
- Field
- Original value
- Cleaned value

This is important in systems where transformations must be explainable.

For example:

`"RAHUL.SHARMA@EXAMPLE.COM "` 

can be shown as transformed into:

`"rahul.sharma@example.com"`

The transformation is visible instead of silently disappearing.

---

## C++ aggregation

The case study groups monetary values by category.

The resulting structure is conceptually:

`Category -> Total Amount`

This demonstrates how cleaned data can immediately support analytical operations.

Cleaning is not the final purpose of a dataset. Clean data becomes the foundation for:

- Reporting
- Analysis
- Dashboards
- Forecasting
- Financial calculations
- Machine learning
- Operational systems

---

## Edge cases

The implementations intentionally include several problematic records.

### Duplicate customer ID

`C005` appears twice.

This demonstrates duplicate detection.

### Missing email

The C005 records have no email.

This demonstrates missing-value handling.

### Invalid date

`31/09/2026`

is impossible because September has 30 days.

The date is rejected.

### Invalid age

`150`

is outside the defined age range.

It is not automatically converted to another age.

### Textual age

`twenty-eight`

does not match the numeric parsing rule.

It is flagged as invalid.

### Negative amount

`-500`

is rejected under the business rule that sales amounts cannot be negative.

A different financial domain might legitimately allow negative amounts for refunds or adjustments. The rule therefore depends on the dataset's meaning.

### Invalid email

`arjun.mehta@example`

does not contain the expected domain structure.

It is rejected by the practical syntax check.

### Ambiguous number

`1O,500`

contains the letter `O`.

The programs reject it rather than assuming it means `10,500`.

---

## Cleaning versus correction

Cleaning does not always mean automatically changing a value.

There are three useful categories:

### Safe transformation

The intended result is clear.

Example:

`"  Rahul Sharma  "` -> `"Rahul Sharma"`

### Rule-based transformation

The transformation is supported by an explicit mapping.

Example:

`"UP"` -> `"Uttar Pradesh"`

### Ambiguous transformation

The intended result cannot be reliably determined.

Example:

`"1O,500"`

It might be a typing error, but automatically changing it to `10,500` would introduce an assumption.

The safest automated behavior is to flag it.

---

## Imputation

Imputation means replacing missing values with estimated or derived values.

Possible techniques include:

- Mean
- Median
- Mode
- Group-based statistics
- Forward filling
- Backward filling
- Model-based estimation

The Python script demonstrates median imputation as an example but deliberately treats it as an optional technique.

Imputation changes the dataset.

It can affect:

- Distributions
- Variance
- Correlations
- Statistical inference
- Model behavior

Missingness should therefore be investigated before imputation.

---

## Outliers

An outlier is an observation that is unusually distant from other observations according to a selected statistical method.

The Python script demonstrates z-scores and an interquartile-range approach.

A statistical outlier is not automatically an error.

For example, a very large transaction may be:

- A genuine enterprise order
- A bulk purchase
- A legitimate exceptional transaction
- A data-entry mistake

The correct action is investigation, not automatic deletion.

---

## Z-score

A z-score measures the distance of a value from the mean in units of standard deviation.

The general form is:

`z = (x - mean) / standard deviation`

Large positive or negative values may indicate unusual observations.

The threshold used to flag observations should be determined according to the statistical context.

---

## Interquartile range

The interquartile range is:

`IQR = Q3 - Q1`

A common exploratory rule identifies potential outliers below:

`Q1 - 1.5 × IQR`

or above:

`Q3 + 1.5 × IQR`

This is a screening technique, not proof of an error.

---

## Lookup-based standardization

A mapping table is often preferable to complex nested formulas.

For example, a mapping table can contain:

| Source value | Standard value |
| --- | --- |
| UP | Uttar Pradesh |
| U.P. | Uttar Pradesh |
| Uttar Pradesh | Uttar Pradesh |
| DL | Delhi |
| Delhi | Delhi |

The same principle is implemented through dictionaries or maps in Python, JavaScript, and C++.

This creates a reusable rule instead of embedding every replacement directly into the transformation logic.

---

## Data cleaning and joins

Cleaning becomes especially important before joining datasets.

Suppose one dataset contains:

`Uttar Pradesh`

and another contains:

`UP`

A join based directly on these values may fail.

Standardization makes the representations compatible.

The same problem occurs with:

- Customer IDs
- Product codes
- Country names
- Department names
- Email addresses
- Phone numbers
- Dates

A join can therefore expose hidden data-quality problems.

---

## Referential consistency

Suppose an order contains:

`Customer ID = C001`

but the customer master table contains no `C001`.

The order record may be syntactically valid but referentially invalid.

This is different from simple field validation.

Referential validation asks whether a value exists in a trusted related dataset.

In Excel, this can be investigated through:

- XLOOKUP
- COUNTIF
- COUNTIFS
- Power Query merges
- Power Pivot relationships

---

## Data validation before data entry

Cleaning is more effective when problems are prevented at the source.

Excel Data Validation can restrict:

- Allowed categories
- Date ranges
- Numeric ranges
- Required formats
- User selections

For example, instead of allowing arbitrary category text, a dropdown can restrict values to:

`Electronics`

`Home Appliances`

`Furniture`

Prevention reduces the amount of later cleaning.

---

## Formula-driven cleaning versus Power Query

Formula-based cleaning is useful when:

- Users need to see the transformation directly
- The dataset is relatively small
- Interactive formulas are desirable
- The transformation is simple

Power Query is useful when:

- The same transformation must be repeated
- Data comes from multiple sources
- Many transformation steps are required
- Refreshability is important
- Manual editing would be error-prone

A formula-based workbook and a Power Query pipeline can solve similar problems while having different maintenance characteristics.

---

## Performance considerations

### Small Excel datasets

For small datasets, formulas and ordinary worksheet operations are usually sufficient.

### Larger datasets

Performance can degrade when a workbook contains:

- Large numbers of formulas
- Volatile formulas
- Repeated full-column references
- Complex nested calculations
- Many lookup operations
- Large numbers of conditional formatting rules

Power Query can move substantial transformation work out of individual worksheet cells.

### Python

The Python implementation uses ordinary lists and dictionaries for clarity.

For very large datasets, loading the entire dataset into memory may become inefficient.

### JavaScript

Array operations are convenient but also require memory proportional to the dataset when complete collections are retained.

### C++

The C++ implementation gives more explicit control over memory and data structures, but that control also requires more implementation responsibility.

---

## Complexity

For a dataset with `N` records and average field length `L`, basic text normalization is approximately:

`O(N × L)`

Duplicate grouping using hash-based structures is generally approximately:

`O(N)`

on average.

Ordered map-based grouping is generally:

`O(N log N)`

The audit trail grows with the number of changed fields.

Memory usage depends on whether the entire raw and cleaned datasets are kept simultaneously.

Streaming approaches can reduce memory consumption when processing very large files.

---

## Security considerations

Spreadsheet data can contain personally identifiable information and commercially sensitive information.

Examples include:

- Names
- Phone numbers
- Email addresses
- Addresses
- Financial transactions
- Customer identifiers

Cleaning workflows should therefore consider:

- Access control
- Secure storage
- File permissions
- Data minimization
- Audit logs
- Version control
- Retention policies
- Secure transfer

Spreadsheet exports should not contain secrets such as:

- Passwords
- API keys
- Access tokens
- Database credentials

---

## Formula injection

Spreadsheet exports require special attention when user-controlled text begins with characters that spreadsheet applications can interpret as formulas.

Depending on the environment, values beginning with characters such as:

`=`

may be interpreted as formulas when opened in spreadsheet software.

CSV generation should therefore consider whether exported values are trusted and how the target spreadsheet application interprets them.

The C++ and JavaScript implementations demonstrate CSV escaping for delimiters and quotes, but CSV syntax escaping alone is not equivalent to spreadsheet formula-injection protection.

---

## Common mistakes

### Editing the only copy

If the original dataset is overwritten, recovering the original values becomes difficult.

### Removing every duplicate automatically

Duplicates may represent legitimate repeated transactions.

### Filling every blank with zero

Zero and missing are not equivalent.

### Automatically fixing ambiguous values

Guessing can introduce silent corruption.

### Treating formatting as validation

A value can look correct while being semantically invalid.

### Treating an outlier as an error

An unusual value may be legitimate.

### Using uncontrolled replacements

A replacement can affect values that were not intended to change.

### Mixing text and numeric values

This can produce incorrect sorting, formulas, and aggregations.

### Ignoring column relationships

Each cell can be valid individually while the complete row is inconsistent.

### Treating email syntax as email verification

A syntactically valid email is not proof that the mailbox exists.

### Ignoring auditability

Important automated transformations should be explainable.

---

## Important distinctions

| Concept | Meaning |
| --- | --- |
| Cleaning | Broad process of improving data quality |
| Standardization | Converting equivalent representations to a common form |
| Validation | Checking whether data satisfies defined rules |
| Correction | Changing incorrect information to a known correct value |
| Imputation | Replacing missing values using a defined estimation method |
| Deduplication | Identifying and resolving repeated records |
| Profiling | Measuring characteristics and quality problems in data |
| Outlier detection | Identifying statistically unusual observations |
| Referential validation | Checking relationships against another dataset |
| Audit trail | Record of transformations and decisions |

---

## Python, JavaScript, and C++ comparison

| Aspect | Python | JavaScript | C++ |
| --- | --- | --- | --- |
| Main focus | Data transformation and analysis | Application-style data processing | Structured systems implementation |
| Dataset representation | Lists and dictionaries | Arrays and objects | Structs and vectors |
| Mapping structure | Dictionary | Map | unordered_map |
| Missing values | `None` | `null` / `undefined` | `std::optional` |
| Text processing | String methods and regex | String methods and regex | Standard library and regex |
| Numeric parsing | Decimal and numeric types | Number | Double and explicit parsing |
| Pipeline style | Functions and classes | Array methods and pipeline steps | Explicit classes/functions |
| Testing | Assertions | Custom assertion function | Compile-time and runtime structure |
| CSV output | `csv` module | Custom CSV serializer | Explicit CSV serializer |
| Memory control | High-level | High-level | More explicit |
| Systems-level control | Lower | Lower | Higher |

---

## Why the three implementations differ

The purpose is not to duplicate the same program in three languages.

Python provides concise data-processing constructs and is well suited to demonstrating cleaning rules, profiling, validation, statistical calculations, and testing.

JavaScript naturally represents JSON-style records and demonstrates how data cleaning can become part of a browser or application workflow. Its array operations are particularly useful for transformations.

C++ requires more explicit modeling and implementation decisions. The case study demonstrates how data cleaning can become part of a structured data-processing service rather than remaining a collection of spreadsheet edits.

The underlying principles remain the same:

`Inspect -> Transform -> Validate -> Audit -> Export`

---

## Implementation considerations

A production cleaning system should separate at least four conceptual layers:

### Input

Responsible for receiving the source data.

### Transformation

Responsible for deterministic standardization.

### Validation

Responsible for detecting violations.

### Output

Responsible for producing a controlled cleaned dataset.

A fifth layer is often valuable:

### Audit

Responsible for recording what changed and why.

This architecture makes the system easier to test and maintain.

---

## Idempotence

A cleaning transformation is desirable when applying it twice produces the same result as applying it once.

For example:

`"  Delhi  "` -> `"Delhi"`

Applying the same whitespace normalization again should leave:

`"Delhi"`

unchanged.

The Python and JavaScript implementations explicitly test this property.

Idempotent transformations reduce the risk of repeated processing producing progressively altered data.

---

## Deterministic transformations

A deterministic transformation produces the same result for the same input and rules.

For example:

`"UP"` -> `"Uttar Pradesh"`

is deterministic when the mapping table is fixed.

Determinism is important for:

- Testing
- Reproducibility
- Auditing
- Debugging
- Batch processing
- Automated refreshes

---

## Error handling

Good cleaning systems should distinguish between:

- Valid data
- Missing data
- Invalid data
- Ambiguous data
- Data requiring manual review

The programs generally represent invalid or unavailable values explicitly rather than silently converting them to arbitrary defaults.

This is especially important for financial, customer, regulatory, and operational datasets.

---

## Production data-cleaning checklist

- Preserve the original source.
- Define the meaning of each column.
- Identify required fields.
- Profile missing values.
- Identify inconsistent representations.
- Standardize text.
- Normalize categories.
- Normalize numeric values.
- Normalize dates.
- Validate data types.
- Validate field ranges.
- Validate cross-field relationships.
- Define duplicate keys.
- Investigate duplicates.
- Investigate outliers.
- Maintain an audit trail.
- Test transformations.
- Measure data quality before and after cleaning.
- Protect sensitive information.
- Document assumptions.
- Export a controlled clean dataset.
- Make repeatable transformations idempotent where possible.

---

## Practical relationship to Excel

The programming implementations model operations that can be performed directly in Excel.

For a simple worksheet, a typical workflow might contain:

1. Raw source sheet
2. Mapping sheet
3. Cleaning formulas or Power Query
4. Validation columns
5. Exception report
6. Clean output table

A mapping sheet might contain standardized categories and state names.

Validation columns can explicitly identify problems such as:

`Missing`

`Invalid`

`Duplicate`

`Inconsistent`

`Valid`

This is preferable to hiding errors through formatting alone.

---

## The role of human review

Not every data-quality problem should be automated.

Automation is well suited to deterministic rules such as:

- Removing extra spaces
- Converting known state codes
- Standardizing known categories
- Parsing known date formats
- Detecting duplicate identifiers

Human review is often appropriate for ambiguous cases such as:

- Unclear names
- Conflicting customer information
- Ambiguous dates
- Suspicious but potentially legitimate transactions
- Statistical outliers
- Conflicting source-system values

The objective is not to maximize the number of automatic changes.

The objective is to produce reliable data while minimizing unjustified changes.

---

## Real-world applications

Data cleaning is used in:

- Customer relationship management
- Financial reporting
- Sales analytics
- Marketing databases
- Human resources
- Healthcare administration
- Supply-chain management
- Inventory systems
- Banking
- E-commerce
- Government datasets
- Research datasets
- Machine-learning pipelines
- Business intelligence
- Regulatory reporting

The specific rules differ by domain, but the underlying process remains similar.

---

## Key implementation lessons

The Python implementation demonstrates detailed data profiling, cleaning functions, validation, duplicate detection, statistical anomaly checks, audit trails, quality metrics, testing, CSV export, and a reusable pipeline.

The JavaScript implementation demonstrates object-based datasets, array transformations, maps, regular expressions, asynchronous execution, validation, functional pipelines, testing, and CSV serialization.

The C++ implementation demonstrates explicit domain modeling, optional values, parsing, date validation, controlled vocabularies, duplicate detection, audit structures, aggregation, CSV serialization, and complexity considerations.

Together, the implementations show that spreadsheet data cleaning is not merely a collection of formatting operations. It is a structured data-quality process involving representation, validation, business rules, traceability, and controlled transformation.
