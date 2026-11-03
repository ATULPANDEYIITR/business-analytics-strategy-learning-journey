DROP SCHEMA IF EXISTS data_cleaning_demo CASCADE;

CREATE SCHEMA data_cleaning_demo;

SET search_path TO data_cleaning_demo;

-- Repository-level source data.
CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    source_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    title TEXT NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN (
            'draft',
            'open',
            'changes_requested',
            'approved',
            'closed',
            'merged'
        )
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    branch_id BIGINT NOT NULL REFERENCES branches(branch_id),
    commit_hash TEXT NOT NULL UNIQUE,
    commit_message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    reviewer_name TEXT NOT NULL,
    reviewer_email TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    review_state TEXT NOT NULL CHECK (
        review_state IN (
            'commented',
            'changes_requested',
            'approved',
            'dismissed'
        )
    ),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dismissed_at TIMESTAMPTZ
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number > 0),
    comment_text TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'passed', 'failed')
    ),
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0
        CHECK (required_reviews >= 0),
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE approval_requirements (
    requirement_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    reviewer_group TEXT NOT NULL,
    minimum_approvals INTEGER NOT NULL CHECK (minimum_approvals > 0),
    UNIQUE (policy_id, reviewer_group)
);

CREATE TABLE merge_events (
    merge_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    merge_strategy TEXT NOT NULL CHECK (
        merge_strategy IN ('merge_commit', 'squash', 'rebase')
    ),
    merged_by TEXT NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pr_repository
    ON pull_requests(repository_id);

CREATE INDEX idx_pr_target_branch
    ON pull_requests(target_branch_id);

CREATE INDEX idx_reviews_pr
    ON reviews(pull_request_id);

CREATE INDEX idx_status_checks_pr_status
    ON status_checks(pull_request_id, status);

CREATE INDEX idx_comments_review_resolved
    ON review_comments(review_id, resolved);

CREATE INDEX idx_commits_branch_time
    ON commits(branch_id, committed_at DESC);

INSERT INTO repositories (repository_name, owner_name)
VALUES
    ('payments-api', 'platform-team'),
    ('inventory-api', 'commerce-team');

INSERT INTO branches (repository_id, branch_name, protected)
SELECT repository_id, 'main', TRUE
FROM repositories
WHERE repository_name IN ('payments-api', 'inventory-api');

INSERT INTO branches (repository_id, branch_name, protected)
SELECT repository_id, 'develop', FALSE
FROM repositories
WHERE repository_name IN ('payments-api', 'inventory-api');

INSERT INTO branches (repository_id, branch_name, protected)
VALUES
    (
        (SELECT repository_id FROM repositories WHERE repository_name = 'payments-api'),
        'feature/payment-validation',
        FALSE
    ),
    (
        (SELECT repository_id FROM repositories WHERE repository_name = 'payments-api'),
        'feature/audit',
        FALSE
    ),
    (
        (SELECT repository_id FROM repositories WHERE repository_name = 'inventory-api'),
        'feature/reports',
        FALSE
    ),
    (
        (SELECT repository_id FROM repositories WHERE repository_name = 'inventory-api'),
        'feature/search',
        FALSE
    );

INSERT INTO reviewers (reviewer_name, reviewer_email)
VALUES
    ('Priya Sharma', 'priya@example.com'),
    ('Rahul Verma', 'rahul@example.com'),
    ('Anita Singh', 'anita@example.com');

INSERT INTO branch_protection_policies (
    branch_id,
    required_reviews,
    require_status_checks,
    require_resolved_conversations,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_linear_history,
    allow_administrator_bypass
)
SELECT
    branch_id,
    1,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    FALSE
FROM branches
WHERE branch_name = 'main';

INSERT INTO approval_requirements (
    policy_id,
    reviewer_group,
    minimum_approvals
)
SELECT
    policy_id,
    'repository-maintainers',
    1
FROM branch_protection_policies;

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    state
)
VALUES
(
    (SELECT repository_id FROM repositories WHERE repository_name = 'payments-api'),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'feature/payment-validation'
    ),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'main'
        AND repository_id = (
            SELECT repository_id
            FROM repositories
            WHERE repository_name = 'payments-api'
        )
    ),
    'Validate payment requests',
    'approved'
),
(
    (SELECT repository_id FROM repositories WHERE repository_name = 'payments-api'),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'feature/audit'
    ),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'main'
        AND repository_id = (
            SELECT repository_id
            FROM repositories
            WHERE repository_name = 'payments-api'
        )
    ),
    'Add audit logging',
    'changes_requested'
),
(
    (SELECT repository_id FROM repositories WHERE repository_name = 'inventory-api'),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'feature/search'
    ),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'develop'
        AND repository_id = (
            SELECT repository_id
            FROM repositories
            WHERE repository_name = 'inventory-api'
        )
    ),
    'Improve search indexing',
    'open'
),
(
    (SELECT repository_id FROM repositories WHERE repository_name = 'inventory-api'),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'feature/reports'
    ),
    (
        SELECT branch_id
        FROM branches
        WHERE branch_name = 'main'
        AND repository_id = (
            SELECT repository_id
            FROM repositories
            WHERE repository_name = 'inventory-api'
        )
    ),
    'Add inventory reports',
    'approved'
);

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    review_state
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved'
FROM pull_requests pr
JOIN reviewers r
    ON r.reviewer_email = 'priya@example.com'
WHERE pr.title = 'Validate payment requests';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    review_state
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'changes_requested'
FROM pull_requests pr
JOIN reviewers r
    ON r.reviewer_email = 'rahul@example.com'
WHERE pr.title = 'Add audit logging';

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    review_state
)
SELECT
    pr.pull_request_id,
    r.reviewer_id,
    'approved'
FROM pull_requests pr
JOIN reviewers r
    ON r.reviewer_email = 'anita@example.com'
WHERE pr.title = 'Add inventory reports';

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    comment_text,
    resolved
)
SELECT
    review_id,
    'src/audit.py',
    42,
    'Validate sensitive audit fields.',
    FALSE
FROM reviews
WHERE review_state = 'changes_requested';

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    comment_text,
    resolved
)
SELECT
    review_id,
    'src/payment.py',
    18,
    'Validation logic is clear.',
    TRUE
FROM reviews
WHERE review_state = 'approved';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    status,
    completed_at
)
SELECT
    pull_request_id,
    'unit-tests',
    CASE
        WHEN title IN (
            'Validate payment requests',
            'Add inventory reports'
        ) THEN 'passed'
        WHEN title = 'Add audit logging' THEN 'failed'
        ELSE 'pending'
    END,
    CASE
        WHEN title IN (
            'Validate payment requests',
            'Add inventory reports',
            'Add audit logging'
        ) THEN CURRENT_TIMESTAMP
        ELSE NULL
    END
FROM pull_requests;

-- Data-cleaning view: normalized branch names, reviewer decisions,
-- unresolved conversations, and status-check outcomes.
CREATE VIEW cleaned_pull_request_records AS
SELECT
    pr.pull_request_id,
    r.repository_name,
    LOWER(TRIM(REPLACE(sb.branch_name, 'refs/heads/', ''))) AS source_branch,
    LOWER(TRIM(REPLACE(tb.branch_name, 'refs/heads/', ''))) AS target_branch,
    pr.title,
    pr.state,
    COUNT(DISTINCT CASE
        WHEN rv.review_state = 'approved' THEN rv.review_id
    END) AS approval_count,
    COUNT(DISTINCT CASE
        WHEN rv.review_state = 'changes_requested' THEN rv.review_id
    END) AS changes_requested_count,
    COUNT(DISTINCT CASE
        WHEN rc.resolved = FALSE THEN rc.comment_id
    END) AS unresolved_comments,
    COUNT(DISTINCT CASE
        WHEN sc.status = 'passed' THEN sc.status_check_id
    END) AS passed_checks,
    COUNT(DISTINCT CASE
        WHEN sc.status = 'failed' THEN sc.status_check_id
    END) AS failed_checks
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN branches sb
    ON sb.branch_id = pr.source_branch_id
JOIN branches tb
    ON tb.branch_id = pr.target_branch_id
LEFT JOIN reviews rv
    ON rv.pull_request_id = pr.pull_request_id
LEFT JOIN review_comments rc
    ON rc.review_id = rv.review_id
LEFT JOIN status_checks sc
    ON sc.pull_request_id = pr.pull_request_id
GROUP BY
    pr.pull_request_id,
    r.repository_name,
    sb.branch_name,
    tb.branch_name,
    pr.title,
    pr.state;

-- Retrieve cleaned records.
SELECT *
FROM cleaned_pull_request_records
ORDER BY pull_request_id;

-- Missing-data validation.
SELECT
    COUNT(*) FILTER (WHERE reviewer_count = 0) AS records_without_reviewers
FROM (
    SELECT
        pr.pull_request_id,
        COUNT(rv.review_id) AS reviewer_count
    FROM pull_requests pr
    LEFT JOIN reviews rv
        ON rv.pull_request_id = pr.pull_request_id
    GROUP BY pr.pull_request_id
) x;

-- Duplicate candidate detection.
SELECT
    repository_name,
    source_branch,
    target_branch,
    title,
    COUNT(*) AS duplicate_count
FROM cleaned_pull_request_records
GROUP BY
    repository_name,
    source_branch,
    target_branch,
    title
HAVING COUNT(*) > 1;

-- Aggregation by repository.
SELECT
    repository_name,
    COUNT(*) AS pull_requests,
    COUNT(*) FILTER (WHERE state = 'approved') AS approved_prs,
    COUNT(*) FILTER (WHERE state = 'changes_requested') AS blocked_prs,
    COUNT(*) FILTER (WHERE state = 'open') AS open_prs
FROM cleaned_pull_request_records
GROUP BY repository_name
ORDER BY repository_name;

-- Merge eligibility evaluation.
WITH policy_state AS (
    SELECT
        pr.pull_request_id,
        pr.title,
        tb.branch_name AS target_branch,
        bp.required_reviews,
        bp.require_status_checks,
        bp.require_resolved_conversations,
        bp.allow_direct_push,
        bp.allow_force_push,
        COUNT(DISTINCT rv.review_id)
            FILTER (WHERE rv.review_state = 'approved')
            AS approvals,
        COUNT(DISTINCT sc.status_check_id)
            FILTER (WHERE sc.status = 'failed')
            AS failed_checks,
        COUNT(DISTINCT sc.status_check_id)
            FILTER (WHERE sc.status = 'pending')
            AS pending_checks,
        COUNT(DISTINCT rc.comment_id)
            FILTER (WHERE rc.resolved = FALSE)
            AS unresolved_comments
    FROM pull_requests pr
    JOIN branches tb
        ON tb.branch_id = pr.target_branch_id
    JOIN branch_protection_policies bp
        ON bp.branch_id = tb.branch_id
    LEFT JOIN reviews rv
        ON rv.pull_request_id = pr.pull_request_id
    LEFT JOIN review_comments rc
        ON rc.review_id = rv.review_id
    LEFT JOIN status_checks sc
        ON sc.pull_request_id = pr.pull_request_id
    GROUP BY
        pr.pull_request_id,
        pr.title,
        tb.branch_name,
        bp.required_reviews,
        bp.require_status_checks,
        bp.require_resolved_conversations,
        bp.allow_direct_push,
        bp.allow_force_push
)
SELECT
    pull_request_id,
    title,
    target_branch,
    approvals,
    failed_checks,
    pending_checks,
    unresolved_comments,
    (
        approvals >= required_reviews
        AND (
            NOT require_status_checks
            OR (failed_checks = 0 AND pending_checks = 0)
        )
        AND (
            NOT require_resolved_conversations
            OR unresolved_comments = 0
        )
    ) AS merge_eligible
FROM policy_state
ORDER BY pull_request_id;

-- Transaction demonstrating controlled merge processing.
BEGIN;

WITH eligibility AS (
    SELECT
        pr.pull_request_id,
        COUNT(DISTINCT rv.review_id)
            FILTER (WHERE rv.review_state = 'approved') AS approvals,
        COUNT(DISTINCT sc.status_check_id)
            FILTER (WHERE sc.status = 'failed') AS failed_checks,
        COUNT(DISTINCT sc.status_check_id)
            FILTER (WHERE sc.status = 'pending') AS pending_checks,
        COUNT(DISTINCT rc.comment_id)
            FILTER (WHERE rc.resolved = FALSE) AS unresolved_comments
    FROM pull_requests pr
    LEFT JOIN reviews rv
        ON rv.pull_request_id = pr.pull_request_id
    LEFT JOIN review_comments rc
        ON rc.review_id = rv.review_id
    LEFT JOIN status_checks sc
        ON sc.pull_request_id = pr.pull_request_id
    WHERE pr.title = 'Validate payment requests'
    GROUP BY pr.pull_request_id
)
INSERT INTO merge_events (
    pull_request_id,
    merge_strategy,
    merged_by
)
SELECT
    pull_request_id,
    'squash',
    'release-manager'
FROM eligibility
WHERE approvals >= 1
  AND failed_checks = 0
  AND pending_checks = 0
  AND unresolved_comments = 0;

UPDATE pull_requests
SET
    state = 'merged',
    merged_at = CURRENT_TIMESTAMP
WHERE pull_request_id IN (
    SELECT pull_request_id
    FROM merge_events
    WHERE title IS NULL
);

COMMIT;

-- Correct the state explicitly for the demonstration merge.
UPDATE pull_requests
SET
    state = 'merged',
    merged_at = CURRENT_TIMESTAMP
WHERE title = 'Validate payment requests'
  AND EXISTS (
      SELECT 1
      FROM merge_events me
      WHERE me.pull_request_id = pull_requests.pull_request_id
  );

-- Reporting query after workflow processing.
SELECT
    r.repository_name,
    pr.title,
    pr.state,
    tb.branch_name AS target_branch,
    me.merge_strategy,
    me.merged_by,
    me.merged_at
FROM pull_requests pr
JOIN repositories r
    ON r.repository_id = pr.repository_id
JOIN branches tb
    ON tb.branch_id = pr.target_branch_id
LEFT JOIN merge_events me
    ON me.pull_request_id = pr.pull_request_id
ORDER BY pr.pull_request_id;
