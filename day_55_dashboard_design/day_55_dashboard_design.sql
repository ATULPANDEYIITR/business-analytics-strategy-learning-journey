DROP SCHEMA IF EXISTS dashboard_governance CASCADE;
CREATE SCHEMA dashboard_governance;

SET search_path = dashboard_governance, public;

CREATE TYPE pr_state AS ENUM ('draft', 'open', 'closed', 'merged');
CREATE TYPE review_state AS ENUM (
    'commented',
    'approved',
    'changes_requested',
    'dismissed'
);
CREATE TYPE check_state AS ENUM ('passing', 'failing', 'pending');
CREATE TYPE merge_strategy AS ENUM ('merge_commit', 'squash', 'rebase');

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    is_protected BOOLEAN NOT NULL DEFAULT FALSE,
    head_sha TEXT,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    sha CHAR(7) NOT NULL,
    message TEXT NOT NULL,
    author_id BIGINT NOT NULL
        REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (repository_id, sha)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id) ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id),
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    state pr_state NOT NULL DEFAULT 'open',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE,
    merge_strategy merge_strategy NOT NULL DEFAULT 'squash',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    UNIQUE (repository_id, number),
    CHECK (source_branch_id <> target_branch_id),
    CHECK (NOT is_draft OR state = 'draft')
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_id BIGINT NOT NULL
        REFERENCES commits(commit_id) ON DELETE RESTRICT,
    commit_order INTEGER NOT NULL CHECK (commit_order > 0),
    PRIMARY KEY (pull_request_id, commit_id),
    UNIQUE (pull_request_id, commit_order)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT
        REFERENCES reviews(review_id) ON DELETE CASCADE,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES users(user_id),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    completed_at TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id) ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 0
        CHECK (required_reviews >= 0),
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT FALSE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_deletion BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE TABLE eligible_reviewers (
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL
        REFERENCES users(user_id),
    PRIMARY KEY (policy_id, user_id)
);

CREATE TABLE merge_events (
    merge_event_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id),
    merged_by BIGINT NOT NULL REFERENCES users(user_id),
    merge_strategy merge_strategy NOT NULL,
    merged_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pr_target_state
    ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state);

CREATE INDEX idx_checks_pr_state
    ON status_checks(pull_request_id, state);

CREATE INDEX idx_comments_pr_resolution
    ON review_comments(pull_request_id, resolved);

INSERT INTO repositories (repository_name)
VALUES ('enterprise-platform');

INSERT INTO users (username)
VALUES
    ('alice'),
    ('bob'),
    ('carol'),
    ('david'),
    ('eve');

INSERT INTO branches (
    repository_id,
    branch_name,
    is_protected,
    head_sha
)
SELECT
    r.repository_id,
    v.branch_name,
    v.is_protected,
    v.head_sha
FROM repositories r
CROSS JOIN (
    VALUES
        ('main', TRUE, 'abc0001'),
        ('feature/dashboard', FALSE, 'abc0003'),
        ('feature/security', FALSE, 'sec0003')
) AS v(branch_name, is_protected, head_sha)
WHERE r.repository_name = 'enterprise-platform';

INSERT INTO commits (
    repository_id,
    sha,
    message,
    author_id
)
SELECT
    r.repository_id,
    v.sha,
    v.message,
    u.user_id
FROM repositories r
CROSS JOIN (
    VALUES
        ('abc0001', 'Initial platform commit', 'alice'),
        ('abc0002', 'Create dashboard architecture', 'alice'),
        ('abc0003', 'Add governance metrics', 'alice'),
        ('sec0001', 'Create security branch', 'david'),
        ('sec0002', 'Add security policy', 'david'),
        ('sec0003', 'Add security checks', 'david')
) AS v(sha, message, username)
JOIN users u ON u.username = v.username
WHERE r.repository_name = 'enterprise-platform';

INSERT INTO pull_requests (
    repository_id,
    number,
    source_branch_id,
    target_branch_id,
    title,
    state,
    is_draft,
    merge_strategy
)
SELECT
    r.repository_id,
    v.number,
    sb.branch_id,
    tb.branch_id,
    v.title,
    v.state::pr_state,
    v.is_draft,
    v.strategy::merge_strategy
FROM repositories r
JOIN (
    VALUES
        (
            101,
            'feature/dashboard',
            'main',
            'Repository governance dashboard',
            'open',
            FALSE,
            'squash'
        ),
        (
            102,
            'feature/security',
            'main',
            'Security controls dashboard',
            'open',
            FALSE,
            'merge_commit'
        )
) AS v(
    number,
    source_branch,
    target_branch,
    title,
    state,
    is_draft,
    strategy
) ON TRUE
JOIN branches sb
    ON sb.repository_id = r.repository_id
    AND sb.branch_name = v.source_branch
JOIN branches tb
    ON tb.repository_id = r.repository_id
    AND tb.branch_name = v.target_branch
WHERE r.repository_name = 'enterprise-platform';

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_id,
    commit_order
)
SELECT
    pr.pull_request_id,
    c.commit_id,
    v.commit_order
FROM pull_requests pr
JOIN repositories r ON r.repository_id = pr.repository_id
JOIN (
    VALUES
        (101, 'abc0002', 1),
        (101, 'abc0003', 2),
        (102, 'sec0001', 1),
        (102, 'sec0002', 2),
        (102, 'sec0003', 3)
) AS v(pr_number, sha, commit_order)
    ON v.pr_number = pr.number
JOIN commits c
    ON c.repository_id = pr.repository_id
    AND c.sha = v.sha
WHERE r.repository_name = 'enterprise-platform';

INSERT INTO branch_protection_policies (
    branch_id,
    required_reviews,
    require_conversation_resolution,
    require_linear_history,
    allow_direct_push,
    allow_force_push,
    allow_deletion
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE
FROM branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, check_name
FROM branch_protection_policies
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan')
) AS v(check_name);

INSERT INTO eligible_reviewers (policy_id, user_id)
SELECT
    p.policy_id,
    u.user_id
FROM branch_protection_policies p
CROSS JOIN users u
WHERE u.username IN ('bob', 'carol', 'david');

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state
)
SELECT
    pr.pull_request_id,
    u.user_id,
    v.state::review_state
FROM pull_requests pr
JOIN (
    VALUES
        (101, 'bob', 'approved'),
        (101, 'carol', 'approved'),
        (102, 'bob', 'approved'),
        (102, 'david', 'changes_requested')
) AS v(pr_number, username, state)
    ON v.pr_number = pr.number
JOIN users u ON u.username = v.username;

INSERT INTO review_comments (
    review_id,
    pull_request_id,
    reviewer_id,
    body,
    resolved
)
SELECT
    rv.review_id,
    rv.pull_request_id,
    rv.reviewer_id,
    v.body,
    v.resolved
FROM reviews rv
JOIN users u ON u.user_id = rv.reviewer_id
JOIN (
    VALUES
        (101, 'bob', 'Clarify metric ownership.', TRUE),
        (101, 'carol', 'Explain the policy label.', FALSE),
        (102, 'david', 'Security control is incomplete.', FALSE)
) AS v(pr_number, username, body, resolved)
    ON v.pr_number = (
        SELECT number
        FROM pull_requests
        WHERE pull_request_id = rv.pull_request_id
    )
    AND v.username = u.username;

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    required
)
SELECT
    pr.pull_request_id,
    v.check_name,
    v.state::check_state,
    v.required
FROM pull_requests pr
JOIN (
    VALUES
        (101, 'unit-tests', 'passing', TRUE),
        (101, 'security-scan', 'passing', TRUE),
        (101, 'performance', 'pending', FALSE),
        (102, 'unit-tests', 'passing', TRUE),
        (102, 'security-scan', 'failing', TRUE)
) AS v(pr_number, check_name, state, required)
    ON v.pr_number = pr.number;

CREATE OR REPLACE FUNCTION enforce_protected_branch_policy()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    policy branch_protection_policies%ROWTYPE;
    approvals INTEGER;
    unresolved INTEGER;
    failed_checks INTEGER;
    required_checks INTEGER;
BEGIN
    IF NEW.state <> 'merged' THEN
        RETURN NEW;
    END IF;

    SELECT p.*
    INTO policy
    FROM branch_protection_policies p
    WHERE p.branch_id = NEW.target_branch_id;

    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    SELECT COUNT(DISTINCT r.reviewer_id)
    INTO approvals
    FROM reviews r
    JOIN eligible_reviewers er
        ON er.policy_id = policy.policy_id
        AND er.user_id = r.reviewer_id
    WHERE r.pull_request_id = NEW.pull_request_id
      AND r.state = 'approved'
      AND NOT EXISTS (
          SELECT 1
          FROM reviews later_review
          WHERE later_review.pull_request_id = r.pull_request_id
            AND later_review.reviewer_id = r.reviewer_id
            AND later_review.state = 'changes_requested'
            AND later_review.submitted_at > r.submitted_at
      );

    IF approvals < policy.required_reviews THEN
        RAISE EXCEPTION
            'Merge blocked: % approvals required, % eligible approvals found',
            policy.required_reviews,
            approvals;
    END IF;

    SELECT COUNT(*)
    INTO unresolved
    FROM review_comments
    WHERE pull_request_id = NEW.pull_request_id
      AND resolved = FALSE;

    IF policy.require_conversation_resolution AND unresolved > 0 THEN
        RAISE EXCEPTION
            'Merge blocked: % unresolved conversations remain',
            unresolved;
    END IF;

    SELECT COUNT(*)
    INTO required_checks
    FROM required_status_checks
    WHERE policy_id = policy.policy_id;

    SELECT COUNT(*)
    INTO failed_checks
    FROM required_status_checks required
    LEFT JOIN status_checks actual
        ON actual.pull_request_id = NEW.pull_request_id
        AND actual.check_name = required.check_name
    WHERE policy_id = policy.policy_id
      AND actual.state <> 'passing';

    IF failed_checks > 0 OR required_checks = 0 AND FALSE THEN
        RAISE EXCEPTION
            'Merge blocked: required status checks are not passing';
    END IF;

    IF policy.require_linear_history
       AND NEW.merge_strategy = 'merge_commit' THEN
        RAISE EXCEPTION
            'Merge blocked: linear history is required';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protected_merge
BEFORE UPDATE OF state ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION enforce_protected_branch_policy();

CREATE OR REPLACE VIEW pull_request_dashboard AS
WITH approval_counts AS (
    SELECT
        pr.pull_request_id,
        COUNT(DISTINCT r.reviewer_id) FILTER (
            WHERE r.state = 'approved'
              AND er.user_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM reviews newer
                  WHERE newer.pull_request_id = r.pull_request_id
                    AND newer.reviewer_id = r.reviewer_id
                    AND newer.state = 'changes_requested'
                    AND newer.submitted_at > r.submitted_at
              )
        ) AS eligible_approvals
    FROM pull_requests pr
    LEFT JOIN reviews r
        ON r.pull_request_id = pr.pull_request_id
    LEFT JOIN branch_protection_policies bp
        ON bp.branch_id = pr.target_branch_id
    LEFT JOIN eligible_reviewers er
        ON er.policy_id = bp.policy_id
        AND er.user_id = r.reviewer_id
    GROUP BY pr.pull_request_id
),
conversation_counts AS (
    SELECT
        pull_request_id,
        COUNT(*) FILTER (WHERE resolved = FALSE) AS unresolved
    FROM review_comments
    GROUP BY pull_request_id
),
check_results AS (
    SELECT
        pr.pull_request_id,
        COUNT(required.check_name) AS required_checks,
        COUNT(required.check_name) FILTER (
            WHERE actual.state = 'passing'
        ) AS passing_required_checks
    FROM pull_requests pr
    JOIN branch_protection_policies bp
        ON bp.branch_id = pr.target_branch_id
    JOIN required_status_checks required
        ON required.policy_id = bp.policy_id
    LEFT JOIN status_checks actual
        ON actual.pull_request_id = pr.pull_request_id
        AND actual.check_name = required.check_name
    GROUP BY pr.pull_request_id
)
SELECT
    pr.pull_request_id,
    r.repository_name,
    pr.number,
    sb.branch_name AS source_branch,
    tb.branch_name AS target_branch,
    pr.title,
    pr.state,
    pr.is_draft,
    COALESCE(a.eligible_approvals, 0) AS eligible_approvals,
    bp.required_reviews,
    COALESCE(c.unresolved, 0) AS unresolved_conversations,
    COALESCE(cr.required_checks, 0) AS required_checks,
    COALESCE(cr.passing_required_checks, 0) AS passing_required_checks,
    CASE
        WHEN pr.state <> 'open' THEN FALSE
        WHEN pr.is_draft THEN FALSE
        WHEN COALESCE(a.eligible_approvals, 0) < bp.required_reviews THEN FALSE
        WHEN bp.require_conversation_resolution
             AND COALESCE(c.unresolved, 0) > 0 THEN FALSE
        WHEN COALESCE(cr.required_checks, 0)
             <> COALESCE(cr.passing_required_checks, 0) THEN FALSE
        WHEN bp.require_linear_history
             AND pr.merge_strategy = 'merge_commit' THEN FALSE
        ELSE TRUE
    END AS merge_eligible
FROM pull_requests pr
JOIN repositories r ON r.repository_id = pr.repository_id
JOIN branches sb ON sb.branch_id = pr.source_branch_id
JOIN branches tb ON tb.branch_id = pr.target_branch_id
LEFT JOIN branch_protection_policies bp
    ON bp.branch_id = pr.target_branch_id
LEFT JOIN approval_counts a
    ON a.pull_request_id = pr.pull_request_id
LEFT JOIN conversation_counts c
    ON c.pull_request_id = pr.pull_request_id
LEFT JOIN check_results cr
    ON cr.pull_request_id = pr.pull_request_id;

-- Primary dashboard retrieval.
SELECT *
FROM pull_request_dashboard
ORDER BY number;

-- High-level information hierarchy metrics.
SELECT
    COUNT(*) FILTER (WHERE state IN ('open', 'draft'))
        AS active_pull_requests,
    COUNT(*) FILTER (WHERE merge_eligible)
        AS mergeable_pull_requests,
    COUNT(*) FILTER (
        WHERE state IN ('open', 'draft') AND NOT merge_eligible
    ) AS blocked_pull_requests,
    SUM(unresolved_conversations)
        AS unresolved_conversations
FROM pull_request_dashboard;

-- Review quality and approval analysis.
SELECT
    r.username AS reviewer,
    COUNT(*) AS review_decisions,
    COUNT(*) FILTER (WHERE rv.state = 'approved') AS approvals,
    COUNT(*) FILTER (WHERE rv.state = 'changes_requested')
        AS requested_changes
FROM reviews rv
JOIN users r ON r.user_id = rv.reviewer_id
GROUP BY r.username
ORDER BY review_decisions DESC;

-- Required checks that currently block each Pull Request.
SELECT
    d.number,
    d.title,
    sc.check_name,
    sc.state
FROM pull_request_dashboard d
JOIN status_checks sc
    ON sc.pull_request_id = d.pull_request_id
WHERE sc.required = TRUE
  AND sc.state <> 'passing'
ORDER BY d.number, sc.check_name;

-- Branch protection configuration.
SELECT
    b.branch_name,
    bp.required_reviews,
    bp.require_conversation_resolution,
    bp.require_linear_history,
    bp.allow_direct_push,
    bp.allow_force_push,
    bp.allow_deletion,
    COALESCE(
        string_agg(rsc.check_name, ', ' ORDER BY rsc.check_name),
        'none'
    ) AS required_status_checks
FROM branches b
LEFT JOIN branch_protection_policies bp
    ON bp.branch_id = b.branch_id
LEFT JOIN required_status_checks rsc
    ON rsc.policy_id = bp.policy_id
WHERE b.is_protected
GROUP BY
    b.branch_name,
    bp.required_reviews,
    bp.require_conversation_resolution,
    bp.require_linear_history,
    bp.allow_direct_push,
    bp.allow_force_push,
    bp.allow_deletion
ORDER BY b.branch_name;

-- Transactional demonstration:
-- The first update is deliberately blocked because PR 101 has an unresolved
-- conversation. The savepoint allows the transaction to continue safely.
BEGIN;

SAVEPOINT before_merge_attempt;

DO $$
BEGIN
    BEGIN
        UPDATE pull_requests
        SET state = 'merged',
            merged_at = now()
        WHERE number = 101;

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Expected merge rejection: %', SQLERRM;
        ROLLBACK TO SAVEPOINT before_merge_attempt;
    END;
END;
$$;

COMMIT;

-- A fully eligible Pull Request can be merged after its governance conditions
-- have been satisfied. PR 101 is made eligible by resolving its conversation.
UPDATE review_comments
SET resolved = TRUE
WHERE pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE number = 101
);

BEGIN;

UPDATE pull_requests
SET state = 'merged',
    merged_at = now()
WHERE number = 101;

INSERT INTO merge_events (
    pull_request_id,
    merged_by,
    merge_strategy
)
SELECT
    pr.pull_request_id,
    u.user_id,
    pr.merge_strategy
FROM pull_requests pr
JOIN users u ON u.username = 'alice'
WHERE pr.number = 101
  AND pr.state = 'merged';

COMMIT;

-- PR 102 remains blocked because its security scan is failing and a reviewer
-- requested changes.
SELECT *
FROM pull_request_dashboard
WHERE number IN (101, 102)
ORDER BY number;
