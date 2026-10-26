DROP SCHEMA IF EXISTS power_bi_fundamentals CASCADE;
CREATE SCHEMA power_bi_fundamentals;

SET search_path = power_bi_fundamentals, public;

CREATE TYPE dataset_status AS ENUM ('created', 'refreshing', 'refreshed', 'failed');
CREATE TYPE review_state AS ENUM ('commented', 'approved', 'changes_requested', 'dismissed');
CREATE TYPE refresh_status AS ENUM ('running', 'succeeded', 'failed');

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE datasets (
    dataset_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    dataset_name TEXT NOT NULL,
    status dataset_status NOT NULL DEFAULT 'created',
    last_refreshed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, dataset_name)
);

CREATE TABLE regions (
    region_id BIGSERIAL PRIMARY KEY,
    region_name TEXT NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id BIGSERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES categories(category_id),
    product_name TEXT NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL UNIQUE
);

CREATE TABLE sales (
    sale_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    sale_date DATE NOT NULL,
    region_id BIGINT NOT NULL REFERENCES regions(region_id),
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    customer_id BIGINT NOT NULL REFERENCES customers(customer_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(14,2) NOT NULL CHECK (unit_price >= 0),
    UNIQUE (dataset_id, sale_id)
);

CREATE TABLE refresh_history (
    refresh_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    status refresh_status NOT NULL,
    rows_loaded INTEGER CHECK (rows_loaded >= 0),
    error_message TEXT
);

CREATE TABLE reports (
    report_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    report_name TEXT NOT NULL,
    UNIQUE (dataset_id, report_name)
);

CREATE TABLE report_pages (
    page_id BIGSERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    page_name TEXT NOT NULL,
    page_order INTEGER NOT NULL CHECK (page_order > 0),
    UNIQUE (report_id, page_name),
    UNIQUE (report_id, page_order)
);

CREATE TABLE visuals (
    visual_id BIGSERIAL PRIMARY KEY,
    page_id BIGINT NOT NULL REFERENCES report_pages(page_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    visual_type TEXT NOT NULL CHECK (
        visual_type IN (
            'card',
            'table',
            'bar_chart',
            'line_chart',
            'slicer'
        )
    ),
    measure_name TEXT NOT NULL,
    dimension_name TEXT
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    protected_branch TEXT NOT NULL,
    require_reviews BOOLEAN NOT NULL DEFAULT TRUE,
    required_approvals INTEGER NOT NULL DEFAULT 1 CHECK (required_approvals >= 0),
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    block_direct_push BOOLEAN NOT NULL DEFAULT TRUE,
    block_force_push BOOLEAN NOT NULL DEFAULT TRUE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (repository_id, protected_branch)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    source_branch TEXT NOT NULL,
    target_branch TEXT NOT NULL,
    draft BOOLEAN NOT NULL DEFAULT FALSE,
    closed BOOLEAN NOT NULL DEFAULT FALSE,
    merge_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    unresolved_conversations INTEGER NOT NULL DEFAULT 0
        CHECK (unresolved_conversations >= 0),
    CHECK (source_branch <> target_branch)
);

CREATE TABLE commits (
    commit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL REFERENCES repositories(repository_id),
    commit_hash TEXT NOT NULL UNIQUE,
    commit_message TEXT NOT NULL
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    commit_id BIGINT NOT NULL REFERENCES commits(commit_id),
    PRIMARY KEY (pull_request_id, commit_id)
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL REFERENCES users(user_id),
    state review_state NOT NULL,
    stale BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL REFERENCES reviews(review_id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER CHECK (line_number > 0),
    comment_text TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    passed BOOLEAN NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (pull_request_id, check_name)
);

CREATE TABLE required_status_checks (
    policy_id BIGINT NOT NULL REFERENCES branch_protection_policies(policy_id) ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    PRIMARY KEY (policy_id, check_name)
);

CREATE INDEX idx_sales_dataset_date
    ON sales(dataset_id, sale_date);

CREATE INDEX idx_sales_region
    ON sales(region_id);

CREATE INDEX idx_reviews_pr_state
    ON reviews(pull_request_id, state, stale);

CREATE INDEX idx_status_checks_pr
    ON status_checks(pull_request_id, check_name, passed);

INSERT INTO repositories (repository_name)
VALUES ('enterprise-bi-platform');

INSERT INTO users (username, display_name)
VALUES
    ('analyst_01', 'BI Analyst'),
    ('engineer_02', 'Data Engineer'),
    ('architect_03', 'Solution Architect');

INSERT INTO regions (region_name)
VALUES ('North'), ('South'), ('East'), ('West');

INSERT INTO categories (category_name)
VALUES ('Computers'), ('Accessories');

INSERT INTO products (category_id, product_name)
SELECT category_id, 'Laptop'
FROM categories
WHERE category_name = 'Computers';

INSERT INTO products (category_id, product_name)
SELECT category_id, 'Monitor'
FROM categories
WHERE category_name = 'Accessories';

INSERT INTO products (category_id, product_name)
SELECT category_id, 'Keyboard'
FROM categories
WHERE category_name = 'Accessories';

INSERT INTO customers (customer_name)
VALUES
    ('Customer 101'),
    ('Customer 102'),
    ('Customer 103'),
    ('Customer 104'),
    ('Customer 105'),
    ('Customer 106');

INSERT INTO datasets (
    repository_id,
    dataset_name,
    status,
    last_refreshed_at
)
SELECT
    repository_id,
    'Sales Analytics Dataset',
    'refreshed',
    CURRENT_TIMESTAMP
FROM repositories
WHERE repository_name = 'enterprise-bi-platform';

INSERT INTO sales (
    dataset_id,
    sale_date,
    region_id,
    product_id,
    customer_id,
    quantity,
    unit_price
)
SELECT
    d.dataset_id,
    v.sale_date::date,
    r.region_id,
    p.product_id,
    c.customer_id,
    v.quantity,
    v.unit_price
FROM datasets d
CROSS JOIN (
    VALUES
        ('2026-01-05', 'North', 'Laptop', 'Customer 101', 2, 85000.00),
        ('2026-01-12', 'South', 'Monitor', 'Customer 102', 5, 18000.00),
        ('2026-02-02', 'North', 'Keyboard', 'Customer 103', 8, 3500.00),
        ('2026-02-14', 'West', 'Laptop', 'Customer 104', 1, 92000.00),
        ('2026-02-21', 'South', 'Laptop', 'Customer 105', 3, 87000.00),
        ('2026-03-03', 'East', 'Monitor', 'Customer 106', 7, 17500.00)
) AS v(sale_date, region_name, product_name, customer_name, quantity, unit_price)
JOIN regions r ON r.region_name = v.region_name
JOIN products p ON p.product_name = v.product_name
JOIN customers c ON c.customer_name = v.customer_name
WHERE d.dataset_name = 'Sales Analytics Dataset';

INSERT INTO reports (dataset_id, report_name)
SELECT dataset_id, 'Regional Sales Report'
FROM datasets
WHERE dataset_name = 'Sales Analytics Dataset';

INSERT INTO report_pages (report_id, page_name, page_order)
SELECT report_id, 'Executive Overview', 1
FROM reports
WHERE report_name = 'Regional Sales Report';

INSERT INTO report_pages (report_id, page_name, page_order)
SELECT report_id, 'North Analysis', 2
FROM reports
WHERE report_name = 'Regional Sales Report';

INSERT INTO visuals (page_id, title, visual_type, measure_name, dimension_name)
SELECT page_id, 'Total Revenue', 'card', 'Revenue', NULL
FROM report_pages
WHERE page_name = 'Executive Overview';

INSERT INTO visuals (page_id, title, visual_type, measure_name, dimension_name)
SELECT page_id, 'Revenue by Region', 'bar_chart', 'Revenue', 'Region'
FROM report_pages
WHERE page_name = 'Executive Overview';

INSERT INTO visuals (page_id, title, visual_type, measure_name, dimension_name)
SELECT page_id, 'Quantity by Category', 'table', 'Quantity', 'Category'
FROM report_pages
WHERE page_name = 'Executive Overview';

INSERT INTO visuals (page_id, title, visual_type, measure_name, dimension_name)
SELECT page_id, 'North Revenue', 'card', 'Revenue', NULL
FROM report_pages
WHERE page_name = 'North Analysis';

INSERT INTO branch_protection_policies (
    repository_id,
    protected_branch,
    require_reviews,
    required_approvals,
    require_status_checks,
    block_direct_push,
    block_force_push,
    require_conversation_resolution
)
SELECT
    repository_id,
    'main',
    TRUE,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE
FROM repositories
WHERE repository_name = 'enterprise-bi-platform';

INSERT INTO required_status_checks (policy_id, check_name)
SELECT policy_id, check_name
FROM branch_protection_policies
CROSS JOIN (
    VALUES ('build'), ('unit-tests'), ('security-scan')
) AS required(check_name)
WHERE protected_branch = 'main';

INSERT INTO pull_requests (
    repository_id,
    source_branch,
    target_branch,
    draft,
    closed,
    merge_conflict,
    unresolved_conversations
)
SELECT
    repository_id,
    'feature/sales-dashboard',
    'main',
    FALSE,
    FALSE,
    FALSE,
    0
FROM repositories
WHERE repository_name = 'enterprise-bi-platform';

INSERT INTO commits (repository_id, commit_hash, commit_message)
SELECT repository_id, 'a81c001', 'Create sales dataset'
FROM repositories
WHERE repository_name = 'enterprise-bi-platform';

INSERT INTO commits (repository_id, commit_hash, commit_message)
SELECT repository_id, 'b92d002', 'Add report measures'
FROM repositories
WHERE repository_name = 'enterprise-bi-platform';

INSERT INTO pull_request_commits (pull_request_id, commit_id)
SELECT pr.pull_request_id, c.commit_id
FROM pull_requests pr
JOIN commits c ON c.commit_hash IN ('a81c001', 'b92d002')
WHERE pr.source_branch = 'feature/sales-dashboard';

INSERT INTO reviews (pull_request_id, reviewer_id, state, stale)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    FALSE
FROM pull_requests pr
JOIN users u ON u.username = 'analyst_01'
WHERE pr.source_branch = 'feature/sales-dashboard';

INSERT INTO reviews (pull_request_id, reviewer_id, state, stale)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    FALSE
FROM pull_requests pr
JOIN users u ON u.username = 'engineer_02'
WHERE pr.source_branch = 'feature/sales-dashboard';

INSERT INTO reviews (pull_request_id, reviewer_id, state, stale)
SELECT
    pr.pull_request_id,
    u.user_id,
    'approved',
    TRUE
FROM pull_requests pr
JOIN users u ON u.username = 'architect_03'
WHERE pr.source_branch = 'feature/sales-dashboard';

INSERT INTO status_checks (pull_request_id, check_name, passed)
SELECT pr.pull_request_id, checks.check_name, TRUE
FROM pull_requests pr
CROSS JOIN (
    VALUES ('build'), ('unit-tests'), ('security-scan')
) AS checks(check_name)
WHERE pr.source_branch = 'feature/sales-dashboard';

CREATE OR REPLACE FUNCTION calculate_revenue(
    p_dataset_id BIGINT
)
RETURNS NUMERIC(18,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(SUM(quantity * unit_price), 0)::NUMERIC(18,2)
    FROM sales
    WHERE dataset_id = p_dataset_id;
$$;

CREATE OR REPLACE FUNCTION merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    failure_reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    policy RECORD;
    approval_count INTEGER;
    missing_checks INTEGER;
BEGIN
    SELECT bp.*
    INTO policy
    FROM pull_requests pr
    JOIN branch_protection_policies bp
      ON bp.repository_id = pr.repository_id
     AND bp.protected_branch = pr.target_branch
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'No branch protection policy found for target branch';
        RETURN;
    END IF;

    SELECT COUNT(DISTINCT reviewer_id)
    INTO approval_count
    FROM reviews
    WHERE pull_request_id = p_pull_request_id
      AND state = 'approved'
      AND stale = FALSE;

    IF policy.require_reviews AND approval_count < policy.required_approvals THEN
        RETURN QUERY
        SELECT FALSE, 'Required current approvals are missing';
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO missing_checks
    FROM required_status_checks rsc
    WHERE rsc.policy_id = policy.policy_id
      AND NOT EXISTS (
          SELECT 1
          FROM status_checks sc
          WHERE sc.pull_request_id = p_pull_request_id
            AND sc.check_name = rsc.check_name
            AND sc.passed = TRUE
      );

    IF policy.require_status_checks AND missing_checks > 0 THEN
        RETURN QUERY
        SELECT FALSE, 'Required status checks are missing or failed';
        RETURN;
    END IF;

    IF policy.require_conversation_resolution THEN
        IF EXISTS (
            SELECT 1
            FROM pull_requests
            WHERE pull_request_id = p_pull_request_id
              AND unresolved_conversations > 0
        ) THEN
            RETURN QUERY
            SELECT FALSE, 'Review conversations remain unresolved';
            RETURN;
        END IF;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pull_requests
        WHERE pull_request_id = p_pull_request_id
          AND (draft OR closed OR merge_conflict)
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Pull Request state blocks merging';
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, NULL::TEXT;
END;
$$;

CREATE OR REPLACE VIEW dataset_revenue_by_region AS
SELECT
    s.dataset_id,
    r.region_name,
    SUM(s.quantity * s.unit_price)::NUMERIC(18,2) AS revenue,
    SUM(s.quantity) AS units
FROM sales s
JOIN regions r ON r.region_id = s.region_id
GROUP BY s.dataset_id, r.region_name;

CREATE OR REPLACE VIEW report_inventory AS
SELECT
    r.report_name,
    rp.page_name,
    rp.page_order,
    v.title,
    v.visual_type,
    v.measure_name,
    v.dimension_name
FROM reports r
JOIN report_pages rp ON rp.report_id = r.report_id
JOIN visuals v ON v.page_id = rp.page_id
ORDER BY r.report_name, rp.page_order, v.visual_id;

-- Retrieval: dataset-level revenue.
SELECT
    d.dataset_name,
    calculate_revenue(d.dataset_id) AS total_revenue
FROM datasets d;

-- Aggregation: revenue by region.
SELECT *
FROM dataset_revenue_by_region
ORDER BY revenue DESC;

-- Report metadata: pages and visuals.
SELECT *
FROM report_inventory;

-- Merge eligibility: valid Pull Request.
SELECT *
FROM merge_eligibility(
    (
        SELECT pull_request_id
        FROM pull_requests
        WHERE source_branch = 'feature/sales-dashboard'
    )
);

-- Transactional demonstration: record a refresh atomically.
BEGIN;

INSERT INTO refresh_history (
    dataset_id,
    status,
    completed_at,
    rows_loaded
)
SELECT
    dataset_id,
    'succeeded',
    CURRENT_TIMESTAMP,
    COUNT(s.sale_id)
FROM datasets d
LEFT JOIN sales s ON s.dataset_id = d.dataset_id
WHERE d.dataset_name = 'Sales Analytics Dataset'
GROUP BY dataset_id;

UPDATE datasets
SET
    status = 'refreshed',
    last_refreshed_at = CURRENT_TIMESTAMP
WHERE dataset_name = 'Sales Analytics Dataset';

COMMIT;

-- Validation query: identify invalid negative or zero quantities.
SELECT *
FROM sales
WHERE quantity <= 0 OR unit_price < 0;

-- Demonstrate that stale approvals are excluded from current approval counts.
SELECT
    u.username,
    r.state,
    r.stale
FROM reviews r
JOIN users u ON u.user_id = r.reviewer_id
WHERE r.pull_request_id = (
    SELECT pull_request_id
    FROM pull_requests
    WHERE source_branch = 'feature/sales-dashboard'
)
ORDER BY r.review_id;
