# SQL Joins: INNER, LEFT, RIGHT and FULL

## Scope

This learning artifact examines four relational join types through realistic repository-development data:

- `INNER JOIN` returns only rows with a matching relationship on both sides.
- `LEFT JOIN` preserves every row from the left relation and represents missing right-side data with `NULL`.
- `RIGHT JOIN` preserves every row from the right relation and is useful when the right-hand relation is the authoritative audit source.
- `FULL OUTER JOIN` preserves unmatched rows from both relations and is especially useful for reconciliation and data-quality analysis.

The implementations deliberately keep these semantics distinct. The examples use repositories, pull requests, reviews, status checks, branches, commits, reviewers, and branch-protection policies because those entities naturally produce one-to-one, one-to-many, missing-data, and reconciliation cases.

---

## Relational Join Fundamentals

A join combines rows from two relations according to a condition, normally expressed through an `ON` predicate.

For example, a repository can be related to a pull request through `repository_id`. The relationship is not based on the position of rows in either table. It is based on values that identify the same logical entity.

Conceptually:

`repositories.repository_id = pull_requests.repository_id`

The four requested join types differ primarily in which unmatched rows they preserve.

| Join | Matching rows | Unmatched left rows | Unmatched right rows |
|---|---|---|---|
| `INNER JOIN` | Yes | No | No |
| `LEFT JOIN` | Yes | Yes | No |
| `RIGHT JOIN` | Yes | No | Yes |
| `FULL OUTER JOIN` | Yes | Yes | Yes |

When an outer join has no matching row on one side, the columns from that side become `NULL`.

The distinction is important because changing `INNER JOIN` to `LEFT JOIN` is not merely a syntax change. It changes which business entities can disappear from the result.

---

## INNER JOIN

`INNER JOIN` is appropriate when the result should contain only entities that have an actual relationship on both sides.

The Python implementation demonstrates this by matching repository rows with pull-request rows. A repository without a pull request disappears from the inner-join result. A pull request whose repository is not represented on the other side also disappears.

The SQL implementation uses the same semantic idea with:

`FROM repositories AS r INNER JOIN pull_requests AS p ON p.repository_id = r.repository_id`

The C++ and Java implementations model the same relationship through hash indexes. Their indexed collections retain multiple rows for a key, which is necessary for one-to-many relationships.

### One-to-many behavior

An inner join does not guarantee one output row per left row.

If repository `payments-api` has three pull requests, joining the repository to those pull requests produces three rows containing that repository.

This is a core relational behavior:

`1 repository × 3 matching pull requests = 3 joined rows`

A program that assumes every join is one-to-one can produce incorrect counts and duplicated business values.

---

## LEFT JOIN

`LEFT JOIN` preserves every row from the left relation.

This is useful when the left relation represents the population that must remain visible.

For repository reporting, a query starting from `repositories` can use a left join to ensure that a repository with no pull requests still appears in the result.

The right-side pull-request columns become `NULL`.

That makes a query such as:

`WHERE p.pull_request_id IS NULL`

useful for finding repositories with no pull requests.

The Python program demonstrates the same pattern by creating a row whose right-side values are explicitly represented as `None`.

The Java implementation uses `Optional` fields in its domain records to represent the absence of a matching object rather than silently inventing a default object.

The C++ program uses `std::optional` for the same purpose.

### Why LEFT JOIN matters for reporting

An inner join answers:

"Which repositories have pull requests?"

A left join can answer:

"Show every repository and attach its pull requests when they exist."

Those questions are different. The first intentionally excludes repositories without activity. The second treats absence of activity as meaningful information.

---

## RIGHT JOIN

`RIGHT JOIN` preserves every row from the right relation.

It is semantically equivalent to reversing the two relations and using a `LEFT JOIN`.

For example:

`pull_requests RIGHT JOIN external_review_audit`

can be expressed as:

`external_review_audit LEFT JOIN pull_requests`

Both preserve every row from `external_review_audit`.

The SQL implementation demonstrates this using an external review-audit table. One audit record intentionally refers to a pull request identifier that is absent from the internal pull-request relation.

The right-side record remains visible.

### When RIGHT JOIN is useful

`RIGHT JOIN` is often less common in application SQL because teams can usually express the same logic with a `LEFT JOIN` by putting the authoritative table first.

Its important semantic property is still worth understanding:

The right relation is the preserved side.

This becomes useful when reading existing SQL, reviewing generated queries, or analyzing queries written around a right-hand audit dataset.

---

## FULL OUTER JOIN

`FULL OUTER JOIN` preserves unmatched rows from both relations.

It produces three logical groups:

- rows that matched
- rows that exist only on the left
- rows that exist only on the right

The SQL implementation uses this for reconciliation between internal pull-request data and an external review-audit source.

A reconciliation query can classify the result using `CASE`:

`MATCHED`

`INTERNAL_ONLY`

`EXTERNAL_ONLY`

This is a stronger use case for `FULL OUTER JOIN` than simply displaying combined data. It makes discrepancies visible.

### Reconciliation pattern

Suppose the internal system contains pull request `101`, while an external audit system contains records for `101` and `9999`.

A full join can reveal:

| Pull Request | External Review | State |
|---|---|---|
| 101 | present | matched |
| 9999 | present | external only |
| internal-only PR | absent | internal only |

An inner join would hide both kinds of discrepancy.

---

## NULL and Join Equality

SQL's treatment of `NULL` is important for join behavior.

The expression:

`NULL = NULL`

does not evaluate to `TRUE`.

It evaluates to the SQL three-valued-logic result `UNKNOWN`.

Therefore, an ordinary equality join does not match one `NULL` key to another `NULL` key.

The Python implementation explicitly reproduces this behavior with `sql_equals`.

The JavaScript implementation also treats `null` as non-matching for ordinary equality joins.

This distinction matters when missing identifiers occur in imported or incomplete datasets.

A developer should not assume that two missing keys represent the same logical entity.

---

## The ON Predicate and WHERE Filtering

Outer joins become particularly subtle when conditions are placed in `ON` versus `WHERE`.

Consider a left join between pull requests and reviews.

A query can first join all reviews and then apply:

`WHERE rv.state = 'APPROVED'`

This removes rows where `rv.state` is `NULL`, because the condition is not true for the unmatched row.

The practical result is that the outer join loses the preservation effect for that condition.

A different query can place the restriction in the join predicate:

`ON rv.pull_request_id = p.pull_request_id AND rv.state = 'APPROVED'`

Now the join searches specifically for approved reviews while still preserving pull requests that have no approved review.

The Python and JavaScript implementations both demonstrate this distinction explicitly.

The difference is not cosmetic. It changes the population returned by the query.

---

## Composite Joins

A single column is not always sufficient to identify a relationship.

The SQL implementation uses:

`repository_id + branch_name`

as a composite logical key for external branch reconciliation.

The join condition therefore requires both values to match.

Matching only `repository_id` could associate the external `main` branch with every branch belonging to that repository, which would produce incorrect multiplicity.

Composite joins are appropriate when the natural identity of an entity consists of multiple attributes.

The Python and JavaScript examples also demonstrate composite matching through predicates.

---

## Join Multiplicity

Joining two one-to-many relationships can multiply rows.

Suppose a pull request has:

- 2 reviews
- 3 status checks

A direct join between the pull request, reviews, and status checks can produce up to:

`2 × 3 = 6`

joined rows for that pull request.

This does not mean there are six reviews or six status checks. It means the relational combination contains six review/check pairings.

The SQL implementation therefore uses `COUNT(DISTINCT ...)` when counting distinct reviews and checks after joining both relations.

This is a critical reporting consideration.

Incorrect aggregation after multi-table joins can silently inflate metrics.

---

## Python Implementation

The Python program provides two equality-join implementations.

### Nested-loop implementation

`nested_loop_join()` compares each left row with each right row.

Its conceptual complexity is:

`O(L × R)`

where `L` is the number of left rows and `R` is the number of right rows.

This implementation is useful because its control flow directly represents the logical definition of an equality join.

It also makes duplicate matching behavior easy to observe.

### Indexed implementation

`indexed_join()` builds a dictionary-based index for the right relation.

A single key maps to a list of right-side rows rather than one row. This preserves one-to-many relationships.

The approximate average-case model is:

`O(L + R + M)`

where `M` is the number of output matches.

The implementation also records which right-side rows matched so that `RIGHT` and `FULL` joins can append unmatched right-side records.

### General predicates

`join_with_predicate()` supports conditions more expressive than a single key.

The composite-key example uses both department and region.

This reflects the fact that SQL's `ON` clause can contain multiple conditions and expressions.

### Python-specific edge handling

The script explicitly handles:

- invalid join types
- missing join keys
- invalid row structures
- `None` values
- duplicate keys
- composite conditions
- post-join filtering
- unmatched outer-join rows
- performance differences between nested-loop and indexed approaches

---

## JavaScript Implementation

The JavaScript implementation uses `Map` as a hash index.

The important design choice is that each key maps to an array of rows.

A structure equivalent to:

`Map<key, row[]>`

is required because multiple records can share the same join key.

The event-driven section models a repository environment where repositories, pull requests, reviews, and policies arrive as separate events.

State is held in JavaScript `Map` instances, then converted into relations for join processing.

This represents a useful application pattern: operational systems may receive related records asynchronously, while reporting logic still needs to combine those entities according to explicit relationships.

The JavaScript implementation also demonstrates:

- predicate-based joins
- event-driven state accumulation
- `null` handling
- composite predicates
- `ON`-style versus post-join filtering
- error handling for invalid join requests

The implementation does not require an npm package.

---

## C++ Case Study

The C++ program implements a repository-governance data integration engine.

Its domain contains:

`Repository`

`PullRequest`

`Review`

`StatusCheck`

`BranchPolicy`

The join pipeline starts with repositories and pull requests, then enriches the result with reviews, status checks, and branch policies.

### Data structures

`std::unordered_map` provides hash-based lookup by join key.

Each key maps to a `std::vector<size_t>` because repository-to-pull-request and pull-request-to-review relationships can be one-to-many.

`std::unordered_set` records which right-side rows have matched. That is required to construct right and full outer joins correctly.

`std::optional` represents an unmatched side of an outer join.

For example, a governance row can contain a repository but no review:

`optional<Review> = empty`

This is preferable to manufacturing a fake review object.

### Merge eligibility

The case study also connects joined data to a realistic governance decision.

A pull request is blocked when:

- no branch-protection policy exists
- the pull request is still a draft
- the required number of approvals has not been reached
- required CI checks are missing
- a required CI check has failed

The join engine supplies the related information, while the merge-eligibility function evaluates policy.

This keeps relational combination separate from business-policy evaluation.

### Performance

The hash-indexed approach avoids scanning the complete right relation for every left row.

A nested-loop strategy may require `O(L × R)` comparisons.

A hash-based equality join generally approaches `O(L + R + M)`, subject to hash behavior and output size.

The output size itself can dominate execution time when a many-to-many relationship produces a large number of matches.

---

## Java Enterprise Model

The Java program models the same domain with immutable records and explicit services.

The principal domain types are:

- `Repository`
- `PullRequest`
- `Review`
- `StatusCheck`
- `BranchProtectionPolicy`

`JoinService` owns join behavior rather than mixing relational logic into the domain records.

`MergeEligibilityService` evaluates whether a pull request satisfies the branch policy.

### Explicit state representation

`ReviewState` is an enum containing:

`APPROVED`

`CHANGES_REQUESTED`

`COMMENTED`

This prevents arbitrary review-state strings from being used throughout the business logic.

`JoinType` provides the four requested join modes as an explicit domain value.

### Optional unmatched data

Java's `Optional` is used in joined records.

For an unmatched left join, a row may contain:

`Optional<Repository>` with a value

and:

`Optional<Review>` empty.

This makes the missing relationship explicit.

### Policy validation

`BranchProtectionPolicy` validates its approval requirement during construction.

The join service also rejects duplicate policies for a repository because the domain model treats the active policy as one-per-repository.

The merge-eligibility service counts distinct approvers rather than blindly counting review rows. This avoids treating multiple approval records from the same reviewer as multiple independent approvals.

---

## SQL Relational Model

The PostgreSQL schema represents the domain through foreign keys.

The main relationships are:

`repositories -> branches`

`repositories -> pull_requests`

`developers -> reviewers`

`pull_requests -> commits`

`pull_requests -> reviews`

`reviews -> review_comments`

`pull_requests -> status_checks`

`branches -> branch_protection_policies`

Foreign keys prevent invalid production relationships.

For example, a review cannot reference a nonexistent pull request.

That is why the SQL demonstration uses `external_review_audit` as a temporary reconciliation table when an intentionally orphaned external record is needed.

---

## SQL Constraints

The schema uses constraints for rules that belong at the database layer.

Primary keys prevent duplicate entity identifiers.

Unique constraints enforce values such as:

`repositories.repository_name`

`developers.username`

`branches(repository_id, branch_name)`

`status_checks(pull_request_id, check_name)`

Check constraints restrict controlled state values such as pull-request state and review state.

Foreign keys enforce parent-child relationships.

The branch-protection table also has a unique constraint on `branch_id`, representing one active policy per protected branch in this model.

---

## SQL Indexes

The script indexes frequently joined foreign-key columns.

Examples include:

`pull_requests(repository_id)`

`reviews(pull_request_id)`

`status_checks(pull_request_id)`

`commits(pull_request_id)`

`branch_protection_policies(repository_id)`

These indexes can reduce the work required to locate matching child rows.

An index does not guarantee that PostgreSQL will use it. PostgreSQL chooses a plan based on statistics, cardinality estimates, available memory, predicates, relation size, and other cost considerations.

The script includes `EXPLAIN` so the selected execution plan can be inspected.

---

## Transactional Policy Configuration

The SQL implementation uses a transaction when configuring a branch-protection policy.

The policy is selected through the branch relation so that the policy is attached only to a branch satisfying the requested repository and branch name.

`ON CONFLICT` makes the operation idempotent for the branch key.

The transaction provides an atomic boundary around the policy update.

This is separate from join semantics: the join retrieves related information, while the transaction controls the integrity of a state-changing operation.

---

## Data Reconciliation

`FULL OUTER JOIN` is especially valuable when two systems represent related data but neither side can be assumed complete.

The external review-audit table intentionally contains:

- one matching review relationship
- one external-only relationship

The full join makes both visible.

This pattern is applicable to data migration validation, integration monitoring, audit reconciliation, and synchronization checks.

A reconciliation query should usually classify the rows rather than simply display them. The SQL examples use `CASE` to distinguish `MATCHED`, `INTERNAL_ONLY`, and `EXTERNAL_ONLY`.

---

## Common Mistakes

### Treating every join as one-to-one

A key may occur multiple times on either side. The result can therefore contain more rows than either input.

### Using INNER JOIN when missing data is meaningful

An inner join silently removes unmatched entities. This is dangerous for completeness reports where absence itself is important.

### Applying an outer-join filter in WHERE unintentionally

A condition such as `WHERE review.state = 'APPROVED'` can remove the `NULL` rows created by a left join.

### Ignoring NULL semantics

Two missing join keys do not match through ordinary SQL equality.

### Counting after a multiplied join

Joining multiple child relations can multiply combinations. Aggregations should use the intended grain and, where appropriate, `COUNT(DISTINCT ...)`.

### Assuming RIGHT JOIN adds unique capability

`RIGHT JOIN` can generally be rewritten as a `LEFT JOIN` with relation order reversed. Its main value is semantic readability when the preserved relation naturally appears on the right.

### Using FULL JOIN without classifying results

A full join is most useful for reconciliation when the result identifies which side contributed the unmatched row.

---

## Performance Considerations

The logical definition of a join is independent of the physical algorithm selected by the database engine.

For equality joins, common physical strategies include:

- nested-loop joins
- hash joins
- merge joins

A nested-loop strategy is often reasonable when one relation is small or an efficient indexed lookup exists.

A hash join can be effective for large equality joins because a hash structure can locate matching keys without comparing every possible pair.

A merge join can be effective when both inputs are appropriately ordered.

The Python, C++, and Java implementations use explicit hash-style indexes to expose the same performance idea at application level.

The SQL implementation delegates physical plan selection to PostgreSQL.

---

## Security and Data Integrity

Join correctness is also an integrity concern.

Foreign keys prevent an application from producing many forms of orphaned relational data.

Parameterized queries should be used when SQL is constructed from external input. The examples use static SQL because the purpose is relational behavior, not dynamic query construction.

Sensitive data should not be exposed merely because two tables can technically be joined. Access control should be applied to the underlying relations and to reporting views.

A full reconciliation report may expose records from systems that normally have separate access boundaries, so its permissions should be considered independently.

---

## Debugging Join Problems

When a join produces unexpected rows, inspect the relationship at its intended grain.

Useful questions include:

- Is the join key actually unique on either side?
- Are there duplicate keys?
- Can the key be `NULL`?
- Is the relationship one-to-one, one-to-many, or many-to-many?
- Is a condition in `ON` when it should be in `WHERE`, or vice versa?
- Is an outer join being unintentionally converted into an inner-like result by filtering?
- Are multiple child tables multiplying the output?
- Are different data types or normalization rules affecting equality?
- Does the query preserve the relation that the business report considers authoritative?

The most useful debugging technique is often to inspect a small joined dataset before applying aggregation.

---

## Distinguishing the Four Join Types

The essential distinction is the preserved side.

`INNER JOIN` preserves only successful relationships.

`LEFT JOIN` preserves the left relation.

`RIGHT JOIN` preserves the right relation.

`FULL OUTER JOIN` preserves both relations.

The choice should follow the question being answered rather than personal preference.

For example:

A report asking for "repositories that have pull requests" naturally fits an inner join.

A report asking for "all repositories and their pull-request activity" naturally fits a left join.

An audit asking for "every external review record, even when the internal PR is missing" can use a right join.

A reconciliation asking for "every internal and external record, including discrepancies on either side" naturally fits a full outer join.

---

## Relationship Between Join Semantics and Application Design

A join answers a relational question: which records belong together under a specified condition?

It does not by itself decide whether the resulting relationship is valid for a business operation.

The C++ and Java implementations therefore separate join processing from merge eligibility.

The joined data provides repository, pull-request, review, CI, and policy context.

The governance service then applies domain rules to that context.

This separation helps prevent a common architectural problem in which data retrieval, relationship resolution, and business policy become one large conditional procedure.

---

## Practical Implementation Map

| File | Primary technical perspective |
|---|---|
| Python | In-memory relational simulation, SQL-like NULL behavior, nested-loop and indexed joins |
| JavaScript | Hash-indexed joins, predicate joins, event-driven relation assembly |
| C++ | Repository-governance case study using hash indexes and `std::optional` |
| Java | Enterprise domain model with immutable records, explicit join services, and policy evaluation |
| SQL | PostgreSQL relational schema, constraints, indexes, outer joins, reconciliation, aggregation, and transactions |

The six implementations use the same core relational distinctions while emphasizing mechanisms that are natural to each technology.
