# Data Cleaning: Missing Values, Duplicates, and Inconsistent Data

## Purpose and scope

Data cleaning transforms raw records into a consistent, validated representation suitable for analysis and operational use. The process must distinguish between absent information, repeated entities, formatting differences, invalid values, and genuine differences in business meaning.

This project uses employee records to demonstrate a practical cleaning pipeline across Python, JavaScript, C++, Java, and PostgreSQL. The implementations address three related but distinct data-quality problems:

- **Missing values:** fields that contain no usable observation, such as an unknown age or an unreported salary.
- **Duplicate records:** multiple rows representing the same business entity or event, even when their source identifiers differ.
- **Inconsistent data:** equivalent values expressed in different forms, such as `eng`, `Engineering`, and ` ENGINEERING `.

The implementations also distinguish normalization from validation, record rejection from field-level correction, and cleaning from statistical imputation.

## Data-quality model

A reliable pipeline does not treat every unusual value as the same kind of error.

| Quality problem | Example | Appropriate treatment |
|---|---|---|
| Missing value | Empty salary field | Preserve as unknown and report |
| Formatting inconsistency | ` ALICE@example.com ` | Trim whitespace and normalize case |
| Category inconsistency | `ops` versus `Operations` | Map known aliases to a canonical category |
| Invalid value | Age of `150` | Reject the record or quarantine it |
| Duplicate identifier | Two rows with the same source ID | Reject the conflicting row for investigation |
| Duplicate business record | Same email, department, and join date | Apply a documented deduplication rule |
| Invalid date | `2023-02-30` | Reject the malformed value or record |
| Statistical uncertainty | Missing age replaced by a median | Mark the replacement as imputed |

These treatments have different consequences. Normalization should preserve meaning, validation should enforce explicit rules, and imputation should introduce an estimate only when a downstream analysis justifies it.

## Missing values and imputation

A missing value means that the system does not possess a usable observation. It does not mean zero, false, or an empty category.

The implementations recognize common textual markers such as empty strings, `N/A`, `NULL`, `None`, and `NaN`. They also distinguish actual missing numeric observations from valid values such as zero. Business rules can prohibit zero for a particular field, but that is a validation decision rather than a missing-value rule.

The Python implementation represents absent numeric values with `None`. JavaScript uses `null`, Java uses nullable wrapper types such as `Integer` and `Double`, and the C++ case study uses `std::optional`. PostgreSQL uses `NULL`, which is distinct from an empty string and from numeric zero.

Missing values are retained in the cleaned dataset when the available information does not justify filling them. The optional median-imputation functions demonstrate a separate analytical transformation:

- The median is calculated from observed values only.
- Missing values are replaced only in a derived copy or query result.
- The original cleaned observations remain available for audit.
- If no observed values exist, the imputation step is skipped.

Median imputation is not universally appropriate. It can reduce variance, distort distributions, and conceal systematic missingness. For example, missing salaries may reflect a particular employment category rather than random omissions. A production process should record the imputation method and distinguish observed values from estimated ones.

## Duplicate detection

### Identifier duplicates and business duplicates

A primary identifier answers whether two rows claim the same record identity. A business key answers whether two differently identified rows represent the same real-world record under the chosen rules.

The example uses the following business fingerprint:

`email + department + join_date`

After normalization, records with equivalent fingerprints are treated as duplicate employee records. The input records `P301` and `P303` in the Java implementation, for example, describe the same employee under this key despite different source identifiers and category formatting.

The business key is illustrative, not universally correct. A real employee system might use an authoritative employee number instead. Email addresses can change, and multiple employment periods may legitimately share an email address. The key must reflect the domain's identity rules.

### Deterministic survivor selection

The SQL implementation ranks equivalent rows by import order and keeps the earliest eligible row. The Python, JavaScript, C++, and Java implementations process records in source order and retain the first accepted business key.

This makes the result deterministic for a fixed input ordering. It does not guarantee that the earliest row is the most accurate. Production systems may select a survivor using source reliability, verification status, update timestamp, or a trusted master record.

The unique constraints in PostgreSQL provide a final integrity barrier. Application-level duplicate detection explains the decision, while database constraints prevent conflicting records from being stored concurrently.

## Inconsistent values and canonicalization

Canonicalization maps recognized variants to a common representation before comparisons, aggregation, or deduplication.

The department mapping is explicit:

| Accepted source values | Canonical department |
|---|---|
| `eng`, `Engineering` | Engineering |
| `finance`, `Finance` | Finance |
| `ops`, `Operations` | Operations |
| `hr`, `Human Resources` | Human Resources |

Unknown department labels are not automatically converted into an existing department. Doing so could turn a source-system defect into a misleading business classification.

Email normalization trims surrounding whitespace and applies lowercase comparison. This is suitable for the simplified employee-data scenario, but email identity rules can be more nuanced in some systems. Validation should be aligned with the authoritative system's policy rather than relying on a simplistic regular expression as proof that an address exists.

Dates are normalized to ISO format, `YYYY-MM-DD`. Parsing must validate calendar correctness, not just the appearance of the string. Salary values can contain thousands separators, but malformed strings, negative amounts, non-finite numbers, and values beyond the configured business limit must not be accepted silently.

Normalization should be idempotent wherever practical: applying it again to an already normalized value should not change that value.

## Validation and rejection policy

Validation enforces the domain's rules before data enters the clean dataset.

The examples apply the following employee-data constraints:

- Record identifiers must be present and unique.
- Email addresses must have an acceptable structure.
- Email and department are required for this workflow.
- Department values must map to known categories.
- Ages must be integral values between 18 and 100.
- Salaries must be finite, nonnegative values within the configured limit.
- Dates must be valid calendar dates and cannot be in the future.

A rejected record is different from a record containing an optional missing value. An employee with a valid email and department but no salary can remain in the cleaned dataset, while an employee with an invalid age representation is rejected by the example's row-level policy.

This policy is deliberately conservative. Other applications may quarantine only the invalid field, accept a partially valid row, or route questionable records for manual review. The correct choice depends on whether downstream consumers can safely use the remaining fields.

## Python implementation

The Python script combines validation functions, normalization rules, record-level processing, quality reporting, and file output.

`is_missing` recognizes common missing markers without incorrectly treating zero or `False` as missing. The email, department, age, salary, and date functions apply field-specific rules instead of using a single generic conversion routine.

`clean_records` processes the input in a deterministic sequence. It validates source identifiers, normalizes fields, checks business keys, and creates `CleaningIssue` objects that record the field, action, original value, and reason. Invalid rows are rejected; optional missing values remain visible in the output.

The `CleaningReport` separates input count, output count, duplicate removals, rejected rows, and individual issues. The reporting functions calculate missing-value counts, department distributions, and observed mean age. Optional median imputation returns a separate list, preserving the cleaned records.

The script uses only the Python standard library. `csv` handles tabular input and output, `json` serializes audit reports, `statistics` computes descriptive statistics, and `tempfile` verifies file-writing behavior without leaving demonstration files in the working directory.

For production use, the same pipeline could be connected to a source file, database extract, or scheduled batch job. The current example uses in-memory sample records to remain executable without external data.

## JavaScript implementation

The JavaScript file emphasizes immutable normalized records, canonical category mapping, and asynchronous batch processing in Node.js.

A `Map` provides explicit department aliases, while `Set` instances track source identifiers and business fingerprints. This avoids repeatedly scanning the accepted records for each duplicate candidate. Expected lookup and insertion costs are approximately constant on average, making the approach suitable for batches where the business key fits in memory.

`cleanRecord` produces a frozen normalized object. Invalid values raise errors that the pipeline records as rejected issues. The streaming-style processing uses Node.js streams and `pipeline`, which propagates failures and provides an explicit completion boundary instead of leaving background work unobserved.

The implementation also demonstrates why immutable records are useful in cleaning workflows. The optional imputation operation creates derived objects and marks estimated ages, avoiding silent mutation of the cleaned dataset.

The current pipeline reads an in-memory array through a stream. For very large imports, a source such as a file stream or database cursor could replace that array, and duplicate tracking might move to a persistent index or staging database. An in-memory `Set` requires memory proportional to the number of distinct keys.

## C++ case study

The C++ program models an employee import service in which source-system inconsistencies affect a downstream reporting dataset.

The `Employee` structure uses `std::optional` for age, salary, and join date. This allows missing values to remain explicit without reserving special numeric values such as `-1` or `0`. The `CleaningResult` aggregates accepted records, issue details, and counts for duplicate removals and rejected rows.

Normalization is divided into field-specific functions. Numeric parsing rejects non-finite and negative values, age validation checks integral bounds, and department mapping translates recognized aliases. The date validator checks the date's basic structure, month range, leap-year behavior, and number of days in each month.

Two `std::set` instances track source identifiers and business fingerprints. This separates primary-key conflicts from duplicate business records. Ordered sets offer logarithmic lookup and insertion, trading some speed for predictable behavior and straightforward implementation.

The program reports every recorded issue and calculates a median from observed ages. It applies imputation only to a copied vector. This is an important design decision in systems where the clean source representation must remain distinguishable from estimates used for analysis.

The sample focuses on deterministic batch processing. It does not implement a complete CSV parser, persistent audit store, or concurrent ingestion service. A production implementation would need explicit ownership of raw source data, structured logs, transactional writes, and a robust CSV parsing library or database staging layer.

## Java implementation

The Java program presents a domain-oriented design for an enterprise employee-data import process.

`RawEmployee` represents untrusted source values. `Employee` represents a validated record and enforces its core invariants in the compact constructor. `CleaningIssue` records the outcome of a transformation, and `CleaningOutcome` exposes immutable copies of accepted records and issues.

`BusinessKey` is a dedicated record, making the identity rule explicit and providing value-based equality for duplicate detection. This is clearer than building a loosely structured string key throughout the service.

The normalization service separates email, age, salary, department, and date validation. `IssueAction` is an enum, so audit events use a controlled vocabulary instead of arbitrary action strings. Collections distinguish source-ID uniqueness from business-key uniqueness.

Streams are used for reporting, including department distributions. The median calculation sorts only observed ages. The optional imputation operation constructs new `Employee` instances, preserving the immutability of the original domain records.

This design is suitable for extension into a service layer where import policy, normalization, audit persistence, and downstream publication can be tested independently. A production implementation should also define how source-row identifiers are assigned, how rejected rows are retried, and how validation policy changes are versioned.

## PostgreSQL data model

The SQL script uses a staging table and a normalized target model.

| Table | Responsibility |
|---|---|
| `employee_import_stage` | Preserves imported text values and source-row metadata |
| `departments` | Defines valid department codes and canonical names |
| `employee_records` | Stores accepted, normalized employee records |
| `cleaning_issues` | Records rejections, duplicate removals, and missing-value decisions |

The staging table permits raw text to be retained before strict validation. This is important because malformed values should remain inspectable even when they cannot be converted into the target column type.

The target table uses a primary key, a unique source-record identifier, a foreign key to the department table, and check constraints for age, salary, email structure, and future join dates. Its composite unique constraint protects the business key at the database layer.

The import uses common table expressions to normalize categories, parse numeric fields, classify invalid records, and rank potential duplicates. Window functions make survivor selection deterministic by import-row order. Invalid rows and duplicate candidates are recorded in the issue table rather than disappearing without explanation.

The quality-summary view reports record counts, missing ages, missing salaries, average observed age, and average observed salary by department. Aggregate functions ignore `NULL` values, so the reported means describe observed values rather than treating missing observations as zero.

Indexes support department-level reporting, lookup of records with missing ages, and recent issue queries by action. Their usefulness depends on actual table sizes and query patterns; indexes add storage and write costs.

The SQL script uses `pg_input_is_valid` to check date conversion before casting. This function is available in modern PostgreSQL versions; the script specifies PostgreSQL 15 or later as its target environment. It runs the import operations in a transaction, ensuring the defined changes commit together or roll back together if a statement fails.

## Auditability and reproducibility

A cleaning result should explain not only what the final value is, but also what happened to the original observation.

The implementations record reasons for rejected rows, removed duplicates, and retained missing values. The Python implementation additionally records normalized values and produces JSON reports. The database implementation persists issue records, while the Java and C++ implementations keep structured issue collections in memory.

A durable audit design should retain the source row or a stable reference to it, the applied rule, the original value where permitted, the resulting value, the timestamp, and the rule-set version. Sensitive fields should be protected through access controls and appropriate retention limits.

Reproducibility also depends on deterministic policies. A change to department aliases, duplicate keys, accepted age ranges, or survivor-selection criteria can change the output. These rules should be versioned when cleaning results are used in regulated reports or operational decisions.

## Performance and scaling

For \(n\) input rows, hash-based duplicate tracking in Python and JavaScript typically provides expected \(O(n)\) total processing time, assuming reasonable hash distribution and bounded per-row validation costs. C++ and Java examples use ordered sets, which typically require \(O(n \log n)\) total key-processing time. Median calculation requires sorting observed values, which takes \(O(n \log n)\) time.

The SQL approach delegates filtering, duplicate ranking, constraints, and aggregation to PostgreSQL. Database execution plans, table statistics, index selectivity, and transaction size determine actual performance.

Memory usage matters when importing millions of rows. Keeping all source records, cleaned records, audit events, and duplicate keys in memory can exceed available resources. Streaming input, staging tables, bounded batches, and persistent uniqueness constraints reduce this pressure. Deduplication across batch boundaries requires a persistent key store or a database constraint rather than a batch-local set alone.

## Failure modes and production considerations

**Over-aggressive deduplication** can remove legitimate records when the chosen business key is too broad. Validate the key against real domain identity rules before enabling destructive deduplication.

**Silent coercion** can turn invalid text into misleading numeric values. A malformed age should not become zero simply because zero is easy to store.

**Unmarked imputation** can cause downstream users to mistake estimates for observations. Derived datasets should preserve an imputation indicator or an equivalent audit trail.

**Locale-dependent parsing** can misinterpret values such as `1,234` or dates written as `04/05/2024`. The examples adopt explicit formats and limited numeric conventions rather than guessing a locale.

**Concurrent imports** can race when application code checks duplicates before inserting records. Database uniqueness constraints remain necessary even when the application performs its own checks.

**Partial failure** can leave an import and its audit trail inconsistent if writes are not transactional. Related database writes should commit atomically, while external publication should be designed for retries and idempotency.

**Sensitive data exposure** can occur when full raw rows or emails are copied into logs. Audit records should contain only the data needed for diagnosis, with restricted access and appropriate retention.

**Schema drift** occurs when upstream systems add fields, change types, or introduce new category values. Import validation should detect unexpected columns and unknown categories instead of assuming the source remains stable.

## Comparing the implementations

| Concern | Python | JavaScript | C++ | Java | PostgreSQL |
|---|---|---|---|---|---|
| Missing-value representation | `None` | `null` | `std::optional` | Nullable wrapper types | `NULL` |
| Category normalization | Dictionary mapping | `Map` | Explicit mapping function | Immutable mapping | `CASE` expressions and reference table |
| Duplicate tracking | `set` | `Set` | `std::set` | `HashSet` | Window functions and unique constraints |
| Validation failures | Exceptions and issue objects | Exceptions and issue objects | Exceptions and issue objects | Exceptions and typed issue records | Rejection queries and check constraints |
| Optional imputation | Separate copied records | Derived immutable objects | Copied vector | New immutable records | Analytical query |
| Audit persistence | JSON output | In-memory issue collection | In-memory issue collection | In-memory issue collection | Relational issue table |

The languages implement the same data-quality objectives through different mechanisms. Python prioritizes concise batch processing and reporting. JavaScript illustrates event-driven stream processing and immutable transformations. C++ emphasizes explicit optional values and deterministic system behavior. Java uses domain types and immutable state. PostgreSQL enforces relational integrity and supports auditable, set-oriented cleaning operations.

The choice of implementation depends on data volume, operational environment, required guarantees, and whether the cleaning process is an exploratory analytical task or a controlled production data pipeline.
