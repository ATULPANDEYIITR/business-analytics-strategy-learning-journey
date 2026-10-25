# Dashboard Design: Information Hierarchy and Dashboard Architecture

## Scope

This project models dashboard design through a repository-governance scenario. The dashboard is not treated as a collection of decorative charts. It is an information system that converts Pull Request workflow state, code-review decisions, approval status, automated checks, and branch-protection rules into a hierarchy of operational information.

The central design relationship is:

Repository  
→ Branches  
→ Commits  
→ Pull Requests  
→ Reviews  
→ Review Comments  
→ Conversations  
→ Status Checks  
→ Branch Protection  
→ Approval Requirements  
→ Merge Eligibility  
→ Merge

The four governance concepts remain distinct:

| Area | Primary purpose | Dashboard representation |
|---|---|---|
| Pull Requests | Propose and manage changes | Work items, lifecycle state, source and target branches |
| Code Review | Evaluate proposed changes | Review decisions, comments, discussions, unresolved conversations |
| Approvals | Express authorized review decisions | Eligible approval count and approval requirements |
| Branch Protection | Enforce repository-level conditions | Required checks, review thresholds, push restrictions, merge rules |

## Information Hierarchy

A useful governance dashboard places information according to decision importance.

    Repository Governance
    |
    +-- Critical state
    |   +-- Mergeable Pull Requests
    |   +-- Blocked Pull Requests
    |   +-- Failing Required Checks
    |   +-- Unresolved Conversations
    |
    +-- Workflow state
    |   +-- Open Pull Requests
    |   +-- Draft Pull Requests
    |   +-- Closed Pull Requests
    |   +-- Merged Pull Requests
    |
    +-- Review state
    |   +-- Eligible approvals
    |   +-- Requested changes
    |   +-- Reviewer participation
    |
    +-- Repository policy
    |   +-- Protected branches
    |   +-- Required reviews
    |   +-- Required checks
    |   +-- Direct-push restrictions
    |   +-- Force-push restrictions
    |
    +-- Detailed records
        +-- Commits
        +-- Inline comments
        +-- Conversations
        +-- Individual status checks

The top level answers the operational question first: which changes can be merged and which changes are blocked?

Lower levels explain why a Pull Request has that state. This prevents a dashboard from presenting dozens of equally prominent metrics without an information hierarchy.

## Dashboard Architecture

The implementations separate domain state from presentation.

    Source Data
        |
        v
    Domain Model
        |
        +--> Pull Request Lifecycle
        |
        +--> Review Decisions
        |
        +--> Approval Evaluation
        |
        +--> Status Checks
        |
        +--> Branch Protection
        |
        v
    Merge Eligibility
        |
        v
    Dashboard Metrics
        |
        +--> Executive State
        +--> Operational Details
        +--> Policy Details

This architecture prevents visual components from independently reconstructing governance rules. Merge eligibility is calculated from the domain model and then exposed as dashboard information.

## Pull Request Lifecycle and Mechanics

A Pull Request represents a proposed change from a source branch to a target branch.

The Python implementation models the source branch, target branch, commits, reviews, comments, checks, merge strategy, and lifecycle state.

The important states are:

| State | Meaning |
|---|---|
| Draft | Work is visible but is not ready for normal merge evaluation |
| Open | The proposed change is active and can enter the merge workflow |
| Closed | The Pull Request is closed without being merged |
| Merged | The proposed change has entered the target branch |

A Pull Request can be reopened after being closed when the repository workflow permits it. Reopening returns the proposal to an active workflow state rather than creating a new changeset automatically.

Base-branch synchronization matters because the target branch can change while a Pull Request remains open. A dashboard should distinguish the Pull Request's proposed changes from the current target-branch state.

Merge conflicts are another distinct condition. A conflict indicates that the source and target histories cannot be combined automatically under the selected merge operation. It is not equivalent to a failed review or failed status check.

## Changesets and Commits

Commits represent the concrete changes behind a Pull Request.

The PostgreSQL model stores commits independently and associates them with Pull Requests through `pull_request_commits`. This allows one commit to remain a repository object while the Pull Request defines its workflow context.

The dashboard should show commit count and recent changes as supporting information rather than allowing commit volume to dominate the primary hierarchy.

A large number of commits does not inherently mean poor review quality. Conversely, a small number of commits does not guarantee a safe change.

## Code Review

Code Review evaluates the proposed changes.

The review model distinguishes:

- Comments
- Approvals
- Requested changes
- Dismissed reviews
- Review discussions
- Resolved conversations

A review comment is evidence of discussion. It is not automatically an approval or a rejection.

A requested-changes decision is stronger than a general discussion comment because it represents an explicit reviewer decision.

The dashboard therefore separates review activity from merge eligibility.

### Review Quality

A useful review dashboard should expose meaningful signals such as:

| Signal | Interpretation |
|---|---|
| Active reviewers | People participating in evaluation |
| Requested changes | Explicit review objections |
| Unresolved conversations | Issues still requiring attention |
| Approvals | Explicit positive review decisions |
| Review scope | Whether reviewers are examining the intended change |

Review volume alone is a weak quality indicator. Ten superficial comments should not automatically be treated as better review than two substantive findings.

## Approval Semantics

An approval represents a review decision that can contribute to merge eligibility when the reviewer satisfies the repository's eligibility rules.

The model uses distinct concepts for:

1. Reviewer identity
2. Reviewer eligibility
3. Review state
4. Required approval count
5. Active approval state

An approval can become stale or ineffective when repository conditions change. A later changes-requested decision from the same reviewer can invalidate the earlier approval in the simplified models.

The Python, C++, Java, and SQL implementations therefore avoid treating every historical approval record as an automatically active approval.

### Approval Eligibility

A reviewer can be ineligible even when the reviewer submitted an approval. Possible policy reasons include:

- The reviewer is outside the permitted reviewer set.
- The review was dismissed.
- A later review requested changes.
- The repository policy requires a different review count.
- Branch protection rules changed after the review.

The dashboard should display active eligible approvals rather than only the total historical number of approval records.

## Branch Protection

Branch Protection operates at the repository policy level.

It determines conditions that must be satisfied before a Pull Request can be merged into a protected branch.

The project models:

- Required reviews
- Required status checks
- Conversation resolution
- Linear-history requirements
- Direct-push restrictions
- Force-push restrictions
- Branch-deletion restrictions

These settings are deliberately separated from review data.

A reviewer cannot satisfy a branch-protection rule simply because a comment exists. A status check cannot replace a required human approval unless the repository policy explicitly defines such behavior.

## Status Checks

Automated status checks provide machine-generated evidence about a proposed change.

Examples in the implementation include:

- `unit-tests`
- `security-scan`
- `performance`

Required and optional checks are separated.

A pending optional check does not necessarily block a merge. A failing required check does.

The PostgreSQL view calculates required-check completion independently from review approval.

This separation is important for dashboard architecture because it prevents a single generic "status" value from hiding the reason a Pull Request is blocked.

## Merge Eligibility

Merge eligibility is a derived state.

It is not simply another review state.

A simplified decision flow is:

    Pull Request open?
            |
           yes
            v
    Required eligible approvals?
            |
           yes
            v
    Required status checks passing?
            |
           yes
            v
    Required conversations resolved?
            |
           yes
            v
    Merge strategy compatible with policy?
            |
           yes
            v
    MERGE ELIGIBLE

A failure at any required stage creates an explanation for the blocked state.

This makes the dashboard actionable. Instead of displaying only `Blocked`, the user can see whether the blocking condition is an approval shortage, unresolved discussion, failed security scan, or merge-policy conflict.

## Python Implementation

The Python implementation uses dataclasses and enums to model repository governance.

Important structures include:

- `Repository`
- `Branch`
- `Commit`
- `PullRequest`
- `Review`
- `ReviewComment`
- `StatusCheck`
- `BranchProtection`
- `RepositoryGovernance`

`RepositoryGovernance.evaluate_merge()` calculates merge eligibility and returns explicit blocking reasons.

`dashboard_metrics()` converts detailed domain state into high-level dashboard metrics.

The implementation also validates branch references, protected-branch references, approval requirements, and Pull Request source and target branches.

The design keeps dashboard aggregation separate from merge-policy evaluation.

## JavaScript Implementation

The JavaScript implementation uses objects, classes, `Map`, `Set`, asynchronous processing, and explicit validation.

`RepositoryDashboard` manages:

- Repository validation
- Eligible reviewers
- Active approvals
- Unresolved conversations
- Merge eligibility
- Dashboard metrics
- Asynchronous status-check refresh

The asynchronous `refreshStatusChecks()` method represents CI and security systems that report results independently of the dashboard.

The implementation does not execute arbitrary commands received through status-check data. Check names and states are treated as structured data, which reduces the risk of command injection through dashboard inputs.

## C++17 Implementation

The C++ implementation uses a repository governance engine as a coherent technical case study.

The domain uses:

- Enums for workflow states
- Structs for domain records
- `std::map` for indexed repository objects
- `std::set` for reviewer and policy membership
- `std::vector` for ordered changes and reviews
- Standard algorithms for aggregation
- Exceptions for invalid repository state

`GovernanceEngine` calculates active approvals, merge eligibility, and dashboard metrics.

The approval calculation uses reviewer identity as the uniqueness boundary so that duplicate approval records do not inflate the approval count.

The implementation returns a nonzero process status when the sample Pull Request is blocked. This makes the program suitable for automation and monitoring scenarios.

## Java 17 Implementation

The Java implementation uses an enterprise-oriented domain model.

Records are used for immutable value objects such as:

- `Commit`
- `Review`
- `ReviewComment`
- `StatusCheck`
- `Branch`
- `BranchProtectionPolicy`
- `MergeDecision`
- `DashboardMetrics`

The mutable workflow object is represented by `PullRequest`, while policy evaluation is isolated in `MergeEligibilityService`.

`DashboardService` is responsible for translating domain information into dashboard metrics.

This separation provides a useful enterprise architecture:

    Repository
        |
        v
    DashboardService
        |
        +--> MergeEligibilityService
        |
        +--> DashboardMetrics

The design prevents presentation-oriented aggregation from becoming the owner of repository governance rules.

## PostgreSQL Implementation

The PostgreSQL implementation provides the relational representation of the complete workflow.

The principal entities are:

| Table | Responsibility |
|---|---|
| `repositories` | Repository identity |
| `users` | Reviewer and author identity |
| `branches` | Source and target branch state |
| `commits` | Repository changesets |
| `pull_requests` | Proposed changes |
| `pull_request_commits` | Pull Request changeset membership |
| `reviews` | Review decisions |
| `review_comments` | Review discussions |
| `status_checks` | Automated validation |
| `branch_protection_policies` | Repository enforcement rules |
| `required_status_checks` | Required automated checks |
| `eligible_reviewers` | Authorized reviewers |
| `merge_events` | Completed merge records |

The `pull_request_dashboard` view is the main relational dashboard surface.

It combines workflow state, approval state, conversation state, status-check state, and branch protection into a single reporting layer.

## Database-Level Enforcement

The PostgreSQL trigger `enforce_protected_branch_policy()` prevents a Pull Request from being transitioned to `merged` when required governance conditions are not satisfied.

This is important because dashboard calculations alone are not sufficient security controls.

A dashboard may report that a merge is eligible, but database-level enforcement provides a second control boundary for the represented workflow.

The trigger evaluates:

- Eligible approvals
- Later changes-requested reviews
- Unresolved conversations
- Required status checks
- Linear-history requirements

The policy is therefore enforced independently of the presentation layer.

## Transactions and Failure Handling

The SQL workflow includes a transaction and savepoint around an intentionally blocked merge.

The first merge attempt encounters an unresolved review conversation. The exception is captured and the transaction returns to a safe savepoint.

After the conversation is resolved, the Pull Request can satisfy the modeled governance rules and be merged.

This demonstrates an important distinction:

    Dashboard state
          |
          v
    Eligibility decision
          |
          v
    Transactional state transition
          |
          v
    Persisted merge event

The dashboard is an observation and decision-support layer. The transaction is the state-changing layer.

## Dashboard States

A practical dashboard should use explicit states rather than ambiguous colors or generic status labels.

| Dashboard state | Meaning |
|---|---|
| Ready | Required merge conditions are satisfied |
| Blocked | One or more mandatory conditions fail |
| Draft | Work is not yet in the normal merge-ready workflow |
| Reviewing | Review activity is still in progress |
| Checks failing | Required automation has failed |
| Discussion pending | Required review conversations remain unresolved |
| Closed | Proposal was closed without merging |
| Merged | Change completed the workflow |

The state should be accompanied by a reason. A user should not have to inspect every underlying record to understand why a Pull Request is blocked.

## Visual Information Architecture

The model supports a dashboard layout such as:

    +-------------------------------------------------------------+
    | REPOSITORY GOVERNANCE                                      |
    +----------------------+----------------------+---------------+
    | Mergeable PRs        | Blocked PRs          | Draft PRs     |
    | 12                   | 5                    | 3             |
    +----------------------+----------------------+---------------+
    | Required Checks      | Approvals            | Conversations |
    | 2 failing            | 14 / 16              | 4 unresolved  |
    +----------------------+----------------------+---------------+
    | Pull Request Work Queue                                    |
    | #104  feature/x       2 approvals   checks pass   READY     |
    | #103  feature/y       1 approval    check fail    BLOCKED   |
    | #102  feature/z       draft          --            DRAFT     |
    +-------------------------------------------------------------+
    | Branch Protection                                          |
    | main: 2 reviews | tests | security | linear history        |
    +-------------------------------------------------------------+

The upper region provides high-level operational state.

The middle region explains the major causes.

The lower region provides records and policy details.

This is an information hierarchy rather than a flat collection of charts.

## Metric Design

The implementations deliberately use counts that correspond to operational decisions.

### Open Pull Requests

Measures active workflow volume.

### Draft Pull Requests

Separates unfinished proposals from review-ready proposals.

### Mergeable Pull Requests

Measures work that has passed the modeled governance conditions.

### Blocked Pull Requests

Identifies active proposals requiring intervention.

### Unresolved Conversations

Provides a direct review-workload signal.

### Eligible Approvals

Measures approvals that can actually contribute to the current policy.

These metrics should not be interpreted as independent business indicators. They describe different dimensions of the same repository workflow.

## Review-Related Failure Modes

Common failure conditions represented by the model include:

- Fewer eligible approvals than required
- Approval from an ineligible reviewer
- Later changes requested after approval
- Unresolved conversations
- Failing required status checks
- Pending required status checks
- Attempting to merge a draft
- Missing branch protection configuration
- Merge strategy incompatible with linear-history requirements
- Invalid source or target branch
- Invalid repository references

These conditions are represented as explicit states rather than silently converting them into a generic failure.

## Branch Protection Failure Modes

Branch protection is broader than approval enforcement.

Relevant controls include:

| Control | Effect |
|---|---|
| Required reviews | Requires a minimum number of eligible review decisions |
| Required status checks | Requires specified automation to pass |
| Conversation resolution | Prevents unresolved review discussions from being ignored |
| Linear history | Restricts merge strategies that introduce merge commits |
| Direct-push restriction | Keeps protected-branch changes inside controlled workflows |
| Force-push restriction | Protects existing branch history |
| Deletion restriction | Prevents accidental removal of protected branches |

Administrator or privileged bypass behavior should be modeled as a separate authorization path when required by a real repository implementation. It should not be silently equated with ordinary reviewer approval.

## Security Considerations

The dashboard should follow least-privilege principles.

Important controls include:

- Do not expose repository credentials.
- Do not expose secrets in dashboard logs.
- Validate branch and Pull Request identifiers.
- Treat status-check names as data.
- Enforce authorization separately from presentation.
- Do not allow dashboard state to bypass repository policy.
- Protect merge operations with transactional validation.
- Prevent unauthorized direct writes to protected branches.
- Distinguish historical review activity from currently effective approvals.

The JavaScript implementation demonstrates structured asynchronous status updates without executing arbitrary input.

The PostgreSQL trigger demonstrates database-side enforcement rather than trusting the dashboard interface.

## Performance Considerations

Dashboard queries should optimize for the information users repeatedly inspect.

The PostgreSQL implementation indexes:

- Pull Request target branch and state
- Review Pull Request and state
- Status-check Pull Request and state
- Unresolved comments

These indexes support common dashboard filters.

The dashboard view uses CTEs to aggregate approval, conversation, and check information before producing the final reporting surface.

For larger repositories, precomputed aggregates, materialized reporting views, incremental event processing, or dedicated analytics storage may be appropriate. The correct choice depends on update frequency, repository size, and acceptable reporting latency.

The application implementations use hash-based collections where membership checks are frequent. This makes reviewer eligibility and policy membership efficient without scanning complete lists for every comparison.

## Design Trade-offs

### Flat Dashboard Versus Hierarchical Dashboard

A flat dashboard exposes many metrics simultaneously but makes prioritization difficult.

A hierarchical dashboard places mergeability and blockers first, then provides explanations and detailed records.

### Client-Side Versus Server-Side Enforcement

Client-side checks provide immediate feedback.

Server-side enforcement provides a stronger control boundary.

The PostgreSQL trigger demonstrates why important merge rules should not depend solely on dashboard rendering logic.

### Historical Data Versus Active State

Historical review records are useful for auditability, but they should not automatically determine current merge eligibility.

The implementations therefore distinguish historical review events from active eligible approvals.

### Detailed Metrics Versus Information Overload

More metrics do not automatically produce better operational visibility.

The dashboard focuses on metrics that answer specific questions:

- What requires attention?
- What is blocked?
- Why is it blocked?
- Who must act?
- Which automated condition failed?
- Which repository policy applies?

## Relationship Between the Four Governance Areas

The four areas form a dependency chain without becoming interchangeable.

    Pull Request
        |
        | proposes changes
        v
    Code Review
        |
        | produces review decisions
        v
    Approvals
        |
        | contributes to policy satisfaction
        v
    Branch Protection
        |
        | enforces repository conditions
        v
    Merge Eligibility
        |
        v
    Merge

A Pull Request is the workflow container.

Code Review is the evaluation activity.

Approvals are explicit review decisions that may satisfy an approval requirement.

Branch Protection is the repository-level enforcement mechanism.

The final merge decision combines these distinct sources of state.

## Practical Dashboard Implications

A repository-governance dashboard should make the next operational action apparent.

If a Pull Request is blocked by missing approvals, the user needs an approval-related explanation.

If it is blocked by a failing security check, the dashboard should surface the failing check.

If it is blocked by unresolved conversations, the relevant discussion count should be visible.

If all conditions are satisfied, the dashboard should clearly indicate merge eligibility.

This produces a direct relationship between information hierarchy and operational workflow:

    Detect state
        ↓
    Explain cause
        ↓
    Identify responsible action
        ↓
    Re-evaluate policy
        ↓
    Permit or reject merge

The five implementations provide different engineering perspectives on the same architecture while keeping workflow, review, approval, branch-protection, and dashboard responsibilities distinct.
