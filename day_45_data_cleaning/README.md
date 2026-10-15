# Data Cleaning: Missing Values, Duplicates and Inconsistent Data

## Scope

This project treats data cleaning as a controlled transformation from unreliable source observations into validated analytical records. The working dataset represents customer transactions received from multiple operational systems.

The central distinction is important:

| Data-quality problem | What it means | Appropriate treatment |
| --- | --- | --- |
| Missing value | The expected information is absent or represented by a missing marker | Standardize to `NULL`, preserve unknown state, or apply a documented imputation rule |
| Duplicate record | The same business observation occurs more than once | Identify a stable business identity and retain the appropriate occurrence |
| Inconsistent data | Equivalent information appears in incompatible representations | Normalize the representation without changing the underlying business meaning |

The implementations deliberately keep these categories separate. A lowercase city is not missing. A repeated transaction is not merely an inconsistent string. An absent transaction amount should not automatically become zero.

The six deliverables approach the same data-quality domain from different technical perspectives:

- Python builds a complete executable cleaning pipeline with audit records, validation, duplicate detection, city-level median imputation, and serialization.
- JavaScript uses immutable records, `Map` and `Set`, an event-driven audit stream, asynchronous pipeline boundaries, and runtime validation.
- C++ models the problem as a non-trivial data-quality engine with explicit normalization, duplicate-key construction, optional values, auditing, and complexity considerations.
- Java models the workflow as enterprise domain services and rule abstractions, separating missing-value processing, consistency normalization, deduplication, imputation, and validation.
- PostgreSQL represents the same domain relationally and enforces important rules with constraints, indexes, a unique normalized key, views, window functions, a median calculation, and transactions.

## Data-quality model

A cleaning pipeline should not modify values simply because they look inconvenient.

A missing email means that the source does not provide an email. Replacing it with an invented address destroys the distinction between unknown and known information. The implementations therefore preserve missing contact information as `None`, `null`, `std::nullopt`, Java `null`, or SQL `NULL`, depending on the language.

A duplicate requires a different decision. If two rows contain the same business information, retaining both can inflate counts, revenue, customer activity, or other measures. Duplicate detection therefore occurs after relevant normalization. This allows representations such as `lucknow` and `Lucknow` to be compared as the same city rather than as unrelated strings.

Inconsistent data concerns representation. The source contains examples such as `INR`, `inr`, and `Rs.`, along with different phone-number formats, mixed status capitalization, and multiple date formats. These values describe the same concepts but require canonical forms before reliable validation and analysis.

## Cleaning workflow

The project uses the following conceptual flow:

```text
Raw observations
      |
      v
Missing-value recognition
      |
      v
Representation normalization
      |
      v
Duplicate detection
      |
      v
Documented missing-value treatment
      |
      v
Validation
      |
      v
Clean relational or structured records
      |
      v
Audit and quality measurement
