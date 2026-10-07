/*
    SQL JOIN Laboratory
    PostgreSQL-compatible SQL

    The schema models repository-development data so that each join type has
    a distinct purpose:

      INNER JOIN
        Returns only entities having a matching relationship.

      LEFT JOIN
        Preserves every row from the left relation and exposes missing right
        records as NULL.

      RIGHT JOIN
        Preserves every row from the right relation. It is useful when the
        right relation is the business-priority side, although many teams
        rewrite RIGHT JOIN as LEFT JOIN by reversing table order.

      FULL OUTER JOIN
        Preserves unmatched rows from both relations and is particularly
        useful for reconciliation and data-quality auditing.

    The data model contains repositories, branches, pull requests, commits,
    reviewers, reviews, comments, status checks, and branch-protection
    policies.
*/

DROP SCHEMA IF EXISTS join_lab CASCADE;
CREATE SCHEMA join_lab;

SET search_path TO join_lab;

/* -------------------------------------------------------------------------
   Core entities
   ------------------------------------------------------------------------- */

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main'
);

CREATE TABLE developers (
    developer_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    author_id BIGINT NOT NULL
        REFERENCES developers(developer_id),
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    state TEXT NOT NULL
        CHECK (state IN ('OPEN', 'CLOSED', 'MERGED')),
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    commit_hash CHAR(40) NOT NULL UNIQUE,
    author_id BIGINT NOT NULL
        REFERENCES developers(developer_id),
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    developer_id BIGINT NOT NULL UNIQUE
        REFERENCES developers(developer_id),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    reviewer_id BIGINT NOT NULL
        REFERENCES reviewers(reviewer_id),
    state TEXT NOT NULL
        CHECK (
            state IN (
                'APPROVED',
                'CHANGES_REQUESTED',
                'COMMENTED',
                'DISMISSED'
            )
        ),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id),
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL CHECK (line_number > 0),
    body TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id),
    check_name TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('PENDING', 'PASSED', 'FAILED')),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id),
    branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    required_approvals INTEGER NOT NULL DEFAULT 0
        CHECK (required_approvals >= 0),
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT FALSE,
    require_status_checks BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (branch_id)
);

/* -------------------------------------------------------------------------
   Indexes

   Join columns receive indexes because the demonstration repeatedly relates
   child rows to their parent rows.
   ------------------------------------------------------------------------- */

CREATE INDEX idx_branches_repository
    ON branches(repository_id);

CREATE INDEX idx_pull_requests_repository
    ON pull_requests(repository_id);

CREATE INDEX idx_pull_requests_target_branch
    ON pull_requests(target_branch_id);

CREATE INDEX idx_commits_pull_request
    ON commits(pull_request_id);

CREATE INDEX idx_reviews_pull_request
    ON reviews(pull_request_id);

CREATE INDEX idx_review_comments_review
    ON review_comments(review_id);

CREATE INDEX idx_status_checks_pull_request
    ON status_checks(pull_request_id);

CREATE INDEX idx_policies_repository
    ON branch_protection_policies(repository_id);

/* -------------------------------------------------------------------------
   Sample data
   ------------------------------------------------------------------------- */

INSERT INTO repositories (repository_id, repository_name, default_branch)
VALUES
    (1, 'payments-api', 'main'),
    (2, 'identity-service', 'main'),
    (3, 'analytics-engine', 'main');

INSERT INTO developers (developer_id, username, display_name)
VALUES
    (1, 'asha', 'Asha'),
    (2, 'rahul', 'Rahul'),
    (3, 'maya', 'Maya'),
    (4, 'daniel', 'Daniel'),
    (5, 'reviewer_c', 'Reviewer C');

INSERT INTO branches (
    branch_id,
    repository_id,
    branch_name,
    is_protected
)
VALUES
    (1, 1, 'main', TRUE),
    (2, 1, 'feature/cache', FALSE),
    (3, 1, 'feature/tracing', FALSE),
    (4, 2, 'main', TRUE),
    (5, 2, 'security/headers', FALSE),
    (6, 3, 'main', TRUE),
    (7, 3, 'experiment/model', FALSE);

INSERT INTO pull_requests (
    pull_request_id,
    repository_id,
    author_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    is_draft
)
VALUES
    (
        101, 1, 1, 2, 1,
        'Improve API caching',
        'OPEN',
        FALSE
    ),
    (
        102, 1, 2, 3, 1,
        'Add distributed tracing',
        'OPEN',
        FALSE
    ),
    (
        103, 2, 3, 5, 4,
        'Add security headers',
        'OPEN',
        TRUE
    ),
    (
        104, 9, 4, 7, 6,
        'External repository record',
        'OPEN',
        FALSE
    );

/*
    The row for pull_request_id 104 intentionally cannot reference repository
    9 under the foreign key. The sample above therefore cannot be inserted
    exactly as written if referential integrity is active.

    The invalid-row scenario is demonstrated later through temporary audit
    tables rather than by violating the production schema.
*/

/* Remove the intentionally invalid demonstration row. */
DELETE FROM pull_requests
WHERE pull_request_id = 104;

/* Add an unmatched pull request in an existing repository instead. */
INSERT INTO branches (
    branch_id,
    repository_id,
    branch_name,
    is_protected
)
VALUES
    (8, 3, 'experiment/unused', FALSE);

INSERT INTO pull_requests (
    pull_request_id,
    repository_id,
    author_id,
    source_branch_id,
    target_branch_id,
    title,
    state,
    is_draft
)
VALUES
    (
        104, 3, 4, 8, 6,
        'Unreviewed analytics experiment',
        'OPEN',
        FALSE
    );

INSERT INTO commits (
    commit_id,
    pull_request_id,
    commit_hash,
    author_id
)
VALUES
    (
        1001, 101,
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        1
    ),
    (
        1002, 101,
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        2
    ),
    (
        1003, 102,
        'cccccccccccccccccccccccccccccccccccccccc',
        2
    );

INSERT INTO reviewers (
    reviewer_id,
    developer_id,
    active
)
VALUES
    (1, 2, TRUE),
    (2, 3, TRUE),
    (3, 4, TRUE),
    (4, 5, TRUE);

INSERT INTO reviews (
    review_id,
    pull_request_id,
    reviewer_id,
    state
)
VALUES
    (2001, 101, 1, 'APPROVED'),
    (2002, 101, 2, 'APPROVED'),
    (2003, 102, 1, 'CHANGES_REQUESTED'),
    (2004, 103, 2, 'APPROVED');

/*
    review_id 2005 intentionally references a nonexistent PR and therefore
    cannot be inserted because the foreign key correctly rejects orphan data.
    A separate audit table is used later to demonstrate FULL JOIN detection.
*/

INSERT INTO review_comments (
    comment_id,
    review_id,
    file_path,
    line_number,
    body,
    is_resolved
)
VALUES
    (
        3001,
        2003,
        'src/tracing.py',
        42,
        'The timeout needs explicit validation.',
        FALSE
    ),
    (
        3002,
        2002,
        'src/cache.py',
        17,
        'Cache invalidation is covered by the tests.',
        TRUE
    );

INSERT INTO status_checks (
    status_check_id,
    pull_request_id,
    check_name,
    status
)
VALUES
    (4001, 101, 'build', 'PASSED'),
    (4002, 101, 'test', 'PASSED'),
    (4003, 102, 'build', 'PASSED'),
    (4004, 102, 'test', 'FAILED'),
    (4005, 103, 'build', 'PASSED');

INSERT INTO branch_protection_policies (
    policy_id,
    repository_id,
    branch_id,
    required_approvals,
    require_conversation_resolution,
    require_status_checks,
    require_linear_history,
    allow_force_push,
    allow_branch_deletion
)
VALUES
    (5001, 1, 1, 2, TRUE, TRUE, TRUE, FALSE, FALSE),
    (5002, 2, 4, 1, TRUE, TRUE, TRUE, FALSE, FALSE);

/* -------------------------------------------------------------------------
   INNER JOIN

   INNER JOIN is appropriate when the report should contain only rows for
   which both relations have a matching key.
   ------------------------------------------------------------------------- */

SELECT
    r.repository_name,
    p.pull_request_id,
    p.title,
    p.state
FROM repositories AS r
INNER JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
ORDER BY r.repository_id, p.pull_request_id;

/* Developers who have actually submitted reviews. */
SELECT
    d.username,
    rv.review_id,
    rv.pull_request_id,
    rv.state
FROM developers AS d
INNER JOIN reviewers AS r
    ON r.developer_id = d.developer_id
INNER JOIN reviews AS rv
    ON rv.reviewer_id = r.reviewer_id
ORDER BY d.username, rv.review_id;

/* -------------------------------------------------------------------------
   LEFT JOIN

   LEFT JOIN is used when the left relation is authoritative for the report.
   An unmatched right side becomes NULL rather than removing the left row.
   ------------------------------------------------------------------------- */

SELECT
    r.repository_name,
    p.pull_request_id,
    p.title
FROM repositories AS r
LEFT JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
ORDER BY r.repository_id, p.pull_request_id;

/*
    Find repositories with no pull requests.

    The IS NULL predicate is applied after the LEFT JOIN to identify the
    unmatched right side.
*/
SELECT
    r.repository_id,
    r.repository_name
FROM repositories AS r
LEFT JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
WHERE p.pull_request_id IS NULL
ORDER BY r.repository_id;

/*
    Preserve every pull request while attaching its reviews.

    PR 104 has no review and remains visible.
*/
SELECT
    p.pull_request_id,
    p.title,
    rv.review_id,
    rv.state
FROM pull_requests AS p
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
ORDER BY p.pull_request_id, rv.review_id;

/* -------------------------------------------------------------------------
   RIGHT JOIN

   RIGHT JOIN preserves every row from the right-hand relation.

   This example treats reviews as the audit source. A review remains visible
   even if the corresponding pull request record is absent from the left side.
   With enforced foreign keys this should normally be impossible in production,
   which makes the same pattern useful when reconciling imported or external
   datasets.
   ------------------------------------------------------------------------- */

CREATE TEMP TABLE external_review_audit (
    review_id BIGINT PRIMARY KEY,
    pull_request_id BIGINT NOT NULL,
    reviewer_username TEXT NOT NULL,
    state TEXT NOT NULL
);

INSERT INTO external_review_audit (
    review_id,
    pull_request_id,
    reviewer_username,
    state
)
VALUES
    (9001, 101, 'reviewer-a', 'APPROVED'),
    (9002, 9999, 'legacy-reviewer', 'APPROVED');

SELECT
    p.pull_request_id,
    p.title,
    a.review_id,
    a.reviewer_username,
    a.state
FROM pull_requests AS p
RIGHT JOIN external_review_audit AS a
    ON a.pull_request_id = p.pull_request_id
ORDER BY a.review_id;

/*
    RIGHT JOIN can be expressed equivalently as a LEFT JOIN by reversing
    relation order. The two queries represent the same preserved side.
*/
SELECT
    p.pull_request_id,
    p.title,
    a.review_id,
    a.reviewer_username
FROM external_review_audit AS a
LEFT JOIN pull_requests AS p
    ON p.pull_request_id = a.pull_request_id
ORDER BY a.review_id;

/* -------------------------------------------------------------------------
   FULL OUTER JOIN

   FULL OUTER JOIN preserves unmatched rows on both sides.

   It is particularly useful for reconciliation because it exposes:
     - left-only records
     - matched records
     - right-only records
   ------------------------------------------------------------------------- */

SELECT
    p.pull_request_id,
    p.title,
    a.review_id,
    a.reviewer_username,
    CASE
        WHEN p.pull_request_id IS NULL THEN 'RIGHT_ONLY'
        WHEN a.review_id IS NULL THEN 'LEFT_ONLY'
        ELSE 'MATCHED'
    END AS reconciliation_status
FROM pull_requests AS p
FULL OUTER JOIN external_review_audit AS a
    ON a.pull_request_id = p.pull_request_id
ORDER BY
    COALESCE(p.pull_request_id, a.pull_request_id),
    a.review_id;

/* -------------------------------------------------------------------------
   JOIN predicates and WHERE predicates

   These two queries deliberately produce different semantics.
   ------------------------------------------------------------------------- */

/*
    Filtering the right table in WHERE after a LEFT JOIN removes rows for
    which the right side is NULL. The outer join therefore behaves like an
    INNER JOIN for this particular condition.
*/
SELECT
    p.pull_request_id,
    p.title,
    rv.state
FROM pull_requests AS p
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
WHERE rv.state = 'APPROVED'
ORDER BY p.pull_request_id;

/*
    Moving the review-state condition into ON preserves pull requests that do
    not have an approved review.
*/
SELECT
    p.pull_request_id,
    p.title,
    rv.state
FROM pull_requests AS p
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
   AND rv.state = 'APPROVED'
ORDER BY p.pull_request_id;

/* -------------------------------------------------------------------------
   Multi-table join

   The query follows a real governance relationship:

       repository
           |
           +-- pull request
                   |
                   +-- review
                   |
                   +-- status check
           |
           +-- protected branch policy
   ------------------------------------------------------------------------- */

SELECT
    r.repository_name,
    p.pull_request_id,
    p.title,
    COUNT(DISTINCT rv.review_id) AS review_count,
    COUNT(DISTINCT c.status_check_id) AS check_count,
    COUNT(DISTINCT CASE
        WHEN rv.state = 'APPROVED' THEN rv.review_id
    END) AS approval_count,
    BOOL_AND(
        c.status = 'PASSED'
    ) FILTER (
        WHERE c.status_check_id IS NOT NULL
    ) AS all_checks_passed,
    bp.required_approvals
FROM repositories AS r
LEFT JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
LEFT JOIN status_checks AS c
    ON c.pull_request_id = p.pull_request_id
LEFT JOIN branch_protection_policies AS bp
    ON bp.branch_id = p.target_branch_id
GROUP BY
    r.repository_name,
    p.pull_request_id,
    p.title,
    bp.required_approvals
ORDER BY
    r.repository_name,
    p.pull_request_id;

/* -------------------------------------------------------------------------
   Common Table Expression with join-based merge eligibility
   ------------------------------------------------------------------------- */

WITH approval_counts AS (
    SELECT
        p.pull_request_id,
        COUNT(DISTINCT rv.reviewer_id) FILTER (
            WHERE rv.state = 'APPROVED'
        ) AS approvals
    FROM pull_requests AS p
    LEFT JOIN reviews AS rv
        ON rv.pull_request_id = p.pull_request_id
    GROUP BY p.pull_request_id
),
check_results AS (
    SELECT
        p.pull_request_id,
        COUNT(c.status_check_id) AS check_count,
        COUNT(c.status_check_id) FILTER (
            WHERE c.status = 'PASSED'
        ) AS passed_count,
        COUNT(c.status_check_id) FILTER (
            WHERE c.status = 'FAILED'
        ) AS failed_count
    FROM pull_requests AS p
    LEFT JOIN status_checks AS c
        ON c.pull_request_id = p.pull_request_id
    GROUP BY p.pull_request_id
)
SELECT
    p.pull_request_id,
    p.title,
    COALESCE(a.approvals, 0) AS approvals,
    COALESCE(cr.check_count, 0) AS check_count,
    COALESCE(cr.failed_count, 0) AS failed_checks,
    CASE
        WHEN p.is_draft THEN FALSE
        WHEN bp.policy_id IS NULL THEN FALSE
        WHEN COALESCE(a.approvals, 0) < bp.required_approvals THEN FALSE
        WHEN bp.require_status_checks
             AND COALESCE(cr.check_count, 0) = 0 THEN FALSE
        WHEN bp.require_status_checks
             AND COALESCE(cr.failed_count, 0) > 0 THEN FALSE
        ELSE TRUE
    END AS merge_eligible
FROM pull_requests AS p
LEFT JOIN approval_counts AS a
    ON a.pull_request_id = p.pull_request_id
LEFT JOIN check_results AS cr
    ON cr.pull_request_id = p.pull_request_id
LEFT JOIN branch_protection_policies AS bp
    ON bp.branch_id = p.target_branch_id
ORDER BY p.pull_request_id;

/* -------------------------------------------------------------------------
   FULL JOIN data-quality audit

   The production tables use foreign keys, so orphan relationships are
   rejected. The temporary external table represents data arriving from a
   system where referential integrity is not guaranteed.
   ------------------------------------------------------------------------- */

SELECT
    COALESCE(p.pull_request_id, a.pull_request_id) AS pull_request_id,
    p.title AS internal_title,
    a.review_id AS external_review_id,
    CASE
        WHEN p.pull_request_id IS NULL THEN 'ORPHAN_EXTERNAL_REVIEW'
        WHEN a.review_id IS NULL THEN 'NO_EXTERNAL_REVIEW'
        ELSE 'MATCHED'
    END AS audit_state
FROM pull_requests AS p
FULL OUTER JOIN external_review_audit AS a
    ON a.pull_request_id = p.pull_request_id
ORDER BY pull_request_id;

/* -------------------------------------------------------------------------
   Join multiplicity

   Joining two one-to-many relationships can multiply rows. Aggregation should
   therefore be performed at the intended grain rather than assuming that one
   pull request always produces one joined row.
   ------------------------------------------------------------------------- */

SELECT
    p.pull_request_id,
    COUNT(DISTINCT rv.review_id) AS review_count,
    COUNT(DISTINCT c.status_check_id) AS status_check_count,
    COUNT(*) AS raw_join_rows
FROM pull_requests AS p
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
LEFT JOIN status_checks AS c
    ON c.pull_request_id = p.pull_request_id
GROUP BY p.pull_request_id
ORDER BY p.pull_request_id;

/*
    DISTINCT counts prevent a review from being counted repeatedly merely
    because the pull request also has multiple status checks.
*/

/* -------------------------------------------------------------------------
   Composite join

   A branch is identified by repository_id + branch_name. Both values are
   required to identify the same logical branch when integrating external
   branch records.
   ------------------------------------------------------------------------- */

CREATE TEMP TABLE external_branches (
    repository_id BIGINT,
    branch_name TEXT,
    source_system TEXT
);

INSERT INTO external_branches (
    repository_id,
    branch_name,
    source_system
)
VALUES
    (1, 'main', 'legacy-git'),
    (1, 'missing-branch', 'legacy-git'),
    (3, 'main', 'legacy-git');

SELECT
    b.repository_id,
    b.branch_name,
    b.is_protected,
    e.source_system,
    CASE
        WHEN b.branch_id IS NULL THEN 'EXTERNAL_ONLY'
        WHEN e.repository_id IS NULL THEN 'INTERNAL_ONLY'
        ELSE 'MATCHED'
    END AS reconciliation_state
FROM branches AS b
FULL OUTER JOIN external_branches AS e
    ON e.repository_id = b.repository_id
   AND e.branch_name = b.branch_name
ORDER BY
    COALESCE(b.repository_id, e.repository_id),
    COALESCE(b.branch_name, e.branch_name);

/* -------------------------------------------------------------------------
   Transactional integrity example

   A branch-protection policy is inserted only if the target branch exists
   and belongs to the declared repository.
   ------------------------------------------------------------------------- */

BEGIN;

INSERT INTO branch_protection_policies (
    repository_id,
    branch_id,
    required_approvals,
    require_conversation_resolution,
    require_status_checks,
    require_linear_history,
    allow_force_push,
    allow_branch_deletion
)
SELECT
    b.repository_id,
    b.branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    FALSE
FROM branches AS b
WHERE b.repository_id = 3
  AND b.branch_name = 'main'
ON CONFLICT (branch_id)
DO UPDATE SET
    required_approvals = EXCLUDED.required_approvals,
    require_conversation_resolution =
        EXCLUDED.require_conversation_resolution,
    require_status_checks =
        EXCLUDED.require_status_checks,
    require_linear_history =
        EXCLUDED.require_linear_history,
    allow_force_push =
        EXCLUDED.allow_force_push,
    allow_branch_deletion =
        EXCLUDED.allow_branch_deletion;

COMMIT;

/* -------------------------------------------------------------------------
   Explain-plan-oriented query

   PostgreSQL can choose a nested-loop, hash, or merge join depending on
   statistics, indexes, estimated cardinalities, available memory, and query
   predicates. EXPLAIN ANALYZE executes the statement and reports actual work.
   ------------------------------------------------------------------------- */

EXPLAIN
SELECT
    p.pull_request_id,
    r.review_id,
    c.status
FROM pull_requests AS p
LEFT JOIN reviews AS r
    ON r.pull_request_id = p.pull_request_id
LEFT JOIN status_checks AS c
    ON c.pull_request_id = p.pull_request_id
WHERE p.repository_id = 1;

/* -------------------------------------------------------------------------
   Final focused reports
   ------------------------------------------------------------------------- */

/* INNER: only repositories that currently contain pull requests. */
SELECT
    r.repository_name,
    COUNT(p.pull_request_id) AS pull_request_count
FROM repositories AS r
INNER JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
GROUP BY r.repository_id, r.repository_name
ORDER BY r.repository_name;

/* LEFT: repositories with their review activity, including zero activity. */
SELECT
    r.repository_name,
    COUNT(DISTINCT p.pull_request_id) AS pull_requests,
    COUNT(DISTINCT rv.review_id) AS reviews
FROM repositories AS r
LEFT JOIN pull_requests AS p
    ON p.repository_id = r.repository_id
LEFT JOIN reviews AS rv
    ON rv.pull_request_id = p.pull_request_id
GROUP BY r.repository_id, r.repository_name
ORDER BY r.repository_name;

/* RIGHT: preserve every external audit record. */
SELECT
    p.pull_request_id,
    a.review_id,
    a.reviewer_username
FROM pull_requests AS p
RIGHT JOIN external_review_audit AS a
    ON a.pull_request_id = p.pull_request_id
ORDER BY a.review_id;

/* FULL: reconciliation of internal and external review relationships. */
SELECT
    p.pull_request_id,
    a.review_id,
    CASE
        WHEN p.pull_request_id IS NULL THEN 'EXTERNAL_ONLY'
        WHEN a.review_id IS NULL THEN 'INTERNAL_ONLY'
        ELSE 'MATCHED'
    END AS relationship_state
FROM pull_requests AS p
FULL OUTER JOIN external_review_audit AS a
    ON a.pull_request_id = p.pull_request_id
ORDER BY
    COALESCE(p.pull_request_id, a.pull_request_id);
