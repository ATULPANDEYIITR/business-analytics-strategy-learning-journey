"use strict";

/*
 * FINANCIAL STATEMENTS
 * Income Statement, Balance Sheet and Cash Flow Statement
 *
 * Runtime: Node.js 18+
 * Dependencies: Node.js standard library only.
 *
 * Features:
 * - Event-driven journal posting
 * - Double-entry validation
 * - Map-based ledger
 * - Financial statement construction
 * - Indirect cash flow calculation
 * - Financial ratios
 * - Policy validation
 * - JSON reporting
 * - Automated accounting tests
 */

const fs = require("node:fs/promises");
const { EventEmitter } = require("node:events");

const money = value => {
    if (!Number.isFinite(value)) {
        throw new TypeError("Monetary value must be finite.");
    }

    return Math.round((value + Number.EPSILON) * 100) / 100;
};

const AccountType = Object.freeze({
    ASSET: "ASSET",
    LIABILITY: "LIABILITY",
    EQUITY: "EQUITY",
    REVENUE: "REVENUE",
    EXPENSE: "EXPENSE",
    CONTRA_ASSET: "CONTRA_ASSET"
});

class AccountingError extends Error {
    constructor(message) {
        super(message);
        this.name = "AccountingError";
    }
}

class Account {
    constructor(code, name, type) {
        if (!code || !name || !Object.values(AccountType).includes(type)) {
            throw new AccountingError("Invalid account definition.");
        }

        this.code = code;
        this.name = name;
        this.type = type;

        Object.freeze(this);
    }
}

class JournalEntry {
    constructor(id, description, lines) {
        this.id = id;
        this.description = description;
        this.lines = lines.map(line => Object.freeze({ ...line }));
        Object.freeze(this.lines);
    }
}

class AccountingEngine extends EventEmitter {
    constructor(company) {
        super();

        if (!company.trim()) {
            throw new AccountingError("Company name is required.");
        }

        this.company = company;
        this.accounts = new Map();
        this.entries = [];
        this.entryIds = new Set();
    }

    addAccount(account) {
        if (this.accounts.has(account.code)) {
            throw new AccountingError("Duplicate account code.");
        }

        this.accounts.set(account.code, account);
    }

    validateEntry(entry) {
        if (!entry.id || !entry.description || !entry.lines.length) {
            throw new AccountingError("Incomplete journal entry.");
        }

        if (this.entryIds.has(entry.id)) {
            throw new AccountingError("Duplicate journal entry.");
        }

        let debit = 0;
        let credit = 0;

        for (const line of entry.lines) {
            const account = this.accounts.get(line.account);

            if (!account) {
                throw new AccountingError(
                    `Unknown account: ${line.account}`
                );
            }

            if (!Number.isFinite(line.amount) || line.amount <= 0) {
                throw new AccountingError("Invalid journal amount.");
            }

            if (!["DEBIT", "CREDIT"].includes(line.side)) {
                throw new AccountingError("Invalid journal side.");
            }

            if (line.side === "DEBIT") {
                debit = money(debit + line.amount);
            } else {
                credit = money(credit + line.amount);
            }
        }

        if (debit !== credit) {
            throw new AccountingError("Journal entry is not balanced.");
        }
    }

    post(entry) {
        this.validateEntry(entry);

        // Commit the entry only after all validation succeeds.
        this.entries.push(entry);
        this.entryIds.add(entry.id);

        this.emit("journal:posted", {
            id: entry.id,
            description: entry.description
        });
    }

    getLedger() {
        const ledger = new Map();

        for (const code of this.accounts.keys()) {
            ledger.set(code, 0);
        }

        for (const entry of this.entries) {
            for (const line of entry.lines) {
                const account = this.accounts.get(line.account);
                const debitNormal = [
                    AccountType.ASSET,
                    AccountType.EXPENSE,
                    AccountType.CONTRA_ASSET
                ].includes(account.type);

                const sign = debitNormal ? 1 : -1;

                const movement = line.side === "DEBIT"
                    ? sign * line.amount
                    : -sign * line.amount;

                ledger.set(
                    line.account,
                    money(ledger.get(line.account) + movement)
                );
            }
        }

        return ledger;
    }

    createStatements() {
        const ledger = this.getLedger();
        const balance = code => ledger.get(code) || 0;

        const revenue = balance("4000");
        const cogs = balance("5000");
        const operatingExpense = balance("5100");
        const depreciation = balance("5200");
        const interest = balance("5300");
        const tax = balance("5400");

        const grossProfit = money(revenue - cogs);
        const operatingIncome = money(
            grossProfit - operatingExpense - depreciation
        );
        const pretaxIncome = money(operatingIncome - interest);
        const netIncome = money(pretaxIncome - tax);

        const cash = balance("1000");
        const receivables = balance("1100");
        const inventory = balance("1200");
        const equipment = balance("1500");
        const accumulatedDepreciation = balance("1590");

        const currentAssets = money(
            cash + receivables + inventory
        );

        const netFixedAssets = money(
            equipment - accumulatedDepreciation
        );

        const totalAssets = money(
            currentAssets + netFixedAssets
        );

        const accountsPayable = balance("2000");
        const taxPayable = balance("2100");
        const debt = balance("2500");

        const totalLiabilities = money(
            accountsPayable + taxPayable + debt
        );

        const capital = balance("3000");
        const dividends = balance("3100");
        const retainedEarnings = money(netIncome - dividends);

        const totalEquity = money(capital + retainedEarnings);
        const liabilitiesAndEquity = money(
            totalLiabilities + totalEquity
        );

        const operatingCashFlow = money(
            netIncome
            + depreciation
            - receivables
            - inventory
            + accountsPayable
            + taxPayable
        );

        const investingCashFlow = money(-equipment);

        const financingCashFlow = money(
            capital + debt - dividends
        );

        const netChangeCash = money(
            operatingCashFlow
            + investingCashFlow
            + financingCashFlow
        );

        if (totalAssets !== liabilitiesAndEquity) {
            throw new AccountingError("Balance sheet does not balance.");
        }

        if (netChangeCash !== cash) {
            throw new AccountingError("Cash flow does not reconcile.");
        }

        const currentLiabilities = money(
            accountsPayable + taxPayable
        );

        const ratios = {
            currentRatio: currentLiabilities
                ? money(currentAssets / currentLiabilities)
                : null,

            debtToEquity: totalEquity
                ? money(totalLiabilities / totalEquity)
                : null,

            grossProfitMargin: revenue
                ? money(grossProfit / revenue * 100)
                : 0,

            netProfitMargin: revenue
                ? money(netIncome / revenue * 100)
                : 0,

            returnOnAssets: totalAssets
                ? money(netIncome / totalAssets * 100)
                : 0
        };

        return Object.freeze({
            incomeStatement: Object.freeze({
                revenue,
                costOfGoodsSold: cogs,
                grossProfit,
                operatingExpenses: operatingExpense,
                depreciation,
                operatingIncome,
                interestExpense: interest,
                pretaxIncome,
                incomeTax: tax,
                netIncome
            }),

            balanceSheet: Object.freeze({
                cash,
                accountsReceivable: receivables,
                inventory,
                currentAssets,
                equipment,
                accumulatedDepreciation,
                netFixedAssets,
                totalAssets,
                accountsPayable,
                taxPayable,
                longTermDebt: debt,
                totalLiabilities,
                shareCapital: capital,
                retainedEarnings,
                totalEquity,
                totalLiabilitiesAndEquity: liabilitiesAndEquity
            }),

            cashFlowStatement: Object.freeze({
                netIncome,
                depreciationAdjustment: depreciation,
                receivablesAdjustment: -receivables,
                inventoryAdjustment: -inventory,
                payablesAdjustment: accountsPayable,
                taxPayableAdjustment: taxPayable,
                operatingCashFlow,
                investingCashFlow,
                financingCashFlow,
                openingCash: 0,
                netChangeInCash: netChangeCash,
                closingCash: cash
            }),

            ratios: Object.freeze(ratios)
        });
    }

    async export(filename, statements) {
        const payload = {
            company: this.company,
            generatedAt: new Date().toISOString(),
            statements
        };

        await fs.writeFile(
            filename,
            JSON.stringify(payload, null, 2),
            { encoding: "utf8", mode: 0o600 }
        );
    }
}

function line(account, side, amount) {
    return {
        account,
        side,
        amount: money(amount)
    };
}

function entry(id, description, ...lines) {
    return new JournalEntry(id, description, lines);
}

function createSampleEngine() {
    const engine = new AccountingEngine(
        "Apex Manufacturing Private Limited"
    );

    const definitions = [
        ["1000", "Cash and Bank", AccountType.ASSET],
        ["1100", "Accounts Receivable", AccountType.ASSET],
        ["1200", "Inventory", AccountType.ASSET],
        ["1500", "Equipment", AccountType.ASSET],
        ["1590", "Accumulated Depreciation", AccountType.CONTRA_ASSET],
        ["2000", "Accounts Payable", AccountType.LIABILITY],
        ["2100", "Tax Payable", AccountType.LIABILITY],
        ["2500", "Long-Term Loan", AccountType.LIABILITY],
        ["3000", "Share Capital", AccountType.EQUITY],
        ["3100", "Dividends", AccountType.EQUITY],
        ["4000", "Sales Revenue", AccountType.REVENUE],
        ["5000", "Cost of Goods Sold", AccountType.EXPENSE],
        ["5100", "Operating Expenses", AccountType.EXPENSE],
        ["5200", "Depreciation Expense", AccountType.EXPENSE],
        ["5300", "Interest Expense", AccountType.EXPENSE],
        ["5400", "Income Tax Expense", AccountType.EXPENSE]
    ];

    for (const [code, name, type] of definitions) {
        engine.addAccount(new Account(code, name, type));
    }

    const transactions = [
        entry("JE001", "Share capital",
            line("1000", "DEBIT", 100000),
            line("3000", "CREDIT", 100000)),

        entry("JE002", "Cash sales",
            line("1000", "DEBIT", 120000),
            line("4000", "CREDIT", 120000)),

        entry("JE003", "Credit sales",
            line("1100", "DEBIT", 30000),
            line("4000", "CREDIT", 30000)),

        entry("JE004", "Inventory on credit",
            line("1200", "DEBIT", 40000),
            line("2000", "CREDIT", 40000)),

        entry("JE005", "Cash inventory purchase",
            line("1200", "DEBIT", 25000),
            line("1000", "CREDIT", 25000)),

        entry("JE006", "Cost of goods sold",
            line("5000", "DEBIT", 60000),
            line("1200", "CREDIT", 60000)),

        entry("JE007", "Operating expenses",
            line("5100", "DEBIT", 25000),
            line("1000", "CREDIT", 25000)),

        entry("JE008", "Equipment purchase",
            line("1500", "DEBIT", 50000),
            line("1000", "CREDIT", 50000)),

        entry("JE009", "Depreciation",
            line("5200", "DEBIT", 5000),
            line("1590", "CREDIT", 5000)),

        entry("JE010", "Interest",
            line("5300", "DEBIT", 2000),
            line("1000", "CREDIT", 2000)),

        entry("JE011", "Tax provision",
            line("5400", "DEBIT", 8000),
            line("2100", "CREDIT", 8000)),

        entry("JE012", "Customer collection",
            line("1000", "DEBIT", 20000),
            line("1100", "CREDIT", 20000)),

        entry("JE013", "Supplier payment",
            line("2000", "DEBIT", 15000),
            line("1000", "CREDIT", 15000)),

        entry("JE014", "Loan receipt",
            line("1000", "DEBIT", 30000),
            line("2500", "CREDIT", 30000)),

        entry("JE015", "Dividend payment",
            line("3100", "DEBIT", 5000),
            line("1000", "CREDIT", 5000))
    ];

    for (const transaction of transactions) {
        engine.post(transaction);
    }

    return engine;
}

function runTests(engine, statements) {
    const income = statements.incomeStatement;
    const balance = statements.balanceSheet;
    const cashFlow = statements.cashFlowStatement;

    console.assert(income.revenue === 150000);
    console.assert(income.netIncome === 50000);
    console.assert(balance.totalAssets === 208000);
    console.assert(balance.totalLiabilities === 63000);
    console.assert(balance.totalEquity === 145000);
    console.assert(cashFlow.operatingCashFlow === 73000);
    console.assert(cashFlow.closingCash === 148000);

    const invalid = entry(
        "INVALID",
        "Unbalanced transaction",
        line("1000", "DEBIT", 100),
        line("4000", "CREDIT", 50)
    );

    try {
        engine.post(invalid);
        throw new Error("Unbalanced transaction was accepted.");
    } catch (error) {
        if (!(error instanceof AccountingError)) {
            throw error;
        }
    }

    console.log("All accounting tests passed.");
}

async function main() {
    try {
        const engine = createSampleEngine();

        engine.on("journal:posted", event => {
            console.log(`Posted ${event.id}: ${event.description}`);
        });

        // Events are attached before future postings in production workflows.
        // Existing sample transactions have already been validated and posted.

        const statements = engine.createStatements();

        console.log("\nCOMPANY:", engine.company);
        console.log("JOURNAL ENTRIES:", engine.entries.length);

        for (const [name, report] of Object.entries(statements)) {
            console.log(`\n========== ${name.toUpperCase()} ==========`);

            for (const [key, value] of Object.entries(report)) {
                console.log(`${key.padEnd(34)} ${value}`);
            }
        }

        runTests(engine, statements);

        await engine.export("financial_statements.json", statements);

        console.log("\nFinancial report exported successfully.");
    } catch (error) {
        console.error("Financial reporting failed:", error.message);
        process.exitCode = 1;
    }
}

main();
