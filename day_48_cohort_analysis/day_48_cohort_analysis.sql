DROP SCHEMA IF EXISTS cohort_analysis CASCADE;
CREATE SCHEMA cohort_analysis;

SET search_path TO cohort_analysis;

CREATE TYPE customer_plan AS ENUM ('basic', 'pro', 'enterprise');

CREATE TYPE event_type AS ENUM (
    'signup',
    'login',
    'purchase',
    'feature_use',
    'support_contact'
);

CREATE TYPE review_state AS ENUM (
    'commented',
    'changes_requested',
    'approved',
    'dismissed'
);

CREATE TYPE pull_request_state AS ENUM (
    'draft',
    'open',
    'closed',
    'merged'
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    external_key TEXT NOT NULL UNIQUE,
    signup_at TIMESTAMPTZ NOT NULL,
    acquisition_channel TEXT NOT NULL,
    plan customer_plan NOT NULL,
    CHECK (length(trim(acquisition_channel)) > 0)
);

CREATE TABLE customer_events (
    event_id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id)
        ON DELETE CASCADE,
    event_at TIMESTAMPTZ NOT NULL,
    event_type event_type NOT NULL,
    revenue NUMERIC(12,2) NOT NULL DEFAULT 0,
    CHECK (revenue >= 0)
);

CREATE INDEX idx_customer_events_customer_date
    ON customer_events(customer_id, event_at);

CREATE INDEX idx_customer_events_date
    ON customer_events(event_at);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE
);

CREATE TABLE repository_branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(repository_id, branch_name)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    target_branch_id BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    state pull_request_state NOT NULL DEFAULT 'open',
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    merged_at TIMESTAMPTZ,
    draft BOOLEAN NOT NULL DEFAULT FALSE,
    merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT TRUE,
    base_changed_after_review BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (
        (state = 'merged' AND merged_at IS NOT NULL)
        OR state <> 'merged'
    )
);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests(target_branch_id, state);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_hash TEXT NOT NULL,
    authored_at TIMESTAMPTZ NOT NULL,
    UNIQUE(pull_request_id, commit_hash)
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES reviewers(reviewer_id),
    state review_state NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    eligible BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state, eligible);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (line_number IS NULL OR line_number > 0),
    CHECK (length(trim(body)) > 0)
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE(pull_request_id, check_name)
);

CREATE TABLE branch_protection (
    branch_id BIGINT PRIMARY KEY REFERENCES repository_branches(branch_id)
        ON DELETE CASCADE,
    require_reviews BOOLEAN NOT NULL DEFAULT TRUE,
    required_approvals INTEGER NOT NULL DEFAULT 1,
    dismiss_stale_approvals BOOLEAN NOT NULL DEFAULT TRUE,
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    restrict_deletion BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_merge_strategies TEXT[] NOT NULL DEFAULT ARRAY['squash'],
    CHECK (required_approvals >= 0)
);

CREATE TABLE required_status_checks (
    branch_id BIGINT NOT NULL REFERENCES repository_branches(branch_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY(branch_id, check_name)
);

INSERT INTO customers (
    external_key,
    signup_at,
    acquisition_channel,
    plan
)
VALUES
    ('C001', '2026-01-05 09:00+00', 'organic', 'pro'),
    ('C002', '2026-01-12 09:00+00', 'paid', 'basic'),
    ('C003', '2026-01-20 09:00+00', 'referral', 'pro'),
    ('C004', '2026-02-03 09:00+00', 'organic', 'basic'),
    ('C005', '2026-02-15 09:00+00', 'paid', 'pro'),
    ('C006', '2026-03-02 09:00+00', 'referral', 'basic');

INSERT INTO customer_events (
    customer_id,
    event_at,
    event_type,
    revenue
)
SELECT c.customer_id, v.event_at, v.event_type::event_type, v.revenue
FROM customers c
JOIN (
    VALUES
        ('C001', '2026-01-05 09:00+00', 'signup', 0::numeric),
        ('C001', '2026-01-10 09:00+00', 'purchase', 49::numeric),
        ('C001', '2026-02-10 09:00+00', 'login', 0::numeric),
        ('C001', '2026-03-10 09:00+00', 'purchase', 49::numeric),
        ('C002', '2026-01-12 09:00+00', 'signup', 0::numeric),
        ('C002', '2026-02-01 09:00+00', 'login', 0::numeric),
        ('C003', '2026-01-20 09:00+00', 'signup', 0::numeric),
        ('C003', '2026-02-15 09:00+00', 'purchase', 49::numeric),
        ('C004', '2026-02-03 09:00+00', 'signup', 0::numeric),
        ('C004', '2026-03-09 09:00+00', 'feature_use', 0::numeric),
        ('C005', '2026-02-15 09:00+00', 'signup', 0::numeric),
        ('C005', '2026-03-12 09:00+00', 'purchase', 49::numeric),
        ('C006', '2026-03-02 09:00+00', 'signup', 0::numeric)
) AS v(external_key, event_at, event_type, revenue)
ON c.external_key = v.external_key;

INSERT INTO repositories (repository_name)
VALUES ('customer-platform');

INSERT INTO repository_branches (
    repository_id,
    branch_name,
    protected
)
SELECT repository_id, 'main', TRUE
FROM repositories
WHERE repository_name = 'customer-platform';

INSERT INTO repository_branches (
    repository_id,
    branch_name,
    protected
)
SELECT repository_id, 'feature/cohort-dashboard', FALSE
FROM repositories
WHERE repository_name = 'customer-platform';

INSERT INTO branch_protection (
    branch_id,
    require_reviews,
    required_approvals,
    dismiss_stale_approvals,
    require_status_checks,
    require_conversation_resolution,
    restrict_direct_push,
    restrict_force_push,
    restrict_deletion,
    require_linear_history,
    allowed_merge_strategies
)
SELECT
    branch_id,
    TRUE,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    ARRAY['squash', 'rebase']
FROM repository_branches
WHERE branch_name = 'main';

INSERT INTO required_status_checks (
    branch_id,
    check_name
)
SELECT branch_id, check_name
FROM repository_branches
CROSS JOIN (
    VALUES ('unit-tests'), ('security-scan'), ('build')
) AS checks(check_name)
WHERE branch_name = 'main';

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    state,
    title,
    draft,
    merge_conflict,
    conversations_resolved
)
SELECT
    r.repository_id,
    source.branch_id,
    target.branch_id,
    'open',
    'Add cohort retention dashboard',
    FALSE,
    FALSE,
    TRUE
FROM repositories r
JOIN repository_branches source
    ON source.repository_id = r.repository_id
    AND source.branch_name = 'feature/cohort-dashboard'
JOIN repository_branches target
    ON target.repository_id = r.repository_id
    AND target.branch_name = 'main'
WHERE r.repository_name = 'customer-platform';

INSERT INTO commits (
    pull_request_id,
    commit_hash,
    authored_at
)
SELECT
    pull_request_id,
    commit_hash,
    authored_at
FROM pull_requests
CROSS JOIN (
    VALUES
        ('a1b2c3d4', '2026-10-18 08:00+00'::timestamptz),
        ('e5f6a7b8', '2026-10-18 09:00+00'::timestamptz)
) AS commits(commit_hash, authored_at)
WHERE title = 'Add cohort retention dashboard';

INSERT INTO reviewers (username)
VALUES
    ('alice'),
    ('bob'),
    ('contractor');

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    eligible
)
SELECT
    p.pull_request_id,
    r.reviewer_id,
    CASE
        WHEN r.username IN ('alice', 'bob') THEN 'approved'::review_state
        ELSE 'approved'::review_state
    END,
    CASE
        WHEN r.username IN ('alice', 'bob') THEN TRUE
        ELSE FALSE
    END
FROM pull_requests p
CROSS JOIN reviewers r
WHERE p.title = 'Add cohort retention dashboard';

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    passed,
    completed_at
)
SELECT
    p.pull_request_id,
    check_name,
    TRUE,
    now()
FROM pull_requests p
CROSS JOIN (
    VALUES
        ('unit-tests'),
        ('security-scan'),
        ('build')
) AS checks(check_name)
WHERE p.title = 'Add cohort retention dashboard';

CREATE OR REPLACE VIEW cohort_members AS
SELECT
    customer_id,
    date_trunc('month', signup_at)::date AS cohort_month,
    acquisition_channel,
    plan
FROM customers;

CREATE OR REPLACE VIEW cohort_activity AS
SELECT DISTINCT
    c.customer_id,
    date_trunc('month', c.signup_at)::date AS cohort_month,
    (
        EXTRACT(YEAR FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        )) * 12
        +
        EXTRACT(MONTH FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        ))
    )::integer AS period_number
FROM customers c
JOIN customer_events e
    ON e.customer_id = c.customer_id
WHERE e.event_at >= c.signup_at;

CREATE OR REPLACE VIEW cohort_retention AS
WITH cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM cohort_members
    GROUP BY cohort_month
),
active AS (
    SELECT
        cohort_month,
        period_number,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_activity
    GROUP BY cohort_month, period_number
)
SELECT
    a.cohort_month,
    a.period_number,
    s.cohort_size,
    a.active_customers,
    ROUND(
        a.active_customers::numeric / NULLIF(s.cohort_size, 0) * 100,
        2
    ) AS retention_percent
FROM active a
JOIN cohort_sizes s USING (cohort_month)
ORDER BY a.cohort_month, a.period_number;

CREATE OR REPLACE VIEW cohort_revenue AS
SELECT
    date_trunc('month', c.signup_at)::date AS cohort_month,
    (
        EXTRACT(YEAR FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        )) * 12
        +
        EXTRACT(MONTH FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        ))
    )::integer AS period_number,
    SUM(e.revenue) AS revenue
FROM customers c
JOIN customer_events e
    ON e.customer_id = c.customer_id
GROUP BY
    date_trunc('month', c.signup_at)::date,
    (
        EXTRACT(YEAR FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        )) * 12
        +
        EXTRACT(MONTH FROM age(
            date_trunc('month', e.event_at),
            date_trunc('month', c.signup_at)
        ))
    )::integer
ORDER BY cohort_month, period_number;

CREATE OR REPLACE VIEW cohort_channel_retention AS
WITH members AS (
    SELECT
        date_trunc('month', signup_at)::date AS cohort_month,
        acquisition_channel,
        COUNT(*) AS cohort_size
    FROM customers
    GROUP BY 1, 2
),
activity AS (
    SELECT DISTINCT
        c.customer_id,
        date_trunc('month', c.signup_at)::date AS cohort_month,
        c.acquisition_channel,
        (
            EXTRACT(YEAR FROM age(
                date_trunc('month', e.event_at),
                date_trunc('month', c.signup_at)
            )) * 12
            +
            EXTRACT(MONTH FROM age(
                date_trunc('month', e.event_at),
                date_trunc('month', c.signup_at)
            ))
        )::integer AS period_number
    FROM customers c
    JOIN customer_events e
        ON e.customer_id = c.customer_id
)
SELECT
    a.cohort_month,
    a.acquisition_channel,
    a.period_number,
    m.cohort_size,
    COUNT(DISTINCT a.customer_id) AS active_customers,
    ROUND(
        COUNT(DISTINCT a.customer_id)::numeric
        / NULLIF(m.cohort_size, 0) * 100,
        2
    ) AS retention_percent
FROM activity a
JOIN members m
    ON m.cohort_month = a.cohort_month
    AND m.acquisition_channel = a.acquisition_channel
GROUP BY
    a.cohort_month,
    a.acquisition_channel,
    a.period_number,
    m.cohort_size
ORDER BY
    a.cohort_month,
    a.acquisition_channel,
    a.period_number;

CREATE OR REPLACE FUNCTION merge_eligibility(
    requested_pr_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    blocker TEXT
)
LANGUAGE sql
AS $$
WITH pr AS (
    SELECT
        p.*,
        bp.required_approvals,
        bp.require_reviews,
        bp.require_status_checks,
        bp.require_conversation_resolution
    FROM pull_requests p
    JOIN branch_protection bp
        ON bp.branch_id = p.target_branch_id
    WHERE p.pull_request_id = requested_pr_id
),
approval_count AS (
    SELECT
        r.pull_request_id,
        COUNT(DISTINCT r.reviewer_id)
            FILTER (
                WHERE r.state = 'approved'
                AND r.eligible = TRUE
            ) AS approvals,
        BOOL_OR(
            r.state = 'changes_requested'
            AND r.eligible = TRUE
        ) AS changes_requested
    FROM reviews r
    WHERE r.pull_request_id = requested_pr_id
    GROUP BY r.pull_request_id
),
check_state AS (
    SELECT
        requested_pr_id AS pull_request_id,
        COUNT(*) FILTER (WHERE passed = FALSE) AS failed_checks,
        COUNT(*) AS supplied_checks
    FROM status_checks
    WHERE pull_request_id = requested_pr_id
),
conversation_state AS (
    SELECT
        p.pull_request_id,
        COUNT(*) FILTER (WHERE rc.resolved = FALSE) AS unresolved_comments
    FROM pull_requests p
    LEFT JOIN reviews r
        ON r.pull_request_id = p.pull_request_id
    LEFT JOIN review_comments rc
        ON rc.review_id = r.review_id
    WHERE p.pull_request_id = requested_pr_id
    GROUP BY p.pull_request_id
)
SELECT
    CASE
        WHEN p.draft THEN FALSE
        WHEN p.state <> 'open' THEN FALSE
        WHEN p.merge_conflict THEN FALSE
        WHEN p.base_changed_after_review THEN FALSE
        WHEN p.require_reviews
            AND COALESCE(a.approvals, 0) < p.required_approvals THEN FALSE
        WHEN COALESCE(a.changes_requested, FALSE) THEN FALSE
        WHEN p.require_status_checks
            AND COALESCE(cs.failed_checks, 0) > 0 THEN FALSE
        WHEN p.require_conversation_resolution
            AND COALESCE(cv.unresolved_comments, 0) > 0 THEN FALSE
        ELSE TRUE
    END AS eligible,
    CASE
        WHEN p.draft THEN 'Pull Request is still a draft'
        WHEN p.state <> 'open' THEN 'Pull Request is not open'
        WHEN p.merge_conflict THEN 'Merge conflict exists'
        WHEN p.base_changed_after_review
            THEN 'Base branch changed after review'
        WHEN p.require_reviews
            AND COALESCE(a.approvals, 0) < p.required_approvals
            THEN 'Required approvals are missing'
        WHEN COALESCE(a.changes_requested, FALSE)
            THEN 'Eligible reviewer requested changes'
        WHEN p.require_status_checks
            AND COALESCE(cs.failed_checks, 0) > 0
            THEN 'A status check failed'
        WHEN p.require_conversation_resolution
            AND COALESCE(cv.unresolved_comments, 0) > 0
            THEN 'Review conversations remain unresolved'
        ELSE 'Merge conditions satisfied'
    END AS blocker
FROM pr p
LEFT JOIN approval_count a
    ON a.pull_request_id = p.pull_request_id
LEFT JOIN check_state cs
    ON cs.pull_request_id = p.pull_request_id
LEFT JOIN conversation_state cv
    ON cv.pull_request_id = p.pull_request_id;
$$;

SELECT *
FROM cohort_retention;

SELECT *
FROM cohort_revenue;

SELECT *
FROM cohort_channel_retention;

SELECT
    cohort_month,
    plan,
    COUNT(*) AS customers
FROM cohort_members
GROUP BY cohort_month, plan
ORDER BY cohort_month, plan;

SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE title = 'Add cohort retention dashboard'
    )
);

BEGIN;

UPDATE pull_requests
SET base_changed_after_review = TRUE
WHERE title = 'Add cohort retention dashboard';

SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE title = 'Add cohort retention dashboard'
    )
);

ROLLBACK;

-- Cohort analysis and repository governance are deliberately separate
-- relational domains. The cohort model evaluates customer behavior over
-- elapsed time, while the governance model evaluates whether a Pull Request
-- satisfies repository-level merge rules.
