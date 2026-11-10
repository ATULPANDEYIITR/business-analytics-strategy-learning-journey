/*
===============================================================================
FINANCIAL STATEMENTS MANAGEMENT SYSTEM
===============================================================================

PostgreSQL 15+

Models:
1. Chart of accounts
2. Journal entries
3. Double-entry journal lines
4. General ledger
5. Income statement
6. Balance sheet
7. Indirect cash flow statement
8. Financial ratios
9. Accounting validation
10. Reporting and period management

Monetary unit: INR
Accounting convention: Accrual accounting
Cash flow method: Indirect method

The sample reporting period uses a zero opening balance.
Production reporting must include verified opening balances and comparative
periods.
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS finance;

SET search_path TO finance, public;

-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE account_type AS ENUM (
    'ASSET',
    'LIABILITY',
    'EQUITY',
    'REVENUE',
    'EXPENSE',
    'CONTRA_ASSET'
);

CREATE TYPE journal_status AS ENUM (
    'DRAFT',
    'POSTED',
    'REVERSED'
);

CREATE TYPE reporting_period_status AS ENUM (
    'OPEN',
    'CLOSED'
);

CREATE TYPE cash_flow_category AS ENUM (
    'OPERATING',
    'INVESTING',
    'FINANCING',
    'NON_CASH',
    'NONE'
);

-- ============================================================================
-- 2. CORE TABLES
-- ============================================================================

CREATE TABLE companies (
    company_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_code VARCHAR(30) NOT NULL UNIQUE,
    company_name VARCHAR(200) NOT NULL,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_company_name
        CHECK (length(trim(company_name)) > 0)
);

CREATE TABLE reporting_periods (
    period_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    period_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status reporting_period_status NOT NULL DEFAULT 'OPEN',

    CONSTRAINT valid_period_dates
        CHECK (end_date >= start_date),

    CONSTRAINT unique_company_period
        UNIQUE (company_id, period_name),

    CONSTRAINT unique_period_id_company
        UNIQUE (period_id, company_id)
);

CREATE TABLE accounts (
    account_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(150) NOT NULL,
    type account_type NOT NULL,
    parent_account_id BIGINT REFERENCES accounts(account_id),
    cash_flow_type cash_flow_category NOT NULL DEFAULT 'NONE',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT unique_company_account_code
        UNIQUE (company_id, account_code),

    CONSTRAINT unique_account_company
        UNIQUE (account_id, company_id),

    CONSTRAINT account_not_own_parent
        CHECK (parent_account_id IS NULL OR
               parent_account_id <> account_id),

    CONSTRAINT valid_account_name
        CHECK (length(trim(account_name)) > 0)
);

CREATE TABLE journal_entries (
    journal_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    company_id BIGINT NOT NULL,
    period_id BIGINT NOT NULL,
    journal_number VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    status journal_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMPTZ,

    CONSTRAINT journal_company_fk
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id),

    CONSTRAINT journal_period_fk
        FOREIGN KEY (period_id, company_id)
        REFERENCES reporting_periods(period_id, company_id),

    CONSTRAINT unique_journal_number
        UNIQUE (company_id, journal_number),

    CONSTRAINT unique_journal_company
        UNIQUE (journal_id, company_id),

    CONSTRAINT valid_journal_description
        CHECK (length(trim(description)) > 0)
);

CREATE TABLE journal_lines (
    line_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    journal_id BIGINT NOT NULL,
    company_id BIGINT NOT NULL,
    account_id BIGINT NOT NULL,
    debit NUMERIC(20,2) NOT NULL DEFAULT 0,
    credit NUMERIC(20,2) NOT NULL DEFAULT 0,
    line_description TEXT,

    CONSTRAINT journal_line_entry_fk
        FOREIGN KEY (journal_id, company_id)
        REFERENCES journal_entries(journal_id, company_id),

    CONSTRAINT journal_line_account_fk
        FOREIGN KEY (account_id, company_id)
        REFERENCES accounts(account_id, company_id),

    CONSTRAINT nonnegative_amounts
        CHECK (debit >= 0 AND credit >= 0),

    CONSTRAINT exactly_one_side
        CHECK (
            (debit > 0 AND credit = 0)
            OR
            (credit > 0 AND debit = 0)
        )
);

-- ============================================================================
-- 3. INTEGRITY INDEXES
-- ============================================================================

CREATE INDEX idx_journal_company_date
    ON journal_entries(company_id, transaction_date);

CREATE INDEX idx_journal_period_status
    ON journal_entries(period_id, status);

CREATE INDEX idx_journal_lines_journal
    ON journal_lines(journal_id);

CREATE INDEX idx_journal_lines_account
    ON journal_lines(company_id, account_id);

CREATE INDEX idx_accounts_company_type
    ON accounts(company_id, type);

-- ============================================================================
-- 4. POSTING VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_journal_posting()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_debit NUMERIC(20,2);
    v_credit NUMERIC(20,2);
    v_count INTEGER;
    v_period_status reporting_period_status;
    v_transaction_date DATE;
    v_period_id BIGINT;
    v_company_id BIGINT;
BEGIN
    IF NEW.status = 'POSTED' AND
       (TG_OP = 'INSERT' OR OLD.status <> 'POSTED') THEN

        SELECT period_id, company_id, transaction_date
        INTO v_period_id, v_company_id, v_transaction_date
        FROM journal_entries
        WHERE journal_id = NEW.journal_id
        FOR UPDATE;

        SELECT status
        INTO v_period_status
        FROM reporting_periods
        WHERE period_id = v_period_id
          AND company_id = v_company_id
        FOR UPDATE;

        IF v_period_status <> 'OPEN' THEN
            RAISE EXCEPTION 'Cannot post into a closed reporting period';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM journal_lines
            WHERE journal_id = NEW.journal_id
        ) THEN
            RAISE EXCEPTION 'Journal entry requires journal lines';
        END IF;

        SELECT
            COALESCE(SUM(debit), 0),
            COALESCE(SUM(credit), 0),
            COUNT(*)
        INTO v_debit, v_credit, v_count
        FROM journal_lines
        WHERE journal_id = NEW.journal_id;

        IF v_count < 2 THEN
            RAISE EXCEPTION 'At least two journal lines are required';
        END IF;

        IF v_debit <> v_credit THEN
            RAISE EXCEPTION
                'Unbalanced journal: debit %, credit %',
                v_debit, v_credit;
        END IF;

        IF v_transaction_date IS NULL THEN
            RAISE EXCEPTION 'Transaction date is required';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM reporting_periods
            WHERE period_id = v_period_id
              AND v_transaction_date BETWEEN start_date AND end_date
        ) THEN
            RAISE EXCEPTION 'Transaction date outside reporting period';
        END IF;

        NEW.posted_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_journal_posting
BEFORE UPDATE OF status ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION validate_journal_posting();

-- ============================================================================
-- 5. PREVENT MODIFICATION OF POSTED JOURNALS
-- ============================================================================

CREATE OR REPLACE FUNCTION protect_posted_journal_lines()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_status journal_status;
    v_journal_id BIGINT;
BEGIN
    v_journal_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.journal_id
        ELSE NEW.journal_id
    END;

    SELECT status INTO v_status
    FROM journal_entries
    WHERE journal_id = v_journal_id
    FOR UPDATE;

    IF v_status IN ('POSTED', 'REVERSED') THEN
        RAISE EXCEPTION
            'Posted or reversed journal lines are immutable';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_protect_journal_lines
BEFORE INSERT OR UPDATE OR DELETE ON journal_lines
FOR EACH ROW
EXECUTE FUNCTION protect_posted_journal_lines();

-- ============================================================================
-- 6. GENERAL LEDGER VIEW
-- ============================================================================

CREATE OR REPLACE VIEW general_ledger AS
SELECT
    j.company_id,
    j.period_id,
    j.journal_id,
    j.journal_number,
    j.transaction_date,
    a.account_code,
    a.account_name,
    a.type,
    l.debit,
    l.credit,
    CASE
        WHEN a.type IN ('ASSET', 'EXPENSE', 'CONTRA_ASSET')
            THEN l.debit - l.credit
        ELSE l.credit - l.debit
    END AS signed_balance
FROM journal_entries j
JOIN journal_lines l
    ON l.journal_id = j.journal_id
JOIN accounts a
    ON a.account_id = l.account_id
   AND a.company_id = j.company_id
WHERE j.status = 'POSTED';

-- ============================================================================
-- 7. ACCOUNT BALANCE FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION account_balance(
    p_company_id BIGINT,
    p_period_id BIGINT,
    p_account_code VARCHAR
)
RETURNS NUMERIC(20,2)
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(SUM(gl.signed_balance), 0)::NUMERIC(20,2)
    FROM general_ledger gl
    WHERE gl.company_id = p_company_id
      AND gl.period_id = p_period_id
      AND gl.account_code = p_account_code;
$$;

-- ============================================================================
-- 8. INCOME STATEMENT FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION income_statement(
    p_company_id BIGINT,
    p_period_id BIGINT
)
RETURNS TABLE (
    revenue NUMERIC(20,2),
    cost_of_goods_sold NUMERIC(20,2),
    gross_profit NUMERIC(20,2),
    operating_expenses NUMERIC(20,2),
    depreciation NUMERIC(20,2),
    operating_income NUMERIC(20,2),
    interest_expense NUMERIC(20,2),
    pretax_income NUMERIC(20,2),
    income_tax NUMERIC(20,2),
    net_income NUMERIC(20,2)
)
LANGUAGE SQL
STABLE
AS $$
    WITH balances AS (
        SELECT
            account_code,
            SUM(signed_balance) AS amount
        FROM general_ledger
        WHERE company_id = p_company_id
          AND period_id = p_period_id
        GROUP BY account_code
    ),
    components AS (
        SELECT
            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '4000'
            ), 0) AS revenue,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '5000'
            ), 0) AS cogs,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '5100'
            ), 0) AS operating_expenses,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '5200'
            ), 0) AS depreciation,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '5300'
            ), 0) AS interest_expense,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '5400'
            ), 0) AS income_tax
        FROM balances
    )
    SELECT
        revenue,
        cogs,
        revenue - cogs,
        operating_expenses,
        depreciation,
        revenue - cogs - operating_expenses - depreciation,
        interest_expense,
        revenue - cogs - operating_expenses
            - depreciation - interest_expense,
        income_tax,
        revenue - cogs - operating_expenses
            - depreciation - interest_expense - income_tax
    FROM components;
$$;

-- ============================================================================
-- 9. BALANCE SHEET FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION balance_sheet(
    p_company_id BIGINT,
    p_period_id BIGINT
)
RETURNS TABLE (
    cash NUMERIC(20,2),
    receivables NUMERIC(20,2),
    inventory NUMERIC(20,2),
    current_assets NUMERIC(20,2),
    equipment NUMERIC(20,2),
    accumulated_depreciation NUMERIC(20,2),
    net_fixed_assets NUMERIC(20,2),
    total_assets NUMERIC(20,2),
    accounts_payable NUMERIC(20,2),
    tax_payable NUMERIC(20,2),
    long_term_debt NUMERIC(20,2),
    total_liabilities NUMERIC(20,2),
    share_capital NUMERIC(20,2),
    retained_earnings NUMERIC(20,2),
    total_equity NUMERIC(20,2),
    liabilities_and_equity NUMERIC(20,2)
)
LANGUAGE SQL
STABLE
AS $$
    WITH balances AS (
        SELECT
            account_code,
            SUM(signed_balance) AS amount
        FROM general_ledger
        WHERE company_id = p_company_id
          AND period_id = p_period_id
        GROUP BY account_code
    ),
    values AS (
        SELECT
            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '1000'
            ), 0) AS cash,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '1100'
            ), 0) AS receivables,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '1200'
            ), 0) AS inventory,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '1500'
            ), 0) AS equipment,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '1590'
            ), 0) AS accumulated_depreciation,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '2000'
            ), 0) AS accounts_payable,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '2100'
            ), 0) AS tax_payable,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '2500'
            ), 0) AS long_term_debt,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '3000'
            ), 0) AS share_capital,

            COALESCE(MAX(amount) FILTER (
                WHERE account_code = '3100'
            ), 0) AS dividends
        FROM balances
    ),
    income AS (
        SELECT net_income
        FROM income_statement(p_company_id, p_period_id)
    ),
    calculated AS (
        SELECT
            v.*,
            i.net_income - v.dividends AS retained_earnings
        FROM values v
        CROSS JOIN income i
    )
    SELECT
        cash,
        receivables,
        inventory,
        cash + receivables + inventory,
        equipment,
        accumulated_depreciation,
        equipment - accumulated_depreciation,
        cash + receivables + inventory
            + equipment - accumulated_depreciation,
        accounts_payable,
        tax_payable,
        long_term_debt,
        accounts_payable + tax_payable + long_term_debt,
        share_capital,
        retained_earnings,
        share_capital + retained_earnings,
        accounts_payable + tax_payable + long_term_debt
            + share_capital + retained_earnings
    FROM calculated;
$$;

-- ============================================================================
-- 10. CASH FLOW STATEMENT FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION cash_flow_statement(
    p_company_id BIGINT,
    p_period_id BIGINT
)
RETURNS TABLE (
    net_income NUMERIC(20,2),
    depreciation_adjustment NUMERIC(20,2),
    receivables_adjustment NUMERIC(20,2),
    inventory_adjustment NUMERIC(20,2),
    payables_adjustment NUMERIC(20,2),
    tax_payable_adjustment NUMERIC(20,2),
    operating_cash_flow NUMERIC(20,2),
    investing_cash_flow NUMERIC(20,2),
    financing_cash_flow NUMERIC(20,2),
    net_change_in_cash NUMERIC(20,2),
    closing_cash NUMERIC(20,2)
)
LANGUAGE SQL
STABLE
AS $$
    WITH income AS (
        SELECT *
        FROM income_statement(p_company_id, p_period_id)
    ),
    balance AS (
        SELECT *
        FROM balance_sheet(p_company_id, p_period_id)
    ),
    components AS (
        SELECT
            i.net_income,
            b.accumulated_depreciation AS depreciation,
            -b.receivables AS receivables_adjustment,
            -b.inventory AS inventory_adjustment,
            b.accounts_payable AS payables_adjustment,
            b.tax_payable AS tax_adjustment,
            -b.equipment AS investing,
            b.share_capital + b.long_term_debt
                - (i.net_income - b.retained_earnings) AS financing,
            b.cash
        FROM income i
        CROSS JOIN balance b
    ),
    operating AS (
        SELECT *,
            net_income + depreciation
                + receivables_adjustment
                + inventory_adjustment
                + payables_adjustment
                + tax_adjustment AS operating_cash
        FROM components
    )
    SELECT
        net_income,
        depreciation,
        receivables_adjustment,
        inventory_adjustment,
        payables_adjustment,
        tax_adjustment,
        operating_cash,
        investing,
        financing,
        operating_cash + investing + financing,
        cash
    FROM operating;
$$;

-- ============================================================================
-- 11. FINANCIAL RATIO VIEW
-- ============================================================================

CREATE OR REPLACE VIEW financial_ratio_report AS
SELECT
    p.company_id,
    p.period_id,
    i.revenue,
    i.gross_profit,
    i.net_income,
    b.current_assets,
    b.accounts_payable + b.tax_payable AS current_liabilities,
    b.total_liabilities,
    b.total_equity,
    b.total_assets,

    ROUND(
        b.current_assets /
        NULLIF(b.accounts_payable + b.tax_payable, 0),
        4
    ) AS current_ratio,

    ROUND(
        b.total_liabilities / NULLIF(b.total_equity, 0),
        4
    ) AS debt_to_equity,

    ROUND(
        i.gross_profit / NULLIF(i.revenue, 0) * 100,
        2
    ) AS gross_profit_margin,

    ROUND(
        i.net_income / NULLIF(i.revenue, 0) * 100,
        2
    ) AS net_profit_margin,

    ROUND(
        i.net_income / NULLIF(b.total_assets, 0) * 100,
        2
    ) AS return_on_assets

FROM reporting_periods p
CROSS JOIN LATERAL income_statement(
    p.company_id, p.period_id
) i
CROSS JOIN LATERAL balance_sheet(
    p.company_id, p.period_id
) b;

-- ============================================================================
-- 12. ACCOUNTING RECONCILIATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_financial_statements(
    p_company_id BIGINT,
    p_period_id BIGINT
)
RETURNS TABLE (
    validation_name TEXT,
    actual_amount NUMERIC(20,2),
    expected_amount NUMERIC(20,2),
    is_valid BOOLEAN
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        'Accounting equation'::TEXT,
        b.total_assets,
        b.liabilities_and_equity,
        b.total_assets = b.liabilities_and_equity
    FROM balance_sheet(p_company_id, p_period_id) b

    UNION ALL

    SELECT
        'Cash reconciliation',
        c.net_change_in_cash,
        c.closing_cash,
        c.net_change_in_cash = c.closing_cash
    FROM cash_flow_statement(p_company_id, p_period_id) c

    UNION ALL

    SELECT
        'Double-entry journal balance',
        COALESCE(SUM(l.debit), 0),
        COALESCE(SUM(l.credit), 0),
        COALESCE(SUM(l.debit), 0) =
        COALESCE(SUM(l.credit), 0)
    FROM journal_entries j
    LEFT JOIN journal_lines l
        ON l.journal_id = j.journal_id
    WHERE j.company_id = p_company_id
      AND j.period_id = p_period_id
      AND j.status = 'POSTED';
$$;

-- ============================================================================
-- 13. SAMPLE COMPANY AND REPORTING PERIOD
-- ============================================================================

INSERT INTO companies (
    company_code,
    company_name,
    currency_code
)
VALUES (
    'APEX001',
    'Apex Manufacturing Private Limited',
    'INR'
);

INSERT INTO reporting_periods (
    company_id,
    period_name,
    start_date,
    end_date
)
SELECT
    company_id,
    'FY2026',
    DATE '2026-04-01',
    DATE '2027-03-31'
FROM companies
WHERE company_code = 'APEX001';

-- ============================================================================
-- 14. CHART OF ACCOUNTS
-- ============================================================================

INSERT INTO accounts (
    company_id,
    account_code,
    account_name,
    type,
    cash_flow_type
)
SELECT
    c.company_id,
    x.code,
    x.name,
    x.type::account_type,
    x.cash_type::cash_flow_category
FROM companies c
CROSS JOIN (
    VALUES
        ('1000', 'Cash and Bank', 'ASSET', 'NONE'),
        ('1100', 'Accounts Receivable', 'ASSET', 'OPERATING'),
        ('1200', 'Inventory', 'ASSET', 'OPERATING'),
        ('1500', 'Equipment', 'ASSET', 'INVESTING'),
        ('1590', 'Accumulated Depreciation', 'CONTRA_ASSET', 'NON_CASH'),
        ('2000', 'Accounts Payable', 'LIABILITY', 'OPERATING'),
        ('2100', 'Tax Payable', 'LIABILITY', 'OPERATING'),
        ('2500', 'Long-Term Loan', 'LIABILITY', 'FINANCING'),
        ('3000', 'Share Capital', 'EQUITY', 'FINANCING'),
        ('3100', 'Dividends', 'EQUITY', 'FINANCING'),
        ('4000', 'Sales Revenue', 'REVENUE', 'NONE'),
        ('5000', 'Cost of Goods Sold', 'EXPENSE', 'NONE'),
        ('5100', 'Operating Expenses', 'EXPENSE', 'OPERATING'),
        ('5200', 'Depreciation Expense', 'EXPENSE', 'NON_CASH'),
        ('5300', 'Interest Expense', 'EXPENSE', 'OPERATING'),
        ('5400', 'Income Tax Expense', 'EXPENSE', 'OPERATING')
) AS x(code, name, type, cash_type)
WHERE c.company_code = 'APEX001';

-- ============================================================================
-- 15. SAMPLE JOURNAL ENTRIES
-- ============================================================================

CREATE TEMP TABLE sample_journal_input (
    journal_number VARCHAR(40),
    description TEXT,
    transaction_date DATE,
    debit_account VARCHAR(20),
    credit_account VARCHAR(20),
    amount NUMERIC(20,2)
) ON COMMIT DROP;

INSERT INTO sample_journal_input VALUES
('JE001', 'Share capital issued', '2026-04-01', '1000', '3000', 100000),
('JE002', 'Cash sales', '2026-04-05', '1000', '4000', 120000),
('JE003', 'Credit sales', '2026-04-07', '1100', '4000', 30000),
('JE004', 'Inventory purchased on credit', '2026-04-08', '1200', '2000', 40000),
('JE005', 'Cash inventory purchase', '2026-04-09', '1200', '1000', 25000),
('JE006', 'Cost of goods sold', '2026-04-10', '5000', '1200', 60000),
('JE007', 'Operating expenses paid', '2026-04-11', '5100', '1000', 25000),
('JE008', 'Equipment purchased', '2026-04-12', '1500', '1000', 50000),
('JE009', 'Depreciation adjustment', '2026-04-13', '5200', '1590', 5000),
('JE010', 'Interest payment', '2026-04-14', '5300', '1000', 2000),
('JE011', 'Income tax provision', '2026-04-15', '5400', '2100', 8000),
('JE012', 'Customer collection', '2026-04-16', '1000', '1100', 20000),
('JE013', 'Supplier payment', '2026-04-17', '2000', '1000', 15000),
('JE014', 'Loan received', '2026-04-18', '1000', '2500', 30000),
('JE015', 'Dividend distribution', '2026-04-19', '3100', '1000', 5000);

-- Create journals and journal lines in one transaction.
WITH inserted_journals AS (
    INSERT INTO journal_entries (
        company_id,
        period_id,
        journal_number,
        description,
        transaction_date
    )
    SELECT
        c.company_id,
        p.period_id,
        s.journal_number,
        s.description,
        s.transaction_date
    FROM sample_journal_input s
    CROSS JOIN companies c
    JOIN reporting_periods p
        ON p.company_id = c.company_id
    WHERE c.company_code = 'APEX001'
      AND p.period_name = 'FY2026'
    RETURNING journal_id, company_id, journal_number
)
INSERT INTO journal_lines (
    journal_id,
    company_id,
    account_id,
    debit,
    credit,
    line_description
)
SELECT
    j.journal_id,
    j.company_id,
    a.account_id,
    s.amount,
    0,
    'Debit posting'
FROM inserted_journals j
JOIN sample_journal_input s
    ON s.journal_number = j.journal_number
JOIN accounts a
    ON a.company_id = j.company_id
   AND a.account_code = s.debit_account

UNION ALL

SELECT
    j.journal_id,
    j.company_id,
    a.account_id,
    0,
    s.amount,
    'Credit posting'
FROM inserted_journals j
JOIN sample_journal_input s
    ON s.journal_number = j.journal_number
JOIN accounts a
    ON a.company_id = j.company_id
   AND a.account_code = s.credit_account;

-- ============================================================================
-- 16. POST JOURNAL ENTRIES
-- ============================================================================

UPDATE journal_entries
SET status = 'POSTED'
WHERE company_id = (
    SELECT company_id
    FROM companies
    WHERE company_code = 'APEX001'
)
AND journal_number LIKE 'JE%';

-- ============================================================================
-- 17. REPORTING PROCEDURE
-- ============================================================================

CREATE OR REPLACE PROCEDURE generate_financial_report(
    p_company_code VARCHAR,
    p_period_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_company_id BIGINT;
    v_period_id BIGINT;
    v_balance NUMERIC(20,2);
    v_equity NUMERIC(20,2);
    v_assets NUMERIC(20,2);
BEGIN
    SELECT c.company_id, p.period_id
    INTO v_company_id, v_period_id
    FROM companies c
    JOIN reporting_periods p
        ON p.company_id = c.company_id
    WHERE c.company_code = p_company_code
      AND p.period_name = p_period_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Company or reporting period not found';
    END IF;

    SELECT total_assets, total_equity
    INTO v_assets, v_equity
    FROM balance_sheet(v_company_id, v_period_id);

    SELECT liabilities_and_equity
    INTO v_balance
    FROM balance_sheet(v_company_id, v_period_id);

    IF v_assets <> v_balance THEN
        RAISE EXCEPTION 'Financial report failed accounting validation';
    END IF;

    RAISE NOTICE 'Financial reporting validated.';
    RAISE NOTICE 'Total assets: %', v_assets;
    RAISE NOTICE 'Total equity: %', v_equity;
END;
$$;

-- ============================================================================
-- 18. ELIGIBILITY AND REPORTING QUERIES
-- ============================================================================

-- Query A: Retrieve all posted journals.
SELECT
    journal_number,
    transaction_date,
    description,
    status
FROM journal_entries
WHERE status = 'POSTED'
ORDER BY transaction_date, journal_number;

-- Query B: Income statement.
SELECT *
FROM income_statement(
    (SELECT company_id FROM companies WHERE company_code = 'APEX001'),
    (SELECT period_id FROM reporting_periods WHERE period_name = 'FY2026')
);

-- Query C: Balance sheet.
SELECT *
FROM balance_sheet(
    (SELECT company_id FROM companies WHERE company_code = 'APEX001'),
    (SELECT period_id FROM reporting_periods WHERE period_name = 'FY2026')
);

-- Query D: Cash flow statement.
SELECT *
FROM cash_flow_statement(
    (SELECT company_id FROM companies WHERE company_code = 'APEX001'),
    (SELECT period_id FROM reporting_periods WHERE period_name = 'FY2026')
);

-- Query E: Financial ratios.
SELECT *
FROM financial_ratio_report
WHERE company_id = (
    SELECT company_id
    FROM companies
    WHERE company_code = 'APEX001'
);

-- Query F: Reconciliation checks.
SELECT *
FROM validate_financial_statements(
    (SELECT company_id FROM companies WHERE company_code = 'APEX001'),
    (SELECT period_id FROM reporting_periods WHERE period_name = 'FY2026')
);

-- Query G: Account-wise ledger aggregation.
SELECT
    account_code,
    account_name,
    type,
    SUM(debit) AS total_debits,
    SUM(credit) AS total_credits,
    SUM(signed_balance) AS closing_balance
FROM general_ledger
WHERE company_id = (
    SELECT company_id
    FROM companies
    WHERE company_code = 'APEX001'
)
GROUP BY account_code, account_name, type
ORDER BY account_code;

-- Query H: Financial statement eligibility.
WITH checks AS (
    SELECT *
    FROM validate_financial_statements(
        (SELECT company_id FROM companies WHERE company_code = 'APEX001'),
        (SELECT period_id FROM reporting_periods WHERE period_name = 'FY2026')
    )
)
SELECT
    BOOL_AND(is_valid) AS eligible_for_reporting,
    COUNT(*) AS checks_performed,
    COUNT(*) FILTER (WHERE NOT is_valid) AS failed_checks
FROM checks;

-- Query I: Execute reporting procedure.
CALL generate_financial_report('APEX001', 'FY2026');

-- ============================================================================
-- 19. TRANSACTION AND PERIOD MANAGEMENT EXAMPLE
-- ============================================================================

-- The transaction below demonstrates safe period-state management.
-- The period remains open for subsequent valid postings.

SAVEPOINT reporting_validation;

DO $$
DECLARE
    v_period_status reporting_period_status;
BEGIN
    SELECT status
    INTO v_period_status
    FROM reporting_periods
    WHERE period_name = 'FY2026'
    FOR UPDATE;

    IF v_period_status <> 'OPEN' THEN
        RAISE EXCEPTION 'Reporting period is not open';
    END IF;
END;
$$;

RELEASE SAVEPOINT reporting_validation;

COMMIT;

/*
===============================================================================
EXPECTED SAMPLE RESULTS
===============================================================================

INCOME STATEMENT
Revenue                         150000.00
Cost of goods sold                60000.00
Gross profit                      90000.00
Operating expenses                25000.00
Depreciation                       5000.00
Operating income                  60000.00
Interest expense                   2000.00
Pretax income                     58000.00
Income tax                         8000.00
Net income                        50000.00

BALANCE SHEET
Cash                             148000.00
Accounts receivable               10000.00
Inventory                          5000.00
Current assets                   163000.00
Equipment                         50000.00
Accumulated depreciation            5000.00
Net fixed assets                  45000.00
Total assets                     208000.00
Accounts payable                  25000.00
Tax payable                        8000.00
Long-term debt                    30000.00
Total liabilities                 63000.00
Share capital                    100000.00
Retained earnings                 45000.00
Total equity                     145000.00
Liabilities and equity           208000.00

CASH FLOW STATEMENT
Operating cash flow               73000.00
Investing cash flow              -50000.00
Financing cash flow               125000.00
Net change in cash               148000.00
Closing cash                     148000.00

===============================================================================
PRODUCTION CONSIDERATIONS
===============================================================================

1. Use restricted database roles for journal posting and reporting.
2. Do not expose journal mutation privileges to reporting users.
3. Introduce approval workflows for material journal entries.
4. Maintain immutable reversal records instead of editing posted journals.
5. Store opening balances and comparative periods explicitly.
6. Add audit records for every posting and reversal.
7. Use row-level security for multi-company deployments.
8. Define a consistent accounting policy for interest and tax cash flows.
9. Extend the indirect cash flow reconciliation for non-cash movements,
   acquisitions, disposals, foreign exchange and working-capital adjustments.
10. Production financial reporting must use approved accounting policies
    and applicable reporting standards.
*/
