# Data Cleaning with Pandas

## Purpose

This project demonstrates data cleaning principles using repository-development workflow data as the domain. The central task is to transform inconsistent records containing Pull Requests, branches, reviews, approvals, status checks, conversations, and branch-protection attributes into validated records suitable for analysis and workflow evaluation.

The implementations intentionally distinguish data quality operations from repository governance concepts.

A Pull Request is the proposed-change workflow. Code Review evaluates the proposed changes. Approvals represent review decisions. Branch Protection enforces repository-level conditions before merging.

The cleaning pipeline does not treat these mechanisms as interchangeable.

## Domain Model

The workflow represented by the examples is:

`Repository`
→ `Branches`
→ `Commits`
→ `Pull Requests`
→ `Reviews`
→ `Review Comments`
→ `Conversations`
→ `Status Checks`
→ `Branch Protection Policies`
→ `Approval Requirements`
→ `Merge Eligibility`
→ `Merge`

The source records contain common data-quality problems:

- inconsistent capitalization
- leading and trailing whitespace
- duplicated Pull Request records
- missing reviewer information
- missing policy flags
- malformed repository names
- invalid review states
- inconsistent boolean representations
- inconsistent branch references

Cleaning must correct representational inconsistencies without silently converting an invalid business decision into a valid one.

## Pull Request Lifecycle

A Pull Request represents a proposed set of changes from a source branch toward a target branch.

A simplified lifecycle is:

`Draft`
→ `Open`
→ `Review`
→ `Approved`
→ `Merge Eligible`
→ `Merged`

Other paths include:

`Open`
→ `Changes Requested`
→ `Open`

and:

`Open`
→ `Closed`

A Pull Request record describes the proposal and its current workflow state. It does not itself represent a review decision or branch-protection policy.

The source branch contains the proposed changes. The target branch represents the branch into which those changes may eventually be merged. These are distinct pieces of state.

The Python, JavaScript, C++17, and Java 17 implementations normalize source and target branch names so values such as `MAIN`, `main`, and `refs/heads/main` can be treated consistently.

## Pull Request Mechanics

The cleaned domain records preserve:

| Field | Meaning |
|---|---|
| `repository` | Repository containing the Pull Request |
| `source_branch` | Branch containing proposed changes |
| `target_branch` | Branch receiving the changes |
| `review_state` | Current Pull Request review workflow state |
| `approval` | Review decision represented in the source data |
| `status_check` | Automated validation result |
| `draft` | Whether the Pull Request is still a draft |
| `conversation_resolved` | Whether required discussions are resolved |
| `merge_eligible` | Result of the implemented eligibility policy |

A changeset is associated with commits on the source branch. Synchronizing the source branch changes the proposed changeset while the Pull Request remains the same workflow object.

A Pull Request can be reopened after being closed when repository workflow rules permit it. A closed Pull Request is not equivalent to a rejected review.

Merge strategies represented conceptually by the PostgreSQL model are:

| Strategy | Main behavior |
|---|---|
| Merge commit | Preserves the branch history and creates a merge commit |
| Squash | Combines the proposed commits into a consolidated commit |
| Rebase | Replays commits onto the target branch history |

Merge conflicts occur when the proposed changes cannot be applied cleanly to the current target-branch state. Cleaning branch names does not resolve conflicts. Conflict resolution is a separate repository operation.

## Code Review

Code Review evaluates the proposed changes in a Pull Request.

A review can contain:

- inline comments
- general review comments
- requested changes
- approval decisions
- dismissed decisions
- resolved or unresolved discussions

The PostgreSQL model separates `reviews` from `pull_requests` and separates `review_comments` from `reviews`.

This distinction prevents a review comment from being interpreted as the Pull Request itself.

A review workflow can be represented as:

`Proposed Changes`
→ `Reviewer Inspection`
→ `Comments`
→ `Requested Changes or Approval`
→ `Resolution`
→ `Eligibility Evaluation`

Review quality depends on scope, correctness, security implications, test coverage, maintainability, and whether the reviewer has sufficient context.

Common review-related failure modes include:

- approving changes without examining the relevant files
- leaving important conversations unresolved
- treating an automated status check as human review
- allowing stale decisions to represent the current changes
- reviewing generated or unrelated changes instead of the intended changeset

## Approvals

An approval is a review decision.

It answers a narrower question than branch protection:

> Has an eligible reviewer approved the proposed changes?

The data-cleaning implementations represent approval states separately from review states.

Examples include:

- `approved`
- `pending`
- `rejected`
- `dismissed`
- `not_required`

An approval should not automatically imply merge eligibility.

A repository may require one or more approvals, and an approval can become stale or be dismissed when the relevant changes change.

The PostgreSQL model stores approval requirements separately from individual reviews. This permits a repository to require a minimum number of approvals without embedding that requirement into every review record.

## Branch Protection

Branch Protection represents repository-level enforcement.

A protected branch can impose conditions such as:

- required reviews
- required status checks
- restricted direct pushes
- restricted force pushes
- restricted branch deletion
- required resolved conversations
- linear-history requirements
- merge restrictions
- administrator bypass rules

The PostgreSQL table `branch_protection_policies` stores these rules independently from Pull Requests and reviews.

This is important because a review approval is a decision, while branch protection is an enforcement policy.

The relationship is:

`Pull Request`
→ proposes changes

`Code Review`
→ evaluates changes

`Approval`
→ records a review decision

`Branch Protection`
→ determines repository-level conditions

`Merge Eligibility`
→ evaluates whether all required conditions are satisfied

## Data Cleaning Workflow

The source data passes through several stages:

`Raw Records`
→ `Normalization`
→ `Validation`
→ `Duplicate Detection`
→ `Missing-Value Handling`
→ `Policy Evaluation`
→ `Clean Records`

### Normalization

Normalization changes representation without changing intended meaning.

Examples include:

- trimming whitespace from reviewer names
- converting branch names to lowercase
- removing the `refs/heads/` prefix
- converting review and approval values to consistent lowercase forms
- converting textual booleans such as `yes`, `no`, `true`, and `false`

For example:

`"  Priya Sharma "` becomes `Priya Sharma`.

`"refs/heads/MAIN"` becomes `main`.

### Validation

Validation rejects records that cannot safely participate in downstream processing.

A Pull Request record is rejected when required structural information is missing or when controlled values are invalid.

Examples include:

- missing repository
- invalid Pull Request identifier
- missing source branch
- missing target branch
- invalid review state
- invalid approval state
- invalid status-check state

Validation is deliberately different from imputation.

A missing policy flag can sometimes be safely derived from repository rules. A missing repository identifier cannot safely be invented.

### Duplicate Detection

Duplicate detection prevents the same logical workflow record from being counted multiple times.

The implementations construct a composite identity from fields such as:

- Pull Request identifier
- repository
- source branch
- target branch
- reviewer

The exact identity key should be selected according to the source system's semantics.

Duplicates are dangerous because they can inflate:

- approval counts
- reviewer counts
- Pull Request volumes
- status-check statistics
- merge-readiness metrics

### Missing Data

Missing values require field-specific treatment.

Some values can be derived from other attributes.

For example, a missing `required_review` value can be derived when the target branch is known to be `main`, `master`, or `production`.

A missing `draft` value can be inferred from an explicit `draft` review state.

A missing `conversation_resolved` value can be conservatively derived from a terminal review state in the sample workflow.

These transformations are domain rules, not generic missing-value replacement.

Replacing every missing value with an empty string would destroy semantic information.

## Pandas-Oriented Interpretation

The Python implementation uses standard Python structures to keep the example self-contained. The same pipeline maps directly to a Pandas workflow.

A typical Pandas representation would use one row per workflow record and columns such as:

| Column | Cleaning operation |
|---|---|
| `repository` | trim and validate |
| `source_branch` | normalize branch reference |
| `target_branch` | normalize branch reference |
| `reviewer` | trim and handle missing values |
| `review_state` | normalize controlled vocabulary |
| `approval` | normalize controlled vocabulary |
| `status_check` | normalize controlled vocabulary |
| `draft` | convert to boolean |
| `required_review` | derive from branch policy |
| `conversation_resolved` | validate or derive |
| `merge_eligible` | calculate from policy conditions |

The important Pandas principles are `isna()` for missing-data detection, `drop_duplicates()` for duplicate removal, `fillna()` for justified imputation, `astype()` for type normalization, and vectorized transformations for scalable processing.

A production Pandas pipeline should avoid applying unrestricted `fillna()` across every column because different fields have different semantics.

## Implementation Comparison

| Language | Primary perspective |
|---|---|
| Python | Structured cleaning pipeline with validation, normalization, imputation, and assertions |
| JavaScript | Event-driven cleaning pipeline using `EventEmitter`, `Set`, and immutable record construction |
| C++17 | Explicit governance and merge-eligibility engine using domain enums and STL containers |
| Java 17 | Enterprise-style model using records, interfaces, policies, immutable collections, and services |
| PostgreSQL | Relational workflow with constraints, indexes, views, aggregation, validation, and transactions |

## Python Implementation

The Python implementation uses:

- dataclasses for cleaning statistics
- enums for controlled review states
- dictionaries for flexible source records
- sets for duplicate detection
- explicit validation rules
- boolean normalization
- domain-specific missing-value handling
- assertions for executable validation

The `PullRequestCleaner` separates normalization, validation, duplicate removal, missing-value handling, and merge-eligibility evaluation.

This separation makes each stage testable and prevents a single transformation from silently performing unrelated operations.

## JavaScript Implementation

The JavaScript implementation uses an event-driven design.

`EventEmitter` reports:

- normalization completion
- validation results
- duplicate-removal results

`Set` provides efficient duplicate detection.

The implementation uses object spread to create cleaned records without mutating the original input objects.

This is useful when raw records must be retained for auditing while cleaned records are passed to downstream processing.

## C++17 Implementation

The C++17 program models workflow states with strongly typed enums.

This avoids representing states such as approval or review status as unrestricted strings.

The program uses:

- `struct` for domain records
- `enum class` for controlled values
- `std::vector` for records
- `std::unordered_set` for duplicate detection
- STL algorithms for normalization
- exceptions for invalid program-level assumptions

The implementation explicitly separates data-cleaning operations from merge-eligibility evaluation.

## Java 17 Implementation

The Java implementation uses immutable records for raw and cleaned data.

`CleaningPolicy` separates validation rules from the service performing the cleaning.

`ValidationPolicy` determines whether a record is structurally acceptable.

`GovernanceService` performs:

1. validation
2. normalization
3. duplicate detection
4. missing-value derivation
5. merge-eligibility evaluation

This design supports enterprise applications where policy logic may evolve independently from data-processing infrastructure.

## PostgreSQL Implementation

The SQL implementation models the workflow relationally.

Important tables include:

- `repositories`
- `branches`
- `commits`
- `pull_requests`
- `reviewers`
- `reviews`
- `review_comments`
- `status_checks`
- `branch_protection_policies`
- `approval_requirements`
- `merge_events`

Foreign keys preserve relationships between these entities.

Check constraints restrict controlled state values.

Unique constraints prevent duplicate repository, branch, reviewer, status-check, and policy records.

Indexes support common workflow queries involving repositories, target branches, reviews, status checks, comments, and commit history.

The `cleaned_pull_request_records` view performs normalized reporting across the workflow tables.

## Relational Integrity

Relational constraints provide a different form of data quality control from application-level cleaning.

Application cleaning can normalize:

`" refs/heads/MAIN "` → `main`

A database constraint can prevent an invalid review state from being stored at all.

The distinction is:

| Mechanism | Primary purpose |
|---|---|
| Normalization | Consistent representation |
| Validation | Detect invalid records |
| Deduplication | Remove repeated logical records |
| Imputation | Derive justified missing values |
| Foreign key | Preserve entity relationships |
| Check constraint | Restrict permitted values |
| Unique constraint | Prevent duplicate keys |
| Index | Improve retrieval performance |
| Trigger or transaction | Enforce or coordinate state changes |

## Merge Eligibility

The implementations treat merge eligibility as a derived state.

A simplified policy is:

`Approved Review`
AND
`Required Approval Present`
AND
`Status Checks Passed`
AND
`Required Conversations Resolved`

The resulting decision is not stored as an unquestioned source fact. It is calculated from the cleaned data and repository rules.

This prevents an approval from being treated as sufficient when branch protection requires additional conditions.

A Pull Request can therefore have:

`approval = approved`

while:

`merge_eligible = false`

For example, a failed status check can block the merge even when the reviewer has approved the changes.

## Edge Cases

Important edge cases include:

### Duplicate Pull Request records

Repeated records can inflate review statistics and must be identified using a domain-appropriate identity key.

### Missing reviewer

A missing reviewer should not automatically become an approval.

### Invalid controlled value

An unknown review state should be rejected instead of silently mapped to a valid state.

### Protected branch

A target branch such as `main` may require approvals and successful status checks.

### Failed status check

A Pull Request can be approved while still being ineligible for merging.

### Unresolved conversation

Required unresolved discussions can prevent merge eligibility.

### Missing policy attribute

Some policy attributes can be derived from branch protection rules. Others require explicit source-system information.

### Force-push permission

The examples default this permission to false because unrestricted force pushing can undermine auditability and branch-history integrity.

## Performance Considerations

For in-memory cleaning, duplicate detection with a hash set provides expected near-linear behavior.

For `n` records:

`Normalization: O(n)`

`Validation: O(n)`

`Duplicate detection: O(n)` expected with hash-based sets

`Missing-value derivation: O(n)`

The PostgreSQL implementation uses indexes on high-frequency join and filtering columns.

Large Pandas workloads should prefer vectorized operations over Python-level row iteration where practical.

For very large datasets, cleaning should be staged so that raw data is not duplicated unnecessarily in memory.

## Security Considerations

Data cleaning is also a security boundary when workflow data influences repository decisions.

Important controls include:

- validate controlled vocabulary values
- do not infer approvals from missing reviewer data
- default dangerous permissions to restrictive values
- preserve raw records for audit purposes
- prevent unauthorized direct pushes to protected branches
- restrict force pushes
- require status checks where appropriate
- distinguish human review from automated checks
- preserve review and merge history
- avoid treating untrusted text as executable SQL

The PostgreSQL implementation uses parameter-independent static SQL values and relational constraints rather than dynamically concatenating user-controlled SQL.

## Failure Handling

A robust pipeline should fail explicitly when data cannot be interpreted safely.

The source implementations reject structurally invalid records rather than producing misleading cleaned records.

A production workflow should also retain rejected records with a rejection reason.

A useful operational structure is:

`Raw Data`
→ `Accepted Records`
→ `Rejected Records`
→ `Cleaning Report`

The rejected-data stream is important for diagnosing upstream ingestion problems.

## Data Quality Rules

The examples enforce these core rules:

| Rule | Action |
|---|---|
| Repository is missing | Reject |
| Pull Request identifier is invalid | Reject |
| Source branch is missing | Reject |
| Target branch is missing | Reject |
| Review state is unknown | Reject |
| Approval state is unknown | Reject |
| Status-check state is unknown | Reject |
| Branch reference has `refs/heads/` | Normalize |
| Text contains surrounding whitespace | Trim |
| Duplicate logical record exists | Keep one record |
| Protected target branch has no explicit review requirement | Derive required review |
| Missing draft flag | Derive from review state |
| Missing force-push policy | Use restrictive default |
| Failed status check | Block merge eligibility |
| Unresolved required conversation | Block merge eligibility |

## Practical Distinctions

The most important conceptual distinctions are:

| Concept | Primary question |
|---|---|
| Pull Request | What changes are being proposed? |
| Code Review | What did reviewers determine about those changes? |
| Approval | Did an eligible reviewer approve the changes? |
| Branch Protection | What repository-level conditions must be satisfied? |
| Status Check | Did an automated validation process pass? |
| Merge Eligibility | Are all required conditions currently satisfied? |
| Merge | Was the proposed change actually integrated? |

These concepts interact, but they should remain separate in both data models and cleaning pipelines.

## Limitations

The examples use a simplified repository workflow model.

They do not attempt to reproduce every feature of a production Git hosting platform, including:

- organization-level policy inheritance
- CODEOWNERS-style reviewer assignment
- stale-review dismissal based on exact changed-file sets
- commit ancestry calculations
- real merge-conflict detection
- signed commits
- deployment environments
- administrator bypass auditing
- platform-specific webhook semantics

The sample data is deliberately small enough to make the cleaning decisions visible.

A production Pandas pipeline would normally include schema validation, typed columns, structured rejection reports, profiling metrics, automated tests, and persistent audit records.

## Educational Focus

The implementations demonstrate that data cleaning is not simply the replacement of missing values.

A reliable cleaning workflow requires:

`Representation`
→ `Validation`
→ `Integrity`
→ `Transformation`
→ `Derived State`
→ `Quality Verification`

The repository-development domain provides a useful example because inaccurate cleaning can change the meaning of approval, review, status checks, or merge eligibility.

The central engineering principle is to clean representation while preserving domain semantics.
