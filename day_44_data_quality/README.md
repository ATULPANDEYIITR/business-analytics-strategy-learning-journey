# Data Quality: Accuracy, Completeness, Consistency and Validity

## Scope

Data quality describes whether data is sufficiently trustworthy for the
business or technical decision that depends on it.

This implementation treats four dimensions as related but distinct:

| Dimension | Core question | Typical failure |
| --- | --- | --- |
| Accuracy | Does the value represent the real-world fact? | A customer's email differs from independently verified information. |
| Completeness | Is required information present? | A required email or customer identifier is missing. |
| Consistency | Do related values agree with one another and across records? | A customer is marked inactive while retaining an active credit limit. |
| Validity | Does the value obey the defined domain, format, type, or range? | An email has an invalid structure or a credit limit is negative. |

The distinction matters because a value can satisfy one dimension while failing
another. `maria.changed@example.com` can be syntactically valid but inaccurate
when the trusted customer record contains `maria@example.com`. A missing value
is incomplete even though it may not be possible to classify it as invalid.
`EUR` is a valid currency code but can be inconsistent when it is attached to a
customer whose country is `US` under a rule that requires USD.

The six artifacts model these distinctions using different technical
approaches rather than repeating the same implementation in every language.

## Quality Dimensions

### Accuracy

Accuracy requires an authoritative or independently trusted reference.

The Python implementation uses `verified` customer records and compares
selected fields against those facts. The JavaScript implementation uses
`VERIFIED_CUSTOMERS`. The C++ and Java programs maintain explicit reference
structures. The SQL implementation stores trusted facts in
`verified_customer_facts`.

A format check cannot establish accuracy. An address can have a correct postal
format and still identify the wrong location. An email can match an email
regular expression while belonging to a different person.

Accuracy therefore usually depends on a source hierarchy, reconciliation
process, or independent verification mechanism.

### Completeness

Completeness concerns the presence of information required for a particular
purpose.

The Python script defines `REQUIRED_FIELDS` and evaluates every record against
that set. Missing keys, `None`, empty strings, and whitespace-only strings are
treated as missing.

The JavaScript pipeline applies a `required-fields` rule. The Java enterprise
model uses `CompletenessRule`. The SQL schema uses `NOT NULL`, non-blank
constraints, and a profiling view to expose population-level completeness.

Completeness should be defined relative to business use. A field can be
optional for one workflow and mandatory for another. Treating every database
column as universally mandatory can create false quality failures.

### Consistency

Consistency examines relationships rather than isolated values.

The implementations use country-to-currency relationships as one example.
The rule says that `IN` maps to `INR`, `US` maps to `USD`, and `DE` maps to
`EUR`. The implementations also model a business-state relationship in which
an inactive customer should not retain a positive credit limit.

Cross-record consistency is represented through duplicate customer identifiers
and duplicate email ownership.

A consistency failure does not necessarily mean that either individual value
is syntactically invalid. `US` and `EUR` are individually valid values, but
their combination violates the selected business relationship.

### Validity

Validity evaluates formal rules.

The implementations validate:

- accepted country codes;
- accepted customer statuses;
- email structure;
- date representation;
- future-date restrictions;
- non-negative credit limits;
- enumerated domain values.

Validity is therefore rule-based. A value may be valid even when it is not
accurate. The distinction prevents format validation from being incorrectly
used as evidence that the underlying information is true.

## Python Implementation

The Python program provides the broadest standalone validation pipeline.

`Issue` represents an individual quality failure, while `QualityReport`
collects the result of a complete assessment. The four dimension-specific
functions make the conceptual separation explicit.

`check_accuracy()` compares data with verified reference facts and also checks
the country-to-currency relationship.

`check_completeness()` evaluates required fields without silently inventing
missing information.

`check_validity()` handles accepted domains, email structure, ISO-style dates,
future dates, and numeric ranges.

`check_consistency()` evaluates relationships within a record.

Dataset-level functions extend consistency checks across records. Duplicate
identifiers and duplicate email ownership cannot be discovered reliably by
looking at one row in isolation.

The `DataQualityEngine` combines these checks into a report and calculates
dimension-level scores. The scoring model is intentionally operational rather
than presented as a universal measure of data quality.

The remediation section demonstrates normalization of whitespace and
case-sensitive identifiers. It does not automatically invent missing values.
That is an important design decision because aggressive imputation can improve
completeness while damaging accuracy.

The script also supports CSV ingestion, JSON issue reporting, profiling,
quarantine of affected records, and explicit edge-case validation.

## JavaScript Implementation

The JavaScript artifact models quality processing as an event-driven pipeline.

`QualityRule` separates a rule's name, dimension, and evaluator. This makes
the validation system extensible without embedding every check inside one
large function.

The `QualityEventBus` provides observable lifecycle events:

- `quality.started` identifies the beginning of a batch;
- `quality.issue` exposes individual failures;
- `quality.completed` exposes the resulting scorecard.

This structure is useful when quality processing must feed operational
monitoring or asynchronous systems.

The JavaScript implementation also performs normalization before validation.
Email addresses are normalized to lowercase, country and currency codes are
normalized to uppercase, and status values are normalized to lowercase.

The asynchronous `validateIncomingBatch()` function models a boundary where
data may arrive from a database, HTTP endpoint, message queue, or file
processing service. The example remains dependency-free and executable with
Node.js.

A quality gate is evaluated after scoring. This demonstrates an important
operational distinction: measuring quality and enforcing a minimum quality
threshold are separate responsibilities.

## C++ Case Study

The C++ program models a customer master-data quality engine where deterministic
rules must execute efficiently over a collection of records.

`Customer` represents the operational entity, while `ReferenceCustomer`
represents independently verified information.

The `QualityEngine` keeps domain rules together while separating the four
dimension checks into distinct operations.

C++ standard containers are used according to their role:

- `std::set` represents accepted domain values;
- `std::map` represents country-to-currency reference mappings;
- `std::unordered_map` supports dataset-level counting and grouping;
- `std::set` identifies customers affected by a quality dimension.

The validity implementation checks email structure, date structure, country
domains, status domains, and non-negative credit limits.

The consistency implementation evaluates related fields. The accuracy
implementation compares customer facts with trusted reference data.

The engine also performs cross-record checks for duplicate identifiers and
duplicate email ownership.

The score calculation records affected customers separately for every
dimension. This prevents a record with several errors from being counted as
several records for the same dimension.

The quality gate is deliberately separated from the engine. A consumer can
choose different thresholds for different operational requirements without
rewriting the validation logic.

## Java Enterprise Model

The Java program represents the same domain using stronger domain abstractions.

`CustomerStatus` is an enum rather than a free-form string. This prevents
unsupported application states from being represented as ordinary status
values.

Java records provide immutable representations for customers, reference facts,
quality issues, reports, and validation context.

The `QualityRule` interface provides a common contract for independent rule
implementations:

- `CompletenessRule` checks required information;
- `ValidityRule` checks formal constraints;
- `ConsistencyRule` evaluates relationships between fields;
- `AccuracyRule` compares operational data with verified facts.

`DatasetConsistencyRule` handles cross-record relationships such as duplicate
identifiers and duplicate email ownership.

`QualityService` composes the rules and calculates dimension-specific quality
scores. The service also exposes an overall quality gate without coupling
individual validation rules to a particular deployment policy.

The model illustrates a useful enterprise design principle: policy,
validation, domain state, reference information, and reporting can be
represented as separate abstractions.

## PostgreSQL Data Model

The SQL implementation places appropriate integrity rules in the database.

`country_currency_reference` provides a controlled reference relationship.

`customers` contains the operational customer data. Its constraints enforce
several validity and completeness requirements:

- `NOT NULL` prevents required fields from becoming absent;
- `CHECK` constraints prevent blank names and emails;
- a regular-expression check validates basic email structure;
- a credit-limit check prevents negative values;
- a date check prevents future signup dates;
- a foreign key constrains country codes to the reference table.

A unique index on normalized email values prevents duplicate email ownership
at the database layer.

The `verified_customer_facts` table represents independent facts needed for
accuracy assessment. Database constraints can ensure structural integrity of
the reference table, but they cannot prove that the reference information is
true. The trustworthiness of the source remains a governance concern.

`customer_consistency_issues` exposes country/currency contradictions and
inactive customers with positive credit limits.

`customer_accuracy_issues` compares operational data with trusted reference
data.

The completeness profile counts populated fields across the dataset. This is
different from `NOT NULL`: constraints prevent certain incomplete states, while
profiling measures the actual population.

The validity profile exposes field-level validity conditions.

The transaction demonstrates controlled normalization. The operation is
committed only after the transformed values can be inspected. In a production
workflow, the same pattern can be combined with approval or automated quality
gates.

## Quality Rules and Enforcement Layers

Data quality is strongest when controls are placed at the correct layer.

Application validation can provide immediate feedback before data reaches a
database. Database constraints provide authoritative structural enforcement.
Reference-data reconciliation supports accuracy. Profiling and monitoring
detect population-level deterioration.

A rule should not be implemented only because it is technically convenient.
The correct location depends on whether the rule concerns syntax, domain
integrity, business state, reference truth, or operational policy.

For example, a non-negative credit limit belongs naturally at the database
constraint layer because accepting a negative value would violate a basic
invariant.

A customer email matching an independently verified source cannot be reduced
to a simple `CHECK` constraint because the expected value is external
reference information.

## Profiling Versus Validation

Validation asks whether a particular value satisfies a defined rule.

Profiling describes the characteristics of a dataset.

The Python implementation reports missing counts, distinct counts, and
completeness rates for columns. The SQL implementation provides a similar
population-level completeness view.

Profiling is useful for detecting drift. A field can technically remain
optional while its missing rate rises from 2% to 30%. That change can be more
important operationally than a small number of individual validation failures.

Validation and profiling should therefore be treated as complementary
activities.

## Quality Scores

The examples calculate a dimension score based on the proportion of records
without detected issues in that dimension.

This approach is simple and transparent, but it has limitations. It does not
measure the business impact of each error, the severity of different fields,
or uncertainty in reference information.

A customer identifier error may be operationally more serious than a
non-critical descriptive-field error. A production scorecard can therefore
assign field-level weights, severity levels, or business-process weights.

The code intentionally keeps the scoring model understandable rather than
pretending that one formula is universally correct.

## Edge Cases

Missing values must be distinguished from legitimate zero values. A credit
limit of `0` is present and non-negative, while an absent credit limit is a
completeness failure.

Case normalization requires a defined policy. Email addresses are normalized
in the examples, while the treatment of names is intentionally conservative.

Duplicate detection must define its comparison key. Two records with different
internal identifiers but the same email may represent a duplicate customer,
while two records with different legitimate contacts must not be merged solely
because of another shared attribute.

Dates require both representation and semantic validation. A correctly shaped
future date can still violate a business rule.

Reference data requires provenance. A comparison is only as useful as the
trusted source against which it is made.

## Common Failure Modes

Treating validity as accuracy is a frequent design mistake. A syntactically
valid email does not prove that it belongs to the intended customer.

Treating missing values as valid defaults can hide completeness problems.
Automatically replacing missing business facts with arbitrary values can create
apparently complete but inaccurate records.

Checking consistency only within individual records misses cross-record
duplicates and conflicts.

Relying only on application validation leaves paths through bulk imports,
administrative scripts, and other integration channels that may bypass those
rules.

Making every quality rule a hard database constraint can also be harmful.
Some rules are diagnostic or advisory, while others represent non-negotiable
integrity conditions.

## Security and Governance Considerations

Quality systems often process sensitive customer information. Logs should not
expose complete personal data unnecessarily.

Quality reports should use controlled access because they may contain customer
identifiers, email addresses, reference values, or evidence of operational
errors.

Reference data should have clear ownership and provenance. An inaccurate
reference source can cause an entire downstream system to classify correct
operational data as inaccurate.

Remediation should be auditable. Automated transformations should record what
changed, why it changed, which rule authorized the transformation, and which
source produced the replacement value.

Database constraints should protect invariants even when application code is
changed or bypassed.

## Performance Considerations

Single-record validation generally scales linearly with the number of records
when each rule performs constant-time work.

Cross-record uniqueness checks require state across the dataset. Hash-based
structures such as Python dictionaries, JavaScript `Map`, C++ hash maps, and
database indexes provide efficient grouping and lookup.

Reference joins in SQL should be supported by appropriate indexes when the
reference and operational tables become large.

Profiling large datasets should avoid repeatedly scanning the same population
when a single aggregation can produce several metrics.

Quality scoring should distinguish the cost of validation from the cost of
remediation. Detecting a problem is often cheaper than safely correcting it.

## Production Interpretation

A production data-quality system should distinguish detection from correction.

Detection identifies evidence of a quality failure.

Classification assigns the failure to a dimension and severity.

Remediation changes the data only when the transformation is justified.

Quarantine isolates records that cannot safely enter downstream workflows.

Monitoring detects changes in quality over time.

Governance determines which rules are mandatory, which are advisory, who owns
the reference data, and what quality threshold is required for a business
process.

The four dimensions therefore form a connected quality model without becoming
interchangeable: accuracy concerns truth against trusted evidence,
completeness concerns required presence, consistency concerns relationships,
and validity concerns formal compliance with defined rules.
